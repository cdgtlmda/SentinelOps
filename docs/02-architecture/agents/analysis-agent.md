# Analysis Agent Documentation

## Overview

The Analysis Agent is a critical component of SentinelOps that uses Google's Vertex AI (Gemini models) to analyze security incidents, correlate events, and provide actionable insights. It processes incidents from Firestore, performs sophisticated correlation analysis, and generates comprehensive security recommendations.

## Architecture

### Core Components

1. **Agent Core** (`agent.py`)
   - Main orchestration logic
   - Message handling and async processing
   - Integration with base agent framework

2. **Incident Retrieval** (`incident_retrieval.py`)
   - Firestore document retrieval
   - Data validation and conversion
   - Error handling for missing data

3. **Event Correlation** (`event_correlation.py`)
   - Temporal pattern analysis
   - Spatial (resource-based) correlation
   - Causal relationship detection
   - Actor behavior analysis

4. **Recommendation Engine** (`recommendation_engine.py`)
   - Template-based recommendations
   - Priority scoring
   - Automation identification

5. **Context Retrieval** (`context_retrieval.py`)
   - Related incident discovery
   - Historical pattern matching
   - Threat intelligence gathering

## Analysis Capabilities

### Event Correlation Types

#### 1. Temporal Correlation
- **Event Clustering**: Groups events occurring within 5-minute windows
- **Burst Detection**: Identifies periods of unusually high activity
- **Time Gap Analysis**: Detects suspicious delays between related events
- **Frequency Analysis**: Tracks event occurrence patterns

#### 2. Spatial Correlation
- **Resource Clustering**: Identifies resources with multiple security events
- **Access Pattern Analysis**: Maps source-to-target resource relationships
- **Cross-Resource Activity**: Detects events affecting multiple resources
- **Resource Targeting**: Ranks resources by security impact

#### 3. Causal Correlation
- **Cause-Effect Detection**: Identifies event chains (e.g., failed login → account lockout)
- **Action Sequences**: Discovers patterns of consecutive related actions
- **Common Attack Patterns**: Recognizes known attack progressions

#### 4. Actor Correlation
- **Behavior Analysis**: Profiles user activity patterns
- **Suspicious Actor Detection**: Flags users with anomalous behavior
- **Collaboration Detection**: Identifies potential coordinated attacks
- **Multi-Actor Resource Access**: Tracks shared resource access

### Supported Incident Types

1. **Unauthorized Access**
   - Failed authentication attempts
   - Access policy violations
   - Forbidden resource access

2. **Data Exfiltration**
   - Large data transfers
   - Unusual download patterns
   - Storage bucket access anomalies

3. **Privilege Escalation**
   - IAM policy changes
   - Role binding modifications
   - Service account creation

4. **Malware Infection**
   - Suspicious process execution
   - Network anomalies
   - File system changes

5. **Account Compromise**
   - Credential theft indicators
   - Session hijacking
   - OAuth token abuse

6. **DDoS Attacks**
   - Traffic volume spikes
   - Request pattern anomalies
   - Resource exhaustion

7. **Configuration Drift**
   - Unauthorized changes
   - Policy violations
   - Security misconfiguration

## Prompt Design Guidelines

### Prompt Structure

The Analysis Agent uses a sophisticated prompt template that includes:

1. **Incident Context**
   - Title, description, severity
   - Creation timestamp
   - Current status and tags

2. **Metadata Summary**
   - Event counts and types
   - Time range analysis
   - Affected resources
   - Data quality score

3. **Correlation Results**
   - Correlation scores (0.0-1.0)
   - Key findings summary
   - Primary events identification

4. **Detailed Event Information**
   - Chronological event listing
   - Actor identification
   - Resource relationships
   - Security indicators

### Prompt Optimization Tips

1. **Be Specific**: Include exact event types and resource names
2. **Provide Context**: Add correlation scores and patterns
3. **Request Structure**: Ask for specific sections (SUMMARY, ANALYSIS, etc.)
4. **Include Metrics**: Add data quality scores to calibrate confidence

### Example Prompt Section

```
Incident Details:
Title: Multiple Failed Login Attempts Followed by Privilege Escalation
Severity: HIGH
Created At: 2024-01-15T10:30:00Z

Event Correlation Analysis:
- Temporal Score: 0.85 (strong time-based clustering)
- Causal Score: 0.90 (clear cause-effect chain detected)
- Actor Score: 0.75 (suspicious actor patterns identified)
```

## Confidence Score Interpretation

### Score Ranges

- **0.8 - 1.0**: Very High Confidence
  - Clear attack patterns identified
  - Strong correlation between events
  - Multiple indicators present
  - Immediate action recommended

- **0.6 - 0.8**: High Confidence
  - Probable security incident
  - Good correlation evidence
  - Some uncertainty in details
  - Prompt investigation needed

- **0.4 - 0.6**: Medium Confidence
  - Possible security concern
  - Limited correlation evidence
  - Could be false positive
  - Further analysis required

- **0.2 - 0.4**: Low Confidence
  - Weak indicators
  - Poor event correlation
  - Likely benign activity
  - Monitor for escalation

- **0.0 - 0.2**: Very Low Confidence
  - Minimal security indicators
  - No clear patterns
  - Probably false positive
  - Low priority

### Factors Affecting Confidence

