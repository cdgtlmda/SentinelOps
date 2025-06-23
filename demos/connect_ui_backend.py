#!/usr/bin/env python3
"""
SentinelOps - Connect Your MVP UI with Backend
Adapts the working backend to serve data in the format your UI expects
"""

import asyncio
import json
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from random import randint, choice

# Create FastAPI app
app = FastAPI(title="SentinelOps API", description="Multi-Agent Security Platform - UI Connected")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generate realistic data for your UI
def generate_timeline_data():
    """Generate incidents timeline data for the last 24 hours"""
    timeline = []
    for hour in range(0, 24, 2):
        timeline.append({
            "time": f"{hour:02d}:00",
            "count": randint(2, 15)
        })
    return timeline

def generate_agent_status_data():
    """Generate weekly agent status data"""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [{"day": day, "online": randint(12, 20)} for day in days]

def generate_agent_table_data():
    """Generate agent table with realistic data"""
    agents = [
        {"name": "orchestrator-agent", "status": "Online", "ago": "2m ago", "statusColor": "text-green-600"},
        {"name": "detection-agent", "status": "Online", "ago": "1m ago", "statusColor": "text-green-600"},
        {"name": "analysis-agent", "status": "Online", "ago": "30s ago", "statusColor": "text-green-600"},
        {"name": "remediation-agent", "status": "Alert", "ago": "5m ago", "statusColor": "text-orange-600"},
        {"name": "communication-agent", "status": "Online", "ago": "45s ago", "statusColor": "text-green-600"},
    ]
    return agents

def generate_live_activity():
    """Generate realistic live activity feed"""
    activities = [
        "Detected suspicious SSH login from 192.168.1.100",
        "SQL injection attempt blocked on web-server-01",
        "Privilege escalation detected on db-server-02",
        "Malware signature updated: Trojan.Win32.Agent",
        "Network anomaly detected: unusual data transfer",
        "Failed authentication from unknown IP: 203.45.67.89",
        "Agent communication restored: srv-east-01",
        "Firewall rule updated: blocked suspicious traffic",
        "Certificate expiration warning: ssl-cert-prod",
        "DDoS attack mitigated: 50k requests/min blocked"
    ]
    
    activity_list = []
    for i in range(6):
        ago_options = ["now", "1m ago", "2m ago", "5m ago", "10m ago", "15m ago"]
        activity_list.append({
            "id": i + 1,
            "msg": choice(activities),
            "ago": choice(ago_options)
        })
    return activity_list

def generate_notifications():
    """Generate recent notifications"""
    return [
        {
            "id": 1,
            "msg": "Agent communication restored",
            "detail": "orchestrator-agent reconnected successfully",
            "ago": "23m ago"
        },
        {
            "id": 2,
            "msg": "Critical threat detected and mitigated",
            "detail": "SQL injection attempt on production database",
            "ago": "1h ago"
        },
        {
            "id": 3,
            "msg": "Security policy updated",
            "detail": "New firewall rules deployed across infrastructure",
            "ago": "2h ago"
        }
    ]

# Current data state
current_data = {
    "kpis": {
        "incidents_detected": randint(25, 40),
        "critical_severity": randint(5, 12),
        "avg_mttr": f"{randint(2, 5)}.{randint(1, 9)} hrs",
        "remediation_rate": randint(80, 95)
    },
    "timeline": generate_timeline_data(),
    "agent_status_chart": generate_agent_status_data(),
    "agent_table": generate_agent_table_data(),
    "live_activity": generate_live_activity(),
    "notifications": generate_notifications()
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# API Endpoints matching your UI expectations
@app.get("/api/dashboard/kpis")
async def get_kpis():
    """Get KPI data for dashboard cards"""
    return current_data["kpis"]

@app.get("/api/dashboard/timeline")
async def get_incidents_timeline():
    """Get incidents timeline data for chart"""
    return {"data": current_data["timeline"]}

@app.get("/api/dashboard/agent-status-chart")
async def get_agent_status_chart():
    """Get agent status chart data"""
    return {"data": current_data["agent_status_chart"]}

@app.get("/api/dashboard/agent-table")
async def get_agent_table():
    """Get agent table data"""
    return {"agents": current_data["agent_table"]}

@app.get("/api/dashboard/live-activity")
async def get_live_activity():
    """Get live activity feed"""
    return {"activities": current_data["live_activity"]}

@app.get("/api/dashboard/notifications")
async def get_notifications():
    """Get recent notifications"""
    return {"notifications": current_data["notifications"]}

@app.get("/api/dashboard/all")
async def get_all_dashboard_data():
    """Get all dashboard data in one request - optimized for your UI"""
    return {
        "kpis": current_data["kpis"],
        "timeline": current_data["timeline"],
        "agentStatusChart": current_data["agent_status_chart"],
        "agentTable": current_data["agent_table"],
        "liveActivity": current_data["live_activity"],
        "notifications": current_data["notifications"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/agents")
async def get_agents():
    """Legacy endpoint for basic agent status"""
    agents = [
        {"id": "orchestrator", "name": "Orchestrator Agent", "status": "online", "tools": 6},
        {"id": "detection", "name": "Detection Agent", "status": "online", "tools": 8},
        {"id": "analysis", "name": "Analysis Agent", "status": "online", "tools": 9},
        {"id": "remediation", "name": "Remediation Agent", "status": "online", "tools": 6},
        {"id": "communication", "name": "Communication Agent", "status": "online", "tools": 5}
    ]
    return {"agents": agents, "total": len(agents)}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_online": 5,
        "incidents_active": current_data["kpis"]["incidents_detected"],
        "api_version": "2.0.0"
    }

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket for real-time dashboard updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            update = {
                "type": "dashboard_update",
                "data": {
                    "kpis": current_data["kpis"],
                    "liveActivity": generate_live_activity(),
                    "timestamp": datetime.now().isoformat()
                }
            }
            await websocket.send_json(update)
            await asyncio.sleep(10)  # Update every 10 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to update data periodically
async def update_data_periodically():
    """Update dashboard data every 30 seconds"""
    while True:
        # Update KPIs
        current_data["kpis"]["incidents_detected"] = randint(25, 40)
        current_data["kpis"]["critical_severity"] = randint(5, 12)
        current_data["kpis"]["remediation_rate"] = randint(80, 95)
        
        # Update live activity
        current_data["live_activity"] = generate_live_activity()
        
        # Broadcast updates to connected WebSocket clients
        await manager.broadcast({
            "type": "live_update",
            "data": {
                "kpis": current_data["kpis"],
                "liveActivity": current_data["live_activity"],
                "timestamp": datetime.now().isoformat()
            }
        })
        
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(update_data_periodically())

if __name__ == "__main__":
    print("🛡️  SentinelOps - Connecting Your MVP UI to Backend")
    print("=" * 60)
    print("🔗 Backend API running on: http://localhost:8081")
    print("📱 Start your UI on: http://localhost:3000")
    print("🔄 WebSocket endpoint: ws://localhost:8081/ws/dashboard")
    print("=" * 60)
    print("📋 API Endpoints for your UI:")
    print("   GET /api/dashboard/all       - All dashboard data")
    print("   GET /api/dashboard/kpis      - KPI cards data")
    print("   GET /api/dashboard/timeline  - Incidents timeline")
    print("   GET /api/dashboard/live-activity - Activity feed")
    print("   WS  /ws/dashboard           - Real-time updates")
    print("=" * 60)
    print("🚀 Ready to connect your MVP UI!")
    
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="info")