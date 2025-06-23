import asyncio
import json
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SentinelOps API", description="Multi-Agent Security Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENTS = [
    {"id": "orchestrator", "name": "Orchestrator Agent", "status": "online", "tools": 6},
    {"id": "detection", "name": "Detection Agent", "status": "online", "tools": 8},
    {"id": "analysis", "name": "Analysis Agent", "status": "online", "tools": 9},
    {"id": "remediation", "name": "Remediation Agent", "status": "online", "tools": 6},
    {"id": "communication", "name": "Communication Agent", "status": "online", "tools": 5}
]

INCIDENTS = [
    {"id": "inc-001", "title": "Suspicious Login Activity", "severity": "high", "status": "investigating", "created_at": "2024-06-17T12:00:00Z"},
    {"id": "inc-002", "title": "Unusual Data Access Pattern", "severity": "medium", "status": "active", "created_at": "2024-06-17T11:30:00Z"}
]

@app.get("/")
async def root():
    return {"message": "🛡️ SentinelOps API", "status": "operational", "agents": len(AGENTS), "incidents": len(INCIDENTS)}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "agents_online": 5}

@app.get("/api/agents")
async def get_agents():
    return {"agents": AGENTS, "total": len(AGENTS)}

@app.get("/api/incidents")
async def get_incidents():
    return {"incidents": INCIDENTS, "total": len(INCIDENTS)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
            await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
