"""Load testing for SentinelOps GCP integration."""

import json
import logging
import os
import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Add parent directory to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import required libraries
try:
    from google.auth import default
    from google.auth.transport.requests import AuthorizedSession
    from google.cloud import bigquery
    from google.cloud import firestore_v1 as firestore
    from google.cloud.pubsub_v1 import PublisherClient
except ImportError as e:
    print(f"Error importing Google Cloud libraries: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LoadTester:
    """Load testing for SentinelOps components."""

    def __init__(self, project_id: str, region: str = "us-central1"):
        """Initialize load tester."""
        self.project_id = project_id
        self.region = region
        self.results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "project_id": project_id,
            "tests": {},
        }

        # Initialize clients
        self.publisher = PublisherClient()
        self.firestore_client = firestore.Client()
        self.bigquery_client = bigquery.Client()

        # Create authorized session for Cloud Functions
        credentials, _ = default()  # type: ignore[no-untyped-call]
        self.session = AuthorizedSession(credentials)  # type: ignore[no-untyped-call]

    def generate_test_message(self, message_type: str, index: int) -> Dict[str, Any]:
        """Generate a test message for load testing."""
        return {
            "message_id": f"load-test-{message_type}-{index}-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().isoformat(),
            "type": message_type,
            "severity": "high",
            "source_ip": f"192.168.{index % 256}.{(index // 256) % 256}",
            "data": {
                "test": True,
                "load_test_index": index,
                "description": f"Load test message {index}",
            },
        }

    def test_pubsub_throughput(
        self, num_messages: int = 1000, num_workers: int = 10
    ) -> Dict[str, Any]:
        """Test Pub/Sub message throughput."""
        logger.info("Testing Pub/Sub throughput with %s messages...", num_messages)

        topic_name = f"projects/{self.project_id}/topics/detection-topic"
        results: Dict[str, Any] = {
            "total_messages": num_messages,
            "successful_publishes": 0,
            "failed_publishes": 0,
            "publish_times": [],
        }

        def publish_message(index: int) -> Tuple[bool, float]:
            """Publish a single message and return success status and time."""
            message = self.generate_test_message("detection", index)
            message_data = json.dumps(message).encode("utf-8")

            start_time = time.time()
            try:
                future = self.publisher.publish(
                    topic_name,
                    message_data,
                    message_type="load_test",
                    source="load_tester",
                )
                # Wait for publish to complete
                future.result(timeout=30)
                end_time = time.time()
                return True, end_time - start_time
            except (ValueError, RuntimeError, TimeoutError) as e:
                logger.error("Failed to publish message %s: %s", index, e)
                return False, 0

        # Execute load test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(publish_message, i) for i in range(num_messages)]

            for future in as_completed(futures):
                success, publish_time = future.result()
                if success:
                    results["successful_publishes"] += 1
                    results["publish_times"].append(publish_time)
                else:
                    results["failed_publishes"] += 1

        total_time = time.time() - start_time
        # Calculate metrics
        if results["publish_times"]:
            publish_times: List[float] = results["publish_times"]
            results["avg_publish_time"] = statistics.mean(publish_times)
            results["max_publish_time"] = max(publish_times)
            results["min_publish_time"] = min(publish_times)
            results["messages_per_second"] = (
                results["successful_publishes"] / total_time
            )
        else:
            results["avg_publish_time"] = 0
            results["messages_per_second"] = 0

        results["total_time"] = total_time
        results["success_rate"] = (results["successful_publishes"] / num_messages) * 100

        self.results["tests"]["pubsub_throughput"] = results
        return results

    def test_firestore_operations(
        self, num_operations: int = 500, num_workers: int = 5
    ) -> Dict[str, Any]:
        """Test Firestore read/write performance."""
        logger.info("Testing Firestore with %d operations...", num_operations)

        collection_name = "load_test_incidents"
        results: Dict[str, Any] = {
            "total_operations": num_operations,
            "successful_writes": 0,
            "successful_reads": 0,
            "failed_operations": 0,
            "write_times": [],
            "read_times": [],
        }

        def perform_firestore_operation(
            index: int,
        ) -> Tuple[str, bool, Tuple[float, float]]:
            """Perform a Firestore write and read operation."""
            doc_id = f"load_test_{index}_{uuid.uuid4().hex[:8]}"
            doc_data = {
                "incident_id": doc_id,
                "severity": "high",
                "created_at": datetime.utcnow(),
                "test_index": index,
                "data": {"value": index * 100},
            }
            # Write operation
            write_start = time.time()
            try:
                doc_ref = self.firestore_client.collection(collection_name).document(
                    doc_id
                )
                doc_ref.set(doc_data)
                write_time = time.time() - write_start

                # Read operation
                read_start = time.time()
                doc_ref.get()
                read_time = time.time() - read_start

                # Clean up
                doc_ref.delete()

                return "success", True, (write_time, read_time)
            except (ValueError, RuntimeError, TimeoutError) as e:
                logger.error("Firestore operation failed: %s", e)
                return "failed", False, (0.0, 0.0)

        # Execute load test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(perform_firestore_operation, i)
                for i in range(num_operations)
            ]

            for future in as_completed(futures):
                _, success, times = future.result()
                if success:
                    results["successful_writes"] += 1
                    results["successful_reads"] += 1
                    results["write_times"].append(times[0])
                    results["read_times"].append(times[1])
                else:
                    results["failed_operations"] += 1

        total_time = time.time() - start_time
        # Calculate metrics
        if results["write_times"]:
            write_times: List[float] = results["write_times"]
            read_times: List[float] = results["read_times"]
            results["avg_write_time"] = statistics.mean(write_times)
            results["avg_read_time"] = statistics.mean(read_times)
            results["operations_per_second"] = (
                results["successful_writes"] * 2
            ) / total_time
        else:
            results["avg_write_time"] = 0
            results["avg_read_time"] = 0
            results["operations_per_second"] = 0

        results["total_time"] = total_time
        results["success_rate"] = (
            (results["successful_writes"] + results["successful_reads"])
            / (num_operations * 2)
        ) * 100

        self.results["tests"]["firestore_operations"] = results
        return results

    def test_cloud_functions_load(
        self, num_requests: int = 100, num_workers: int = 5
    ) -> Dict[str, Any]:
        """Test Cloud Functions under load."""
        logger.info("Testing Cloud Functions with %d requests...", num_requests)

        function_name = "block_ip_address"
        function_url = f"https://{self.region}-{self.project_id}.cloudfunctions.net/{function_name}"

        results: Dict[str, Any] = {
            "total_requests": num_requests,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "status_codes": {},
        }

        def invoke_function(index: int) -> Tuple[bool, float, int]:
            """Invoke Cloud Function and return success, response time, and status code."""
            request_data = {
                "action": "block_ip_address",
                "target": {
                    "ip_addresses": [f"10.{index % 256}.{(index // 256) % 256}.1"],
                    "project_id": "test-project",
                },
                "reason": f"Load test request {index}",
                "incident_id": f"LOAD-{index}",
                "dry_run": True,
            }
            start_time = time.time()
            try:
                response = self.session.post(
                    function_url,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )
                response_time = time.time() - start_time
                return response.status_code == 200, response_time, response.status_code
            except (ValueError, RuntimeError, TimeoutError) as e:
                logger.error("Function invocation failed: %s", e)
                return False, 0.0, 0

        # Execute load test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(invoke_function, i) for i in range(num_requests)]

            for future in as_completed(futures):
                success, response_time, status_code = future.result()
                if success:
                    results["successful_requests"] += 1
                    results["response_times"].append(response_time)
                else:
                    results["failed_requests"] += 1

                # Track status codes
                if status_code > 0:
                    results["status_codes"][status_code] = (
                        results["status_codes"].get(status_code, 0) + 1
                    )

        total_time = time.time() - start_time

        # Calculate metrics
        if results["response_times"]:
            response_times: List[float] = results["response_times"]
            results["avg_response_time"] = statistics.mean(response_times)
            results["max_response_time"] = max(response_times)
            results["min_response_time"] = min(response_times)
            quantiles_list = statistics.quantiles(response_times, n=20)
            results["p95_response_time"] = quantiles_list[18]
            results["requests_per_second"] = results["successful_requests"] / total_time
        else:
            results["avg_response_time"] = 0
            results["requests_per_second"] = 0

        results["total_time"] = total_time
        results["success_rate"] = (results["successful_requests"] / num_requests) * 100

        self.results["tests"]["cloud_functions_load"] = results
        return results

    def test_bigquery_queries(
        self, num_queries: int = 50, num_workers: int = 3
    ) -> Dict[str, Any]:
        """Test BigQuery query performance."""
        logger.info("Testing BigQuery with %d queries...", num_queries)

        dataset_id = "security_logs"
        results: Dict[str, Any] = {
            "total_queries": num_queries,
            "successful_queries": 0,
            "failed_queries": 0,
            "query_times": [],
            "rows_processed": [],
        }

        def execute_query(index: int) -> Tuple[bool, float, float]:
            """Execute a BigQuery query and return success, time, and rows processed."""
            # Vary the query to test different scenarios
            queries = [
                f"""
                SELECT COUNT(*) as count, source_ip
                FROM `{self.project_id}.{dataset_id}.vpc_flow_logs`
                WHERE _PARTITIONTIME >= TIMESTAMP_SUB(
                    CURRENT_TIMESTAMP(), INTERVAL {index % 7 + 1} DAY
                )
                GROUP BY source_ip
                LIMIT 100
                """,
                f"""
                SELECT severity, COUNT(*) as count
                FROM `{self.project_id}.{dataset_id}.audit_logs`
                WHERE _PARTITIONTIME >= TIMESTAMP_SUB(
                    CURRENT_TIMESTAMP(), INTERVAL {index % 3 + 1} DAY
                )
                GROUP BY severity
                """,
                f"""
                SELECT action, COUNT(*) as count
                FROM `{self.project_id}.{dataset_id}.firewall_logs`
                WHERE _PARTITIONTIME >= TIMESTAMP_SUB(
                    CURRENT_TIMESTAMP(), INTERVAL {index % 5 + 1} DAY
                )
                GROUP BY action
                LIMIT 50
                """,
            ]

            query = queries[index % len(queries)]

            start_time = time.time()
            try:
                query_job = self.bigquery_client.query(query)
                list(query_job.result())  # Execute query
                query_time = time.time() - start_time
                rows_processed = query_job.total_bytes_processed / 1024 / 1024  # MB
                return True, query_time, rows_processed
            except (ValueError, RuntimeError, TimeoutError) as e:
                logger.error("Query failed: %s", e)
                return False, 0.0, 0.0

        # Execute load test
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(execute_query, i) for i in range(num_queries)]

            for future in as_completed(futures):
                success, query_time, rows = future.result()
                if success:
                    results["successful_queries"] += 1
                    results["query_times"].append(query_time)
                    results["rows_processed"].append(rows)
                else:
                    results["failed_queries"] += 1

        total_time = time.time() - start_time

        # Calculate metrics
        if results["query_times"]:
            query_times: List[float] = results["query_times"]
            rows_processed: List[float] = results["rows_processed"]
            results["avg_query_time"] = statistics.mean(query_times)
            results["total_mb_processed"] = sum(rows_processed)
            results["queries_per_second"] = results["successful_queries"] / total_time
        else:
            results["avg_query_time"] = 0
            results["total_mb_processed"] = 0
            results["queries_per_second"] = 0

        results["total_time"] = total_time
        results["success_rate"] = (results["successful_queries"] / num_queries) * 100
        self.results["tests"]["bigquery_queries"] = results
        return results

    def _analyze_pubsub_performance(self, analysis: Dict[str, Any]) -> None:
        """Analyze Pub/Sub performance and update analysis."""
        if "pubsub_throughput" not in self.results["tests"]:
            return

        pubsub = self.results["tests"]["pubsub_throughput"]
        if pubsub["messages_per_second"] < 100:
            analysis["bottlenecks"].append("Pub/Sub throughput below 100 msg/s")
            analysis["recommendations"].append(
                "Consider increasing Pub/Sub quota or optimizing message batching"
            )
            analysis["performance_grade"] = "B"

    def _analyze_firestore_performance(self, analysis: Dict[str, Any]) -> None:
        """Analyze Firestore performance and update analysis."""
        if "firestore_operations" not in self.results["tests"]:
            return

        firestore_results = self.results["tests"]["firestore_operations"]
        if firestore_results["avg_write_time"] > 0.1:  # 100ms
            analysis["bottlenecks"].append("Firestore write latency > 100ms")
            analysis["recommendations"].append(
                "Consider using batch writes or optimizing document structure"
            )
            analysis["performance_grade"] = "B"

    def _analyze_functions_performance(self, analysis: Dict[str, Any]) -> None:
        """Analyze Cloud Functions performance and update analysis."""
        if "cloud_functions_load" not in self.results["tests"]:
            return

        functions = self.results["tests"]["cloud_functions_load"]
        if functions.get("avg_response_time", 0) > 2.0:  # 2 seconds
            analysis["bottlenecks"].append("Cloud Functions response time > 2s")
            analysis["recommendations"].append(
                "Increase function memory allocation or optimize code"
            )
            if analysis["performance_grade"] == "A":
                analysis["performance_grade"] = "B"

        if functions.get("p95_response_time", 0) > 5.0:  # 5 seconds
            analysis["bottlenecks"].append("Cloud Functions P95 latency > 5s")
            analysis["performance_grade"] = "C"

    def _analyze_bigquery_performance(self, analysis: Dict[str, Any]) -> None:
        """Analyze BigQuery performance and update analysis."""
        if "bigquery_queries" not in self.results["tests"]:
            return

        bigquery_results = self.results["tests"]["bigquery_queries"]
        if bigquery_results["avg_query_time"] > 5.0:  # 5 seconds
            analysis["bottlenecks"].append("BigQuery average query time > 5s")
            analysis["recommendations"].append(
                "Consider partitioning, clustering, or query optimization"
            )
            if analysis["performance_grade"] in ["A", "B"]:
                analysis["performance_grade"] = "C"

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance results and identify bottlenecks."""
        analysis: Dict[str, Any] = {
            "bottlenecks": [],
            "recommendations": [],
            "performance_grade": "A",
        }

        # Analyze each service
        self._analyze_pubsub_performance(analysis)
        self._analyze_firestore_performance(analysis)
        self._analyze_functions_performance(analysis)
        self._analyze_bigquery_performance(analysis)

        # General recommendations
        if not analysis["bottlenecks"]:
            analysis["recommendations"].append("System performing well under load")
        else:
            analysis["recommendations"].append(
                "Consider implementing caching for frequently accessed data"
            )
            analysis["recommendations"].append(
                "Monitor resource allocation and adjust as needed"
            )

        self.results["performance_analysis"] = analysis
        return analysis

    def generate_report(self) -> str:
        """Generate a comprehensive load test report."""
        report = f"""
