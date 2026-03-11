"""
AI Assistant Service (Phase XVI)

AI 업무 비서 서비스 - 할 일 관리, 알림, 일정, 자연어 명령 처리
Contract-First + Evidence-Gated 원칙 준수

핵심 기능:
1. 할 일 (Task) 관리
2. 알림 (Notification) 생성 및 관리
3. 일정 (Schedule) 관리
4. 자연어 명령 파싱 및 실행
5. 업무량 분석 및 우선순위 제안
6. 일일 요약 생성
"""

import json
import logging
import uuid
import re
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field, asdict
import random

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Task:
    """할 일 데이터"""
    task_id: str
    title: str
    description: Optional[str] = None
    priority: str = "MEDIUM"  # URGENT, HIGH, MEDIUM, LOW
    status: str = "PENDING"   # PENDING, IN_PROGRESS, COMPLETED, OVERDUE, CANCELLED
    due_date: Optional[date] = None
    due_time: Optional[time] = None
    category: str = "GENERAL"
    related_entity: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: list = field(default_factory=list)


@dataclass
class Notification:
    """알림 데이터"""
    notification_id: str
    type: str  # DEADLINE, ESTIMATE_RESPONSE, FOLLOW_UP, SCHEDULE, SYSTEM, ACHIEVEMENT
    title: str
    message: str
    priority: str = "MEDIUM"
    related_entity: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    is_read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class Schedule:
    """일정 데이터"""
    schedule_id: str
    title: str
    description: Optional[str] = None
    start_datetime: datetime = field(default_factory=datetime.utcnow)
    end_datetime: Optional[datetime] = None
    all_day: bool = False
    location: Optional[str] = None
    category: str = "MEETING"
    attendees: list = field(default_factory=list)
    reminder_minutes: Optional[int] = 30
    related_entity: Optional[str] = None
    recurrence: Optional[str] = None


@dataclass
class Reminder:
    """알림 설정 데이터"""
    reminder_id: str
    title: str
    message: Optional[str] = None
    remind_at: datetime = field(default_factory=datetime.utcnow)
    repeat: str = "NONE"  # NONE, DAILY, WEEKLY, MONTHLY
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# AI Assistant Service
# ============================================================================

