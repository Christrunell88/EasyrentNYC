import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight, Building2, Shield, Clock, Sparkles } from 'lucide-react';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import SignupModal from '../components/SignupModal';
import EmailCaptureModal from '../components/EmailCaptureModal';
import ListingCard from '../components/ListingCard';
import SEO from '@/components/SEO';
import Footer from '@/components/Footer';

const Landing = () => {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ buildings: 34, units: 180 });
  const statsLoadedRef = useRef(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [featuredUnits, setFeaturedUnits] = useState([]);
  const [subscribeEmail, setSubscribeEmail] = useState('');
  const [subscribing, setSubscribing] = useState(false);

  useEffect(() => {
    checkAuth();
    fetchFeaturedUnits();
    fetchStats();
  }, []);

  const fetchStats = async () => {
    // Only fetch once to prevent overwriting
    if (statsLoadedRef.current) return;
    
    try {
      // Add timestamp to bust cache
      const response = await axios.get(`${API}/stats?_t=${Date.now()}`);
      if (response.data && response.data.total_units) {
        statsLoadedRef.current = true;
        setStats({
          buildings: response.data.total_buildings || 34,
          units: response.data.total_units
        });
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
      // Keep the default values
    }
  };

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
      // Fetch most recently added units
      const response = await axios.get(`${API}/units/recent?limit=6`);
      setFeaturedUnits(response.data);
    } catch (error) {
      console.error('Error fetching featured units:', error);
      // Fallback to regular units if recent endpoint fails
      try {
        const fallback = await axios.get(`${API}/units?limit=6`);
        setFeaturedUnits(fallback.data);
      } catch (e) {
        console.error('Fallback also failed:', e);
      }
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
      <div className="min-h-screen flex items-center justify-center bg-[#0a0a0a]">
        <div className="text-lg text-[#D4AF37] font-philosopher">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <SEO
        title="No Broker Fee Apartments NYC & NJ"
        description={`Find your perfect apartment with zero broker fees. Browse ${stats.units}+ verified no-fee listings in NYC and Northern New Jersey.`}
        keywords="no fee apartments NYC, no broker fee apartments, NYC apartments, Northern New Jersey apartments, no fee apartments near me, cheap no fee apartments NYC, luxury no fee apartments, rent without broker fee NYC, best no fee apartment websites, streeteasy alternative, Jersey City no fee, Hoboken apartments no fee, how to find no fee apartments NYC"
        url="/"
      />
      
      {/* Organization Schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "RealEstateAgent",
          "name": "NoFeesApts.com",
          "alternateName": "No Fees Apts",
          "description": "No broker fee apartment listings in NYC, Northern New Jersey, and Pennsylvania. Save thousands on broker fees.",
          "url": "https://www.nofeesapts.com",
          "logo": "https://www.nofeesapts.com/logo.png",
          "sameAs": [
            "https://www.facebook.com/Places.NYC.LLC"
          ],
          "address": {
            "@type": "PostalAddress",
            "addressLocality": "New York",
            "addressRegion": "NY",
            "addressCountry": "US"
          },
          "areaServed": [
            { "@type": "City", "name": "New York" },
            { "@type": "City", "name": "Brooklyn" },
            { "@type": "City", "name": "Jersey City" },
            { "@type": "City", "name": "Hoboken" },
            { "@type": "State", "name": "New Jersey" }
          ],
          "priceRange": "$1,500 - $15,000/month"
        }) }}
      />
      
      {/* WebSite Schema for Sitelinks Search */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "WebSite",
          "name": "NoFeesApts.com",
          "alternateName": "No Fee Apartments NYC",
          "url": "https://www.nofeesapts.com",
          "description": "Find no broker fee apartments in NYC, NJ & PA",
          "potentialAction": {
            "@type": "SearchAction",
            "target": {
              "@type": "EntryPoint",
              "urlTemplate": "https://www.nofeesapts.com/dashboard?search={search_term_string}"
            },
            "query-input": "required name=search_term_string"
          }
        }) }}
      />
      
      {/* ItemList Schema for Featured Listings */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify({
          "@context": "https://schema.org",
          "@type": "ItemList",
          "name": "No Fee Apartments",
          "description": "Featured no broker fee apartments in NYC and NJ",
          "numberOfItems": stats.units,
          "itemListElement": [
            {
              "@type": "ListItem",
              "position": 1,
              "name": "Studio Apartments",
              "url": "https://www.nofeesapts.com/dashboard?bedrooms=0"
            },
            {
              "@type": "ListItem", 
              "position": 2,
              "name": "1 Bedroom Apartments",
              "url": "https://www.nofeesapts.com/dashboard?bedrooms=1"
            },
            {
              "@type": "ListItem",
              "position": 3,
              "name": "2 Bedroom Apartments", 
              "url": "https://www.nofeesapts.com/dashboard?bedrooms=2"
            }
          ]
        }) }}
      />
      
      {/* Navigation - Clean White Theme */}
      <nav className="fixed top-0 w-full z-50 bg-white/95 backdrop-blur-sm border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-center h-20">
            <span className="text-2xl font-philosopher font-bold text-[#0a0a0a] tracking-wide">
              NoFeesApts
            </span>
            
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <Button
                  onClick={() => navigate('/dashboard')}
                  className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-6 py-2.5 rounded-none tracking-wider"
                  data-testid="dashboard-btn"
                >
                  VIEW COLLECTION
                </Button>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/auth')}
                    className="text-[#0a0a0a] hover:text-[#D4AF37] font-philosopher tracking-wide"
                    data-testid="signin-btn"
                  >
                    Sign In
                  </Button>
                  <Button
                    onClick={() => navigate('/auth')}
                    className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-6 py-2.5 rounded-none tracking-wider transition-all duration-300"
                    data-testid="get-started-nav-btn"
                  >
                    FREE SIGN UP
                  </Button>
                </>  
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - Clean White Theme with Three Interior Images */}
      <section className="min-h-screen relative overflow-hidden pt-20 bg-white">
        {/* Content */}
        <div className="relative z-10 min-h-[calc(100vh-5rem)] flex items-center">
          <div className="max-w-7xl mx-auto px-6 w-full py-12">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              {/* Left Content */}
              <div className="max-w-xl">
                {/* Decorative line */}
                <div className="w-16 h-px bg-[#D4AF37] mb-8" />
                
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-philosopher font-bold text-[#0a0a0a] leading-tight tracking-wide mb-6">
                  Find Your<br />No-Fee Apartment
                </h1>
                
                <p className="text-lg text-[#555555] font-philosopher mb-8 leading-relaxed">
                  Verified luxury apartments in NYC, NJ & PA — <span className="text-[#D4AF37] font-semibold">zero broker fees</span>, ready in minutes.
                </p>

                {/* Call to Action Box */}
                <div className="bg-[#f8f8f8] border border-[#D4AF37]/40 p-6 mb-8">
                  <p className="text-[#D4AF37] font-philosopher tracking-[0.15em] uppercase text-xs mb-4 font-semibold">
                    Free Sign Up for Full Access
                  </p>
                  <p className="text-[#0a0a0a] font-philosopher text-lg mb-4">
                    Get <span className="text-[#D4AF37] font-bold">full access</span> and <span className="text-[#D4AF37] font-bold">new listings alerts</span>
                  </p>
                  
                  <div className="space-y-3 text-[#555555]">
                    <div className="flex items-center gap-3">
                      <span className="text-[#D4AF37]">📞</span>
                      <a href="tel:646-408-8048" className="font-philosopher hover:text-[#D4AF37] transition-colors">
                        Call Office: <span className="text-[#0a0a0a] font-semibold">646-408-8048</span>
                      </a>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[#D4AF37]">✉️</span>
                      <a href="mailto:Placesfirm@gmail.com" className="font-philosopher hover:text-[#D4AF37] transition-colors">
                        Email: <span className="text-[#0a0a0a] font-semibold">Placesfirm@gmail.com</span>
                      </a>
                    </div>
                  </div>
                </div>
                
                {/* SEO-only text - hidden visually but accessible to search engines */}
                <p className="sr-only">
                  An exclusive selection of premium no fee apartments and luxury residences in NYC, Northern NJ & PA — handpicked for discerning renters seeking broker-free rentals.
                </p>
                
                <div className="flex flex-col items-start gap-3">
                  <Button
                    data-testid="get-started-btn"
                    onClick={handleGetStarted}
                    size="lg"
                    className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-12 py-7 text-lg rounded-none tracking-[0.15em] transition-all duration-300 hover:shadow-[0_0_40px_rgba(212,175,55,0.3)]"
                  >
                    FREE SIGN UP
                    <ArrowRight className="w-5 h-5 ml-3" />
                  </Button>
                  <span className="text-[#16a34a] text-xs font-semibold tracking-wider flex items-center gap-1.5 ml-1">
                    <span className="w-1.5 h-1.5 bg-[#16a34a] rounded-full animate-pulse"></span>
                    100% FREE • No Credit Card Required
                  </span>
                </div>
              </div>
              
              {/* Right side - Three Interior Images Gallery */}
              <div className="hidden lg:block">
                <div className="grid grid-cols-2 gap-4">
                  {/* Large main image - Studio */}
                  <div className="col-span-2 relative overflow-hidden group">
                    <img 
                      src="https://customer-assets.emergentagent.com/job_2d2ca551-0173-4299-a0a8-c483c5631a96/artifacts/cufz4u39_Mercedes%201.avif"
                      alt="Modern studio apartment with open floor plan and natural light"
                      className="w-full h-64 object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-4">
                      <span className="text-white font-philosopher text-sm tracking-wider">Studio</span>
                    </div>
                  </div>
                  
                  {/* 1 Bedroom image */}
                  <div className="relative overflow-hidden group">
                    <img 
                      src="https://manhattanskyline.com/storage/_styles/multi-hero/unit/DrhLWHRUuysjFGyY3xcMq5qP90nNeFGHQlloJn02.jpg"
                      alt="Spacious one bedroom apartment living area"
                      className="w-full h-48 object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
                      <span className="text-white font-philosopher text-sm tracking-wider">1 Bedroom</span>
                    </div>
                  </div>
                  
                  {/* 2 Bedroom image */}
                  <div className="relative overflow-hidden group">
                    <img 
                      src="https://customer-assets.emergentagent.com/job_8fbd80f2-6d7f-4862-a8ee-2ee677906dbe/artifacts/pv5un3kv_301%20Living%20Room.jpeg"
                      alt="Elegant two bedroom apartment with city views"
                      className="w-full h-48 object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
                      <span className="text-white font-philosopher text-sm tracking-wider">2 Bedroom</span>
                    </div>
                  </div>
                </div>
                
                {/* Stats below images */}
                <div className="mt-6 flex justify-between items-center border-t border-gray-200 pt-6">
                  <div className="text-center">
                    <p className="text-3xl font-philosopher font-bold text-[#0a0a0a]">{stats.units}+</p>
                    <p className="text-[#888888] text-xs mt-1">No Fee Apartments</p>
                  </div>
                  <div className="w-px h-10 bg-gray-200" />
                  <div className="text-center">
                    <p className="text-3xl font-philosopher font-bold text-[#0a0a0a]">{stats.buildings}</p>
                    <p className="text-[#888888] text-xs mt-1">Premium Buildings</p>
                  </div>
                  <div className="w-px h-10 bg-gray-200" />
                  <div className="text-center">
                    <p className="text-3xl font-philosopher font-bold text-[#D4AF37]">$0</p>
                    <p className="text-[#888888] text-xs mt-1">Broker Fees</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Bottom scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
          <div className="w-px h-16 bg-gradient-to-b from-transparent via-[#D4AF37] to-transparent animate-pulse" />
        </div>
      </section>

      {/* Recent Listings Section */}
      <section className="py-24 px-6 bg-[#f8f8f8]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-[#D4AF37] font-philosopher tracking-[0.3em] uppercase text-sm mb-4">
              Just Added
            </p>
            <h2 className="text-3xl sm:text-4xl font-philosopher font-bold text-[#0a0a0a] mb-4">
              New Arrivals
            </h2>
            <div className="w-16 h-px bg-[#D4AF37] mx-auto mt-6" />
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
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
              className="border border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37] hover:text-[#0a0a0a] font-philosopher font-bold px-10 py-5 rounded-none tracking-[0.15em] transition-all duration-300"
            >
              SIGN UP TO VIEW ALL {stats.units}+ PROPERTIES
              <ArrowRight className="w-4 h-4 ml-3" />
            </Button>
          </div>
        </div>
      </section>

      {/* Value Props - Clean Style */}
      <section className="py-24 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-[#D4AF37] font-philosopher tracking-[0.3em] uppercase text-sm mb-4">
              Why Choose Us
            </p>
            <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a]">
              The NoFeesApts Difference
            </h2>
            <div className="w-16 h-px bg-[#D4AF37] mx-auto mt-6" />
          </div>
          
          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center group">
              <div className="w-16 h-16 border border-[#D4AF37]/50 flex items-center justify-center mx-auto mb-6 group-hover:border-[#D4AF37] group-hover:bg-[#D4AF37]/5 transition-all duration-300">
                <Shield className="w-7 h-7 text-[#D4AF37]" />
              </div>
              <h3 className="text-lg font-philosopher font-bold text-[#0a0a0a] mb-3 tracking-wide">Zero Broker Fees</h3>
              <p className="text-[#666666] text-sm leading-relaxed">
                Save thousands on your next move. Every property listed is direct from management.
              </p>
            </div>
            
            <div className="text-center group">
              <div className="w-16 h-16 border border-[#D4AF37]/50 flex items-center justify-center mx-auto mb-6 group-hover:border-[#D4AF37] group-hover:bg-[#D4AF37]/5 transition-all duration-300">
                <Clock className="w-7 h-7 text-[#D4AF37]" />
              </div>
              <h3 className="text-lg font-philosopher font-bold text-[#0a0a0a] mb-3 tracking-wide">Updated Daily</h3>
              <p className="text-[#666666] text-sm leading-relaxed">
                Fresh listings every 48 hours. No outdated or unavailable properties.
              </p>
            </div>
            
            <div className="text-center group">
              <div className="w-16 h-16 border border-[#D4AF37]/50 flex items-center justify-center mx-auto mb-6 group-hover:border-[#D4AF37] group-hover:bg-[#D4AF37]/5 transition-all duration-300">
                <Sparkles className="w-7 h-7 text-[#D4AF37]" />
              </div>
              <h3 className="text-lg font-philosopher font-bold text-[#0a0a0a] mb-3 tracking-wide">Curated Selection</h3>
              <p className="text-[#666666] text-sm leading-relaxed">
                Only the finest properties make our collection. Quality over quantity.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Locations */}
      <section className="py-24 px-6 bg-[#f8f8f8]">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-[#D4AF37] font-philosopher tracking-[0.3em] uppercase text-sm mb-4">
              Neighborhoods
            </p>
            <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a]">Popular Locations</h2>
            <div className="w-16 h-px bg-[#D4AF37] mx-auto mt-6" />
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
                className="px-6 py-3 border border-[#D4AF37]/40 text-[#0a0a0a] text-sm font-philosopher tracking-wide hover:border-[#D4AF37] hover:bg-[#D4AF37]/10 transition-all duration-300"
              >
                {location.name}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Email Signup */}
      <section className="py-24 px-6 bg-white relative border-t border-gray-200">
        <div className="max-w-xl mx-auto text-center relative z-10">
          <p className="text-[#D4AF37] font-philosopher tracking-[0.3em] uppercase text-sm mb-4">
            Stay Informed
          </p>
          <h2 className="text-3xl font-philosopher font-bold text-[#0a0a0a] mb-4">
            New Listings in Your Inbox
          </h2>
          <p className="text-[#666666] mb-10">
            Be the first to know when exceptional properties become available.
          </p>
          
          <form onSubmit={handleSubscribe} className="flex flex-col sm:flex-row gap-4">
            <input
              type="email"
              value={subscribeEmail}
              onChange={(e) => setSubscribeEmail(e.target.value)}
              placeholder="Enter your email"
              required
              className="flex-1 px-6 py-4 bg-[#f8f8f8] border border-gray-300 text-[#0a0a0a] placeholder:text-[#999999] focus:outline-none focus:border-[#D4AF37] transition-colors font-philosopher"
            />
            <Button
              type="submit"
              disabled={subscribing}
              className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-8 py-4 rounded-none tracking-[0.1em] transition-all duration-300"
            >
              {subscribing ? 'SUBSCRIBING...' : 'SUBSCRIBE'}
            </Button>
          </form>
          
          <p className="text-xs text-[#888888] mt-6 font-philosopher">
            No spam. Unsubscribe anytime.
          </p>
        </div>
      </section>

      {/* Footer - Clean Light Theme */}
      <footer className="py-16 px-6 border-t border-gray-200 bg-[#f8f8f8]">
        <div className="max-w-6xl mx-auto">
          {/* Main Footer Content */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
            {/* Brand & Description */}
            <div className="lg:col-span-1">
              <span className="text-2xl font-philosopher font-bold text-[#0a0a0a] tracking-wide">NoFeesApts</span>
              <p className="text-sm text-[#666666] mt-3 leading-relaxed">
                Your trusted source for no broker fee apartments in NYC, Northern New Jersey, and Pennsylvania. 
                Save thousands on broker fees with our curated collection of verified no-fee rentals.
              </p>
              <p className="text-xs text-[#888888] mt-4">
                <a href="mailto:placesfirm@gmail.com" className="hover:text-[#D4AF37] transition-colors">
                  placesfirm@gmail.com
                </a>
              </p>
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="text-sm font-semibold text-[#D4AF37] mb-4 tracking-wide uppercase">Quick Links</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <button onClick={handleGetStarted} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Browse All Apartments
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/fee-free-finds')} className="text-[#888888] hover:text-[#D4AF37] transition-colors">
                    #FeeFreeFinds
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/blog')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Apartment Hunting Blog
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/blog/guide-to-no-fee-apartments')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    No-Fee Apartment Guide
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/faq')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    FAQ
                  </button>
                </li>
              </ul>
            </div>

            {/* NYC Neighborhoods */}
            <div>
              <h3 className="text-sm font-semibold text-[#D4AF37] mb-4 tracking-wide uppercase">NYC No-Fee Apartments</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <button onClick={() => navigate('/location/Upper West Side-New York')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Upper West Side
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Upper East Side-New York')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Upper East Side
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Midtown West-New York')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Midtown West
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Chelsea-New York')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Chelsea
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Tribeca-New York')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Tribeca
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/SoHo-New York')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    SoHo
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/East Village-New York')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    East Village
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Long Island City-Queens')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Long Island City
                  </button>
                </li>
              </ul>
            </div>

            {/* NJ & Brooklyn */}
            <div>
              <h3 className="text-sm font-semibold text-[#D4AF37] mb-4 tracking-wide uppercase">NJ & Brooklyn</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <button onClick={() => navigate('/location/Harrison-Harrison')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Harrison, NJ
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Princeton-Princeton')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Princeton, NJ
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Linden-Linden')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Linden, NJ
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/DUMBO-Brooklyn')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    DUMBO, Brooklyn
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Carroll Gardens-Brooklyn')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Carroll Gardens
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/location/Langhorne-Langhorne')} className="text-[#666666] hover:text-[#D4AF37] transition-colors">
                    Langhorne, PA
                  </button>
                </li>
              </ul>
            </div>
          </div>

          {/* SEO Content Section */}
          <div className="border-t border-gray-300 pt-10 mb-10">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm text-[#666666] leading-relaxed">
              <div>
                <h4 className="text-[#D4AF37] font-semibold mb-2">About No-Fee Apartments</h4>
                <p>
                  NoFeesApts.com specializes in no broker fee apartment rentals across New York City, Northern New Jersey, 
                  and Pennsylvania. We help renters save thousands of dollars by connecting them directly with 
                  landlords and management companies that don't charge broker fees. Our listings include studios, 
                  1-bedroom, 2-bedroom, and 3-bedroom apartments in Manhattan, Brooklyn, Queens, and Jersey City.
                </p>
              </div>
              <div>
                <h4 className="text-[#D4AF37] font-semibold mb-2">Why Choose No-Fee Rentals?</h4>
                <p>
                  Broker fees in NYC typically range from one month's rent to 15% of annual rent—that's $3,000 to $6,000+ 
                  you could save. Our verified no-fee listings are updated daily, featuring luxury amenities like 
                  doorman buildings, fitness centers, rooftop terraces, in-unit laundry, and pet-friendly policies. 
                  Start your apartment search with NoFeesApts.com today.
                </p>
              </div>
            </div>
          </div>
        </div>
      </footer>

      {/* Footer with Internal Links */}
      <Footer />

      {/* Signup Modal */}
      <SignupModal isOpen={showSignupModal} onClose={() => setShowSignupModal(false)} />
      
      {/* Email Capture Modal */}
      <EmailCaptureModal />
    </div>
  );
};

export default Landing;
