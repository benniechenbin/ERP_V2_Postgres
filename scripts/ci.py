#!/usr/bin/env python3
"""
CI Automation Script for ERP V2 Postgres.
Provides docs-check and version-check tasks.
"""

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

REQUIRED_DOCS = [
    "README.md",
    "ARCHITECTURE.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "pyproject.toml",
]


def check_version() -> bool:
    """Validate project version consistency in pyproject.toml."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    if not pyproject_path.exists():
        print("❌ Error: pyproject.toml not found.", file=sys.stderr)
        return False

    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        print("❌ Error: version tag missing in pyproject.toml.", file=sys.stderr)
        return False

    version = match.group(1)
    # Check valid semver pattern (e.g. 0.1.0, 1.2.3-alpha)
    if not re.match(r"^\d+\.\d+\.\d+(?:-[\w.]+)?$", version):
        print(f"❌ Error: invalid semver format '{version}'.", file=sys.stderr)
        return False

    print(f"✅ Version check passed: pyproject.toml version = {version}")
    return True


def check_docs() -> bool:
    """Validate existence of mandatory governance documentation files."""
    missing = []
    for doc in REQUIRED_DOCS:
        doc_path = ROOT_DIR / doc
        if not doc_path.exists() or doc_path.stat().st_size == 0:
            missing.append(doc)

    if missing:
        print(f"❌ Error: missing or empty required docs: {', '.join(missing)}", file=sys.stderr)
        return False

    print(f"✅ Docs check passed: all {len(REQUIRED_DOCS)} mandatory governance documents exist.")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ci.py [docs-check|version-check]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "version-check":
        success = check_version()
    elif command == "docs-check":
        success = check_docs()
    else:
        print(f"❌ Unknown command: {command}", file=sys.stderr)
        print("Available commands: docs-check, version-check")
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
