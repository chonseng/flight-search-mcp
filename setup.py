"""Setup script for Flight Search MCP."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
with open(readme_file, "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the requirements file and filter dependencies
requirements_file = Path(__file__).parent / "requirements.txt"
with open(requirements_file, "r", encoding="utf-8") as fh:
    all_requirements = [
        line.strip()
        for line in fh
        if line.strip() and not line.startswith("#") and not line.startswith("-")
    ]

# Separate core and development dependencies
core_requirements = []
dev_requirements = []
doc_requirements = []
mcp_requirements = []

# Development tools that should be in dev extras
dev_tools = {
    "pytest",
    "black",
    "flake8",
    "mypy",
    "isort",
    "safety",
    "bandit",
    "pre-commit",
    "commitizen",
    "build",
    "twine",
}

# Documentation tools
doc_tools = {"sphinx", "sphinx-rtd-theme"}

# MCP specific tools
mcp_tools = {"fastmcp"}

for req in all_requirements:
    req_name = req.split(">=")[0].split("==")[0].split("[")[0]

    if any(tool in req_name for tool in dev_tools):
        dev_requirements.append(req)
    elif any(tool in req_name for tool in doc_tools):
        doc_requirements.append(req)
    elif any(tool in req_name for tool in mcp_tools):
        mcp_requirements.append(req)
    else:
        core_requirements.append(req)

setup(
    name="flight-search-mcp",
    version="1.0.0",
    author="Peter Che",
    author_email="chonseng@berkeley.edu",
    description="A comprehensive flight search scraper with MCP server support and modular architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/chonseng/flight-search-mcp",
    project_urls={
        "Documentation": "https://github.com/chonseng/flight-search-mcp/wiki",
        "Bug Reports": "https://github.com/chonseng/flight-search-mcp/issues",
        "Source": "https://github.com/chonseng/flight-search-mcp",
        "Changelog": "https://github.com/chonseng/flight-search-mcp/blob/main/CHANGELOG.md",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "docs"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Topic :: Office/Business :: Scheduling",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "Framework :: Pydantic",
    ],
    keywords=[
        "google",
        "flights",
        "scraper",
        "playwright",
        "web",
        "automation",
        "mcp",
        "server",
        "travel",
        "booking",
        "airline",
        "price",
        "monitoring",
        "async",
        "browser",
        "selenium",
        "beautifulsoup",
        "data",
        "extraction",
    ],
    python_requires=">=3.8",
    install_requires=core_requirements,
    extras_require={
        "dev": dev_requirements + doc_requirements,
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-benchmark>=4.0.0",
        ],
        "lint": [
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "types-python-dateutil>=2.8.0",
        ],
        "security": [
            "safety>=2.3.0",
            "bandit>=1.7.0",
        ],
        "docs": doc_requirements,
        "mcp": mcp_requirements,
        "build": [
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
        "all": dev_requirements + doc_requirements + mcp_requirements,
    },
    include_package_data=True,
    package_data={
        "flight_scraper": [
            "py.typed",  # Mark as typed package
            "core/selectors/*.json",  # Future selector definitions
            "config/*.yml",  # Future config templates
        ],
    },
    zip_safe=False,
    # Enhanced metadata
    platforms=["any"],
    license="MIT",
    # Test configuration
    test_suite="tests",
    # Additional build configuration
    options={
        "egg_info": {
            "tag_build": "",
            "tag_date": False,
        },
    },
    # Dependency management
    dependency_links=[],
)

# Post-install message
print(
    """
Flight Search MCP installation complete!

Next steps:
1. Install Playwright browsers: playwright install chromium
2. Run tests: pytest tests/
3. Check installation: python -c "import flight_scraper; print('Ready!')"

Documentation: https://github.com/chonseng/flight-search-mcp/wiki
Issues: https://github.com/chonseng/flight-search-mcp/issues

Happy scraping!
"""
)
