import pytest
from unittest.mock import patch, MagicMock

from runtime.engine import AgentEngine


@pytest.mark.asyncio
async def test_engine_initialize():

    fake_agent = MagicMock()

    with patch("agents.factory.AgentFactory.create_agent", return_value=fake_agent), \
         patch("tools.loader.load_all_tools"), \
         patch("runtime.piflow_engine.registry") as fake_registry:

        fake_registry.list_records.return_value = []

        engine = AgentEngine()

        await engine.initialize()

        assert engine.agent is fake_agent
        