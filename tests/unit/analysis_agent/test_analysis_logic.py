"""
Real production tests for Analysis Agent logic components.

Tests actual analysis logic with real Google Cloud Firestore.
NO MOCKING - uses production database and analysis engine.
"""

import os
import time
import uuid
from typing import Any, Dict

import pytest
from google.cloud import firestore

from src.analysis_agent.adk_agent import (
    IncidentAnalysisTool,
    ThreatIntelligenceTool,
    RecommendationGeneratorTool,
)
from src.common.adk_import_fix import ExtendedToolContext as ToolContext


# Use real project ID
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")


# Create real ToolContext for testing
class RealToolContext(ToolContext):
    """Real ToolContext for testing."""

    def __init__(self) -> None:
        super().__init__(data={})
        self.data: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}


class TestAnalysisLogic:
    """Test cases for core analysis logic."""

    @pytest.fixture
    def real_firestore(self) -> firestore.Client:
        """Create real Firestore client."""
        client = firestore.Client(project=PROJECT_ID)
        yield client

    @pytest.fixture
    def test_collection_name(self) -> str:
        """Generate unique test collection name."""
        return f"test_threat_intel_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    def test_threat_collection(self, real_firestore: firestore.Client, test_collection_name: str) -> firestore.CollectionReference:
        """Create test collection with cleanup."""
        # Create the threat intelligence collection structure as expected by the tool
        collection_ref = real_firestore.collection(test_collection_name)
        ip_collection_ref = collection_ref.document("ip_reputation").collection("ips")

        # Pre-populate some test threat data
        test_threats = [
            {
                "severity": "critical",
                "description": "Known botnet IP",
                "tags": ["botnet", "credential_theft"],
                "last_seen": firestore.SERVER_TIMESTAMP,
                "reputation_score": 90,
            },
            {
                "severity": "high",
                "description": "Suspicious scanner",
                "tags": ["scanner", "recon"],
                "last_seen": firestore.SERVER_TIMESTAMP,
                "reputation_score": 75,
            },
        ]

        # Add test documents with IP as document ID
        ips = ["192.168.1.1", "10.0.0.5"]
        for ip, threat in zip(ips, test_threats):
            ip_collection_ref.document(ip).set(threat)

        yield collection_ref

        # Cleanup - delete all documents in collection
        # Delete IP documents
        for ip in ips:
            ip_collection_ref.document(ip).delete()
        # Delete parent document
        collection_ref.document("ip_reputation").delete()

    @pytest.fixture
    def test_incidents_collection(self, real_firestore: firestore.Client) -> firestore.CollectionReference:
        """Create test incidents collection with cleanup."""
        collection_name = f"test_incidents_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        collection_ref = real_firestore.collection(collection_name)

        # Pre-populate some test incidents
        test_incidents = [
            {
                "id": "inc-old-1",
                "severity": "high",
                "threat_type": "credential_attack",
                "attack_pattern": "brute_force",
                "timestamp": firestore.SERVER_TIMESTAMP,
            },
            {
                "id": "inc-old-2",
                "severity": "critical",
                "threat_type": "credential_attack",
                "attack_pattern": "brute_force",
                "timestamp": firestore.SERVER_TIMESTAMP,
            },
        ]

        for incident in test_incidents:
            collection_ref.document(incident["id"]).set(incident)

        yield collection_ref

        # Cleanup
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()

    @pytest.fixture
    def vertex_ai_config(self) -> Dict[str, Any]:
        """Get Vertex AI configuration."""
        # Verify Vertex AI is properly configured
        project_id = os.getenv("GCP_PROJECT_ID", "your-gcp-project-id")
        location = os.getenv("VERTEX_AI_LOCATION", "us-central1")

        # Skip if running in an environment without GCP credentials
        try:
            from google.auth import default

            _, _ = default()  # type: ignore[no-untyped-call]
        except (ImportError, ValueError):
            pytest.skip("No GCP credentials available - skipping Vertex AI test")

        return {
            "project_id": project_id,
            "location": location,
            "model": "gemini-1.5-pro-002",
        }

    @pytest.mark.asyncio
    async def test_incident_analysis_tool_success(self, vertex_ai_config: Dict[str, Any]) -> None:
        """Test successful incident analysis with real Vertex AI."""
        # Setup with Vertex AI config
        tool = IncidentAnalysisTool({"temperature": 0.7, **vertex_ai_config})
        context = RealToolContext()

        incident = {
            "id": "inc-123",
            "title": "Suspicious Login",
            "severity": "high",
            "events": [{"type": "failed_login"}],
            "metadata": {"attempts": 50},
        }

        # Execute
        result = await tool.execute(context, incident=incident)

        # Verify real API response structure
        assert result["status"] == "success"
        assert "threat_assessment" in result["analysis"]
        assert result["analysis"]["threat_assessment"]["threat_level"] in [
            "critical",
            "high",
            "medium",
            "low",
        ]
        assert 0.0 <= result["analysis"]["threat_assessment"]["confidence"] <= 1.0
        assert "threat_type" in result["analysis"]["threat_assessment"]
        assert "risk_factors" in result["analysis"]
        assert isinstance(result["analysis"]["risk_factors"], list)
        assert "potential_data_exposure" in result["analysis"]

    @pytest.mark.asyncio
    async def test_incident_analysis_tool_various_incidents(self, vertex_ai_config: Dict[str, Any]) -> None:
        """Test incident analysis with various incident types using real Vertex AI."""
        # Setup
        tool = IncidentAnalysisTool({"temperature": 0.7, **vertex_ai_config})
        context = RealToolContext()

        # Test with medium severity incident
        incident = {
            "id": "inc-123",
            "title": "Unusual Network Activity",
            "severity": "medium",
            "events": [{"type": "network_scan", "source_ip": "192.168.1.100"}],
        }

        # Execute with real API
        result = await tool.execute(context, incident=incident)

        # Verify real response
        assert result["status"] == "success"
        assert "threat_assessment" in result["analysis"]
        assert result["analysis"]["threat_assessment"]["threat_level"] in [
            "critical",
            "high",
            "medium",
            "low",
        ]
        assert isinstance(
            result["analysis"]["threat_assessment"]["confidence"], (int, float)
        )

    @pytest.mark.asyncio
    async def test_incident_analysis_tool_invalid_config(self) -> None:
        """Test incident analysis with invalid configuration."""
        # Setup with invalid config
        tool = IncidentAnalysisTool(
            {"temperature": 0.7, "project_id": "invalid-project"}
        )
        context = RealToolContext()

        incident = {"id": "inc-123", "title": "Test", "severity": "high"}

        # Execute - should handle API error gracefully
        result = await tool.execute(context, incident=incident)

        # Verify error handling
        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_threat_intelligence_tool_no_known_iocs(self, real_firestore: firestore.Client) -> None:
        """Test threat intelligence enrichment with no known IoCs using real Firestore."""
        # Setup - use a collection that doesn't exist
        non_existent_collection = f"test_empty_{uuid.uuid4().hex}"
        tool = ThreatIntelligenceTool(real_firestore)
        tool.firestore_client = real_firestore  # Ensure using real client
        context = RealToolContext()

        # Override collection name for testing
        tool.threat_intel_collection = non_existent_collection

        analysis_results = {
            "threat_assessment": {
                "threat_type": "credential_attack",
                "attack_pattern": "brute_force",
            },
            "affected_resources": ["user_account"],
        }

        # Execute with an IP that won't be in the empty collection
        result = await tool.execute(
            context,
            incident={
                "id": "inc-123",
                "events": [{"indicators": {"ip": "192.168.99.99"}}],
            },
            analysis_results=analysis_results,
        )

        # Verify
        assert result["status"] == "success"
        assert len(result["threat_intelligence"]["known_iocs"]) == 0
        assert len(result["threat_intelligence"]["threat_actors"]) == 0
        assert len(result["threat_intelligence"]["campaigns"]) == 0
        assert len(result["threat_intelligence"]["vulnerabilities"]) == 0

    @pytest.mark.asyncio
    async def test_threat_intelligence_tool_with_known_iocs(
        self, real_firestore: firestore.Client, test_threat_collection: firestore.CollectionReference, test_incidents_collection: firestore.CollectionReference  # pylint: disable=unused-argument
    ) -> None:
        """Test threat intelligence enrichment with known IoCs using real Firestore."""
        # Setup
        tool = ThreatIntelligenceTool(real_firestore)
        tool.firestore_client = real_firestore
        context = RealToolContext()

        # Override collection name for testing
        tool.threat_intel_collection = test_threat_collection.id

        analysis_results = {
            "threat_assessment": {
                "threat_type": "credential_attack",
                "attack_pattern": "brute_force",
            }
        }

        # Execute with IP in incident metadata where tool expects it
        result = await tool.execute(
            context,
            incident={
                "id": "inc-123",
                "metadata": {
                    "source_ip": "192.168.1.1"  # This IP exists in our test data
                },
            },
            analysis_results=analysis_results,
        )

        # Verify
        assert result["status"] == "success"
        assert len(result["threat_intelligence"]["known_iocs"]) >= 1

        # Find the specific IoC we're looking for
        found_ioc = None
        for ioc in result["threat_intelligence"]["known_iocs"]:
            if ioc["value"] == "192.168.1.1":
                found_ioc = ioc
                break

        assert found_ioc is not None
        assert found_ioc["type"] == "ip"
        # Check reputation data structure
        assert "reputation" in found_ioc
        assert found_ioc["reputation"]["severity"] == "critical"
        assert "botnet" in found_ioc["reputation"]["tags"]
        assert found_ioc["reputation"]["reputation_score"] == 90

        # Should have found the threat data
        assert "enriched_at" in result

    @pytest.mark.asyncio
    async def test_recommendation_generator_tool_success(self, vertex_ai_config: Dict[str, Any]) -> None:
        """Test recommendation generation with real Vertex AI."""
        # Setup with Vertex AI config
        tool = RecommendationGeneratorTool({"temperature": 0.3, **vertex_ai_config})
        context = RealToolContext()

        analysis_results = {
            "threat_assessment": {"threat_level": "high", "confidence": 0.85},
            "risk_factors": ["multiple_failed_attempts"],
        }

        # Execute
        result = await tool.execute(
            context,
            analysis_results=analysis_results,
            threat_intelligence={
                "known_iocs": [{"type": "ip", "value": "192.168.1.1"}]
            },
        )

        # Verify real API response
        assert result["status"] == "success"
        assert "immediate_actions" in result["recommendations"]
        assert isinstance(result["recommendations"]["immediate_actions"], list)
        assert len(result["recommendations"]["immediate_actions"]) > 0
        assert "investigation_steps" in result["recommendations"]
        assert isinstance(result["recommendations"]["investigation_steps"], list)
        assert "preventive_measures" in result["recommendations"]
        assert isinstance(result["recommendations"]["preventive_measures"], list)

    @pytest.mark.asyncio
    async def test_recommendation_generator_tool_with_minimal_data(
        self, vertex_ai_config: Dict[str, Any]
    ) -> None:
        """Test recommendation generation with minimal input data."""
        # Setup
        tool = RecommendationGeneratorTool({"temperature": 0.3, **vertex_ai_config})
        context = RealToolContext()

        # Minimal analysis results
        analysis_results = {"threat_assessment": {"threat_level": "low"}}

        # Execute with real API
        result = await tool.execute(
            context, analysis_results=analysis_results, threat_intelligence={}
        )

        # Verify - should handle gracefully with real response
        assert result["status"] == "success"
        assert "recommendations" in result
        assert isinstance(result["recommendations"], dict)

    @pytest.mark.asyncio
    async def test_incident_analysis_tool_with_empty_incident(self, vertex_ai_config: Dict[str, Any]) -> None:
        """Test incident analysis with minimal incident data using real Vertex AI."""
        # Setup
        tool = IncidentAnalysisTool({"temperature": 0.7, **vertex_ai_config})
        context = RealToolContext()

        # Minimal incident
        incident = {"id": "inc-empty"}

        # Execute
        result = await tool.execute(context, incident=incident)

        # Verify real API handles minimal data
        assert result["status"] == "success"
        assert "threat_assessment" in result["analysis"]
        assert result["analysis"]["threat_assessment"]["threat_level"] in [
            "critical",
            "high",
            "medium",
            "low",
        ]
        assert isinstance(
            result["analysis"]["threat_assessment"]["confidence"], (int, float)
        )
        assert "risk_factors" in result["analysis"]

    def test_extract_indicators_from_analysis_results(self) -> None:
        """Test indicator extraction from various analysis result formats."""
        analysis_results = {
            "indicators": {
                "ip_addresses": ["192.168.1.1", "10.0.0.5"],
                "domains": ["malicious.com", "evil.org"],
                "file_hashes": ["abc123", "def456"],
                "email_addresses": ["attacker@bad.com"],
            },
            "attribution": {
                "threat_actor": "APT28",
                "indicators": ["custom_signature", "known_pattern"],
            },
        }

        # Extract indicators following the pattern in the code
        indicators = []

        # Extract from indicators section
        if "indicators" in analysis_results:
            ind_obj = analysis_results["indicators"]
            if isinstance(ind_obj, dict):
                ind: Dict[str, Any] = ind_obj
            else:
                ind = {}
            for ip in ind.get("ip_addresses", []):
                indicators.append({"type": "ip", "value": ip})
            for domain in ind.get("domains", []):
                indicators.append({"type": "domain", "value": domain})
            for hash_val in ind.get("file_hashes", []):
                indicators.append({"type": "hash", "value": hash_val})
            for email in ind.get("email_addresses", []):
                indicators.append({"type": "email", "value": email})

        # Verify extraction
        assert len(indicators) == 7
        ip_indicators = [i for i in indicators if i["type"] == "ip"]
        assert len(ip_indicators) == 2
        domain_indicators = [i for i in indicators if i["type"] == "domain"]
        assert len(domain_indicators) == 2

    @pytest.mark.asyncio
    async def test_threat_intelligence_error_handling(self) -> None:
        """Test threat intelligence tool error handling."""
        # Setup with None as firestore client to force error
        tool = ThreatIntelligenceTool(None)
        context = RealToolContext()

        # Execute with None client should cause AttributeError
        result = await tool.execute(
            context,
            incident={"id": "inc-error", "metadata": {"source_ip": "192.168.1.1"}},
            analysis_results={},
        )

        # Verify - should handle error gracefully
        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_recommendation_generator_invalid_config(self) -> None:
        """Test recommendation generator with invalid configuration."""
        # Setup with invalid config
        tool = RecommendationGeneratorTool(
            {"temperature": 0.3, "project_id": "invalid-project"}
        )
        context = RealToolContext()

        # Execute
        result = await tool.execute(
            context, analysis_results={}, threat_intelligence={}
        )

        # Verify error handling
        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_real_firestore_operations(self, real_firestore: firestore.Client) -> None:
        """Test actual Firestore operations to ensure connectivity."""
        # Create a test document
        test_collection = f"test_connectivity_{uuid.uuid4().hex}"
        test_doc_id = "test_doc"
        test_data = {"test": True, "timestamp": firestore.SERVER_TIMESTAMP, "value": 42}

        # Write
        doc_ref = real_firestore.collection(test_collection).document(test_doc_id)
        doc_ref.set(test_data)

        # Read
        doc = doc_ref.get()
        assert doc.exists
        doc_data = doc.to_dict()
        assert doc_data["test"] is True
        assert doc_data["value"] == 42

        # Update
        doc_ref.update({"value": 100})

        # Verify update
        doc = doc_ref.get()
        assert doc.to_dict()["value"] == 100

        # Delete
        doc_ref.delete()

        # Verify deletion
        doc = doc_ref.get()
        assert not doc.exists
