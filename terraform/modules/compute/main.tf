variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "service_account_email" {
  type = string
}

variable "vpc_connector_id" {
  type = string
}

variable "environment" {
  type = string
}

variable "labels" {
  type = map(string)
}

resource "google_cloud_run_service" "api" {
  name     = "sentinelops-api-${var.environment}"
  location = var.region

  template {
    spec {
      service_account_name = var.service_account_email
      
      containers {
        image = "gcr.io/${var.project_id}/sentinelops-api:latest"
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
        
        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "run.googleapis.com/vpc-access-connector" = var.vpc_connector_id
        "run.googleapis.com/cpu-throttling"        = "false"
      }
      labels = var.labels
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}

resource "google_cloud_run_service_iam_member" "api_invoker" {
  service  = google_cloud_run_service.api.name
  location = google_cloud_run_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "api_url" {
  value = google_cloud_run_service.api.status[0].url
}