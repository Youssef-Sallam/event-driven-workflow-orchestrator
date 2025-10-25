import httpx
from typing import Dict, Any
import asyncio

class OrderServiceStub:
    async def reconcile(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate API call to in-house order service
        await asyncio.sleep(0.1) # Latency

        # Mock reconciliation: sum quantities, validate
        total_orders - sum(item['qty'] for item in order_data.get('items', []))
        return {
            "status": "reconciled",
            "total": total_orders,
            "sku_summary": {
                item['sku']: item['qty'] for item in order_data.get('items', []) if 'sku' in item
            }
        }
        