1. **Positive Factors**
   - High correlation scores
   - Multiple related events
   - Known attack patterns
   - Critical severity events
   - Suspicious actor behavior

2. **Negative Factors**
   - Low data quality
   - Missing event data
   - Temporal gaps
   - Isolated events
   - No actor information

## Configuration Options

### Environment Variables

```bash
# Required - Vertex AI uses Application Default Credentials
# No API key needed

# Optional
ANALYSIS_AGENT_LOG_LEVEL=INFO
```

### Configuration File Settings

```yaml
google_cloud:
  vertex_ai:
    model: "gemini-1.5-pro-002"  # or "gemini-1.5-flash-002"
    temperature: 0.7     # 0.0-1.0, lower = more focused
    max_output_tokens: 2048
    top_k: 40
    top_p: 0.95
    location: "us-central1"

agents:
  analysis:
    # Correlation settings
    correlation_window: 3600  # seconds
    max_related_events: 50
    
    # Confidence thresholds
    confidence_thresholds:
      high: 0.8
      medium: 0.6
      low: 0.4
    
    # Performance settings
    performance:
      cache_ttl: 3600  # seconds
      max_cache_size: 1000
      rate_limit:
        max_per_minute: 30
        max_per_hour: 500
    
    # Retry configuration
    retry:
      max_attempts: 3
      initial_delay: 1.0
      max_delay: 10.0
      exponential_base: 2
```

### Tuning Recommendations

1. **For High-Security Environments**
   - Lower temperature (0.3-0.5) for consistent analysis
   - Higher confidence thresholds
   - Longer correlation windows
   - More aggressive caching

2. **For High-Volume Environments**
   - Increase rate limits
   - Larger cache size
   - Shorter correlation windows
   - Enable request batching

3. **For Development/Testing**
   - Higher temperature for varied responses
   - Lower confidence thresholds
   - Verbose logging
   - Disable caching

## Performance Optimization

### Caching Strategy

- **What's Cached**: Complete analysis results
- **Cache Key**: Incident ID + incident hash
- **TTL**: Configurable (default 1 hour)
- **Invalidation**: On incident update

### Rate Limiting

- **Per Minute**: 30 requests (default)
- **Per Hour**: 500 requests (default)
- **Burst Handling**: Token bucket algorithm
- **Monitoring**: Metrics for limit hits

### Resource Usage

- **Memory**: ~200MB baseline + cache
- **CPU**: Minimal (mostly I/O bound)
- **Network**: Gemini API calls
- **Storage**: Firestore queries

## Monitoring and Metrics

### Key Metrics Tracked

1. **Analysis Performance**
   - Total analyses performed
   - Average response time
   - Cache hit rate
   - Error rate

2. **Gemini API Usage**
   - API calls per hour
   - Token consumption
   - Retry attempts
   - API errors

3. **Correlation Quality**
   - Average correlation scores
   - Confidence score distribution
   - Primary events identified
   - Suspicious actors detected

4. **Business Metrics**
   - Incidents analyzed
   - Recommendations generated
   - Automation opportunities
   - Time to analysis

### Health Indicators

- **Healthy**: 
  - API success rate > 95%
  - Average response < 10s
  - Cache hit rate > 30%

- **Degraded**:
  - API success rate 85-95%
  - Average response 10-30s
  - High retry rate

- **Unhealthy**:
  - API success rate < 85%
  - Average response > 30s
  - Consistent errors

## Troubleshooting

### Common Issues

1. **High Latency**
   - Check Gemini API status
   - Verify rate limits
   - Review cache configuration
   - Check Firestore performance

2. **Low Confidence Scores**
   - Verify data quality
   - Check event completeness
   - Review correlation window
   - Validate prompt template

3. **Missing Analyses**
   - Check message subscriptions
   - Verify incident retrieval
   - Review error logs
   - Check API credentials

### Debug Mode

Enable detailed logging:
```bash
export ANALYSIS_AGENT_LOG_LEVEL=DEBUG
```

### Log Analysis

Key log patterns to monitor:
- `"Starting analysis for incident"` - Analysis initiated
- `"Event correlation completed"` - Correlation finished
- `"Successfully received Vertex AI analysis"` - API success
- `"Analysis completed"` - Full success
- `"Error analyzing incident"` - Failure indicator

## Integration Points

### Input Sources
- **Orchestrator Agent**: Analysis requests
- **Firestore**: Incident data

### Output Destinations
- **Orchestrator Agent**: Analysis results
- **Firestore**: Cached results (optional)

### API Dependencies
- **Vertex AI API**: AI analysis using Gemini models
- **Firestore API**: Data retrieval
- **Pub/Sub API**: Messaging

## Security Considerations

1. **Authentication Management**
   - Uses Application Default Credentials (ADC)
   - No API keys needed for Vertex AI
   - Service account based authentication

2. **Data Privacy**
   - No PII in prompts
   - Sanitize sensitive data
   - Audit log access

3. **Access Control**
   - Service account permissions
   - Firestore security rules
   - Pub/Sub ACLs

## Future Enhancements

1. **Planned Features**
   - Multi-model support
   - Custom prompt templates
   - Real-time streaming analysis
   - Advanced caching strategies

2. **Performance Improvements**
   - Request batching
   - Parallel correlation
   - Optimized prompts
   - Edge caching

3. **Integration Expansion**
   - External threat feeds
   - SIEM integration
   - Custom analyzers
   - Webhook notifications
