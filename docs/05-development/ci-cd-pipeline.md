# CI/CD Pipeline Documentation

## Overview

The SentinelOps project uses a comprehensive CI/CD pipeline that ensures code quality, security, and reliable deployments. The pipeline is implemented using GitHub Actions for continuous integration and Google Cloud Build for deployment.

## Pipeline Components

### 1. GitHub Actions Workflows

#### Main CI/CD Pipeline (`.github/workflows/ci.yml`)
- **Triggers**: Push to main/develop branches, pull requests
- **Jobs**:
  - **Linting**: Code quality checks (Black, isort, Flake8, MyPy, Ruff)
  - **Security**: Vulnerability scanning (Bandit, Safety, pip-audit)
  - **Unit Tests**: Python 3.11 and 3.12 with coverage requirements (90%)
  - **Integration Tests**: Tests requiring external services
  - **Web Interface Tests**: Next.js application testing (ui directory)
  - **Docker Build**: Multi-agent containerization
  - **Performance Tests**: Benchmark testing
  - **E2E Tests**: Full system integration testing
  - **Deployment**: Staging (develop branch) and Production (main branch)

#### Pull Request Checks (`.github/workflows/pr-checks.yml`)
- **PR Validation**: Branch naming, commit message format
- **Size Check**: PR complexity assessment
- **Dependency Review**: Security vulnerability scanning
- **Coverage Diff**: Test coverage comparison
- **Documentation Check**: Ensures docs are updated
- **API Compatibility**: OpenAPI spec validation

#### Nightly Tests (`.github/workflows/nightly.yml`)
- **Chaos Engineering**: Fault injection testing
- **Load Testing**: Performance under high load
- **Stress Testing**: Resource exhaustion scenarios
- **Security Deep Scan**: Comprehensive vulnerability assessment
- **Compatibility Testing**: Multi-OS and Python version testing
- **Long-Running Tests**: Extended duration tests
- **Memory Leak Detection**: Memory usage analysis

#### Release Pipeline (`.github/workflows/release.yml`)
- **Tag Validation**: Semantic versioning enforcement
- **Build & Test**: Full test suite execution
- **Docker Images**: Multi-registry publishing
- **GitHub Release**: Automated release notes
- **PyPI Publishing**: Python package distribution
- **Multi-Region Deployment**: Global rollout
- **Post-Release Verification**: Smoke tests

### 2. Google Cloud Build

The `cloudbuild.yaml` configuration includes:
- Code quality checks and linting
- Security scanning with artifact storage
- Unit and integration testing
- Parallel Docker image builds for all agents
- Performance testing (main branch only)
- Environment-based deployment (staging/production)
- Post-deployment smoke tests

### 3. Local Development Tools

The `Makefile` provides local CI/CD commands:
```bash
make ci              # Run full CI pipeline locally
make pre-commit      # Pre-commit checks
make security        # Security scans
make test-unit       # Unit tests only
make test-integration # Integration tests
make test-coverage   # Coverage report
make docker-build    # Build all images
make deploy-staging  # Deploy to staging
make deploy-prod     # Deploy to production
```

## Security Measures

1. **Dependency Scanning**: Regular vulnerability checks
2. **Code Analysis**: Static security analysis with Bandit
3. **Secret Management**: No hardcoded secrets, uses GitHub Secrets
4. **Access Control**: Environment-based deployment approvals
5. **Container Scanning**: Trivy for Docker image vulnerabilities

## Quality Gates

- **Code Coverage**: Minimum 90% coverage required
- **Linting**: All code must pass style checks
- **Type Checking**: Full MyPy compliance
- **Security**: No high/critical vulnerabilities
- **Performance**: Regression detection via benchmarks

## Deployment Strategy

### Staging Deployment
- Triggered on push to `develop` branch
- Single region deployment (us-central1)
- Automated smoke tests

### Production Deployment
- Triggered on push to `main` branch
- Multi-region deployment (us-central1, us-east1, us-west1)
- Requires environment approval
- Blue-green deployment with traffic management
- Automated rollback on failure

### Release Process
1. Create semantic version tag (e.g., v1.2.3)
2. Automated validation and testing
3. Build and publish artifacts
4. Deploy to all production regions
5. Update traffic routing
6. Post-deployment verification

## Monitoring and Notifications

- **Slack Integration**: Build status notifications
- **Artifact Storage**: Test results and coverage reports
- **Performance Tracking**: Benchmark result trending
- **Deployment Metrics**: Success/failure tracking

## Best Practices

1. **Branch Protection**: Main and develop branches protected
2. **PR Reviews**: Required before merging
3. **Commit Standards**: Conventional commits enforced
4. **Test First**: No deployment without passing tests
5. **Incremental Rollout**: Gradual traffic shifting
6. **Rollback Ready**: Quick reversion capability

## Troubleshooting

### Common Issues

1. **Coverage Failure**: Ensure new code has tests
2. **Linting Errors**: Run `make format` locally
3. **Type Errors**: Check MyPy output
4. **Security Vulnerabilities**: Update dependencies
5. **Build Timeouts**: Check for inefficient tests

### Debug Commands

```bash
# Check CI status locally
make ci

# Run specific workflow steps
make lint
make test-unit
make security

# Debug Docker builds
docker build -t test:latest .
```

## Maintenance

- Review and update dependencies monthly
- Monitor CI/CD performance metrics
- Update GitHub Actions versions quarterly
- Review security scan results weekly
- Optimize slow tests and builds
