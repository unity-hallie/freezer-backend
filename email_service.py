import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import secrets
from typing import Optional

# Load environment variables from current directory
load_dotenv(".env")

class GmailEmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.port = 587  # For TLS
        self.sender_email = os.getenv("GMAIL_EMAIL")
        self.password = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("MAIL_APP_PASSWORD")  # App-specific password
        
        if not self.sender_email or not self.password:
            print("⚠️  WARNING: GMAIL_EMAIL or GMAIL_APP_PASSWORD not found - using email simulation mode")
            print("💡 To use Gmail: Add GMAIL_EMAIL and GMAIL_APP_PASSWORD to .env file")
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> bool:
        """Send email via Gmail SMTP"""
        
        if not self.sender_email or not self.password:
            # Fallback: log email content for development
            print(f"\n📧 EMAIL SIMULATION MODE")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Content: {text_content}")
            print("=" * 50)
            return True
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"Freezer App <{self.sender_email}>"
            message["To"] = to_email
            
            # Add both plain text and HTML parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            message.attach(text_part)
            message.attach(html_part)
            
            # Create secure connection and send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            print(f"✅ Gmail email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Gmail error: {e}")
            # Fall back to simulation
            print(f"\n📧 EMAIL FALLBACK MODE")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Content: {text_content}")
            print("=" * 50)
            return False

# Global email service
email_service = GmailEmailService()

def generate_verification_token():
    return secrets.token_urlsafe(32)

def send_verification_email(email: str, token: str, base_url: str = "http://localhost:3000") -> bool:
    """Send verification email using Mailgun"""
    verification_url = f"{base_url}/verify-email?token={token}"
    
    subject = "✅ Verify your Freezer App account"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
            <h1 style="margin: 0; font-size: 28px;">🧊 Welcome to Freezer App!</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Please verify your email address</p>
        </div>
        
        <div style="padding: 30px 0;">
            <p>Hi there! 👋</p>
            
            <p>Welcome to Freezer App! Please verify your email address to get started.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background: #4CAF50; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 8px; font-weight: bold;
                          display: inline-block;">
                    ✅ Verify Email Address
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                This link will expire in 24 hours for security reasons.
            </p>
            
            <p style="color: #666; font-size: 14px;">
                If you didn't create this account, you can safely ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
Welcome to Freezer App!

Please verify your email address by clicking this link:
{verification_url}

This link will expire in 24 hours.

If you didn't create this account, you can safely ignore this email.

---
Freezer App - Keep your household inventory organized
    """
    
    return email_service.send_email(email, subject, html_content, text_content)

def send_password_reset_email(email: str, token: str, user_name: str = "User", base_url: str = "http://localhost:3000") -> bool:
    """Send password reset email using Mailgun"""
    reset_url = f"{base_url}/reset-password?token={token}"
    
    subject = "🔑 Password Reset - Freezer App"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; text-align: center;">
            <h1 style="margin: 0; font-size: 28px;">🧊 Freezer App</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Password Reset Request</p>
        </div>
        
        <div style="padding: 30px 0;">
            <p>Hi {user_name},</p>
            
            <p>We received a request to reset your password for your Freezer App account.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background: #667eea; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 8px; font-weight: bold;
                          display: inline-block;">
                    🔓 Reset My Password
                </a>
            </div>
            
            <p style="color: #666; font-size: 14px;">
                This link will expire in 1 hour for security reasons.
            </p>
            
            <p style="color: #666; font-size: 14px;">
                If you didn't request this reset, you can safely ignore this email.
            </p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; text-align: center;">
                Freezer App - Keep your household inventory organized
            </p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
Password Reset - Freezer App

Hi {user_name},

We received a request to reset your password for your Freezer App account.

Click this link to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this reset, you can safely ignore this email.

---
Freezer App - Keep your household inventory organized
    """
    
    return email_service.send_email(email, subject, html_content, text_content)

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