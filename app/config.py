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
    BORDER_THICKNESS: int = 25              # 25px on all edges (reduced from 50)
    GAP_THICKNESS: int = 10                 # 10px gap between boxes (reduced from 15)

    # Base backgrounds (pastel with geometric patterns)
    BACKGROUNDS_PATH: Path = PROJECT_ROOT / "assets" / "backgrounds"
    BASE_BACKGROUNDS: list = [
        "base_light_pink.png",
        "base_mint_green.png",
        "base_powder_blue.png",
        "base_lavender.png",
        "base_cream.png",
    ]

    # Solid color overlays for product box (light to dark)
    SOLID_OVERLAYS: list = [
        ((135, 206, 235), "sky_blue"),      # Sky Blue #87CEEB - lightest
        ((255, 248, 220), "cream"),         # Cream #FFF8DC
        ((210, 180, 140), "tan"),           # Tan #D2B48C
        ((128, 128, 0), "olive"),           # Olive #808000
        ((0, 106, 78), "bottle_green"),     # Bottle Green #006A4E - darkest
    ]


settings = Settings()
