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
import { ArrowLeft, Building2, BedDouble, Bath, DollarSign, Heart, MapPin, Calendar, Send, Share2, Clock } from 'lucide-react';
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from '@/components/ui/carousel';
import ShareDialog from '@/components/ShareDialog';
import SEO from '@/components/SEO';
import { trackApartmentView, trackContactForm } from '../utils/analytics';

const UnitDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [unit, setUnit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFavorite, setIsFavorite] = useState(false);
  const [contactOpen, setContactOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);

  useEffect(() => {
    fetchUnit();
    checkFavorite();
  }, [id]);

  const fetchUnit = async () => {
    try {
      const response = await axios.get(`${API}/units/${id}`, { withCredentials: true });
      const unitData = response.data;
      setUnit(unitData);
      
      // Track apartment view
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-xl text-slate-300">Loading...</div>
      </div>
    );
  }

  if (!unit) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-900">
        <div className="text-xl text-slate-300 mb-4">Apartment not found</div>
        <Button onClick={() => navigate('/dashboard')} className="warm-gradient text-slate-900">Back to Dashboard</Button>
      </div>
    );
  }

  const bedroomText = unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} Bedroom`;
  const buildingName = unit.building?.name || 'NYC Apartment';
  const neighborhood = unit.building?.neighborhood || unit.building?.city || 'NYC';
  
  return (
    <div className="min-h-screen bg-slate-900">
      <SEO
        title={`${bedroomText} at ${buildingName} - $${unit.rent.toLocaleString()}/mo - No Fee`}
        description={`No broker fee ${bedroomText.toLowerCase()} apartment in ${neighborhood}. $${unit.rent.toLocaleString()}/month, ${unit.bathrooms} bath. ${unit.description || 'Move-in ready with modern amenities.'}`}
        keywords={`no fee apartment ${neighborhood}, ${bedroomText} ${neighborhood}, ${buildingName}, rent apartment ${unit.building?.city}, no broker fee`}
        url={`/unit/${unit.id}`}
        image={unit.images && unit.images.length > 0 ? unit.images[0] : null}
        type="product"
        structuredData={{
          "@context": "https://schema.org",
          "@type": "Apartment",
          "name": `${bedroomText} at ${buildingName}`,
          "description": unit.description || `${bedroomText} apartment with ${unit.bathrooms} bathroom in ${neighborhood}`,
          "image": unit.images || [],
          "address": {
            "@type": "PostalAddress",
            "streetAddress": unit.building?.address,
            "addressLocality": unit.building?.city,
            "addressRegion": unit.building?.state,
            "postalCode": unit.building?.zip_code,
            "addressCountry": "US"
          },
          "numberOfRooms": unit.bedrooms + 1,
          "numberOfBedrooms": unit.bedrooms,
          "numberOfBathroomsTotal": unit.bathrooms,
          "floorSize": {
            "@type": "QuantitativeValue",
            "value": unit.square_feet || 0,
            "unitText": "sqft"
          },
          "offers": {
            "@type": "Offer",
            "price": unit.rent,
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "priceValidUntil": new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            "seller": {
              "@type": "RealEstateAgent",
              "name": "NoFeesApts.com"
            }
          },
          "amenityFeature": (unit.amenities || []).map(amenity => ({
            "@type": "LocationFeatureSpecification",
            "name": amenity
          }))
        }}
      />
      
      {/* Header */}
      <header className="bg-slate-800/90 backdrop-blur-sm border-b border-amber-500/20 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            data-testid="back-to-dashboard-btn"
            className="text-slate-200 hover:text-amber-500"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Search
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" data-testid="unit-details">
        {/* Image Gallery */}
        <Card className="mb-8 overflow-hidden shadow-2xl border border-amber-500/20 bg-slate-800/90 backdrop-blur-sm">
          {unit.images && unit.images.length > 0 ? (
            <Carousel className="w-full">
              <CarouselContent>
                {unit.images.map((image, index) => (
                  <CarouselItem key={index}>
                    <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                      <img
                        src={image}
                        alt={`Unit ${unit.unit_number} - ${index + 1}`}
                        className="absolute inset-0 w-full h-full object-contain bg-slate-900"
                      />
                    </div>
                  </CarouselItem>
                ))}
              </CarouselContent>
              <CarouselPrevious className="left-4 bg-slate-800/90 border-amber-500/30 text-amber-500" />
              <CarouselNext className="right-4 bg-slate-800/90 border-amber-500/30 text-amber-500" />
            </Carousel>
          ) : (
            <div className="h-96 bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
              <Building2 className="w-24 h-24 text-amber-500/30" />
            </div>
          )}
        </Card>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <Card className="shadow-2xl border border-amber-500/20 bg-slate-800/90 backdrop-blur-sm">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h1 className="text-3xl font-bold text-slate-100 mb-2">
                      {unit.building?.name}
                    </h1>
                    <div className="flex items-center text-slate-300 mb-2">
                      <MapPin className="w-5 h-5 mr-2 text-amber-500" />
                      <span>{unit.building?.address}, {unit.building?.city}, {unit.building?.state}</span>
                    </div>
                    <p className="text-slate-400">Unit {unit.unit_number}</p>
                  </div>
                  <Badge className="warm-gradient text-slate-900 text-lg px-4 py-2 font-semibold">No Fee</Badge>
                </div>

                <div className="flex items-center gap-8 py-6 border-y border-amber-500/20">
                  <div className="flex items-center gap-2 text-slate-200">
                    <BedDouble className="w-6 h-6 text-amber-500" />
                    <span className="text-xl font-semibold">
                      {unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} Bedrooms`}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-200">
                    <Bath className="w-6 h-6 text-amber-500" />
                    <span className="text-xl font-semibold">{unit.bathrooms} Bathrooms</span>
                  </div>
                </div>

                <div className="mt-6">
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-4xl font-bold warm-gradient-text">${unit.rent.toLocaleString()}</span>
                    <span className="text-xl text-slate-400">/month</span>
                  </div>
                  {unit.available_date && (
                    <div className="flex items-center text-slate-300 mt-2">
                      <Calendar className="w-5 h-5 mr-2 text-amber-500" />
                      <span>Available: {unit.available_date}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Description */}
            {unit.description && (
              <Card className="shadow-2xl border border-amber-500/20 bg-slate-800/90 backdrop-blur-sm">
                <CardContent className="p-6">
                  <h2 className="text-2xl font-bold text-slate-100 mb-4">About This Unit</h2>
                  <p className="text-slate-300 leading-relaxed">
                    {formatDescription(unit.description, unit)}
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Amenities */}
            {unit.amenities && unit.amenities.length > 0 && (
              <Card className="shadow-2xl border border-amber-500/20 bg-slate-800/90 backdrop-blur-sm">
                <CardContent className="p-6">
                  <h2 className="text-2xl font-bold text-slate-100 mb-4">Amenities</h2>
                  <div className="flex flex-wrap gap-2">
                    {unit.amenities.map((amenity, index) => (
                      <Badge key={index} variant="secondary" className="px-4 py-2 text-sm bg-slate-700/50 text-slate-200 border border-amber-500/20">
                        {amenity}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card className="shadow-2xl border border-amber-500/20 bg-slate-800/90 backdrop-blur-sm sticky top-24">
              <CardContent className="p-6 space-y-4">
                <Button
                  onClick={() => setShareOpen(true)}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                  data-testid="share-btn"
                >
                  <Share2 className="w-5 h-5 mr-2" />
                  Share This Apartment
                </Button>

                <Button
                  onClick={toggleFavorite}
                  variant={isFavorite ? "default" : "outline"}
                  className={isFavorite ? "w-full bg-red-500 hover:bg-red-600 text-white" : "w-full border-amber-500/30 text-slate-200 hover:bg-slate-700"}
                  data-testid="toggle-favorite-btn"
                >
                  <Heart className={`w-5 h-5 mr-2 ${isFavorite ? 'fill-current' : ''}`} />
                  {isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
                </Button>

                <Dialog open={contactOpen} onOpenChange={setContactOpen}>
                  <DialogTrigger asChild>
                    <Button className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold" data-testid="contact-btn">
                      <Send className="w-5 h-5 mr-2" />
                      Contact About Unit
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="bg-slate-800 border-amber-500/20 text-slate-100">
                    <DialogHeader>
                      <DialogTitle className="text-slate-100">Contact About This Unit</DialogTitle>
                      <DialogDescription className="text-slate-300">
                        Send a message to inquire about this apartment. We'll get back to you soon!
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleContact} className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="name" className="text-slate-200">Name</Label>
                          <Input id="name" name="name" required data-testid="contact-name-input" className="bg-slate-700 border-amber-500/20 text-slate-100" />
                        </div>
                        <div>
                          <Label htmlFor="phone" className="text-slate-200">Phone <span className="text-slate-400 text-sm">(optional)</span></Label>
                          <Input id="phone" name="phone" type="tel" data-testid="contact-phone-input" className="bg-slate-700 border-amber-500/20 text-slate-100" placeholder="Optional" />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="email" className="text-slate-200">Email</Label>
                        <Input id="email" name="email" type="email" required data-testid="contact-email-input" className="bg-slate-700 border-amber-500/20 text-slate-100" />
                      </div>
                      
                      {/* Schedule Viewing Section */}
                      <div className="border border-amber-500/30 rounded-lg p-4 bg-slate-700/30">
                        <div className="flex items-center gap-2 mb-3">
                          <Calendar className="w-4 h-4 text-amber-400" />
                          <Label className="text-amber-400 font-semibold">Schedule a Viewing</Label>
                        </div>
                        
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <Label htmlFor="preferred_date" className="text-slate-200 text-sm">Preferred Date</Label>
                              <Input 
                                id="preferred_date" 
                                name="preferred_date" 
                                type="date"
                                min={new Date().toISOString().split('T')[0]}
                                className="bg-slate-700 border-amber-500/20 text-slate-100"
                              />
                            </div>
                            <div>
                              <Label htmlFor="preferred_time" className="text-slate-200 text-sm">Preferred Time</Label>
                              <select 
                                id="preferred_time" 
                                name="preferred_time"
                                className="w-full h-10 px-3 rounded-md bg-slate-700 border border-amber-500/20 text-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                              >
                                <option value="">Select time</option>
                                <option value="morning">Morning (9am-12pm)</option>
                                <option value="afternoon">Afternoon (12pm-5pm)</option>
                                <option value="evening">Evening (5pm-8pm)</option>
                              </select>
                            </div>
                          </div>
                          
                          <div className="text-xs text-slate-400 flex items-start gap-2">
                            <Clock className="w-3 h-3 mt-0.5 flex-shrink-0" />
                            <span>Alternative time (optional)</span>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <Input 
                                id="alternative_date" 
                                name="alternative_date" 
                                type="date"
                                min={new Date().toISOString().split('T')[0]}
                                placeholder="Alternative date"
                                className="bg-slate-700 border-amber-500/30 text-slate-100 text-sm"
                              />
                            </div>
                            <div>
                              <select 
                                id="alternative_time" 
                                name="alternative_time"
                                className="w-full h-10 px-3 rounded-md bg-slate-700 border border-amber-500/30 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                              >
                                <option value="">Select time</option>
                                <option value="morning">Morning (9am-12pm)</option>
                                <option value="afternoon">Afternoon (12pm-5pm)</option>
                                <option value="evening">Evening (5pm-8pm)</option>
                              </select>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <Label htmlFor="message" className="text-slate-200">Message</Label>
                        <Textarea
                          id="message"
                          name="message"
                          rows={3}
                          placeholder="Tell us about yourself and any questions you have..."
                          required
                          data-testid="contact-message-input"
                          className="bg-slate-700 border-amber-500/20 text-slate-100 placeholder:text-slate-400"
                        />
                      </div>
                      <Button type="submit" className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold" data-testid="contact-submit-btn">
                        <Calendar className="w-4 h-4 mr-2" />
                        Request Viewing
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>

                <div className="pt-4 border-t border-amber-500/20">
                  <h3 className="font-semibold text-slate-100 mb-2">Building Details</h3>
                  <div className="space-y-2 text-sm text-slate-300">
                    <p><strong className="text-amber-500">Address:</strong> {unit.building?.address}</p>
                    <p><strong className="text-amber-500">Neighborhood:</strong> {unit.building?.neighborhood}</p>
                    <p><strong className="text-amber-500">City:</strong> {unit.building?.city}, {unit.building?.state}</p>
                    <p><strong className="text-amber-500">Zip:</strong> {unit.building?.zip_code}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
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
