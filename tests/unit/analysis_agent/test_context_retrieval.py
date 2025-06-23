"""
Real production tests for analysis_agent.context_retrieval module.

Uses actual Firestore database with project ID: your-gcp-project-id
No mocks - all tests use real GCP services and production code behavior.
"""

# pylint: disable=redefined-outer-name  # Pytest fixtures

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from google.cloud import firestore_v1 as firestore

from src.analysis_agent.context_retrieval import ContextRetriever
from src.common.models import (
    EventSource,
    Incident,
    IncidentStatus,
    SecurityEvent,
    SeverityLevel,
)


@pytest.fixture
def db() -> firestore.Client:
    """Real Firestore client for testing."""
    return firestore.Client(project="your-gcp-project-id")


@pytest.fixture
def logger() -> logging.Logger:
    """Logger for testing."""
    return logging.getLogger(__name__)


@pytest.fixture
def context_retriever(db: firestore.Client, logger: logging.Logger) -> ContextRetriever:
    """Create ContextRetriever instance with real Firestore."""
    return ContextRetriever(db=db, logger=logger)


@pytest.fixture
def sample_incident() -> Incident:
    """Create a sample incident for testing."""
    event_source = EventSource(
        source_type="cloud_audit",
        source_name="compute.googleapis.com",
        source_id="compute-instance-123",
        resource_type="gce_instance",
        resource_name="test-instance",
        resource_id="instance-456",
    )

    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        event_type="unauthorized_access",
        source=event_source,
        severity=SeverityLevel.HIGH,
        description="Unauthorized access detected",
        raw_data={"ip_address": "192.168.1.100", "user": "suspicious_user"},
        actor="suspicious_user",
        affected_resources=["instance-456", "vpc-789"],
        indicators={"risk_score": 0.8},
    )

    incident = Incident(
        incident_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        title="Test Security Incident",
        description="Test incident for context retrieval testing",
        severity=SeverityLevel.HIGH,
        status=IncidentStatus.ANALYZING,
        events=[event],
        tags=["test", "security"],
        metadata={"test": True},
    )

    return incident


@pytest.fixture
def sample_correlation_results() -> dict[str, Any]:
    """Sample correlation results for testing."""
    return {
        "actor_patterns": {
            "suspicious_actors": [
                {
                    "actor": "suspicious_user",
                    "reasons": ["Multiple failed logins", "Access at unusual hours"],
                    "risk_level": "high",
                }
            ]
        },
        "causal_patterns": {
            "action_sequences": [
                {
                    "events": [
                        {"type": "login_attempt", "timestamp": "2025-06-13T10:00:00Z"},
                        {
                            "type": "unauthorized_access",
                            "timestamp": "2025-06-13T10:05:00Z",
                        },
                    ]
                }
            ]
        },
        "correlation_scores": {"overall_score": 0.8},
        "attack_techniques": ["T1078", "T1133"],
    }


@pytest.fixture(scope="function")
def test_data_cleanup(db: firestore.Client) -> Any:
    """Fixture to clean up test data after each test."""
    test_collections = ["incidents", "knowledge_base", "historical_patterns"]
    test_docs: list[Any] = []

    yield test_docs

    # Clean up test data
    for collection_name in test_collections:
        collection = db.collection(collection_name)
        try:
            docs = collection.where("metadata.test", "==", True).stream()
            for doc in docs:
                doc.reference.delete()
        except (ConnectionError, ValueError, RuntimeError):
            # Ignore cleanup errors
            pass


