variable "project_id" {
  type = string
}

variable "environment" {
  type = string
}

variable "labels" {
  type = map(string)
}

variable "database_instance_name" {
  type = string
}

variable "primary_region" {
  type = string
}

variable "backup_regions" {
  type    = list(string)
  default = ["us-east1", "europe-west1", "asia-east1"]
}

# Backup buckets in multiple regions
resource "google_storage_bucket" "backups" {
  for_each = toset(var.backup_regions)
  
  name          = "${var.project_id}-sentinelops-backups-${each.value}-${var.environment}"
  location      = each.value
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = var.environment == "prod" ? 90 : 30
      matches_storage_class = ["STANDARD"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  lifecycle_rule {
    condition {
      age = var.environment == "prod" ? 365 : 90
      matches_storage_class = ["NEARLINE"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
  
  lifecycle_rule {
    condition {
      age = var.environment == "prod" ? 2555 : 180  # 7 years for prod
    }
    action {
      type = "Delete"
    }
  }
  
  labels = var.labels
}

# Cross-region replication for critical data
resource "google_storage_bucket" "critical_backups" {
  name          = "${var.project_id}-sentinelops-critical-${var.environment}"
  location      = "US"  # Multi-region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = var.environment == "prod" ? 2555 : 365  # 7 years for prod
    }
    action {
      type = "Delete"
    }
  }
  
  retention_policy {
    retention_period = var.environment == "prod" ? 2592000 : 604800  # 30 days for prod, 7 days for others
    is_locked        = var.environment == "prod" ? true : false
  }
  
  labels = var.labels
}

# Database backup configuration
resource "google_sql_database_instance" "backup_replica" {
  count = var.environment == "prod" ? length(var.backup_regions) : 0
  
  name             = "${var.database_instance_name}-backup-${var.backup_regions[count.index]}"
  database_version = "POSTGRES_15"
  region           = var.backup_regions[count.index]
  
  master_instance_name = var.database_instance_name
  
  replica_configuration {
    failover_target = false
  }
  
  settings {
    tier = "db-custom-2-8192"
    
    backup_configuration {
      enabled    = false  # Backups handled by primary
      binary_log_enabled = false
    }
    
    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
    
    user_labels = var.labels
  }
}

# Scheduled backup Cloud Function
resource "google_cloudfunctions_function" "backup_scheduler" {
  name        = "sentinelops-backup-scheduler-${var.environment}"
  runtime     = "python311"
  region      = var.primary_region
  
  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.function_source.name
  source_archive_object = google_storage_bucket_object.backup_function.name
  
  entry_point = "backup_handler"
  
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.backup_trigger.name
  }
  
  environment_variables = {
    PROJECT_ID     = var.project_id
    ENVIRONMENT    = var.environment
    BACKUP_REGIONS = join(",", var.backup_regions)
  }
  
  labels = var.labels
}

# Backup trigger schedule
resource "google_cloud_scheduler_job" "backup_schedule" {
  name             = "sentinelops-backup-schedule-${var.environment}"
  description      = "Trigger backups for SentinelOps"
  schedule         = var.environment == "prod" ? "0 2,14 * * *" : "0 2 * * *"  # Twice daily for prod
  time_zone        = "UTC"
  attempt_deadline = "320s"
  region           = var.primary_region
  
  pubsub_target {
    topic_name = google_pubsub_topic.backup_trigger.id
    data       = base64encode(jsonencode({
      backup_type = "scheduled"
      timestamp   = timestamp()
    }))
  }
}

# Pub/Sub topic for backup triggers
resource "google_pubsub_topic" "backup_trigger" {
  name = "sentinelops-backup-trigger-${var.environment}"
  
  labels = var.labels
}

# Storage for Cloud Function source
resource "google_storage_bucket" "function_source" {
  name          = "${var.project_id}-sentinelops-functions-${var.environment}"
  location      = var.primary_region
  force_destroy = true
  
  uniform_bucket_level_access = true
  
  labels = var.labels
}

# Upload backup function code
resource "google_storage_bucket_object" "backup_function" {
  name   = "backup-function-${filemd5("${path.module}/backup_function.zip")}.zip"
  bucket = google_storage_bucket.function_source.name
  source = "${path.module}/backup_function.zip"
}

# Disaster Recovery documentation
resource "google_storage_bucket_object" "dr_runbook" {
  name   = "disaster-recovery/runbook.md"
  bucket = google_storage_bucket.critical_backups.name
  content = templatefile("${path.module}/dr_runbook.tpl", {
    project_id     = var.project_id
    environment    = var.environment
    backup_regions = var.backup_regions
  })
}

# Backup monitoring
resource "google_monitoring_alert_policy" "backup_failure" {
  display_name = "Backup Failure Alert - ${var.environment}"
  combiner     = "OR"
  
  conditions {
    display_name = "Backup function errors"
    
    condition_threshold {
      filter     = "resource.type=\"cloud_function\" AND resource.labels.function_name=\"sentinelops-backup-scheduler-${var.environment}\" AND metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" AND metric.labels.status!=\"ok\""
      duration   = "300s"
      comparison = "COMPARISON_GT"
      
      threshold_value = 0
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }
  
  documentation {
    content = "Backup function has failed. Check Cloud Function logs for details.\n\nRunbook: ${google_storage_bucket_object.dr_runbook.self_link}"
  }
}

output "backup_bucket_names" {
  value = {
    for region, bucket in google_storage_bucket.backups : region => bucket.name
  }
}

output "critical_backup_bucket" {
  value = google_storage_bucket.critical_backups.name
}

output "backup_function_name" {
  value = google_cloudfunctions_function.backup_scheduler.name
}