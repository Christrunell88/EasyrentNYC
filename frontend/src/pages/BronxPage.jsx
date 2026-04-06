import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, BedDouble, Bath, Heart, ArrowRight, Check, Star, Train } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Footer from '@/components/Footer';
import axios from '../utils/axiosConfig';
import { API } from '../App';

// Bronx neighborhoods data
const bronxNeighborhoods = [
  { slug: 'riverdale', name: 'Riverdale', description: 'Leafy streets with Hudson River views' },
  { slug: 'fordham', name: 'Fordham', description: 'Near Fordham University with great transit' },
  { slug: 'pelham-bay', name: 'Pelham Bay', description: 'Close to NYC\'s largest park' },
  { slug: 'kingsbridge', name: 'Kingsbridge', description: 'Affordable family neighborhood' },
  { slug: 'mott-haven', name: 'Mott Haven', description: 'Up-and-coming arts district' },
  { slug: 'throgs-neck', name: 'Throgs Neck', description: 'Waterfront community feel' },
  { slug: 'morris-park', name: 'Morris Park', description: 'Quiet residential streets' },
  { slug: 'city-island', name: 'City Island', description: 'Charming fishing village vibe' }
];

// FAQ data for SEO
const faqs = [
  {
    q: "What is the average rent for a no-fee apartment in the Bronx?",
    a: "No-fee apartment rents in the Bronx typically range from $1,500 for studios to $2,800 for 2-bedrooms—significantly lower than Manhattan or Brooklyn. By avoiding broker fees, you save an additional $2,000-$4,000."
  },
  {
    q: "Which Bronx neighborhoods have the most no-fee apartments?",
    a: "Riverdale, Mott Haven, and Fordham have the most no-fee apartment options due to newer developments and larger management companies. These areas offer modern amenities at more affordable prices."
  },
  {
    q: "Is the Bronx a good place to live?",
    a: "Absolutely! The Bronx offers the best value in NYC with lower rents, diverse communities, excellent parks (including the Bronx Zoo and Botanical Garden), and improving transit connections. Neighborhoods like Riverdale are among the most desirable in NYC."
  },
  {
    q: "How long is the commute from the Bronx to Manhattan?",
    a: "Commute times vary by neighborhood: Mott Haven to Midtown is about 25 minutes, Fordham to Grand Central is 30 minutes, and Riverdale to Times Square is around 40 minutes via Metro-North or subway."
  },
  {
    q: "Are Bronx apartments safe?",
    a: "Many Bronx neighborhoods like Riverdale, Pelham Bay, and City Island are very safe and family-friendly. Crime has decreased significantly across the borough. Research specific neighborhoods and visit in person before signing a lease."
  }
];

// Top reasons listicle
const topReasons = [
  "Save 30-50% compared to Manhattan rents",
  "Avoid $2,000-$4,000 in broker fees",
  "Access to NYC's best parks and green spaces",
  "Strong community feel and cultural diversity",
  "Improving transit and new developments"
];

