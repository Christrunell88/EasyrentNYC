import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight, Building2, Search, Shield, Clock, MapPin } from 'lucide-react';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import SignupModal from '../components/SignupModal';
import EmailCaptureModal from '../components/EmailCaptureModal';
import ListingCard from '../components/ListingCard';
import SEO from '@/components/SEO';

const Landing = () => {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ buildings: 5, units: 206 });
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [featuredUnits, setFeaturedUnits] = useState([]);
  const [subscribeEmail, setSubscribeEmail] = useState('');
  const [subscribing, setSubscribing] = useState(false);

  useEffect(() => {
    checkAuth();
    fetchFeaturedUnits();
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

  const fetchFeaturedUnits = async () => {
    try {
      const response = await axios.get(`${API}/units?limit=3`);
      setFeaturedUnits(response.data);
    } catch (error) {
      console.error('Error fetching featured units:', error);
    }
  };

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/auth');
    }
  };

  const handleSubscribe = async (e) => {
    e.preventDefault();
    if (!subscribeEmail) return;
    
    setSubscribing(true);
    try {
      await axios.post(`${API}/subscribe`, { email: subscribeEmail });
      alert('Thanks for subscribing! Check your inbox for a welcome email.');
      setSubscribeEmail('');
    } catch (error) {
      if (error.response?.data?.detail === 'Email already subscribed') {
        alert('This email is already subscribed!');
      } else {
        alert('Failed to subscribe. Please try again.');
      }
    } finally {
      setSubscribing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-lg text-slate-900">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <SEO
        title="No Broker Fee Apartments NYC & NJ"
        description={`Find your perfect apartment with zero broker fees. Browse ${stats.units}+ verified no-fee listings in NYC and Northern New Jersey.`}
        keywords="no fee apartments NYC, no broker fee apartments, NYC apartments, Northern New Jersey apartments"
        url="/"
        structuredData={{
          "@context": "https://schema.org",
          "@type": "RealEstateAgent",
          "name": "NoFeesApts.com",
          "description": "No broker fee apartment listings in NYC and Northern New Jersey",
          "url": "https://nofeesapts.com",
          "areaServed": [
            { "@type": "City", "name": "New York City" },
            { "@type": "State", "name": "New Jersey" }
          ],
          "numberOfUnits": stats.units
        }}
      />
      
      {/* Navigation - Clean & Minimal */}
      <nav className="fixed top-0 w-full z-50 bg-white/95 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <span className="text-xl font-bold text-slate-900 tracking-tight">
              NoFeesApts
            </span>
            
            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <Button
                  onClick={() => navigate('/dashboard')}
                  className="bg-slate-900 hover:bg-slate-800 text-white font-medium px-5 py-2 rounded-lg"
                  data-testid="dashboard-btn"
                >
                  View Apartments
                </Button>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/auth')}
                    className="text-slate-600 hover:text-slate-900 font-medium"
                    data-testid="signin-btn"
                  >
                    Sign In
                  </Button>
                  <Button
                    onClick={() => navigate('/auth')}
                    className="bg-slate-900 hover:bg-slate-800 text-white font-medium px-5 py-2 rounded-lg"
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

      {/* Hero Section - Tall, Clean, Dominant */}
      <section className="min-h-screen flex items-center justify-center px-6 pt-16">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-900 leading-tight tracking-tight mb-10">
            Sign Up to Find 1000's of Apartments
          </h1>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              data-testid="get-started-btn"
              onClick={handleGetStarted}
              size="lg"
              className="bg-slate-900 hover:bg-slate-800 text-white font-semibold px-8 py-6 text-lg rounded-xl"
            >
              GET EARLY ACCESS
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* Value Props - 3 Clean Blocks */}
      <section className="py-24 px-6 bg-slate-50">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-12 h-12 bg-slate-900 rounded-xl flex items-center justify-center mx-auto mb-5">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Zero Broker Fees</h3>
              <p className="text-slate-500 text-sm">
                Save thousands. Every listing is direct from building management.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-slate-900 rounded-xl flex items-center justify-center mx-auto mb-5">
                <Clock className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Updated Daily</h3>
              <p className="text-slate-500 text-sm">
                Fresh listings every 48 hours. No outdated or fake apartments.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-slate-900 rounded-xl flex items-center justify-center mx-auto mb-5">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Verified Buildings</h3>
              <p className="text-slate-500 text-sm">
                Real photos, real addresses, real availability.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Listings - Minimal */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              Featured Apartments
            </h2>
            <p className="text-slate-500 max-w-lg mx-auto">
              A preview of available no-fee listings. Sign up to see full details.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-12">
            {featuredUnits.map((unit) => (
              <ListingCard
                key={unit.id}
                unit={unit}
                user={null}
                isFavorite={false}
                onToggleFavorite={() => navigate('/auth')}
                showBlur={true}
              />
            ))}
          </div>

          <div className="text-center">
            <Button
              onClick={() => navigate('/auth')}
              variant="outline"
              size="lg"
              className="border-slate-300 text-slate-900 hover:bg-slate-50 font-medium px-8 py-5 rounded-xl"
            >
              View All {stats.units}+ Apartments
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* Locations - Compact */}
      <section className="py-24 px-6 bg-slate-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Popular Locations</h2>
            <p className="text-slate-500">Browse apartments by neighborhood</p>
          </div>
          
          <div className="flex flex-wrap justify-center gap-3">
            {[
              { name: 'Manhattan', url: '/location/manhattan' },
              { name: 'Brooklyn', url: '/location/brooklyn' },
              { name: 'Queens', url: '/location/queens' },
              { name: 'Jersey City', url: '/location/jersey-city' },
              { name: 'Hoboken', url: '/location/hoboken' },
              { name: 'Long Island City', url: '/location/long-island-city' },
              { name: 'Williamsburg', url: '/location/williamsburg' },
              { name: 'Harrison', url: '/location/harrison' }
            ].map((location) => (
              <button
                key={location.name}
                onClick={() => navigate(location.url)}
                className="px-5 py-2.5 bg-white text-slate-700 rounded-full text-sm font-medium hover:bg-slate-900 hover:text-white transition-colors"
              >
                {location.name}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Email Signup - Clean CTA */}
      <section className="py-24 px-6">
        <div className="max-w-xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            Get new listings in your inbox
          </h2>
          <p className="text-slate-500 mb-8">
            Be the first to know when new no-fee apartments become available.
          </p>
          
          <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-3">
            <input
              type="email"
              value={subscribeEmail}
              onChange={(e) => setSubscribeEmail(e.target.value)}
              placeholder="Enter your email"
              required
              className="flex-1 px-5 py-4 rounded-xl bg-slate-50 border-0 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900"
            />
            <Button
              type="submit"
              disabled={subscribing}
              size="lg"
              className="bg-slate-900 hover:bg-slate-800 text-white font-semibold px-8 py-4 rounded-xl"
            >
              {subscribing ? 'Subscribing...' : 'Subscribe'}
            </Button>
          </form>
          
          <p className="text-xs text-slate-400 mt-4">
            No spam. Unsubscribe anytime.
          </p>
        </div>
      </section>

      {/* Footer - Minimal */}
      <footer className="py-12 px-6 border-t border-slate-100">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-center md:text-left">
              <span className="text-lg font-bold text-slate-900">NoFeesApts</span>
              <p className="text-sm text-slate-500 mt-1">NYC & Northern New Jersey</p>
            </div>
            
            <div className="flex flex-wrap justify-center gap-6 text-sm">
              <button
                onClick={handleGetStarted}
                className="text-slate-500 hover:text-slate-900"
              >
                Browse Apartments
              </button>
              <button
                onClick={() => navigate('/fee-free-finds')}
                className="text-slate-500 hover:text-slate-900"
              >
                #FeeFreeFinds
              </button>
              <button
                onClick={() => navigate('/blog')}
                className="text-slate-500 hover:text-slate-900"
              >
                Blog
              </button>
              <button
                onClick={() => navigate('/faq')}
                className="text-slate-500 hover:text-slate-900"
              >
                FAQ
              </button>
              <a
                href="mailto:placesfirm@gmail.com"
                className="text-slate-500 hover:text-slate-900"
              >
                Contact
              </a>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-400">
              © 2025 NoFeesApts.com. All rights reserved.
            </p>
          </div>
        </div>
      </footer>

      {/* Signup Modal */}
      <SignupModal isOpen={showSignupModal} onClose={() => setShowSignupModal(false)} />
      
      {/* Email Capture Modal */}
      <EmailCaptureModal />
    </div>
  );
};

export default Landing;