class TestContextRetriever:
    """Test suite for ContextRetriever class."""

    def test_init(self, db: firestore.Client, logger: logging.Logger) -> None:
        """Test ContextRetriever initialization."""
        retriever = ContextRetriever(db=db, logger=logger)

        assert retriever.db == db
        assert retriever.logger == logger
        assert retriever.incidents_collection is not None
        assert retriever.knowledge_base_collection is not None
        assert retriever.historical_patterns_collection is not None

        # Verify collection names
        assert retriever.incidents_collection.id == "incidents"
        assert retriever.knowledge_base_collection.id == "knowledge_base"
        assert retriever.historical_patterns_collection.id == "historical_patterns"

    @pytest.mark.asyncio
    async def test_gather_additional_context(
        self,
        context_retriever: ContextRetriever,
        sample_incident: Incident,
        sample_correlation_results: dict[str, Any],
        test_data_cleanup: Any,
    ) -> None:
        """Test main context gathering functionality."""
        # Create test data in Firestore
        self._setup_test_data(context_retriever.db, test_data_cleanup)

        # Test context gathering
        context = await context_retriever.gather_additional_context(
            sample_incident, sample_correlation_results
        )

        # Verify context structure
        assert isinstance(context, dict)
        assert "related_incidents" in context
        assert "historical_patterns" in context
        assert "knowledge_base_entries" in context
        assert "similar_incidents" in context
        assert "threat_intelligence" in context
        assert "context_summary" in context

        # Verify data types
        assert isinstance(context["related_incidents"], list)
        assert isinstance(context["historical_patterns"], list)
        assert isinstance(context["knowledge_base_entries"], list)
        assert isinstance(context["similar_incidents"], list)
        assert isinstance(context["threat_intelligence"], dict)
        assert isinstance(context["context_summary"], str)

    @pytest.mark.asyncio
    async def test_fetch_related_incidents(
        self,
        context_retriever: ContextRetriever,
        sample_incident: Incident,
        sample_correlation_results: dict[str, Any],
        test_data_cleanup: Any,
    ) -> None:
        """Test fetching related incidents from Firestore."""
        # Create test incidents in Firestore
        self._create_test_incidents(context_retriever.db, test_data_cleanup)

        # Test fetching related incidents
        related = await context_retriever._fetch_related_incidents(
            sample_incident, sample_correlation_results
        )

        # Verify results
        assert isinstance(related, list)
        for incident in related:
            assert isinstance(incident, dict)
            assert "incident_id" in incident
            assert "title" in incident
            assert "relevance_score" in incident
            assert "relevance_reasons" in incident
            assert isinstance(incident["relevance_score"], float)
            assert incident["relevance_score"] >= 0.0

    @pytest.mark.asyncio
    async def test_retrieve_historical_patterns(
        self,
        context_retriever: ContextRetriever,
        sample_incident: Incident,
        sample_correlation_results: dict[str, Any],
        test_data_cleanup: Any,
    ) -> None:
        """Test retrieving historical attack patterns."""
        # Create test patterns in Firestore
        self._create_test_patterns(context_retriever.db, test_data_cleanup)

        # Test pattern retrieval
        patterns = await context_retriever._retrieve_historical_patterns(
            sample_incident, sample_correlation_results
        )

        # Verify results
        assert isinstance(patterns, list)
        for pattern in patterns:
            assert isinstance(pattern, dict)
            assert "pattern_id" in pattern
            assert "pattern_name" in pattern
            assert "attack_techniques" in pattern
            assert isinstance(pattern["attack_techniques"], list)

    @pytest.mark.asyncio
    async def test_query_knowledge_base(
        self,
        context_retriever: ContextRetriever,
        sample_incident: Incident,
        sample_correlation_results: dict[str, Any],
        test_data_cleanup: Any,
    ) -> None:
        """Test querying knowledge base for relevant information."""
        # Create test knowledge base entries
        self._create_test_knowledge_base(context_retriever.db, test_data_cleanup)

        # Test knowledge base querying
        kb_entries = await context_retriever._query_knowledge_base(
            sample_incident, sample_correlation_results
        )

        # Verify results
        assert isinstance(kb_entries, list)
        for entry in kb_entries:
            assert isinstance(entry, dict)
            assert "entry_id" in entry
            assert "title" in entry
            assert "category" in entry
            assert "tags" in entry
            assert isinstance(entry["tags"], list)

    @pytest.mark.asyncio
    async def test_find_similar_incidents(
        self,
        context_retriever: ContextRetriever,
        sample_incident: Incident,
        test_data_cleanup: Any,
    ) -> None:
        """Test finding similar incidents based on event types and severity."""
        # Create test similar incidents
        self._create_test_similar_incidents(context_retriever.db, test_data_cleanup)

        # Test finding similar incidents (avoid complex queries)
        similar = await context_retriever._find_similar_incidents(sample_incident)

        # Verify results (may be empty due to index requirements)
        assert isinstance(similar, list)
        for incident in similar:
            assert isinstance(incident, dict)
            assert "incident_id" in incident
            assert "similarity_score" in incident
            assert isinstance(incident["similarity_score"], float)
            assert 0.0 <= incident["similarity_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_get_threat_intelligence(
        self,
        context_retriever: ContextRetriever,
        sample_incident: Incident,
        sample_correlation_results: dict[str, Any],
    ) -> None:
        """Test threat intelligence gathering."""
        # Test threat intelligence extraction
        threat_intel = await context_retriever._get_threat_intelligence(
            sample_incident, sample_correlation_results
        )

        # Verify structure
        assert isinstance(threat_intel, dict)
        assert "indicators_of_compromise" in threat_intel
        assert "threat_actors" in threat_intel
        assert "ttps" in threat_intel
        assert "risk_assessment" in threat_intel

        # Verify data types
        assert isinstance(threat_intel["indicators_of_compromise"], list)
        assert isinstance(threat_intel["threat_actors"], list)
        assert isinstance(threat_intel["ttps"], list)
        assert isinstance(threat_intel["risk_assessment"], str)

        # Verify IoCs from sample incident
        iocs = threat_intel["indicators_of_compromise"]
        ip_found = any(
            ioc["type"] == "ip" and ioc["value"] == "192.168.1.100" for ioc in iocs
        )
        assert ip_found, "Should extract IP address from event raw_data"

    def test_generate_context_summary(
        self, context_retriever: ContextRetriever
    ) -> None:
        """Test context summary generation."""
        context = {
            "related_incidents": [
                {"incident_id": "inc1", "title": "Similar incident"},
                {"incident_id": "inc2", "title": "Another incident"},
            ],
            "historical_patterns": [{"pattern_name": "Lateral Movement Pattern"}],
            "knowledge_base_entries": [{"entry_type": "mitigation"}],
            "similar_incidents": [{"incident_id": "inc3"}],
            "threat_intelligence": {"indicators": ["192.168.1.100"]},
        }

        empty_context: dict[str, Any] = {
            "related_incidents": [],
            "historical_patterns": [],
            "knowledge_base_entries": [],
            "similar_incidents": [],
            "threat_intelligence": {},
        }

        summary = context_retriever._generate_context_summary(empty_context)
        assert summary == "No additional context found"

        summary = context_retriever._generate_context_summary(context)
        assert "2 related incidents" in summary
        assert "Lateral Movement Pattern" in summary
        assert "1 relevant knowledge base" in summary
        assert "1 historically similar" in summary
        assert "1 IoCs" in summary
        assert "1 suspicious actors" in summary

    def test_calculate_risk_score(
        self, context_retriever: ContextRetriever, sample_incident: Incident
    ) -> None:
        """Test risk score calculation."""
        # Test with different severity levels
        sample_incident.severity = SeverityLevel.LOW
        score = context_retriever._calculate_risk_score(sample_incident)
        assert score == 2.5

        sample_incident.severity = SeverityLevel.MEDIUM
        score = context_retriever._calculate_risk_score(sample_incident)
        assert score == 5.0

        sample_incident.severity = SeverityLevel.HIGH
        score = context_retriever._calculate_risk_score(sample_incident)
        assert score == 7.5

        sample_incident.severity = SeverityLevel.CRITICAL
        score = context_retriever._calculate_risk_score(sample_incident)
        assert score == 10.0

    def test_classify_risk_category(self, context_retriever: ContextRetriever) -> None:
        """Test risk category classification."""
        assert context_retriever._classify_risk_category(10.0) == "CRITICAL"
        assert context_retriever._classify_risk_category(8.0) == "CRITICAL"
        assert context_retriever._classify_risk_category(7.0) == "HIGH"
        assert context_retriever._classify_risk_category(6.0) == "HIGH"
        assert context_retriever._classify_risk_category(5.0) == "MEDIUM"
        assert context_retriever._classify_risk_category(4.0) == "MEDIUM"
        assert context_retriever._classify_risk_category(3.0) == "LOW"
        assert context_retriever._classify_risk_category(1.0) == "LOW"

    def test_calculate_composite_risk(
        self, context_retriever: ContextRetriever
    ) -> None:
        """Test composite risk calculation."""
        # Test with empty factors
        assert context_retriever._calculate_composite_risk({}) == 0.0

        # Test with zero weights
        assert (
            context_retriever._calculate_composite_risk(
                {"factor1": 0.0, "factor2": 0.0}
            )
            == 0.0
        )

        # Test with normal factors
        factors = {"factor1": 3.0, "factor2": 7.0}
        result = context_retriever._calculate_composite_risk(factors)
        assert result == 5.0  # (3.0 + 7.0) / 2

        # Test with high values (should cap at 10.0)
        factors = {"factor1": 15.0, "factor2": 25.0}
        result = context_retriever._calculate_composite_risk(factors)
        assert result == 10.0

    @pytest.mark.asyncio
    async def test_get_additional_context_alias(
        self,
        context_retriever: ContextRetriever,
        sample_incident: Incident,
        test_data_cleanup: Any,
    ) -> None:
        """Test get_additional_context alias method."""
        # Create minimal test data
        self._setup_test_data(context_retriever.db, test_data_cleanup)

        # Test alias method
        context = await context_retriever.get_additional_context(sample_incident)

        # Verify it returns the same structure as main method
        assert isinstance(context, dict)
        assert "related_incidents" in context
        assert "historical_patterns" in context
        assert "knowledge_base_entries" in context
        assert "similar_incidents" in context
        assert "threat_intelligence" in context
        assert "context_summary" in context

    @pytest.mark.asyncio
    async def test_error_handling(self, logger: logging.Logger) -> None:
        """Test error handling in context retrieval."""
        # Test error handling by creating retriever that will fail on queries
        # We can't pass None to __init__ since it accesses db immediately
        # Instead test with empty/invalid results
        context_retriever = ContextRetriever(
            db=firestore.Client(project="your-gcp-project-id"), logger=logger
        )

        # Test with incident that has no events
        empty_incident = Incident(
            incident_id="test", title="Test", description="Test", events=[]  # No events
        )

        # All methods should handle empty data gracefully
        context = await context_retriever.gather_additional_context(empty_incident, {})
        assert context["related_incidents"] == []
        assert context["historical_patterns"] == []
        assert context["knowledge_base_entries"] == []
        assert context["similar_incidents"] == []
        assert isinstance(context["threat_intelligence"], dict)
        assert isinstance(context["context_summary"], str)

        kb_entries = await context_retriever._query_knowledge_base(empty_incident, {})
        assert kb_entries == []

    def _setup_test_data(self, db: firestore.Client, test_docs: list[Any]) -> None:
        """Set up test data in Firestore."""
        self._create_test_incidents(db, test_docs)
        self._create_test_patterns(db, test_docs)
        self._create_test_knowledge_base(db, test_docs)
        self._create_test_similar_incidents(db, test_docs)

    def _create_test_incidents(
        self, db: firestore.Client, test_docs: list[Any]
    ) -> None:
        """Create test incidents in Firestore."""
        incidents_collection = db.collection("incidents")

        # Create related incident 1
        incident1_data = {
            "title": "Related Security Incident 1",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
            "severity": "high",
            "status": "analyzing",
            "events": [
                {
                    "event_type": "unauthorized_access",
                    "actor": "suspicious_user",
                    "affected_resources": ["instance-456"],
                    "source": {"resource_type": "gce_instance"},
                }
            ],
            "metadata": {"test": True},
        }

        doc_ref1 = incidents_collection.document()
        doc_ref1.set(incident1_data)
        test_docs.append(doc_ref1)

        # Create related incident 2
        incident2_data = {
            "title": "Related Security Incident 2",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
            "severity": "medium",
            "status": "resolved",
            "events": [
                {
                    "event_type": "privilege_escalation",
                    "actor": "different_user",
                    "affected_resources": ["vpc-789"],
                    "source": {"resource_type": "vpc"},
                }
            ],
            "metadata": {"test": True},
        }

        doc_ref2 = incidents_collection.document()
        doc_ref2.set(incident2_data)
        test_docs.append(doc_ref2)

    def _create_test_patterns(self, db: firestore.Client, test_docs: list[Any]) -> None:
        """Create test patterns in Firestore."""
        patterns_collection = db.collection("historical_patterns")

        pattern1_data = {
            "name": "Unauthorized Access Pattern",
            "description": "Common pattern for unauthorized access attempts",
            "attack_techniques": ["unauthorized_access", "privilege_escalation"],
            "typical_duration": "2-4 hours",
            "severity": "high",
            "countermeasures": ["Enable MFA", "Monitor access logs"],
            "metadata": {"test": True},
        }

        doc_ref1 = patterns_collection.document()
        doc_ref1.set(pattern1_data)
        test_docs.append(doc_ref1)

        pattern2_data = {
            "name": "Data Exfiltration Pattern",
            "description": "Pattern indicating potential data theft",
            "attack_techniques": ["data_exfiltration", "lateral_movement"],
            "typical_duration": "1-3 hours",
            "severity": "critical",
            "countermeasures": ["Block suspicious IPs", "Isolate affected systems"],
            "metadata": {"test": True},
        }

        doc_ref2 = patterns_collection.document()
        doc_ref2.set(pattern2_data)
        test_docs.append(doc_ref2)

    def _create_test_knowledge_base(
        self, db: firestore.Client, test_docs: list[Any]
    ) -> None:
        """Create test knowledge base entries in Firestore."""
        kb_collection = db.collection("knowledge_base")

        kb1_data = {
            "title": "Unauthorized Access Response Guide",
            "category": "incident_response",
            "content": "This guide covers how to respond to unauthorized access incidents...",
            "tags": ["unauthorized_access", "security", "response"],
            "last_updated": datetime.now(timezone.utc),
            "metadata": {"test": True},
        }

        doc_ref1 = kb_collection.document()
        doc_ref1.set(kb1_data)
        test_docs.append(doc_ref1)

        kb2_data = {
            "title": "GCE Instance Security Best Practices",
            "category": "prevention",
            "content": "Best practices for securing Google Compute Engine instances...",
            "tags": ["gce_instance", "security", "prevention"],
            "last_updated": datetime.now(timezone.utc),
            "metadata": {"test": True},
        }

        doc_ref2 = kb_collection.document()
        doc_ref2.set(kb2_data)
        test_docs.append(doc_ref2)

    def _create_test_similar_incidents(
        self, db: firestore.Client, test_docs: list[Any]
    ) -> None:
        """Create test similar incidents in Firestore."""
        incidents_collection = db.collection("incidents")

        # Create simple incident without complex queries
        similar_incident_data = {
            "title": "Similar Past Incident",
            "created_at": datetime.now(timezone.utc) - timedelta(days=30),
            "updated_at": datetime.now(timezone.utc) - timedelta(days=29),
            "severity": "high",
            "status": "resolved",
            "events": [
                {
                    "event_type": "unauthorized_access",
                    "source": {"resource_type": "gce_instance"},
                }
            ],
            "resolution_notes": "Resolved by revoking user access and updating security policies",
            "metadata": {"test": True},
        }

        doc_ref = incidents_collection.document()
        doc_ref.set(similar_incident_data)
        test_docs.append(doc_ref)


