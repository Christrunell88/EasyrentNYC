import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import Logo from '@/components/Logo';

const ResetPassword = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const tokenParam = searchParams.get('token');
    if (!tokenParam) {
      toast.error('Invalid reset link');
      navigate('/auth');
    } else {
      setToken(tokenParam);
    }
  }, [searchParams, navigate]);

  const handleResetPassword = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);
    try {
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: newPassword
      });
      toast.success('Password reset successful! Please log in.');
      navigate('/auth');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <Card className="w-full max-w-md shadow-2xl border border-amber-500/20 bg-slate-800/90 backdrop-blur-sm">
        <CardHeader className="text-center space-y-4">
          <div className="flex justify-center">
            <Logo size="large" />
          </div>
          <CardTitle className="text-3xl font-bold warm-gradient-text">
            Reset Your Password
          </CardTitle>
          <CardDescription className="text-base text-slate-300">
            Enter your new password below
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-password" className="text-slate-200">New Password</Label>
              <Input
                id="new-password"
                type="password"
                placeholder="••••••••"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password" className="text-slate-200">Confirm Password</Label>
              <Input
                id="confirm-password"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
              />
            </div>
            <Button
              type="submit"
              className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold"
              disabled={isLoading}
            >
              {isLoading ? 'Resetting...' : 'Reset Password'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm">
            <button
              onClick={() => navigate('/auth')}
              className="text-amber-500 hover:text-amber-400 hover:underline"
            >
              Back to Login
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResetPassword;
