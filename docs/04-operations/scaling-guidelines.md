# SentinelOps Scaling Guidelines

This document provides comprehensive guidelines for scaling the SentinelOps platform to handle increased load, optimize performance, and maintain cost efficiency.

## Table of Contents

1. [Scaling Principles](#scaling-principles)
2. [Capacity Planning](#capacity-planning)
3. [Horizontal Scaling](#horizontal-scaling)
4. [Vertical Scaling](#vertical-scaling)
5. [Auto-scaling Configuration](#auto-scaling-configuration)
6. [Database Scaling](#database-scaling)
7. [Message Queue Scaling](#message-queue-scaling)
8. [Geographic Scaling](#geographic-scaling)
9. [Cost-Optimized Scaling](#cost-optimized-scaling)
10. [Monitoring and Metrics](#monitoring-and-metrics)

## Scaling Principles

### Key Principles

1. **Scale Horizontally First**: Add more instances before increasing instance size
2. **Data Locality**: Keep compute close to data to minimize latency
3. **Stateless Design**: Ensure services can scale without state management issues
4. **Gradual Scaling**: Scale incrementally and monitor impact
5. **Cost Awareness**: Balance performance needs with budget constraints

### Scaling Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU Utilization | > 70% sustained | Add instances |
| Memory Usage | > 85% | Increase memory or add instances |
| Request Latency p95 | > 1s | Scale out |
| Error Rate | > 1% | Investigate, then scale |
| Queue Depth | > 1000 messages | Add consumers |

## Capacity Planning

### Current Capacity Baseline

```python
#!/usr/bin/env python3
# analyze_current_capacity.py

from google.cloud import monitoring_v3
from datetime import datetime, timedelta
import pandas as pd

def analyze_service_capacity(service_name):
    """Analyze current capacity and utilization."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    # Define metrics to analyze
    metrics = {
        'cpu': 'run.googleapis.com/container/cpu/utilizations',
        'memory': 'run.googleapis.com/container/memory/utilizations',
        'requests': 'run.googleapis.com/request_count',
        'latency': 'run.googleapis.com/request_latencies'
    }

    interval = monitoring_v3.TimeInterval({
        "end_time": {"seconds": int(datetime.now().timestamp())},
        "start_time": {"seconds": int((datetime.now() - timedelta(days=7)).timestamp())}
    })

    capacity_analysis = {}

    for metric_name, metric_type in metrics.items():
        filter_str = f'metric.type="{metric_type}" AND resource.labels.service_name="{service_name}"'

        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": filter_str,
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL
            }
        )

        values = []
        for result in results:
            for point in result.points:
                values.append(point.value.double_value or point.value.int64_value)

        if values:
            capacity_analysis[metric_name] = {
                'current_avg': sum(values) / len(values),
                'peak': max(values),
                'headroom': 1.0 - (max(values) / 100) if metric_name in ['cpu', 'memory'] else None
            }

    return capacity_analysis

# Analyze all services
for service in ['detection-agent', 'analysis-agent', 'communication-agent', 'orchestration-agent']:
    print(f"\n{service} Capacity Analysis:")
    analysis = analyze_service_capacity(service)
    for metric, data in analysis.items():
        print(f"  {metric}: avg={data['current_avg']:.2f}, peak={data['peak']:.2f}")
        if data['headroom']:
            print(f"    Headroom: {data['headroom']*100:.1f}%")
```

### Growth Projection

```python
#!/usr/bin/env python3
# project_growth.py

import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

def project_growth(historical_data, days_ahead=90):
    """Project future growth based on historical trends."""

    # Prepare data for regression
    X = np.array(range(len(historical_data))).reshape(-1, 1)
    y = np.array(historical_data)

    # Fit linear regression
    model = LinearRegression()
    model.fit(X, y)

    # Project future
    future_X = np.array(range(len(historical_data), len(historical_data) + days_ahead)).reshape(-1, 1)
    future_y = model.predict(future_X)

    # Calculate growth rate
    daily_growth_rate = model.coef_[0]
    monthly_growth_rate = daily_growth_rate * 30

    return {
        'daily_growth': daily_growth_rate,
        'monthly_growth': monthly_growth_rate,
        'projected_value_30d': future_y[29],
        'projected_value_90d': future_y[89],
        'current_value': historical_data[-1]
    }

# Example: Project request volume growth
historical_requests = [1000, 1100, 1150, 1200, 1300, 1400, 1500]  # Daily averages
projection = project_growth(historical_requests)

print("Request Volume Projection:")
print(f"  Current: {projection['current_value']:.0f} req/day")
print(f"  30-day projection: {projection['projected_value_30d']:.0f} req/day")
print(f"  90-day projection: {projection['projected_value_90d']:.0f} req/day")
print(f"  Monthly growth: {projection['monthly_growth']:.1f} req/day")
```

### Capacity Planning Matrix

| Service | Current RPS | 30-Day Target | 90-Day Target | Required Instances |
|---------|-------------|---------------|---------------|-------------------|
| Detection Agent | 100 | 150 | 225 | 5 → 8 → 12 |
| Analysis Agent | 50 | 75 | 112 | 3 → 5 → 7 |
| Communication Agent | 200 | 300 | 450 | 4 → 6 → 9 |
| Orchestration Agent | 150 | 225 | 337 | 5 → 8 → 11 |

## Horizontal Scaling

### Cloud Run Auto-scaling

```yaml
# cloud-run-scaling-config.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: detection-agent
  annotations:
    run.googleapis.com/execution-environment: gen2
spec:
  template:
    metadata:
      annotations:
        # Scaling annotations
        autoscaling.knative.dev/minScale: "2"
        autoscaling.knative.dev/maxScale: "100"
        autoscaling.knative.dev/target: "80"
        autoscaling.knative.dev/targetUtilizationPercentage: "70"
        # Startup optimization
        run.googleapis.com/startup-cpu-boost: "true"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 1000
      timeoutSeconds: 300
      serviceAccountName: detection-agent-sa
      containers:
      - image: gcr.io/PROJECT_ID/detection-agent:latest
        resources:
          limits:
            cpu: "2"
            memory: "2Gi"
        env:
        - name: WORKERS
          value: "4"  # Multi-threading within instance
```

### Implementing Horizontal Scaling

```bash
#!/bin/bash
# scale_horizontally.sh

SERVICE=$1
TARGET_INSTANCES=$2

if [ -z "$SERVICE" ] || [ -z "$TARGET_INSTANCES" ]; then
  echo "Usage: $0 SERVICE_NAME TARGET_INSTANCES"
  exit 1
fi

echo "Scaling $SERVICE to $TARGET_INSTANCES instances"

# Update auto-scaling configuration
gcloud run services update $SERVICE \
  --min-instances=$((TARGET_INSTANCES / 2)) \
  --max-instances=$((TARGET_INSTANCES * 2)) \
  --region=us-central1

# Update concurrency for optimal distribution
CONCURRENCY=$((1000 / TARGET_INSTANCES))
gcloud run services update $SERVICE \
  --concurrency=$CONCURRENCY \
  --region=us-central1

# Verify scaling
echo "Waiting for scaling to complete..."
sleep 30

ACTUAL_INSTANCES=$(gcloud run services describe $SERVICE \
  --region=us-central1 \
  --format="value(status.latestReadyRevisionName)" | \
  xargs -I {} gcloud run revisions describe {} \
  --region=us-central1 \
  --format="value(status.containerStatuses[0].name)" | wc -l)

echo "Scaled to $ACTUAL_INSTANCES instances"
```

### Load Distribution Strategy

```python
#!/usr/bin/env python3
# configure_load_balancing.py

from google.cloud import compute_v1
import math

def configure_load_distribution(service_name, expected_rps):
    """Configure load balancing for optimal distribution."""

    # Calculate optimal instance count
    rps_per_instance = 50  # Conservative estimate
    target_instances = math.ceil(expected_rps / rps_per_instance)

    # Configure backend service
    backend_service = compute_v1.BackendService()
    backend_service.name = f"{service_name}-backend"
    backend_service.load_balancing_scheme = "EXTERNAL_MANAGED"
    backend_service.protocol = "HTTPS"
    backend_service.session_affinity = "NONE"  # Stateless
    backend_service.connection_draining = compute_v1.ConnectionDraining(draining_timeout_sec=30)

    # Health check configuration
    backend_service.health_checks = [f"projects/{PROJECT_ID}/global/healthChecks/{service_name}-health"]

    # Circuit breaker configuration
    backend_service.circuit_breakers = compute_v1.CircuitBreakers(
        max_requests_per_connection=10,
        max_connections=target_instances * 100,
        max_pending_requests=target_instances * 50,
        max_requests=target_instances * 200,
        max_retries=3
    )

    # Outlier detection
    backend_service.outlier_detection = compute_v1.OutlierDetection(
        consecutive_errors=5,
        interval=compute_v1.Duration(seconds=30),
        base_ejection_time=compute_v1.Duration(seconds=30),
        max_ejection_percent=50,
        enforcing_consecutive_errors=100,
        enforcing_success_rate=95,
        success_rate_minimum_hosts=5,
        success_rate_request_volume=100
    )

    return backend_service

# Configure for each service
services_config = {
    'detection-agent': 200,
    'analysis-agent': 100,
    'communication-agent': 300,
    'orchestration-agent': 250
}

for service, expected_rps in services_config.items():
    backend = configure_load_distribution(service, expected_rps)
    print(f"Configured {service} for {expected_rps} RPS")
```

## Vertical Scaling

### Resource Optimization Analysis

```python
#!/usr/bin/env python3
# analyze_vertical_scaling_needs.py

from google.cloud import monitoring_v3
import statistics

def analyze_resource_requirements(service_name):
    """Analyze if vertical scaling is needed."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    # Get CPU and memory metrics
    metrics = {}
    for metric_type in ['cpu/utilizations', 'memory/utilizations']:
        filter_str = f'metric.type="run.googleapis.com/container/{metric_type}" AND resource.labels.service_name="{service_name}"'

        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": filter_str,
                "interval": monitoring_v3.TimeInterval({
                    "end_time": {"seconds": int(datetime.now().timestamp())},
                    "start_time": {"seconds": int((datetime.now() - timedelta(hours=24)).timestamp())}
                }),
                "aggregation": monitoring_v3.Aggregation({
                    "alignment_period": {"seconds": 300},
                    "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN
                })
            }
        )

        values = []
        for result in results:
            for point in result.points:
                values.append(point.value.double_value * 100)

        if values:
            metrics[metric_type] = {
                'p50': statistics.median(values),
                'p95': statistics.quantiles(values, n=20)[18],  # 95th percentile
                'p99': statistics.quantiles(values, n=100)[98],  # 99th percentile
                'max': max(values)
            }

    # Make recommendations
    recommendations = []

    # CPU analysis
    if 'cpu/utilizations' in metrics:
        cpu_p95 = metrics['cpu/utilizations']['p95']
        if cpu_p95 > 80:
            recommendations.append({
                'type': 'increase_cpu',
                'reason': f'CPU P95 is {cpu_p95:.1f}%',
                'suggestion': 'Double CPU allocation'
            })
        elif cpu_p95 < 30:
            recommendations.append({
                'type': 'decrease_cpu',
                'reason': f'CPU P95 is only {cpu_p95:.1f}%',
                'suggestion': 'Halve CPU allocation'
            })

    # Memory analysis
    if 'memory/utilizations' in metrics:
        mem_p95 = metrics['memory/utilizations']['p95']
        if mem_p95 > 85:
            recommendations.append({
                'type': 'increase_memory',
                'reason': f'Memory P95 is {mem_p95:.1f}%',
                'suggestion': 'Increase memory by 50%'
            })

    return metrics, recommendations

# Analyze all services
for service in ['detection-agent', 'analysis-agent', 'communication-agent', 'orchestration-agent']:
    print(f"\n{service} Resource Analysis:")
    metrics, recommendations = analyze_resource_requirements(service)

    for metric_type, values in metrics.items():
        print(f"  {metric_type}:")
        print(f"    P50: {values['p50']:.1f}%, P95: {values['p95']:.1f}%, P99: {values['p99']:.1f}%")

    if recommendations:
        print("  Recommendations:")
        for rec in recommendations:
            print(f"    - {rec['suggestion']} ({rec['reason']})")
```

### Vertical Scaling Implementation

```bash
#!/bin/bash
# scale_vertically.sh

SERVICE=$1
CPU=$2
MEMORY=$3

if [ -z "$SERVICE" ] || [ -z "$CPU" ] || [ -z "$MEMORY" ]; then
  echo "Usage: $0 SERVICE_NAME CPU MEMORY"
  echo "Example: $0 detection-agent 4 4Gi"
  exit 1
fi

echo "Vertically scaling $SERVICE to CPU=$CPU, Memory=$MEMORY"

# Store current configuration
CURRENT_CPU=$(gcloud run services describe $SERVICE --region=us-central1 \
  --format="value(spec.template.spec.containers[0].resources.limits.cpu)")
CURRENT_MEM=$(gcloud run services describe $SERVICE --region=us-central1 \
  --format="value(spec.template.spec.containers[0].resources.limits.memory)")

echo "Current: CPU=$CURRENT_CPU, Memory=$CURRENT_MEM"

# Update resources
gcloud run services update $SERVICE \
  --cpu=$CPU \
  --memory=$MEMORY \
  --region=us-central1 \
  --tag=scaled-$(date +%Y%m%d-%H%M%S)

# Gradual traffic migration
echo "Migrating traffic gradually..."
for percent in 10 25 50 75 100; do
  gcloud run services update-traffic $SERVICE \
    --to-latest=$percent \
    --region=us-central1

  echo "Traffic at $percent%, monitoring for 2 minutes..."
  sleep 120

  # Check error rate
  ERROR_COUNT=$(gcloud logging read \
    "resource.labels.service_name=\"$SERVICE\" AND severity=\"ERROR\"" \
    --freshness=2m --format="value(timestamp)" | wc -l)

  if [ $ERROR_COUNT -gt 10 ]; then
    echo "High error rate detected, rolling back..."
    gcloud run services update-traffic $SERVICE \
      --to-revisions=${SERVICE}-$(date +%Y%m%d)=100 \
      --region=us-central1
    exit 1
  fi
done

echo "Vertical scaling completed successfully"
```

## Auto-scaling Configuration

### Advanced Auto-scaling Rules

```yaml
# autoscaling-policy.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: detection-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: serving.knative.dev/v1
    kind: Service
    name: detection-agent
  minReplicas: 2
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: custom_request_latency
      target:
        type: AverageValue
        averageValue: "500m"  # 500ms
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 5
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 10
        periodSeconds: 30
      selectPolicy: Max
```

### Custom Metrics for Auto-scaling

```python
#!/usr/bin/env python3
# setup_custom_metrics.py

from google.cloud import monitoring_v3
import time

def create_custom_metric(metric_name, metric_kind="GAUGE", value_type="DOUBLE"):
    """Create custom metric for auto-scaling."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    descriptor = monitoring_v3.MetricDescriptor()
    descriptor.type = f"custom.googleapis.com/{metric_name}"
    descriptor.metric_kind = monitoring_v3.MetricDescriptor.MetricKind[metric_kind]
    descriptor.value_type = monitoring_v3.MetricDescriptor.ValueType[value_type]
    descriptor.description = f"Custom metric for {metric_name}"

    # Add labels
    labels = monitoring_v3.LabelDescriptor()
    labels.key = "service_name"
    labels.value_type = monitoring_v3.LabelDescriptor.ValueType.STRING
    descriptor.labels.append(labels)

    descriptor = client.create_metric_descriptor(
        name=project_name,
        metric_descriptor=descriptor
    )

    print(f"Created metric: {descriptor.name}")
    return descriptor

def report_custom_metric(metric_name, value, service_name):
    """Report custom metric value."""
    client = monitoring_v3.MetricServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    series = monitoring_v3.TimeSeries()
    series.metric.type = f"custom.googleapis.com/{metric_name}"
    series.metric.labels["service_name"] = service_name
    series.resource.type = "global"
    series.resource.labels["project_id"] = PROJECT_ID

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)

    point = monitoring_v3.Point()
    point.interval.end_time.seconds = seconds
    point.interval.end_time.nanos = nanos
    point.value.double_value = value

    series.points = [point]

    client.create_time_series(name=project_name, time_series=[series])

# Create custom metrics
create_custom_metric("queue_depth", "GAUGE", "INT64")
create_custom_metric("processing_backlog", "GAUGE", "INT64")
create_custom_metric("business_transactions_per_second", "GAUGE", "DOUBLE")

# Example: Report queue depth for auto-scaling decisions
report_custom_metric("queue_depth", 150, "detection-agent")
```

### Predictive Auto-scaling

```python
#!/usr/bin/env python3
# predictive_autoscaling.py

from google.cloud import aiplatform
from google.cloud import monitoring_v3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PredictiveAutoscaler:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        aiplatform.init(project=project_id, location=location)
        self.monitoring_client = monitoring_v3.MetricServiceClient()

    def collect_historical_data(self, service_name, days=30):
        """Collect historical metrics for training."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        # Collect various metrics
        metrics_to_collect = [
            'run.googleapis.com/request_count',
            'run.googleapis.com/container/cpu/utilizations',
            'run.googleapis.com/container/memory/utilizations'
        ]

        data = []

        for metric_type in metrics_to_collect:
            filter_str = f'metric.type="{metric_type}" AND resource.labels.service_name="{service_name}"'

            interval = monitoring_v3.TimeInterval({
                "end_time": {"seconds": int(end_time.timestamp())},
                "start_time": {"seconds": int(start_time.timestamp())}
            })

            results = self.monitoring_client.list_time_series(
                request={
                    "name": f"projects/{self.project_id}",
                    "filter": filter_str,
                    "interval": interval,
                    "aggregation": monitoring_v3.Aggregation({
                        "alignment_period": {"seconds": 3600},  # 1 hour
                        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN
                    })
                }
            )

            for result in results:
                for point in result.points:
                    timestamp = point.interval.end_time
                    value = point.value.double_value or point.value.int64_value

                    data.append({
                        'timestamp': timestamp,
                        'metric': metric_type.split('/')[-1],
                        'value': value,
                        'hour': timestamp.hour,
                        'day_of_week': timestamp.weekday(),
                        'is_weekend': timestamp.weekday() >= 5
                    })

        return pd.DataFrame(data)

    def train_prediction_model(self, training_data):
        """Train model to predict future load."""
        # Prepare features
        features = ['hour', 'day_of_week', 'is_weekend']
        X = training_data[features]
        y = training_data['value']

        # Train using Vertex AI AutoML
        dataset = aiplatform.TabularDataset.create(
            display_name=f"autoscaling_data_{datetime.now().strftime('%Y%m%d')}",
            dataframe=training_data
        )

        job = aiplatform.AutoMLTabularTrainingJob(
            display_name="autoscaling_prediction_model",
            optimization_prediction_type="regression"
        )

        model = job.run(
            dataset=dataset,
            target_column="value",
            training_fraction_split=0.8,
            validation_fraction_split=0.1,
            test_fraction_split=0.1,
            model_display_name="autoscaling_model"
        )

        return model

    def predict_future_load(self, model, hours_ahead=24):
        """Predict load for the next N hours."""
        future_times = []
        now = datetime.now()

        for i in range(hours_ahead):
            future_time = now + timedelta(hours=i)
            future_times.append({
                'hour': future_time.hour,
                'day_of_week': future_time.weekday(),
                'is_weekend': future_time.weekday() >= 5
            })

        predictions_df = pd.DataFrame(future_times)
        predictions = model.predict(predictions_df)

        return list(zip(future_times, predictions.predictions))

    def calculate_required_instances(self, predicted_load, instance_capacity=50):
        """Calculate required instances based on predicted load."""
        scaling_plan = []

        for time_data, load in predicted_load:
            required_instances = max(2, int(np.ceil(load / instance_capacity)))

            # Add buffer for peak times
            if time_data['hour'] in range(9, 17) and not time_data['is_weekend']:
                required_instances = int(required_instances * 1.2)

            scaling_plan.append({
                'hour': time_data['hour'],
                'predicted_load': load,
                'required_instances': required_instances
            })

        return scaling_plan

    def apply_scaling_plan(self, service_name, scaling_plan):
        """Apply the scaling plan using Cloud Scheduler."""
        # Create scheduled scaling jobs
        for plan in scaling_plan:
            schedule = f"0 {plan['hour']} * * *"
            job_name = f"scale-{service_name}-{plan['hour']}h"

            command = f"""
            gcloud run services update {service_name} \
              --min-instances={max(2, plan['required_instances'] - 2)} \
              --max-instances={plan['required_instances'] + 5} \
              --region={self.location}
            """

            # Create Cloud Scheduler job
            print(f"Creating scheduled job: {job_name}")
            print(f"  Schedule: {schedule}")
            print(f"  Instances: {plan['required_instances']}")

# Usage
autoscaler = PredictiveAutoscaler(PROJECT_ID)

# Collect data and train model
for service in ['detection-agent', 'analysis-agent']:
    print(f"Setting up predictive scaling for {service}")

    # Collect historical data
    data = autoscaler.collect_historical_data(service)

    # Train prediction model
    model = autoscaler.train_prediction_model(data)

    # Predict future load
    predictions = autoscaler.predict_future_load(model)

    # Calculate scaling plan
    scaling_plan = autoscaler.calculate_required_instances(predictions)

    # Apply scaling plan
    autoscaler.apply_scaling_plan(service, scaling_plan)
```

## Database Scaling

### BigQuery Optimization

```sql
-- Optimize table partitioning and clustering
CREATE OR REPLACE TABLE sentinelops_logs.audit_logs_optimized
PARTITION BY DATE(timestamp)
CLUSTER BY severity, event_type, resource_type
AS
SELECT * FROM sentinelops_logs.audit_logs;

-- Create materialized views for common queries
CREATE MATERIALIZED VIEW sentinelops_logs.hourly_event_summary
PARTITION BY event_date
CLUSTER BY event_type, severity
AS
SELECT
  DATE(timestamp) as event_date,
  EXTRACT(HOUR FROM timestamp) as hour,
  event_type,
  severity,
  COUNT(*) as event_count,
  AVG(processing_time_ms) as avg_processing_time
FROM sentinelops_logs.audit_logs
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY event_date, hour, event_type, severity;

-- Implement table sharding for high-volume data
CREATE OR REPLACE TABLE sentinelops_logs.audit_logs_shard_template
PARTITION BY DATE(timestamp)
CLUSTER BY severity, event_type
AS
SELECT * FROM sentinelops_logs.audit_logs
WHERE FALSE;  -- Empty template

-- Create sharded tables
DECLARE shard_date DATE DEFAULT CURRENT_DATE();
DECLARE table_name STRING;

WHILE shard_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) DO
  SET table_name = CONCAT('audit_logs_', FORMAT_DATE('%Y%m%d', shard_date));

  EXECUTE IMMEDIATE FORMAT("""
    CREATE OR REPLACE TABLE sentinelops_logs.%s
    PARTITION BY DATE(timestamp)
    CLUSTER BY severity, event_type
    AS
    SELECT * FROM sentinelops_logs.audit_logs
    WHERE DATE(timestamp) = '%t'
  """, table_name, shard_date);

  SET shard_date = DATE_SUB(shard_date, INTERVAL 1 DAY);
END WHILE;
```

### Firestore Scaling

```python
#!/usr/bin/env python3
# scale_firestore.py

from google.cloud import firestore
from concurrent.futures import ThreadPoolExecutor
import hashlib

class FirestoreScaler:
    def __init__(self, project_id):
        self.db = firestore.Client(project=project_id)

    def implement_sharding(self, collection_name, num_shards=10):
        """Implement collection sharding for better write throughput."""

        def get_shard_id(document_id):
            """Determine shard based on document ID."""
            hash_value = hashlib.md5(document_id.encode()).hexdigest()
            return int(hash_value[:8], 16) % num_shards

        # Create shard collections
        for i in range(num_shards):
            shard_name = f"{collection_name}_shard_{i}"
            # Initialize shard with metadata
            self.db.collection(shard_name).document('_metadata').set({
                'shard_id': i,
                'created_at': firestore.SERVER_TIMESTAMP,
                'parent_collection': collection_name
            })

        return get_shard_id

    def parallel_write(self, collection_name, documents, num_workers=10):
        """Write documents in parallel for better throughput."""

        def write_batch(batch_docs):
            batch = self.db.batch()
            for doc_id, doc_data in batch_docs:
                ref = self.db.collection(collection_name).document(doc_id)
                batch.set(ref, doc_data)
            batch.commit()

        # Split documents into batches
        batch_size = 500  # Firestore limit
        batches = []
        current_batch = []

        for doc in documents:
            current_batch.append(doc)
            if len(current_batch) >= batch_size:
                batches.append(current_batch)
                current_batch = []

        if current_batch:
            batches.append(current_batch)

        # Write batches in parallel
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(write_batch, batch) for batch in batches]
            for future in futures:
                future.result()

    def implement_caching_layer(self, collection_name, cache_ttl=300):
        """Implement caching to reduce read load."""
        import redis

        # Connect to Redis (Memorystore)
        redis_client = redis.Redis(
            host='10.0.0.3',  # Internal IP of Memorystore instance
            port=6379,
            decode_responses=True
        )

        def cached_read(document_id):
            # Check cache first
            cache_key = f"{collection_name}:{document_id}"
            cached_data = redis_client.get(cache_key)

            if cached_data:
                return json.loads(cached_data)

            # Read from Firestore
            doc = self.db.collection(collection_name).document(document_id).get()

            if doc.exists:
                data = doc.to_dict()
                # Cache the result
                redis_client.setex(
                    cache_key,
                    cache_ttl,
                    json.dumps(data, default=str)
                )
                return data

            return None

        return cached_read

    def optimize_queries(self, collection_name):
        """Optimize common query patterns."""

        # Create composite indexes
        indexes = [
            {
                'fields': [
                    {'field_path': 'severity', 'order': 'DESCENDING'},
                    {'field_path': 'timestamp', 'order': 'DESCENDING'}
                ]
            },
            {
                'fields': [
                    {'field_path': 'status', 'order': 'ASCENDING'},
                    {'field_path': 'priority', 'order': 'DESCENDING'},
                    {'field_path': 'created_at', 'order': 'DESCENDING'}
                ]
            }
        ]

        # Apply indexes (would be done via Firebase console or CLI)
        print(f"Recommended indexes for {collection_name}:")
        for idx in indexes:
            print(f"  Fields: {[f['field_path'] for f in idx['fields']]}")

# Usage
scaler = FirestoreScaler(PROJECT_ID)

# Implement sharding for high-write collections
shard_func = scaler.implement_sharding('incidents', num_shards=20)

# Example: Write with sharding
def write_incident(incident_id, incident_data):
    shard_id = shard_func(incident_id)
    collection_name = f"incidents_shard_{shard_id}"

    db = firestore.Client()
    db.collection(collection_name).document(incident_id).set(incident_data)
```

## Message Queue Scaling

### Pub/Sub Optimization

```python
#!/usr/bin/env python3
# scale_pubsub.py

from google.cloud import pubsub_v1
from concurrent.futures import ThreadPoolExecutor
import json

class PubSubScaler:
    def __init__(self, project_id):
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()

    def configure_high_throughput_publishing(self, topic_name):
        """Configure publisher for high throughput."""

        # Batch settings for optimal throughput
        batch_settings = pubsub_v1.types.BatchSettings(
            max_bytes=1024 * 1024 * 10,  # 10MB
            max_latency=0.1,  # 100ms
            max_messages=1000,  # Maximum messages per batch
        )

        # Flow control settings
        flow_control = pubsub_v1.types.PublishFlowControl(
            message_limit=10000,
            byte_limit=1024 * 1024 * 100,  # 100MB
            limit_exceeded_behavior=pubsub_v1.types.LimitExceededBehavior.BLOCK,
        )

        # Create publisher with settings
        publisher = pubsub_v1.PublisherClient(
            batch_settings=batch_settings,
            publisher_options=pubsub_v1.types.PublisherOptions(
                flow_control=flow_control
            )
        )

        return publisher

    def configure_parallel_subscription(self, subscription_name,
                                      max_workers=100,
                                      max_messages=1000):
        """Configure subscription for parallel processing."""

        subscription_path = self.subscriber.subscription_path(
            self.project_id, subscription_name
        )

        # Update subscription settings
        update_mask = {
            'paths': [
                'ack_deadline_seconds',
                'message_retention_duration',
                'enable_exactly_once_delivery',
                'retry_policy'
            ]
        }

        subscription = pubsub_v1.types.Subscription(
            name=subscription_path,
            ack_deadline_seconds=600,  # 10 minutes for processing
            message_retention_duration={'seconds': 604800},  # 7 days
            enable_exactly_once_delivery=True,
            retry_policy=pubsub_v1.types.RetryPolicy(
                minimum_backoff={'seconds': 10},
                maximum_backoff={'seconds': 600}
            )
        )

        self.subscriber.update_subscription(
            subscription=subscription,
            update_mask=update_mask
        )

        # Flow control for subscriber
        flow_control = pubsub_v1.types.FlowControl(
            max_messages=max_messages,
            max_bytes=1024 * 1024 * 100,  # 100MB
            max_lease_duration=3600,  # 1 hour
        )

        return flow_control

    def implement_message_deduplication(self, topic_name):
        """Implement message deduplication."""

        class DeduplicationPublisher:
            def __init__(self, publisher, topic_path, cache_ttl=3600):
                self.publisher = publisher
                self.topic_path = topic_path
                self.seen_messages = {}  # In production, use Redis
                self.cache_ttl = cache_ttl

            def publish(self, message_data, message_id=None):
                # Generate message ID if not provided
                if not message_id:
                    message_id = hashlib.sha256(
                        json.dumps(message_data, sort_keys=True).encode()
                    ).hexdigest()

                # Check if already published
                if message_id in self.seen_messages:
                    current_time = time.time()
                    if current_time - self.seen_messages[message_id] < self.cache_ttl:
                        print(f"Duplicate message skipped: {message_id}")
                        return None

                # Publish message
                future = self.publisher.publish(
                    self.topic_path,
                    json.dumps(message_data).encode(),
                    message_id=message_id
                )

                # Record publication
                self.seen_messages[message_id] = time.time()

                # Clean old entries
                current_time = time.time()
                self.seen_messages = {
                    k: v for k, v in self.seen_messages.items()
                    if current_time - v < self.cache_ttl
                }

                return future

        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        return DeduplicationPublisher(self.publisher, topic_path)

    def implement_priority_queue(self, base_topic_name):
        """Implement priority-based message processing."""

        # Create priority topics
        priority_levels = ['critical', 'high', 'medium', 'low']
        topics = {}

        for priority in priority_levels:
            topic_name = f"{base_topic_name}-{priority}"
            topic_path = self.publisher.topic_path(self.project_id, topic_name)

            # Create topic if not exists
            try:
                self.publisher.create_topic(request={"name": topic_path})
            except:
                pass  # Topic already exists

            topics[priority] = topic_path

        # Create subscriptions with different processing priorities
        for priority in priority_levels:
            subscription_name = f"{base_topic_name}-{priority}-sub"
            subscription_path = self.subscriber.subscription_path(
                self.project_id, subscription_name
            )

            # Configure based on priority
            if priority == 'critical':
                ack_deadline = 60  # 1 minute
                max_delivery_attempts = 10
            elif priority == 'high':
                ack_deadline = 300  # 5 minutes
                max_delivery_attempts = 5
            else:
                ack_deadline = 600  # 10 minutes
                max_delivery_attempts = 3

            try:
                self.subscriber.create_subscription(
                    request={
                        "name": subscription_path,
                        "topic": topics[priority],
                        "ack_deadline_seconds": ack_deadline,
                        "dead_letter_policy": {
                            "dead_letter_topic": f"projects/{self.project_id}/topics/dead-letter-{priority}",
                            "max_delivery_attempts": max_delivery_attempts
                        }
                    }
                )
            except:
                pass  # Subscription already exists

        return topics

# Usage
scaler = PubSubScaler(PROJECT_ID)

# Configure high-throughput publisher
publisher = scaler.configure_high_throughput_publishing('detection-topic')

# Configure parallel subscription processing
flow_control = scaler.configure_parallel_subscription(
    'detection-subscription',
    max_workers=50,
    max_messages=500
)

# Implement deduplication
dedup_publisher = scaler.implement_message_deduplication('analysis-topic')

# Implement priority queues
priority_topics = scaler.implement_priority_queue('remediation')
```

## Geographic Scaling

### Multi-Region Deployment

```bash
#!/bin/bash
# deploy_multi_region.sh

REGIONS=("us-central1" "us-east1" "europe-west1" "asia-southeast1")
SERVICES=("detection-agent" "analysis-agent" "communication-agent" "orchestration-agent")

for region in "${REGIONS[@]}"; do
  echo "Deploying to $region..."

  for service in "${SERVICES[@]}"; do
    echo "  Deploying $service..."

    # Deploy service to region
    gcloud run deploy $service-$region \
      --image gcr.io/${PROJECT_ID}/$service:latest \
      --region $region \
      --platform managed \
      --service-account $service-sa@${PROJECT_ID}.iam.gserviceaccount.com \
      --min-instances 1 \
      --max-instances 50 \
      --memory 2Gi \
      --cpu 2
  done

  # Set up regional Pub/Sub
  for topic in detection analysis remediation communication; do
    gcloud pubsub topics create $topic-topic-$region
    gcloud pubsub subscriptions create $topic-sub-$region \
      --topic $topic-topic-$region \
      --ack-deadline 600
  done
done

# Configure global load balancer
gcloud compute backend-services create sentinelops-global-backend \
  --global \
  --protocol HTTPS \
  --health-checks sentinelops-health-check

# Add regional backends
for region in "${REGIONS[@]}"; do
  gcloud compute backend-services add-backend sentinelops-global-backend \
    --global \
    --network-endpoint-group=sentinelops-neg-$region \
    --network-endpoint-group-region=$region
done
```

### Data Replication Strategy

```python
#!/usr/bin/env python3
# setup_data_replication.py

from google.cloud import firestore
from google.cloud import bigquery
import asyncio

class MultiRegionReplicator:
    def __init__(self, project_id, regions):
        self.project_id = project_id
        self.regions = regions
        self.firestore_clients = {
            region: firestore.Client(project=project_id, database=f"firestore-{region}")
            for region in regions
        }
        self.bq_client = bigquery.Client(project=project_id)

    async def replicate_firestore_document(self, collection, doc_id, doc_data):
        """Replicate document across regions."""
        tasks = []

        for region, client in self.firestore_clients.items():
            task = asyncio.create_task(
                self._write_document(client, collection, doc_id, doc_data)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def _write_document(self, client, collection, doc_id, doc_data):
        """Write document to specific region."""
        return client.collection(collection).document(doc_id).set(doc_data)

    def setup_bigquery_replication(self):
        """Set up cross-region BigQuery dataset replication."""

        for region in self.regions:
            dataset_id = f"sentinelops_{region.replace('-', '_')}"

            # Create regional dataset
            dataset = bigquery.Dataset(f"{self.project_id}.{dataset_id}")
            dataset.location = region
            dataset.description = f"SentinelOps dataset for {region}"

            try:
                dataset = self.bq_client.create_dataset(dataset, timeout=30)
                print(f"Created dataset {dataset_id} in {region}")
            except:
                print(f"Dataset {dataset_id} already exists")

            # Create materialized views for replication
            source_tables = ['audit_logs', 'vpc_flow_logs', 'firewall_logs']

            for table in source_tables:
                view_query = f"""
                CREATE MATERIALIZED VIEW `{self.project_id}.{dataset_id}.{table}`
                PARTITION BY DATE(timestamp)
                CLUSTER BY severity, event_type
                AS
                SELECT * FROM `{self.project_id}.sentinelops_logs.{table}`
                WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                """

                try:
                    self.bq_client.query(view_query).result()
                    print(f"Created materialized view for {table} in {region}")
                except:
                    print(f"View {table} already exists in {region}")

    def implement_eventual_consistency(self):
        """Implement eventual consistency across regions."""

        class ConsistencyManager:
            def __init__(self, regions):
                self.regions = regions
                self.version_vectors = {}  # Track versions across regions

            def write_with_consistency(self, key, value, region):
                # Generate version vector
                version = self.version_vectors.get(key, {})
                version[region] = version.get(region, 0) + 1

                # Write with version
                write_data = {
                    'value': value,
                    'version': version,
                    'timestamp': datetime.utcnow(),
                    'region': region
                }

                # Propagate to other regions asynchronously
                for target_region in self.regions:
                    if target_region != region:
                        # Queue replication task
                        self._queue_replication(key, write_data, target_region)

                self.version_vectors[key] = version
                return version

            def _queue_replication(self, key, data, target_region):
                # In production, use Pub/Sub for async replication
                print(f"Queuing replication of {key} to {target_region}")

        return ConsistencyManager(self.regions)

# Usage
regions = ["us-central1", "us-east1", "europe-west1", "asia-southeast1"]
replicator = MultiRegionReplicator(PROJECT_ID, regions)

# Set up BigQuery replication
replicator.setup_bigquery_replication()

# Example: Replicate critical data
async def replicate_incident(incident_id, incident_data):
    results = await replicator.replicate_firestore_document(
        'incidents', incident_id, incident_data
    )
    print(f"Replicated to {len(results)} regions")

# Run replication
asyncio.run(replicate_incident('INC-12345', {'severity': 'HIGH', 'status': 'active'}))
```

## Cost-Optimized Scaling

### Preemptible Instance Strategy

```python
#!/usr/bin/env python3
# preemptible_scaling.py

from google.cloud import compute_v1
import time

class PreemptibleScaler:
    def __init__(self, project_id, zone):
        self.project_id = project_id
        self.zone = zone
        self.compute_client = compute_v1.InstancesClient()

    def create_preemptible_pool(self, base_name, count, machine_type="e2-medium"):
        """Create a pool of preemptible instances."""

        instances = []

        for i in range(count):
            instance_name = f"{base_name}-preempt-{i}"

            instance = compute_v1.Instance()
            instance.name = instance_name
            instance.machine_type = f"zones/{self.zone}/machineTypes/{machine_type}"

            # Configure as preemptible
            instance.scheduling = compute_v1.Scheduling()
            instance.scheduling.preemptible = True
            instance.scheduling.automatic_restart = False
            instance.scheduling.on_host_maintenance = "TERMINATE"

            # Add startup script to rejoin pool on restart
            instance.metadata = compute_v1.Metadata()
            instance.metadata.items = [
                compute_v1.Items(
                    key="startup-script",
                    value="""
                    #!/bin/bash
                    # Register with orchestrator
                    curl -X POST https://orchestrator.sentinelops.com/register \
                      -H "Content-Type: application/json" \
                      -d '{"instance": "'$(hostname)'", "type": "preemptible"}'

                    # Start worker process
                    docker run --rm \
                      -e INSTANCE_TYPE=preemptible \
                      gcr.io/${PROJECT_ID}/worker:latest
                    """
                )
            ]

            # Network configuration
            network_interface = compute_v1.NetworkInterface()
            network_interface.network = f"projects/{self.project_id}/global/networks/sentinelops-vpc"
            network_interface.subnetwork = f"projects/{self.project_id}/regions/{self.zone[:-2]}/subnetworks/sentinelops-subnet"

            instance.network_interfaces = [network_interface]

            # Boot disk
            boot_disk = compute_v1.AttachedDisk()
            boot_disk.auto_delete = True
            boot_disk.boot = True
            boot_disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
            boot_disk.initialize_params.source_image = "projects/cos-cloud/global/images/cos-stable-latest"
            boot_disk.initialize_params.disk_size_gb = 10

            instance.disks = [boot_disk]

            # Create instance
            operation = self.compute_client.insert(
                project=self.project_id,
                zone=self.zone,
                instance_resource=instance
            )

            instances.append(instance_name)
            print(f"Created preemptible instance: {instance_name}")

        return instances

    def implement_spot_bidding_strategy(self):
        """Implement strategy for Spot/Preemptible instances."""

        def calculate_bid_price(current_price, urgency_factor=1.0):
            """Calculate optimal bid price based on urgency."""
            # Base bid is 20% above current price
            base_bid = current_price * 1.2

            # Adjust based on urgency
            adjusted_bid = base_bid * urgency_factor

            # Cap at 80% of on-demand price
            max_bid = current_price * 2.0 * 0.8

            return min(adjusted_bid, max_bid)

        def distribute_workload(total_instances_needed):
            """Distribute between on-demand and preemptible."""
            # Always keep 20% as on-demand for stability
            on_demand_count = max(2, int(total_instances_needed * 0.2))
            preemptible_count = total_instances_needed - on_demand_count

            return {
                'on_demand': on_demand_count,
                'preemptible': preemptible_count,
                'cost_savings': preemptible_count * 0.7  # 70% savings
            }

        return calculate_bid_price, distribute_workload

# Usage
scaler = PreemptibleScaler(PROJECT_ID, "us-central1-a")

# Create preemptible pool for batch processing
batch_instances = scaler.create_preemptible_pool(
    "batch-processor",
    count=10,
    machine_type="n1-standard-4"
)

# Implement bidding strategy
bid_calculator, workload_distributor = scaler.implement_spot_bidding_strategy()

# Example: Scale based on workload
total_needed = 20
distribution = workload_distributor(total_needed)
print(f"Scaling strategy: {distribution}")
```

### Resource Scheduling for Cost Optimization

```python
#!/usr/bin/env python3
# cost_aware_scaling.py

from datetime import datetime, time
import pytz

class CostAwareScaler:
    def __init__(self, project_id):
        self.project_id = project_id
        self.timezone = pytz.timezone('US/Pacific')

        # Define cost periods
        self.cost_periods = {
            'peak': {'start': time(9, 0), 'end': time(17, 0), 'multiplier': 1.0},
            'off_peak': {'start': time(17, 0), 'end': time(9, 0), 'multiplier': 0.7},
            'weekend': {'multiplier': 0.5}
        }

    def get_current_cost_period(self):
        """Determine current cost period."""
        now = datetime.now(self.timezone)

        # Check if weekend
        if now.weekday() >= 5:
            return 'weekend'

        # Check time of day
        current_time = now.time()
        if self.cost_periods['peak']['start'] <= current_time < self.cost_periods['peak']['end']:
            return 'peak'
        else:
            return 'off_peak'

    def calculate_optimal_scaling(self, base_instances, load_factor):
        """Calculate optimal instance count based on cost period."""
        period = self.get_current_cost_period()
        cost_multiplier = self.cost_periods[period]['multiplier']

        # Adjust scaling based on cost period
        if period == 'peak':
            # Full scaling during peak
            target_instances = int(base_instances * load_factor)
        elif period == 'off_peak':
            # Moderate scaling during off-peak
            target_instances = int(base_instances * load_factor * 0.8)
        else:  # weekend
            # Minimal scaling on weekends
            target_instances = int(base_instances * load_factor * 0.5)

        # Ensure minimum instances
        target_instances = max(2, target_instances)

        return {
            'period': period,
            'target_instances': target_instances,
            'cost_multiplier': cost_multiplier,
            'estimated_cost': target_instances * cost_multiplier * 0.05  # $0.05/hour/instance
        }

    def implement_scheduled_scaling(self):
        """Create scheduled scaling rules."""

        scaling_schedule = [
            # Weekday scale-up
            {
                'name': 'weekday-morning-scaleup',
                'schedule': '0 8 * * 1-5',
                'action': 'scale_to_peak'
            },
            # Weekday scale-down
            {
                'name': 'weekday-evening-scaledown',
                'schedule': '0 18 * * 1-5',
                'action': 'scale_to_minimum'
            },
            # Weekend scale-down
            {
                'name': 'weekend-scaledown',
                'schedule': '0 0 * * 6',
                'action': 'scale_to_weekend'
            },
            # Monday scale-up
            {
                'name': 'monday-scaleup',
                'schedule': '0 6 * * 1',
                'action': 'scale_to_normal'
            }
        ]

        return scaling_schedule

# Usage
cost_scaler = CostAwareScaler(PROJECT_ID)

# Get optimal scaling for current period
current_load = 1.5  # 150% of baseline
optimal = cost_scaler.calculate_optimal_scaling(base_instances=10, load_factor=current_load)
print(f"Optimal scaling: {optimal}")

# Implement scheduled scaling
schedule = cost_scaler.implement_scheduled_scaling()
for rule in schedule:
    print(f"Schedule: {rule['name']} at {rule['schedule']} - {rule['action']}")
```

## Monitoring and Metrics

### Scaling Metrics Dashboard

```python
#!/usr/bin/env python3
# create_scaling_dashboard.py

from google.cloud import monitoring_dashboard_v1

def create_scaling_dashboard(project_id):
    """Create comprehensive scaling metrics dashboard."""

    client = monitoring_dashboard_v1.DashboardsServiceClient()
    project_name = f"projects/{project_id}"

    dashboard = monitoring_dashboard_v1.Dashboard()
    dashboard.display_name = "SentinelOps Scaling Metrics"
    dashboard.mosaicLayout = monitoring_dashboard_v1.MosaicLayout()

    # Define tiles for different metrics
    tiles = []

    # Instance count tile
    instance_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
    instance_tile.widget = monitoring_dashboard_v1.Widget()
    instance_tile.widget.title = "Instance Count by Service"
    instance_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()
    instance_tile.widget.xyChart.dataSets.append(
        monitoring_dashboard_v1.XyChart.DataSet(
            timeSeriesQuery=monitoring_dashboard_v1.XyChart.TimeSeriesQuery(
                timeSeriesFilter=monitoring_dashboard_v1.XyChart.TimeSeriesFilter(
                    filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/instance_count"',
                    aggregation=monitoring_dashboard_v1.Aggregation(
                        alignmentPeriod={"seconds": 60},
                        perSeriesAligner="ALIGN_MEAN",
                        groupByFields=["resource.label.service_name"]
                    )
                )
            )
        )
    )
    instance_tile.width = 6
    instance_tile.height = 4
    tiles.append(instance_tile)

    # CPU utilization tile
    cpu_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
    cpu_tile.widget = monitoring_dashboard_v1.Widget()
    cpu_tile.widget.title = "CPU Utilization"
    cpu_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()
    cpu_tile.widget.xyChart.dataSets.append(
        monitoring_dashboard_v1.XyChart.DataSet(
            timeSeriesQuery=monitoring_dashboard_v1.XyChart.TimeSeriesQuery(
                timeSeriesFilter=monitoring_dashboard_v1.XyChart.TimeSeriesFilter(
                    filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/container/cpu/utilizations"',
                    aggregation=monitoring_dashboard_v1.Aggregation(
                        alignmentPeriod={"seconds": 60},
                        perSeriesAligner="ALIGN_MEAN",
                        groupByFields=["resource.label.service_name"]
                    )
                )
            )
        )
    )
    cpu_tile.xPos = 6
    cpu_tile.width = 6
    cpu_tile.height = 4
    tiles.append(cpu_tile)

    # Request rate tile
    request_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
    request_tile.widget = monitoring_dashboard_v1.Widget()
    request_tile.widget.title = "Request Rate"
    request_tile.widget.xyChart = monitoring_dashboard_v1.XyChart()
    request_tile.widget.xyChart.dataSets.append(
        monitoring_dashboard_v1.XyChart.DataSet(
            timeSeriesQuery=monitoring_dashboard_v1.XyChart.TimeSeriesQuery(
                timeSeriesFilter=monitoring_dashboard_v1.XyChart.TimeSeriesFilter(
                    filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count"',
                    aggregation=monitoring_dashboard_v1.Aggregation(
                        alignmentPeriod={"seconds": 60},
                        perSeriesAligner="ALIGN_RATE",
                        groupByFields=["resource.label.service_name"]
                    )
                )
            )
        )
    )
    request_tile.yPos = 4
    request_tile.width = 6
    request_tile.height = 4
    tiles.append(request_tile)

    # Cost projection tile
    cost_tile = monitoring_dashboard_v1.MosaicLayout.Tile()
    cost_tile.widget = monitoring_dashboard_v1.Widget()
    cost_tile.widget.title = "Estimated Hourly Cost"
    cost_tile.widget.scorecard = monitoring_dashboard_v1.Scorecard()
    cost_tile.widget.scorecard.timeSeriesQuery = monitoring_dashboard_v1.TimeSeriesQuery(
        timeSeriesFilter=monitoring_dashboard_v1.TimeSeriesFilter(
            filter='metric.type="custom.googleapis.com/cost/hourly_estimate"',
            aggregation=monitoring_dashboard_v1.Aggregation(
                alignmentPeriod={"seconds": 3600},
                perSeriesAligner="ALIGN_MEAN"
            )
        )
    )
    cost_tile.xPos = 6
    cost_tile.yPos = 4
    cost_tile.width = 6
    cost_tile.height = 4
    tiles.append(cost_tile)

    dashboard.mosaicLayout.tiles.extend(tiles)

    # Create dashboard
    created_dashboard = client.create_dashboard(
        parent=project_name,
        dashboard=dashboard
    )

    print(f"Created dashboard: {created_dashboard.name}")
    return created_dashboard

# Create the dashboard
create_scaling_dashboard(PROJECT_ID)
```

### Scaling Alerts

```yaml
# scaling-alerts.yaml
---
displayName: "High Instance Count Alert"
conditions:
  - displayName: "Instance count exceeds threshold"
    conditionThreshold:
      filter: |
        resource.type="cloud_run_revision"
        AND metric.type="run.googleapis.com/container/instance_count"
      comparison: COMPARISON_GT
      thresholdValue: 50
      duration: 300s
      aggregations:
        - alignmentPeriod: 60s
          perSeriesAligner: ALIGN_MAX
          groupByFields:
            - resource.label.service_name
notificationChannels:
  - projects/[PROJECT_ID]/notificationChannels/[CHANNEL_ID]
documentation:
  content: |
    Service has scaled beyond expected threshold.
    Check for traffic spike or potential DDoS attack.
---
displayName: "Scaling Failure Alert"
conditions:
  - displayName: "Unable to scale - quota exceeded"
    conditionThreshold:
      filter: |
        resource.type="cloud_run_revision"
        AND metric.type="run.googleapis.com/container/instance_count"
        AND metric.label.state="pending"
      comparison: COMPARISON_GT
      thresholdValue: 0
      duration: 180s
notificationChannels:
  - projects/[PROJECT_ID]/notificationChannels/[CHANNEL_ID]
documentation:
  content: |
    Service unable to scale due to quota limits.
    Increase quotas or implement load shedding.
```

## Best Practices Summary

### Scaling Checklist

- [ ] **Capacity Planning**
  - [ ] Analyze historical growth trends
  - [ ] Project future capacity needs
  - [ ] Plan for seasonal variations

- [ ] **Horizontal Scaling**
  - [ ] Configure auto-scaling policies
  - [ ] Implement load balancing
  - [ ] Test scaling behavior under load

- [ ] **Vertical Scaling**
  - [ ] Monitor resource utilization
  - [ ] Right-size instances regularly
  - [ ] Use profiling to identify bottlenecks

- [ ] **Cost Optimization**
  - [ ] Use preemptible instances for batch work
  - [ ] Implement time-based scaling
  - [ ] Monitor and optimize costs continuously

- [ ] **Geographic Distribution**
  - [ ] Deploy to multiple regions
  - [ ] Implement data replication
  - [ ] Configure global load balancing

- [ ] **Monitoring**
  - [ ] Create scaling dashboards
  - [ ] Set up proactive alerts
  - [ ] Track scaling metrics and costs

### Scaling Anti-Patterns to Avoid

1. **Over-provisioning**: Don't scale for peak 24/7
2. **Under-monitoring**: Always track scaling events
3. **Ignoring costs**: Balance performance with budget
4. **Manual scaling**: Automate wherever possible
5. **Single region**: Plan for geographic distribution
