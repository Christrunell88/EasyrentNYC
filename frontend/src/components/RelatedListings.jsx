import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BedDouble, Bath, MapPin, ArrowRight } from 'lucide-react';

const RelatedListings = ({ currentUnit, limit = 4 }) => {
  const navigate = useNavigate();
  const [relatedUnits, setRelatedUnits] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRelatedUnits = async () => {
      if (!currentUnit) return;
      
      try {
        // Fetch units with similar characteristics
        const params = new URLSearchParams();
        
        // Match by neighborhood/city first
        if (currentUnit.building?.neighborhood) {
          params.append('neighborhood', currentUnit.building.neighborhood);
        } else if (currentUnit.building?.city) {
          params.append('city', currentUnit.building.city);
        }
        
        // Get more than we need to filter out current unit
        params.append('limit', String(limit + 5));
        
        const response = await axios.get(`${API}/units?${params.toString()}`, { withCredentials: true });
        
        // Filter out current unit and units from same building
        let filtered = response.data.filter(
          unit => unit.id !== currentUnit.id && unit.building?.id !== currentUnit.building?.id
        );
        
        // If not enough results, try similar price range
        if (filtered.length < limit) {
          const priceParams = new URLSearchParams();
          const minPrice = Math.floor(currentUnit.rent * 0.8);
          const maxPrice = Math.ceil(currentUnit.rent * 1.2);
          priceParams.append('min_rent', String(minPrice));
          priceParams.append('max_rent', String(maxPrice));
          priceParams.append('limit', String(limit + 5));
          
          const priceResponse = await axios.get(`${API}/units?${priceParams.toString()}`, { withCredentials: true });
          const priceFiltered = priceResponse.data.filter(
            unit => unit.id !== currentUnit.id && !filtered.find(f => f.id === unit.id)
          );
          
          filtered = [...filtered, ...priceFiltered];
        }
        
        // Sort by relevance (same bedrooms first, then similar price)
        filtered.sort((a, b) => {
          const aBedroomMatch = a.bedrooms === currentUnit.bedrooms ? 1 : 0;
          const bBedroomMatch = b.bedrooms === currentUnit.bedrooms ? 1 : 0;
          if (aBedroomMatch !== bBedroomMatch) return bBedroomMatch - aBedroomMatch;
          
          const aPriceDiff = Math.abs(a.rent - currentUnit.rent);
          const bPriceDiff = Math.abs(b.rent - currentUnit.rent);
          return aPriceDiff - bPriceDiff;
        });
        
        setRelatedUnits(filtered.slice(0, limit));
      } catch (error) {
        console.error('Error fetching related units:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRelatedUnits();
  }, [currentUnit, limit]);

  if (loading || relatedUnits.length === 0) {
    return null;
  }

  const handleUnitClick = (unitId) => {
    navigate(`/unit/${unitId}`);
    window.scrollTo(0, 0);
  };

  return (
    <div className="mt-12 pt-8 border-t border-[#D4AF37]/20">
      <h2 className="text-2xl font-bold text-white mb-6 font-philosopher flex items-center gap-2">
        <MapPin className="w-6 h-6 text-[#D4AF37]" />
        Similar Apartments Nearby
      </h2>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {relatedUnits.map((unit) => (
          <Card
            key={unit.id}
            className="bg-[#1a1a1a] border-[#D4AF37]/20 hover:border-[#D4AF37]/50 transition-all cursor-pointer group overflow-hidden"
            onClick={() => handleUnitClick(unit.id)}
          >
            {/* Image */}
            <div className="relative aspect-[4/3] bg-[#111] overflow-hidden">
              {unit.images?.[0] ? (
                <img
                  src={unit.images[0]}
                  alt={`${unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} bedroom`} apartment at ${unit.building?.name || 'NYC'}`}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-[#666]">
                  <BedDouble className="w-8 h-8" />
                </div>
              )}
              <Badge className="absolute top-2 left-2 bg-[#D4AF37] text-[#0a0a0a] text-xs font-bold">
                NO FEE
              </Badge>
            </div>
            
            <CardContent className="p-4">
              {/* Price */}
              <div className="flex items-baseline justify-between mb-2">
                <span className="text-lg font-bold text-[#D4AF37]">
                  ${unit.rent?.toLocaleString()}
                </span>
                <span className="text-xs text-[#666]">/mo</span>
              </div>
              
              {/* Details */}
              <div className="flex items-center gap-2 text-sm text-[#888] mb-2">
                <span>{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} bed`}</span>
                <span className="text-[#D4AF37]/50">|</span>
                <span>{unit.bathrooms} bath</span>
              </div>
              
              {/* Location */}
              <div className="flex items-center gap-1 text-xs text-[#666] truncate">
                <MapPin className="w-3 h-3 text-[#D4AF37]" />
                <span>{unit.building?.neighborhood || unit.building?.city || 'NYC'}</span>
              </div>
              
              {/* View CTA */}
              <div className="mt-3 pt-3 border-t border-[#333] flex items-center justify-between">
                <span className="text-xs text-[#888]">{unit.building?.name}</span>
                <ArrowRight className="w-4 h-4 text-[#D4AF37] opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Internal Link to Browse More */}
      <div className="mt-6 text-center">
        <button
          onClick={() => navigate(`/location/${currentUnit.building?.city?.toLowerCase().replace(/\s+/g, '-') || 'manhattan'}`)}
          className="text-[#D4AF37] hover:text-[#E5C158] text-sm font-medium inline-flex items-center gap-1"
        >
          Browse more apartments in {currentUnit.building?.neighborhood || currentUnit.building?.city || 'this area'}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default RelatedListings;
