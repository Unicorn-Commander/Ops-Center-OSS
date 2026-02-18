# LLM Hub Development Workflow

This document outlines the development workflow for the unified LLM Management system (Phase 1).

## Branch Strategy

### Branch Hierarchy

```
main (production)
  └── staging (pre-production)
        └── feature/llm-hub (main development)
              ├── feature/llm-hub-ui (UI components)
              ├── feature/llm-hub-api (Backend APIs)
              ├── feature/llm-hub-db (Database changes)
              └── feature/llm-hub-tests (Test suite)
```

### Branch Purposes

- **main**: Production-ready code, protected, requires approval
- **staging**: Pre-production testing, merged from feature/llm-hub
- **feature/llm-hub**: Main development branch for LLM Hub
- **feature/llm-hub-***: Feature-specific branches for parallel work

### Branch Protection Rules

**main**:
- Requires 2 approvals
- CI/CD must pass
- No direct pushes
- Must be up-to-date with staging

**staging**:
- Requires 1 approval
- CI/CD must pass
- No direct pushes

**feature/llm-hub**:
- Requires 1 approval
- CI/CD must pass
- Can merge feature branches

## Development Workflow

### 1. Starting New Work

```bash
# Update main development branch
git checkout feature/llm-hub
git pull origin feature/llm-hub

# Create feature branch
git checkout -b feature/llm-hub-provider-keys

# Make changes
# ... edit files ...

# Commit with conventional commits
git add .
git commit -m "feat(llm): add provider key encryption"

# Push to remote
git push origin feature/llm-hub-provider-keys
```

### 2. Creating Pull Request

Create PR from your branch → `feature/llm-hub`:

**PR Template**:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing Checklist
- [ ] Unit tests pass (pytest)
- [ ] Frontend tests pass (Jest)
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Database migrations tested
- [ ] Rollback tested

## Feature Flag Status
- [ ] Feature flag configured
- [ ] Rollout percentage set
- [ ] Whitelist users defined

## Documentation
- [ ] Code comments added
- [ ] API docs updated
- [ ] User docs updated

## Screenshots (if UI changes)
[Attach screenshots]

## Breaking Changes
[List any breaking changes]

## Rollback Plan
[Describe rollback procedure]
```

### 3. Code Review Process

**Reviewer Checklist**:
- [ ] Code follows style guide
- [ ] Tests cover new code
- [ ] No hardcoded secrets
- [ ] Error handling adequate
- [ ] Logging appropriate
- [ ] Performance acceptable
- [ ] Security reviewed
- [ ] Documentation complete

**Review Guidelines**:
- Respond within 24 hours
- Provide constructive feedback
- Test locally if significant changes
- Approve only if all checks pass

### 4. Merging to Staging

```bash
# After PR approved and merged to feature/llm-hub
git checkout staging
git pull origin staging

# Merge feature branch
git merge feature/llm-hub

# Run integration tests
docker compose -f docker-compose.staging.yml up -d
./backend/scripts/test_integration.sh

# Push to staging
git push origin staging
```

### 5. Production Deployment

```bash
# After staging validation complete
git checkout main
git pull origin main

# Merge staging
git merge staging

# Tag release
git tag -a v1.0.0-llm-hub -m "LLM Hub Phase 1 release"

# Push to production
git push origin main
git push origin v1.0.0-llm-hub
```

## Testing Checklist

### Unit Tests

```bash
cd backend
pytest tests/test_feature_flags.py -v
pytest tests/test_llm_hub_api.py -v
pytest tests/ --cov=. --cov-report=html
```

**Requirements**:
- Code coverage > 80%
- All tests pass
- No flaky tests

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

**Requirements**:
- Component tests pass
- Integration tests pass
- E2E tests pass (if applicable)

### Integration Tests

```bash
cd backend
./scripts/test_integration.sh
```

**Tests**:
- API endpoints functional
- Database migrations successful
- Feature flags work correctly
- Old pages still accessible
- Authentication working
- CSRF protection active

### Manual Testing

**Test Scenarios**:
1. **Feature Flag Off**: Old pages work normally
2. **Feature Flag On (0% rollout)**: Old pages work, new hub not visible
3. **Feature Flag On (whitelist user)**: New hub visible and functional
4. **Feature Flag On (100% rollout)**: All users see new hub
5. **Rollback**: Disable flag, old pages work immediately

### Database Migration Testing

```bash
# Apply migration
./backend/scripts/setup_test_db.sh

