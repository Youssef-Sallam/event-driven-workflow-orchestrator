from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
import redis.asyncio as redis
from pydantic import BaseModel
from typing import List, Dict, Any
import yaml
from stubs.order_service import OrderServiceStub
from stubs.inventory_service import InventoryServiceStub
from logger import SecureLogger
import uuid

app = FastAPI()
redis_client = None
order_stub = OrderServiceStub()
inventory_stub = InventoryServiceStub()
logger = SecureLogger()
connected_clients: List[WebSocket] = []

class Workflow(BaseModel):
    id: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class Event(BaseModel):
    type: str
    data: Dict[str, Any]
    workflow_id: str

# Custom Workflow Engine (Simple FSM)
class WorkflowEngine:
    def __init__(self):
        self.active_runs: Dict[str, Dict[str, Any]] = {} # run_id -> state
    
    async def execute(self, event: Event):
        run_id = str(uuid.uuid4())
        self.active_runs[run_id] = {"state": "start", "data": event.data, "steps": []}
        await self._process_step(run_id, "start")
    
    async def _process_step(self, run_id: str, current_node: str):
        state = self.active_runs[run_id]
        node = next((n for n in state["workflow"]["nodes"] if n["id"] == current_node), None)
        if not node:
            state["state"] = "completed"
            await self._notify_dashboard(run_id, "completed")
            return

        try:
            if node["type"] == "reconcile_orders":
                result = await order_stub.reconcile(state["data"])
                state["steps"].append({"step": node["id"], "result": result})
                logger.info(f"Reconciled orders for run {run_id}", extra={"run_id": run_id, "step": node["id"]})
                next_node = self._get_next_node(state["workflow"]["edges"], node["id"])
                await self._process_step(run_id, next_node)
            
            elif node["type"] == "restocke_check":
                low_skus = await inventory_stub.check_restock(state["data"])
                state["steps"].append({"step": node["id"], "low_skus": low_skus})
                if low_skus:
                    await self._trigger_alert(run_id, low_skus)
                    logger.warning(f"Low inventory alert for {len(low_skus)} SKUs in run {run_id}", extra={"run_id": run_id})
                
                next_node = self._get_next_node(state["workflow"]["edges"], node["id"], condition="low_inventory" if low_skus else "ok")
                await self._process_step(run_id, next_node)
            
            # Add more node types: decision, paraller (asyncio.gather), retry (loop with backoff)
        
        except Exception as e:
            state["state"] = "failed"
            logger.error(f"Error in step {node["id"]} for run {run_id}: {str(e)}")

            # Retry logic: up tp 3 attempts
            if state.get("retries", 0) < 3:
                state["retries"] = state.get("retries", 0) + 1
                await asyncio.sleep(2 ** state["retries"])
                await self._process_step(run_id, current_node)
            
            await self._notify_dashboard(run_id, "failed")

    def _get_next_node(self, edges: List[Dict], from_id: str, condition: str = None) -> str:
        edge = next((e for e in edges if e["from"] == from_id and (not condition or e.get("condition") == condition)), None)
        return edge["to"] if edge else None
    
    async def _trigger_alert(self, run_id: str, low_skus: List[str]):
        # Simulate alert (e.g., email/Slack)
        await self._notify_dashboard(run_id, "alert", {"low_skus": low_skus})

    async def _notify_dashboard(self, run_id: str, status: str, data: Dict = None):
        message = {"run_id": run_id, "status": status, "data": data}
        await redis_client.publish("dashboard_updates", json.dumps(message))

engine = WorkflowEngine()

# Redis setup
async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis.from_url("redis://localhost:6379")
    return redis_client

# Event ingestion (Pub/sub subscriber)
async def event_subscriber():
    r = await get_redis()
    pubsub = r.pubsub()
    await pubsub.subscribe("order_events")
    async for message in pubsub.listen():
        if message["type"] == "message":
            event_data = json.loads(message["data"])
            event = Event(**event_data)
            wf = await load_workflow(event.workflow_id) # Load from Redis/FS
            event.workflow = wf

asyncio.create_task(engine.execute(event)) # Concurrent execution

@app.on_event("startup")
async def startup():
    asyncio.create_task(event_subscriber())

# API Endpoints

@app.post("/workflows")
async def create_workflow(wf: Workflow):
    wf.id = str(uuid.uuid4())
    # Save to Redis/FS
    r = await get_redis()
    await r.set(f"workflow: {wf.id}", json.dumps(wf.dict()))
    logger.info(f"Created workflow {wf.id}")
    return {"id": wf.id}

@app.get("/workflows/{wf_id}")
async def get_workflow(wf_id: str):
    r = await get_redis()
    data = await r.get(f"workflow: {wf_id}")
    return json.loads(data) if data else {"error": "Not found"}

# Websocket for Real-Time
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        r = await get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe("dashboard_updates")
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def load_workflow(wf_id: str):
    r = await get_redis()
    data = await r.get(f"workflow:{wf_id}")
    return json.loads(data) if data else None

# Event publisher (for simulation)

@app.post("/publish_event")
async def publish_event(event: Event):
    r = await get_redis()
    await r.publish("order_events", json.dumps(event.dict()))
    return {"published": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)