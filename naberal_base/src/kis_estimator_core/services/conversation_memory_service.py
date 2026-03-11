"""
대화 영구 메모리 서비스 (SSOT - Single Source of Truth)
- Railway PostgreSQL DB 기반 영구 저장소
- 세션 관리, 자동 요약 생성
- 대화 연속성 보장
- FileBasedStorage fallback 유지
"""
import json
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


# ===== 스키마 정의 =====
class ConversationMessage(BaseModel):
    """단일 대화 메시지"""
    role: str = Field(..., description="user 또는 assistant")
    content: str = Field(..., description="메시지 내용")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    intent: Optional[str] = Field(default=None, description="파싱된 인텐트")
    metadata: dict = Field(default_factory=dict)


class ConversationSession(BaseModel):
    """대화 세션"""
    session_id: str = Field(..., description="세션 고유 ID")
    user_id: str = Field(default="default", description="사용자 ID")
    title: Optional[str] = Field(default=None, description="세션 제목 (자동 생성)")
    messages: list[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    summary: Optional[str] = Field(default=None, description="대화 요약")
    context_tags: list[str] = Field(default_factory=list, description="컨텍스트 태그")
    is_active: bool = Field(default=True)


class MemoryEntry(BaseModel):
    """영구 메모리 항목 (중요한 정보 저장)"""
    memory_id: str
    user_id: str = "default"
    category: str = Field(..., description="customer|project|preference|knowledge")
    key: str = Field(..., description="메모리 키")
    value: str = Field(..., description="메모리 값")
    source_session_id: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
    importance: int = Field(default=5, ge=1, le=10)


# ===== PostgreSQL DB 기반 저장소 =====
class DatabaseStorage:
    """PostgreSQL 기반 영구 저장소 (Railway DB)"""

    def __init__(self):
        self._db = None

    def _get_db(self):
        if self._db is None:
            from kis_estimator_core.infra.db import get_db_instance
            self._db = get_db_instance()
        return self._db

    # ===== 세션 관리 =====
    async def save_session(self, session: ConversationSession) -> bool:
        """세션 저장 (UPSERT session + 새 메시지만 INSERT)"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                session.updated_at = datetime.utcnow()

                # UPSERT session
                await conn.execute(text("""
                    INSERT INTO conversation_sessions
                        (session_id, user_id, title, summary, is_active, created_at, updated_at)
                    VALUES
                        (:session_id, :user_id, :title, :summary, :is_active, :created_at, :updated_at)
                    ON CONFLICT (session_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        summary = EXCLUDED.summary,
                        is_active = EXCLUDED.is_active,
                        updated_at = EXCLUDED.updated_at
                """), {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "title": session.title,
                    "summary": session.summary,
                    "is_active": session.is_active,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                })

                # Count existing messages
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM conversation_messages WHERE session_id = :sid"),
                    {"sid": session.session_id}
                )
                existing_count = result.scalar() or 0

                # Insert only new messages
                new_messages = session.messages[existing_count:]
                for msg in new_messages:
                    meta_json = json.dumps(msg.metadata or {}, ensure_ascii=False)
                    await conn.execute(text("""
                        INSERT INTO conversation_messages
                            (session_id, role, content, timestamp, intent, metadata)
                        VALUES
                            (:session_id, :role, :content, :ts, :intent, CAST(:metadata AS jsonb))
                    """), {
                        "session_id": session.session_id,
                        "role": msg.role,
                        "content": msg.content,
                        "ts": msg.timestamp,
                        "intent": msg.intent,
                        "metadata": meta_json,
                    })

            logger.debug(f"Session saved to DB: {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session to DB: {e}")
            return False

    async def load_session(self, session_id: str) -> Optional[ConversationSession]:
        """세션 로드 (session + messages JOIN)"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                result = await conn.execute(
                    text("SELECT * FROM conversation_sessions WHERE session_id = :sid"),
                    {"sid": session_id}
                )
                row = result.mappings().first()
                if not row:
                    return None

                # Load messages
                msg_result = await conn.execute(
                    text("SELECT * FROM conversation_messages WHERE session_id = :sid ORDER BY timestamp ASC"),
                    {"sid": session_id}
                )
                messages = []
                for m in msg_result.mappings():
                    messages.append(ConversationMessage(
                        role=m["role"],
                        content=m["content"],
                        timestamp=m["timestamp"],
                        intent=m.get("intent"),
                        metadata=m.get("metadata") or {}
                    ))

                return ConversationSession(
                    session_id=row["session_id"],
                    user_id=row["user_id"],
                    title=row.get("title"),
                    messages=messages,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    summary=row.get("summary"),
                    context_tags=list(row.get("context_tags") or []),
                    is_active=row.get("is_active", True)
                )
        except Exception as e:
            logger.error(f"Failed to load session from DB: {e}")
            return None

    async def list_sessions(self, user_id: str = "default", limit: int = 20) -> list[ConversationSession]:
        """세션 목록 조회 (batch query for efficiency)"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                # Get sessions
                result = await conn.execute(text("""
                    SELECT * FROM conversation_sessions
                    WHERE user_id = :uid
                    ORDER BY updated_at DESC
                    LIMIT :lim
                """), {"uid": user_id, "lim": limit})
                session_rows = result.mappings().all()

                if not session_rows:
                    return []

                # Batch load message counts
                session_ids = [r["session_id"] for r in session_rows]

                # Build message count map
                count_result = await conn.execute(text("""
                    SELECT session_id, COUNT(*) as cnt
                    FROM conversation_messages
                    WHERE session_id = ANY(:sids)
                    GROUP BY session_id
                """), {"sids": session_ids})
                count_map = {r["session_id"]: r["cnt"] for r in count_result.mappings()}

                # Batch load all messages for these sessions
                msgs_result = await conn.execute(text("""
                    SELECT * FROM conversation_messages
                    WHERE session_id = ANY(:sids)
                    ORDER BY timestamp ASC
                """), {"sids": session_ids})

                messages_by_session: dict[str, list[ConversationMessage]] = {}
                for m in msgs_result.mappings():
                    sid = m["session_id"]
                    if sid not in messages_by_session:
                        messages_by_session[sid] = []
                    messages_by_session[sid].append(ConversationMessage(
                        role=m["role"],
                        content=m["content"],
                        timestamp=m["timestamp"],
                        intent=m.get("intent"),
                        metadata=m.get("metadata") or {}
                    ))

                # Build session objects
                sessions = []
                for row in session_rows:
                    sessions.append(ConversationSession(
                        session_id=row["session_id"],
                        user_id=row["user_id"],
                        title=row.get("title"),
                        messages=messages_by_session.get(row["session_id"], []),
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        summary=row.get("summary"),
                        context_tags=list(row.get("context_tags") or []),
                        is_active=row.get("is_active", True)
                    ))

                return sessions
        except Exception as e:
            logger.error(f"Failed to list sessions from DB: {e}")
            return []

    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제 (CASCADE deletes messages)"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                await conn.execute(
                    text("DELETE FROM conversation_sessions WHERE session_id = :sid"),
                    {"sid": session_id}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to delete session from DB: {e}")
            return False

    # ===== 요약 파일 관리 =====
    async def save_summary_md(self, session_id: str, md_content: str) -> bool:
        """세션 요약 저장 (conversation_summaries 테이블 + session.summary 업데이트)"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                # Update session summary
                await conn.execute(text("""
                    UPDATE conversation_sessions SET summary = :summary, updated_at = NOW()
                    WHERE session_id = :sid
                """), {"summary": md_content, "sid": session_id})

                # UPSERT into conversation_summaries
                await conn.execute(text("""
                    INSERT INTO conversation_summaries (session_id, summary_md, generated_at)
                    VALUES (:sid, :md, NOW())
                    ON CONFLICT (session_id) DO UPDATE SET
                        summary_md = EXCLUDED.summary_md,
                        generated_at = EXCLUDED.generated_at
                """), {"sid": session_id, "md": md_content})

            logger.info(f"Summary saved to DB: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save summary to DB: {e}")
            return False

    async def load_summary_md(self, session_id: str) -> Optional[str]:
        """세션 요약 로드"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                result = await conn.execute(
                    text("SELECT summary_md FROM conversation_summaries WHERE session_id = :sid"),
                    {"sid": session_id}
                )
                row = result.first()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to load summary from DB: {e}")
            return None

    async def load_latest_summary(self) -> Optional[str]:
        """최신 요약 로드 (대화 복원용)"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                result = await conn.execute(text("""
                    SELECT summary_md FROM conversation_summaries
                    ORDER BY generated_at DESC LIMIT 1
                """))
                row = result.first()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to load latest summary from DB: {e}")
            return None

    # ===== 메모리 관리 =====
    async def save_memory(self, memory: MemoryEntry) -> bool:
        """메모리 저장"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                await conn.execute(text("""
                    INSERT INTO conversation_memories
                        (memory_id, user_id, category, key, value,
                         source_session_id, importance, created_at, expires_at)
                    VALUES
                        (:mid, :uid, :cat, :key, :val,
                         :src_sid, :imp, :created, :expires)
                    ON CONFLICT (memory_id) DO UPDATE SET
                        value = EXCLUDED.value,
                        importance = EXCLUDED.importance,
                        expires_at = EXCLUDED.expires_at
                """), {
                    "mid": memory.memory_id,
                    "uid": memory.user_id,
                    "cat": memory.category,
                    "key": memory.key,
                    "val": memory.value,
                    "src_sid": memory.source_session_id,
                    "imp": memory.importance,
                    "created": memory.created_at,
                    "expires": memory.expires_at,
                })
            return True
        except Exception as e:
            logger.error(f"Failed to save memory to DB: {e}")
            return False

    async def load_memories(self, user_id: str = "default", category: Optional[str] = None) -> list[MemoryEntry]:
        """메모리 목록 조회"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                if category:
                    result = await conn.execute(text("""
                        SELECT * FROM conversation_memories
                        WHERE user_id = :uid AND category = :cat
                            AND (expires_at IS NULL OR expires_at > NOW())
                        ORDER BY importance DESC
                    """), {"uid": user_id, "cat": category})
                else:
                    result = await conn.execute(text("""
                        SELECT * FROM conversation_memories
                        WHERE user_id = :uid
                            AND (expires_at IS NULL OR expires_at > NOW())
                        ORDER BY importance DESC
                    """), {"uid": user_id})

                memories = []
                for row in result.mappings():
                    memories.append(MemoryEntry(
                        memory_id=row["memory_id"],
                        user_id=row["user_id"],
                        category=row["category"],
                        key=row["key"],
                        value=row["value"],
                        source_session_id=row.get("source_session_id"),
                        importance=row.get("importance", 5),
                        created_at=row["created_at"],
                        expires_at=row.get("expires_at"),
                    ))
                return memories
        except Exception as e:
            logger.error(f"Failed to load memories from DB: {e}")
            return []

    async def delete_memory(self, memory_id: str, user_id: str = "default") -> bool:
        """메모리 삭제"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                await conn.execute(
                    text("DELETE FROM conversation_memories WHERE memory_id = :mid AND user_id = :uid"),
                    {"mid": memory_id, "uid": user_id}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory from DB: {e}")
            return False

    # ===== 시스템 프롬프트 =====
    async def load_system_prompt(self) -> Optional[str]:
        """시스템 프롬프트 로드 (conversation_memories에서)"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                result = await conn.execute(text("""
                    SELECT value FROM conversation_memories
                    WHERE memory_id = 'system_prompt' AND user_id = 'system'
                """))
                row = result.first()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to load system prompt from DB: {e}")
            return None

    async def save_system_prompt(self, content: str) -> bool:
        """시스템 프롬프트 저장"""
        try:
            db = self._get_db()
            async with db.session_scope() as conn:
                await conn.execute(text("""
                    INSERT INTO conversation_memories
                        (memory_id, user_id, category, key, value, importance, created_at)
                    VALUES
                        ('system_prompt', 'system', 'system', 'system_prompt', :content, 10, NOW())
                    ON CONFLICT (memory_id) DO UPDATE SET
                        value = EXCLUDED.value
                """), {"content": content})
            return True
        except Exception as e:
            logger.error(f"Failed to save system prompt to DB: {e}")
            return False


# ===== 파일 기반 저장소 (Legacy fallback) =====
class FileBasedStorage:
    """파일 기반 영구 저장소 (DB 불가 시 fallback)"""

    def __init__(self, base_path: Optional[Path] = None):
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent / "data" / "ai_memory"

        self.base_path = Path(base_path)
        self.sessions_path = self.base_path / "sessions"
        self.memories_path = self.base_path / "memories"
        self.summaries_path = self.base_path / "summaries"
        self.system_prompt_path = self.base_path / "system_prompt.md"

        self.sessions_path.mkdir(parents=True, exist_ok=True)
        self.memories_path.mkdir(parents=True, exist_ok=True)
        self.summaries_path.mkdir(parents=True, exist_ok=True)

    def _session_file(self, session_id: str) -> Path:
        return self.sessions_path / f"{session_id}.json"

    def _memory_file(self, user_id: str) -> Path:
        return self.memories_path / f"{user_id}_memories.json"

    def _summary_file(self, session_id: str) -> Path:
        return self.summaries_path / f"{session_id}.md"

    @property
    def latest_summary_path(self) -> Path:
        return self.summaries_path / "latest_summary.md"

    # All methods are async for interface compatibility with DatabaseStorage
    async def save_session(self, session: ConversationSession) -> bool:
        try:
            session.updated_at = datetime.utcnow()
            file_path = self._session_file(session.session_id)
            data = json.loads(session.model_dump_json())
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False

    async def load_session(self, session_id: str) -> Optional[ConversationSession]:
        try:
            file_path = self._session_file(session_id)
            if not file_path.exists():
                return None
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ConversationSession(**data)
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    async def list_sessions(self, user_id: str = "default", limit: int = 20) -> list[ConversationSession]:
        sessions = []
        try:
            for file_path in self.sessions_path.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    session = ConversationSession(**data)
                    if session.user_id == user_id:
                        sessions.append(session)
                except Exception:
                    continue
            sessions.sort(key=lambda x: x.updated_at, reverse=True)
            return sessions[:limit]
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    async def delete_session(self, session_id: str) -> bool:
        try:
            file_path = self._session_file(session_id)
            if file_path.exists():
                file_path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    async def save_summary_md(self, session_id: str, md_content: str) -> bool:
        try:
            self._summary_file(session_id).write_text(md_content, encoding="utf-8")
            self.latest_summary_path.write_text(md_content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to save summary MD: {e}")
            return False

    async def load_summary_md(self, session_id: str) -> Optional[str]:
        try:
            f = self._summary_file(session_id)
            return f.read_text(encoding="utf-8") if f.exists() else None
        except Exception as e:
            logger.error(f"Failed to load summary MD: {e}")
            return None

    async def load_latest_summary(self) -> Optional[str]:
        try:
            return self.latest_summary_path.read_text(encoding="utf-8") if self.latest_summary_path.exists() else None
        except Exception as e:
            logger.error(f"Failed to load latest summary: {e}")
            return None

    async def save_memory(self, memory: MemoryEntry) -> bool:
        try:
            file_path = self._memory_file(memory.user_id)
            memories = {}
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    memories = json.load(f)
            memories[memory.memory_id] = json.loads(memory.model_dump_json())
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            return False

    async def load_memories(self, user_id: str = "default", category: Optional[str] = None) -> list[MemoryEntry]:
        try:
            file_path = self._memory_file(user_id)
            if not file_path.exists():
                return []
            with open(file_path, "r", encoding="utf-8") as f:
                memories_data = json.load(f)
            memories = []
            for data in memories_data.values():
                memory = MemoryEntry(**data)
                if category is None or memory.category == category:
                    if memory.expires_at is None or memory.expires_at > datetime.utcnow():
                        memories.append(memory)
            memories.sort(key=lambda x: x.importance, reverse=True)
            return memories
        except Exception as e:
            logger.error(f"Failed to load memories: {e}")
            return []

    async def delete_memory(self, memory_id: str, user_id: str = "default") -> bool:
        try:
            file_path = self._memory_file(user_id)
            if not file_path.exists():
                return False
            with open(file_path, "r", encoding="utf-8") as f:
                memories = json.load(f)
            if memory_id in memories:
                del memories[memory_id]
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(memories, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False

    async def load_system_prompt(self) -> Optional[str]:
        try:
            return self.system_prompt_path.read_text(encoding="utf-8") if self.system_prompt_path.exists() else None
        except Exception as e:
            logger.error(f"Failed to load system prompt: {e}")
            return None

    async def save_system_prompt(self, content: str) -> bool:
        try:
            self.system_prompt_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to save system prompt: {e}")
            return False


# ===== 요약 생성기 (규칙 기반) =====
class SummaryGenerator:
    """대화 세션에서 요약을 규칙 기반으로 생성"""

    TOPIC_KEYWORDS: dict[str, list[str]] = {
        "견적 요청": ["견적", "분전반", "차단기", "외함", "브레이커", "quote", "estimate"],
        "도면 분석": ["도면", "단선", "결선도", "배치도", "외형도", "drawing"],
        "ERP 작업": ["erp", "발주", "재고", "주문", "order", "inventory"],
        "이메일 발송": ["이메일", "메일", "발송", "전송"],
        "일정 관리": ["일정", "캘린더", "스케줄", "납품", "미팅"],
        "가격 조회": ["가격", "단가", "비용", "원", "견적가"],
        "차단기 정보": ["차단기", "MCCB", "ELB", "누전", "배선용", "상도", "LS"],
        "외함 정보": ["외함", "옥내", "옥외", "자립", "노출", "매입함", "STEEL", "SUS"],
        "부속자재": ["마그네트", "타이머", "SPD", "계량기", "부속자재"],
        "도면 업로드": ["업로드", "첨부", "이미지", "파일"],
        "일반 대화": ["안녕", "고마워", "감사", "도움"],
    }

    DECISION_PATTERNS: list[str] = [
        r"확정|결정|선택|채택|적용",
        r"으로\s*(하겠|진행|결정)",
        r"(상도|LS)\s*(차단기|경제형|표준형)",
        r"\d+P\s*\d+A",
        r"옥내노출|옥외노출|옥내자립|옥외자립|매입함",
        r"STEEL|SUS",
    ]

    PENDING_PATTERNS: list[str] = [
        r"나중에|추후|다음에|이따가",
        r"확인\s*(해|필요|해야|해볼|해봐)",
        r"검토\s*(해|필요|해야)",
        r"수정\s*(해|필요|해야)",
        r"보내|전송|발송.*(?:예정|할)",
    ]

    PREFERENCE_PATTERNS: list[str] = [
        r"(항상|기본|보통|늘)\s+(.{2,20})\s*(으로|사용|적용)",
        r"(선호|좋아|원하|원해)",
        r"경제형|표준형",
        r"상도|LS",
    ]

    @classmethod
    def generate_summary(cls, session: ConversationSession) -> str:
        if not session.messages:
            return cls._build_empty_summary(session)

        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M")

        user_messages: list[str] = []
        assistant_messages: list[str] = []
        all_content: list[str] = []

        for msg in session.messages:
            if msg.role == "user":
                user_messages.append(msg.content)
            elif msg.role == "assistant":
                assistant_messages.append(msg.content)
            all_content.append(msg.content)

        combined_text = " ".join(all_content)

        topics = cls._extract_topics(combined_text)
        decisions = cls._extract_decisions(user_messages, assistant_messages)
        pending_tasks = cls._extract_pending_tasks(combined_text)
        preferences = cls._extract_preferences(user_messages)
        key_data = cls._extract_key_data(combined_text)

        md_parts: list[str] = []
        md_parts.append(f"# 대화 요약 - {timestamp_str}")
        md_parts.append(f"## 세션 ID: {session.session_id}")
        md_parts.append(f"## 세션 제목: {session.title or '제목 없음'}")
        md_parts.append(f"## 메시지 수: {len(session.messages)}개")
        md_parts.append("")

        md_parts.append("## 주요 주제")
        if topics:
            for topic in topics:
                md_parts.append(f"- {topic}")
        else:
            md_parts.append("- (감지된 주제 없음)")
        md_parts.append("")

        md_parts.append("## 결정 사항")
        if decisions:
            for decision in decisions:
                md_parts.append(f"- {decision}")
        else:
            md_parts.append("- (결정 사항 없음)")
        md_parts.append("")

        md_parts.append("## 미완료 작업")
        if pending_tasks:
            for task in pending_tasks:
                md_parts.append(f"- [ ] {task}")
        else:
            md_parts.append("- (미완료 작업 없음)")
        md_parts.append("")

        md_parts.append("## 대표님 선호사항")
        if preferences:
            for pref in preferences:
                md_parts.append(f"- {pref}")
        else:
            md_parts.append("- (감지된 선호사항 없음)")
        md_parts.append("")

        md_parts.append("## 핵심 데이터")
        if key_data.get("estimate_ids"):
            md_parts.append(f"- 견적 ID: {', '.join(key_data['estimate_ids'])}")
        else:
            md_parts.append("- 견적 ID: 없음")
        if key_data.get("customer_names"):
            md_parts.append(f"- 고객명: {', '.join(key_data['customer_names'])}")
        else:
            md_parts.append("- 고객명: 없음")
        if key_data.get("breaker_specs"):
            md_parts.append(f"- 차단기 스펙: {', '.join(key_data['breaker_specs'][:5])}")
        md_parts.append("")

        md_parts.append("## 최근 대화 요약")
        recent_pairs = cls._get_recent_pairs(session.messages, max_pairs=3)
        if recent_pairs:
            for user_msg, ai_msg in recent_pairs:
                truncated_user = user_msg[:100] + ("..." if len(user_msg) > 100 else "")
                truncated_ai = ai_msg[:150] + ("..." if len(ai_msg) > 150 else "")
                md_parts.append(f"- **대표님**: {truncated_user}")
                md_parts.append(f"- **나베랄**: {truncated_ai}")
                md_parts.append("")
        else:
            md_parts.append("- (대화 내용 없음)")
        md_parts.append("")

        md_parts.append("---")
        md_parts.append(f"*자동 생성: {now.strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(md_parts)

    @classmethod
    def _build_empty_summary(cls, session: ConversationSession) -> str:
        now = datetime.now()
        return f"""# 대화 요약 - {now.strftime('%Y-%m-%d %H:%M')}
## 세션 ID: {session.session_id}

## 주요 주제
- (대화 없음)

## 결정 사항
- (결정 사항 없음)

## 미완료 작업
- (미완료 작업 없음)

## 대표님 선호사항
- (감지된 선호사항 없음)

## 핵심 데이터
- 견적 ID: 없음
- 고객명: 없음

---
*자동 생성: {now.strftime('%Y-%m-%d %H:%M:%S')}*"""

    @classmethod
    def _extract_topics(cls, combined_text: str) -> list[str]:
        topics: list[str] = []
        text_lower = combined_text.lower()
        for topic_name, keywords in cls.TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    if topic_name not in topics:
                        topics.append(topic_name)
                    break
        return topics

    @classmethod
    def _extract_decisions(cls, user_msgs: list[str], ai_msgs: list[str]) -> list[str]:
        decisions: list[str] = []
        all_msgs = user_msgs + ai_msgs
        for msg in all_msgs:
            for pattern in cls.DECISION_PATTERNS:
                matches = re.findall(pattern, msg)
                if matches:
                    sentences = re.split(r'[.!?\n]', msg)
                    for sentence in sentences:
                        if re.search(pattern, sentence) and len(sentence.strip()) > 5:
                            trimmed = sentence.strip()[:120]
                            if trimmed and trimmed not in decisions:
                                decisions.append(trimmed)
                                break
                    break
        return decisions[:10]

    @classmethod
    def _extract_pending_tasks(cls, combined_text: str) -> list[str]:
        pending: list[str] = []
        sentences = re.split(r'[.!?\n]', combined_text)
        for sentence in sentences:
            for pattern in cls.PENDING_PATTERNS:
                if re.search(pattern, sentence) and len(sentence.strip()) > 5:
                    trimmed = sentence.strip()[:120]
                    if trimmed and trimmed not in pending:
                        pending.append(trimmed)
                    break
        return pending[:10]

    @classmethod
    def _extract_preferences(cls, user_msgs: list[str]) -> list[str]:
        preferences: list[str] = []
        for msg in user_msgs:
            for pattern in cls.PREFERENCE_PATTERNS:
                if re.search(pattern, msg):
                    sentences = re.split(r'[.!?\n]', msg)
                    for sentence in sentences:
                        if re.search(pattern, sentence) and len(sentence.strip()) > 3:
                            trimmed = sentence.strip()[:120]
                            if trimmed and trimmed not in preferences:
                                preferences.append(trimmed)
                            break
                    break
        return preferences[:10]

    @classmethod
    def _extract_key_data(cls, combined_text: str) -> dict[str, list[str]]:
        data: dict[str, list[str]] = {
            "estimate_ids": [],
            "customer_names": [],
            "breaker_specs": [],
        }
        est_matches = re.findall(r'EST-\d{8,14}', combined_text, re.IGNORECASE)
        data["estimate_ids"] = list(set(est_matches))[:5]
        customer_matches = re.findall(r'([가-힣]{2,10}(?:전력|전기|건설|산업|상사|엔지니어링))', combined_text)
        data["customer_names"] = list(set(customer_matches))[:5]
        spec_matches = re.findall(r'\d[Pp]\s*\d+[Aa]', combined_text)
        data["breaker_specs"] = list(set(spec_matches))[:10]
        return data

    @classmethod
    def _get_recent_pairs(
        cls, messages: list[ConversationMessage], max_pairs: int = 3
    ) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        i = len(messages) - 1
        while i >= 1 and len(pairs) < max_pairs:
            if messages[i].role == "assistant" and messages[i - 1].role == "user":
                pairs.insert(0, (messages[i - 1].content, messages[i].content))
                i -= 2
            else:
                i -= 1
        return pairs


# ===== 메인 서비스 (async) =====
class ConversationMemoryService:
    """대화 영구 메모리 서비스 (SSOT) - async"""

    SUMMARY_TRIGGER_INTERVAL: int = 10

    def __init__(self, storage=None):
        self.storage = storage or DatabaseStorage()
        self._current_session: Optional[ConversationSession] = None
        self._message_count_since_summary: int = 0

    # ===== 세션 관리 =====
    async def create_session(self, user_id: str = "default", title: Optional[str] = None) -> ConversationSession:
        session_id = self._generate_session_id()
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            title=title or f"대화 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await self.storage.save_session(session)
        self._current_session = session
        self._message_count_since_summary = 0
        logger.info(f"New session created: {session_id}")
        return session

    async def get_or_create_session(self, session_id: Optional[str] = None, user_id: str = "default") -> ConversationSession:
        if session_id:
            session = await self.storage.load_session(session_id)
            if session:
                self._current_session = session
                self._message_count_since_summary = len(session.messages) % self.SUMMARY_TRIGGER_INTERVAL
                return session

        sessions = await self.storage.list_sessions(user_id, limit=1)
        if sessions and sessions[0].is_active:
            if datetime.utcnow() - sessions[0].updated_at < timedelta(hours=24):
                self._current_session = sessions[0]
                self._message_count_since_summary = len(sessions[0].messages) % self.SUMMARY_TRIGGER_INTERVAL
                return sessions[0]

        return await self.create_session(user_id)

    async def get_active_session(self, user_id: str = "default") -> Optional[ConversationSession]:
        sessions = await self.storage.list_sessions(user_id, limit=1)
        if sessions and sessions[0].is_active:
            if datetime.utcnow() - sessions[0].updated_at < timedelta(hours=24):
                return sessions[0]
        return None

    async def add_message(
        self,
        role: str,
        content: str,
        session_id: Optional[str] = None,
        intent: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> ConversationMessage:
        session = self._current_session
        if session_id:
            session = await self.storage.load_session(session_id)

        if not session:
            session = await self.create_session()

        message = ConversationMessage(
            role=role,
            content=content,
            intent=intent,
            metadata=metadata or {}
        )

        session.messages.append(message)

        if len(session.messages) == 1 and role == "user":
            session.title = self._generate_title(content)

        await self.storage.save_session(session)
        self._current_session = session

        self._message_count_since_summary += 1
        if self._message_count_since_summary >= self.SUMMARY_TRIGGER_INTERVAL:
            await self._auto_generate_summary(session)
            self._message_count_since_summary = 0

        return message

    async def get_recent_messages(self, session_id: Optional[str] = None, limit: int = 10) -> list[ConversationMessage]:
        session = self._current_session
        if session_id:
            session = await self.storage.load_session(session_id)
        if not session:
            return []
        return session.messages[-limit:]

    async def get_conversation_context(self, session_id: Optional[str] = None, max_tokens: int = 4000) -> str:
        messages = await self.get_recent_messages(session_id, limit=20)

        context_parts: list[str] = []
        total_chars = 0
        max_chars = max_tokens * 4

        for msg in reversed(messages):
            line = f"[{msg.role}]: {msg.content}"
            if total_chars + len(line) > max_chars:
                break
            context_parts.insert(0, line)
            total_chars += len(line)

        return "\n".join(context_parts)

    async def list_sessions(self, user_id: str = "default", limit: int = 20) -> list[dict]:
        sessions = await self.storage.list_sessions(user_id, limit)
        result: list[dict] = []
        for s in sessions:
            result.append({
                "session_id": s.session_id,
                "title": s.title,
                "message_count": len(s.messages),
                "updated_at": s.updated_at.isoformat(),
                "is_active": s.is_active,
                "summary": s.summary,
            })
        return result

    async def close_session(self, session_id: str) -> bool:
        session = await self.storage.load_session(session_id)
        if session:
            session.is_active = False
            await self.generate_summary(session_id)
            return await self.storage.save_session(session)
        return False

    async def delete_session(self, session_id: str) -> bool:
        if self._current_session and self._current_session.session_id == session_id:
            self._current_session = None
        return await self.storage.delete_session(session_id)

    # ===== 요약 생성 =====
    async def generate_summary(self, session_id: str) -> Optional[str]:
        session = await self.storage.load_session(session_id)
        if not session:
            return None

        try:
            md_content = SummaryGenerator.generate_summary(session)
            session.summary = md_content
            await self.storage.save_session(session)
            await self.storage.save_summary_md(session_id, md_content)
            logger.info(f"Summary generated for session {session_id}")
            return md_content
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None

    async def get_summary(self, session_id: str) -> Optional[str]:
        md_content = await self.storage.load_summary_md(session_id)
        if md_content:
            return md_content
        session = await self.storage.load_session(session_id)
        if session and session.summary:
            return session.summary
        return None

    async def get_latest_summary(self) -> Optional[str]:
        return await self.storage.load_latest_summary()

    async def _auto_generate_summary(self, session: ConversationSession) -> None:
        try:
            await self.generate_summary(session.session_id)
        except Exception as e:
            logger.error(f"Auto-summary generation failed: {e}")

    # ===== 메모리 관리 =====
    async def remember(
        self,
        key: str,
        value: str,
        category: str = "knowledge",
        importance: int = 5,
        expires_in_days: Optional[int] = None,
        user_id: str = "default"
    ) -> MemoryEntry:
        memory_id = hashlib.md5(f"{user_id}:{category}:{key}".encode()).hexdigest()[:16]
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        memory = MemoryEntry(
            memory_id=memory_id,
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            source_session_id=self._current_session.session_id if self._current_session else None,
            importance=importance,
            expires_at=expires_at
        )
        await self.storage.save_memory(memory)
        return memory

    async def recall(self, category: Optional[str] = None, user_id: str = "default") -> list[MemoryEntry]:
        return await self.storage.load_memories(user_id, category)

    async def recall_by_key(self, key: str, user_id: str = "default") -> Optional[MemoryEntry]:
        memories = await self.storage.load_memories(user_id)
        for memory in memories:
            if memory.key == key:
                return memory
        return None

    async def forget(self, memory_id: str, user_id: str = "default") -> bool:
        return await self.storage.delete_memory(memory_id, user_id)

    async def get_memory_context(self, user_id: str = "default", max_items: int = 20) -> str:
        memories = (await self.recall(user_id=user_id))[:max_items]
        if not memories:
            return ""
        context_parts = ["[저장된 메모리]"]
        for memory in memories:
            context_parts.append(f"- [{memory.category}] {memory.key}: {memory.value}")
        return "\n".join(context_parts)

    # ===== 시스템 프롬프트 =====
    async def get_system_prompt(self) -> Optional[str]:
        return await self.storage.load_system_prompt()

    async def set_system_prompt(self, content: str) -> bool:
        return await self.storage.save_system_prompt(content)

    # ===== AIKnowledgeService 호환 레이어 =====
    async def save_conversation_pair(self, user_message: str, ai_response: str, user_id: str = "default") -> bool:
        try:
            session = await self.get_or_create_session(user_id=user_id)
            await self.add_message(role="user", content=user_message, session_id=session.session_id)
            await self.add_message(role="assistant", content=ai_response, session_id=session.session_id)
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation pair: {e}")
            return False

    async def load_conversation_history(self, user_id: str = "default", limit: int = 50) -> list[dict]:
        session = await self.get_or_create_session(user_id=user_id)
        messages = session.messages[-limit:]
        return [{"role": m.role, "content": m.content} for m in messages]

    async def get_full_context_for_ai(self, user_id: str = "default", session_id: Optional[str] = None) -> dict:
        previous_summary = await self.get_latest_summary()
        return {
            "system_prompt": await self.get_system_prompt(),
            "memories": await self.get_memory_context(user_id),
            "conversation": await self.get_conversation_context(session_id),
            "previous_summary": previous_summary,
            "session_id": self._current_session.session_id if self._current_session else None
        }

    # ===== 유틸리티 =====
    def _generate_session_id(self) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = hashlib.md5(str(datetime.utcnow().timestamp()).encode()).hexdigest()[:8]
        return f"sess_{timestamp}_{random_part}"

    def _generate_title(self, first_message: str) -> str:
        title = first_message[:50]
        if "\n" in title:
            title = title.split("\n")[0]
        if len(title) < len(first_message):
            title += "..."
        return title


# ===== 싱글톤 인스턴스 =====
_memory_service: Optional[ConversationMemoryService] = None


def get_memory_service() -> ConversationMemoryService:
    """메모리 서비스 싱글톤 반환 (DB 우선, 파일 fallback)"""
    global _memory_service
    if _memory_service is None:
        try:
            storage = DatabaseStorage()
            _memory_service = ConversationMemoryService(storage)
            logger.info("ConversationMemoryService initialized with DatabaseStorage")
        except Exception as e:
            logger.warning(f"DB storage init failed, using file fallback: {e}")
            _memory_service = ConversationMemoryService(FileBasedStorage())
    return _memory_service
