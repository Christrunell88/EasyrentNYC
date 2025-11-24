"""
Export all units to CSV and send via Gmail API
"""
import asyncio
import csv
import os
from motor.motor_asyncio import AsyncIOMotorClient
from email_service import send_contact_email, get_gmail_service, create_email_message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64
from datetime import datetime

async def export_units_to_csv():
    """Export all units with building info to CSV"""
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Fetching units from database...")
    
    # Fetch all units
    units = await db.units.find({}, {"_id": 0}).to_list(1000)
    
    # Fetch all buildings for reference
    buildings = await db.buildings.find({}, {"_id": 0}).to_list(1000)
    buildings_dict = {b['id']: b for b in buildings}
    
    print(f"Found {len(units)} units")
    
    # Create CSV file
    csv_filename = '/tmp/nofeesapts_units.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Unit ID',
            'Building Name',
            'Building Address',
            'Neighborhood',
            'City',
            'State',
            'Zip Code',
            'Unit Number',
            'Rent',
            'Bedrooms',
            'Bathrooms',
            'Square Feet',
            'Available Date',
            'Description',
            'Amenities',
            'Number of Images',
            'Has Real Images',
            'Source URL',
            'Available'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for unit in units:
            building = buildings_dict.get(unit.get('building_id'), {})
            
            # Check if unit has real images (not placeholder)
            has_real_images = False
            images = unit.get('images', [])
            if images:
                # Check if images are not Unsplash placeholders
                has_real_images = not any('unsplash' in img.lower() for img in images)
            
            writer.writerow({
                'Unit ID': unit.get('id', ''),
                'Building Name': building.get('name', ''),
                'Building Address': building.get('address', ''),
                'Neighborhood': building.get('neighborhood', ''),
                'City': building.get('city', ''),
                'State': building.get('state', ''),
                'Zip Code': building.get('zip_code', ''),
                'Unit Number': unit.get('unit_number', ''),
                'Rent': unit.get('rent', ''),
                'Bedrooms': unit.get('bedrooms', ''),
                'Bathrooms': unit.get('bathrooms', ''),
                'Square Feet': unit.get('square_feet', ''),
                'Available Date': unit.get('available_date', ''),
                'Description': unit.get('description', '')[:200] if unit.get('description') else '',  # Truncate long descriptions
                'Amenities': ', '.join(unit.get('amenities', [])),
                'Number of Images': len(images),
                'Has Real Images': 'Yes' if has_real_images else 'No',
                'Source URL': building.get('source_url', ''),
                'Available': 'Yes' if unit.get('is_available', True) else 'No'
            })
    
    print(f"CSV created: {csv_filename}")
    
    client.close()
    return csv_filename, len(units)

def send_csv_via_gmail(csv_filename, num_units):
    """Send CSV file as email attachment via Gmail API"""
    try:
        # Get Gmail service
        service = get_gmail_service()
        
        # Create message
        sender_email = os.getenv("GMAIL_SENDER_EMAIL", "placesfirm@gmail.com")
        recipient_email = "placesfirm@gmail.com"
        subject = f"NoFeesApts.com - Complete Unit Listing ({num_units} Units)"
        
        # Create multipart message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Email body
        body = f"""
Hello!

Here is the complete listing of all {num_units} apartment units from NoFeesApts.com.

The attached CSV file includes:
- Unit details (rent, bedrooms, bathrooms, etc.)
- Building information (name, address, neighborhood)
- Amenities
- Image availability status
- Availability status

You can open this file in:
- Google Sheets (File → Import)
- Microsoft Excel
- Any spreadsheet application

Export Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

Best regards,
NoFeesApts.com System
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach CSV file
        with open(csv_filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename=NoFeesApts_Units_{datetime.now().strftime("%Y%m%d")}.csv'
        )
        
        msg.attach(part)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        # Send message
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"\n✅ Email sent successfully!")
        print(f"Message ID: {sent_message['id']}")
        print(f"Sent to: {recipient_email}")
        print(f"Attachment: {num_units} units in CSV format")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("="*80)
    print("📊 NoFeesApts.com - Unit Export & Email")
    print("="*80)
    print()
    
    # Export units to CSV
    csv_filename, num_units = await export_units_to_csv()
    
    print()
    print("📧 Sending CSV via email...")
    
    # Send via Gmail
    success = send_csv_via_gmail(csv_filename, num_units)
    
    if success:
        print()
        print("="*80)
        print("🎉 SUCCESS!")
        print("="*80)
        print(f"✅ {num_units} units exported to CSV")
        print(f"✅ Email sent to placesfirm@gmail.com")
        print(f"✅ Check your inbox for the attachment")
        print()
    else:
        print()
        print("❌ Failed to send email")
        print(f"But CSV file is available at: {csv_filename}")

if __name__ == "__main__":
    asyncio.run(main())
