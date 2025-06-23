#!/bin/bash
# SentinelOps Threat Intelligence Ingestion Script
# Downloads and ingests free threat intelligence feeds

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"your-gcp-project-id"}
BUCKET_NAME="threat-feeds-${PROJECT_ID}"
DATASET_NAME="threat_intel"
TEMP_DIR="/tmp/threat_feeds"

echo "🔄 Starting threat intelligence ingestion..."
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# Create temp directory
mkdir -p ${TEMP_DIR}
cd ${TEMP_DIR}

# Function to log with timestamp
log() {
    echo "[$(date -u '+%H:%M:%S')] $1"
}

# 1. CISA Known Exploited Vulnerabilities
log "📡 Fetching CISA KEV catalog..."
DATE_SUFFIX=$(date +%Y%m%d_%H%M%S)

curl -sSL https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json \
  -o cisa_kev_${DATE_SUFFIX}.json

# Transform CISA KEV data for BigQuery
log "🔧 Transforming CISA KEV data..."
python3 -c "
import json
import sys
from datetime import datetime

with open('cisa_kev_${DATE_SUFFIX}.json', 'r') as f:
    data = json.load(f)

with open('cisa_kev_transformed.jsonl', 'w') as f:
    for vuln in data.get('vulnerabilities', []):
        # Add ingestion timestamp
        vuln['_ingestion_timestamp'] = datetime.utcnow().isoformat() + 'Z'
        f.write(json.dumps(vuln) + '\n')

print(f'Processed {len(data.get(\"vulnerabilities\", []))} vulnerabilities')
"

# Upload to Cloud Storage and load to BigQuery
gsutil cp cisa_kev_transformed.jsonl gs://${BUCKET_NAME}/cisa_kev/kev_${DATE_SUFFIX}.jsonl

bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
  ${DATASET_NAME}.cisa_kev \
  gs://${BUCKET_NAME}/cisa_kev/kev_${DATE_SUFFIX}.jsonl

log "✅ CISA KEV data loaded"

# 2. AbuseIPDB (requires API key, using sample data for demo)
log "📡 Generating AbuseIPDB sample data..."
python3 -c "
import json
import random
from datetime import datetime, timedelta

# Generate realistic sample data for demo
sample_ips = []
malicious_ranges = [
    '185.220.', '194.147.', '178.73.', '91.134.',  # Known bad ranges
    '103.94.', '45.142.', '167.99.', '159.203.'
]

