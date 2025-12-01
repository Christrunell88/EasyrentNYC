import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';
import { API } from '../App';
import { Building2 } from 'lucide-react';
import { trackLogin, trackSignup } from '../utils/analytics';

const Auth = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');

  // Process OAuth session_id from URL and check for admin mode
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const adminParam = searchParams.get('admin');
    if (adminParam === 'true') {
      setIsAdminMode(true);
    }

    const hash = location.hash;
    if (hash.includes('session_id')) {
      const params = new URLSearchParams(hash.substring(1));
      const sessionId = params.get('session_id');
      if (sessionId) {
        processOAuthSession(sessionId);
      }
    } else {
      // Check if already authenticated
      checkAuth();
    }
  }, [location]);

  const checkAuth = async () => {
    try {
      await axios.get(`${API}/auth/me`, { withCredentials: true });
      
      // Check if there's a redirect destination stored
      const redirectPath = sessionStorage.getItem('redirectAfterLogin');
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin');
        navigate(redirectPath);
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      // Not authenticated, stay on auth page
    }
  };

  const processOAuthSession = async (sessionId) => {
    setIsLoading(true);
    try {
      await axios.post(
        `${API}/auth/session`,
        {},
        {
          headers: { 'X-Session-ID': sessionId },
          withCredentials: true
        }
      );
      toast.success('Login successful!');
      
      // Check if there's a redirect destination stored
      const redirectPath = sessionStorage.getItem('redirectAfterLogin');
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin');
        navigate(redirectPath);
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('OAuth error:', error);
      toast.error('Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const redirectUrl = `${window.location.origin}/auth`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleEmailSignup = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.target);
    const data = {
      name: formData.get('name'),
      email: formData.get('email'),
      password: formData.get('password')
    };

    try {
      await axios.post(`${API}/auth/signup`, data, { withCredentials: true });
      toast.success('Account created successfully!');
      
      // Track signup event
      trackSignup('email');
      
      // Check if there's a redirect destination stored
      const redirectPath = sessionStorage.getItem('redirectAfterLogin');
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin');
        navigate(redirectPath);
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.target);
    const data = {
      email: formData.get('email'),
      password: formData.get('password')
    };

    try {
      await axios.post(`${API}/auth/login`, data, { withCredentials: true });
      toast.success('Login successful!');
      
      // Check if there's a redirect destination stored
      const redirectPath = sessionStorage.getItem('redirectAfterLogin');
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin');
        navigate(redirectPath);
      } else {
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!forgotEmail) {
      toast.error('Please enter your email');
      return;
    }

    setIsLoading(true);
    try {
      await axios.post(`${API}/auth/forgot-password`, { email: forgotEmail });
      toast.success('Password reset link sent! Check your email.');
      setShowForgotPassword(false);
      setForgotEmail('');
    } catch (error) {
      toast.error('Failed to send reset link');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <Card className="w-full max-w-md shadow-2xl border border-amber-500/20 bg-slate-800/90 backdrop-blur-sm">
        <CardHeader className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-2xl warm-gradient flex items-center justify-center shadow-lg shadow-amber-500/20">
              <Building2 className="w-10 h-10 text-slate-900" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold warm-gradient-text">
            {isAdminMode ? 'Admin Login' : 'Welcome to NoFeesApts.com'}
          </CardTitle>
          <CardDescription className="text-base text-slate-300">
            {isAdminMode ? 'Sign in to access the admin panel' : 'Sign in to find your perfect no-fee apartment'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="login" className="w-full">
            {!isAdminMode && (
              <TabsList className="grid w-full grid-cols-2 mb-6 bg-slate-700/50">
                <TabsTrigger value="login" data-testid="login-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Login</TabsTrigger>
                <TabsTrigger value="signup" data-testid="signup-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Sign Up</TabsTrigger>
              </TabsList>
            )}

            <TabsContent value="login" data-testid="login-content">
              <form onSubmit={handleEmailLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email" className="text-slate-200">Email</Label>
                  <Input
                    id="login-email"
                    name="email"
                    type="email"
                    placeholder="you@example.com"
                    defaultValue=""
                    required
                    data-testid="login-email-input"
                    className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password" className="text-slate-200">Password</Label>
                  <Input
                    id="login-password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    defaultValue=""
                    required
                    data-testid="login-password-input"
                    className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold"
                  disabled={isLoading}
                  data-testid="email-login-btn"
                >
                  {isLoading ? 'Logging in...' : (isAdminMode ? 'Admin Login' : 'Login with Email')}
                </Button>
                
                {!isAdminMode && (
                  <div className="text-center mt-2">
                    <button
                      type="button"
                      onClick={() => setShowForgotPassword(true)}
                      className="text-sm text-amber-500 hover:text-amber-400 transition-colors"
                    >
                      Forgot Password?
                    </button>
                  </div>
                )}
              </form>

              {!isAdminMode && (
                <>
                  <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-slate-600" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-slate-800 px-2 text-slate-400">Or continue with</span>
                    </div>
                  </div>

                  <Button
                    onClick={handleGoogleLogin}
                    variant="outline"
                    className="w-full border-2 border-slate-600 bg-slate-700/50 hover:bg-slate-700 text-slate-200"
                    data-testid="google-login-btn"
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
                </>
              )}
            </TabsContent>

            <TabsContent value="signup" data-testid="signup-content">
              <form onSubmit={handleEmailSignup} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signup-name" className="text-slate-200">Full Name</Label>
                  <Input
                    id="signup-name"
                    name="name"
                    type="text"
                    placeholder="John Doe"
                    required
                    data-testid="signup-name-input"
                    className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-email" className="text-slate-200">Email</Label>
                  <Input
                    id="signup-email"
                    name="email"
                    type="email"
                    placeholder="you@example.com"
                    required
                    data-testid="signup-email-input"
                    className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-password" className="text-slate-200">Password</Label>
                  <Input
                    id="signup-password"
                    name="password"
                    type="password"
                    placeholder="••••••••"
                    required
                    minLength={6}
                    data-testid="signup-password-input"
                    className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold"
                  disabled={isLoading}
                  data-testid="email-signup-btn"
                >
                  {isLoading ? 'Creating account...' : 'Sign Up with Email'}
                </Button>
              </form>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-slate-600" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-slate-800 px-2 text-slate-400">Or continue with</span>
                </div>
              </div>

              <Button
                onClick={handleGoogleLogin}
                variant="outline"
                className="w-full border-2 border-slate-600 bg-slate-700/50 hover:bg-slate-700 text-slate-200"
                data-testid="google-signup-btn"
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
            </TabsContent>
          </Tabs>

          <div className="mt-6 text-center text-sm">
            <button
              onClick={() => navigate('/')}
              className="text-amber-500 hover:text-amber-400 hover:underline"
              data-testid="back-home-btn"
            >
              Back to Home
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Forgot Password Dialog */}
      <Dialog open={showForgotPassword} onOpenChange={setShowForgotPassword}>
        <DialogContent className="bg-slate-800 border-amber-500/20 text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-slate-100">Reset Your Password</DialogTitle>
            <DialogDescription className="text-slate-300">
              Enter your email address and we'll send you a link to reset your password.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="forgot-email" className="text-slate-200">Email</Label>
              <Input
                id="forgot-email"
                type="email"
                placeholder="you@example.com"
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
              />
            </div>
            <div className="flex gap-3">
              <Button
                onClick={() => setShowForgotPassword(false)}
                variant="outline"
                className="flex-1 border-slate-600 text-slate-200 hover:bg-slate-700"
              >
                Cancel
              </Button>
              <Button
                onClick={handleForgotPassword}
                disabled={isLoading}
                className="flex-1 warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold"
              >
                {isLoading ? 'Sending...' : 'Send Reset Link'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Auth;
