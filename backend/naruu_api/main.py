"""NARUU AI Platform — FastAPI 엔트리포인트."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from naruu_api.deps import get_naruu_settings, get_plugin_manager
from naruu_api.routes import health, plugins

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """앱 시작/종료 시 플러그인 자동 디스커버리."""
    settings = get_naruu_settings()
    pm = get_plugin_manager()

    if settings.auto_discover_plugins:
        plugin_dir = Path(__file__).parent.parent / settings.plugin_dir
        discovered = await pm.discover(plugin_dir)
        logger.info(
            "플러그인 디스커버리 완료: %d개 로드 (%s)",
            len(discovered),
            ", ".join(p.name for p in discovered) or "없음",
        )

    logger.info(
        "%s v%s 시작 — 플러그인 %d개 등록",
        settings.app_name,
        settings.app_version,
        pm.count,
    )

    yield

    # shutdown
    for info in pm.list_plugins():
        plugin = pm.get(info.name)
        if plugin:
            await plugin.shutdown()
    logger.info("서버 종료. 모든 플러그인 정리 완료.")


def create_app() -> FastAPI:
    """FastAPI 앱 팩토리."""
    settings = get_naruu_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(plugins.router, prefix=settings.api_prefix)

    return app


app = create_app()
