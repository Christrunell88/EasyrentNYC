import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { Home, CheckSquare } from 'lucide-react';

const ApartmentChecklist = () => {
  return (
    <div className='min-h-screen bg-gray-50'>
      <Helmet>
        <title>NYC Apartment Hunting Checklist: Complete Guide | NoFeesApts.com</title>
        <meta name='description' content='Do not miss crucial steps in your NYC apartment search. Complete checklist covering documents, viewing tips, lease terms, and move-in requirements.' />
        <meta name='keywords' content='NYC apartment checklist, apartment hunting tips NYC, what to know before renting NYC, NYC rental requirements, documents needed for NYC apartment, how to rent in NYC first time, NYC apartment application tips, credit score for NYC apartment, guarantor NYC rental' />
      </Helmet>

      <div className='bg-white border-b'>
        <div className='max-w-4xl mx-auto px-4 py-4'>
          <div className='flex items-center gap-4'>
            <Link to='/' className='flex items-center gap-2 text-gray-600 hover:text-gray-900'>
              <Home className='w-4 h-4' />
              Home
            </Link>
            <span className='text-gray-300'>/</span>
            <Link to='/blog' className='text-gray-600 hover:text-gray-900'>Blog</Link>
          </div>
        </div>
      </div>

      <article className='max-w-4xl mx-auto px-4 py-12'>
        <div className='bg-white rounded-lg shadow-sm p-8'>
          <h1 className='text-4xl font-bold text-gray-900 mb-4'>NYC Apartment Hunting Checklist: What to Know Before You Rent</h1>
          
          <p className='text-lg text-gray-600 mb-8'>Renting an apartment in New York City requires preparation, speed, and attention to detail. This comprehensive checklist will help you navigate the process from search to move-in day.</p>

          <h2 className='text-3xl font-bold text-gray-900 mt-8 mb-4'>Before You Start Your Search</h2>

          <h3 className='text-2xl font-bold text-gray-900 mt-6 mb-3'><CheckSquare className='inline w-6 h-6 mr-2' />Financial Preparation</h3>
          <div className='bg-blue-50 p-4 rounded-lg mb-4'>
            <ul className='space-y-3 text-gray-700'>
              <li>
                <strong>Calculate Your Budget</strong>
                <ul className='ml-6 mt-1 space-y-1'>
                  <li>• Maximum monthly rent: 30% of gross income</li>
                  <li>• One-time costs: First month plus security deposit</li>
                  <li>• Monthly expenses: Utilities, internet, insurance</li>
                </ul>
              </li>
              <li>
                <strong>Check Your Credit Score</strong>
                <ul className='ml-6 mt-1 space-y-1'>
                  <li>• Pull free report from AnnualCreditReport.com</li>
                  <li>• Most landlords require 650 or higher</li>
                </ul>
              </li>
            </ul>
          </div>

          <h3 className='text-2xl font-bold text-gray-900 mt-6 mb-3'>Required Documents</h3>
          <ul className='list-disc list-inside space-y-2 text-gray-700 mb-4'>
            <li>Last 2-3 pay stubs</li>
            <li>Last 2 years of tax returns</li>
            <li>Bank statements (2-3 months)</li>
            <li>Employment verification letter</li>
            <li>Previous landlord references</li>
          </ul>

          <h2 className='text-3xl font-bold text-gray-900 mt-8 mb-4'>During Your Search</h2>

          <h3 className='text-2xl font-bold text-gray-900 mt-6 mb-3'>Questions to Ask at Every Viewing</h3>
          <ul className='list-disc list-inside space-y-2 text-gray-700 mb-4'>
            <li>Who pays the broker fee?</li>
            <li>What is included in the rent?</li>
            <li>What are the average utility costs?</li>
            <li>What is the lease term?</li>
            <li>When is the apartment available?</li>
            <li>What is the pet policy?</li>
          </ul>

          <h3 className='text-2xl font-bold text-gray-900 mt-6 mb-3'>Things to Check in Person</h3>
          <div className='grid md:grid-cols-2 gap-4 mb-4'>
            <div className='bg-gray-50 p-4 rounded-lg'>
              <ul className='space-y-2 text-gray-700'>
                <li><strong>Water pressure</strong> - Run all faucets</li>
                <li><strong>Hot water</strong> - Check heating speed</li>
                <li><strong>Windows</strong> - Check for drafts</li>
                <li><strong>Outlets</strong> - Count in each room</li>
              </ul>
            </div>
            <div className='bg-gray-50 p-4 rounded-lg'>
              <ul className='space-y-2 text-gray-700'>
                <li><strong>Cell reception</strong> - Test your phone</li>
                <li><strong>Noise levels</strong> - Listen carefully</li>
                <li><strong>Appliances</strong> - Test everything</li>
                <li><strong>Door locks</strong> - Check function</li>
              </ul>
            </div>
          </div>

          <h2 className='text-3xl font-bold text-gray-900 mt-8 mb-4'>The Application Process</h2>

          <h3 className='text-2xl font-bold text-gray-900 mt-6 mb-3'>Income Requirements</h3>
          <div className='bg-blue-50 p-4 rounded-lg mb-4'>
            <ul className='space-y-2 text-gray-700'>
              <li><strong>Standard:</strong> 40x monthly rent in annual income</li>
              <li><strong>Example:</strong> For $3,000/month rent, you need $120,000 annual income</li>
              <li><strong>Guarantor option:</strong> 80x monthly rent if you do not qualify</li>
            </ul>
          </div>

          <h2 className='text-3xl font-bold text-gray-900 mt-8 mb-4'>Red Flags to Watch For</h2>
          
          <div className='bg-red-50 border-l-4 border-red-400 p-4 mb-4'>
            <h3 className='text-xl font-bold text-gray-900 mb-2'>Immediate Deal Breakers</h3>
            <ul className='list-disc list-inside space-y-1 text-gray-700'>
              <li>Landlord will not let you view apartment</li>
              <li>Requests for payment before viewing</li>
              <li>Significantly below-market pricing</li>
              <li>Cannot verify landlord identity</li>
              <li>Pressure to sign immediately</li>
            </ul>
          </div>

          <h2 className='text-3xl font-bold text-gray-900 mt-8 mb-4'>NYC Tenant Rights</h2>
          
          <div className='bg-green-50 p-4 rounded-lg mb-4'>
            <h3 className='text-xl font-bold text-gray-900 mb-2'>You Have the Right To:</h3>
            <ul className='list-disc list-inside space-y-2 text-gray-700'>
              <li>A habitable apartment</li>
              <li>A signed lease in your language</li>
              <li>Return of security deposit</li>
              <li>Privacy (24-hour notice for entry)</li>
            </ul>
          </div>

          <div className='bg-blue-50 p-6 rounded-lg mt-8'>
            <h2 className='text-2xl font-bold text-gray-900 mb-4'>Ready to Find Your NYC Home?</h2>
            <p className='text-gray-700 mb-4'>Start your no-fee apartment search on NoFeesApts.com with confidence.</p>
            <Link to='/' className='inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition'>
              Start Your Search
            </Link>
          </div>
        </div>
      </article>
    </div>
  );
};

export default ApartmentChecklist;