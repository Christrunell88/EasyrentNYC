"""
Script to send SEO content draft to placesfirm@gmail.com
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_service import get_gmail_service
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_seo_content_email():
    """Send SEO content HTML file as email attachment"""
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Email details
        sender = "placesfirm@gmail.com"
        recipient = "placesfirm@gmail.com"
        subject = "NoFeesApts.com - SEO Content Draft for Review (9,500+ words)"
        
        # Create message
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        
        # Email body
        body = """
Hello,

Attached is the comprehensive SEO content draft for NoFeesApts.com.

📊 CONTENT SUMMARY:
• 3 Blog Posts: 6,000+ words total
• FAQ Section: 50+ questions, 3,500+ words
• Total: 9,500+ words of SEO-optimized content

📝 BLOG POSTS:
1. Ultimate Guide to Finding No-Fee Apartments in NYC (2,200+ words)
2. Top 10 NYC Neighborhoods for No-Fee Apartments (1,800+ words)
3. NYC Apartment Hunting Checklist (2,000+ words)

❓ FAQ SECTION:
• 50+ comprehensive questions and answers
• Organized by category
• 3,500+ words

✅ SEO FEATURES:
• Target keywords naturally integrated
• Meta titles and descriptions for each post
• Proper heading hierarchy (H1, H2, H3)
• Internal linking opportunities
• Long-form, helpful content
• Local SEO optimized

📂 HOW TO VIEW:
Simply open the attached HTML file in any web browser (Chrome, Firefox, Safari, Edge).

The content is ready for your review. Let me know if you'd like any changes!

Best regards,
E1 AI Agent
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach HTML file
        html_file_path = '/app/SEO_CONTENT_SIMPLE.html'
        
        with open(html_file_path, 'rb') as f:
            attachment = MIMEBase('text', 'html')
            attachment.set_payload(f.read())
        
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename=NoFeesApts_SEO_Content_Draft.html'
        )
        msg.attach(attachment)
        
        # Encode and send
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"\n✅ Email sent successfully!")
        print(f"   To: {recipient}")
        print(f"   Subject: {subject}")
        print(f"   Message ID: {sent_message['id']}")
        print(f"   Attachment: NoFeesApts_SEO_Content_Draft.html")
        print(f"\n📧 Please check your inbox at placesfirm@gmail.com")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to send email: {str(e)}")
        print(f"\n💡 Alternative: Download the file from /app/SEO_CONTENT_SIMPLE.html")
        return False

if __name__ == "__main__":
    send_seo_content_email()
