"""Setup script for Google Flights Scraper."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="google-flights-scraper",
    version="1.0.0",
    author="Flight Scraper Team",
    author_email="contact@flightscraper.com",
    description="A comprehensive web scraper for Google Flights with MCP server support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/flight-scrapper-2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
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
    ],
    keywords="google flights scraper playwright web automation mcp server",
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "mcp": [
            "fastmcp>=0.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flight-scraper=flight_scraper.cli.main:app",
            "flight-scraper-legacy=main:app",
            "flight-scraper-mcp=run_mcp_server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)