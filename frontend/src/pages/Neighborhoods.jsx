import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Building2, MapPin, ArrowRight, Home } from 'lucide-react';
import SEO from '../components/SEO';
import Footer from '../components/Footer';

const Neighborhoods = () => {
  const navigate = useNavigate();

  // All neighborhoods organized by region
  const regions = [
    {
      name: 'New York City',
      locations: [
        { slug: 'manhattan', name: 'Manhattan', description: 'Heart of NYC with iconic neighborhoods', avgRent: '$3,200 - $4,500' },
        { slug: 'brooklyn', name: 'Brooklyn', description: 'Trendy neighborhoods with character', avgRent: '$2,400 - $3,800' },
        { slug: 'queens', name: 'Queens', description: 'Best value with diverse communities', avgRent: '$1,800 - $3,200' },
        { slug: 'bronx', name: 'Bronx', description: 'Affordable with growing arts scene', avgRent: '$1,600 - $2,800' },
      ]
    },
    {
      name: 'Popular NYC Neighborhoods',
      locations: [
        { slug: 'williamsburg', name: 'Williamsburg', description: 'Hip Brooklyn neighborhood', avgRent: '$2,600 - $4,200' },
        { slug: 'long-island-city', name: 'Long Island City', description: 'Modern high-rises with views', avgRent: '$2,200 - $3,600' },
      ]
    },
    {
      name: 'New Jersey',
      locations: [
        { slug: 'jersey-city', name: 'Jersey City', description: 'Quick PATH train to Manhattan', avgRent: '$2,000 - $3,400' },
        { slug: 'hoboken', name: 'Hoboken', description: 'Charming waterfront community', avgRent: '$2,200 - $3,600' },
        { slug: 'weehawken', name: 'Weehawken', description: 'Stunning NYC skyline views', avgRent: '$2,400 - $3,800' },
        { slug: 'harrison', name: 'Harrison', description: 'Modern living near PATH', avgRent: '$2,200 - $3,500' },
      ]
    }
  ];

  // FAQ for SEO
  const faqItems = [
    {
      question: "What is a no-fee apartment?",
      answer: "A no-fee apartment is a rental where the landlord pays the broker's fee, so renters don't have to pay any commission. This can save you 10-15% of your annual rent."
    },
    {
      question: "Which NYC neighborhoods have the most no-fee apartments?",
      answer: "Long Island City, Jersey City, and newer developments in Brooklyn tend to have the most no-fee apartments as landlords in these areas often cover broker fees to attract tenants."
    },
    {
      question: "How much can I save with a no-fee apartment?",
      answer: "In NYC, broker fees typically equal one month's rent or 15% of annual rent. On a $3,000/month apartment, you could save $3,000 - $5,400 by finding a no-fee listing."
    },
    {
      question: "Are no-fee apartments lower quality?",
      answer: "No! No-fee apartments often include newer buildings with modern amenities. The fee structure is determined by the landlord's marketing strategy, not the apartment quality."
    }
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <SEO
        title="Browse All Neighborhoods - No Fee Apartments NYC & NJ"
        description="Explore no broker fee apartments across NYC and New Jersey neighborhoods. Manhattan, Brooklyn, Queens, Jersey City, Hoboken and more. Find your perfect no-fee apartment."
        keywords="no fee apartments by neighborhood, NYC neighborhoods no broker fee, manhattan apartments, brooklyn rentals, jersey city no fee, hoboken apartments, queens rentals, no broker fee neighborhoods"
        url="/neighborhoods"
        faq={faqItems}
        breadcrumbs={[
          { name: 'Home', url: '/' },
          { name: 'Neighborhoods', url: '/neighborhoods' }
        ]}
        structuredData={{
          "@context": "https://schema.org",
          "@type": "ItemList",
          "name": "No Fee Apartment Neighborhoods",
          "description": "Browse no broker fee apartments by neighborhood in NYC and NJ",
          "numberOfItems": regions.reduce((sum, r) => sum + r.locations.length, 0),
          "itemListElement": regions.flatMap((region, ri) => 
            region.locations.map((loc, li) => ({
              "@type": "ListItem",
              "position": ri * 10 + li + 1,
              "item": {
                "@type": "Place",
                "name": loc.name,
                "description": loc.description,
                "url": `https://nofeesapts.com/location/${loc.slug}`
              }
            }))
          )
        }}
      />

      {/* Header */}
      <header className="bg-[#0a0a0a] border-b border-[#D4AF37]/20 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#D4AF37] to-[#B8963E] flex items-center justify-center">
                <Building2 className="w-6 h-6 text-[#0a0a0a]" />
              </div>
              <span className="text-xl font-bold text-[#D4AF37] font-philosopher">NoFeesApts</span>
            </div>
            <Button
              onClick={() => navigate('/dashboard')}
              className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-semibold"
            >
              Browse All Apartments
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0a0a] to-[#111]">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-6 font-philosopher">
            Browse Apartments by <span className="text-[#D4AF37]">Neighborhood</span>
          </h1>
          <p className="text-xl text-[#888] max-w-3xl mx-auto">
            Explore no broker fee apartments across NYC and New Jersey. Click on any neighborhood to see available listings, average rents, and local highlights.
          </p>
        </div>
      </section>

      {/* Neighborhoods Grid by Region */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {regions.map((region) => (
            <div key={region.name} className="mb-12">
              <h2 className="text-2xl font-bold text-white mb-6 font-philosopher flex items-center gap-2">
                <MapPin className="w-6 h-6 text-[#D4AF37]" />
                {region.name}
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {region.locations.map((location) => (
                  <Card
                    key={location.slug}
                    className="bg-[#1a1a1a] border-[#D4AF37]/20 hover:border-[#D4AF37]/50 transition-all cursor-pointer group"
                    onClick={() => navigate(`/location/${location.slug}`)}
                  >
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-3">
                        <div className="w-12 h-12 rounded-lg bg-[#D4AF37]/10 flex items-center justify-center group-hover:bg-[#D4AF37]/20 transition-colors">
                          <Home className="w-6 h-6 text-[#D4AF37]" />
                        </div>
                        <ArrowRight className="w-5 h-5 text-[#D4AF37] opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <h3 className="text-lg font-semibold text-white mb-2 font-philosopher">{location.name}</h3>
                      <p className="text-sm text-[#888] mb-3">{location.description}</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-[#666]">Avg Rent</span>
                        <span className="text-sm font-semibold text-[#D4AF37]">{location.avgRent}</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-[#111]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-white mb-8 text-center font-philosopher">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            {faqItems.map((item, index) => (
              <Card key={index} className="bg-[#1a1a1a] border-[#333]">
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-[#F5F5F5] mb-2">{item.question}</h3>
                  <p className="text-[#888]">{item.answer}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-[#D4AF37] via-[#E5C158] to-[#D4AF37]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-[#0a0a0a] mb-4 font-philosopher">
            Ready to Find Your Perfect Apartment?
          </h2>
          <p className="text-lg text-[#333] mb-8">
            Browse 180+ verified no-fee apartments. Sign up free and save thousands.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => navigate('/auth')}
              size="lg"
              className="bg-[#0a0a0a] hover:bg-[#1a1a1a] text-[#D4AF37] font-bold px-10"
            >
              Sign Up Free
            </Button>
            <Button
              onClick={() => navigate('/dashboard')}
              size="lg"
              variant="outline"
              className="border-2 border-[#0a0a0a] text-[#0a0a0a] hover:bg-[#0a0a0a] hover:text-[#D4AF37] font-bold px-10"
            >
              View All Apartments
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default Neighborhoods;