# Verify tables created
docker exec unicorn-postgresql psql -U unicorn -d unicorn_test -c "\dt"

# Test rollback
docker exec unicorn-postgresql psql -U unicorn -d unicorn_test -f /migrations/rollback_llm_management_tables.sql

# Verify rollback successful
docker exec unicorn-postgresql psql -U unicorn -d unicorn_test -c "\dt"
```

## Development Environment Setup

### 1. Local Development

```bash
# Clone repository
git clone https://github.com/Unicorn-Commander/UC-Cloud.git
cd UC-Cloud/services/ops-center

# Checkout development branch
git checkout feature/llm-hub

# Copy development environment
cp .env.development .env

# Setup test database
./backend/scripts/setup_test_db.sh

# Start services
docker compose -f docker-compose.dev.yml up -d

# Install dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

cd ../frontend
npm install
```

### 2. Running Development Server

```bash
# Backend (with hot reload)
cd backend
uvicorn server:app --reload --port 8084

# Frontend (with hot reload)
cd frontend
npm run dev
```

### 3. Environment Variables

Use `.env.development` for local development:
- Feature flags enabled
- Test database configured
- Debug logging enabled
- CSRF disabled for local testing
- Mock external services

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(llm): add unified LLM management hub

Replaces 4 separate pages with single unified interface.
Includes provider keys, model catalog, routing, analytics.

BREAKING CHANGE: Old /admin/llm-* routes deprecated
```

```
fix(api): correct provider key encryption

Fixed bug where provider keys weren't properly encrypted
before storing in database.

Closes #123
```

## Code Quality Standards

### Python (Backend)

```bash
# Linting
ruff check .

# Type checking
mypy .

# Formatting
black .

# Security scanning
bandit -r .
```

**Standards**:
- Follow PEP 8
- Type hints required
- Docstrings for all functions
- No security vulnerabilities

### JavaScript/TypeScript (Frontend)

```bash
# Linting
npm run lint

# Type checking
npm run typecheck

# Formatting
npm run format
```

**Standards**:
- Follow ESLint config
- TypeScript strict mode
- JSDoc comments
- Accessible UI (WCAG 2.1 AA)

## Monitoring Development Progress

### Feature Flag Dashboard

Check current rollout status:
```bash
curl http://localhost:8084/api/v1/features/unified_llm_hub
```

### Logs

Monitor feature flag usage:
```bash
docker logs ops-center-direct | grep LLM_HUB
```

### Metrics

Track adoption:
- Page views (old vs new)
- Error rates
- Response times
- User feedback

## Troubleshooting

### Feature Flag Not Working

1. Check environment variables loaded:
   ```bash
   docker exec ops-center-direct printenv | grep FEATURE_
   ```

2. Verify user in whitelist:
   ```python
   from config.feature_flags import FeatureFlags
   print(FeatureFlags.is_enabled("unified_llm_hub", "user@example.com"))
   ```

3. Check logs:
   ```bash
   docker logs ops-center-direct | grep feature_flags
   ```

### Database Migration Failed

1. Check current state:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt"
   ```

2. Rollback migration:
   ```bash
   ./backend/scripts/rollback_migration.sh
   ```

3. Re-apply migration:
   ```bash
   ./backend/scripts/setup_test_db.sh
   ```

### Tests Failing

1. Clear test database:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -c "DROP DATABASE unicorn_test;"
   docker exec unicorn-postgresql psql -U unicorn -c "CREATE DATABASE unicorn_test;"
   ```

2. Re-run migrations:
   ```bash
   ./backend/scripts/setup_test_db.sh
   ```

3. Clear pytest cache:
   ```bash
   rm -rf .pytest_cache
   pytest --cache-clear
   ```

## Resources

- [Architecture Document](./LLM_HUB_ARCHITECTURE.md)
- [Database Schema](./LLM_HUB_DATABASE_SCHEMA.md)
- [API Documentation](./LLM_HUB_API_DOCS.md)
- [Rollback Plan](../deployments/ROLLBACK_PLAN.md)
- [Testing Guide](./TESTING_GUIDE.md)

## Questions?

Contact the platform team:
- Slack: #llm-hub-dev
- Email: platform-team@unicorncommander.ai
