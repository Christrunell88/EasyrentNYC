import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ChevronDown, ChevronUp, Search, MessageCircle } from 'lucide-react';
import SEO from '../components/SEO';
import { Helmet } from 'react-helmet-async';

const faqs = [
  {
    category: 'About No-Fee Apartments',
    questions: [
      {
        question: 'What does "no-fee" mean?',
        answer: 'A no-fee apartment means you don\'t have to pay a broker fee to rent the apartment. Typically in NYC, broker fees can be 12-15% of your annual rent (that\'s $3,000-$5,000+ for most apartments). With no-fee apartments, the landlord either pays the broker directly or lists the apartment without a broker.'
      },
      {
        question: 'Are no-fee apartments lower quality?',
        answer: 'Absolutely not! No-fee apartments span all price ranges and quality levels. Many luxury buildings and new developments offer no-fee rentals as a competitive advantage. The "no-fee" designation simply refers to who pays the broker \u2013 not the quality of the apartment.'
      },
      {
        question: 'Why do some apartments have broker fees and others don\'t?',
        answer: 'It depends on how competitive the rental market is and the landlord\'s marketing strategy. Buildings with high demand (luxury buildings, popular neighborhoods) often don\'t need brokers. Smaller landlords or older buildings may use brokers to find tenants and pass that cost to renters.'
      }
    ]
  },
  {
    category: 'Finding & Applying',
    questions: [
      {
        question: 'How do I know if an apartment listing is truly "no-fee"?',
        answer: 'Always verify directly with the listing source. On NoFeesApts.com, we verify every listing before publishing. When contacting landlords directly, ask: "Is there any broker fee, application fee, or administrative fee I would need to pay?" Get it in writing before viewing.'
      },
      {
        question: 'What documents do I need to apply for a no-fee apartment?',
        answer: 'Most landlords require: \n\u2022 Credit report (score above 700 preferred)\n\u2022 Proof of income (2-3 months of pay stubs showing 40x monthly rent annually)\n\u2022 Bank statements (2-3 months)\n\u2022 Photo ID (driver\'s license or passport)\n\u2022 References from previous landlords\n\u2022 Employment verification letter'
      },
      {
        question: 'How quickly do I need to act on a no-fee apartment listing?',
        answer: 'Very quickly! Good no-fee apartments in NYC go within 24-72 hours of being listed. Have your documents ready, schedule viewings immediately, and be prepared to submit your application same-day if you love the apartment.'
      },
      {
        question: 'Can I negotiate rent on a no-fee apartment?',
        answer: 'It depends on market conditions and how long the apartment has been available. You have more leverage in winter months, for units available for 30+ days, or if you can offer to sign a longer lease. Always ask politely \u2013 the worst they can say is no!'
      }
    ]
  },
  {
    category: 'Costs & Payments',
    questions: [
      {
        question: 'What are typical move-in costs for a no-fee apartment?',
        answer: 'Expect to pay:\n\u2022 First month\'s rent\n\u2022 Security deposit (usually 1 month\'s rent)\n\u2022 Sometimes last month\'s rent\n\nTotal: Typically 2-3 months\' rent upfront. This is significantly less than fee apartments which require 3-4 months\' rent plus the broker fee.'
      },
      {
        question: 'Are application fees legal in NYC?',
        answer: 'Yes, but they\'re capped at $20 per application under NYC law. If a landlord asks for more, it\'s a red flag. Never pay large "application fees" \u2013 this is sometimes a way to disguise broker fees.'
      },
      {
        question: 'What if I have low credit or no credit history?',
        answer: 'Options include:\n\u2022 Provide a guarantor (someone with good credit who agrees to cover rent if you can\'t)\n\u2022 Offer to pay several months upfront\n\u2022 Provide proof of savings (showing financial stability)\n\u2022 Look for landlords who accept alternative credit scoring (rent payment history, utility bills)'
      }
    ]
  },
  {
    category: 'Using NoFeesApts.com',
    questions: [
      {
        question: 'Is NoFeesApts.com really free to use?',
        answer: 'Yes! 100% free for renters. We make money through partnerships with property management companies and landlords, never from tenants. You get full access to all listings, search tools, and features at no cost.'
      },
      {
        question: 'How often are listings updated?',
        answer: 'Our listings are updated daily. Properties are marked as "Available," "Application Pending," or "Rented" in real-time as we receive updates from landlords. We recommend checking back daily or setting up alerts for new listings in your preferred areas.'
      },
      {
        question: 'Do you have listings outside of NYC?',
        answer: 'Yes! We cover Northern New Jersey including Jersey City, Hoboken, Weehawken, and other areas popular with NYC commuters. Many people find better value and space across the river \u2013 often still with no broker fees!'
      },
      {
        question: 'Can I save my favorite apartments?',
        answer: 'Absolutely! Create a free account to save your favorite listings, set up email alerts for new apartments matching your criteria, and track your application status. All your favorites are synced across devices.'
      }
    ]
  },
  {
    category: 'Neighborhoods & Areas',
    questions: [
      {
        question: 'Which NYC neighborhoods have the most no-fee apartments?',
        answer: 'The highest concentration of no-fee apartments are in:\n\u2022 Financial District & Battery Park City (Manhattan)\n\u2022 Long Island City (Queens)\n\u2022 Downtown Brooklyn\n\u2022 Williamsburg (Brooklyn)\n\u2022 Midtown West / Hudson Yards (Manhattan)\n\nThese areas have many large, professionally managed buildings that don\'t use brokers.'
      },
      {
        question: 'Is Jersey City a good alternative to Manhattan?',
        answer: 'Yes! Jersey City offers:\n\u2022 20-40% lower rents than Manhattan\n\u2022 More space for your money\n\u2022 Many no-fee options\n\u2022 PATH train to Manhattan in 10-20 minutes\n\u2022 Waterfront views and parks\n\nPopular areas: Journal Square, Grove Street, Newport'
      }
    ]
  }
];

