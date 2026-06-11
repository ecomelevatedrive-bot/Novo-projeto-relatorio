import os
from dotenv import load_dotenv

load_dotenv()

def _req(key: str) -> str:
    val = os.getenv(key, "")
    if not val:
        raise RuntimeError(
            f"\n  ❌  Variável de ambiente '{key}' não definida.\n"
            f"  Copie .env.example para .env e preencha o valor.\n"
        )
    return val

# ── Shopee ────────────────────────────────────────────────
PARTNER_ID   = int(os.getenv("SHOPEE_PARTNER_ID", "0"))
PARTNER_KEY  = os.getenv("SHOPEE_PARTNER_KEY", "")
SHOP_ID      = int(os.getenv("SHOPEE_SHOP_ID", "0"))
ACCESS_TOKEN = os.getenv("SHOPEE_ACCESS_TOKEN", "")
ENVIRONMENT  = os.getenv("SHOPEE_ENVIRONMENT", "production")

# ── Monday.com ────────────────────────────────────────────
MONDAY_API_TOKEN = _req("MONDAY_API_TOKEN")
MONDAY_BOARD_ID  = os.getenv("MONDAY_BOARD_ID", "18414132966")

# ── Dolphin Anty ──────────────────────────────────────────
DOLPHIN_API_TOKEN = _req("DOLPHIN_API_TOKEN")

BASE_URLS = {
    "production": "https://partner.shopeemobile.com",
    "sandbox":    "https://partner.uat.shopeemobile.com",
}

BASE_URL = BASE_URLS[ENVIRONMENT]
