import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import { Mail, Copy, Check, Facebook, Twitter, MessageCircle, Linkedin, Code, ExternalLink, Instagram } from 'lucide-react';

const ShareDialog = ({ open, onOpenChange, unit, building }) => {
  const [emailTo, setEmailTo] = useState('');
  const [emailMessage, setEmailMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showEmbed, setShowEmbed] = useState(false);

  // Generate share URL - use production URL for SEO value
  const shareUrl = `https://nofeesapts.com/unit/${unit.id}`;
  
  // Generate bedroom text
  const bedroomText = unit.bedrooms === 0 ? 'Studio' : unit.bedrooms === 1 ? '1 Bedroom' : `${unit.bedrooms} Bedrooms`;
  
  // Generate share text with hashtags for better visibility
  const shareText = `🏠 No broker fee ${bedroomText} in ${building?.neighborhood || building?.city || 'NYC'}! $${unit.rent.toLocaleString()}/mo at ${building?.name || 'this amazing building'}. Save thousands! #NoFeeApartments #NYC #NoBrokerFee`;
  
  // Short share text for platforms with character limits
  const shortShareText = `No-fee ${bedroomText} - $${unit.rent.toLocaleString()}/mo in ${building?.neighborhood || 'NYC'}`;

  // Embed code for blogs (generates backlinks)
  const embedCode = `<div style="border:1px solid #D4AF37;border-radius:8px;padding:16px;max-width:350px;font-family:system-ui;background:#1a1a1a;">
  <a href="${shareUrl}" target="_blank" rel="noopener" style="text-decoration:none;">
    <div style="color:#D4AF37;font-size:16px;font-weight:bold;margin-bottom:6px;">${bedroomText} at ${building?.name || 'NYC'}</div>
    <div style="color:#fff;font-size:22px;font-weight:bold;">$${unit.rent.toLocaleString()}/mo</div>
    <div style="color:#888;font-size:13px;margin:6px 0;">${building?.neighborhood || building?.city || 'NYC'} • No Broker Fee</div>
    <div style="background:#D4AF37;color:#000;padding:8px;text-align:center;border-radius:4px;font-weight:bold;margin-top:10px;">View Listing →</div>
  </a>
  <div style="font-size:9px;color:#666;margin-top:8px;text-align:center;">via <a href="https://nofeesapts.com" style="color:#D4AF37;">NoFeesApts.com</a></div>
</div>`;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    toast.success('Link copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyEmbed = () => {
    navigator.clipboard.writeText(embedCode);
    toast.success('Embed code copied! Paste it on any website or blog.');
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
    // Use the share endpoint for Facebook/LinkedIn to get proper og:image
    const shareApiUrl = `https://nofeesapts.com/api/share/${unit.id}`;
    const encodedShareApiUrl = encodeURIComponent(shareApiUrl);
    const encodedUrl = encodeURIComponent(shareUrl);
    const encodedText = encodeURIComponent(shareText);
    const encodedShortText = encodeURIComponent(shortShareText);
    const listingImage = unit.images?.[0] || '';
    const encodedImage = encodeURIComponent(listingImage);
    
    let shareLink = '';
    
    switch(platform) {
      case 'facebook':
        // Use the share API endpoint which has proper og:meta tags with listing image
        shareLink = `https://www.facebook.com/sharer/sharer.php?u=${encodedShareApiUrl}`;
        break;
      case 'twitter':
        shareLink = `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedShortText}&hashtags=NoFeeApartments,NYC,NoBrokerFee`;
        break;
      case 'whatsapp':
        shareLink = `https://wa.me/?text=${encodedText}%20${encodedUrl}`;
        break;
      case 'linkedin':
        // LinkedIn also scrapes og:tags, use share API endpoint
        shareLink = `https://www.linkedin.com/sharing/share-offsite/?url=${encodedShareApiUrl}`;
        break;
      case 'reddit':
        shareLink = `https://reddit.com/submit?url=${encodedUrl}&title=${encodedShortText}`;
        break;
      case 'pinterest':
        shareLink = `https://pinterest.com/pin/create/button/?url=${encodedUrl}&description=${encodedText}${listingImage ? `&media=${encodedImage}` : ''}`;
        break;
      default:
        return;
    }
    
    window.open(shareLink, '_blank', 'width=600,height=500');
    toast.success(`Opening ${platform}...`);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-[#1a1a1a] border-[#D4AF37]/20 text-[#F5F5F5] max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-[#D4AF37] font-philosopher">Share This Apartment</DialogTitle>
          <DialogDescription className="text-[#888]">
            Share with friends or embed on your website
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          {/* Social Media Share Buttons */}
          <div className="space-y-2">
            <Label className="text-[#F5F5F5] text-sm">Share on Social Media</Label>
            <div className="grid grid-cols-3 gap-2">
              <Button
                onClick={() => handleSocialShare('facebook')}
                variant="outline"
                size="sm"
                className="border-blue-500/50 hover:bg-blue-500/20 text-blue-400"
              >
                <Facebook className="w-4 h-4 mr-1" />
                Facebook
              </Button>
              <Button
                onClick={() => handleSocialShare('twitter')}
                variant="outline"
                size="sm"
                className="border-sky-400/50 hover:bg-sky-400/20 text-sky-400"
              >
                <Twitter className="w-4 h-4 mr-1" />
                Twitter
              </Button>
              <Button
                onClick={() => handleSocialShare('linkedin')}
                variant="outline"
                size="sm"
                className="border-blue-600/50 hover:bg-blue-600/20 text-blue-500"
              >
                <Linkedin className="w-4 h-4 mr-1" />
                LinkedIn
              </Button>
              <Button
                onClick={() => handleSocialShare('whatsapp')}
                variant="outline"
                size="sm"
                className="border-green-500/50 hover:bg-green-500/20 text-green-400"
              >
                <MessageCircle className="w-4 h-4 mr-1" />
                WhatsApp
              </Button>
              <Button
                onClick={() => handleSocialShare('reddit')}
                variant="outline"
                size="sm"
                className="border-orange-500/50 hover:bg-orange-500/20 text-orange-400"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                Reddit
              </Button>
              <Button
                onClick={() => handleSocialShare('pinterest')}
                variant="outline"
                size="sm"
                className="border-red-500/50 hover:bg-red-500/20 text-red-400"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                Pinterest
              </Button>
            </div>
          </div>

          {/* Copy Link */}
          <div className="space-y-2">
            <Label className="text-[#F5F5F5] text-sm">Copy Link</Label>
            <div className="flex gap-2">
              <Input
                value={shareUrl}
                readOnly
                className="bg-[#0a0a0a] border-[#333] text-[#888] text-sm"
              />
              <Button
                onClick={handleCopyLink}
                className="bg-[#D4AF37] hover:bg-[#B8963E] text-black font-semibold"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
          </div>

          {/* Embed Code for Backlinks */}
          <div className="space-y-2">
            <Button
              onClick={() => setShowEmbed(!showEmbed)}
              variant="outline"
              size="sm"
              className="w-full border-[#D4AF37]/50 text-[#D4AF37] hover:bg-[#D4AF37]/10"
            >
              <Code className="w-4 h-4 mr-2" />
              {showEmbed ? 'Hide Embed Code' : 'Get Embed Code (for blogs)'}
            </Button>
            
            {showEmbed && (
              <div className="space-y-2 p-3 bg-[#0a0a0a] rounded-lg border border-[#333]">
                <Textarea
                  value={embedCode}
                  readOnly
                  rows={6}
                  className="bg-transparent border-none text-[#666] text-xs font-mono"
                />
                <Button
                  onClick={handleCopyEmbed}
                  size="sm"
                  className="w-full bg-[#D4AF37] hover:bg-[#B8963E] text-black font-semibold"
                >
                  <Copy className="w-4 h-4 mr-2" /> Copy Embed Code
                </Button>
                <p className="text-[#666] text-xs">
                  Paste this on your blog or website to create a backlink
                </p>
              </div>
            )}
          </div>

          {/* Email Share */}
          <div className="space-y-3 pt-2 border-t border-[#333]">
            <Label className="text-[#F5F5F5] text-sm flex items-center gap-2">
              <Mail className="w-4 h-4" />
              Send via Email
            </Label>
            <div className="space-y-3">
              <Input
                type="email"
                placeholder="friend@example.com"
                value={emailTo}
                onChange={(e) => setEmailTo(e.target.value)}
                className="bg-[#0a0a0a] border-[#333] text-[#F5F5F5] placeholder:text-[#666]"
              />
              <Textarea
                placeholder="I thought you might like this apartment..."
                value={emailMessage}
                onChange={(e) => setEmailMessage(e.target.value)}
                rows={2}
                className="bg-[#0a0a0a] border-[#333] text-[#F5F5F5] placeholder:text-[#666]"
              />
              <Button
                onClick={handleEmailShare}
                disabled={isSending}
                className="w-full bg-[#D4AF37] hover:bg-[#B8963E] text-black font-semibold"
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