const FAQ = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategory, setExpandedCategory] = useState(0);
  const [expandedQuestions, setExpandedQuestions] = useState({});

  const toggleQuestion = (categoryIndex, questionIndex) => {
    const key = `${categoryIndex}-${questionIndex}`;
    setExpandedQuestions(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const filteredFaqs = faqs.map(category => ({
    ...category,
    questions: category.questions.filter(q =>
      q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.answer.toLowerCase().includes(searchTerm.toLowerCase())
    )
  })).filter(category => category.questions.length > 0);

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faqs.flatMap(category =>
      category.questions.map(q => ({
        "@type": "Question",
        "name": q.question,
        "acceptedAnswer": {
          "@type": "Answer",
          "text": q.answer
        }
      }))
    )
  };

  return (
    <>
      <SEO 
        title="FAQ - No-Fee Apartments NYC & New Jersey | NoFeesApts"
        description="Get answers to common questions about finding no-fee apartments in NYC. Learn about costs, application process, and how to save thousands on broker fees."
        keywords="no-fee apartments faq, nyc rental questions, broker fee questions, apartment hunting help"
      />
      
      <Helmet>
        <script type="application/ld+json">
          {JSON.stringify(faqSchema)}
        </script>
      </Helmet>

      <div className="min-h-screen bg-slate-900">
        {/* Header */}
        <div className="bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 py-16 px-4">
          <div className="max-w-4xl mx-auto">
            <Link to="/" className="text-white/80 hover:text-white mb-4 inline-block">
              \u2190 Back to Home
            </Link>
            <h1 className="text-5xl font-bold text-white mb-4">
              Frequently Asked Questions
            </h1>
            <p className="text-xl text-white/90">
              Everything you need to know about finding no-fee apartments in NYC
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-4 py-12">
          {/* Search */}
          <div className="mb-8">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                type="text"
                placeholder="Search for answers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-12 py-6 text-lg bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>

          {/* FAQ Categories */}
          <div className="space-y-6">
            {filteredFaqs.map((category, categoryIndex) => (
              <Card key={categoryIndex} className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <button
                    onClick={() => setExpandedCategory(expandedCategory === categoryIndex ? -1 : categoryIndex)}
                    className="w-full flex items-center justify-between mb-4"
                  >
                    <h2 className="text-2xl font-bold text-white">{category.category}</h2>
                    {expandedCategory === categoryIndex ? (
                      <ChevronUp className="w-6 h-6 text-amber-500" />
                    ) : (
                      <ChevronDown className="w-6 h-6 text-amber-500" />
                    )}
                  </button>

                  {expandedCategory === categoryIndex && (
                    <div className="space-y-4">
                      {category.questions.map((faq, questionIndex) => (
                        <div key={questionIndex} className="border-l-2 border-amber-500 pl-4">
                          <button
                            onClick={() => toggleQuestion(categoryIndex, questionIndex)}
                            className="w-full text-left"
                          >
                            <div className="flex items-start justify-between gap-4">
                              <h3 className="text-lg font-semibold text-white hover:text-amber-500 transition-colors">
                                {faq.question}
                              </h3>
                              {expandedQuestions[`${categoryIndex}-${questionIndex}`] ? (
                                <ChevronUp className="w-5 h-5 text-amber-500 flex-shrink-0 mt-1" />
                              ) : (
                                <ChevronDown className="w-5 h-5 text-slate-400 flex-shrink-0 mt-1" />
                              )}
                            </div>
                          </button>

                          {expandedQuestions[`${categoryIndex}-${questionIndex}`] && (
                            <div className="mt-3 text-slate-300 whitespace-pre-line">
                              {faq.answer}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredFaqs.length === 0 && (
            <div className="text-center py-12">
              <p className="text-slate-400 text-lg mb-4">No questions found matching your search.</p>
              <p className="text-slate-500">Try different keywords or browse all categories.</p>
            </div>
          )}

          {/* Still have questions CTA */}
          <Card className="mt-12 bg-gradient-to-br from-amber-500 via-orange-600 to-red-600 border-0">
            <CardContent className="p-8 text-center">
              <MessageCircle className="w-12 h-12 text-white mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-3">
                Still Have Questions?
              </h2>
              <p className="text-white/90 mb-6">
                Can't find what you're looking for? Start browsing our verified no-fee apartments.
              </p>
              <Link to="/auth">
                <Button size="lg" className="bg-white text-orange-600 hover:bg-gray-100 font-semibold">
                  Browse Apartments \u2192
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
};

export default FAQ;
