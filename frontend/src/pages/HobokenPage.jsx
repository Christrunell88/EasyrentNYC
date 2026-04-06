import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowRight, Check, Star, Train } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';
import axios from '../utils/axiosConfig';
import { API } from '../App';

// Hoboken neighborhoods/areas
const hobokenAreas = [
  { slug: 'hoboken', name: 'Downtown Hoboken', description: 'Vibrant Washington Street nightlife' },
  { slug: 'hoboken', name: 'Uptown Hoboken', description: 'Quieter, family-friendly streets' },
  { slug: 'hoboken', name: 'Hoboken Waterfront', description: 'NYC skyline views and parks' },
  { slug: 'weehawken', name: 'Weehawken', description: 'Lincoln Tunnel access, great views' },
  { slug: 'jersey-city', name: 'Journal Square', description: 'PATH hub with diverse dining' },
  { slug: 'jersey-city', name: 'Newport', description: 'Waterfront living near PATH' }
];

// FAQ data for SEO
const faqs = [
  {
    q: "What is the average rent for a no-fee apartment in Hoboken?",
    a: "No-fee apartment rents in Hoboken range from $2,400 for studios to $4,500+ for 2-bedrooms. While similar to some NYC neighborhoods, you save $3,000-$5,000 by avoiding broker fees AND benefit from lower NJ income taxes."
  },
  {
    q: "How long is the commute from Hoboken to Manhattan?",
    a: "Hoboken offers one of the fastest commutes to NYC: PATH train to World Trade Center is 10 minutes, to 33rd Street (Midtown) is 15-20 minutes. Ferry service to various Manhattan locations takes 5-10 minutes."
  },
  {
    q: "Is Hoboken better than living in NYC?",
    a: "Many choose Hoboken for: lower NJ income taxes (saving thousands annually), cleaner streets, excellent restaurants and nightlife, easy NYC access, strong community feel, and beautiful waterfront parks—often at similar or lower rents than comparable NYC neighborhoods."
  },
  {
    q: "What are the best areas to live in Hoboken?",
    a: "Downtown Hoboken (near Washington St) is best for nightlife and dining. Uptown is quieter and family-friendly. The Waterfront offers stunning NYC views and new luxury buildings. All areas have excellent PATH access."
  },
  {
    q: "Are there pet-friendly no-fee apartments in Hoboken?",
    a: "Yes! Many newer buildings in Hoboken are pet-friendly with dog runs and nearby parks like Pier A and Stevens Park. Filter for pet-friendly options on NoFeesApts.com."
  }
];

// Top reasons listicle
const topReasons = [
  "10-minute PATH ride to World Trade Center",
  "Save thousands on NJ income taxes vs NYC",
  "Avoid $3,000-$5,000 in broker fees",
  "Stunning Manhattan skyline views",
  "Walkable downtown with top restaurants"
];