for i in range(100):
    prefix = random.choice(malicious_ranges)
    ip = prefix + str(random.randint(1, 254)) + '.' + str(random.randint(1, 254))
    
    record = {
        'ip': ip,
        'country_code': random.choice(['CN', 'RU', 'IR', 'KP', 'BR']),
        'usage_type': random.choice(['hosting', 'business', 'residential']),
        'isp': f'ISP-{random.randint(1000, 9999)}',
        'domain': f'domain{random.randint(100, 999)}.com',
        'total_reports': random.randint(10, 500),
        'num_distinct_users': random.randint(5, 50),
        'last_reported_at': (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).isoformat() + 'Z',
        'confidence_percentage': random.randint(75, 100),
        '_ingestion_timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    sample_ips.append(record)

with open('abuseipdb_sample.jsonl', 'w') as f:
    for record in sample_ips:
        f.write(json.dumps(record) + '\n')

print(f'Generated {len(sample_ips)} sample malicious IPs')
"

gsutil cp abuseipdb_sample.jsonl gs://${BUCKET_NAME}/abuseipdb/blacklist_${DATE_SUFFIX}.jsonl

bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
  ${DATASET_NAME}.abuseipdb_blacklist \
  gs://${BUCKET_NAME}/abuseipdb/blacklist_${DATE_SUFFIX}.jsonl

log "✅ AbuseIPDB sample data loaded"

# 3. FireHOL IP lists
log "📡 Fetching FireHOL Level 1 list..."
curl -sSL https://iplists.firehol.org/files/firehol_level1.netset \
  -o firehol_level1.txt

# Transform FireHOL data
python3 -c "
import json
from datetime import datetime

with open('firehol_level1.txt', 'r') as f:
    lines = f.readlines()

records = []
for line in lines:
    line = line.strip()
    if line and not line.startswith('#'):
        record = {
            'ip_range': line,
            'list_name': 'firehol_level1',
            'list_level': 1,
            'description': 'High confidence malicious IPs',
            '_ingestion_timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        records.append(record)

with open('firehol_transformed.jsonl', 'w') as f:
    for record in records:
        f.write(json.dumps(record) + '\n')

print(f'Processed {len(records)} IP ranges from FireHOL Level 1')
"

gsutil cp firehol_transformed.jsonl gs://${BUCKET_NAME}/firehol/level1_${DATE_SUFFIX}.jsonl

bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
  ${DATASET_NAME}.firehol_ips \
  gs://${BUCKET_NAME}/firehol/level1_${DATE_SUFFIX}.jsonl

log "✅ FireHOL data loaded"

# 4. MITRE ATT&CK (using enterprise techniques)
log "📡 Fetching MITRE ATT&CK techniques..."
curl -sSL https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json \
  -o mitre_attack.json

# Transform MITRE ATT&CK data
python3 -c "
import json
from datetime import datetime

with open('mitre_attack.json', 'r') as f:
    data = json.load(f)

techniques = []
for obj in data.get('objects', []):
    if obj.get('type') == 'attack-pattern':
        # Extract technique info
        technique_id = ''
        for ref in obj.get('external_references', []):
            if ref.get('source_name') == 'mitre-attack':
                technique_id = ref.get('external_id', '')
                break
        
        if technique_id:
            record = {
                'technique_id': technique_id,
                'technique_name': obj.get('name', ''),
                'tactic': ','.join([phase.get('phase_name', '') for phase in obj.get('kill_chain_phases', [])]),
                'platform': ','.join(obj.get('x_mitre_platforms', [])),
                'description': obj.get('description', '')[:1000],  # Truncate for BigQuery
                'external_references': json.dumps(obj.get('external_references', [])),
                '_ingestion_timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            techniques.append(record)

with open('mitre_attack_transformed.jsonl', 'w') as f:
    for record in techniques:
        f.write(json.dumps(record) + '\n')

print(f'Processed {len(techniques)} MITRE ATT&CK techniques')
"

gsutil cp mitre_attack_transformed.jsonl gs://${BUCKET_NAME}/mitre_attack/techniques_${DATE_SUFFIX}.jsonl

bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
  ${DATASET_NAME}.mitre_attack \
  gs://${BUCKET_NAME}/mitre_attack/techniques_${DATE_SUFFIX}.jsonl

log "✅ MITRE ATT&CK data loaded"

# 5. Spamhaus DROP list
log "📡 Fetching Spamhaus DROP list..."
curl -sSL https://www.spamhaus.org/drop/drop.txt -o spamhaus_drop.txt

# Transform Spamhaus data
python3 -c "
import json
import re
from datetime import datetime

with open('spamhaus_drop.txt', 'r') as f:
    lines = f.readlines()

records = []
for line in lines:
    line = line.strip()
    if line and not line.startswith(';'):
        # Parse format: 1.2.3.0/24 ; SBL123456
        match = re.match(r'([0-9./]+)\s*;\s*(.+)', line)
        if match:
            ip_range, description = match.groups()
            sbl_match = re.search(r'SBL(\d+)', description)
            sbl_number = sbl_match.group(1) if sbl_match else ''
            
            record = {
                'ip_range': ip_range,
                'sbl_number': sbl_number,
                'description': description.strip(),
                '_ingestion_timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            records.append(record)

with open('spamhaus_transformed.jsonl', 'w') as f:
    for record in records:
        f.write(json.dumps(record) + '\n')

print(f'Processed {len(records)} Spamhaus DROP entries')
"

gsutil cp spamhaus_transformed.jsonl gs://${BUCKET_NAME}/spamhaus/drop_${DATE_SUFFIX}.jsonl

bq load --replace --source_format=NEWLINE_DELIMITED_JSON \
  ${DATASET_NAME}.spamhaus_drop \
  gs://${BUCKET_NAME}/spamhaus/drop_${DATE_SUFFIX}.jsonl

log "✅ Spamhaus DROP data loaded"

# Clean up temp files
cd /
rm -rf ${TEMP_DIR}

# Show summary statistics
log "📊 Ingestion Summary:"
echo ""
echo "🗄️ BigQuery Tables Updated:"
bq query --use_legacy_sql=false --format=table "
SELECT 
  table_name,
  row_count,
  size_bytes,
  TIMESTAMP_MILLIS(last_modified_time) as last_modified
FROM \`${PROJECT_ID}.${DATASET_NAME}.__TABLES__\`
ORDER BY table_name
"

echo ""
echo "🎯 Threat Intelligence Summary:"
bq query --use_legacy_sql=false --format=table "
SELECT 
  source,
  indicator_type,
  severity,
  COUNT(*) as indicator_count,
  AVG(confidence) as avg_confidence
FROM \`${PROJECT_ID}.${DATASET_NAME}.threat_indicators\`
GROUP BY source, indicator_type, severity
ORDER BY source, severity DESC
"

log "✅ Threat intelligence ingestion complete!"
echo ""
echo "🚀 Next: Configure SentinelOps agents to use threat intel with queries like:"
echo "   LEFT JOIN \`${PROJECT_ID}.${DATASET_NAME}.threat_indicators\` ti ON vpc_flow.src_ip = ti.indicator"