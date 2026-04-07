from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def background_reminder_task():
    """Background loop to send meeting reminders."""
    from models.database import get_session, Meeting
    from agents.email_agent import EmailAgent
    from datetime import datetime, timedelta
    import json

    logger.info("Starting background reminder task…")
    email_agent = EmailAgent(demo_mode=settings.DEMO_MODE)

    while True:
        try:
            now = datetime.utcnow()
            with get_session() as session:
                # Find confirmed meetings starting in the next 24 hours
                target_time = now + timedelta(hours=25)
                upcoming = session.query(Meeting).filter(
                    Meeting.status == "confirmed",
                    Meeting.start_time > now,
                    Meeting.start_time < target_time
                ).all()

                for meeting in upcoming:
                    sent = json.loads(meeting.reminders_sent or "[]")
                    diff = meeting.start_time - now
                    
                    attendees = json.loads(meeting.attendees or "[]")

                    # 1 Day Reminder
                    if "1d" not in sent and timedelta(hours=23) < diff <= timedelta(hours=24):
                        await email_agent.send_reminder(attendees, meeting.title, meeting.start_time.isoformat(), "1 day")
                        sent.append("1d")
                    
                    # 1 Hour Reminder
                    if "1h" not in sent and timedelta(minutes=55) < diff <= timedelta(hours=1, minutes=5):
                        await email_agent.send_reminder(attendees, meeting.title, meeting.start_time.isoformat(), "1 hour")
                        sent.append("1h")

                    meeting.reminders_sent = json.dumps(sent)

        except Exception as e:
            logger.error(f"Reminder task error: {e}")
        
        await asyncio.sleep(60) # Check every minute

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Meridian starting up — demo_mode=%s", settings.DEMO_MODE)
    import asyncio
    reminder_task = asyncio.create_task(background_reminder_task())
    yield
    reminder_task.cancel()
    logger.info("Meridian shutting down")


app = FastAPI(
    title="Meridian — Smart Meeting Scheduler",
    version="1.0.0",
    description="Multi-agent AI scheduling powered by Google Cloud & Gemini",
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_timing(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{(time.perf_counter() - start):.4f}s"
    return response

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["ops"])
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
    }


@app.get("/api/v1/config", tags=["ops"])
async def public_config():
    """Returns non-sensitive config the frontend needs."""
    return {
        "demo_mode": settings.DEMO_MODE,
        "google_client_id": settings.GOOGLE_CLIENT_ID,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )