"""
Dynamic Open Graph meta tags for social media sharing.

Serves lightweight HTML with OG tags to social media crawlers
(Facebook, Twitter, LinkedIn, iMessage, Slack, Discord, etc.)
while regular users get the React SPA.
"""
import re
import logging
from fastapi import Request
from fastapi.responses import HTMLResponse
from database import db

logger = logging.getLogger(__name__)

# Social media crawler User-Agent patterns
CRAWLER_PATTERNS = re.compile(
    r'facebookexternalhit|Facebot|Twitterbot|LinkedInBot|Slackbot|'
    r'WhatsApp|TelegramBot|Discordbot|Pinterest|vkShare|Viber|'
    r'Googlebot|bingbot|Applebot|iMessage|SkypeUriPreview|Embedly|'
    r'Quora Link Preview|redditbot|Rogerbot|SummalyBot|Slurp',
    re.IGNORECASE
)

BASE_URL = "https://www.nofeesapts.com"
DEFAULT_IMAGE = "https://static.prod-images.emergentagent.com/jobs/809a99b2-794a-4bcc-9110-b50857b9c814/images/669505f9b273977a606a8fe480082945aab2c6997e18616eb33fb32a2c5e4eb9.png"
SITE_NAME = "NoFeesApts.com"


def is_crawler(request: Request) -> bool:
    """Check if the request is from a social media crawler."""
    ua = request.headers.get("user-agent", "")
    return bool(CRAWLER_PATTERNS.search(ua))


def _render_og_html(
    title: str,
    description: str,
    url: str,
    image: str = DEFAULT_IMAGE,
    og_type: str = "website",
    extra_meta: str = ""
) -> str:
    """Render minimal HTML page with OG meta tags."""
    title_escaped = title.replace('"', '&quot;').replace('<', '&lt;')
    desc_escaped = description.replace('"', '&quot;').replace('<', '&lt;')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{title_escaped}</title>
<meta name="description" content="{desc_escaped}"/>

<!-- Open Graph / Facebook -->
<meta property="og:type" content="{og_type}"/>
<meta property="og:url" content="{url}"/>
<meta property="og:title" content="{title_escaped}"/>
<meta property="og:description" content="{desc_escaped}"/>
<meta property="og:image" content="{image}"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="og:site_name" content="{SITE_NAME}"/>

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{title_escaped}"/>
<meta name="twitter:description" content="{desc_escaped}"/>
<meta name="twitter:image" content="{image}"/>

{extra_meta}

