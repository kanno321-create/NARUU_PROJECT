"""
KIS Estimator API - Calendar (일정 관리)

일정 관리 API:
- 일정 생성/조회/수정/삭제
- 납품일정, 미팅, 작업 등 관리
- per-user 일정 + 공유 기능
- PostgreSQL 기반 영구 저장소
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text

from kis_estimator_core.infra.db import get_db_instance

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar", tags=["calendar"])


# ==================== Table Initialization ====================

_tables_initialized = False


async def _ensure_tables() -> None:
    """Idempotent table creation on first use."""
    global _tables_initialized
    if _tables_initialized:
        return

    db = get_db_instance()
    async with db.session_scope() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id VARCHAR(100) NOT NULL DEFAULT 'default',
                title VARCHAR(500) NOT NULL,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ NOT NULL,
                description TEXT,
                location VARCHAR(500),
                event_type VARCHAR(50) NOT NULL DEFAULT 'task',
                priority VARCHAR(20) DEFAULT 'normal',
                color VARCHAR(20),
                all_day BOOLEAN DEFAULT false,
                is_shared BOOLEAN DEFAULT false,
                completed BOOLEAN DEFAULT false,
                reminder VARCHAR(50),
                customer VARCHAR(200),
                estimate_id VARCHAR(100),
                created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc'),
                updated_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc')
            )
        """))
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS calendar_shared_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_id UUID NOT NULL REFERENCES calendar_events(id) ON DELETE CASCADE,
                shared_with_user_id VARCHAR(100) NOT NULL,
                permission VARCHAR(20) NOT NULL DEFAULT 'view',
                shared_by_user_id VARCHAR(100) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT (now() AT TIME ZONE 'utc'),
                UNIQUE(event_id, shared_with_user_id)
            )
        """))

    _tables_initialized = True
    logger.info("calendar_events / calendar_shared_events tables ensured")


# ==================== Models ====================

class CalendarEventCreate(BaseModel):
    """일정 생성 요청"""
    title: str = Field(..., min_length=1, description="일정 제목")
    start: str = Field(..., description="시작 시간 (ISO 8601)")
    end: Optional[str] = Field(None, description="종료 시간 (ISO 8601)")
    description: Optional[str] = Field(None, description="일정 설명")
    type: str = Field("task", description="일정 유형: meeting, task, delivery, reminder, other")
    location: Optional[str] = Field(None, description="장소")
    customer: Optional[str] = Field(None, description="관련 거래처")
    estimate_id: Optional[str] = Field(None, description="관련 견적 ID")
    color: Optional[str] = Field(None, description="캘린더 색상")
    reminders: list[dict] = Field(default_factory=list, description="알림 설정")
    all_day: bool = Field(False, description="종일 일정 여부")
    recurring: Optional[dict] = Field(None, description="반복 설정")
    priority: Optional[str] = Field("normal", description="우선순위: high, normal, low")


class CalendarEventUpdate(BaseModel):
    """일정 수정 요청"""
    title: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    customer: Optional[str] = None
    estimate_id: Optional[str] = None
    color: Optional[str] = None
    reminders: Optional[list[dict]] = None
    all_day: Optional[bool] = None
    recurring: Optional[dict] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None


class CalendarEvent(BaseModel):
    """일정 응답"""
    id: str
    title: str
    start: str
    end: Optional[str] = None
    description: Optional[str] = None
    type: str = "task"
    location: Optional[str] = None
    customer: Optional[str] = None
    estimate_id: Optional[str] = None
    color: Optional[str] = None
    reminders: list[dict] = Field(default_factory=list)
    all_day: bool = False
    recurring: Optional[dict] = None
    completed: bool = False
    created_at: str = ""
    updated_at: str = ""
    priority: Optional[str] = "normal"
    user_id: str = "default"
    is_shared: bool = False


class CalendarStats(BaseModel):
    """캘린더 통계"""
    total_events: int
    upcoming_events: int
    overdue_tasks: int
    this_week: int
    this_month: int
    by_type: dict


class ShareEventRequest(BaseModel):
    """일정 공유 요청"""
    shared_with_user_id: str = Field(..., description="공유 대상 사용자 ID")
    permission: str = Field("view", description="권한: view, edit")


# ==================== Helper Functions ====================

def _row_to_event(row) -> CalendarEvent:
    """DB row mapping to CalendarEvent response model."""
    row_dict = row._mapping if hasattr(row, '_mapping') else dict(row)

    start_time = row_dict["start_time"]
    end_time = row_dict["end_time"]
    created_at = row_dict.get("created_at")
    updated_at = row_dict.get("updated_at")

    return CalendarEvent(
        id=str(row_dict["id"]),
        title=row_dict["title"],
        start=start_time.isoformat() if start_time else "",
        end=end_time.isoformat() if end_time else None,
        description=row_dict.get("description"),
        type=row_dict.get("event_type", "task"),
        location=row_dict.get("location"),
        customer=row_dict.get("customer"),
        estimate_id=row_dict.get("estimate_id"),
        color=row_dict.get("color"),
        all_day=row_dict.get("all_day", False),
        completed=row_dict.get("completed", False),
        created_at=created_at.isoformat() if created_at else "",
        updated_at=updated_at.isoformat() if updated_at else "",
        priority=row_dict.get("priority", "normal"),
        user_id=row_dict.get("user_id", "default"),
        is_shared=row_dict.get("is_shared", False),
    )


def get_type_color(event_type: str) -> str:
    """일정 유형별 기본 색상"""
    colors = {
        "meeting": "#3b82f6",
        "task": "#10b981",
        "delivery": "#f59e0b",
        "reminder": "#8b5cf6",
        "deadline": "#ef4444",
        "other": "#6b7280",
    }
    return colors.get(event_type, "#6b7280")


def _parse_datetime_safe(dt_str: str) -> datetime:
    """Parse ISO 8601 datetime string to timezone-aware datetime (UTC)."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(dt_str, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Invalid datetime format: {dt_str}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ==================== API Endpoints ====================

