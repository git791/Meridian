from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
from datetime import datetime, timedelta
from pydantic import BaseModel

from api.auth import get_current_user, get_demo_user
from core.config import settings

router = APIRouter()

# Schema for the confirmation request
class ConfirmRequest(BaseModel):
    slot: dict
    title: str
    attendees: List[str]

def _get_user(demo: bool = Query(False)):
    """Allow demo mode without OAuth."""
    if demo or settings.DEMO_MODE:
        return get_demo_user()
    return None 

@router.post("/schedule")
async def schedule(
    request: dict,
    demo: bool = Query(False),
):
    """
    SSE endpoint — streams multi-agent events to the UI.
    """
    from agents.orchestrator import OrchestratorAgent

    user_token = request.get("token") or (settings.DEMO_TOKEN if (demo or settings.DEMO_MODE) else None)
    if not user_token and not (demo or settings.DEMO_MODE):
        raise HTTPException(status_code=401, detail="Authentication required")

    agent = OrchestratorAgent(user_token=user_token, demo_mode=(demo or settings.DEMO_MODE))

    async def event_stream():
        try:
            async for event in agent.run(
                user_message=request.get("message", ""),
                audio_file=request.get("audio_file"),
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'agent': 'orchestrator', 'status': 'error', 'message': str(e)})}\n\n"
        yield 'data: {"agent": "done"}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

from api.auth import get_current_user, get_demo_user, oauth2_scheme

# --- NEW ENDPOINT TO FIX YOUR BUTTON ---
@router.post("/calendar/confirm")
async def confirm_calendar_slot(data: ConfirmRequest, demo: bool = Query(False), token: str = Depends(oauth2_scheme)):
    """Receives the confirmed slot from the UI and saves it to the DB."""
    from agents.calendar_agent import CalendarAgent
    
    try:
        is_demo = demo or settings.DEMO_MODE
        agent = CalendarAgent(user_token=None if is_demo else token, demo_mode=is_demo)
        
        result = agent.create_event(
            title=data.title,
            slot=data.slot,
            attendees=data.attendees
        )

        # Trigger invitations after confirmation
        from agents.email_agent import EmailAgent
        email_agent = EmailAgent(user_token=None if is_demo else token, demo_mode=is_demo)
        async for _ in email_agent.send_invite(data.model_dump()):
            pass # Consume the generator
        
        return {"status": "success", "event": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database save failed: {str(e)}")

@router.get("/events")
async def list_events(
    timeMin: str = Query(default=None),
    timeMax: str = Query(default=None),
    demo: bool = Query(False),
    token: str = Depends(oauth2_scheme)
):
    """
    Returns events for the calendar. 
    In Demo mode, merges hardcoded events with real database records.
    """
    is_demo = demo or settings.DEMO_MODE
    if is_demo:
        # Start with hardcoded demo data
        events = _demo_events()
        
        # Incorporate real confirmed meetings from our DB
        from models.database import get_session, Meeting
        try:
            with get_session() as session:
                db_meetings = session.query(Meeting).all()
                for m in db_meetings:
                    events.append({
                        "summary": m.title, # UI expects 'summary' or 'title'
                        "title": m.title,
                        "start": {"dateTime": m.start_time.isoformat() if m.start_time else ""},
                        "end": {"dateTime": m.end_time.isoformat() if m.end_time else ""},
                        "status": m.status,
                        "color": "#3de8a0" if m.status == "confirmed" else "#4db8ff"
                    })
        except Exception:
            pass # Graceful fallback to just demo events if DB is sleepy
            
        return events

    # --- REAL GOOGLE CALENDAR PATH ---
    from agents.calendar_agent import CalendarAgent

    try:
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required for live calendar")
            
        agent = CalendarAgent(user_token=token, demo_mode=False)

        now = datetime.utcnow()
        t_min = timeMin or now.isoformat() + "Z"
        t_max = timeMax or (now + timedelta(days=7)).isoformat() + "Z"

        events = agent.service.events().list(
            calendarId="primary",
            timeMin=t_min,
            timeMax=t_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        return events.get("items", [])
    except Exception:
        return _demo_events() # Last resort fallback

@router.get("/summaries")
async def list_summaries(demo: bool = Query(False)):
    from models.database import get_session, MeetingSummary
    import json

    if demo or settings.DEMO_MODE:
        return _demo_summaries()

    with get_session() as session:
        meetings = session.query(MeetingSummary).order_by(MeetingSummary.id.desc()).limit(20).all()
        return [
            {
                "id": m.id, 
                "title": m.title, 
                **json.loads(m.summary if m.summary else "{}")
            } for m in meetings
        ]

def _demo_events():
    now = datetime.utcnow()
    return [
        {
            "summary": "Design Review",
            "start": {"dateTime": (now + timedelta(hours=1)).isoformat() + "Z"},
            "end":   {"dateTime": (now + timedelta(hours=2)).isoformat() + "Z"},
        },
        {
            "summary": "Q3 Planning",
            "start": {"dateTime": (now + timedelta(days=1, hours=2)).isoformat() + "Z"},
            "end":   {"dateTime": (now + timedelta(days=1, hours=4)).isoformat() + "Z"},
        },
    ]

def _demo_summaries():
    return [
        {
            "title": "Q3 Planning Session",
            "summary_paragraph": "The team aligned on Q3 OKRs...",
            "key_decisions": ["Ship onboarding v2", "Defer legacy migration"],
            "action_items": [
                {"owner": "alice@company.com", "task": "Draft spec", "deadline": "2025-07-10"},
            ],
            "topics_covered": ["OKRs", "Onboarding"],
            "follow_up_meeting_needed": True,
        }
    ]