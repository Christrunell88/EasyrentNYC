import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Building2, MapPin, DollarSign, TrendingUp, ArrowRight, Home, Train, Utensils, TreePine, ChevronDown, ChevronUp, Clock, Users, Shield } from 'lucide-react';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import SEO from '../components/SEO';
import { Helmet } from 'react-helmet-async';

const LocationPage = () => {
  const { location } = useParams();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ totalUnits: 0, avgRent: 0, buildings: [] });
  const [expandedFaq, setExpandedFaq] = useState(null);

  const locationData = {
    manhattan: {
      name: 'Manhattan',
      title: 'No Fee Apartments in Manhattan, NYC',
      description: 'Find your perfect Manhattan apartment with zero broker fees. Browse verified no-fee apartments in Upper West Side, Upper East Side, Midtown, and Downtown Manhattan.',
      longDescription: `Manhattan is the heart of New York City and the most sought-after borough for renters. From the tree-lined streets of the Upper West Side to the bustling energy of Midtown, Manhattan offers unparalleled access to world-class dining, entertainment, and career opportunities. While traditionally known for high broker fees (often 12-15% of annual rent), our curated no-fee listings help you save $4,000-$8,000 on your move.`,
      neighborhoods: ['Upper West Side', 'Upper East Side', 'Midtown', 'Downtown', 'Financial District', 'Tribeca', 'Chelsea', 'Hell\'s Kitchen'],
      highlights: [
        'Heart of NYC with iconic landmarks',
        'Excellent public transportation (all subway lines)',
        'World-class dining and entertainment',
        'Central Park and waterfront access'
      ],
      commuteInfo: {
        subway: 'All major subway lines (1,2,3,4,5,6,7,A,C,E,B,D,F,M,N,Q,R,W,L)',
        avgCommute: '15-30 min to most NYC destinations',
        walkScore: 95
      },
      lifestyle: {
        dining: 'Michelin-starred restaurants to iconic delis',
        nightlife: 'Broadway, jazz clubs, rooftop bars',
        outdoors: 'Central Park, Hudson River Greenway, High Line'
      },
      avgRent: '$3,200 - $4,500',
      brokerFeeSavings: '$4,000 - $8,000',
      seoKeywords: 'no fee apartments manhattan, manhattan apartments no broker fee, upper west side apartments, upper east side rentals, luxury no fee apartments manhattan, cheap apartments manhattan no broker, rent manhattan without broker fee, best no fee deals manhattan, midtown apartments no fee, chelsea no broker fee',
      faqs: [
        {
          q: 'How much can I save with a no-fee apartment in Manhattan?',
          a: 'Manhattan broker fees typically range from 12-15% of annual rent. On a $3,500/month apartment, that\'s $5,040-$6,300. Our no-fee listings save you this entire amount.'
        },
        {
          q: 'Which Manhattan neighborhoods have the most no-fee apartments?',
          a: 'Newer developments in Hudson Yards, Financial District, and Midtown West tend to have more no-fee options as landlords cover broker costs to fill units quickly.'
        },
        {
          q: 'What\'s the average rent for a no-fee apartment in Manhattan?',
          a: 'Studios start around $2,800/month, one-bedrooms average $3,500-$4,500, and two-bedrooms range from $4,500-$7,000+ depending on neighborhood and amenities.'
        },
        {
          q: 'Are no-fee apartments in Manhattan lower quality?',
          a: 'Not at all. No-fee simply means the landlord pays the broker instead of you. Many luxury buildings with doormen, gyms, and rooftop access are no-fee.'
        }
      ],
      relatedLocations: ['brooklyn', 'queens', 'jersey-city', 'hoboken']
    },
    brooklyn: {
      name: 'Brooklyn',
      title: 'No Fee Apartments in Brooklyn, NYC',
      description: 'Discover Brooklyn\'s best no-fee apartments. From trendy Williamsburg to family-friendly Park Slope, find your Brooklyn home without paying broker fees.',
      longDescription: `Brooklyn has transformed from a Manhattan alternative to a destination in its own right. With world-renowned restaurants, a thriving arts scene, and diverse neighborhoods from hipster Williamsburg to historic Brooklyn Heights, the borough offers something for everyone. Brooklyn's no-fee market has grown significantly, especially in newer developments along the waterfront.`,
      neighborhoods: ['Williamsburg', 'Downtown Brooklyn', 'Park Slope', 'DUMBO', 'Brooklyn Heights', 'Greenpoint', 'Bushwick', 'Bedford-Stuyvesant'],
      highlights: [
        'Vibrant arts and culture scene',
        'Diverse neighborhoods with unique character',
        'Excellent restaurants and nightlife',
        'Waterfront parks and Brooklyn Bridge Park'
      ],
      commuteInfo: {
        subway: 'L, G, J, M, Z, 2, 3, 4, 5, A, C, F, N, Q, R lines',
        avgCommute: '20-40 min to Manhattan',
        walkScore: 89
      },
      lifestyle: {
        dining: 'Farm-to-table restaurants, ethnic cuisine, artisan coffee',
        nightlife: 'Live music venues, craft cocktail bars, comedy clubs',
        outdoors: 'Prospect Park, Brooklyn Bridge Park, beaches'
      },
      avgRent: '$2,400 - $3,800',
      brokerFeeSavings: '$3,500 - $5,500',
      seoKeywords: 'no fee apartments brooklyn, brooklyn apartments no broker fee, williamsburg apartments, dumbo rentals, affordable brooklyn apartments no fee, how to find no fee brooklyn, park slope no broker fee, downtown brooklyn rentals, greenpoint no fee',
      faqs: [
        {
          q: 'Is Brooklyn cheaper than Manhattan for no-fee apartments?',
          a: 'Yes, Brooklyn averages 15-25% lower rent than Manhattan. A one-bedroom in Williamsburg might be $3,200 vs $4,000+ in comparable Manhattan areas.'
        },
        {
          q: 'Which Brooklyn neighborhoods are best for young professionals?',
          a: 'Williamsburg, DUMBO, and Downtown Brooklyn are popular for their nightlife and quick Manhattan commutes. Greenpoint and Bushwick offer more affordable options with creative vibes.'
        },
        {
          q: 'How long is the commute from Brooklyn to Manhattan?',
          a: 'It varies by neighborhood: DUMBO/Downtown Brooklyn is 10-15 minutes, Williamsburg 15-20 minutes, Park Slope 25-35 minutes to Midtown.'
        },
        {
          q: 'Are there luxury no-fee apartments in Brooklyn?',
          a: 'Absolutely. Downtown Brooklyn and the Williamsburg waterfront have numerous luxury high-rises with amenities like pools, gyms, and concierge services—all no-fee.'
        }
      ],
      relatedLocations: ['manhattan', 'queens', 'williamsburg', 'jersey-city']
    },
    queens: {
      name: 'Queens',
      title: 'No Fee Apartments in Queens, NYC',
      description: 'Queens offers the best value in NYC. Browse no-fee apartments in Long Island City, Astoria, and Forest Hills. More space, lower rent, no broker fees.',
      longDescription: `Queens is NYC's most ethnically diverse borough and offers exceptional value for renters. Long Island City provides stunning Manhattan skyline views and a quick commute, while Astoria delivers a village-like feel with incredible Greek, Middle Eastern, and Asian cuisine. Queens apartments typically offer more square footage per dollar than Manhattan or Brooklyn.`,
      neighborhoods: ['Long Island City', 'Astoria', 'Forest Hills', 'Flushing', 'Jackson Heights', 'Sunnyside', 'Ridgewood', 'Woodside'],
      highlights: [
        'Most affordable borough with great value',
        'Direct access to Manhattan (7, N, W, E trains)',
        'Diverse international food scene',
        'Family-friendly with excellent schools'
      ],
      commuteInfo: {
        subway: '7, N, W, E, M, R, F, G lines',
        avgCommute: '20-45 min to Manhattan',
        walkScore: 82
      },
      lifestyle: {
        dining: 'Authentic ethnic cuisines from 100+ countries',
        nightlife: 'Beer gardens, lounges, local bars',
        outdoors: 'Flushing Meadows Park, Gantry Plaza, beaches'
      },
      avgRent: '$1,800 - $3,200',
      brokerFeeSavings: '$2,500 - $4,500',
      seoKeywords: 'no fee apartments queens, queens apartments no broker fee, long island city apartments, astoria rentals, cheap no fee apartments queens, affordable queens rentals, best value nyc apartments no fee, flushing apartments',
      faqs: [
        {
          q: 'Why is Queens more affordable than Manhattan or Brooklyn?',
          a: 'Queens has more housing supply, larger apartments, and slightly longer commutes. You can often get a spacious one-bedroom for the price of a Manhattan studio.'
        },
        {
          q: 'What\'s the best Queens neighborhood for Manhattan commuters?',
          a: 'Long Island City is just one stop from Midtown on the 7 train (5-10 minutes). Astoria is also excellent with N/W trains reaching Midtown in 15-20 minutes.'
        },
        {
          q: 'Are Queens apartments bigger than Manhattan apartments?',
          a: 'Generally yes. A Queens one-bedroom averages 650-800 sq ft compared to 550-650 sq ft in Manhattan for similar prices.'
        },
        {
          q: 'Is Queens safe for renters?',
          a: 'Queens is one of NYC\'s safest boroughs. Areas like Forest Hills, Astoria, and Long Island City have low crime rates and strong community feel.'
        }
      ],
      relatedLocations: ['long-island-city', 'brooklyn', 'manhattan', 'bronx']
    },
    'long-island-city': {
      name: 'Long Island City',
      title: 'No Fee Apartments in Long Island City, Queens',
      description: 'Discover Long Island City\'s newest no-fee apartments. Minutes from Manhattan with modern amenities and stunning skyline views. No broker fees.',
      longDescription: `Long Island City (LIC) has rapidly transformed into one of NYC's most desirable neighborhoods. With a 5-minute subway ride to Midtown Manhattan, stunning skyline views, and numerous new luxury developments, LIC offers the best of both worlds. The area's explosive growth means many buildings offer no-fee apartments to attract tenants.`,
      neighborhoods: ['Hunters Point', 'Court Square', 'Dutch Kills', 'Queensboro Plaza'],
      highlights: [
        'One stop to Manhattan (7, E, M, G trains)',
        'Modern high-rise buildings with amenities',
        'Waterfront parks and East River views',
        'Rapidly growing arts and dining scene'
      ],
      commuteInfo: {
        subway: '7, E, M, G, N, W lines',
        avgCommute: '5-15 min to Midtown Manhattan',
        walkScore: 91
      },
      lifestyle: {
        dining: 'Trendy restaurants, rooftop bars, artisan cafes',
        nightlife: 'Growing scene with lounges and beer halls',
        outdoors: 'Gantry Plaza State Park, Hunter\'s Point South Park'
      },
      avgRent: '$2,200 - $3,600',
      brokerFeeSavings: '$3,000 - $5,000',
      seoKeywords: 'no fee apartments long island city, lic apartments no broker fee, hunters point apartments, luxury no fee lic, long island city rentals near manhattan, waterfront apartments lic no fee, court square apartments',
      faqs: [
        {
          q: 'Why do so many LIC apartments have no broker fees?',
          a: 'LIC has seen massive development with many new buildings competing for tenants. Landlords often cover broker fees as an incentive to fill units quickly.'
        },
        {
          q: 'How close is Long Island City to Manhattan?',
          a: 'LIC is incredibly close—just one stop on the 7 train to Grand Central (5 minutes) or Times Square. The E/M trains reach Midtown in under 10 minutes.'
        },
        {
          q: 'What amenities do LIC luxury buildings offer?',
          a: 'Most newer buildings include gyms, rooftop decks with Manhattan views, doormen, package rooms, bike storage, and sometimes pools or co-working spaces.'
        },
        {
          q: 'Is Long Island City good for families?',
          a: 'Yes! LIC has excellent waterfront parks, good schools, and a safe environment. Many families choose LIC for space and value while staying close to Manhattan.'
        }
      ],
      relatedLocations: ['queens', 'astoria', 'manhattan', 'brooklyn']
    },
    williamsburg: {
      name: 'Williamsburg',
      title: 'No Fee Apartments in Williamsburg, Brooklyn',
      description: 'Find trendy Williamsburg apartments with no broker fees. Brooklyn\'s hottest neighborhood for young professionals and creatives. Zero fees guaranteed.',
      longDescription: `Williamsburg is Brooklyn's most iconic neighborhood, known for its creative energy, world-class dining, and vibrant nightlife. Once an industrial area, it's now home to tech workers, artists, and young professionals. The waterfront has seen massive development with luxury high-rises offering stunning Manhattan views—many of which are no-fee.`,
      neighborhoods: ['North Williamsburg', 'South Williamsburg', 'East Williamsburg', 'Northside'],
      highlights: [
        'Hip neighborhood with vibrant nightlife',
        'L train to Manhattan in 10 minutes',
        'Trendy restaurants, bars, and music venues',
        'Waterfront parks and Brooklyn Brewery'
      ],
      commuteInfo: {
        subway: 'L, G, J, M, Z lines',
        avgCommute: '10-20 min to Manhattan',
        walkScore: 94
      },
      lifestyle: {
        dining: 'Michelin-recommended spots, food halls, brunch culture',
        nightlife: 'Live music, rooftop bars, clubs',
        outdoors: 'Domino Park, McCarren Park, East River waterfront'
      },
      avgRent: '$2,600 - $4,200',
      brokerFeeSavings: '$3,500 - $6,000',
      seoKeywords: 'no fee apartments williamsburg, williamsburg brooklyn apartments no broker fee, north williamsburg rentals, cheap williamsburg apartments, how to find no fee williamsburg, hipster apartments brooklyn no fee, south williamsburg no fee',
      faqs: [
        {
          q: 'Is Williamsburg still trendy or overpriced?',
          a: 'Williamsburg remains one of NYC\'s most desirable neighborhoods. While not cheap, no-fee apartments help offset costs, and the lifestyle/convenience justify prices for many.'
        },
        {
          q: 'What\'s the L train situation in Williamsburg?',
          a: 'The L train is fully operational and runs 24/7. It connects to Manhattan (14th Street) in about 10 minutes, with trains every 3-5 minutes during rush hour.'
        },
        {
          q: 'Where are the best no-fee apartments in Williamsburg?',
          a: 'The waterfront (North Williamsburg) has the most no-fee luxury options. South Williamsburg and East Williamsburg offer more affordable no-fee alternatives.'
        },
        {
          q: 'Is Williamsburg good for remote workers?',
          a: 'Excellent. The neighborhood has numerous cafes, co-working spaces, and most luxury buildings include work-from-home amenities like lounges and private offices.'
        }
      ],
      relatedLocations: ['brooklyn', 'greenpoint', 'bushwick', 'manhattan']
    },
    'jersey-city': {
      name: 'Jersey City',
      title: 'No Fee Apartments in Jersey City, NJ',
      description: 'Jersey City offers affordable NYC-area living with no broker fees. Quick PATH train access to Manhattan. Modern apartments at lower prices.',
      longDescription: `Jersey City has emerged as a top alternative to Manhattan, offering modern apartments, stunning NYC skyline views, and significant cost savings. The PATH train provides quick access to Manhattan (10-20 minutes), while Jersey City's own downtown has developed into a vibrant area with restaurants, bars, and waterfront parks. Unlike NYC, New Jersey has no broker fee tradition for renters.`,
      neighborhoods: ['Downtown Jersey City', 'Newport', 'Journal Square', 'Paulus Hook', 'Hamilton Park', 'The Heights'],
      highlights: [
        '10-20 minute PATH train to Manhattan',
        'Stunning NYC skyline views',
        'Lower taxes and cost of living',
        'Family-friendly with great schools'
      ],
      commuteInfo: {
        subway: 'PATH train (Grove Street, Exchange Place, Newport)',
        avgCommute: '10-25 min to Manhattan',
        walkScore: 87
      },
      lifestyle: {
        dining: 'Growing food scene, waterfront restaurants',
        nightlife: 'Bars, lounges, Newark Ave pedestrian plaza',
        outdoors: 'Liberty State Park, waterfront promenades'
      },
      avgRent: '$2,000 - $3,400',
      brokerFeeSavings: '$3,000 - $5,000',
      seoKeywords: 'no fee apartments jersey city, jersey city apartments no broker fee, downtown jersey city rentals, jersey city nj no fee, apartments near PATH train no fee, luxury jersey city apartments, newport jersey city rentals, paulus hook apartments',
      faqs: [
        {
          q: 'Are broker fees common in Jersey City?',
          a: 'No! Unlike NYC, Jersey City (and NJ generally) doesn\'t have a tenant-paid broker fee culture. Most apartments are effectively no-fee by default.'
        },
        {
          q: 'How does Jersey City compare to Manhattan pricing?',
          a: 'Jersey City averages 20-35% lower rent than comparable Manhattan neighborhoods. A luxury one-bedroom that\'s $4,000 in Manhattan might be $2,800-$3,200 in JC.'
        },
        {
          q: 'Is the PATH train reliable?',
          a: 'Yes, the PATH is clean, safe, and runs 24/7. Trains to Manhattan run every 5-10 minutes during peak hours, with 15-20 minute frequency late night.'
        },
        {
          q: 'What are the tax implications of living in NJ vs NYC?',
          a: 'NJ has no city income tax (NYC has ~3.5%). However, NJ state income tax is similar to NY state. Overall, many find slight tax savings in JC.'
        }
      ],
      relatedLocations: ['hoboken', 'manhattan', 'brooklyn', 'harrison']
    },
    hoboken: {
      name: 'Hoboken',
      title: 'No Fee Apartments in Hoboken, NJ',
      description: 'Charming Hoboken apartments with no broker fees. Easy NYC commute via PATH train. Vibrant downtown area with restaurants and nightlife.',
      longDescription: `Hoboken is a charming, walkable city just across the Hudson from Manhattan. Known for its brownstone-lined streets, excellent restaurants, and vibrant bar scene, Hoboken attracts young professionals and families alike. The city offers a small-town feel with big-city access—the PATH train reaches Manhattan in 15 minutes.`,
      neighborhoods: ['Downtown Hoboken', 'Uptown Hoboken', 'Waterfront', 'Castle Point'],
      highlights: [
        '15-minute PATH train to Manhattan',
        'Walkable downtown with restaurants and bars',
        'Beautiful waterfront parks with NYC views',
        'Safe, family-friendly community'
      ],
      commuteInfo: {
        subway: 'PATH train (Hoboken Terminal), NJ Transit, Ferry',
        avgCommute: '15-25 min to Manhattan',
        walkScore: 92
      },
      lifestyle: {
        dining: 'Italian restaurants, brunch spots, upscale dining',
        nightlife: 'Washington Street bars, live music',
        outdoors: 'Pier A Park, Stevens Park, waterfront running paths'
      },
      avgRent: '$2,200 - $3,600',
      brokerFeeSavings: '$3,000 - $5,000',
      seoKeywords: 'no fee apartments hoboken, hoboken apartments no broker fee, hoboken nj rentals, hoboken waterfront apartments, cheap hoboken apartments no fee, how to find no fee hoboken, hoboken near PATH, downtown hoboken rentals',
      faqs: [
        {
          q: 'Is Hoboken a good alternative to Manhattan?',
          a: 'Many think so! Hoboken offers lower rent, no broker fees, a walkable downtown, and a 15-minute PATH commute. It\'s particularly popular with young professionals and couples.'
        },
        {
          q: 'What\'s the nightlife like in Hoboken?',
          a: 'Hoboken has a vibrant bar scene along Washington Street. It\'s known for a fun, social atmosphere—especially popular with 20s and 30s professionals.'
        },
        {
          q: 'How family-friendly is Hoboken?',
          a: 'Very! Hoboken has excellent schools, numerous parks, and a safe environment. Many families stay in Hoboken rather than moving to the suburbs.'
        },
        {
          q: 'Are there luxury apartments in Hoboken?',
          a: 'Yes, especially along the waterfront. Buildings offer Manhattan views, doormen, gyms, and rooftop decks at prices below comparable Manhattan buildings.'
        }
      ],
      relatedLocations: ['jersey-city', 'manhattan', 'weehawken', 'harrison']
    },
    harrison: {
      name: 'Harrison',
      title: 'No Fee Apartments in Harrison, NJ',
      description: 'Just minutes from Manhattan, Harrison NJ offers modern apartments with no broker fees. Perfect for NYC commuters seeking more space and lower rent.',
      longDescription: `Harrison is one of NJ's fastest-growing towns, attracting NYC commuters with brand-new luxury developments and excellent PATH train access. Located just 15 minutes from Manhattan, Harrison offers modern apartments with resort-style amenities at prices significantly below NYC. The area around Red Bull Arena has seen massive investment.`,
      neighborhoods: ['Downtown Harrison', 'Harrison Waterfront', 'PATH Station Area', 'Riverbend District'],
      highlights: [
        '15-minute PATH train to Manhattan',
        'Modern luxury buildings with amenities',
        'Lower cost of living than NYC',
        'Red Bull Arena and waterfront parks'
      ],
      commuteInfo: {
        subway: 'PATH train (Harrison Station)',
        avgCommute: '15-20 min to Manhattan',
        walkScore: 78
      },
      lifestyle: {
        dining: 'Growing restaurant scene, waterfront dining',
        nightlife: 'Local bars, proximity to Newark/JC nightlife',
        outdoors: 'Riverfront Park, Red Bull Arena events'
      },
      avgRent: '$2,200 - $3,500',
      brokerFeeSavings: '$3,000 - $5,000',
      seoKeywords: 'no fee apartments harrison nj, harrison new jersey apartments no broker fee, harrison yards apartments, luxury harrison nj rentals, harrison PATH train apartments, affordable nj apartments near nyc, riverbend harrison',
      faqs: [
        {
          q: 'Why is Harrison becoming so popular?',
          a: 'Harrison offers new luxury apartments at 30-40% below Manhattan prices, direct PATH access (15 min to WTC), and modern amenities. It\'s a value play for commuters.'
        },
        {
          q: 'What\'s the Harrison PATH commute like?',
          a: 'The PATH from Harrison to World Trade Center takes about 15 minutes. Trains run frequently during rush hour (every 5-10 minutes) and 24/7.'
        },
        {
          q: 'Are Harrison apartments better value than Jersey City?',
          a: 'Often yes. Harrison is slightly further out but has newer buildings with more amenities at lower prices. It\'s ideal for those prioritizing apartment quality over neighborhood buzz.'
        },
        {
          q: 'What amenities do Harrison buildings offer?',
          a: 'Most new Harrison buildings include pools, fitness centers, rooftop lounges, co-working spaces, package lockers, and parking—often included or at low cost.'
        }
      ],
      relatedLocations: ['jersey-city', 'hoboken', 'newark', 'manhattan']
    },
    weehawken: {
      name: 'Weehawken',
      title: 'No Fee Apartments in Weehawken, NJ',
      description: 'Weehawken offers stunning NYC views and no-fee apartments. Quick NYC Ferry or bus commute to Manhattan. Premium living without broker fees.',
      longDescription: `Weehawken is a hidden gem offering arguably the best Manhattan skyline views in the metro area. Perched on the cliffs above the Hudson River, Weehawken provides a quieter, more residential alternative to nearby Hoboken and Jersey City. The NYC Ferry and express buses provide easy Manhattan access.`,
      neighborhoods: ['Waterfront', 'The Heights', 'Lincoln Harbor', 'Boulevard East'],
      highlights: [
        'Spectacular NYC skyline views',
        'NYC Ferry and express bus service',
        'Quiet, residential atmosphere',
        'Premium amenities and modern buildings'
      ],
      commuteInfo: {
        subway: 'NYC Ferry, NJ Transit buses, Light Rail to Hoboken PATH',
        avgCommute: '20-35 min to Manhattan',
        walkScore: 72
      },
      lifestyle: {
        dining: 'Waterfront restaurants with views, local eateries',
        nightlife: 'Quiet residential area, close to Hoboken/JC',
        outdoors: 'Hamilton Park, waterfront paths, stunning views'
      },
      avgRent: '$2,400 - $3,800',
      brokerFeeSavings: '$3,500 - $5,500',
      seoKeywords: 'no fee apartments weehawken, weehawken nj apartments no broker fee, weehawken waterfront rentals, luxury weehawken apartments, nyc views apartments nj no fee, lincoln harbor apartments, boulevard east apartments',
      faqs: [
        {
          q: 'What makes Weehawken special?',
          a: 'The views. Weehawken offers unobstructed Manhattan skyline views that rival penthouse apartments in NYC—at a fraction of the cost and without broker fees.'
        },
        {
          q: 'How do you commute from Weehawken to Manhattan?',
          a: 'Options include the NYC Ferry (scenic 10-min ride to Midtown), NJ Transit buses, or Light Rail to Hoboken PATH. Most residents use a combination based on destination.'
        },
        {
          q: 'Is Weehawken more expensive than Hoboken?',
          a: 'Similar pricing, but Weehawken is quieter and more residential. You\'re paying for views and peace rather than walkable nightlife.'
        },
        {
          q: 'Are there good restaurants in Weehawken?',
          a: 'Weehawken has excellent waterfront dining (Chart House, Molos) but is more limited than Hoboken. Most residents enjoy the quiet and head to Hoboken/JC for variety.'
        }
      ],
      relatedLocations: ['hoboken', 'jersey-city', 'manhattan', 'union-city']
    },
    bronx: {
      name: 'Bronx',
      title: 'No Fee Apartments in The Bronx, NYC',
      description: 'Find affordable Bronx apartments with no broker fees. Great value with easy access to Manhattan. Family-friendly neighborhoods with parks and culture.',
      longDescription: `The Bronx is NYC's most affordable borough and offers tremendous value for renters. From the upscale Riverdale neighborhood to the rapidly developing South Bronx, the borough provides diverse housing options. With direct subway access to Manhattan and attractions like Yankee Stadium, the Bronx Zoo, and the New York Botanical Garden, the Bronx deserves serious consideration.`,
      neighborhoods: ['Riverdale', 'Concourse', 'Fordham', 'Pelham Bay', 'Mott Haven', 'South Bronx', 'Kingsbridge', 'Woodlawn'],
      highlights: [
        'Most affordable NYC borough',
        'Direct subway access to Manhattan',
        'Home to Yankee Stadium and Bronx Zoo',
        'Growing arts scene and waterfront parks'
      ],
      commuteInfo: {
        subway: '1, 2, 4, 5, 6, B, D lines',
        avgCommute: '30-50 min to Midtown Manhattan',
        walkScore: 75
      },
      lifestyle: {
        dining: 'Arthur Avenue Italian, diverse ethnic cuisines',
        nightlife: 'Local bars, growing scene in Mott Haven',
        outdoors: 'Bronx Zoo, NY Botanical Garden, Van Cortlandt Park'
      },
      avgRent: '$1,600 - $2,800',
      brokerFeeSavings: '$2,000 - $4,000',
      seoKeywords: 'no fee apartments bronx, bronx apartments no broker fee, south bronx rentals, affordable bronx apartments, cheap no fee apartments bronx, riverdale apartments no fee, mott haven rentals, fordham apartments',
      faqs: [
        {
          q: 'Is the Bronx safe?',
          a: 'Safety varies by neighborhood. Riverdale, Pelham Bay, and Woodlawn are among NYC\'s safest areas. The South Bronx has improved dramatically but research specific blocks.'
        },
        {
          q: 'Why is the Bronx so much cheaper?',
          a: 'Longer commutes and historical reputation keep prices lower, but the gap is closing. The Bronx offers 30-50% savings vs Manhattan for similar apartment sizes.'
        },
        {
          q: 'What\'s the best Bronx neighborhood for families?',
          a: 'Riverdale is the top choice—excellent schools, safe streets, and a suburban feel while still in NYC. Pelham Bay and Country Club are also family favorites.'
        },
        {
          q: 'Is the South Bronx worth considering?',
          a: 'Yes! Mott Haven has seen significant investment with new developments, galleries, and restaurants. It offers great value with improving amenities and quick Manhattan access.'
        }
      ],
      relatedLocations: ['manhattan', 'queens', 'westchester', 'harlem']
    }
  };

  const currentLocation = locationData[location] || locationData.manhattan;

  const fetchLocationStats = React.useCallback(async () => {
    try {
      const response = await axios.get(`${API}/units?city=${currentLocation.name}`, { withCredentials: true });
      const units = response.data;
      setStats({
        totalUnits: units.length,
        avgRent: units.length > 0 ? Math.round(units.reduce((sum, u) => sum + u.rent, 0) / units.length) : 0,
        buildings: [...new Set(units.map(u => u.building?.name))].filter(Boolean)
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, [currentLocation.name]);

  useEffect(() => {
    fetchLocationStats();
    setExpandedFaq(null); // Reset FAQ state when location changes
  }, [location, fetchLocationStats]);

  // Generate FAQ Schema
  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": currentLocation.faqs?.map(faq => ({
      "@type": "Question",
      "name": faq.q,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.a
      }
    })) || []
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <SEO
        title={currentLocation.title}
        description={currentLocation.description}
        keywords={currentLocation.seoKeywords}
        ogType="website"
      />
      
      <Helmet>
        <script type="application/ld+json">
          {JSON.stringify(faqSchema)}
        </script>
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "RealEstateAgent",
            "name": "NoFeesApts.com",
            "description": currentLocation.description,
            "url": `https://nofeesapts.com/location/${location}`,
            "areaServed": {
              "@type": "City",
              "name": currentLocation.name
            },
            "priceRange": currentLocation.avgRent,
            "availableLanguage": ["en"]
          })}
        </script>
      </Helmet>
      
      {/* Header */}
      <header className="bg-[#0a0a0a] border-b border-[#D4AF37]/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
              <span className="text-xl font-semibold text-[#D4AF37] font-philosopher">NoFeesApts</span>
            </div>
            <nav className="hidden md:flex items-center gap-6 text-sm font-philosopher">
              <Link to="/dashboard" className="text-[#F5F5F5] hover:text-[#D4AF37] transition-colors">Browse Apartments</Link>
              <Link to="/blog" className="text-[#F5F5F5] hover:text-[#D4AF37] transition-colors">Blog</Link>
              <Link to="/faq" className="text-[#F5F5F5] hover:text-[#D4AF37] transition-colors">FAQ</Link>
            </nav>
            <Button onClick={() => navigate('/auth')} className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold rounded-none">
              Get Started
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-16 md:py-24 px-4 sm:px-6 lg:px-8 border-b border-[#D4AF37]/10">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#D4AF37]/10 border border-[#D4AF37]/30 mb-6">
            <MapPin className="w-4 h-4 text-[#D4AF37]" />
            <span className="text-sm font-semibold text-[#D4AF37] font-philosopher">{currentLocation.name}</span>
          </div>
          
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-[#F5F5F5] mb-6 leading-tight font-philosopher">
            {currentLocation.title}
          </h1>
          
          <p className="text-lg text-[#888888] mb-4 max-w-3xl mx-auto font-philosopher">
            {currentLocation.description}
          </p>
          
          <p className="text-base text-[#F5F5F5]/70 mb-8 max-w-3xl mx-auto">
            {currentLocation.longDescription}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button
              onClick={() => navigate('/dashboard?city=' + currentLocation.name)}
              size="lg"
              className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-bold px-10 py-6 text-lg rounded-none font-philosopher"
              data-testid="view-apartments-btn"
            >
              View {stats.totalUnits || 'All'} Apartments
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button
              onClick={() => navigate('/auth')}
              variant="outline"
              size="lg"
              className="border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37]/10 px-10 py-6 text-lg font-semibold rounded-none font-philosopher"
            >
              Sign Up Free
            </Button>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <Card className="bg-[#1a1a1a] border-[#D4AF37]/20 rounded-none">
              <CardContent className="p-4 text-center">
                <Home className="w-6 h-6 text-[#D4AF37] mx-auto mb-2" />
                <p className="text-2xl font-bold text-[#D4AF37] font-philosopher">{stats.totalUnits || '50+'}</p>
                <p className="text-xs text-[#888888] font-philosopher">Apartments</p>
              </CardContent>
            </Card>
            <Card className="bg-[#1a1a1a] border-[#D4AF37]/20 rounded-none">
              <CardContent className="p-4 text-center">
                <DollarSign className="w-6 h-6 text-[#D4AF37] mx-auto mb-2" />
                <p className="text-2xl font-bold text-[#D4AF37] font-philosopher">${stats.avgRent || '2,500'}</p>
                <p className="text-xs text-[#888888] font-philosopher">Avg Rent</p>
              </CardContent>
            </Card>
            <Card className="bg-[#1a1a1a] border-[#D4AF37]/20 rounded-none">
              <CardContent className="p-4 text-center">
                <Shield className="w-6 h-6 text-[#D4AF37] mx-auto mb-2" />
                <p className="text-2xl font-bold text-[#D4AF37] font-philosopher">{currentLocation.brokerFeeSavings?.split(' - ')[0] || '$3,000'}</p>
                <p className="text-xs text-[#888888] font-philosopher">You Save</p>
              </CardContent>
            </Card>
            <Card className="bg-[#1a1a1a] border-[#D4AF37]/20 rounded-none">
              <CardContent className="p-4 text-center">
                <Clock className="w-6 h-6 text-[#D4AF37] mx-auto mb-2" />
                <p className="text-2xl font-bold text-[#D4AF37] font-philosopher">{currentLocation.commuteInfo?.avgCommute?.split(' ')[0] || '20'}</p>
                <p className="text-xs text-[#888888] font-philosopher">Min to Manhattan</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Commute & Lifestyle Info */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-[#1a1a1a]/50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-[#F5F5F5] mb-8 text-center font-philosopher">Living in {currentLocation.name}</h2>
          
          <div className="grid md:grid-cols-3 gap-6">
            {/* Commute */}
            <Card className="bg-[#0a0a0a] border-[#D4AF37]/20 rounded-none">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Train className="w-6 h-6 text-[#D4AF37]" />
                  <h3 className="text-lg font-semibold text-[#F5F5F5] font-philosopher">Commute</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <p className="text-[#888888]"><span className="text-[#F5F5F5]">Transit:</span> {currentLocation.commuteInfo?.subway}</p>
                  <p className="text-[#888888]"><span className="text-[#F5F5F5]">To Manhattan:</span> {currentLocation.commuteInfo?.avgCommute}</p>
                  <p className="text-[#888888]"><span className="text-[#F5F5F5]">Walk Score:</span> {currentLocation.commuteInfo?.walkScore}/100</p>
                </div>
              </CardContent>
            </Card>

            {/* Dining */}
            <Card className="bg-[#0a0a0a] border-[#D4AF37]/20 rounded-none">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Utensils className="w-6 h-6 text-[#D4AF37]" />
                  <h3 className="text-lg font-semibold text-[#F5F5F5] font-philosopher">Dining & Nightlife</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <p className="text-[#888888]"><span className="text-[#F5F5F5]">Food:</span> {currentLocation.lifestyle?.dining}</p>
                  <p className="text-[#888888]"><span className="text-[#F5F5F5]">Nightlife:</span> {currentLocation.lifestyle?.nightlife}</p>
                </div>
              </CardContent>
            </Card>

            {/* Outdoors */}
            <Card className="bg-[#0a0a0a] border-[#D4AF37]/20 rounded-none">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <TreePine className="w-6 h-6 text-[#D4AF37]" />
                  <h3 className="text-lg font-semibold text-[#F5F5F5] font-philosopher">Parks & Outdoors</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <p className="text-[#888888]">{currentLocation.lifestyle?.outdoors}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Popular Neighborhoods */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-[#F5F5F5] mb-8 text-center font-philosopher">Popular Neighborhoods</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {currentLocation.neighborhoods.map((hood, idx) => (
              <Card 
                key={idx} 
                className="bg-[#1a1a1a] border-[#D4AF37]/20 hover:border-[#D4AF37]/50 transition-all cursor-pointer rounded-none"
                onClick={() => navigate(`/dashboard?neighborhood=${hood}`)}
              >
                <CardContent className="p-4">
                  <MapPin className="w-5 h-5 text-[#D4AF37] mb-2" />
                  <h3 className="text-sm font-semibold text-[#F5F5F5] font-philosopher">{hood}</h3>
                  <p className="text-xs text-[#D4AF37] mt-1 font-philosopher">View Apartments →</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Why Live Here */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-[#1a1a1a]/50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-[#F5F5F5] mb-8 text-center font-philosopher">Why Live in {currentLocation.name}?</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {currentLocation.highlights.map((highlight, idx) => (
              <div key={idx} className="flex gap-4 items-start">
                <div className="w-10 h-10 bg-[#D4AF37] flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-5 h-5 text-[#0a0a0a]" />
                </div>
                <div>
                  <p className="text-[#F5F5F5] font-philosopher">{highlight}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      {currentLocation.faqs && currentLocation.faqs.length > 0 && (
        <section className="py-12 px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold text-[#F5F5F5] mb-8 text-center font-philosopher">
              Frequently Asked Questions: {currentLocation.name}
            </h2>
            <div className="space-y-3">
              {currentLocation.faqs.map((faq, idx) => (
                <Card 
                  key={idx} 
                  className="bg-[#1a1a1a] border-[#D4AF37]/20 rounded-none overflow-hidden"
                >
                  <button
                    onClick={() => setExpandedFaq(expandedFaq === idx ? null : idx)}
                    className="w-full p-4 flex items-center justify-between text-left"
                  >
                    <span className="text-[#F5F5F5] font-medium font-philosopher pr-4">{faq.q}</span>
                    {expandedFaq === idx ? (
                      <ChevronUp className="w-5 h-5 text-[#D4AF37] flex-shrink-0" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-[#D4AF37] flex-shrink-0" />
                    )}
                  </button>
                  {expandedFaq === idx && (
                    <div className="px-4 pb-4">
                      <p className="text-[#888888] text-sm leading-relaxed">{faq.a}</p>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Compare Locations */}
      {currentLocation.relatedLocations && (
        <section className="py-12 px-4 sm:px-6 lg:px-8 bg-[#1a1a1a]/50">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-[#F5F5F5] mb-6 text-center font-philosopher">Compare Other Locations</h2>
            <div className="flex flex-wrap justify-center gap-3">
              {currentLocation.relatedLocations.map((loc) => {
                const locData = locationData[loc];
                if (!locData) return null;
                return (
                  <Link
                    key={loc}
                    to={`/location/${loc}`}
                    className="px-4 py-2 bg-[#0a0a0a] border border-[#D4AF37]/30 text-[#F5F5F5] hover:border-[#D4AF37] hover:text-[#D4AF37] transition-all font-philosopher text-sm"
                  >
                    {locData.name}
                  </Link>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-[#D4AF37]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-[#0a0a0a] mb-4 font-philosopher">Ready to Find Your {currentLocation.name} Apartment?</h2>
          <p className="text-lg text-[#0a0a0a]/80 mb-8 font-philosopher">Sign up free. Browse apartments. Save {currentLocation.brokerFeeSavings || '$3,000+'} on broker fees.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => navigate('/auth')}
              size="lg"
              className="bg-[#0a0a0a] hover:bg-[#1a1a1a] text-[#D4AF37] font-bold px-10 py-6 rounded-none font-philosopher"
            >
              Sign Up Free
            </Button>
            <Button
              onClick={() => navigate('/dashboard?city=' + currentLocation.name)}
              size="lg"
              variant="outline"
              className="border-2 border-[#0a0a0a] text-[#0a0a0a] hover:bg-[#0a0a0a] hover:text-[#D4AF37] font-bold px-10 py-6 rounded-none font-philosopher"
            >
              View All Apartments
            </Button>
          </div>
        </div>
      </section>

      {/* Footer with Internal Links */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 bg-[#0a0a0a] border-t border-[#D4AF37]/10">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-[#D4AF37] font-bold mb-4 font-philosopher">NYC Locations</h3>
              <ul className="space-y-2 text-sm">
                <li><Link to="/location/manhattan" className="text-[#888888] hover:text-[#D4AF37]">Manhattan</Link></li>
                <li><Link to="/location/brooklyn" className="text-[#888888] hover:text-[#D4AF37]">Brooklyn</Link></li>
                <li><Link to="/location/queens" className="text-[#888888] hover:text-[#D4AF37]">Queens</Link></li>
                <li><Link to="/location/bronx" className="text-[#888888] hover:text-[#D4AF37]">Bronx</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-[#D4AF37] font-bold mb-4 font-philosopher">NJ Locations</h3>
              <ul className="space-y-2 text-sm">
                <li><Link to="/location/jersey-city" className="text-[#888888] hover:text-[#D4AF37]">Jersey City</Link></li>
                <li><Link to="/location/hoboken" className="text-[#888888] hover:text-[#D4AF37]">Hoboken</Link></li>
                <li><Link to="/location/harrison" className="text-[#888888] hover:text-[#D4AF37]">Harrison</Link></li>
                <li><Link to="/location/weehawken" className="text-[#888888] hover:text-[#D4AF37]">Weehawken</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-[#D4AF37] font-bold mb-4 font-philosopher">Popular Areas</h3>
              <ul className="space-y-2 text-sm">
                <li><Link to="/location/long-island-city" className="text-[#888888] hover:text-[#D4AF37]">Long Island City</Link></li>
                <li><Link to="/location/williamsburg" className="text-[#888888] hover:text-[#D4AF37]">Williamsburg</Link></li>
              </ul>
            </div>
            <div>
              <h3 className="text-[#D4AF37] font-bold mb-4 font-philosopher">Resources</h3>
              <ul className="space-y-2 text-sm">
                <li><Link to="/blog" className="text-[#888888] hover:text-[#D4AF37]">Blog</Link></li>
                <li><Link to="/faq" className="text-[#888888] hover:text-[#D4AF37]">FAQ</Link></li>
                <li><Link to="/dashboard" className="text-[#888888] hover:text-[#D4AF37]">All Apartments</Link></li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-[#D4AF37]/10 text-center">
            <p className="text-[#888888] text-sm">© 2025 NoFeesApts.com - No Fee Apartments NYC & NJ</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LocationPage;
