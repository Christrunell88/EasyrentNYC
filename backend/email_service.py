"""
Gmail API Email Service
Handles email sending via Gmail API for contact form notifications
"""

import base64
import os
import pickle
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
# Use relative paths from current file location
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.environ.get('GMAIL_CREDENTIALS_FILE', os.path.join(ROOT_DIR, 'gmail_credentials.json'))
TOKEN_FILE = os.environ.get('GMAIL_TOKEN_FILE', os.path.join(ROOT_DIR, 'token.pickle'))


def get_gmail_service():
    """
    Authenticate with Gmail API and return service object.
    Handles OAuth credential flow and token caching.
    """
    creds = None
    
    # Load cached credentials if available
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
            logger.info("Loaded cached Gmail credentials")
        except Exception as e:
            logger.warning(f"Failed to load cached credentials: {e}")
            creds = None
    
    # If no valid credentials, perform OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired Gmail credentials")
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            # Check if credentials file exists
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Gmail credentials file not found at {CREDENTIALS_FILE}. "
                    "Please add your OAuth credentials JSON file."
                )
            
            # Run OAuth flow for new credentials
            logger.info("Starting OAuth flow for Gmail authentication")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            # Use run_local_server for initial setup, will open browser
            creds = flow.run_local_server(port=0)
            logger.info("OAuth flow completed successfully")
        
        # Save credentials for future use
        try:
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("Saved Gmail credentials to cache")
        except Exception as e:
            logger.warning(f"Failed to cache credentials: {e}")
    
    # Build and return Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service


def create_email_message(
    sender_email: str,
    recipient_email: str,
    subject: str,
    name: str,
    user_email: str,
    phone: Optional[str],
    apartment_unit: str,
    message: str
) -> Dict[str, str]:
    """
    Create a properly formatted email message with HTML content.
    Returns base64url encoded message suitable for Gmail API.
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    # Plain text version
    text = f"""
New Contact Form Submission - NoFeesApts.com

Name: {name}
Email: {user_email}
Phone: {phone if phone else 'Not provided'}
Apartment Unit: {apartment_unit}

Message:
{message}

---
This message was sent from the NoFeesApts.com contact form.
"""
    
    # HTML version with professional formatting
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 20px;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background-color: #f8f9fa;
            padding: 20px;
            border: 1px solid #e0e0e0;
        }}
        .info-box {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #f59e0b;
        }}
        .info-row {{
            margin: 10px 0;
        }}
        .label {{
            font-weight: bold;
            color: #555;
        }}
        .message-box {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            white-space: pre-wrap;
            line-height: 1.6;
        }}
        .footer {{
            text-align: center;
            padding: 15px;
            font-size: 12px;
            color: #999;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">🏢 New Apartment Inquiry</h2>
            <p style="margin: 5px 0 0 0;">NoFeesApts.com Contact Form</p>
        </div>
        
        <div class="content">
            <div class="info-box">
                <div class="info-row">
                    <span class="label">Name:</span> {name}
                </div>
                <div class="info-row">
                    <span class="label">Email:</span> <a href="mailto:{user_email}">{user_email}</a>
                </div>
                <div class="info-row">
                    <span class="label">Phone:</span> {phone if phone else 'Not provided'}
                </div>
                <div class="info-row">
                    <span class="label">Apartment Unit:</span> <strong>{apartment_unit}</strong>
                </div>
            </div>
            
            <h3 style="color: #333; margin-top: 20px;">Message:</h3>
            <div class="message-box">
{message}
            </div>
        </div>
        
        <div class="footer">
            This message was sent from the NoFeesApts.com apartment inquiry form.<br>
            Please respond to the user at {user_email}
        </div>
    </div>
</body>
</html>
"""
    
    # Attach both text and HTML versions
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    # Encode message in base64url format required by Gmail API
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {'raw': raw_message}


def send_contact_email(
    name: str,
    user_email: str,
    phone: Optional[str],
    apartment_unit: str,
    message: str
) -> Dict[str, str]:
    """
    Send contact form notification email through Gmail API.
    Includes comprehensive error handling and logging.
    
    Args:
        name: Name of the person inquiring
        user_email: Email address of the person
        phone: Phone number (optional)
        apartment_unit: The apartment unit they're inquiring about
        message: Their message/inquiry
        
    Returns:
        Dict with status and message_id on success
        
    Raises:
        Exception: On email sending failure
    """
    try:
        # Get authenticated Gmail service
        service = get_gmail_service()
        
        # Email configuration
        sender_email = os.getenv("GMAIL_SENDER_EMAIL", "placesfirm@gmail.com")
        recipient_email = os.getenv("GMAIL_RECIPIENT_EMAIL", "placesfirm@gmail.com")
        subject = f"New Apartment Inquiry - Unit {apartment_unit} - From {name}"
        
        # Create message object
        email_message = create_email_message(
            sender_email,
            recipient_email,
            subject,
            name,
            user_email,
            phone,
            apartment_unit,
            message
        )
        
        # Send message through Gmail API
        sent_message = service.users().messages().send(
            userId='me',
            body=email_message
        ).execute()
        
        logger.info(
            f"Email sent successfully to {recipient_email}. "
            f"Message ID: {sent_message['id']}, "
            f"From: {name} ({user_email}), "
            f"Unit: {apartment_unit}"
        )
        
        return {
            "status": "success",
            "message_id": sent_message['id']
        }
        
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        raise Exception(f"Failed to send email via Gmail API: {str(error)}")
    except FileNotFoundError as error:
        logger.error(f"Credentials file error: {error}")
        raise Exception("Gmail credentials not configured. Please add credentials file.")
    except Exception as error:
        logger.error(f"Unexpected error sending email: {error}")
        raise Exception(f"Failed to send email: {str(error)}")


def test_email_service():
    """
    Test function to verify Gmail API setup is working.
    Call this after adding credentials to test the integration.
    """
    try:
        result = send_contact_email(
            name="Test User",
            user_email="test@example.com",
            phone="+12125551234",
            apartment_unit="Test Unit 101",
            message="This is a test email to verify Gmail API integration is working correctly."
        )
        print(f"✅ Test email sent successfully! Message ID: {result['message_id']}")
        return True
    except Exception as e:
        print(f"❌ Test email failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run test when this file is executed directly
    print("Testing Gmail API email service...")
    test_email_service()
