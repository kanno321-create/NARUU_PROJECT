"""
AI Assistant API Schemas (Phase XVI)

AI 업무 비서의 Request/Response 스키마 정의
Contract-First 원칙에 따라 API 계약을 먼저 정의합니다.

핵심 기능:
- 자동 알림 (마감 임박, 미응답 견적 등)
- 스마트 일정 관리
- 업무 우선순위 추천
- 실시간 업무 현황 모니터링
- 자연어 명령 처리
"""

from datetime import datetime, date, time
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


# ============================================================================
# Enums & Types
# ============================================================================

TaskPriority = Literal[
    "URGENT",      # 긴급 (즉시 처리)
    "HIGH",        # 높음 (오늘 처리)
    "MEDIUM",      # 보통 (이번 주)
    "LOW"          # 낮음 (여유 있음)
]

TaskStatus = Literal[
    "PENDING",     # 대기
    "IN_PROGRESS", # 진행 중
    "COMPLETED",   # 완료
    "OVERDUE",     # 기한 초과
    "CANCELLED"    # 취소
]

NotificationType = Literal[
    "DEADLINE",           # 마감 임박
    "ESTIMATE_RESPONSE",  # 견적 응답 필요
    "FOLLOW_UP",          # 팔로업 필요
    "SCHEDULE",           # 일정 알림
    "SYSTEM",             # 시스템 알림
    "ACHIEVEMENT"         # 성과 알림
]

CommandType = Literal[
    "CREATE_TASK",       # 할 일 생성
    "UPDATE_TASK",       # 할 일 수정
    "QUERY_TASKS",       # 할 일 조회
    "CREATE_SCHEDULE",   # 일정 생성
    "QUERY_SCHEDULE",    # 일정 조회
    "GET_SUMMARY",       # 현황 요약
    "SET_REMINDER",      # 알림 설정
    "ANALYZE_WORKLOAD",  # 업무량 분석
    "SUGGEST_PRIORITY",  # 우선순위 제안
    "UNKNOWN"            # 알 수 없음
]


# ============================================================================
# Task Management (할 일 관리)
# ============================================================================

class TaskItem(BaseModel):
    """할 일 항목"""
    task_id: str = Field(..., description="할 일 ID")
    title: str = Field(..., description="제목")
    description: Optional[str] = Field(None, description="설명")
    priority: TaskPriority = Field(..., description="우선순위")
    status: TaskStatus = Field(..., description="상태")
    due_date: Optional[date] = Field(None, description="마감일")
    due_time: Optional[time] = Field(None, description="마감 시간")
    category: str = Field(default="GENERAL", description="카테고리")
    related_entity: Optional[str] = Field(None, description="연관 엔티티 (견적ID, 고객ID 등)")
    assigned_to: Optional[str] = Field(None, description="담당자")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    tags: list[str] = Field(default_factory=list, description="태그")


class CreateTaskRequest(BaseModel):
    """할 일 생성 요청"""
    title: str = Field(..., min_length=1, max_length=200, description="제목")
    description: Optional[str] = Field(None, max_length=1000, description="설명")
    priority: TaskPriority = Field(default="MEDIUM", description="우선순위")
    due_date: Optional[date] = Field(None, description="마감일")
    due_time: Optional[time] = Field(None, description="마감 시간")
    category: str = Field(default="GENERAL", description="카테고리")
    related_entity: Optional[str] = Field(None, description="연관 엔티티")
    tags: list[str] = Field(default_factory=list, description="태그")


class UpdateTaskRequest(BaseModel):
    """할 일 수정 요청"""
    title: Optional[str] = Field(None, description="제목")
    description: Optional[str] = Field(None, description="설명")
    priority: Optional[TaskPriority] = Field(None, description="우선순위")
    status: Optional[TaskStatus] = Field(None, description="상태")
    due_date: Optional[date] = Field(None, description="마감일")
    due_time: Optional[time] = Field(None, description="마감 시간")


class TaskListResponse(BaseModel):
    """할 일 목록 응답"""
    tasks: list[TaskItem] = Field(..., description="할 일 목록")
    total: int = Field(..., description="전체 개수")
    pending_count: int = Field(..., description="대기 중 개수")
    overdue_count: int = Field(..., description="기한 초과 개수")
    today_count: int = Field(..., description="오늘 마감 개수")


