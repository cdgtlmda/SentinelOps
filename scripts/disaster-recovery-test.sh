#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-dev}"
TEST_TYPE="${3:-partial}"  # partial or full

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT] [TEST_TYPE]"
    echo "TEST_TYPE: partial (default) or full"
    exit 1
fi

echo "Starting disaster recovery test for project: $PROJECT_ID (environment: $ENVIRONMENT)"
echo "Test type: $TEST_TYPE"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test results
PASSED=0
FAILED=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "\n${YELLOW}Running test: $test_name${NC}"
    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
    fi
}

# Test 1: Verify backup exists
run_test "Recent backup exists" "
    gsutil ls gs://${PROJECT_ID}-sentinelops-backups-us-central1-${ENVIRONMENT}/database/ | grep -q $(date +%Y-%m-%d)
"

# Test 2: Test backup restoration
if [ "$TEST_TYPE" == "full" ]; then
    run_test "Database backup restoration" "
        # Create test instance
        gcloud sql instances create sentinelops-dr-test-${ENVIRONMENT} \
            --database-version=POSTGRES_15 \
            --tier=db-f1-micro \
            --region=us-central1 \
            --project=$PROJECT_ID
        
        # Restore from backup
        LATEST_BACKUP=\$(gsutil ls gs://${PROJECT_ID}-sentinelops-backups-us-central1-${ENVIRONMENT}/database/*.sql | tail -1)
        gcloud sql import sql sentinelops-dr-test-${ENVIRONMENT} \$LATEST_BACKUP \
            --database=sentinelops \
            --project=$PROJECT_ID
        
        # Cleanup
        gcloud sql instances delete sentinelops-dr-test-${ENVIRONMENT} \
            --project=$PROJECT_ID --quiet
    "
fi

# Test 3: Verify cross-region replication
run_test "Cross-region backup replication" "
    REGIONS='us-east1 europe-west1 asia-east1'
    for REGION in \$REGIONS; do
        gsutil ls gs://${PROJECT_ID}-sentinelops-backups-\${REGION}-${ENVIRONMENT}/ || return 1
    done
"

# Test 4: Test failover to replica (if prod)
if [ "$ENVIRONMENT" == "prod" ]; then
    run_test "Database replica availability" "
        gcloud sql instances describe sentinelops-db-prod-backup-us-east1 \
            --project=$PROJECT_ID \
            --format='value(state)' | grep -q RUNNABLE
    "
fi

# Test 5: Verify monitoring alerts
run_test "DR monitoring alerts configured" "
    gcloud alpha monitoring policies list \
        --project=$PROJECT_ID \
        --filter='displayName:\"Backup Failure Alert\"' \
        --format='value(name)' | grep -q .
"

# Test 6: Test application deployment to backup region
if [ "$TEST_TYPE" == "full" ]; then
    run_test "Deploy to backup region" "
        gcloud run deploy sentinelops-dr-test \
            --image=gcr.io/$PROJECT_ID/sentinelops:latest \
            --region=us-east1 \
            --platform=managed \
            --no-allow-unauthenticated \
            --project=$PROJECT_ID
        
        # Test health check
        SERVICE_URL=\$(gcloud run services describe sentinelops-dr-test \
            --region=us-east1 \
            --project=$PROJECT_ID \
            --format='value(status.url)')
        
        curl -s -o /dev/null -w '%{http_code}' \$SERVICE_URL/health | grep -q 200
        
        # Cleanup
        gcloud run services delete sentinelops-dr-test \
            --region=us-east1 \
            --project=$PROJECT_ID --quiet
    "
fi

# Test 7: Verify secrets replication
run_test "Secrets accessible in backup regions" "
    gcloud secrets versions access latest \
        --secret=sentinelops-api-keys-${ENVIRONMENT} \
        --project=$PROJECT_ID > /dev/null
"

# Test 8: Test data export functionality
run_test "Data export to BigQuery" "
    bq query --project_id=$PROJECT_ID --use_legacy_sql=false \
        'SELECT COUNT(*) FROM sentinelops_analytics_${ENVIRONMENT}.incidents LIMIT 1' > /dev/null
"

# Test 9: Verify backup retention
run_test "Backup retention policy" "
    BUCKET=gs://${PROJECT_ID}-sentinelops-backups-us-central1-${ENVIRONMENT}
    gsutil lifecycle get \$BUCKET | grep -q lifecycle
"

# Test 10: Documentation accessibility
run_test "DR documentation accessible" "
    gsutil cat gs://${PROJECT_ID}-sentinelops-critical-${ENVIRONMENT}/disaster-recovery/runbook.md | grep -q 'Disaster Recovery'
"

# Summary
echo -e "\n${YELLOW}=== Disaster Recovery Test Summary ===${NC}"
echo -e "Total tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All disaster recovery tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some disaster recovery tests failed. Please review and fix.${NC}"
    exit 1
fi