import axios from 'axios';

// Function to get cookie value by name
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

// Add request interceptor to include session token for localhost development
axios.interceptors.request.use(
  (config) => {
    // For localhost development, add session token from cookie as header
    if (window.location.hostname === 'localhost') {
      const sessionToken = getCookie('session_token');
      if (sessionToken) {
        config.headers['X-Session-Token'] = sessionToken;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default axios;