class AIAssistantService:
    """AI 업무 비서 서비스"""

    # 자연어 명령 패턴
    COMMAND_PATTERNS = {
        "CREATE_TASK": [
            r"(?:할\s*일|태스크|task)\s*(?:추가|생성|만들|등록)",
            r"(?:해야\s*할\s*일|해야할일)\s*(?:추가|등록)",
            r"(?:내일|오늘|이번\s*주).*(?:하기|처리)",
        ],
        "QUERY_TASKS": [
            r"(?:할\s*일|태스크)\s*(?:목록|리스트|보여|조회|뭐)",
            r"(?:오늘|내일|이번\s*주)\s*(?:할\s*일|일정)",
            r"(?:뭐|무엇)\s*(?:해야|해야\s*해|할\s*거)",
        ],
        "CREATE_SCHEDULE": [
            r"(?:일정|미팅|회의|약속)\s*(?:추가|생성|잡|등록)",
            r"(?:내일|오늘|다음\s*주).*(?:미팅|회의|약속)",
        ],
        "QUERY_SCHEDULE": [
            r"(?:일정|미팅|회의)\s*(?:목록|리스트|보여|조회)",
            r"(?:오늘|내일|이번\s*주)\s*일정",
        ],
        "GET_SUMMARY": [
            r"(?:오늘|현재|지금)\s*(?:상황|현황|요약)",
            r"(?:업무|일)\s*(?:현황|상황|요약)",
            r"(?:어떤\s*일|뭐\s*있)",
        ],
        "SET_REMINDER": [
            r"(?:알림|리마인더)\s*(?:설정|등록|추가)",
            r"(?:알려\s*줘|기억해\s*줘|잊지\s*말)",
        ],
        "ANALYZE_WORKLOAD": [
            r"(?:업무량|일량|워크로드)\s*(?:분석|확인|체크)",
            r"(?:바쁜|한가한)\s*(?:지|가)",
        ],
        "SUGGEST_PRIORITY": [
            r"(?:우선순위|중요도)\s*(?:정해|추천|제안)",
            r"(?:뭐부터|어떤\s*거\s*부터)\s*(?:해야|하면)",
        ],
    }

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Args:
            data_dir: 데이터 저장 디렉토리
        """
        self.data_dir = data_dir or Path(__file__).parent.parent.parent.parent / "data" / "assistant"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 데이터 저장소
        self._tasks: dict[str, Task] = {}
        self._notifications: dict[str, Notification] = {}
        self._schedules: dict[str, Schedule] = {}
        self._reminders: dict[str, Reminder] = {}

        # 통계
        self._stats = {
            "total_tasks_created": 0,
            "total_tasks_completed": 0,
            "total_notifications": 0,
            "total_schedules": 0,
            "commands_processed": 0,
            "summaries_generated": 0
        }

        self._load_data()
        self._generate_sample_data()
        logger.info("AIAssistantService 초기화 완료")

    def _load_data(self) -> None:
        """저장된 데이터 로드"""
        # 실제 구현에서는 DB에서 로드
        pass

    def _save_data(self) -> None:
        """데이터 저장"""
        # 실제 구현에서는 DB에 저장
        pass

    def _generate_sample_data(self) -> None:
        """샘플 데이터 생성"""
        today = date.today()

        # 샘플 할 일
        sample_tasks = [
            Task(
                task_id=f"TSK-{uuid.uuid4().hex[:8].upper()}",
                title="ABC건설 견적서 발송",
                description="ABC건설 분전반 견적서 최종 검토 후 발송",
                priority="URGENT",
                status="PENDING",
                due_date=today,
                category="ESTIMATE",
                related_entity="EST-2024001"
            ),
            Task(
                task_id=f"TSK-{uuid.uuid4().hex[:8].upper()}",
                title="LS 차단기 재고 확인",
                description="LS산전 ABN-54 재고 현황 확인 필요",
                priority="HIGH",
                status="PENDING",
                due_date=today + timedelta(days=1),
                category="INVENTORY"
            ),
            Task(
                task_id=f"TSK-{uuid.uuid4().hex[:8].upper()}",
                title="신규 고객 미팅 준비",
                description="금요일 대한전력 미팅 자료 준비",
                priority="MEDIUM",
                status="IN_PROGRESS",
                due_date=today + timedelta(days=3),
                category="MEETING"
            ),
            Task(
                task_id=f"TSK-{uuid.uuid4().hex[:8].upper()}",
                title="월간 매출 보고서 작성",
                description="11월 매출 분석 및 보고서 작성",
                priority="LOW",
                status="PENDING",
                due_date=today + timedelta(days=7),
                category="REPORT"
            ),
        ]

        for task in sample_tasks:
            self._tasks[task.task_id] = task

        # 샘플 알림
        sample_notifications = [
            Notification(
                notification_id=f"NTF-{uuid.uuid4().hex[:8].upper()}",
                type="DEADLINE",
                title="견적 마감 임박",
                message="ABC건설 견적서 오늘 마감입니다",
                priority="URGENT",
                related_entity="EST-2024001",
                action_url="/estimates/EST-2024001",
                action_label="견적서 확인"
            ),
            Notification(
                notification_id=f"NTF-{uuid.uuid4().hex[:8].upper()}",
                type="ESTIMATE_RESPONSE",
                title="견적 회신 대기",
                message="XYZ전기 견적 회신 3일 경과",
                priority="HIGH",
                related_entity="EST-2024002"
            ),
            Notification(
                notification_id=f"NTF-{uuid.uuid4().hex[:8].upper()}",
                type="ACHIEVEMENT",
                title="월간 목표 달성",
                message="이번 달 견적 성공률 80% 달성! 👏",
                priority="LOW"
            ),
        ]

        for notif in sample_notifications:
            self._notifications[notif.notification_id] = notif

        # 샘플 일정
        now = datetime.now()
        sample_schedules = [
            Schedule(
                schedule_id=f"SCH-{uuid.uuid4().hex[:8].upper()}",
                title="ABC건설 미팅",
                description="분전반 설치 일정 협의",
                start_datetime=now.replace(hour=14, minute=0) + timedelta(days=1),
                end_datetime=now.replace(hour=15, minute=30) + timedelta(days=1),
                location="ABC건설 본사",
                category="MEETING",
                attendees=["김사장", "이과장"]
            ),
            Schedule(
                schedule_id=f"SCH-{uuid.uuid4().hex[:8].upper()}",
                title="주간 팀 미팅",
                description="주간 업무 진행 상황 공유",
                start_datetime=now.replace(hour=10, minute=0) + timedelta(days=2),
                end_datetime=now.replace(hour=11, minute=0) + timedelta(days=2),
                category="MEETING",
                recurrence="WEEKLY"
            ),
        ]

        for schedule in sample_schedules:
            self._schedules[schedule.schedule_id] = schedule

    # ========================================================================
    # Task Management (할 일 관리)
    # ========================================================================

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "MEDIUM",
        due_date: Optional[date] = None,
        due_time: Optional[time] = None,
        category: str = "GENERAL",
        related_entity: Optional[str] = None,
        tags: list = None
    ) -> Task:
        """할 일 생성"""
        task_id = f"TSK-{uuid.uuid4().hex[:8].upper()}"

        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            status="PENDING",
            due_date=due_date,
            due_time=due_time,
            category=category,
            related_entity=related_entity,
            tags=tags or []
        )

        self._tasks[task_id] = task
        self._stats["total_tasks_created"] += 1

        logger.info(f"할 일 생성: {task_id} - {title}")
        return task

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        due_date: Optional[date] = None,
        due_time: Optional[time] = None
    ) -> Optional[Task]:
        """할 일 수정"""
        if task_id not in self._tasks:
            return None

        task = self._tasks[task_id]

        if title:
            task.title = title
        if description is not None:
            task.description = description
        if priority:
            task.priority = priority
        if status:
            task.status = status
            if status == "COMPLETED":
                task.completed_at = datetime.utcnow()
                self._stats["total_tasks_completed"] += 1
        if due_date:
            task.due_date = due_date
        if due_time:
            task.due_time = due_time

        task.updated_at = datetime.utcnow()

        logger.info(f"할 일 수정: {task_id}")
        return task

    async def get_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        due_date: Optional[date] = None,
        include_overdue: bool = True
    ) -> list[Task]:
        """할 일 목록 조회"""
        tasks = list(self._tasks.values())
        today = date.today()

        # 기한 초과 업데이트
        for task in tasks:
            if task.status == "PENDING" and task.due_date and task.due_date < today:
                task.status = "OVERDUE"

        # 필터링
        if status:
            tasks = [t for t in tasks if t.status == status]
        if priority:
            tasks = [t for t in tasks if t.priority == priority]
        if category:
            tasks = [t for t in tasks if t.category == category]
        if due_date:
            tasks = [t for t in tasks if t.due_date == due_date]
        if not include_overdue:
            tasks = [t for t in tasks if t.status != "OVERDUE"]

        # 정렬: 우선순위 > 마감일
        priority_order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        tasks.sort(key=lambda t: (
            priority_order.get(t.priority, 4),
            t.due_date or date.max
        ))

        return tasks

    async def get_task_stats(self) -> dict:
        """할 일 통계"""
        tasks = list(self._tasks.values())
        today = date.today()

        return {
            "total": len(tasks),
            "pending": sum(1 for t in tasks if t.status == "PENDING"),
            "in_progress": sum(1 for t in tasks if t.status == "IN_PROGRESS"),
            "completed": sum(1 for t in tasks if t.status == "COMPLETED"),
            "overdue": sum(1 for t in tasks if t.status == "OVERDUE" or (t.status == "PENDING" and t.due_date and t.due_date < today)),
            "today": sum(1 for t in tasks if t.due_date == today),
            "urgent": sum(1 for t in tasks if t.priority == "URGENT" and t.status not in ["COMPLETED", "CANCELLED"])
        }

    # ========================================================================
    # Notification Management (알림 관리)
    # ========================================================================

    async def create_notification(
        self,
        type: str,
        title: str,
        message: str,
        priority: str = "MEDIUM",
        related_entity: Optional[str] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Notification:
        """알림 생성"""
        notification_id = f"NTF-{uuid.uuid4().hex[:8].upper()}"

        notification = Notification(
            notification_id=notification_id,
            type=type,
            title=title,
            message=message,
            priority=priority,
            related_entity=related_entity,
            action_url=action_url,
            action_label=action_label,
            expires_at=expires_at
        )

        self._notifications[notification_id] = notification
        self._stats["total_notifications"] += 1

        logger.info(f"알림 생성: {notification_id} - {title}")
        return notification

    async def get_notifications(
        self,
        unread_only: bool = False,
        type: Optional[str] = None,
        limit: int = 50
    ) -> list[Notification]:
        """알림 목록 조회"""
        notifications = list(self._notifications.values())

        # 만료된 알림 제외
        now = datetime.utcnow()
        notifications = [n for n in notifications if not n.expires_at or n.expires_at > now]

        if unread_only:
            notifications = [n for n in notifications if not n.is_read]
        if type:
            notifications = [n for n in notifications if n.type == type]

        # 정렬: 우선순위 > 생성일
        priority_order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        notifications.sort(key=lambda n: (
            priority_order.get(n.priority, 4),
            n.created_at
        ), reverse=True)

        return notifications[:limit]

    async def mark_notification_read(self, notification_id: str) -> bool:
        """알림 읽음 처리"""
        if notification_id in self._notifications:
            self._notifications[notification_id].is_read = True
            return True
        return False

    # ========================================================================
    # Schedule Management (일정 관리)
    # ========================================================================

    async def create_schedule(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: Optional[datetime] = None,
        description: Optional[str] = None,
        all_day: bool = False,
        location: Optional[str] = None,
        category: str = "MEETING",
        reminder_minutes: int = 30
    ) -> Schedule:
        """일정 생성"""
        schedule_id = f"SCH-{uuid.uuid4().hex[:8].upper()}"

        schedule = Schedule(
            schedule_id=schedule_id,
            title=title,
            description=description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            all_day=all_day,
            location=location,
            category=category,
            reminder_minutes=reminder_minutes
        )

        self._schedules[schedule_id] = schedule
        self._stats["total_schedules"] += 1

        logger.info(f"일정 생성: {schedule_id} - {title}")
        return schedule

    async def get_schedules(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None
    ) -> list[Schedule]:
        """일정 목록 조회"""
        schedules = list(self._schedules.values())

        if start_date:
            schedules = [s for s in schedules if s.start_datetime.date() >= start_date]
        if end_date:
            schedules = [s for s in schedules if s.start_datetime.date() <= end_date]
        if category:
            schedules = [s for s in schedules if s.category == category]

        # 시간순 정렬
        schedules.sort(key=lambda s: s.start_datetime)

        return schedules

    # ========================================================================
    # Natural Language Command (자연어 명령)
    # ========================================================================

    async def process_natural_command(
        self,
        command: str,
        context: dict = None
    ) -> dict:
        """자연어 명령 처리"""
        request_id = str(uuid.uuid4())
        self._stats["commands_processed"] += 1

        # 명령 파싱
        parsed = self._parse_command(command)

        # 명령 실행
        result = await self._execute_command(parsed, context or {})

        # 응답 생성
        message = self._generate_response_message(parsed, result)
        suggestions = self._generate_suggestions(parsed, result)

        return {
            "request_id": request_id,
            "parsed": {
                "command_type": parsed["type"],
                "confidence": parsed["confidence"],
                "parameters": parsed["parameters"],
                "original_text": command
            },
            "result": result,
            "message": message,
            "suggestions": suggestions,
            "executed_at": datetime.utcnow().isoformat()
        }

    def _parse_command(self, command: str) -> dict:
        """명령 파싱"""
        command_lower = command.lower()

        for cmd_type, patterns in self.COMMAND_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, command_lower):
                    parameters = self._extract_parameters(command, cmd_type)
                    return {
                        "type": cmd_type,
                        "confidence": 0.85,
                        "parameters": parameters
                    }

        return {
            "type": "UNKNOWN",
            "confidence": 0.3,
            "parameters": {}
        }

    def _extract_parameters(self, command: str, cmd_type: str) -> dict:
        """명령에서 파라미터 추출"""
        params = {}

        # 날짜 추출
        if "오늘" in command:
            params["date"] = date.today()
        elif "내일" in command:
            params["date"] = date.today() + timedelta(days=1)
        elif "이번 주" in command or "이번주" in command:
            params["date_range"] = "this_week"

        # 우선순위 추출
        if "긴급" in command or "급해" in command:
            params["priority"] = "URGENT"
        elif "중요" in command:
            params["priority"] = "HIGH"

        # 제목 추출 (간단한 휴리스틱)
        if cmd_type == "CREATE_TASK":
            # "~하기", "~하자", "~해야" 등의 패턴에서 제목 추출
            match = re.search(r"['\"](.+?)['\"]", command)
            if match:
                params["title"] = match.group(1)

        return params

    async def _execute_command(self, parsed: dict, context: dict) -> Any:
        """명령 실행"""
        cmd_type = parsed["type"]
        params = parsed["parameters"]

        if cmd_type == "CREATE_TASK":
            title = params.get("title", "새 할 일")
            task = await self.create_task(
                title=title,
                priority=params.get("priority", "MEDIUM"),
                due_date=params.get("date")
            )
            return {"task": asdict(task)}

        elif cmd_type == "QUERY_TASKS":
            tasks = await self.get_tasks(
                due_date=params.get("date")
            )
            return {"tasks": [asdict(t) for t in tasks[:10]]}

        elif cmd_type == "CREATE_SCHEDULE":
            title = params.get("title", "새 일정")
            start = datetime.combine(
                params.get("date", date.today() + timedelta(days=1)),
                time(10, 0)
            )
            schedule = await self.create_schedule(
                title=title,
                start_datetime=start
            )
            return {"schedule": asdict(schedule)}

        elif cmd_type == "QUERY_SCHEDULE":
            schedules = await self.get_schedules(
                start_date=params.get("date", date.today())
            )
            return {"schedules": [asdict(s) for s in schedules[:10]]}

        elif cmd_type == "GET_SUMMARY":
            summary = await self.get_daily_summary()
            return summary

        elif cmd_type == "ANALYZE_WORKLOAD":
            analysis = await self.analyze_workload()
            return analysis

        elif cmd_type == "SUGGEST_PRIORITY":
            suggestions = await self.suggest_priorities()
            return suggestions

        else:
            return {"message": "명령을 이해하지 못했습니다. 다시 말씀해 주세요."}

    def _generate_response_message(self, parsed: dict, result: Any) -> str:
        """응답 메시지 생성"""
        cmd_type = parsed["type"]

        if cmd_type == "CREATE_TASK":
            return f"할 일을 추가했습니다: {result.get('task', {}).get('title', '')}"
        elif cmd_type == "QUERY_TASKS":
            count = len(result.get("tasks", []))
            return f"{count}개의 할 일이 있습니다."
        elif cmd_type == "CREATE_SCHEDULE":
            return f"일정을 추가했습니다: {result.get('schedule', {}).get('title', '')}"
        elif cmd_type == "QUERY_SCHEDULE":
            count = len(result.get("schedules", []))
            return f"{count}개의 일정이 있습니다."
        elif cmd_type == "GET_SUMMARY":
            return "오늘의 업무 현황입니다."
        elif cmd_type == "ANALYZE_WORKLOAD":
            return "업무량 분석 결과입니다."
        elif cmd_type == "SUGGEST_PRIORITY":
            return "우선순위 제안입니다."
        else:
            return "명령을 이해하지 못했습니다. 다른 표현으로 말씀해 주세요."

    def _generate_suggestions(self, parsed: dict, result: Any) -> list[str]:
        """추가 제안 생성"""
        suggestions = []

        if parsed["type"] == "UNKNOWN":
            suggestions.extend([
                "'오늘 할 일 보여줘'라고 말해보세요",
                "'견적서 발송하기 추가해줘'라고 말해보세요",
                "'업무 현황 알려줘'라고 말해보세요"
            ])
        elif parsed["type"] == "QUERY_TASKS":
            if len(result.get("tasks", [])) > 0:
                suggestions.append("우선순위 제안이 필요하면 '우선순위 정해줘'라고 말해보세요")

        return suggestions

    # ========================================================================
    # Workload Analysis (업무량 분석)
    # ========================================================================

    async def analyze_workload(self) -> dict:
        """업무량 분석"""
        tasks = list(self._tasks.values())
        today = date.today()

        # 통계 계산
        pending_tasks = [t for t in tasks if t.status in ["PENDING", "IN_PROGRESS"]]
        completed_today = [t for t in tasks if t.status == "COMPLETED" and t.completed_at and t.completed_at.date() == today]
        overdue = [t for t in tasks if t.status == "OVERDUE" or (t.status == "PENDING" and t.due_date and t.due_date < today)]

        # 우선순위별 분류
        urgent = sum(1 for t in pending_tasks if t.priority == "URGENT")
        high = sum(1 for t in pending_tasks if t.priority == "HIGH")
        medium = sum(1 for t in pending_tasks if t.priority == "MEDIUM")
        low = sum(1 for t in pending_tasks if t.priority == "LOW")

        # 업무 부하 점수 계산 (0-100)
        workload_score = min(100, (
            urgent * 25 +
            high * 15 +
            medium * 8 +
            low * 3 +
            len(overdue) * 20
        ))

        # 상태 결정
        if workload_score >= 80:
            status = "OVERLOADED"
        elif workload_score >= 60:
            status = "BUSY"
        elif workload_score >= 30:
            status = "NORMAL"
        else:
            status = "LIGHT"

        # 예상 소요 시간 (시간 기준)
        estimated_hours = urgent * 2 + high * 1.5 + medium * 1 + low * 0.5

        # 권장사항
        recommendations = []
        if urgent > 0:
            recommendations.append(f"긴급 업무 {urgent}건을 먼저 처리하세요")
        if len(overdue) > 0:
            recommendations.append(f"기한 초과 업무 {len(overdue)}건을 확인하세요")
        if workload_score >= 80:
            recommendations.append("업무 위임 또는 일정 조정을 고려하세요")
        if workload_score < 30:
            recommendations.append("추가 업무를 처리할 여유가 있습니다")

        return {
            "total_tasks": len(tasks),
            "completed_today": len(completed_today),
            "pending_urgent": urgent,
            "pending_high": high,
            "pending_medium": medium,
            "pending_low": low,
            "overdue_tasks": len(overdue),
            "workload_score": round(workload_score, 1),
            "workload_status": status,
            "estimated_hours": round(estimated_hours, 1),
            "recommendations": recommendations
        }

    # ========================================================================
    # Priority Suggestions (우선순위 제안)
    # ========================================================================

    async def suggest_priorities(self) -> dict:
        """우선순위 제안"""
        tasks = await self.get_tasks(include_overdue=True)
        pending_tasks = [t for t in tasks if t.status in ["PENDING", "IN_PROGRESS", "OVERDUE"]]

        suggestions = []
        optimized_order = []

        for task in pending_tasks:
            current = task.priority
            suggested = current
            reason = ""
            impact = ""

            # 기한 기반 조정
            if task.due_date:
                days_until = (task.due_date - date.today()).days

                if days_until < 0:  # 기한 초과
                    suggested = "URGENT"
                    reason = f"기한이 {abs(days_until)}일 초과되었습니다"
                    impact = "즉시 처리하지 않으면 고객 신뢰 하락"
                elif days_until == 0:  # 오늘 마감
                    suggested = "URGENT"
                    reason = "오늘이 마감일입니다"
                    impact = "오늘 완료하지 않으면 기한 초과"
                elif days_until <= 2:  # 2일 이내
                    if current not in ["URGENT", "HIGH"]:
                        suggested = "HIGH"
                        reason = f"마감까지 {days_until}일 남았습니다"
                        impact = "조기 완료로 여유 확보"

            # 카테고리 기반 조정
            if task.category == "ESTIMATE" and current not in ["URGENT", "HIGH"]:
                suggested = "HIGH"
                reason = "견적 관련 업무는 우선 처리 필요"
                impact = "빠른 회신으로 수주 확률 향상"

            if suggested != current:
                suggestions.append({
                    "task_id": task.task_id,
                    "task_title": task.title,
                    "current_priority": current,
                    "suggested_priority": suggested,
                    "reason": reason,
                    "impact": impact
                })

            optimized_order.append(task.task_id)

        # 최적 순서로 재정렬
        priority_order = {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        optimized_order = [t.task_id for t in sorted(
            pending_tasks,
            key=lambda t: (priority_order.get(t.priority, 4), t.due_date or date.max)
        )]

        return {
            "suggestions": suggestions,
            "optimized_order": optimized_order,
            "rationale": "마감일과 업무 중요도를 기반으로 최적화했습니다",
            "estimated_efficiency_gain": min(30, len(suggestions) * 5)
        }

    # ========================================================================
    # Daily Summary (일일 요약)
    # ========================================================================

    async def get_daily_summary(self, target_date: Optional[date] = None) -> dict:
        """일일 요약 생성"""
        target = target_date or date.today()
        self._stats["summaries_generated"] += 1

        # 인사말 생성
        hour = datetime.now().hour
        if hour < 12:
            greeting = "좋은 아침입니다, 대표님! ☀️"
        elif hour < 18:
            greeting = "좋은 오후입니다, 대표님! 🌤️"
        else:
            greeting = "좋은 저녁입니다, 대표님! 🌙"

        # 할 일 통계
        task_stats = await self.get_task_stats()

        # 오늘 일정
        today_schedules = await self.get_schedules(start_date=target, end_date=target)

        # 다음 일정
        upcoming_schedules = await self.get_schedules(start_date=target)
        next_schedule = upcoming_schedules[0] if upcoming_schedules else None

        # 긴급 알림
        urgent_notifications = await self.get_notifications(unread_only=True)
        urgent_notifications = [n for n in urgent_notifications if n.priority in ["URGENT", "HIGH"]][:3]

        # 우선 처리 권장 할 일
        priority_tasks = await self.get_tasks(priority="URGENT")
        if len(priority_tasks) < 3:
            high_tasks = await self.get_tasks(priority="HIGH")
            priority_tasks.extend(high_tasks[:3 - len(priority_tasks)])

        # 인사이트 생성
        insights = []
        if task_stats["overdue"] > 0:
            insights.append(f"⚠️ 기한 초과 업무가 {task_stats['overdue']}건 있습니다")
        if task_stats["today"] > 3:
            insights.append(f"📋 오늘 마감 업무가 {task_stats['today']}건입니다. 효율적인 시간 관리가 필요합니다")
        if task_stats["completed"] > 5:
            insights.append("🎉 완료한 업무가 많습니다. 잘 진행되고 있습니다!")

        # 팁 생성
        tips = [
            "가장 어려운 업무를 오전에 처리하면 효율이 높아집니다",
            "짧은 휴식을 취하면 집중력이 향상됩니다",
            "견적 회신은 24시간 이내가 효과적입니다"
        ]

        return {
            "summary_date": target.isoformat(),
            "greeting": greeting,
            "tasks_completed": task_stats["completed"],
            "tasks_remaining": task_stats["pending"] + task_stats["in_progress"],
            "tasks_overdue": task_stats["overdue"],
            "schedules_today": len(today_schedules),
            "next_schedule": asdict(next_schedule) if next_schedule else None,
            "estimates_pending": 5,  # 실제 구현에서는 DB에서 조회
            "estimates_urgent": 2,
            "urgent_notifications": [asdict(n) for n in urgent_notifications],
            "priority_tasks": [asdict(t) for t in priority_tasks[:5]],
            "insights": insights,
            "tips": [random.choice(tips)],
            "generated_at": datetime.utcnow().isoformat()
        }

    # ========================================================================
    # Reminder Management (알림 관리)
    # ========================================================================

    async def create_reminder(
        self,
        title: str,
        remind_at: datetime,
        message: Optional[str] = None,
        repeat: str = "NONE",
        related_entity: Optional[str] = None
    ) -> Reminder:
        """알림 설정"""
        reminder_id = f"RMD-{uuid.uuid4().hex[:8].upper()}"

        reminder = Reminder(
            reminder_id=reminder_id,
            title=title,
            message=message,
            remind_at=remind_at,
            repeat=repeat
        )

        self._reminders[reminder_id] = reminder

        logger.info(f"알림 설정: {reminder_id} - {title}")
        return reminder

    async def get_reminders(self, active_only: bool = True) -> list[Reminder]:
        """알림 목록 조회"""
        reminders = list(self._reminders.values())

        if active_only:
            reminders = [r for r in reminders if r.is_active]

        reminders.sort(key=lambda r: r.remind_at)
        return reminders

    # ========================================================================
    # Status (상태)
    # ========================================================================

    def get_status(self) -> dict:
        """AI 비서 상태 조회"""
        return {
            "is_active": True,
            "last_activity": datetime.utcnow(),
            "pending_reminders": len([r for r in self._reminders.values() if r.is_active]),
            "active_monitors": 3,  # 모니터링 항목 수
            "stats": self._stats.copy(),
            "capabilities": [
                "할 일 관리",
                "일정 관리",
                "알림 설정",
                "자연어 명령",
                "업무량 분석",
                "우선순위 제안",
                "일일 요약"
            ],
            "message": "AI 비서가 정상적으로 작동 중입니다"
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_assistant_service: Optional[AIAssistantService] = None


def get_assistant_service() -> AIAssistantService:
    """AIAssistantService 싱글톤 인스턴스 반환"""
    global _assistant_service
    if _assistant_service is None:
        _assistant_service = AIAssistantService()
    return _assistant_service
