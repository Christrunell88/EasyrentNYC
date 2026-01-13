import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Search, Calendar, Clock, ArrowRight } from 'lucide-react';
import SEO from '../components/SEO';
import { Helmet } from 'react-helmet-async';

const blogPosts = [
  {
    id: 'broker-fees',
    slug: 'why-nyc-renters-pay-broker-fees',
    title: 'Why NYC Renters Pay Broker Fees When No One Else Does',
    excerpt: 'NYC is one of the only markets in America where tenants pay broker fees. Learn why the NYC rental market is different from every other city—and how to avoid these fees entirely.',
    author: 'NoFeesApts Team',
    date: 'January 2025',
    readTime: '8 min read',
    category: 'Market Insights',
    tags: ['broker fees', 'nyc market', 'rental tips', 'save money'],
    image: 'https://images.unsplash.com/photo-1534430480872-3498386e7856?w=800&q=80',
    featured: true
  },
  {
    id: 'guide',
    slug: 'guide-to-no-fee-apartments',
    title: 'Ultimate Guide to Finding No-Fee Apartments in NYC (2024-2025)',
    excerpt: 'Discover how to find no-fee apartments in NYC and save thousands on broker fees. Complete guide to NYC apartment hunting with expert tips and neighborhood insights.',
    author: 'NoFeesApts Team',
    date: 'December 2024',
    readTime: '10 min read',
    category: 'Guides',
    tags: ['no-fee', 'apartment hunting', 'nyc', 'broker fees'],
    image: 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80'
  },
  {
    id: 'neighborhoods',
    slug: 'best-neighborhoods',
    title: 'Top 10 NYC Neighborhoods for No-Fee Apartments in 2024',
    excerpt: 'Not all NYC neighborhoods are equal when it comes to no-fee apartments. Compare the top 10 areas with rent prices, transit scores, and lifestyle recommendations.',
    author: 'NoFeesApts Team',
    date: 'December 2024',
    readTime: '8 min read',
    category: 'Neighborhoods',
    tags: ['neighborhoods', 'no-fee', 'comparison', 'manhattan', 'brooklyn', 'queens'],
    image: 'https://images.unsplash.com/photo-1496568816309-51d7c20e3b21?w=800&q=80'
  },
  {
    id: 'checklist',
    slug: 'apartment-checklist',
    title: 'NYC Apartment Hunting Checklist: What to Know Before You Rent',
    excerpt: 'Renting in NYC requires preparation. This comprehensive checklist covers documents, viewing tips, lease terms, red flags, and tenant rights.',
    author: 'NoFeesApts Team',
    date: 'December 2024',
    readTime: '12 min read',
    category: 'Tips & Advice',
    tags: ['checklist', 'apartment hunting', 'tenant rights', 'lease'],
    image: 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&q=80'
  },
  {
    id: '1',
    slug: 'ultimate-guide-no-fee-apartments-nyc-2025',
    title: 'The Ultimate Guide to Finding No-Fee Apartments in NYC (2025)',
    excerpt: 'Discover proven strategies to save thousands on broker fees when apartment hunting in New York City. Learn the insider tips that landlords don\'t want you to know.',
    content: '',
    author: 'NoFeesApts Team',
    date: '2025-01-15',
    readTime: '8 min read',
    category: 'Guides',
    tags: ['apartment hunting', 'nyc', 'no-fee', 'moving tips'],
    image: 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800&q=80'
  },
  {
    id: '2',
    slug: 'hidden-costs-renting-nyc-how-to-avoid',
    title: 'Hidden Costs of Renting in NYC & How to Avoid Them',
    excerpt: 'Beyond broker fees, discover the hidden costs that can add thousands to your move-in expenses. From application fees to credit checks, we break down every cost.',
    author: 'NoFeesApts Team',
    date: '2025-01-10',
    readTime: '6 min read',
    category: 'Finances',
    tags: ['moving costs', 'budget', 'nyc rentals'],
    image: 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800&q=80'
  },
  {
    id: '3',
    slug: 'best-neighborhoods-young-professionals-2025',
    title: 'Best NYC Neighborhoods for Young Professionals in 2025',
    excerpt: 'Looking for the perfect neighborhood to start your NYC career? We rank the top areas based on commute times, nightlife, affordability, and quality of life.',
    author: 'NoFeesApts Team',
    date: '2025-01-05',
    readTime: '10 min read',
    category: 'Neighborhoods',
    tags: ['neighborhoods', 'young professionals', 'career'],
    image: 'https://images.unsplash.com/photo-1496568816309-51d7c20e3b21?w=800&q=80'
  },
  {
    id: '4',
    slug: 'no-fee-apartments-jersey-city-complete-guide',
    title: 'No-Fee Apartments in Jersey City: The Complete 2025 Guide',
    excerpt: 'Jersey City offers amazing alternatives to Manhattan with lower costs and no broker fees. Discover why thousands are making the move across the river.',
    author: 'NoFeesApts Team',
    date: '2024-12-28',
    readTime: '7 min read',
    category: 'Guides',
    tags: ['jersey city', 'new jersey', 'no-fee', 'alternative'],
    image: 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800&q=80'
  },
  {
    id: '5',
    slug: 'first-apartment-checklist-nyc',
    title: 'Your First Apartment in NYC: The Essential Checklist',
    excerpt: 'Moving to your first NYC apartment? Don\'t forget these essentials! From renters insurance to furniture, we\'ve got you covered.',
    author: 'NoFeesApts Team',
    date: '2024-12-20',
    readTime: '5 min read',
    category: 'Moving Tips',
    tags: ['first apartment', 'checklist', 'moving'],
    image: 'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&q=80'
  },
  {
    id: '6',
    slug: 'nyc-rental-market-trends-2025',
    title: 'NYC Rental Market Trends: What to Expect in 2025',
    excerpt: 'Stay ahead of the market! Our analysis of 2025 rental trends, price forecasts, and the best times to search for your perfect no-fee apartment.',
    author: 'NoFeesApts Team',
    date: '2024-12-15',
    readTime: '9 min read',
    category: 'Market Analysis',
    tags: ['trends', 'market analysis', '2025'],
    image: 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&q=80'
  }
];

