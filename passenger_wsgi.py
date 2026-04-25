import os
import sys
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR

if not (BASE_DIR / "config").exists() and (BASE_DIR / "bump" / "config").exists():
    PROJECT_DIR = BASE_DIR / "bump"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config.wsgi import application
