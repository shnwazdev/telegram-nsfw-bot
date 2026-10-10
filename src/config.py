"""
Configuration Module for Telegram NSFW Shield Bot
Loads environment variables and sets defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
MODELS_DIR = ROOT_DIR / "models"
ASSETS_DIR = ROOT_DIR / "assets"

# Load .env from ROOT_DIR
load_dotenv(ROOT_DIR / ".env")

# Model & Asset Paths
OPEN_NSFW_MODEL_PATH = str(MODELS_DIR / "open_nsfw.onnx")
BANNER_PATH = str(ASSETS_DIR / "banner.jpg")
BANNER_URL = "https://files.catbox.moe/it2a10.jpg"

# Telegram API & Credentials (https://my.telegram.org & @BotFather)
TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID", "38972657"))
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "277a40896fe7983582dd35c8f131cef4")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8889285131:AAFx_PDzgSU4UCCFILleTWR0KpYgLXGoz9I")

# Owner & Log Group
OWNER_ID = int(os.environ.get("OWNER_ID", "8677818347"))
LOG_GROUP_ID = int(os.environ.get("LOG_GROUP_ID", "-1003951821704"))
SUPPORT_CHANNEL_URL = os.environ.get("SUPPORT_CHANNEL_URL", "https://t.me/shnwazx")

# Moderation Settings
DEFAULT_SENSITIVITY = os.environ.get("DEFAULT_SENSITIVITY", "balanced").lower()
TELEGRAM_SEND_WARNING = os.environ.get("TELEGRAM_SEND_WARNING", "true").lower() in ("true", "1")
TELEGRAM_WARNING_AUTO_DELETE_SEC = int(os.environ.get("TELEGRAM_WARNING_AUTO_DELETE_SEC", "15"))

# Cache Settings
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", "50000"))

# Sensitivity Presets
SENSITIVITY_PRESETS = {
    "strict": {
        "classifier_threshold": 0.14,
        "explicit_part_threshold": 0.12,
        "weak_part_threshold": 0.25,
        "description": "Zero tolerance: Deletes any suggestive or erotic content."
    },
    "balanced": {
        "classifier_threshold": 0.18,
        "explicit_part_threshold": 0.15,
        "weak_part_threshold": 0.60,
        "description": "Deletes all 18+ porn stickers, exposed parts, and sex scenes. Safe stickers pass."
    },
    "permissive": {
        "classifier_threshold": 0.60,
        "explicit_part_threshold": 0.35,
        "weak_part_threshold": 0.85,
        "description": "Only deletes hard pornography and exposed genitalia."
    }
}
