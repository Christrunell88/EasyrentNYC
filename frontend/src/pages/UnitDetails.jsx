import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { API } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ArrowLeft, Building2, BedDouble, Bath, DollarSign, Heart, MapPin, Calendar, Send, Share2 } from 'lucide-react';
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious } from '@/components/ui/carousel';
import ShareDialog from '@/components/ShareDialog';

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
      setUnit(response.data);
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
        message: formData.get('message')
      }, { withCredentials: true });
      
      toast.success('Contact request submitted!');
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

  return (
    <div className="min-h-screen bg-slate-900">
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
                    <div className="h-96 bg-slate-700">
                      <img
                        src={image}
                        alt={`Unit ${unit.unit_number} - ${index + 1}`}
                        className="w-full h-full object-cover"
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
                  <h2 className="text-2xl font-bold text-slate-100 mb-4">Description</h2>
                  <p className="text-slate-300 leading-relaxed">{unit.description}</p>
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
                      <div>
                        <Label htmlFor="name" className="text-slate-200">Name</Label>
                        <Input id="name" name="name" required data-testid="contact-name-input" className="bg-slate-700 border-amber-500/20 text-slate-100" />
                      </div>
                      <div>
                        <Label htmlFor="email" className="text-slate-200">Email</Label>
                        <Input id="email" name="email" type="email" required data-testid="contact-email-input" className="bg-slate-700 border-amber-500/20 text-slate-100" />
                      </div>
                      <div>
                        <Label htmlFor="phone" className="text-slate-200">Phone (Optional)</Label>
                        <Input id="phone" name="phone" type="tel" data-testid="contact-phone-input" className="bg-slate-700 border-amber-500/20 text-slate-100" />
                      </div>
                      <div>
                        <Label htmlFor="message" className="text-slate-200">Message</Label>
                        <Textarea
                          id="message"
                          name="message"
                          rows={4}
                          placeholder="I'm interested in this unit..."
                          required
                          data-testid="contact-message-input"
                          className="bg-slate-700 border-amber-500/20 text-slate-100 placeholder:text-slate-400"
                        />
                      </div>
                      <Button type="submit" className="w-full warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold" data-testid="contact-submit-btn">
                        Send Message
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
    </div>
  );
};

export default UnitDetails;
