import React from 'react';
import { MapPin, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';

const GoogleMapEmbed = ({ address, city, state, zipCode, buildingName, lat, lng }) => {
  // Create a full address string for the embed
  const fullAddress = [address, city, state, zipCode].filter(Boolean).join(', ');
  
  // Create Google Maps embed URL
  // Using the embed API which doesn't require an API key for basic embedding
  const embedUrl = `https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=${encodeURIComponent(fullAddress)}`;
  
  // Alternative: Use OpenStreetMap embed (no API key needed)
  const osmUrl = lat && lng 
    ? `https://www.openstreetmap.org/export/embed.html?bbox=${lng-0.01}%2C${lat-0.01}%2C${lng+0.01}%2C${lat+0.01}&layer=mapnik&marker=${lat}%2C${lng}`
    : `https://www.openstreetmap.org/export/embed.html?bbox=-74.05%2C40.68%2C-73.85%2C40.8&layer=mapnik`;
  
  // Google Maps directions link
  const directionsUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(fullAddress)}`;
  
  // Google Maps view link
  const viewUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(fullAddress)}`;

  return (
    <div className="rounded-lg overflow-hidden border border-[#D4AF37]/20 bg-[#1a1a1a]">
      {/* Map Header */}
      <div className="p-4 border-b border-[#333] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPin className="w-5 h-5 text-[#D4AF37]" />
          <div>
            <h3 className="text-white font-semibold text-sm">{buildingName || 'Location'}</h3>
            <p className="text-[#888] text-xs">{fullAddress}</p>
          </div>
        </div>
        <a
          href={viewUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#D4AF37] hover:text-[#E5C158] text-sm flex items-center gap-1"
        >
          <ExternalLink className="w-4 h-4" />
          Open in Maps
        </a>
      </div>
      
      {/* Map Embed - Using static image fallback for better SEO */}
      <div className="relative aspect-video bg-[#111]">
        {/* Static map image for SEO (loads faster, no JS required) */}
        <img
          src={`https://maps.googleapis.com/maps/api/staticmap?center=${encodeURIComponent(fullAddress)}&zoom=15&size=600x300&maptype=roadmap&markers=color:gold%7C${encodeURIComponent(fullAddress)}&key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&style=feature:all|element:geometry|color:0x1a1a1a&style=feature:all|element:labels.text.fill|color:0xffffff&style=feature:water|element:geometry|color:0x0a0a0a`}
          alt={`Map showing location of ${buildingName || 'apartment'} at ${fullAddress}`}
          className="w-full h-full object-cover"
          loading="lazy"
          onError={(e) => {
            // Fallback to OpenStreetMap iframe if Google Static Maps fails
            e.target.style.display = 'none';
            e.target.nextSibling.style.display = 'block';
          }}
        />
        {/* Fallback iframe (hidden by default) */}
        <iframe
          src={osmUrl}
          title={`Map of ${buildingName || 'apartment location'}`}
          className="w-full h-full border-0 hidden"
          loading="lazy"
          allowFullScreen
        />
        
        {/* Overlay with View Full Map button */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#0a0a0a] to-transparent p-4">
          <div className="flex gap-2">
            <Button
              onClick={() => window.open(viewUrl, '_blank')}
              size="sm"
              className="bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-semibold flex-1"
            >
              <MapPin className="w-4 h-4 mr-1" />
              View on Google Maps
            </Button>
            <Button
              onClick={() => window.open(directionsUrl, '_blank')}
              size="sm"
              variant="outline"
              className="border-[#D4AF37]/50 text-[#D4AF37] hover:bg-[#D4AF37]/10"
            >
              Get Directions
            </Button>
          </div>
        </div>
      </div>
      
      {/* Nearby Info - Good for local SEO */}
      <div className="p-4 border-t border-[#333]">
        <p className="text-xs text-[#666]">
          Located in {city || 'NYC'}, {state || 'NY'}. View this apartment on Google Maps to see nearby transit, restaurants, and amenities.
        </p>
      </div>
    </div>
  );
};

export default GoogleMapEmbed;