const Blog = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  
  const categories = ['All', 'Guides', 'Market Insights', 'Neighborhoods', 'Finances', 'Moving Tips', 'Market Analysis', 'Tips & Advice'];
  
  const filteredPosts = blogPosts.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         post.excerpt.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         post.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'All' || post.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <>
      <SEO 
        title="NYC No-Fee Apartment Blog | Guides, Tips & Market Insights"
        description="Expert guides on finding no-fee apartments in NYC and New Jersey. Get insider tips, neighborhood guides, and market analysis to save thousands on your move."
        keywords="nyc apartment blog, no-fee apartments guide, nyc rental tips, apartment hunting nyc, moving to nyc, how to find no fee apartments, rent without broker NYC, first apartment NYC tips, avoid broker fees NYC, best neighborhoods NYC rentals"
      />
      
      <Helmet>
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": "NoFeesApts Blog",
            "description": "Expert guides and tips for finding no-fee apartments in NYC",
            "url": "https://nofeesapts.com/blog",
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
        {/* Header */}
        <div className="bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 py-16 px-4">
          <div className="max-w-6xl mx-auto">
            <Link to="/" className="text-white/80 hover:text-white mb-4 inline-block">
              ← Back to Home
            </Link>
            <h1 className="text-5xl font-bold text-white mb-4">
              NYC Apartment Hunting Blog
            </h1>
            <p className="text-xl text-white/90 max-w-2xl">
              Expert guides, insider tips, and market insights to help you find your perfect no-fee apartment.
            </p>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="bg-slate-800 rounded-xl p-6 mb-8">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  type="text"
                  placeholder="Search articles..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-slate-700 border-slate-600 text-white"
                />
              </div>
              
              {/* Categories */}
              <div className="flex flex-wrap gap-2">
                {categories.map(category => (
                  <Button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    variant={selectedCategory === category ? 'default' : 'outline'}
                    className={selectedCategory === category ? 'bg-amber-600 hover:bg-amber-700' : 'border-slate-600 text-white hover:bg-slate-700'}
                  >
                    {category}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          {/* Blog Posts Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPosts.map(post => (
              <Link key={post.id} to={`/blog/${post.slug}`}>
                <Card className="bg-slate-800 border-slate-700 hover:border-amber-500 transition-all h-full group overflow-hidden">
                  <div className="relative h-48 overflow-hidden">
                    <img 
                      src={post.image} 
                      alt={post.title}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                      loading="lazy"
                      decoding="async"
                    />
                    <div className="absolute top-3 left-3">
                      <span className="bg-amber-600 text-white text-xs px-3 py-1 rounded-full">
                        {post.category}
                      </span>
                    </div>
                  </div>
                  
                  <CardHeader>
                    <CardTitle className="text-white group-hover:text-amber-500 transition-colors line-clamp-2">
                      {post.title}
                    </CardTitle>
                    <CardDescription className="text-slate-400 line-clamp-3">
                      {post.excerpt}
                    </CardDescription>
                  </CardHeader>
                  
                  <CardContent>
                    <div className="flex items-center justify-between text-sm text-slate-400">
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          {new Date(post.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {post.readTime}
                        </span>
                      </div>
                      <ArrowRight className="w-5 h-5 text-amber-500 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {filteredPosts.length === 0 && (
            <div className="text-center py-12">
              <p className="text-slate-400 text-lg">No articles found matching your search.</p>
            </div>
          )}
        </div>

        {/* CTA Section */}
        <div className="max-w-6xl mx-auto px-4 py-16">
          <Card className="bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 border-0">
            <CardContent className="p-8 text-center">
              <h2 className="text-3xl font-bold text-white mb-4">
                Ready to Find Your No-Fee Apartment?
              </h2>
              <p className="text-white/90 mb-6 max-w-2xl mx-auto">
                Browse 206+ verified no-fee apartments in NYC and Northern New Jersey. No broker fees. No hidden costs.
              </p>
              <Link to="/auth">
                <Button size="lg" className="bg-white text-orange-600 hover:bg-gray-100 font-semibold">
                  Start Your Search →
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
};

export default Blog;