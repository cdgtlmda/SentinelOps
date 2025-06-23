# Test Data Generation Guide

This guide describes the comprehensive test data generation system for SentinelOps, which provides realistic and varied data for all testing scenarios.

## Overview

The test data generation system consists of:

1. **Security Event Generators** - Create realistic security events and incidents
2. **Log Generators** - Generate GCP service logs and system logs
3. **Performance Data Generators** - Create high-volume data for load testing
4. **Edge Case Generators** - Generate unusual data patterns and edge cases
5. **Test Data Manager** - Unified interface for all data generation needs
6. **CLI Tool** - Command-line interface for easy data generation

## Quick Start

### Using the CLI Tool

```bash
# Generate a complete test dataset
python scripts/generate_test_data.py complete --events 1000 --incidents 50

# Generate focused dataset for detection testing
python scripts/generate_test_data.py focused detection

# Generate performance test data
python scripts/generate_test_data.py performance burst --rate 1000 --duration 60

# Generate edge cases
python scripts/generate_test_data.py edge-cases all --count 20

# Stream data in real-time
python scripts/generate_test_data.py stream --rate 100 --duration 300
```

### Programmatic Usage

```python
from tests.generators import TestDataManager, TestDataConfig

# Configure data generation
config = TestDataConfig(
    num_events=1000,
    num_incidents=50,
    include_scenarios=True,
    include_edge_cases=True
)

# Create manager
manager = TestDataManager(config)

# Generate complete dataset
dataset = manager.generate_complete_dataset()

# Access generated data
events = dataset['security_events']
incidents = dataset['incidents']
scenarios = dataset['scenarios']
```

## Data Generators

### Security Event Generator

Generates realistic security events with configurable severity and types:

```python
from tests.generators import SecurityEventGenerator

gen = SecurityEventGenerator()

# Generate single event
event = gen.generate_event(
    event_type="unauthorized_access",
    severity="high"
)

# Generate batch of events
events = gen.generate_batch(
    count=100,
    start_time=datetime.utcnow() - timedelta(hours=24),
    end_time=datetime.utcnow()
)
```

Event types:
- `unauthorized_access` - Failed authentication attempts
- `data_exfiltration` - Suspicious data transfers
- `malware` - Malware detection events
- `privilege_escalation` - Privilege abuse attempts
- `misconfiguration` - Security misconfiguration detection

### Incident Scenario Generator

Creates complete attack scenarios with correlated events:

```python
from tests.generators import IncidentScenarioGenerator

gen = IncidentScenarioGenerator()

# Generate attack scenario
scenario = gen.generate_scenario("brute_force_attack")

# Available scenarios
scenarios = [
    "brute_force_attack",
    "insider_threat",
    "ransomware_infection",
    "misconfiguration_exploit"
]
```

### Log Generator

Generates realistic GCP service logs:

```python
from tests.generators import LogGenerator

gen = LogGenerator()

# Generate compute engine log
log = gen.generate_log_entry(
    service="compute",
    log_type="ssh_login"
)

# Generate batch of mixed logs
logs = gen.generate_mixed_logs(count=1000)
```

Supported services:
- Compute Engine (SSH, processes, system)
- Cloud Storage (object access, bucket operations)
- BigQuery (queries, exports, access)
- IAM (role changes, permissions)

### Performance Data Generator

Creates high-volume data for performance testing:

```python
from tests.generators import PerformanceDataGenerator

gen = PerformanceDataGenerator()

# Generate burst traffic
burst_data = gen.generate_burst_traffic(
    burst_size=10000,
    burst_duration_seconds=60
)

# Generate sustained load
for batch in gen.generate_sustained_load(
    events_per_second=100,
    duration_seconds=300
):
    process_batch(batch)

# Generate stress test data
stress_data = gen.generate_stress_test_data(
    test_type="cpu",
    intensity="high"
)
```

### Edge Case Generator

Generates unusual data patterns to test robustness:

```python
from tests.generators import EdgeCaseGenerator

gen = EdgeCaseGenerator()

# Generate specific edge cases
malformed = gen.generate_edge_cases("malformed_log", count=10)
unicode = gen.generate_edge_cases("unicode_data", count=5)
extreme = gen.generate_edge_cases("extreme_values", count=5)

# Generate security edge cases
security_cases = gen.generate_security_edge_cases()
```

