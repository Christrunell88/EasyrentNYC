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
    // Check if user has already submitted
    const hasSubmitted = localStorage.getItem('emailCaptureSubmitted');
    if (hasSubmitted) return;

    // Check if dismissed - respect 30-day cool-off period
    const dismissedTime = localStorage.getItem('emailCaptureDismissedTime');
    if (dismissedTime) {
      const daysSinceDismissed = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60 * 24);
      if (daysSinceDismissed < 30) return; // Don't show for 30 days after dismiss
    }

    // Check session - only show once per session
    const shownThisSession = sessionStorage.getItem('emailCaptureShownThisSession');
    if (shownThisSession) return;

    // Count page views in this session
    const pageViews = parseInt(sessionStorage.getItem('pageViewCount') || '0') + 1;
    sessionStorage.setItem('pageViewCount', pageViews.toString());

    // Only show after user has viewed at least 3 pages (showing genuine interest)
    if (pageViews < 3) return;

    // Show modal after 60 seconds of being on the page (user is engaged)
    const timer = setTimeout(() => {
      // Double-check they haven't navigated away
      if (document.visibilityState === 'visible') {
        setOpen(true);
        sessionStorage.setItem('emailCaptureShownThisSession', 'true');
      }
    }, 60000); // 60 seconds - more respectful

    return () => {
      clearTimeout(timer);
    };
  }, []);

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
    localStorage.setItem('emailCaptureDismissedTime', Date.now().toString());
    sessionStorage.setItem('emailCaptureShownThisSession', 'true');
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      if (!isOpen) handleDismiss();
      setOpen(isOpen);
    }}>
      <DialogContent className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white max-w-md p-8 rounded-none">
        <button
          onClick={handleDismiss}
          className="absolute right-4 top-4 p-1.5 bg-[#0a0a0a] border border-[#D4AF37]/20 opacity-70 transition-opacity hover:opacity-100 hover:border-[#D4AF37] focus:outline-none"
        >
          <X className="h-4 w-4 text-[#D4AF37]" />
          <span className="sr-only">Close</span>
        </button>

        <DialogHeader>
          <div className="mx-auto mb-4 h-14 w-14 border border-[#D4AF37]/30 bg-[#D4AF37]/10 flex items-center justify-center">
            <Bell className="h-7 w-7 text-[#D4AF37]" />
          </div>
          <DialogTitle className="text-white text-center text-2xl font-philosopher font-bold">
            Get New Listing Alerts
          </DialogTitle>
          <DialogDescription className="text-[#888888] text-center pt-2 text-base font-philosopher">
            Be the first to know when new luxury no-fee apartments become available.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="capture-email" className="text-[#F5F5F5] flex items-center gap-2 text-sm font-philosopher">
              <Mail className="w-4 h-4 text-[#D4AF37]" />
              Email Address
            </Label>
            <Input
              id="capture-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-[#0a0a0a] border border-[#D4AF37]/20 text-white placeholder:text-[#666666] focus:border-[#D4AF37] focus:ring-0 rounded-none py-5 font-philosopher"
              required
            />
          </div>

          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold py-6 text-base rounded-none tracking-wide"
          >
            {isSubmitting ? 'SUBSCRIBING...' : 'SUBSCRIBE'}
          </Button>

          <p className="text-xs text-[#666666] text-center font-philosopher">
            No spam. Unsubscribe anytime.
          </p>
        </form>

        <button
          onClick={handleDismiss}
          className="text-sm text-[#888888] hover:text-[#D4AF37] text-center w-full transition-colors font-philosopher"
        >
          Maybe later
        </button>
      </DialogContent>
    </Dialog>
  );
};

export default EmailCaptureModal;
