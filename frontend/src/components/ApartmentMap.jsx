import React, { useState, useEffect, useCallback } from 'react';
import { APIProvider, Map, AdvancedMarker, InfoWindow, Pin } from '@vis.gl/react-google-maps';
import axios from 'axios';
import { API } from '../App';
import './ApartmentMap.css';

const ApartmentMap = ({ apartments = [], onMapBoundsChange, center, zoom = 12 }) => {
  const [selectedApartment, setSelectedApartment] = useState(null);
  const [mapCenter, setMapCenter] = useState(center || { lat: 40.7128, lng: -74.0060 });
  const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

  useEffect(() => {
    if (center) {
      setMapCenter(center);
    }
  }, [center]);

  const handleMarkerClick = useCallback((apartment) => {
    setSelectedApartment(apartment);
  }, []);

  const handleBoundsChanged = useCallback((map) => {
    if (!map || !onMapBoundsChange) return;

    const bounds = map.getBounds();
    if (bounds) {
      const ne = bounds.getNorthEast();
      const sw = bounds.getSouthWest();
      
      onMapBoundsChange({
        minLat: sw.lat(),
        maxLat: ne.lat(),
        minLng: sw.lng(),
        maxLng: ne.lng()
      });
    }
  }, [onMapBoundsChange]);

  if (!apiKey) {
    return (
      <div className="map-error">
        <p>Google Maps API key not configured. Please add REACT_APP_GOOGLE_MAPS_API_KEY to your environment.</p>
      </div>
    );
  }

  return (
    <div className="apartment-map-container">
      <APIProvider apiKey={apiKey}>
        <Map
          defaultZoom={zoom}
          defaultCenter={mapCenter}
          mapId="apartment-map"
          onBoundsChanged={handleBoundsChanged}
          gestureHandling="greedy"
          disableDefaultUI={false}
          style={{ width: '100%', height: '100%' }}
        >
          {apartments.map((apartment) => (
            <AdvancedMarker
              key={apartment.id}
              position={{
                lat: parseFloat(apartment.latitude || apartment.lat || 40.7128),
                lng: parseFloat(apartment.longitude || apartment.lng || -74.0060)
              }}
              onClick={() => handleMarkerClick(apartment)}
            >
              <Pin
                background={selectedApartment?.id === apartment.id ? '#f59e0b' : '#1e40af'}
                borderColor={selectedApartment?.id === apartment.id ? '#d97706' : '#1e3a8a'}
                glyphColor="white"
              />
            </AdvancedMarker>
          ))}

          {selectedApartment && (
            <InfoWindow
              position={{
                lat: parseFloat(selectedApartment.latitude || selectedApartment.lat || 40.7128),
                lng: parseFloat(selectedApartment.longitude || selectedApartment.lng || -74.0060)
              }}
              onCloseClick={() => setSelectedApartment(null)}
            >
              <div className="info-window-content">
                <h3 className="info-title">
                  {selectedApartment.building?.name || selectedApartment.address || 'Apartment'}
                </h3>
                <p className="info-address">{selectedApartment.address}</p>
                <div className="info-details">
                  <p><strong>Rent:</strong> ${selectedApartment.rent}/month</p>
                  <p><strong>Bedrooms:</strong> {selectedApartment.bedrooms}</p>
                  <p><strong>Bathrooms:</strong> {selectedApartment.bathrooms}</p>
                  {selectedApartment.sqft && (
                    <p><strong>Size:</strong> {selectedApartment.sqft} sqft</p>
                  )}
                </div>
                <button
                  className="view-details-btn"
                  onClick={() => window.location.href = `/unit/${selectedApartment.id}`}
                >
                  View Details
                </button>
              </div>
            </InfoWindow>
          )}
        </Map>
      </APIProvider>
    </div>
  );
};

export default ApartmentMap;
