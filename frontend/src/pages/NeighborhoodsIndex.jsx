import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { MapPin, Building2, DollarSign, Home, ArrowRight } from 'lucide-react';
import { API } from '../config/api';

const NeighborhoodsIndex = () => {
  const [neighborhoods, setNeighborhoods] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/neighborhoods`)
      .then(res => res.json())
      .then(data => {
        setNeighborhoods(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching neighborhoods:', err);
        setLoading(false);
      });
  }, []);

  // Group by state/region
  const nycNeighborhoods = neighborhoods.filter(n => n.state === 'NY');
  const njNeighborhoods = neighborhoods.filter(n => n.state === 'NJ');
  const paNeighborhoods = neighborhoods.filter(n => n.state === 'PA');

  const NeighborhoodCard = ({ neighborhood }) => (
    <Link 
      to={`/apartments/${neighborhood.slug}`}
      className="group bg-white border border-gray-200 rounded-lg p-5 hover:border-amber-400 hover:shadow-lg transition-all"
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-bold text-gray-900 group-hover:text-amber-600 transition-colors">
            {neighborhood.name}
          </h3>
          <p className="text-sm text-gray-500">{neighborhood.city}, {neighborhood.state}</p>
        </div>
        <span className="bg-amber-100 text-amber-700 text-xs font-bold px-2 py-1 rounded">
          {neighborhood.count} {neighborhood.count === 1 ? 'unit' : 'units'}
        </span>
      </div>
      
      <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
        <span className="flex items-center gap-1">
          <DollarSign className="w-4 h-4 text-amber-500" />
          ${neighborhood.min_rent.toLocaleString()} - ${neighborhood.max_rent.toLocaleString()}
        </span>
      </div>
      
      <div className="flex gap-2 text-xs text-gray-500">
        {neighborhood.studios > 0 && <span className="bg-gray-100 px-2 py-1 rounded">{neighborhood.studios} Studios</span>}
        {neighborhood.one_beds > 0 && <span className="bg-gray-100 px-2 py-1 rounded">{neighborhood.one_beds} 1-Beds</span>}
        {neighborhood.two_plus_beds > 0 && <span className="bg-gray-100 px-2 py-1 rounded">{neighborhood.two_plus_beds} 2+ Beds</span>}
      </div>
      
      <div className="mt-4 flex items-center text-amber-600 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
        View apartments <ArrowRight className="w-4 h-4 ml-1" />
      </div>
    </Link>
  );

  const RegionSection = ({ title, neighborhoods, icon }) => (
    neighborhoods.length > 0 && (
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          {icon}
          {title}
          <span className="text-sm font-normal text-gray-500 ml-2">
            ({neighborhoods.reduce((sum, n) => sum + n.count, 0)} apartments)
          </span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {neighborhoods.map(n => (
            <NeighborhoodCard key={n.slug} neighborhood={n} />
          ))}
        </div>
      </div>
    )
  );

  const totalUnits = neighborhoods.reduce((sum, n) => sum + n.count, 0);
  const pageTitle = `No Fee Apartments by Neighborhood | NYC, NJ & PA`;
  const pageDescription = `Browse ${totalUnits}+ no fee apartments across ${neighborhoods.length} neighborhoods in NYC, New Jersey, and Pennsylvania. Find broker-free rentals in Manhattan, Brooklyn, Queens, and more.`;
  const socialImage = 'https://static.prod-images.emergentagent.com/jobs/47dd6b46-e381-45f3-b7a5-c4e5965d2ca7/images/7cc4822cb8a1477005344990d5785c45f97816fa18a46f0e57cadfe289bec671.png';

  return (
    <>
      <Helmet>
        <title>{pageTitle} | NoFeesApts</title>
        <meta name="description" content={pageDescription} />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://nofeesapts.com/apartments" />
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={`${totalUnits}+ no fee apartments across ${neighborhoods.length} neighborhoods. Zero broker fees.`} />
        <meta property="og:image" content={socialImage} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:site_name" content="NoFeesApts" />
        <meta property="og:locale" content="en_US" />
        
        {/* Twitter Card */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:url" content="https://nofeesapts.com/apartments" />
        <meta name="twitter:title" content={pageTitle} />
        <meta name="twitter:description" content={`${totalUnits}+ no fee apartments across ${neighborhoods.length} neighborhoods. Zero broker fees.`} />
        <meta name="twitter:image" content={socialImage} />
        
        {/* Additional SEO */}
        <meta name="robots" content="index, follow" />
        <meta name="author" content="NoFeesApts" />
        <link rel="canonical" href="https://nofeesapts.com/apartments" />
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <Link to="/" className="text-2xl font-philosopher font-bold text-gray-900">
              NoFeesApts
            </Link>
            <Link 
              to="/auth" 
              className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded font-medium text-sm transition-colors"
            >
              Sign Up Free
            </Link>
          </div>
        </header>

        {/* Hero */}
        <div className="bg-gradient-to-b from-amber-50 to-white py-12">
          <div className="max-w-7xl mx-auto px-4">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              No Fee Apartments by Neighborhood
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl">
              Explore <span className="text-amber-600 font-semibold">{totalUnits}+</span> broker-free apartments across <span className="text-amber-600 font-semibold">{neighborhoods.length}</span> neighborhoods in NYC, New Jersey, and Pennsylvania.
            </p>
          </div>
        </div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-12">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <>
              <RegionSection 
                title="New York City" 
                neighborhoods={nycNeighborhoods}
                icon={<Building2 className="w-6 h-6 text-amber-500" />}
              />
              
              <RegionSection 
                title="New Jersey" 
                neighborhoods={njNeighborhoods}
                icon={<MapPin className="w-6 h-6 text-amber-500" />}
              />
              
              <RegionSection 
                title="Pennsylvania" 
                neighborhoods={paNeighborhoods}
                icon={<Home className="w-6 h-6 text-amber-500" />}
              />
            </>
          )}
        </main>

        {/* CTA */}
        <div className="bg-gray-900 py-16">
          <div className="max-w-3xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to find your no-fee apartment?
            </h2>
            <p className="text-gray-400 mb-8">
              Sign up for free to see full addresses, save favorites, and get alerts for new listings.
            </p>
            <Link 
              to="/auth"
              className="inline-block bg-amber-500 hover:bg-amber-600 text-white px-8 py-4 rounded font-bold text-lg transition-colors"
            >
              Sign Up Free — No Credit Card Required
            </Link>
          </div>
        </div>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 py-8">
          <div className="max-w-7xl mx-auto px-4 text-center text-gray-500 text-sm">
            © 2025 NoFeesApts.com — No Fee Apartments in NYC, NJ & PA
          </div>
        </footer>
      </div>
    </>
  );
};

export default NeighborhoodsIndex;
