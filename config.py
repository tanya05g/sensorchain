import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    d = Path(os.environ.get("SENSORCHAIN_DATA", ROOT / "data"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_sensors(path=None) -> dict:
    path = Path(path or ROOT / "sensors.yaml")
    return yaml.safe_load(path.read_text())["sensors"]
