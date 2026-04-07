"""Admin property import routes - search, discovery, crawl, import."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import os
import logging

from database import db
from models import User, PropertySearchRequest, PropertyCrawlRequest, PropertyImportRequest, DiscoverySearchRequest
from auth_utils import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()

# Known management companies with their property/availability URLs
MANAGEMENT_COMPANIES = [
    # === ORIGINAL 12 ===
    {
        "name": "Two Trees Management",
        "website": "https://www.twotreesny.com",
        "availability_url": "https://www.twotreesny.com/availabilities",
        "neighborhoods": ["DUMBO", "Williamsburg", "Brooklyn"],
        "description": "Major Brooklyn developer with luxury no-fee buildings"
    },
    {
        "name": "Rose Associates",
        "website": "https://www.roseassociates.com",
        "availability_url": "https://www.roseassociates.com/availabilities",
        "neighborhoods": ["Manhattan", "Multiple"],
        "description": "Large NYC property manager with diverse portfolio"
    },
    {
        "name": "TF Cornerstone",
        "website": "https://www.tfcornerstone.com",
        "availability_url": "https://www.tfcornerstone.com/apartments",
        "neighborhoods": ["Long Island City", "Manhattan", "Brooklyn"],
        "description": "Major developer in LIC and Manhattan waterfront"
    },
    {
        "name": "Manhattan Skyline",
        "website": "https://www.manhattanskyline.com",
        "availability_url": "https://www.manhattanskyline.com/availability",
        "neighborhoods": ["Chelsea", "Midtown", "Financial District"],
        "description": "Luxury Manhattan no-fee apartments"
    },
    {
        "name": "Gotham Organization",
        "website": "https://www.gothamorg.com",
        "availability_url": "https://www.gothamorg.com/availabilities",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "NYC developer with multiple luxury buildings"
    },
    {
        "name": "Brookfield Properties",
        "website": "https://www.brookfieldproperties.com",
        "availability_url": "https://www.brookfieldproperties.com/en/properties.html",
        "neighborhoods": ["Manhattan", "Multiple"],
        "description": "Major commercial and residential developer"
    },
    {
        "name": "Related Companies",
        "website": "https://www.related.com",
        "availability_url": "https://www.related.com/rentals",
        "neighborhoods": ["Hudson Yards", "Manhattan"],
        "description": "Hudson Yards developer with luxury rentals"
    },
    {
        "name": "Extell Development",
        "website": "https://www.extelldev.com",
        "availability_url": "https://www.extelldev.com/rentals",
        "neighborhoods": ["Manhattan", "Upper West Side"],
        "description": "Luxury Manhattan high-rise developer"
    },
    {
        "name": "LeFrak",
        "website": "https://www.lefrak.com",
        "availability_url": "https://www.lefrak.com/residential",
        "neighborhoods": ["Jersey City", "Queens"],
        "description": "Major developer in Jersey City and Queens"
    },
    {
        "name": "Avalon Bay",
        "website": "https://www.avaloncommunities.com",
        "availability_url": "https://www.avaloncommunities.com/new-york",
        "neighborhoods": ["Multiple NYC Areas"],
        "description": "National apartment developer with NYC presence"
    },
    {
        "name": "Equity Residential",
        "website": "https://www.equityapartments.com",
        "availability_url": "https://www.equityapartments.com/new-york-city",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "Large national REIT with NYC properties"
    },
    {
        "name": "The Durst Organization",
        "website": "https://www.durst.org",
        "availability_url": "https://www.durst.org/residential",
        "neighborhoods": ["Midtown", "Financial District"],
        "description": "Historic NYC developer and property manager"
    },
    # === NEW ADDITIONS ===
    {
        "name": "Silverstein Properties",
        "website": "https://www.silversteinproperties.com",
        "availability_url": "https://www.silversteinproperties.com/residential",
        "neighborhoods": ["Financial District", "WTC", "Manhattan"],
        "description": "World Trade Center developer with luxury residential"
    },
    {
        "name": "SL Green",
        "website": "https://www.slgreen.com",
        "availability_url": "https://www.slgreen.com/properties/residential",
        "neighborhoods": ["Midtown", "Manhattan"],
        "description": "NYC's largest office landlord with residential portfolio"
    },
    {
        "name": "Rockrose Development",
        "website": "https://www.rockrose.com",
        "availability_url": "https://www.rockrose.com/residences",
        "neighborhoods": ["Long Island City", "Manhattan"],
        "description": "Major LIC developer with waterfront properties"
    },
    {
        "name": "Moinian Group",
        "website": "https://www.moinian.com",
        "availability_url": "https://www.moinian.com/residential",
        "neighborhoods": ["Hudson Yards", "Midtown", "Manhattan"],
        "description": "Sky and other luxury Manhattan developments"
    },
    {
        "name": "L+M Development",
        "website": "https://www.lmdevpartners.com",
        "availability_url": "https://www.lmdevpartners.com/portfolio",
        "neighborhoods": ["Harlem", "Brooklyn", "Bronx"],
        "description": "Affordable and market-rate housing developer"
    },
    {
        "name": "Toll Brothers City Living",
        "website": "https://www.tollbrothers.com/city-living",
        "availability_url": "https://www.tollbrothers.com/city-living/new-york",
        "neighborhoods": ["Manhattan", "Brooklyn", "Jersey City"],
        "description": "Luxury condo and rental developer"
    },
    {
        "name": "Property Markets Group (PMG)",
        "website": "https://www.propertymg.com",
        "availability_url": "https://www.propertymg.com/properties",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "Boutique luxury developer in NYC"
    },
    {
        "name": "Hines",
        "website": "https://www.hines.com",
        "availability_url": "https://www.hines.com/properties?region=new-york",
        "neighborhoods": ["Manhattan", "Multiple"],
        "description": "Global real estate firm with NYC residential"
    },
    {
        "name": "Tishman Speyer",
        "website": "https://www.tishmanspeyer.com",
        "availability_url": "https://www.tishmanspeyer.com/rentals",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "Major developer - Rockefeller Center owners"
    },
    {
        "name": "Stonehenge NYC",
        "website": "https://www.stonehengenyc.com",
        "availability_url": "https://www.stonehengenyc.com/apartments",
        "neighborhoods": ["Midtown", "Upper East Side", "Manhattan"],
        "description": "Boutique Manhattan apartment operator"
    },
    {
        "name": "Glenwood Management",
        "website": "https://www.glenwoodnyc.com",
        "availability_url": "https://www.glenwoodnyc.com/available-apartments",
        "neighborhoods": ["Upper East Side", "Midtown", "FiDi"],
        "description": "Luxury Manhattan high-rise apartments"
    },
    {
        "name": "Brodsky Organization",
        "website": "https://www.brodsky.com",
        "availability_url": "https://www.brodsky.com/rentals",
        "neighborhoods": ["Upper West Side", "Manhattan"],
        "description": "Family-owned Manhattan apartment operator"
    },
    {
        "name": "UDR",
        "website": "https://www.udr.com",
        "availability_url": "https://www.udr.com/new-york-city-apartments",
        "neighborhoods": ["Manhattan", "Brooklyn"],
        "description": "National REIT with luxury NYC apartments"
    },
    {
        "name": "Bozzuto",
        "website": "https://www.bozzuto.com",
        "availability_url": "https://www.bozzuto.com/apartments/region/new-york",
        "neighborhoods": ["Jersey City", "Hoboken", "NYC Area"],
        "description": "Property manager with NJ and NYC presence"
    },
    {
        "name": "Ironstate Development",
        "website": "https://www.ironstate.com",
        "availability_url": "https://www.ironstate.com/portfolio",
        "neighborhoods": ["Jersey City", "Hoboken"],
        "description": "Major Jersey City waterfront developer"
    },
    {
        "name": "Mack-Cali (Veris Residential)",
        "website": "https://www.verisresidential.com",
        "availability_url": "https://www.verisresidential.com/apartments",
        "neighborhoods": ["Jersey City", "Weehawken", "NJ Waterfront"],
        "description": "NJ waterfront luxury apartment developer"
    },
    {
        "name": "Applied Companies",
        "website": "https://www.appliedcompanies.com",
        "availability_url": "https://www.appliedcompanies.com/communities",
        "neighborhoods": ["Hoboken", "Jersey City"],
        "description": "NJ luxury apartment communities"
    }
]

# Pattern recognition keywords for no-fee buildings
NO_FEE_PATTERNS = [
    "no fee", "no broker fee", "no broker", "owner pays fee", 
    "net effective", "free rent", "lease-up", "new construction",
    "luxury rental", "luxury apartments", "direct from owner",
    "in-house leasing", "on-site leasing", "management company"
]

# Areas to focus discovery searches
DISCOVERY_AREAS = [
    {"area": "Manhattan", "neighborhoods": ["Chelsea", "Tribeca", "FiDi", "Midtown", "UWS", "UES", "Hudson Yards", "Harlem"]},
    {"area": "Brooklyn", "neighborhoods": ["DUMBO", "Williamsburg", "Brooklyn Heights", "Fort Greene", "Greenpoint", "Downtown Brooklyn"]},
    {"area": "Queens", "neighborhoods": ["Long Island City", "Astoria", "Flushing"]},
    {"area": "New Jersey", "neighborhoods": ["Jersey City", "Hoboken", "Weehawken", "Harrison", "Newark"]},
    {"area": "Pennsylvania", "neighborhoods": ["Philadelphia"]}
]

@router.get("/admin/management-companies")
async def get_management_companies(user: User = Depends(require_admin)):
    """Get list of known management companies for quick search."""
    return {
        "companies": MANAGEMENT_COMPANIES,
        "total": len(MANAGEMENT_COMPANIES)
    }

@router.post("/admin/property-search")
async def property_search(request: PropertySearchRequest, user: User = Depends(require_admin)):
    """
    AI-powered property search that finds building websites using SerpApi.
    Prioritizes known management companies and filters aggregators.
    """
    from serpapi import GoogleSearch
    import asyncio
    
    serpapi_key = os.environ.get('SERPAPI_KEY')
    if not serpapi_key:
        raise HTTPException(status_code=500, detail="SerpApi not configured. Add SERPAPI_KEY to environment.")
    
    try:
        buildings = []
        
        # If searching management companies, return the curated list
        if request.search_type == "management_companies":
            for company in MANAGEMENT_COMPANIES:
                buildings.append({
                    "name": company["name"],
                    "url": company["availability_url"],
                    "domain": company["website"].replace("https://", "").replace("http://", ""),
                    "snippet": f"{company['description']}. Areas: {', '.join(company['neighborhoods'])}",
                    "source": "curated_management_company",
                    "is_management_company": True
                })
            return {
                "query": request.query,
                "results": buildings,
                "total_found": len(buildings),
                "search_type": "management_companies"
            }
        
        loop = asyncio.get_event_loop()
        
        # Enhanced search query with management company patterns
        management_terms = "Two Trees OR Rose Associates OR TF Cornerstone OR Manhattan Skyline OR Gotham OR Related OR Extell OR LeFrak"
        search_query = f"{request.query} ({management_terms}) apartments availability -streeteasy -zillow"
        
        def execute_search():
            search = GoogleSearch({
                "q": search_query,
                "api_key": serpapi_key,
                "num": 20,
                "gl": "us",
                "hl": "en"
            })
            return search.get_dict()
        
        results = await loop.run_in_executor(None, execute_search)
        
        organic_results = results.get("organic_results", [])
        
        # Filter and structure results
        seen_domains = set()
        
        # Skip aggregators and non-building sites (Trulia removed - we now have a dedicated scraper)
        skip_domains = ['streeteasy', 'zillow', 'apartments.com', 'realtor', 
                      'apartmentguide', 'rent.com', 'hotpads', 'facebook', 'instagram',
                      'youtube', 'twitter', 'linkedin', 'yelp', 'wikipedia', 'craigslist',
                      'reddit', 'pinterest', 'glassdoor', 'indeed', 'nytimes', 'curbed']
        
        # Priority domains from management companies
        priority_domains = ['twotreesny.com', 'roseassociates.com', 'tfcornerstone.com', 
                          'manhattanskyline.com', 'gothamorg.com', 'related.com',
                          'extelldev.com', 'lefrak.com', 'durst.org', 'brookfieldproperties.com']
        
        priority_results = []
        other_results = []
        
        for result in organic_results:
            link = result.get("link", "")
            domain = result.get("displayed_link", "").split("/")[0] if result.get("displayed_link") else ""
            
            if any(skip in domain.lower() for skip in skip_domains):
                continue
            
            if domain in seen_domains:
                continue
            seen_domains.add(domain)
            
            # Check if it looks like a building/property website
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()
            
            property_terms = ['apartment', 'rental', 'residence', 'living', 'lease', 'rent', 
                            'bedroom', 'studio', 'availability', 'no fee', 'no broker']
            
            if any(term in title or term in snippet for term in property_terms):
                building_data = {
                    "name": result.get("title", "Unknown Building"),
                    "url": link,
                    "domain": domain,
                    "snippet": result.get("snippet", ""),
                    "source": "google_search",
                    "is_management_company": any(pd in domain.lower() for pd in priority_domains)
                }
                
                # Prioritize management company results
                if building_data["is_management_company"]:
                    priority_results.append(building_data)
                else:
                    other_results.append(building_data)
        
        # Combine with priority results first
        buildings = priority_results + other_results
        
        return {
            "query": request.query,
            "results": buildings[:15],
            "total_found": len(buildings),
            "search_type": "web_search",
            "priority_count": len(priority_results)
        }
        
    except Exception as e:
        logger.error(f"Property search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/admin/property-discovery")
async def property_discovery(request: DiscoverySearchRequest, user: User = Depends(require_admin)):
    """
    AI-powered discovery search to find NEW no-fee buildings and management companies.
    Uses pattern recognition to identify potential no-fee sources.
    """
    from serpapi import GoogleSearch
    import asyncio
    
    serpapi_key = os.environ.get('SERPAPI_KEY')
    if not serpapi_key:
        raise HTTPException(status_code=500, detail="SerpApi not configured.")
    
    try:
        all_results = []
        loop = asyncio.get_event_loop()
        
        # Build discovery queries based on area
        discovery_queries = []
        
        if request.area == "all":
            areas = ["Manhattan NYC", "Brooklyn NYC", "Queens NYC", "Jersey City NJ", "Hoboken NJ"]
        else:
            areas = [request.area]
        
        for area in areas:
            # Query 1: New construction
            if request.search_new_construction:
                discovery_queries.append(f"new luxury rental building {area} 2024 2025 no fee apartments")
            
            # Query 2: Net effective / lease-up specials
            if request.search_net_effective:
                discovery_queries.append(f"no broker fee luxury apartments {area} net effective rent")
            
            # Query 3: Management company search
            discovery_queries.append(f"luxury apartment management company {area} availability rentals")
        
        # Skip aggregators (Trulia removed - we now have a dedicated scraper)
        skip_domains = ['streeteasy', 'zillow', 'apartments.com', 'realtor', 
                      'apartmentguide', 'rent.com', 'hotpads', 'facebook', 'instagram',
                      'youtube', 'twitter', 'linkedin', 'yelp', 'wikipedia', 'craigslist',
                      'reddit', 'pinterest', 'nytimes', 'curbed', 'timeout', 'thrillist']
        
        # Known management domains for priority
        known_domains = [c['website'].replace('https://', '').replace('http://', '').replace('www.', '') 
                        for c in MANAGEMENT_COMPANIES]
        
        seen_domains = set()
        priority_results = []
        new_discoveries = []
        
        # Execute searches (limit to avoid rate limits)
        for query in discovery_queries[:6]:
            def execute_search(q=query):
                search = GoogleSearch({
                    "q": q,
                    "api_key": serpapi_key,
                    "num": 10,
                    "gl": "us",
                    "hl": "en"
                })
                return search.get_dict()
            
            try:
                results = await loop.run_in_executor(None, execute_search)
                organic_results = results.get("organic_results", [])
                
                for result in organic_results:
                    link = result.get("link", "")
                    domain = result.get("displayed_link", "").split("/")[0] if result.get("displayed_link") else ""
                    domain_clean = domain.replace("www.", "").lower()
                    
                    # Skip aggregators
                    if any(skip in domain_clean for skip in skip_domains):
                        continue
                    
                    if domain_clean in seen_domains:
                        continue
                    seen_domains.add(domain_clean)
                    
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    combined_text = (title + " " + snippet).lower()
                    
                    # Pattern recognition score
                    pattern_score = 0
                    matched_patterns = []
                    
                    for pattern in NO_FEE_PATTERNS:
                        if pattern in combined_text:
                            pattern_score += 1
                            matched_patterns.append(pattern)
                    
                    # Check for property-related terms
                    property_terms = ['apartment', 'rental', 'residence', 'living', 'bedroom', 'studio', 'availability']
                    if any(term in combined_text for term in property_terms):
                        pattern_score += 1
                    
                    # Must have some relevance
                    if pattern_score == 0:
                        continue
                    
                    building_data = {
                        "name": title,
                        "url": link,
                        "domain": domain,
                        "snippet": snippet,
                        "pattern_score": pattern_score,
                        "matched_patterns": matched_patterns,
                        "is_known_company": domain_clean in known_domains,
                        "source": "discovery"
                    }
                    
                    if building_data["is_known_company"]:
                        priority_results.append(building_data)
                    else:
                        new_discoveries.append(building_data)
                        
            except Exception as search_error:
                logger.warning(f"Discovery search error for query '{query}': {search_error}")
                continue
        
        # Sort new discoveries by pattern score
        new_discoveries.sort(key=lambda x: x["pattern_score"], reverse=True)
        
        # Combine: known companies first, then new discoveries
        all_results = priority_results + new_discoveries
        
        return {
            "area": request.area,
            "results": all_results[:20],
            "total_found": len(all_results),
            "known_company_count": len(priority_results),
            "new_discovery_count": len(new_discoveries),
            "queries_executed": len(discovery_queries[:6])
        }
        
    except Exception as e:
        logger.error(f"Discovery search error: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

@router.get("/admin/discovery-areas")
async def get_discovery_areas(user: User = Depends(require_admin)):
    """Get available discovery areas and their neighborhoods."""
    return {
        "areas": DISCOVERY_AREAS,
        "patterns": NO_FEE_PATTERNS
    }

@router.post("/admin/property-crawl")
async def property_crawl(request: PropertyCrawlRequest, user: User = Depends(require_admin)):
    """
    Crawl a building website to extract property data.
    Returns structured building and unit information for preview.
    """
    import httpx
    from bs4 import BeautifulSoup
    import re
    
    try:
        # Fetch the page
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = await client.get(request.url, headers=headers)
            response.raise_for_status()
            html = response.text
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract building info
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Look for address patterns
        address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Place|Pl|Drive|Dr|Lane|Ln|Way)[\w\s,]*(?:NY|NJ|PA|New York|New Jersey|Pennsylvania)?[\s,]*\d{5}?'
        address_matches = re.findall(address_pattern, soup.get_text(), re.IGNORECASE)
        address = address_matches[0] if address_matches else ""
        
        # Extract neighborhood from common patterns
        neighborhood = ""
        neighborhood_patterns = ['Chelsea', 'Tribeca', 'DUMBO', 'Williamsburg', 'Long Island City', 
                                'Financial District', 'Midtown', 'Upper West Side', 'Upper East Side',
                                'Brooklyn Heights', 'Fort Greene', 'Astoria', 'Jersey City', 'Hoboken',
                                'Harrison', 'SoHo', 'West Village', 'East Village', 'Harlem', 'Murray Hill']
        page_text = soup.get_text().lower()
        for n in neighborhood_patterns:
            if n.lower() in page_text:
                neighborhood = n
                break
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '') or img.get('data-src', '')
            if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'button', 'arrow', 'sprite']):
                # Make absolute URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(request.url)
                    src = f"{parsed.scheme}://{parsed.netloc}{src}"
                elif not src.startswith('http'):
                    from urllib.parse import urljoin
                    src = urljoin(request.url, src)
                
                if src not in images:
                    images.append(src)
        
        # Extract units/apartments info
        units = []
        
        # Look for pricing patterns
        price_pattern = r'\$[\d,]+(?:\s*[-–]\s*\$[\d,]+)?(?:/mo|/month)?'
        prices = re.findall(price_pattern, soup.get_text())
        
        # Look for bedroom patterns
        bed_pattern = r'(\d+)\s*(?:bed|bedroom|br)|studio'
        beds = re.findall(bed_pattern, soup.get_text(), re.IGNORECASE)
        
        # Look for unit numbers
        unit_pattern = r'(?:unit|apt|apartment|#)\s*([A-Za-z0-9-]+)'
        unit_nums = re.findall(unit_pattern, soup.get_text(), re.IGNORECASE)
        
        # Try to find availability tables or listings
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = ' '.join(cell.get_text() for cell in cells)
                
                # Check if row contains apartment info
                if any(term in row_text.lower() for term in ['bed', 'studio', 'rent', '$']):
                    price_match = re.search(r'\$[\d,]+', row_text)
                    bed_match = re.search(r'(\d+)\s*(?:bed|br)|studio', row_text, re.IGNORECASE)
                    unit_match = re.search(r'(?:unit|apt|#)?\s*([A-Za-z0-9-]+)', row_text, re.IGNORECASE)
                    
                    if price_match:
                        unit_data = {
                            'unit_number': unit_match.group(1) if unit_match else f"Unit-{len(units)+1}",
                            'rent': int(price_match.group().replace('$', '').replace(',', '')),
                            'bedrooms': int(bed_match.group(1)) if bed_match and bed_match.group(1) else 0,
                            'bathrooms': 1,
                            'images': images[:5] if images else []
                        }
                        units.append(unit_data)
        
        # If no units found from tables, create sample units from extracted prices
        if not units and prices:
            for i, price in enumerate(prices[:5]):
                price_clean = int(re.sub(r'[^\d]', '', price.split('-')[0].split('/')[0]))
                if 1000 < price_clean < 50000:  # Reasonable rent range
                    units.append({
                        'unit_number': f"Unit-{i+1}",
                        'rent': price_clean,
                        'bedrooms': int(beds[i]) if i < len(beds) and beds[i].isdigit() else 1,
                        'bathrooms': 1,
                        'images': images[i*2:(i+1)*2] if images else []
                    })
        
        building_data = {
            'name': request.building_name or title_text.split('|')[0].split('-')[0].strip(),
            'address': address,
            'neighborhood': neighborhood,
            'city': 'New York' if 'NY' in address.upper() else 'Unknown',
            'state': 'NY' if 'NY' in address.upper() else ('NJ' if 'NJ' in address.upper() else 'Unknown'),
            'source_url': request.url,
            'images': images[:10]
        }
        
        return {
            'building': building_data,
            'units': units,
            'raw_images': images[:20],
            'crawl_status': 'success',
            'units_found': len(units)
        }
        
    except Exception as e:
        logger.error(f"Property crawl error: {e}")
        return {
            'building': {
                'name': request.building_name or 'Unknown Building',
                'source_url': request.url
            },
            'units': [],
            'crawl_status': 'partial',
            'error': str(e),
            'message': 'Could not automatically extract data. Please enter manually.'
        }

@router.post("/admin/property-import")
async def property_import(request: PropertyImportRequest, user: User = Depends(require_admin)):
    """
    Import crawled property data to staging for review.
    """
    try:
        batch_id = f"import-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        
        # Create staging building
        building_data = {
            'id': str(uuid.uuid4()),
            'name': request.building['name'],
            'address': request.building.get('address', ''),
            'neighborhood': request.building.get('neighborhood', ''),
            'city': request.building.get('city', 'New York'),
            'state': request.building.get('state', 'NY'),
            'zip_code': request.building.get('zip_code', ''),
            'source_url': request.building.get('source_url', ''),
            'images': request.building.get('images', []),
            'crawler_source': request.building.get('source_url', ''),
            'crawler_batch_id': batch_id,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.buildings_staging.insert_one(building_data)
        
        # Create staging units
        units_created = 0
        for unit in request.units:
            unit_data = {
                'id': str(uuid.uuid4()),
                'building_id': building_data['id'],
                'unit_number': unit.get('unit_number', f"Unit-{units_created+1}"),
                'rent': unit.get('rent', 0),
                'bedrooms': unit.get('bedrooms', 0),
                'bathrooms': unit.get('bathrooms', 1),
                'square_feet': unit.get('square_feet'),
                'amenities': unit.get('amenities', []),
                'images': unit.get('images', []),
                'description': unit.get('description', ''),
                'is_available': True,
                'crawler_source': request.building.get('source_url', ''),
                'crawler_batch_id': batch_id,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            await db.units_staging.insert_one(unit_data)
            units_created += 1
        
        return {
            'success': True,
            'building_id': building_data['id'],
            'units_created': units_created,
            'batch_id': batch_id,
            'message': f"Successfully imported {building_data['name']} with {units_created} units to staging."
        }
        
    except Exception as e:
        logger.error(f"Property import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# Note: Router is included after all routes are defined (see below)

# ============ DATABASE SEEDING ENDPOINT ============

