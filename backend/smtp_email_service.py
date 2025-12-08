"""
SMTP Email Service for sending contact notifications
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMTPEmailService:
    def __init__(self):
        self.gmail_user = os.getenv('GMAIL_USER')
        self.gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
    
    def send_email(self, to_email: str, subject: str, body_html: str, reply_to: Optional[str] = None) -> bool:
        """Send an email using Gmail SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.gmail_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Attach HTML body
            html_part = MIMEText(body_html, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_inquiry_notification(
        self,
        admin_email: str,
        user_name: str,
        user_email: str,
        user_phone: Optional[str],
        message: str,
        building_name: str,
        building_address: str,
        unit_number: str,
        rent: float,
        bedrooms: int,
        bathrooms: float,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
        alternative_date: Optional[str] = None,
        alternative_time: Optional[str] = None
    ) -> bool:
        """Send inquiry notification to admin"""
        
        subject = f"New Inquiry - {building_name} Unit #{unit_number}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #f59e0b; border-bottom: 2px solid #f59e0b; padding-bottom: 10px;">
                    New Inquiry from NoFeesApts.com
                </h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e293b; margin-top: 0;">Contact Details:</h3>
                    <p style="margin: 5px 0;"><strong>Name:</strong> {user_name}</p>
                    <p style="margin: 5px 0;"><strong>Email:</strong> <a href="mailto:{user_email}">{user_email}</a></p>
                    <p style="margin: 5px 0;"><strong>Phone:</strong> {user_phone or 'Not provided'}</p>
                </div>
                
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e293b; margin-top: 0;">Interested In:</h3>
                    <p style="margin: 5px 0;"><strong>Building:</strong> {building_name}</p>
                    <p style="margin: 5px 0;"><strong>Address:</strong> {building_address}</p>
                    <p style="margin: 5px 0;"><strong>Unit:</strong> #{unit_number}</p>
                    <p style="margin: 5px 0;"><strong>Rent:</strong> ${rent:,.0f}/month</p>
                    <p style="margin: 5px 0;"><strong>Layout:</strong> {bedrooms}BR / {bathrooms}BA</p>
                </div>
                
                <div style="background: #e0f2fe; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e293b; margin-top: 0;">Message:</h3>
                    <p style="white-space: pre-wrap;">{message}</p>
                </div>
                
                {self._format_viewing_schedule(preferred_date, preferred_time, alternative_date, alternative_time)}
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                
                <p style="color: #64748b; font-size: 14px;">
                    <strong>Quick Action:</strong> Reply directly to this email to contact {user_name}.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(admin_email, subject, body, reply_to=user_email)
    
    def send_inquiry_confirmation(
        self,
        user_email: str,
        user_name: str,
        message: str,
        building_name: str,
        building_address: str,
        unit_number: str,
        rent: float,
        bedrooms: int,
        bathrooms: float,
        preferred_date: Optional[str] = None,
        preferred_time: Optional[str] = None,
        alternative_date: Optional[str] = None,
        alternative_time: Optional[str] = None
    ) -> bool:
        """Send confirmation email to user"""
        
        subject = f"We Received Your Inquiry - {building_name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #f59e0b; border-bottom: 2px solid #f59e0b; padding-bottom: 10px;">
                    Thank You for Your Inquiry!
                </h2>
                
                <p>Hi {user_name},</p>
                
                <p>Thank you for your interest in this property through NoFeesApts.com. We've received your inquiry and will get back to you as soon as possible!</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e293b; margin-top: 0;">Property Details:</h3>
                    <p style="margin: 5px 0;"><strong>{building_name}</strong></p>
                    <p style="margin: 5px 0;">Unit #{unit_number}</p>
                    <p style="margin: 5px 0;">{building_address}</p>
                    <p style="margin: 5px 0;"><strong>Rent:</strong> ${rent:,.0f}/month</p>
                    <p style="margin: 5px 0;"><strong>Layout:</strong> {bedrooms}BR / {bathrooms}BA</p>
                </div>
                
                <div style="background: #e0f2fe; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1e293b; margin-top: 0;">Your Message:</h3>
                    <p style="white-space: pre-wrap;">{message}</p>
                </div>
                
                {self._format_viewing_schedule(preferred_date, preferred_time, alternative_date, alternative_time)}
                
                <p>We typically respond within 24 hours. If you have any urgent questions, please feel free to contact us directly.</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                
                <p style="color: #64748b; font-size: 14px;">
                    <strong>NoFeesApts Team</strong><br>
                    <a href="mailto:placesfirm@gmail.com" style="color: #f59e0b; text-decoration: none;">placesfirm@gmail.com</a><br>
                    <a href="https://rentdirect-6.preview.emergentagent.com" style="color: #f59e0b; text-decoration: none;">NoFeesApts.com</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body)


# Create singleton instance
smtp_service = SMTPEmailService()
