import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowLeft, ChevronRight, ArrowRight } from 'lucide-react';
import { API } from '../config/api';

// Related neighborhoods mapping for internal linking
const relatedNeighborhoods = {
  'long-island-city': ['williamsburg', 'dumbo', 'midtown-west', 'jersey-city'],
  'financial-district': ['tribeca', 'battery-park-city', 'dumbo', 'jersey-city'],
  'chelsea': ['west-village', 'midtown-west', 'tribeca', 'hudson-yards'],
  'tribeca': ['financial-district', 'chelsea', 'west-village', 'soho'],
  'midtown-west': ['chelsea', 'upper-west-side', 'hells-kitchen', 'hudson-yards'],
  'williamsburg': ['dumbo', 'long-island-city', 'greenpoint', 'bushwick'],
  'dumbo': ['williamsburg', 'brooklyn-heights', 'financial-district', 'long-island-city'],
  'upper-west-side': ['upper-east-side', 'midtown-west', 'harlem', 'morningside-heights'],
  'west-village': ['chelsea', 'tribeca', 'soho', 'greenwich-village'],
  'prospect-heights': ['fort-greene', 'crown-heights', 'park-slope', 'clinton-hill'],
  'harrison': ['jersey-city', 'hoboken', 'newark', 'long-island-city'],
  'jersey-city': ['hoboken', 'harrison', 'financial-district', 'dumbo'],
  'hoboken': ['jersey-city', 'harrison', 'west-village', 'tribeca']
};

// Neighborhood display names for links
const neighborhoodNames = {
  'long-island-city': 'Long Island City',
  'financial-district': 'Financial District',
  'chelsea': 'Chelsea',
  'tribeca': 'Tribeca',
  'midtown-west': 'Midtown West',
  'williamsburg': 'Williamsburg',
  'dumbo': 'DUMBO',
  'upper-west-side': 'Upper West Side',
  'west-village': 'West Village',
  'prospect-heights': 'Prospect Heights',
  'harrison': 'Harrison',
  'jersey-city': 'Jersey City',
  'hoboken': 'Hoboken',
  'fort-greene': 'Fort Greene',
  'brooklyn-heights': 'Brooklyn Heights',
  'greenpoint': 'Greenpoint',
  'soho': 'SoHo',
  'hudson-yards': 'Hudson Yards',
  'upper-east-side': 'Upper East Side',
  'battery-park-city': 'Battery Park City',
  'hells-kitchen': "Hell's Kitchen",
  'greenwich-village': 'Greenwich Village',
  'crown-heights': 'Crown Heights',
  'park-slope': 'Park Slope',
  'clinton-hill': 'Clinton Hill',
  'harlem': 'Harlem',
  'morningside-heights': 'Morningside Heights',
  'bushwick': 'Bushwick',
  'newark': 'Newark'
};

