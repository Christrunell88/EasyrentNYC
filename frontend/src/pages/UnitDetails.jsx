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
import { ArrowLeft, Building2, BedDouble, Bath, Heart, MapPin, Calendar, Send, Share2, Clock, ChevronLeft, ChevronRight, Info } from 'lucide-react';
import ShareDialog from '@/components/ShareDialog';
import SEO from '@/components/SEO';
import { trackApartmentView } from '../utils/analytics';

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
    
    try {
      await axios.post(`${API}/contact`, {
        unit_id: id,
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        message: formData.get('message'),
        preferred_date: formData.get('preferred_date'),
        preferred_time: formData.get('preferred_time'),
        alternative_date: formData.get('alternative_date'),
        alternative_time: formData.get('alternative_time')
      }, { withCredentials: true });
      
      toast.success('Contact request submitted! We will reach out to confirm your viewing time.');
      setContactOpen(false);
    } catch (error) {
      toast.error('Failed to submit request');
    }
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
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!unit) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-white">
        <div className="text-xl text-gray-600 mb-4">Apartment not found</div>
        <Button onClick={() => navigate('/dashboard')} className="bg-[#1a2b4a] hover:bg-[#0f1d33] text-white">Back to Dashboard</Button>
      </div>
    );
  }

  const bedroomText = unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} bed`;
  const buildingName = unit.building?.name || 'NYC Apartment';
  const neighborhood = unit.building?.neighborhood || unit.building?.city || 'NYC';
  const images = unit.images || [];
  
  return (
    <div className="min-h-screen bg-white">
      <SEO
        title={`${bedroomText} at ${buildingName} - $${unit.rent.toLocaleString()}/mo - No Fee`}
        description={`No broker fee ${bedroomText.toLowerCase()} in ${neighborhood}. $${unit.rent.toLocaleString()}/mo, ${unit.bathrooms} bath.`}
        keywords={`no fee apartment ${neighborhood}, ${bedroomText} ${neighborhood}, ${buildingName}`}
        url={`/unit/${unit.id}`}
        image={images.length > 0 ? images[0] : null}
        type="product"
      />
      
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={() => navigate(-1)}
              data-testid="back-to-dashboard-btn"
              className="text-gray-600 hover:text-[#1a2b4a]"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            {/* Breadcrumb */}
            <nav className="hidden md:flex text-sm text-gray-500">
              <span>Rentals</span>
              <span className="mx-2">›</span>
              <span>{unit.building?.state || 'NY'}</span>
              <span className="mx-2">›</span>
              <span className="text-gray-700">{neighborhood}</span>
              <span className="mx-2">›</span>
              <span className="text-[#1a2b4a] font-medium">{unit.building?.address} #{unit.unit_number}</span>
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
            <div className="relative bg-gray-100 rounded-lg overflow-hidden mb-3">
              {images.length > 0 ? (
                <>
                  <div className="relative aspect-[4/3]">
                    <img
                      src={images[currentImageIndex]}
                      alt={`${buildingName} - Image ${currentImageIndex + 1}`}
                      className="w-full h-full object-cover"
                    />
                    
                    {/* Image Counter Badge */}
                    <div className="absolute bottom-4 left-4 bg-black/70 text-white px-3 py-1.5 rounded text-sm font-medium">
                      {currentImageIndex + 1} of {images.length}
                    </div>
                    
                    {/* Navigation Arrows */}
                    {images.length > 1 && (
                      <>
                        <button
                          onClick={prevImage}
                          className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-lg transition-all"
                        >
                          <ChevronLeft className="w-6 h-6 text-gray-700" />
                        </button>
                        <button
                          onClick={nextImage}
                          className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-lg transition-all"
                        >
                          <ChevronRight className="w-6 h-6 text-gray-700" />
                        </button>
                      </>
                    )}
                  </div>
                </>
              ) : (
                <div className="aspect-[4/3] bg-gray-200 flex items-center justify-center">
                  <Building2 className="w-24 h-24 text-gray-400" />
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
                    className={`flex-shrink-0 w-20 h-16 rounded overflow-hidden border-2 transition-all ${
                      index === currentImageIndex 
                        ? 'border-[#1a2b4a] ring-2 ring-[#1a2b4a]/30' 
                        : 'border-transparent hover:border-gray-300'
                    }`}
                  >
                    <img
                      src={image}
                      alt={`Thumbnail ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
                {images.length > 8 && (
                  <div className="flex-shrink-0 w-20 h-16 rounded bg-gray-100 flex items-center justify-center text-gray-500 text-sm font-medium">
                    +{images.length - 8}
                  </div>
                )}
              </div>
            )}

            {/* About Section - Below Images */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h2 className="text-xl font-bold text-[#1a2b4a] mb-4">About</h2>
              {unit.description ? (
                <p className="text-gray-600 leading-relaxed">
                  {formatDescription(unit.description, unit)}
                </p>
              ) : (
                <p className="text-gray-500">
                  {bedroomText === 'Studio' ? 'Studio' : `${unit.bedrooms} bedroom`} apartment with {unit.bathrooms} bathroom{unit.bathrooms > 1 ? 's' : ''} in {neighborhood}. No broker fee required.
                </p>
              )}
              
              {/* Amenities */}
              {unit.amenities && unit.amenities.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-[#1a2b4a] mb-3">Features & Amenities</h3>
                  <div className="flex flex-wrap gap-2">
                    {unit.amenities.map((amenity, index) => (
                      <Badge key={index} variant="secondary" className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 border border-gray-200">
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
                <h1 className="text-2xl md:text-3xl font-bold text-[#1a2b4a] mb-1">
                  {unit.building?.address}
                </h1>
                <p className="text-lg text-gray-600">#{unit.unit_number}</p>
              </div>

              {/* Price Section */}
              <div className="mb-6">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl md:text-4xl font-bold text-[#1a2b4a]">${unit.rent.toLocaleString()}</span>
                  <span className="text-gray-500 text-lg">FOR RENT</span>
                </div>
                <p className="text-sm text-gray-500 mt-1">No broker fee. Move-in ready.</p>
              </div>

              {/* Key Details Row */}
              <div className="flex items-center gap-4 text-gray-700 py-4 border-y border-gray-200 mb-6">
                {unit.square_feet && (
                  <>
                    <span className="font-medium">{unit.square_feet} ft²</span>
                    <span className="text-gray-300">|</span>
                  </>
                )}
                <span className="font-medium">{unit.bedrooms + 1} rooms</span>
                <span className="text-gray-300">|</span>
                <span className="font-medium">{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} bed`}</span>
                <span className="text-gray-300">|</span>
                <span className="font-medium">{unit.bathrooms} bath</span>
              </div>

              {/* Location */}
              <div className="mb-6 text-sm">
                <p className="text-gray-500">Rental unit</p>
                <p className="text-[#1a2b4a] font-medium">{neighborhood}</p>
              </div>

              {/* No Fee Notice */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-gray-700">
                    <strong>No broker fee</strong> - You won't be charged a broker fee for this apartment.
                  </p>
                </div>
              </div>

              {/* Schedule Viewing Button */}
              <Dialog open={contactOpen} onOpenChange={setContactOpen}>
                <DialogTrigger asChild>
                  <Button 
                    className="w-full bg-[#1a2b4a] hover:bg-[#0f1d33] text-white py-5 text-base font-semibold mb-4 flex items-center justify-center gap-2 transition-all hover:shadow-lg" 
                    data-testid="contact-btn"
                  >
                    <Calendar className="w-5 h-5" />
                    Schedule Viewing
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-white border-gray-200 text-gray-900 max-w-md">
                  <DialogHeader>
                    <DialogTitle className="text-[#1a2b4a]">Contact About This Unit</DialogTitle>
                    <DialogDescription className="text-gray-500">
                      Send a message to inquire about this apartment.
                    </DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleContact} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="name" className="text-gray-700">Name</Label>
                        <Input id="name" name="name" required data-testid="contact-name-input" className="border-gray-300" />
                      </div>
                      <div>
                        <Label htmlFor="phone" className="text-gray-700">Phone</Label>
                        <Input id="phone" name="phone" type="tel" data-testid="contact-phone-input" className="border-gray-300" />
                      </div>
                    </div>
                    <div>
                      <Label htmlFor="email" className="text-gray-700">Email</Label>
                      <Input id="email" name="email" type="email" required data-testid="contact-email-input" className="border-gray-300" />
                    </div>
                    
                    {/* Schedule Viewing */}
                    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      <div className="flex items-center gap-2 mb-3">
                        <Calendar className="w-4 h-4 text-[#1a2b4a]" />
                        <Label className="text-[#1a2b4a] font-semibold">Schedule a Viewing</Label>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label htmlFor="preferred_date" className="text-gray-600 text-sm">Date</Label>
                          <Input 
                            id="preferred_date" 
                            name="preferred_date" 
                            type="date"
                            min={new Date().toISOString().split('T')[0]}
                            className="border-gray-300"
                          />
                        </div>
                        <div>
                          <Label htmlFor="preferred_time" className="text-gray-600 text-sm">Time</Label>
                          <select 
                            id="preferred_time" 
                            name="preferred_time"
                            className="w-full h-10 px-3 rounded-md border border-gray-300 text-gray-700 focus:outline-none focus:ring-2 focus:ring-[#1a2b4a]/30"
                          >
                            <option value="">Select time</option>
                            <option value="morning">Morning (9am-12pm)</option>
                            <option value="afternoon">Afternoon (12pm-5pm)</option>
                            <option value="evening">Evening (5pm-8pm)</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="message" className="text-gray-700">Message</Label>
                      <Textarea
                        id="message"
                        name="message"
                        rows={3}
                        placeholder="I'm interested in this apartment..."
                        required
                        data-testid="contact-message-input"
                        className="border-gray-300"
                      />
                    </div>
                    <Button type="submit" className="w-full bg-[#1a2b4a] hover:bg-[#0f1d33] text-white" data-testid="contact-submit-btn">
                      Send Message
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>

              {/* Action Buttons Row */}
              <div className="flex gap-3 mb-6">
                <Button
                  onClick={toggleFavorite}
                  variant="outline"
                  className={`flex-1 border-gray-300 ${isFavorite ? 'bg-red-50 border-red-300 text-red-600' : 'text-gray-700 hover:bg-gray-50'}`}
                  data-testid="toggle-favorite-btn"
                >
                  <Heart className={`w-4 h-4 mr-2 ${isFavorite ? 'fill-current' : ''}`} />
                  SAVE
                </Button>
                <Button
                  onClick={() => setShareOpen(true)}
                  variant="outline"
                  className="flex-1 border-gray-300 text-gray-700 hover:bg-gray-50"
                  data-testid="share-btn"
                >
                  <Share2 className="w-4 h-4 mr-2" />
                  SHARE
                </Button>
              </div>

              {/* Building Details Card */}
              <Card className="border border-gray-200">
                <CardContent className="p-4">
                  <h3 className="font-semibold text-[#1a2b4a] mb-3">Building Details</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Building</span>
                      <span className="text-gray-900 font-medium">{unit.building?.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Address</span>
                      <span className="text-gray-900">{unit.building?.address}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Neighborhood</span>
                      <span className="text-gray-900">{unit.building?.neighborhood}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">City</span>
                      <span className="text-gray-900">{unit.building?.city}, {unit.building?.state}</span>
                    </div>
                    {unit.available_date && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Available</span>
                        <span className="text-green-600 font-medium">{unit.available_date}</span>
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
    </div>
  );
};

export default UnitDetails;
