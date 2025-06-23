variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "network_id" {
  type = string
}

variable "environment" {
  type = string
}

variable "labels" {
  type = map(string)
}

resource "google_sql_database_instance" "main" {
  name             = "sentinelops-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.environment == "prod" ? "db-custom-4-16384" : "db-custom-2-8192"
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "prod"
      transaction_log_retention_days = var.environment == "prod" ? 7 : 1
      retained_backups               = var.environment == "prod" ? 30 : 7
    }
    
    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
    }
    
    maintenance_window {
      day          = 7
      hour         = 4
      update_track = "stable"
    }
    
    user_labels = var.labels
  }
  
  deletion_protection = var.environment == "prod"
}

resource "google_sql_database" "app" {
  name     = "sentinelops"
  instance = google_sql_database_instance.main.name
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = "sentinelops_analytics_${var.environment}"
  friendly_name               = "SentinelOps Analytics ${var.environment}"
  description                 = "Analytics data for SentinelOps"
  location                    = "US"
  default_table_expiration_ms = var.environment == "prod" ? null : 7776000000
  
  labels = var.labels
}

output "database_connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "bigquery_dataset_id" {
  value = google_bigquery_dataset.analytics.dataset_id
}