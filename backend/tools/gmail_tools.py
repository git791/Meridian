import pytest
from agents.email_agent import EmailAgent

@pytest.mark.asyncio
async def test_email_agent_demo_mode():
    agent = EmailAgent(demo_mode=True)
    events = []
    async for event in agent.send_invite({"attendees": ["test@test.com"]}):
        events.append(event)
    assert any(e["status"] == "sent" for e in events)