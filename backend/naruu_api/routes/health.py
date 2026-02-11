"""헬스 체크 라우터."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from naruu_api.deps import get_naruu_settings, get_plugin_manager
from naruu_core.config import NaruuSettings
from naruu_core.plugin_manager import PluginManager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    settings: NaruuSettings = Depends(get_naruu_settings),
    pm: PluginManager = Depends(get_plugin_manager),
) -> dict:
    """서버 상태 확인."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "plugins_count": pm.count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
