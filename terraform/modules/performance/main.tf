variable "project_id" {
  type = string
}

variable "environment" {
  type = string
}

variable "labels" {
  type = map(string)
}

# Redis instance for caching
resource "google_redis_instance" "cache" {
  name               = "sentinelops-cache-${var.environment}"
  memory_size_gb     = var.environment == "prod" ? 5 : 1
  region             = var.region
  location_id        = var.zone
  
  redis_version     = "REDIS_7_0"
  display_name      = "SentinelOps Cache ${var.environment}"
  
  tier = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
    notify-keyspace-events = "Ex"
  }
  
  auth_enabled = true
  transit_encryption_mode = "SERVER_AUTHENTICATION"
  
  persistence_config {
    persistence_mode = var.environment == "prod" ? "RDB" : "DISABLED"
    rdb_snapshot_period = var.environment == "prod" ? "TWELVE_HOURS" : null
  }
  
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours = 4
        minutes = 0
      }
    }
  }
  
  labels = var.labels
}

# Autoscaling configuration for Cloud Run
resource "google_cloud_run_service" "optimized_api" {
  name     = "sentinelops-api-optimized-${var.environment}"
  location = var.region

  template {
    spec {
      container_concurrency = 1000
      timeout_seconds       = 300
      
      containers {
        image = "gcr.io/${var.project_id}/sentinelops-api:latest"
        
        resources {
          limits = {
            cpu    = var.environment == "prod" ? "4000m" : "2000m"
            memory = var.environment == "prod" ? "8Gi" : "4Gi"
          }
          requests = {
            cpu    = "1000m"
            memory = "2Gi"
          }
        }
        
        env {
          name  = "REDIS_HOST"
          value = google_redis_instance.cache.host
        }
        
        env {
          name  = "REDIS_PORT"
          value = google_redis_instance.cache.port
        }
        
        env {
          name = "REDIS_AUTH"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.redis_auth.secret_id
              key  = "latest"
            }
          }
        }
        
        startup_probe {
          initial_delay_seconds = 10
          timeout_seconds       = 3
          period_seconds        = 5
          failure_threshold     = 10
          tcp_socket {
            port = 8080
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"         = var.environment == "prod" ? "3" : "1"
        "autoscaling.knative.dev/maxScale"         = var.environment == "prod" ? "100" : "10"
        "autoscaling.knative.dev/target"           = "80"
        "autoscaling.knative.dev/targetBurstCapacity" = "200"
        "autoscaling.knative.dev/panicWindowPercentage" = "10.0"
        "autoscaling.knative.dev/panicThresholdPercentage" = "200.0"
        "run.googleapis.com/cpu-throttling"        = "false"
        "run.googleapis.com/startup-cpu-boost"     = "true"
      }
      
      labels = var.labels
    }
  }
}

# Cloud CDN configuration for static assets
resource "google_compute_backend_bucket" "static_assets" {
  name        = "sentinelops-static-assets-${var.environment}"
  bucket_name = google_storage_bucket.static_assets.name
  enable_cdn  = true
  
  cdn_policy {
    cache_mode = "CACHE_ALL_STATIC"
    default_ttl = 3600
    max_ttl     = 86400
    
    negative_caching = true
    negative_caching_policy {
      code = 404
      ttl  = 300
    }
    
    serve_while_stale = 86400
  }
}

resource "google_storage_bucket" "static_assets" {
  name          = "${var.project_id}-sentinelops-static-${var.environment}"
  location      = "US"
  force_destroy = true
  
  uniform_bucket_level_access = true
  
  cors {
    origin          = ["https://*.sentinelops.com"]
    method          = ["GET", "HEAD", "OPTIONS"]
    response_header = ["Content-Type", "Cache-Control"]
    max_age_seconds = 3600
  }
  
  labels = var.labels
}

