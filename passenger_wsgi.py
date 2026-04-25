import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
def _find_project_dir(base_dir: Path) -> Path:
    candidates = [
        base_dir,
        base_dir / "bump",
        base_dir / "app",
        base_dir / "src",
    ]
    for candidate in candidates:
        if (candidate / "manage.py").exists() and (candidate / "config" / "wsgi.py").exists():
            return candidate
    for manage_file in base_dir.rglob("manage.py"):
        candidate = manage_file.parent
        if (candidate / "config" / "wsgi.py").exists():
            return candidate
    return base_dir

PROJECT_DIR = _find_project_dir(BASE_DIR)

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from config.wsgi import application
