#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ENVIRONMENT="${2:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ENVIRONMENT]"
    exit 1
fi

echo "Running production readiness checks for project: $PROJECT_ID"
echo "Environment: $ENVIRONMENT"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Check function
check() {
    local category="$1"
    local check_name="$2"
    local check_cmd="$3"
    local severity="${4:-error}"  # error or warning
    
    printf "%-50s" "$category: $check_name"
    
    if eval "$check_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        if [ "$severity" == "warning" ]; then
            echo -e "${YELLOW}⚠ WARNING${NC}"
            ((WARNINGS++))
        else
            echo -e "${RED}✗ FAIL${NC}"
            ((FAILED++))
        fi
    fi
}

echo -e "\n${BLUE}1. Infrastructure Checks${NC}"
echo "------------------------"

check "Compute" "Cloud Run services deployed" \
    "gcloud run services list --project=$PROJECT_ID --format='value(name)' | grep -q sentinelops"

check "Database" "Cloud SQL instance running" \
    "gcloud sql instances describe sentinelops-db-$ENVIRONMENT --project=$PROJECT_ID --format='value(state)' | grep -q RUNNABLE"

check "Database" "Automated backups enabled" \
    "gcloud sql instances describe sentinelops-db-$ENVIRONMENT --project=$PROJECT_ID --format='value(settings.backupConfiguration.enabled)' | grep -q True"

check "Storage" "Artifact Registry configured" \
    "gcloud artifacts repositories describe sentinelops --location=us-central1 --project=$PROJECT_ID"

check "Network" "VPC configured" \
    "gcloud compute networks describe sentinelops-vpc-$ENVIRONMENT --project=$PROJECT_ID"

check "Network" "Cloud NAT configured" \
    "gcloud compute routers nats list --router=sentinelops-router --region=us-central1 --project=$PROJECT_ID | grep -q sentinelops"

echo -e "\n${BLUE}2. Security Checks${NC}"
echo "------------------"

check "IAM" "Service accounts configured" \
    "gcloud iam service-accounts list --project=$PROJECT_ID --format='value(email)' | grep -q sentinelops"

check "IAM" "Workload Identity enabled" \
    "gcloud container clusters describe sentinelops-gke-$ENVIRONMENT --zone=us-central1-a --project=$PROJECT_ID --format='value(workloadIdentityConfig.workloadPool)' | grep -q '.svc.id.goog'" \
    "warning"

check "Secrets" "Secret Manager configured" \
    "gcloud secrets list --project=$PROJECT_ID --format='value(name)' | grep -q sentinelops"

check "Encryption" "KMS keys configured" \
    "gcloud kms keys list --location=global --keyring=sentinelops-keyring-$ENVIRONMENT --project=$PROJECT_ID | grep -q encryption"

check "Security" "Binary Authorization enabled" \
    "gcloud container binauthz policy export --project=$PROJECT_ID | grep -q evaluationMode" \
    "warning"

check "Security" "Cloud Armor configured" \
    "gcloud compute security-policies list --project=$PROJECT_ID | grep -q sentinelops"

echo -e "\n${BLUE}3. Monitoring & Logging${NC}"
echo "-----------------------"

check "Monitoring" "Alert policies configured" \
    "gcloud alpha monitoring policies list --project=$PROJECT_ID --format='value(displayName)' | grep -q 'Error Rate'"

check "Monitoring" "Uptime checks configured" \
    "gcloud monitoring uptime-check-configs list --project=$PROJECT_ID --format='value(displayName)' | grep -q Health"

check "Monitoring" "Log sinks configured" \
    "gcloud logging sinks list --project=$PROJECT_ID --format='value(name)' | grep -q security"

check "Monitoring" "Error reporting enabled" \
    "gcloud services list --enabled --project=$PROJECT_ID | grep -q clouderrorreporting"

check "Monitoring" "Custom metrics defined" \
    "gcloud logging metrics list --project=$PROJECT_ID --format='value(name)' | grep -q incident_count"

check "Monitoring" "SLOs defined" \
    "gcloud alpha monitoring services list --project=$PROJECT_ID | grep -q sentinelops" \
    "warning"

echo -e "\n${BLUE}4. High Availability${NC}"
echo "--------------------"

check "HA" "Multi-region deployment" \
    "gcloud run services list --project=$PROJECT_ID --format='value(metadata.name,region)' | grep -c sentinelops | [ \$(cat) -gt 1 ]" \
    "warning"

check "HA" "Database HA configured" \
    "gcloud sql instances describe sentinelops-db-$ENVIRONMENT --project=$PROJECT_ID --format='value(settings.availabilityType)' | grep -q REGIONAL" \
    "warning"

check "HA" "Load balancer configured" \
    "gcloud compute forwarding-rules list --global --project=$PROJECT_ID | grep -q sentinelops"

