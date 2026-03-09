import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight, Building2, Shield, Clock, Sparkles, Play, X } from 'lucide-react';
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
  const [showVideoModal, setShowVideoModal] = useState(false);
  
  // Hero carousel state
  const [heroUnits, setHeroUnits] = useState([]);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const carouselIntervalRef = useRef(null);

  useEffect(() => {
    checkAuth();
    fetchFeaturedUnits();
    fetchStats();
    fetchHeroUnits();
  }, []);
  
  // Hero carousel auto-advance
  useEffect(() => {
    if (heroUnits.length > 1 && !isPaused) {
      carouselIntervalRef.current = setInterval(() => {
        setCurrentSlide(prev => (prev + 1) % heroUnits.length);
      }, 5500); // 5.5 seconds per slide - slower pace
    }
    return () => {
      if (carouselIntervalRef.current) {
        clearInterval(carouselIntervalRef.current);
      }
    };
  }, [heroUnits.length, isPaused]);

  const fetchHeroUnits = async () => {
    try {
      // Curated hero images - best living room interiors from specific buildings
      const curatedHeroImages = [
        {
          id: 'hero-507-west',
          images: ['https://customer-assets.emergentagent.com/job_nofeeapts/artifacts/oikxad8h_507%20Living%20Best.jpg'],
          building: { name: '507 West Chelsea', neighborhood: 'Chelsea' }
        },
        {
          id: 'hero-20-broad',
          images: ['https://customer-assets.emergentagent.com/job_2d2ca551-0173-4299-a0a8-c483c5631a96/artifacts/m60slrg7_20%20Broad%20LIving%20Room.jpg'],
          building: { name: '20 Broad', neighborhood: 'Financial District' }
        },
        {
          id: 'hero-60-water',
          images: ['https://assets.nestiostatic.com/unit_photos/originals/03efa49e3fa354f9842232d28b098f49.jpg?s=58d64a8acbab763307892fd2b5023b0b'],
          building: { name: '60 Water', neighborhood: 'DUMBO' }
        },
        {
          id: 'hero-aro',
          images: ['https://aro.nyc/wp-content/uploads/2017/11/Midtown-West-Luxury-Rentals-Living-1.jpg'],
          building: { name: 'Aro', neighborhood: 'Midtown West' }
        },
        {
          id: 'hero-7w21',
          images: ['https://www.7w21.com/img/DDP_0560-web.jpg'],
          building: { name: '7W21', neighborhood: 'Flatiron District' }
        }
      ];
      setHeroUnits(curatedHeroImages);
    } catch (error) {
      console.error('Error setting hero images:', error);
    }
  };
  
  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

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
      <nav className="fixed top-0 w-full z-50 bg-transparent">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex justify-between items-center h-20">
            <span className="text-2xl font-philosopher font-bold text-white tracking-wide drop-shadow-lg">
              NoFeesApts
            </span>
            
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <Button
                  onClick={() => navigate('/dashboard')}
                  className="bg-white/90 hover:bg-white text-[#0a0a0a] font-philosopher font-bold px-6 py-2.5 rounded-none tracking-wider shadow-lg"
                  data-testid="dashboard-btn"
                >
                  VIEW COLLECTION
                </Button>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    onClick={() => navigate('/auth')}
                    className="text-white hover:text-[#D4AF37] font-philosopher tracking-wide drop-shadow-lg"
                    data-testid="signin-btn"
                  >
                    Sign In
                  </Button>
                  <Button
                    onClick={() => navigate('/auth')}
                    className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-6 py-2.5 rounded-none tracking-wider transition-all duration-300 shadow-lg"
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

      {/* Hero Section - Full-Width Immersive Carousel */}
      <section 
        className="h-screen relative overflow-hidden"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        {/* Carousel Images */}
        <div className="absolute inset-0">
          {heroUnits.map((unit, index) => (
            <div
              key={unit.id}
              className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${
                index === currentSlide ? 'opacity-100' : 'opacity-0'
              }`}
            >
              <img
                src={unit.images?.[0] || 'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1920'}
                alt={`Luxury no-fee apartment interior ${index + 1}`}
                className="w-full h-full object-cover"
              />
              {/* Subtle gradient overlay for text readability */}
              <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/60" />
            </div>
          ))}
          
          {/* Fallback if no images */}
          {heroUnits.length === 0 && (
            <div className="absolute inset-0">
              <img
                src="https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1920"
                alt="Luxury apartment interior"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/60" />
            </div>
          )}
        </div>

        {/* Centered Content - Alluring CTA */}
        <div className="relative z-10 h-full flex flex-col items-center justify-center px-6">
          <div className="text-center animate-fade-in">
            {/* Decorative line */}
            <div className="w-12 h-px bg-[#D4AF37] mx-auto mb-6 opacity-80" />
            
            {/* Main headline */}
            <p className="text-white/90 font-philosopher text-lg tracking-[0.25em] uppercase mb-3">
              Explore
            </p>
            <h2 className="text-white font-philosopher text-4xl sm:text-5xl lg:text-6xl font-bold tracking-wide mb-4">
              <span className="text-[#D4AF37]">{stats.units}+</span> No-Fee Apartments
            </h2>
            <p className="text-white/70 font-philosopher text-base tracking-wider mb-8">
              NYC · NJ · PA
            </p>
            
            {/* CTA Button */}
            <button
              onClick={() => navigate('/auth')}
              className="group relative px-10 py-4 bg-transparent border border-white/30 hover:border-[#D4AF37] text-white font-philosopher tracking-[0.2em] text-sm transition-all duration-500 hover:bg-[#D4AF37]/10"
              data-testid="hero-cta-btn"
            >
              <span className="relative z-10 group-hover:text-[#D4AF37] transition-colors duration-300">
                BROWSE FREE
              </span>
            </button>
            
            {/* Subtle trust signal */}
            <p className="text-white/40 text-xs mt-6 tracking-wider">
              No credit card required
            </p>
          </div>
          
          {/* Carousel Indicators - moved to bottom left */}
          <div className="absolute bottom-32 left-6 max-w-7xl">
            {heroUnits.length > 1 && (
              <div className="flex items-center gap-3">
                {heroUnits.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => goToSlide(index)}
                    className={`h-0.5 transition-all duration-500 ${
                      index === currentSlide 
                        ? 'w-12 bg-white' 
                        : 'w-6 bg-white/40 hover:bg-white/60'
                    }`}
                    aria-label={`Go to slide ${index + 1}`}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* SEO-only text - hidden visually but accessible to search engines */}
        <div className="sr-only">
          <h1>No Broker Fee Apartments NYC & NJ</h1>
          <p>Find your perfect apartment with zero broker fees. Browse {stats.units}+ verified no-fee listings in NYC and Northern New Jersey.</p>
          <p>An exclusive selection of premium no fee apartments and luxury residences in NYC, Northern NJ & PA — handpicked for discerning renters seeking broker-free rentals.</p>
        </div>
        
        {/* Bottom scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
          <div className="w-px h-16 bg-gradient-to-b from-transparent via-white/60 to-transparent animate-pulse" />
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
              { name: 'Chelsea', url: '/apartments/chelsea' },
              { name: 'Tribeca', url: '/apartments/tribeca' },
              { name: 'Financial District', url: '/apartments/financial-district' },
              { name: 'Midtown West', url: '/apartments/midtown-west' },
              { name: 'Williamsburg', url: '/apartments/williamsburg' },
              { name: 'DUMBO', url: '/apartments/dumbo' },
              { name: 'Long Island City', url: '/apartments/long-island-city' },
              { name: 'Jersey City', url: '/apartments/jersey-city' },
              { name: 'Harrison', url: '/apartments/harrison' }
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
          
          <div className="text-center mt-8">
            <button
              onClick={() => navigate('/apartments')}
              className="text-[#D4AF37] text-sm font-philosopher tracking-wide hover:underline"
            >
              View All 28 Neighborhoods →
            </button>
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

      {/* Video Modal */}
      {showVideoModal && (
        <div 
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
          onClick={() => setShowVideoModal(false)}
        >
          <div 
            className="relative w-full max-w-4xl bg-black rounded-lg overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setShowVideoModal(false)}
              className="absolute top-4 right-4 z-10 w-10 h-10 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors"
            >
              <X className="w-5 h-5 text-white" />
            </button>
            <video
              src="https://customer-assets.emergentagent.com/job_47dd6b46-e381-45f3-b7a5-c4e5965d2ca7/artifacts/er34lg4y_The_No-Fee_Revolution.mp4"
              controls
              autoPlay
              className="w-full aspect-video"
            />
            <div className="p-4 bg-gray-900">
              <h3 className="text-white font-bold mb-1">The No-Fee Revolution</h3>
              <p className="text-gray-400 text-sm">Learn how NoFeesApts saves you thousands on broker fees</p>
              <Link 
                to="/how-it-works" 
                className="text-amber-400 text-sm mt-2 inline-block hover:underline"
                onClick={() => setShowVideoModal(false)}
              >
                Learn more →
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Landing;
