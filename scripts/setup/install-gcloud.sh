#!/bin/bash
# Script to install Google Cloud SDK on macOS

echo "Installing Google Cloud SDK for macOS..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Installing via official method..."
    curl https://sdk.cloud.google.com | bash
else
    echo "Installing Google Cloud SDK via Homebrew..."
    brew install --cask google-cloud-sdk
fi

echo ""
echo "After installation completes:"
echo "1. Restart your terminal or run: source ~/.zshrc (or ~/.bash_profile)"
echo "2. Run: gcloud init"
echo "3. Authenticate with: gcloud auth login"
echo "4. Set project: gcloud config set project [PROJECT_ID]"
echo ""
echo "To claim hackathon credits:"
echo "Visit: https://docs.google.com/forms/d/e/1FAIpQLSeqzYFwqW5IyHD4wipyDxMrs1Idr91Up7S4PQO1ue058oYuTg/viewform"
