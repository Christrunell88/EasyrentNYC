import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowRight, Check, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';
import axios from '../utils/axiosConfig';
import { API } from '../App';

// Queens neighborhoods data
const queensNeighborhoods = [
  { slug: 'long-island-city', name: 'Long Island City', description: 'Stunning skyline views and waterfront parks' },
  { slug: 'astoria', name: 'Astoria', description: 'Diverse dining and vibrant nightlife' },
  { slug: 'flushing', name: 'Flushing', description: 'Cultural hub with authentic Asian cuisine' },
  { slug: 'jamaica', name: 'Jamaica', description: 'Transit hub with growing development' },
  { slug: 'forest-hills', name: 'Forest Hills', description: 'Tree-lined streets and Tudor architecture' },
  { slug: 'sunnyside', name: 'Sunnyside', description: 'Affordable charm near Manhattan' },
  { slug: 'jackson-heights', name: 'Jackson Heights', description: 'Historic co-ops and diverse community' },
  { slug: 'rego-park', name: 'Rego Park', description: 'Family-friendly with great shopping' }
];

// FAQ data for SEO
const faqs = [
  {
    q: "What is the average rent for a no-fee apartment in Queens?",
    a: "No-fee apartment rents in Queens range from $1,800 for studios in Jamaica to $4,500+ for luxury 2-bedrooms in Long Island City. By avoiding broker fees (typically 12-15% of annual rent), you can save $2,500-$6,000 on your move."
  },
  {
    q: "Which Queens neighborhoods have the most no-fee apartments?",
    a: "Long Island City has the highest concentration of no-fee apartments due to its many luxury high-rises. Astoria, Sunnyside, and Forest Hills also offer good no-fee inventory in newer developments."
  },
  {
    q: "How do I find a no-fee apartment in Queens?",
    a: "Use NoFeesApts.com to browse verified no-fee listings updated daily. Filter by neighborhood, price, and bedrooms. Sign up free to see full addresses and contact landlords directly—no broker needed."
  },
  {
    q: "Is Queens a good alternative to Manhattan?",
    a: "Absolutely! Queens offers more space for your money, diverse neighborhoods, excellent food scenes, and quick subway access to Manhattan. Long Island City is just one stop from Midtown on the 7 train."
  },
  {
    q: "What's the best time to find no-fee apartments in Queens?",
    a: "Winter (December-February) often has the best deals as demand is lower. Long Island City sees new inventory year-round from luxury developments. Set up alerts on NoFeesApts.com to be notified instantly."
  }
];

// Top reasons listicle
const topReasons = [
  "Save $2,500-$6,000 by avoiding broker fees",
  "More space for your money than Manhattan",
  "Quick subway access to Midtown",
  "Diverse food scenes and culture",
  "Waterfront parks and skyline views"
];

