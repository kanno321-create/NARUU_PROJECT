"""NARUU FastAPI Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.routers import ai_chat, auth, content, customers, dashboard, expenses, goods, line_webhook, orders, packages, partners, reviews, tour_routes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="NARUU API",
    description="나루 종합 업무관리 시스템 — 의료관광·관광·굿즈·AI·LINE 통합",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS (must be last middleware added)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# --- Routers ---
app.include_router(auth.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(ai_chat.router, prefix="/api")
app.include_router(line_webhook.router, prefix="/api")
app.include_router(packages.router, prefix="/api")
app.include_router(tour_routes.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(content.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(partners.router, prefix="/api")
app.include_router(goods.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")


# --- Health Checks ---


@app.get("/health")
async def health():
    return {"status": "ok", "service": "naruu-api", "version": "0.1.0"}


@app.get("/health/db")
async def health_db():
    from sqlalchemy import text

    from app.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
