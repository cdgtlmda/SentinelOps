#!/bin/bash
# SentinelOps Threat Intelligence Feeds Setup
# Sets up free threat intel feeds for BigQuery integration

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"your-gcp-project-id"}
BUCKET_NAME="threat-feeds-${PROJECT_ID}"
DATASET_NAME="threat_intel"

echo "🚀 Setting up SentinelOps Threat Intelligence Feeds"
echo "Project: ${PROJECT_ID}"
echo "Bucket: ${BUCKET_NAME}"
echo "Dataset: ${DATASET_NAME}"

# Create Cloud Storage bucket for threat feeds
echo "📦 Creating Cloud Storage bucket..."
gsutil mb -p ${PROJECT_ID} gs://${BUCKET_NAME} || echo "Bucket already exists"

# Create BigQuery dataset
echo "🗄️ Creating BigQuery dataset..."
bq mk --project_id=${PROJECT_ID} --dataset --location=US ${DATASET_NAME} || echo "Dataset already exists"

# Create directory structure in bucket
echo "📁 Creating directory structure..."
gsutil -m cp /dev/null gs://${BUCKET_NAME}/cisa_kev/.keep
gsutil -m cp /dev/null gs://${BUCKET_NAME}/abuseipdb/.keep
gsutil -m cp /dev/null gs://${BUCKET_NAME}/firehol/.keep
gsutil -m cp /dev/null gs://${BUCKET_NAME}/mitre_attack/.keep
gsutil -m cp /dev/null gs://${BUCKET_NAME}/spamhaus/.keep

echo "✅ Threat feeds infrastructure setup complete!"

# Create BigQuery tables
echo "🏗️ Creating BigQuery tables..."

# CISA KEV table
bq mk --project_id=${PROJECT_ID} \
  --table ${DATASET_NAME}.cisa_kev \
  cveID:STRING,vendorProject:STRING,product:STRING,vulnerabilityName:STRING,dateAdded:DATE,shortDescription:STRING,requiredAction:STRING,dueDate:DATE,knownRansomwareCampaignUse:STRING,notes:STRING,cwes:STRING,_ingestion_timestamp:TIMESTAMP

# AbuseIPDB table
bq mk --project_id=${PROJECT_ID} \
  --table ${DATASET_NAME}.abuseipdb_blacklist \
  ip:STRING,country_code:STRING,usage_type:STRING,isp:STRING,domain:STRING,total_reports:INTEGER,num_distinct_users:INTEGER,last_reported_at:TIMESTAMP,confidence_percentage:INTEGER,_ingestion_timestamp:TIMESTAMP

# FireHOL IP lists table
bq mk --project_id=${PROJECT_ID} \
  --table ${DATASET_NAME}.firehol_ips \
  ip_range:STRING,list_name:STRING,list_level:INTEGER,description:STRING,_ingestion_timestamp:TIMESTAMP

# MITRE ATT&CK table
bq mk --project_id=${PROJECT_ID} \
  --table ${DATASET_NAME}.mitre_attack \
  technique_id:STRING,technique_name:STRING,tactic:STRING,platform:STRING,description:STRING,external_references:STRING,_ingestion_timestamp:TIMESTAMP

# Spamhaus DROP table
bq mk --project_id=${PROJECT_ID} \
  --table ${DATASET_NAME}.spamhaus_drop \
  ip_range:STRING,sbl_number:STRING,description:STRING,_ingestion_timestamp:TIMESTAMP

# Create enrichment views
echo "📊 Creating enrichment views..."

# Unified threat indicators view
bq mk --project_id=${PROJECT_ID} \
  --view \
  --description="Unified view of all threat indicators" \
  ${DATASET_NAME}.threat_indicators \
  "SELECT 
    ip as indicator,
    'ip' as indicator_type,
    'high' as severity,
    'abuseipdb' as source,
    confidence_percentage/100.0 as confidence,
    _ingestion_timestamp
  FROM \`${PROJECT_ID}.${DATASET_NAME}.abuseipdb_blacklist\`
  WHERE confidence_percentage >= 75
  
  UNION ALL
  
  SELECT 
    REGEXP_EXTRACT(ip_range, r'([0-9.]+)') as indicator,
    'ip' as indicator_type,
    CASE 
      WHEN list_level <= 2 THEN 'critical'
      WHEN list_level = 3 THEN 'high' 
      ELSE 'medium'
    END as severity,
    'firehol' as source,
    0.8 as confidence,
    _ingestion_timestamp
  FROM \`${PROJECT_ID}.${DATASET_NAME}.firehol_ips\`
  
  UNION ALL
  
  SELECT 
    REGEXP_EXTRACT(ip_range, r'([0-9.]+)') as indicator,
    'ip' as indicator_type,
    'critical' as severity,
    'spamhaus' as source,
    0.95 as confidence,
    _ingestion_timestamp
  FROM \`${PROJECT_ID}.${DATASET_NAME}.spamhaus_drop\`"

echo "✅ BigQuery tables and views created!"

echo "🎯 Next steps:"
echo "1. Run initial data ingestion: ./ingest_threat_feeds.sh"
echo "2. Set up Cloud Scheduler for automated updates"
echo "3. Configure SentinelOps Detection Agent to use threat intel"
echo ""
echo "📚 Available tables:"
echo "  - ${DATASET_NAME}.cisa_kev (Known Exploited Vulnerabilities)"
echo "  - ${DATASET_NAME}.abuseipdb_blacklist (Malicious IPs)"
echo "  - ${DATASET_NAME}.firehol_ips (IP reputation lists)"
echo "  - ${DATASET_NAME}.mitre_attack (ATT&CK techniques)"
echo "  - ${DATASET_NAME}.spamhaus_drop (Spam/botnet IPs)"
echo "  - ${DATASET_NAME}.threat_indicators (Unified view)"