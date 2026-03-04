import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { ArrowRight, CheckCircle, Building2, Users, DollarSign, Shield, Clock, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

const HowItWorks = () => {
  const videoUrl = "https://customer-assets.emergentagent.com/job_47dd6b46-e381-45f3-b7a5-c4e5965d2ca7/artifacts/er34lg4y_The_No-Fee_Revolution.mp4";

  const steps = [
    {
      number: "01",
      title: "We Partner with Landlords",
      description: "NoFeesApts works directly with building owners and management companies who want to fill vacancies faster with qualified tenants.",
      icon: Building2
    },
    {
      number: "02",
      title: "We Showcase Vetted Apartments",
      description: "Every listing is verified as truly no-fee. We curate quality apartments across NYC, NJ, and PA so you only see the best options.",
      icon: Shield
    },
    {
      number: "03",
      title: "Landlords Compensate Us",
      description: "Instead of you paying a broker fee, landlords pay us for bringing them reliable, qualified tenants. You save thousands.",
      icon: DollarSign
    }
  ];

  const renterBenefits = [
    "Save $3,000 - $6,000+ on broker fees",
    "Access to vetted, real apartments only",
    "Professional guidance throughout the process",
    "Help with relocating and guarantors",
    "Daily updated listings",
    "Free to use - no hidden costs"
  ];

  const landlordBenefits = [
    "Fill vacancies faster",
    "Access to qualified, screened tenants",
    "Marketing and listing services",
    "Pricing and market advice",
    "Professional leasing support",
    "Flexible partnership options"
  ];

  // Schema.org structured data for SEO
  const schemaData = {
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": "How to Find a No-Fee Apartment in NYC",
    "description": "Learn how NoFeesApts helps renters find broker-free apartments and save thousands on fees.",
    "step": steps.map((step, index) => ({
      "@type": "HowToStep",
      "position": index + 1,
      "name": step.title,
      "text": step.description
    })),
    "totalTime": "PT5M"
  };

  const videoSchema = {
    "@context": "https://schema.org",
    "@type": "VideoObject",
    "name": "The No-Fee Revolution - How NoFeesApts Works",
    "description": "Learn how NoFeesApts eliminates broker fees for renters by working directly with landlords.",
    "contentUrl": videoUrl,
    "uploadDate": "2024-01-01",
    "duration": "PT5M34S",
    "publisher": {
      "@type": "Organization",
      "name": "NoFeesApts"
    }
  };

  return (
    <>
      <Helmet>
        <title>How No-Fee Apartments Work | Save Thousands on Broker Fees | NoFeesApts</title>
        <meta name="description" content="Learn how NoFeesApts saves you $3,000-$6,000+ on broker fees. We work directly with landlords so you pay $0 in fees. Watch our explainer video." />
        <meta property="og:title" content="How No-Fee Apartments Work | NoFeesApts" />
        <meta property="og:description" content="Save thousands on broker fees. Learn how our no-fee model works for renters and landlords." />
        <meta property="og:video" content={videoUrl} />
        <meta property="og:type" content="video.other" />
        <link rel="canonical" href="https://nofeesapts.com/how-it-works" />
        <script type="application/ld+json">{JSON.stringify(schemaData)}</script>
        <script type="application/ld+json">{JSON.stringify(videoSchema)}</script>
      </Helmet>

      <div className="min-h-screen bg-white">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <Link to="/" className="text-2xl font-philosopher font-bold text-gray-900">
              NoFeesApts
            </Link>
            <Link 
              to="/auth" 
              className="bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded font-medium text-sm transition-colors"
            >
              Sign Up Free
            </Link>
          </div>
        </header>

        {/* Hero with Video */}
        <section className="bg-gradient-to-b from-gray-900 to-gray-800 text-white py-16">
          <div className="max-w-6xl mx-auto px-4">
            <div className="text-center mb-8">
              <span className="inline-block bg-amber-500/20 text-amber-400 text-sm font-medium px-4 py-1 rounded-full mb-4">
                5 minute explainer
              </span>
              <h1 className="text-4xl md:text-5xl font-bold mb-4">
                How No-Fee Apartments Work
              </h1>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                Watch how NoFeesApts saves renters thousands by eliminating broker fees
              </p>
            </div>

            {/* Video Player */}
            <div className="max-w-4xl mx-auto">
              <div className="bg-black rounded-lg overflow-hidden shadow-2xl">
                <video
                  src={videoUrl}
                  controls
                  poster=""
                  className="w-full aspect-video"
                >
                  Your browser does not support the video tag.
                </video>
              </div>
            </div>
          </div>
        </section>

        {/* Key Stats */}
        <section className="py-12 bg-amber-50 border-y border-amber-100">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid md:grid-cols-3 gap-8 text-center">
              <div>
                <p className="text-4xl font-bold text-amber-600">$0</p>
                <p className="text-gray-600">Broker Fee for Renters</p>
              </div>
              <div>
                <p className="text-4xl font-bold text-amber-600">$3,000+</p>
                <p className="text-gray-600">Average Savings</p>
              </div>
              <div>
                <p className="text-4xl font-bold text-amber-600">200+</p>
                <p className="text-gray-600">Verified Listings</p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works Steps */}
        <section className="py-16">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
              The No-Fee Model in 3 Steps
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              {steps.map((step, index) => (
                <div key={index} className="relative">
                  <div className="bg-gray-50 rounded-lg p-6 h-full border border-gray-200">
                    <span className="text-5xl font-bold text-amber-500/20">{step.number}</span>
                    <div className="w-12 h-12 bg-amber-500 rounded-lg flex items-center justify-center mb-4 -mt-6">
                      <step.icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{step.title}</h3>
                    <p className="text-gray-600">{step.description}</p>
                  </div>
                  {index < steps.length - 1 && (
                    <div className="hidden md:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                      <ArrowRight className="w-8 h-8 text-amber-300" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Benefits Grid */}
        <section className="py-16 bg-gray-50">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
              Why It Works for Everyone
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              {/* Renter Benefits */}
              <div className="bg-white rounded-lg p-8 border border-gray-200">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-green-500 rounded-lg flex items-center justify-center">
                    <Users className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">For Renters</h3>
                </div>
                <ul className="space-y-3">
                  {renterBenefits.map((benefit, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Landlord Benefits */}
              <div className="bg-white rounded-lg p-8 border border-gray-200">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-amber-500 rounded-lg flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">For Landlords</h3>
                </div>
                <ul className="space-y-3">
                  {landlordBenefits.map((benefit, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-16">
          <div className="max-w-4xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
              Frequently Asked Questions
            </h2>
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-2">What is a no-fee apartment?</h3>
                <p className="text-gray-600">A no-fee apartment is a rental where the tenant pays $0 in broker fees. The landlord covers all fees, typically because they work directly with platforms like NoFeesApts to find tenants faster.</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-2">How much do broker fees usually cost?</h3>
                <p className="text-gray-600">In NYC, broker fees typically range from one month's rent to 15% of the annual rent. For a $3,000/month apartment, that's $3,000 to $5,400 you'd pay upfront. With no-fee apartments, you save this entire amount.</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-2">Is NoFeesApts really free?</h3>
                <p className="text-gray-600">Yes! NoFeesApts is 100% free for renters. We're compensated by landlords who want to fill their vacancies with qualified tenants. You never pay us anything.</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-2">Are no-fee apartments lower quality?</h3>
                <p className="text-gray-600">Not at all. Many luxury buildings offer no-fee apartments because it helps them fill units faster. Our listings include doorman buildings, modern amenities, and prime locations throughout NYC, NJ, and PA.</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 bg-gray-900 text-white">
          <div className="max-w-3xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold mb-4">
              Ready to Save Thousands?
            </h2>
            <p className="text-gray-400 mb-8">
              Join thousands of renters who found their perfect no-fee apartment. Sign up takes 30 seconds.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/auth">
                <Button className="bg-amber-500 hover:bg-amber-600 text-white px-8 py-6 text-lg font-bold">
                  Sign Up Free <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link to="/apartments">
                <Button variant="outline" className="border-gray-600 text-white hover:bg-gray-800 px-8 py-6 text-lg">
                  Browse Apartments
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 py-8">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500 mb-4">
              <Link to="/" className="hover:text-amber-600">Home</Link>
              <Link to="/apartments" className="hover:text-amber-600">Neighborhoods</Link>
              <Link to="/blog" className="hover:text-amber-600">Blog</Link>
              <Link to="/faq" className="hover:text-amber-600">FAQ</Link>
              <Link to="/auth" className="hover:text-amber-600">Sign Up</Link>
            </div>
            <p className="text-center text-gray-400 text-sm">
              © 2025 NoFeesApts.com — No Fee Apartments in NYC, NJ & PA
            </p>
          </div>
        </footer>
      </div>
    </>
  );
};

export default HowItWorks;