@router.post("/events", response_model=CalendarEvent, status_code=201, summary="일정 생성")
async def create_event(
    request: CalendarEventCreate,
    user_id: str = Query("default", description="사용자 ID"),
) -> CalendarEvent:
    """
    새 일정을 생성합니다.

    일정 유형:
    - meeting: 미팅/회의
    - task: 작업/할일
    - delivery: 납품 일정
    - deadline: 마감
    - reminder: 알림
    - other: 기타
    """
    await _ensure_tables()

    start_dt = _parse_datetime_safe(request.start)
    end_dt = _parse_datetime_safe(request.end) if request.end else start_dt
    event_id = str(uuid4())
    now_utc = datetime.now(timezone.utc)
    color = request.color or get_type_color(request.type)

    db = get_db_instance()
    async with db.session_scope() as session:
        await session.execute(
            text("""
                INSERT INTO calendar_events
                    (id, user_id, title, start_time, end_time, description, location,
                     event_type, priority, color, all_day, completed, customer,
                     estimate_id, created_at, updated_at)
                VALUES
                    (:id, :user_id, :title, :start_time, :end_time, :description,
                     :location, :event_type, :priority, :color, :all_day, false,
                     :customer, :estimate_id, :created_at, :updated_at)
            """),
            {
                "id": event_id,
                "user_id": user_id,
                "title": request.title,
                "start_time": start_dt,
                "end_time": end_dt,
                "description": request.description,
                "location": request.location,
                "event_type": request.type,
                "priority": request.priority or "normal",
                "color": color,
                "all_day": request.all_day,
                "customer": request.customer,
                "estimate_id": request.estimate_id,
                "created_at": now_utc,
                "updated_at": now_utc,
            },
        )

    logger.info(f"일정 생성: {event_id} - {request.title} (user={user_id})")

    return CalendarEvent(
        id=event_id,
        title=request.title,
        start=start_dt.isoformat(),
        end=end_dt.isoformat(),
        description=request.description,
        type=request.type,
        location=request.location,
        customer=request.customer,
        estimate_id=request.estimate_id,
        color=color,
        all_day=request.all_day,
        completed=False,
        created_at=now_utc.isoformat(),
        updated_at=now_utc.isoformat(),
        priority=request.priority or "normal",
        user_id=user_id,
        is_shared=False,
    )


