variable "project_id" {
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

# Cloud Armor security policy
resource "google_compute_security_policy" "sentinelops" {
  name = "sentinelops-security-policy-${var.environment}"

  # Default rule
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default rule"
  }

  # Rate limiting rule
  rule {
    action   = "rate_based_ban"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action = "deny(429)"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
      ban_duration_sec = 600
    }
    description = "Rate limiting rule"
  }

  # Block known malicious IPs
  rule {
    action   = "deny(403)"
    priority = "100"
    match {
      expr {
        expression = "origin.region_code == 'XX'"
      }
    }
    description = "Block traffic from unknown regions"
  }

  # SQL injection protection
  rule {
    action   = "deny(403)"
    priority = "200"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "SQL injection protection"
  }

  # XSS protection
  rule {
    action   = "deny(403)"
    priority = "201"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "Cross-site scripting protection"
  }
}

# Web Application Firewall
resource "google_compute_backend_service" "waf_backend" {
  name            = "sentinelops-waf-backend-${var.environment}"
  security_policy = google_compute_security_policy.sentinelops.id
}

# Binary Authorization
resource "google_binary_authorization_policy" "policy" {
  count = var.environment == "prod" ? 1 : 0
  
  admission_whitelist_patterns {
    name_pattern = "gcr.io/${var.project_id}/*"
  }

  default_admission_rule {
    evaluation_mode         = "REQUIRE_ATTESTATION"
    enforcement_mode        = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    require_attestations_by = [google_binary_authorization_attestor.prod_attestor[0].name]
  }

  cluster_admission_rules {
    cluster                 = "*.${var.project_id}"
    evaluation_mode        = "REQUIRE_ATTESTATION"
    enforcement_mode       = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    require_attestations_by = [google_binary_authorization_attestor.prod_attestor[0].name]
  }
}

resource "google_binary_authorization_attestor" "prod_attestor" {
  count = var.environment == "prod" ? 1 : 0
  
  name = "prod-attestor"
  
  attestation_authority_note {
    note_reference = google_container_analysis_note.attestor_note[0].name
    
    public_keys {
      id = data.google_kms_crypto_key_version.attestor_key[0].id
      pkix_public_key {
        public_key_pem      = data.google_kms_crypto_key_version.attestor_key[0].public_key[0].pem
        signature_algorithm = data.google_kms_crypto_key_version.attestor_key[0].public_key[0].algorithm
      }
    }
  }
}

resource "google_container_analysis_note" "attestor_note" {
  count = var.environment == "prod" ? 1 : 0
  
  name = "prod-attestor-note"
  
  attestation_authority {
    hint {
      human_readable_name = "Production attestor"
    }
  }
}

data "google_kms_crypto_key_version" "attestor_key" {
  count      = var.environment == "prod" ? 1 : 0
  crypto_key = google_kms_crypto_key.attestor_key[0].id
}

resource "google_kms_crypto_key" "attestor_key" {
  count    = var.environment == "prod" ? 1 : 0
  name     = "attestor-key"
  key_ring = google_kms_key_ring.sentinelops.id
  purpose  = "ASYMMETRIC_SIGN"

  version_template {
    algorithm = "RSA_SIGN_PKCS1_4096_SHA512"
  }
}

# KMS for encryption
resource "google_kms_key_ring" "sentinelops" {
  name     = "sentinelops-keyring-${var.environment}"
  location = "global"
}

resource "google_kms_crypto_key" "database" {
  name     = "database-encryption-key"
  key_ring = google_kms_key_ring.sentinelops.id
  
  rotation_period = "7776000s" # 90 days
  
  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key" "storage" {
  name     = "storage-encryption-key"
  key_ring = google_kms_key_ring.sentinelops.id
  
  rotation_period = "7776000s" # 90 days
  
  lifecycle {
    prevent_destroy = true
  }
}

# VPC Service Controls
resource "google_access_context_manager_service_perimeter" "sentinelops" {
  count = var.environment == "prod" ? 1 : 0
  
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/sentinelops_${var.environment}"
  title  = "SentinelOps ${var.environment} Perimeter"
  
  status {
    restricted_services = [
      "storage.googleapis.com",
      "bigquery.googleapis.com",
      "sqladmin.googleapis.com",
      "run.googleapis.com",
      "artifactregistry.googleapis.com"
    ]
    
    resources = [
      "projects/${var.project_id}"
    ]
    
    ingress_policies {
      ingress_from {
        identity_type = "ANY_IDENTITY"
        sources {
          resource = "projects/${var.project_id}"
        }
      }
      
      ingress_to {
        resources = ["*"]
        operations {
          service_name = "storage.googleapis.com"
          method_selectors {
            method = "*"
          }
        }
      }
    }
    
    egress_policies {
      egress_from {
        identity_type = "ANY_SERVICE_ACCOUNT"
      }
      
      egress_to {
        resources = ["*"]
        operations {
          service_name = "storage.googleapis.com"
          method_selectors {
            method = "*"
          }
        }
      }
    }
  }
}

# Workload Identity
resource "google_service_account" "workload_identity" {
  account_id   = "sentinelops-wi-${var.environment}"
  display_name = "SentinelOps Workload Identity ${var.environment}"
}

resource "google_project_iam_member" "workload_identity_user" {
  project = var.project_id
  role    = "roles/iam.workloadIdentityUser"
  member  = "serviceAccount:${var.project_id}.svc.id.goog[sentinelops/sentinelops-api]"
}

# Secret Manager
resource "google_secret_manager_secret" "api_keys" {
  secret_id = "sentinelops-api-keys-${var.environment}"
  
  replication {
    automatic = true
  }
  
  labels = var.labels
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "sentinelops-db-password-${var.environment}"
  
  replication {
    automatic = true
  }
  
  rotation {
    rotation_period = "7776000s" # 90 days
  }
  
  labels = var.labels
}

# Network security
resource "google_compute_firewall" "deny_all_ingress" {
  name    = "sentinelops-deny-all-ingress-${var.environment}"
  network = var.network_id
  
  priority = 65534
  
  deny {
    protocol = "all"
  }
  
  source_ranges = ["0.0.0.0/0"]
  
  description = "Deny all ingress traffic by default"
}

output "kms_keyring_id" {
  value = google_kms_key_ring.sentinelops.id
}

output "database_key_id" {
  value = google_kms_crypto_key.database.id
}

output "storage_key_id" {
  value = google_kms_crypto_key.storage.id
}

output "security_policy_id" {
  value = google_compute_security_policy.sentinelops.id
}