import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowRight, Check, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';
import axios from '../utils/axiosConfig';
import { API } from '../App';

// Brooklyn neighborhoods data
const brooklynNeighborhoods = [
  { slug: 'dumbo', name: 'DUMBO', description: 'Waterfront luxury with Manhattan skyline views' },
  { slug: 'williamsburg', name: 'Williamsburg', description: 'Trendy bars, boutiques, and creative energy' },
  { slug: 'brooklyn-heights', name: 'Brooklyn Heights', description: 'Historic brownstones and the famous Promenade' },
  { slug: 'fort-greene', name: 'Fort Greene', description: 'Cultural hub near BAM with tree-lined streets' },
  { slug: 'prospect-heights', name: 'Prospect Heights', description: 'Near Prospect Park and Brooklyn Museum' },
  { slug: 'carroll-gardens', name: 'Carroll Gardens', description: 'Italian heritage with charming gardens' },
  { slug: 'park-slope', name: 'Park Slope', description: 'Family-friendly with brownstones galore' },
  { slug: 'cobble-hill', name: 'Cobble Hill', description: 'Quaint streets and boutique shopping' }
];

// FAQ data for SEO
const faqs = [
  {
    q: "What is the average rent for a no-fee apartment in Brooklyn?",
    a: "No-fee apartment rents in Brooklyn range from $2,200 for studios in emerging neighborhoods to $5,500+ for luxury 2-bedrooms in DUMBO and Williamsburg. By avoiding broker fees (typically 12-15% of annual rent), you can save $3,000-$8,000 on your move."
  },
  {
    q: "Which Brooklyn neighborhoods have the most no-fee apartments?",
    a: "DUMBO, Williamsburg, Fort Greene, and Downtown Brooklyn have the highest concentration of no-fee apartments due to newer luxury developments. Brooklyn Heights and Carroll Gardens have fewer but offer charming pre-war options."
  },
  {
    q: "How do I find a no-fee apartment in Brooklyn?",
    a: "Use NoFeesApts.com to browse verified no-fee listings updated daily. Filter by neighborhood, price, and bedrooms. Sign up free to see full addresses and contact landlords directly—no broker needed."
  },
  {
    q: "Are no-fee apartments in Brooklyn legit?",
    a: "Yes! No-fee apartments are offered directly by landlords or management companies who pay for marketing themselves. At NoFeesApts.com, we verify all listings to ensure they're genuinely broker-fee-free."
  },
  {
    q: "What's the best time to find no-fee apartments in Brooklyn?",
    a: "Winter (December-February) often has the best deals as demand is lower. However, new no-fee inventory is added year-round. Set up alerts on NoFeesApts.com to be notified of new listings instantly."
  }
];

// Top reasons listicle
const topReasons = [
  "Save $3,000-$8,000 by avoiding broker fees",
  "Deal directly with landlords—no middleman",
  "Luxury amenities: doorman, gym, rooftop, laundry",
  "Prime locations near subways and parks",
  "Transparent pricing—what you see is what you pay"
];

