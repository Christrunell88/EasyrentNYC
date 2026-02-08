import asyncio
import os
import uuid
import re
from datetime import datetime, timezone
from pathlib import Path

os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

from motor.motor_asyncio import AsyncIOMotorClient
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Load env
env_path = Path('/app/backend/.env')
for line in env_path.read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        key, val = line.split('=', 1)
        os.environ[key.strip()] = val.strip()

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

def normalize_unit_number(unit_number):
    if not unit_number:
        return ''
    normalized = unit_number.upper().strip()
    prefixes = ['UNIT', 'APT', 'APARTMENT', 'SUITE', 'STE', '#', 'NO', 'NUMBER']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
        if normalized.startswith(prefix + ' ') or normalized.startswith(prefix + '.'):
            normalized = normalized[len(prefix)+1:].strip()
    normalized = normalized.lstrip('#.-').strip()
    normalized = re.sub(r'(\d+)\s+([A-Z])', r'\1\2', normalized)
    return normalized

async def standard_crawl_with_stats():
    stats = {
        'listings_discovered': 0,
        'listings_skipped': 0,
        'skip_reasons': [],
        'production_match_count': 0,
        'duplicate_match_count': 0,
        'freshness_blocks': 0,
        'last_seen_filters': 0,
        'successful_inserts': 0,
        'database_written_to': db_name
    }
    
    building = await db.buildings.find_one({}, {'_id': 0})
    
    print('='*70)
    print('  STANDARD CRAWL - 4650 Center Blvd')
    print('='*70)
    print()
    print(f"  Database:       {db_name}")
    print(f"  Building:       {building['name']}")
    print(f"  Building ID:    {building['id']}")
    print(f"  Source URL:     {building.get('source_url', 'N/A')}")
    print()
    
    url = building.get('source_url', '')
    
    production_units = await db.units.find({'building_id': building['id']}, {'_id': 0}).to_list(1000)
    production_unit_map = {}
    for u in production_units:
        norm = normalize_unit_number(u.get('unit_number', ''))
        production_unit_map[norm] = u
    
    print(f'  Production units in building: {len(production_units)}')
    
    staging_units = await db.units_staging.find({'building_id': building['id']}, {'_id': 0}).to_list(1000)
    staging_unit_map = {}
    for u in staging_units:
        norm = normalize_unit_number(u.get('unit_number', ''))
        if norm not in staging_unit_map:
            staging_unit_map[norm] = []
        staging_unit_map[norm].append(u)
    
    print(f'  Existing staging units: {len(staging_units)}')
    print()
    
    print('  Crawling website...')
    print('-'*70)
    
    units_data = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(5000)
            
            frames = page.frames
            iframe_content = None
            for frame in frames:
                if 'rosenyc.com' in frame.url:
                    iframe_content = await frame.content()
                    break
            
            content = iframe_content if iframe_content else await page.content()
            await browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            tables = soup.find_all('table')
            
            seen_units = set()
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                header_row = rows[0]
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                
                has_unit = any('unit' in h or 'residence' in h for h in headers)
                has_rent = any('rent' in h for h in headers)
                
                if not has_unit:
                    continue
                
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 3:
                        continue
                    
                    unit_data = {
                        'unit_number': '',
                        'rent': 0.0,
                        'bedrooms': 0,
                        'bathrooms': 1.0,
                        'square_feet': None,
                        'images': [],
                        'amenities': [],
                        'description': '',
                        'available_date': 'Immediate',
                    }
                    
                    for idx, cell in enumerate(cells):
                        text = cell.get_text(strip=True)
                        header = headers[idx] if idx < len(headers) else ''
                        
                        if 'unit' in header or 'residence' in header or idx == 0:
                            if text and re.match(r'^[0-9]{3,4}[A-Z]?$', text):
                                unit_data['unit_number'] = text
                        
                        if 'rent' in header:
                            rent_matches = re.findall(r'\$([0-9,]+)', text)
                            if rent_matches:
                                unit_data['rent'] = float(rent_matches[0].replace(',', ''))
                        
                        if 'bedroom' in header or 'bed' in header:
                            if 'studio' in text.lower():
                                unit_data['bedrooms'] = 0
                            else:
                                bed_match = re.search(r'(\d+)\s*BR', text, re.I)
                                if bed_match:
                                    unit_data['bedrooms'] = int(bed_match.group(1))
                        
                        if 'bathroom' in header or 'bath' in header:
                            bath_match = re.search(r'(\d+)\s*BA', text, re.I)
                            if bath_match:
                                unit_data['bathrooms'] = float(bath_match.group(1))
                        
                        if 'sq' in header:
                            sqft_match = re.search(r'(\d+)', text)
                            if sqft_match:
                                unit_data['square_feet'] = int(sqft_match.group(1))
                        
                        if 'availability' in header or 'avail' in header:
                            if text and text != 'View':
                                unit_data['available_date'] = text
                    
                    if unit_data['unit_number'] and unit_data['rent'] > 0:
                        if unit_data['unit_number'] not in seen_units:
                            seen_units.add(unit_data['unit_number'])
                            units_data.append(unit_data)
    
    except Exception as e:
        print(f'  ERROR: {e}')
    
    stats['listings_discovered'] = len(units_data)
    print(f'  Listings discovered: {len(units_data)}')
    print()
    
    if units_data:
        print('  DISCOVERED UNITS:')
        for u in units_data:
            print(f"    • {u['unit_number']}: ${u['rent']:,.0f} | {u['bedrooms']}BR | {u.get('square_feet', 'N/A')} sqft")
        print()
    
    print('  PROCESSING UNITS (all checks enabled)')
    print('-'*70)
    
    batch_id = f"standard_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    for unit_data in units_data:
        unit_num = unit_data['unit_number']
        normalized = normalize_unit_number(unit_num)
        skip_reason = None
        
        print(f"  Unit: {unit_num} | ${unit_data['rent']:,.0f} | {unit_data['bedrooms']}BR")
        
        if normalized in production_unit_map:
            stats['production_match_count'] += 1
            prod_unit = production_unit_map[normalized]
            print(f"    → PRODUCTION MATCH: Exists (prod rent: ${prod_unit.get('rent', 0):,.0f})")
        
        if normalized in staging_unit_map:
            for staged in staging_unit_map[normalized]:
                created = staged.get('created_at', '')
                if created:
                    try:
                        created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        age_hours = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
                        if age_hours < 24:
                            stats['freshness_blocks'] += 1
                            skip_reason = f'Freshness block: In staging {age_hours:.1f}h ago'
                            print(f'    → FRESHNESS BLOCK: {age_hours:.1f}h old')
                            break
                    except:
                        pass
        
        if not skip_reason and normalized in staging_unit_map:
            for staged in staging_unit_map[normalized]:
                if staged.get('review_status') == 'rejected':
                    stats['last_seen_filters'] += 1
                    skip_reason = f'Last seen filter: Previously rejected'
                    print(f'    → LAST SEEN FILTER: Rejected')
                    break
        
        if not skip_reason and normalized in staging_unit_map:
            for staged in staging_unit_map[normalized]:
                if staged.get('review_status') == 'pending':
                    stats['duplicate_match_count'] += 1
                    skip_reason = f'Duplicate: Already pending in staging'
                    print(f'    → DUPLICATE: Pending in staging')
                    break
        
        if skip_reason:
            stats['listings_skipped'] += 1
            stats['skip_reasons'].append(f'{unit_num}: {skip_reason}')
            print(f'    ✗ SKIPPED')
        else:
            dup_score = 0.8 if normalized in production_unit_map else 0.0
            matched_prod_id = production_unit_map.get(normalized, {}).get('id')
            
            staging_unit = {
                'id': str(uuid.uuid4()),
                'building_id': building['id'],
                'unit_number': unit_num,
                'normalized_unit_number': normalized,
                'rent': unit_data['rent'],
                'bedrooms': unit_data['bedrooms'],
                'bathrooms': unit_data['bathrooms'],
                'square_feet': unit_data.get('square_feet'),
                'available_date': unit_data.get('available_date', 'Immediate'),
                'amenities': unit_data.get('amenities', []),
                'images': unit_data.get('images', []),
                'description': unit_data.get('description', ''),
                'is_available': True,
                'review_status': 'pending',
                'crawler_source': 'fortysixfifty.com',
                'crawler_batch_id': batch_id,
                'validation_flags': ['likely_duplicate'] if dup_score >= 0.8 else [],
                'duplicate_score': dup_score,
                'matched_production_id': matched_prod_id,
                'raw_data': str(unit_data),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            try:
                await db.units_staging.insert_one(staging_unit)
                stats['successful_inserts'] += 1
                flag = ' [FLAGGED: likely_duplicate]' if dup_score >= 0.8 else ''
                print(f'    ✓ INSERTED{flag}')
            except Exception as e:
                stats['listings_skipped'] += 1
                stats['skip_reasons'].append(f'{unit_num}: Insert error - {e}')
                print(f'    ✗ FAILED: {e}')
    
    print()
    print('='*70)
    print('  STANDARD CRAWL RESULTS')
    print('='*70)
    print(f"  Listings Discovered:      {stats['listings_discovered']}")
    print(f"  Listings Skipped:         {stats['listings_skipped']}")
    print(f"  Production Match Count:   {stats['production_match_count']}")
    print(f"  Duplicate Match Count:    {stats['duplicate_match_count']}")
    print(f"  Freshness Blocks:         {stats['freshness_blocks']}")
    print(f"  Last Seen Filters:        {stats['last_seen_filters']}")
    print(f"  Successful Inserts:       {stats['successful_inserts']}")
    print(f"  Database Written To:      {stats['database_written_to']}")
    print()
    print('  SKIP REASONS (FULL):')
    if stats['skip_reasons']:
        for reason in stats['skip_reasons']:
            print(f'    • {reason}')
    else:
        print('    None')
    print()
    
    final_staging = await db.units_staging.count_documents({})
    print('='*70)
    print('  FINAL COLLECTION COUNTS')
    print('='*70)
    print(f"  {db_name}.units_staging:      {final_staging}")
    print(f"  {db_name}.buildings_staging:  {await db.buildings_staging.count_documents({})}")
    print(f"  {db_name}.units:              {await db.units.count_documents({})}")
    print(f"  {db_name}.buildings:          {await db.buildings.count_documents({})}")
    print('='*70)

if __name__ == "__main__":
    asyncio.run(standard_crawl_with_stats())