const QueensPage = () => {
  const navigate = useNavigate();
  const [units, setUnits] = useState([]);
  const [stats, setStats] = useState({ count: 0, avgRent: 0, minRent: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchQueensUnits();
  }, []);

  const fetchQueensUnits = async () => {
    try {
      const response = await axios.get(`${API}/units?limit=150`);
      const allUnits = response.data || [];
      
      // Queens neighborhoods to filter
      const queensNeighborhoodNames = ['Long Island City', 'Astoria', 'Flushing', 'Jamaica', 
        'Forest Hills', 'Sunnyside', 'Jackson Heights', 'Rego Park', 'Woodside', 'Elmhurst',
        'Corona', 'Ridgewood', 'Glendale', 'Bayside', 'Fresh Meadows'];
      
      const queensUnits = allUnits.filter(u => {
        const building = u.building || {};
        const city = (building.city || '').toLowerCase();
        const neighborhood = building.neighborhood || '';
        return city === 'queens' || city === 'long island city' || city === 'jamaica' || queensNeighborhoodNames.includes(neighborhood);
      });
      
      setUnits(queensUnits);

      if (queensUnits.length > 0) {
        const rents = queensUnits.map(u => u.rent).filter(r => r > 0);
        setStats({
          count: queensUnits.length,
          avgRent: rents.length > 0 ? Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) : 0,
          minRent: rents.length > 0 ? Math.min(...rents) : 0
        });
      }
    } catch (error) {
      console.error('Error fetching Queens units:', error);
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
    "name": "Best No Fee Apartments in Queens, NY",
    "description": "Find the best no broker fee apartments in Queens. Browse verified no-fee listings in Long Island City, Astoria, Flushing, and more.",
    "url": "https://www.nofeesapts.com/queens",
    "mainEntity": {
      "@type": "ItemList",
      "name": "Queens No-Fee Apartments",
      "numberOfItems": stats.count,
      "itemListElement": queensNeighborhoods.map((n, i) => ({
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
        { "@type": "ListItem", "position": 2, "name": "Queens", "item": "https://www.nofeesapts.com/queens" }
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
        <title>Best No Fee Apartments in Queens, NY | {String(stats.count)}+ Verified Listings | NoFeesApts</title>
        <meta name="description" content={`Find the best no broker fee apartments in Queens. Browse ${String(stats.count)}+ verified no-fee listings in Long Island City, Astoria, Flushing & more. Save thousands on broker fees. Updated daily.`} />
        <meta name="keywords" content="no fee apartments Queens, Queens no broker fee, Long Island City apartments no fee, Astoria no fee apartments, Flushing rentals, Jamaica Queens apartments, no broker fee Queens NY, best Queens apartments, LIC apartments no fee" />
        <link rel="canonical" href="https://www.nofeesapts.com/queens" />
        <meta property="og:title" content="Best No Fee Apartments in Queens, NY | NoFeesApts" />
        <meta property="og:description" content={`${String(stats.count)}+ verified no-fee apartments in Queens. LIC, Astoria, Flushing & more. Save thousands on broker fees.`} />
        <meta property="og:url" content="https://www.nofeesapts.com/queens" />
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
            <span className="text-gray-900">Queens</span>
          </nav>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl sm:text-5xl font-philosopher font-bold text-[#0a0a0a] mb-6">
                Best No Fee Apartments in <span className="text-[#D4AF37]">Queens</span>
              </h1>
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                Discover {stats.count}+ verified no broker fee apartments across Queens' most dynamic neighborhoods. From Long Island City's stunning skyline views to Astoria's vibrant food scene—find your perfect home without paying thousands in broker fees.
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
                BROWSE ALL QUEENS LISTINGS <ArrowRight className="w-5 h-5 ml-2" />
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

      {/* Queens Neighborhoods */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-3">Queens Neighborhoods</h2>
          <p className="text-gray-600 mb-8">Explore no-fee apartments in Queens' most popular areas</p>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {queensNeighborhoods.map((neighborhood) => (
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
                <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-2">Featured Queens Apartments</h2>
                <p className="text-gray-600">Sign up free to see all details and contact landlords</p>
              </div>
              <Button onClick={() => navigate('/auth')} variant="outline" className="border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#0a0a0a] font-philosopher">View All</Button>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {units.slice(0, 6).map((unit) => (
                <div key={unit.id} onClick={() => navigate('/auth')} className="group bg-white border border-gray-200 overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300">
                  <div className="relative h-48 overflow-hidden">
                    <img src={unit.images?.[0] || 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600'} alt={`No fee apartment in ${unit.building?.neighborhood || 'Queens'}`} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
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
                    <p className="text-sm text-gray-400 blur-[3px] select-none">{unit.building?.address || '123 Queens Blvd'}</p>
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
          <p className="text-gray-600 text-center mb-10">Everything you need to know about no-fee apartments in Queens</p>
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
          <h2 className="text-2xl font-philosopher font-bold text-[#0a0a0a] mb-6">Finding No Fee Apartments in Queens</h2>
          <div className="prose prose-gray max-w-none">
            <p className="text-gray-600 mb-4">Queens is New York City's largest and most diverse borough, offering incredible value for renters seeking more space without sacrificing Manhattan access. From the gleaming towers of Long Island City to the authentic ethnic enclaves of Flushing and Jackson Heights, Queens has something for everyone.</p>
            <p className="text-gray-600 mb-4">No-fee apartments in Queens are offered by landlords and management companies who handle their own marketing, eliminating the need for a broker. This means you deal directly with the property, get faster responses, and most importantly—keep thousands of dollars in your pocket.</p>
            <p className="text-gray-600 mb-4">At NoFeesApts.com, we specialize in verified no broker fee listings across Queens. Our database is updated daily with new inventory from luxury waterfront high-rises in Long Island City to charming walk-ups in Astoria and Sunnyside.</p>
            <p className="text-gray-600"><strong>Ready to find your Queens apartment?</strong> Sign up free to browse all listings, see full addresses, and contact landlords directly. No credit card required, no broker fees ever.</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-6 bg-[#0a0a0a]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-philosopher font-bold text-white mb-4">Start Your Queens Apartment Search</h2>
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
            <p className="text-xs text-gray-400">Our team verifies all listings and updates this page with the latest Queens market data.</p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default QueensPage;