// Neighborhood descriptions for SEO - includes Q&A, facts, and listicles
const neighborhoodDescriptions = {
  'long-island-city': {
    title: 'Long Island City',
    description: 'Long Island City (LIC) offers stunning Manhattan skyline views, waterfront parks, and easy subway access. A hub for young professionals and artists.',
    highlights: ['Manhattan skyline views', '7 train to Midtown in 10 min', 'Waterfront parks', 'Growing restaurant scene'],
    faqs: [
      { q: 'What is the average rent in Long Island City?', a: 'Average rent in LIC ranges from $2,800 for studios to $4,500 for 2-bedrooms. No-fee apartments can save you 12-15% of annual rent in broker fees.' },
      { q: 'Is Long Island City safe?', a: 'Yes, LIC is considered one of the safest neighborhoods in Queens with low crime rates and well-lit streets, especially near the waterfront.' },
      { q: 'How long is the commute from LIC to Manhattan?', a: 'The 7 train gets you to Times Square in 10 minutes and Grand Central in 12 minutes. The E/M trains reach Midtown in 15 minutes.' }
    ],
    facts: ['LIC has over 2 miles of waterfront parkland', 'Home to MoMA PS1 contemporary art museum', 'Fastest-growing neighborhood in NYC since 2010'],
    topReasons: ['No broker fee apartments available', 'Stunning Manhattan skyline views', 'Quick subway access to Midtown', 'More space for your money than Manhattan', 'Thriving food and art scene']
  },
  'financial-district': {
    title: 'Financial District',
    description: 'The Financial District features historic architecture, luxury high-rises, and proximity to Wall Street. Cobblestone streets meet modern amenities.',
    highlights: ['Historic architecture', 'Steps from Wall Street', 'Easy PATH access to NJ', 'Waterfront dining'],
    faqs: [
      { q: 'What is the average rent in the Financial District?', a: 'FiDi rents average $3,200 for studios and $5,500 for 2-bedrooms. Many luxury buildings offer no-fee apartments with amenities.' },
      { q: 'Is the Financial District good for families?', a: 'Yes, FiDi has become family-friendly with new schools, Pier 25 playground, and proximity to Battery Park. Weekend crowds are minimal.' },
      { q: 'What subway lines serve the Financial District?', a: 'FiDi is served by 2/3, 4/5, A/C, J/Z, R/W, and 1 trains, plus the PATH to New Jersey. It\'s one of NYC\'s best-connected areas.' }
    ],
    facts: ['Over 60,000 residents call FiDi home', 'Home to One World Trade Center', 'Stone Street is NYC\'s first paved street (1658)'],
    topReasons: ['Luxury amenity buildings', 'Historic cobblestone streets', 'Easy commute anywhere in NYC', 'Waterfront living at Battery Park', 'No broker fee options available']
  },
  'chelsea': {
    title: 'Chelsea',
    description: 'Chelsea is NYC\'s art gallery capital with the High Line, excellent restaurants, and beautiful brownstones. A vibrant, walkable neighborhood.',
    highlights: ['The High Line', '200+ art galleries', 'Chelsea Market', 'Tree-lined streets'],
    faqs: [
      { q: 'What is the average rent in Chelsea?', a: 'Chelsea rents average $3,500 for studios and $5,800 for 1-bedrooms. It\'s one of Manhattan\'s most desirable neighborhoods. For lower rents with similar vibes, consider the West Village or Midtown West.' },
      { q: 'What is Chelsea known for?', a: 'Chelsea is famous for its 200+ art galleries, the High Line elevated park, Chelsea Market, and vibrant LGBTQ+ community. It borders the West Village and Midtown West.' },
      { q: 'Is Chelsea walkable?', a: 'Chelsea has a Walk Score of 99/100, making it one of NYC\'s most walkable neighborhoods with easy access to shops, dining, and transit. Similar walkability can be found in Tribeca and the West Village.' }
    ],
    facts: ['The High Line attracts 8 million visitors annually', 'Chelsea has over 200 art galleries', 'Chelsea Market was once a Nabisco factory'],
    topReasons: ['World-class art galleries', 'The High Line at your doorstep', 'Chelsea Market dining', 'Tree-lined brownstone streets', 'No-fee luxury apartments']
  },
  'tribeca': {
    title: 'Tribeca',
    description: 'Tribeca is one of NYC\'s most desirable neighborhoods with converted lofts, celebrity residents, and upscale dining.',
    highlights: ['Converted loft spaces', 'Robert De Niro\'s restaurants', 'Cobblestone streets', 'Hudson River Park'],
    faqs: [
      { q: 'Why is Tribeca so expensive?', a: 'Tribeca features converted industrial lofts with high ceilings, celebrity residents, top schools, and some of NYC\'s best restaurants.' },
      { q: 'What celebrities live in Tribeca?', a: 'Notable residents include Taylor Swift, Beyoncé, Ryan Reynolds, and Robert De Niro, who helped revitalize the neighborhood.' },
      { q: 'Is Tribeca family-friendly?', a: 'Yes, Tribeca is one of NYC\'s most family-friendly neighborhoods with top-rated schools, safe streets, and numerous playgrounds.' }
    ],
    facts: ['Tribeca has the highest concentration of celebrity residents', 'Home to the Tribeca Film Festival', 'Median home price exceeds $3 million'],
    topReasons: ['Converted loft apartments', 'Celebrity neighborhood', 'Top-rated schools', 'Cobblestone charm', 'Hudson River Park access']
  },
  'midtown-west': {
    title: 'Midtown West',
    description: 'Midtown West offers convenience to Times Square, Hudson Yards, and Penn Station. Perfect for commuters and entertainment lovers.',
    highlights: ['Hudson Yards', 'Theater District', 'Penn Station access', 'Restaurant Row'],
    faqs: [
      { q: 'What is Midtown West known for?', a: 'Midtown West is home to Hudson Yards, the Theater District, Penn Station, and Hell\'s Kitchen\'s famous Restaurant Row.' },
      { q: 'Is Midtown West noisy?', a: 'While Times Square is busy, residential blocks west of 9th Avenue are surprisingly quiet with tree-lined streets.' },
      { q: 'What is the commute from Midtown West?', a: 'You\'re already in Midtown! Penn Station offers NJ Transit, LIRR, and Amtrak. Multiple subway lines serve the area.' }
    ],
    facts: ['Hudson Yards cost $25 billion to develop', 'Home to 40+ Broadway theaters', 'Restaurant Row has 30+ dining options'],
    topReasons: ['Walk to work in Midtown', 'Broadway at your doorstep', 'Hudson Yards shopping', 'Every subway line nearby', 'No-fee buildings available']
  },
  'williamsburg': {
    title: 'Williamsburg',
    description: 'Williamsburg is Brooklyn\'s trendiest neighborhood with waterfront parks, indie boutiques, and a thriving nightlife scene.',
    highlights: ['Domino Park', 'Bedford Avenue shops', 'L train to Manhattan', 'Rooftop bars'],
    faqs: [
      { q: 'What is Williamsburg Brooklyn known for?', a: 'Williamsburg is known for its hipster culture, craft breweries, vintage shops, waterfront parks, and thriving music scene.' },
      { q: 'How far is Williamsburg from Manhattan?', a: 'The L train reaches Union Square in 15 minutes. The Williamsburg Bridge connects to the Lower East Side for easy biking.' },
      { q: 'Is Williamsburg expensive?', a: 'Williamsburg rents are comparable to parts of Manhattan, averaging $3,200 for studios. No-fee apartments offer significant savings.' }
    ],
    facts: ['Bedford Avenue is Brooklyn\'s busiest shopping street', 'Domino Park opened in 2018 on former sugar refinery land', 'Home to Brooklyn Brewery'],
    topReasons: ['Waterfront living at Domino Park', 'Vibrant nightlife scene', 'Quick L train to Manhattan', 'Brooklyn\'s best restaurants', 'No broker fee options']
  },
  'dumbo': {
    title: 'DUMBO',
    description: 'DUMBO (Down Under the Manhattan Bridge Overpass) features iconic views, tech startups, and converted warehouse lofts.',
    highlights: ['Brooklyn Bridge views', 'Jane\'s Carousel', 'Tech hub', 'Cobblestone streets'],
    faqs: [
      { q: 'Why is DUMBO so popular?', a: 'DUMBO offers iconic Brooklyn Bridge views, converted warehouse lofts, cobblestone streets, and a thriving tech/startup scene.' },
      { q: 'Is DUMBO a good place to live?', a: 'DUMBO is excellent for young professionals seeking luxury lofts, waterfront parks, and a creative community near Manhattan.' },
      { q: 'How do you get to DUMBO?', a: 'The F train stops at York Street. The A/C trains stop at High Street. NYC Ferry also serves DUMBO\'s waterfront.' }
    ],
    facts: ['DUMBO stands for Down Under the Manhattan Bridge Overpass', 'Washington Street view is NYC\'s most Instagrammed spot', 'Home to Etsy headquarters'],
    topReasons: ['Iconic Brooklyn Bridge views', 'Converted warehouse lofts', 'Tech startup community', 'Waterfront parks', 'No-fee luxury rentals']
  },
  'upper-west-side': {
    title: 'Upper West Side',
    description: 'The Upper West Side is a classic NYC neighborhood with Central Park, Lincoln Center, and excellent pre-war apartments.',
    highlights: ['Central Park West', 'Lincoln Center', 'Top-rated schools', 'Riverside Park'],
    faqs: [
      { q: 'Is the Upper West Side a good neighborhood?', a: 'Yes, UWS is one of NYC\'s most desirable neighborhoods with top schools, two parks, cultural institutions, and classic architecture.' },
      { q: 'What is the Upper West Side known for?', a: 'UWS is known for Lincoln Center, the American Museum of Natural History, Central Park, Riverside Park, and intellectual culture.' },
      { q: 'Is Upper West Side expensive?', a: 'UWS is affluent but offers range. Pre-war apartments average $3,000-4,500 for 1-bedrooms. No-fee options save 12-15% in fees.' }
    ],
    facts: ['Home to Lincoln Center and the Met Opera', 'Two parks: Central Park and Riverside Park', 'Zabar\'s deli has operated since 1934'],
    topReasons: ['Central Park at your door', 'Lincoln Center culture', 'Top-rated public schools', 'Classic pre-war apartments', 'No broker fees available']
  },
  'west-village': {
    title: 'West Village',
    description: 'The West Village has charming tree-lined streets, historic townhouses, and NYC\'s best boutiques and restaurants.',
    highlights: ['Washington Square Park', 'Intimate restaurants', 'LGBTQ+ history', 'Quiet streets'],
    faqs: [
      { q: 'Why is the West Village so desirable?', a: 'The West Village offers quiet tree-lined streets, historic townhouses, celebrity residents, and NYC\'s most charming restaurants.' },
      { q: 'What is the West Village known for?', a: 'Known for the Stonewall Inn (LGBTQ+ history), Washington Square Park, brownstones, and being NYC\'s most romantic neighborhood.' },
      { q: 'Is the West Village quiet?', a: 'Yes, the residential blocks are remarkably quiet for Manhattan, with narrow tree-lined streets and limited through traffic.' }
    ],
    facts: ['The Stonewall Inn sparked the LGBTQ+ rights movement', 'Carrie Bradshaw\'s apartment from SATC is here', 'Streets don\'t follow the grid pattern'],
    topReasons: ['Charming tree-lined streets', 'Historic brownstones', 'NYC\'s best restaurants', 'Quiet residential feel', 'No-fee apartments available']
  },
  'prospect-heights': {
    title: 'Prospect Heights',
    description: 'Prospect Heights borders Prospect Park and the Brooklyn Museum. A family-friendly neighborhood with brownstone charm.',
    highlights: ['Prospect Park', 'Brooklyn Museum', 'Grand Army Plaza', 'Farmers market'],
    faqs: [
      { q: 'Is Prospect Heights a good neighborhood?', a: 'Yes, Prospect Heights is one of Brooklyn\'s best neighborhoods with Prospect Park, the Brooklyn Museum, and beautiful brownstones.' },
      { q: 'What is Prospect Heights known for?', a: 'Known for Prospect Park, Brooklyn Museum, Brooklyn Botanic Garden, Grand Army Plaza, and excellent brownstone architecture.' },
      { q: 'How far is Prospect Heights from Manhattan?', a: 'The 2/3 trains reach Midtown in 25 minutes. The B/Q reach Herald Square in 20 minutes via the express.' }
    ],
    facts: ['Prospect Park was designed by Central Park creators', 'Brooklyn Museum is NYC\'s second-largest art museum', 'Home to the Brooklyn Botanic Garden'],
    topReasons: ['Prospect Park living', 'Brooklyn Museum access', 'Beautiful brownstones', 'Saturday farmers market', 'No-fee rental options']
  },
  'harrison': {
    title: 'Harrison, NJ',
    description: 'Harrison offers affordable luxury apartments with quick PATH train access to NYC. A growing commuter community.',
    highlights: ['PATH to WTC in 20 min', 'New luxury buildings', 'Red Bull Arena', 'Affordable rents'],
    faqs: [
      { q: 'Is Harrison NJ a good place to live?', a: 'Yes, Harrison offers new luxury apartments at 30-40% less than Manhattan, with PATH trains to WTC in just 20 minutes.' },
      { q: 'How is the commute from Harrison to NYC?', a: 'PATH trains run 24/7 to World Trade Center (20 min) and Newark Penn Station (10 min). Peak service runs every 5-10 minutes.' },
      { q: 'Is Harrison NJ safe?', a: 'Harrison has transformed with new development, bringing improved safety and amenities. New buildings have 24/7 security.' }
    ],
    facts: ['PATH fare is $2.75 one-way to Manhattan', 'Home to Red Bull Arena (25,000 capacity)', 'New developments added 5,000+ apartments since 2015'],
    topReasons: ['30-40% cheaper than Manhattan', 'PATH to WTC in 20 minutes', 'Brand new luxury buildings', 'No broker fees', 'Waterfront development']
  },
  'jersey-city': {
    title: 'Jersey City',
    description: 'Jersey City provides Manhattan skyline views at lower prices. Excellent PATH access and a booming food scene.',
    highlights: ['NYC skyline views', 'PATH train access', 'Liberty State Park', 'Lower rents than NYC'],
    faqs: [
      { q: 'Is Jersey City cheaper than NYC?', a: 'Yes, Jersey City rents average 20-30% less than comparable Manhattan neighborhoods while offering skyline views and PATH access.' },
      { q: 'How long is the PATH from Jersey City to Manhattan?', a: 'PATH trains reach WTC in 10 minutes from Exchange Place, and 15 minutes from Journal Square. Trains run 24/7.' },
      { q: 'Is Jersey City a good alternative to NYC?', a: 'Absolutely. Jersey City offers lower taxes (no NYC income tax), skyline views, waterfront parks, and quick Manhattan access.' }
    ],
    facts: ['No NYC income tax saves residents 3-4% annually', 'Liberty State Park offers Statue of Liberty views', 'Fastest-growing city in NJ'],
    topReasons: ['Manhattan skyline views', '20-30% lower rent than NYC', 'No NYC income tax', 'PATH runs 24/7', 'No broker fee apartments']
  },
  'hoboken': {
    title: 'Hoboken',
    description: 'Hoboken is a walkable waterfront city with young professionals, great bars, and easy NYC commutes.',
    highlights: ['Walkable downtown', 'PATH to NYC', 'Waterfront parks', 'Vibrant nightlife'],
    faqs: [
      { q: 'Is Hoboken a good place for young professionals?', a: 'Yes, Hoboken is ideal for young professionals with walkable streets, active nightlife, waterfront parks, and easy NYC commutes.' },
      { q: 'How long is the commute from Hoboken to NYC?', a: 'PATH trains reach WTC in 15 minutes and 33rd Street in 20 minutes. NY Waterway ferries reach Midtown in 10 minutes.' },
      { q: 'Is Hoboken expensive?', a: 'Hoboken is pricier than other NJ cities but still 15-20% cheaper than Manhattan, with no NYC income tax savings.' }
    ],
    facts: ['Hoboken is just 1 square mile', 'Birthplace of baseball and Frank Sinatra', 'Walk Score of 95 makes it NJ\'s most walkable city'],
    topReasons: ['Most walkable city in NJ', 'Vibrant bar and restaurant scene', 'PATH and Ferry to NYC', 'Waterfront parks', 'No-fee apartments']
  }
};