Edge case types:
- `malformed_log` - Invalid log formats
- `missing_fields` - Events with missing required fields
- `extreme_values` - Boundary values and limits
- `unicode_data` - Unicode and encoding challenges
- `nested_complexity` - Deeply nested structures
- `timing_anomaly` - Time-based anomalies
- `null_injection` - Null and undefined values
- `type_confusion` - Type mismatches
- `size_limits` - Size boundary testing

## Test Data Manager

The TestDataManager provides a unified interface for all data generation:

```python
from tests.generators import TestDataManager, TestDataConfig

# Configure generation
config = TestDataConfig(
    # Time range
    start_time=datetime.utcnow() - timedelta(days=7),
    end_time=datetime.utcnow(),
    
    # Volume settings
    num_events=1000,
    num_incidents=50,
    num_resources=100,
    
    # Options
    include_scenarios=True,
    include_edge_cases=True,
    enable_high_volume=False,
    
    # Output settings
    output_dir=Path("tests/data/generated"),
    save_to_file=True
)

manager = TestDataManager(config)

# Generate complete dataset
dataset = manager.generate_complete_dataset()

# Generate focused datasets
detection_data = manager.generate_focused_dataset("detection")
analysis_data = manager.generate_focused_dataset("analysis")

# Generate streaming data
for events in manager.generate_streaming_data(events_per_second=100):
    process_events(events)

# Generate test case specific data
test_data = manager.generate_test_case_data(
    "detection_rule_trigger",
    rule_type="failed_login"
)
```

## CLI Tool Usage

### Complete Dataset Generation

```bash
# Basic usage
python scripts/generate_test_data.py complete

# With options
python scripts/generate_test_data.py complete \
    --events 5000 \
    --incidents 100 \
    --include-scenarios \
    --include-edge-cases \
    --high-volume \
    --output dataset.json \
    --pretty
```

### Focused Dataset Generation

```bash
# Detection-focused data
python scripts/generate_test_data.py focused detection --output detection_test.json

# Analysis-focused data  
python scripts/generate_test_data.py focused analysis --output analysis_test.json

# Available focus areas: detection, analysis, remediation, communication, orchestration
```

### Performance Test Data

```bash
# Burst traffic pattern
python scripts/generate_test_data.py performance burst \
    --rate 5000 \
    --duration 120 \
    --output burst_test.json

# Sustained load pattern
python scripts/generate_test_data.py performance sustained \
    --rate 1000 \
    --duration 600

# Parallel streams
python scripts/generate_test_data.py performance parallel

# Stress test data
python scripts/generate_test_data.py performance stress
```

### Edge Case Generation

```bash
# All edge cases
python scripts/generate_test_data.py edge-cases all --count 50

# Specific edge case types
python scripts/generate_test_data.py edge-cases malformed_log --count 20
python scripts/generate_test_data.py edge-cases unicode_data --count 10
python scripts/generate_test_data.py edge-cases security

# Output formats
python scripts/generate_test_data.py edge-cases all --format jsonl --output edges.jsonl
```

### Streaming Data Generation

```bash
# Basic streaming
python scripts/generate_test_data.py stream

# High-rate streaming
python scripts/generate_test_data.py stream --rate 1000 --duration 300

# Stream to file (JSONL format)
python scripts/generate_test_data.py stream --format jsonl --output stream.jsonl
```

### Advanced Options

```bash
# Set random seed for reproducible data
python scripts/generate_test_data.py complete --seed 42

# Output formats
--format json    # Single JSON document (default)
--format jsonl   # JSON Lines format (one object per line)
--format csv     # CSV format (not yet implemented)

# Pretty printing
--pretty         # Pretty print JSON with indentation

# Output destination
--output file.json  # Save to file (default: stdout)
```

## Data Formats

### Security Event Format

```json
{
  "event_id": "evt_123456",
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "unauthorized_access",
  "severity": "high",
  "source": "auth_service",
  "actor": {
    "user": "john.doe@example.com",
    "ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  },
  "affected_resources": ["project-123", "instance-456"],
  "metadata": {
    "attempts": 5,
    "method": "password",
    "success": false
  },
  "raw_log": "..."
}
```

### Incident Format

```json
{
  "id": "INC-0001",
  "title": "Brute Force Attack Detected",
  "description": "Multiple failed login attempts detected",
  "severity": "high",
  "status": "active",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "events": [...],
  "analysis": {...},
  "tags": ["brute_force", "authentication"]
}
```

