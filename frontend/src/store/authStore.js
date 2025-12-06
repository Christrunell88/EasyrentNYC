import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      user: null,
      loading: true,
      error: null,

      // Actions
      setUser: (user) => set({ user, error: null }),
      
      setLoading: (loading) => set({ loading }),
      
      setError: (error) => set({ error }),

      // Check authentication status
      checkAuth: async () => {
        try {
          set({ loading: true, error: null });
          const response = await axios.get(`${API}/auth/me`, { 
            withCredentials: true 
          });
          set({ user: response.data, loading: false, error: null });
          return response.data;
        } catch (error) {
          set({ user: null, loading: false, error: null });
          return null;
        }
      },

      // Login with email/password
      login: async (email, password) => {
        try {
          set({ loading: true, error: null });
          const response = await axios.post(
            `${API}/auth/login`,
            { email, password },
            { withCredentials: true }
          );
          
          // For localhost development, manually set the session token cookie
          // since cross-origin cookies don't work reliably
          if (response.data.session_token && window.location.hostname === 'localhost') {
            document.cookie = `session_token=${response.data.session_token}; path=/; max-age=${7 * 24 * 60 * 60}`;
          }
          
          set({ 
            user: response.data.user, 
            loading: false, 
            error: null 
          });
          return { success: true, user: response.data.user };
        } catch (error) {
          const errorMsg = error.response?.data?.detail || 'Login failed';
          set({ loading: false, error: errorMsg });
          return { success: false, error: errorMsg };
        }
      },

      // Signup with email/password
      signup: async (email, password, name) => {
        try {
          set({ loading: true, error: null });
          const response = await axios.post(
            `${API}/auth/signup`,
            { email, password, name },
            { withCredentials: true }
          );
          set({ 
            user: response.data.user, 
            loading: false, 
            error: null 
          });
          return { success: true, user: response.data.user };
        } catch (error) {
          const errorMsg = error.response?.data?.detail || 'Signup failed';
          set({ loading: false, error: errorMsg });
          return { success: false, error: errorMsg };
        }
      },

      // Process OAuth session
      processSession: async (sessionId) => {
        try {
          set({ loading: true, error: null });
          const response = await axios.post(
            `${API}/auth/session`,
            {},
            {
              headers: { 'X-Session-ID': sessionId },
              withCredentials: true
            }
          );
          set({ 
            user: response.data.user, 
            loading: false, 
            error: null 
          });
          return { success: true, user: response.data.user };
        } catch (error) {
          const errorMsg = error.response?.data?.detail || 'Authentication failed';
          set({ loading: false, error: errorMsg });
          return { success: false, error: errorMsg };
        }
      },

      // Logout
      logout: async () => {
        try {
          await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({ user: null, loading: false, error: null });
          window.location.href = '/';
        }
      },

      // Clear auth state
      clearAuth: () => set({ user: null, loading: false, error: null }),

      // Check if user is authenticated
      isAuthenticated: () => {
        const { user } = get();
        return !!user;
      },

      // Check if user is admin
      isAdmin: () => {
        const { user } = get();
        return user?.is_admin || false;
      },
    }),
    {
      name: 'auth-storage', // unique name for localStorage key
      partialize: (state) => ({ 
        user: state.user, // only persist user, not loading/error states
      }),
    }
  )
);

export default useAuthStore;
