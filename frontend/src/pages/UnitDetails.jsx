import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from '../utils/axiosConfig';
import { toast } from 'sonner';
import { API } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ArrowLeft, Building2, BedDouble, Bath, Heart, MapPin, Calendar, Send, Share2, Clock, ChevronLeft, ChevronRight, Info, CalendarPlus, CheckCircle2 } from 'lucide-react';
import ShareDialog from '@/components/ShareDialog';
import SEO from '@/components/SEO';
import { trackApartmentView } from '../utils/analytics';

// Generate Google Calendar URL
const generateGoogleCalendarUrl = (unit, date, time) => {
  const buildingName = unit?.building?.name || 'Apartment';
  const address = unit?.building?.address || '';
  const city = unit?.building?.city || '';
  const state = unit?.building?.state || '';
  const unitNumber = unit?.unit_number || '';
  
  const title = encodeURIComponent(`Apartment Viewing - ${buildingName} #${unitNumber}`);
  const location = encodeURIComponent(`${address}, ${city}, ${state}`);
  const details = encodeURIComponent(
    `Apartment viewing scheduled via NoFeesApts.com\n\n` +
    `Property: ${buildingName}\n` +
    `Unit: #${unitNumber}\n` +
    `Rent: $${unit?.rent?.toLocaleString()}/month\n` +
    `Address: ${address}, ${city}, ${state}\n\n` +
    `No broker fee apartment!`
  );
  
  // Parse date and time
  let startDate = new Date();
  if (date) {
    startDate = new Date(date);
  }
  
  // Set time based on selection
  const timeMap = {
    'morning': { hour: 10, label: '10:00 AM' },
    'afternoon': { hour: 14, label: '2:00 PM' },
    'evening': { hour: 18, label: '6:00 PM' }
  };
  
  const selectedTime = timeMap[time] || timeMap['afternoon'];
  startDate.setHours(selectedTime.hour, 0, 0, 0);
  
  const endDate = new Date(startDate);
  endDate.setHours(startDate.getHours() + 1); // 1 hour viewing
  
  // Format dates for Google Calendar (YYYYMMDDTHHmmss)
  const formatDate = (d) => {
    return d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
  };
  
  const dates = `${formatDate(startDate)}/${formatDate(endDate)}`;
  
  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${dates}&details=${details}&location=${location}`;
};

// Smart description formatter
const formatDescription = (description, unit) => {
  if (!description) return null;
  
  let clean = description
    .replace(/SHOWINGS BY APPOINTMENT ONLY\.?\s*/gi, '')
    .replace(/NO FEE\.?\s*/gi, '')
    .replace(/\bno broker fee\b/gi, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
  
  if (clean.length <= 200) return clean;
  
  const highlights = [];
  if (/ceiling|ceilings/i.test(clean)) {
    const match = clean.match(/(\d+)[\s-]?foot\s+ceiling/i);
    if (match) highlights.push(`${match[1]}ft ceilings`);
  }
  if (/penthouse/i.test(clean)) highlights.push('Penthouse');
  if (/renovated|updated|modern/i.test(clean)) highlights.push('Modern finishes');
  if (/view|views/i.test(clean)) highlights.push('Great views');
  if (/laundry|washer|dryer/i.test(clean)) highlights.push('In-unit laundry');
  if (/doorman|concierge/i.test(clean)) highlights.push('Doorman building');
  if (/gym|fitness/i.test(clean)) highlights.push('Fitness center');
  if (/rooftop|roof deck/i.test(clean)) highlights.push('Rooftop access');
  if (/balcony|terrace|patio/i.test(clean)) highlights.push('Private outdoor space');
  
  if (highlights.length > 0) {
    return highlights.slice(0, 4).join(' • ');
  }
  
  const sentences = clean.split(/[.!?]+/);
  let brief = '';
  for (const sentence of sentences) {
    if ((brief + sentence).length > 200) break;
    brief += sentence.trim() + '. ';
  }
  
  return brief.trim() || clean.slice(0, 200) + '...';
};

const UnitDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [unit, setUnit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFavorite, setIsFavorite] = useState(false);
  const [contactOpen, setContactOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [successOpen, setSuccessOpen] = useState(false);
  const [scheduledViewing, setScheduledViewing] = useState({ date: null, time: null });

  useEffect(() => {
    fetchUnit();
    checkFavorite();
  }, [id]);

  const fetchUnit = async () => {
    try {
      const response = await axios.get(`${API}/units/${id}`, { withCredentials: true });
      const unitData = response.data;
      setUnit(unitData);
      trackApartmentView(
        unitData.id, 
        unitData.building?.name || 'Unknown Building',
        unitData.rent
      );
    } catch (error) {
      console.error('Error fetching unit:', error);
      toast.error('Failed to load apartment');
    } finally {
      setLoading(false);
    }
  };

  const checkFavorite = async () => {
    try {
      const response = await axios.get(`${API}/favorites`, { withCredentials: true });
      const favIds = response.data.map(f => f.unit.id);
      setIsFavorite(favIds.includes(id));
    } catch (error) {
      console.error('Error checking favorites:', error);
    }
  };

  const toggleFavorite = async () => {
    try {
      if (isFavorite) {
        await axios.delete(`${API}/favorites/${id}`, { withCredentials: true });
        setIsFavorite(false);
        toast.success('Removed from favorites');
      } else {
        await axios.post(`${API}/favorites/${id}`, {}, { withCredentials: true });
        setIsFavorite(true);
        toast.success('Added to favorites');
      }
    } catch (error) {
      toast.error('Failed to update favorites');
    }
  };

  const handleContact = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const preferredDate = formData.get('preferred_date');
    const preferredTime = formData.get('preferred_time');
    
    try {
      await axios.post(`${API}/contact`, {
        unit_id: id,
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        message: formData.get('message'),
        preferred_date: preferredDate,
        preferred_time: preferredTime,
        alternative_date: formData.get('alternative_date'),
        alternative_time: formData.get('alternative_time')
      }, { withCredentials: true });
      
      // Store the scheduled viewing details for calendar
      setScheduledViewing({ date: preferredDate, time: preferredTime });
      setContactOpen(false);
      setSuccessOpen(true);
    } catch (error) {
      toast.error('Failed to submit request');
    }
  };

  const openGoogleCalendar = () => {
    const url = generateGoogleCalendarUrl(unit, scheduledViewing.date, scheduledViewing.time);
    window.open(url, '_blank');
  };

  const nextImage = () => {
    if (unit?.images?.length > 0) {
      setCurrentImageIndex((prev) => (prev + 1) % unit.images.length);
    }
  };

  const prevImage = () => {
    if (unit?.images?.length > 0) {
      setCurrentImageIndex((prev) => (prev - 1 + unit.images.length) % unit.images.length);
    }
  };

  const selectImage = (index) => {
    setCurrentImageIndex(index);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0a0a0a]">
        <div className="text-xl text-[#D4AF37] font-philosopher">Loading...</div>
      </div>
    );
  }

  if (!unit) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#0a0a0a]">
        <div className="text-xl text-[#F5F5F5] font-philosopher mb-4">Apartment not found</div>
        <Button onClick={() => navigate('/dashboard')} className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold rounded-none">Back to Dashboard</Button>
      </div>
    );
  }

  const bedroomText = unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} bed`;
  const buildingName = unit.building?.name || 'NYC Apartment';
  const neighborhood = unit.building?.neighborhood || unit.building?.city || 'NYC';
  const images = unit.images || [];
  
  // RealEstateListing Schema for Google Rich Results
  const realEstateSchema = {
    "@context": "https://schema.org",
    "@type": "RealEstateListing",
    "name": `${bedroomText} Apartment at ${buildingName}`,
    "description": unit.description || `No broker fee ${bedroomText.toLowerCase()} apartment in ${neighborhood}. Features ${unit.bathrooms} bathroom(s) and modern amenities.`,
    "url": `https://www.nofeesapts.com/unit/${unit.id}`,
    "datePosted": unit.created_at || new Date().toISOString(),
    "image": images.length > 0 ? images : undefined,
    "offers": {
      "@type": "Offer",
      "price": unit.rent,
      "priceCurrency": "USD",
      "availability": unit.is_available ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      "priceSpecification": {
        "@type": "UnitPriceSpecification",
        "price": unit.rent,
        "priceCurrency": "USD",
        "unitText": "MONTH"
      }
    },
    "address": {
      "@type": "PostalAddress",
      "streetAddress": `${unit.building?.address || ''} #${unit.unit_number}`,
      "addressLocality": unit.building?.city || "New York",
      "addressRegion": unit.building?.state || "NY",
      "postalCode": unit.building?.zip_code || "",
      "addressCountry": "US"
    },
    "geo": unit.building?.latitude && unit.building?.longitude ? {
      "@type": "GeoCoordinates",
      "latitude": unit.building.latitude,
      "longitude": unit.building.longitude
    } : undefined,
    "floorSize": unit.square_feet ? {
      "@type": "QuantitativeValue",
      "value": unit.square_feet,
      "unitCode": "FTK"
    } : undefined,
    "numberOfRooms": unit.bedrooms === 0 ? 1 : unit.bedrooms + 1,
    "numberOfBedrooms": unit.bedrooms,
    "numberOfBathroomsTotal": unit.bathrooms,
    "amenityFeature": (unit.amenities || []).map(amenity => ({
      "@type": "LocationFeatureSpecification",
      "name": amenity,
      "value": true
    })),
    "landlord": {
      "@type": "Organization",
      "name": "NoFeesApts.com",
      "url": "https://www.nofeesapts.com"
    }
  };

  // Product schema for additional price display in SERPs
  const productSchema = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": `${bedroomText} No-Fee Apartment at ${buildingName}, ${neighborhood}`,
    "description": `No broker fee ${bedroomText.toLowerCase()} apartment in ${neighborhood}. $${unit.rent.toLocaleString()}/month rent. ${unit.bathrooms} bath.`,
    "image": images.length > 0 ? images[0] : undefined,
    "brand": {
      "@type": "Brand",
      "name": buildingName
    },
    "offers": {
      "@type": "Offer",
      "url": `https://www.nofeesapts.com/unit/${unit.id}`,
      "price": unit.rent,
      "priceCurrency": "USD",
      "priceValidUntil": new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      "availability": unit.is_available ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      "seller": {
        "@type": "Organization",
        "name": "NoFeesApts.com"
      }
    }
  };

  // Apartment schema (more specific for rentals)
  const apartmentSchema = {
    "@context": "https://schema.org",
    "@type": "Apartment",
    "name": `Unit ${unit.unit_number} at ${buildingName}`,
    "description": unit.description || `${bedroomText} apartment available for rent in ${neighborhood}`,
    "url": `https://www.nofeesapts.com/unit/${unit.id}`,
    "image": images,
    "address": {
      "@type": "PostalAddress",
      "streetAddress": unit.building?.address || '',
      "addressLocality": unit.building?.city || "New York",
      "addressRegion": unit.building?.state || "NY",
      "postalCode": unit.building?.zip_code || "",
      "addressCountry": "US"
    },
    "floorSize": unit.square_feet ? {
      "@type": "QuantitativeValue",
      "value": unit.square_feet,
      "unitCode": "FTK"
    } : undefined,
    "numberOfRooms": unit.bedrooms === 0 ? 1 : unit.bedrooms + 1,
    "numberOfBedrooms": unit.bedrooms,
    "numberOfBathroomsTotal": unit.bathrooms,
    "petsAllowed": (unit.amenities || []).some(a => a.toLowerCase().includes('pet')) || false,
    "amenityFeature": (unit.amenities || []).map(amenity => ({
      "@type": "LocationFeatureSpecification", 
      "name": amenity
    }))
  };
  
  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Structured Data for Google Rich Results */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(realEstateSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(productSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(apartmentSchema) }}
      />
      
      <SEO
        title={`${bedroomText} at ${buildingName} - $${unit.rent.toLocaleString()}/mo - No Fee`}
        description={`No broker fee ${bedroomText.toLowerCase()} apartment for rent in ${neighborhood}, ${unit.building?.city || 'NYC'}. $${unit.rent.toLocaleString()}/mo, ${unit.bathrooms} bath${unit.square_feet ? `, ${unit.square_feet} sq ft` : ''}. Available ${unit.available_date || 'now'}. Save thousands on broker fees!`}
        keywords={`no fee apartment ${neighborhood}, ${bedroomText} ${neighborhood}, ${buildingName}, no broker fee ${unit.building?.city || 'NYC'}, ${neighborhood} apartments for rent, ${bedroomText.toLowerCase()} no fee NYC, cheap apartments ${neighborhood}, ${unit.building?.state === 'NJ' ? 'New Jersey no fee apartments' : 'NYC no fee apartments'}`}
        url={`/unit/${unit.id}`}
        image={images.length > 0 ? images[0] : null}
        type="product"
        breadcrumbs={[
          { name: 'Home', url: '/' },
          { name: 'Apartments', url: '/dashboard' },
          { name: unit.building?.state || 'NY', url: `/location/${(unit.building?.state || 'NY').toLowerCase()}` },
          { name: neighborhood, url: `/dashboard?neighborhood=${encodeURIComponent(neighborhood)}` },
          { name: `${buildingName} #${unit.unit_number}` }
        ]}
        product={{
          name: `${bedroomText} No-Fee Apartment at ${buildingName}`,
          description: `No broker fee ${bedroomText.toLowerCase()} in ${neighborhood}`,
          image: images.length > 0 ? images[0] : null,
          price: unit.rent,
          brand: buildingName,
          available: unit.is_available
        }}
      />
      
      {/* Header */}
      <header className="bg-[#0a0a0a] border-b border-[#D4AF37]/10 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={() => navigate(-1)}
              data-testid="back-to-dashboard-btn"
              className="text-[#F5F5F5] hover:text-[#D4AF37] font-philosopher"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            {/* Breadcrumb */}
            <nav className="hidden md:flex text-sm text-[#888888] font-philosopher">
              <span>Rentals</span>
              <span className="mx-2 text-[#D4AF37]/50">›</span>
              <span>{unit.building?.state || 'NY'}</span>
              <span className="mx-2 text-[#D4AF37]/50">›</span>
              <span className="text-[#F5F5F5]">{neighborhood}</span>
              <span className="mx-2 text-[#D4AF37]/50">›</span>
              <span className="text-[#D4AF37]">{unit.building?.address} #{unit.unit_number}</span>
            </nav>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6" data-testid="unit-details">
        {/* Main Content - Two Column Layout */}
        <div className="flex flex-col lg:flex-row gap-8">
          
          {/* LEFT COLUMN - Image Gallery (60-65%) */}
          <div className="lg:w-[62%]">
            {/* Main Image */}
            <div className="relative bg-[#1a1a1a] overflow-hidden mb-3 border border-[#D4AF37]/10">
              {images.length > 0 ? (
                <>
                  <div className="relative aspect-[4/3]">
                    <img
                      src={images[currentImageIndex]}
                      alt={`${unit?.bedrooms === 0 ? 'Studio' : unit?.bedrooms === 1 ? 'One bedroom' : `${unit?.bedrooms} bedroom`} apartment ${currentImageIndex === 0 ? 'interior' : currentImageIndex === 1 ? 'kitchen' : currentImageIndex === 2 ? 'bedroom' : 'view'} at ${buildingName}, ${unit?.building?.neighborhood || unit?.building?.city || 'NYC'}`}
                      className="w-full h-full object-cover"
                    />
                    
                    {/* Image Counter Badge */}
                    <div className="absolute bottom-4 left-4 bg-[#0a0a0a]/90 text-[#D4AF37] px-4 py-2 text-sm font-philosopher tracking-wide border border-[#D4AF37]/30">
                      {currentImageIndex + 1} of {images.length}
                    </div>
                    
                    {/* Navigation Arrows */}
                    {images.length > 1 && (
                      <>
                        <button
                          onClick={prevImage}
                          className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-[#0a0a0a]/80 hover:bg-[#D4AF37] border border-[#D4AF37]/30 hover:border-[#D4AF37] flex items-center justify-center transition-all group"
                        >
                          <ChevronLeft className="w-6 h-6 text-[#D4AF37] group-hover:text-[#0a0a0a]" />
                        </button>
                        <button
                          onClick={nextImage}
                          className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-[#0a0a0a]/80 hover:bg-[#D4AF37] border border-[#D4AF37]/30 hover:border-[#D4AF37] flex items-center justify-center transition-all group"
                        >
                          <ChevronRight className="w-6 h-6 text-[#D4AF37] group-hover:text-[#0a0a0a]" />
                        </button>
                      </>
                    )}
                  </div>
                </>
              ) : (
                <div className="aspect-[4/3] bg-[#1a1a1a] flex items-center justify-center">
                  <Building2 className="w-24 h-24 text-[#D4AF37]/30" />
                </div>
              )}
            </div>

            {/* Thumbnail Gallery */}
            {images.length > 1 && (
              <div className="flex gap-2 overflow-x-auto pb-2">
                {images.slice(0, 8).map((image, index) => (
                  <button
                    key={index}
                    onClick={() => selectImage(index)}
                    className={`flex-shrink-0 w-20 h-16 overflow-hidden border transition-all ${
                      index === currentImageIndex 
                        ? 'border-[#D4AF37] ring-1 ring-[#D4AF37]/30' 
                        : 'border-[#D4AF37]/20 hover:border-[#D4AF37]/50'
                    }`}
                  >
                    <img
                      src={image}
                      alt={`${unit?.bedrooms === 0 ? 'Studio' : unit?.bedrooms === 1 ? 'One bedroom' : `${unit?.bedrooms} bedroom`} apartment thumbnail ${index + 1} at ${buildingName}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
                {images.length > 8 && (
                  <div className="flex-shrink-0 w-20 h-16 bg-[#1a1a1a] border border-[#D4AF37]/20 flex items-center justify-center text-[#D4AF37] text-sm font-philosopher">
                    +{images.length - 8}
                  </div>
                )}
              </div>
            )}

            {/* About Section - Below Images */}
            <div className="mt-8 pt-6 border-t border-[#D4AF37]/10">
              <h2 className="text-xl font-philosopher font-bold text-white mb-4">About</h2>
              {unit.description ? (
                <p className="text-[#F5F5F5] leading-relaxed">
                  {formatDescription(unit.description, unit)}
                </p>
              ) : (
                <p className="text-[#888888]">
                  {bedroomText === 'Studio' ? 'Studio' : `${unit.bedrooms} bedroom`} apartment with {unit.bathrooms} bathroom{unit.bathrooms > 1 ? 's' : ''} in {neighborhood}. No broker fee required.
                </p>
              )}
              
              {/* Amenities */}
              {unit.amenities && unit.amenities.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-philosopher font-semibold text-white mb-3">Features & Amenities</h3>
                  <div className="flex flex-wrap gap-2">
                    {unit.amenities.map((amenity, index) => (
                      <Badge key={index} variant="secondary" className="px-3 py-1.5 text-sm bg-[#1a1a1a] text-[#F5F5F5] border border-[#D4AF37]/20 rounded-none font-philosopher">
                        {amenity}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN - Property Info (35-40%) */}
          <div className="lg:w-[38%]">
            <div className="lg:sticky lg:top-24">
              {/* Property Title & Address */}
              <div className="mb-6">
                <h1 className="text-2xl md:text-3xl font-philosopher font-bold text-white mb-1">
                  {unit.building?.address}
                </h1>
                <p className="text-lg text-[#888888] font-philosopher">#{unit.unit_number}</p>
              </div>

              {/* Price Section */}
              <div className="mb-6">
                <div className="flex items-baseline gap-3">
                  <span className="text-3xl md:text-4xl font-philosopher font-bold text-[#D4AF37]">${unit.rent.toLocaleString()}</span>
                  <span className="text-[#888888] text-sm font-philosopher tracking-wide">FOR RENT</span>
                </div>
                <p className="text-sm text-[#888888] mt-2 font-philosopher">No broker fee. Move-in ready.</p>
              </div>

              {/* Key Details Row */}
              <div className="flex items-center gap-4 text-[#F5F5F5] py-4 border-y border-[#D4AF37]/20 mb-6 font-philosopher">
                {unit.square_feet && (
                  <>
                    <span className="font-medium">{unit.square_feet} ft²</span>
                    <span className="text-[#D4AF37]/50">|</span>
                  </>
                )}
                <span className="font-medium">{unit.bedrooms + 1} rooms</span>
                <span className="text-[#D4AF37]/50">|</span>
                <span className="font-medium">{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} bed`}</span>
                <span className="text-[#D4AF37]/50">|</span>
                <span className="font-medium">{unit.bathrooms} bath</span>
              </div>

              {/* Location */}
              <div className="mb-6 text-sm font-philosopher">
                <p className="text-[#888888]">Rental unit</p>
                <p className="text-[#D4AF37] font-medium">{neighborhood}</p>
              </div>

              {/* No Fee Notice */}
              <div className="bg-[#D4AF37]/10 border border-[#D4AF37]/30 p-4 mb-6">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-[#D4AF37] flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-[#F5F5F5] font-philosopher">
                    <strong className="text-[#D4AF37]">No broker fee</strong> - You won't be charged a broker fee for this property.
                  </p>
                </div>
              </div>

              {/* Schedule Viewing Button */}
              <Dialog open={contactOpen} onOpenChange={setContactOpen}>
                <DialogTrigger asChild>
                  <Button 
                    className="w-full bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] py-5 text-base font-philosopher font-bold mb-4 flex items-center justify-center gap-2 transition-all rounded-none tracking-wide hover:shadow-[0_0_20px_rgba(212,175,55,0.3)]" 
                    data-testid="contact-btn"
                  >
                    <Calendar className="w-5 h-5" />
                    Schedule Viewing
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white max-w-md rounded-none">
                  <DialogHeader>
                    <DialogTitle className="text-white text-xl font-philosopher">Schedule a Viewing</DialogTitle>
                    <DialogDescription className="text-[#888888] font-philosopher">
                      Pick a time that works for you. We'll confirm your appointment shortly.
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleContact} className="space-y-4 mt-2">
                    {/* Schedule Section - Primary */}
                    <div className="bg-[#D4AF37]/10 border border-[#D4AF37]/30 p-4">
                      <div className="flex items-center gap-2 mb-4">
                        <Calendar className="w-5 h-5 text-[#D4AF37]" />
                        <span className="text-[#D4AF37] font-philosopher font-semibold">Select Your Preferred Time</span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label htmlFor="preferred_date" className="text-[#F5F5F5] text-sm mb-1 block font-philosopher">Date</Label>
                          <Input 
                            id="preferred_date" 
                            name="preferred_date" 
                            type="date"
                            min={new Date().toISOString().split('T')[0]}
                            className="border-[#D4AF37]/30 bg-[#0a0a0a] text-white rounded-none"
                          />
                        </div>
                        <div>
                          <Label htmlFor="preferred_time" className="text-[#F5F5F5] text-sm mb-1 block font-philosopher">Time</Label>
                          <select 
                            id="preferred_time" 
                            name="preferred_time"
                            className="w-full h-10 px-3 border border-[#D4AF37]/30 bg-[#0a0a0a] text-white focus:outline-none focus:border-[#D4AF37] font-philosopher"
                          >
                            <option value="">Select time</option>
                            <option value="morning">Morning (9-12pm)</option>
                            <option value="afternoon">Afternoon (12-5pm)</option>
                            <option value="evening">Evening (5-8pm)</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Contact Info Section */}
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label htmlFor="name" className="text-[#F5F5F5] text-sm mb-1 block font-philosopher">Name *</Label>
                          <Input id="name" name="name" required placeholder="Your name" data-testid="contact-name-input" className="border-[#D4AF37]/30 bg-[#0a0a0a] text-white rounded-none font-philosopher placeholder:text-[#666666]" />
                        </div>
                        <div>
                          <Label htmlFor="phone" className="text-[#F5F5F5] text-sm mb-1 block font-philosopher">Phone</Label>
                          <Input id="phone" name="phone" type="tel" placeholder="(555) 123-4567" data-testid="contact-phone-input" className="border-[#D4AF37]/30 bg-[#0a0a0a] text-white rounded-none font-philosopher placeholder:text-[#666666]" />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="email" className="text-[#F5F5F5] text-sm mb-1 block font-philosopher">Email *</Label>
                        <Input id="email" name="email" type="email" required placeholder="you@example.com" data-testid="contact-email-input" className="border-[#D4AF37]/30 bg-[#0a0a0a] text-white rounded-none font-philosopher placeholder:text-[#666666]" />
                      </div>
                      <div>
                        <Label htmlFor="message" className="text-[#F5F5F5] text-sm mb-1 block font-philosopher">Message (optional)</Label>
                        <Textarea
                          id="message"
                          name="message"
                          rows={2}
                          placeholder="Any questions or special requests?"
                          data-testid="contact-message-input"
                          className="border-[#D4AF37]/30 bg-[#0a0a0a] text-white rounded-none resize-none font-philosopher placeholder:text-[#666666]"
                        />
                      </div>
                    </div>
                    
                    <Button type="submit" className="w-full bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] py-5 font-philosopher font-bold flex items-center justify-center gap-2 rounded-none tracking-wide" data-testid="contact-submit-btn">
                      <Calendar className="w-4 h-4" />
                      Request Viewing
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>

              {/* Action Buttons Row */}
              <div className="flex gap-3 mb-6">
                <Button
                  onClick={toggleFavorite}
                  variant="outline"
                  className={`flex-1 border-[#D4AF37]/30 rounded-none font-philosopher ${isFavorite ? 'bg-[#D4AF37]/10 border-[#D4AF37] text-[#D4AF37]' : 'text-[#F5F5F5] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]'}`}
                  data-testid="toggle-favorite-btn"
                >
                  <Heart className={`w-4 h-4 mr-2 ${isFavorite ? 'fill-current' : ''}`} />
                  SAVE
                </Button>
                <Button
                  onClick={() => setShareOpen(true)}
                  variant="outline"
                  className="flex-1 border-[#D4AF37]/30 text-[#F5F5F5] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37] rounded-none font-philosopher"
                  data-testid="share-btn"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  SHARE
                </Button>
              </div>

              {/* Building Details Card */}
              <Card className="border border-[#D4AF37]/20 bg-[#1a1a1a] rounded-none">
                <CardContent className="p-4">
                  <h3 className="font-philosopher font-semibold text-[#D4AF37] mb-3">Building Details</h3>
                  <div className="space-y-2 text-sm font-philosopher">
                    <div className="flex justify-between">
                      <span className="text-[#888888]">Building</span>
                      <span className="text-[#F5F5F5] font-medium">{unit.building?.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#888888]">Address</span>
                      <span className="text-[#F5F5F5]">{unit.building?.address}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#888888]">Neighborhood</span>
                      <span className="text-[#F5F5F5]">{unit.building?.neighborhood}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#888888]">City</span>
                      <span className="text-[#F5F5F5]">{unit.building?.city}, {unit.building?.state}</span>
                    </div>
                    {unit.available_date && (
                      <div className="flex justify-between">
                        <span className="text-[#888888]">Available</span>
                        <span className="text-[#D4AF37] font-medium">{unit.available_date}</span>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* Share Dialog */}
      {unit && (
        <ShareDialog
          open={shareOpen}
          onOpenChange={setShareOpen}
          unit={unit}
          building={unit.building}
        />
      )}

      {/* Success Dialog with Google Calendar */}
      <Dialog open={successOpen} onOpenChange={setSuccessOpen}>
        <DialogContent className="bg-[#1a1a1a] border border-[#D4AF37]/20 text-white max-w-md text-center rounded-none">
          <div className="flex flex-col items-center py-4">
            <div className="w-16 h-16 bg-[#D4AF37]/10 border border-[#D4AF37]/30 flex items-center justify-center mb-4">
              <CheckCircle2 className="w-10 h-10 text-[#D4AF37]" />
            </div>
            <DialogTitle className="text-white text-xl font-philosopher mb-2">Viewing Request Sent!</DialogTitle>
            <DialogDescription className="text-[#888888] font-philosopher mb-6">
              We'll confirm your appointment shortly. Add it to your calendar so you don't forget!
            </DialogDescription>
            
            {/* Google Calendar Button */}
            <Button 
              onClick={openGoogleCalendar}
              className="w-full bg-[#0a0a0a] hover:bg-[#D4AF37]/10 text-[#F5F5F5] border border-[#D4AF37]/30 hover:border-[#D4AF37] py-5 font-philosopher flex items-center justify-center gap-3 mb-3 rounded-none"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18.316 5.684H5.684A2.684 2.684 0 003 8.368v10.948a2.684 2.684 0 002.684 2.684h12.632a2.684 2.684 0 002.684-2.684V8.368a2.684 2.684 0 00-2.684-2.684z" fill="#1a1a1a" stroke="#D4AF37" strokeWidth="1.5"/>
                <path d="M16 2v4M8 2v4M3 10h18" stroke="#D4AF37" strokeWidth="1.5" strokeLinecap="round"/>
                <path d="M7 14h2v2H7v-2zM11 14h2v2h-2v-2zM15 14h2v2h-2v-2z" fill="#D4AF37"/>
              </svg>
              Add to Google Calendar
            </Button>

            <Button 
              onClick={() => setSuccessOpen(false)}
              className="w-full bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] py-5 font-philosopher font-bold rounded-none tracking-wide"
            >
              Done
            </Button>

            <p className="text-xs text-gray-400 mt-4">
              You'll receive an email confirmation with all the details.
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UnitDetails;
