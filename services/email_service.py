import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging

class EmailService:
    def __init__(self):
        # Gmail SMTP configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email = os.environ.get('SMTP_EMAIL')
        self.password = os.environ.get('SMTP_PASSWORD')
        
        # Check if email credentials are available and clean app password
        if self.password:
            # Remove spaces from app password (common copy/paste issue)
            self.password = self.password.replace(' ', '').strip()
        self.email_enabled = bool(self.email and self.password)
        
    def send_password_reset_otp(self, to_email, username, otp_code):
        """Send password reset OTP to user's email"""
        if not self.email_enabled:
            logging.warning("Email service not configured - SMTP credentials missing")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = "Diagn'AI'zer - Password Reset OTP"
            
            # HTML email body
            html_body = f"""
            <html>
            <head></head>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #1e3a8a; margin-bottom: 10px;">🧠 Diagn'AI'zer</h1>
                        <p style="color: #666; font-size: 16px;">AI-Powered Medical Analysis</p>
                    </div>
                    
                    <div style="background-color: #f8fafc; padding: 30px; border-radius: 10px; border-left: 4px solid #3b82f6;">
                        <h2 style="color: #1e3a8a; margin-bottom: 20px;">Password Reset Request</h2>
                        
                        <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
                            Hello <strong>{username}</strong>,
                        </p>
                        
                        <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
                            We received a request to reset your password for your Diagn'AI'zer account. 
                            Use the following One-Time Password (OTP) to reset your password:
                        </p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="background-color: #1e3a8a; color: white; font-size: 32px; font-weight: bold; 
                                       padding: 20px; border-radius: 8px; letter-spacing: 8px; display: inline-block;">
                                {otp_code}
                            </div>
                        </div>
                        
                        <div style="background-color: #fef3cd; border: 1px solid #fbbf24; border-radius: 6px; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; color: #92400e; font-size: 14px;">
                                <strong>⏰ Important:</strong> This OTP will expire in 15 minutes for security reasons.
                            </p>
                        </div>
                        
                        <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
                            If you didn't request a password reset, please ignore this email. Your account remains secure.
                        </p>
                        
                        <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 30px;">
                            <p style="font-size: 14px; color: #6b7280; margin: 0;">
                                This is an automated email from Diagn'AI'zer. Please do not reply to this email.
                            </p>
                            <p style="font-size: 14px; color: #6b7280; margin: 5px 0 0 0;">
                                For support, contact our team through the application.
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML body
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email with error handling
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Ensure credentials are strings and strip whitespace
            email_str = str(self.email).strip()
            password_str = str(self.password).strip()
            
            server.login(email_str, password_str)
            text = msg.as_string()
            server.sendmail(email_str, to_email, text)
            server.quit()
            
            logging.info(f"Password reset OTP sent to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send password reset email: {str(e)}")
            return False
    
    def send_password_change_confirmation(self, to_email, username):
        """Send confirmation email after successful password change"""
        if not self.email_enabled:
            logging.warning("Email service not configured - SMTP credentials missing")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = "Diagn'AI'zer - Password Successfully Changed"
            
            # HTML email body
            html_body = f"""
            <html>
            <head></head>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #1e3a8a; margin-bottom: 10px;">🧠 Diagn'AI'zer</h1>
                        <p style="color: #666; font-size: 16px;">AI-Powered Medical Analysis</p>
                    </div>
                    
                    <div style="background-color: #f0fdf4; padding: 30px; border-radius: 10px; border-left: 4px solid #10b981;">
                        <h2 style="color: #065f46; margin-bottom: 20px;">✅ Password Successfully Changed</h2>
                        
                        <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
                            Hello <strong>{username}</strong>,
                        </p>
                        
                        <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
                            Your password has been successfully changed for your Diagn'AI'zer account.
                        </p>
                        
                        <p style="font-size: 16px; color: #374151; margin-bottom: 20px;">
                            If you did not make this change, please contact our support team immediately.
                        </p>
                        
                        <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 30px;">
                            <p style="font-size: 14px; color: #6b7280; margin: 0;">
                                This is an automated email from Diagn'AI'zer. Please do not reply to this email.
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML body
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email with error handling
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            # Ensure credentials are strings and strip whitespace
            email_str = str(self.email).strip()
            password_str = str(self.password).strip()
            
            server.login(email_str, password_str)
            text = msg.as_string()
            server.sendmail(email_str, to_email, text)
            server.quit()
            
            logging.info(f"Password change confirmation sent to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send password change confirmation: {str(e)}")
            return False