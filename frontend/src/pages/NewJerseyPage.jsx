import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowRight, Check, Star, Train } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';
import axios from '../utils/axiosConfig';
import { API } from '../App';

// NJ neighborhoods data
const njNeighborhoods = [
  { slug: 'jersey-city', name: 'Jersey City', description: 'NYC views, waterfront living, PATH access' },
  { slug: 'hoboken', name: 'Hoboken', description: 'Walkable streets, vibrant nightlife, NYC commute' },
  { slug: 'weehawken', name: 'Weehawken', description: 'Stunning Manhattan skyline views' },
  { slug: 'harrison', name: 'Harrison', description: 'Emerging waterfront with new developments' },
  { slug: 'newark', name: 'Newark', description: 'Urban revival with affordable options' },
  { slug: 'edgewater', name: 'Edgewater', description: 'Quiet waterfront community' },
  { slug: 'fort-lee', name: 'Fort Lee', description: 'GW Bridge access, high-rise living' },
  { slug: 'union-city', name: 'Union City', description: 'Affordable with NYC proximity' }
];

// FAQ data for SEO
const faqs = [
  {
    q: "What is the average rent for a no-fee apartment in Northern New Jersey?",
    a: "No-fee apartment rents in Northern NJ range from $1,800 for studios in Harrison to $4,500+ for luxury 2-bedrooms in Jersey City and Hoboken waterfront. By avoiding broker fees (typically one month's rent), you can save $2,000-$5,000 on your move."
  },
  {
    q: "Which NJ towns have the most no-fee apartments?",
    a: "Jersey City has the highest concentration of no-fee apartments due to its many luxury waterfront developments. Hoboken, Harrison, and Weehawken also offer significant no-fee inventory from major developers like LeFrak, Ironstate, and Veris Residential."
  },
  {
    q: "How long is the commute from Jersey City to Manhattan?",
    a: "The PATH train connects Jersey City to Manhattan in just 10-20 minutes. From Exchange Place to World Trade Center is under 10 minutes. Hoboken to 33rd Street is about 20 minutes. NY Waterway ferries offer scenic alternatives."
  },
  {
    q: "Is Northern NJ cheaper than NYC?",
    a: "Yes! You can typically save 20-40% on rent compared to similar Manhattan apartments. A luxury 1-bedroom in Jersey City averages $3,200 vs $4,500+ in Manhattan, plus NJ has no city income tax on top of state taxes."
  },
  {
    q: "What's the best NJ town for young professionals?",
    a: "Hoboken is ideal for young professionals with its walkable downtown, bars/restaurants, and easy NYC commute. Jersey City's downtown and waterfront areas offer more space and growing food/entertainment scenes. Harrison is emerging as an affordable alternative."
  }
];

// Top reasons listicle
const topReasons = [
  "Save 20-40% compared to Manhattan rents",
  "10-20 minute PATH train to NYC",
  "No broker fees at major developments",
  "Luxury amenities: pools, gyms, rooftops",
  "More space for your money"
];

