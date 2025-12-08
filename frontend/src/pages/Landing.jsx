import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Building2, Search, Heart, Key, TrendingUp, Sparkles, ArrowRight, Eye, MapPin } from 'lucide-react';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import SignupModal from '../components/SignupModal';
import Logo from '@/components/Logo';
import SEO from '@/components/SEO';

const Landing = () => {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ buildings: 5, units: 206 });
  const [showSignupModal, setShowSignupModal] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      await axios.get(`${API}/auth/me`, { withCredentials: true });
      setIsAuthenticated(true);
    } catch (error) {
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/auth');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-900 to-slate-800">
        <div className="text-xl text-amber-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 overflow-hidden">
      <SEO
        title="No Broker Fee Apartments NYC & NJ"
        description={`Find your perfect apartment with zero broker fees. Browse ${stats.units}+ verified no-fee listings in NYC and Northern New Jersey. Real photos, real apartments, real savings.`}
        keywords="no fee apartments NYC, no broker fee apartments, NYC apartments, Northern New Jersey apartments, rent apartments NYC, no fee rentals, Manhattan apartments, Brooklyn apartments, Queens apartments"
        url="/"
        structuredData={{
          "@context": "https://schema.org",
          "@type": "RealEstateAgent",
          "name": "NoFeesApts.com",
          "description": "No broker fee apartment listings in NYC and Northern New Jersey",
          "url": "https://nofeesapts.com",
          "logo": "https://nofeesapts.com/logo.png",
          "address": {
            "@type": "PostalAddress",
            "addressRegion": "NY",
            "addressCountry": "US"
          },
          "areaServed": [
            {
              "@type": "City",
              "name": "New York City"
            },
            {
              "@type": "State",
              "name": "New Jersey"
            }
          ],
          "numberOfUnits": stats.units,
          "priceRange": "$2,800 - $5,445",
          "offers": {
            "@type": "Offer",
            "availability": "https://schema.org/InStock",
            "priceCurrency": "USD"
          }
        }}
      />
      
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-window border-b border-amber-500/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Logo size="default" />
            
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <Button
                  onClick={() => navigate('/dashboard')}
                  className="warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold px-6"
                  data-testid="dashboard-btn"
                >
                  View Apartments
                </Button>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/auth')}
                    className="text-slate-300 hover:text-amber-500 hover:bg-slate-800/50"
                    data-testid="signin-btn"
                  >
                    Sign In
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/auth?admin=true')}
                    className="text-amber-400 hover:text-amber-500 hover:bg-slate-800/50 border border-amber-500/30"
                    data-testid="admin-btn"
                  >
                    Admin
                  </Button>
                  <Button
                    onClick={() => navigate('/auth')}
                    className="warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold px-6"
                    data-testid="get-started-nav-btn"
                  >
                    Get Started
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - NYC Night Sky */}
      <section className="relative pt-32 pb-24 px-4 sm:px-6 lg:px-8 overflow-hidden min-h-[90vh] flex items-center">
        {/* Background - NYC Skyline Image */}
        <div className="absolute inset-0">
          {/* Hero Image */}
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat"
            style={{
              backgroundImage: `url('https://customer-assets.emergentagent.com/job_nyc-nofee/artifacts/r3ox8vya_105ab7408ce711f0acaefb59b9276889.png')`
            }}
          />
          
          {/* Gradient Overlays for better text readability and depth */}
          <div className="absolute inset-0 bg-gradient-to-b from-slate-900/70 via-slate-900/50 to-slate-900/90" />
          <div className="absolute inset-0 bg-gradient-to-r from-slate-900/60 via-transparent to-slate-900/60" />
          
          {/* Animated light particles for extra splash */}
          <div className="absolute inset-0 opacity-20">
            {[...Array(15)].map((_, i) => (
              <div
                key={i}
                className="absolute rounded-full city-light-shimmer"
                style={{
                  width: Math.random() * 6 + 3 + 'px',
                  height: Math.random() * 6 + 3 + 'px',
                  background: i % 2 === 0 ? '#f59e0b' : '#fbbf24',
                  left: Math.random() * 100 + '%',
                  top: Math.random() * 100 + '%',
                  animationDelay: Math.random() * 3 + 's',
                  boxShadow: `0 0 ${Math.random() * 30 + 15}px currentColor`
                }}
              />
            ))}
          </div>
          
          {/* Warm glow from bottom */}
          <div className="absolute bottom-0 left-0 right-0 h-96 bg-gradient-to-t from-amber-500/20 via-amber-500/5 to-transparent" />
        </div>

        <div className="max-w-7xl mx-auto relative z-10 w-full">
          <div className="text-center max-w-4xl mx-auto">
            {/* Main Heading - Minimal and clean */}
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 leading-tight animate-in fade-in slide-in-from-bottom duration-1000">
              <span className="block warm-gradient-text drop-shadow-2xl" style={{textShadow: '0 4px 30px rgba(245,158,11,0.5), 0 0 60px rgba(245,158,11,0.3)'}}>
                No Broker Fees
              </span>
            </h1>
            
            {/* Subheading - Minimal and clean */}
            <p className="text-lg sm:text-xl text-slate-100 mb-10 max-w-2xl mx-auto drop-shadow-lg animate-in fade-in slide-in-from-bottom duration-1000 delay-200" style={{textShadow: '0 2px 10px rgba(0,0,0,0.8)'}}>
              <span className="text-amber-400 font-semibold">{stats.units}+ apartments</span> in NYC & NJ
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-5 justify-center mb-16 animate-in fade-in slide-in-from-bottom duration-1000 delay-300">
              <Button
                data-testid="get-started-btn"
                onClick={handleGetStarted}
                size="lg"
                className="text-xl px-16 py-8 warm-gradient hover:shadow-2xl hover:shadow-amber-500/60 text-slate-900 font-bold rounded-2xl transition-all duration-300 hover:scale-105 shadow-2xl"
              >
                <Search className="w-6 h-6 mr-3" />
                Find Your View
                <ArrowRight className="w-6 h-6 ml-3" />
              </Button>
            </div>

            {/* Stats Bar - Minimal and clean */}
            <div className="flex gap-6 justify-center items-center max-w-2xl mx-auto glass-window border border-amber-500/20 rounded-xl px-8 py-6 backdrop-blur-md shadow-2xl shadow-amber-500/10 animate-in fade-in slide-in-from-bottom duration-1000 delay-300">
              <div className="text-center">
                <div className="text-3xl font-bold warm-gradient-text">{stats.units}+</div>
                <div className="text-xs text-slate-400 uppercase tracking-wide">Apartments</div>
              </div>
              <div className="h-10 w-px bg-slate-700/50"></div>
              <div className="text-center">
                <div className="text-3xl font-bold warm-gradient-text">$0</div>
                <div className="text-xs text-slate-400 uppercase tracking-wide">Fees</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How to Find Apartments - Simplified */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-slate-800/50 border-y border-amber-500/10">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
            Start Your Search
          </h2>
          <p className="text-base text-slate-300 mb-6">
            Browse verified no-fee listings in NYC & NJ
          </p>
          
          <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
            <Button
              onClick={() => setShowSignupModal(true)}
              size="lg"
              className="warm-gradient hover:shadow-xl hover:shadow-amber-500/40 text-slate-900 font-bold px-8"
            >
              Browse Apartments
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button
              onClick={handleGetStarted}
              variant="outline"
              size="lg"
              className="border-amber-500/30 text-amber-500 hover:bg-slate-700 px-8 font-semibold"
            >
              Sign In
            </Button>
          </div>
            </a>
            {' '}or{' '}
            <a href="tel:+16464088048" className="text-amber-500 hover:text-amber-400 font-medium">
              646-408-8048
            </a>
          </p>
        </div>
      </section>

      {/* The Moment Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 first-moment">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
              The Moment You've Been
              <span className="block warm-gradient-text">Working Towards</span>
            </h2>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto">
              Every late night. Every sacrifice. Every dream of your own space in this city.
              This is where it starts.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Search,
                title: 'Your Search Begins',
                description: 'Browse real apartments in real buildings. No games. No hidden fees. Just honest listings from people who get it.',
                gradient: 'from-amber-500 to-orange-600'
              },
              {
                icon: Key,
                title: 'Your Keys Arrive',
                description: 'Direct contact with buildings. No middleman taking your money. Your savings stay where they belong—in your pocket.',
                gradient: 'from-orange-500 to-red-600'
              },
              {
                icon: Eye,
                title: 'Move In With Confidence',
                description: 'Preview apartments with detailed photos, floor plans, and neighborhood information. Find your perfect NYC home with transparency and ease.',
                gradient: 'from-red-500 to-rose-600'
              }
            ].map((step, index) => (
              <div
                key={index}
                className="card-city-view glass-window border border-amber-500/10 rounded-2xl p-8"
              >
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${step.gradient} flex items-center justify-center mb-6 shadow-lg`}>
                  <step.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-white mb-4">{step.title}</h3>
                <p className="text-slate-300 leading-relaxed">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Section - Intimate & Personal */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-12 text-center">
              Because You've Earned This
            </h2>

            <div className="space-y-8">
              {[
                {
                  icon: Heart,
                  title: 'Save Thousands',
                  description: 'That broker fee? Keep it. Spend it on furniture. On exploring your new neighborhood. On living.'
                },
                {
                  icon: Building2,
                  title: 'Real Buildings, Real People',
                  description: 'Every listing verified. Updated every 48 hours. From actual building websites. No scams. No surprises.'
                },
                {
                  icon: TrendingUp,
                  title: 'Always Current',
                  description: 'The apartments you see are available right now. Not from three months ago. Not fake listings. Real homes.'
                },
                {
                  icon: Sparkles,
                  title: 'Your First Chapter',
                  description: 'This isn\'t just about finding an apartment. It\'s about claiming your spot in this city. Making it yours.'
                }
              ].map((feature, index) => (
                <div
                  key={index}
                  className="flex gap-6 glass-window border border-amber-500/10 rounded-2xl p-8 hover:border-amber-500/30 transition-all duration-300"
                >
                  <div className="flex-shrink-0 w-14 h-14 rounded-xl warm-gradient flex items-center justify-center shadow-lg shadow-amber-500/20">
                    <feature.icon className="w-7 h-7 text-slate-900" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-3">{feature.title}</h3>
                    <p className="text-slate-300 leading-relaxed text-lg">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Popular Locations */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-white mb-4">Find Apartments by Location</h2>
            <p className="text-lg text-slate-300 max-w-2xl mx-auto">
              Browse no-fee apartments in NYC's most popular neighborhoods and surrounding areas
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-6">
            {[
              { name: 'Manhattan', url: '/location/manhattan' },
              { name: 'Brooklyn', url: '/location/brooklyn' },
              { name: 'Queens', url: '/location/queens' },
              { name: 'Long Island City', url: '/location/long-island-city' },
              { name: 'Williamsburg', url: '/location/williamsburg' },
              { name: 'Jersey City', url: '/location/jersey-city' },
              { name: 'Hoboken', url: '/location/hoboken' },
              { name: 'Harrison', url: '/location/harrison' },
              { name: 'Weehawken', url: '/location/weehawken' },
              { name: 'Bronx', url: '/location/bronx' }
            ].map((location) => (
              <button
                key={location.name}
                onClick={() => navigate(location.url)}
                className="glass-window border border-amber-500/20 rounded-xl p-6 hover:border-amber-500/40 transition-all group text-center"
              >
                <MapPin className="w-8 h-8 text-amber-500 mx-auto mb-3 group-hover:scale-110 transition-transform" />
                <h3 className="text-lg font-semibold text-slate-100 group-hover:text-amber-400 transition-colors">
                  {location.name}
                </h3>
                <p className="text-sm text-slate-400 mt-1">View Apartments →</p>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA - Emotional */}
      <section className="py-32 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-slate-900 to-slate-800" />
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, #f59e0b 1px, transparent 0)',
            backgroundSize: '50px 50px'
          }} />
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-5xl sm:text-6xl font-bold text-white mb-8 leading-tight">
            Your Window.
            <br />
            <span className="warm-gradient-text">Your City.</span>
            <br />
            Your Time.
          </h2>
          <p className="text-2xl text-slate-300 mb-12 leading-relaxed">
            The lights are waiting. Your apartment is out there.
            <br />
            Let's find your view.
          </p>
          <Button
            data-testid="cta-start-btn"
            onClick={handleGetStarted}
            size="lg"
            className="text-xl px-16 py-8 warm-gradient hover:shadow-2xl hover:shadow-amber-500/50 text-slate-900 font-bold rounded-2xl transition-all duration-300 btn-warm"
          >
            Start Your Search
            <ArrowRight className="w-6 h-6 ml-3" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 border-t border-slate-800 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            {/* Brand */}
            <div className="text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start mb-4">
                <Logo size="default" />
              </div>
              <p className="text-sm text-slate-400">Your first apartment awaits.</p>
              <p className="text-sm text-slate-500 mt-2">NYC & Northern New Jersey</p>
            </div>
            
            {/* Quick Links */}
            <div className="text-center">
              <h3 className="text-white font-semibold mb-4">Quick Links</h3>
              <div className="space-y-2">
                <button
                  onClick={handleGetStarted}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Browse Apartments
                </button>
                <button
                  onClick={() => navigate('/blog')}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Blog & Guides
                </button>
                <button
                  onClick={() => navigate('/faq')}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  FAQ
                </button>
                <button
                  onClick={() => navigate('/auth')}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={() => setShowSignupModal(true)}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Create Account
                </button>
              </div>
            </div>
            
            {/* Locations */}
            <div className="text-center">
              <h3 className="text-white font-semibold mb-4">Locations</h3>
              <div className="space-y-2">
                <button
                  onClick={() => navigate('/location/manhattan')}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Manhattan
                </button>
                <button
                  onClick={() => navigate('/location/brooklyn')}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Brooklyn
                </button>
                <button
                  onClick={() => navigate('/location/queens')}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Queens
                </button>
                <button
                  onClick={() => navigate('/location/jersey-city')}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Jersey City
                </button>
                <button
                  onClick={() => navigate('/location/hoboken')}
                  className="block mx-auto text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  Hoboken
                </button>
              </div>
            </div>
            
            {/* Contact */}
            <div className="text-center md:text-right">
              <h3 className="text-white font-semibold mb-4">Contact Us</h3>
              <div className="space-y-2">
                <a
                  href="mailto:placesfirm@gmail.com"
                  className="block text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  placesfirm@gmail.com
                </a>
                <a
                  href="tel:+16464088048"
                  className="block text-slate-400 hover:text-amber-500 text-sm transition-colors"
                >
                  646-408-8048
                </a>
                <p className="text-xs text-slate-500 mt-4">
                  Available Mon-Fri, 9AM-6PM EST
                </p>
              </div>
            </div>
          </div>
          
          <div className="border-t border-slate-800 pt-8 text-center">
            <p className="text-sm text-slate-500">
              © 2025 NoFeesApts.com. All rights reserved. • No Broker Fees Ever
            </p>
          </div>
        </div>
      </footer>

      {/* Sticky CTA Banner - Only show if not authenticated */}
      {!isAuthenticated && (
        <div className="fixed bottom-0 left-0 right-0 z-50 animate-in slide-in-from-bottom duration-500">
          <div className="bg-gradient-to-r from-amber-600 via-orange-500 to-amber-600 shadow-2xl shadow-amber-500/50 border-t-2 border-amber-400">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-center sm:text-left">
                  <div className="flex items-center justify-center sm:justify-start gap-2 mb-1">
                    <Sparkles className="w-5 h-5 text-slate-900 animate-pulse" />
                    <h3 className="text-xl sm:text-2xl font-bold text-slate-900">
                      FREE SIGN UP FOR FULL ACCESS
                    </h3>
                  </div>
                  <p className="text-sm sm:text-base text-slate-800 font-medium">
                    Save favorites • Schedule viewings • Get instant alerts on 208+ no-fee apartments
                  </p>
                </div>
                <Button
                  onClick={() => setShowSignupModal(true)}
                  size="lg"
                  className="bg-slate-900 hover:bg-slate-800 text-amber-500 font-bold px-8 py-6 text-lg shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105 whitespace-nowrap"
                >
                  Join Free Now
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Signup Modal */}
      <SignupModal isOpen={showSignupModal} onClose={() => setShowSignupModal(false)} />
    </div>
  );
};

export default Landing;
