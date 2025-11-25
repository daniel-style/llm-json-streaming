# GitHub Actions Workflows

This directory contains the GitHub Actions workflows for the `llm-json-streaming` project.

## Workflows Overview

### `release.yml` - Package Release

**Triggers:**
- Git tags starting with `v` (e.g., `v0.1.0`)
- Manual workflow dispatch

**Features:**
- Package building and validation
- Publishing to PyPI (for tags)
- Publishing to Test PyPI (manual)
- GitHub Release creation
- Artifact management

## Required Secrets

To enable full functionality, configure these secrets in your GitHub repository:

### For Publishing to PyPI

1. **PyPI API Token**
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token
   - Environment: `pypi`

2. **Test PyPI API Token** (optional)
   - Name: `TEST_PYPI_API_TOKEN`
   - Value: Your Test PyPI API token
   - Environment: `test-pypi`

### For Code Coverage (optional)

3. **Codecov Token** (optional)
   - Name: `CODECOV_TOKEN`
   - Value: Your Codecov token
   - Configure in Codecov settings for automatic upload

## Setup Instructions

### 1. Configure PyPI Tokens

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Generate an API token with package publishing permissions
3. Add the token as a repository secret:
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI token

### 2. Configure Test PyPI (Optional)

1. Go to [Test PyPI](https://test.pypi.org/)
2. Generate an API token
3. Add as `TEST_PYPI_API_TOKEN` secret

### 3. Configure Codecov (Optional)

1. Go to [Codecov](https://codecov.io/)
2. Connect your GitHub repository
3. Copy the upload token
4. Add as `CODECOV_TOKEN` secret

## Usage

### Running Tests Locally (Optional)

While CI checks are simplified, you can still run quality checks locally:

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Optional: Run quality checks
uv run black llm_json_streaming tests
uv run isort llm_json_streaming tests
uv run mypy llm_json_streaming
uv run ruff check llm_json_streaming tests
```

### Publishing Releases

#### Automatic Release (Tag-based)

```bash
# Create and push a tag
git tag v0.1.1
git push origin v0.1.1

# This will automatically:
# 1. Build and test the package
# 2. Publish to PyPI
# 3. Create a GitHub Release
```

#### Manual Release

1. Go to Actions tab in GitHub
2. Select "Release" workflow
3. Click "Run workflow"
4. Configure:
   - Version (e.g., `0.1.1`)
   - Test PyPI (true/false)
5. Run workflow

### Monitoring Workflows

- **Actions Tab**: View workflow runs and logs
- **Release Management**: Track releases and versions

## Troubleshooting

### Common Issues

1. **Publishing Failures**
   - Verify PyPI token is correct and has proper permissions
   - Check if version already exists on PyPI
   - Ensure package passes all checks before publishing

2. **Build Failures**
   - Check workflow logs for specific error messages
   - Ensure all dependencies are properly declared in `pyproject.toml`
   - Verify package metadata in `pyproject.toml`

### Debugging Steps

1. **Download Artifacts**: Workflow artifacts include build files and logs
2. **Reproduce Locally**: Use the same commands that fail in CI
3. **Check Dependencies**: Ensure `uv sync --dev` works locally

## Best Practices

1. **Version Management**: Use semantic versioning
2. **Documentation**: Keep CHANGELOG updated for releases
3. **Local Testing**: Test package building locally before release

## Security Considerations

- API tokens are stored as encrypted secrets
- Workflows run in isolated environments
- No external API calls in workflows (except package publishing)