# ============================================================================
# Notifications (알림)
# ============================================================================

class NotificationItem(BaseModel):
    """알림 항목"""
    notification_id: str = Field(..., description="알림 ID")
    type: NotificationType = Field(..., description="알림 유형")
    title: str = Field(..., description="알림 제목")
    message: str = Field(..., description="알림 내용")
    priority: TaskPriority = Field(..., description="중요도")
    related_entity: Optional[str] = Field(None, description="연관 엔티티")
    action_url: Optional[str] = Field(None, description="액션 URL")
    action_label: Optional[str] = Field(None, description="액션 버튼 텍스트")
    is_read: bool = Field(default=False, description="읽음 여부")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="만료 시간")


class NotificationListResponse(BaseModel):
    """알림 목록 응답"""
    notifications: list[NotificationItem] = Field(..., description="알림 목록")
    unread_count: int = Field(..., description="읽지 않은 알림 수")
    urgent_count: int = Field(..., description="긴급 알림 수")


# ============================================================================
# Schedule (일정)
# ============================================================================

class ScheduleItem(BaseModel):
    """일정 항목"""
    schedule_id: str = Field(..., description="일정 ID")
    title: str = Field(..., description="제목")
    description: Optional[str] = Field(None, description="설명")
    start_datetime: datetime = Field(..., description="시작 시간")
    end_datetime: Optional[datetime] = Field(None, description="종료 시간")
    all_day: bool = Field(default=False, description="종일 여부")
    location: Optional[str] = Field(None, description="장소")
    category: str = Field(default="MEETING", description="카테고리")
    attendees: list[str] = Field(default_factory=list, description="참석자")
    reminder_minutes: Optional[int] = Field(None, description="알림 (분 전)")
    related_entity: Optional[str] = Field(None, description="연관 엔티티")
    recurrence: Optional[str] = Field(None, description="반복 규칙")


class CreateScheduleRequest(BaseModel):
    """일정 생성 요청"""
    title: str = Field(..., min_length=1, max_length=200, description="제목")
    description: Optional[str] = Field(None, description="설명")
    start_datetime: datetime = Field(..., description="시작 시간")
    end_datetime: Optional[datetime] = Field(None, description="종료 시간")
    all_day: bool = Field(default=False, description="종일 여부")
    location: Optional[str] = Field(None, description="장소")
    category: str = Field(default="MEETING", description="카테고리")
    reminder_minutes: int = Field(default=30, description="알림 (분 전)")


class ScheduleListResponse(BaseModel):
    """일정 목록 응답"""
    schedules: list[ScheduleItem] = Field(..., description="일정 목록")
    total: int = Field(..., description="전체 개수")
    today_count: int = Field(..., description="오늘 일정 수")
    week_count: int = Field(..., description="이번 주 일정 수")


# ============================================================================
# Natural Language Command (자연어 명령)
# ============================================================================

class NaturalCommandRequest(BaseModel):
    """자연어 명령 요청"""
    command: str = Field(..., min_length=1, description="자연어 명령")
    context: dict = Field(default_factory=dict, description="추가 컨텍스트")


class ParsedCommand(BaseModel):
    """파싱된 명령"""
    command_type: CommandType = Field(..., description="명령 유형")
    confidence: float = Field(..., ge=0, le=1, description="파싱 신뢰도")
    parameters: dict = Field(default_factory=dict, description="추출된 파라미터")
    original_text: str = Field(..., description="원본 텍스트")


class NaturalCommandResponse(BaseModel):
    """자연어 명령 응답"""
    request_id: str = Field(..., description="요청 ID")
    parsed: ParsedCommand = Field(..., description="파싱 결과")
    result: Any = Field(..., description="실행 결과")
    message: str = Field(..., description="응답 메시지")
    suggestions: list[str] = Field(default_factory=list, description="추가 제안")
    executed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Workload Analysis (업무량 분석)
# ============================================================================