const NeighborhoodPage = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API}/neighborhoods/${slug}`)
      .then(res => {
        if (!res.ok) throw new Error('Neighborhood not found');
        return res.json();
      })
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Neighborhood not found</h1>
          <Link to="/apartments" className="text-amber-600 hover:underline">Browse all neighborhoods</Link>
        </div>
      </div>
    );
  }

  const info = neighborhoodDescriptions[slug] || {
    title: data.name,
    description: `Explore no fee apartments in ${data.name}, ${data.city}. Find broker-free rentals with zero fees.`,
    highlights: [],
    faqs: [],
    facts: [],
    topReasons: []
  };

  const getBedText = (beds) => {
    if (beds === 0) return 'Studio';
    if (beds === 1) return '1 Bed';
    return `${beds} Bed`;
  };

  // Schema.org structured data - ItemList for apartments
  const schemaData = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": `No Fee Apartments in ${data.name}`,
    "description": info.description,
    "numberOfItems": data.stats.total_units,
    "itemListElement": data.units.slice(0, 10).map((unit, index) => ({
      "@type": "Apartment",
      "position": index + 1,
      "name": `${getBedText(unit.bedrooms)} in ${data.name}`,
      "address": {
        "@type": "PostalAddress",
        "addressLocality": data.city,
        "addressRegion": data.state
      }
    }))
  };

  // Schema.org FAQPage for AI and Google
  const faqSchema = info.faqs?.length > 0 ? {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": info.faqs.map(faq => ({
      "@type": "Question",
      "name": faq.q,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.a
      }
    }))
  } : null;

  // Schema.org Article with Author - Expertise Signal
  const articleSchema = {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": `No Fee Apartments in ${data?.name || ''} - ${data?.stats?.total_units || 0} Verified Listings`,
    "description": info.description,
    "author": {
      "@type": "Person",
      "name": "Chris Trunell",
      "jobTitle": "Licensed Real Estate Professional",
      "description": "NYC rental market expert with 10+ years experience specializing in no-fee apartments",
      "knowsAbout": ["NYC Real Estate", "No Fee Apartments", "Manhattan Rentals", "Brooklyn Rentals"]
    },
    "publisher": {
      "@type": "Organization",
      "name": "NoFeesApts",
      "url": "https://nofeesapts.com"
    },
    "datePublished": "2024-01-01",
    "dateModified": new Date().toISOString().split('T')[0],
    "mainEntityOfPage": `https://nofeesapts.com/apartments/${slug}`
  };

  // Get a representative image for social sharing - use first unit image or default
  const defaultSocialImage = 'https://static.prod-images.emergentagent.com/jobs/47dd6b46-e381-45f3-b7a5-c4e5965d2ca7/images/7cc4822cb8a1477005344990d5785c45f97816fa18a46f0e57cadfe289bec671.png';
  const socialImage = data?.units?.[0]?.images?.[0] || defaultSocialImage;
  const pageTitle = `No Fee Apartments in ${data?.name || 'Loading'} | ${data?.stats?.total_units || 0} Listings`;
  const pageDescription = `${data?.stats?.total_units || 0} no fee apartments in ${data?.name || ''}, ${data?.city || ''}. Rent from $${(data?.stats?.min_rent || 0).toLocaleString()}/mo. Zero broker fees.`;

  return (
    <>
      <Helmet>
        <title>{pageTitle} | NoFeesApts</title>
        <meta name="description" content={`${pageDescription} ${info.description}`} />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content={`https://nofeesapts.com/apartments/${slug}`} />
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={pageDescription} />
        <meta property="og:image" content={socialImage} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:site_name" content="NoFeesApts" />
        <meta property="og:locale" content="en_US" />
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content={`https://nofeesapts.com/apartments/${slug}`} />
        <meta name="twitter:title" content={pageTitle} />
        <meta name="twitter:description" content={pageDescription} />
        <meta name="twitter:image" content={socialImage} />
        
        {/* Additional SEO */}
        <meta name="robots" content="index, follow" />
        <meta name="author" content="NoFeesApts" />
        <link rel="canonical" href={`https://nofeesapts.com/apartments/${slug}`} />
        
        {/* Structured Data - Apartments */}
        <script type="application/ld+json">{JSON.stringify(schemaData)}</script>
        
        {/* Structured Data - FAQ for AI reach */}
        {faqSchema && <script type="application/ld+json">{JSON.stringify(faqSchema)}</script>}
        
        {/* Structured Data - Article with Author for E-E-A-T */}
        <script type="application/ld+json">{JSON.stringify(articleSchema)}</script>
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="text-2xl font-philosopher font-bold text-gray-900">
                NoFeesApts
              </Link>
              <span className="text-gray-300">|</span>
              <Link to="/apartments" className="text-sm text-gray-600 hover:text-amber-600 flex items-center gap-1">
                <ArrowLeft className="w-4 h-4" /> All Neighborhoods
              </Link>
            </div>
            <Link 
              to="/auth" 
              className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded font-medium text-sm transition-colors"
            >
              Sign Up Free
            </Link>
          </div>
        </header>

        {/* Hero Section */}
        <div className="bg-gradient-to-b from-gray-900 to-gray-800 text-white py-16">
          <div className="max-w-7xl mx-auto px-4">
            {/* Breadcrumb */}
            <nav className="flex items-center gap-2 text-sm text-gray-400 mb-6">
              <Link to="/" className="hover:text-white">Home</Link>
              <ChevronRight className="w-4 h-4" />
              <Link to="/apartments" className="hover:text-white">Neighborhoods</Link>
              <ChevronRight className="w-4 h-4" />
              <span className="text-white">{data.name}</span>
            </nav>

            {/* Trust Badges */}
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <span className="inline-flex items-center gap-1.5 bg-green-500/20 text-green-400 text-xs font-medium px-2.5 py-1 rounded-full border border-green-500/30">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/></svg>
                Verified Listings
              </span>
              <span className="inline-flex items-center gap-1.5 bg-amber-500/20 text-amber-400 text-xs font-medium px-2.5 py-1 rounded-full border border-amber-500/30">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd"/></svg>
                Updated Daily
              </span>
              <span className="inline-flex items-center gap-1.5 bg-blue-500/20 text-blue-400 text-xs font-medium px-2.5 py-1 rounded-full border border-blue-500/30">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/><path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd"/></svg>
                Curated by Local Experts
              </span>
            </div>

            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              No Fee Apartments in {data.name}
            </h1>
            
            <p className="text-xl text-gray-300 max-w-3xl mb-6">
              {info.description}
            </p>

            {/* Expert Byline & Last Updated */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-400 mb-8">
              <span className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-amber-500 flex items-center justify-center text-gray-900 text-xs font-bold">C</div>
                <span>Curated by <strong className="text-white">Chris Trunell</strong></span>
              </span>
              <span className="text-gray-600">•</span>
              <span>NYC Real Estate Expert, 10+ Years</span>
              <span className="text-gray-600">•</span>
              <span>Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
            </div>

            {/* Stats Row */}
            <div className="flex flex-wrap gap-8">
              <div>
                <p className="text-3xl font-bold text-amber-400">{data.stats.total_units}</p>
                <p className="text-gray-400 text-sm">Available Units</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-amber-400">${data.stats.avg_rent.toLocaleString()}</p>
                <p className="text-gray-400 text-sm">Avg. Rent/mo</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-amber-400">${data.stats.min_rent.toLocaleString()}</p>
                <p className="text-gray-400 text-sm">Starting From</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-amber-400">$0</p>
                <p className="text-gray-400 text-sm">Broker Fee</p>
              </div>
            </div>

            {/* Highlights */}
            {info.highlights.length > 0 && (
              <div className="mt-8 flex flex-wrap gap-3">
                {info.highlights.map((h, i) => (
                  <span key={i} className="bg-white/10 px-3 py-1 rounded-full text-sm">
                    {h}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-white border-b border-gray-200 py-4 sticky top-[65px] z-40">
          <div className="max-w-7xl mx-auto px-4 flex items-center justify-between">
            <div className="flex gap-2">
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-700">
                {data.stats.studios} Studios
              </span>
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-700">
                {data.stats.one_beds} 1-Beds
              </span>
              <span className="bg-gray-100 px-3 py-1 rounded-full text-sm text-gray-700">
                {data.stats.two_plus_beds} 2+ Beds
              </span>
            </div>
            <p className="text-sm text-gray-500">
              Sorted by rent (low to high)
            </p>
          </div>
        </div>

        {/* Listings Grid */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.units.map((unit) => (
              <div 
                key={unit.id}
                onClick={() => navigate('/auth')}
                className="bg-white rounded-lg overflow-hidden border border-gray-200 hover:border-amber-400 hover:shadow-lg transition-all cursor-pointer group"
              >
                {/* Image */}
                <div className="relative aspect-[4/3] bg-gray-100">
                  {unit.images?.[0] ? (
                    <img 
                      src={unit.images[0]} 
                      alt={`${getBedText(unit.bedrooms)} apartment in ${data.name}`}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <BedDouble className="w-12 h-12 text-gray-300" />
                    </div>
                  )}
                  <button className="absolute top-3 right-3 w-8 h-8 bg-white/90 rounded-full flex items-center justify-center">
                    <Heart className="w-4 h-4 text-gray-400" />
                  </button>
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
                    <span className="text-white font-bold text-lg">${unit.rent?.toLocaleString()}<span className="text-white/70 text-sm font-normal">/mo</span></span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <span>{getBedText(unit.bedrooms)}</span>
                    <span className="text-gray-300">•</span>
                    <span>{unit.bathrooms} Bath</span>
                    {unit.square_feet && (
                      <>
                        <span className="text-gray-300">•</span>
                        <span>{unit.square_feet.toLocaleString()} ft²</span>
                      </>
                    )}
                  </div>
                  
                  <p className="text-sm text-gray-500 blur-[3px] select-none">
                    {unit.building?.address || '123 Example Street'}
                  </p>
                  
                  <p className="text-xs text-amber-600 mt-2">Sign up to view address</p>
                </div>
              </div>
            ))}
          </div>
        </main>

        {/* CTA Section */}
        <div className="bg-amber-50 py-16 border-t border-amber-100">
          <div className="max-w-3xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Like what you see in {data.name}?
            </h2>
            <p className="text-gray-600 mb-8">
              Sign up for free to see full addresses, save your favorites, and get instant alerts when new {data.name} apartments are listed.
            </p>
            <Link 
              to="/auth"
              className="inline-block bg-amber-500 hover:bg-amber-600 text-white px-8 py-4 rounded font-bold text-lg transition-colors"
            >
              Sign Up Free — See All Addresses
            </Link>
            <p className="text-sm text-gray-500 mt-4">No credit card required • 100% free</p>
          </div>
        </div>

        {/* SEO Content Section */}
        <div className="bg-white py-16 border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              About No Fee Apartments in {data.name}
            </h2>
            <div className="prose prose-gray max-w-none">
              <p>
                Looking for a no fee apartment in {data.name}? You've come to the right place. 
                NoFeesApts lists <strong>{data.stats.total_units} broker-free apartments</strong> in {data.name}, {data.city} 
                with rents starting at <strong>${data.stats.min_rent.toLocaleString()}/month</strong>.
              </p>
              <p>
                {info.description}
              </p>
              <p>
                All apartments listed on NoFeesApts are no-fee, meaning you pay <strong>$0 in broker fees</strong>. 
                The average rent in {data.name} is ${data.stats.avg_rent.toLocaleString()}/month, with options ranging 
                from ${data.stats.min_rent.toLocaleString()} to ${data.stats.max_rent.toLocaleString()}.
              </p>
              <h3>What's Available in {data.name}?</h3>
              <ul>
                {data.stats.studios > 0 && <li><strong>{data.stats.studios} Studios</strong> available</li>}
                {data.stats.one_beds > 0 && <li><strong>{data.stats.one_beds} One-bedroom</strong> apartments</li>}
                {data.stats.two_plus_beds > 0 && <li><strong>{data.stats.two_plus_beds} Two+ bedroom</strong> apartments</li>}
              </ul>
            </div>
          </div>
        </div>

        {/* Quick Facts Section - Listicle for AI */}
        {info.facts?.length > 0 && (
          <div className="bg-gray-50 py-12 border-t border-gray-200">
            <div className="max-w-4xl mx-auto px-4">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Quick Facts About {data.name}
              </h2>
              <ul className="grid md:grid-cols-3 gap-4">
                {info.facts.map((fact, i) => (
                  <li key={i} className="flex items-start gap-2 bg-white p-4 rounded-lg border border-gray-200">
                    <span className="text-amber-500 font-bold">✓</span>
                    <span className="text-gray-700 text-sm">{fact}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Top Reasons Listicle for AI */}
        {info.topReasons?.length > 0 && (
          <div className="bg-white py-12 border-t border-gray-200">
            <div className="max-w-4xl mx-auto px-4">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Top {info.topReasons.length} Reasons to Rent in {data.name}
              </h2>
              <ol className="space-y-3">
                {info.topReasons.map((reason, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="flex-shrink-0 w-7 h-7 rounded-full bg-amber-500 text-white text-sm font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                    <span className="text-gray-700 pt-1">{reason}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}

        {/* FAQ Section for AI reach */}
        {info.faqs?.length > 0 && (
          <div className="bg-gray-50 py-12 border-t border-gray-200">
            <div className="max-w-4xl mx-auto px-4">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                Frequently Asked Questions About {data.name}
              </h2>
              <div className="space-y-4">
                {info.faqs.map((faq, i) => (
                  <div key={i} className="bg-white rounded-lg border border-gray-200 p-5">
                    <h3 className="font-semibold text-gray-900 mb-2">{faq.q}</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">{faq.a}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Data Methodology & Sources - Expertise Signal */}
        <div className="bg-white py-10 border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-4">
            <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
              <h3 className="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"/></svg>
                Data & Methodology
              </h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <p className="mb-2"><strong className="text-gray-900">Data Source:</strong> Direct partnerships with {data.stats.total_buildings} no-fee buildings in {data.name}</p>
                  <p><strong className="text-gray-900">Verification:</strong> All listings verified as no-fee directly with building management</p>
                </div>
                <div>
                  <p className="mb-2"><strong className="text-gray-900">Update Frequency:</strong> Listings refreshed daily via automated crawlers</p>
                  <p><strong className="text-gray-900">Price Accuracy:</strong> Rents confirmed within 48 hours of posting</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-4 pt-3 border-t border-gray-200">
                Statistics based on {data.stats.total_units} verified no-fee apartments in {data.name} as of {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}. 
                Average rent calculated from current available listings. Actual rents may vary.
              </p>
            </div>
          </div>
        </div>

        {/* Expert About Section */}
        <div className="bg-gray-50 py-10 border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-4">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-white text-xl font-bold flex-shrink-0">
                CT
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-1">About the Author</h3>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Chris Trunell</strong> is a licensed real estate professional with over 10 years of experience in the NYC rental market. 
                  Specializing in no-fee apartments, Chris has helped hundreds of renters find broker-free homes across Manhattan, Brooklyn, Queens, and Northern New Jersey.
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded">Licensed RE Agent</span>
                  <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">10+ Years Experience</span>
                  <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">500+ Clients Served</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Related Neighborhoods - Internal Linking */}
        <div className="bg-white py-12 border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-4">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              Explore Nearby Neighborhoods
            </h2>
            <p className="text-gray-600 text-sm mb-6">
              Looking for more options? Check out these similar neighborhoods with no-fee apartments.
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {(relatedNeighborhoods[slug] || ['chelsea', 'tribeca', 'williamsburg', 'jersey-city']).map((relatedSlug) => (
                <Link
                  key={relatedSlug}
                  to={`/apartments/${relatedSlug}`}
                  className="group bg-gray-50 hover:bg-amber-50 border border-gray-200 hover:border-amber-300 rounded-lg p-4 transition-all"
                >
                  <h3 className="font-semibold text-gray-900 group-hover:text-amber-600 mb-1">
                    {neighborhoodNames[relatedSlug] || relatedSlug}
                  </h3>
                  <p className="text-xs text-gray-500 mb-2">No-fee apartments available</p>
                  <span className="text-amber-600 text-sm font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    View listings <ArrowRight className="w-3 h-3" />
                  </span>
                </Link>
              ))}
            </div>
            <div className="text-center mt-6">
              <Link 
                to="/apartments" 
                className="text-amber-600 hover:text-amber-700 text-sm font-medium inline-flex items-center gap-1"
              >
                Browse all 28 neighborhoods <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-12">
          <div className="max-w-7xl mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
              <div>
                <h4 className="font-bold mb-4">Popular NYC</h4>
                <ul className="space-y-2 text-gray-400 text-sm">
                  <li><Link to="/apartments/chelsea" className="hover:text-white">Chelsea</Link></li>
                  <li><Link to="/apartments/tribeca" className="hover:text-white">Tribeca</Link></li>
                  <li><Link to="/apartments/williamsburg" className="hover:text-white">Williamsburg</Link></li>
                  <li><Link to="/apartments/financial-district" className="hover:text-white">Financial District</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold mb-4">Brooklyn</h4>
                <ul className="space-y-2 text-gray-400 text-sm">
                  <li><Link to="/apartments/dumbo" className="hover:text-white">DUMBO</Link></li>
                  <li><Link to="/apartments/williamsburg" className="hover:text-white">Williamsburg</Link></li>
                  <li><Link to="/apartments/prospect-heights" className="hover:text-white">Prospect Heights</Link></li>
                  <li><Link to="/apartments/fort-greene" className="hover:text-white">Fort Greene</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold mb-4">Queens & NJ</h4>
                <ul className="space-y-2 text-gray-400 text-sm">
                  <li><Link to="/apartments/long-island-city" className="hover:text-white">Long Island City</Link></li>
                  <li><Link to="/apartments/harrison" className="hover:text-white">Harrison, NJ</Link></li>
                  <li><Link to="/apartments/jersey-city" className="hover:text-white">Jersey City</Link></li>
                  <li><Link to="/apartments/hoboken" className="hover:text-white">Hoboken</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold mb-4">Resources</h4>
                <ul className="space-y-2 text-gray-400 text-sm">
                  <li><Link to="/apartments" className="hover:text-white">All Neighborhoods</Link></li>
                  <li><Link to="/blog" className="hover:text-white">Blog & Guides</Link></li>
                  <li><Link to="/faq" className="hover:text-white">FAQ</Link></li>
                  <li><Link to="/auth" className="hover:text-white">Sign Up Free</Link></li>
                </ul>
              </div>
            </div>
            
            {/* Additional Internal Links for SEO */}
            <div className="border-t border-gray-800 pt-6 pb-4">
              <p className="text-xs text-gray-500 mb-3">More neighborhoods:</p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                <Link to="/apartments/chelsea" className="hover:text-amber-400">Chelsea</Link>
                <Link to="/apartments/tribeca" className="hover:text-amber-400">Tribeca</Link>
                <Link to="/apartments/financial-district" className="hover:text-amber-400">Financial District</Link>
                <Link to="/apartments/midtown-west" className="hover:text-amber-400">Midtown West</Link>
                <Link to="/apartments/upper-west-side" className="hover:text-amber-400">Upper West Side</Link>
                <Link to="/apartments/west-village" className="hover:text-amber-400">West Village</Link>
                <Link to="/apartments/dumbo" className="hover:text-amber-400">DUMBO</Link>
                <Link to="/apartments/williamsburg" className="hover:text-amber-400">Williamsburg</Link>
                <Link to="/apartments/long-island-city" className="hover:text-amber-400">Long Island City</Link>
                <Link to="/apartments/prospect-heights" className="hover:text-amber-400">Prospect Heights</Link>
                <Link to="/apartments/fort-greene" className="hover:text-amber-400">Fort Greene</Link>
                <Link to="/apartments/jersey-city" className="hover:text-amber-400">Jersey City</Link>
                <Link to="/apartments/harrison" className="hover:text-amber-400">Harrison</Link>
                <Link to="/apartments/hoboken" className="hover:text-amber-400">Hoboken</Link>
              </div>
            </div>
            
            <div className="border-t border-gray-800 pt-8 text-center text-gray-500 text-sm">
              © 2025 NoFeesApts.com — No Fee Apartments in NYC, NJ & PA
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default NeighborhoodPage;
