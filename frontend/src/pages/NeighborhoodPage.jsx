import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowLeft, ChevronRight } from 'lucide-react';
import { API } from '../config/api';

// Neighborhood descriptions for SEO
const neighborhoodDescriptions = {
  'long-island-city': {
    title: 'Long Island City',
    description: 'Long Island City (LIC) offers stunning Manhattan skyline views, waterfront parks, and easy subway access. A hub for young professionals and artists.',
    highlights: ['Manhattan skyline views', '7 train to Midtown in 10 min', 'Waterfront parks', 'Growing restaurant scene']
  },
  'financial-district': {
    title: 'Financial District',
    description: 'The Financial District features historic architecture, luxury high-rises, and proximity to Wall Street. Cobblestone streets meet modern amenities.',
    highlights: ['Historic architecture', 'Steps from Wall Street', 'Easy PATH access to NJ', 'Waterfront dining']
  },
  'chelsea': {
    title: 'Chelsea',
    description: 'Chelsea is NYC\'s art gallery capital with the High Line, excellent restaurants, and beautiful brownstones. A vibrant, walkable neighborhood.',
    highlights: ['The High Line', '200+ art galleries', 'Chelsea Market', 'Tree-lined streets']
  },
  'tribeca': {
    title: 'Tribeca',
    description: 'Tribeca is one of NYC\'s most desirable neighborhoods with converted lofts, celebrity residents, and upscale dining.',
    highlights: ['Converted loft spaces', 'Robert De Niro\'s restaurants', 'Cobblestone streets', 'Hudson River Park']
  },
  'midtown-west': {
    title: 'Midtown West',
    description: 'Midtown West offers convenience to Times Square, Hudson Yards, and Penn Station. Perfect for commuters and entertainment lovers.',
    highlights: ['Hudson Yards', 'Theater District', 'Penn Station access', 'Restaurant Row']
  },
  'williamsburg': {
    title: 'Williamsburg',
    description: 'Williamsburg is Brooklyn\'s trendiest neighborhood with waterfront parks, indie boutiques, and a thriving nightlife scene.',
    highlights: ['Domino Park', 'Bedford Avenue shops', 'L train to Manhattan', 'Rooftop bars']
  },
  'dumbo': {
    title: 'DUMBO',
    description: 'DUMBO (Down Under the Manhattan Bridge Overpass) features iconic views, tech startups, and converted warehouse lofts.',
    highlights: ['Brooklyn Bridge views', 'Jane\'s Carousel', 'Tech hub', 'Cobblestone streets']
  },
  'upper-west-side': {
    title: 'Upper West Side',
    description: 'The Upper West Side is a classic NYC neighborhood with Central Park, Lincoln Center, and excellent pre-war apartments.',
    highlights: ['Central Park West', 'Lincoln Center', 'Top-rated schools', 'Riverside Park']
  },
  'west-village': {
    title: 'West Village',
    description: 'The West Village has charming tree-lined streets, historic townhouses, and NYC\'s best boutiques and restaurants.',
    highlights: ['Washington Square Park', 'Intimate restaurants', 'LGBTQ+ history', 'Quiet streets']
  },
  'prospect-heights': {
    title: 'Prospect Heights',
    description: 'Prospect Heights borders Prospect Park and the Brooklyn Museum. A family-friendly neighborhood with brownstone charm.',
    highlights: ['Prospect Park', 'Brooklyn Museum', 'Grand Army Plaza', 'Farmers market']
  },
  'harrison': {
    title: 'Harrison, NJ',
    description: 'Harrison offers affordable luxury apartments with quick PATH train access to NYC. A growing commuter community.',
    highlights: ['PATH to WTC in 20 min', 'New luxury buildings', 'Red Bull Arena', 'Affordable rents']
  },
  'jersey-city': {
    title: 'Jersey City',
    description: 'Jersey City provides Manhattan skyline views at lower prices. Excellent PATH access and a booming food scene.',
    highlights: ['NYC skyline views', 'PATH train access', 'Liberty State Park', 'Lower rents than NYC']
  },
  'hoboken': {
    title: 'Hoboken',
    description: 'Hoboken is a walkable waterfront city with young professionals, great bars, and easy NYC commutes.',
    highlights: ['Walkable downtown', 'PATH to NYC', 'Waterfront parks', 'Vibrant nightlife']
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
    highlights: []
  };

  const getBedText = (beds) => {
    if (beds === 0) return 'Studio';
    if (beds === 1) return '1 Bed';
    return `${beds} Bed`;
  };

  // Schema.org structured data
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
        
        {/* Structured Data */}
        <script type="application/ld+json">{JSON.stringify(schemaData)}</script>
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

            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              No Fee Apartments in {data.name}
            </h1>
            
            <p className="text-xl text-gray-300 max-w-3xl mb-8">
              {info.description}
            </p>

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
                  <li><Link to="/apartments/prospect-heights" className="hover:text-white">Prospect Heights</Link></li>
                  <li><Link to="/apartments/fort-greene" className="hover:text-white">Fort Greene</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold mb-4">New Jersey</h4>
                <ul className="space-y-2 text-gray-400 text-sm">
                  <li><Link to="/apartments/harrison" className="hover:text-white">Harrison</Link></li>
                  <li><Link to="/apartments/jersey-city" className="hover:text-white">Jersey City</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold mb-4">Company</h4>
                <ul className="space-y-2 text-gray-400 text-sm">
                  <li><Link to="/apartments" className="hover:text-white">All Neighborhoods</Link></li>
                  <li><Link to="/auth" className="hover:text-white">Sign Up</Link></li>
                </ul>
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
