import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Check, Heart, Eye, Calendar, Bell, Search, Shield, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import axios from '../utils/axiosConfig';
import { API } from '../App';

const SignupModal = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: ''
  });

  const benefits = [
    {
      icon: Eye,
      title: 'See Full Apartment Listings',
      description: 'Access complete details, photos, and amenities for every unit'
    },
    {
      icon: Heart,
      title: 'Save Your Favorites',
      description: 'Create a personalized list of apartments you love'
    },
    {
      icon: Calendar,
      title: 'Schedule Viewings',
      description: 'Book apartment tours directly from the site'
    },
    {
      icon: Bell,
      title: 'Get Instant Alerts',
      description: 'Be the first to know when new no-fee apartments are listed'
    },
    {
      icon: Search,
      title: 'Advanced Filters',
      description: 'Search by neighborhood, price, bedrooms, and more'
    },
    {
      icon: Shield,
      title: 'Verified Listings',
      description: 'All apartments verified for no broker fees'
    }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await axios.post(`${API}/auth/signup`, formData, { withCredentials: true });
      toast.success('Account created successfully!');
      onClose();
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignup = () => {
    const redirectUrl = `${window.location.origin}/auth`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/90 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-800 rounded-2xl shadow-2xl border border-amber-500/20">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-10 h-10 rounded-full bg-slate-700 hover:bg-slate-600 flex items-center justify-center transition-colors z-10"
        >
          <X className="w-5 h-5 text-slate-300" />
        </button>

        <div className="grid md:grid-cols-2 gap-8 p-8">
          {/* Left Side - Benefits */}
          <div className="space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-6 h-6 text-amber-500" />
                <h2 className="text-3xl font-bold warm-gradient-text">Join NoFeesApts</h2>
              </div>
              <p className="text-slate-300 text-lg">Your gateway to no-fee apartments in NYC</p>
            </div>

            <div className="space-y-4">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex gap-3 items-start">
                  <div className="w-10 h-10 rounded-lg warm-gradient flex items-center justify-center flex-shrink-0 shadow-lg shadow-amber-500/20">
                    <benefit.icon className="w-5 h-5 text-slate-900" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-100">{benefit.title}</h3>
                    <p className="text-sm text-slate-400">{benefit.description}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-4 border-t border-slate-700">
              <div className="flex items-center gap-2 text-amber-500 mb-2">
                <Check className="w-5 h-5" />
                <span className="font-semibold">100% Free Forever</span>
              </div>
              <p className="text-sm text-slate-400">No hidden fees, no credit card required</p>
            </div>
          </div>

          {/* Right Side - Signup Form */}
          <div className="space-y-6">
            <div className="text-center md:text-left">
              <h3 className="text-2xl font-bold text-slate-100 mb-2">Create Your Free Account</h3>
              <p className="text-slate-400">Start finding your perfect apartment today</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="modal-name" className="text-slate-200">Full Name</Label>
                <Input
                  id="modal-name"
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="modal-email" className="text-slate-200">Email</Label>
                <Input
                  id="modal-email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="modal-password" className="text-slate-200">Password</Label>
                <Input
                  id="modal-password"
                  type="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  minLength={6}
                  className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                />
                <p className="text-xs text-slate-500">At least 6 characters</p>
              </div>

              <Button
                type="submit"
                className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold py-6 text-lg"
                disabled={isLoading}
              >
                {isLoading ? 'Creating Account...' : 'Sign Up Free'}
              </Button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-slate-600" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-slate-800 px-2 text-slate-400">Or continue with</span>
              </div>
            </div>

            <Button
              onClick={handleGoogleSignup}
              variant="outline"
              className="w-full border-2 border-slate-600 bg-slate-700/50 hover:bg-slate-700 text-slate-200"
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Continue with Google
            </Button>

            <p className="text-xs text-center text-slate-500">
              Already have an account?{' '}
              <button
                onClick={() => {
                  onClose();
                  navigate('/auth');
                }}
                className="text-amber-500 hover:text-amber-400 font-medium"
              >
                Sign In
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupModal;
