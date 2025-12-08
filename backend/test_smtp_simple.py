"""
Simple SMTP test to verify Gmail credentials
"""
import smtplib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

gmail_user = os.getenv('GMAIL_USER')
gmail_password = os.getenv('GMAIL_APP_PASSWORD')

print(f"Testing Gmail SMTP connection...")
print(f"User: {gmail_user}")
print(f"Password length: {len(gmail_password) if gmail_password else 0}")
print(f"Password: {gmail_password}")
print("=" * 80)

try:
    # Try to connect and authenticate
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.set_debuglevel(1)  # Enable debug output
    server.starttls()
    print("\n✅ TLS connection established")
    
    server.login(gmail_user, gmail_password)
    print("\n✅ LOGIN SUCCESSFUL!")
    
    server.quit()
    print("✅ SMTP test passed!")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
    print("\nPossible issues:")
    print("1. App password is incorrect")
    print("2. 2-Step Verification is not enabled on the account")
    print("3. Less secure app access needs to be enabled")