const NewJerseyPage = () => {
  const navigate = useNavigate();
  const [units, setUnits] = useState([]);
  const [stats, setStats] = useState({ count: 0, avgRent: 0, minRent: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNJUnits();
  }, []);

  const fetchNJUnits = async () => {
    try {
      const response = await axios.get(`${API}/units?limit=150`);
      const allUnits = response.data || [];
      
      // NJ cities and neighborhoods to filter
      const njCities = ['jersey city', 'hoboken', 'weehawken', 'harrison', 'newark', 
        'edgewater', 'fort lee', 'union city', 'north bergen', 'west new york',
        'bayonne', 'secaucus', 'linden', 'princeton', 'hamilton township'];
      
      const njUnits = allUnits.filter(u => {
        const building = u.building || {};
        const state = (building.state || '').toUpperCase();
        const city = (building.city || '').toLowerCase();
        return state === 'NJ' || njCities.some(c => city.includes(c));
      });
      
      setUnits(njUnits);

      if (njUnits.length > 0) {
        const rents = njUnits.map(u => u.rent).filter(r => r > 0);
        setStats({
          count: njUnits.length,
          avgRent: rents.length > 0 ? Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) : 0,
          minRent: rents.length > 0 ? Math.min(...rents) : 0
        });
      }
    } catch (error) {
      console.error('Error fetching NJ units:', error);
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
    "name": "Best No Fee Apartments in New Jersey",
    "description": "Find the best no broker fee apartments in Northern New Jersey. Browse verified no-fee listings in Jersey City, Hoboken, Weehawken, Harrison, and more.",
    "url": "https://www.nofeesapts.com/new-jersey",
    "mainEntity": {
      "@type": "ItemList",
      "name": "New Jersey No-Fee Apartments",
      "numberOfItems": stats.count,
      "itemListElement": njNeighborhoods.map((n, i) => ({
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
        { "@type": "ListItem", "position": 2, "name": "New Jersey", "item": "https://www.nofeesapts.com/new-jersey" }
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
        <title>Best No Fee Apartments in New Jersey | {String(stats.count)}+ Verified Listings | NoFeesApts</title>
        <meta name="description" content={`Find the best no broker fee apartments in Northern New Jersey. Browse ${String(stats.count)}+ verified no-fee listings in Jersey City, Hoboken, Harrison & more. 10-20 min to NYC. Save thousands on broker fees.`} />
        <meta name="keywords" content="no fee apartments New Jersey, NJ no broker fee, Jersey City apartments no fee, Hoboken no fee apartments, Harrison NJ rentals, Weehawken apartments, no broker fee NJ, best NJ apartments near NYC, waterfront apartments NJ" />
        <link rel="canonical" href="https://www.nofeesapts.com/new-jersey" />
        <meta property="og:title" content="Best No Fee Apartments in New Jersey | NoFeesApts" />
        <meta property="og:description" content={`${String(stats.count)}+ verified no-fee apartments in NJ. Jersey City, Hoboken, Harrison & more. 10-20 min to NYC. Save thousands.`} />
        <meta property="og:url" content="https://www.nofeesapts.com/new-jersey" />
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
            <span className="text-gray-900">New Jersey</span>
          </nav>

          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl sm:text-5xl font-philosopher font-bold text-[#0a0a0a] mb-6">
                Best No Fee Apartments in <span className="text-[#D4AF37]">New Jersey</span>
              </h1>
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                Discover {stats.count}+ verified no broker fee apartments across Northern New Jersey's hottest waterfront communities. From Jersey City's stunning skyline views to Hoboken's walkable charm—find your perfect home minutes from Manhattan without paying broker fees.
              </p>
              
              {/* Transit highlight */}
              <div className="flex items-center gap-2 mb-6 text-sm text-gray-600 bg-blue-50 px-4 py-2 rounded-lg w-fit">
                <Train className="w-4 h-4 text-blue-600" />
                <span><strong className="text-blue-600">10-20 min</strong> PATH train to Manhattan</span>
              </div>
              
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
                BROWSE ALL NJ LISTINGS <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>

            <div className="bg-white border border-gray-200 p-8 shadow-sm">
              <h2 className="text-xl font-philosopher font-bold text-[#0a0a0a] mb-6">Why Choose NJ Over NYC?</h2>
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

      {/* NJ Neighborhoods */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-3">Northern NJ Towns</h2>
          <p className="text-gray-600 mb-8">Explore no-fee apartments in NJ's most popular NYC-commuter towns</p>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {njNeighborhoods.map((neighborhood) => (
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
                <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-2">Featured NJ Apartments</h2>
                <p className="text-gray-600">Sign up free to see all details and contact landlords</p>
              </div>
              <Button onClick={() => navigate('/auth')} variant="outline" className="border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#0a0a0a] font-philosopher">View All</Button>
            </div>

            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {units.slice(0, 6).map((unit) => (
                <div key={unit.id} onClick={() => navigate('/auth')} className="group bg-white border border-gray-200 overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300">
                  <div className="relative h-48 overflow-hidden">
                    <img src={unit.images?.[0] || 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600'} alt={`No fee apartment in ${unit.building?.city || 'New Jersey'}`} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
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
                    <p className="text-sm text-gray-400 blur-[3px] select-none">{unit.building?.address || '123 Waterfront Dr'}</p>
                    <p className="text-xs text-[#D4AF37] mt-2">Sign up to view address →</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Commute Info */}
      <section className="py-16 px-6 bg-blue-50">
        <div className="max-w-4xl mx-auto text-center">
          <Train className="w-12 h-12 text-blue-600 mx-auto mb-4" />
          <h2 className="text-2xl font-philosopher font-bold text-[#0a0a0a] mb-4">Easy NYC Commute</h2>
          <div className="grid sm:grid-cols-3 gap-6 mt-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <p className="text-3xl font-bold text-blue-600">10 min</p>
              <p className="text-gray-600 text-sm mt-1">Exchange Place → WTC</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <p className="text-3xl font-bold text-blue-600">15 min</p>
              <p className="text-gray-600 text-sm mt-1">Hoboken → 33rd St</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <p className="text-3xl font-bold text-blue-600">20 min</p>
              <p className="text-gray-600 text-sm mt-1">Harrison → WTC</p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-3 text-center">Frequently Asked Questions</h2>
          <p className="text-gray-600 text-center mb-10">Everything you need to know about no-fee apartments in New Jersey</p>
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
          <h2 className="text-2xl font-philosopher font-bold text-[#0a0a0a] mb-6">Finding No Fee Apartments in New Jersey</h2>
          <div className="prose prose-gray max-w-none">
            <p className="text-gray-600 mb-4">Northern New Jersey has become one of the most popular alternatives to living in New York City. With stunning Manhattan skyline views, waterfront parks, and a fraction of the commute time many NYC residents endure, towns like Jersey City, Hoboken, and Harrison offer the best of both worlds.</p>
            <p className="text-gray-600 mb-4">No-fee apartments in NJ are offered by major developers like LeFrak, Ironstate Development, Veris Residential (formerly Mack-Cali), and Bozzuto who manage their own leasing. This means you deal directly with the property, avoid broker fees, and often receive move-in specials like free months of rent.</p>
            <p className="text-gray-600 mb-4">Jersey City's waterfront has transformed into a luxury residential destination with buildings offering amenities rivaling Manhattan towers—pools, rooftop lounges, fitness centers, co-working spaces—at significantly lower rents. Hoboken maintains its charming walkable downtown while adding modern high-rises. Harrison, with its new PATH station, is emerging as the affordable alternative for those priced out of JC and Hoboken.</p>
            <p className="text-gray-600"><strong>Ready to find your NJ apartment?</strong> Sign up free to browse all listings, see full addresses, and contact landlords directly. No credit card required, no broker fees ever.</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-6 bg-[#0a0a0a]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-philosopher font-bold text-white mb-4">Start Your NJ Apartment Search</h2>
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
            <p className="text-xs text-gray-400">Our team verifies all listings and updates this page with the latest NJ market data.</p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default NewJerseyPage;
