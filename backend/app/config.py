"""
BharatRoad Twin - Application Configuration
============================================
Loads settings from .env file and YAML config files.
All configuration is centralized here — no magic numbers elsewhere.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


# ── Paths ──────────────────────────────────────────────────
# Project root is two levels up from this file (backend/app/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
DEMO_DIR = DATA_DIR / "demo"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure required directories exist
for d in [DATA_DIR, DEMO_DIR, REPORTS_DIR, DATA_DIR / "uploads", DATA_DIR / "networks"]:
    d.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    All settings have sensible defaults so the app works out of the box.
    """

    # General
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Backend server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8001
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'data' / 'bharatroad.db'}"

    # SUMO
    sumo_home: str = ""

    # ML Model
    yolo_model_path: str = ""
    yolo_confidence: float = 0.25

    # Demo mode - use bundled sample data
    demo_mode: bool = True

    # Upload limits
    max_upload_size_mb: int = 500
    allowed_video_types: str = ".mp4,.avi,.mov,.mkv"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_database_url(self) -> str:
        """Resolve database URL to an absolute path for SQLite on Windows/Linux."""
        if self.database_url.startswith("sqlite:///"):
            raw_path = self.database_url.replace("sqlite:///", "")
            if not os.path.isabs(raw_path):
                db_name = Path(raw_path).name
                abs_path = (DATA_DIR / db_name).resolve().as_posix()
                return f"sqlite:///{abs_path}"
        return self.database_url

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def allowed_video_types_list(self) -> list[str]:
        """Parse allowed video types string into a list."""
        return [ext.strip() for ext in self.allowed_video_types.split(",")]

    @property
    def sumo_available(self) -> bool:
        """Check if SUMO is available on this system."""
        sumo_home = self.sumo_home or os.environ.get("SUMO_HOME", "")
        if sumo_home and Path(sumo_home).exists():
            return True
        # Try to find sumo on PATH
        import shutil
        return shutil.which("sumo") is not None

    @property
    def sumo_bin_dir(self) -> Optional[Path]:
        """Get the SUMO bin directory path."""
        sumo_home = self.sumo_home or os.environ.get("SUMO_HOME", "")
        if sumo_home:
            bin_dir = Path(sumo_home) / "bin"
            if bin_dir.exists():
                return bin_dir
        return None


def load_yaml_config(filename: str) -> dict:
    """
    Load a YAML configuration file from the config directory.
    
    Args:
        filename: Name of the YAML file (e.g., 'indian_road_rules.yaml')
    
    Returns:
        Dictionary with the parsed YAML content.
    """
    filepath = CONFIG_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_road_rules() -> dict:
    """Load Indian road rules configuration."""
    return load_yaml_config("indian_road_rules.yaml")


def get_corridors() -> dict:
    """Load study corridors configuration."""
    return load_yaml_config("corridors.yaml")


def get_simulation_params() -> dict:
    """Load simulation parameters configuration."""
    return load_yaml_config("simulation_params.yaml")


# Create a singleton settings instance
settings = Settings()