const BrooklynPage = () => {
  const navigate = useNavigate();
  const [units, setUnits] = useState([]);
  const [stats, setStats] = useState({ count: 0, avgRent: 0, minRent: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBrooklynUnits();
  }, []);

  const fetchBrooklynUnits = async () => {
    try {
      // Fetch all units and filter for Brooklyn neighborhoods
      const response = await axios.get(`${API}/units?limit=100`);
      const allUnits = response.data || [];
      
      // Brooklyn neighborhoods to filter
      const brooklynNeighborhoodNames = ['DUMBO', 'Williamsburg', 'Brooklyn Heights', 'Fort Greene', 
        'Prospect Heights', 'Carroll Gardens', 'Park Slope', 'Cobble Hill', 'Bushwick', 'Greenpoint',
        'Crown Heights', 'Bed-Stuy', 'Clinton Hill'];
      
      // Filter units that are in Brooklyn (by city or neighborhood)
      const brooklynUnits = allUnits.filter(u => {
        const building = u.building || {};
        const city = (building.city || '').toLowerCase();
        const neighborhood = building.neighborhood || '';
        return city === 'brooklyn' || brooklynNeighborhoodNames.includes(neighborhood);
      });
      
      setUnits(brooklynUnits);

      // Calculate stats
      if (brooklynUnits.length > 0) {
        const rents = brooklynUnits.map(u => u.rent).filter(r => r > 0);
        setStats({
          count: brooklynUnits.length,
          avgRent: rents.length > 0 ? Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) : 0,
          minRent: rents.length > 0 ? Math.min(...rents) : 0
        });
      }
    } catch (error) {
      console.error('Error fetching Brooklyn units:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(price);
  };

  // Schema.org structured data
  const schemaData = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": "Best No Fee Apartments in Brooklyn, NY",
    "description": "Find the best no broker fee apartments in Brooklyn. Browse verified no-fee listings in DUMBO, Williamsburg, Brooklyn Heights, Fort Greene, and more.",
    "url": "https://www.nofeesapts.com/brooklyn",
    "mainEntity": {
      "@type": "ItemList",
      "name": "Brooklyn No-Fee Apartments",
      "numberOfItems": stats.count,
      "itemListElement": brooklynNeighborhoods.map((n, i) => ({
        "@type": "ListItem",
        "position": i + 1,
        "name": `No Fee Apartments in ${n.name}`,
        "url": `https://www.nofeesapts.com/apartments/${n.slug}`
      }))
    },
    "breadcrumb": {
      "@type": "BreadcrumbList",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.nofeesapts.com" },
        { "@type": "ListItem", "position": 2, "name": "Brooklyn", "item": "https://www.nofeesapts.com/brooklyn" }
      ]
    }
  };

  // FAQ Schema
  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faqs.map(faq => ({
      "@type": "Question",
      "name": faq.q,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.a
      }
    }))
  };

  return (
    <div className="min-h-screen bg-white">
      <Helmet>
        <title>Best No Fee Apartments in Brooklyn, NY | {String(stats.count)}+ Verified Listings | NoFeesApts</title>
        <meta name="description" content={`Find the best no broker fee apartments in Brooklyn. Browse ${String(stats.count)}+ verified no-fee listings in DUMBO, Williamsburg, Brooklyn Heights & more. Save thousands on broker fees. Updated daily.`} />
        <meta name="keywords" content="no fee apartments Brooklyn, Brooklyn no broker fee, DUMBO apartments no fee, Williamsburg no fee apartments, Brooklyn Heights rentals, Fort Greene apartments, no broker fee Brooklyn NY, best Brooklyn apartments, cheap Brooklyn apartments no fee" />
        <link rel="canonical" href="https://www.nofeesapts.com/brooklyn" />
        
        {/* Open Graph */}
        <meta property="og:title" content="Best No Fee Apartments in Brooklyn, NY | NoFeesApts" />
        <meta property="og:description" content={`${String(stats.count)}+ verified no-fee apartments in Brooklyn. DUMBO, Williamsburg, Brooklyn Heights & more. Save thousands on broker fees.`} />
        <meta property="og:url" content="https://www.nofeesapts.com/brooklyn" />
        <meta property="og:type" content="website" />
        
        {/* Schema.org */}
        <script type="application/ld+json">{JSON.stringify(schemaData)}</script>
        <script type="application/ld+json">{JSON.stringify(faqSchema)}</script>
      </Helmet>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link to="/" className="text-2xl font-philosopher font-bold text-[#0a0a0a]">
            NoFeesApts
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/auth" className="text-gray-600 hover:text-[#D4AF37] font-philosopher">
              Sign In
            </Link>
            <Button
              onClick={() => navigate('/auth')}
              className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-6 py-2 rounded-none"
            >
              FREE SIGN UP
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-16 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Breadcrumb */}
          <nav className="text-sm text-gray-500 mb-6">
            <Link to="/" className="hover:text-[#D4AF37]">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-gray-900">Brooklyn</span>
          </nav>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl sm:text-5xl font-philosopher font-bold text-[#0a0a0a] mb-6">
                Best No Fee Apartments in <span className="text-[#D4AF37]">Brooklyn</span>
              </h1>
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                Discover {stats.count}+ verified no broker fee apartments across Brooklyn's most sought-after neighborhoods. From DUMBO's waterfront luxury to Williamsburg's creative energy—find your perfect home without paying thousands in broker fees.
              </p>
              
              {/* Stats */}
              <div className="flex gap-8 mb-8">
                <div>
                  <p className="text-3xl font-bold text-[#D4AF37]">{stats.count}+</p>
                  <p className="text-sm text-gray-500">No-Fee Listings</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-[#0a0a0a]">{formatPrice(stats.avgRent)}</p>
                  <p className="text-sm text-gray-500">Avg. Rent</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-green-600">$0</p>
                  <p className="text-sm text-gray-500">Broker Fees</p>
                </div>
              </div>

              <Button
                onClick={() => navigate('/auth')}
                className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-8 py-6 text-lg rounded-none"
              >
                BROWSE ALL BROOKLYN LISTINGS
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>

            {/* Top Reasons Card */}
            <div className="bg-white border border-gray-200 p-8 shadow-sm">
              <h2 className="text-xl font-philosopher font-bold text-[#0a0a0a] mb-6">
                Why Choose No-Fee Apartments?
              </h2>
              <ul className="space-y-4">
                {topReasons.map((reason, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-[#D4AF37] mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Brooklyn Neighborhoods */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-3">
            Brooklyn Neighborhoods
          </h2>
          <p className="text-gray-600 mb-8">
            Explore no-fee apartments in Brooklyn's most popular areas
          </p>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {brooklynNeighborhoods.map((neighborhood) => (
              <Link
                key={neighborhood.slug}
                to={`/apartments/${neighborhood.slug}`}
                className="group block p-6 border border-gray-200 hover:border-[#D4AF37] transition-all duration-300 hover:shadow-lg"
              >
                <h3 className="text-lg font-philosopher font-bold text-[#0a0a0a] group-hover:text-[#D4AF37] transition-colors mb-2">
                  {neighborhood.name}
                </h3>
                <p className="text-sm text-gray-500 mb-4">
                  {neighborhood.description}
                </p>
                <span className="text-[#D4AF37] text-sm font-medium flex items-center gap-1">
                  View Listings <ArrowRight className="w-4 h-4" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Listings Preview */}
      {units.length > 0 && (
        <section className="py-16 px-6 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-2">
                  Featured Brooklyn Apartments
                </h2>
                <p className="text-gray-600">Sign up free to see all details and contact landlords</p>
              </div>
              <Button
                onClick={() => navigate('/auth')}
                variant="outline"
                className="border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#0a0a0a] font-philosopher"
              >
                View All
              </Button>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {units.slice(0, 6).map((unit) => (
                <div
                  key={unit.id}
                  onClick={() => navigate('/auth')}
                  className="group bg-white border border-gray-200 overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300"
                >
                  {/* Image */}
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={unit.images?.[0] || 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600'}
                      alt={`No fee apartment in ${unit.building?.neighborhood || 'Brooklyn'}`}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute top-3 left-3 bg-[#D4AF37] text-[#0a0a0a] px-3 py-1 text-sm font-bold">
                      NO FEE
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <p className="text-2xl font-bold text-[#0a0a0a] mb-1">
                      {formatPrice(unit.rent)}<span className="text-sm font-normal text-gray-500">/mo</span>
                    </p>
                    <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
                      <span>{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} Bed`}</span>
                      <span>•</span>
                      <span>{unit.bathrooms} Bath</span>
                      {unit.square_feet && (
                        <>
                          <span>•</span>
                          <span>{unit.square_feet} SF</span>
                        </>
                      )}
                    </div>
                    <p className="text-sm text-gray-400 blur-[3px] select-none">
                      {unit.building?.address || '123 Brooklyn St'}
                    </p>
                    <p className="text-xs text-[#D4AF37] mt-2">Sign up to view address →</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* FAQ Section */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-3 text-center">
            Frequently Asked Questions
          </h2>
          <p className="text-gray-600 text-center mb-10">
            Everything you need to know about no-fee apartments in Brooklyn
          </p>

          <div className="space-y-6">
            {faqs.map((faq, i) => (
              <div key={i} className="border-b border-gray-200 pb-6">
                <h3 className="text-lg font-semibold text-[#0a0a0a] mb-3">
                  {faq.q}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {faq.a}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SEO Content */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-philosopher font-bold text-[#0a0a0a] mb-6">
            Finding No Fee Apartments in Brooklyn
          </h2>
          <div className="prose prose-gray max-w-none">
            <p className="text-gray-600 mb-4">
              Brooklyn has transformed from a sleepy borough into one of the most desirable places to live in New York City. From the cobblestone streets of DUMBO with its jaw-dropping Manhattan skyline views to the hipster haven of Williamsburg, Brooklyn offers diverse neighborhoods to match any lifestyle.
            </p>
            <p className="text-gray-600 mb-4">
              No-fee apartments in Brooklyn are offered by landlords and management companies who handle their own marketing, eliminating the need for a broker. This means you deal directly with the property, get faster responses, and most importantly—keep thousands of dollars in your pocket.
            </p>
            <p className="text-gray-600 mb-4">
              At NoFeesApts.com, we specialize in verified no broker fee listings across Brooklyn. Our database is updated daily with new inventory from luxury high-rises in Downtown Brooklyn to charming walk-ups in Carroll Gardens. Whether you're a young professional seeking a studio in Williamsburg or a family looking for a 2-bedroom in Park Slope, we've got you covered.
            </p>
            <p className="text-gray-600">
              <strong>Ready to find your Brooklyn apartment?</strong> Sign up free to browse all listings, see full addresses, and contact landlords directly. No credit card required, no broker fees ever.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-6 bg-[#0a0a0a]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-philosopher font-bold text-white mb-4">
            Start Your Brooklyn Apartment Search
          </h2>
          <p className="text-gray-400 mb-8">
            Join thousands of renters who found their perfect no-fee apartment
          </p>
          <Button
            onClick={() => navigate('/auth')}
            className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-10 py-6 text-lg rounded-none"
          >
            BROWSE FREE — NO CREDIT CARD REQUIRED
          </Button>
        </div>
      </section>

      {/* Author/Trust Signal */}
      <section className="py-8 px-6 bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <div className="w-12 h-12 bg-[#D4AF37] rounded-full flex items-center justify-center">
            <Star className="w-6 h-6 text-white" />
          </div>
          <div>
            <p className="text-sm text-gray-500">
              <strong className="text-gray-900">NoFeesApts Editorial Team</strong> · Updated March 2026
            </p>
            <p className="text-xs text-gray-400">
              Our team verifies all listings and updates this page with the latest Brooklyn market data.
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default BrooklynPage;
