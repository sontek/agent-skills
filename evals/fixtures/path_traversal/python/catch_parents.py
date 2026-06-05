import sys
from pathlib import Path

# Counts three directories up to find the repo root — breaks silently the day
# this file moves to a different depth (the wrong path may still exist).
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))
