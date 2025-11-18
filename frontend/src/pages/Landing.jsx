import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Building2, Search, Heart, Shield } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const Landing = () => {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-full shadow-sm mb-8">
              <Building2 className="w-5 h-5 text-indigo-600" />
              <span className="text-sm font-medium text-gray-700">NYC & Northern NJ</span>
            </div>
            
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 mb-6">
              Find Your Perfect
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-purple-600">
                No-Fee Apartment
              </span>
            </h1>
            
            <p className="text-lg sm:text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
              Search hundreds of no-fee apartments in NYC and Northern New Jersey. 
              Save thousands on broker fees and find your dream home.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                data-testid="get-started-btn"
                onClick={handleGetStarted}
                size="lg"
                className="text-lg px-8 py-6 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all"
              >
                <Search className="w-5 h-5 mr-2" />
                Start Searching
              </Button>
              
              {!isAuthenticated && (
                <Button
                  data-testid="signin-btn"
                  onClick={() => navigate('/auth')}
                  variant="outline"
                  size="lg"
                  className="text-lg px-8 py-6 border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 rounded-full"
                >
                  Sign In
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-3xl sm:text-4xl font-bold text-center text-gray-900 mb-16">
          Why Choose NoFeesApts.com?
        </h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all">
            <div className="w-14 h-14 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
              <Building2 className="w-8 h-8 text-indigo-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Verified Listings</h3>
            <p className="text-gray-600">
              All apartments are verified and updated regularly from official building websites.
            </p>
          </div>
          
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all">
            <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
              <Heart className="w-8 h-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">Save Favorites</h3>
            <p className="text-gray-600">
              Keep track of apartments you love and get notified about price changes.
            </p>
          </div>
          
          <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all">
            <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
              <Shield className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-3">100% No Fee</h3>
            <p className="text-gray-600">
              Every listing is genuinely no-fee. Save thousands on broker fees.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-3xl p-12 sm:p-16 text-center shadow-2xl">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to Find Your Dream Apartment?
          </h2>
          <p className="text-xl text-indigo-100 mb-8 max-w-2xl mx-auto">
            Join thousands of renters who found their perfect no-fee apartment.
          </p>
          <Button
            data-testid="cta-start-btn"
            onClick={handleGetStarted}
            size="lg"
            className="text-lg px-10 py-6 bg-white text-indigo-600 hover:bg-gray-50 rounded-full shadow-lg hover:shadow-xl transition-all"
          >
            Get Started Free
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Landing;
