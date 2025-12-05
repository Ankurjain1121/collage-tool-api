import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://collage_user:collage_secure_2024@localhost:5432/collage_db"
    )

    # Storage paths
    STORAGE_PATH: Path = Path(os.getenv("STORAGE_PATH", "/var/www/collage"))
    UPLOADS_PATH: Path = STORAGE_PATH / "uploads"
    INPUTS_PATH: Path = UPLOADS_PATH / "inputs"
    OUTPUTS_PATH: Path = UPLOADS_PATH / "outputs"
    ASSETS_PATH: Path = STORAGE_PATH / "assets"
    BORDERS_PATH: Path = ASSETS_PATH / "borders"

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    BASE_URL: str = os.getenv("BASE_URL", "https://collage.paraslace.in")

    # Slack (optional, for direct API calls)
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")

    # Replicate API
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")

    # Collage settings
    CANVAS_WIDTH: int = 1920
    CANVAS_HEIGHT: int = 1080
    IMAGE1_WIDTH_RATIO: float = 0.25  # 25% for product image
    IMAGE2_WIDTH_RATIO: float = 0.75  # 75% for color variants

    # Border settings
    BORDER_THICKNESS: int = 80              # 80px on all edges
    DIVIDER_THICKNESS: int = 40             # 40px vertical divider
    BORDER_COLOR: tuple = (0, 0, 0)         # Solid black #000000


settings = Settings()
