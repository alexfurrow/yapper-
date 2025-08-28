import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, url_for
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        self.app_url = os.environ.get('APP_URL', 'http://localhost:3000')
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email using SMTP"""
        if not all([self.smtp_username, self.smtp_password]):
            print(f"Email would be sent to {to_email}: {subject}")
            print(f"Content: {html_content}")
            return True  # Mock email sending for development
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Attach both HTML and text versions
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def send_verification_email(self, user, token):
        """Send email verification email"""
        verification_url = f"{self.app_url}/verify-email?token={token}"
        
        subject = "Verify Your Email Address"
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Yapper!</h2>
            <p>Hi {user.username},</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}">Verify Email Address</a></p>
            <p>If the link doesn't work, copy and paste this URL into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>Thanks,<br>The Yapper Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Yapper!
        
        Hi {user.username},
        
        Please verify your email address by visiting this link:
        {verification_url}
        
        This link will expire in 24 hours.
        
        Thanks,
        The Yapper Team
        """
        
        return self.send_email(user.email, subject, html_content, text_content)
    
    def send_password_reset_email(self, user, token):
        """Send password reset email"""
        reset_url = f"{self.app_url}/reset-password?token={token}"
        
        subject = "Reset Your Password"
        html_content = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi {user.username},</p>
            <p>You requested to reset your password. Click the link below to set a new password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>If the link doesn't work, copy and paste this URL into your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>Thanks,<br>The Yapper Team</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {user.username},
        
        You requested to reset your password. Visit this link to set a new password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Thanks,
        The Yapper Team
        """
        
        return self.send_email(user.email, subject, html_content, text_content)
