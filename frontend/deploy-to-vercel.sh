#!/bin/bash

# SentinelOps UI - Quick Vercel Deployment Script

echo "🚀 SentinelOps UI - Vercel Deployment"
echo "===================================="

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Must run from the frontend directory"
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm i -g vercel
fi

# Create production environment file if it doesn't exist
if [ ! -f ".env.production" ]; then
    echo "📝 Creating .env.production from .env.example..."
    cp .env.example .env.production
    echo ""
    echo "⚠️  Please update .env.production with your production URLs:"
    echo "   - NEXT_PUBLIC_API_URL (your Cloud Run API endpoint)"
    echo "   - NEXT_PUBLIC_WEBSOCKET_URL (your WebSocket endpoint)"
    echo ""
    echo "Press Enter to continue after updating .env.production..."
    read
fi

# Create vercel.json if it doesn't exist
if [ ! -f "vercel.json" ]; then
    echo "📄 Creating vercel.json..."
    cat > vercel.json << 'EOF'
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_WEBSOCKET_URL": "@websocket_url",
    "NEXT_PUBLIC_API_URL": "@api_url",
    "NEXT_PUBLIC_ENABLE_WEBSOCKET": "true",
    "NEXT_PUBLIC_ENABLE_OFFLINE_MODE": "true",
    "NEXT_PUBLIC_ENABLE_MESSAGE_QUEUE": "true"
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Credentials", "value": "true" },
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,OPTIONS,PATCH,DELETE,POST,PUT" },
        { "key": "Access-Control-Allow-Headers", "value": "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version" }
      ]
    }
  ]
}
EOF
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the project locally first to catch any errors
echo "🔨 Building project..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please fix errors before deploying."
    exit 1
fi

echo ""
echo "✅ Build successful!"
echo ""
echo "🚀 Deploying to Vercel..."
echo ""

# Deploy to Vercel
vercel --prod

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Set environment variables in Vercel dashboard:"
echo "   - NEXT_PUBLIC_API_URL"
echo "   - NEXT_PUBLIC_WEBSOCKET_URL"
echo "2. Configure custom domain (optional)"
echo "3. Enable Vercel Analytics (recommended)"
echo ""
echo "🔗 Your app should be live at the URL provided above!"
