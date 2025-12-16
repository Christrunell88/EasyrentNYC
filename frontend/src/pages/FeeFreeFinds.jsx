import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Sparkles, 
  ArrowRight, 
  Heart, 
  Building2, 
  DollarSign, 
  TrendingUp,
  CheckCircle,
  Copy,
  Hash,
  MapPin
} from 'lucide-react';
import { toast } from 'sonner';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import ListingCard from '../components/ListingCard';
import Logo from '@/components/Logo';
import SEO from '@/components/SEO';
import useAuthStore from '../store/authStore';

const FeeFreeFinds = () => {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState(new Set());
  const [stats, setStats] = useState({ totalUnits: 0, totalSavings: 0 });

  useEffect(() => {
    fetchFeeFreeFinds();
    if (user) {
      fetchFavorites();
    }
  }, [user]);

  const fetchFeeFreeFinds = async () => {
    try {
      // Fetch all units - they're all no-fee
      const response = await axios.get(`${API}/units?limit=50`);
      const allUnits = response.data;
      
      // Calculate total potential savings (avg broker fee is 15% of annual rent, or ~1.8 months rent)
      const totalSavings = allUnits.reduce((sum, unit) => sum + Math.round(unit.rent * 1.8), 0);
      
      setUnits(allUnits);
      setStats({
        totalUnits: allUnits.length,
        totalSavings: totalSavings
      });
    } catch (error) {
      console.error('Error fetching units:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchFavorites = async () => {
    try {
      const response = await axios.get(`${API}/favorites`, { withCredentials: true });
      const favIds = new Set(response.data.map(f => f.unit.id));
      setFavorites(favIds);
    } catch (error) {
      console.error('Error fetching favorites:', error);
    }
  };

  const toggleFavorite = async (unitId) => {
    if (!user) {
      navigate('/auth');
      return;
    }
    
    try {
      if (favorites.has(unitId)) {
        await axios.delete(`${API}/favorites/${unitId}`, { withCredentials: true });
        setFavorites(prev => {
          const newSet = new Set(prev);
          newSet.delete(unitId);
          return newSet;
        });
      } else {
        await axios.post(`${API}/favorites/${unitId}`, {}, { withCredentials: true });
        setFavorites(prev => new Set(prev).add(unitId));
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-slate-900 overflow-hidden">
      <SEO
        title="#FeeFreeFinds - No Broker Fee Apartments NYC & NJ"
        description="Discover #FeeFreeFinds - curated no broker fee apartments in NYC and New Jersey. Save thousands on your next apartment. Real listings, real savings, zero fees."
        keywords="FeeFreeFinds, no fee apartments NYC, no broker fee apartments, NYC apartments, New Jersey apartments, free apartment listings, save on broker fees"
        url="/fee-free-finds"
        structuredData={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          "name": "#FeeFreeFinds - No Broker Fee Apartments",
          "description": "Curated collection of no broker fee apartments in NYC and New Jersey",
          "url": "https://nofeesapts.com/fee-free-finds",
          "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": stats.totalUnits,
            "itemListElement": units.slice(0, 10).map((unit, index) => ({
              "@type": "ListItem",
              "position": index + 1,
              "item": {
                "@type": "Apartment",
                "name": `${unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`} at ${unit.building?.name}`,
                "offers": {
                  "@type": "Offer",
                  "price": unit.rent,
                  "priceCurrency": "USD"
                }
              }
            }))
          }
        }}
      />

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-window border-b border-amber-500/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Logo size="default" />
            
            <div className="flex items-center gap-4">
              {user ? (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/favorites')}
                    className="text-slate-300 hover:text-amber-500 hover:bg-slate-800/50"
                  >
                    <Heart className="w-5 h-5 mr-2" />
                    Favorites
                  </Button>
                  <Button
                    onClick={() => navigate('/dashboard')}
                    className="warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold px-6"
                  >
                    Browse All
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/auth')}
                    className="text-slate-300 hover:text-amber-500 hover:bg-slate-800/50"
                  >
                    Sign In
                  </Button>
                  <Button
                    onClick={() => navigate('/auth')}
                    className="warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold px-6"
                  >
                    Get Started
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8 overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-amber-600/20 via-slate-900 to-emerald-600/10" />
        
        {/* Animated hashtag symbols */}
        <div className="absolute inset-0 overflow-hidden opacity-10">
          {[...Array(12)].map((_, i) => (
            <Hash
              key={i}
              className="absolute text-amber-500 animate-pulse"
              style={{
                width: Math.random() * 60 + 30 + 'px',
                height: Math.random() * 60 + 30 + 'px',
                left: Math.random() * 100 + '%',
                top: Math.random() * 100 + '%',
                animationDelay: Math.random() * 3 + 's',
                opacity: Math.random() * 0.5 + 0.2
              }}
            />
          ))}
        </div>

        <div className="max-w-5xl mx-auto relative z-10 text-center">
          {/* Brand Badge */}
          <div className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-500/20 to-emerald-500/20 border border-amber-500/40 rounded-full mb-8 shadow-lg shadow-amber-500/10">
            <Sparkles className="w-5 h-5 text-amber-400 animate-pulse" />
            <span className="text-lg font-bold text-amber-400">#FeeFreeFinds</span>
            <Sparkles className="w-5 h-5 text-amber-400 animate-pulse" />
          </div>
          
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
            <span className="block text-white">Your Next Home,</span>
            <span className="block warm-gradient-text" style={{textShadow: '0 4px 30px rgba(245,158,11,0.4)'}}>
              Zero Fees
            </span>
          </h1>
          
          <p className="text-xl sm:text-2xl text-slate-300 mb-10 max-w-3xl mx-auto leading-relaxed">
            Every apartment in our collection is a <span className="text-amber-400 font-semibold">#FeeFreeFind</span> — 
            verified no-fee listings that save you thousands on broker costs.
          </p>

          {/* Stats Row */}
          <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-12">
            <div className="glass-window border border-amber-500/30 rounded-xl px-8 py-4 text-center">
              <div className="text-3xl font-bold warm-gradient-text">{stats.totalUnits}+</div>
              <div className="text-sm text-slate-400">No-Fee Apartments</div>
            </div>
            <div className="glass-window border border-emerald-500/30 rounded-xl px-8 py-4 text-center">
              <div className="text-3xl font-bold text-emerald-400">{formatCurrency(stats.totalSavings)}</div>
              <div className="text-sm text-slate-400">Total Savings Available</div>
            </div>
            <div className="glass-window border border-amber-500/30 rounded-xl px-8 py-4 text-center">
              <div className="text-3xl font-bold warm-gradient-text">$0</div>
              <div className="text-sm text-slate-400">Broker Fees</div>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => user ? navigate('/dashboard') : navigate('/auth')}
              size="lg"
              className="text-xl px-12 py-7 warm-gradient hover:shadow-2xl hover:shadow-amber-500/50 text-slate-900 font-bold rounded-xl transition-all duration-300 hover:scale-105"
            >
              Find Your #FeeFreeFind
              <ArrowRight className="w-6 h-6 ml-3" />
            </Button>
            <Button
              onClick={() => {
                navigator.clipboard.writeText('https://nofeesapts.com/fee-free-finds');
                alert('Link copied! Share #FeeFreeFinds with friends');
              }}
              variant="outline"
              size="lg"
              className="text-xl px-12 py-7 border-amber-500/40 text-amber-400 hover:bg-amber-500/10 font-semibold rounded-xl"
            >
              <Share2 className="w-5 h-5 mr-2" />
              Share
            </Button>
          </div>
        </div>
      </section>

      {/* What Makes a #FeeFreeFind */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/50 border-y border-amber-500/10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              What Makes a <span className="warm-gradient-text">#FeeFreeFind</span>?
            </h2>
            <p className="text-lg text-slate-300 max-w-2xl mx-auto">
              Every listing in our collection meets these standards
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: DollarSign,
                title: 'Zero Broker Fees',
                description: 'Direct from building management. No middlemen taking 15% of your annual rent.',
                highlight: 'Save $3,000-$8,000'
              },
              {
                icon: CheckCircle,
                title: 'Verified Listings',
                description: 'Crawled directly from official building websites. Updated every 48 hours.',
                highlight: 'Always Current'
              },
              {
                icon: Building2,
                title: 'Real Photos',
                description: 'Actual apartment images, not stock photos. See exactly what you\'re getting.',
                highlight: 'No Surprises'
              }
            ].map((feature, index) => (
              <Card 
                key={index} 
                className="bg-slate-900/50 border-amber-500/20 hover:border-amber-500/40 transition-all duration-300 group"
              >
                <CardContent className="p-8 text-center">
                  <div className="w-16 h-16 rounded-2xl warm-gradient flex items-center justify-center mx-auto mb-6 shadow-lg shadow-amber-500/20 group-hover:scale-110 transition-transform">
                    <feature.icon className="w-8 h-8 text-slate-900" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                  <p className="text-slate-400 mb-4">{feature.description}</p>
                  <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-3 py-1">
                    {feature.highlight}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Featured #FeeFreeFinds */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-400 border border-amber-500/30 px-4 py-2 text-sm font-semibold mb-4">
              <Sparkles className="w-4 h-4 mr-2 inline" />
              FEATURED COLLECTION
            </Badge>
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
              Latest <span className="warm-gradient-text">#FeeFreeFinds</span>
            </h2>
            <p className="text-lg text-slate-300 max-w-2xl mx-auto">
              Fresh no-fee apartments added to our collection. Sign up to unlock full details.
            </p>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="text-xl text-amber-500">Loading #FeeFreeFinds...</div>
            </div>
          ) : (
            <>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                {units.slice(0, 9).map((unit) => (
                  <div key={unit.id} className="relative">
                    {/* FeeFreeFinds Badge Overlay */}
                    <div className="absolute top-3 left-3 z-20">
                      <Badge className="bg-gradient-to-r from-amber-500 to-orange-500 text-slate-900 font-bold px-3 py-1.5 shadow-lg">
                        <Hash className="w-3.5 h-3.5 mr-1" />
                        FeeFreeFind
                      </Badge>
                    </div>
                    <ListingCard
                      unit={unit}
                      user={user}
                      isFavorite={favorites.has(unit.id)}
                      onToggleFavorite={toggleFavorite}
                      showBlur={!user}
                    />
                  </div>
                ))}
              </div>

              {/* View More CTA */}
              <div className="text-center">
                <Button
                  onClick={() => user ? navigate('/dashboard') : navigate('/auth')}
                  size="lg"
                  className="warm-gradient hover:shadow-xl hover:shadow-amber-500/40 text-slate-900 font-bold px-12 py-6 text-lg"
                >
                  View All {stats.totalUnits}+ #FeeFreeFinds
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </div>
            </>
          )}
        </div>
      </section>

      {/* Savings Calculator Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-emerald-900/20 via-slate-900 to-slate-900 border-y border-emerald-500/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
            See How Much You&apos;ll <span className="text-emerald-400">Save</span>
          </h2>
          
          <div className="glass-window border border-emerald-500/30 rounded-2xl p-8 mb-8">
            <div className="grid md:grid-cols-3 gap-8">
              <div>
                <p className="text-slate-400 text-sm mb-2">Typical Broker Fee</p>
                <p className="text-3xl font-bold text-red-400 line-through">15% Annual Rent</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm mb-2">Your Cost with Us</p>
                <p className="text-4xl font-bold text-emerald-400">$0</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm mb-2">Average Savings</p>
                <p className="text-3xl font-bold warm-gradient-text">$4,500+</p>
              </div>
            </div>
          </div>

          <p className="text-lg text-slate-300 mb-8">
            The average NYC renter pays <span className="text-red-400 font-semibold">$4,500 or more</span> in broker fees. 
            With #FeeFreeFinds, that money stays in your pocket.
          </p>

          <Button
            onClick={() => user ? navigate('/dashboard') : navigate('/auth')}
            size="lg"
            className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-10 py-6 text-lg shadow-lg shadow-emerald-500/30"
          >
            Start Saving Today
            <TrendingUp className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </section>

      {/* Browse by Location */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Find #FeeFreeFinds by Location
            </h2>
            <p className="text-lg text-slate-300">
              Explore no-fee apartments in your preferred neighborhood
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'Manhattan', url: '/location/manhattan' },
              { name: 'Brooklyn', url: '/location/brooklyn' },
              { name: 'Queens', url: '/location/queens' },
              { name: 'Jersey City', url: '/location/jersey-city' },
              { name: 'Hoboken', url: '/location/hoboken' },
              { name: 'Long Island City', url: '/location/long-island-city' },
              { name: 'Harrison', url: '/location/harrison' },
              { name: 'Weehawken', url: '/location/weehawken' }
            ].map((location) => (
              <button
                key={location.name}
                onClick={() => navigate(location.url)}
                className="glass-window border border-amber-500/20 rounded-xl p-4 hover:border-amber-500/40 transition-all group text-center"
              >
                <MapPin className="w-6 h-6 text-amber-500 mx-auto mb-2 group-hover:scale-110 transition-transform" />
                <span className="text-sm font-semibold text-slate-100 group-hover:text-amber-400 transition-colors">
                  {location.name}
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Social Share CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-amber-600 via-orange-500 to-amber-600">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900/20 rounded-full mb-6">
            <Hash className="w-5 h-5 text-slate-900" />
            <span className="font-bold text-slate-900">Share the Savings</span>
          </div>
          
          <h2 className="text-4xl sm:text-5xl font-bold text-slate-900 mb-6">
            Know Someone Apartment Hunting?
          </h2>
          <p className="text-xl text-slate-800 mb-8">
            Share #FeeFreeFinds and help them save thousands on broker fees.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => {
                const url = "https://nofeesapts.com/fee-free-finds";
                navigator.clipboard.writeText(url);
                toast.success('Link copied to clipboard!');
              }}
              size="lg"
              className="bg-slate-900 hover:bg-slate-800 text-amber-500 font-bold px-8 py-6"
            >
              Copy Link to Share
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 border-t border-slate-800 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <Logo size="default" />
          <p className="text-slate-400 mt-4 mb-6">
            #FeeFreeFinds - Saving NYC & NJ renters thousands on broker fees.
          </p>
          <div className="flex gap-6 justify-center text-sm">
            <button onClick={() => navigate('/')} className="text-slate-400 hover:text-amber-500 transition-colors">
              Home
            </button>
            <button onClick={() => navigate('/dashboard')} className="text-slate-400 hover:text-amber-500 transition-colors">
              Browse Apartments
            </button>
            <button onClick={() => navigate('/blog')} className="text-slate-400 hover:text-amber-500 transition-colors">
              Blog
            </button>
            <button onClick={() => navigate('/faq')} className="text-slate-400 hover:text-amber-500 transition-colors">
              FAQ
            </button>
          </div>
          <p className="text-sm text-slate-500 mt-8">
            © 2025 NoFeesApts.com. All rights reserved. • #FeeFreeFinds
          </p>
        </div>
      </footer>
    </div>
  );
};

export default FeeFreeFinds;