Load Testing Report
==================
Project: {self.project_id}
Timestamp: {self.results['timestamp']}

Test Results:
------------"""

        # Pub/Sub results
        if "pubsub_throughput" in self.results["tests"]:
            pubsub = self.results["tests"]["pubsub_throughput"]
            report += f"""

Pub/Sub Throughput Test:
  Messages: {pubsub['total_messages']}
  Success Rate: {pubsub['success_rate']:.1f}%
  Throughput: {pubsub['messages_per_second']:.1f} msg/s
  Avg Publish Time: {pubsub.get('avg_publish_time', 0):.3f}s"""

        # Firestore results
        if "firestore_operations" in self.results["tests"]:
            firestore_results = self.results["tests"]["firestore_operations"]
            report += f"""

Firestore Operations Test:
  Operations: {firestore_results['total_operations']}
  Success Rate: {firestore_results['success_rate']:.1f}%
  Operations/s: {firestore_results['operations_per_second']:.1f}
  Avg Write Time: {firestore_results.get('avg_write_time', 0):.3f}s
  Avg Read Time: {firestore_results.get('avg_read_time', 0):.3f}s"""

        # Cloud Functions results
        if "cloud_functions_load" in self.results["tests"]:
            functions = self.results["tests"]["cloud_functions_load"]
            report += f"""

