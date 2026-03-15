"""Pytest configuration for interview-ui tests.

Adds the interview-ui package directory to sys.path so that
``from client import ...`` and ``from state import ...`` work without
needing an installed package.
"""
import os
import sys

# Add interview-ui/ to path so tests can import client, state, theme directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
