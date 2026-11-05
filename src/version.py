import os


def get_version() -> str:
    """Read application version from the VERSION file (single source of truth, also used by meson)."""
    version_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')
    try:
        with open(version_path, 'r') as f:
            return f.read().strip()
    except OSError:
        return 'unknown'
