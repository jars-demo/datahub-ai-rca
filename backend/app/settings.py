import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
INGESTION_DIR = REPO_ROOT / "ingestion"


@dataclass(frozen=True)
class Settings:
    state_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("RCA_STATE_DIR", REPO_ROOT / "backend" / ".data")
        )
    )
    env_file: Path = field(
        default_factory=lambda: Path(os.environ.get("RCA_ENV_FILE", REPO_ROOT / ".env"))
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            os.environ.get(
                "RCA_CORS_ORIGINS", "http://localhost:3300,http://127.0.0.1:3300"
            ).split(",")
        )
    )
    ingestion_python: Path = field(
        default_factory=lambda: Path(
            os.environ.get("RCA_INGESTION_PYTHON", INGESTION_DIR / ".venv" / "bin" / "python")
        )
    )

    @property
    def connections_file(self) -> Path:
        return self.state_dir / "connections.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def read_env(settings: Settings) -> dict[str, str]:
    """Values from the .env file, overridden by real environment variables.

    Read into a dict on purpose: secrets are never written into this process's environment.
    """
    values = {k: v for k, v in dotenv_values(settings.env_file).items() if v}
    values.update({k: v for k, v in os.environ.items() if v})
    return values
