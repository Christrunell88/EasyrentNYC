import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowRight, Check, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';
import axios from '../utils/axiosConfig';
import { API } from '../App';

// Manhattan neighborhoods data
const manhattanNeighborhoods = [
  { slug: 'chelsea', name: 'Chelsea', description: 'Art galleries, High Line, and trendy dining' },
  { slug: 'tribeca', name: 'Tribeca', description: 'Celebrity-favorite with cobblestone streets' },
  { slug: 'financial-district', name: 'Financial District', description: 'Historic Wall Street with modern towers' },
  { slug: 'midtown-west', name: 'Midtown West', description: 'Theater District and Hudson Yards access' },
  { slug: 'upper-west-side', name: 'Upper West Side', description: 'Central Park views and cultural institutions' },
  { slug: 'upper-east-side', name: 'Upper East Side', description: 'Museum Mile and classic elegance' },
  { slug: 'west-village', name: 'West Village', description: 'Charming brownstones and nightlife' },
  { slug: 'soho', name: 'SoHo', description: 'Cast-iron architecture and designer shopping' }
];

// FAQ data for SEO
const faqs = [
  {
    q: "What is the average rent for a no-fee apartment in Manhattan?",
    a: "No-fee apartment rents in Manhattan range from $2,800 for studios in Upper Manhattan to $8,000+ for luxury 2-bedrooms in Tribeca and Chelsea. By avoiding broker fees (typically 12-15% of annual rent), you can save $4,000-$12,000 on your move."
  },
  {
    q: "Which Manhattan neighborhoods have the most no-fee apartments?",
    a: "Financial District, Midtown West, and Chelsea have the highest concentration of no-fee apartments due to large luxury developments. The Upper West Side and Murray Hill also offer strong no-fee inventory in newer buildings."
  },
  {
    q: "How do I find a no-fee apartment in Manhattan?",
    a: "Use NoFeesApts.com to browse verified no-fee listings updated daily. Filter by neighborhood, price, and bedrooms. Sign up free to see full addresses and contact landlords directly—no broker needed."
  },
  {
    q: "Are no-fee apartments in Manhattan legit?",
    a: "Yes! No-fee apartments are offered directly by landlords or management companies who pay for marketing themselves. At NoFeesApts.com, we verify all listings to ensure they're genuinely broker-fee-free."
  },
  {
    q: "What's the best time to find no-fee apartments in Manhattan?",
    a: "Winter (December-February) often has the best deals as demand is lower. However, new no-fee inventory from luxury buildings is added year-round. Set up alerts on NoFeesApts.com to be notified instantly."
  }
];

// Top reasons listicle
const topReasons = [
  "Save $4,000-$12,000 by avoiding broker fees",
  "Deal directly with landlords—no middleman",
  "Luxury amenities: doorman, gym, rooftop, laundry",
  "Prime locations near subways and parks",
  "Transparent pricing—what you see is what you pay"
];

