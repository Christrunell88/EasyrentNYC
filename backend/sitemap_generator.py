"""
Dynamic sitemap generator for NoFeesApts.com
"""
from datetime import datetime, timezone
from typing import List
import xml.etree.ElementTree as ET


def generate_sitemap(units: List[dict], buildings: List[dict], base_url: str = "https://nofeesapts.com") -> str:
    """
    Generate XML sitemap with all pages
    """
    # Create root element
    urlset = ET.Element(
        "urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    )
    
    # Static pages with their priorities and change frequencies
    static_pages = [
        {"loc": "/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "/auth", "priority": "0.8", "changefreq": "monthly"},
        {"loc": "/dashboard", "priority": "0.9", "changefreq": "daily"},
        {"loc": "/apartments", "priority": "0.9", "changefreq": "daily"},
        {"loc": "/faq", "priority": "0.7", "changefreq": "monthly"},
        {"loc": "/blog", "priority": "0.7", "changefreq": "weekly"},
        {"loc": "/blog/guide-to-no-fee-apartments", "priority": "0.6", "changefreq": "monthly"},
        {"loc": "/blog/best-neighborhoods", "priority": "0.6", "changefreq": "monthly"},
        {"loc": "/blog/apartment-checklist", "priority": "0.6", "changefreq": "monthly"},
    ]
    
    # Add static pages
    for page in static_pages:
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = f"{base_url}{page['loc']}"
        ET.SubElement(url_elem, "lastmod").text = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ET.SubElement(url_elem, "changefreq").text = page["changefreq"]
        ET.SubElement(url_elem, "priority").text = page["priority"]
    
    # Add neighborhood SEO pages (high priority for SEO)
    neighborhoods_set = set()
    for building in buildings:
        if building.get('neighborhood'):
            neighborhood_slug = building['neighborhood'].lower().replace(' ', '-').replace("'", "")
            neighborhoods_set.add((building['neighborhood'], neighborhood_slug))
    
    for name, slug in neighborhoods_set:
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = f"{base_url}/apartments/{slug}"
        ET.SubElement(url_elem, "lastmod").text = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ET.SubElement(url_elem, "changefreq").text = "daily"
        ET.SubElement(url_elem, "priority").text = "0.9"  # High priority for neighborhood pages
    
    # Add legacy location pages for unique neighborhoods
    neighborhoods = set()
    for building in buildings:
        if building.get('neighborhood') and building.get('city'):
            location = f"{building['neighborhood']}-{building['city']}"
            neighborhoods.add(location)
    
    for location in neighborhoods:
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = f"{base_url}/location/{location}"
        ET.SubElement(url_elem, "lastmod").text = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ET.SubElement(url_elem, "changefreq").text = "daily"
        ET.SubElement(url_elem, "priority").text = "0.8"
    
    # Add unit detail pages (high priority - these are the money pages)
    for unit in units:
        url_elem = ET.SubElement(urlset, "url")
        ET.SubElement(url_elem, "loc").text = f"{base_url}/unit/{unit['id']}"
        
        # Use updated_at if available, otherwise created_at
        lastmod = unit.get('updated_at') or unit.get('created_at')
        if lastmod:
            if isinstance(lastmod, str):
                # Parse ISO format and convert to date
                lastmod_date = datetime.fromisoformat(lastmod.replace('Z', '+00:00'))
            else:
                lastmod_date = lastmod
            ET.SubElement(url_elem, "lastmod").text = lastmod_date.strftime("%Y-%m-%d")
        else:
            ET.SubElement(url_elem, "lastmod").text = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        ET.SubElement(url_elem, "changefreq").text = "weekly"
        ET.SubElement(url_elem, "priority").text = "0.9"  # High priority for unit pages
    
    # Generate XML string with proper declaration
    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    
    # Convert to string
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_str += ET.tostring(urlset, encoding="unicode")
    
    return xml_str
