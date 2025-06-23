module "networking" {
  source = "./modules/networking"
  
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  labels      = local.labels
}

resource "google_service_account" "app_service_account" {
  account_id   = "sentinelops-${var.environment}"
  display_name = "SentinelOps Service Account ${var.environment}"
}

resource "google_project_iam_member" "service_account_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/bigquery.dataEditor",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent"
  ])
  
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.app_service_account.email}"
}

module "database" {
  source = "./modules/database"
  
  project_id  = var.project_id
  region      = var.region
  network_id  = module.networking.network_id
  environment = var.environment
  labels      = local.labels
  
  depends_on = [module.networking]
}

module "storage" {
  source = "./modules/storage"
  
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  labels      = local.labels
}

module "compute" {
  source = "./modules/compute"
  
  project_id            = var.project_id
  region                = var.region
  service_account_email = google_service_account.app_service_account.email
  vpc_connector_id      = module.networking.vpc_connector_id
  environment           = var.environment
  labels                = local.labels
  
  depends_on = [
    module.networking,
    google_project_iam_member.service_account_roles
  ]
}

module "load_balancer" {
  source = "./modules/load-balancer"
  
  project_id             = var.project_id
  cloud_run_service_name = module.compute.api_url
  region                 = var.region
  environment            = var.environment
  labels                 = local.labels
  
  depends_on = [module.compute]
}

module "security" {
  source = "./modules/security"
  
  project_id       = var.project_id
  network_id       = module.networking.network_id
  environment      = var.environment
  labels           = local.labels
  access_policy_id = var.access_policy_id
}