# Integration test to verify end-to-end functionality
@pytest.mark.asyncio
async def test_context_retrieval_integration(
    db: firestore.Client, logger: logging.Logger
) -> None:
    """Integration test for context retrieval with real Firestore operations."""
    # Create retriever
    retriever = ContextRetriever(db=db, logger=logger)

    # Create comprehensive test incident
    event_source = EventSource(
        source_type="cloud_audit",
        source_name="compute.googleapis.com",
        source_id="compute-instance-integration",
        resource_type="gce_instance",
        resource_name="integration-test-instance",
    )

    event = SecurityEvent(
        event_type="unauthorized_access",
        source=event_source,
        severity=SeverityLevel.CRITICAL,
        description="Integration test unauthorized access",
        raw_data={
            "ip_address": "10.0.0.100",
            "domain": "malicious.example.com",
            "md5": "abcd1234efgh5678",
        },
        actor="integration_test_user",
        affected_resources=["integration-instance-123"],
    )

    incident = Incident(
        title="Integration Test Incident",
        description="Full integration test for context retrieval",
        severity=SeverityLevel.CRITICAL,
        events=[event],
        tags=["integration", "test"],
    )

    correlation_results = {
        "actor_patterns": {
            "suspicious_actors": [
                {
                    "actor": "integration_test_user",
                    "reasons": [
                        "Multiple security violations",
                        "Access from suspicious IP",
                    ],
                }
            ]
        },
        "correlation_scores": {"overall_score": 0.9},
        "attack_techniques": ["T1078", "T1133"],
    }

    # Test full context gathering
    context = await retriever.gather_additional_context(incident, correlation_results)

    # Verify comprehensive response structure
    assert isinstance(context, dict)
    required_keys = [
        "related_incidents",
        "historical_patterns",
        "knowledge_base_entries",
        "similar_incidents",
        "threat_intelligence",
        "context_summary",
    ]
    for key in required_keys:
        assert key in context, f"Missing required key: {key}"

    # Verify threat intelligence extraction
    threat_intel = context["threat_intelligence"]
    assert "indicators_of_compromise" in threat_intel
    assert "threat_actors" in threat_intel
    assert "risk_assessment" in threat_intel

    # Should extract IoCs from event data
    iocs = threat_intel["indicators_of_compromise"]
    assert len(iocs) > 0, "Should extract IoCs from event raw_data"

    # Verify context summary is generated
    assert len(context["context_summary"]) > 0
    assert isinstance(context["context_summary"], str)

    print("✅ Integration test passed - Context retrieval working with real Firestore")
    print(f"📊 Context summary: {context['context_summary']}")


if __name__ == "__main__":
    # Run basic functionality test
    asyncio.run(
        test_context_retrieval_integration(
            firestore.Client(project="your-gcp-project-id"),
            logging.getLogger(__name__),
        )
    )