@router.get("/events", response_model=list[CalendarEvent], summary="일정 목록 조회")
async def list_events(
    user_id: str = Query("default", description="사용자 ID"),
    start_date: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    type: Optional[str] = Query(None, description="일정 유형 필터"),
    customer: Optional[str] = Query(None, description="거래처 필터"),
    completed: Optional[bool] = Query(None, description="완료 여부"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[CalendarEvent]:
    """
    일정 목록을 조회합니다.
    사용자 본인 일정 + 공유받은 일정을 모두 반환합니다.
    """
    await _ensure_tables()

    # Build query: own events UNION shared events
    conditions_own = ["ce.user_id = :user_id"]
    params: dict = {"user_id": user_id, "limit": limit, "offset": offset}

    if start_date:
        conditions_own.append("ce.start_time >= :start_dt")
        params["start_dt"] = _parse_datetime_safe(start_date + "T00:00:00")
    if end_date:
        conditions_own.append("ce.start_time <= :end_dt")
        params["end_dt"] = _parse_datetime_safe(end_date + "T23:59:59")
    if type:
        conditions_own.append("ce.event_type = :event_type")
        params["event_type"] = type
    if customer:
        conditions_own.append("LOWER(ce.customer) LIKE :customer")
        params["customer"] = f"%{customer.lower()}%"
    if completed is not None:
        conditions_own.append("ce.completed = :completed")
        params["completed"] = completed

    where_own = " AND ".join(conditions_own)

    # Shared events use the same date/type/customer/completed filters
    conditions_shared = ["cse.shared_with_user_id = :user_id"]
    if start_date:
        conditions_shared.append("ce.start_time >= :start_dt")
    if end_date:
        conditions_shared.append("ce.start_time <= :end_dt")
    if type:
        conditions_shared.append("ce.event_type = :event_type")
    if customer:
        conditions_shared.append("LOWER(ce.customer) LIKE :customer")
    if completed is not None:
        conditions_shared.append("ce.completed = :completed")

    where_shared = " AND ".join(conditions_shared)

    sql = f"""
        SELECT ce.*, false AS is_shared_view FROM calendar_events ce
        WHERE {where_own}
        UNION ALL
        SELECT ce.*, true AS is_shared_view FROM calendar_events ce
        INNER JOIN calendar_shared_events cse ON cse.event_id = ce.id
        WHERE {where_shared}
        ORDER BY start_time ASC
        LIMIT :limit OFFSET :offset
    """

    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(text(sql), params)
        rows = result.fetchall()

    events = []
    for row in rows:
        ev = _row_to_event(row)
        # Mark shared events
        row_dict = row._mapping if hasattr(row, '_mapping') else dict(row)
        if row_dict.get("is_shared_view"):
            ev.is_shared = True
        events.append(ev)

    return events


@router.get("/events/today", response_model=list[CalendarEvent], summary="오늘 일정 조회")
async def get_today_events(
    user_id: str = Query("default", description="사용자 ID"),
) -> list[CalendarEvent]:
    """오늘의 모든 일정을 조회합니다."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return await list_events(user_id=user_id, start_date=today, end_date=today)


@router.get("/events/upcoming", response_model=list[CalendarEvent], summary="다가오는 일정 조회")
async def get_upcoming_events(
    user_id: str = Query("default", description="사용자 ID"),
    days: int = Query(7, ge=1, le=90),
) -> list[CalendarEvent]:
    """다가오는 일정을 조회합니다."""
    today = datetime.now(timezone.utc)
    end_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
    return await list_events(
        user_id=user_id,
        start_date=today.strftime("%Y-%m-%d"),
        end_date=end_date,
        completed=False,
    )


@router.get("/events/{event_id}", response_model=CalendarEvent, summary="일정 상세 조회")
async def get_event(
    event_id: str,
    user_id: str = Query("default", description="사용자 ID"),
) -> CalendarEvent:
    """특정 일정의 상세 정보를 조회합니다."""
    await _ensure_tables()

    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(
            text("""
                SELECT ce.* FROM calendar_events ce
                WHERE ce.id = :event_id
                  AND (ce.user_id = :user_id
                       OR EXISTS (
                           SELECT 1 FROM calendar_shared_events cse
                           WHERE cse.event_id = ce.id
                             AND cse.shared_with_user_id = :user_id
                       ))
            """),
            {"event_id": event_id, "user_id": user_id},
        )
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"일정을 찾을 수 없습니다: {event_id}")

    return _row_to_event(row)


@router.put("/events/{event_id}", response_model=CalendarEvent, summary="일정 수정")
async def update_event(
    event_id: str,
    request: CalendarEventUpdate,
    user_id: str = Query("default", description="사용자 ID"),
) -> CalendarEvent:
    """일정을 수정합니다."""
    await _ensure_tables()

    update_fields = []
    params: dict = {
        "event_id": event_id,
        "user_id": user_id,
        "updated_at": datetime.now(timezone.utc),
    }

    update_data = request.model_dump(exclude_unset=True)

    field_mapping = {
        "title": "title",
        "start": "start_time",
        "end": "end_time",
        "description": "description",
        "type": "event_type",
        "location": "location",
        "customer": "customer",
        "estimate_id": "estimate_id",
        "color": "color",
        "all_day": "all_day",
        "completed": "completed",
        "priority": "priority",
    }

    for req_field, db_field in field_mapping.items():
        if req_field in update_data:
            value = update_data[req_field]
            if req_field in ("start", "end") and value is not None:
                value = _parse_datetime_safe(value)
            update_fields.append(f"{db_field} = :{db_field}")
            params[db_field] = value

    if not update_fields:
        raise HTTPException(status_code=400, detail="수정할 필드가 없습니다")

    update_fields.append("updated_at = :updated_at")
    set_clause = ", ".join(update_fields)

    db = get_db_instance()
    async with db.session_scope() as session:
        # Check ownership or edit permission
        perm_result = await session.execute(
            text("""
                SELECT ce.user_id FROM calendar_events ce
                WHERE ce.id = :event_id
                  AND (ce.user_id = :user_id
                       OR EXISTS (
                           SELECT 1 FROM calendar_shared_events cse
                           WHERE cse.event_id = ce.id
                             AND cse.shared_with_user_id = :user_id
                             AND cse.permission = 'edit'
                       ))
            """),
            {"event_id": event_id, "user_id": user_id},
        )
        if not perm_result.fetchone():
            raise HTTPException(status_code=404, detail=f"일정을 찾을 수 없거나 수정 권한이 없습니다: {event_id}")

        await session.execute(
            text(f"UPDATE calendar_events SET {set_clause} WHERE id = :event_id"),
            params,
        )

        # Fetch updated row
        result = await session.execute(
            text("SELECT * FROM calendar_events WHERE id = :event_id"),
            {"event_id": event_id},
        )
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"일정을 찾을 수 없습니다: {event_id}")

    logger.info(f"일정 수정: {event_id} (user={user_id})")
    return _row_to_event(row)


@router.patch("/events/{event_id}/complete", response_model=CalendarEvent, summary="일정 완료 처리")
async def complete_event(
    event_id: str,
    user_id: str = Query("default", description="사용자 ID"),
) -> CalendarEvent:
    """일정을 완료 처리합니다."""
    return await update_event(event_id, CalendarEventUpdate(completed=True), user_id=user_id)


@router.delete("/events/{event_id}", summary="일정 삭제")
async def delete_event(
    event_id: str,
    user_id: str = Query("default", description="사용자 ID"),
) -> dict:
    """일정을 삭제합니다. 소유자만 삭제 가능합니다."""
    await _ensure_tables()

    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(
            text("""
                DELETE FROM calendar_events
                WHERE id = :event_id AND user_id = :user_id
                RETURNING id, title
            """),
            {"event_id": event_id, "user_id": user_id},
        )
        row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"일정을 찾을 수 없거나 삭제 권한이 없습니다: {event_id}")

    row_dict = row._mapping if hasattr(row, '_mapping') else dict(row)
    logger.info(f"일정 삭제: {event_id} (user={user_id})")
    return {
        "success": True,
        "deleted_id": str(row_dict["id"]),
        "deleted_title": row_dict.get("title"),
    }


# ==================== Sharing Endpoints ====================

@router.post("/events/{event_id}/share", summary="일정 공유")
async def share_event(
    event_id: str,
    request: ShareEventRequest,
    user_id: str = Query("default", description="공유하는 사용자 ID"),
) -> dict:
    """일정을 다른 사용자에게 공유합니다. 소유자만 공유 가능합니다."""
    await _ensure_tables()

    if request.permission not in ("view", "edit"):
        raise HTTPException(status_code=400, detail="permission은 'view' 또는 'edit'만 가능합니다")

    db = get_db_instance()
    async with db.session_scope() as session:
        # Verify ownership
        owner_check = await session.execute(
            text("SELECT id FROM calendar_events WHERE id = :event_id AND user_id = :user_id"),
            {"event_id": event_id, "user_id": user_id},
        )
        if not owner_check.fetchone():
            raise HTTPException(status_code=404, detail=f"일정을 찾을 수 없거나 공유 권한이 없습니다: {event_id}")

        # Cannot share with self
        if request.shared_with_user_id == user_id:
            raise HTTPException(status_code=400, detail="자기 자신에게는 공유할 수 없습니다")

        # Upsert share record
        share_id = str(uuid4())
        await session.execute(
            text("""
                INSERT INTO calendar_shared_events
                    (id, event_id, shared_with_user_id, permission, shared_by_user_id)
                VALUES
                    (:id, :event_id, :shared_with_user_id, :permission, :shared_by_user_id)
                ON CONFLICT (event_id, shared_with_user_id)
                DO UPDATE SET permission = :permission
            """),
            {
                "id": share_id,
                "event_id": event_id,
                "shared_with_user_id": request.shared_with_user_id,
                "permission": request.permission,
                "shared_by_user_id": user_id,
            },
        )

        # Mark event as shared
        await session.execute(
            text("UPDATE calendar_events SET is_shared = true WHERE id = :event_id"),
            {"event_id": event_id},
        )

    logger.info(f"일정 공유: {event_id} -> {request.shared_with_user_id} (permission={request.permission})")
    return {
        "success": True,
        "event_id": event_id,
        "shared_with": request.shared_with_user_id,
        "permission": request.permission,
    }


@router.delete("/events/{event_id}/share/{target_user_id}", summary="일정 공유 해제")
async def revoke_share(
    event_id: str,
    target_user_id: str,
    user_id: str = Query("default", description="공유를 해제하는 사용자 ID"),
) -> dict:
    """일정 공유를 해제합니다. 소유자만 해제 가능합니다."""
    await _ensure_tables()

    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(
            text("""
                DELETE FROM calendar_shared_events
                WHERE event_id = :event_id
                  AND shared_with_user_id = :target_user_id
                  AND shared_by_user_id = :user_id
                RETURNING id
            """),
            {
                "event_id": event_id,
                "target_user_id": target_user_id,
                "user_id": user_id,
            },
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"공유 기록을 찾을 수 없거나 해제 권한이 없습니다",
            )

        # Check if any shares remain; if not, unmark is_shared
        remaining = await session.execute(
            text("SELECT COUNT(*) FROM calendar_shared_events WHERE event_id = :event_id"),
            {"event_id": event_id},
        )
        count = remaining.scalar()
        if count == 0:
            await session.execute(
                text("UPDATE calendar_events SET is_shared = false WHERE id = :event_id"),
                {"event_id": event_id},
            )

    logger.info(f"일정 공유 해제: {event_id} x {target_user_id}")
    return {
        "success": True,
        "event_id": event_id,
        "revoked_user": target_user_id,
    }


@router.get("/shared", response_model=list[CalendarEvent], summary="공유받은 일정 조회")
async def get_shared_events(
    user_id: str = Query("default", description="사용자 ID"),
) -> list[CalendarEvent]:
    """나에게 공유된 일정만 조회합니다."""
    await _ensure_tables()

    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(
            text("""
                SELECT ce.* FROM calendar_events ce
                INNER JOIN calendar_shared_events cse ON cse.event_id = ce.id
                WHERE cse.shared_with_user_id = :user_id
                ORDER BY ce.start_time ASC
            """),
            {"user_id": user_id},
        )
        rows = result.fetchall()

    events = []
    for row in rows:
        ev = _row_to_event(row)
        ev.is_shared = True
        events.append(ev)

    return events


# ==================== Stats & Utility ====================

@router.get("/stats", response_model=CalendarStats, summary="캘린더 통계")
async def get_stats(
    user_id: str = Query("default", description="사용자 ID"),
) -> CalendarStats:
    """캘린더 통계를 조회합니다."""
    await _ensure_tables()

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    week_end = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    month_end = (now + timedelta(days=30)).strftime("%Y-%m-%d")

    db = get_db_instance()
    async with db.session_scope() as session:
        # Total
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM calendar_events WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        total = total_result.scalar() or 0

        # Upcoming (not completed, start >= today)
        upcoming_result = await session.execute(
            text("""
                SELECT COUNT(*) FROM calendar_events
                WHERE user_id = :user_id AND completed = false
                  AND start_time >= :today
            """),
            {"user_id": user_id, "today": _parse_datetime_safe(today + "T00:00:00")},
        )
        upcoming = upcoming_result.scalar() or 0

        # Overdue (not completed, start < today)
        overdue_result = await session.execute(
            text("""
                SELECT COUNT(*) FROM calendar_events
                WHERE user_id = :user_id AND completed = false
                  AND start_time < :today
            """),
            {"user_id": user_id, "today": _parse_datetime_safe(today + "T00:00:00")},
        )
        overdue = overdue_result.scalar() or 0

        # This week
        this_week_result = await session.execute(
            text("""
                SELECT COUNT(*) FROM calendar_events
                WHERE user_id = :user_id AND completed = false
                  AND start_time >= :today AND start_time <= :week_end
            """),
            {
                "user_id": user_id,
                "today": _parse_datetime_safe(today + "T00:00:00"),
                "week_end": _parse_datetime_safe(week_end + "T23:59:59"),
            },
        )
        this_week = this_week_result.scalar() or 0

        # This month
        this_month_result = await session.execute(
            text("""
                SELECT COUNT(*) FROM calendar_events
                WHERE user_id = :user_id AND completed = false
                  AND start_time >= :today AND start_time <= :month_end
            """),
            {
                "user_id": user_id,
                "today": _parse_datetime_safe(today + "T00:00:00"),
                "month_end": _parse_datetime_safe(month_end + "T23:59:59"),
            },
        )
        this_month = this_month_result.scalar() or 0

        # By type
        type_result = await session.execute(
            text("""
                SELECT event_type, COUNT(*) as cnt FROM calendar_events
                WHERE user_id = :user_id
                GROUP BY event_type
            """),
            {"user_id": user_id},
        )
        by_type = {}
        for row in type_result.fetchall():
            row_dict = row._mapping if hasattr(row, '_mapping') else dict(row)
            by_type[row_dict["event_type"]] = row_dict["cnt"]

    return CalendarStats(
        total_events=total,
        upcoming_events=upcoming,
        overdue_tasks=overdue,
        this_week=this_week,
        this_month=this_month,
        by_type=by_type,
    )


@router.post("/events/quick", response_model=CalendarEvent, summary="빠른 일정 생성")
async def quick_create_event(
    title: str = Query(..., description="일정 제목"),
    date: str = Query(..., description="날짜 (YYYY-MM-DD)"),
    time: Optional[str] = Query(None, description="시간 (HH:MM)"),
    type: str = Query("task", description="일정 유형"),
    user_id: str = Query("default", description="사용자 ID"),
) -> CalendarEvent:
    """
    빠른 일정 생성 (간단한 파라미터로)

    예: /calendar/events/quick?title=납품&date=2024-12-15&type=delivery
    """
    start = f"{date}T{time}:00" if time else f"{date}T09:00:00"

    return await create_event(
        CalendarEventCreate(title=title, start=start, type=type),
        user_id=user_id,
    )


@router.get("/health", summary="캘린더 서비스 헬스체크")
async def health_check() -> dict:
    """캘린더 서비스 상태 확인"""
    await _ensure_tables()

    db = get_db_instance()
    async with db.session_scope() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM calendar_events"))
        count = result.scalar() or 0

    return {
        "status": "healthy",
        "storage": "postgresql",
        "total_events": count,
    }
