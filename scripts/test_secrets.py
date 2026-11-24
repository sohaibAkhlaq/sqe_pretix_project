"""Load a named local test secret without echoing it or committing it."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get_test_secret(name):
    value = os.environ.get(name)
    if value:
        return value
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, raw_value = line.partition("=")
            if separator and key.strip() == name:
                value = raw_value.strip().strip("\"'")
                if value:
                    return value
    raise RuntimeError(f"Missing {name}; define it in the ignored .env file or process environment.")
