variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "environment" {
  type = string
}

variable "labels" {
  type = map(string)
}

resource "google_storage_bucket" "artifacts" {
  name          = "${var.project_id}-sentinelops-artifacts-${var.environment}"
  location      = var.region
  force_destroy = var.environment != "prod"
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = var.environment == "prod" ? 90 : 30
    }
    action {
      type = "Delete"
    }
  }
  
  labels = var.labels
}

resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-sentinelops-backups-${var.environment}"
  location      = var.region
  force_destroy = false
  
  uniform_bucket_level_access = true
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = var.environment == "prod" ? 365 : 30
    }
    action {
      type = "Delete"
    }
  }
  
  labels = var.labels
}

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "sentinelops-${var.environment}"
  description   = "Container images for SentinelOps"
  format        = "DOCKER"
  
  labels = var.labels
}

output "artifacts_bucket" {
  value = google_storage_bucket.artifacts.name
}

output "backups_bucket" {
  value = google_storage_bucket.backups.name
}

output "container_registry" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}"
}