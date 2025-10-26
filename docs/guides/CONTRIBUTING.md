# Contributing Guide

Thank you for contributing to the Cap Table Generator!

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a virtual environment
4. Install dependencies (see DEVELOPMENT_SETUP.md)

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring

### 2. Make Changes

- Follow code style guidelines
- Write tests for new features
- Update documentation
- Keep commits focused

### 3. Run Tests

```bash
# Backend tests
pytest tests/

# Frontend tests (if applicable)
cd webapp/frontend && npm test

# Type checking
mypy src/ webapp/backend/

# Linting
pylint src/ webapp/backend/
black --check src/ webapp/backend/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new formula resolution method"
```

Commit messages should:
- Use conventional commits format
- Be clear and descriptive
- Reference issues when applicable

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

## Code Standards

### Python

- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for all public APIs
- Keep functions focused and small
- Use meaningful variable names

### TypeScript

- Follow ESLint configuration
- Use TypeScript types
- Write JSDoc comments
- Follow React best practices

## Testing Requirements

- All new code must have tests
- Maintain or increase coverage
- Include unit and integration tests
- Test error cases

## Documentation

- Update relevant docs for new features
- Add examples for public APIs
- Keep architecture diagrams current
- Update API reference

## Pull Request Process

1. Ensure all tests pass
2. Update CHANGELOG.md
3. Request review from maintainers
4. Address feedback
5. Merge after approval

## Questions?

Open an issue or contact maintainers.

