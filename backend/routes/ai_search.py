"""AI search agent routes for NoFeesApts."""
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
import os
import logging
import uuid

from database import db
from models import User, AISearchRequest
from auth_utils import get_current_user, require_admin

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/ai-search")
async def ai_search(request: Request, search_request: AISearchRequest):
    """AI-powered apartment search agent with Google Search grounding"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from serpapi import GoogleSearch
    import re
    import json
    import asyncio
    
    async def get_google_search_context(query: str) -> dict:
        """Fetch real-time market data from Google Search via SerpApi"""
        serpapi_key = os.environ.get('SERPAPI_KEY')
        if not serpapi_key:
            return {"error": "SerpApi not configured"}
        
        try:
            # Run SerpApi search in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            
            def execute_search():
                search = GoogleSearch({
                    "q": f"{query} NYC apartments rent prices 2025",
                    "api_key": serpapi_key,
                    "num": 5,
                    "gl": "us",
                    "hl": "en"
                })
                return search.get_dict()
            
            results = await loop.run_in_executor(None, execute_search)
            
            # Parse relevant info
            organic_results = results.get("organic_results", [])[:3]
            answer_box = results.get("answer_box", {})
            
            context = {
                "search_performed": True,
                "query": query,
                "snippets": [
                    {
                        "title": r.get("title", ""),
                        "snippet": r.get("snippet", ""),
                        "source": r.get("displayed_link", "")
                    }
                    for r in organic_results
                ],
                "answer_box": answer_box.get("snippet") or answer_box.get("answer") if answer_box else None
            }
            return context
            
        except Exception as e:
            return {"error": str(e), "search_performed": False}
    
    try:
        # Get current user if logged in
        user = None
        user_email = None
        try:
            user = await get_current_user(request)
            if user:
                user_email = user.email
        except:
            pass
        
        # Generate session ID if not provided
        session_id = search_request.session_id or str(uuid.uuid4())
        
        # Get database stats for context
        total_units = await db.units.count_documents({'is_available': True})
        total_buildings = await db.buildings.count_documents({})
        
        # Get all units for search context
        units = await db.units.find(
            {'is_available': True},
            {'_id': 0, 'id': 1, 'unit_number': 1, 'rent': 1, 'bedrooms': 1, 'bathrooms': 1, 
             'building_id': 1, 'neighborhood': 1, 'amenities': 1, 'square_feet': 1}
        ).to_list(500)
        
        # Get building info
        buildings = await db.buildings.find({}, {'_id': 0}).to_list(100)
        building_map = {b['id']: b for b in buildings}
        
        # Enrich units with building info
        for unit in units:
            building = building_map.get(unit.get('building_id', ''), {})
            unit['building_name'] = building.get('name', 'Unknown')
            unit['neighborhood'] = building.get('neighborhood', 'Unknown')
            unit['city'] = building.get('city', 'New York')
        
        # Get unique neighborhoods and price ranges
        neighborhoods = list(set(u.get('neighborhood', '') for u in units if u.get('neighborhood')))
        min_rent = min((u.get('rent', 0) for u in units if u.get('rent')), default=0)
        max_rent = max((u.get('rent', 0) for u in units if u.get('rent')), default=0)
        
        # Determine if we should search Google for market context
        query_lower = search_request.message.lower()
        market_keywords = ['average', 'market', 'trend', 'price', 'compare', 'typical', 'worth', 'fair', 'expensive', 'cheap', 'afford', 'neighborhood', 'area', 'best', 'popular', 'safe']
        should_search_google = any(kw in query_lower for kw in market_keywords)
        
        # Get Google search context for market questions
        google_context = {}
        if should_search_google:
            # Extract neighborhood or location from query
            search_term = search_request.message
            for n in neighborhoods:
                if n.lower() in query_lower:
                    search_term = n
                    break
            google_context = await get_google_search_context(search_term)
        
        # Build Google context string for system prompt
        google_context_str = ""
        if google_context.get("search_performed") and google_context.get("snippets"):
            google_context_str = "\n\nREAL-TIME MARKET DATA (from Google Search):\n"
            if google_context.get("answer_box"):
                google_context_str += f"Quick Answer: {google_context['answer_box']}\n\n"
            for snippet in google_context.get("snippets", []):
                google_context_str += f"- {snippet['title']}: {snippet['snippet']} (Source: {snippet['source']})\n"
        
        # Create system prompt with Google context
        system_prompt = f"""You are the NoFeesApts.com AI Search Assistant - a friendly, knowledgeable apartment search expert for NYC, Northern NJ, and PA no-fee apartments.

CURRENT INVENTORY:
- {total_units} no-fee apartments available across {total_buildings} buildings
- Price range: ${min_rent:,.0f} - ${max_rent:,.0f}/month
- Neighborhoods: {', '.join(neighborhoods[:15])}
{google_context_str}
YOUR CAPABILITIES:
1. Search our database of {total_units} verified no-fee listings
2. Answer questions about NYC neighborhoods, apartment hunting tips, and the rental market
3. Help users find apartments that match their criteria (budget, bedrooms, location, amenities)
4. Provide real-time market insights using current data
5. For requests outside our current inventory, mention that you can help find additional options

CONTACT INFORMATION (Always provide when relevant):
- Phone: (646) 408-8048
- Email: placesfirm@gmail.com
- Name: Kiri (AI Expert Leasing Agent)

RESPONSE STYLE:
- You are Kiri, an AI expert leasing agent who helps renters find their perfect no-fee apartment
- Be conversational, helpful, and enthusiastic
- When showing results, be specific about unit details
- When answering market questions, cite the real-time data when available
- If no exact matches, suggest alternatives or offer to help find more options
- For off-site searches or special requests, offer to help directly
- Keep responses concise but informative

