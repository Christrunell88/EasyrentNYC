"""
20 Broad Street - Metro Loft / Cetra Ruddy
20 Broad St, New York, NY 10005
Financial District, Manhattan (at Wall Street / NYSE)

Historic building with mid-century modern design by Cetra Ruddy architects.
"""

BUILDING_DATA = {
    "id": "9a7632e7-8e2b-4be2-90a0-6cd04eb639ad",
    "name": "20 Broad Street",
    "address": "20 Broad St",
    "city": "New York",
    "state": "NY",
    "zip": "10005",
    "neighborhood": "Financial District",
    "borough": "Manhattan",
    "description": """Located at the intersection of Wall Street and the New York Stock Exchange, 20 Broad Street offers elevated living in the heart of Manhattan's Financial District.

With mid-century modern style in mind, architects Cetra Ruddy carefully designed this historic property with abstract brass, handsome marble, and custom bookshelves creating a warm lobby greeting.

Residences feature 9'+ ceilings with grand picture windows capturing views of the neighborhood's architectural history, stripped oak flooring, in-ceiling lighting, and washers/dryers in every home.

The Sky Lounge and Rooftop Terrace provide intimate views of historic Downtown, the Harbor, and beyond, with opportunities to screen movies on the lawn and barbecue with friends. The Game Room and Lounge allow for social occasions, while the Library offers quiet time. A yoga studio and state-of-the-art Technogym Fitness Center complete the amenity package.""",
    "amenities": [
        "24-Hour Concierge",
        "Sky Lounge",
        "Rooftop Terrace",
        "Outdoor Theater",
        "Green Lawn & Grills",
        "Technogym Fitness Center",
        "Yoga Studio",
        "Children's Playroom",
        "Library",
        "Game Room & Lounge",
        "Keyless Entry",
        "Resident Storage",
        "Bicycle Storage",
        "Pet Friendly",
        "Elevator"
    ],
    "apartment_features": [
        "9'+ Ceilings",
        "Grand Picture Windows",
        "In-Ceiling Lighting",
        "Stripped Oak Flooring",
        "Washers & Dryers",
        "Custom Italian Cabinetry",
        "Sleek Painted Appliances",
        "Quartz Countertops & Backsplash",
        "Glass Showers",
        "Double Vanities (select units)",
        "Private Outdoor Space (select units)"
    ],
    "pet_policy": "Pet Friendly ($50/pet/month)",
    "website": "https://20broadst.com",
    "management_company": "Metro Loft",
    "architect": "Cetra Ruddy",
    "latitude": 40.7069,
    "longitude": -74.0113,
    "images": [
        "https://20broadst.com/assets/images/cache/20-Broad-Unit-622-Living-room-staged-corrected-DS-efbb9f71c88af907ec674854f1aff16e.jpg",
        "https://20broadst.com/assets/images/cache/20-Broad-Unit-622-Kitchen-staged-corrected-DS-71720817626ec6dbcc510125e601bd97.jpg",
        "https://20broadst.com/assets/images/cache/20-Broad-Unit-622-First-bedroom-staged-corrected-DS-2-e09d1f97d60c015118e7d897b37bc619.jpg",
        "https://20broadst.com/assets/images/cache/20-Broad-Unit-1601-Balcony_staged2_IK-81d52eeb9045a943137a13be82397d13.jpg",
        "https://20broadst.com/assets/images/cache/20-Broad-Unit-1601-Kitchen_staged_IK-1-ff3f7455c04ec33de07b08a1e106f654.jpg",
        "https://20broadst.com/assets/images/cache/featured_gallery_1-d9c21734c1804078b9e4ccc9af150ecb.jpg",
        "https://20broadst.com/assets/images/cache/lobby-b9b9e6820be8dadc7fe18e0ed8a31aa2.jpg"
    ],
    "transportation": {
        "subway": [
            {"station": "Wall St", "lines": ["2", "3"], "distance": "1 min walk"},
            {"station": "Broad St", "lines": ["J", "Z"], "distance": "1 min walk"},
            {"station": "Rector St", "lines": ["R", "W"], "distance": "3 min walk"},
            {"station": "Fulton St", "lines": ["2", "3", "4", "5", "A", "C", "J", "Z"], "distance": "5 min walk"}
        ],
        "bus": ["M5", "M15", "M20"]
    },
    "fees": {
        "application_fee": "$20 per applicant",
        "community_amenity_fee": "$75/month per leaseholder",
        "pet_rent": "$50/pet/month",
        "storage_rental": "$250/month"
    }
}

