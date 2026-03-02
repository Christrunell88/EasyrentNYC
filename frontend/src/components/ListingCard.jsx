import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, ChevronLeft, ChevronRight, MapPin, BedDouble, Mail, Phone, Send } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import axios from 'axios';
import { API } from '../config/api';

const ListingCard = ({ 
  unit, 
  user, 
  isFavorite = false, 
  onToggleFavorite, 
  onShare,
  showBlur = false,
  theme = 'dark',
  hideAddress = false
}) => {
  const navigate = useNavigate();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);
  const [contactOpen, setContactOpen] = useState(false);
  const [contactLoading, setContactLoading] = useState(false);
  const imageContainerRef = useRef(null);

  // Theme-aware colors
  const isLight = theme === 'light';
  const cardBg = isLight ? 'bg-white' : 'bg-[#1a1a1a]';
  const cardBorder = isLight ? 'border-gray-200 hover:border-amber-400' : 'border-[#D4AF37]/10 hover:border-[#D4AF37]/40';
  const cardShadow = isLight 
    ? 'shadow-sm hover:shadow-md' 
    : 'shadow-lg shadow-black/20 hover:shadow-[0_15px_40px_rgba(0,0,0,0.4)]';
  const textPrimary = isLight ? 'text-gray-900' : 'text-[#F5F5F5]';
  const textMuted = isLight ? 'text-gray-500' : 'text-[#888]';
  const accentColor = isLight ? 'text-amber-600' : 'text-[#D4AF37]';

  // Smart image selection - prioritize interior images
  const getInteriorImages = (allImages) => {
    if (!allImages || allImages.length === 0) return [];
    const exteriorKeywords = ['slideshow', 'building', 'exterior', 'facade', 'street', 'aerial', '_web_', 'hero'];
    const interiorKeywords = ['living', 'bedroom', 'kitchen', 'bath', 'interior', 'unit_photos', 'apartment', 'room'];
    return [...allImages].sort((a, b) => {
      const aLower = a.toLowerCase();
      const bLower = b.toLowerCase();
      const aIsExterior = exteriorKeywords.some(kw => aLower.includes(kw));
      const bIsExterior = exteriorKeywords.some(kw => bLower.includes(kw));
      const aIsInterior = interiorKeywords.some(kw => aLower.includes(kw));
      const bIsInterior = interiorKeywords.some(kw => bLower.includes(kw));
      if (aIsInterior && !bIsInterior) return -1;
      if (bIsInterior && !aIsInterior) return 1;
      if (aIsExterior && !bIsExterior) return 1;
      if (bIsExterior && !aIsExterior) return -1;
      return 0;
    });
  };

  const images = getInteriorImages(unit.images);
  const displayImages = images.slice(0, 4);
  
  const getBedText = (bedrooms) => {
    if (bedrooms === 0) return 'Studio';
    if (bedrooms === 1) return '1 Bed';
    return `${bedrooms} Bed`;
  };
  const bedText = getBedText(unit.bedrooms);
  const bathText = `${unit.bathrooms} Bath`;

  // Handle contact form submission
  const handleContactSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!user) {
      toast.error('Please sign in to contact agent');
      navigate('/auth');
      return;
    }
    
    setContactLoading(true);
    const formData = new FormData(e.target);
    
    try {
      await axios.post(`${API}/api/contact`, {
        unit_id: unit.id,
        name: formData.get('name'),
        email: formData.get('email'),
        phone: formData.get('phone') || '',
        message: formData.get('message'),
      }, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('session_token')}` }
      });
      
      toast.success('Message sent!', {
        description: 'The agent will contact you shortly.'
      });
      setContactOpen(false);
      e.target.reset();
    } catch (error) {
      toast.error('Failed to send message', {
        description: error.response?.data?.detail || 'Please try again.'
      });
    } finally {
      setContactLoading(false);
    }
  };

  // Swipe detection
  const minSwipeDistance = 50;
  const onTouchStart = (e) => { setTouchEnd(null); setTouchStart(e.targetTouches[0].clientX); };
  const onTouchMove = (e) => { setTouchEnd(e.targetTouches[0].clientX); };
  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    if (distance > minSwipeDistance && images.length > 1) {
      setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
    }
    if (distance < -minSwipeDistance && images.length > 1) {
      setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
    }
  };

  const handlePrevImage = (e) => { e.stopPropagation(); setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1)); };
  const handleNextImage = (e) => { e.stopPropagation(); setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1)); };
  const handleFavoriteClick = (e) => { e.stopPropagation(); onToggleFavorite?.(unit.id); };
  const handleCardClick = () => {
    if (user) { navigate(`/unit/${unit.id}`); } 
    else { sessionStorage.setItem('redirectAfterLogin', `/unit/${unit.id}`); navigate('/auth'); }
  };

  return (
    <div
      className={`group ${cardBg} rounded-lg overflow-hidden transition-all duration-300 cursor-pointer border ${cardBorder} ${cardShadow}`}
      onClick={handleCardClick}
    >
      {/* Main Image */}
      <div 
        ref={imageContainerRef}
        className={`relative aspect-[4/3] ${isLight ? 'bg-gray-100' : 'bg-[#111]'} overflow-hidden`}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        {images.length > 0 ? (
          <>
            <div className="relative w-full h-full">
              {displayImages.map((img, idx) => (
                <img
                  key={idx}
                  src={img}
                  alt={`${bedText} apartment at ${unit.building?.neighborhood || 'NYC'}`}
                  className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${idx === currentImageIndex ? 'opacity-100' : 'opacity-0'}`}
                  loading={idx === 0 ? 'eager' : 'lazy'}
                />
              ))}
            </div>
            
            {/* Navigation arrows on hover */}
            {images.length > 1 && (
              <>
                <button onClick={handlePrevImage} className="absolute left-2 top-1/2 -translate-y-1/2 w-7 h-7 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronLeft className="w-4 h-4 text-white" />
                </button>
                <button onClick={handleNextImage} className="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <ChevronRight className="w-4 h-4 text-white" />
                </button>
              </>
            )}
          </>
        ) : (
          <div className={`w-full h-full flex items-center justify-center ${isLight ? 'bg-gray-100' : 'bg-[#111]'}`}>
            <BedDouble className={`w-10 h-10 ${isLight ? 'text-gray-300' : 'text-[#333]'}`} />
          </div>
        )}
        
        {/* Favorite button */}
        <button onClick={handleFavoriteClick} className={`absolute top-2 right-2 w-8 h-8 ${isLight ? 'bg-white/90' : 'bg-black/50'} rounded-full flex items-center justify-center`}>
          <Heart className={`w-4 h-4 ${isFavorite ? (isLight ? 'fill-amber-500 text-amber-500' : 'fill-[#D4AF37] text-[#D4AF37]') : (isLight ? 'text-gray-500' : 'text-white')}`} />
        </button>
      </div>

      {/* Thumbnail strip below main image */}
      {displayImages.length > 1 && (
        <div className={`flex gap-1 p-1 ${isLight ? 'bg-gray-50' : 'bg-[#111]'}`}>
          {displayImages.map((img, idx) => (
            <button
              key={idx}
              onClick={(e) => { e.stopPropagation(); setCurrentImageIndex(idx); }}
              className={`flex-1 aspect-[3/2] overflow-hidden rounded-sm ${idx === currentImageIndex ? (isLight ? 'ring-2 ring-amber-500' : 'ring-2 ring-[#D4AF37]') : 'opacity-60 hover:opacity-100'}`}
            >
              <img src={img} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      )}
      
      {/* Content - minimal and clean */}
      <div className="p-3">
        {/* Price and beds/baths on same line */}
        <div className="flex items-baseline justify-between mb-1">
          <span className={`text-lg font-bold ${isLight ? 'text-gray-900' : 'text-white'}`}>
            ${unit.rent?.toLocaleString()}<span className={`text-xs font-normal ${textMuted}`}>/mo</span>
          </span>
          <span className={`text-xs ${textMuted}`}>{bedText} · {bathText}</span>
        </div>
        
        {/* Address or blur */}
        {showBlur && !user ? (
          <div className="relative">
            <p className={`text-xs blur-sm select-none ${textMuted}`}>
              {unit.building?.address?.substring(0, 20) || 'Premium Location'}
            </p>
            <div className="absolute inset-0 flex items-center">
              <span className={`text-xs ${accentColor}`}>Sign up to view</span>
            </div>
          </div>
        ) : hideAddress ? (
          <p className={`text-xs ${textMuted} truncate`}>
            <MapPin className="w-3 h-3 inline mr-1" />
            {unit.building?.neighborhood || unit.building?.city || 'Manhattan'}
          </p>
        ) : (
          <p className={`text-xs ${textMuted} truncate`}>
            <MapPin className="w-3 h-3 inline mr-1" />
            {unit.building?.address}{unit.unit_number && ` #${unit.unit_number}`}
          </p>
        )}

        {/* Contact buttons - smaller */}
        <div className="flex gap-1.5 mt-2">
          <button
            onClick={(e) => { e.stopPropagation(); setContactOpen(true); }}
            data-testid="email-agent-button"
            className={`flex-1 flex items-center justify-center gap-1 py-1.5 ${isLight ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'bg-[#D4AF37] hover:bg-[#E5C158] text-black'} text-xs font-medium rounded transition-colors`}
          >
            <Mail className="w-3 h-3" />
            Email
          </button>
          <a
            href="tel:646-408-8048"
            onClick={(e) => e.stopPropagation()}
            className={`flex-1 flex items-center justify-center gap-1 py-1.5 ${isLight ? 'bg-gray-100 hover:bg-gray-200 text-gray-700' : 'bg-[#222] hover:bg-[#333] text-white'} text-xs font-medium rounded transition-colors`}
          >
            <Phone className="w-3 h-3" />
            Call
          </a>
        </div>
      </div>

      {/* Contact Modal */}
      <Dialog open={contactOpen} onOpenChange={setContactOpen}>
        <DialogContent 
          className="sm:max-w-md bg-[#1a1a1a] border border-[#D4AF37]/30 text-white"
          onClick={(e) => e.stopPropagation()}
          data-testid="contact-modal"
        >
          <DialogHeader>
            <DialogTitle className="text-[#D4AF37] font-philosopher text-xl">
              Contact Agent
            </DialogTitle>
            <p className="text-[#A0A0A0] text-sm font-philosopher">
              {unit.building?.address} {unit.unit_number && `#${unit.unit_number}`}
            </p>
          </DialogHeader>
          
          <form onSubmit={handleContactSubmit} className="space-y-4 mt-4">
            <div>
              <Input
                name="name"
                placeholder="Your Name *"
                required
                defaultValue={user?.full_name || ''}
                className="bg-[#0a0a0a] border-[#D4AF37]/30 text-white placeholder:text-gray-500 focus:border-[#D4AF37]"
                data-testid="contact-name-input"
              />
            </div>
            <div>
              <Input
                name="email"
                type="email"
                placeholder="Your Email *"
                required
                defaultValue={user?.email || ''}
                className="bg-[#0a0a0a] border-[#D4AF37]/30 text-white placeholder:text-gray-500 focus:border-[#D4AF37]"
                data-testid="contact-email-input"
              />
            </div>
            <div>
              <Input
                name="phone"
                type="tel"
                placeholder="Phone (optional)"
                className="bg-[#0a0a0a] border-[#D4AF37]/30 text-white placeholder:text-gray-500 focus:border-[#D4AF37]"
                data-testid="contact-phone-input"
              />
            </div>
            <div>
              <Textarea
                name="message"
                placeholder="Your message... *"
                required
                rows={3}
                defaultValue={`Hi, I'm interested in the ${unit.bedrooms === 0 ? 'studio' : `${unit.bedrooms} bedroom`} apartment at ${unit.building?.address || 'this building'}${unit.unit_number ? ` #${unit.unit_number}` : ''} for $${unit.rent?.toLocaleString()}/month. Please contact me with more details.`}
                className="bg-[#0a0a0a] border-[#D4AF37]/30 text-white placeholder:text-gray-500 focus:border-[#D4AF37] resize-none"
                data-testid="contact-message-input"
              />
            </div>
            
            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  setContactOpen(false);
                }}
                className="flex-1 border-[#D4AF37]/30 text-[#D4AF37] hover:bg-[#D4AF37]/10"
                data-testid="contact-cancel-button"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={contactLoading}
                className="flex-1 bg-[#D4AF37] text-[#0a0a0a] hover:bg-[#E5C158] font-philosopher font-bold"
                data-testid="contact-submit-button"
              >
                {contactLoading ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-[#0a0a0a]/30 border-t-[#0a0a0a] rounded-full animate-spin" />
                    Sending...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Send className="w-4 h-4" />
                    Send Message
                  </span>
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ListingCard;
