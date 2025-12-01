import React, { useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Calendar, Clock, ArrowLeft, Share2, Facebook, Twitter, Linkedin } from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { toast } from 'sonner';

const blogPostsContent = {
  'ultimate-guide-no-fee-apartments-nyc-2025': {
    title: 'The Ultimate Guide to Finding No-Fee Apartments in NYC (2025)',
    excerpt: 'Discover proven strategies to save thousands on broker fees when apartment hunting in New York City.',
    author: 'NoFeesApts Team',
    date: '2025-01-15',
    readTime: '8 min read',
    category: 'Guides',
    image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=1200&q=80',
    content: `
<h2>Why No-Fee Apartments Matter</h2>
<p>In New York City, broker fees can cost 12-15% of your annual rent – that's $3,000-$5,000+ for most apartments. For young professionals and families, this is a significant financial burden that can delay your move or force compromises on your dream apartment.</p>

<h2>What Are No-Fee Apartments?</h2>
<p>No-fee apartments are rentals where the landlord pays the broker fee (if there is one) rather than passing the cost to the tenant. This means you save thousands of dollars at move-in, making your transition to NYC much more affordable.</p>

<h2>Where to Find No-Fee Apartments</h2>
<p><strong>1. Direct from Property Management Companies</strong></p>
<p>Large buildings and property management companies often list apartments directly without broker involvement. Look for:</p>
<ul>
  <li>New developments and luxury buildings</li>
  <li>Buildings managed by large companies like Related, Avalon, or Equity</li>
  <li>Property websites and leasing offices</li>
</ul>

<p><strong>2. Online Platforms Like NoFeesApts.com</strong></p>
<p>Specialized platforms aggregate no-fee listings from multiple sources, saving you hours of research. NoFeesApts.com verifies all listings to ensure they're truly fee-free.</p>

<p><strong>3. Craigslist and StreetEasy</strong></p>
<p>Filter for "no fee" listings, but be cautious – always verify directly with the landlord that there are no hidden fees.</p>

<h2>Best Neighborhoods for No-Fee Apartments</h2>
<p><strong>Manhattan:</strong> Battery Park City, Financial District, Midtown West (Hudson Yards)</p>
<p><strong>Brooklyn:</strong> Downtown Brooklyn, Williamsburg, Long Island City (technically Queens)</p>
<p><strong>Queens:</strong> Long Island City, Astoria, Forest Hills</p>
<p><strong>New Jersey:</strong> Jersey City (Journal Square, Newport), Hoboken</p>

<h2>Timing Your Search</h2>
<p>The best time to find no-fee apartments is during off-peak seasons:</p>
<ul>
  <li><strong>Winter (December-February):</strong> Fewer renters = more negotiating power</li>
  <li><strong>Mid-month:</strong> Landlords are motivated to fill vacancies before month-end</li>
  <li><strong>Avoid summer:</strong> May-September is peak moving season with fewer deals</li>
</ul>

<h2>Red Flags to Watch Out For</h2>
<ul>
  <li>"No fee" listings that require an "application fee" over $100</li>
  <li>Listings that seem too good to be true (they usually are)</li>
  <li>Brokers claiming to represent "no fee" apartments but asking for payment later</li>
  <li>Apartments requiring 4+ months upfront (first, last, security, and broker fee)</li>
</ul>

<h2>How to Maximize Your Chances</h2>
<p><strong>1. Have Your Documents Ready</strong></p>
<ul>
  <li>Credit report (above 700 preferred)</li>
  <li>Pay stubs (2-3 months, showing 40x monthly rent annually)</li>
  <li>Bank statements</li>
  <li>References from previous landlords</li>
  <li>Government-issued ID</li>
</ul>

<p><strong>2. Act Fast</strong></p>
<p>Good no-fee apartments go quickly. Be ready to view and apply within 24-48 hours of listings going live.</p>

<p><strong>3. Be Flexible on Move-In Dates</strong></p>
<p>Landlords love tenants who can move in immediately or can wait for a specific date. Flexibility = leverage.</p>

<h2>Conclusion</h2>
<p>Finding a no-fee apartment in NYC requires strategy, timing, and persistence, but the savings are worth it. Use platforms like NoFeesApts.com to streamline your search and start your NYC journey with thousands of dollars still in your pocket.</p>

<p><strong>Ready to start your search?</strong> Browse 206+ verified no-fee apartments on NoFeesApts.com today.</p>
    `
  },
  // Add more blog posts here as needed
};

