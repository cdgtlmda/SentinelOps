# ADK Troubleshooting Guide for SentinelOps

## Common Issues and Solutions

### 1. ADK Import Errors

#### Issue: `ModuleNotFoundError: No module named 'google.adk'`

**Solution:**
```bash
# Ensure ADK is installed
cd /path/to/sentinelops
pip install -e ./adk

# Verify installation
python -c "import google.adk; print(google.adk.__version__)"
```

#### Issue: `ImportError: cannot import name 'LLMAgent' from 'google.adk.agents'`

**Solution:**
The correct import is `LlmAgent` (not `LLMAgent`):
```python
# Incorrect
from google.adk.agents import LLMAgent  # ❌

# Correct
from google.adk.agents import LlmAgent  # ✅
```

### 2. Agent Initialization Failures

#### Issue: Agent fails to start with "No credentials provided"

**Solution:**
```bash
# Set up Application Default Credentials
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Verify credentials
gcloud auth application-default print-access-token
```

#### Issue: Firestore initialization fails

**Solution:**
```bash
# Ensure Firestore is enabled
gcloud firestore databases create --region=us-central1

# Check if database exists
gcloud firestore databases list
```

### 3. Tool Execution Errors

#### Issue: `AttributeError: 'NoneType' object has no attribute 'execute'`

**Solution:**
Ensure tools are properly initialized:
```python
# Check tool initialization in agent
def _init_tools(self):
    self.tools = [
        MyTool(param1, param2),  # Ensure all params are provided
    ]
    
# Verify tools are registered
for tool in self.tools:
    print(f"Tool: {tool.name}, Type: {type(tool)}")
```

#### Issue: Tool execution timeout

**Solution:**
Increase timeout in tool configuration:
```python
class MyTool(BaseTool):
    async def execute(self, context: ToolContext, **kwargs):
        # Add timeout handling
        try:
            async with asyncio.timeout(300):  # 5 minutes
                return await self._perform_operation(**kwargs)
        except asyncio.TimeoutError:
            return {"success": False, "error": "Operation timeout"}
```

### 4. Inter-Agent Communication Issues

#### Issue: Agent transfer fails with "Target agent not found"

**Solution:**
Verify routing configuration:
```python
# Check agent registration
from src.common.adk_routing import get_routing_config

routing_config = get_routing_config()
print(routing_config.get_registered_agents())

# Ensure agent names match exactly
AGENT_NAMES = {
    "detection_agent",     # Must match exactly
    "analysis_agent",
    "remediation_agent",
    "communication_agent",
    "orchestrator_agent"
}
```

#### Issue: Workflow gets stuck between agents

**Solution:**
Check workflow state in Firestore:
```python
# Debug workflow state
workflow_ref = firestore_client.collection("incident_workflows").document(workflow_id)
workflow_data = workflow_ref.get().to_dict()
print(f"Current stage: {workflow_data.get('current_stage')}")
print(f"Status: {workflow_data.get('status')}")
print(f"Last updated: {workflow_data.get('updated_at')}")
```

### 5. Gemini Integration Issues

#### Issue: Gemini API returns 401 Unauthorized

**Solution:**
```bash
# Verify API key in Secret Manager
gcloud secrets versions access latest --secret="gemini-api-key"

# Test API key directly
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models
```

#### Issue: Gemini response parsing fails

**Solution:**
Add error handling for response parsing:
```python
try:
    response = model.generate_content(prompt)
    analysis_text = response.text
except Exception as e:
    logger.error(f"Gemini error: {e}")
    # Fallback to rule-based analysis
    return self._fallback_analysis(incident)
```

### 6. Performance Issues

#### Issue: Agent response time is slow

**Solution:**
1. Enable ADK caching:
```python
# In agent initialization
self.cache_config = {
    "enabled": True,
    "ttl": 3600,  # 1 hour
    "max_size": 1000
}
```

2. Optimize BigQuery queries:
```sql
-- Add partitioning filter
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
  AND _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
```

3. Use batch processing:
```python
# Process events in batches
async def process_events(events):
    batch_size = 100
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        await self._process_batch(batch)
```

### 7. Memory Issues

#### Issue: Agent crashes with OOM (Out of Memory)

**Solution:**
1. Increase Cloud Run memory:
```bash
gcloud run services update detection-agent \
  --memory=2Gi \
  --region=us-central1
```

