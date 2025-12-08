import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

const BestNeighborhoods = () => {
  const neighborhoods = [
    {
      name: 'Upper East Side',
      borough: 'Manhattan',
      studio: '$2,400 - $3,200',
      oneBr: '$3,000 - $4,500',
      twoBr: '$4,200 - $6,500',
      highlights: ['Central Park', 'Museum Mile', 'Family-friendly', 'Multiple subway lines (4, 5, 6, Q)'],
      bestFor: 'Young professionals, families, museum lovers'
    },
    {
      name: 'Chelsea',
      borough: 'Manhattan',
      studio: '$2,800 - $3,800',
      oneBr: '$3,500 - $5,200',
      twoBr: '$5,000 - $8,000',
      highlights: ['Chelsea Market', 'The High Line', 'Art galleries', 'Trendy restaurants'],
      bestFor: 'Creatives, foodies, active lifestyle enthusiasts'
    },
    {
      name: 'Financial District',
      borough: 'Manhattan',
      studio: '$2,600 - $3,500',
      oneBr: '$3,200 - $4,800',
      twoBr: '$4,500 - $7,000',
      highlights: ['Waterfront parks', 'Seaport District', 'Quiet on weekends', 'Multiple subway lines'],
      bestFor: 'Finance professionals, history buffs, quiet seekers'
    },
    {
      name: 'Williamsburg',
      borough: 'Brooklyn',
      studio: '$2,200 - $3,200',
      oneBr: '$2,800 - $4,200',
      twoBr: '$3,800 - $6,000',
      highlights: ['Arts scene', 'Brooklyn Brewery', 'Waterfront parks', 'L and G trains'],
      bestFor: 'Artists, musicians, young professionals'
    },
    {
      name: 'Long Island City',
      borough: 'Queens',
      studio: '$2,000 - $2,800',
      oneBr: '$2,500 - $3,800',
      twoBr: '$3,200 - $5,200',
      highlights: ['Manhattan skyline views', 'MoMA PS1', 'Gantry Plaza Park', 'One stop to Midtown'],
      bestFor: 'Commuters, art lovers, value seekers'
    }
  ];

  return (
    <div className='min-h-screen bg-gray-50'>
      <Helmet>
        <title>Best NYC Neighborhoods for No-Fee Apartments | 2024 Guide</title>
        <meta name='description' content='Discover the top NYC neighborhoods with the most no-fee apartment listings. Compare prices, amenities, and lifestyle in Manhattan, Brooklyn, and Queens.' />
        <meta name='keywords' content='NYC neighborhoods, no fee apartments by neighborhood, best areas to rent NYC, affordable NYC neighborhoods' />
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
          <h1 className='text-4xl font-bold text-gray-900 mb-4'>Top 10 NYC Neighborhoods for No-Fee Apartments in 2024</h1>
          
          <p className='text-lg text-gray-600 mb-8'>Not all NYC neighborhoods are created equal when it comes to no-fee apartment availability. Some areas have significantly more landlord-paid fee listings than others.</p>

          {neighborhoods.map((neighborhood, index) => (
            <div key={index} className='mb-8 pb-8 border-b border-gray-200 last:border-0'>
              <h2 className='text-3xl font-bold text-gray-900 mb-2'>{index + 1}. {neighborhood.name}, {neighborhood.borough}</h2>
              
              <div className='bg-blue-50 p-4 rounded-lg mb-4'>
                <h3 className='font-bold text-gray-900 mb-2'>Average Rent:</h3>
                <ul className='text-gray-700 space-y-1'>
                  <li>Studio: {neighborhood.studio}</li>
                  <li>1BR: {neighborhood.oneBr}</li>
                  <li>2BR: {neighborhood.twoBr}</li>
                </ul>
              </div>

              <h3 className='text-xl font-bold text-gray-900 mb-2'>Neighborhood Highlights:</h3>
              <ul className='list-disc list-inside space-y-1 text-gray-700 mb-3'>
                {neighborhood.highlights.map((highlight, i) => (
                  <li key={i}>{highlight}</li>
                ))}
              </ul>

              <p className='text-gray-700'><strong>Best for:</strong> {neighborhood.bestFor}</p>
            </div>
          ))}

          <h2 className='text-3xl font-bold text-gray-900 mt-8 mb-4'>How to Choose Your NYC Neighborhood</h2>
          
          <div className='space-y-4 mb-8'>
            <div>
              <h4 className='font-bold text-gray-900 mb-2'>Commute Time</h4>
              <ul className='list-disc list-inside text-gray-700 space-y-1'>
                <li>Calculate door-to-door time during rush hour</li>
                <li>Consider backup transit options</li>
                <li>Weekend service can be very different</li>
              </ul>
            </div>

            <div>
              <h4 className='font-bold text-gray-900 mb-2'>Budget Reality</h4>
              <ul className='list-disc list-inside text-gray-700 space-y-1'>
                <li>Do not spend more than 30% of gross income on rent</li>
                <li>Factor in utilities</li>
                <li>Consider amenity fees in luxury buildings</li>
              </ul>
            </div>
          </div>

          <div className='bg-blue-50 p-6 rounded-lg mt-8'>
            <h2 className='text-2xl font-bold text-gray-900 mb-4'>Start Your Neighborhood Search</h2>
            <p className='text-gray-700 mb-4'>Ready to explore no-fee apartments in these neighborhoods? Browse available rentals and find your perfect NYC home.</p>
            <Link to='/' className='inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition'>
              Explore Neighborhoods
            </Link>
          </div>
        </div>
      </article>
    </div>
  );
};

export default BestNeighborhoods;