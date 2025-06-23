# Glossary of Terms

**Last Updated**: June 11, 2025

## A

**ADK (Agent Development Kit)**  
Google's framework for building AI agents that can use tools, collaborate with other agents, and integrate with Google Cloud services. The core framework powering SentinelOps.

**Agent**  
An autonomous component in SentinelOps that performs specific security operations tasks. Examples include Detection Agent, Analysis Agent, and Remediation Agent.

**Agent State**  
The current operational status and health metrics of an agent, stored in Firestore and used for orchestration decisions.

**Analysis Agent**  
The SentinelOps agent responsible for analyzing security incidents using Gemini AI to determine root causes, assess impact, and recommend remediation actions.

**Anomaly Detection**  
The process of identifying patterns in data that do not conform to expected behavior, used by the Detection Agent to identify potential security threats.

**API (Application Programming Interface)**  
A set of protocols and tools for building software applications. SentinelOps uses various GCP APIs for its operations.

## B

**BaseTool**  
The foundational ADK class that all SentinelOps tools extend from, providing standard interfaces for tool execution.

**BigQuery**  
Google's serverless data warehouse used by SentinelOps for log analysis and security event queries.

**Bulk Operations**  
Processing multiple items in a single operation for improved performance, used throughout SentinelOps for efficiency.

## C

**Circuit Breaker**  
A design pattern that prevents cascading failures by temporarily blocking operations to a failing service.

**Cloud Armor**  
Google Cloud's DDoS protection and WAF service, used by the Remediation Agent to block malicious IPs.

**Cloud Functions**  
Serverless compute platform used for event-driven processing and scheduled tasks in SentinelOps.

**Cloud Logging**  
Google's log management service that collects and stores logs from GCP resources, monitored by the Detection Agent.

**Cloud Monitoring**  
Google's observability platform that provides metrics, dashboards, and alerting capabilities.

**Cloud Run**  
Google's managed compute platform for deploying containerized applications, used to host SentinelOps agents.

**Communication Agent**  
The SentinelOps agent responsible for sending notifications through various channels (Slack, email, SMS).

**Correlation**  
The process of connecting related security events across different sources to identify complex attack patterns.

## D

**Detection Agent**  
The SentinelOps agent that monitors logs and metrics to identify security incidents using rules and anomaly detection.

**Dry Run**  
A mode where remediation actions are simulated but not actually executed, used for testing and validation.

**DDoS (Distributed Denial of Service)**  
A type of cyber attack that SentinelOps can detect and mitigate automatically.

## E

**Event Correlation**  
The process of analyzing relationships between multiple security events to identify attack patterns.

**Event-Driven Architecture**  
A software architecture pattern where components communicate through events, used in SentinelOps for agent coordination.

## F

**False Positive**  
A security alert that incorrectly indicates malicious activity when none exists.

**Firestore**  
Google's NoSQL document database used by SentinelOps for storing incidents, rules, and system state.

**Forensic Snapshot**  
A point-in-time copy of a disk or system state created for security investigation purposes.

## G

**GCP (Google Cloud Platform)**  
The cloud computing platform that hosts SentinelOps and provides the services it monitors.

**Gemini**  
Google's advanced AI model used by the Analysis Agent for intelligent incident analysis.

**gRPC**  
A high-performance RPC framework used for some internal GCP service communications.

## H

**High Availability (HA)**  
System design that ensures continuous operation even when components fail.

**Horizontal Scaling**  
Adding more instances of a service to handle increased load, supported by SentinelOps architecture.

## I

**IAM (Identity and Access Management)**  
Google Cloud's service for managing access to resources, monitored by SentinelOps for security violations.

**Incident**  
A security event that requires investigation or response, the primary work unit in SentinelOps.

**Incident Response**  
The organized approach to addressing and managing security incidents.

**Infrastructure as Code (IaC)**  
Managing infrastructure through code, used for SentinelOps deployment with Terraform.

## J

**JSON (JavaScript Object Notation)**  
A data format used extensively in SentinelOps for configuration and data exchange.

**JWT (JSON Web Token)**  
An authentication token format used for secure communication between services.

## K

**KMS (Key Management Service)**  
Google Cloud's service for managing cryptographic keys, used for securing sensitive data.

## L

**LLM (Large Language Model)**  
The type of AI model (like Gemini) used by the Analysis Agent for natural language processing.

**Load Balancer**  
Distributes incoming traffic across multiple instances of a service for reliability and performance.

**Log Sink**  
A Cloud Logging configuration that routes logs to specific destinations for processing.

## M

**Machine Learning (ML)**  
Technology used in SentinelOps for anomaly detection and pattern recognition.

**Multi-Agent System**  
An architecture where multiple specialized agents collaborate to solve complex problems.

**Multi-Region**  
Deployment across multiple geographic regions for improved availability and performance.

## N

**Notification Channel**  
A configured destination for alerts (Slack, email, SMS, webhook).

## O

**Orchestrator Agent**  
The SentinelOps agent that coordinates workflows between other agents.

