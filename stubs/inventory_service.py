import httpx
from typing import Dict, Any, List
import asyncio
import random

class InventoryServiceStub:
    # Mock inventory state
    _inventory = {f"SKU{i}": random.randint(5,50) for i in range(1,101)} # 100 SKUs

    async def check_restock(self, sku_summary: Dict[str, int]) -> List[str]:
        low_skus = []
        for sku, qty in sku_summary.items():
            self._inventory[sku] = self._inventory.get(sku, 50) - qty
            if self._inventory[sku] < 10: # Threshold
                low_skus.append(sku)

                # Trigger restock (simulate)
                await self._restock(sku)
        return low_skus
    
    async def _restock(self, sku: str):
        await asyncio.sleep(0.5)
        self._inventory[sku] += 100 # Restock amount