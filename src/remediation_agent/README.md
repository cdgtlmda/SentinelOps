# SentinelOps Remediation Agent

The Remediation Agent is a critical component of the SentinelOps security platform that executes automated response actions to security incidents in Google Cloud Platform environments.

## Features

### Core Capabilities
- **Automated Remediation**: Execute pre-defined remediation actions based on security analysis
- **Safety Mechanisms**: Built-in validation, approval workflows, and rollback capabilities
- **Multi-Resource Support**: Actions for Compute, IAM, Storage, and Network resources
- **Dry-Run Mode**: Test remediation actions safely without making actual changes
- **Performance Optimization**: Caching, batching, and concurrent execution

### Supported Remediation Actions

#### Network Security
- Block suspicious IP addresses
- Update firewall rules
- Configure Cloud Armor policies
- Modify VPC security settings

#### Identity & Access Management
- Disable compromised user accounts
- Revoke IAM permissions
- Remove service account keys
- Enable MFA requirements

#### Compute Resources
- Quarantine infected instances
- Stop/start instances
- Create instance snapshots
- Apply security patches

#### Storage Security
- Update bucket permissions
- Enable versioning
- Set retention policies
- Apply encryption

#### Credentials & Logging
- Rotate credentials
- Revoke API keys
- Enable audit logging
- Increase log retention

## Architecture

The Remediation Agent consists of several key components:

1. **Agent Core** (`agent.py`): Main orchestration and message handling
2. **Action Registry** (`action_registry.py`): Manages action definitions and implementations
3. **Execution Engine** (`execution_engine.py`): Priority queuing and concurrent execution
4. **Safety Mechanisms** (`safety_mechanisms.py`): Validation, approvals, and rollback
5. **Integrations** (`integrations.py`): Communication with other SentinelOps agents
6. **Security** (`security.py`): Authorization, audit logging, and credential management
7. **Performance** (`performance.py`): Caching, batching, and monitoring

## Usage

### Basic Setup

```python
from src.remediation_agent import RemediationAgent

# Configure the agent
config = {
    "project_id": "your-gcp-project",
    "dry_run_mode": True,  # Start in dry-run for safety
    "max_concurrent_actions": 5,
    "max_api_calls_per_minute": 60,
    "action_timeout_seconds": 300,
}

# Create and start the agent
agent = RemediationAgent(config)
await agent.run()
```

### Processing Remediation Recommendations

The agent receives recommendations from the Analysis Agent via Pub/Sub:

```python
# Example message from Analysis Agent
message = {
    "incident_id": "incident-123",
    "actions": [
        {
            "action_type": "block_ip_address",
            "description": "Block suspicious IP",
            "target_resource": "192.168.1.100",
            "params": {
                "ip_address": "192.168.1.100",
                "project_id": "your-project"
            }
        }
    ]
}
```

### Testing with Dry-Run Mode

Always test remediation actions in dry-run mode first:

```python
from src.remediation_agent.testing_harness import (
    MockGCPResponses,
    DryRunSimulator,
    create_test_action
)

# Create test action
test_action = create_test_action("stop_instance", {
    "instance_name": "test-vm",
    "zone": "us-central1-a",
    "project_id": "test-project"
})

# Run in dry-run mode
simulator = DryRunSimulator()
result = simulator.simulate_action(test_action, action_def)
```

### Security and Authorization

The agent implements multiple security layers:

```python
from src.remediation_agent.security import (
    SecurityContext,
    AuthorizationLevel,
    ActionAuthorizer
)

# Create security context
security_context = SecurityContext(
    principal="remediation-sa@project.iam.gserviceaccount.com",
    auth_level=AuthorizationLevel.ELEVATED,
    permissions={"compute.instances.stop", "compute.firewalls.create"}
)

# Authorize action
authorizer = ActionAuthorizer(project_id)
authorized, reason = authorizer.authorize_action(action, security_context)
```

## Configuration

### Environment Variables

