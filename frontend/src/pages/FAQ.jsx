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
        question: 'What exactly is a "no-fee" apartment?',
        answer: 'A no-fee apartment is a rental where the landlord or building management pays the broker\'s commission instead of the tenant. In a typical broker-fee rental, tenants pay 12-15% of the annual rent (often one month\'s rent or more) directly to the broker. With no-fee apartments, you avoid this cost entirely.'
      },
      {
        question: 'How much can I save with a no-fee apartment?',
        answer: 'Savings vary based on the rent amount, but typically you\'ll save one to two months\' rent:\n\u2022 On a $3,000/month apartment: Save $3,000-$6,000\n\u2022 On a $4,000/month apartment: Save $4,000-$8,000\n\u2022 On a $5,000/month apartment: Save $5,000-$10,000'
      },
      {
        question: 'Are no-fee apartments lower quality than broker-fee apartments?',
        answer: 'No! No-fee apartments are simply properties where the landlord has chosen to pay the broker commission (or rent directly without a broker). You\'ll find no-fee options across all price ranges and quality levels, from budget-friendly studios to luxury penthouses.'
      },
      {
        question: 'Why do some landlords pay the broker fee while others don\'t?',
        answer: 'Landlords typically pay broker fees for several reasons:\n\u2022 They own multiple properties and use a management company\n\u2022 The building has its own leasing office\n\u2022 They want to attract more qualified tenants\n\u2022 The rental market is slower and they need to incentivize renters\n\u2022 They\'re managing the property themselves without a broker'
      }
    ]
  },
  {
    category: 'Finding & Applying',
    questions: [
      {
        question: 'How do I find legitimate no-fee apartments?',
        answer: 'Use specialized no-fee sites like NoFeesApts.com, look for "For Rent By Owner" (FRBO) listings, contact building management companies directly, and check with large residential complexes. Be wary of listings marked "CYOF" (Collect Your Own Fee)\u2014these often still charge broker fees.'
      },
      {
        question: 'What is "CYOF" and should I avoid it?',
        answer: 'CYOF stands for "Collect Your Own Fee." While it may appear in no-fee search results, it actually means the broker expects YOU to pay their fee. Always ask directly: "Who pays the broker fee?" before scheduling a viewing.'
      },
      {
        question: 'Do I still need to pay application fees for no-fee apartments?',
        answer: 'Yes. No-fee refers specifically to the broker fee. You\'ll still typically pay:\n\u2022 Application fee: $20-$100 per applicant\n\u2022 Credit check fee (often included in application fee)\n\u2022 First month\'s rent\n\u2022 Security deposit (usually 1 month\'s rent)\n\u2022 Move-in fees (if applicable)'
      },
      {
        question: 'What documents do I need to apply for a no-fee apartment?',
        answer: 'Standard application requirements include:\n\u2022 Government-issued photo ID (driver\'s license or passport)\n\u2022 Proof of income (last 2-3 pay stubs)\n\u2022 Tax returns (last 1-2 years)\n\u2022 Bank statements (last 2-3 months)\n\u2022 Employment verification letter\n\u2022 Previous landlord references\n\u2022 Personal references'
      },
      {
        question: 'What are the income requirements for NYC apartments?',
        answer: 'Most NYC landlords require:\n\u2022 40x rule: Annual income of at least 40 times the monthly rent\n\u2022 Example: For $3,000/month rent, you need $120,000 annual income\n\u2022 If you don\'t meet this, you can use a guarantor (who needs 80x monthly rent) or a third-party guarantor service'
      },
      {
        question: 'Can I negotiate the rent on a no-fee apartment?',
        answer: 'Yes! Just because it\'s no-fee doesn\'t mean the rent is fixed. You can negotiate: monthly rent amount (especially in off-peak seasons), free month (first or last month free), reduced security deposit, longer lease term for lower monthly rate, and move-in date flexibility.'
      }
    ]
  },
  {
    category: 'Lease Terms & Moving In',
    questions: [
      {
        question: 'How long are typical NYC apartment leases?',
        answer: 'Most NYC leases are 12 months, but you may find:\n\u2022 6-month leases (often at a premium)\n\u2022 9-month leases (less common)\n\u2022 18-24 month leases (sometimes offered with incentives)\n\u2022 Month-to-month (rare and usually more expensive)'
      },
      {
        question: 'What\'s included in my rent?',
        answer: 'This varies by building, but typically:\n\u2022 Usually included: Water, heat (during winter)\n\u2022 Sometimes included: Hot water, gas\n\u2022 Rarely included: Electricity, internet, cable\n\u2022 Always ask what utilities are included before signing'
      },
      {
        question: 'How much is a security deposit in NYC?',
        answer: 'Typically one month\'s rent for buildings with 6+ units. May be higher for luxury buildings or if you have pets. Must be held in an interest-bearing account (buildings with 6+ units). Must be returned within 14 days of move-out with itemized deductions.'
      },
      {
        question: 'What happens if I need to break my lease?',
        answer: 'Breaking a lease early typically involves: paying rent until landlord finds a new tenant, possible early termination fee (usually 1-2 months\' rent), and loss of security deposit in some cases. Check your lease for specific terms\u2014some have "buyout" clauses.'
      },
      {
        question: 'Can I sublet my NYC apartment?',
        answer: 'New York State law gives tenants the right to sublet with landlord\'s permission. Must get written permission from landlord, landlord can refuse for valid reasons, typically allowed for up to 2 years, you remain responsible for the apartment. Check your lease\u2014some buildings have stricter rules.'
      }
    ]
  },
  {
    category: 'Neighborhoods & Lifestyle',
    questions: [
      {
        question: 'Which NYC neighborhoods have the most no-fee apartments?',
        answer: 'Top neighborhoods for no-fee apartments:\n\u2022 Manhattan: Upper East Side, Chelsea, Financial District, Murray Hill\n\u2022 Brooklyn: Williamsburg, Downtown Brooklyn, DUMBO\n\u2022 Queens: Long Island City, Astoria\n\nGenerally, areas with newer developments and large management companies have more no-fee options.'
      },
      {
        question: 'When is the best time to look for an apartment in NYC?',
        answer: 'Best times for deals: Winter (December-February) with less competition and more concessions, mid-month when most people move month-end, and off-peak seasons in fall and early spring.\n\nMost competitive times: May-September (peak moving season), end of month (everyone wants same move-in dates), and August-September for college students.'
      },
      {
        question: 'How quickly do NYC apartments get rented?',
        answer: 'The NYC rental market moves fast. Good apartments can rent within 24-48 hours. Popular neighborhoods during peak season (spring/summer) are fastest. Have your application materials ready to submit immediately. Be prepared to make decisions quickly\u2014but not impulsively.'
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
