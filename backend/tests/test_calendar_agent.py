import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from agents.calendar_agent import CalendarAgent

@pytest.fixture
def agent():
    # Patch where 'build' is actually defined in the library
    with patch("googleapiclient.discovery.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield CalendarAgent(user_token="fake-token", demo_mode=False), mock_service

@pytest.mark.asyncio
async def test_find_slots_returns_top_3(agent):
    cal_agent, mock_service = agent
    mock_service.freebusy().query().execute.return_value = {
        "calendars": {
            "alice@test.com": {"busy": []},
            "bob@test.com": {"busy": []}
        }
    }
    with patch.object(cal_agent.model, "generate_content") as mock_gemini:
        mock_gemini.return_value.text = '{"start":"2025-05-12T09:00:00","end":"2025-05-12T18:00:00"}'
        events = []
        async for event in cal_agent.find_slots(
            attendees=["alice@test.com", "bob@test.com"],
            duration=60,
            preference="Monday morning"
        ):
            events.append(event)
    slot_events = [e for e in events if e.get("status") == "found"]
    assert len(slot_events) == 1
    assert len(slot_events[0]["slots"]) <= 3

@pytest.mark.asyncio
async def test_find_slots_respects_busy_times(agent):
    cal_agent, mock_service = agent
    mock_service.freebusy().query().execute.return_value = {
        "calendars": {
            "alice@test.com": {"busy": [
                {"start": "2025-05-12T09:00:00", "end": "2025-05-12T17:00:00"}
            ]}
        }
    }
    with patch.object(cal_agent.model, "generate_content") as mock_gemini:
        mock_gemini.return_value.text = '{"start":"2025-05-12T09:00:00","end":"2025-05-12T12:00:00"}'
        events = []
        async for event in cal_agent.find_slots(
            attendees=["alice@test.com"],
            duration=60,
            preference="Monday morning"
        ):
            events.append(event)
    slot_events = [e for e in events if e.get("status") == "found"]
    assert slot_events[0]["slots"] == []

def test_create_event_calls_api(agent):
    cal_agent, mock_service = agent
    mock_service.events.return_value.insert.return_value.execute.return_value = {"id": "abc123"}
    result = cal_agent.create_event(
        title="Q3 Planning",
        slot={"start": "2025-05-12T10:00:00", "end": "2025-05-12T11:00:00"},
        attendees=["alice@test.com", "bob@test.com"]
    )
    assert result["id"] == "abc123"
    mock_service.events().insert.assert_called_once()