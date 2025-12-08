import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { Home, CheckSquare } from 'lucide-react';

const ApartmentChecklist = () => {
  return (
    <div className=\"min-h-screen bg-gray-50\">
      <Helmet>
        <title>NYC Apartment Hunting Checklist: Complete Guide | NoFeesApts.com</title>
        <meta name=\"description\" content=\"Don't miss crucial steps in your NYC apartment search. Complete checklist covering documents, viewing tips, lease terms, and move-in requirements.\" />
        <meta name=\"keywords\" content=\"NYC apartment checklist, apartment hunting tips NYC, what to know before renting NYC, NYC rental requirements\" />
      </Helmet>

      <div className=\"bg-white border-b\">
        <div className=\"max-w-4xl mx-auto px-4 py-4\">
          <div className=\"flex items-center gap-4\">
            <Link to=\"/\" className=\"flex items-center gap-2 text-gray-600 hover:text-gray-900\">
              <Home className=\"w-4 h-4\" />
              Home
            </Link>
            <span className=\"text-gray-300\">/</span>
            <Link to=\"/blog\" className=\"text-gray-600 hover:text-gray-900\">Blog</Link>
          </div>
        </div>
      </div>

      <article className=\"max-w-4xl mx-auto px-4 py-12\">
        <div className=\"bg-white rounded-lg shadow-sm p-8\">
          <h1 className=\"text-4xl font-bold text-gray-900 mb-4\">NYC Apartment Hunting Checklist: What to Know Before You Rent</h1>
          
          <p className=\"text-lg text-gray-600 mb-8\">Renting an apartment in New York City requires preparation, speed, and attention to detail. This comprehensive checklist will help you navigate the process from search to move-in day.</p>

          <h2 className=\"text-3xl font-bold text-gray-900 mt-8 mb-4\">Before You Start Your Search</h2>

          <h3 className=\"text-2xl font-bold text-gray-900 mt-6 mb-3\"><CheckSquare className=\"inline w-6 h-6 mr-2\" />Financial Preparation</h3>
          <div className=\"bg-blue-50 p-4 rounded-lg mb-4\">
            <ul className=\"space-y-2 text-gray-700\">
              <li><strong>☐ Calculate Your Budget</strong>
                <ul className=\"ml-6 mt-1 space-y-1\">
                  <li>• Maximum monthly rent: 30% of gross monthly income</li>
                  <li>• One-time costs: First month + security deposit + moving costs</li>
                  <li>• Monthly expenses: Utilities, internet, renter's insurance</li>
                </ul>
              </li>
              <li><strong>☐ Check Your Credit Score</strong>
                <ul className=\"ml-6 mt-1 space-y-1\">
                  <li>• Pull your free credit report from AnnualCreditReport.com</li>
                  <li>• Fix any errors before applying</li>
                  <li>• Know your score (most landlords require 650+)</li>
                </ul>
              </li>
              <li><strong>☐ Save Moving Money</strong>
                <ul className=\"ml-6 mt-1 space-y-1\">
                  <li>• First month's rent</li>
                  <li>• Security deposit (typically 1 month's rent)</li>
                  <li>• Moving costs ($500-$2,000 depending on distance)</li>
                  <li>• Furniture and setup costs</li>
                </ul>
              </li>
            </ul>
          </div>

          <h3 className=\"text-2xl font-bold text-gray-900 mt-6 mb-3\">Required Documents</h3>
          <ul className=\"list-disc list-inside space-y-2 text-gray-700 mb-4\">\n            <li>Last 2-3 pay stubs</li>
            <li>Last 2 years of tax returns</li>
            <li>Bank statements (last 2-3 months)</li>
            <li>Employment verification letter</li>
            <li>Previous landlord references</li>
          </ul>

          <h2 className=\"text-3xl font-bold text-gray-900 mt-8 mb-4\">During Your Search</h2>

          <h3 className=\"text-2xl font-bold text-gray-900 mt-6 mb-3\">Questions to Ask at Every Viewing</h3>
          <ul className=\"list-disc list-inside space-y-2 text-gray-700 mb-4\">
            <li>Who pays the broker fee? (Confirm it's truly no-fee)</li>
            <li>What's included in the rent? (Heat, hot water, gas?)</li>
            <li>What are the average utility costs?</li>
            <li>What's the lease term? (12 months standard)</li>
            <li>When is the apartment available?</li>
            <li>What's the application process timeline?</li>
            <li>Is renters insurance required?</li>
            <li>What's the pet policy? (Weight limits, deposit, monthly fee?)</li>
          </ul>

          <h3 className=\"text-2xl font-bold text-gray-900 mt-6 mb-3\">Things to Check in Person</h3>
          <div className=\"grid md:grid-cols-2 gap-4 mb-4\">
            <div className=\"bg-gray-50 p-4 rounded-lg\">
              <ul className=\"space-y-2 text-gray-700\">
                <li><strong>Water pressure</strong> - Run all faucets and shower</li>
                <li><strong>Hot water</strong> - Wait to see how fast it heats up</li>
                <li><strong>Windows</strong> - Open and close, check for drafts</li>
                <li><strong>Outlets</strong> - Count outlets in each room</li>
                <li><strong>Storage</strong> - Measure closet space</li>
              </ul>
            </div>
            <div className=\"bg-gray-50 p-4 rounded-lg\">
              <ul className=\"space-y-2 text-gray-700\">
                <li><strong>Cell reception</strong> - Test your phone signal</li>
                <li><strong>Noise levels</strong> - Listen for street/neighbor noise</li>
                <li><strong>Appliances</strong> - Test stove, fridge, dishwasher</li>
                <li><strong>Heat/AC</strong> - Turn on systems</li>
                <li><strong>Door locks</strong> - Check all locks function</li>
              </ul>
            </div>
          </div>

          <h2 className=\"text-3xl font-bold text-gray-900 mt-8 mb-4\">The Application Process</h2>

          <h3 className=\"text-2xl font-bold text-gray-900 mt-6 mb-3\">Income Requirements</h3>
          <div className=\"bg-blue-50 p-4 rounded-lg mb-4\">
            <ul className=\"space-y-2 text-gray-700\">
              <li><strong>Standard:</strong> 40x monthly rent in annual income</li>
              <li><strong>Example:</strong> For $3,000/month rent, you need $120,000 annual income</li>
              <li><strong>Guarantor option:</strong> 80x monthly rent if you don't qualify</li>
              <li><strong>Third-party services:</strong> Insurent, TheGuarantors</li>
            </ul>
          </div>

          <h3 className=\"text-2xl font-bold text-gray-900 mt-6 mb-3\">Review the Lease Carefully</h3>
          <ul className=\"list-disc list-inside space-y-2 text-gray-700 mb-4\">
            <li>Read every line before signing</li>
            <li>Understand automatic renewal clauses</li>
            <li>Note lease end date</li>
            <li>Check rent increase terms</li>
            <li>Understand early termination penalties</li>
            <li>Verify all promises are in writing</li>
          </ul>

          <h2 className=\"text-3xl font-bold text-gray-900 mt-8 mb-4\">Red Flags to Watch For</h2>
          
          <div className=\"bg-red-50 border-l-4 border-red-400 p-4 mb-4\">
            <h3 className=\"text-xl font-bold text-gray-900 mb-2\">🚩 Immediate Deal Breakers</h3>
            <ul className=\"list-disc list-inside space-y-1 text-gray-700\">
              <li>Landlord won't let you view the apartment</li>
              <li>Requests for payment before viewing</li>
              <li>Significantly below-market pricing</li>
              <li>Can't verify landlord identity</li>
              <li>Lease terms that seem too good to be true</li>
              <li>Pressure to sign immediately without reading</li>
            </ul>
          </div>

          <h2 className=\"text-3xl font-bold text-gray-900 mt-8 mb-4\">NYC Tenant Rights to Know</h2>
          
          <div className=\"bg-green-50 p-4 rounded-lg mb-4\">
            <h3 className=\"text-xl font-bold text-gray-900 mb-2\">You Have the Right To:</h3>
            <ul className=\"list-disc list-inside space-y-2 text-gray-700\">
              <li>A habitable apartment (heat, hot water, no pests)</li>
              <li>A signed lease in your language</li>
              <li>Return of security deposit (minus lawful deductions)</li>
              <li>14 days notice for rent increases</li>
              <li>Privacy (24-hour notice for non-emergency entry)</li>
              <li>Make reasonable modifications if disabled</li>
            </ul>
          </div>

          <h2 className=\"text-3xl font-bold text-gray-900 mt-8 mb-4\">Final Tips for Success</h2>
          
          <div className=\"bg-yellow-50 p-4 rounded-lg mb-8\">
            <h3 className=\"font-bold text-gray-900 mb-2\">Speed Matters in NYC</h3>
            <ul className=\"list-disc list-inside space-y-1 text-gray-700\">
              <li>Have application materials ready to submit immediately</li>
              <li>Decision time is often 24-48 hours</li>
              <li>Don't wait to apply for your top choice</li>
            </ul>
            
            <h3 className=\"font-bold text-gray-900 mt-4 mb-2\">Trust Your Gut</h3>
            <ul className=\"list-disc list-inside space-y-1 text-gray-700\">
              <li>If something feels off, it probably is</li>
              <li>Don't settle due to pressure</li>
              <li>There's always another apartment</li>
            </ul>
          </div>

          <div className=\"bg-blue-50 p-6 rounded-lg mt-8\">
            <h2 className=\"text-2xl font-bold text-gray-900 mb-4\">Ready to Find Your NYC Home?</h2>
            <p className=\"text-gray-700 mb-4\">Start your no-fee apartment search on NoFeesApts.com with confidence, knowing you have the complete checklist for success.</p>
            <Link to=\"/\" className=\"inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition\">
              Start Your Search
            </Link>
          </div>
        </div>
      </article>
    </div>
  );
};

export default ApartmentChecklist;
