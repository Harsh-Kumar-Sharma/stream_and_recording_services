"""Validate the local Python version before dependency installation."""

from __future__ import annotations

import platform
import sys


MIN_VERSION = (3, 11)
MAX_EXCLUSIVE_VERSION = (3, 14)


def main() -> int:
    version = sys.version_info[:3]
    if version < MIN_VERSION or version >= MAX_EXCLUSIVE_VERSION:
        print(
            "Unsupported Python version: "
            f"{platform.python_version()}. Use Python 3.11, 3.12, or 3.13 for this project."
        )
        print(
            "Python 3.14 may force pydantic-core/native dependencies to build from source "
            "on Windows and fail without Visual Studio C++ Build Tools."
        )
        return 1

    print(f"Python version OK: {platform.python_version()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

