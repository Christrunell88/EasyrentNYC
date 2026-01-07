import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import { trackLogin, trackSignup } from '../utils/analytics';
import useAuthStore from '../store/authStore';

const Auth = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');

  const user = useAuthStore((state) => state.user);
  const loading = useAuthStore((state) => state.loading);
  const login = useAuthStore((state) => state.login);
  const signup = useAuthStore((state) => state.signup);
  const processSession = useAuthStore((state) => state.processSession);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const adminParam = searchParams.get('admin');
    if (adminParam === 'true') {
      setIsAdminMode(true);
    }
  }, [location.search]);

  const handleOAuthSession = useCallback(async (sessionId) => {
    const result = await processSession(sessionId);
    
    if (result.success) {
      toast.success('Login successful!');
      trackLogin('google');
      
      if (result.user.is_admin) {
        navigate('/admin');
      } else {
        const redirectPath = sessionStorage.getItem('redirectAfterLogin');
        sessionStorage.removeItem('redirectAfterLogin');
        navigate(redirectPath || '/dashboard');
      }
    } else {
      toast.error(result.error || 'Authentication failed');
    }
  }, [processSession, navigate]);

  useEffect(() => {
    const hash = location.hash;
    if (hash.includes('session_id')) {
      const params = new URLSearchParams(hash.substring(1));
      const sessionId = params.get('session_id');
      if (sessionId) {
        window.history.replaceState(null, '', '/auth');
        handleOAuthSession(sessionId);
      }
    } else if (user) {
      if (user.is_admin) {
        navigate('/admin');
      } else {
        const redirectPath = sessionStorage.getItem('redirectAfterLogin');
        sessionStorage.removeItem('redirectAfterLogin');
        navigate(redirectPath || '/dashboard');
      }
    }
  }, [location.hash, user, navigate, handleOAuthSession]);

  const handleGoogleLogin = () => {
    trackLogin('google');
    const redirectUrl = `${window.location.origin}/auth`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleEmailSignup = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const name = formData.get('name');
    const email = formData.get('email');
    const password = formData.get('password');

    const result = await signup(email, password, name);

    if (result.success) {
      toast.success('Account created successfully!');
      trackSignup('email');
    } else {
      toast.error(result.error || 'Signup failed');
    }
  };

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const email = formData.get('email');
    const password = formData.get('password');

    const result = await login(email, password);

    if (result.success) {
      toast.success('Login successful!');
      trackLogin('email');
    } else {
      toast.error(result.error || 'Login failed');
    }
  };

  const handleForgotPassword = async () => {
    if (!forgotEmail) {
      toast.error('Please enter your email');
      return;
    }

    try {
      await axios.post(`${API}/auth/forgot-password`, { email: forgotEmail });
      toast.success('Password reset link sent! Check your email.');
      setShowForgotPassword(false);
      setForgotEmail('');
    } catch (error) {
      toast.error('Failed to send reset link');
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
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0a] px-4 relative overflow-hidden">
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#D4AF37]/5 via-transparent to-transparent pointer-events-none" />
      
      <div className="w-full max-w-sm relative z-10">
        {/* Luxury Header */}
        <div className="text-center mb-10">
          <div className="w-12 h-px bg-[#D4AF37] mx-auto mb-6" />
          <h1 className="text-2xl font-philosopher font-bold text-white tracking-wide mb-2">
            {isAdminMode ? 'Admin Access' : 'Welcome'}
          </h1>
          <p className="text-[#888888] text-sm font-philosopher">
            {isAdminMode ? 'Administrative portal' : 'Access our curated collection'}
          </p>
          {!isAdminMode && (
            <div className="mt-4 inline-flex items-center gap-2 bg-[#4ade80]/10 border border-[#4ade80]/30 px-4 py-2 rounded-full">
              <span className="w-2 h-2 bg-[#4ade80] rounded-full animate-pulse"></span>
              <span className="text-[#4ade80] text-xs font-semibold tracking-wide">FREE FOREVER • No Credit Card</span>
            </div>
          )}
        </div>

        {/* Auth Form */}
        <Tabs defaultValue="signup" className="w-full">
          {!isAdminMode && (
            <TabsList className="grid w-full grid-cols-2 mb-8 bg-[#1a1a1a] p-1 rounded-none border border-[#D4AF37]/20">
              <TabsTrigger 
                value="signup" 
                data-testid="signup-tab" 
                className="rounded-none font-philosopher tracking-wide data-[state=active]:bg-[#D4AF37] data-[state=active]:text-[#0a0a0a] data-[state=active]:font-bold text-[#888888]"
              >
                Sign Up
              </TabsTrigger>
              <TabsTrigger 
                value="login" 
                data-testid="login-tab" 
                className="rounded-none font-philosopher tracking-wide data-[state=active]:bg-[#D4AF37] data-[state=active]:text-[#0a0a0a] data-[state=active]:font-bold text-[#888888]"
              >
                Login
              </TabsTrigger>
            </TabsList>
          )}

          <TabsContent value="login" data-testid="login-content">
            <form onSubmit={handleEmailLogin} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="login-email" className="text-[#F5F5F5] text-sm font-philosopher tracking-wide">Email</Label>
                <Input
                  id="login-email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  required
                  data-testid="login-email-input"
                  className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white placeholder:text-[#666666] focus:border-[#D4AF37] focus:ring-0 rounded-none py-5 font-philosopher"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="login-password" className="text-[#F5F5F5] text-sm font-philosopher tracking-wide">Password</Label>
                <Input
                  id="login-password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  required
                  data-testid="login-password-input"
                  className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white placeholder:text-[#666666] focus:border-[#D4AF37] focus:ring-0 rounded-none py-5 font-philosopher"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold py-5 rounded-none tracking-[0.1em] transition-all duration-300"
                disabled={loading}
                data-testid="email-login-btn"
              >
                {loading ? 'LOGGING IN...' : 'LOGIN'}
              </Button>
              
              {!isAdminMode && (
                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => setShowForgotPassword(true)}
                    className="text-sm text-[#888888] hover:text-[#D4AF37] font-philosopher transition-colors"
                  >
                    Forgot password?
                  </button>
                </div>
              )}
            </form>

            {!isAdminMode && (
              <>
                <div className="relative my-8">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t border-[#D4AF37]/20" />
                  </div>
                  <div className="relative flex justify-center text-xs">
                    <span className="bg-[#0a0a0a] px-4 text-[#666666] font-philosopher">or</span>
                  </div>
                </div>

                <Button
                  onClick={handleGoogleLogin}
                  variant="outline"
                  className="w-full border border-[#D4AF37]/30 bg-transparent hover:bg-[#D4AF37]/10 hover:border-[#D4AF37] text-[#F5F5F5] font-philosopher py-5 rounded-none tracking-wide transition-all duration-300"
                  data-testid="google-login-btn"
                >
                  <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                    <path fill="#D4AF37" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#D4AF37" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#D4AF37" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#D4AF37" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </Button>
              </>
            )}
          </TabsContent>

          <TabsContent value="signup" data-testid="signup-content">
            <form onSubmit={handleEmailSignup} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="signup-name" className="text-[#F5F5F5] text-sm font-philosopher tracking-wide">Full Name</Label>
                <Input
                  id="signup-name"
                  name="name"
                  type="text"
                  placeholder="John Doe"
                  required
                  data-testid="signup-name-input"
                  className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white placeholder:text-[#666666] focus:border-[#D4AF37] focus:ring-0 rounded-none py-5 font-philosopher"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signup-email" className="text-[#F5F5F5] text-sm font-philosopher tracking-wide">Email</Label>
                <Input
                  id="signup-email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  required
                  data-testid="signup-email-input"
                  className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white placeholder:text-[#666666] focus:border-[#D4AF37] focus:ring-0 rounded-none py-5 font-philosopher"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signup-password" className="text-[#F5F5F5] text-sm font-philosopher tracking-wide">Password</Label>
                <Input
                  id="signup-password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  required
                  minLength={6}
                  data-testid="signup-password-input"
                  className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white placeholder:text-[#666666] focus:border-[#D4AF37] focus:ring-0 rounded-none py-5 font-philosopher"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold py-5 rounded-none tracking-[0.1em] transition-all duration-300"
                disabled={loading}
                data-testid="email-signup-btn"
              >
                {loading ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT'}
              </Button>
            </form>

            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-[#D4AF37]/20" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-[#0a0a0a] px-4 text-[#666666] font-philosopher">or</span>
              </div>
            </div>

            <Button
              onClick={handleGoogleLogin}
              variant="outline"
              className="w-full border border-[#D4AF37]/30 bg-transparent hover:bg-[#D4AF37]/10 hover:border-[#D4AF37] text-[#F5F5F5] font-philosopher py-5 rounded-none tracking-wide transition-all duration-300"
              data-testid="google-signup-btn"
            >
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                <path fill="#D4AF37" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#D4AF37" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#D4AF37" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#D4AF37" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </Button>
          </TabsContent>
        </Tabs>

        {/* Back Link */}
        <div className="mt-10 text-center">
          <div className="w-8 h-px bg-[#D4AF37]/30 mx-auto mb-4" />
          <button
            onClick={() => navigate('/')}
            className="text-sm text-[#888888] hover:text-[#D4AF37] font-philosopher tracking-wide transition-colors"
            data-testid="back-home-btn"
          >
            ← Back to Home
          </button>
        </div>
      </div>

      {/* Forgot Password Dialog */}
      <Dialog open={showForgotPassword} onOpenChange={setShowForgotPassword}>
        <DialogContent className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white max-w-sm rounded-none">
          <DialogHeader>
            <DialogTitle className="text-white text-xl font-philosopher">Reset Password</DialogTitle>
            <DialogDescription className="text-[#888888] font-philosopher">
              Enter your email and we'll send you a reset link.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-5 py-2">
            <div className="space-y-2">
              <Label htmlFor="forgot-email" className="text-[#F5F5F5] text-sm font-philosopher">Email</Label>
              <Input
                id="forgot-email"
                type="email"
                placeholder="you@example.com"
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                className="bg-[#0a0a0a] border border-[#D4AF37]/20 text-white placeholder:text-[#666666] focus:border-[#D4AF37] focus:ring-0 rounded-none py-5 font-philosopher"
              />
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => setShowForgotPassword(false)}
                variant="outline"
                className="flex-1 border border-[#D4AF37]/30 text-[#F5F5F5] hover:bg-[#D4AF37]/10 rounded-none font-philosopher"
              >
                Cancel
              </Button>
              <Button
                onClick={handleForgotPassword}
                disabled={loading}
                className="flex-1 bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold rounded-none"
              >
                {loading ? 'Sending...' : 'Send Link'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Auth;
