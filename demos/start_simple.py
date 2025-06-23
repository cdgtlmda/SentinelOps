#!/usr/bin/env python3
"""
SentinelOps - Simple Working Demo
One script that actually works!
"""

import asyncio
import json
import webbrowser
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import threading
import time

# Create FastAPI app
app = FastAPI(title="SentinelOps", description="Multi-Agent Security Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data
AGENTS = [
    {"id": "orchestrator", "name": "Orchestrator Agent", "status": "online", "tools": 6, "description": "Workflow coordination"},
    {"id": "detection", "name": "Detection Agent", "status": "online", "tools": 8, "description": "Continuous monitoring"},
    {"id": "analysis", "name": "Analysis Agent", "status": "online", "tools": 9, "description": "AI-powered analysis"},
    {"id": "remediation", "name": "Remediation Agent", "status": "online", "tools": 6, "description": "Automated response"},
    {"id": "communication", "name": "Communication Agent", "status": "online", "tools": 5, "description": "Notifications"}
]

INCIDENTS = [
    {"id": "inc-001", "title": "Suspicious Login Activity", "severity": "high", "status": "investigating", "created_at": "2024-06-17T12:00:00Z", "description": "Multiple failed login attempts from IP 192.168.1.100"},
    {"id": "inc-002", "title": "Unusual Data Access", "severity": "medium", "status": "active", "created_at": "2024-06-17T11:30:00Z", "description": "Abnormal database access pattern detected"},
    {"id": "inc-003", "title": "Malware Detection", "severity": "critical", "status": "remediating", "created_at": "2024-06-17T10:15:00Z", "description": "Trojan detected on workstation DESK-001"}
]

@app.get("/")
async def dashboard():
    """Main dashboard with working interface"""
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ SentinelOps Security Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        .header {{
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 2rem auto; 
            padding: 0 2rem;
        }}
        .dashboard {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 2rem; 
            margin-top: 2rem;
        }}
        .card {{ 
            background: rgba(255,255,255,0.95);
            backdrop-filter: blur(10px);
            padding: 2rem; 
            border-radius: 12px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .agent {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 1rem; 
            margin: 0.5rem 0; 
            background: #f8f9ff; 
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .incident {{ 
            padding: 1rem; 
            margin: 0.5rem 0; 
            border-radius: 8px;
            background: #fff;
            border-left: 4px solid #ff6b6b;
        }}
        .incident.high {{ border-left-color: #dc3545; background: #fff5f5; }}
        .incident.medium {{ border-left-color: #ffc107; background: #fffbf0; }}
        .incident.critical {{ border-left-color: #6f42c1; background: #f8f5ff; }}
        .status {{ 
            padding: 0.25rem 0.75rem; 
            border-radius: 20px; 
            font-size: 0.8rem; 
            font-weight: bold;
        }}
        .online {{ background: #d4edda; color: #155724; }}
        .investigating {{ background: #fff3cd; color: #856404; }}
        .active {{ background: #f8d7da; color: #721c24; }}
        .remediating {{ background: #d1ecf1; color: #0c5460; }}
        h1 {{ color: #2c3e50; font-size: 2.5rem; }}
        h2 {{ color: #34495e; margin-bottom: 1rem; }}
        .stats {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 1rem; 
            margin: 2rem 0;
        }}
        .stat {{ 
            text-align: center; 
            padding: 1.5rem; 
            background: rgba(255,255,255,0.9);
            border-radius: 8px;
        }}
        .stat-number {{ font-size: 2rem; font-weight: bold; color: #667eea; }}
        .refresh-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            margin: 1rem 0;
        }}
        .refresh-btn:hover {{ background: #5a6fd8; }}
        .footer {{ 
            text-align: center; 
            padding: 2rem; 
            color: rgba(255,255,255,0.8);
            font-size: 0.9rem;
        }}
        .api-links {{
            background: rgba(255,255,255,0.1);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }}
        .api-links a {{
            color: white;
            text-decoration: none;
            margin: 0 1rem;
            padding: 0.5rem 1rem;
            background: rgba(255,255,255,0.2);
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 0.5rem;
        }}
        .api-links a:hover {{ background: rgba(255,255,255,0.3); }}
        @media (max-width: 768px) {{
            .dashboard {{ grid-template-columns: 1fr; }}
            .stats {{ grid-template-columns: 1fr 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ SentinelOps Security Dashboard</h1>
        <p>Autonomous Multi-Agent Incident Response Platform</p>
    </div>

    <div class="container">
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len([a for a in AGENTS if a['status'] == 'online'])}</div>
                <div>Agents Online</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len(INCIDENTS)}</div>
                <div>Active Incidents</div>
            </div>
            <div class="stat">
                <div class="stat-number">{sum(a['tools'] for a in AGENTS)}</div>
                <div>Security Tools</div>
            </div>
            <div class="stat">
                <div class="stat-number">98.7%</div>
                <div>System Uptime</div>
            </div>
        </div>

        <div class="dashboard">
            <div class="card">
                <h2>🤖 Security Agents</h2>
                <button class="refresh-btn" onclick="location.reload()">Refresh Status</button>
                {"".join(f'''
                <div class="agent">
                    <div>
                        <strong>{agent['name']}</strong><br>
                        <small>{agent['description']} • {agent['tools']} tools</small>
                    </div>
                    <span class="status online">{agent['status']}</span>
                </div>
                ''' for agent in AGENTS)}
            </div>

            <div class="card">
                <h2>🚨 Security Incidents</h2>
                <button class="refresh-btn" onclick="loadIncidents()">Refresh Incidents</button>
                {"".join(f'''
                <div class="incident {incident['severity']}">
                    <strong>{incident['title']}</strong>
                    <span class="status {incident['status']}">{incident['status']}</span><br>
                    <small>{incident['description']}</small><br>
                    <small>🕒 {incident['created_at']}</small>
                </div>
                ''' for incident in INCIDENTS)}
            </div>
        </div>

        <div class="api-links">
            <h2 style="color: white; margin-bottom: 1rem;">🔌 API Endpoints</h2>
            <a href="/api/agents">View Agents JSON</a>
            <a href="/api/incidents">View Incidents JSON</a>
            <a href="/health">Health Check</a>
            <a href="/docs">API Documentation</a>
        </div>
    </div>

    <div class="footer">
        <p>🛡️ SentinelOps Multi-Agent Security Platform | Running on Python FastAPI</p>
        <p>Real-time monitoring • AI-powered analysis • Automated response</p>
    </div>

    <script>
        // Auto-refresh every 30 seconds
        setInterval(() => {{
            fetch('/api/agents')
                .then(r => r.json())
                .then(data => console.log('Agents:', data.total, 'online'))
                .catch(e => console.log('API connection:', e.message));
        }}, 30000);

        function loadIncidents() {{
            fetch('/api/incidents')
                .then(r => r.json())
                .then(data => {{
                    alert(`Found ${{data.total}} incidents (${{data.active}} active)`);
                }})
                .catch(e => alert('Failed to load incidents'));
        }}

        // Show that we're live
        console.log('🛡️ SentinelOps Dashboard Loaded');
        console.log('Backend API running on http://localhost:8080');
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "agents_online": len([a for a in AGENTS if a["status"] == "online"]),
        "incidents_active": len([i for i in INCIDENTS if i["status"] in ["active", "investigating"]])
    }

@app.get("/api/agents")
async def get_agents():
    return {"agents": AGENTS, "total": len(AGENTS), "online": len([a for a in AGENTS if a["status"] == "online"])}

@app.get("/api/incidents") 
async def get_incidents():
    return {
        "incidents": INCIDENTS, 
        "total": len(INCIDENTS),
        "active": len([i for i in INCIDENTS if i["status"] in ["active", "investigating"]])
    }

def open_browser():
    """Open browser after server starts"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

if __name__ == "__main__":
    print("🛡️  SentinelOps Multi-Agent Security Platform")
    print("=" * 50)
    print("🚀 Starting server on http://localhost:8080")
    print("📱 Dashboard will open automatically")
    print("🔍 API docs available at http://localhost:8080/docs")
    print("=" * 50)
    
    # Start browser opener in background
    def open_browser_new():
        time.sleep(2)
        webbrowser.open('http://localhost:8080')
    
    browser_thread = threading.Thread(target=open_browser_new)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")