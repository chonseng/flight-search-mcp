# Contributing to Flight Search MCP

Thank you for your interest in contributing! This guide covers everything you need to know about our development workflow, code standards, and contribution process.

## 🚀 Quick Setup

### Development Environment

```bash
# Clone and setup
git clone https://github.com/chonseng/flight-search-mcp.git
cd flight-search-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Install Playwright browsers
playwright install chromium

# Verify setup
python verify_installation.py
```

### Verify Your Environment

```bash
# Test core functionality
python -c "from flight_scraper.core import GoogleFlightsScraper; print('✅ Setup complete')"

# Run quick tests
pytest tests/unit/ -v --tb=short
```

## 🔄 Development Workflow

### 1. Branch Strategy

- **`main`**: Production-ready code
- **`develop`**: Integration branch for features
- **`feature/*`**: Individual feature branches
- **`hotfix/*`**: Emergency fixes
- **`release/*`**: Release preparation

### 2. Feature Development

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### 3. Code Quality Checks

Run these checks before committing:

```bash
# Format code
black flight_scraper/ tests/
isort flight_scraper/ tests/

# Lint code
flake8 flight_scraper/ tests/

# Type checking
mypy flight_scraper/

# Security checks
bandit -r flight_scraper/
safety check

# Run tests
pytest tests/unit/ --cov=flight_scraper --cov-fail-under=85
```

### 4. Pre-commit Hooks

We use pre-commit hooks to ensure code quality:

```bash
# Install hooks (done in setup above)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## 📐 Code Quality Standards

### Formatting

- **Black**: Code formatter with 100-character line limit
- **isort**: Import statement sorting

```bash
# Auto-format code
black --line-length=100 flight_scraper/ tests/
isort flight_scraper/ tests/

# Check formatting without changes
black --check --line-length=100 flight_scraper/
isort --check-only flight_scraper/
```

### Linting

- **Flake8**: PEP 8 compliance and error detection
- **Configuration**: See [`pyproject.toml`](pyproject.toml:98)

```ini
# .flake8 settings
[flake8]
max-line-length = 100
ignore = E203, W503, E501
exclude = .git,__pycache__,venv,build,dist
```

### Type Checking

- **MyPy**: Static type analysis required
- **Type hints**: Required for all public APIs

```python
# Example with proper type hints
from typing import List, Optional, Dict, Any
from datetime import date

async def scrape_flights(
    criteria: SearchCriteria,
    headless: bool = True,
    timeout: int = 30000
) -> ScrapingResult:
    """Scrape flights with proper type annotations."""
    pass
```

### Documentation

- **Docstrings**: Required for all public functions and classes
- **Format**: Google-style docstrings

```python
def parse_price(price_text: str) -> Optional[float]:
    """Parse price text into float value.
    
    Args:
        price_text: Raw price text from webpage (e.g., "$299", "€450")
        
    Returns:
        Parsed price as float, or None if parsing fails
        
    Examples:
        >>> parse_price("$299")
        299.0
        >>> parse_price("€450.50")
        450.5
    """
    pass
```

## 🧪 Testing Requirements

### Test Coverage

- **Minimum**: 85% overall coverage
- **Unit tests**: 90%+ coverage required
- **Critical paths**: 95%+ coverage required

### Test Types

#### Unit Tests (Required)
```bash
# Run unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=flight_scraper --cov-report=html
```

#### Integration Tests (Recommended)
```bash
# Test package integration
python tests/integration/test_scraper_integration.py

# Test full system
python tests/integration/test_robust_selectors.py
```

### Writing Tests

#### Unit Test Example
```python
# tests/unit/test_new_feature.py
import pytest
from flight_scraper.core.models import SearchCriteria
from datetime import date

class TestNewFeature:
    """Test suite for new feature."""
    
    def test_search_criteria_validation(self):
        """Test SearchCriteria validation logic."""
        criteria = SearchCriteria(
            origin="NYC",
            destination="LAX",
            departure_date=date(2024, 7, 15)
        )
        assert criteria.origin == "NYC"
        assert criteria.destination == "LAX"
    
    @pytest.mark.parametrize("input_val,expected", [
        ("$299", 299.0),
        ("€450", 450.0),
        ("£200", 200.0),
    ])
    def test_price_parsing(self, input_val, expected):
        """Test price parsing with various currencies."""
        from flight_scraper.utils import parse_price
        result = parse_price(input_val)
        assert result == expected
```

#### Integration Test Example
```python
# tests/integration/test_new_integration.py
import pytest
from flight_scraper.core import GoogleFlightsScraper, SearchCriteria
from datetime import date, timedelta

@pytest.mark.integration
@pytest.mark.browser
async def test_full_workflow():
    """Test complete scraping workflow."""
    criteria = SearchCriteria(
        origin="NYC",
        destination="LAX", 
        departure_date=date.today() + timedelta(days=30),
        max_results=5
    )
    
    async with GoogleFlightsScraper(headless=True) as scraper:
        result = await scraper.scrape_flights(criteria)
        
        assert result.success
        assert len(result.flights) >= 0  # May be 0 if no flights available
        assert result.execution_time > 0
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Fast unit tests
@pytest.mark.integration   # Integration tests  
@pytest.mark.browser      # Tests requiring browser
@pytest.mark.slow         # Slow-running tests
@pytest.mark.network      # Network-dependent tests
@pytest.mark.mcp          # MCP server tests
```

## 🚀 CI/CD Pipeline

### Automated Checks

Our CI pipeline runs on every push and PR:

1. **Code Quality**
   - Black formatting check
   - isort import sorting
   - Flake8 linting
   - MyPy type checking

2. **Security**
   - Bandit security analysis
   - Safety dependency checking

3. **Testing**
   - Unit tests with coverage
   - Multi-Python version testing (3.8-3.12)

4. **Build**
   - Package build verification
   - Installation testing

### Local CI Simulation

```bash
# Run full CI pipeline locally
./scripts/ci-check.sh

