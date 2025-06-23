variable "project_id" {
  type = string
}

variable "cloud_run_service_name" {
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

resource "google_compute_global_address" "lb_ip" {
  name = "sentinelops-lb-ip-${var.environment}"
}

resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  name                  = "sentinelops-neg-${var.environment}"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  
  cloud_run {
    service = var.cloud_run_service_name
  }
}

resource "google_compute_backend_service" "backend" {
  name = "sentinelops-backend-${var.environment}"
  
  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg.id
  }
  
  enable_cdn = true
  
  cdn_policy {
    cache_mode        = "USE_ORIGIN_HEADERS"
    serve_while_stale = 86400
    
    cache_key_policy {
      include_host         = true
      include_protocol     = true
      include_query_string = true
    }
  }
}

resource "google_compute_url_map" "url_map" {
  name            = "sentinelops-url-map-${var.environment}"
  default_service = google_compute_backend_service.backend.id
}

resource "google_compute_managed_ssl_certificate" "ssl_cert" {
  name = "sentinelops-ssl-cert-${var.environment}"
  
  managed {
    domains = ["sentinelops-${var.environment}.example.com"]
  }
}

resource "google_compute_target_https_proxy" "https_proxy" {
  name             = "sentinelops-https-proxy-${var.environment}"
  url_map          = google_compute_url_map.url_map.id
  ssl_certificates = [google_compute_managed_ssl_certificate.ssl_cert.id]
}

resource "google_compute_global_forwarding_rule" "forwarding_rule" {
  name       = "sentinelops-forwarding-rule-${var.environment}"
  target     = google_compute_target_https_proxy.https_proxy.id
  port_range = "443"
  ip_address = google_compute_global_address.lb_ip.address
}

output "load_balancer_ip" {
  value = google_compute_global_address.lb_ip.address
}