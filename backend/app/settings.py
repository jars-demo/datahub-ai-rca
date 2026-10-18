import os
from dataclasses import dataclass, field
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("RCA_DATA_DIR", _BACKEND_DIR / ".data")
        )
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            os.environ.get(
                "RCA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
            ).split(",")
        )
    )

    @property
    def connections_file(self) -> Path:
        return self.data_dir / "connections.json"


def get_settings() -> Settings:
    return Settings()