check "HA" "CDN enabled" \
    "gcloud compute backend-services describe sentinelops-backend-$ENVIRONMENT --global --project=$PROJECT_ID --format='value(enableCdn)' | grep -q True"

echo -e "\n${BLUE}5. Backup & Recovery${NC}"
echo "--------------------"

check "Backup" "Backup buckets exist" \
    "gsutil ls -p $PROJECT_ID | grep -q sentinelops-backups"

check "Backup" "Cross-region replication" \
    "gsutil ls -p $PROJECT_ID | grep -c sentinelops-backups | [ \$(cat) -gt 2 ]" \
    "warning"

check "Backup" "Backup schedule configured" \
    "gcloud scheduler jobs list --location=us-central1 --project=$PROJECT_ID | grep -q backup"

check "DR" "DR documentation exists" \
    "gsutil ls gs://${PROJECT_ID}-sentinelops-critical-$ENVIRONMENT/disaster-recovery/ | grep -q runbook"

echo -e "\n${BLUE}6. Performance${NC}"
echo "--------------"

check "Cache" "Redis cache configured" \
    "gcloud redis instances describe sentinelops-cache-$ENVIRONMENT --region=us-central1 --project=$PROJECT_ID" \
    "warning"

check "Performance" "Autoscaling configured" \
    "gcloud run services describe sentinelops-api --region=us-central1 --project=$PROJECT_ID --format='value(spec.template.metadata.annotations)' | grep -q autoscaling"

check "Performance" "Container resources defined" \
    "gcloud run services describe sentinelops-api --region=us-central1 --project=$PROJECT_ID --format='value(spec.template.spec.containers[0].resources.limits.cpu)' | grep -q ."

echo -e "\n${BLUE}7. CI/CD Pipeline${NC}"
echo "-----------------"

check "CI/CD" "Cloud Build triggers configured" \
    "gcloud builds triggers list --project=$PROJECT_ID | grep -q sentinelops"

check "CI/CD" "Build artifacts bucket exists" \
    "gsutil ls -p $PROJECT_ID | grep -q build-artifacts"

check "Testing" "Test coverage meets threshold" \
    "[ -f coverage.xml ] && grep -o 'line-rate=\"[0-9.]*\"' coverage.xml | grep -o '[0-9.]*' | awk '\$1 >= 0.8'" \
    "warning"

echo -e "\n${BLUE}8. Documentation${NC}"
echo "----------------"

check "Docs" "README exists" \
    "[ -f README.md ]"

check "Docs" "API documentation" \
    "[ -d docs/06-reference/api-reference.md ]"

check "Docs" "Deployment guide" \
    "[ -f docs/03-deployment/production-deployment-guide.md ]"

check "Docs" "Runbooks exist" \
    "[ -d docs/04-operations ]"

echo -e "\n${BLUE}9. Compliance${NC}"
echo "-------------"

check "Compliance" "Security scanning in CI/CD" \
    "grep -q 'security-scan' cloudbuild.yaml"

check "Compliance" "Audit logging enabled" \
    "gcloud logging sinks list --project=$PROJECT_ID | grep -q audit"

check "Compliance" "Data retention configured" \
    "gcloud sql instances describe sentinelops-db-$ENVIRONMENT --project=$PROJECT_ID --format='value(settings.backupConfiguration.transactionLogRetentionDays)' | grep -q ."

echo -e "\n${BLUE}10. Final Checks${NC}"
echo "----------------"

check "DNS" "Domain configured" \
    "gcloud compute addresses describe sentinelops-lb-ip-$ENVIRONMENT --global --project=$PROJECT_ID" \
    "warning"

check "SSL" "SSL certificate provisioned" \
    "gcloud compute ssl-certificates describe sentinelops-ssl-cert-$ENVIRONMENT --global --project=$PROJECT_ID --format='value(managed.status)' | grep -q ACTIVE" \
    "warning"

check "Budget" "Budget alerts configured" \
    "gcloud billing budgets list --billing-account=\$(gcloud beta billing projects describe $PROJECT_ID --format='value(billingAccountName)') | grep -q $PROJECT_ID" \
    "warning"

# Summary
echo -e "\n${BLUE}===============================================${NC}"
echo -e "${BLUE}Production Readiness Check Summary${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "Total checks: $((PASSED + FAILED + WARNINGS))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "\n${GREEN}✓ All production readiness checks passed!${NC}"
        echo "Your deployment is ready for production."
    else
        echo -e "\n${YELLOW}⚠ Production readiness checks passed with warnings.${NC}"
        echo "Review warnings before proceeding to production."
    fi
    exit 0
else
    echo -e "\n${RED}✗ Production readiness checks failed.${NC}"
    echo "Please fix the failed checks before deploying to production."
    exit 1
fi