<!-- Redirect real users to SPA -->
<meta http-equiv="refresh" content="0;url={url}"/>
<link rel="canonical" href="{url}"/>
</head>
<body>
<h1>{title_escaped}</h1>
<p>{desc_escaped}</p>
<p><a href="{url}">View on {SITE_NAME}</a></p>
</body>
</html>"""


def _bed_label(bedrooms: int) -> str:
    if bedrooms == 0:
        return "Studio"
    return f"{bedrooms} Bed"


async def og_unit_page(unit_id: str) -> HTMLResponse | None:
    """Generate OG tags for a unit listing page."""
    unit = await db.units.find_one({"id": unit_id}, {"_id": 0})
    if not unit:
        return None

    building = await db.buildings.find_one(
        {"id": unit.get("building_id")},
        {"_id": 0, "name": 1, "address": 1, "neighborhood": 1, "city": 1, "state": 1}
    )
    bldg_name = building.get("name", "") if building else ""
    neighborhood = building.get("neighborhood", "") if building else ""
    city = building.get("city", "NYC") if building else "NYC"

    beds = _bed_label(unit.get("bedrooms", 1))
    baths = unit.get("bathrooms", 1)
    rent = unit.get("rent", 0)
    unit_num = unit.get("unit_number", "")

    title = f"${rent:,.0f}/mo {beds} | {bldg_name} #{unit_num} — No Fee | {SITE_NAME}"
    location_parts = [x for x in [neighborhood, city] if x]
    location = ", ".join(location_parts)
    description = (
        f"No-fee {beds}/{baths:.0g} Bath apartment at {bldg_name}, {location}. "
        f"${rent:,.0f}/month. No broker fee — save thousands. "
        f"Browse 225+ verified no-fee apartments on {SITE_NAME}."
    )

    images = unit.get("images", [])
    image = images[0] if images else DEFAULT_IMAGE

    url = f"{BASE_URL}/unit/{unit_id}"

    extra = f'<meta property="og:price:amount" content="{rent}"/>\n<meta property="og:price:currency" content="USD"/>'

    html = _render_og_html(title, description, url, image, og_type="article", extra_meta=extra)
    return HTMLResponse(content=html, status_code=200)


# Borough/area page metadata
AREA_OG_DATA = {
    "brooklyn": {
        "title": "No Fee Apartments in Brooklyn — DUMBO, Williamsburg & More",
        "description": "Find no-fee apartments across Brooklyn neighborhoods including DUMBO, Williamsburg, Brooklyn Heights, Fort Greene, and more. Zero broker fees. Updated daily.",
    },
    "manhattan": {
        "title": "No Fee Apartments in Manhattan — Chelsea, Tribeca, UWS & More",
        "description": "Browse no-fee Manhattan apartments in Chelsea, Tribeca, FiDi, Midtown, Upper West Side, and more. Save thousands on broker fees.",
    },
    "queens": {
        "title": "No Fee Apartments in Queens — Long Island City, Astoria & More",
        "description": "Discover no-fee Queens apartments in Long Island City, Astoria, and beyond. Zero broker fees with verified listings updated daily.",
    },
    "new-jersey": {
        "title": "No Fee Apartments in New Jersey — Jersey City, Hoboken & More",
        "description": "Find no-fee NJ apartments in Jersey City, Hoboken, Weehawken, and Harrison. Waterfront luxury without the broker fee.",
    },
    "bronx": {
        "title": "No Fee Apartments in The Bronx — Verified Listings",
        "description": "Browse verified no-fee Bronx apartments. Zero broker fees, updated daily on NoFeesApts.com.",
    },
    "hoboken": {
        "title": "No Fee Apartments in Hoboken, NJ — Waterfront Living, No Broker Fee",
        "description": "Find no-fee Hoboken apartments with stunning waterfront views. Save thousands on broker fees with verified listings.",
    },
    "jersey-city": {
        "title": "No Fee Apartments in Jersey City — Waterfront & Downtown",
        "description": "Discover no-fee Jersey City apartments in waterfront and downtown neighborhoods. Zero broker fees, updated daily.",
    },
}


async def og_area_page(area_slug: str) -> HTMLResponse | None:
    """Generate OG tags for a borough/area page."""
    data = AREA_OG_DATA.get(area_slug)
    if not data:
        return None

    url = f"{BASE_URL}/{area_slug}"
    title = f"{data['title']} | {SITE_NAME}"
    html = _render_og_html(title, data["description"], url)
    return HTMLResponse(content=html, status_code=200)


async def og_neighborhood_page(slug: str) -> HTMLResponse | None:
    """Generate OG tags for a dynamic neighborhood page (/apartments/:slug)."""
    name = slug.replace("-", " ").title()

    count = await db.units.count_documents({"is_available": True})

    title = f"No Fee Apartments in {name} | {SITE_NAME}"
    description = (
        f"Browse verified no-fee apartments in {name}. "
        f"{count}+ listings with zero broker fees, updated daily on {SITE_NAME}."
    )
    url = f"{BASE_URL}/apartments/{slug}"
    html = _render_og_html(title, description, url)
    return HTMLResponse(content=html, status_code=200)


async def og_landing_page() -> HTMLResponse:
    """Generate OG tags for the landing page."""
    count = await db.units.count_documents({"is_available": True})
    title = f"{count}+ No Fee Apartments in NYC & NJ | {SITE_NAME}"
    description = (
        f"Find your perfect apartment with ZERO broker fees. "
        f"Browse {count}+ verified no-fee apartments in Manhattan, Brooklyn, Queens, Bronx & NJ. "
        f"Updated daily. Save $3,000+ on broker fees."
    )
    html = _render_og_html(title, description, f"{BASE_URL}/")
    return HTMLResponse(content=html, status_code=200)


# Route patterns for crawler interception
ROUTE_HANDLERS = [
    (re.compile(r'^/unit/(.+)$'), lambda m: og_unit_page(m.group(1))),
    (re.compile(r'^/apartments/(.+)$'), lambda m: og_neighborhood_page(m.group(1))),
    (re.compile(r'^/(brooklyn|manhattan|queens|new-jersey|bronx|hoboken|jersey-city)$'), lambda m: og_area_page(m.group(1))),
    (re.compile(r'^/$'), lambda m: og_landing_page()),
]


async def handle_crawler_request(request: Request) -> HTMLResponse | None:
    """
    Check if request is from a social media crawler and serve OG tags.
    Returns HTMLResponse for crawlers, None for regular users.
    """
    if not is_crawler(request):
        return None

    path = request.url.path
    for pattern, handler in ROUTE_HANDLERS:
        match = pattern.match(path)
        if match:
            logger.info(f"OG crawler hit: {request.headers.get('user-agent', '')[:60]} -> {path}")
            return await handler(match)

    return None
