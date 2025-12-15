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
      className="group bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer border border-gray-100"
      onClick={handleCardClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Image Section */}
      <div className="relative aspect-[4/3] bg-gray-100 overflow-hidden">
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
                  className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-lg transition-all"
                >
                  <ChevronLeft className="w-5 h-5 text-gray-700" />
                </button>
                <button
                  onClick={handleNextImage}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-lg transition-all"
                >
                  <ChevronRight className="w-5 h-5 text-gray-700" />
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
                    className={`w-1.5 h-1.5 rounded-full transition-all ${
                      idx === currentImageIndex 
                        ? 'bg-white w-3' 
                        : 'bg-white/60 hover:bg-white/80'
                    }`}
                  />
                ))}
                {images.length > 5 && (
                  <span className="text-white text-xs font-medium ml-1">+{images.length - 5}</span>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
            <div className="text-center text-gray-400">
              <BedDouble className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <span className="text-sm">No image</span>
            </div>
          </div>
        )}
        
        {/* Favorite Button */}
        <button
          onClick={handleFavoriteClick}
          className="absolute top-3 right-3 w-9 h-9 bg-white/90 hover:bg-white rounded-full flex items-center justify-center shadow-md transition-all hover:scale-110"
        >
          <Heart
            className={`w-5 h-5 transition-colors ${
              isFavorite 
                ? 'fill-red-500 text-red-500' 
                : 'text-gray-600 hover:text-red-500'
            }`}
          />
        </button>
        
        {/* No Fee Badge */}
        <Badge className="absolute top-3 left-3 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold px-2.5 py-1 text-xs">
          NO FEE
        </Badge>
        
        {/* Featured Badge */}
        {unit.is_featured && (
          <Badge className="absolute top-12 left-3 bg-amber-500 hover:bg-amber-600 text-white font-semibold px-2.5 py-1 text-xs">
            FEATURED
          </Badge>
        )}
      </div>
      
      {/* Content Section */}
      <div className="p-4">
        {/* Price Row */}
        <div className="flex items-baseline justify-between mb-2">
          <div className="flex items-baseline">
            <span className="text-2xl font-bold text-gray-900">
              ${unit.rent?.toLocaleString()}
            </span>
            <span className="text-gray-500 text-sm ml-1">/mo</span>
          </div>
          {sqftText && (
            <span className="text-gray-500 text-sm">
              ${Math.round(unit.rent / unit.square_feet)}/ft²
            </span>
          )}
        </div>
        
        {/* Details Row */}
        <div className="flex items-center gap-1 text-gray-600 text-sm mb-3">
          <span className="font-medium">{bedroomText}</span>
          <span className="text-gray-300">|</span>
          <span className="font-medium">{bathText}</span>
          {sqftText && (
            <>
              <span className="text-gray-300">|</span>
              <span className="font-medium">{sqftText}</span>
            </>
          )}
        </div>
        
        {/* Address */}
        <div className="mb-2">
          {showBlur && !user ? (
            <div className="relative">
              <h3 className="font-semibold text-gray-900 blur-sm select-none">
                123 Example Street #4B
              </h3>
              <p className="text-sm text-gray-500 blur-sm select-none">
                Manhattan, New York
              </p>
              <div className="absolute inset-0 flex items-center justify-center bg-gray-50/50 rounded">
                <span className="text-xs text-amber-600 font-medium">Sign up to view</span>
              </div>
            </div>
          ) : (
            <>
              <h3 className="font-semibold text-gray-900 truncate">
                {unit.building?.address || 'Address Available'}
                {unit.unit_number && ` #${unit.unit_number}`}
              </h3>
              <div className="flex items-center gap-1.5 text-sm text-gray-500">
                <MapPin className="w-3.5 h-3.5" />
                <span>{unit.building?.neighborhood || unit.building?.city || 'New York'}</span>
              </div>
            </>
          )}
        </div>
        
        {/* Building Name Badge */}
        {user && unit.building?.name && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <span className="text-xs text-gray-400 uppercase tracking-wide">Building</span>
            <p className="text-sm font-medium text-gray-700 truncate">{unit.building.name}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ListingCard;
