import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import { Mail, Copy, Check, Facebook, Twitter, MessageCircle } from 'lucide-react';

const ShareDialog = ({ open, onOpenChange, unit, building }) => {
  const [emailTo, setEmailTo] = useState('');
  const [emailMessage, setEmailMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [copied, setCopied] = useState(false);

  // Generate share URL
  const shareUrl = `${window.location.origin}/unit/${unit.id}`;
  
  // Generate share text
  const shareText = `Check out this no-fee apartment at ${building?.name || 'NYC'}! ${unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`} for $${unit.rent.toLocaleString()}/month`;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    toast.success('Link copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleEmailShare = async () => {
    if (!emailTo) {
      toast.error('Please enter an email address');
      return;
    }

    setIsSending(true);
    try {
      await axios.post(`${API}/share-unit`, {
        unit_id: unit.id,
        recipient_email: emailTo,
        message: emailMessage
      }, { withCredentials: true });

      toast.success('Email sent successfully!');
      setEmailTo('');
      setEmailMessage('');
      onOpenChange(false);
    } catch (error) {
      toast.error('Failed to send email');
    } finally {
      setIsSending(false);
    }
  };

  const handleSocialShare = (platform) => {
    const encodedUrl = encodeURIComponent(shareUrl);
    const encodedText = encodeURIComponent(shareText);
    
    let shareLink = '';
    
    switch(platform) {
      case 'facebook':
        shareLink = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
        break;
      case 'twitter':
        shareLink = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedText}`;
        break;
      case 'whatsapp':
        shareLink = `https://wa.me/?text=${encodedText}%20${encodedUrl}`;
        break;
      default:
        return;
    }
    
    window.open(shareLink, '_blank', 'width=600,height=400');
    toast.success(`Sharing on ${platform}!`);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-slate-800 border-amber-500/20 text-slate-100 max-w-md">
        <DialogHeader>
          <DialogTitle className="text-slate-100">Share This Apartment</DialogTitle>
          <DialogDescription className="text-slate-300">
            Share this listing with friends and family
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Copy Link */}
          <div className="space-y-2">
            <Label className="text-slate-200">Copy Link</Label>
            <div className="flex gap-2">
              <Input
                value={shareUrl}
                readOnly
                className="bg-slate-700/50 border-slate-600 text-slate-300"
              />
              <Button
                onClick={handleCopyLink}
                className="warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
          </div>

          {/* Email Share */}
          <div className="space-y-3 pt-2">
            <Label className="text-slate-200 flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Send via Email
            </Label>
            <div className="space-y-3">
              <div>
                <Label htmlFor="email-to" className="text-slate-300 text-sm">Recipient Email</Label>
                <Input
                  id="email-to"
                  type="email"
                  placeholder="friend@example.com"
                  value={emailTo}
                  onChange={(e) => setEmailTo(e.target.value)}
                  className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                />
              </div>
              <div>
                <Label htmlFor="email-message" className="text-slate-300 text-sm">Personal Message (Optional)</Label>
                <Textarea
                  id="email-message"
                  placeholder="I thought you might be interested in this apartment..."
                  value={emailMessage}
                  onChange={(e) => setEmailMessage(e.target.value)}
                  rows={3}
                  className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                />
              </div>
              <Button
                onClick={handleEmailShare}
                disabled={isSending}
                className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold"
              >
                {isSending ? 'Sending...' : 'Send Email'}
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ShareDialog;