### Log Entry Format

```json
{
  "insertId": "log_123456",
  "timestamp": "2024-01-15T10:30:00Z",
  "severity": "WARNING",
  "logName": "projects/test/logs/compute.googleapis.com%2Fsshd",
  "resource": {
    "type": "gce_instance",
    "labels": {
      "instance_id": "123456789",
      "zone": "us-central1-a"
    }
  },
  "jsonPayload": {
    "message": "Failed SSH login attempt",
    "user": "root",
    "sourceIp": "192.168.1.100"
  }
}
```

## Best Practices

### 1. Use Appropriate Data Volumes

```python
# Development testing
config = TestDataConfig(num_events=100, num_incidents=10)

# Integration testing
config = TestDataConfig(num_events=1000, num_incidents=50)

# Performance testing
config = TestDataConfig(
    num_events=10000,
    enable_high_volume=True,
    high_volume_multiplier=10
)
```

### 2. Set Time Ranges Appropriately

```python
# Recent data (last 24 hours)
config = TestDataConfig(
    start_time=datetime.utcnow() - timedelta(hours=24),
    end_time=datetime.utcnow()
)

# Historical data (last month)
config = TestDataConfig(
    start_time=datetime.utcnow() - timedelta(days=30),
    end_time=datetime.utcnow()
)
```

### 3. Use Seeds for Reproducibility

```python
# In tests
import random
random.seed(42)

# CLI
python scripts/generate_test_data.py complete --seed 42
```

### 4. Generate Realistic Distributions

```python
# Configure severity weights
config = TestDataConfig(
    event_severity_weights={
        "critical": 0.02,    # 2% critical
        "high": 0.08,        # 8% high
        "medium": 0.25,      # 25% medium
        "low": 0.50,         # 50% low
        "informational": 0.15 # 15% informational
    }
)
```

### 5. Include Edge Cases in Tests

```python
# Always test with edge cases
dataset = manager.generate_complete_dataset()
edge_cases = dataset.get('edge_cases', [])

for case in edge_cases:
    try:
        process_event(case['data'])
    except Exception as e:
        # Edge cases should be handled gracefully
        log_error(f"Failed to process edge case: {case['type']}")
```

## Integration with Testing

### Unit Tests

```python
import pytest
from tests.generators import SecurityEventGenerator

class TestEventProcessor:
    @pytest.fixture
    def event_gen(self):
        return SecurityEventGenerator()
    
    def test_process_event(self, event_gen):
        event = event_gen.generate_event()
        result = process_event(event)
        assert result.status == "processed"
```

### Integration Tests

```python
from tests.generators import TestDataManager

def test_detection_pipeline():
    manager = TestDataManager()
    dataset = manager.generate_focused_dataset("detection")
    
    # Test detection rules
    for event in dataset['trigger_events']:
        alert = detection_engine.process(event)
        assert alert is not None
```

### Performance Tests

```python
from tests.generators import PerformanceDataGenerator

def test_high_load():
    gen = PerformanceDataGenerator()
    
    start_time = time.time()
    events_processed = 0
    
    for batch in gen.generate_sustained_load(
        events_per_second=1000,
        duration_seconds=60
    ):
        process_batch(batch)
        events_processed += len(batch)
    
    duration = time.time() - start_time
    rate = events_processed / duration
    
    assert rate >= 900  # 90% of target rate
```

## Troubleshooting

### Memory Issues

If generating large datasets causes memory issues:

```python
# Use streaming instead of batch generation
for events in manager.generate_streaming_data(events_per_second=100):
    # Process and discard each batch
    process_and_save(events)
```

### Slow Generation

For faster generation:

```python
# Disable file saving
config = TestDataConfig(save_to_file=False)

# Use simpler data
config = TestDataConfig(
    include_scenarios=False,
    include_edge_cases=False
)
```

### Invalid Data

If generated data seems invalid:

```python
# Check configuration
print(manager.config.__dict__)

# Validate generated data
from jsonschema import validate
validate(event, event_schema)
```

## Extending the Generators

To add custom generators:

```python
class CustomEventGenerator:
    def generate_event(self, **kwargs):
        return {
            "event_type": "custom",
            "timestamp": datetime.utcnow().isoformat(),
            "custom_field": "custom_value",
            **kwargs
        }

# Register with manager
manager = TestDataManager()
manager.custom_gen = CustomEventGenerator()
```