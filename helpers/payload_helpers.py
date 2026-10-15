#!/usr/bin/env python3

"""Compatibility imports for older payload-helper usage."""

try:
    from . import *  # noqa: F401,F403
except ImportError:
    from helpers import *  # noqa: F401,F403


if __name__ == "__main__":
    print("Import or copy the helpers you need; this file is not an exploit.")
