import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import { Mail, X, Bell } from 'lucide-react';

const EmailCaptureModal = () => {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Check if user has already submitted or dismissed
    const hasSubmitted = localStorage.getItem('emailCaptureSubmitted');
    const hasDismissed = localStorage.getItem('emailCaptureDismissed');
    const dismissedTime = localStorage.getItem('emailCaptureDismissedTime');

    // Don't show if already submitted
    if (hasSubmitted) return;

    // If dismissed, check if 7 days have passed
    if (hasDismissed && dismissedTime) {
      const daysSinceDismissed = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 7) return; // Don't show for 7 days after dismiss
    }

    // Show modal after 30 seconds
    const timer = setTimeout(() => {
      setOpen(true);
    }, 30000); // 30 seconds

    // Or show on scroll (if user scrolls 50% down the page)
    const handleScroll = () => {
      const scrollPercent = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
      if (scrollPercent > 50 && !hasSubmitted && !open) {
        setOpen(true);
      }
    };

    window.addEventListener('scroll', handleScroll);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('scroll', handleScroll);
    };
  }, [open]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!email || !email.includes('@')) {
      toast.error('Please enter a valid email address');
      return;
    }

    setIsSubmitting(true);
    try {
      await axios.post(`${API}/subscribe`, {
        email: email
      });

      toast.success('🎉 Success! You\'ll get alerts for new apartments!');
      localStorage.setItem('emailCaptureSubmitted', 'true');
      setEmail('');
      setOpen(false);
    } catch (error) {
      if (error.response?.status === 400) {
        toast.error('This email is already subscribed!');
      } else {
        toast.error('Failed to subscribe. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDismiss = () => {
    localStorage.setItem('emailCaptureDismissed', 'true');
    localStorage.setItem('emailCaptureDismissedTime', Date.now().toString());
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="bg-slate-800 border-amber-500/20 text-slate-100 max-w-md">
        <button
          onClick={handleDismiss}
          className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-slate-900 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:pointer-events-none"
        >
          <X className="h-4 w-4 text-slate-400" />
          <span className="sr-only">Close</span>
        </button>

        <DialogHeader>
          <div className="mx-auto mb-4 h-12 w-12 rounded-full warm-gradient flex items-center justify-center">
            <Bell className="h-6 w-6 text-slate-900" />
          </div>
          <DialogTitle className="text-slate-100 text-center text-2xl">
            Never Miss a No-Fee Apartment!
          </DialogTitle>
          <DialogDescription className="text-slate-300 text-center pt-2">
            Get instant email alerts when new apartments are posted. Be the first to know!
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="capture-email" className="text-slate-200 flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Your Email Address
            </Label>
            <Input
              id="capture-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
              required
            />
          </div>

          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold py-6 text-base"
          >
            {isSubmitting ? 'Subscribing...' : '🔔 Get Instant Alerts'}
          </Button>

          <p className="text-xs text-slate-400 text-center">
            No spam. Unsubscribe anytime. We respect your privacy.
          </p>
        </form>

        <button
          onClick={handleDismiss}
          className="text-sm text-slate-400 hover:text-slate-300 text-center w-full"
        >
          Maybe later
        </button>
      </DialogContent>
    </Dialog>
  );
};

export default EmailCaptureModal;
