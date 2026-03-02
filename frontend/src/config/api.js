/**
 * Centralized API Configuration
 * 
 * This file provides the single source of truth for API URL configuration
 * across the entire frontend application.
 */

/**
 * Get the API base URL with /api suffix
 * Uses current origin for custom domains to avoid CORS issues,
 * falls back to environment variable for local development
 * @returns {string} The API base URL with /api suffix
 */
export const getApiUrl = () => {
  // For production/custom domains, use current origin to avoid CORS
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return `${window.location.origin}/api`;
  }
  // For local development, use environment variable
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
  return `${BACKEND_URL}/api`;
};

/**
 * The API base URL - use this constant throughout the application
 * Already includes /api suffix
 */
export const API = getApiUrl();

/**
 * Get the raw backend URL without /api suffix
 * Useful for special cases like OAuth redirects
 * @returns {string} The raw backend URL
 */
export const getRawBackendUrl = () => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    return window.location.origin;
  }
  return process.env.REACT_APP_BACKEND_URL || window.location.origin;
};

/**
 * Build a full API endpoint URL
 * @param {string} path - The API path (e.g., '/units' - without /api prefix)
 * @returns {string} The full API URL
 */
export const buildApiUrl = (path) => {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${API}${cleanPath}`;
};

export default API;

