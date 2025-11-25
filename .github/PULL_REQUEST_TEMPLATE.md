## 📋 Description

<!-- Describe your changes in detail -->

## 🎯 Type of Change

- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 💥 Breaking change
- [ ] 📚 Documentation update
- [ ] 🛠️ Refactoring
- [ ] ⚡ Performance improvement
- [ ] 🧪 Test improvements

## 🧪 Testing

- [ ] All tests pass locally
- [ ] Added new tests for the changes
- [ ] Manual testing completed

## ✅ Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated if needed
- [ ] CHANGELOG.md updated (for significant changes)
- [ ] No breaking changes (or clearly documented)

## 🔗 Related Issues

<!-- Link any related issues here -->
Closes #

## 📝 Additional Notes

<!-- Any additional context or notes -->

### Testing Commands Used

```bash
# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Code quality checks
uv run black --check llm_json_streaming tests
uv run isort --check-only llm_json_streaming tests
uv run mypy llm_json_streaming
uv run ruff check llm_json_streaming tests
```