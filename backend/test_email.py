"""
Test script to send a test email using SMTP service
"""
import asyncio
from smtp_email_service import smtp_service

async def test_emails():
    print("Testing SMTP Email Service...")
    print("=" * 80)
    
    # Test sending admin notification
    print("\n1. Testing admin notification email...")
    admin_result = smtp_service.send_inquiry_notification(
        admin_email='placesfirm@gmail.com',
        user_name='Test User',
        user_email='test@example.com',
        user_phone='555-1234',
        message='This is a test inquiry to verify the email system is working correctly.',
        building_name='Test Building',
        building_address='123 Test Street, New York, NY 10001',
        unit_number='5A',
        rent=3500.0,
        bedrooms=1,
        bathrooms=1.0
    )
    
    if admin_result:
        print("✅ Admin notification sent successfully!")
    else:
        print("❌ Failed to send admin notification")
    
    # Test sending user confirmation
    print("\n2. Testing user confirmation email...")
    user_result = smtp_service.send_inquiry_confirmation(
        user_email='placesfirm@gmail.com',  # Sending to you for testing
        user_name='Test User',
        message='This is a test inquiry to verify the email system is working correctly.',
        building_name='Test Building',
        building_address='123 Test Street, New York, NY 10001',
        unit_number='5A',
        rent=3500.0,
        bedrooms=1,
        bathrooms=1.0
    )
    
    if user_result:
        print("✅ User confirmation sent successfully!")
    else:
        print("❌ Failed to send user confirmation")
    
    print("\n" + "=" * 80)
    if admin_result and user_result:
        print("✅ EMAIL SERVICE IS WORKING!")
        print("📧 Check placesfirm@gmail.com for both test emails")
    else:
        print("❌ Some emails failed to send")

if __name__ == "__main__":
    asyncio.run(test_emails())