2. Implement memory-efficient patterns:
```python
# Use generators for large datasets
def process_large_dataset(self):
    for chunk in self._read_in_chunks():
        yield self._process_chunk(chunk)

# Clear caches periodically
async def _cleanup_memory(self):
    if hasattr(self, '_cache'):
        self._cache.clear()
    gc.collect()
```

### 8. Deployment Issues

#### Issue: Cloud Build fails with "ADK not found"

**Solution:**
Ensure Dockerfile includes ADK:
```dockerfile
# Install ADK
COPY adk/ /app/adk/
RUN pip install -e /app/adk/

# Verify installation
RUN python -c "from google.adk.agents import LlmAgent"
```

#### Issue: Service account permissions error

**Solution:**
Grant required permissions:
```bash
# Grant BigQuery access
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:detection-agent@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# Grant Firestore access
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:orchestrator-agent@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"
```

### 9. Testing Issues

#### Issue: Unit tests fail with ADK imports

**Solution:**
Mock ADK components in tests:
```python
# test_detection_agent.py
from unittest.mock import Mock, patch

@patch('google.adk.agents.LlmAgent')
def test_detection_agent(mock_llm_agent):
    mock_llm_agent.return_value = Mock()
    agent = DetectionAgent(config)
    assert agent is not None
```

#### Issue: Integration tests timeout

**Solution:**
Increase test timeout and use async properly:
```python
# Use pytest-asyncio
@pytest.mark.asyncio
@pytest.mark.timeout(300)  # 5 minutes
async def test_full_workflow():
    agent = OrchestratorAgent(test_config)
    result = await agent.run(incident=test_incident)
    assert result["status"] == "success"
```

### 10. Debugging Techniques

#### Enable Detailed Logging

```python
# Set logging level
import logging
logging.basicConfig(level=logging.DEBUG)

# ADK-specific logging
os.environ["ADK_LOG_LEVEL"] = "DEBUG"
```

#### Use ADK Telemetry

```python
# Enable telemetry
config = {
    "telemetry_enabled": True,
    "telemetry_export_interval": 10  # seconds
}

# View telemetry in Cloud Monitoring
# Metrics will be under custom.googleapis.com/adk/*
```

#### Interactive Debugging

```python
# Add breakpoints in agent code
import pdb; pdb.set_trace()

# Or use remote debugging
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

#### Trace Agent Execution

```python
# Add execution tracing
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("detection_scan"):
    # Your code here
    pass
```

### 11. Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Tool not found" | Tool not registered | Check tool name matches registration |
| "Context missing required data" | Invalid tool context | Ensure context.data contains required fields |
| "Agent timeout" | Long-running operation | Increase timeout or optimize operation |
| "Rate limit exceeded" | Too many API calls | Implement rate limiting and caching |
| "Invalid state transition" | Workflow logic error | Check stage transition rules |

### 12. Health Checks

#### Agent Health Check Endpoint

```python
# Add health check to agent
async def health_check(self) -> Dict[str, Any]:
    checks = {
        "agent": "healthy",
        "tools": len(self.tools),
        "memory_usage": self._get_memory_usage(),
        "last_execution": self.last_execution_time
    }
    
    # Check external dependencies
    try:
        self.firestore_client.collection("_health").document("check").set({"ts": datetime.utcnow()})
        checks["firestore"] = "healthy"
    except:
        checks["firestore"] = "unhealthy"
    
    return checks
```

#### Monitoring Script

```bash
#!/bin/bash
# health_check.sh

AGENTS=("detection" "analysis" "remediation" "communication" "orchestrator")

for agent in "${AGENTS[@]}"; do
    URL="https://${agent}-agent-xxxxx.run.app/health"
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)
    
    if [ $RESPONSE -eq 200 ]; then
        echo "✅ $agent agent: Healthy"
    else
        echo "❌ $agent agent: Unhealthy (HTTP $RESPONSE)"
    fi
done
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**: 
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit=100
   ```

2. **ADK Community**: 
   - Stack Overflow tag: `google-adk`
   - GitHub Issues: https://github.com/googleapis/google-adk/issues

3. **SentinelOps Support**:
   - Internal Slack: #sentinelops-help
   - Email: sentinelops-support@company.com

4. **Emergency Contacts**:
   - On-call Engineer: See PagerDuty
   - Escalation: security-team@company.com
