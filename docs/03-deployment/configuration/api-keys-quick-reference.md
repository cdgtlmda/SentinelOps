# API Keys Quick Reference for SentinelOps

## After Enabling Billing

Once you've enabled billing in Google Cloud Console, here's how to manage different API keys:

### 1. Google Cloud APIs
**No additional keys needed!**
- The service account key you already have (`service-account-key.json`) provides access to all Google Cloud APIs
- Just need to enable the APIs using: `./scripts/setup/enable-apis.sh`

### 2. External Service APIs

#### Slack Webhook (for notifications)
1. Go to https://api.slack.com/apps
2. Create a new app or use existing
3. Add "Incoming Webhooks" feature
4. Copy the webhook URL
5. Add to `.env`: `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`

#### Email (if using SMTP)
1. For Gmail: Create app-specific password at https://myaccount.google.com/apppasswords
2. Add to `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

#### Chronicle API (optional - if you have access)
1. Get API key from Chronicle console
2. Add to `.env`:
   ```
   CHRONICLE_API_KEY=your-key
   CHRONICLE_CUSTOMER_ID=your-id
   ```

### 3. Storage Best Practices

#### Development
- Store in `.env` file (never commit to git!)
- Use `.env.example` as template

#### Production
- Use Google Secret Manager (after enabling the API)
- Migrate secrets: `python scripts/manage_secrets.py migrate`
- Access in Cloud Run with: `--set-secrets=KEY_NAME=secret-name:latest`

### 4. Which APIs Need Billing?

**Require Billing:**
- ✅ Compute Engine API (for VM management)
- ✅ Cloud Run API (for deployment)
- ✅ Secret Manager API (for production secrets)

**Already Enabled (no billing needed):**
- ✅ BigQuery API
- ✅ Vertex AI API (Gemini)
- ✅ Cloud Storage API
- ✅ Logging API
- ✅ Pub/Sub API

### 5. After Enabling Billing Checklist

1. ✅ Run `./scripts/enable-apis.sh` to enable remaining APIs
2. ✅ Create Slack webhook and add to `.env`
3. ✅ (Optional) Set up email credentials
4. ✅ (Optional) Add any Chronicle API keys
5. ✅ For production: Migrate secrets to Secret Manager

### 6. Testing API Access

After setup, verify everything works:
```bash
# Test Google Cloud APIs
python scripts/check-gcloud-connectivity.py

# Test Slack webhook (if configured)
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"Hello from SentinelOps!"}' \
  $SLACK_WEBHOOK_URL
```

## Important Notes

- **Service Account Key**: Already handles all Google Cloud API authentication
- **Vertex AI (Gemini models)**: Uses Application Default Credentials - no API key needed
- **Billing Required**: Only for Compute Engine, Cloud Run, and Secret Manager APIs
- **Security**: Never commit API keys to git! Use Secret Manager for production
