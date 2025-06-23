# SentinelOps Demo Script

## Duration: 3 minutes

## Introduction (30 seconds)
- **Hook**: "What if your cloud infrastructure could defend itself against threats in real-time?"
- **Problem Statement**:
  - Security teams are overwhelmed with alerts
  - Manual incident response is slow and error-prone
  - Cloud environments are complex and constantly changing
- **Solution Introduction**: "SentinelOps - An AI-powered, multi-agent security platform built with Google's ADK"

## Architecture Overview (30 seconds)
- **Show architecture diagram**
- **Key Components**:
  - 5 specialized AI agents working in harmony
  - Detection Agent: Monitors for threats 24/7
  - Analysis Agent: Powered by Gemini AI for intelligent threat assessment
  - Remediation Agent: Takes automated corrective actions
  - Communication Agent: Keeps teams informed
  - Orchestration Agent: Coordinates the entire response
- **Google Cloud Integration**: BigQuery, Vertex AI, Cloud Run, Pub/Sub

## Live Demo - Attack Scenario (1 minute 30 seconds)

### Scenario 1: SSH Brute Force Attack (30 seconds)
1. **Run attack simulator**: `python demo/attack_simulator.py --scenario brute_force`
2. **Show Detection**:
   - Real-time alert appears in dashboard
   - Detection Agent identifies pattern of failed login attempts
3. **Show Analysis**:
   - Gemini AI analyzes the threat severity
   - Provides context about the attacking IP
4. **Show Remediation**:
   - Automatically blocks the IP in firewall
   - Enforces SSH key-only authentication
5. **Show Communication**:
   - Slack notification sent to security team
   - Incident ticket created automatically

### Scenario 2: Data Exfiltration (30 seconds)
1. **Trigger exfiltration**: Show unusual data transfer
2. **Detection**: Anomaly detection identifies unusual transfer volume
3. **Analysis**: AI determines this is 20x normal traffic
4. **Remediation**:
   - Revokes compromised credentials
   - Blocks destination IP
5. **Communication**: Critical alert with full incident report

### Scenario 3: Privilege Escalation (30 seconds)
1. **Show unauthorized IAM change**
2. **Immediate detection and analysis**
3. **Automatic rollback of dangerous permissions**
4. **Detailed audit trail and notifications**

## Key Benefits & Metrics (20 seconds)
- **Response Time**: From detection to remediation in < 5 minutes (vs hours manually)
- **Coverage**: 24/7 automated monitoring
- **Accuracy**: AI-powered analysis reduces false positives by 80%
- **Cost Savings**: Reduce security operations costs by 60%
- **Compliance**: Automated audit trails and reporting

## Technical Innovation (20 seconds)
- **ADK Integration**: Leverages Google's Agent Development Kit for robust multi-agent coordination
- **Explainable AI**: Every decision includes reasoning and confidence scores
- **Modular Architecture**: Easy to extend with new detection rules and response actions
- **Cloud-Native**: Fully serverless, scales automatically

## Closing (20 seconds)
- **Impact**: "SentinelOps transforms reactive security into proactive defense"
- **Call to Action**:
  - Visit the GitHub: github.com/cdgtlmda/SentinelOps
  - Try the demo: [demo URL]
  - Read the blog post about building with ADK
- **Thank You**: "Thank you for watching! Questions? Reach out at [contact]"

---

## Demo Preparation Checklist
- [ ] Start Cloud Run service
- [ ] Ensure BigQuery has sample data
- [ ] Test attack simulator scripts
- [ ] Open dashboard in browser
- [ ] Have Slack channel ready for notifications
- [ ] Terminal ready with commands pre-typed
- [ ] Architecture diagram open in separate tab
- [ ] Backup slides ready in case of technical issues

## Talking Points for Q&A
1. **How does it handle false positives?**
   - Gemini AI provides confidence scores
   - Remediation actions are reversible
   - Continuous learning from security team feedback

2. **What makes this different from existing solutions?**
   - True multi-agent collaboration using ADK
   - Combines detection, analysis, AND automated response
   - Explainable AI decisions

3. **How does it scale?**
   - Serverless architecture on Cloud Run
   - Auto-scaling based on load
   - Distributed agent processing

4. **Security of the platform itself?**
   - Least privilege IAM policies
   - Encrypted secrets management
   - Audit logging of all actions

## Backup Plan
If live demo fails:
1. Show pre-recorded video of the three scenarios
2. Walk through static screenshots
3. Focus on architecture and benefits
4. Show code snippets of interesting agent interactions