const BlogPost = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const post = blogPostsContent[slug];

  useEffect(() => {
    if (!post) {
      navigate('/blog');
    }
  }, [post, navigate]);

  if (!post) {
    return null;
  }

  const shareUrl = `https://nofeesapts.com/blog/${slug}`;

  const handleShare = (platform) => {
    const urls = {
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
      twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(post.title)}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`
    };

    if (platform === 'copy') {
      navigator.clipboard.writeText(shareUrl);
      toast.success('Link copied to clipboard!');
    } else {
      window.open(urls[platform], '_blank', 'width=600,height=400');
    }
  };

  return (
    <>
      <Helmet>
        <title>{post.title} | NoFeesApts Blog</title>
        <meta name="description" content={post.excerpt} />
        <meta property="og:title" content={post.title} />
        <meta property="og:description" content={post.excerpt} />
        <meta property="og:image" content={post.image} />
        <meta property="og:url" content={shareUrl} />
        <meta property="og:type" content="article" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={post.title} />
        <meta name="twitter:description" content={post.excerpt} />
        <meta name="twitter:image" content={post.image} />
        
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": post.excerpt,
            "image": post.image,
            "datePublished": post.date,
            "author": {
              "@type": "Organization",
              "name": post.author
            },
            "publisher": {
              "@type": "Organization",
              "name": "NoFeesApts",
              "logo": {
                "@type": "ImageObject",
                "url": "https://nofeesapts.com/logo.png"
              }
            }
          })}
        </script>
      </Helmet>

      <div className="min-h-screen bg-slate-900">
        {/* Hero Image */}
        <div className="relative h-96 overflow-hidden">
          <img 
            src={post.image} 
            alt={post.title}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/50 to-transparent" />
        </div>

        {/* Content */}
        <div className="max-w-4xl mx-auto px-4 -mt-32 relative z-10">
          <Link to="/blog" className="text-amber-500 hover:text-amber-400 mb-6 inline-flex items-center">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Blog
          </Link>

          <Card className="bg-slate-800 border-slate-700">
            <CardContent className="p-8 md:p-12">
              {/* Header */}
              <div className="mb-8">
                <span className="inline-block bg-amber-600 text-white text-sm px-3 py-1 rounded-full mb-4">
                  {post.category}
                </span>
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                  {post.title}
                </h1>
                <div className="flex items-center gap-6 text-slate-400 text-sm">
                  <span className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    {new Date(post.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                  </span>
                  <span className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    {post.readTime}
                  </span>
                </div>
              </div>

              {/* Share Buttons */}
              <div className="flex gap-2 mb-8 pb-8 border-b border-slate-700">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleShare('facebook')}
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  <Facebook className="w-4 h-4 mr-2" />
                  Share
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleShare('twitter')}
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  <Twitter className="w-4 h-4 mr-2" />
                  Tweet
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleShare('linkedin')}
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  <Linkedin className="w-4 h-4 mr-2" />
                  Share
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleShare('copy')}
                  className="border-slate-600 text-slate-300 hover:bg-slate-700"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  Copy Link
                </Button>
              </div>

              {/* Article Content */}
              <div 
                className="prose prose-invert prose-amber max-w-none"
                dangerouslySetInnerHTML={{ __html: post.content }}
                style={{
                  color: '#e2e8f0',
                  fontSize: '1.125rem',
                  lineHeight: '1.75'
                }}
              />

              {/* CTA */}
              <div className="mt-12 p-6 bg-gradient-to-br from-amber-500/20 to-orange-600/20 rounded-xl border border-amber-500/30">
                <h3 className="text-2xl font-bold text-white mb-3">
                  Find Your No-Fee Apartment Today
                </h3>
                <p className="text-slate-300 mb-4">
                  Browse 206+ verified no-fee apartments in NYC and New Jersey. No broker fees. No hidden costs.
                </p>
                <Link to="/auth">
                  <Button className="bg-amber-600 hover:bg-amber-700 text-white">
                    Start Your Search →
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Related Articles would go here */}
        <div className="py-16" />
      </div>
    </>
  );
};

export default BlogPost;