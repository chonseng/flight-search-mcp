"""Installation script for Google Flights Scraper."""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main installation process."""
    print("🛫 Google Flights Scraper Installation")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install Python dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Install Playwright browsers
    if not run_command("playwright install chromium", "Installing Playwright browsers"):
        print("❌ Failed to install Playwright browsers")
        sys.exit(1)
    
    # Test installation
    print("\n🧪 Testing installation...")
    try:
        import playwright
        import typer
        import loguru
        print("✅ All dependencies imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    
    print("\n🎉 Installation completed successfully!")
    print("\nQuick start:")
    print("  python main.py example  # View usage examples")
    print("  python main.py scrape LAX NYC 2025-07-01  # Basic search")
    print("  python example.py  # Run example script")
    print("\nFor more information, see README.md")


if __name__ == "__main__":
    main()