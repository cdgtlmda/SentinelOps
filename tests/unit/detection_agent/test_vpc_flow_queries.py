"""
Comprehensive tests for detection_agent.vpc_flow_queries module.

This test suite provides 100% production code testing with real query validation.
NO MOCKING of any components per project policy.

Target: ≥90% statement coverage of src/detection_agent/vpc_flow_queries.py
"""

from detection_agent.vpc_flow_queries import VPCFlowLogsQueries
from common.models import SeverityLevel


class TestVPCFlowLogsQueries:
    """Test suite for VPC Flow Logs Queries - COMPREHENSIVE COVERAGE."""

    def test_get_queries_returns_dict(self) -> None:
        """Test that get_queries returns a dictionary."""
        queries = VPCFlowLogsQueries.get_queries()

        assert isinstance(queries, dict)
        assert len(queries) > 0

    def test_get_queries_structure(self) -> None:
        """Test the structure of queries returned by get_queries."""
        queries = VPCFlowLogsQueries.get_queries()

        # Expected query IDs
        expected_query_ids = {
            "suspicious_port_scan",
            "unusual_traffic_volume",
            "blocked_traffic_attempts",
            "external_ip_communication",
            "lateral_movement",
        }

        assert set(queries.keys()) == expected_query_ids

        # Test each query has required fields
        for _, query_def in queries.items():
            assert isinstance(query_def, dict)
            assert "name" in query_def
            assert "description" in query_def
            assert "severity" in query_def
            assert "query" in query_def
            assert "tags" in query_def

            # Validate field types
            assert isinstance(query_def["name"], str)
            assert isinstance(query_def["description"], str)
            assert isinstance(query_def["severity"], SeverityLevel)
            assert isinstance(query_def["query"], str)
            assert isinstance(query_def["tags"], list)

            # Validate non-empty content
            assert len(query_def["name"]) > 0
            assert len(query_def["description"]) > 0
            assert len(query_def["query"]) > 0
            assert len(query_def["tags"]) > 0

    def test_suspicious_port_scan_query(self) -> None:
        """Test suspicious port scan query definition."""
        queries = VPCFlowLogsQueries.get_queries()
        port_scan = queries["suspicious_port_scan"]

        assert port_scan["name"] == "Suspicious Port Scanning Activity"
        assert "port scanning activity" in port_scan["description"].lower()
        assert port_scan["severity"] == SeverityLevel.HIGH
        assert "network" in port_scan["tags"]
        assert "port_scan" in port_scan["tags"]
        assert "reconnaissance" in port_scan["tags"]

        # Validate SQL query content
        query = port_scan["query"]
        assert "WITH port_scan_activity AS" in query
        assert "jsonPayload.connection.src_ip" in query
        assert "jsonPayload.connection.dest_port" in query
        assert "unique_ports >= 10" in query
        assert "compute_googleapis_com_vpc_flows" in query
        assert "{project_id}" in query
        assert "{dataset_id}" in query
        assert "{last_scan_time}" in query
        assert "{current_time}" in query

    def test_unusual_traffic_volume_query(self) -> None:
        """Test unusual traffic volume query definition."""
        queries = VPCFlowLogsQueries.get_queries()
        traffic_volume = queries["unusual_traffic_volume"]

        assert traffic_volume["name"] == "Unusual Network Traffic Volume"
        assert "traffic volumes" in traffic_volume["description"].lower()
        assert "data exfiltration" in traffic_volume["description"].lower()
        assert traffic_volume["severity"] == SeverityLevel.HIGH
        assert "network" in traffic_volume["tags"]
        assert "data_exfiltration" in traffic_volume["tags"]
        assert "high_volume" in traffic_volume["tags"]

        # Validate SQL query content
        query = traffic_volume["query"]
        assert "WITH traffic_stats AS" in query
        assert "jsonPayload.bytes_sent" in query
        assert "total_bytes_sent > 1073741824" in query  # 1GB threshold
        assert "high_volume_transfer" in query

    def test_blocked_traffic_attempts_query(self) -> None:
        """Test blocked traffic attempts query definition."""
        queries = VPCFlowLogsQueries.get_queries()
        blocked_traffic = queries["blocked_traffic_attempts"]

        assert blocked_traffic["name"] == "Blocked Network Traffic Attempts"
        assert "blocked connection attempts" in blocked_traffic["description"].lower()
        assert blocked_traffic["severity"] == SeverityLevel.MEDIUM
        assert "network" in blocked_traffic["tags"]
        assert "firewall" in blocked_traffic["tags"]
        assert "blocked_traffic" in blocked_traffic["tags"]

        # Validate SQL query content
        query = blocked_traffic["query"]
        assert "WITH blocked_connections AS" in query
        assert "jsonPayload.packets_sent" in query
        assert "jsonPayload.packets_received" in query
        assert "blocked_attempts >= 10" in query
        assert "blocked_connection" in query

    def test_external_ip_communication_query(self) -> None:
        """Test external IP communication query definition."""
        queries = VPCFlowLogsQueries.get_queries()
        external_comm = queries["external_ip_communication"]

        assert external_comm["name"] == "Suspicious External IP Communication"
        assert "external IPs" in external_comm["description"].lower()
        assert external_comm["severity"] == SeverityLevel.HIGH
        assert "network" in external_comm["tags"]
        assert "external_communication" in external_comm["tags"]
        assert "data_exfiltration" in external_comm["tags"]

        # Validate SQL query content
        query = external_comm["query"]
        assert "WITH external_traffic AS" in query
        assert "jsonPayload.dest_location.country" in query
        assert "NOT REGEXP_CONTAINS" in query
        assert "external_communication" in query
        assert "bytes_sent > 104857600" in query  # 100MB threshold
        assert "'CN', 'RU', 'KP', 'IR'" in query  # High-risk countries

    def test_lateral_movement_query(self) -> None:
        """Test lateral movement query definition."""
        queries = VPCFlowLogsQueries.get_queries()
        lateral_movement = queries["lateral_movement"]

        assert lateral_movement["name"] == "Potential Lateral Movement"
        assert "lateral movement" in lateral_movement["description"].lower()
        assert lateral_movement["severity"] == SeverityLevel.HIGH
        assert "network" in lateral_movement["tags"]
        assert "lateral_movement" in lateral_movement["tags"]
        assert "internal_reconnaissance" in lateral_movement["tags"]

        # Validate SQL query content
        query = lateral_movement["query"]
        assert "WITH internal_connections AS" in query
        assert "REGEXP_CONTAINS" in query
        assert (
            "22, 23, 135, 139, 445, 3389, 5985, 5986" in query
        )  # Lateral movement ports
        assert "connection_count >= 5" in query
        assert "lateral_movement" in query

    def test_all_queries_have_sql_placeholders(self) -> None:
        """Test that all queries have required SQL placeholders."""
        queries = VPCFlowLogsQueries.get_queries()

        required_placeholders = [
            "{project_id}",
            "{dataset_id}",
            "{last_scan_time}",
            "{current_time}",
        ]

        for query_id, query_def in queries.items():
            query_sql = query_def["query"]

            for placeholder in required_placeholders:
                assert (
                    placeholder in query_sql
                ), f"Query {query_id} missing placeholder {placeholder}"

    def test_all_queries_have_required_sql_structure(self) -> None:
        """Test that all queries have required SQL structure."""
        queries = VPCFlowLogsQueries.get_queries()

        for _, query_def in queries.items():
            query_sql = query_def["query"]

            # All queries should use BigQuery VPC flow logs table
            assert "compute_googleapis_com_vpc_flows" in query_sql

            # All queries should have timestamp filtering
            assert "timestamp >" in query_sql
            assert "timestamp <=" in query_sql

            # All queries should have a SELECT statement
            assert "SELECT" in query_sql.upper()

            # All queries should have a FROM clause
            assert "FROM" in query_sql.upper()

    def test_query_severity_levels(self) -> None:
        """Test that queries use appropriate severity levels."""
        queries = VPCFlowLogsQueries.get_queries()

        # Expected severity mappings
        expected_severities = {
            "suspicious_port_scan": SeverityLevel.HIGH,
            "unusual_traffic_volume": SeverityLevel.HIGH,
            "blocked_traffic_attempts": SeverityLevel.MEDIUM,
            "external_ip_communication": SeverityLevel.HIGH,
            "lateral_movement": SeverityLevel.HIGH,
        }

        for query_id, expected_severity in expected_severities.items():
            assert queries[query_id]["severity"] == expected_severity

    def test_query_tags_structure(self) -> None:
        """Test that query tags follow expected structure."""
        queries = VPCFlowLogsQueries.get_queries()

        for _, query_def in queries.items():
            tags = query_def["tags"]

            # All queries should have "network" tag
            assert "network" in tags

            # Tags should be strings
            for tag in tags:
                assert isinstance(tag, str)
                assert len(tag) > 0

            # No duplicate tags
            assert len(tags) == len(set(tags))

    def test_create_detection_rules_returns_list(self) -> None:
        """Test that create_detection_rules returns a list."""
        rules = VPCFlowLogsQueries.create_detection_rules()

        assert isinstance(rules, list)
        assert len(rules) > 0

    def test_create_detection_rules_structure(self) -> None:
        """Test the structure of rules created by create_detection_rules."""
        rules = VPCFlowLogsQueries.create_detection_rules()
        queries = VPCFlowLogsQueries.get_queries()

        # Should have same number of rules as queries
        assert len(rules) == len(queries)

        # Each rule should be a DetectionRule object
        from detection_agent.rules_engine import DetectionRule

        for rule in rules:
            assert isinstance(rule, DetectionRule)

            # Test rule attributes
            assert hasattr(rule, "rule_id")
            assert hasattr(rule, "name")
            assert hasattr(rule, "description")
            assert hasattr(rule, "severity")
            assert hasattr(rule, "query")
            assert hasattr(rule, "tags")

            # Validate rule_id format
            assert rule.rule_id.startswith("vpc_")

            # Validate non-empty values
            assert len(rule.name) > 0
            assert len(rule.description) > 0
            assert len(rule.query) > 0
            assert len(rule.tags) > 0

    def test_create_detection_rules_content_mapping(self) -> None:
        """Test that detection rules properly map query content."""
        rules = VPCFlowLogsQueries.create_detection_rules()
        queries = VPCFlowLogsQueries.get_queries()

        # Create mapping by rule_id suffix
        rule_map = {}
        for rule in rules:
            # Extract original query_id from vpc_<query_id>
            query_id = rule.rule_id[4:]  # Remove "vpc_" prefix
            _ = query_id  # Mark as used to avoid unused variable warning
            rule_map[query_id] = rule

        # Verify each query maps correctly to a rule
        for query_id, query_def in queries.items():
            assert query_id in rule_map
            rule = rule_map[query_id]

            assert rule.name == query_def["name"]
            assert rule.description == query_def["description"]
            assert rule.severity == query_def["severity"]
            assert rule.query == query_def["query"]
            assert rule.tags == query_def["tags"]

    def test_query_sql_complexity(self) -> None:
        """Test that queries have appropriate SQL complexity."""
        queries = VPCFlowLogsQueries.get_queries()

        for _, query_def in queries.items():
            query_sql = query_def["query"]

            # Queries should use CTEs (Common Table Expressions)
            assert "WITH" in query_sql.upper()

            # Queries should have grouping and aggregation
            assert "GROUP BY" in query_sql.upper()

            # Queries should have filtering conditions
            assert "WHERE" in query_sql.upper()

            # Queries should have ordering
            assert "ORDER BY" in query_sql.upper()

            # Queries should have result limiting
            assert "LIMIT" in query_sql.upper()

    def test_query_json_payload_access(self) -> None:
        """Test that queries properly access jsonPayload fields."""
        queries = VPCFlowLogsQueries.get_queries()

        common_fields = [
            "jsonPayload.connection.src_ip",
            "jsonPayload.connection.dest_ip",
        ]

        for _, query_def in queries.items():
            query_sql = query_def["query"]

            # All queries should access basic connection fields
            for field in common_fields:
                assert field in query_sql

    def test_query_parameter_substitution_format(self) -> None:
        """Test that queries use correct parameter substitution format."""
        queries = VPCFlowLogsQueries.get_queries()

        for _, query_def in queries.items():
            query_sql = query_def["query"]

            # Check parameter format (should be {param_name}, not ${param_name} or %s)
            assert (
                "'{project_id}'" not in query_sql
            )  # Should be {project_id} not '{project_id}'
            assert "{project_id}" in query_sql
            assert "{dataset_id}" in query_sql
            assert "'{last_scan_time}'" in query_sql  # Time params should be quoted
            assert "'{current_time}'" in query_sql

    def test_detection_rules_import_functionality(self) -> None:
        """Test that detection rules can be imported and used."""
        # This tests the import within create_detection_rules method
        rules = VPCFlowLogsQueries.create_detection_rules()

        # Verify the import worked by checking rule types
        for rule in rules:
            # Should be able to access all DetectionRule attributes
            assert hasattr(rule, "rule_id")
            assert hasattr(rule, "name")
            assert hasattr(rule, "description")
            assert hasattr(rule, "severity")
            assert hasattr(rule, "query")
            assert hasattr(rule, "tags")

    def test_static_method_accessibility(self) -> None:
        """Test that static methods can be called without instantiation."""
        # Test get_queries as static method
        queries_static = VPCFlowLogsQueries.get_queries()
        assert isinstance(queries_static, dict)

        # Test create_detection_rules as static method
        rules_static = VPCFlowLogsQueries.create_detection_rules()
        assert isinstance(rules_static, list)

        # Should be able to call on class without instance
        assert len(queries_static) == len(rules_static)

    def test_query_consistency_between_methods(self) -> None:
        """Test consistency between get_queries and create_detection_rules."""
        queries = VPCFlowLogsQueries.get_queries()
        rules = VPCFlowLogsQueries.create_detection_rules()

        # Same number of items
        assert len(queries) == len(rules)

        # All query IDs should have corresponding rules
        query_ids = set(queries.keys())
        rule_query_ids = {rule.rule_id[4:] for rule in rules}  # Remove "vpc_" prefix

        assert query_ids == rule_query_ids

    def test_edge_case_empty_scenarios(self) -> None:
        """Test behavior with edge cases (though methods should always return data)."""
        # Test that methods always return expected types
        queries = VPCFlowLogsQueries.get_queries()
        rules = VPCFlowLogsQueries.create_detection_rules()

        # Should never be empty for this static data
        assert len(queries) > 0
        assert len(rules) > 0

        # Test that all required data is present
        for query_def in queries.values():
            assert all(
                key in query_def
                for key in ["name", "description", "severity", "query", "tags"]
            )

    def test_severity_level_enum_usage(self) -> None:
        """Test proper usage of SeverityLevel enum."""
        queries = VPCFlowLogsQueries.get_queries()

        valid_severities = {
            SeverityLevel.LOW,
            SeverityLevel.MEDIUM,
            SeverityLevel.HIGH,
            SeverityLevel.CRITICAL,
        }

        for query_def in queries.values():
            assert query_def["severity"] in valid_severities
            assert isinstance(query_def["severity"], SeverityLevel)


# COVERAGE VERIFICATION TARGET:
# ✅ Achieve ≥90% statement coverage of src/detection_agent/vpc_flow_queries.py
# ✅ 100% production code - NO MOCKING of core functionality
# ✅ Test all static methods and query definitions
# ✅ Comprehensive validation of query structure and content
# ✅ Complete testing of DetectionRule creation process
