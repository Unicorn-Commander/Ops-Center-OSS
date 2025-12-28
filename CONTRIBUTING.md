# Contributing to Ops-Center

First off, thanks for taking the time to contribute!

This document provides guidelines for contributing to Ops-Center. These are guidelines, not rules—use your best judgment and feel free to propose changes to this document.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Issues

- **Bug Reports**: Use the bug report template. Include steps to reproduce, expected behavior, and actual behavior.
- **Feature Requests**: Use the feature request template. Explain the use case and why it would be valuable.
- **Questions**: Use GitHub Discussions for questions about using Ops-Center.

### Before Contributing

1. Check existing issues to see if someone has already reported your bug or requested your feature
2. For significant changes, open an issue first to discuss your approach
3. Fork the repository and create your branch from `main`

## How to Contribute

### Types of Contributions

- **Bug fixes**: Fix something that's broken
- **Features**: Add new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Refactoring**: Improve code quality without changing functionality

### Good First Issues

Look for issues labeled `good first issue` — these are specifically curated for newcomers.

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.10+
- PostgreSQL (or use Docker)
- Redis (or use Docker)

### Local Development

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ops-center.git
cd ops-center

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Copy environment template
cp .env.example .env.auth

# Start supporting services (PostgreSQL, Redis)
docker compose -f docker-compose.direct.yml up -d postgres redis

# Run backend
cd backend
uvicorn server:app --reload --port 8084

# In another terminal, run frontend
npm run dev
```

### Running Tests

```bash
# Frontend tests
npm test

# Backend tests
cd backend
pytest

# Linting
npm run lint
ruff check backend/
```

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Use prefixes:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation
- `refactor/` for refactoring
- `test/` for tests

### 2. Make Your Changes

- Write clear, readable code
- Add tests for new functionality
- Update documentation if needed
- Follow the style guidelines below

### 3. Commit Your Changes

We use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>(<scope>): <description>

# Examples
feat(auth): add Google OAuth provider
fix(billing): correct credit calculation for BYOK users
docs(readme): update installation instructions
refactor(api): simplify user management endpoints
test(llm): add tests for model routing
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

### 5. PR Requirements

- Clear description of changes
- Reference related issues (`Fixes #123`)
- All tests passing
- No linting errors
- Documentation updated (if applicable)
- Changelog entry (for significant changes)

### 6. Review Process

- A maintainer will review your PR
- Address any requested changes
- Once approved, a maintainer will merge

## Style Guidelines

### Python (Backend)

- Follow PEP 8
- Use type hints
- Use `ruff` for linting
- Document public functions with docstrings

```python
async def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Retrieve a user by their ID.

    Args:
        user_id: The unique identifier of the user

    Returns:
        User object if found, None otherwise
    """
    ...
```

### JavaScript/React (Frontend)

- Use functional components with hooks
- Use TypeScript types where possible
- Follow ESLint configuration
- Use meaningful component and variable names

```jsx
// Good
const UserProfile = ({ userId }) => {
  const [user, setUser] = useState(null);
  // ...
};

// Avoid
const UP = ({ id }) => {
  const [u, setU] = useState(null);
  // ...
};
```

### SQL

- Use lowercase for SQL keywords
- Use snake_case for table and column names
- Include comments for complex queries

```sql
-- Get active users with their subscription tier
select u.id, u.email, st.tier_code
from "user" u
join subscription_tiers st on u.subscription_tier_id = st.id
where u.is_active = true;
```

### Commits

- Keep commits focused and atomic
- Write meaningful commit messages
- Reference issues when applicable

## Documentation

- Update README.md for user-facing changes
- Update CLAUDE.md for technical/architectural changes
- Add inline comments for complex logic
- Include JSDoc/docstrings for public APIs

## Testing

### Backend Tests

```python
# tests/test_user_api.py
async def test_get_user_returns_user_details():
    response = await client.get("/api/v1/admin/users/123")
    assert response.status_code == 200
    assert "email" in response.json()
```

### Frontend Tests

```javascript
// src/pages/UserManagement.test.jsx
test('renders user list', async () => {
  render(<UserManagement />);
  await waitFor(() => {
    expect(screen.getByText('Users')).toBeInTheDocument();
  });
});
```

## Community

### Getting Help

- **GitHub Discussions**: For questions and discussions
- **Issues**: For bugs and feature requests
- **Discord**: Join our community server (link in README)

### Recognition

Contributors are recognized in:
- The project's contributors list
- Release notes for significant contributions
- Our community highlights

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to Ops-Center!
