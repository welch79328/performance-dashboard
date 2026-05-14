import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.engine import engine, async_session
from app.db.tables import Base
from app.routers import auth, workload, efficiency, schedule, quality, sync, export

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables + seed users
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    async with async_session() as session:
        from app.services.user_service import seed_default_users
        await seed_default_users(session)
        logger.info("Default users seeded")

    # Run initial sync
    try:
        async with async_session() as session:
            from app.routers.data_deps import get_monday_service
            from app.services.sync_service import sync_monday_to_db
            svc = get_monday_service()
            result = await sync_monday_to_db(session, svc)
            logger.info(f"Initial sync: {result['work_orders']} work orders, {result['campaigns']} campaigns")
    except Exception as e:
        logger.warning(f"Initial sync failed (will retry on first request): {e}")

    yield

    await engine.dispose()


app = FastAPI(
    title="績效管理平台 API",
    description="串接 Monday.com，四大維度績效評估：工作量、流程效率、專案排程、品質指標",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost", "http://localhost:80", "http://localhost:8088"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workload.router)
app.include_router(efficiency.router)
app.include_router(schedule.router)
app.include_router(quality.router)
app.include_router(sync.router)
app.include_router(export.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.2.0"}