UNITS_DATA = [
    {
        "id": "9b6a41c4-6864-42b4-83b8-8fa45b8fd24b",
        "unit_number": "0213",
        "rent": 4202,
        "total_monthly": 4602,  # includes $75 community fee + $400 other fees
        "bedrooms": 0,
        "bathrooms": 1,
        "sqft": 524,
        "available_date": "January 24",
        "lease_term": "15 months",
        "floor_plan": "20bs10bt",
        "description": "Bright studio apartment with 9'+ ceilings and grand picture windows offering views of historic Downtown Manhattan. Features stripped oak flooring, in-ceiling lighting, custom Italian cabinetry, quartz countertops, and in-unit washer/dryer.",
        "features": [
            "9' Ceilings",
            "Grand Picture Windows",
            "Stripped Oak Flooring",
            "In-Ceiling Lighting",
            "Custom Italian Cabinetry",
            "Quartz Countertops",
            "Washer/Dryer",
            "Glass Shower"
        ],
        "images": [
            "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/mdcpaquu_20%20Broad%20LIving%20Room.jpg",
            "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/h8y18ctm_20%20Broad%20Street%20Kitchen%20studio.jpg",
            "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/fjams7rs_20%20Broad%20Bath.jpg"
        ],
        "source_url": "https://20broadst.com/floorplans/unit-b27703006c884487ac0c8ccbed197005/",
        "no_fee": True
    }
]

# ============ IMAGE LIBRARY FOR NEW LISTINGS ============
# Use these images for future unit listings at 20 Broad Street

IMAGES_LIBRARY = {
    "living_room": "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/mdcpaquu_20%20Broad%20LIving%20Room.jpg",
    "kitchen_studio": "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/h8y18ctm_20%20Broad%20Street%20Kitchen%20studio.jpg",
    "bath": "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/fjams7rs_20%20Broad%20Bath.jpg",
    "bedroom_1": "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/krjvwfb2_20%20Broad%20Bedroom.jpg",
    "bedroom_2": "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/ddnfu4yk_20%20Broad%20Bedroom%202.jpg",
    "bedroom_3": "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/96bok48w_20%20Broad%20Bedroom%203.jpg",
    "office": "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/n91c1vyj_20%20Broad%20Office.jpg",
    "terrace": "https://customer-assets.emergentagent.com/job_b77f5f3c-00e4-44d8-860f-4562e00e9632/artifacts/zep6aekf_20%20Broad%20Terrace.jpg"
}

# Usage Guide:
# - Studios: living_room, kitchen_studio, bath (NO bedroom)
# - 1BR: living_room, kitchen_studio, bedroom_1, bath, (optional: office or terrace)
# - 2BR: living_room, kitchen_studio, bedroom_1, bedroom_2, bath, (optional: office or terrace)

# Floor Plans Available:
# Studios: 20bs10e, 20bs10i, 20bs10bd, 20bs10bo, 20bs10bt, 20bs10ce, 20bs10cj
# 1BR: 20ba10f, 20ba10p, 20ba10bh
# 2BR: Various

# Note: Total Monthly Leasing Price includes base rent + $75 community amenity fee + other mandatory fees
# Check https://20broadst.com/floorplans/ for current availability
