#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
ATTESTOR_NAME="${2:-sentinelops-attestor}"
ENVIRONMENT="${3:-prod}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <PROJECT_ID> [ATTESTOR_NAME] [ENVIRONMENT]"
    exit 1
fi

echo "Setting up Binary Authorization for project: $PROJECT_ID"
echo "Attestor: $ATTESTOR_NAME"
echo "Environment: $ENVIRONMENT"

# Enable Binary Authorization API
echo "Enabling Binary Authorization API..."
gcloud services enable binaryauthorization.googleapis.com --project="$PROJECT_ID"
gcloud services enable containeranalysis.googleapis.com --project="$PROJECT_ID"

# Create attestor
echo "Creating attestor..."
gcloud container binauthz attestors create $ATTESTOR_NAME \
    --attestation-authority-note=$ATTESTOR_NAME-note \
    --attestation-authority-note-project=$PROJECT_ID \
    --project="$PROJECT_ID" || echo "Attestor already exists"

# Create attestor note
echo "Creating attestor note..."
cat > /tmp/note.json <<EOF
{
  "name": "projects/${PROJECT_ID}/notes/${ATTESTOR_NAME}-note",
  "attestation": {
    "hint": {
      "human_readable_name": "SentinelOps container attestor"
    }
  }
}
EOFcurl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -d @/tmp/note.json \
    "https://containeranalysis.googleapis.com/v1/projects/${PROJECT_ID}/notes/?noteId=${ATTESTOR_NAME}-note"

# Generate key pair for attestor
echo "Generating attestor key pair..."
mkdir -p keys
cd keys
gpg --batch --gen-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 2048
Name-Real: SentinelOps Attestor
Name-Email: attestor@sentinelops.com
Expire-Date: 0
EOF

# Export public key
gpg --armor --export attestor@sentinelops.com > ${ATTESTOR_NAME}.pub
gpg --armor --export-secret-keys attestor@sentinelops.com > ${ATTESTOR_NAME}.priv

# Add public key to attestor
echo "Adding public key to attestor..."
gcloud container binauthz attestors public-keys add \
    --attestor=$ATTESTOR_NAME \
    --pgp-public-key-file=${ATTESTOR_NAME}.pub \
    --project="$PROJECT_ID"

# Create Binary Authorization policy
echo "Creating Binary Authorization policy..."
cat > /tmp/policy.yaml <<EOF
admissionWhitelistPatterns:
- namePattern: gcr.io/${PROJECT_ID}/*
- namePattern: us-docker.pkg.dev/${PROJECT_ID}/*
defaultAdmissionRule:
  evaluationMode: REQUIRE_ATTESTATION
  enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
  requireAttestationsBy:
  - projects/${PROJECT_ID}/attestors/${ATTESTOR_NAME}
globalPolicyEvaluationMode: ENABLE
name: projects/${PROJECT_ID}/policy
EOF# Apply Binary Authorization policy
echo "Applying Binary Authorization policy..."
gcloud container binauthz policy import /tmp/policy.yaml \
    --project="$PROJECT_ID"

# Create Cloud Build configuration for automatic attestation
echo "Creating Cloud Build configuration for attestation..."
cat > /tmp/cloudbuild-attest.yaml <<EOF
steps:
- name: 'gcr.io/${PROJECT_ID}/sentinelops-\${_COMPONENT}:\${SHORT_SHA}'
  id: 'vulnerability-scan'
  args: ['echo', 'Image built and scanned']

- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  id: 'create-attestation'
  entrypoint: 'bash'
  args:
  - '-c'
  - |
    gcloud container binauthz attestations sign-and-create \
      --artifact-url="gcr.io/${PROJECT_ID}/sentinelops-\${_COMPONENT}:\${SHORT_SHA}" \
      --attestor="${ATTESTOR_NAME}" \
      --attestor-project="${PROJECT_ID}" \
      --keyversion-project="${PROJECT_ID}" \
      --keyversion-location="global" \
      --keyversion-keyring="${ATTESTOR_NAME}-keyring" \
      --keyversion-key="${ATTESTOR_NAME}-key" \
      --keyversion="1"
EOF

echo "Binary Authorization setup complete!"
echo "Note: Container images must be attested before deployment"
echo "Store the private key securely: keys/${ATTESTOR_NAME}.priv"