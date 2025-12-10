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
    
    def _format_viewing_schedule(
        self, 
        preferred_date: Optional[str], 
        preferred_time: Optional[str],
        alternative_date: Optional[str],
        alternative_time: Optional[str]
    ) -> str:
        """Format viewing schedule section for email"""
        if not any([preferred_date, preferred_time, alternative_date, alternative_time]):
            return ""
        
        time_mapping = {
            "morning": "Morning (9am-12pm)",
            "afternoon": "Afternoon (12pm-5pm)",
            "evening": "Evening (5pm-8pm)"
        }
        
        html = '<div style="background: #dcfce7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">'
        html += '<h3 style="color: #1e293b; margin-top: 0;">📅 Requested Viewing Times:</h3>'
        
        if preferred_date or preferred_time:
            html += '<div style="margin: 10px 0;">'
            html += '<p style="margin: 5px 0;"><strong style="color: #059669;">Preferred:</strong></p>'
            if preferred_date:
                html += f'<p style="margin: 5px 0 5px 20px;">📆 Date: {preferred_date}</p>'
            if preferred_time:
                time_display = time_mapping.get(preferred_time, preferred_time)
                html += f'<p style="margin: 5px 0 5px 20px;">⏰ Time: {time_display}</p>'
            html += '</div>'
        
        if alternative_date or alternative_time:
            html += '<div style="margin: 10px 0;">'
            html += '<p style="margin: 5px 0;"><strong style="color: #059669;">Alternative:</strong></p>'
            if alternative_date:
                html += f'<p style="margin: 5px 0 5px 20px;">📆 Date: {alternative_date}</p>'
            if alternative_time:
                time_display = time_mapping.get(alternative_time, alternative_time)
                html += f'<p style="margin: 5px 0 5px 20px;">⏰ Time: {time_display}</p>'
            html += '</div>'
        
        html += '<p style="margin: 15px 0 0 0; color: #047857; font-size: 14px;"><em>💡 Please confirm availability with the prospective tenant.</em></p>'
        html += '</div>'
        
        return html
    
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
                    <a href="https://nyc-apt-finder.preview.emergentagent.com" style="color: #f59e0b; text-decoration: none;">NoFeesApts.com</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body)
    
    def send_welcome_email(
        self,
        user_email: str,
        user_name: str
    ) -> bool:
        """Send welcome email to new user"""
        
        subject = "Welcome to NoFeesApts.com - Start Your No-Fee Apartment Search! 🎉"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 40px 20px; border-radius: 10px 10px 0 0; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 32px;">🏢 Welcome to NoFeesApts!</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb;">
                    <h2 style="color: #1e293b; margin-top: 0;">Hi {user_name}! 👋</h2>
                    
                    <p style="font-size: 16px;">Thank you for joining <strong>NoFeesApts.com</strong> — your trusted source for finding quality apartments in NYC and Northern New Jersey without paying broker fees!</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                        <h3 style="color: #1e293b; margin-top: 0;">🎯 What You Can Do Now:</h3>
                        <ul style="color: #475569; line-height: 1.8;">
                            <li>🔍 <strong>Search hundreds of apartments</strong> — all with zero broker fees</li>
                            <li>💰 <strong>Save thousands</strong> — no hidden costs or surprise fees</li>
                            <li>❤️ <strong>Save favorites</strong> — keep track of apartments you love</li>
                            <li>📅 <strong>Schedule viewings</strong> — request tours directly through our platform</li>
                            <li>🔔 <strong>Get instant alerts</strong> — be the first to know about new listings</li>
                        </ul>
                    </div>
                    
                    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #1e293b; margin-top: 0;">💡 Pro Tips:</h3>
                        <p style="margin: 5px 0; color: #64748b;">✨ Use our advanced filters to narrow down your perfect apartment</p>
                        <p style="margin: 5px 0; color: #64748b;">📍 Explore different neighborhoods to find your ideal location</p>
                        <p style="margin: 5px 0; color: #64748b;">⚡ Act fast on new listings — no-fee apartments go quickly!</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://nyc-apt-finder.preview.emergentagent.com/dashboard" style="display: inline-block; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 16px;">
                            Start Searching Now →
                        </a>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                    
                    <p style="color: #64748b; font-size: 14px; text-align: center;">
                        <strong>Need Help?</strong><br>
                        We're here for you! Reply to this email or contact us at<br>
                        <a href="mailto:placesfirm@gmail.com" style="color: #f59e0b; text-decoration: none;">placesfirm@gmail.com</a>
                    </p>
                    
                    <p style="color: #64748b; font-size: 14px; text-align: center; margin-top: 20px;">
                        Happy apartment hunting! 🏠<br>
                        <strong>The NoFeesApts Team</strong>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, body)


# Create singleton instance
smtp_service = SMTPEmailService()
