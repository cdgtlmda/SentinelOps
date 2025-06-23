# Monitoring and Logging configuration for SentinelOps

# Notification channels
resource "google_monitoring_notification_channel" "email_security" {
  display_name = "Security Team Email"
  type         = "email"
  
  labels = {
    email_address = "security-team@example.com"
  }
}

resource "google_monitoring_notification_channel" "slack" {
  display_name = "Slack Security Alerts"
  type         = "slack"
  
  labels = {
    url = var.slack_webhook_url
  }
  
  sensitive_labels {
    auth_token = var.slack_auth_token
  }
}

# Custom metrics
resource "google_logging_metric" "incident_count" {
  name   = "incident_count"
  filter = "jsonPayload.event_type=\"security_incident\""
  
  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "INT64"
    
    labels {
      key         = "severity"
      value_type  = "STRING"
      description = "Incident severity level"
    }
    
    labels {
      key         = "type"
      value_type  = "STRING"
      description = "Incident type"
    }
  }
  
  label_extractors = {
    "severity" = "EXTRACT(jsonPayload.severity)"
    "type"     = "EXTRACT(jsonPayload.incident_type)"
  }
}

resource "google_logging_metric" "remediation_success_rate" {
  name   = "remediation_success_rate"
  filter = "jsonPayload.action=\"remediation_complete\""
  
  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "DOUBLE"
    unit        = "1"
  }
  
  value_extractor = "EXTRACT(IF(jsonPayload.success=\"true\", 1, 0))"
}

resource "google_logging_metric" "detection_latency" {
  name   = "detection_latency"
  filter = "jsonPayload.event_type=\"threat_detected\""
  
  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "INT64"
    unit        = "ms"
  }
  
  value_extractor = "EXTRACT(jsonPayload.detection_latency_ms)"
}

# Alert policies
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate - Cloud Run Services"
  combiner     = "OR"
  
  conditions {
    display_name = "Error rate exceeds 5%"
    
    condition_threshold {
      filter     = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class=\"5xx\""
      duration   = "180s"
      comparison = "COMPARISON_GT"
      
      threshold_value = 0.05
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email_security.name,
    google_monitoring_notification_channel.slack.name
  ]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  documentation {
    content = "Cloud Run service error rate is above 5%. Check application logs for errors.\n\nRunbook: https://wiki.example.com/sentinelops/runbooks/high-error-rate"
  }
}

resource "google_monitoring_alert_policy" "security_incident_surge" {
  display_name = "Security Incident Surge"
  combiner     = "OR"
  
  conditions {
    display_name = "Incident rate increased by 300%"
    
    condition_threshold {
      filter     = "metric.type=\"logging.googleapis.com/user/incident_count\""
      duration   = "600s"
      comparison = "COMPARISON_GT"
      
      threshold_value = 3.0
      
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email_security.name,
    google_monitoring_notification_channel.slack.name
  ]
  
  documentation {
    content = "Significant increase in security incidents detected. This may indicate an ongoing attack.\n\nImmediate actions:\n1. Check the security dashboard\n2. Review recent incidents\n3. Enable enhanced monitoring\n4. Contact security team lead"
  }
}

resource "google_monitoring_alert_policy" "remediation_failures" {
  display_name = "Remediation Success Rate Low"
  combiner     = "OR"
  
  conditions {
    display_name = "Success rate below 90%"
    
    condition_threshold {
      filter     = "metric.type=\"logging.googleapis.com/user/remediation_success_rate\""
      duration   = "300s"
      comparison = "COMPARISON_LT"
      
      threshold_value = 0.9
      
      aggregations {
        alignment_period   = "600s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [
    google_monitoring_notification_channel.email_security.name
  ]
  
  documentation {
    content = "Remediation success rate has dropped below 90%. This may indicate:\n- Permission issues\n- API failures\n- Invalid remediation targets\n\nCheck remediation logs for specific errors."
  }
}

# Uptime checks
resource "google_monitoring_uptime_check_config" "orchestrator_health" {
  display_name = "Orchestrator Health Check"
  timeout      = "10s"
  period       = "60s"
  
  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
    
    accepted_response_status_codes {
      status_value = 200
    }
  }
  
  monitored_resource {
    type = "uptime_url"
    
    labels = {
      project_id = var.project_id
      host       = "${module.compute.api_url}"
    }
  }
  
  selected_regions = [
    "USA",
    "EUROPE"
  ]
  
  content_matchers {
    content = "healthy"
    matcher = "CONTAINS_STRING"
  }
}

# Log sinks
resource "google_logging_project_sink" "security_logs_to_bigquery" {
  name        = "security-logs-to-bigquery"
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${module.database.bigquery_dataset_id}"
  
  filter = <<-EOT
    jsonPayload.event_type="security_incident" OR
    jsonPayload.event_type="threat_detected" OR
    severity >= ERROR
  EOT
  
  unique_writer_identity = true
  
  bigquery_options {
    use_partitioned_tables = true
  }
}

resource "google_logging_project_sink" "audit_logs_to_storage" {
  name        = "audit-logs-to-storage"
  destination = "storage.googleapis.com/${module.storage.backups_bucket}"
  
  filter = "protoPayload.@type=\"type.googleapis.com/google.cloud.audit.AuditLog\""
  
  unique_writer_identity = true
}

# Dashboard (JSON configuration)
resource "google_monitoring_dashboard" "security_overview" {
  dashboard_json = jsonencode({
    displayName = "SentinelOps Security Overview"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Active Security Incidents"
            scorecard = {
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"logging.googleapis.com/user/incident_count\""
                  aggregation = {
                    alignmentPeriod  = "60s"
                    perSeriesAligner = "ALIGN_MEAN"
                  }
                }
              }
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Threat Severity Distribution"
            pieChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"logging.googleapis.com/user/incident_count\""
                    aggregation = {
                      alignmentPeriod  = "300s"
                      perSeriesAligner = "ALIGN_MEAN"
                      groupByFields    = ["metric.label.severity"]
                    }
                  }
                }
              }]
            }
          }
        },
        {
          yPos   = 4
          width  = 12
          height = 4
          widget = {
            title = "Detection Agent Activity"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"sentinelops-detection\""
                    aggregation = {
                      alignmentPeriod  = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                    }
                  }
                }
                plotType = "LINE"
              }]
            }
          }
        }
      ]
    }
  })
}

# SLO for API availability
resource "google_monitoring_slo" "api_availability" {
  service      = google_monitoring_service.sentinelops_api.service_id
  display_name = "99.9% Availability"
  
  goal                = 0.999
  rolling_period_days = 30
  
  request_based_sli {
    good_total_ratio {
      good_service_filter = "metric.type=\"run.googleapis.com/request_count\" AND metric.label.response_code_class!=\"5xx\""
      total_service_filter = "metric.type=\"run.googleapis.com/request_count\""
    }
  }
}

# Error reporting configuration (note: this is automatically enabled)
resource "google_project_service" "error_reporting" {
  service = "clouderrorreporting.googleapis.com"
}

# Monitoring service for SLOs
resource "google_monitoring_service" "sentinelops_api" {
  service_id   = "sentinelops-api"
  display_name = "SentinelOps API"
  
  basic_service {
    service_type = "CLOUD_RUN"
    service_labels = {
      service_name = "sentinelops-orchestrator"
      location     = var.region
    }
  }
}