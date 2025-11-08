# Pull Request

## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test improvements

## Related Issue

<!-- Link to the related issue (if applicable) -->

Fixes #(issue number)

## Changes Made

<!-- List the main changes made in this PR -->

-
-
-

## Testing

<!-- Describe the tests you ran to verify your changes -->

### Test Commands Run

```bash
# Example:
make test-fast
make test-cov
make lint
```

### Test Results

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Code coverage maintained/improved (≥85%)
- [ ] Tests pass on all platforms (if applicable)

## Checklist

<!-- Mark completed items with an "x" -->

### Code Quality

- [ ] Code follows the project's style guidelines
- [ ] Code has been formatted with `black` and `isort`
- [ ] No linting errors (ran `make lint` or `flake8`)
- [ ] Type hints added/updated where appropriate
- [ ] Code is well-commented and documented

### Testing

- [ ] Unit tests added/updated for new functionality
- [ ] Integration tests added/updated if needed
- [ ] All tests pass locally (`make test-fast`)
- [ ] Coverage report shows ≥85% coverage (`make test-cov`)
- [ ] Tests run without external API dependencies (mocked)

### Documentation

- [ ] README.md updated (if applicable)
- [ ] CLAUDE.md updated (if applicable)
- [ ] Docstrings added/updated for new functions/classes
- [ ] Comments added for complex logic
- [ ] `docs/` updated (if applicable)

### Configuration

- [ ] `config/` files updated (if applicable)
- [ ] No secrets or API keys committed
- [ ] Environment variables documented (if new ones added)

### Security

- [ ] No security vulnerabilities introduced
- [ ] Dependencies reviewed (if added/updated)
- [ ] Sensitive data handled appropriately

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Performance Impact

<!-- Describe any performance implications of this change -->

- [ ] No significant performance impact
- [ ] Performance improved
- [ ] Performance impact assessed and documented below

<!-- If performance is affected, provide details: -->

## Breaking Changes

<!-- List any breaking changes and migration steps -->

- [ ] No breaking changes
- [ ] Breaking changes documented below

<!-- If breaking changes exist, explain:
- What breaks
- Why it was necessary
- How to migrate existing code
-->

## Deployment Notes

<!-- Any special deployment considerations? -->

- [ ] No special deployment steps required
- [ ] Deployment notes below

<!-- Deployment notes: -->

## Additional Context

<!-- Add any other context about the PR here -->

---

## For Reviewers

### Review Checklist

- [ ] Code is clear and maintainable
- [ ] Tests are comprehensive and meaningful
- [ ] Documentation is accurate and complete
- [ ] No obvious bugs or edge cases missed
- [ ] Performance considerations addressed
- [ ] Security implications considered

### CI/CD Status

<!-- GitHub Actions will automatically run. Ensure all checks pass. -->

- ✅ Lint checks
- ✅ Unit tests (all platforms)
- ✅ Integration tests
- ✅ Coverage ≥ 85%
- ✅ Security scan

---

**Thank you for contributing to Aegis!** 🛡️
