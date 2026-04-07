import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from agents.orchestrator import OrchestratorAgent

@pytest.fixture
def orchestrator():
    # Patch the actual classes inside the agents module
    with patch("agents.calendar_agent.CalendarAgent"), \
         patch("agents.email_agent.EmailAgent"), \
         patch("agents.transcription_agent.TranscriptionAgent"), \
         patch("agents.summary_agent.SummaryAgent"):
        return OrchestratorAgent(user_token="fake-token", demo_mode=True)

@pytest.mark.asyncio
async def test_schedule_intent_calls_calendar_then_email(orchestrator):
    mock_response = MagicMock()
    mock_response.text = '{"intent":"schedule","attendees":["a@b.com"],"duration_minutes":60,"preferred_time":"Tuesday","meeting_title":"Sync","notes":""}'

    orchestrator.model = MagicMock()
    orchestrator.model.generate_content.return_value = mock_response
    orchestrator.calendar.find_slots = MagicMock(return_value=aiter([{"status":"found","slots":[]}]))
    orchestrator.email.send_invite = MagicMock(return_value=aiter([{"status":"sent"}]))

    events = []
    async for e in orchestrator.run("Schedule a meeting with a@b.com on Tuesday"):
        events.append(e)

    agents_activated = [e["agent"] for e in events]
    assert "calendar_agent" in agents_activated
    assert "email_agent" in agents_activated

@pytest.mark.asyncio
async def test_summarise_intent_calls_transcription_then_summary(orchestrator):
    mock_response = MagicMock()
    mock_response.text = '{"intent":"summarise","attendees":["a@b.com"],"duration_minutes":0,"preferred_time":"","meeting_title":null,"notes":""}'

    orchestrator.model = MagicMock()
    orchestrator.model.generate_content.return_value = mock_response
    orchestrator.transcription.transcribe = AsyncMock(return_value="Meeting about Q3 planning...")
    orchestrator.summary.process = MagicMock(return_value=aiter([{"status":"done"}]))

    events = []
    async for e in orchestrator.run("Summarise this meeting", audio_file="test.mp3"):
        events.append(e)

    agents_activated = [e["agent"] for e in events]
    assert "transcription_agent" in agents_activated

# helper for async iteration in tests
async def aiter(items):
    for item in items:
        yield item