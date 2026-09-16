"""Resolve source/config locations without depending on the working directory."""
from pathlib import Path

AGENTS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = AGENTS_ROOT.parent
