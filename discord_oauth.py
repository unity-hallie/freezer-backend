import httpx
from typing import Optional, Dict
from decouple import config
from fastapi import HTTPException, status

# Discord OAuth Configuration
DISCORD_CLIENT_ID = config('DISCORD_CLIENT_ID', default='')
DISCORD_CLIENT_SECRET = config('DISCORD_CLIENT_SECRET', default='')
DISCORD_REDIRECT_URI = config('DISCORD_REDIRECT_URI', default='http://localhost:3000/auth/discord/callback')

class DiscordOAuth:
    BASE_URL = "https://discord.com/api"
    
    @staticmethod
    def get_authorization_url() -> str:
        """Generate Discord OAuth authorization URL (safely URL-encoded)."""
        if not DISCORD_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Discord OAuth not configured"
            )
        # Build URL with proper encoding to avoid malformed redirect URIs
        url = httpx.URL("https://discord.com/api/oauth2/authorize").copy_with(
            params={
                "client_id": DISCORD_CLIENT_ID,
                "redirect_uri": DISCORD_REDIRECT_URI,
                "response_type": "code",
                "scope": "identify email",
            }
        )
        return str(url)
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> Dict:
        """Exchange authorization code for access token, with timeouts and clearer errors."""
        if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Discord OAuth not configured"
            )
        
        data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI,
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        # Add explicit timeouts to avoid hanging upstream calls
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{DiscordOAuth.BASE_URL}/oauth2/token",
                data=data,
                headers=headers,
            )
            if resp.status_code != 200:
                # Include short body for diagnosis but avoid leaking secrets
                snippet = resp.text[:200] if isinstance(resp.text, str) else str(resp.status_code)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Discord token exchange failed: {resp.status_code} {snippet}"
                )
            return resp.json()
    
    @staticmethod
    async def get_user_info(access_token: str) -> Dict:
        """Get Discord user information, with timeouts and clearer errors."""
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                f"{DiscordOAuth.BASE_URL}/users/@me",
                headers=headers,
            )
            if resp.status_code != 200:
                snippet = resp.text[:200] if isinstance(resp.text, str) else str(resp.status_code)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Discord userinfo failed: {resp.status_code} {snippet}"
                )
            return resp.json()
