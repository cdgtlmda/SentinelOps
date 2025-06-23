# Frequently Asked Questions (FAQ)

**Last Updated**: June 11, 2025

## General Questions

### What is SentinelOps?
SentinelOps is an AI-powered Security Orchestration, Automation, and Response (SOAR) platform built on Google's Agent Development Kit (ADK). It provides automated detection, analysis, and remediation of security incidents in Google Cloud Platform environments.

### How is SentinelOps different from traditional SIEM/SOAR solutions?
- **AI-Native**: Built with AI at its core using Google's ADK and Gemini
- **Multi-Agent Architecture**: Specialized agents handle different aspects of security operations
- **Cloud-Native**: Designed specifically for GCP environments
- **Autonomous Operation**: Can detect, analyze, and remediate incidents without human intervention
- **Cost-Effective**: Serverless architecture with usage-based pricing

### What are the main components of SentinelOps?
1. **Detection Agent**: Monitors logs and metrics for security threats
2. **Analysis Agent**: Uses Gemini AI to analyze incidents
3. **Remediation Agent**: Executes response actions
4. **Communication Agent**: Sends notifications and alerts
5. **Orchestrator Agent**: Coordinates multi-agent workflows

### Is SentinelOps open source?
Yes, SentinelOps is open source under the MIT License. You can find the source code at [https://github.com/cdgtlmda/SentinelOps](https://github.com/cdgtlmda/SentinelOps).

## Technical Questions

### What is Google ADK and why use it?
Google Agent Development Kit (ADK) is a framework for building AI agents that can:
- Use tools to interact with external systems
- Collaborate with other agents
- Leverage Google's AI models
- Integrate seamlessly with Google Cloud services

ADK provides the foundation for SentinelOps' autonomous capabilities.

### What programming language is SentinelOps written in?
SentinelOps is primarily written in Python 3.11+. The choice of Python allows for:
- Easy integration with Google Cloud APIs
- Rich ecosystem of security and data analysis libraries
- Rapid development and deployment
- Strong community support

### Does SentinelOps require Kubernetes?
No, SentinelOps uses Cloud Run, which is a managed serverless platform. This eliminates the complexity of managing Kubernetes clusters while providing similar scalability benefits.

### What databases does SentinelOps use?
- **Firestore**: Primary database for incidents, rules, and state management
- **BigQuery**: For log analysis and historical data
- **Cloud Storage**: For long-term archival and large file storage

### Can I use my own AI models instead of Gemini?
While SentinelOps is designed to work with Gemini, the ADK framework allows for customization. You would need to:
1. Implement a custom analysis tool extending `BaseTool`
2. Configure the Analysis Agent to use your tool
3. Handle API authentication and rate limiting

## Deployment Questions

### What are the minimum GCP services required?
Essential services:
- Cloud Run (for agents)
- Firestore (for data storage)
- Cloud Logging (for log ingestion)
- Cloud IAM (for security)
- Pub/Sub (for messaging)

Additional recommended services:
- BigQuery (for advanced analytics)
- Cloud Monitoring (for metrics)
- Cloud Armor (for IP blocking)

### How much does it cost to run SentinelOps?
Costs vary based on usage, but typical monthly costs for a medium-sized deployment:
- Cloud Run: $50-200 (depending on traffic)
- Firestore: $20-100 (based on storage and operations)
- BigQuery: $5-50 (query volume dependent)
- Gemini API: $10-100 (analysis frequency)
- Other services: $20-50

Total: ~$100-500/month for most deployments

### Can I deploy SentinelOps on-premises?
SentinelOps is designed for cloud deployment. While technically possible to adapt for on-premises, you would need to:
- Replace GCP services with equivalents
- Modify authentication mechanisms
- Implement your own scaling solution
- Handle ADK compatibility

### How do I handle multi-region deployment?
SentinelOps supports multi-region deployment through:
1. Deploy agents in multiple regions
2. Use Firestore multi-region replication
3. Configure Cloud Load Balancing
4. Set up cross-region Pub/Sub topics

See the [Multi-Region HA Guide](../02-architecture/multi-region-ha-guide.md) for details.

## Security Questions

### How does SentinelOps handle sensitive data?
- **Encryption at Rest**: All data in Firestore and Cloud Storage is encrypted
- **Encryption in Transit**: TLS 1.2+ for all communications
- **Access Control**: Fine-grained IAM policies
- **Audit Logging**: All actions are logged in Cloud Audit Logs
- **Secrets Management**: Integration with Secret Manager for API keys

### What compliance certifications does SentinelOps support?
SentinelOps inherits GCP's compliance certifications. Additional compliance depends on your configuration:
- Enable audit logging for SOC 2
- Configure data retention for GDPR
- Implement access controls for HIPAA
- Use Customer-Managed Encryption Keys (CMEK) for PCI DSS

### Can SentinelOps access my application data?
SentinelOps only accesses:
- Security logs and metrics
- GCP resource metadata
- Data you explicitly configure it to monitor

It does not access application data unless specifically configured to do so.

### How do I ensure SentinelOps doesn't take harmful actions?
- **Dry Run Mode**: Test all remediation actions before enabling
- **Approval Workflows**: Require human approval for critical actions
- **Rate Limiting**: Prevent excessive actions
- **Rollback Capability**: Undo remediation actions if needed
- **Audit Trails**: Complete logging of all actions taken

## Operations Questions

### How do I add custom detection rules?
1. Access the Firestore `rules` collection
2. Create a new document with your rule definition
3. Include conditions (queries, patterns, thresholds)
4. Define actions (notify, remediate, escalate)
5. Enable the rule

See [Detection Agent Rules](../02-architecture/agents/detection-agent-rules.md) for examples.

### How do I integrate with my existing SIEM?
SentinelOps can integrate through:
- **Webhook notifications**: Send alerts to your SIEM
- **API endpoints**: Pull data from SentinelOps
- **Log forwarding**: Export to SIEM-compatible formats
- **Custom Communication Tools**: Build integrations using ADK

### What notification channels are supported?
Built-in support for:
- Slack (webhooks and OAuth)
- Email (SMTP/SendGrid)
- SMS (Twilio)
- Generic webhooks
- Google Chat

Custom channels can be added by extending the Communication Agent.

### How do I monitor SentinelOps itself?
- **Cloud Monitoring dashboards**: Pre-built dashboards for agent health
- **Custom metrics**: Agent-specific performance metrics
- **Alerting policies**: Notifications for agent failures
- **Health checks**: Automated endpoint monitoring
- **Log analysis**: Cloud Logging queries for troubleshooting

### Can I disable specific agents?
Yes, you can:
1. Scale Cloud Run service to 0 instances
2. Disable agent in system configuration
3. Remove IAM permissions
4. Stop Pub/Sub subscriptions

## Troubleshooting Questions

### Why aren't my detection rules triggering?
Common causes:
1. Rules are disabled in Firestore
2. Time windows are too narrow
3. Log ingestion delays
4. Incorrect query syntax
5. Missing IAM permissions

Check the [ADK Troubleshooting Guide](../04-operations/adk-troubleshooting.md).

### Why is the Analysis Agent slow?
Possible reasons:
- High Gemini API latency
- Large incident data size
- Rate limiting in effect
- Cold starts on Cloud Run

Enable caching in the Performance Optimizer to improve response times.

### How do I debug agent communication issues?
1. Check Pub/Sub subscription acknowledgments
2. Verify IAM permissions for service accounts
3. Review agent logs in Cloud Logging
4. Test with the transfer tools directly
5. Enable debug logging in agents

### What do I do if an agent crashes?
Cloud Run automatically restarts crashed containers. To investigate:
1. Check Cloud Logging for error messages
2. Review Cloud Error Reporting
3. Verify resource limits aren't exceeded
4. Check for Firestore quota issues
5. Test with increased memory allocation

## Development Questions

### How do I create a custom ADK tool?
1. Extend the `BaseTool` class
2. Implement the `execute()` method
3. Define input parameters
4. Add error handling
5. Write unit tests
6. Register with the appropriate agent

See [ADK Tool Reference](./adk-tool-reference.md) for examples.

### How do I test agents locally?
1. Install ADK: `pip install -e ./adk`
2. Set up local Firestore emulator
3. Configure environment variables
4. Use test fixtures for GCP services
5. Run agents with `--debug` flag

Details in [Local Development Guide](../05-development/local-development-guide.md).

### Can I contribute to SentinelOps?
Yes! We welcome contributions. Please:
1. Read [CONTRIBUTING.md](../../CONTRIBUTING.md)
2. Check existing issues on GitHub
3. Follow the code style guide
4. Write tests for new features
5. Submit a pull request

### Where can I get help?
- **Documentation**: Start with this comprehensive documentation
- **GitHub Issues**: [https://github.com/cdgtlmda/SentinelOps/issues](https://github.com/cdgtlmda/SentinelOps/issues)
- **Discussions**: GitHub Discussions for questions
- **Email**: cdgtlmda@pm.me for security issues

## Performance Questions

### How many incidents can SentinelOps handle?
Performance scales with Cloud Run instances:
- Single instance: ~10-50 incidents/minute
- Auto-scaled: 1000+ incidents/minute
- With caching: 5000+ incidents/minute

Actual performance depends on incident complexity and analysis depth.

### How can I reduce Gemini API costs?
1. Enable the Performance Optimizer caching
2. Batch similar incidents for analysis
3. Adjust analysis depth based on severity
4. Use rate limiting to control costs
5. Implement local analysis for simple incidents

### What's the typical incident response time?
- Detection: 1-5 seconds (from log entry)
- Analysis: 2-10 seconds (with Gemini)
- Remediation: 1-30 seconds (action dependent)
- Notification: <1 second

Total: 5-45 seconds from incident to remediation

### How do I scale for large environments?
1. Enable auto-scaling on Cloud Run
2. Use regional deployments
3. Implement caching strategies
4. Optimize detection rules
5. Use BigQuery for historical analysis
6. Partition Firestore collections

## Migration Questions

### How do I migrate from another SOAR platform?
1. Export rules in a compatible format
2. Map rule conditions to SentinelOps format
3. Convert playbooks to multi-agent workflows
4. Migrate historical incident data
5. Run both systems in parallel initially
6. Gradually transition workflows

### Can I import existing detection rules?
Yes, with some conversion:
- Splunk: Convert SPL to BigQuery SQL
- Elastic: Transform DSL queries
- Sigma: Use sigma-to-bigquery converter
- YARA: Implement as custom detection tools

### What about my existing integrations?
Most integrations can be preserved by:
- Using webhook compatibility
- Implementing custom communication tools
- Building API adapters
- Leveraging existing notification channels

## Future Questions

### What's on the roadmap?
Current priorities include:
- Additional cloud provider support
- Enhanced ML models for detection
- More remediation actions
- Improved visualization dashboards
- Extended third-party integrations

### Will there be a managed service version?
While not currently available, a managed SaaS version could simplify deployment for organizations that prefer not to manage infrastructure.

## UI and Interface

### Does SentinelOps include a web interface?

Yes, SentinelOps includes a production-ready web interface located in the `/frontend/sentinelops-ui` directory. It features:

- Modern React dashboard with real-time updates
- Interactive incident management
- Agent status monitoring
- Threat simulation interface
- Interactive analytics and reporting

The main interface runs on port 3000 by default and connects to the API server on port 8000. The monorepo also includes a marketing site on port 3001. See the [Quick Start Guide](../01-getting-started/quick-start.md) for setup instructions.

## Related Documentation

- [Introduction](../01-getting-started/introduction.md)
- [Architecture Overview](../02-architecture/architecture.md)
- [Quick Start Guide](../01-getting-started/quick-start.md)
- [Troubleshooting Guide](../04-operations/adk-troubleshooting.md)
- [Contributing Guide](../../CONTRIBUTING.md)