const ManhattanPage = () => {
  const navigate = useNavigate();
  const [units, setUnits] = useState([]);
  const [stats, setStats] = useState({ count: 0, avgRent: 0, minRent: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchManhattanUnits();
  }, []);

  const fetchManhattanUnits = async () => {
    try {
      const response = await axios.get(`${API}/units?limit=150`);
      const allUnits = response.data || [];
      
      // Manhattan neighborhoods to filter
      const manhattanNeighborhoodNames = ['Chelsea', 'Tribeca', 'Financial District', 'Midtown West', 
        'Upper West Side', 'Upper East Side', 'West Village', 'SoHo', 'Flatiron District', 'Murray Hill',
        'Kips Bay', 'Gramercy', 'East Village', 'Hudson Yards', 'Harlem', 'Hell\'s Kitchen', 'NoHo', 'Nolita'];
      
      const manhattanUnits = allUnits.filter(u => {
        const building = u.building || {};
        const city = (building.city || '').toLowerCase();
        const neighborhood = building.neighborhood || '';
        return city === 'manhattan' || city === 'new york' || manhattanNeighborhoodNames.includes(neighborhood);
      });
      
      setUnits(manhattanUnits);

      if (manhattanUnits.length > 0) {
        const rents = manhattanUnits.map(u => u.rent).filter(r => r > 0);
        setStats({
          count: manhattanUnits.length,
          avgRent: rents.length > 0 ? Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) : 0,
          minRent: rents.length > 0 ? Math.min(...rents) : 0
        });
      }
    } catch (error) {
      console.error('Error fetching Manhattan units:', error);
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
    "name": "Best No Fee Apartments in Manhattan, NY",
    "description": "Find the best no broker fee apartments in Manhattan. Browse verified no-fee listings in Chelsea, Tribeca, Financial District, Upper West Side, and more.",
    "url": "https://www.nofeesapts.com/manhattan",
    "mainEntity": {
      "@type": "ItemList",
      "name": "Manhattan No-Fee Apartments",
      "numberOfItems": stats.count,
      "itemListElement": manhattanNeighborhoods.map((n, i) => ({
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
        { "@type": "ListItem", "position": 2, "name": "Manhattan", "item": "https://www.nofeesapts.com/manhattan" }
      ]
    }
  };

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faqs.map(faq => ({
      "@type": "Question",
      "name": faq.q,
      "acceptedAnswer": { "@type": "Answer", "text": faq.a }
    }))
  };

  return (
    <div className="min-h-screen bg-white">
      <Helmet>
        <title>Best No Fee Apartments in Manhattan, NY | {String(stats.count)}+ Verified Listings | NoFeesApts</title>
        <meta name="description" content={`Find the best no broker fee apartments in Manhattan. Browse ${String(stats.count)}+ verified no-fee listings in Chelsea, Tribeca, Financial District & more. Save thousands on broker fees. Updated daily.`} />
        <meta name="keywords" content="no fee apartments Manhattan, Manhattan no broker fee, Chelsea apartments no fee, Tribeca no fee apartments, Financial District rentals, Upper West Side apartments, no broker fee Manhattan NY, best Manhattan apartments, luxury Manhattan apartments no fee" />
        <link rel="canonical" href="https://www.nofeesapts.com/manhattan" />
        <meta property="og:title" content="Best No Fee Apartments in Manhattan, NY | NoFeesApts" />
        <meta property="og:description" content={`${String(stats.count)}+ verified no-fee apartments in Manhattan. Chelsea, Tribeca, FiDi & more. Save thousands on broker fees.`} />
        <meta property="og:url" content="https://www.nofeesapts.com/manhattan" />
        <meta property="og:type" content="website" />
        <script type="application/ld+json">{JSON.stringify(schemaData)}</script>
        <script type="application/ld+json">{JSON.stringify(faqSchema)}</script>
      </Helmet>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link to="/" className="text-2xl font-philosopher font-bold text-[#0a0a0a]">NoFeesApts</Link>
          <div className="flex items-center gap-4">
            <Link to="/auth" className="text-gray-600 hover:text-[#D4AF37] font-philosopher">Sign In</Link>
            <Button onClick={() => navigate('/auth')} className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-6 py-2 rounded-none">FREE SIGN UP</Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-16 px-6">
        <div className="max-w-7xl mx-auto">
          <nav className="text-sm text-gray-500 mb-6">
            <Link to="/" className="hover:text-[#D4AF37]">Home</Link>
            <span className="mx-2">/</span>
            <span className="text-gray-900">Manhattan</span>
          </nav>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl sm:text-5xl font-philosopher font-bold text-[#0a0a0a] mb-6">
                Best No Fee Apartments in <span className="text-[#D4AF37]">Manhattan</span>
              </h1>
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                Discover {stats.count}+ verified no broker fee apartments across Manhattan's most iconic neighborhoods. From Chelsea's art scene to Tribeca's celebrity lofts—find your perfect home without paying thousands in broker fees.
              </p>
              
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

              <Button onClick={() => navigate('/auth')} className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-8 py-6 text-lg rounded-none">
                BROWSE ALL MANHATTAN LISTINGS <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>

            <div className="bg-white border border-gray-200 p-8 shadow-sm">
              <h2 className="text-xl font-philosopher font-bold text-[#0a0a0a] mb-6">Why Choose No-Fee Apartments?</h2>
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

      {/* Manhattan Neighborhoods */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-3">Manhattan Neighborhoods</h2>
          <p className="text-gray-600 mb-8">Explore no-fee apartments in Manhattan's most sought-after areas</p>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {manhattanNeighborhoods.map((neighborhood) => (
              <Link key={neighborhood.slug} to={`/apartments/${neighborhood.slug}`} className="group block p-6 border border-gray-200 hover:border-[#D4AF37] transition-all duration-300 hover:shadow-lg">
                <h3 className="text-lg font-philosopher font-bold text-[#0a0a0a] group-hover:text-[#D4AF37] transition-colors mb-2">{neighborhood.name}</h3>
                <p className="text-sm text-gray-500 mb-4">{neighborhood.description}</p>
                <span className="text-[#D4AF37] text-sm font-medium flex items-center gap-1">View Listings <ArrowRight className="w-4 h-4" /></span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Listings */}
      {units.length > 0 && (
        <section className="py-16 px-6 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-2">Featured Manhattan Apartments</h2>
                <p className="text-gray-600">Sign up free to see all details and contact landlords</p>
              </div>
              <Button onClick={() => navigate('/auth')} variant="outline" className="border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#0a0a0a] font-philosopher">View All</Button>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {units.slice(0, 6).map((unit) => (
                <div key={unit.id} onClick={() => navigate('/auth')} className="group bg-white border border-gray-200 overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300">
                  <div className="relative h-48 overflow-hidden">
                    <img src={unit.images?.[0] || 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600'} alt={`No fee apartment in ${unit.building?.neighborhood || 'Manhattan'}`} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    <div className="absolute top-3 left-3 bg-[#D4AF37] text-[#0a0a0a] px-3 py-1 text-sm font-bold">NO FEE</div>
                  </div>
                  <div className="p-4">
                    <p className="text-2xl font-bold text-[#0a0a0a] mb-1">{formatPrice(unit.rent)}<span className="text-sm font-normal text-gray-500">/mo</span></p>
                    <div className="flex items-center gap-3 text-sm text-gray-600 mb-2">
                      <span>{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} Bed`}</span>
                      <span>•</span>
                      <span>{unit.bathrooms} Bath</span>
                      {unit.square_feet && (<><span>•</span><span>{unit.square_feet} SF</span></>)}
                    </div>
                    <p className="text-sm text-gray-400 blur-[3px] select-none">{unit.building?.address || '123 Manhattan St'}</p>
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
          <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-3 text-center">Frequently Asked Questions</h2>
          <p className="text-gray-600 text-center mb-10">Everything you need to know about no-fee apartments in Manhattan</p>
          <div className="space-y-6">
            {faqs.map((faq, i) => (
              <div key={i} className="border-b border-gray-200 pb-6">
                <h3 className="text-lg font-semibold text-[#0a0a0a] mb-3">{faq.q}</h3>
                <p className="text-gray-600 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SEO Content */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-philosopher font-bold text-[#0a0a0a] mb-6">Finding No Fee Apartments in Manhattan</h2>
          <div className="prose prose-gray max-w-none">
            <p className="text-gray-600 mb-4">Manhattan remains the heart of New York City, offering unparalleled access to world-class dining, entertainment, and career opportunities. From the cobblestone streets of Tribeca to the bustling energy of Midtown, each neighborhood has its own distinct character.</p>
            <p className="text-gray-600 mb-4">No-fee apartments in Manhattan are offered by landlords and management companies who handle their own marketing, eliminating the need for a broker. This means you deal directly with the property, get faster responses, and most importantly—keep thousands of dollars in your pocket.</p>
            <p className="text-gray-600 mb-4">At NoFeesApts.com, we specialize in verified no broker fee listings across Manhattan. Our database is updated daily with new inventory from luxury high-rises in Hudson Yards to classic pre-war buildings on the Upper West Side.</p>
            <p className="text-gray-600"><strong>Ready to find your Manhattan apartment?</strong> Sign up free to browse all listings, see full addresses, and contact landlords directly. No credit card required, no broker fees ever.</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-6 bg-[#0a0a0a]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-philosopher font-bold text-white mb-4">Start Your Manhattan Apartment Search</h2>
          <p className="text-gray-400 mb-8">Join thousands of renters who found their perfect no-fee apartment</p>
          <Button onClick={() => navigate('/auth')} className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-10 py-6 text-lg rounded-none">BROWSE FREE — NO CREDIT CARD REQUIRED</Button>
        </div>
      </section>

      {/* Author/Trust Signal */}
      <section className="py-8 px-6 bg-white border-t border-gray-200">
        <div className="max-w-4xl mx-auto flex items-center gap-4">
          <div className="w-12 h-12 bg-[#D4AF37] rounded-full flex items-center justify-center">
            <Star className="w-6 h-6 text-white" />
          </div>
          <div>
            <p className="text-sm text-gray-500"><strong className="text-gray-900">NoFeesApts Editorial Team</strong> · Updated March 2026</p>
            <p className="text-xs text-gray-400">Our team verifies all listings and updates this page with the latest Manhattan market data.</p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default ManhattanPage;
