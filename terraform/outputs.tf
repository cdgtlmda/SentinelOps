output "api_url" {
  description = "The URL of the deployed API"
  value       = module.compute.api_url
}

output "load_balancer_ip" {
  description = "The IP address of the load balancer"
  value       = module.load_balancer.load_balancer_ip
}

output "database_connection_name" {
  description = "The connection name for Cloud SQL"
  value       = module.database.database_connection_name
  sensitive   = true
}

output "bigquery_dataset_id" {
  description = "The BigQuery dataset ID"
  value       = module.database.bigquery_dataset_id
}

output "container_registry" {
  description = "The Artifact Registry URL for container images"
  value       = module.storage.container_registry
}

output "service_account_email" {
  description = "The service account email for the application"
  value       = google_service_account.app_service_account.email
}