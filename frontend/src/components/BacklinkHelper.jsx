import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { Copy, ExternalLink, Code, Share2, Link2, Facebook, Twitter, Linkedin, Mail} from 'lucide-react';

/**
 * BacklinkHelper - Generates embed codes, share links, and backlink opportunities
 * Use this to increase high-authority backlinks and improve SEO
 */
const BacklinkHelper = ({ unit, building }) => {
  const [copied, setCopied] = useState(null);
  const baseUrl = 'https://nofeesapts.com';
  
  // Generate URLs
  const unitUrl = unit ? `${baseUrl}/unit/${unit.id}` : baseUrl;
  const buildingName = unit?.building?.name || building?.name || 'NoFeesApts';
  const neighborhood = unit?.building?.neighborhood || unit?.building?.city || 'NYC';
  const rent = unit?.rent ? `$${unit.rent.toLocaleString()}/mo` : '';
  const bedrooms = unit?.bedrooms === 0 ? 'Studio' : unit?.bedrooms === 1 ? '1 Bedroom' : `${unit?.bedrooms} Bedrooms`;
  
  // Share text templates
  const shareTitle = unit 
    ? `No Fee ${bedrooms} in ${neighborhood} - ${rent}`
    : `Find No Fee Apartments in NYC & NJ`;
  
  const shareDescription = unit
    ? `Check out this no broker fee apartment at ${buildingName}! ${bedrooms}, ${rent}. Save thousands on broker fees.`
    : `Browse 200+ no broker fee apartments in NYC, NJ & PA. Save thousands with NoFeesApts.com!`;

  // Social share URLs
  const shareUrls = {
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(unitUrl)}&quote=${encodeURIComponent(shareDescription)}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(unitUrl)}&text=${encodeURIComponent(shareTitle)}&hashtags=NoFeeApartments,NYC,NoBrokerFee`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(unitUrl)}`,
    email: `mailto:?subject=${encodeURIComponent(shareTitle)}&body=${encodeURIComponent(`${shareDescription}\n\n${unitUrl}`)}`,
    pinterest: `https://pinterest.com/pin/create/button/?url=${encodeURIComponent(unitUrl)}&description=${encodeURIComponent(shareDescription)}`,
    reddit: `https://reddit.com/submit?url=${encodeURIComponent(unitUrl)}&title=${encodeURIComponent(shareTitle)}`,
  };

  // Embed code for blogs/websites
  const embedCode = unit ? `<!-- NoFeesApts.com Listing Widget -->
<div style="border:1px solid #D4AF37;border-radius:8px;padding:16px;max-width:400px;font-family:system-ui;">
  <a href="${unitUrl}" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;">
    <div style="font-size:18px;font-weight:bold;color:#D4AF37;margin-bottom:8px;">
      ${bedrooms} at ${buildingName}
    </div>
    <div style="font-size:24px;font-weight:bold;color:#333;margin-bottom:4px;">${rent}</div>
    <div style="font-size:14px;color:#666;margin-bottom:12px;">${neighborhood} • No Broker Fee</div>
    <div style="background:#D4AF37;color:#000;padding:8px 16px;text-align:center;border-radius:4px;font-weight:bold;">
      View Listing →
    </div>
  </a>
  <div style="font-size:10px;color:#888;margin-top:8px;text-align:center;">
    Powered by <a href="https://nofeesapts.com" target="_blank" style="color:#D4AF37;">NoFeesApts.com</a>
  </div>
</div>` : `<!-- NoFeesApts.com Search Widget -->
<div style="border:1px solid #D4AF37;border-radius:8px;padding:20px;max-width:400px;font-family:system-ui;text-align:center;">
  <div style="font-size:20px;font-weight:bold;color:#D4AF37;margin-bottom:8px;">
    No Fee Apartments NYC & NJ
  </div>
  <div style="font-size:14px;color:#666;margin-bottom:16px;">
    Browse 200+ verified no broker fee apartments
  </div>
  <a href="https://nofeesapts.com" target="_blank" rel="noopener" 
     style="display:inline-block;background:#D4AF37;color:#000;padding:12px 24px;text-decoration:none;border-radius:4px;font-weight:bold;">
    Search Apartments →
  </a>
  <div style="font-size:10px;color:#888;margin-top:12px;">
    Save thousands on broker fees
  </div>
</div>`;

  // Badge/button code for partner sites
  const badgeCode = `<a href="https://nofeesapts.com" target="_blank" rel="noopener" title="Find No Fee Apartments">
  <img src="https://nofeesapts.com/badge.png" alt="NoFeesApts.com - No Broker Fee Apartments" width="200" height="60" />
</a>`;

  // Text link for forums/comments
  const textLink = unit 
    ? `[${bedrooms} in ${neighborhood} - ${rent} (No Fee)](${unitUrl})`
    : `[Find No Fee Apartments in NYC & NJ](https://nofeesapts.com)`;

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    toast.success('Copied to clipboard!');
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <Card className="bg-[#1a1a1a] border-[#D4AF37]/20">
      <CardHeader>
        <CardTitle className="text-[#D4AF37] font-philosopher flex items-center gap-2">
          <Link2 className="w-5 h-5" />
          Share & Embed
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Social Share Buttons */}
        <div>
          <Label className="text-[#F5F5F5] text-sm mb-3 block">Share on Social Media</Label>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(shareUrls.facebook, '_blank')}
              className="border-blue-500 text-blue-500 hover:bg-blue-500/10"
            >
              <Facebook className="w-4 h-4 mr-1" /> Facebook
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(shareUrls.twitter, '_blank')}
              className="border-sky-400 text-sky-400 hover:bg-sky-400/10"
            >
              <Twitter className="w-4 h-4 mr-1" /> Twitter
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(shareUrls.linkedin, '_blank')}
              className="border-blue-600 text-blue-600 hover:bg-blue-600/10"
            >
              <Linkedin className="w-4 h-4 mr-1" /> LinkedIn
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(shareUrls.email, '_blank')}
              className="border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37]/10"
            >
              <Mail className="w-4 h-4 mr-1" /> Email
            </Button>
          </div>
        </div>

        {/* Direct Link */}
        <div>
          <Label className="text-[#F5F5F5] text-sm mb-2 block">Direct Link</Label>
          <div className="flex gap-2">
            <Input 
              value={unitUrl} 
              readOnly 
              className="bg-[#0a0a0a] border-[#333] text-[#F5F5F5] text-sm"
            />
            <Button
              variant="outline"
              onClick={() => copyToClipboard(unitUrl, 'link')}
              className="border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37]/10"
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Embed Code */}
        <div>
          <Label className="text-[#F5F5F5] text-sm mb-2 block flex items-center gap-2">
            <Code className="w-4 h-4" /> Embed Widget (for blogs & websites)
          </Label>
          <Textarea 
            value={embedCode}
            readOnly
            rows={6}
            className="bg-[#0a0a0a] border-[#333] text-[#888] text-xs font-mono"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => copyToClipboard(embedCode, 'embed')}
            className="mt-2 border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37]/10"
          >
            <Copy className="w-4 h-4 mr-2" /> Copy Embed Code
          </Button>
        </div>

        {/* Markdown Link */}
        <div>
          <Label className="text-[#F5F5F5] text-sm mb-2 block">
            Markdown Link (for Reddit, forums, comments)
          </Label>
          <div className="flex gap-2">
            <Input 
              value={textLink}
              readOnly 
              className="bg-[#0a0a0a] border-[#333] text-[#888] text-xs font-mono"
            />
            <Button
              variant="outline"
              onClick={() => copyToClipboard(textLink, 'markdown')}
              className="border-[#D4AF37] text-[#D4AF37] hover:bg-[#D4AF37]/10"
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* SEO Tips */}
        <div className="p-4 bg-[#0a0a0a] rounded-lg border border-[#333]">
          <h4 className="text-[#D4AF37] font-philosopher text-sm mb-2">Backlink Tips</h4>
          <ul className="text-[#888] text-xs space-y-1">
            <li>• Share on real estate forums (Reddit r/NYCapartments, r/jerseycity)</li>
            <li>• Post to neighborhood Facebook groups</li>
            <li>• Share with relocation services and HR departments</li>
            <li>• Embed widget on apartment review blogs</li>
            <li>• Add to "moving to NYC" guides and resources</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default BacklinkHelper;
