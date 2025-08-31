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
        """Generate Discord OAuth authorization URL"""
        if not DISCORD_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Discord OAuth not configured"
            )
        
        params = {
            'client_id': DISCORD_CLIENT_ID,
            'redirect_uri': DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'identify email'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"https://discord.com/api/oauth2/authorize?{query_string}"
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> Dict:
        """Exchange authorization code for access token"""
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
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DiscordOAuth.BASE_URL}/oauth2/token",
                data=data,
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange code for token"
                )
            
            return response.json()
    
    @staticmethod
    async def get_user_info(access_token: str) -> Dict:
        """Get Discord user information"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DiscordOAuth.BASE_URL}/users/@me",
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get Discord user info"
                )
            
            return response.json()