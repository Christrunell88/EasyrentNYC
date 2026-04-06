import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowRight, Check, Star, Train } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';
import axios from '../utils/axiosConfig';
import { API } from '../App';

// Jersey City neighborhoods
const jerseyCityNeighborhoods = [
  { slug: 'downtown-jersey-city', name: 'Downtown/Exchange Place', description: 'Waterfront towers with NYC views' },
  { slug: 'newport', name: 'Newport', description: 'Mall, PATH, and luxury high-rises' },
  { slug: 'journal-square', name: 'Journal Square', description: 'Historic transit hub, diverse dining' },
  { slug: 'jersey-city-heights', name: 'The Heights', description: 'Up-and-coming with great views' },
  { slug: 'grove-street', name: 'Grove Street', description: 'Trendy restaurants and nightlife' },
  { slug: 'liberty-state-park', name: 'Liberty State Park Area', description: 'Near the park and Liberty Landing' },
  { slug: 'greenville', name: 'Greenville', description: 'Affordable family neighborhood' },
  { slug: 'bergen-lafayette', name: 'Bergen-Lafayette', description: 'Artists and young professionals' }
];

// FAQ data for SEO
const faqs = [
  {
    q: "What is the average rent for a no-fee apartment in Jersey City?",
    a: "No-fee apartment rents in Jersey City range from $2,000 for studios to $4,000+ for luxury 2-bedrooms downtown. By avoiding broker fees AND paying lower NJ taxes, you can save $5,000-$10,000+ annually compared to similar Manhattan apartments."
  },
  {
    q: "How long is the commute from Jersey City to Manhattan?",
    a: "Jersey City offers excellent NYC access: Exchange Place to WTC is just 5 minutes on PATH, Grove Street to WTC is 8 minutes, and Journal Square to 33rd Street (Midtown) is about 20 minutes. Ferry options add more flexibility."
  },
  {
    q: "Is Jersey City a good alternative to NYC?",
    a: "Absolutely! Jersey City combines NYC-level dining, culture, and nightlife with lower taxes, cleaner streets, and waterfront living. The PATH train runs 24/7, making it as connected as many NYC neighborhoods—often more so."
  },
  {
    q: "Which Jersey City neighborhood is best for young professionals?",
    a: "Grove Street and Downtown (Exchange Place) are most popular for young professionals—walkable to restaurants, bars, and PATH. Newport offers luxury amenities. Journal Square provides better value with diverse food options."
  },
  {
    q: "What's the difference between Jersey City and Hoboken?",
    a: "Jersey City is larger and more diverse with varying neighborhoods from luxury waterfront (Downtown) to family-friendly (The Heights). Hoboken is smaller, more uniform, and centered around Washington Street nightlife. Both have excellent PATH access."
  }
];

// Top reasons listicle
const topReasons = [
  "5-minute PATH ride to World Trade Center",
  "Save $5,000-$10,000 annually on NJ taxes",
  "No broker fees—save another $3,000-$5,000",
  "24/7 PATH train service to Manhattan",
  "Waterfront parks with Statue of Liberty views"
];

