# Performance Profiling Guide

This comprehensive guide covers performance profiling and optimization techniques for SentinelOps agents built with Google's Agent Development Kit (ADK), including profiling tools, optimization strategies, and best practices.

## Table of Contents
1. [Performance Overview](#performance-overview)
2. [Profiling Tools](#profiling-tools)
3. [Agent Performance Profiling](#agent-performance-profiling)
4. [API and Database Optimization](#api-and-database-optimization)
5. [Memory Profiling](#memory-profiling)
6. [Cost Optimization](#cost-optimization)
7. [Performance Monitoring](#performance-monitoring)
8. [Optimization Strategies](#optimization-strategies)

## Performance Overview

### Performance Goals
- **Agent Latency**: < 100ms for tool execution
- **End-to-End Response**: < 30s for incident resolution
- **Throughput**: > 1000 events/second per detection agent
- **Memory Usage**: < 1GB per agent instance
- **API Costs**: < $0.01 per incident processed

### Performance Stack
```
┌─────────────────────────────────────┐
│          Application Layer          │
│  - Agent Logic                      │
│  - Tool Execution                   │
│  - Business Rules                   │
├─────────────────────────────────────┤
│          ADK Framework              │
│  - Transfer System                  │
│  - Tool Validation                  │
│  - Context Management               │
├─────────────────────────────────────┤
│          Infrastructure             │
│  - Cloud Run Instances              │
│  - Firestore Database               │
│  - BigQuery Analytics               │
└─────────────────────────────────────┘
```

## Profiling Tools

### 1. Python Profilers

```python
# src/profiling/profiler_setup.py
import cProfile
import pstats
import io
from memory_profiler import profile
from line_profiler import LineProfiler

class ProfilerManager:
    """Manage different profiling tools."""

    def __init__(self):
        self.cpu_profiler = cProfile.Profile()
        self.line_profiler = LineProfiler()
        self.profiles = {}

    def profile_function(self, func, *args, **kwargs):
        """Profile a single function execution."""
        # CPU profiling
        self.cpu_profiler.enable()
        result = func(*args, **kwargs)
        self.cpu_profiler.disable()

        # Generate report
        s = io.StringIO()
        ps = pstats.Stats(self.cpu_profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions

        self.profiles[func.__name__] = {
            "cpu_profile": s.getvalue(),
            "result": result
        }

        return result

    def profile_async_function(self, async_func):
        """Decorator for profiling async functions."""
        async def wrapper(*args, **kwargs):
            import asyncio

            # Start profiling
            self.cpu_profiler.enable()
            start_time = asyncio.get_event_loop().time()

            try:
                result = await async_func(*args, **kwargs)
            finally:
                # Stop profiling
                self.cpu_profiler.disable()
                end_time = asyncio.get_event_loop().time()

                # Store timing
                self.profiles[async_func.__name__] = {
                    "duration": end_time - start_time,
                    "timestamp": datetime.utcnow()
                }

            return result

        return wrapper
```

### 2. ADK Performance Inspector

```python
# src/profiling/adk_performance_inspector.py
from google.adk.profiling import PerformanceInspector
import json

class ADKPerformanceInspector:
    """Specialized profiling for ADK components."""

    def __init__(self):
        self.inspector = PerformanceInspector()
        self.metrics = {
            "tool_executions": {},
            "transfer_times": {},
            "llm_calls": {},
            "context_operations": {}
        }

    def profile_agent(self, agent, duration_seconds=60):
        """Profile ADK agent performance."""
        print(f"Profiling {agent.name} for {duration_seconds} seconds...")

        # Attach to agent
        self.inspector.attach_to_agent(agent)

        # Set up callbacks
        self.inspector.on_tool_execution = self._record_tool_execution
        self.inspector.on_transfer = self._record_transfer
        self.inspector.on_llm_call = self._record_llm_call

        # Run profiling
        self.inspector.start_profiling()
        time.sleep(duration_seconds)
        self.inspector.stop_profiling()

        # Generate report
        return self._generate_performance_report()

    def _record_tool_execution(self, event):
        """Record tool execution metrics."""
        tool_name = event.tool_name
        duration = event.duration_ms

        if tool_name not in self.metrics["tool_executions"]:
            self.metrics["tool_executions"][tool_name] = []

        self.metrics["tool_executions"][tool_name].append({
            "duration_ms": duration,
            "timestamp": event.timestamp,
            "success": event.success,
            "context_size": event.context_size
        })

    def _generate_performance_report(self):
        """Generate comprehensive performance report."""
        report = {
            "summary": self._calculate_summary(),
            "tool_performance": self._analyze_tool_performance(),
            "transfer_performance": self._analyze_transfer_performance(),
            "llm_performance": self._analyze_llm_performance(),
            "recommendations": self._generate_recommendations()
        }

        return report

    def _analyze_tool_performance(self):
        """Analyze tool execution performance."""
        tool_stats = {}

        for tool_name, executions in self.metrics["tool_executions"].items():
            durations = [e["duration_ms"] for e in executions]

            tool_stats[tool_name] = {
                "count": len(executions),
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p95_duration_ms": np.percentile(durations, 95),
                "success_rate": sum(1 for e in executions if e["success"]) / len(executions)
            }

        return tool_stats
```

### 3. Flame Graph Generator

```python
# scripts/profiling/generate_flame_graph.py
import py_spy
import subprocess

class FlameGraphGenerator:
    """Generate flame graphs for performance visualization."""

    def generate_flame_graph(self, pid, duration=30, output="flame_graph.svg"):
        """Generate flame graph for running process."""
        try:
            # Use py-spy to record
            subprocess.run([
                "py-spy", "record",
                "-o", output,
                "-d", str(duration),
                "-p", str(pid),
                "-f", "flamegraph"
            ], check=True)

            print(f"Flame graph saved to {output}")

        except subprocess.CalledProcessError as e:
            print(f"Error generating flame graph: {e}")

    def generate_agent_flame_graph(self, agent_name):
        """Generate flame graph for specific agent."""
        # Find agent process
        pid = self._find_agent_pid(agent_name)

        if pid:
            output_file = f"flame_graph_{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
            self.generate_flame_graph(pid, output=output_file)
        else:
            print(f"Could not find process for agent: {agent_name}")

    def _find_agent_pid(self, agent_name):
        """Find PID of running agent."""
        import psutil

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if agent_name in cmdline and 'main.py' in cmdline:
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return None
```

## Agent Performance Profiling

### 1. Detection Agent Profiling

```python
# src/profiling/detection_agent_profiler.py
class DetectionAgentProfiler:
    """Profile detection agent performance."""

    def __init__(self, agent):
        self.agent = agent
        self.query_times = []
        self.rule_evaluation_times = []
        self.event_processing_times = []

    async def profile_detection_cycle(self):
        """Profile complete detection cycle."""
        cycle_start = time.time()

        # Profile log query
        query_start = time.time()
        logs = await self._profile_log_query()
        query_time = time.time() - query_start
        self.query_times.append(query_time)

        # Profile rule evaluation
        eval_start = time.time()
        incidents = await self._profile_rule_evaluation(logs)
        eval_time = time.time() - eval_start
        self.rule_evaluation_times.append(eval_time)

        # Profile event processing
        process_start = time.time()
        results = await self._profile_event_processing(incidents)
        process_time = time.time() - process_start
        self.event_processing_times.append(process_time)

        cycle_time = time.time() - cycle_start

        return {
            "cycle_time": cycle_time,
            "query_time": query_time,
            "eval_time": eval_time,
            "process_time": process_time,
            "logs_processed": len(logs),
            "incidents_created": len(incidents)
        }

    async def _profile_log_query(self):
        """Profile BigQuery log queries."""
        with self.agent.profiler.profile("bigquery_query"):
            query = f"""
            SELECT *
            FROM `{self.agent.project_id}.{self.agent.dataset}.logs`
            WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
            LIMIT 10000
            """

            query_job = self.agent.bigquery_client.query(query)
            results = list(query_job.result())

            # Record query statistics
            self.agent.metrics.record_query_stats({
                "bytes_processed": query_job.total_bytes_processed,
                "bytes_billed": query_job.total_bytes_billed,
                "slot_millis": query_job.slot_millis,
                "row_count": len(results)
            })

            return results
```

### 2. Analysis Agent Profiling

```python
# src/profiling/analysis_agent_profiler.py
class AnalysisAgentProfiler:
    """Profile analysis agent with focus on LLM performance."""

    def __init__(self, agent):
        self.agent = agent
        self.llm_metrics = {
            "prompt_tokens": [],
            "completion_tokens": [],
            "total_tokens": [],
            "latency_ms": [],
            "cache_hits": 0,
            "cache_misses": 0
        }

    async def profile_analysis(self, incident):
        """Profile incident analysis performance."""
        analysis_start = time.time()

        # Check cache first
        cache_key = self._generate_cache_key(incident)
        cached_result = await self._check_cache(cache_key)

        if cached_result:
            self.llm_metrics["cache_hits"] += 1
            return {
                "cached": True,
                "latency_ms": (time.time() - analysis_start) * 1000,
                "result": cached_result
            }

        self.llm_metrics["cache_misses"] += 1

        # Profile LLM call
        llm_start = time.time()

        # Prepare prompt
        prompt = self._build_analysis_prompt(incident)
        prompt_tokens = self._estimate_tokens(prompt)

        # Call LLM
        response = await self.agent.llm_client.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2048
        )

        llm_latency = (time.time() - llm_start) * 1000

        # Record metrics
        self.llm_metrics["prompt_tokens"].append(prompt_tokens)
        self.llm_metrics["completion_tokens"].append(response.usage.completion_tokens)
        self.llm_metrics["total_tokens"].append(response.usage.total_tokens)
        self.llm_metrics["latency_ms"].append(llm_latency)

        # Cache result
        await self._cache_result(cache_key, response.text)

        total_latency = (time.time() - analysis_start) * 1000

        return {
            "cached": False,
            "latency_ms": total_latency,
            "llm_latency_ms": llm_latency,
            "tokens_used": response.usage.total_tokens,
            "result": response.text
        }

    def generate_cost_report(self):
        """Generate LLM cost analysis report."""
        # Gemini pricing (example rates)
        PROMPT_TOKEN_COST = 0.00025  # per 1K tokens
        COMPLETION_TOKEN_COST = 0.0005  # per 1K tokens

        total_prompt_tokens = sum(self.llm_metrics["prompt_tokens"])
        total_completion_tokens = sum(self.llm_metrics["completion_tokens"])

        prompt_cost = (total_prompt_tokens / 1000) * PROMPT_TOKEN_COST
        completion_cost = (total_completion_tokens / 1000) * COMPLETION_TOKEN_COST
        total_cost = prompt_cost + completion_cost

        cache_ratio = (
            self.llm_metrics["cache_hits"] /
            (self.llm_metrics["cache_hits"] + self.llm_metrics["cache_misses"])
            if self.llm_metrics["cache_misses"] > 0 else 0
        )

        return {
            "total_requests": len(self.llm_metrics["latency_ms"]),
            "cache_hit_ratio": cache_ratio,
            "total_tokens": sum(self.llm_metrics["total_tokens"]),
            "estimated_cost_usd": total_cost,
            "avg_latency_ms": np.mean(self.llm_metrics["latency_ms"]),
            "p95_latency_ms": np.percentile(self.llm_metrics["latency_ms"], 95)
        }
```

### 3. Remediation Agent Profiling

```python
# src/profiling/remediation_agent_profiler.py
class RemediationAgentProfiler:
    """Profile remediation agent focusing on API latencies."""

    def __init__(self, agent):
        self.agent = agent
        self.api_metrics = defaultdict(list)
        self.action_metrics = defaultdict(list)

    async def profile_remediation_action(self, action_type, resource_id):
        """Profile specific remediation action."""
        action_start = time.time()

        # Pre-execution checks
        check_start = time.time()
        checks_passed = await self._profile_pre_checks(action_type, resource_id)
        check_time = time.time() - check_start

        if not checks_passed:
            return {
                "action": action_type,
                "status": "skipped",
                "reason": "pre-checks failed",
                "duration_ms": (time.time() - action_start) * 1000
            }

        # Execute action
        exec_start = time.time()

        if action_type == "block_ip":
            result = await self._profile_block_ip(resource_id)
        elif action_type == "isolate_vm":
            result = await self._profile_isolate_vm(resource_id)
        elif action_type == "revoke_credentials":
            result = await self._profile_revoke_credentials(resource_id)

        exec_time = time.time() - exec_start

        # Post-execution verification
        verify_start = time.time()
        verified = await self._profile_verification(action_type, resource_id)
        verify_time = time.time() - verify_start

        total_time = time.time() - action_start

        # Record metrics
        self.action_metrics[action_type].append({
            "total_ms": total_time * 1000,
            "check_ms": check_time * 1000,
            "exec_ms": exec_time * 1000,
            "verify_ms": verify_time * 1000,
            "success": result.get("success", False)
        })

        return {
            "action": action_type,
            "status": "completed" if result.get("success") else "failed",
            "duration_ms": total_time * 1000,
            "breakdown": {
                "pre_checks_ms": check_time * 1000,
                "execution_ms": exec_time * 1000,
                "verification_ms": verify_time * 1000
            }
        }

    async def _profile_block_ip(self, ip_address):
        """Profile IP blocking with Cloud Armor."""
        api_start = time.time()

        # Create firewall rule
        rule = {
            "name": f"block-ip-{ip_address.replace('.', '-')}",
            "sourceRanges": [ip_address],
            "denied": [{"IPProtocol": "all"}],
            "priority": 1000
        }

        try:
            operation = self.agent.compute_client.firewalls().insert(
                project=self.agent.project_id,
                body=rule
            ).execute()

            # Wait for operation
            result = await self._wait_for_operation(operation)

            api_time = time.time() - api_start
            self.api_metrics["compute.firewalls.insert"].append(api_time * 1000)

            return {"success": True, "operation_id": operation['name']}

        except Exception as e:
            api_time = time.time() - api_start
            self.api_metrics["compute.firewalls.insert_error"].append(api_time * 1000)
            return {"success": False, "error": str(e)}
```

## API and Database Optimization

### 1. BigQuery Optimization

```python
# src/optimization/bigquery_optimizer.py
class BigQueryOptimizer:
    """Optimize BigQuery queries for performance and cost."""

    def __init__(self, project_id):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.query_cache = {}

    def analyze_query_performance(self, query):
        """Analyze query performance and suggest optimizations."""
        # Dry run to get query stats
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query_job = self.client.query(query, job_config=job_config)

        bytes_processed = query_job.total_bytes_processed

        # Analyze query plan
        analysis = {
            "bytes_processed": bytes_processed,
            "estimated_cost": (bytes_processed / 1e12) * 5.00,  # $5 per TB
            "suggestions": []
        }

        # Check for full table scans
        if "WHERE" not in query.upper():
            analysis["suggestions"].append(
                "Add WHERE clause to filter data and reduce bytes processed"
            )

        # Check for SELECT *
        if "SELECT *" in query.upper():
            analysis["suggestions"].append(
                "Replace SELECT * with specific columns to reduce data transfer"
            )

        # Check for partitioning opportunities
        if "timestamp" in query.lower() and "_PARTITIONDATE" not in query:
            analysis["suggestions"].append(
                "Use _PARTITIONDATE for timestamp filtering on partitioned tables"
            )

        # Suggest clustering
        if bytes_processed > 1e9:  # > 1GB
            analysis["suggestions"].append(
                "Consider clustering table on frequently filtered columns"
            )

        return analysis

    def optimize_detection_queries(self):
        """Optimize common detection queries."""
        optimizations = []

        # Optimize log scanning query
        original_query = """
        SELECT *
        FROM `project.dataset.logs`
        WHERE severity IN ('ERROR', 'CRITICAL')
        ORDER BY timestamp DESC
        """

        optimized_query = """
        SELECT timestamp, resource, severity, message, jsonPayload
        FROM `project.dataset.logs`
        WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
          AND severity IN ('ERROR', 'CRITICAL')
          AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        ORDER BY timestamp DESC
        LIMIT 1000
        """

        original_analysis = self.analyze_query_performance(original_query)
        optimized_analysis = self.analyze_query_performance(optimized_query)

        savings = (
            original_analysis["bytes_processed"] -
            optimized_analysis["bytes_processed"]
        ) / original_analysis["bytes_processed"]

        optimizations.append({
            "query": "log_scanning",
            "bytes_saved": original_analysis["bytes_processed"] - optimized_analysis["bytes_processed"],
            "cost_saved": original_analysis["estimated_cost"] - optimized_analysis["estimated_cost"],
            "percentage_saved": savings * 100
        })

        return optimizations
```

### 2. Firestore Optimization

```python
# src/optimization/firestore_optimizer.py
class FirestoreOptimizer:
    """Optimize Firestore operations."""

    def __init__(self):
        self.client = firestore.Client()
        self.batch_size = 500  # Firestore batch limit
        self.cache = TTLCache(maxsize=1000, ttl=300)  # 5 min cache

    def optimize_batch_writes(self, documents):
        """Optimize multiple document writes."""
        total_documents = len(documents)
        batches_needed = (total_documents + self.batch_size - 1) // self.batch_size

        write_times = []

        for i in range(batches_needed):
            batch_start = time.time()
            batch = self.client.batch()

            start_idx = i * self.batch_size
            end_idx = min((i + 1) * self.batch_size, total_documents)

            for doc in documents[start_idx:end_idx]:
                ref = self.client.collection(doc['collection']).document(doc['id'])
                batch.set(ref, doc['data'])

            batch.commit()
            write_times.append(time.time() - batch_start)

        return {
            "total_documents": total_documents,
            "batches": batches_needed,
            "avg_batch_time": np.mean(write_times),
            "total_time": sum(write_times)
        }

    def optimize_read_patterns(self, collection_name, filters):
        """Optimize Firestore read patterns."""
        # Check cache first
        cache_key = f"{collection_name}:{json.dumps(filters, sort_keys=True)}"
        cached_result = self.cache.get(cache_key)

        if cached_result:
            return {
                "source": "cache",
                "documents": cached_result,
                "read_time_ms": 0
            }

        # Optimize query
        read_start = time.time()
        query = self.client.collection(collection_name)

        # Apply filters efficiently
        for field, value in filters.items():
            query = query.where(field, '==', value)

        # Limit results
        query = query.limit(100)

        # Execute query
        documents = list(query.stream())
        read_time = (time.time() - read_start) * 1000

        # Cache results
        self.cache[cache_key] = documents

        return {
            "source": "firestore",
            "documents": documents,
            "read_time_ms": read_time
        }
```

## Memory Profiling

### 1. Memory Usage Tracking

```python
# src/profiling/memory_profiler.py
import tracemalloc
import psutil
import gc

class MemoryProfiler:
    """Profile memory usage of agents."""

    def __init__(self):
        self.snapshots = []
        self.process = psutil.Process()
        tracemalloc.start()

    def take_snapshot(self, label):
        """Take memory snapshot."""
        gc.collect()  # Force garbage collection

        snapshot = tracemalloc.take_snapshot()
        memory_info = self.process.memory_info()

        self.snapshots.append({
            "label": label,
            "timestamp": datetime.utcnow(),
            "snapshot": snapshot,
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024
        })

    def analyze_memory_growth(self):
        """Analyze memory growth between snapshots."""
        if len(self.snapshots) < 2:
            return "Need at least 2 snapshots"

        first = self.snapshots[0]
        last = self.snapshots[-1]

        # Compare snapshots
        top_stats = last["snapshot"].compare_to(first["snapshot"], 'lineno')

        print(f"\nMemory Growth Analysis")
        print(f"From: {first['label']} to {last['label']}")
        print(f"RSS Growth: {last['rss_mb'] - first['rss_mb']:.2f} MB")
        print(f"Time: {last['timestamp'] - first['timestamp']}")
        print("\nTop 10 memory allocations:")

        for stat in top_stats[:10]:
            print(f"{stat}")

    def find_memory_leaks(self):
        """Identify potential memory leaks."""
        if len(self.snapshots) < 3:
            return "Need at least 3 snapshots"

        # Look for consistent growth
        rss_values = [s["rss_mb"] for s in self.snapshots]

        # Simple leak detection: consistent growth
        differences = [rss_values[i+1] - rss_values[i] for i in range(len(rss_values)-1)]

        if all(d > 0 for d in differences):
            avg_growth = sum(differences) / len(differences)
            print(f"⚠️  Potential memory leak detected!")
            print(f"Average growth: {avg_growth:.2f} MB per snapshot")

            # Find biggest contributors
            last_snapshot = self.snapshots[-1]["snapshot"]
            stats = last_snapshot.statistics('lineno')

            print("\nTop memory consumers:")
            for stat in sorted(stats, key=lambda x: x.size, reverse=True)[:10]:
                print(f"{stat.filename}:{stat.lineno}: {stat.size / 1024 / 1024:.2f} MB")
```

### 2. Memory-Efficient Data Structures

```python
# src/optimization/memory_optimization.py
from collections import deque
import numpy as np

class MemoryOptimizedBuffer:
    """Memory-efficient circular buffer for event storage."""

    def __init__(self, max_size=10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.stats = {
            "total_added": 0,
            "total_evicted": 0,
            "current_size": 0
        }

    def add(self, item):
        """Add item to buffer."""
        if len(self.buffer) == self.max_size:
            self.stats["total_evicted"] += 1

        self.buffer.append(item)
        self.stats["total_added"] += 1
        self.stats["current_size"] = len(self.buffer)

    def get_memory_usage(self):
        """Estimate memory usage."""
        if not self.buffer:
            return 0

        # Sample first item to estimate size
        sample_size = sys.getsizeof(self.buffer[0])
        estimated_total = sample_size * len(self.buffer)

        return {
            "items": len(self.buffer),
            "estimated_bytes": estimated_total,
            "estimated_mb": estimated_total / 1024 / 1024,
            "stats": self.stats
        }

class CompressedIncidentStore:
    """Compress incidents in memory to save space."""

    def __init__(self):
        self.compressed_data = {}
        self.compression_stats = {
            "original_size": 0,
            "compressed_size": 0,
            "compression_ratio": 0
        }

    def store_incident(self, incident_id, incident_data):
        """Store incident with compression."""
        import zlib
        import pickle

        # Serialize
        serialized = pickle.dumps(incident_data)
        original_size = len(serialized)

        # Compress
        compressed = zlib.compress(serialized, level=6)
        compressed_size = len(compressed)

        self.compressed_data[incident_id] = compressed

        # Update stats
        self.compression_stats["original_size"] += original_size
        self.compression_stats["compressed_size"] += compressed_size
        self.compression_stats["compression_ratio"] = (
            1 - (self.compression_stats["compressed_size"] /
                 self.compression_stats["original_size"])
        ) * 100

    def get_incident(self, incident_id):
        """Retrieve and decompress incident."""
        import zlib
        import pickle

        if incident_id not in self.compressed_data:
            return None

        compressed = self.compressed_data[incident_id]
        decompressed = zlib.decompress(compressed)
        return pickle.loads(decompressed)
```

## Cost Optimization

### 1. API Cost Tracker

```python
# src/optimization/cost_tracker.py
class CostTracker:
    """Track and optimize API costs."""

    # Cost per operation (example rates)
    COSTS = {
        "gemini_prompt_token": 0.00025 / 1000,  # per token
        "gemini_completion_token": 0.0005 / 1000,  # per token
        "bigquery_query_tb": 5.00,  # per TB
        "firestore_read": 0.06 / 100000,  # per document
        "firestore_write": 0.18 / 100000,  # per document
        "cloud_run_cpu_second": 0.00002400,  # per vCPU-second
        "cloud_run_memory_gb_second": 0.00000250  # per GB-second
    }

    def __init__(self):
        self.usage = defaultdict(int)
        self.costs = defaultdict(float)

    def track_gemini_usage(self, prompt_tokens, completion_tokens):
        """Track Gemini API usage."""
        self.usage["gemini_prompt_tokens"] += prompt_tokens
        self.usage["gemini_completion_tokens"] += completion_tokens

        prompt_cost = prompt_tokens * self.COSTS["gemini_prompt_token"]
        completion_cost = completion_tokens * self.COSTS["gemini_completion_token"]

        self.costs["gemini"] += (prompt_cost + completion_cost)

        return prompt_cost + completion_cost

    def track_bigquery_usage(self, bytes_processed):
        """Track BigQuery usage."""
        tb_processed = bytes_processed / 1e12
        self.usage["bigquery_tb"] += tb_processed

        cost = tb_processed * self.COSTS["bigquery_query_tb"]
        self.costs["bigquery"] += cost

        return cost

    def generate_cost_report(self, period_hours=24):
        """Generate cost report."""
        total_cost = sum(self.costs.values())

        report = {
            "period_hours": period_hours,
            "total_cost_usd": total_cost,
            "daily_rate_usd": (total_cost / period_hours) * 24,
            "monthly_projection_usd": (total_cost / period_hours) * 24 * 30,
            "breakdown": dict(self.costs),
            "usage": dict(self.usage),
            "optimization_suggestions": self._generate_suggestions()
        }

        return report

    def _generate_suggestions(self):
        """Generate cost optimization suggestions."""
        suggestions = []

        # Gemini optimization
        if self.usage["gemini_prompt_tokens"] > 1000000:
            suggestions.append({
                "service": "Gemini",
                "suggestion": "Implement prompt caching to reduce token usage",
                "potential_savings": self.costs["gemini"] * 0.3
            })

        # BigQuery optimization
        if self.usage["bigquery_tb"] > 1:
            suggestions.append({
                "service": "BigQuery",
                "suggestion": "Use partitioned tables and clustered columns",
                "potential_savings": self.costs["bigquery"] * 0.5
            })

        return suggestions
```

### 2. Resource Usage Optimizer

```python
# src/optimization/resource_optimizer.py
class ResourceOptimizer:
    """Optimize Cloud Run resource usage."""

    def __init__(self):
        self.metrics_client = monitoring.MetricServiceClient()
        self.project_name = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT')}"

    def analyze_resource_usage(self, service_name, hours=24):
        """Analyze Cloud Run service resource usage."""
        interval = monitoring.TimeInterval(
            {
                "end_time": datetime.utcnow(),
                "start_time": datetime.utcnow() - timedelta(hours=hours)
            }
        )

        # Get CPU usage
        cpu_usage = self._get_metric(
            service_name,
            "run.googleapis.com/container/cpu/utilizations",
            interval
        )

        # Get memory usage
        memory_usage = self._get_metric(
            service_name,
            "run.googleapis.com/container/memory/utilizations",
            interval
        )

        # Get request count
        request_count = self._get_metric(
            service_name,
            "run.googleapis.com/request_count",
            interval
        )

        # Analyze and recommend
        recommendations = []

        # CPU recommendations
        avg_cpu = np.mean([p.value.double_value for p in cpu_usage])
        if avg_cpu < 0.3:  # 30% utilization
            recommendations.append({
                "resource": "CPU",
                "current": "1.0 vCPU",
                "recommended": "0.5 vCPU",
                "reason": f"Average CPU usage is {avg_cpu*100:.1f}%",
                "monthly_savings": 15.00  # Example
            })

        # Memory recommendations
        avg_memory = np.mean([p.value.double_value for p in memory_usage])
        if avg_memory < 0.5:  # 50% utilization
            current_memory = 2048  # MB
            recommended_memory = 1024  # MB
            recommendations.append({
                "resource": "Memory",
                "current": f"{current_memory}MB",
                "recommended": f"{recommended_memory}MB",
                "reason": f"Average memory usage is {avg_memory*100:.1f}%",
                "monthly_savings": 8.00  # Example
            })

        return {
            "service": service_name,
            "period_hours": hours,
            "metrics": {
                "avg_cpu_utilization": avg_cpu,
                "avg_memory_utilization": avg_memory,
                "total_requests": sum([p.value.int64_value for p in request_count])
            },
            "recommendations": recommendations,
            "total_monthly_savings": sum(r["monthly_savings"] for r in recommendations)
        }
```

## Performance Monitoring

### 1. Real-time Performance Dashboard

```python
# src/monitoring/performance_dashboard.py
from flask import Flask, render_template, jsonify
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, generate_latest

class PerformanceDashboard:
    """Real-time performance monitoring dashboard."""

    def __init__(self):
        self.app = Flask(__name__)

        # Define metrics
        self.agent_latency = Histogram(
            'agent_latency_seconds',
            'Agent processing latency',
            ['agent_name', 'operation'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        )

        self.tool_execution_time = Histogram(
            'tool_execution_seconds',
            'Tool execution time',
            ['agent_name', 'tool_name']
        )

        self.active_incidents = Gauge(
            'active_incidents',
            'Number of active incidents',
            ['severity']
        )

        self.api_calls = Counter(
            'api_calls_total',
            'Total API calls',
            ['service', 'method', 'status']
        )

        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('performance_dashboard.html')

        @self.app.route('/metrics')
        def metrics():
            return generate_latest()

        @self.app.route('/api/performance/summary')
        def performance_summary():
            return jsonify({
                "agents": self._get_agent_performance(),
                "tools": self._get_tool_performance(),
                "incidents": self._get_incident_metrics(),
                "costs": self._get_cost_metrics()
            })

    def _get_agent_performance(self):
        """Get agent performance metrics."""
        # This would query Prometheus or internal metrics
        return {
            "detection_agent": {
                "avg_latency_ms": 45.2,
                "p95_latency_ms": 120.5,
                "throughput_eps": 1250.0,
                "error_rate": 0.001
            },
            "analysis_agent": {
                "avg_latency_ms": 890.5,
                "p95_latency_ms": 2100.0,
                "cache_hit_rate": 0.65,
                "llm_calls_per_minute": 45
            }
        }
```

### 2. Performance Alerts

```python
# src/monitoring/performance_alerts.py
class PerformanceAlertManager:
    """Manage performance-based alerts."""

    def __init__(self):
        self.thresholds = {
            "agent_latency_p95": 5000,  # 5 seconds
            "memory_usage_percent": 80,
            "cpu_usage_percent": 70,
            "error_rate_percent": 1,
            "cost_per_hour_usd": 10
        }

        self.alert_history = deque(maxlen=1000)

    def check_performance_thresholds(self, metrics):
        """Check if any performance thresholds are exceeded."""
        alerts = []

        # Check agent latency
        if metrics.get("agent_latency_p95_ms", 0) > self.thresholds["agent_latency_p95"]:
            alerts.append({
                "severity": "WARNING",
                "type": "high_latency",
                "message": f"Agent latency P95 is {metrics['agent_latency_p95_ms']}ms",
                "threshold": self.thresholds["agent_latency_p95"],
                "value": metrics["agent_latency_p95_ms"]
            })

        # Check memory usage
        if metrics.get("memory_usage_percent", 0) > self.thresholds["memory_usage_percent"]:
            alerts.append({
                "severity": "CRITICAL",
                "type": "high_memory",
                "message": f"Memory usage is {metrics['memory_usage_percent']}%",
                "threshold": self.thresholds["memory_usage_percent"],
                "value": metrics["memory_usage_percent"],
                "action": "Consider scaling up or optimizing memory usage"
            })

        # Check costs
        if metrics.get("cost_per_hour_usd", 0) > self.thresholds["cost_per_hour_usd"]:
            alerts.append({
                "severity": "WARNING",
                "type": "high_cost",
                "message": f"Hourly cost is ${metrics['cost_per_hour_usd']:.2f}",
                "threshold": self.thresholds["cost_per_hour_usd"],
                "value": metrics["cost_per_hour_usd"],
                "action": "Review API usage and optimization opportunities"
            })

        # Record alerts
        for alert in alerts:
            alert["timestamp"] = datetime.utcnow()
            self.alert_history.append(alert)

        return alerts
```

## Optimization Strategies

### 1. Caching Strategy

```python
# src/optimization/caching_strategy.py
from functools import lru_cache
import hashlib
import redis

class OptimizedCache:
    """Multi-level caching strategy."""

    def __init__(self):
        # L1: In-memory LRU cache
        self.memory_cache = {}
        self.memory_cache_size = 1000

        # L2: Redis cache
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )

        # L3: Firestore cache for persistence
        self.firestore_client = firestore.Client()

        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0
        }

    async def get(self, key):
        """Get value with multi-level cache lookup."""
        # L1: Memory cache
        if key in self.memory_cache:
            self.stats["l1_hits"] += 1
            return self.memory_cache[key]

        # L2: Redis cache
        redis_value = self.redis_client.get(key)
        if redis_value:
            self.stats["l2_hits"] += 1
            # Promote to L1
            self.memory_cache[key] = redis_value
            return redis_value

        # L3: Firestore cache
        doc_ref = self.firestore_client.collection('cache').document(key)
        doc = doc_ref.get()

        if doc.exists:
            self.stats["l3_hits"] += 1
            value = doc.to_dict()['value']
            # Promote to L1 and L2
            self.memory_cache[key] = value
            self.redis_client.setex(key, 3600, value)  # 1 hour TTL
            return value

        self.stats["misses"] += 1
        return None

    def get_cache_performance(self):
        """Get cache performance metrics."""
        total_requests = sum(self.stats.values())

        if total_requests == 0:
            return {"hit_rate": 0, "stats": self.stats}

        hit_rate = 1 - (self.stats["misses"] / total_requests)

        return {
            "hit_rate": hit_rate,
            "stats": self.stats,
            "recommendations": self._generate_cache_recommendations()
        }

    def _generate_cache_recommendations(self):
        """Generate caching recommendations."""
        recommendations = []

        total_hits = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]

        if total_hits > 0:
            l1_ratio = self.stats["l1_hits"] / total_hits

            if l1_ratio < 0.7:
                recommendations.append(
                    "Consider increasing memory cache size for better L1 hit rate"
                )

        if self.stats["misses"] > total_hits:
            recommendations.append(
                "High miss rate detected. Consider caching more data types"
            )

        return recommendations
```

### 2. Batch Processing Optimization

```python
# src/optimization/batch_processor.py
class OptimizedBatchProcessor:
    """Optimize batch processing for efficiency."""

    def __init__(self):
        self.batch_queue = asyncio.Queue()
        self.processing = False
        self.batch_size = 100
        self.batch_timeout = 5.0  # seconds

    async def add_item(self, item):
        """Add item to batch queue."""
        await self.batch_queue.put(item)

        if not self.processing:
            asyncio.create_task(self._process_batches())

    async def _process_batches(self):
        """Process items in batches."""
        self.processing = True

        while True:
            batch = []
            deadline = asyncio.get_event_loop().time() + self.batch_timeout

            # Collect batch
            while len(batch) < self.batch_size:
                timeout = deadline - asyncio.get_event_loop().time()

                if timeout <= 0:
                    break

                try:
                    item = await asyncio.wait_for(
                        self.batch_queue.get(),
                        timeout=timeout
                    )
                    batch.append(item)
                except asyncio.TimeoutError:
                    break

            if batch:
                await self._process_batch(batch)
            else:
                # No items for a while, stop processing
                self.processing = False
                break

    async def _process_batch(self, batch):
        """Process a batch of items efficiently."""
        start_time = time.time()

        # Group by type for efficient processing
        grouped = defaultdict(list)
        for item in batch:
            grouped[item.get('type', 'unknown')].append(item)

        # Process each group in parallel
        tasks = []
        for item_type, items in grouped.items():
            if item_type == 'log_entry':
                tasks.append(self._process_log_batch(items))
            elif item_type == 'metric':
                tasks.append(self._process_metric_batch(items))
            elif item_type == 'incident':
                tasks.append(self._process_incident_batch(items))

        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time

        # Record performance metrics
        items_per_second = len(batch) / duration

        print(f"Processed batch of {len(batch)} items in {duration:.2f}s "
              f"({items_per_second:.1f} items/s)")
```

### 3. Query Optimization Patterns

```python
# src/optimization/query_patterns.py
class QueryOptimizationPatterns:
    """Common query optimization patterns."""

    @staticmethod
    def optimize_time_range_query(table, start_time, end_time):
        """Optimize time-range queries."""
        # Use partitioning
        query = f"""
        SELECT *
        FROM `{table}`
        WHERE _PARTITIONDATE BETWEEN DATE('{start_time}') AND DATE('{end_time}')
          AND timestamp BETWEEN '{start_time}' AND '{end_time}'
        """

        return query

    @staticmethod
    def optimize_aggregation_query(table, group_by_field, time_bucket):
        """Optimize aggregation queries."""
        query = f"""
        SELECT
          TIMESTAMP_TRUNC(timestamp, {time_bucket}) as time_bucket,
          {group_by_field},
          COUNT(*) as count,
          APPROX_QUANTILES(response_time, 100)[OFFSET(95)] as p95_latency
        FROM `{table}`
        WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        GROUP BY time_bucket, {group_by_field}
        ORDER BY time_bucket DESC
        """

        return query

    @staticmethod
    def create_materialized_view(source_table, view_name):
        """Create materialized view for performance."""
        query = f"""
        CREATE MATERIALIZED VIEW `{view_name}`
        PARTITION BY DATE(timestamp)
        CLUSTER BY severity, resource_type
        AS
        SELECT
          timestamp,
          severity,
          resource_type,
          COUNT(*) OVER (
            PARTITION BY severity
            ORDER BY timestamp
            ROWS BETWEEN 3600 PRECEDING AND CURRENT ROW
          ) as events_last_hour
        FROM `{source_table}`
        WHERE _PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        """

        return query
```

---

*This comprehensive performance profiling guide provides the tools and techniques needed to optimize SentinelOps for maximum efficiency and minimum cost.*
