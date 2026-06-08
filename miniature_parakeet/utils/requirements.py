"""Requirements utilities."""

import os
from typing import List


def get_required_packages() -> List[str]:
    """Get list of required packages."""
    return [
        "langgraph",
        "langchain",
        "fastmcp",
    ]


def update_requirements() -> bool:
    """Update requirements.txt with required packages."""
    # Get project root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    requirements_path = os.path.join(project_root, "requirements.txt")

    required = get_required_packages()

    # Read existing requirements
    existing = []
    if os.path.exists(requirements_path):
        with open(requirements_path, "r") as f:
            existing = [line.strip() for line in f if line.strip()]

    # Add missing packages
    updated = set(existing) | set(required)

    # Write back
    with open(requirements_path, "w") as f:
        for package in sorted(updated):
            f.write(f"{package}\n")

    return True


def check_requirements() -> List[str]:
    """Check if required packages are installed."""
    required = get_required_packages()
    missing = []

    for package in required:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)

    return missing