**OAuth 2.0**  
An authorization framework used for secure API access.

## P

**ParallelAgent**  
An ADK class for agents that can execute multiple tasks concurrently.

**Performance Optimizer**  
Component that implements caching, batching, and rate limiting to reduce costs and improve speed.

**Pub/Sub**  
Google's messaging service used for asynchronous communication between agents.

**Python**  
The primary programming language used to develop SentinelOps.

## Q

**Query Builder**  
A component that constructs BigQuery SQL queries for log analysis.

**Queue**  
A data structure used for managing tasks and messages between agents.

## R

**Rate Limiting**  
Controlling the frequency of operations to prevent overload and manage costs.

**Remediation**  
Actions taken to resolve or mitigate security incidents.

**Remediation Agent**  
The SentinelOps agent that executes response actions like blocking IPs or isolating VMs.

**REST API**  
An architectural style for web services, used for some SentinelOps integrations.

**Rollback**  
The ability to undo a remediation action if needed.

**Root Cause Analysis**  
Determining the fundamental reason for a security incident.

**Rules Engine**  
Component that evaluates detection rules against incoming events.

## S

**SDK (Software Development Kit)**  
A collection of tools for developing applications, such as the Google Cloud SDK.

**Security Operations Center (SOC)**  
Team responsible for monitoring and responding to security incidents.

**Service Account**  
A special Google account used by applications to authenticate with GCP services.

**Severity Level**  
Classification of incident importance (CRITICAL, HIGH, MEDIUM, LOW).

**SIEM (Security Information and Event Management)**  
Traditional security monitoring systems that SentinelOps enhances with AI.

**SLO (Service Level Objective)**  
Performance targets for system availability and response time.

**SOAR (Security Orchestration, Automation and Response)**  
The category of security tools that SentinelOps belongs to.

**State Management**  
Tracking and coordinating the status of agents and workflows.

## T

**Terraform**  
Infrastructure as Code tool used for deploying SentinelOps to GCP.

**Threat Intelligence**  
Information about current security threats used to enhance detection.

**Time Series**  
Data points indexed in time order, used for metrics and anomaly detection.

**Tool**  
In ADK context, a class that provides specific functionality to agents.

**ToolContext**  
ADK object that provides execution context to tools.

**ToolResult**  
ADK object returned by tools to indicate success/failure and provide data.

**Transfer Tool**  
Special ADK tools that enable agents to hand off tasks to other agents.

**TTL (Time To Live)**  
Duration for which cached data remains valid.

## U

**UUID (Universally Unique Identifier)**  
A standardized 128-bit identifier used for various IDs in SentinelOps.

## V

**VPC (Virtual Private Cloud)**  
Isolated network environment in Google Cloud.

**VM (Virtual Machine)**  
Compute instances that can be isolated by the Remediation Agent during incidents.

## W

**WAF (Web Application Firewall)**  
Security layer that protects web applications, integrated with Cloud Armor.

**Webhook**  
HTTP callback used for real-time notifications.

**Workflow**  
A coordinated sequence of agent actions to respond to an incident.

**Workflow Engine**  
Component that manages multi-step incident response processes.

## Y

**YAML**  
Data serialization format used for configuration files.

## Z

**Zero Trust**  
Security model that assumes no implicit trust, implemented in SentinelOps access controls.

**Zone**  
Geographic location within a GCP region where resources are deployed.

## Acronyms Quick Reference

- **ADK**: Agent Development Kit
- **API**: Application Programming Interface  
- **CPU**: Central Processing Unit
- **CRUD**: Create, Read, Update, Delete
- **DDoS**: Distributed Denial of Service
- **DNS**: Domain Name System
- **GCP**: Google Cloud Platform
- **GKE**: Google Kubernetes Engine
- **HTTP**: Hypertext Transfer Protocol
- **HTTPS**: HTTP Secure
- **IAM**: Identity and Access Management
- **IP**: Internet Protocol
- **JSON**: JavaScript Object Notation
- **JWT**: JSON Web Token
- **KMS**: Key Management Service
- **LLM**: Large Language Model
- **ML**: Machine Learning
- **REST**: Representational State Transfer
- **SDK**: Software Development Kit
- **SIEM**: Security Information and Event Management
- **SLO**: Service Level Objective
- **SMS**: Short Message Service
- **SOAR**: Security Orchestration, Automation and Response
- **SOC**: Security Operations Center
- **SQL**: Structured Query Language
- **SSL**: Secure Sockets Layer
- **TLS**: Transport Layer Security
- **TTL**: Time To Live
- **UUID**: Universally Unique Identifier
- **VM**: Virtual Machine
- **VPC**: Virtual Private Cloud
- **WAF**: Web Application Firewall
- **YAML**: YAML Ain't Markup Language

## Related Documentation

- [Architecture Overview](../02-architecture/architecture.md)
- [Agent Overview](../02-architecture/agents/agents-overview.md)
- [ADK Tool Reference](./adk-tool-reference.md)
- [System Requirements](../01-getting-started/system-requirements.md)