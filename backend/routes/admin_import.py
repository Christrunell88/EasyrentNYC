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
    Crawl a building website to extract property data using Playwright.
    Uses headless browser to render JS-heavy management company sites.
    Returns structured building and unit information for preview.
    """
    from bs4 import BeautifulSoup
    from scrapers.base import get_browser
    from scrapers.generic import crawl as generic_crawl
    import re
    from urllib.parse import urlparse
    
    try:
        logger.info(f"Crawling property URL with Playwright: {request.url}")
        
        # Use Playwright to render the full page (handles JS-heavy sites)
        p, browser = await get_browser()
        html = ""
        images = []
        title_text = ""
        address = ""
        neighborhood = ""
        
        try:
            page = await browser.new_page()
            await page.goto(request.url, wait_until='networkidle', timeout=45000)
            await page.wait_for_timeout(5000)
            
            # Auto-scroll to trigger lazy-loaded content
            await page.evaluate("""
                async () => {
                    const delay = ms => new Promise(r => setTimeout(r, ms));
                    for (let i = 0; i < 5; i++) {
                        window.scrollBy(0, window.innerHeight);
                        await delay(800);
                    }
                    window.scrollTo(0, 0);
                }
            """)
            await page.wait_for_timeout(2000)
            
            # Check for iframes (some sites embed availability in iframes)
            frames = page.frames
            iframe_content = None
            for frame in frames:
                if frame.url != 'about:blank' and 'google' not in frame.url and frame.url != request.url:
                    try:
                        iframe_content = await frame.content()
                        logger.info(f"Found iframe with potential content: {frame.url}")
                        break
                    except Exception:
                        continue
            
            html = iframe_content if iframe_content else await page.content()
            await browser.close()
        finally:
            await p.stop()
        
        if not html:
            return {
                'building': {'name': request.building_name or 'Unknown Building', 'source_url': request.url},
                'units': [], 'crawl_status': 'error', 'units_found': 0,
                'message': 'Could not load page content.'
            }
        
        soup = BeautifulSoup(html, 'html.parser')
        parsed_url = urlparse(request.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Extract page title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else ""
        
        # Extract ALL addresses from page (for multi-building detection)
        address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Place|Pl|Drive|Dr|Lane|Ln|Way)[\w\s,]*(?:NY|NJ|PA|New York|New Jersey|Pennsylvania)?[\s,]*\d{5}?'
        full_text = soup.get_text(separator='\n')
        address_positions = []
        seen_addr_normalized = set()
        for match in re.finditer(address_pattern, full_text, re.IGNORECASE):
            addr = match.group().strip()
            addr_norm = re.sub(r'\s+', ' ', addr).lower()
            if addr_norm not in seen_addr_normalized:
                seen_addr_normalized.add(addr_norm)
                address_positions.append((match.start(), addr))
        
        address = address_positions[0][1] if address_positions else ""
        is_multi_building = len(address_positions) > 1
        logger.info(f"Found {len(address_positions)} unique addresses on page: {[a[1] for a in address_positions[:10]]}")
        
        # Extract neighborhood
        neighborhood_patterns = [
            'Chelsea', 'Tribeca', 'TriBeCa', 'DUMBO', 'Williamsburg', 'Long Island City', 'LIC',
            'Financial District', 'FiDi', 'Midtown', 'Upper West Side', 'UWS', 'Upper East Side', 'UES',
            'Brooklyn Heights', 'Fort Greene', 'Astoria', 'Jersey City', 'Hoboken',
            'Harrison', 'SoHo', 'West Village', 'East Village', 'Harlem', 'Murray Hill',
            'Battery Park', 'Greenpoint', 'Bushwick', 'Crown Heights', 'Prospect Heights',
            'Kips Bay', 'Gramercy', 'NoMad', 'Flatiron', 'Hudson Yards', 'Hell\'s Kitchen',
            'Prospect Park', 'Park Slope', 'Downtown Brooklyn', 'Boerum Hill',
            'Weehawken', 'Union City', 'North Bergen', 'Edgewater'
        ]
        page_text = soup.get_text()
        for n in neighborhood_patterns:
            if n.lower() in page_text.lower():
                neighborhood = n
                break
        
        # Extract images
        for img in soup.find_all('img'):
            src = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy-src', '') or img.get('data-original', '')
            if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'button', 'arrow', 'sprite', 'tracking', 'pixel', 'blank', '1x1']):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = base_url + src
                elif not src.startswith('http'):
                    from urllib.parse import urljoin
                    src = urljoin(request.url, src)
                if src not in images:
                    images.append(src)
        
        # Use the generic scraper's parsing logic on the rendered content
        units = []
        
        # Strategy 1: Parse HTML tables
        from scrapers.generic import _parse_tables, _parse_divs
        units = _parse_tables(soup, base_url)
        
        # Strategy 2: Parse div-based listings
        if not units:
            units = _parse_divs(soup, base_url)
        
        # Strategy 3: Regex fallback on full page text for prices + bedrooms
        if not units:
            logger.info("Table/div parsing found no units, trying regex extraction...")
            text = soup.get_text(separator=' ')
            
            # Find all price mentions
            price_matches = list(re.finditer(r'\$\s*([\d,]+)', text))
            bed_matches = list(re.finditer(r'(\d+)\s*(?:bed(?:room)?s?|br)\b|(?:studio)', text, re.IGNORECASE))
            unit_matches = list(re.finditer(r'(?:unit|apt|apartment|#|suite)\s*([A-Za-z0-9-]+)', text, re.IGNORECASE))
            bath_matches = list(re.finditer(r'(\d+(?:\.\d+)?)\s*(?:bath(?:room)?s?|ba)\b', text, re.IGNORECASE))
            sqft_matches = list(re.finditer(r'([\d,]+)\s*(?:sq\.?\s*ft|sf|sqft)', text, re.IGNORECASE))
            
            # Try to pair prices with bedroom info
            for i, pm in enumerate(price_matches):
                rent = int(pm.group(1).replace(',', ''))
                if rent < 800 or rent > 50000:
                    continue
                
                bedrooms = 1
                if i < len(bed_matches):
                    bm = bed_matches[i]
                    if 'studio' in bm.group(0).lower():
                        bedrooms = 0
                    elif bm.group(1):
                        bedrooms = int(bm.group(1))
                
                bathrooms = 1.0
                if i < len(bath_matches):
                    bathrooms = float(bath_matches[i].group(1))
                
                sqft = None
                if i < len(sqft_matches):
                    sqft = int(sqft_matches[i].group(1).replace(',', ''))
                
                unit_num = f"Unit-{len(units)+1}"
                if i < len(unit_matches):
                    unit_num = unit_matches[i].group(1)
                
                units.append({
                    'unit_number': unit_num,
                    'rent': rent,
                    'bedrooms': bedrooms,
                    'bathrooms': bathrooms,
                    'square_feet': sqft,
                    'images': images[i*2:(i+1)*2] if images else []
                })
        
        # Deduplicate units by rent + bedrooms combo
        seen = set()
        unique_units = []
        for u in units:
            key = (u['rent'], u['bedrooms'], u.get('unit_number', ''))
            if key not in seen:
                seen.add(key)
                unique_units.append(u)
        units = unique_units
        
        # Assign per-unit building addresses on multi-building pages
        if is_multi_building and units and address_positions:
            for unit in units:
                raw = unit.get('raw_data', '')
                if raw:
                    unit_text_snippet = BeautifulSoup(raw, 'html.parser').get_text()[:80]
                    unit_pos = full_text.find(unit_text_snippet) if unit_text_snippet.strip() else -1
                else:
                    unit_pos = -1
                
                if unit_pos >= 0:
                    nearest_addr = address_positions[0][1]
                    for pos, addr in address_positions:
                        if pos <= unit_pos:
                            nearest_addr = addr
                        else:
                            break
                    unit['building_address'] = nearest_addr
                else:
                    unit['building_address'] = address
            
            logger.info(f"Multi-building page: assigned per-unit addresses for {len(units)} units")
        
        # Determine city/state from address or URL
        city = 'New York'
        state = 'NY'
        combined_text = (address + ' ' + page_text[:2000]).upper()
        if any(x in combined_text for x in ['JERSEY CITY', 'HOBOKEN', 'WEEHAWKEN', 'HARRISON, NJ', 'NEW JERSEY']):
            state = 'NJ'
            city = 'Jersey City' if 'JERSEY CITY' in combined_text else 'Hoboken' if 'HOBOKEN' in combined_text else 'New Jersey'
        elif any(x in combined_text for x in [' NJ ', ', NJ', 'NJ 07']):
            state = 'NJ'
            city = 'New Jersey'
        elif any(x in combined_text for x in ['PENNSYLVANIA', ', PA ', 'PA 1']):
            state = 'PA'
            city = 'Pennsylvania'
        elif any(x in combined_text for x in ['BROOKLYN', 'DUMBO', 'WILLIAMSBURG', 'BUSHWICK', 'CROWN HEIGHTS', 'FORT GREENE']):
            city = 'Brooklyn'
            state = 'NY'
        elif any(x in combined_text for x in ['QUEENS', 'LONG ISLAND CITY', 'LIC', 'ASTORIA']):
            city = 'Queens'
            state = 'NY'
        elif any(x in combined_text for x in ['BRONX']):
            city = 'Bronx'
            state = 'NY'
        
        building_data = {
            'name': request.building_name or title_text.split('|')[0].split('-')[0].strip() or 'Unknown Building',
            'address': address,
            'neighborhood': neighborhood,
            'city': city,
            'state': state,
            'source_url': request.url,
            'images': images[:10]
        }
        
        logger.info(f"Crawl complete: {len(units)} units found from {request.url}")
        
        return {
            'building': building_data,
            'units': units,
            'raw_images': images[:20],
            'crawl_status': 'success' if units else 'no_units',
            'units_found': len(units),
            'is_multi_building': is_multi_building,
            'unique_addresses': [a[1] for a in address_positions] if is_multi_building else [],
            'message': None if units else 'No units auto-extracted. You can add units manually below.'
        }
        
    except Exception as e:
        logger.error(f"Property crawl error for {request.url}: {e}", exc_info=True)
        return {
            'building': {
                'name': request.building_name or 'Unknown Building',
                'source_url': request.url,
                'address': '',
                'neighborhood': '',
                'city': 'New York',
                'state': 'NY'
            },
            'units': [],
            'crawl_status': 'error',
            'units_found': 0,
            'error': str(e),
            'message': 'Crawl failed. You can add the building and units manually below.'
        }

@router.post("/admin/property-import")
async def property_import(request: PropertyImportRequest, user: User = Depends(require_admin)):
    """
    Import crawled property data to staging for review.
    Groups units by building_address if provided, creating separate staging buildings.
    """
    try:
        batch_id = f"import-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        source_url = request.building.get('source_url', '')
        building_images = request.building.get('images', [])
        default_building_name = request.building.get('name', 'Unknown Building')
        default_address = request.building.get('address', '')
        default_neighborhood = request.building.get('neighborhood', '')
        default_city = request.building.get('city', 'New York')
        default_state = request.building.get('state', 'NY')
        default_zip = request.building.get('zip_code', '')
        
        # Group units by building_address (for multi-building management company pages)
        building_groups = {}
        for unit in request.units:
            addr = unit.get('building_address', '') or default_address
            bname = unit.get('building_name', '') or default_building_name
            key = addr.strip() if addr.strip() else default_address
            if key not in building_groups:
                building_groups[key] = {'name': bname, 'address': key, 'units': []}
            building_groups[key]['units'].append(unit)
        
        # If only one group, use the top-level building info
        if len(building_groups) <= 1:
            building_groups = {default_address: {
                'name': default_building_name,
                'address': default_address,
                'units': list(request.units)
            }}
        
        total_units_created = 0
        buildings_created = []
        
        for group_addr, group in building_groups.items():
            building_name = group['name'] if group['name'] != default_building_name and len(building_groups) > 1 else (group['address'] or default_building_name)
            building_address = group['address']
            
            building_data = {
                'id': str(uuid.uuid4()),
                'name': building_name,
                'address': building_address,
                'neighborhood': default_neighborhood,
                'city': default_city,
                'state': default_state,
                'zip_code': default_zip,
                'source_url': source_url,
                'images': building_images,
                'crawler_source': source_url,
                'crawler_batch_id': batch_id,
                'review_status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            await db.buildings_staging.insert_one(building_data)
            buildings_created.append(building_name)
            
            for i, unit in enumerate(group['units']):
                unit_images = unit.get('images', [])
                if not unit_images and building_images:
                    imgs_per_unit = max(1, min(3, len(building_images) // max(len(group['units']), 1)))
                    start_idx = (i * imgs_per_unit) % len(building_images)
                    unit_images = building_images[start_idx:start_idx + imgs_per_unit]
                
                unit_data = {
                    'id': str(uuid.uuid4()),
                    'building_id': building_data['id'],
                    'building_name': building_name,
                    'building_address': building_address,
                    'unit_number': unit.get('unit_number', f"Unit-{total_units_created+1}"),
                    'rent': unit.get('rent', 0),
                    'bedrooms': unit.get('bedrooms', 0),
                    'bathrooms': unit.get('bathrooms', 1),
                    'square_feet': unit.get('square_feet'),
                    'amenities': unit.get('amenities', []),
                    'images': unit_images,
                    'description': unit.get('description', ''),
                    'is_available': True,
                    'crawler_source': source_url,
                    'crawler_batch_id': batch_id,
                    'review_status': 'pending',
                    'validation_flags': [],
                    'duplicate_score': 0.0,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }
                await db.units_staging.insert_one(unit_data)
                total_units_created += 1
        
        bldg_summary = ', '.join(buildings_created) if len(buildings_created) > 1 else buildings_created[0]
        logger.info(f"Imported {total_units_created} units across {len(buildings_created)} buildings from batch {batch_id}")
        
        return {
            'success': True,
            'buildings_created': len(buildings_created),
            'building_names': buildings_created,
            'units_created': total_units_created,
            'batch_id': batch_id,
            'message': f'Successfully imported {total_units_created} units across {len(buildings_created)} building(s) ({bldg_summary}) to staging for review'
        }
        
    except Exception as e:
        logger.error(f"Property import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# Note: Router is included after all routes are defined (see below)

# ============ DATABASE SEEDING ENDPOINT ============

