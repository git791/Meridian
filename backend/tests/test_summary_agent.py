import pytest
from agents.summary_agent import SummaryAgent

@pytest.mark.asyncio
async def test_summary_processing():
    agent = SummaryAgent(demo_mode=True)
    events = []
    async for event in agent.process("Test transcript", ["alice@test.com"]):
        events.append(event)
    assert any(e["status"] == "done" for e in events)