AVAILABLE UNITS DATA:
{json.dumps(units[:50], default=str)}

When searching, analyze the user's request and find matching units. Report the count and key details."""

        # Initialize Gemini chat
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        chat = LlmChat(
            api_key=llm_key,
            session_id=session_id,
            system_message=system_prompt
        ).with_model("gemini", "gemini-3-flash-preview")
        
        # Send user message
        user_message = UserMessage(text=search_request.message)
        response = await chat.send_message(user_message)
        
        # Extract analytics from the query
        query_lower = search_request.message.lower()
        
        # Detect neighborhoods mentioned
        neighborhoods_mentioned = [n for n in neighborhoods if n.lower() in query_lower]
        
        # Detect bedrooms
        bedrooms_requested = None
        if 'studio' in query_lower:
            bedrooms_requested = 0
        elif '1 bed' in query_lower or '1br' in query_lower or 'one bed' in query_lower:
            bedrooms_requested = 1
        elif '2 bed' in query_lower or '2br' in query_lower or 'two bed' in query_lower:
            bedrooms_requested = 2
        elif '3 bed' in query_lower or '3br' in query_lower or 'three bed' in query_lower:
            bedrooms_requested = 3
        
        # Detect price range
        price_match = re.findall(r'\$?(\d{1,2}),?(\d{3})', query_lower)
        price_range = None
        if price_match:
            prices = [int(p[0] + p[1]) for p in price_match]
            price_range = {'min': min(prices), 'max': max(prices)} if len(prices) > 1 else {'target': prices[0]}
        
        # Count matching units for analytics
        units_found = 0
        for unit in units:
            matches = True
            if bedrooms_requested is not None and unit.get('bedrooms') != bedrooms_requested:
                matches = False
            if neighborhoods_mentioned and unit.get('neighborhood', '').lower() not in [n.lower() for n in neighborhoods_mentioned]:
                matches = False
            if price_range:
                rent = unit.get('rent', 0)
                if 'min' in price_range and 'max' in price_range:
                    if rent < price_range['min'] or rent > price_range['max']:
                        matches = False
                elif 'target' in price_range:
                    if abs(rent - price_range['target']) > 1000:
                        matches = False
            if matches:
                units_found += 1
        
        # Save search to database
        search_record = {
            'id': str(uuid.uuid4()),
            'session_id': session_id,
            'user_id': user.id if user else None,
            'user_email': user_email,
            'query': search_request.message,
            'response': response,
            'units_found': units_found,
            'neighborhoods_mentioned': neighborhoods_mentioned,
            'price_range': price_range,
            'bedrooms_requested': bedrooms_requested,
            'google_search_used': google_context.get('search_performed', False),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.ai_searches.insert_one(search_record)
        
        return {
            'response': response,
            'session_id': session_id,
            'units_found': units_found,
            'google_grounded': google_context.get('search_performed', False)
        }
        
    except Exception as e:
        logger.error(f"AI Search error: {e}")
        # Fallback response
        return {
            'response': f"I apologize, but I'm having trouble processing your request right now. Please contact me directly at (646) 408-8048 or placesfirm@gmail.com for personalized apartment search assistance!",
            'session_id': search_request.session_id or str(uuid.uuid4()),
            'units_found': 0
        }

@router.get("/admin/ai-searches")
async def get_ai_searches(user: User = Depends(require_admin), limit: int = 100):
    """Get AI search history for admin review"""
    searches = await db.ai_searches.find(
        {},
        {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    return searches

@router.get("/admin/search-analytics")
async def get_search_analytics(user: User = Depends(require_admin)):
    """Get AI search analytics for admin dashboard"""
    
    # Total searches
    total_searches = await db.ai_searches.count_documents({})
    
    # Searches in last 24 hours
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    recent_searches = await db.ai_searches.count_documents({
        'created_at': {'$gte': yesterday.isoformat()}
    })
    
    # Get all searches for analytics
    all_searches = await db.ai_searches.find({}, {'_id': 0}).to_list(1000)
    
    # Most searched neighborhoods
    neighborhood_counts = {}
    for search in all_searches:
        for n in search.get('neighborhoods_mentioned', []):
            neighborhood_counts[n] = neighborhood_counts.get(n, 0) + 1
    top_neighborhoods = sorted(neighborhood_counts.items(), key=lambda x: -x[1])[:10]
    
    # Bedroom preferences
    bedroom_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for search in all_searches:
        br = search.get('bedrooms_requested')
        if br is not None and br in bedroom_counts:
            bedroom_counts[br] += 1
    
    # Price range analysis
    price_searches = [s for s in all_searches if s.get('price_range')]
    avg_target_price = 0
    if price_searches:
        prices = []
        for s in price_searches:
            pr = s.get('price_range', {})
            if 'target' in pr:
                prices.append(pr['target'])
            elif 'min' in pr and 'max' in pr:
                prices.append((pr['min'] + pr['max']) / 2)
        avg_target_price = sum(prices) / len(prices) if prices else 0
    
    # Searches with no matches
    no_match_searches = len([s for s in all_searches if s.get('units_found', 0) == 0])
    
    return {
        'total_searches': total_searches,
        'searches_last_24h': recent_searches,
        'top_neighborhoods': [{'name': n, 'count': c} for n, c in top_neighborhoods],
        'bedroom_preferences': {
            'studio': bedroom_counts[0],
            'one_bed': bedroom_counts[1],
            'two_bed': bedroom_counts[2],
            'three_plus': bedroom_counts[3]
        },
        'avg_target_price': round(avg_target_price, 0),
        'no_match_rate': round(no_match_searches / total_searches * 100, 1) if total_searches > 0 else 0
    }

