# Analysis Agent Documentation

## Overview

The Analysis Agent is a critical component of the SentinelOps security platform that provides intelligent analysis of security incidents using Google's Vertex AI (Gemini models). It performs event correlation, generates insights, and provides actionable remediation recommendations.

## Architecture

### Core Components

1. **Agent Core (`agent.py`)**
   - Main orchestration logic
   - Message handling and routing
   - Integration with other components

2. **Incident Retrieval (`incident_retrieval.py`)**
   - Fetches incident data from Firestore
   - Validates data completeness
   - Handles data conversion

3. **Event Extraction (`event_extraction.py`)**
   - Extracts metadata from incidents
   - Enriches event data
   - Validates data quality

4. **Event Correlation (`event_correlation.py`)**
   - Temporal correlation analysis
   - Spatial (resource-based) correlation
   - Causal pattern detection
   - Actor behavior analysis

5. **Recommendation Engine (`recommendation_engine.py`)**
   - Generates remediation recommendations
   - Prioritizes actions based on severity
   - Identifies automatable actions

6. **Context Retrieval (`context_retrieval.py`)**
   - Finds related incidents
   - Retrieves historical patterns
   - Queries knowledge base
   - Gathers threat intelligence

7. **Performance Optimizer (`performance_optimizer.py`)**
   - Caching mechanism
   - Request batching
   - Rate limiting

8. **Monitoring (`monitoring.py`)**
   - Metrics collection
   - Performance tracking
   - Error monitoring

## Configuration

The Analysis Agent uses a comprehensive configuration schema defined in `config_schema.py`. Key configuration sections:

### Gemini Configuration
```yaml
gemini:
  model: "gemini-pro"  # Model to use
  temperature: 0.7     # Controls response randomness
  max_output_tokens: 2048
  retry_attempts: 3
  timeout: 30
```

### Analysis Configuration
```yaml
analysis:
  confidence_thresholds:
    low: 0.3
    medium: 0.6
    high: 0.8
    critical: 0.9
  correlation_window: 3600  # 1 hour
  max_related_events: 50
  enable_context_retrieval: true
  enable_recommendation_engine: true
```

### Performance Configuration
```yaml
performance:
  cache_enabled: true
  cache_ttl: 3600
  batch_size: 10
  max_concurrent_analyses: 5
  rate_limit:
    enabled: true
    max_per_minute: 30
    max_per_hour: 500
```

## Message Flow

1. **Incoming Analysis Request**
   ```json
   {
     "message_type": "analyze_incident",
     "incident_id": "inc-12345"
   }
   ```

2. **Processing Steps**
   - Retrieve incident from Firestore
   - Check cache for existing analysis
   - Extract event metadata
   - Perform event correlation
   - Gather additional context
   - Generate Gemini prompt
   - Get AI analysis
   - Generate recommendations
   - Cache results
   - Publish results

3. **Outgoing Analysis Result**
   ```json
   {
     "message_type": "analysis_complete",
     "incident_id": "inc-12345",
     "analysis": {
       "confidence_score": 0.85,
       "summary": "...",
       "detailed_analysis": "...",
       "attack_techniques": ["T1078", "T1068"],
       "recommendations": ["..."],
       "evidence": {...}
     }
   }
   ```

## Event Correlation

The agent performs sophisticated event correlation across multiple dimensions:

### Temporal Correlation
- Identifies event clusters based on time proximity
- Detects burst periods of high activity
- Analyzes event frequency patterns

### Spatial Correlation
- Groups events by affected resources
- Identifies resource access patterns
- Detects cross-resource activity

### Causal Correlation
- Identifies cause-effect relationships
- Detects action sequences
- Finds common attack patterns

### Actor Correlation
- Tracks actor behavior patterns
- Identifies suspicious actors
- Detects potential collaboration

## Gemini Integration

### Prompt Engineering

The agent constructs detailed prompts including:
- Incident metadata
- Event details with enriched context
- Correlation analysis results
- Additional context from related incidents
- Data quality indicators

### Response Parsing

Gemini responses are parsed to extract:
- Summary (brief incident overview)
- Detailed analysis (comprehensive explanation)
- Confidence score (0.0 to 1.0)
- Attack techniques (MITRE ATT&CK framework)
- Recommendations (actionable steps)
- Additional evidence needed

