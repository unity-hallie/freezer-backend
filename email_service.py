from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from decouple import config
from typing import List
import secrets
from sqlalchemy.orm import Session
import models

conf = ConnectionConfig(
    MAIL_USERNAME=config('MAIL_USERNAME', default=''),
    MAIL_PASSWORD=config('MAIL_PASSWORD', default=''),
    MAIL_FROM=config('MAIL_FROM', default='noreply@freezerapp.com'),
    MAIL_PORT=config('MAIL_PORT', default=587, cast=int),
    MAIL_SERVER=config('MAIL_SERVER', default='smtp.gmail.com'),
    MAIL_FROM_NAME=config('MAIL_FROM_NAME', default='Freezer App'),
    MAIL_STARTTLS=config('MAIL_STARTTLS', default=True, cast=bool),
    MAIL_SSL_TLS=config('MAIL_SSL_TLS', default=False, cast=bool),
    USE_CREDENTIALS=config('USE_CREDENTIALS', default=True, cast=bool),
    VALIDATE_CERTS=config('VALIDATE_CERTS', default=True, cast=bool)
)

fastmail = FastMail(conf)

def generate_verification_token():
    return secrets.token_urlsafe(32)

async def send_verification_email(email: str, token: str, base_url: str = "http://localhost:3000"):
    verification_url = f"{base_url}/verify-email?token={token}"
    
    html = f"""
    <html>
        <body>
            <h2>Welcome to Freezer App!</h2>
            <p>Please click the link below to verify your email address:</p>
            <a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">
                Verify Email
            </a>
            <p>Or copy and paste this link in your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Verify your Freezer App account",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    try:
        if conf.MAIL_USERNAME:  # Only send if email is configured
            await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False

async def send_password_reset_email(email: str, token: str, base_url: str = "http://localhost:3000"):
    reset_url = f"{base_url}/reset-password?token={token}"
    
    html = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You have requested to reset your password. Click the link below to reset it:</p>
            <a href="{reset_url}" style="background-color: #FF6B6B; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">
                Reset Password
            </a>
            <p>Or copy and paste this link in your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Reset your Freezer App password",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    try:
        if conf.MAIL_USERNAME:  # Only send if email is configured
            await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False

async def send_household_invitation(email: str, household_name: str, invite_code: str, inviter_name: str, base_url: str = "http://localhost:3000"):
    join_url = f"{base_url}/join-household?code={invite_code}"
    
    html = f"""
    <html>
        <body>
            <h2>You're invited to join a household!</h2>
            <p><strong>{inviter_name}</strong> has invited you to join the <strong>{household_name}</strong> household on Freezer App.</p>
            <p>Click the link below to join:</p>
            <a href="{join_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">
                Join Household
            </a>
            <p>Or use invite code: <strong>{invite_code}</strong></p>
            <p>This invitation does not expire, but can be revoked by the household owner.</p>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject=f"Invitation to join {household_name} on Freezer App",
        recipients=[email],
        body=html,
        subtype="html"
    )
    
    try:
        if conf.MAIL_USERNAME:  # Only send if email is configured
            await fastmail.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send household invitation: {e}")
        return False