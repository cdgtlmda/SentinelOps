# Web Interface Architecture

## Overview

SentinelOps includes a modern web interface built with Next.js 15.3, providing real-time security monitoring and management capabilities.

## Directory Structure

The project now uses a modern monorepo structure with the new SentinelOps UI:

### Production Interface (`/frontend/sentinelops-ui`)
- **Status**: Active development
- **Purpose**: Production-ready monorepo with multiple applications
- **Technology Stack**:
  - Next.js 14.2 with App Router
  - TypeScript for type safety
  - TailwindCSS for styling
  - Radix UI for accessible components
  - Turborepo for monorepo management
  - Biome for linting and formatting

### Applications Structure
The sentinelops-ui monorepo contains three main applications:

#### Main Application (`/apps/app`)
- **Port**: 3000 (development)
- **Purpose**: Core SentinelOps security management interface
- **Features**:
  - Real-time incident monitoring
  - Agent status visualization
  - Security dashboard
  - Interactive threat simulation

#### Marketing Website (`/apps/web`)
- **Port**: 3001 (development)
- **Purpose**: Public-facing marketing and documentation site
- **Features**:
  - Product information
  - Documentation portal
  - User onboarding

#### API Integration (`/apps/api`)
- **Purpose**: Backend integration layer
- **Features**:
  - Supabase integration
  - Authentication handling
  - Real-time subscriptions

### Shared Packages (`/packages`)
- **UI Components** (`/packages/ui`): Shadcn-based component library
- **Analytics** (`/packages/analytics`): OpenPanel analytics integration
- **Supabase** (`/packages/supabase`): Database queries and mutations
- **Email** (`/packages/email`): React Email templates
- **Jobs** (`/packages/jobs`): Background job processing
- **KV Storage** (`/packages/kv`): Upstash Redis integration
- **Logger** (`/packages/logger`): Centralized logging

### Legacy Interface (`/frontend` - excluding sentinelops-ui)
- **Status**: Deprecated (maintained for compatibility)
- **Purpose**: Original prototype interface
- **Note**: No new features are being added to this interface

## Production Interface Features

The `/frontend/sentinelops-ui` directory contains the modern web interface with:

### Dashboard Components
- **Real-time Incident Monitoring**: Live incident feed with severity indicators
- **Agent Status Visualization**: Visual representation of all security agents
- **KPI Cards**: Key performance indicators for security metrics
- **Activity Timeline**: Historical view of security events
- **Threat Simulation Interface**: Interactive threat scenario testing

### Navigation Structure
- **Platform**: Core security features and agent management
- **Solutions**: Use-case specific implementations
- **Resources**: Documentation and learning materials
- **Enterprise**: Enterprise-specific features
- **Pricing**: Subscription and billing information

### Technical Implementation
- **Main App Port**: Runs on port 3000 (configurable via PORT environment variable)
- **Marketing Site Port**: Runs on port 3001 for development
- **API Integration**: Connects to backend API on port 8081
- **WebSocket Connection**: Real-time updates via `ws://localhost:8081/ws/dashboard`
- **State Management**: React hooks and context for global state
- **Performance**: Optimized with Next.js production builds and Turborepo caching
- **Monorepo Management**: Turborepo for efficient builds and development

## Migration Guide

If you're currently using the legacy `/frontend` interface:

1. **Install Dependencies**:
   ```bash
   cd frontend/sentinelops-ui
   bun install
   ```

2. **Start the Interface**:
   ```bash
   bun dev        # Starts all applications in development mode
   bun dev:app    # Starts only the main app (port 3000)
   bun dev:web    # Starts only the marketing site (port 3001)

   # Production mode
   bun build && bun start
   ```

3. **Update Configuration**:
   - Update any scripts referencing `/frontend` to use `/frontend/sentinelops-ui`
   - Update CI/CD pipelines to build from the monorepo structure
   - Update deployment configurations for multiple apps

4. **Feature Parity**:
   - All features from the legacy interface are available in the production interface
   - Additional features include enhanced UI components, better performance, and improved developer experience

## Development Guidelines

When contributing to the web interface:

1. **Use the `/frontend/sentinelops-ui` directory** for all new development
2. **Follow the monorepo structure** with shared packages for reusable code
3. **Use the established patterns** for components and styling
4. **Maintain TypeScript type safety** throughout the codebase
5. **Test accessibility** using the built-in accessibility tools
6. **Optimize for performance** with proper code splitting and lazy loading
7. **Use Turborepo** for efficient builds and task running

## Related Documentation

- [Quick Start Guide](../01-getting-started/quick-start.md)
- [Local Development Guide](../05-development/local-development-guide.md)
- [API Reference](../06-reference/api-reference.md)
