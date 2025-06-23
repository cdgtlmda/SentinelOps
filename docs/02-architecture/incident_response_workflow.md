# SentinelOps Incident Response Workflow

The following sequence diagram illustrates the complete incident response workflow in the SentinelOps multi-agent architecture.

```mermaid
sequenceDiagram
    autonumber
    participant BQ as BigQuery
    participant Det as Detection Agent
    participant Orch as Orchestrator Agent
    participant Ana as Analysis Agent
    participant Gem as Gemini AI
    participant Rem as Remediation Agent
    participant CF as Cloud Functions
    participant Com as Communication Agent
    participant ST as Security Team
    participant SL as Slack/Email
    participant FS as Firestore

    Note over Det,ST: Incident Detection Phase

    BQ->>Det: Security log data
    activate Det
    Det->>Det: Apply detection rules
    Det->>Det: Generate security events
    Det->>Det: Correlate events
    Det->>Orch: new_incident (incidents.orchestration)
    deactivate Det

    activate Orch
    Orch->>FS: Store incident details

    Note over Det,ST: Analysis Phase

    Orch->>Ana: analyze_incident (incidents.analysis)
    activate Ana
    Ana->>FS: Retrieve incident data
    Ana->>Ana: Extract event information
    Ana->>Gem: Generate AI prompt with incident data
    Gem->>Ana: AI analysis and explanation
    Ana->>Ana: Process AI response
    Ana->>Ana: Create analysis result
    Ana->>Orch: analysis_complete (incidents.orchestration)
    deactivate Ana

    Orch->>FS: Update incident with analysis

    Note over Det,ST: Remediation Planning Phase

    Orch->>Rem: propose_remediation (incidents.remediation)
    activate Rem
    Rem->>Rem: Evaluate incident severity
    Rem->>Gem: Request remediation suggestions
    Gem->>Rem: Proposed remediation actions
    Rem->>Rem: Generate action plan
    Rem->>Orch: remediation_proposed (incidents.orchestration)
    deactivate Rem

    Orch->>FS: Update incident with remediation plan

    Note over Det,ST: Approval Phase

    alt Approval Required
        Orch->>Com: request_approval (incidents.communication)
        activate Com
        Com->>Com: Determine recipients
        Com->>Com: Generate message content
        Com->>SL: approval_required notification
        SL->>ST: Deliver approval request
        ST->>SL: Approve/reject actions
        SL->>Com: User response
        Com->>Orch: actions_approved (incidents.orchestration)
        deactivate Com
    end

    Note over Det,ST: Remediation Execution Phase

    Orch->>Rem: execute_remediation (incidents.remediation)
    activate Rem
    Rem->>CF: Execute cloud function for remediation
    CF->>CF: Perform remediation actions
    CF->>Rem: Action results
    Rem->>Rem: Verify effectiveness
    Rem->>Rem: Document results
    Rem->>Orch: remediation_complete (incidents.orchestration)
    deactivate Rem

    Orch->>FS: Update incident with remediation results

    Note over Det,ST: Communication Phase

    Orch->>Com: send_notification (incidents.communication)
    activate Com
    Com->>Com: Determine recipients
    Com->>Com: Generate resolution message
    Com->>SL: incident_resolved notification
    SL->>ST: Deliver resolution notification
    Com->>Orch: notification_sent (incidents.orchestration)
    deactivate Com

    Orch->>FS: Update incident with communication log
    Orch->>FS: Mark incident as resolved
    deactivate Orch

    Note over Det,ST: Optional Post-Incident Review

    opt Post-Incident Review
        ST->>Com: Request incident report
        activate Com
        Com->>FS: Retrieve complete incident data
        Com->>Com: Generate comprehensive report
        Com->>ST: Deliver incident report
        deactivate Com
    end
```

## Workflow Explanation

This diagram shows the complete incident response workflow in SentinelOps:

1. **Detection Phase**: The Detection Agent monitors BigQuery logs, applies detection rules, and creates incidents when suspicious activity is found.

2. **Analysis Phase**: The Orchestrator coordinates with the Analysis Agent, which uses Gemini AI to assess the incident's severity and impact.

3. **Remediation Planning**: The Remediation Agent works with Gemini AI to develop an action plan based on the incident analysis.

4. **Approval Workflow**: For incidents requiring human oversight, the Communication Agent manages the interaction with the Security Team via Slack or email.

5. **Remediation Execution**: Upon approval, remediation actions are executed through Cloud Functions to address the security issue.

6. **Resolution Communication**: The Communication Agent notifies all stakeholders of incident resolution and outcomes.

7. **Post-Incident Review**: An optional comprehensive incident report can be generated for review and future improvements.

All incident data is persisted in Firestore throughout the workflow, and the Gemini AI integration provides intelligent analysis and remediation planning.
