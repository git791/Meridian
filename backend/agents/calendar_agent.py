import json
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator
from core.config import settings

DEMO_SLOTS = [
    {
        "start": (datetime.utcnow() + timedelta(days=1, hours=9)).isoformat(),
        "end":   (datetime.utcnow() + timedelta(days=1, hours=10)).isoformat(),
    },
    {
        "start": (datetime.utcnow() + timedelta(days=2, hours=14)).isoformat(),
        "end":   (datetime.utcnow() + timedelta(days=2, hours=15)).isoformat(),
    },
    {
        "start": (datetime.utcnow() + timedelta(days=3, hours=10)).isoformat(),
        "end":   (datetime.utcnow() + timedelta(days=3, hours=11)).isoformat(),
    },
]


class CalendarAgent:
    def __init__(self, user_token: str | None, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.service = None
        self.model = None

        if not demo_mode and user_token:
            try:
                from googleapiclient.discovery import build
                from google.oauth2.credentials import Credentials
                import vertexai
                from vertexai.generative_models import GenerativeModel

                vertexai.init(project=settings.GCP_PROJECT, location=settings.VERTEX_LOCATION)
                creds = Credentials(token=user_token)
                self.service = build("calendar", "v3", credentials=creds)
                self.model = GenerativeModel("gemini-1.5-pro-001")
            except Exception:
                pass  # graceful degradation

    def _get_busy_times(self, attendees: list[str], start: datetime, end: datetime) -> dict:
        if not self.service:
            return {}
        body = {
            "timeMin": start.isoformat() + "Z",
            "timeMax": end.isoformat() + "Z",
            "items": [{"id": email} for email in attendees],
        }
        result = self.service.freebusy().query(body=body).execute()
        return result.get("calendars", {})

    async def find_slots(
        self, attendees: list[str], duration: int, preference: str
    ) -> AsyncGenerator[dict, None]:
        yield {"status": "searching", "message": f"Checking calendars for {len(attendees)} attendee(s)…"}
        await asyncio.sleep(0.1)  # allow SSE flush

        if self.demo_mode or not self.service:
            await asyncio.sleep(0.8)  # simulate network

            # Generate dynamic slots relative to now
            now = datetime.utcnow()
            dynamic_slots = [
                {
                    "start": (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0).isoformat() + "Z",
                    "end":   (now + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0).isoformat() + "Z",
                },
                {
                    "start": (now + timedelta(days=2)).replace(hour=14, minute=0, second=0, microsecond=0).isoformat() + "Z",
                    "end":   (now + timedelta(days=2)).replace(hour=15, minute=0, second=0, microsecond=0).isoformat() + "Z",
                },
            ]

            yield {"status": "found", "slots": dynamic_slots, "message": f"Found {len(dynamic_slots)} available slots"}
            return

        # Real path
        now = datetime.utcnow()
        window = {"start": now.isoformat(), "end": (now + timedelta(days=7)).isoformat()}

        if self.model:
            try:
                resp = self.model.generate_content(
                    f"Today is {now.strftime('%A %B %d %Y')}. "
                    f"Return ISO 8601 start/end for search window: '{preference}'. "
                    f"JSON only: {{\"start\": \"...\", \"end\": \"...\"}}"
                )
                window = json.loads(resp.text)
            except Exception:
                pass

        start = datetime.fromisoformat(window["start"].replace("Z", ""))
        end = datetime.fromisoformat(window["end"].replace("Z", ""))
        busy = self._get_busy_times(attendees, start, end)

        slots = []
        cursor = start
        while cursor < end and len(slots) < 3:
            slot_end = cursor + timedelta(minutes=duration)
            is_free = all(
                not any(
                    datetime.fromisoformat(b["start"].replace("Z", "")) < slot_end
                    and datetime.fromisoformat(b["end"].replace("Z", "")) > cursor
                    for b in busy.get(email, {}).get("busy", [])
                )
                for email in attendees
            )
            if is_free:
                slots.append({"start": cursor.isoformat(), "end": slot_end.isoformat()})
            cursor += timedelta(minutes=30)

        yield {"status": "found", "slots": slots, "message": f"Found {len(slots)} available slot(s)"}

    def create_event(self, title: str, slot: dict, attendees: list[str], description: str = "") -> dict:
        event_dict = {"id": "demo-event-001", "htmlLink": "#", "status": "confirmed"}

        if not self.demo_mode and self.service:
            event = {
                "summary": title,
                "description": description,
                "start": {"dateTime": slot["start"], "timeZone": "UTC"},
                "end":   {"dateTime": slot["end"],   "timeZone": "UTC"},
                "attendees": [{"email": e} for e in attendees],
                "conferenceData": {
                    "createRequest": {"requestId": f"meet-{slot['start']}"}
                },
            }
            event_dict = self.service.events().insert(
                calendarId="primary",
                body=event,
                conferenceDataVersion=1,
                sendUpdates="all",
            ).execute()

        try:
            from models.database import get_session, Meeting
            from datetime import datetime
            import json

            start_dt = datetime.fromisoformat(slot["start"].replace("Z", ""))
            end_dt = datetime.fromisoformat(slot["end"].replace("Z", ""))

            with get_session() as session:
                new_meeting = Meeting(
                    title=title,
                    start_time=start_dt,
                    end_time=end_dt,
                    attendees=json.dumps(attendees),
                    status="confirmed"
                )
                session.add(new_meeting)
        except Exception as e:
            print(f"Failed to save meeting to DB: {e}")

        return event_dict