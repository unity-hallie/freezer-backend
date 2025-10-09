from fastapi import APIRouter
from decouple import config

router = APIRouter(prefix="/health", tags=["health"]) 


@router.get("/dev")
async def dev_health():
    """Non-sensitive configuration health. Booleans only; no secrets.

    Returns masks/flags indicating whether critical configuration is present.
    """
    # Presence checks only; never expose values
    def present(name: str) -> bool:
        try:
            v = config(name, default="")
            return bool(v)
        except Exception:
            return False

    return {
        "discord_configured": present("DISCORD_CLIENT_ID") and present("DISCORD_CLIENT_SECRET"),
        "discord_redirect_uri_set": present("DISCORD_REDIRECT_URI"),
        "frontend_url_set": present("FRONTEND_URL"),
        "allowed_hosts_set": present("ALLOWED_HOSTS"),
        "jwt_secrets_set": present("SECRET_KEY") and present("JWT_SECRET_KEY"),
        "email_simulation_mode": not (present("GMAIL_EMAIL") and present("GMAIL_APP_PASSWORD")),
    }

