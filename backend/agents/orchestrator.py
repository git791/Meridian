import json
import asyncio
from typing import AsyncGenerator
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from core.config import settings

vertexai.init(project=settings.GCP_PROJECT, location=settings.VERTEX_LOCATION)

ROUTING_PROMPT = """
You are a meeting scheduling orchestrator. Parse the user's request and return JSON only:
{
  "intent": "schedule|reschedule|transcribe|summarise|cancel|query",
  "attendees": ["email1@example.com"],
  "duration_minutes": 60,
  "preferred_time": "next Tuesday afternoon",
  "meeting_title": "string or null",
  "notes": "any extra context"
}

Rules:
- intent must be exactly one of: schedule, reschedule, transcribe, summarise, cancel, query
- attendees: extract email addresses, default to []
- duration_minutes: extract number, default to 60
- preferred_time: natural language, default to "next available"
- Return ONLY valid JSON. No markdown, no explanation.
"""

DEMO_RESPONSES = {
    "schedule": {
        "intent": "schedule",
        "attendees": ["alice@company.com", "bob@company.com"],
        "duration_minutes": 60,
        "preferred_time": "next Tuesday afternoon",
        "meeting_title": "Team Sync",
        "notes": "Demo mode",
    },
    "summarise": {
        "intent": "summarise",
        "attendees": ["alice@company.com"],
        "duration_minutes": 0,
        "preferred_time": "",
        "meeting_title": None,
        "notes": "Demo mode",
    },
}


class OrchestratorAgent:
    def __init__(self, user_token: str | None, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.user_token = user_token

        if settings.GCP_PROJECT:
            self.model = GenerativeModel("gemini-1.5-pro-001")
        else:
            self.model = None

        # Lazy import agents to avoid import errors if deps missing
        self._init_agents()

    def _init_agents(self):
        try:
            from agents.calendar_agent import CalendarAgent
            from agents.email_agent import EmailAgent
            from agents.transcription_agent import TranscriptionAgent
            from agents.summary_agent import SummaryAgent

            self.calendar = CalendarAgent(user_token=self.user_token, demo_mode=self.demo_mode)
            self.email = EmailAgent(user_token=self.user_token, demo_mode=self.demo_mode)
            self.transcription = TranscriptionAgent(demo_mode=self.demo_mode)
            self.summary = SummaryAgent(demo_mode=self.demo_mode)
        except Exception as e:
            # Graceful degradation — agents fail individually
            self.calendar = None
            self.email = None
            self.transcription = None
            self.summary = None

    async def _parse_intent(self, user_message: str) -> dict:
        if self.demo_mode or not self.model:
            # Heuristic routing for demo
            msg = user_message.lower()
            import re
            emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', user_message)
            
            if any(w in msg for w in ["summar", "transcript", "record", "action item"]):
                resp = DEMO_RESPONSES["summarise"].copy()
                if emails: resp["attendees"] = emails
                return resp
                
            resp = DEMO_RESPONSES["schedule"].copy()
            if emails: 
                # Use extracted emails
                resp["attendees"] = emails
            return resp

        try:
            from models.schemas import IntentSchema
            response = self.model.generate_content(
                f"{ROUTING_PROMPT}\n\nUser request: {user_message}",
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=IntentSchema.model_json_schema() if hasattr(IntentSchema, "model_json_schema") else IntentSchema.schema(),
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Orchestrator fallback due to error: {e}")
            # Fallback
            return DEMO_RESPONSES["schedule"]

    async def run(
        self, user_message: str, audio_file: str | None = None
    ) -> AsyncGenerator[dict, None]:
        # Step 1: Parse intent
        yield {"agent": "orchestrator", "status": "thinking", "message": "Parsing your request…"}
        intent_data = await self._parse_intent(user_message)
        yield {"agent": "orchestrator", "status": "parsed", "data": intent_data}

        intent = intent_data.get("intent", "schedule")

        if intent == "schedule":
            yield {"agent": "orchestrator", "status": "routing", "message": "Routing to Calendar Agent"}

            if self.calendar:
                async for event in self.calendar.find_slots(
                    attendees=intent_data.get("attendees", []),
                    duration=intent_data.get("duration_minutes", 60),
                    preference=intent_data.get("preferred_time", "next available"),
                ):
                    yield {"agent": "calendar_agent", **event}

            yield {"agent": "orchestrator", "status": "routing", "message": "Routing to Email Agent"}

            if self.email:
                async for event in self.email.send_invite(intent_data):
                    yield {"agent": "email_agent", **event}

        elif intent in ("summarise", "transcribe"):
            yield {"agent": "orchestrator", "status": "routing", "message": "Routing to Transcription Agent"}

            transcript = ""
            if self.transcription:
                transcript = await self.transcription.transcribe(audio_file or "")
                yield {
                    "agent": "transcription_agent",
                    "status": "done",
                    "chars": len(transcript),
                    "message": f"Transcribed {len(transcript):,} characters",
                }

            yield {"agent": "orchestrator", "status": "routing", "message": "Routing to Summary Agent"}

            if self.summary:
                async for event in self.summary.process(
                    transcript=transcript,
                    attendees=intent_data.get("attendees", []),
                ):
                    yield {"agent": "summary_agent", **event}

        elif intent == "reschedule":
            yield {"agent": "orchestrator", "status": "info", "message": "Reschedule flow: finding new slots…"}
            if self.calendar:
                async for event in self.calendar.find_slots(
                    attendees=intent_data.get("attendees", []),
                    duration=intent_data.get("duration_minutes", 60),
                    preference=intent_data.get("preferred_time", "next available"),
                ):
                    yield {"agent": "calendar_agent", **event}

        elif intent == "cancel":
            yield {"agent": "orchestrator", "status": "info", "message": "Cancellation flow initiated"}
            if self.email:
                async for event in self.email.send_cancellation(intent_data):
                    yield {"agent": "email_agent", **event}

        else:
            yield {"agent": "orchestrator", "status": "unsupported", "message": f"Intent '{intent}' not yet supported"}

        yield {"agent": "orchestrator", "status": "complete", "message": "All agents finished"}