import axios from 'axios';

// Function to get cookie value by name
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

// Function to get session token from localStorage or cookie
function getSessionToken() {
  // First try localStorage (more reliable for cross-domain)
  const localStorageToken = localStorage.getItem('session_token');
  if (localStorageToken) {
    return localStorageToken;
  }
  // Fallback to cookie
  return getCookie('session_token');
}

// Add request interceptor to include session token for all requests
axios.interceptors.request.use(
  (config) => {
    // Add session token from localStorage or cookie as Authorization header
    const sessionToken = getSessionToken();
    if (sessionToken) {
      config.headers['Authorization'] = `Bearer ${sessionToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default axios;