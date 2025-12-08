import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Building2, MapPin, DollarSign, TrendingUp, ArrowRight, Home } from 'lucide-react';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import SEO from '../components/SEO';

const LocationPage = () => {
  const { location } = useParams();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ totalUnits: 0, avgRent: 0, buildings: [] });

  const locationData = {
    manhattan: {
      name: 'Manhattan',
      title: 'No Fee Apartments in Manhattan, NYC',
      description: 'Find your perfect Manhattan apartment with zero broker fees. Browse verified no-fee apartments in Upper West Side, Upper East Side, Midtown, and Downtown Manhattan.',
      neighborhoods: ['Upper West Side', 'Upper East Side', 'Midtown', 'Downtown', 'Financial District', 'Tribeca'],
      highlights: [
        'Heart of NYC with iconic landmarks',
        'Excellent public transportation (all subway lines)',
        'World-class dining and entertainment',
        'Central Park and waterfront access'
      ],
      avgRent: '$3,200 - $4,500',
      seoKeywords: 'no fee apartments manhattan, manhattan apartments no broker fee, upper west side apartments, upper east side rentals'
    },
    brooklyn: {
      name: 'Brooklyn',
      title: 'No Fee Apartments in Brooklyn, NYC',
      description: 'Discover Brooklyn\'s best no-fee apartments. From trendy Williamsburg to family-friendly Park Slope, find your Brooklyn home without paying broker fees.',
      neighborhoods: ['Williamsburg', 'Downtown Brooklyn', 'Park Slope', 'DUMBO', 'Brooklyn Heights', 'Greenpoint'],
      highlights: [
        'Vibrant arts and culture scene',
        'Diverse neighborhoods with unique character',
        'Excellent restaurants and nightlife',
        'Waterfront parks and Brooklyn Bridge Park'
      ],
      avgRent: '$2,400 - $3,800',
      seoKeywords: 'no fee apartments brooklyn, brooklyn apartments no broker fee, williamsburg apartments, dumbo rentals'
    },
    queens: {
      name: 'Queens',
      title: 'No Fee Apartments in Queens, NYC',
      description: 'Queens offers the best value in NYC. Browse no-fee apartments in Long Island City, Astoria, and Forest Hills. More space, lower rent, no broker fees.',
      neighborhoods: ['Long Island City', 'Astoria', 'Forest Hills', 'Flushing', 'Jackson Heights', 'Sunnyside'],
      highlights: [
        'Most affordable borough with great value',
        'Direct access to Manhattan (7, N, W, E trains)',
        'Diverse international food scene',
        'Family-friendly with excellent schools'
      ],
      avgRent: '$1,800 - $3,200',
      seoKeywords: 'no fee apartments queens, queens apartments no broker fee, long island city apartments, astoria rentals'
    },
    'long-island-city': {
      name: 'Long Island City',
      title: 'No Fee Apartments in Long Island City, Queens',
      description: 'Discover Long Island City\'s newest no-fee apartments. Minutes from Manhattan with modern amenities and stunning skyline views. No broker fees.',
      neighborhoods: ['Hunters Point', 'Court Square', 'Dutch Kills', 'Astoria Heights'],
      highlights: [
        'One stop to Manhattan (7, E, M, G trains)',
        'Modern high-rise buildings with amenities',
        'Waterfront parks and East River views',
        'Rapidly growing arts and dining scene'
      ],
      avgRent: '$2,200 - $3,600',
      seoKeywords: 'no fee apartments long island city, lic apartments no broker fee, hunters point apartments'
    },
    williamsburg: {
      name: 'Williamsburg',
      title: 'No Fee Apartments in Williamsburg, Brooklyn',
      description: 'Find trendy Williamsburg apartments with no broker fees. Brooklyn\'s hottest neighborhood for young professionals and creatives. Zero fees guaranteed.',
      neighborhoods: ['North Williamsburg', 'South Williamsburg', 'East Williamsburg', 'Northside'],
      highlights: [
        'Hip neighborhood with vibrant nightlife',
        'L train to Manhattan in 10 minutes',
        'Trendy restaurants, bars, and music venues',
        'Waterfront parks and Brooklyn Brewery'
      ],
      avgRent: '$2,600 - $4,200',
      seoKeywords: 'no fee apartments williamsburg, williamsburg brooklyn apartments no broker fee, north williamsburg rentals'
    },
    'jersey-city': {
      name: 'Jersey City',
      title: 'No Fee Apartments in Jersey City, NJ',
      description: 'Jersey City offers affordable NYC-area living with no broker fees. Quick PATH train access to Manhattan. Modern apartments at lower prices.',
      neighborhoods: ['Downtown Jersey City', 'Newport', 'Journal Square', 'Paulus Hook', 'Hamilton Park'],
      highlights: [
        '10-20 minute PATH train to Manhattan',
        'Stunning NYC skyline views',
        'Lower taxes and cost of living',
        'Family-friendly with great schools'
      ],
      avgRent: '$2,000 - $3,400',
      seoKeywords: 'no fee apartments jersey city, jersey city apartments no broker fee, downtown jersey city rentals'
    },
    hoboken: {
      name: 'Hoboken',
      title: 'No Fee Apartments in Hoboken, NJ',
      description: 'Charming Hoboken apartments with no broker fees. Easy NYC commute via PATH train. Vibrant downtown area with restaurants and nightlife.',
      neighborhoods: ['Downtown Hoboken', 'Uptown Hoboken', 'Waterfront', 'Castle Point'],
      highlights: [
        '15-minute PATH train to Manhattan',
        'Walkable downtown with restaurants and bars',
        'Beautiful waterfront parks with NYC views',
        'Safe, family-friendly community'
      ],
      avgRent: '$2,200 - $3,600',
      seoKeywords: 'no fee apartments hoboken, hoboken apartments no broker fee, hoboken nj rentals'
    },
    harrison: {
      name: 'Harrison',
      title: 'No Fee Apartments in Harrison, NJ',
      description: 'Just minutes from Manhattan, Harrison NJ offers modern apartments with no broker fees. Perfect for NYC commuters seeking more space and lower rent.',
      neighborhoods: ['Downtown Harrison', 'Harrison Waterfront', 'PATH Station Area'],
      highlights: [
        '15-minute PATH train to Manhattan',
        'Modern luxury buildings with amenities',
        'Lower cost of living than NYC',
        'Red Bull Arena and waterfront parks'
      ],
      avgRent: '$2,200 - $3,500',
      seoKeywords: 'no fee apartments harrison nj, harrison new jersey apartments no broker fee'
    },
    weehawken: {
      name: 'Weehawken',
      title: 'No Fee Apartments in Weehawken, NJ',
      description: 'Weehawken offers stunning NYC views and no-fee apartments. Quick NYC Ferry or bus commute to Manhattan. Premium living without broker fees.',
      neighborhoods: ['Waterfront', 'The Heights', 'Lincoln Harbor', 'Boulevard East'],
      highlights: [
        'Spectacular NYC skyline views',
        'NYC Ferry and express bus service',
        'Quiet, residential atmosphere',
        'Premium amenities and modern buildings'
      ],
      avgRent: '$2,400 - $3,800',
      seoKeywords: 'no fee apartments weehawken, weehawken nj apartments no broker fee, weehawken waterfront rentals'
    },
    bronx: {
      name: 'Bronx',
      title: 'No Fee Apartments in The Bronx, NYC',
      description: 'Find affordable Bronx apartments with no broker fees. Great value with easy access to Manhattan. Family-friendly neighborhoods with parks and culture.',
      neighborhoods: ['Riverdale', 'Concourse', 'Fordham', 'Pelham Bay', 'Mott Haven', 'South Bronx'],
      highlights: [
        'Most affordable NYC borough',
        'Direct subway access to Manhattan',
        'Home to Yankee Stadium and Bronx Zoo',
        'Growing arts scene and waterfront parks'
      ],
      avgRent: '$1,600 - $2,800',
      seoKeywords: 'no fee apartments bronx, bronx apartments no broker fee, south bronx rentals'
    }
  };

  const currentLocation = locationData[location] || locationData.manhattan;

  const fetchLocationStats = React.useCallback(async () => {
    try {
      const response = await axios.get(`${API}/units?city=${currentLocation.name}`, { withCredentials: true });
      const units = response.data;
      setStats({
        totalUnits: units.length,
        avgRent: units.length > 0 ? Math.round(units.reduce((sum, u) => sum + u.rent, 0) / units.length) : 0,
        buildings: [...new Set(units.map(u => u.building?.name))].filter(Boolean)
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, [currentLocation.name]);

  useEffect(() => {
    fetchLocationStats();
  }, [location, fetchLocationStats]);

  return (
    <div className="min-h-screen bg-slate-900">
      <SEO
        title={currentLocation.title}
        description={currentLocation.description}
        keywords={currentLocation.seoKeywords}
        ogType="website"
        schema={{
          "@context": "https://schema.org",
          "@type": "RealEstateAgent",
          "name": "NoFeesApts.com",
          "description": currentLocation.description,
          "url": `https://nofeesapts.com/location/${location}`,
          "areaServed": {
            "@type": "City",
            "name": currentLocation.name
          },
          "priceRange": currentLocation.avgRent,
          "availableLanguage": ["en"],
          "makesOffer": {
            "@type": "Offer",
            "itemOffered": {
              "@type": "Apartment",
              "name": `No Fee Apartments in ${currentLocation.name}`
            },
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock"
          }
        }}
      />
      
      {/* Header */}
      <header className="glass-window border-b border-amber-500/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg warm-gradient flex items-center justify-center shadow-lg shadow-amber-500/20">
              <Building2 className="w-6 h-6 text-slate-900" />
            </div>
            <span className="text-xl font-semibold warm-gradient-text cursor-pointer" onClick={() => navigate('/')}>NoFeesApts.com</span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/30 rounded-full mb-6">
            <MapPin className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-semibold text-amber-400">{currentLocation.name}</span>
          </div>
          
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
            {currentLocation.title}
          </h1>
          
          <p className="text-xl text-slate-300 mb-8 max-w-3xl mx-auto">
            {currentLocation.description}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button
              onClick={() => navigate('/dashboard?city=' + currentLocation.name)}
              size="lg"
              className="warm-gradient hover:shadow-xl hover:shadow-amber-500/40 text-slate-900 font-bold px-10 py-6 text-lg"
            >
              View {stats.totalUnits} Apartments
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button
              onClick={() => navigate('/auth')}
              variant="outline"
              size="lg"
              className="border-amber-500/30 text-amber-500 hover:bg-slate-700 px-10 py-6 text-lg font-semibold"
            >
              Sign Up Free
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <Card className="bg-slate-800/50 border-amber-500/20">
              <CardContent className="p-6 text-center">
                <Home className="w-8 h-8 text-amber-500 mx-auto mb-2" />
                <p className="text-3xl font-bold warm-gradient-text">{stats.totalUnits}</p>
                <p className="text-sm text-slate-400">Apartments</p>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-amber-500/20">
              <CardContent className="p-6 text-center">
                <DollarSign className="w-8 h-8 text-amber-500 mx-auto mb-2" />
                <p className="text-3xl font-bold warm-gradient-text">${stats.avgRent}</p>
                <p className="text-sm text-slate-400">Avg Rent</p>
              </CardContent>
            </Card>
            <Card className="bg-slate-800/50 border-amber-500/20 col-span-2 md:col-span-1">
              <CardContent className="p-6 text-center">
                <Building2 className="w-8 h-8 text-amber-500 mx-auto mb-2" />
                <p className="text-3xl font-bold warm-gradient-text">{stats.buildings.length}</p>
                <p className="text-sm text-slate-400">Buildings</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Popular Neighborhoods */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">Popular Neighborhoods</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {currentLocation.neighborhoods.map((hood, idx) => (
              <Card key={idx} className="bg-slate-700/50 border-amber-500/20 hover:border-amber-500/40 transition-all cursor-pointer">
                <CardContent className="p-6">
                  <MapPin className="w-6 h-6 text-amber-500 mb-3" />
                  <h3 className="text-lg font-semibold text-slate-100 mb-2">{hood}</h3>
                  <Button
                    variant="ghost"
                    className="text-amber-500 hover:text-amber-400 p-0"
                    onClick={() => navigate(`/dashboard?neighborhood=${hood}`)}
                  >
                    View Apartments →
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-white mb-8 text-center">Why Live in {currentLocation.name}?</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {currentLocation.highlights.map((highlight, idx) => (
              <div key={idx} className="flex gap-4 items-start">
                <div className="w-10 h-10 rounded-lg warm-gradient flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-5 h-5 text-slate-900" />
                </div>
                <div>
                  <p className="text-slate-200 text-lg">{highlight}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <p className="text-xl text-slate-300 mb-6">
              Average Rent Range: <span className="warm-gradient-text font-bold">{currentLocation.avgRent}</span>
            </p>
            <Button
              onClick={() => navigate('/dashboard?city=' + currentLocation.name)}
              size="lg"
              className="warm-gradient hover:shadow-xl text-slate-900 font-bold"
            >
              Browse All {currentLocation.name} Apartments
            </Button>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-amber-600 via-orange-500 to-amber-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">Ready to Find Your {currentLocation.name} Apartment?</h2>
          <p className="text-lg text-slate-800 mb-8">Sign up free. Browse apartments. Save thousands on broker fees.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => navigate('/auth')}
              size="lg"
              className="bg-slate-900 hover:bg-slate-800 text-amber-500 font-bold px-10 py-6"
            >
              Sign Up Free
            </Button>
            <Button
              onClick={() => navigate('/dashboard')}
              size="lg"
              variant="outline"
              className="border-2 border-slate-900 text-slate-900 hover:bg-slate-900 hover:text-amber-500 font-bold px-10 py-6"
            >
              View All Apartments
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default LocationPage;
