#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
GITHUB_REPO="${2:-}"
GITHUB_OWNER="${3:-}"
ENVIRONMENT="${4:-dev}"

if [ -z "$PROJECT_ID" ] || [ -z "$GITHUB_REPO" ]; then
    echo "Usage: $0 <PROJECT_ID> <GITHUB_REPO> [GITHUB_OWNER] [ENVIRONMENT]"
    echo "Example: $0 my-project sentinelops myusername dev"
    exit 1
fi

echo "Setting up Cloud Build for project: $PROJECT_ID"

# Enable Cloud Build API
echo "Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com --project="$PROJECT_ID"
gcloud services enable containerregistry.googleapis.com --project="$PROJECT_ID"
gcloud services enable sourcerepo.googleapis.com --project="$PROJECT_ID"

# Grant Cloud Build permissions
echo "Granting Cloud Build service account permissions..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
CLOUD_BUILD_SA="$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"

for role in \
    "roles/run.admin" \
    "roles/iam.serviceAccountUser" \
    "roles/storage.admin" \
    "roles/container.developer" \
    "roles/artifactregistry.writer" \
    "roles/cloudsql.client" \
    "roles/secretmanager.secretAccessor"
do
    echo "Granting $role..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$CLOUD_BUILD_SA" \
        --role="$role" \
        --condition=None
done

# Create Cloud Build trigger for main branch
echo "Creating Cloud Build trigger for main branch..."
gcloud builds triggers create github \
    --repo-name="$GITHUB_REPO" \
    --repo-owner="$GITHUB_OWNER" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml" \
    --description="Deploy to production on push to main" \
    --substitutions="_ENVIRONMENT=production,_DEPLOY_REGION=us-central1" \
    --project="$PROJECT_ID" || echo "Main trigger already exists"

# Create Cloud Build trigger for develop branch
echo "Creating Cloud Build trigger for develop branch..."
gcloud builds triggers create github \
    --repo-name="$GITHUB_REPO" \
    --repo-owner="$GITHUB_OWNER" \
    --branch-pattern="^develop$" \
    --build-config="cloudbuild.yaml" \
    --description="Deploy to staging on push to develop" \
    --substitutions="_ENVIRONMENT=staging,_DEPLOY_REGION=us-central1" \
    --project="$PROJECT_ID" || echo "Develop trigger already exists"

# Create Cloud Build trigger for pull requests
echo "Creating Cloud Build trigger for pull requests..."
gcloud builds triggers create github \
    --repo-name="$GITHUB_REPO" \
    --repo-owner="$GITHUB_OWNER" \
    --pull-request-pattern="^.*" \
    --build-config="cloudbuild.yaml" \
    --description="Run tests on pull requests" \
    --comment-control=COMMENTS_ENABLED \
    --substitutions="_ENVIRONMENT=test,_DEPLOY_REGION=us-central1" \
    --project="$PROJECT_ID" || echo "PR trigger already exists"

# Create bucket for build artifacts
echo "Creating bucket for build artifacts..."
gsutil mb -p "$PROJECT_ID" -l us-central1 "gs://${PROJECT_ID}-build-artifacts" || echo "Bucket already exists"

# Set up build notifications
echo "Setting up build notifications..."
gcloud pubsub topics create cloud-builds --project="$PROJECT_ID" || echo "Topic already exists"

# Create notification channel for build failures
gcloud pubsub subscriptions create build-failures \
    --topic=cloud-builds \
    --push-endpoint="https://sentinelops-communication-${ENVIRONMENT}.run.app/webhooks/build-notification" \
    --project="$PROJECT_ID" || echo "Subscription already exists"

echo "Cloud Build setup complete!"
echo "Next steps:"
echo "1. Connect your GitHub repository in the Cloud Console"
echo "2. Authorize Cloud Build to access your repository"
echo "3. Update cloudbuild.yaml with your specific build steps"