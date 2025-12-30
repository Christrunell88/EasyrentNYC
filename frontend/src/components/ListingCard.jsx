import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, ChevronLeft, ChevronRight, MapPin, BedDouble, Bath, Maximize } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const ListingCard = ({ 
  unit, 
  user, 
  isFavorite = false, 
  onToggleFavorite, 
  onShare,
  showBlur = false 
}) => {
  const navigate = useNavigate();
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  const images = unit.images?.length > 0 ? unit.images : [];
  const hasMultipleImages = images.length > 1;
  
  const bedroomText = unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} bed`;
  const bathText = `${unit.bathrooms} bath`;
  const sqftText = unit.square_feet ? `${unit.square_feet.toLocaleString()} ft²` : null;
  
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
      className="group bg-[#1a1a1a] overflow-hidden transition-all duration-400 cursor-pointer border border-[#D4AF37]/10 hover:border-[#D4AF37]/50 hover:shadow-[0_20px_60px_rgba(0,0,0,0.5),0_0_30px_rgba(212,175,55,0.1)]"
      onClick={handleCardClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Image Section */}
      <div className="relative aspect-[4/3] bg-[#111111] overflow-hidden">
        {images.length > 0 ? (
          <>
            <img
              src={images[currentImageIndex]}
              alt={`${unit.building?.name || 'Apartment'} - Image ${currentImageIndex + 1}`}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            
            {/* Image Navigation Arrows - Only show on hover with multiple images */}
            {hasMultipleImages && isHovered && (
              <>
                <button
                  onClick={handlePrevImage}
                  className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-[#0a0a0a]/80 hover:bg-[#D4AF37] border border-[#D4AF37]/30 flex items-center justify-center transition-all group/btn"
                >
                  <ChevronLeft className="w-5 h-5 text-[#D4AF37] group-hover/btn:text-[#0a0a0a]" />
                </button>
                <button
                  onClick={handleNextImage}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-[#0a0a0a]/80 hover:bg-[#D4AF37] border border-[#D4AF37]/30 flex items-center justify-center transition-all group/btn"
                >
                  <ChevronRight className="w-5 h-5 text-[#D4AF37] group-hover/btn:text-[#0a0a0a]" />
                </button>
              </>
            )}
            
            {/* Image Dots Indicator */}
            {hasMultipleImages && (
              <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
                {images.slice(0, 5).map((_, idx) => (
                  <button
                    key={idx}
                    onClick={(e) => {
                      e.stopPropagation();
                      setCurrentImageIndex(idx);
                    }}
                    className={`w-1.5 h-1.5 transition-all ${
                      idx === currentImageIndex 
                        ? 'bg-[#D4AF37] w-3' 
                        : 'bg-white/40 hover:bg-white/60'
                    }`}
                  />
                ))}
                {images.length > 5 && (
                  <span className="text-[#D4AF37] text-xs font-philosopher ml-1">+{images.length - 5}</span>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-[#111111]">
            <div className="text-center text-[#888888]">
              <BedDouble className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <span className="text-sm font-philosopher">No image</span>
            </div>
          </div>
        )}
        
        {/* Favorite Button */}
        <button
          onClick={handleFavoriteClick}
          className="absolute top-3 right-3 w-9 h-9 bg-[#0a0a0a]/80 hover:bg-[#D4AF37]/20 border border-[#D4AF37]/30 flex items-center justify-center transition-all hover:scale-110"
        >
          <Heart
            className={`w-5 h-5 transition-colors ${
              isFavorite 
                ? 'fill-[#D4AF37] text-[#D4AF37]' 
                : 'text-[#D4AF37]/70 hover:text-[#D4AF37]'
            }`}
          />
        </button>
        
        {/* No Fee Badge */}
        <Badge className="absolute top-3 left-3 bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-philosopher font-bold px-2.5 py-1 text-xs rounded-none tracking-wide">
          NO FEE
        </Badge>
        
        {/* Featured Badge */}
        {unit.is_featured && (
          <Badge className="absolute top-12 left-3 bg-[#0a0a0a]/80 border border-[#D4AF37]/50 text-[#D4AF37] font-philosopher font-bold px-2.5 py-1 text-xs rounded-none tracking-wide">
            FEATURED
          </Badge>
        )}
      </div>
      
      {/* Content Section */}
      <div className="p-4">
        {/* Price Row */}
        <div className="flex items-baseline justify-between mb-2">
          <div className="flex items-baseline">
            <span className="text-2xl font-philosopher font-bold text-[#D4AF37]">
              ${unit.rent?.toLocaleString()}
            </span>
            <span className="text-[#888888] text-sm ml-1 font-philosopher">/mo</span>
          </div>
          {sqftText && (
            <span className="text-[#888888] text-sm font-philosopher">
              ${Math.round(unit.rent / unit.square_feet)}/ft²
            </span>
          )}
        </div>
        
        {/* Details Row */}
        <div className="flex items-center gap-1 text-[#F5F5F5] text-sm mb-3 font-philosopher">
          <span className="font-medium">{bedroomText}</span>
          <span className="text-[#D4AF37]/50">|</span>
          <span className="font-medium">{bathText}</span>
          {sqftText && (
            <>
              <span className="text-[#D4AF37]/50">|</span>
              <span className="font-medium">{sqftText}</span>
            </>
          )}
        </div>
        
        {/* Address */}
        <div className="mb-2">
          {showBlur && !user ? (
            <div className="relative">
              <h3 className="font-philosopher font-semibold text-white blur-sm select-none">
                123 Example Street #4B
              </h3>
              <p className="text-sm text-[#888888] blur-sm select-none font-philosopher">
                Manhattan, New York
              </p>
              <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0a]/50">
                <span className="text-xs text-[#D4AF37] font-philosopher font-medium tracking-wide">Sign up to view</span>
              </div>
            </div>
          ) : (
            <>
              <h3 className="font-philosopher font-semibold text-white truncate">
                {unit.building?.address || 'Address Available'}
                {unit.unit_number && ` #${unit.unit_number}`}
              </h3>
              <div className="flex items-center gap-1.5 text-sm text-[#888888] font-philosopher">
                <MapPin className="w-3.5 h-3.5 text-[#D4AF37]" />
                <span>{unit.building?.neighborhood || unit.building?.city || 'New York'}</span>
              </div>
            </>
          )}
        </div>
        
        {/* Building Name Badge */}
        {user && unit.building?.name && (
          <div className="mt-3 pt-3 border-t border-[#D4AF37]/10">
            <span className="text-xs text-[#888888] uppercase tracking-wider font-philosopher">Building</span>
            <p className="text-sm font-philosopher font-medium text-[#F5F5F5] truncate">{unit.building.name}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ListingCard;
