import pytest
from main import WorkflowEngine, Event
from stubs.order_service import OrderServiceStub
from unittest.mock import AsyncMock, patch

@pytest.fixture
def engine():
    return WorkflowEngine()

@pytest.mark.asyncio
async def test_execute_reconcile(engine):
    event = Event(
        type="order", 
        data={
            "items": [
                {
                    "sku": "SKU1",
                    "qty": 5
                }
            ]
        },
        workflow_id="test"
    )
    event.workflow = {
        "nodes": [
            {
                "id": "reconcile",
                "type": "reconcile_orders"
            }
        ],
        "edges": []
    }
    with patch.object(OrderServiceStub, "reconcile", new_callable=AsyncMock) as mock_reconcile:
        mock_reconcile.return_value = {"status": "ok"}
        await engine.execute(event)
        assert "reconcile" in [step["step"] for step in engine.active_runs[list(engine.active_runs)[0]]["steps"]]

# More tests: error handling, retries, branches, coverage >70%
# Run: pytest --cov=.