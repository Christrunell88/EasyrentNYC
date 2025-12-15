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

      toast.success('Success! You\'ll get alerts for new apartments!');
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
      <DialogContent className="bg-white border-slate-200 text-slate-900 max-w-md p-8 rounded-2xl">
        <button
          onClick={handleDismiss}
          className="absolute right-4 top-4 rounded-full p-1.5 bg-slate-100 opacity-70 transition-opacity hover:opacity-100 focus:outline-none"
        >
          <X className="h-4 w-4 text-slate-600" />
          <span className="sr-only">Close</span>
        </button>

        <DialogHeader>
          <div className="mx-auto mb-4 h-14 w-14 rounded-full bg-slate-900 flex items-center justify-center">
            <Bell className="h-7 w-7 text-white" />
          </div>
          <DialogTitle className="text-slate-900 text-center text-2xl font-bold">
            Get New Listing Alerts
          </DialogTitle>
          <DialogDescription className="text-slate-500 text-center pt-2 text-base">
            Be the first to know when new no-fee apartments become available.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="capture-email" className="text-slate-700 flex items-center gap-2 text-sm font-medium">
              <Mail className="w-4 h-4" />
              Email Address
            </Label>
            <Input
              id="capture-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-slate-50 border-0 text-slate-900 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900 rounded-xl py-5"
              required
            />
          </div>

          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold py-6 text-base rounded-xl"
          >
            {isSubmitting ? 'Subscribing...' : 'Subscribe'}
          </Button>

          <p className="text-xs text-slate-400 text-center">
            No spam. Unsubscribe anytime.
          </p>
        </form>

        <button
          onClick={handleDismiss}
          className="text-sm text-slate-400 hover:text-slate-600 text-center w-full transition-colors"
        >
          Maybe later
        </button>
      </DialogContent>
    </Dialog>
  );
};

export default EmailCaptureModal;
