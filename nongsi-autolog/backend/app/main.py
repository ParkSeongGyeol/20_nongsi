from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import router
from app.api.sessions import router as sessions_router
from app.core.config import settings
from app.db.database import init_db, session_factory
from app.services.mqtt.subscriber import MQTTSubscriber
from app.services.event_detection import DeviceConfigRepository, StateDetectionService
from app.services.telemetry import TelemetryIngestor
from app.services.work_sessions import seed_demo_data
from app.services.container import work_session_service

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

device_configs = DeviceConfigRepository(settings.device_config_path)
state_detector = StateDetectionService(session_factory, device_configs)
ingestor = TelemetryIngestor(session_factory, state_detector)
mqtt_subscriber = MQTTSubscriber(settings, ingestor)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    del app
    init_db()
    seed_demo_data(session_factory)
    mqtt_subscriber.start()
    work_session_service.set_event_publisher(mqtt_subscriber.publish_json)
    logger.info("%s started", settings.app_name)
    try:
        yield
    finally:
        work_session_service.set_event_publisher(None)
        mqtt_subscriber.stop()
        logger.info("%s stopped", settings.app_name)


app = FastAPI(title=settings.app_name, version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(sessions_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}


@app.get("/health")
def health(response: Response) -> dict[str, str | bool]:
    database_ready = False
    try:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
        database_ready = True
    except Exception:
        logger.exception("Database health check failed")

    ready = database_ready and mqtt_subscriber.connected
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "ok" if ready else "degraded",
        "database": "ready" if database_ready else "unavailable",
        "mqtt_connected": mqtt_subscriber.connected,
    }
