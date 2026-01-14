"""Add TFC Buildings (95 Horatio, 4540 Center Blvd, 595 Dean) and their units to the database"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from uuid import uuid4

load_dotenv('/app/backend/.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

# Building data with their units from TFC crawl
BUILDINGS_DATA = [
    {
        "name": "95 Horatio",
        "address": "95 Horatio St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10014",
        "neighborhood": "West Village",
        "source_url": "https://tfc.com/west-village-nyc/luxury-no-fee-apartments/west-coast",
        "latitude": 40.7370,
        "longitude": -74.0086,
        "amenities": [
            "24-Hour Doorman", "Fitness Center", "Outdoor Children's Play Area",
            "Landscaped Roof Deck", "Sundeck", "BBQ Grills", "Pet-Friendly",
            "Live-in Super", "Valet", "Package Room", "Laundry Room", "Storage",
            "Bicycle Storage", "Elevator", "WiFi", "ATM in Building"
        ],
        "units": [
            {
                "unit_number": "007P",
                "rent": 7895.0,
                "bedrooms": 0,
                "bathrooms": 1.0,
                "amenities": ["Alcove", "Loft", "Open Kitchen", "Dining Area", "Washer Dryer", 
                             "Strip Wood Flooring", "High Ceiling", "Northern Exposure", "City Views"],
                "description": "Beautifully Renovated Loft-Like Studio Apartment Featuring an Open Kitchen, Spacious Dining Area, Large Alcove with Custom French Doors, In-Home Washer/Dryer, Strip Wood Flooring, and Northern Exposure Providing Highline and City Views.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio-St-702-Dining-Area_Kitchen.jpg",
                    "https://cdn.tfc.com/marketing/files/residential/WCCOA1/1110x625/95-Horatio-St-Roofdeck-View.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/2024052420240524_DSC4112-Edit_95-Horatio-St_Roof-Deck_95-Horatio-St_Roof-Deck.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/20250612_DSC9021-Edit_95-Horatio-St_Roof-Deck_Playground_16x9.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio-St_West-Coast_Lobby_Bower_06-2019.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-horatio-model-apt-702-kitchen-dining.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio-St_308_Kitchen.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio_Open-Kitchen_Living-Room.jpg"
                ]
            },
            {
                "unit_number": "004B",
                "rent": 7275.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer", "Strip Wood Flooring", "High Ceiling"],
                "description": "Beautifully renovated 1 bedroom apartment in the heart of the West Village featuring modern finishes, in-home washer/dryer, and excellent natural light.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio-St-702-Dining-Area_Kitchen.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-horatio-model-apt-702-livingroom.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio_Open-Kitchen_Living-Room.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio-St_Model-Apartment.jpg"
                ]
            },
            {
                "unit_number": "010J",
                "rent": 6745.0,
                "bedrooms": 0,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer", "Strip Wood Flooring"],
                "description": "Modern studio apartment in the sought-after West Village neighborhood with contemporary finishes and in-home washer/dryer.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio-St_308_Kitchen.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio-St_Dining-Area_Kitchen.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/95-Horatio-St_Model-Apartment.jpg"
                ]
            }
        ]
    },
    {
        "name": "4540 Center Blvd",
        "address": "4540 Center Blvd",
        "city": "Long Island City",
        "state": "NY",
        "zip_code": "11109",
        "neighborhood": "Long Island City",
        "source_url": "https://tfc.com/long-island-city-lic/luxury-no-fee-apartments/4540-center-blvd",
        "latitude": 40.7447,
        "longitude": -73.9583,
        "amenities": [
            "24-Hour Doorman", "Sundeck", "Pet-Friendly", "Live-in Super", "Valet",
            "Package Room", "Laundry Room", "Bicycle Storage", "Elevator", "WiFi",
            "ATM in Building", "River Views", "City Views", "Parking Garage"
        ],
        "units": [
            {
                "unit_number": "1404",
                "rent": 6795.0,
                "bedrooms": 2,
                "bathrooms": 2.0,
                "amenities": ["Corner Unit", "Open Kitchen", "Dining Area", "Washer Dryer",
                             "Strip Wood Flooring", "Floor to Ceiling Windows", "Balcony",
                             "River Views", "City Views", "Northwest Exposure"],
                "description": "Incredible 2 bed, 2 bath home featuring a huge corner living area and private balcony with breathtaking waterfront views of the Manhattan skyline. This apartment also features a beautiful open kitchen and dining alcove, an in-home washer/dryer, ample closet space, and Northwest exposure.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Open-Kitchen_Balcony.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/2019-06-03_4540_Center_Blvd_307_Balcony_View_tfc.com.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Open-Kitchen_Living-Room_Bedroom.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Open-Kitchen.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Living-Room_Open-Kitchen.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Living-Room.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Lobby_16x9.jpg",
                    "https://cdn.tfc.com/marketing/files/residential/4540A1/1110x625/4540-Center-Boulevard-Exterior.jpg"
                ]
            },
            {
                "unit_number": "3101",
                "rent": 6160.0,
                "bedrooms": 2,
                "bathrooms": 2.0,
                "amenities": ["Corner Unit", "Open Kitchen", "Washer Dryer", "Floor to Ceiling Windows",
                             "River Views", "City Views"],
                "description": "Stunning 2 bedroom 2 bathroom apartment with spectacular Manhattan skyline views and modern finishes throughout.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Open-Kitchen_Balcony.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Open-Kitchen_Living-Room_Bedroom.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Living-Room.jpg"
                ]
            },
            {
                "unit_number": "2207",
                "rent": 4995.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer", "Floor to Ceiling Windows", "City Views"],
                "description": "Beautiful 1 bedroom apartment with city views and modern amenities including in-home washer/dryer.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Open-Kitchen_Living-Room_Bedroom.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Living-Room.jpg"
                ]
            },
            {
                "unit_number": "807",
                "rent": 4391.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer", "City Views"],
                "description": "Modern 1 bedroom apartment with open kitchen and excellent natural light.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Open-Kitchen_Living-Room_Bedroom.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Lobby_16x9.jpg"
                ]
            },
            {
                "unit_number": "2603",
                "rent": 3956.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer", "City Views"],
                "description": "Comfortable 1 bedroom apartment with modern finishes and city views.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Living-Room.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Lobby_16x9.jpg"
                ]
            },
            {
                "unit_number": "202",
                "rent": 3846.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer"],
                "description": "Spacious 1 bedroom apartment on a lower floor with modern amenities.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Open-Kitchen_Living-Room_Bedroom.jpg"
                ]
            },
            {
                "unit_number": "2508",
                "rent": 3754.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer"],
                "description": "Well-appointed 1 bedroom apartment with in-home washer/dryer.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_307_Living-Room.jpg"
                ]
            },
            {
                "unit_number": "3206",
                "rent": 3117.0,
                "bedrooms": 0,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Strip Wood Flooring"],
                "description": "Modern studio apartment on a high floor with beautiful finishes.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/4540-Center-Blvd_Open-Kitchen_Living-Room_Bedroom.jpg"
                ]
            }
        ]
    },
    {
        "name": "595 Dean",
        "address": "595 Dean St",
        "city": "Brooklyn",
        "state": "NY",
        "zip_code": "11238",
        "neighborhood": "Prospect Heights",
        "source_url": "https://tfc.com/prospect-heights-brooklyn/luxury-no-fee-apartments/595-dean",
        "latitude": 40.6810,
        "longitude": -73.9694,
        "amenities": [
            "24-Hour Doorman", "Lobby Lounge", "Fitness Center", "Swimming Pool",
            "Peloton Bikes", "Chelsea Piers", "Club Room", "Resident Lounge",
            "Billiards", "Screening Room", "HomeWork: Co Working Space",
            "Children's Playroom", "Landscaped Roof Deck", "Sundeck", "Water Feature",
            "BBQ Grills", "Pet-Friendly", "Live-in Super", "Package Room",
            "Laundry Room", "Bicycle Storage", "Elevator", "WiFi", "ATM in Building",
            "Parking Garage"
        ],
        "units": [
            {
                "unit_number": "1710",
                "rent": 8105.0,
                "bedrooms": 2,
                "bathrooms": 2.0,
                "amenities": ["Alcove", "Corner Unit", "Window-in-Kitchen", "Walk-In Closet",
                             "Washer Dryer", "Solar Shades", "Southern Exposure", "Western Exposure"],
                "description": "Breathtaking 2 bed, 2 bath apartment featuring a windowed kitchen, spacious living area, corner dining alcove, king-size primary suite with en-suite bath and walk-in closet. This home also boasts in-home laundry, and bright southwestern exposure with amazing views of Brooklyn.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/20230511_DSC7103-Edit_595-Dean-St_703_Living-Room_Bedroom.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/595dean-mr-aug6.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/20230510_DSC6969_595-Dean-St_724_Bedroom_Kitchen_Dining-Area.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/20230510_DSC7006_595-Dean-St_724_Bedroom.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/20230511_DSC7189_595-Dean-St_10th-Fl-Terrace64b1618a5c308.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/595dean-mr-aug.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/595-dean-hero-exterior-west-1000.jpg"
                ]
            },
            {
                "unit_number": "2739",
                "rent": 6733.0,
                "bedrooms": 2,
                "bathrooms": 2.0,
                "amenities": ["Corner Unit", "Window-in-Kitchen", "Washer Dryer", "Southern Exposure"],
                "description": "Spacious 2 bedroom 2 bathroom apartment with windowed kitchen and modern finishes throughout.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/595dean-mr-aug6.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/595dean-mr-aug.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/595dean-mr-aug3.jpg"
                ]
            },
            {
                "unit_number": "2530",
                "rent": 5622.0,
                "bedrooms": 2,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer", "Solar Shades"],
                "description": "Beautiful 2 bedroom apartment with open concept living and modern amenities.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/595dean-mr-aug6.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/595dean-mr-aug2.jpg"
                ]
            },
            {
                "unit_number": "1934",
                "rent": 5272.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer", "Solar Shades", "City Views"],
                "description": "Modern 1 bedroom apartment with excellent Brooklyn views and in-home laundry.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-02.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-01.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/1736-bedroom-01.jpg"
                ]
            },
            {
                "unit_number": "2532",
                "rent": 4538.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer"],
                "description": "Well-appointed 1 bedroom apartment with modern finishes and in-home washer/dryer.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-03.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/1736-bedroom-01.jpg"
                ]
            },
            {
                "unit_number": "713",
                "rent": 4113.0,
                "bedrooms": 1,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Washer Dryer"],
                "description": "Comfortable 1 bedroom apartment in prime Prospect Heights location.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-01.jpg",
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-02.jpg"
                ]
            },
            {
                "unit_number": "1105",
                "rent": 3719.0,
                "bedrooms": 0,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "Solar Shades"],
                "description": "Modern studio apartment with quality finishes and natural light.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-03.jpg"
                ]
            },
            {
                "unit_number": "510",
                "rent": 3317.0,
                "bedrooms": 0,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen"],
                "description": "Efficient studio apartment in the heart of Prospect Heights near Barclays Center.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-01.jpg"
                ]
            },
            {
                "unit_number": "326",
                "rent": 3233.0,
                "bedrooms": 0,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen"],
                "description": "Cozy studio apartment with open kitchen and modern amenities.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-02.jpg"
                ]
            },
            {
                "unit_number": "2733",
                "rent": 3094.0,
                "bedrooms": 0,
                "bathrooms": 1.0,
                "amenities": ["Open Kitchen", "City Views"],
                "description": "High floor studio with excellent Brooklyn views and contemporary finishes.",
                "images": [
                    "https://cdn.tfc.com/marketing/files/building_images/1736-living-03.jpg"
                ]
            }
        ]
    }
]


async def main():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🏢 Adding TFC Buildings to NoFeesApts...\n")
    
    total_units_added = 0
    total_buildings_added = 0
    
    for building_data in BUILDINGS_DATA:
        building_name = building_data["name"]
        
        # Check if building already exists
        existing_building = await db.buildings.find_one({'name': building_name})
        
        if existing_building:
            building_id = existing_building['id']
            print(f"✅ Building '{building_name}' already exists (ID: {building_id})")
        else:
            building_id = str(uuid4())
            building = {
                'id': building_id,
                'name': building_data["name"],
                'address': building_data["address"],
                'city': building_data["city"],
                'state': building_data["state"],
                'zip_code': building_data["zip_code"],
                'neighborhood': building_data["neighborhood"],
                'source_url': building_data["source_url"],
                'latitude': building_data["latitude"],
                'longitude': building_data["longitude"],
                'created_at': datetime.now(timezone.utc).isoformat(),
                'last_crawled': datetime.now(timezone.utc).isoformat()
            }
            await db.buildings.insert_one(building)
            total_buildings_added += 1
            print(f"✅ Created building: {building_name} (ID: {building_id})")
        
        # Add units for this building
        building_amenities = building_data["amenities"]
        
        for unit_data in building_data["units"]:
            unit_number = unit_data["unit_number"]
            
            # Check if unit already exists
            existing_unit = await db.units.find_one({
                'building_id': building_id, 
                'unit_number': unit_number
            })
            
            if existing_unit:
                print(f"   ⚠️ Unit {unit_number} already exists, skipping")
                continue
            
            unit = {
                'id': str(uuid4()),
                'building_id': building_id,
                'unit_number': unit_number,
                'rent': unit_data["rent"],
                'bedrooms': unit_data["bedrooms"],
                'bathrooms': unit_data["bathrooms"],
                'square_feet': None,
                'available_date': 'Immediate',
                'amenities': building_amenities + unit_data["amenities"],
                'description': unit_data["description"],
                'images': unit_data["images"],
                'is_available': True,
                'is_featured': False,
                'latitude': building_data["latitude"],
                'longitude': building_data["longitude"],
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            await db.units.insert_one(unit)
            total_units_added += 1
            bed_type = "Studio" if unit_data["bedrooms"] == 0 else f"{unit_data['bedrooms']}BR"
            print(f"   ✅ Added Unit {unit_number}: {bed_type}/{unit_data['bathrooms']}BA - ${unit_data['rent']:,.0f}/mo")
        
        print()
    
    # Summary
    total_units = await db.units.count_documents({})
    total_buildings = await db.buildings.count_documents({})
    
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"   Buildings added this session: {total_buildings_added}")
    print(f"   Units added this session: {total_units_added}")
    print(f"\n📈 Database totals: {total_buildings} buildings, {total_units} units")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