const BronxPage = () => {
  const navigate = useNavigate();
  const [units, setUnits] = useState([]);
  const [stats, setStats] = useState({ count: 0, avgRent: 0, minRent: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBronxUnits();
  }, []);

  const fetchBronxUnits = async () => {
    try {
      const response = await axios.get(`${API}/units?limit=100`);
      const allUnits = response.data || [];
      
      const bronxNeighborhoodNames = ['Riverdale', 'Fordham', 'Pelham Bay', 'Kingsbridge', 
        'Mott Haven', 'Throgs Neck', 'Morris Park', 'City Island', 'Bronx'];
      
      const bronxUnits = allUnits.filter(u => {
        const building = u.building || {};
        const city = (building.city || '').toLowerCase();
        const neighborhood = building.neighborhood || '';
        const state = building.state || '';
        
        return (
          city.includes('bronx') ||
          state === 'NY' && bronxNeighborhoodNames.some(n => 
            neighborhood.toLowerCase().includes(n.toLowerCase())
          )
        );
      });
      
      setUnits(bronxUnits.slice(0, 6));
      
      if (bronxUnits.length > 0) {
        const rents = bronxUnits.map(u => u.rent).filter(r => r > 0);
        setStats({
          count: bronxUnits.length,
          avgRent: rents.length > 0 ? Math.round(rents.reduce((a, b) => a + b, 0) / rents.length) : 0,
          minRent: rents.length > 0 ? Math.min(...rents) : 0
        });
      }
    } catch (error) {
      console.error('Error fetching Bronx units:', error);
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
        <title>No Fee Apartments in the Bronx | Best Deals NYC | NoFeesApts.com</title>
        <meta name="description" content={`Find ${stats.count || 'verified'} no-fee apartments in the Bronx. Save $2,000-$4,000 on broker fees. Affordable rents from ${stats.minRent ? formatRent(stats.minRent) : '$1,500'}/month. Browse Riverdale, Mott Haven, Fordham & more.`} />
        <meta name="keywords" content="no fee apartments bronx, bronx apartments no broker fee, riverdale apartments, mott haven apartments, fordham apartments, affordable bronx rentals, no fee rentals bronx ny" />
        <link rel="canonical" href="https://nofeesapts.com/bronx" />
        
        <meta property="og:title" content="No Fee Apartments in the Bronx - Save Thousands | NoFeesApts.com" />
        <meta property="og:description" content={`Browse ${stats.count || 'verified'} no-fee apartments in the Bronx. The most affordable borough with rents from ${stats.minRent ? formatRent(stats.minRent) : '$1,500'}/month.`} />
        <meta property="og:url" content="https://nofeesapts.com/bronx" />
        <meta property="og:type" content="website" />
        
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "No Fee Apartments in the Bronx",
            "description": "Browse verified no-fee apartments in the Bronx, NYC",
            "url": "https://nofeesapts.com/bronx",
            "isPartOf": { "@type": "WebSite", "name": "NoFeesApts.com", "url": "https://nofeesapts.com" },
            "about": { "@type": "Place", "name": "Bronx", "address": { "@type": "PostalAddress", "addressLocality": "Bronx", "addressRegion": "NY" }}
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
              <Link to="/apartments" className="text-gray-600 hover:text-amber-600 text-sm">All Neighborhoods</Link>
              <Button onClick={() => navigate('/auth')} className="bg-amber-500 hover:bg-amber-600 text-white">
                Browse Free
              </Button>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="bg-gradient-to-br from-green-900 via-green-800 to-emerald-900 text-white py-20 px-6">
          <div className="max-w-5xl mx-auto text-center">
            <p className="text-green-300 text-sm tracking-widest uppercase mb-4">The Bronx, NY</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              No Fee Apartments in the <span className="text-amber-400">Bronx</span>
            </h1>
            <p className="text-xl text-green-100 mb-8 max-w-2xl mx-auto">
              NYC's most affordable borough with incredible value. Save thousands on broker fees.
            </p>
            
            <div className="flex flex-wrap justify-center gap-8 mb-10">
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">{stats.count || '10'}+</p>
                <p className="text-green-200 text-sm">No-Fee Listings</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">{stats.avgRent ? formatRent(stats.avgRent) : '$2,100'}</p>
                <p className="text-green-200 text-sm">Average Rent</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-400">$0</p>
                <p className="text-green-200 text-sm">Broker Fees</p>
              </div>
            </div>
            
            <Button 
              onClick={() => navigate('/auth')} 
              size="lg"
              className="bg-amber-500 hover:bg-amber-600 text-white px-8 py-6 text-lg"
            >
              View Bronx Apartments <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </div>
        </section>

        {/* Why Bronx Section */}
        <section className="py-16 px-6 bg-gray-50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-4">Why Choose the Bronx?</h2>
            <p className="text-gray-600 text-center mb-10 max-w-2xl mx-auto">
              The best value in NYC with lower rents, beautiful parks, and strong communities
            </p>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white p-8 rounded-xl shadow-sm">
                <h3 className="text-xl font-bold mb-4 text-gray-900">Top 5 Reasons for No-Fee Bronx Apartments</h3>
                <ul className="space-y-3">
                  {topReasons.map((reason, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="bg-white p-8 rounded-xl shadow-sm">
                <h3 className="text-xl font-bold mb-4 text-gray-900">Commute Times to Manhattan</h3>
                <div className="space-y-4">
                  {[
                    { from: 'Mott Haven', to: 'Midtown', time: '25 min' },
                    { from: 'Fordham', to: 'Grand Central', time: '30 min' },
                    { from: 'Pelham Bay', to: 'Union Square', time: '35 min' },
                    { from: 'Riverdale', to: 'Times Square', time: '40 min' }
                  ].map((route, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100">
                      <div className="flex items-center gap-2">
                        <Train className="w-4 h-4 text-green-600" />
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
            <h2 className="text-3xl font-bold text-center mb-4">Bronx Neighborhoods</h2>
            <p className="text-gray-600 text-center mb-10">Explore no-fee apartments across the Bronx</p>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {bronxNeighborhoods.map((hood) => (
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
              <h2 className="text-3xl font-bold text-center mb-10">Featured Bronx Apartments</h2>
              
              <div className="grid md:grid-cols-3 gap-6">
                {units.map((unit) => (
                  <div key={unit.id} className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow">
                    <div className="relative h-48">
                      <img 
                        src={unit.images?.[0] || unit.building?.images?.[0] || '/placeholder-apt.jpg'} 
                        alt={`${unit.building?.name || 'Apartment'}`}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute top-3 left-3 bg-green-600 text-white text-xs font-bold px-2 py-1 rounded">
                        NO FEE
                      </div>
                    </div>
                    <div className="p-4">
                      <p className="text-2xl font-bold text-gray-900">{formatRent(unit.rent)}<span className="text-sm font-normal text-gray-500">/mo</span></p>
                      <p className="text-gray-600 mt-1">{unit.building?.name || 'Bronx Apartment'}</p>
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
                  View All Bronx Apartments <ArrowRight className="ml-2 w-4 h-4" />
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
        <section className="py-16 px-6 bg-green-900 text-white">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Find Your Bronx Apartment?</h2>
            <p className="text-green-200 mb-8">
              Browse {stats.count || 'verified'} no-fee listings. Save thousands on broker fees.
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

export default BronxPage;
