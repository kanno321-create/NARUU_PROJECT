"""
AI Assistant API Routes (Phase XVI)

AI 업무 비서 API 엔드포인트
Contract-First 원칙에 따라 정의된 API 계약을 구현합니다.

엔드포인트:
- POST /v1/assistant/tasks              - 할 일 생성
- GET  /v1/assistant/tasks              - 할 일 목록
- PATCH /v1/assistant/tasks/{task_id}   - 할 일 수정
- GET  /v1/assistant/notifications      - 알림 목록
- POST /v1/assistant/schedules          - 일정 생성
- GET  /v1/assistant/schedules          - 일정 목록
- POST /v1/assistant/command            - 자연어 명령
- GET  /v1/assistant/summary            - 일일 요약
- GET  /v1/assistant/workload           - 업무량 분석
- GET  /v1/assistant/priorities         - 우선순위 제안
- POST /v1/assistant/reminders          - 알림 설정
- GET  /v1/assistant/status             - 비서 상태
"""

import logging
from datetime import date, datetime, time
from typing import Optional
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, status

from kis_estimator_core.api.schemas.assistant import (
    TaskItem,
    CreateTaskRequest,
    UpdateTaskRequest,
    TaskListResponse,
    NotificationItem,
    NotificationListResponse,
    ScheduleItem,
    CreateScheduleRequest,
    ScheduleListResponse,
    NaturalCommandRequest,
    NaturalCommandResponse,
    ParsedCommand,
    WorkloadAnalysis,
    PrioritySuggestion,
    PrioritySuggestionResponse,
    DailySummary,
    ReminderRequest,
    ReminderItem,
    AssistantStatusResponse,
)
from kis_estimator_core.services.assistant_service import (
    get_assistant_service,
    AIAssistantService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


# ============================================================================
# Helper Functions
# ============================================================================

def _convert_task(task) -> TaskItem:
    """Task 객체를 TaskItem으로 변환"""
    return TaskItem(
        task_id=task.task_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        due_date=task.due_date,
        due_time=task.due_time,
        category=task.category,
        related_entity=task.related_entity,
        assigned_to=task.assigned_to,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        tags=task.tags
    )


def _convert_notification(notif) -> NotificationItem:
    """Notification 객체를 NotificationItem으로 변환"""
    return NotificationItem(
        notification_id=notif.notification_id,
        type=notif.type,
        title=notif.title,
        message=notif.message,
        priority=notif.priority,
        related_entity=notif.related_entity,
        action_url=notif.action_url,
        action_label=notif.action_label,
        is_read=notif.is_read,
        created_at=notif.created_at,
        expires_at=notif.expires_at
    )


def _convert_schedule(schedule) -> ScheduleItem:
    """Schedule 객체를 ScheduleItem으로 변환"""
    return ScheduleItem(
        schedule_id=schedule.schedule_id,
        title=schedule.title,
        description=schedule.description,
        start_datetime=schedule.start_datetime,
        end_datetime=schedule.end_datetime,
        all_day=schedule.all_day,
        location=schedule.location,
        category=schedule.category,
        attendees=schedule.attendees,
        reminder_minutes=schedule.reminder_minutes,
        related_entity=schedule.related_entity,
        recurrence=schedule.recurrence
    )


def _convert_reminder(reminder) -> ReminderItem:
    """Reminder 객체를 ReminderItem으로 변환"""
    return ReminderItem(
        reminder_id=reminder.reminder_id,
        title=reminder.title,
        message=reminder.message,
        remind_at=reminder.remind_at,
        repeat=reminder.repeat,
        is_active=reminder.is_active,
        created_at=reminder.created_at
    )


# ============================================================================
# Task Management Endpoints
# ============================================================================

@router.post(
    "/tasks",
    response_model=TaskItem,
    status_code=status.HTTP_201_CREATED,
    summary="할 일 생성",
    description="새로운 할 일을 생성합니다."
)
async def create_task(request: CreateTaskRequest):
    """할 일 생성"""
    logger.info(f"할 일 생성 요청: {request.title}")

    try:
        service = get_assistant_service()

        task = await service.create_task(
            title=request.title,
            description=request.description,
            priority=request.priority,
            due_date=request.due_date,
            due_time=request.due_time,
            category=request.category,
            related_entity=request.related_entity,
            tags=request.tags
        )

        return _convert_task(task)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    summary="할 일 목록",
    description="할 일 목록을 조회합니다."
)
async def get_tasks(
    status_filter: Optional[str] = Query(None, alias="status", description="상태 필터"),
    priority: Optional[str] = Query(None, description="우선순위 필터"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    due_date: Optional[date] = Query(None, description="마감일 필터")
):
    """할 일 목록 조회"""
    try:
        service = get_assistant_service()

        tasks = await service.get_tasks(
            status=status_filter,
            priority=priority,
            category=category,
            due_date=due_date
        )

        task_stats = await service.get_task_stats()

        return TaskListResponse(
            tasks=[_convert_task(t) for t in tasks],
            total=len(tasks),
            pending_count=task_stats["pending"],
            overdue_count=task_stats["overdue"],
            today_count=task_stats["today"]
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskItem,
    summary="할 일 수정",
    description="할 일을 수정합니다."
)
async def update_task(task_id: str, request: UpdateTaskRequest):
    """할 일 수정"""
    logger.info(f"할 일 수정 요청: {task_id}")

    try:
        service = get_assistant_service()

        task = await service.update_task(
            task_id=task_id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            status=request.status,
            due_date=request.due_date,
            due_time=request.due_time
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"할 일을 찾을 수 없습니다: {task_id}"
            )

        return _convert_task(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Notification Endpoints
# ============================================================================

@router.get(
    "/notifications",
    response_model=NotificationListResponse,
    summary="알림 목록",
    description="알림 목록을 조회합니다."
)
async def get_notifications(
    unread_only: bool = Query(False, description="읽지 않은 알림만"),
    type_filter: Optional[str] = Query(None, alias="type", description="알림 유형 필터"),
    limit: int = Query(50, ge=1, le=100, description="최대 개수")
):
    """알림 목록 조회"""
    try:
        service = get_assistant_service()

        notifications = await service.get_notifications(
            unread_only=unread_only,
            type=type_filter,
            limit=limit
        )

        unread_count = sum(1 for n in notifications if not n.is_read)
        urgent_count = sum(1 for n in notifications if n.priority in ["URGENT", "HIGH"])

        return NotificationListResponse(
            notifications=[_convert_notification(n) for n in notifications],
            unread_count=unread_count,
            urgent_count=urgent_count
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post(
    "/notifications/{notification_id}/read",
    summary="알림 읽음 처리",
    description="알림을 읽음 처리합니다."
)
async def mark_notification_read(notification_id: str):
    """알림 읽음 처리"""
    try:
        service = get_assistant_service()
        success = await service.mark_notification_read(notification_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"알림을 찾을 수 없습니다: {notification_id}"
            )

        return {"message": "알림을 읽음 처리했습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Schedule Endpoints
# ============================================================================

@router.post(
    "/schedules",
    response_model=ScheduleItem,
    status_code=status.HTTP_201_CREATED,
    summary="일정 생성",
    description="새로운 일정을 생성합니다."
)
async def create_schedule(request: CreateScheduleRequest):
    """일정 생성"""
    logger.info(f"일정 생성 요청: {request.title}")

    try:
        service = get_assistant_service()

        schedule = await service.create_schedule(
            title=request.title,
            start_datetime=request.start_datetime,
            end_datetime=request.end_datetime,
            description=request.description,
            all_day=request.all_day,
            location=request.location,
            category=request.category,
            reminder_minutes=request.reminder_minutes
        )

        return _convert_schedule(schedule)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/schedules",
    response_model=ScheduleListResponse,
    summary="일정 목록",
    description="일정 목록을 조회합니다."
)
async def get_schedules(
    start_date: Optional[date] = Query(None, description="시작일"),
    end_date: Optional[date] = Query(None, description="종료일"),
    category: Optional[str] = Query(None, description="카테고리 필터")
):
    """일정 목록 조회"""
    try:
        service = get_assistant_service()

        if not start_date:
            start_date = date.today()

        schedules = await service.get_schedules(
            start_date=start_date,
            end_date=end_date,
            category=category
        )

        today = date.today()
        week_end = today + timedelta(days=7)

        today_count = sum(1 for s in schedules if s.start_datetime.date() == today)
        week_count = sum(1 for s in schedules if s.start_datetime.date() <= week_end)

        return ScheduleListResponse(
            schedules=[_convert_schedule(s) for s in schedules],
            total=len(schedules),
            today_count=today_count,
            week_count=week_count
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Natural Language Command Endpoint
# ============================================================================

@router.post(
    "/command",
    response_model=NaturalCommandResponse,
    summary="자연어 명령",
    description="자연어로 명령을 내립니다."
)
async def process_command(request: NaturalCommandRequest):
    """
    자연어 명령 처리

    예시:
    - "오늘 할 일 보여줘"
    - "ABC건설 견적서 발송하기 추가해줘"
    - "내일 오후 2시 미팅 잡아줘"
    - "업무 현황 알려줘"
    - "우선순위 정해줘"
    """
    logger.info(f"자연어 명령: {request.command}")

    try:
        service = get_assistant_service()

        result = await service.process_natural_command(
            command=request.command,
            context=request.context
        )

        return NaturalCommandResponse(
            request_id=result["request_id"],
            parsed=ParsedCommand(
                command_type=result["parsed"]["command_type"],
                confidence=result["parsed"]["confidence"],
                parameters=result["parsed"]["parameters"],
                original_text=result["parsed"]["original_text"]
            ),
            result=result["result"],
            message=result["message"],
            suggestions=result.get("suggestions", [])
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Analysis Endpoints
# ============================================================================

@router.get(
    "/summary",
    response_model=DailySummary,
    summary="일일 요약",
    description="오늘의 업무 현황을 요약합니다."
)
async def get_daily_summary(target_date: Optional[date] = Query(None, description="대상 날짜")):
    """일일 요약 조회"""
    try:
        service = get_assistant_service()
        summary = await service.get_daily_summary(target_date)

        return DailySummary(
            date=summary["date"],
            greeting=summary["greeting"],
            tasks_completed=summary["tasks_completed"],
            tasks_remaining=summary["tasks_remaining"],
            tasks_overdue=summary["tasks_overdue"],
            schedules_today=summary["schedules_today"],
            next_schedule=ScheduleItem(**summary["next_schedule"]) if summary.get("next_schedule") else None,
            estimates_pending=summary.get("estimates_pending", 0),
            estimates_urgent=summary.get("estimates_urgent", 0),
            urgent_notifications=[NotificationItem(**n) for n in summary.get("urgent_notifications", [])],
            priority_tasks=[TaskItem(**t) for t in summary.get("priority_tasks", [])],
            insights=summary.get("insights", []),
            tips=summary.get("tips", [])
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/workload",
    response_model=WorkloadAnalysis,
    summary="업무량 분석",
    description="현재 업무량을 분석합니다."
)
async def analyze_workload():
    """업무량 분석"""
    try:
        service = get_assistant_service()
        analysis = await service.analyze_workload()

        return WorkloadAnalysis(**analysis)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/priorities",
    response_model=PrioritySuggestionResponse,
    summary="우선순위 제안",
    description="업무 우선순위를 제안합니다."
)
async def suggest_priorities():
    """우선순위 제안"""
    try:
        service = get_assistant_service()
        suggestions = await service.suggest_priorities()

        return PrioritySuggestionResponse(
            suggestions=[
                PrioritySuggestion(**s) for s in suggestions.get("suggestions", [])
            ],
            optimized_order=suggestions.get("optimized_order", []),
            rationale=suggestions.get("rationale", ""),
            estimated_efficiency_gain=suggestions.get("estimated_efficiency_gain", 0)
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Reminder Endpoints
# ============================================================================

@router.post(
    "/reminders",
    response_model=ReminderItem,
    status_code=status.HTTP_201_CREATED,
    summary="알림 설정",
    description="알림을 설정합니다."
)
async def create_reminder(request: ReminderRequest):
    """알림 설정"""
    logger.info(f"알림 설정 요청: {request.title}")

    try:
        service = get_assistant_service()

        reminder = await service.create_reminder(
            title=request.title,
            remind_at=request.remind_at,
            message=request.message,
            repeat=request.repeat,
            related_entity=request.related_entity
        )

        return _convert_reminder(reminder)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/reminders",
    summary="알림 목록",
    description="설정된 알림 목록을 조회합니다."
)
async def get_reminders(active_only: bool = Query(True, description="활성화된 알림만")):
    """알림 목록 조회"""
    try:
        service = get_assistant_service()
        reminders = await service.get_reminders(active_only=active_only)

        return {
            "reminders": [_convert_reminder(r) for r in reminders],
            "total": len(reminders)
        }

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Status Endpoint
# ============================================================================

@router.get(
    "/status",
    response_model=AssistantStatusResponse,
    summary="비서 상태",
    description="AI 비서의 현재 상태를 조회합니다."
)
async def get_assistant_status():
    """AI 비서 상태 조회"""
    try:
        service = get_assistant_service()
        status_info = service.get_status()

        return AssistantStatusResponse(**status_info)

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ============================================================================
# Quick Actions
# ============================================================================

@router.get(
    "/quick/today",
    summary="오늘의 업무",
    description="오늘 처리해야 할 업무를 빠르게 조회합니다."
)
async def get_today_work():
    """오늘의 업무 빠른 조회"""
    try:
        service = get_assistant_service()

        today = date.today()

        # 오늘 할 일
        tasks = await service.get_tasks(due_date=today)

        # 오늘 일정
        schedules = await service.get_schedules(start_date=today, end_date=today)

        # 읽지 않은 알림
        notifications = await service.get_notifications(unread_only=True)

        return {
            "date": today.isoformat(),
            "tasks": {
                "count": len(tasks),
                "urgent": sum(1 for t in tasks if t.priority == "URGENT"),
                "items": [_convert_task(t) for t in tasks[:5]]
            },
            "schedules": {
                "count": len(schedules),
                "items": [_convert_schedule(s) for s in schedules]
            },
            "notifications": {
                "unread": len(notifications),
                "items": [_convert_notification(n) for n in notifications[:3]]
            },
            "message": f"오늘 할 일 {len(tasks)}건, 일정 {len(schedules)}건이 있습니다."
        }

    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# timedelta import for ScheduleListResponse
from datetime import timedelta
