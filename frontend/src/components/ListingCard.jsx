import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, ChevronLeft, ChevronRight, MapPin, BedDouble, Bath, Maximize, Mail, Phone, X, Send } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Helper function to determine rental type based on unit characteristics
const getRentalType = (unit) => {
  const rent = unit.rent || 0;
  const amenities = (unit.amenities || []).map(a => a.toLowerCase()).join(' ');
  const buildingName = (unit.building?.name || '').toLowerCase();
  
  // Luxury indicators
  const luxuryKeywords = ['luxury', 'penthouse', 'doorman', 'concierge', 'rooftop', 'pool', 'gym', 'spa', 'terrace', 'balcony'];
  const hasLuxuryAmenities = luxuryKeywords.some(kw => amenities.includes(kw) || buildingName.includes(kw));
  
  // Price-based categorization (NYC market)
  if (rent >= 5000 || hasLuxuryAmenities) {
    return 'Luxury Rental';
  } else if (rent >= 3500) {
    return 'Modern Rental';
  } else if (rent >= 2500) {
    return 'Prime Rental';
  } else if (unit.bedrooms === 0) {
    return 'Studio Rental';
  } else {
    return 'No Fee Rental';
  }
};

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
  const [isHovered, setIsHovered] = useState(false);
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
    ? 'shadow-md hover:shadow-xl hover:shadow-amber-100/50' 
    : 'shadow-lg shadow-black/20 hover:shadow-[0_25px_60px_rgba(0,0,0,0.6),0_0_40px_rgba(212,175,55,0.08)]';
  const textPrimary = isLight ? 'text-gray-900' : 'text-[#F5F5F5]';
  const textSecondary = isLight ? 'text-gray-600' : 'text-[#A0A0A0]';
  const textMuted = isLight ? 'text-gray-500' : 'text-[#888]';
  const accentColor = isLight ? 'text-amber-600' : 'text-[#D4AF37]';
  const bgAccent = isLight ? 'bg-amber-500' : 'bg-[#D4AF37]';
  const bgMuted = isLight ? 'bg-gray-100' : 'bg-[#111]';

  const images = unit.images?.length > 0 ? unit.images : [];
  const hasMultipleImages = images.length > 1;
  const displayImages = images.slice(0, 5); // Max 5 images for carousel
  
  // Convert bedrooms to rooms: Studio=2, 1BR=3, 2BR=4, etc.
  const getRoomCount = (bedrooms) => {
    if (bedrooms === 0) return 2; // Studio = 2 rooms
    return bedrooms + 2; // 1BR = 3 rooms, 2BR = 4 rooms, etc.
  };
  const roomCount = getRoomCount(unit.bedrooms);
  const roomText = `${roomCount} Rooms`;
  const bathText = `${unit.bathrooms} bath`;
  const sqftText = unit.square_feet ? `${unit.square_feet.toLocaleString()} ft²` : null;

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
      await axios.post(`${API}/contact`, {
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

  // Swipe detection threshold
  const minSwipeDistance = 50;

  const onTouchStart = (e) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;
    
    if (isLeftSwipe && hasMultipleImages) {
      setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
    }
    if (isRightSwipe && hasMultipleImages) {
      setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
    }
  };

  // Auto-advance on hover (desktop)
  useEffect(() => {
    let interval;
    if (isHovered && hasMultipleImages && images.length > 1) {
      interval = setInterval(() => {
        setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
      }, 2000); // Change image every 2 seconds on hover
    }
    return () => clearInterval(interval);
  }, [isHovered, hasMultipleImages, images.length]);
  
  const handlePrevImage = (e) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };
  
  const handleNextImage = (e) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  const handleFavoriteClick = (e) => {
    e.stopPropagation();
    onToggleFavorite?.(unit.id);
  };

  const handleCardClick = () => {
    if (user) {
      navigate(`/unit/${unit.id}`);
    } else {
      sessionStorage.setItem('redirectAfterLogin', `/unit/${unit.id}`);
      navigate('/auth');
    }
  };

  return (
    <div
      className={`group ${cardBg} rounded-lg overflow-hidden transition-all duration-400 cursor-pointer border ${cardBorder} ${cardShadow} hover:-translate-y-1`}
      onClick={handleCardClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => { setIsHovered(false); setCurrentImageIndex(0); }}
    >
      {/* Image Section with Carousel */}
      <div 
        ref={imageContainerRef}
        className={`relative aspect-[4/3] ${isLight ? 'bg-gray-100' : 'bg-[#111111]'} overflow-hidden`}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        {images.length > 0 ? (
          <>
            {/* Main Image with Slide Animation */}
            <div className="relative w-full h-full">
              {displayImages.map((img, idx) => (
                <img
                  key={idx}
                  src={img}
                  alt={`${unit.bedrooms === 0 ? 'Studio' : unit.bedrooms === 1 ? 'One bedroom' : `${unit.bedrooms} bedroom`} apartment photo ${idx + 1} at ${unit.building?.name || 'luxury building'}, ${unit.building?.neighborhood || unit.building?.city || 'NYC'}`}
                  className={`absolute inset-0 w-full h-full object-cover transition-all duration-500 ${
                    idx === currentImageIndex 
                      ? 'opacity-100 scale-100' 
                      : 'opacity-0 scale-105'
                  }`}
                  loading={idx === 0 ? 'eager' : 'lazy'}
                />
              ))}
            </div>
            
            {/* Image Navigation Arrows - Always visible on desktop hover */}
            {hasMultipleImages && isHovered && (
              <>
                <button
                  onClick={handlePrevImage}
                  className="absolute left-2 top-1/2 -translate-y-1/2 w-9 h-9 bg-[#0a0a0a]/80 hover:bg-[#D4AF37] rounded-full border border-[#D4AF37]/30 flex items-center justify-center transition-all group/btn backdrop-blur-sm"
                >
                  <ChevronLeft className="w-5 h-5 text-[#D4AF37] group-hover/btn:text-[#0a0a0a]" />
                </button>
                <button
                  onClick={handleNextImage}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 bg-[#0a0a0a]/80 hover:bg-[#D4AF37] rounded-full border border-[#D4AF37]/30 flex items-center justify-center transition-all group/btn backdrop-blur-sm"
                >
                  <ChevronRight className="w-5 h-5 text-[#D4AF37] group-hover/btn:text-[#0a0a0a]" />
                </button>
              </>
            )}
            
            {/* Thumbnail Strip - Shows 3 thumbnails on hover */}
            {hasMultipleImages && isHovered && displayImages.length >= 2 && (
              <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex gap-1.5 p-1.5 bg-[#0a0a0a]/70 backdrop-blur-sm rounded-lg">
                {displayImages.slice(0, 3).map((img, idx) => (
                  <button
                    key={idx}
                    onClick={(e) => {
                      e.stopPropagation();
                      setCurrentImageIndex(idx);
                    }}
                    className={`relative w-12 h-9 rounded overflow-hidden transition-all ${
                      idx === currentImageIndex 
                        ? 'ring-2 ring-[#D4AF37] scale-105' 
                        : 'opacity-70 hover:opacity-100'
                    }`}
                  >
                    <img
                      src={img}
                      alt={`Thumbnail ${idx + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
                {displayImages.length > 3 && (
                  <div className="w-12 h-9 rounded bg-[#1a1a1a] flex items-center justify-center text-[#D4AF37] text-xs font-semibold">
                    +{images.length - 3}
                  </div>
                )}
              </div>
            )}
            
            {/* Image Dots Indicator - Always visible */}
            {hasMultipleImages && (
              <div className={`absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5 transition-opacity ${isHovered ? 'opacity-0' : 'opacity-100'}`}>
                {displayImages.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={(e) => {
                      e.stopPropagation();
                      setCurrentImageIndex(idx);
                    }}
                    className={`h-1.5 rounded-full transition-all ${
                      idx === currentImageIndex 
                        ? 'bg-[#D4AF37] w-4' 
                        : 'bg-white/50 w-1.5 hover:bg-white/80'
                    }`}
                  />
                ))}
                {images.length > 5 && (
                  <span className="text-white/70 text-[10px] font-medium ml-1">+{images.length - 5}</span>
                )}
              </div>
            )}

            {/* Photo Count Badge */}
            {images.length > 1 && (
              <div className="absolute top-3 left-3 px-2 py-1 bg-[#0a0a0a]/70 backdrop-blur-sm rounded text-white text-xs font-medium flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {images.length}
              </div>
            )}

            {/* Swipe Hint for Mobile - Only on first render */}
            {hasMultipleImages && (
              <div className="absolute bottom-3 right-3 md:hidden px-2 py-1 bg-[#0a0a0a]/60 backdrop-blur-sm rounded text-white/70 text-[10px] flex items-center gap-1">
                <ChevronLeft className="w-3 h-3" />
                Swipe
                <ChevronRight className="w-3 h-3" />
              </div>
            )}
          </>
        ) : (
          <div className={`w-full h-full flex items-center justify-center ${isLight ? 'bg-gray-100' : 'bg-[#111111]'}`}>
            <div className={`text-center ${isLight ? 'text-gray-400' : 'text-[#888888]'}`}>
              <BedDouble className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <span className="text-sm font-philosopher">No image</span>
            </div>
          </div>
        )}
        
        {/* Favorite Button */}
        <button
          onClick={handleFavoriteClick}
          className={`absolute top-3 right-3 w-9 h-9 ${isLight ? 'bg-white/90 hover:bg-amber-50 border-amber-300' : 'bg-[#0a0a0a]/80 hover:bg-[#D4AF37]/20 border-[#D4AF37]/30'} border flex items-center justify-center transition-all hover:scale-110 rounded-full`}
        >
          <Heart
            className={`w-5 h-5 transition-colors ${
              isFavorite 
                ? isLight ? 'fill-amber-500 text-amber-500' : 'fill-[#D4AF37] text-[#D4AF37]'
                : isLight ? 'text-amber-400 hover:text-amber-500' : 'text-[#D4AF37]/70 hover:text-[#D4AF37]'
            }`}
          />
        </button>
        
        {/* Contact Agent Buttons */}
        <div className="absolute top-3 left-3 flex gap-1.5">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setContactOpen(true);
            }}
            data-testid="email-agent-button"
            className={`flex items-center gap-1 px-2 py-1 ${isLight ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a]'} font-philosopher font-bold text-xs rounded-none tracking-wide transition-colors`}
            title="Email Agent"
          >
            <Mail className="w-3 h-3" />
            <span>Email Agent</span>
          </button>
          <a
            href="tel:646-408-8048"
            onClick={(e) => e.stopPropagation()}
            className={`flex items-center gap-1 px-2 py-1 ${isLight ? 'bg-white/90 border border-amber-400 text-amber-600 hover:bg-amber-50' : 'bg-[#0a0a0a]/80 border border-[#D4AF37]/50 text-[#D4AF37] hover:bg-[#D4AF37]/20'} font-philosopher font-bold text-xs rounded-none tracking-wide transition-colors`}
            title="Call Agent"
          >
            <Phone className="w-3 h-3" />
            <span>646-408-8048</span>
          </a>
        </div>
        
        {/* Featured Badge */}
        {unit.is_featured && (
          <Badge className={`absolute bottom-3 left-3 ${isLight ? 'bg-white/90 border-amber-400 text-amber-600' : 'bg-[#0a0a0a]/80 border-[#D4AF37]/50 text-[#D4AF37]'} border font-philosopher font-bold px-2.5 py-1 text-xs rounded-none tracking-wide`}>
            FEATURED
          </Badge>
        )}
      </div>
      
      {/* Content Section */}
      <div className="p-4">
        {/* Price Row */}
        <div className="flex items-baseline justify-between mb-2">
          <div className="flex items-baseline">
            <span className={`text-2xl font-philosopher font-bold ${isLight ? 'text-amber-600' : 'text-[#D4AF37]'}`}>
              ${unit.rent?.toLocaleString()}
            </span>
            <span className={`text-sm ml-1 font-philosopher ${textMuted}`}>/mo</span>
          </div>
          {sqftText && (
            <span className={`text-sm font-philosopher ${textMuted}`}>
              ${Math.round(unit.rent / unit.square_feet)}/ft²
            </span>
          )}
        </div>
        
        {/* Details Row */}
        <div className={`flex items-center gap-1 text-sm mb-3 font-philosopher ${textPrimary}`}>
          <span className="font-medium">{roomText}</span>
          <span className={isLight ? 'text-amber-400' : 'text-[#D4AF37]/50'}>|</span>
          <span className="font-medium">{bathText}</span>
          {sqftText && (
            <>
              <span className={isLight ? 'text-amber-400' : 'text-[#D4AF37]/50'}>|</span>
              <span className="font-medium">{sqftText}</span>
            </>
          )}
        </div>
        
        {/* Address */}
        <div className="mb-2">
          {hideAddress ? (
            // Show only building name and neighborhood when hideAddress is true
            <div>
              <h3 className={`font-philosopher font-semibold truncate ${textPrimary}`}>
                {unit.building?.name || 'Premium Building'}
              </h3>
              <div className={`flex items-center gap-1.5 text-sm font-philosopher mt-1 ${textMuted}`}>
                <MapPin className={`w-3.5 h-3.5 ${accentColor}`} />
                <span className={`font-medium ${isLight ? 'text-amber-600' : 'text-[#D4AF37]/90'}`}>
                  {unit.building?.neighborhood || unit.building?.city || 'Manhattan'}
                </span>
                <span className={isLight ? 'text-gray-400' : 'text-[#666]'}>•</span>
                <span className={textMuted}>
                  {getRentalType(unit)}
                </span>
              </div>
            </div>
          ) : showBlur && !user ? (
            <div className="relative">
              <h3 className={`font-philosopher font-semibold blur-sm select-none ${textPrimary}`}>
                {unit.building?.address ? unit.building.address.substring(0, 15) + '...' : 'Premium Location'} #{unit.unit_number || 'XXX'}
              </h3>
              <p className={`text-sm blur-sm select-none font-philosopher ${textMuted}`}>
                {unit.building?.neighborhood || unit.building?.city || 'Manhattan'}, {unit.building?.state || 'NY'}
              </p>
              <div className={`absolute inset-0 flex items-center justify-center ${isLight ? 'bg-white/70' : 'bg-[#0a0a0a]/50'}`}>
                <span className={`text-xs font-philosopher font-medium tracking-wide ${accentColor}`}>Sign up to view</span>
              </div>
            </div>
          ) : (
            <>
              <h3 className={`font-philosopher font-semibold truncate ${textPrimary}`}>
                {unit.building?.address || 'Address Available'}
                {unit.unit_number && ` #${unit.unit_number}`}
              </h3>
              {/* Neighborhood Tag - e.g., "Kips Bay - Luxury Rental" */}
              <div className={`flex items-center gap-1.5 text-sm font-philosopher mt-1 ${textMuted}`}>
                <MapPin className={`w-3.5 h-3.5 ${accentColor}`} />
                <span className={`font-medium ${isLight ? 'text-amber-600' : 'text-[#D4AF37]/90'}`}>
                  {unit.building?.neighborhood || unit.building?.city || 'Manhattan'}
                </span>
                <span className={isLight ? 'text-gray-400' : 'text-[#666]'}>•</span>
                <span className={textMuted}>
                  {getRentalType(unit)}
                </span>
              </div>
            </>
          )}
        </div>
        
        {/* Building Name Badge */}
        {user && unit.building?.name && (
          <div className={`mt-3 pt-3 border-t ${isLight ? 'border-gray-200' : 'border-[#D4AF37]/10'}`}>
            <span className={`text-xs uppercase tracking-wider font-philosopher ${textMuted}`}>Building</span>
            <p className={`text-sm font-philosopher font-medium truncate ${textPrimary}`}>{unit.building.name}</p>
          </div>
        )}
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
