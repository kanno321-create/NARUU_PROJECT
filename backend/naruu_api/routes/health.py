"""헬스 체크 라우터."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from naruu_api.deps import get_naruu_settings, get_plugin_manager
from naruu_core.config import NaruuSettings
from naruu_core.db import get_database
from naruu_core.plugin_manager import PluginManager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    settings: NaruuSettings = Depends(get_naruu_settings),
    pm: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """서버 상태 확인. DB 설정 시 연결 상태 포함."""
    result: dict = {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "plugins_count": pm.count,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    if settings.database_url:
        try:
            db = get_database()
            result["db_status"] = "connected" if await db.test_connection() else "disconnected"
        except RuntimeError:
            result["db_status"] = "not_initialized"
    else:
        result["db_status"] = "not_configured"

    return result
