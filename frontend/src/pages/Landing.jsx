import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Building2, Search, Heart, Key, TrendingUp, Sparkles, ArrowRight, Eye } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import SignupModal from '../components/SignupModal';
import Logo from '@/components/Logo';

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
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-window border-b border-amber-500/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg warm-gradient flex items-center justify-center shadow-lg shadow-amber-500/20">
                <Building2 className="w-6 h-6 text-slate-900" />
              </div>
              <span className="text-xl font-semibold warm-gradient-text">
                NoFeesApts.com
              </span>
            </div>
            
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
          <div className="text-center max-w-5xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-6 py-3 glass-window border border-amber-500/30 rounded-full mb-8 backdrop-blur-md shadow-xl shadow-amber-500/20 animate-in fade-in slide-in-from-top duration-700">
              <Eye className="w-5 h-5 text-amber-500" />
              <span className="text-base font-semibold text-amber-400">Your First View of the City</span>
            </div>
            
            {/* Main Heading - Enhanced with stronger shadows */}
            <h1 className="text-5xl sm:text-6xl lg:text-8xl font-bold mb-8 leading-tight animate-in fade-in slide-in-from-bottom duration-1000">
              <span className="block text-white mb-4 drop-shadow-2xl" style={{textShadow: '0 4px 20px rgba(0,0,0,0.8), 0 0 40px rgba(0,0,0,0.5)'}}>
                Your First Apartment.
              </span>
              <span className="block warm-gradient-text drop-shadow-2xl" style={{textShadow: '0 4px 30px rgba(245,158,11,0.5), 0 0 60px rgba(245,158,11,0.3)'}}>
                Your New Beginning.
              </span>
            </h1>
            
            {/* Subheading - Enhanced readability */}
            <p className="text-xl sm:text-2xl text-slate-100 mb-12 max-w-3xl mx-auto leading-relaxed drop-shadow-lg animate-in fade-in slide-in-from-bottom duration-1000 delay-200" style={{textShadow: '0 2px 10px rgba(0,0,0,0.8)'}}>
              <span className="text-amber-400 font-bold">{stats.units}+ no-fee apartments</span> in NYC and Northern New Jersey.
              <span className="block mt-3 text-lg text-slate-200 font-medium">No broker fees. No hidden costs. Just your perfect home.</span>
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

            {/* Stats Bar - City lights inspired */}
            <div className="grid grid-cols-3 gap-8 max-w-3xl mx-auto glass-window border border-amber-500/20 rounded-2xl p-10 backdrop-blur-md shadow-2xl shadow-amber-500/10 animate-in fade-in slide-in-from-bottom duration-1000 delay-500">
              <div className="text-center">
                <div className="text-5xl font-bold warm-gradient-text mb-2">{stats.units}+</div>
                <div className="text-sm text-slate-400 uppercase tracking-wider">No-Fee Homes</div>
              </div>
              <div className="text-center border-x border-slate-700/50">
                <div className="text-5xl font-bold warm-gradient-text mb-2">{stats.buildings}+</div>
                <div className="text-sm text-slate-400 uppercase tracking-wider">NYC Buildings</div>
              </div>
              <div className="text-center">
                <div className="text-5xl font-bold warm-gradient-text mb-2">$0</div>
                <div className="text-sm text-slate-400 uppercase tracking-wider">Broker Fees</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How to Find Apartments - Quick Guide */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-slate-800/50 border-y border-amber-500/10">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-5 py-2 bg-amber-500/10 border border-amber-500/30 rounded-full mb-6">
            <Search className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-semibold text-amber-400">Start Your Search Now</span>
          </div>
          
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Ready to Find Your Apartment?
          </h2>
          <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto">
            Sign up free to access <span className="warm-gradient-text font-semibold">208+ verified no-fee listings</span>. 
            Use our smart filters to search by neighborhood, price, bedrooms, and more.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-6">
            <Button
              onClick={() => setShowSignupModal(true)}
              size="lg"
              className="warm-gradient hover:shadow-xl hover:shadow-amber-500/40 text-slate-900 font-bold px-10 py-6 text-lg"
            >
              Browse All Apartments
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <span className="text-slate-400 text-sm">or</span>
            <Button
              onClick={handleGetStarted}
              variant="outline"
              size="lg"
              className="border-amber-500/30 text-amber-500 hover:bg-slate-700 px-10 py-6 text-lg font-semibold"
            >
              Sign In to Dashboard
            </Button>
          </div>
          
          <p className="text-sm text-slate-500">
            Questions? Contact us at{' '}
            <a href="mailto:placesfirm@gmail.com" className="text-amber-500 hover:text-amber-400 font-medium">
              placesfirm@gmail.com
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
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            {/* Brand */}
            <div className="text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg warm-gradient flex items-center justify-center shadow-lg shadow-amber-500/20">
                  <Building2 className="w-6 h-6 text-slate-900" />
                </div>
                <span className="text-xl font-semibold warm-gradient-text">NoFeesApts.com</span>
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