```bash
# Core Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Agent Settings
REMEDIATION_DRY_RUN=true
REMEDIATION_MAX_CONCURRENT=5
REMEDIATION_TIMEOUT_SECONDS=300

# Pub/Sub Topics
PUBSUB_TOPIC_REMEDIATION=remediation-recommendations
PUBSUB_TOPIC_APPROVALS=approval-requests
PUBSUB_TOPIC_ACTION_RESULTS=action-results
```

### Action Risk Levels

Actions are categorized by risk level:
- **LOW**: Minimal impact, easily reversible (e.g., enable logging)
- **MEDIUM**: Moderate impact, reversible (e.g., update firewall rule)
- **HIGH**: Significant impact, difficult to reverse (e.g., stop instance)
- **CRITICAL**: Major impact, may be irreversible (e.g., rotate credentials)

## Safety Features

### Pre-Execution Validation
- Resource existence verification
- Permission checks
- Parameter validation
- Conflict detection

### Approval Workflows
- Critical actions require manual approval
- Auto-approval for low-risk actions in dev/test
- Configurable approval policies

### Rollback Capabilities
- Automatic state snapshots before execution
- Rollback plans for reversible actions
- Automatic rollback on failure

### Audit Logging
- All actions logged with full context
- Integration with Cloud Logging
- Tamper-proof audit trail

## Performance Optimization

### Caching
- Results cached for idempotent operations
- Configurable TTL per action type
- Redis support for distributed caching

### Batch Operations
- Automatic batching of similar operations
- Reduced API calls and improved throughput
- Configurable batch sizes and timeouts

### Monitoring
- Real-time performance metrics
- Integration with Cloud Monitoring
- Alerting on performance degradation

## Development and Testing

### Running Tests

```bash
# Run unit tests
pytest tests/remediation_agent/

# Run integration tests
pytest tests/integration/remediation/

# Run with coverage
pytest --cov=src.remediation_agent tests/
```

### Adding New Actions

1. Define the action in `action_registry.py`:
```python
self.register_definition(ActionDefinition(
    action_type="your_new_action",
    display_name="Your New Action",
    description="Description of what it does",
    category=ActionCategory.NETWORK_SECURITY,
    risk_level=ActionRiskLevel.MEDIUM,
    required_params=["param1", "param2"],
    required_permissions=["compute.something.do"],
    is_reversible=True,
    requires_approval=False,
))
```

2. Implement the action class:
```python
class YourNewAction(BaseRemediationAction):
    async def execute(self, action, gcp_clients, dry_run=False):
        # Implementation
        pass
    
    async def validate_prerequisites(self, action, gcp_clients):
        # Validation logic
        pass
    
    async def capture_state(self, action, gcp_clients):
        # State capture for rollback
        pass
    
    def get_rollback_definition(self):
        # Rollback definition
        pass
```

3. Register the implementation:
```python
self._action_registry.register_implementation(
    "your_new_action", YourNewAction
)
```

## Troubleshooting

### Common Issues

1. **Action not executing**: Check if in dry-run mode
2. **Permission denied**: Verify service account permissions
3. **Rate limit exceeded**: Adjust max_api_calls_per_minute
4. **Timeout errors**: Increase action_timeout_seconds

### Debug Mode

Enable debug logging:
```python
config["debug"] = True
config["log_level"] = "DEBUG"
```

## Best Practices

1. **Always start in dry-run mode** when deploying to new environments
2. **Monitor execution metrics** to optimize performance
3. **Review audit logs regularly** for security compliance
4. **Test rollback procedures** for critical actions
5. **Keep action implementations idempotent** where possible
6. **Document custom actions thoroughly** for team members

## Security Considerations

- Service account should have minimal required permissions
- Enable audit logging for all remediation actions
- Regularly rotate service account keys
- Monitor for unusual remediation patterns
- Implement alerting for failed remediation attempts

## License

This component is part of the SentinelOps platform and is subject to the project's licensing terms.
