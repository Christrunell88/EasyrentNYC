/**
 * Centralized API Configuration
 * 
 * This file provides the single source of truth for API URL configuration
 * across the entire frontend application.
 */

/**
 * Get the API base URL
 * Uses environment variable if available, falls back to window.location.origin
 * @returns {string} The API base URL
 */
export const getApiUrl = () => {
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  if (envUrl) {
    return envUrl;
  }
  // Fallback for local development or when env var is not set
  return window.location.origin;
};

/**
 * The API base URL - use this constant throughout the application
 */
export const API_URL = getApiUrl();

/**
 * Convenience alias for API_URL
 */
export const API = API_URL;

/**
 * Build a full API endpoint URL
 * @param {string} path - The API path (e.g., '/api/units')
 * @returns {string} The full API URL
 */
export const buildApiUrl = (path) => {
  const base = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${cleanPath}`;
};

export default API_URL;