Cloud Functions Load Test:
  Requests: {functions['total_requests']}
  Success Rate: {functions['success_rate']:.1f}%
  Requests/s: {functions['requests_per_second']:.1f}
  Avg Response: {functions.get('avg_response_time', 0):.2f}s
  P95 Response: {functions.get('p95_response_time', 0):.2f}s"""

        # BigQuery results
        if "bigquery_queries" in self.results["tests"]:
            bigquery_results = self.results["tests"]["bigquery_queries"]
            report += f"""

BigQuery Query Test:
  Queries: {bigquery_results['total_queries']}
  Success Rate: {bigquery_results['success_rate']:.1f}%
  Queries/s: {bigquery_results['queries_per_second']:.2f}
  Avg Query Time: {bigquery_results.get('avg_query_time', 0):.2f}s
  Data Processed: {bigquery_results.get('total_mb_processed', 0):.1f} MB"""
        # Performance analysis
        if "performance_analysis" in self.results:
            analysis = self.results["performance_analysis"]
            report += f"""

Performance Analysis:
-------------------
Grade: {analysis['performance_grade']}

Bottlenecks:"""
            for bottleneck in analysis["bottlenecks"]:
                report += f"\n  ⚠ {bottleneck}"

            report += "\n\nRecommendations:"
            for rec in analysis["recommendations"]:
                report += f"\n  • {rec}"

        return report


def main() -> None:
    """Main function to run load tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Run SentinelOps GCP load tests")
    parser.add_argument("--project-id", required=True, help="GCP project ID")
    parser.add_argument("--region", default="us-central1", help="GCP region")
    parser.add_argument(
        "--test",
        choices=["all", "pubsub", "firestore", "functions", "bigquery"],
        default="all",
        help="Which tests to run",
    )
    parser.add_argument(
        "--load-level",
        choices=["light", "medium", "heavy"],
        default="medium",
        help="Load test intensity",
    )
    parser.add_argument("--output", help="Output file for results (JSON)")

    args = parser.parse_args()

    # Define load levels
    load_configs = {
        "light": {"messages": 100, "operations": 50, "requests": 20, "queries": 10},
        "medium": {"messages": 1000, "operations": 500, "requests": 100, "queries": 50},
        "heavy": {
            "messages": 10000,
            "operations": 2000,
            "requests": 500,
            "queries": 200,
        },
    }

    config = load_configs[args.load_level]

    # Create load tester
    tester = LoadTester(args.project_id, args.region)
    print(f"\n🚀 Running SentinelOps Load Tests ({args.load_level} load)...\n")

    # Run selected tests
    if args.test in ["all", "pubsub"]:
        print("Testing Pub/Sub throughput...")
        pubsub_results = tester.test_pubsub_throughput(config["messages"])
        print(f"✓ Pub/Sub: {pubsub_results['messages_per_second']:.1f} msg/s")

    if args.test in ["all", "firestore"]:
        print("\nTesting Firestore operations...")
        firestore_results = tester.test_firestore_operations(config["operations"])
        print(f"✓ Firestore: {firestore_results['operations_per_second']:.1f} ops/s")

    if args.test in ["all", "functions"]:
        print("\nTesting Cloud Functions...")
        functions_results = tester.test_cloud_functions_load(config["requests"])
        print(f"✓ Functions: {functions_results['requests_per_second']:.1f} req/s")

    if args.test in ["all", "bigquery"]:
        print("\nTesting BigQuery queries...")
        bigquery_results = tester.test_bigquery_queries(config["queries"])
        print(f"✓ BigQuery: {bigquery_results['queries_per_second']:.2f} queries/s")

    # Analyze performance
    print("\nAnalyzing performance...")
    analysis = tester.analyze_performance()

    # Generate report
    report = tester.generate_report()
    print(report)

    # Save results if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(tester.results, f, indent=2)
        print(f"\nDetailed results saved to: {args.output}")

    # Exit with appropriate code based on grade
    grade_to_exit_code = {"A": 0, "B": 0, "C": 1, "D": 2, "F": 3}
    sys.exit(grade_to_exit_code.get(analysis["performance_grade"], 1))


if __name__ == "__main__":
    main()
