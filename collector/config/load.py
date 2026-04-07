from pathlib import Path

import yaml

from utils import project_root


def _load_config() -> dict:
    for path in [
        Path("config.yaml"),
        Path("config.yml"),
        Path("/etc/pgwarden/config.yaml"),
        Path(f"{project_root}/../config.yaml")
    ]:
        if path.exists():
            with path.open(encoding="utf-8") as f:
                return yaml.safe_load(f)
    return {}