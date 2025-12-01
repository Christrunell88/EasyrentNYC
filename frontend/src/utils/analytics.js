/**
 * Google Analytics 4 Integration
 * Tracks page views, events, and user interactions
 */

import ReactGA from 'react-ga4';

const GA_MEASUREMENT_ID = process.env.REACT_APP_GA_MEASUREMENT_ID;

// Initialize GA4
export const initGA = () => {
  if (!GA_MEASUREMENT_ID) {
    console.warn('Google Analytics Measurement ID not found');
    return false;
  }

  try {
    ReactGA.initialize(GA_MEASUREMENT_ID, {
      gaOptions: {
        send_page_view: false, // We'll manually track page views
      },
    });
    console.log('✅ Google Analytics initialized:', GA_MEASUREMENT_ID);
    return true;
  } catch (error) {
    console.error('Failed to initialize Google Analytics:', error);
    return false;
  }
};

// Track page view
export const trackPageView = (path, title) => {
  if (!GA_MEASUREMENT_ID) return;
  
  try {
    ReactGA.send({
      hitType: 'pageview',
      page: path,
      title: title || document.title,
    });
    console.log('📊 Page view tracked:', path);
  } catch (error) {
    console.error('Failed to track page view:', error);
  }
};

// Track custom event
export const trackEvent = (category, action, label, value) => {
  if (!GA_MEASUREMENT_ID) return;
  
  try {
    ReactGA.event({
      category,
      action,
      label,
      value,
    });
    console.log('📊 Event tracked:', { category, action, label, value });
  } catch (error) {
    console.error('Failed to track event:', error);
  }
};

// Predefined event tracking functions

export const trackApartmentView = (unitId, buildingName, rent) => {
  trackEvent('Apartment', 'View Details', buildingName, rent);
  
  // Also track as GA4 recommended event
  ReactGA.event('view_item', {
    items: [{
      item_id: unitId,
      item_name: buildingName,
      price: rent,
    }],
  });
};

export const trackApartmentFavorite = (unitId, buildingName) => {
  trackEvent('Engagement', 'Add to Favorites', buildingName);
  
  // GA4 recommended event
  ReactGA.event('add_to_wishlist', {
    items: [{
      item_id: unitId,
      item_name: buildingName,
    }],
  });
};

export const trackApartmentShare = (unitId, buildingName, method) => {
  trackEvent('Engagement', 'Share Apartment', `${buildingName} via ${method}`);
  
  // GA4 recommended event
  ReactGA.event('share', {
    method: method,
    content_type: 'apartment',
    item_id: unitId,
  });
};

export const trackSearch = (searchTerm, filters) => {
  trackEvent('Search', 'Apartment Search', searchTerm);
  
  // GA4 recommended event
  ReactGA.event('search', {
    search_term: searchTerm,
    ...filters,
  });
};

export const trackSignup = (method) => {
  trackEvent('User', 'Sign Up', method); // 'email' or 'google'
  
  // GA4 recommended event
  ReactGA.event('sign_up', {
    method: method,
  });
};

export const trackLogin = (method) => {
  trackEvent('User', 'Login', method);
  
  // GA4 recommended event
  ReactGA.event('login', {
    method: method,
  });
};

export const trackContactForm = (apartmentId) => {
  trackEvent('Lead', 'Contact Form Submit', apartmentId);
  
  // GA4 recommended event
  ReactGA.event('generate_lead', {
    value: 1,
    item_id: apartmentId,
  });
};

export const trackMapView = () => {
  trackEvent('Engagement', 'View Map', 'Apartments Map');
};

export const trackFilterUsage = (filterType, filterValue) => {
  trackEvent('Filter', 'Apply Filter', `${filterType}: ${filterValue}`);
};

export const trackAdminAction = (action, details) => {
  trackEvent('Admin', action, details);
};

export default {
  initGA,
  trackPageView,
  trackEvent,
  trackApartmentView,
  trackApartmentFavorite,
  trackApartmentShare,
  trackSearch,
  trackSignup,
  trackLogin,
  trackContactForm,
  trackMapView,
  trackFilterUsage,
  trackAdminAction,
};
