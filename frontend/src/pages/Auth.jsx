import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';
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
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-lg text-slate-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4">
      <div className="w-full max-w-sm">
        {/* Simple Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            {isAdminMode ? 'Admin Login' : 'Unlock thousands of apartments'}
          </h1>
        </div>

        {/* Auth Form */}
        <Tabs defaultValue="signup" className="w-full">
          {!isAdminMode && (
            <TabsList className="grid w-full grid-cols-2 mb-6 bg-slate-100 p-1 rounded-lg">
              <TabsTrigger 
                value="signup" 
                data-testid="signup-tab" 
                className="rounded-md data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-sm"
              >
                Sign Up
              </TabsTrigger>
              <TabsTrigger 
                value="login" 
                data-testid="login-tab" 
                className="rounded-md data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-sm"
              >
                Login
              </TabsTrigger>
            </TabsList>
          )}

          <TabsContent value="login" data-testid="login-content">
            <form onSubmit={handleEmailLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="login-email" className="text-slate-700 text-sm">Email</Label>
                <Input
                  id="login-email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  required
                  data-testid="login-email-input"
                  className="bg-slate-50 border-0 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900 rounded-lg py-5"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="login-password" className="text-slate-700 text-sm">Password</Label>
                <Input
                  id="login-password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  required
                  data-testid="login-password-input"
                  className="bg-slate-50 border-0 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900 rounded-lg py-5"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium py-5 rounded-lg"
                disabled={loading}
                data-testid="email-login-btn"
              >
                {loading ? 'Logging in...' : 'Login'}
              </Button>
              
              {!isAdminMode && (
                <div className="text-center">
                  <button
                    type="button"
                    onClick={() => setShowForgotPassword(true)}
                    className="text-sm text-slate-500 hover:text-slate-900"
                  >
                    Forgot password?
                  </button>
                </div>
              )}
            </form>

            {!isAdminMode && (
              <>
                <div className="relative my-6">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t border-slate-200" />
                  </div>
                  <div className="relative flex justify-center text-xs">
                    <span className="bg-white px-3 text-slate-400">or</span>
                  </div>
                </div>

                <Button
                  onClick={handleGoogleLogin}
                  variant="outline"
                  className="w-full border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-medium py-5 rounded-lg"
                  data-testid="google-login-btn"
                >
                  <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </Button>
              </>
            )}
          </TabsContent>

          <TabsContent value="signup" data-testid="signup-content">
            <form onSubmit={handleEmailSignup} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="signup-name" className="text-slate-700 text-sm">Full Name</Label>
                <Input
                  id="signup-name"
                  name="name"
                  type="text"
                  placeholder="John Doe"
                  required
                  data-testid="signup-name-input"
                  className="bg-slate-50 border-0 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900 rounded-lg py-5"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signup-email" className="text-slate-700 text-sm">Email</Label>
                <Input
                  id="signup-email"
                  name="email"
                  type="email"
                  placeholder="you@example.com"
                  required
                  data-testid="signup-email-input"
                  className="bg-slate-50 border-0 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900 rounded-lg py-5"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signup-password" className="text-slate-700 text-sm">Password</Label>
                <Input
                  id="signup-password"
                  name="password"
                  type="password"
                  placeholder="••••••••"
                  required
                  minLength={6}
                  data-testid="signup-password-input"
                  className="bg-slate-50 border-0 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900 rounded-lg py-5"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-slate-900 hover:bg-slate-800 text-white font-medium py-5 rounded-lg"
                disabled={loading}
                data-testid="email-signup-btn"
              >
                {loading ? 'Creating account...' : 'Sign Up'}
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-white px-3 text-slate-400">or</span>
              </div>
            </div>

            <Button
              onClick={handleGoogleLogin}
              variant="outline"
              className="w-full border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-medium py-5 rounded-lg"
              data-testid="google-signup-btn"
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </Button>
          </TabsContent>
        </Tabs>

        {/* Back Link */}
        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/')}
            className="text-sm text-slate-500 hover:text-slate-900"
            data-testid="back-home-btn"
          >
            ← Back to Home
          </button>
        </div>
      </div>

      {/* Forgot Password Dialog */}
      <Dialog open={showForgotPassword} onOpenChange={setShowForgotPassword}>
        <DialogContent className="bg-white border-slate-200 text-slate-900 max-w-sm rounded-2xl">
          <DialogHeader>
            <DialogTitle className="text-slate-900 text-xl">Reset Password</DialogTitle>
            <DialogDescription className="text-slate-500">
              Enter your email and we'll send you a reset link.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="forgot-email" className="text-slate-700 text-sm">Email</Label>
              <Input
                id="forgot-email"
                type="email"
                placeholder="you@example.com"
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                className="bg-slate-50 border-0 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900 rounded-lg py-5"
              />
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => setShowForgotPassword(false)}
                variant="outline"
                className="flex-1 border-slate-200 text-slate-700 hover:bg-slate-50 rounded-lg"
              >
                Cancel
              </Button>
              <Button
                onClick={handleForgotPassword}
                disabled={loading}
                className="flex-1 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-lg"
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