const JerseyCityPage = () => {
  const navigate = useNavigate();
  const [units, setUnits] = useState([]);
  const [stats, setStats] = useState({ count: 0, avgRent: 0, minRent: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJerseyCityUnits();
  }, []);

  const fetchJerseyCityUnits = async () => {
    try {
      const response = await axios.get(`${API}/units?limit=100`);
      const allUnits = response.data || [];
      
      const jcUnits = allUnits.filter(u => {
        const building = u.building || {};
        const city = (building.city || '').toLowerCase();
        const neighborhood = (building.neighborhood || '').toLowerCase();
        
        return (
          city.includes('jersey city') ||
          neighborhood.includes('jersey city') ||
          neighborhood.includes('exchange place') ||
          neighborhood.includes('newport') ||
          neighborhood.includes('grove street') ||
          neighborhood.includes('journal square')
        );
      });
      
      setUnits(jcUnits.slice(0, 6));
      
      if (jcUnits.length > 0) {
        const rents = jcUnits.map(u => u.rent).filter(r => r > 0);
        setStats({
          count: jcUnits.length,
          avgRent: rents.length > 0 ? Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) : 0,
          minRent: rents.length > 0 ? Math.min(...rents) : 0
        });
      }
    } catch (error) {
      console.error('Error fetching Jersey City units:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatRent = (rent) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(rent);
  };

  return (
    <>
      <Helmet>
        <title>No Fee Apartments in Jersey City | 5 Min to NYC | NoFeesApts.com</title>
        <meta name="description" content={`Find ${stats.count || 'verified'} no-fee apartments in Jersey City. 5-min PATH to WTC. Save on broker fees AND NJ taxes. Waterfront living from ${stats.minRent ? formatRent(stats.minRent) : '$2,000'}/month.`} />
        <meta name="keywords" content="no fee apartments jersey city, jersey city apartments no broker fee, downtown jersey city apartments, grove street apartments, exchange place rentals, no fee rentals jersey city nj" />
        <link rel="canonical" href="https://nofeesapts.com/jersey-city" />
        
        <meta property="og:title" content="No Fee Apartments in Jersey City - 5 Min to NYC | NoFeesApts.com" />
        <meta property="og:description" content={`Browse ${stats.count || 'verified'} no-fee apartments in Jersey City. Waterfront views, 5-min PATH ride, massive tax savings.`} />
        <meta property="og:url" content="https://nofeesapts.com/jersey-city" />
        <meta property="og:type" content="website" />
        
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "No Fee Apartments in Jersey City",
            "description": "Browse verified no-fee apartments in Jersey City, New Jersey",
            "url": "https://nofeesapts.com/jersey-city",
            "isPartOf": { "@type": "WebSite", "name": "NoFeesApts.com", "url": "https://nofeesapts.com" },
            "about": { "@type": "Place", "name": "Jersey City", "address": { "@type": "PostalAddress", "addressLocality": "Jersey City", "addressRegion": "NJ" }}
          })}
        </script>
        
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faqs.map(faq => ({
              "@type": "Question",
              "name": faq.q,
              "acceptedAnswer": { "@type": "Answer", "text": faq.a }
            }))
          })}
        </script>
      </Helmet>

      <div className="min-h-screen bg-white">
        {/* Navigation */}
        <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
            <Link to="/" className="text-xl font-bold text-gray-900">NoFeesApts</Link>
            <div className="flex items-center gap-4">
              <Link to="/new-jersey" className="text-gray-600 hover:text-amber-600 text-sm">All NJ</Link>
              <Link to="/hoboken" className="text-gray-600 hover:text-amber-600 text-sm">Hoboken</Link>
              <Button onClick={() => navigate('/auth')} className="bg-amber-500 hover:bg-amber-600 text-white">
                Browse Free
              </Button>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="bg-gradient-to-br from-teal-900 via-teal-800 to-cyan-900 text-white py-20 px-6">
          <div className="max-w-5xl mx-auto text-center">
            <p className="text-teal-300 text-sm tracking-widest uppercase mb-4">Jersey City, New Jersey</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              No Fee Apartments in <span className="text-amber-400">Jersey City</span>
            </h1>
            <p className="text-xl text-teal-100 mb-8 max-w-2xl mx-auto">
              NYC's sixth borough. 5-minute PATH to Manhattan. Zero broker fees.
            </p>
            
            <div className="flex flex-wrap justify-center gap-8 mb-10">
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">{stats.count || '25'}+</p>
                <p className="text-teal-200 text-sm">No-Fee Listings</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">5 min</p>
                <p className="text-teal-200 text-sm">PATH to WTC</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">$0</p>
                <p className="text-teal-200 text-sm">Broker Fees</p>
              </div>
            </div>
            
            <Button 
              onClick={() => navigate('/auth')} 
              size="lg"
              className="bg-amber-500 hover:bg-amber-600 text-white px-8 py-6 text-lg"
            >
              View Jersey City Apartments <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        </section>

        {/* Why Jersey City Section */}
        <section className="py-16 px-6 bg-gray-50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-4">Why Choose Jersey City?</h2>
            <p className="text-gray-600 text-center mb-10 max-w-2xl mx-auto">
              Manhattan access, NJ taxes, waterfront living—the best of all worlds
            </p>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white p-8 rounded-xl shadow-sm">
                <h3 className="text-xl font-bold mb-4 text-gray-900">Top 5 Reasons for Jersey City</h3>
                <ul className="space-y-3">
                  {topReasons.map((reason, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-teal-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="bg-white p-8 rounded-xl shadow-sm">
                <h3 className="text-xl font-bold mb-4 text-gray-900">PATH Train to Manhattan</h3>
                <div className="space-y-4">
                  {[
                    { from: 'Exchange Place', to: 'World Trade Center', time: '5 min' },
                    { from: 'Grove Street', to: 'World Trade Center', time: '8 min' },
                    { from: 'Newport', to: 'World Trade Center', time: '6 min' },
                    { from: 'Journal Square', to: '33rd St (Midtown)', time: '20 min' }
                  ].map((route, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100">
                      <div className="flex items-center gap-2">
                        <Train className="w-4 h-4 text-teal-600" />
                        <span className="text-gray-700">{route.from} → {route.to}</span>
                      </div>
                      <span className="font-semibold text-amber-600">{route.time}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Neighborhoods Grid */}
        <section className="py-16 px-6">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-4">Jersey City Neighborhoods</h2>
            <p className="text-gray-600 text-center mb-10">From waterfront luxury to diverse communities</p>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {jerseyCityNeighborhoods.map((hood) => (
                <Link
                  key={hood.slug}
                  to={`/apartments/${hood.slug}`}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:border-amber-400 hover:shadow-md transition-all group"
                >
                  <h3 className="font-semibold text-gray-900 group-hover:text-amber-600">{hood.name}</h3>
                  <p className="text-gray-500 text-sm mt-1">{hood.description}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Featured Listings */}
        {units.length > 0 && (
          <section className="py-16 px-6 bg-gray-50">
            <div className="max-w-5xl mx-auto">
              <h2 className="text-3xl font-bold text-center mb-10">Featured Jersey City Apartments</h2>
              
              <div className="grid md:grid-cols-3 gap-6">
                {units.map((unit) => (
                  <div key={unit.id} className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow">
                    <div className="relative h-48">
                      <img 
                        src={unit.images?.[0] || unit.building?.images?.[0] || '/placeholder-apt.jpg'} 
                        alt={`${unit.building?.name || 'Apartment'}`}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute top-3 left-3 bg-teal-600 text-white text-xs font-bold px-2 py-1 rounded">
                        NO FEE
                      </div>
                    </div>
                    <div className="p-4">
                      <p className="text-2xl font-bold text-gray-900">{formatRent(unit.rent)}<span className="text-sm font-normal text-gray-500">/mo</span></p>
                      <p className="text-gray-600 mt-1">{unit.building?.name || 'Jersey City Apartment'}</p>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <BedDouble className="w-4 h-4" />
                          {unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} Bed`}
                        </span>
                        <span className="flex items-center gap-1">
                          <Bath className="w-4 h-4" />
                          {unit.bathrooms} Bath
                        </span>
                      </div>
                      <Button 
                        onClick={() => navigate(`/unit/${unit.id}`)}
                        className="w-full mt-4 bg-amber-500 hover:bg-amber-600"
                      >
                        View Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="text-center mt-10">
                <Button onClick={() => navigate('/auth')} variant="outline" size="lg">
                  View All Jersey City Apartments <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </div>
            </div>
          </section>
        )}

        {/* FAQ Section */}
        <section className="py-16 px-6">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-10">Frequently Asked Questions</h2>
            
            <div className="space-y-6">
              {faqs.map((faq, i) => (
                <div key={i} className="border-b border-gray-200 pb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{faq.q}</h3>
                  <p className="text-gray-600">{faq.a}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 px-6 bg-teal-900 text-white">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Find Your Jersey City Apartment?</h2>
            <p className="text-teal-200 mb-8">
              Waterfront living, Manhattan access, zero broker fees. Start your search today.
            </p>
            <Button 
              onClick={() => navigate('/auth')}
              size="lg"
              className="bg-amber-500 hover:bg-amber-600 text-white px-8"
            >
              Start Browsing Free <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        </section>

        <Footer />
      </div>
    </>
  );
};

export default JerseyCityPage;