class WorkloadAnalysis(BaseModel):
    """업무량 분석 결과"""
    total_tasks: int = Field(..., description="전체 할 일 수")
    completed_today: int = Field(..., description="오늘 완료한 할 일")
    pending_urgent: int = Field(..., description="긴급 대기 중")
    pending_high: int = Field(..., description="높음 대기 중")
    pending_medium: int = Field(..., description="보통 대기 중")
    pending_low: int = Field(..., description="낮음 대기 중")
    overdue_tasks: int = Field(..., description="기한 초과")
    workload_score: float = Field(..., ge=0, le=100, description="업무 부하 점수")
    workload_status: Literal["LIGHT", "NORMAL", "BUSY", "OVERLOADED"] = Field(
        ...,
        description="업무 상태"
    )
    estimated_hours: float = Field(..., description="예상 소요 시간")
    recommendations: list[str] = Field(default_factory=list, description="권장 사항")


# ============================================================================
# Priority Suggestions (우선순위 제안)
# ============================================================================

class PrioritySuggestion(BaseModel):
    """우선순위 제안"""
    task_id: str = Field(..., description="할 일 ID")
    task_title: str = Field(..., description="할 일 제목")
    current_priority: TaskPriority = Field(..., description="현재 우선순위")
    suggested_priority: TaskPriority = Field(..., description="제안 우선순위")
    reason: str = Field(..., description="제안 이유")
    impact: str = Field(..., description="예상 영향")


class PrioritySuggestionResponse(BaseModel):
    """우선순위 제안 응답"""
    suggestions: list[PrioritySuggestion] = Field(..., description="제안 목록")
    optimized_order: list[str] = Field(..., description="최적화된 처리 순서 (task_id)")
    rationale: str = Field(..., description="최적화 근거")
    estimated_efficiency_gain: float = Field(..., description="예상 효율 향상 (%)")


# ============================================================================
# Daily Summary (일일 요약)
# ============================================================================

class DailySummary(BaseModel):
    """일일 요약"""
    summary_date: date = Field(..., description="날짜")
    greeting: str = Field(..., description="인사말")

    # 업무 현황
    tasks_completed: int = Field(..., description="완료한 할 일")
    tasks_remaining: int = Field(..., description="남은 할 일")
    tasks_overdue: int = Field(..., description="기한 초과")

    # 일정 현황
    schedules_today: int = Field(..., description="오늘 일정")
    next_schedule: Optional[ScheduleItem] = Field(None, description="다음 일정")

    # 견적 현황
    estimates_pending: int = Field(..., description="대기 중 견적")
    estimates_urgent: int = Field(..., description="긴급 견적")

    # 알림
    urgent_notifications: list[NotificationItem] = Field(
        default_factory=list,
        description="긴급 알림"
    )

    # 우선 처리 권장
    priority_tasks: list[TaskItem] = Field(
        default_factory=list,
        description="우선 처리 권장 할 일"
    )

    # 인사이트
    insights: list[str] = Field(default_factory=list, description="오늘의 인사이트")
    tips: list[str] = Field(default_factory=list, description="업무 팁")

    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Reminder (알림 설정)
# ============================================================================

class ReminderRequest(BaseModel):
    """알림 설정 요청"""
    title: str = Field(..., description="알림 제목")
    message: Optional[str] = Field(None, description="알림 내용")
    remind_at: datetime = Field(..., description="알림 시간")
    repeat: Optional[Literal["NONE", "DAILY", "WEEKLY", "MONTHLY"]] = Field(
        default="NONE",
        description="반복 설정"
    )
    related_entity: Optional[str] = Field(None, description="연관 엔티티")


class ReminderItem(BaseModel):
    """알림 항목"""
    reminder_id: str = Field(..., description="알림 ID")
    title: str = Field(..., description="알림 제목")
    message: Optional[str] = Field(None, description="알림 내용")
    remind_at: datetime = Field(..., description="알림 시간")
    repeat: str = Field(..., description="반복 설정")
    is_active: bool = Field(default=True, description="활성화 여부")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Assistant Status (비서 상태)
# ============================================================================

class AssistantStatusResponse(BaseModel):
    """AI 비서 상태 응답"""
    is_active: bool = Field(..., description="활성화 상태")
    last_activity: Optional[datetime] = Field(None, description="마지막 활동")
    pending_reminders: int = Field(..., description="대기 중 알림")
    active_monitors: int = Field(..., description="활성 모니터링")
    stats: dict = Field(default_factory=dict, description="통계")
    capabilities: list[str] = Field(..., description="사용 가능 기능")
    message: str = Field(..., description="상태 메시지")
