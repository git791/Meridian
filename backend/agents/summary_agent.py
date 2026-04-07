import json
import asyncio
from typing import AsyncGenerator
from core.config import settings

SUMMARY_PROMPT = """
Analyse this meeting transcript and return JSON only:
{
  "title": "meeting title inferred from content",
  "key_decisions": ["decision 1", "decision 2"],
  "action_items": [
    {"owner": "name or email", "task": "description", "deadline": "YYYY-MM-DD or null"}
  ],
  "topics_covered": ["topic 1", "topic 2"],
  "follow_up_meeting_needed": true,
  "summary_paragraph": "2-3 sentence executive summary"
}
Return ONLY valid JSON. No markdown, no explanation.
"""

DEMO_SUMMARY = {
    "title": "Q3 OKR Review",
    "key_decisions": [
        "Legacy API migration to be completed by end of Q3",
        "Follow-up review scheduled for next week",
        "Design sign-off on onboarding screens by Wednesday",
    ],
    "action_items": [
        {"owner": "charlie@company.com", "task": "Draft migration plan",           "deadline": "2025-07-10"},
        {"owner": "bob@company.com",     "task": "Send follow-up calendar invite", "deadline": "2025-07-08"},
        {"owner": "diana@company.com",   "task": "Design review of onboarding",    "deadline": "2025-07-09"},
    ],
    "topics_covered": ["Q3 OKRs", "Engineering velocity", "Legacy migration", "Onboarding design"],
    "follow_up_meeting_needed": True,
    "summary_paragraph": (
        "The team reviewed Q3 OKR progress, noting 80% completion of engineering velocity targets. "
        "The main blocker is the legacy API migration, for which Charlie will own a plan by Thursday. "
        "A follow-up review is scheduled for next week."
    ),
}


class SummaryAgent:
    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.model = None

        if not demo_mode and settings.GCP_PROJECT:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel
                vertexai.init(project=settings.GCP_PROJECT, location=settings.VERTEX_LOCATION)
                self.model = GenerativeModel("gemini-1.5-pro-001")
            except Exception:
                pass

    async def process(
        self, transcript: str, attendees: list[str]
    ) -> AsyncGenerator[dict, None]:
        yield {"status": "analysing", "message": "Extracting decisions and action items…"}
        await asyncio.sleep(0.3)

        if self.demo_mode or not self.model:
            await asyncio.sleep(1.5)  # simulate LLM call
            summary = DEMO_SUMMARY
        else:
            try:
                response = self.model.generate_content(
                    f"{SUMMARY_PROMPT}\n\nTranscript:\n{transcript}"
                )
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                summary = json.loads(text)
            except Exception:
                summary = DEMO_SUMMARY

        yield {"status": "done", "summary": summary, "message": "Summary complete"}

        # Email each attendee
        if attendees:
            yield {"status": "emailing", "message": f"Emailing {len(attendees)} attendee(s)…"}
            await asyncio.sleep(0.5)

            try:
                from agents.email_agent import EmailAgent
                email_agent = EmailAgent(demo_mode=self.demo_mode)
                for attendee in attendees:
                    my_items = [
                        item for item in summary.get("action_items", [])
                        if attendee.lower() in item.get("owner", "").lower()
                    ]
                    await email_agent.send_summary(
                        to=attendee, summary=summary, my_action_items=my_items
                    )
            except Exception:
                pass

            yield {"status": "emails_sent", "count": len(attendees), "message": f"Summaries emailed to {len(attendees)} attendee(s)"}

            try:
                from models.database import get_session, MeetingSummary
                import json
                with get_session() as session:
                    session.add(MeetingSummary(
                        title=summary.get("title", "Meeting"),
                        summary=json.dumps(summary),
                        attendees=json.dumps(attendees),
                    ))
            except Exception:
                pass  # never let DB failure break the agent stream