const HobokenPage = () => {
  const navigate = useNavigate();
  const [units, setUnits] = useState([]);
  const [stats, setStats] = useState({ count: 0, avgRent: 0, minRent: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHobokenUnits();
  }, []);

  const fetchHobokenUnits = async () => {
    try {
      const response = await axios.get(`${API}/units?limit=100`);
      const allUnits = response.data || [];
      
      const hobokenUnits = allUnits.filter(u => {
        const building = u.building || {};
        const city = (building.city || '').toLowerCase();
        const neighborhood = (building.neighborhood || '').toLowerCase();
        
        return (
          city.includes('hoboken') ||
          neighborhood.includes('hoboken')
        );
      });
      
      setUnits(hobokenUnits.slice(0, 6));
      
      if (hobokenUnits.length > 0) {
        const rents = hobokenUnits.map(u => u.rent).filter(r => r > 0);
        setStats({
          count: hobokenUnits.length,
          avgRent: rents.length > 0 ? Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) : 0,
          minRent: rents.length > 0 ? Math.min(...rents) : 0
        });
      }
    } catch (error) {
      console.error('Error fetching Hoboken units:', error);
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
        <title>No Fee Apartments in Hoboken NJ | NYC Access | NoFeesApts.com</title>
        <meta name="description" content={`Find ${stats.count || 'verified'} no-fee apartments in Hoboken, NJ. 10-min PATH to NYC. Save on broker fees AND NJ taxes. Rents from ${stats.minRent ? formatRent(stats.minRent) : '$2,400'}/month.`} />
        <meta name="keywords" content="no fee apartments hoboken, hoboken apartments no broker fee, hoboken nj rentals, hoboken waterfront apartments, no fee rentals hoboken, apartments near path train" />
        <link rel="canonical" href="https://nofeesapts.com/hoboken" />
        
        <meta property="og:title" content="No Fee Apartments in Hoboken NJ - 10 Min to NYC | NoFeesApts.com" />
        <meta property="og:description" content={`Browse ${stats.count || 'verified'} no-fee apartments in Hoboken. NYC skyline views, 10-min PATH ride, lower taxes.`} />
        <meta property="og:url" content="https://nofeesapts.com/hoboken" />
        <meta property="og:type" content="website" />
        
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "No Fee Apartments in Hoboken",
            "description": "Browse verified no-fee apartments in Hoboken, New Jersey",
            "url": "https://nofeesapts.com/hoboken",
            "isPartOf": { "@type": "WebSite", "name": "NoFeesApts.com", "url": "https://nofeesapts.com" },
            "about": { "@type": "Place", "name": "Hoboken", "address": { "@type": "PostalAddress", "addressLocality": "Hoboken", "addressRegion": "NJ" }}
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
              <Link to="/apartments" className="text-gray-600 hover:text-amber-600 text-sm">All Neighborhoods</Link>
              <Button onClick={() => navigate('/auth')} className="bg-amber-500 hover:bg-amber-600 text-white">
                Browse Free
              </Button>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 text-white py-20 px-6">
          <div className="max-w-5xl mx-auto text-center">
            <p className="text-blue-300 text-sm tracking-widest uppercase mb-4">Hoboken, New Jersey</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              No Fee Apartments in <span className="text-amber-400">Hoboken</span>
            </h1>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              NYC skyline views, 10-minute PATH ride to Manhattan, and no broker fees.
            </p>
            
            <div className="flex flex-wrap justify-center gap-8 mb-10">
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">{stats.count || '15'}+</p>
                <p className="text-blue-200 text-sm">No-Fee Listings</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">10 min</p>
                <p className="text-blue-200 text-sm">PATH to WTC</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">$0</p>
                <p className="text-blue-200 text-sm">Broker Fees</p>
              </div>
            </div>
            
            <Button 
              onClick={() => navigate('/auth')} 
              size="lg"
              className="bg-amber-500 hover:bg-amber-600 text-white px-8 py-6 text-lg"
            >
              View Hoboken Apartments <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        </section>

        {/* Why Hoboken Section */}
        <section className="py-16 px-6 bg-gray-50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-4">Why Choose Hoboken?</h2>
            <p className="text-gray-600 text-center mb-10 max-w-2xl mx-auto">
              The perfect blend of NYC access and suburban charm—with tax savings
            </p>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white p-8 rounded-xl shadow-sm">
                <h3 className="text-xl font-bold mb-4 text-gray-900">Top 5 Reasons for Hoboken</h3>
                <ul className="space-y-3">
                  {topReasons.map((reason, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="bg-white p-8 rounded-xl shadow-sm">
                <h3 className="text-xl font-bold mb-4 text-gray-900">PATH Train to Manhattan</h3>
                <div className="space-y-4">
                  {[
                    { from: 'Hoboken', to: 'World Trade Center', time: '10 min' },
                    { from: 'Hoboken', to: '33rd St (Midtown)', time: '15-20 min' },
                    { from: 'Hoboken', to: 'Christopher St', time: '8 min' },
                    { from: 'Hoboken Ferry', to: 'Pier 11 (FiDi)', time: '5 min' }
                  ].map((route, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100">
                      <div className="flex items-center gap-2">
                        <Train className="w-4 h-4 text-blue-600" />
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

        {/* Nearby Areas Grid */}
        <section className="py-16 px-6">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-4">Hoboken & Nearby Areas</h2>
            <p className="text-gray-600 text-center mb-10">Explore the Hudson County waterfront</p>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {hobokenAreas.map((area, i) => (
                <Link
                  key={i}
                  to={`/apartments/${area.slug}`}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:border-amber-400 hover:shadow-md transition-all group"
                >
                  <h3 className="font-semibold text-gray-900 group-hover:text-amber-600">{area.name}</h3>
                  <p className="text-gray-500 text-sm mt-1">{area.description}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Featured Listings */}
        {units.length > 0 && (
          <section className="py-16 px-6 bg-gray-50">
            <div className="max-w-5xl mx-auto">
              <h2 className="text-3xl font-bold text-center mb-10">Featured Hoboken Apartments</h2>
              
              <div className="grid md:grid-cols-3 gap-6">
                {units.map((unit) => (
                  <div key={unit.id} className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow">
                    <div className="relative h-48">
                      <img 
                        src={unit.images?.[0] || unit.building?.images?.[0] || '/placeholder-apt.jpg'} 
                        alt={`${unit.building?.name || 'Apartment'}`}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute top-3 left-3 bg-blue-600 text-white text-xs font-bold px-2 py-1 rounded">
                        NO FEE
                      </div>
                    </div>
                    <div className="p-4">
                      <p className="text-2xl font-bold text-gray-900">{formatRent(unit.rent)}<span className="text-sm font-normal text-gray-500">/mo</span></p>
                      <p className="text-gray-600 mt-1">{unit.building?.name || 'Hoboken Apartment'}</p>
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
                  View All Hoboken Apartments <ArrowRight className="ml-2 w-4 h-4" />
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
        <section className="py-16 px-6 bg-blue-900 text-white">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Find Your Hoboken Apartment?</h2>
            <p className="text-blue-200 mb-8">
              Manhattan views, NJ taxes, zero broker fees. The best of both worlds.
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

export default HobokenPage;