# BigQuery optimization
resource "google_bigquery_table" "events_clustered" {
  dataset_id = var.bigquery_dataset_id
  table_id   = "events_optimized"
  
  time_partitioning {
    type  = "HOUR"
    field = "timestamp"
  }
  
  clustering = ["event_type", "severity", "source"]
  
  schema = jsonencode([
    {
      name = "event_id"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "timestamp"
      type = "TIMESTAMP"
      mode = "REQUIRED"
    },
    {
      name = "event_type"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "severity"
      type = "STRING"
      mode = "REQUIRED"
    },
    {
      name = "source"
      type = "STRING"
      mode = "NULLABLE"
    },
    {
      name = "data"
      type = "JSON"
      mode = "NULLABLE"
    }
  ])
  
  labels = var.labels
}

# Materialized view for common queries
resource "google_bigquery_table" "incident_summary_mv" {
  dataset_id = var.bigquery_dataset_id
  table_id   = "incident_summary_mv"
  
  materialized_view {
    query = <<-EOQ
      SELECT 
        DATE(timestamp) as date,
        severity,
        event_type,
        COUNT(*) as event_count,
        COUNT(DISTINCT event_id) as unique_events
      FROM `${var.project_id}.${var.bigquery_dataset_id}.events_optimized`
      WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
      GROUP BY date, severity, event_type
    EOQ
    
    enable_refresh = true
    refresh_interval_ms = 3600000  # 1 hour
  }
  
  labels = var.labels
}

# Dataflow for stream processing
resource "google_dataflow_job" "event_processor" {
  count = var.environment == "prod" ? 1 : 0
  
  name              = "sentinelops-event-processor-${var.environment}"
  template_gcs_path = "gs://dataflow-templates-${var.region}/latest/PubSub_to_BigQuery"
  temp_gcs_location = google_storage_bucket.dataflow_temp.url
  
  parameters = {
    inputTopic      = google_pubsub_topic.events.id
    outputTableSpec = "${var.project_id}:${var.bigquery_dataset_id}.events_optimized"
  }
  
  machine_type = "n1-standard-2"
  max_workers  = var.environment == "prod" ? 10 : 2
  
  on_delete = "cancel"
  
  labels = var.labels
}

resource "google_storage_bucket" "dataflow_temp" {
  name          = "${var.project_id}-sentinelops-dataflow-${var.environment}"
  location      = var.region
  force_destroy = true
  
  uniform_bucket_level_access = true
  
  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "Delete"
    }
  }
  
  labels = var.labels
}

resource "google_pubsub_topic" "events" {
  name = "sentinelops-events-${var.environment}"
  
  message_retention_duration = var.environment == "prod" ? "86400s" : "3600s"
  
  labels = var.labels
}

# Secret for Redis auth
resource "google_secret_manager_secret" "redis_auth" {
  secret_id = "sentinelops-redis-auth-${var.environment}"
  
  replication {
    automatic = true
  }
  
  labels = var.labels
}

resource "google_secret_manager_secret_version" "redis_auth" {
  secret = google_secret_manager_secret.redis_auth.id
  
  secret_data = google_redis_instance.cache.auth_string
}

# Cost optimization through committed use discounts
resource "google_compute_resource_policy" "committed_use" {
  count = var.environment == "prod" ? 1 : 0
  
  name   = "sentinelops-committed-use-${var.environment}"
  region = var.region
  
  instance_schedule_policy {
    vm_start_schedule {
      schedule = "0 6 * * MON-FRI"
    }
    vm_stop_schedule {
      schedule = "0 18 * * MON-FRI"
    }
    time_zone = "America/New_York"
  }
}

variable "region" {
  type = string
}

variable "zone" {
  type = string
}

variable "bigquery_dataset_id" {
  type = string
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "redis_port" {
  value = google_redis_instance.cache.port
}

output "static_assets_bucket" {
  value = google_storage_bucket.static_assets.name
}

output "events_topic" {
  value = google_pubsub_topic.events.id
}