### Error Handling

- Retry logic with exponential backoff
- Graceful degradation on API failures
- Default values for malformed responses

## Recommendation Generation

### Template-Based Recommendations

The engine includes templates for common incident types:
- Unauthorized access
- Data exfiltration
- Privilege escalation
- Malware infection
- Account compromise
- DDoS attacks
- Configuration drift

### Prioritization

Recommendations are prioritized based on:
- Incident severity
- Correlation strength
- Action urgency keywords
- Automation possibility

### Automation Identification

The engine identifies actions that can be automated:
- Account disabling
- Session revocation
- Firewall rule creation
- Instance termination
- IAM modifications

## Performance Optimization

### Caching

- In-memory cache with TTL
- Cache key based on incident data hash
- Automatic eviction of old entries
- Cache hit rate tracking

### Rate Limiting

- Per-minute and per-hour limits
- Automatic throttling
- Queue management for bursts

### Batching

- Groups similar requests
- Reduces API calls
- Configurable batch size and timeout

## Monitoring and Metrics

### Key Metrics Tracked

- Total analyses performed
- Success/failure rates
- Average analysis duration
- Confidence score distribution
- Gemini API usage
- Cache hit rates
- Error frequencies

### Time Series Data

- Analyses per minute
- Average confidence scores
- High correlation incidents
- Rate limit hits

### Cloud Monitoring Integration

- Custom metrics exported to Google Cloud Monitoring
- Real-time dashboards
- Alert configuration

## Security Considerations

1. **API Key Management**
   - Gemini API key stored in environment variables
   - Never logged or exposed

2. **Data Privacy**
   - Sensitive data redacted in logs
   - Cache cleared on shutdown
   - No persistent storage of analysis results

3. **Rate Limiting**
   - Prevents API abuse
   - Protects against DoS

4. **Input Validation**
   - All inputs validated before processing
   - Malformed data rejected

## Troubleshooting

### Common Issues

1. **Gemini API Errors**
   - Check API key validity
   - Verify quota limits
   - Review rate limiting settings

2. **High Latency**
   - Check cache configuration
   - Monitor Gemini response times
   - Verify correlation window settings

3. **Low Confidence Scores**
   - Review data quality scores
   - Check event completeness
   - Verify correlation parameters

### Debug Mode

Enable debug logging:
```python
config = {
    "debug": True,
    "log_level": "DEBUG"
}
```

### Metrics Endpoints

Access metrics via the agent's status method:
```python
status = agent.get_status()
metrics = status["metrics"]
```

## Best Practices

1. **Configuration Tuning**
   - Adjust correlation window based on incident patterns
   - Set appropriate confidence thresholds
   - Configure cache TTL based on data volatility

2. **Resource Management**
   - Monitor memory usage with large incidents
   - Set reasonable max_related_events limits
   - Use batching for high-volume scenarios

3. **Quality Assurance**
   - Regularly review recommendation accuracy
   - Monitor confidence score distributions
   - Track false positive rates

## API Reference

### Public Methods

```python
class AnalysisAgent(Agent):
    async def start() -> None
    async def stop() -> None
    def process_message(message: Dict[str, Any], sender_info: Dict[str, Any]) -> None
    def get_status() -> Dict[str, Any]
```

### Message Types

**Input:**
- `analyze_incident`: Trigger analysis of an incident

**Output:**
- `analysis_complete`: Analysis results ready
- `analysis_failed`: Analysis failed with error

## Testing

### Unit Tests
- Event correlation logic
- Prompt generation
- Response parsing
- Recommendation engine

### Integration Tests
- Firestore connectivity
- Vertex AI integration
- End-to-end analysis flow

### Test Fixtures
- Sample incidents
- Mock Vertex AI responses
- Correlation test cases

## Deployment

### Environment Variables
```bash
# Vertex AI uses Application Default Credentials
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=us-central1
```

### Resource Requirements
- Memory: 2GB minimum
- CPU: 2 cores recommended
- Network: Low latency to Google Cloud APIs

### Scaling Considerations
- Horizontal scaling supported
- Stateless design
- Cache not shared between instances
