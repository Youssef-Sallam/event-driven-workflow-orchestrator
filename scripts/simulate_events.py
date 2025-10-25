import asyncio
import json
import random
from faker import Faker
from main import Event
import requests
import argparse

fake = Faker()
wf_id = "post_flash_sale" # From template

async def simulate_event():
    items = [
        {
            "sku": f"SKU{random.randint(1, 100)}",
            "qty": random.randint(1,10)
        } for _ in range(random.randint(1,5))        
    ]
    event = Event(
        type="order_event",
        data={
            "order_id": fake.uuid4(),
            "items": items,
            "customer_id": "[REDACTED]"
        }, # No real PII
        workflow_id=wf_id
    )
    requests.post("http://localhost:8000/publish_event", json=event.dict())

async def main(rate: int):
    while True:
        tasks = [simulate_event() for _ in range(rate // 60)] # Per minute / 60 for per sec
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=int, default=1000)
    args = parser.parse_args()
    asyncio.run(main(args.rate))