# Or individual steps
black --check flight_scraper/ tests/
isort --check-only flight_scraper/ tests/
flake8 flight_scraper/ tests/
mypy flight_scraper/
bandit -r flight_scraper/
safety check
pytest tests/unit/ --cov=flight_scraper --cov-fail-under=85
```

## 📝 Pull Request Process

### 1. Before Submitting

- [ ] All tests pass locally
- [ ] Code coverage ≥ 85%
- [ ] Code formatted with Black and isort
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Security checks pass
- [ ] Documentation updated

### 2. PR Requirements

- **Title**: Use conventional commit format
  ```
  feat: add flight price comparison feature
  fix: resolve selector timeout issue
  docs: update API documentation
  test: add integration tests for data extraction
  ```

- **Description**: Include:
  - What changed and why
  - Testing performed
  - Any breaking changes
  - Related issues

### 3. Review Process

1. Automated checks must pass
2. Code review by maintainers
3. All feedback addressed
4. Approved by at least one maintainer
5. Squash and merge to maintain clean history

### 4. Conventional Commits

Follow conventional commit format for automated changelog:

```bash
# Types
feat: new feature
fix: bug fix
docs: documentation changes
style: formatting changes
refactor: code refactoring
test: test additions/changes
chore: maintenance tasks

# Examples
feat: add round-trip flight search support
fix: handle timeout errors in form handler
docs: update MCP server configuration guide
test: add unit tests for price parsing
refactor: improve selector health monitoring
```

## 🏗️ Architecture Guidelines

### Component Design

- **Single Responsibility**: Each class has one clear purpose
- **Dependency Injection**: Pass dependencies rather than creating them
- **Error Handling**: Comprehensive error handling with fallbacks
- **Async/Await**: Use async patterns for I/O operations

### Code Organization

```
flight_scraper/
├── core/                    # Core business logic
│   ├── scraper.py          # Main orchestrator
│   ├── browser_manager.py  # Browser lifecycle
│   ├── form_handler.py     # Form interactions
│   ├── data_extractor.py   # Data extraction
│   ├── models.py           # Data models
│   └── config.py           # Configuration
├── mcp/                    # MCP server
├── cli/                    # Command-line interface
└── utils.py               # Utilities and selectors
```

### Adding New Features

1. **Models**: Add data models to [`models.py`](flight_scraper/core/models.py:1)
2. **Business Logic**: Add to appropriate core module
3. **Tests**: Add comprehensive unit and integration tests
4. **Documentation**: Update relevant documentation
5. **Examples**: Add usage examples if applicable

## 🐛 Debugging and Troubleshooting

### Development Debugging

```python
# Enable debug logging
import os
from loguru import logger

os.environ['FLIGHT_SCRAPER_LOG_LEVEL'] = 'DEBUG'
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="DEBUG", colorize=True)

# Run with visual debugging
async with GoogleFlightsScraper(headless=False) as scraper:
    result = await scraper.scrape_flights(criteria)
    health = scraper.get_health_report()
    print(f"Health: {health}")
```

### Selector Issues

```bash
# Run selector diagnostics
python tests/diagnostics/test_selector_diagnostics.py

# Check selector health
python -c "
from flight_scraper.utils import ROBUST_SELECTORS
for name, selector in ROBUST_SELECTORS.items():
    print(f'{name}: {len(selector.selectors)} strategies')
"
```

## 🔒 Security Guidelines

### Code Security

- **Input Validation**: Validate all external inputs
- **SQL Injection**: Use parameterized queries (if applicable)
- **XSS Prevention**: Sanitize any HTML content
- **Dependency Management**: Keep dependencies updated

### Scraping Ethics

- **Rate Limiting**: Implement reasonable delays
- **Terms of Service**: Respect website terms
- **Resource Usage**: Monitor and limit resource consumption
- **User Agent**: Use legitimate user agent strings

## 📞 Getting Help

### Resources

- **[DEVELOPMENT.md](DEVELOPMENT.md)**: Detailed technical documentation
- **[README.md](README.md)**: Quick start and basic usage
- **[MCP_SERVER_GUIDE.md](MCP_SERVER_GUIDE.md)**: MCP server details
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)**: Complete testing guide

### Communication

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions
- **Reviews**: Engage constructively in code reviews

### Maintainer Contact

- Review response time: 2-3 business days
- Complex PRs may require additional review time
- Breaking changes require discussion before implementation

---

## 🎯 Contribution Checklist

Before submitting your contribution:

- [ ] Code follows style guidelines (Black, isort, flake8)
- [ ] Type hints added for public APIs
- [ ] Tests added with ≥85% coverage
- [ ] Documentation updated
- [ ] Conventional commit format used
- [ ] All CI checks pass
- [ ] Security scan passes
- [ ] Breaking changes documented

Thank you for contributing to Flight Search MCP! 🚀