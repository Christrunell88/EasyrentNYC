"""
The Eugene - Brookfield Properties Building
435 W 31st St, New York, NY 10001
Hudson Yards / Manhattan West, Manhattan
"""

BUILDING_DATA = {
    "id": "5547be5a-88ce-4b06-9353-9f49cca68cf6",
    "name": "The Eugene",
    "address": "435 W 31st St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "neighborhood": "Hudson Yards",
    "borough": "Manhattan",
    "description": """The Eugene is a luxury high-rise in Hudson Yards/Manhattan West featuring world-class amenities. In the heart of NYC's Hudson Yards, explore the charm of your new neighborhood with easy access to The Vessel, Hudson Yards shopping, High Line, and Penn Station.

Amenities include La Palestra fitness center with Peloton bikes, indoor basketball court, two-story rock climbing wall, golf simulator, 31st floor rooftop terrace (Panorama Lounge) with panoramic city views, piano lounge with fireplace, game room with billiards and arcade, spin room, screening room, library lounge, co-working study lounge, children's playroom, social lounge, and outdoor BBQ grills.""",
    "amenities": [
        "24-Hour Doorman",
        "Concierge",
        "La Palestra Fitness Center",
        "Peloton Bikes",
        "Basketball Court",
        "Two-Story Rock Climbing Wall",
        "Golf Simulator",
        "Yoga Room",
        "Spin Room",
        "Rooftop Terrace (Panorama Lounge)",
        "Panoramic City Views",
        "Piano Lounge",
        "Fireplace Lounge",
        "Game Room",
        "Billiards",
        "Arcade",
        "Screening Room",
        "Library Lounge",
        "Study Lounge",
        "HomeWork Co-Working Space",
        "Social Lounge",
        "Children's Playroom",
        "BBQ Grills",
        "Outdoor Terrace",
        "Package Room",
        "Bicycle Storage",
        "Pet-Friendly",
        "Elevator",
        "Parking Garage"
    ],
    "pet_policy": "Pet Friendly ($800 annual non-refundable fee)",
    "website": "https://rent.brookfieldproperties.com/property/the-eugene/",
    "leasing_phone": "332-286-3192",
    "management_company": "Brookfield Properties",
    "latitude": 40.7516,
    "longitude": -73.9992,
    "images": [
        # INTERIOR APARTMENT IMAGES ONLY
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Living-Room-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg",
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Model-Kitchen-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg",
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Kitchen-Living-Space-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg",
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Master-Bedroom-2-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg",
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Lofe-Kitchen-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg",
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Lounge-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg",
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Living-Room-with-a-View-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg",
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Dining-Table-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg",
        "https://rent.brookfieldproperties.com/wp-content/uploads/2024/05/Master-Bedroom-at-The-Eugene-Apartments-in-New-York-NY_Web.jpg"
    ],
    "transportation": {
        "subway": [
            {"station": "34th St/Penn Station", "lines": ["1", "2", "3", "A", "C", "E"], "distance": "5 min walk"},
            {"station": "34th St/Hudson Yards", "lines": ["7"], "distance": "3 min walk"}
        ],
        "train": ["Penn Station (Amtrak, LIRR, NJ Transit)"],
        "bus": ["M34", "M12", "M11"]
    },
    "fees": {
        "application_fee": 20.00,
        "security_deposit": 1000.00,
        "pet_fee_annual": 800.00,
        "bike_storage_cellar": 25.00,  # monthly
        "bike_storage_1st_floor": 35.00,  # monthly
        "club_membership": 185.00,  # monthly per occupant (optional)
        "storage_small": 100.00,  # monthly
        "storage_medium": 200.00,  # monthly
        "storage_large": 300.00  # monthly
    },
    "office_hours": {
        "weekdays": "9:00 AM - 6:00 PM",
        "weekends": "10:00 AM - 5:00 PM"
    }
}

UNITS_DATA = [
    {
        "id": "8dc8a395-a72a-4b8a-92d0-4ee05ee0b8de",
        "unit_number": "SD",
        "rent": 3857,
        "rent_range": "$3,857 - $4,082",
        "bedrooms": 0,
        "bathrooms": 1,
        "description": "Studio apartment featuring open living areas, culinary kitchen with stainless steel appliances, and city views.",
        "has_special_offer": True
    },
    {
        "id": "38eaa9d8-0ecc-45a3-ac9f-04c2209a1c62",
        "unit_number": "1B",
        "rent": 5259,
        "rent_range": "$5,259 - $6,419",
        "bedrooms": 1,
        "bathrooms": 1,
        "description": "Spacious one-bedroom apartment featuring open living areas, master bedroom oasis, and stunning city views."
    },
    {
        "id": "abac5ba2-a304-4a8a-a913-bb00b7cc9468",
        "unit_number": "2A",
        "rent": 8186,
        "rent_range": "$8,186 - $8,216",
        "bedrooms": 2,
        "bathrooms": 2,
        "description": "Luxurious two-bedroom, two-bathroom apartment featuring spacious open living/dining areas and two bedroom suites."
    }
]

# Additional floor plans available at The Eugene:
# Studios: SD ($3,857-$4,082), SF Penthouse ($4,802-$4,812), SG ($4,052-$4,242), SN ($4,422-$4,472), SP ($5,182)
# 1BR: 1B ($5,259-$6,419), 1E ($5,424), 1G ($5,289), 1J ($5,739), 1K ($6,009-$6,074), 1P ($5,694-$5,894)
# 2BR: 2A ($8,186-$8,216), 2B ($7,931)
