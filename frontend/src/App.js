import React, { useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { Toaster, toast } from 'sonner';
import Landing from './pages/Landing';
import Auth from './pages/Auth';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import UnitDetails from './pages/UnitDetails';
import Favorites from './pages/Favorites';
import AdminPanel from './pages/AdminPanel';
import LocationPage from './pages/LocationPage';
import Blog from './pages/Blog';
import BlogPost from './pages/BlogPost';
import FAQ from './pages/FAQ';
import GuideToNoFeeApartments from './pages/blog/GuideToNoFeeApartments';
import BestNeighborhoods from './pages/blog/BestNeighborhoods';
import ApartmentChecklist from './pages/blog/ApartmentChecklist';
import FeeFreeFinds from './pages/FeeFreeFinds';
import Neighborhoods from './pages/Neighborhoods';
import NeighborhoodsIndex from './pages/NeighborhoodsIndex';
import NeighborhoodPage from './pages/NeighborhoodPage';
import HowItWorks from './pages/HowItWorks';
import BrooklynPage from './pages/BrooklynPage';
import ManhattanPage from './pages/ManhattanPage';
import QueensPage from './pages/QueensPage';
import AISearchAgent from './components/AISearchAgent';
import { initGA, trackPageView } from './utils/analytics';
import useAuthStore from './store/authStore';

// Use current origin for API calls to ensure proper routing on custom domains
// This ensures /api calls go through the same domain and avoid CORS issues
// Centralized in config/api.js
import { API, getApiUrl } from './config/api';

export { API };

// Export useAuth hook for backward compatibility
export const useAuth = () => {
  const user = useAuthStore((state) => state.user);
  const loading = useAuthStore((state) => state.loading);
  const checkAuth = useAuthStore((state) => state.checkAuth);
  const logout = useAuthStore((state) => state.logout);
  
  return { user, loading, checkAuth, logout };
};

// Protected route - simplified with Zustand
const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const user = useAuthStore((state) => state.user);
  const loading = useAuthStore((state) => state.loading);
  const checkAuth = useAuthStore((state) => state.checkAuth);
  
  React.useEffect(() => {
    // Check auth on mount if user is not set
    if (!user && !loading) {
      checkAuth();
    }
  }, [user, loading, checkAuth]);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/auth" replace />;
  }
  
  if (requireAdmin && !user.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Session handler for OAuth
const SessionHandler = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const processSession = useAuthStore((state) => state.processSession);
  
  useEffect(() => {
    const handleSession = async () => {
      const hash = location.hash;
      const params = new URLSearchParams(hash.substring(1));
      const sessionId = params.get('session_id');
      
      if (sessionId) {
        const result = await processSession(sessionId);
        
        if (result.success) {
          window.location.href = '/dashboard';
        } else {
          toast.error(result.error || 'Authentication failed');
          navigate('/auth');
        }
      }
    };
    
    handleSession();
  }, [location, navigate, processSession]);
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-xl text-gray-600">Authenticating...</div>
    </div>
  );
};

// Page view tracker component
const PageViewTracker = () => {
  const location = useLocation();
  
  useEffect(() => {
    // Track page view on route change
    trackPageView(location.pathname + location.search, document.title);
  }, [location]);
  
  return null;
};

// Initialize auth on app load
const AuthInitializer = () => {
  const checkAuth = useAuthStore((state) => state.checkAuth);
  
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
  
  return null;
};

function App() {
  // Initialize Google Analytics on app load
  useEffect(() => {
    initGA();
  }, []);
  
  return (
    <HelmetProvider>
      <div className="App">
        <Toaster position="top-center" richColors />
        <BrowserRouter>
          <PageViewTracker />
          <AuthInitializer />
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/login" element={<Navigate to="/auth" replace />} />
            <Route path="/signup" element={<Navigate to="/auth" replace />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/session" element={<SessionHandler />} />
            <Route path="/location/:location" element={<LocationPage />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/blog/guide-to-no-fee-apartments" element={<GuideToNoFeeApartments />} />
            <Route path="/blog/best-neighborhoods" element={<BestNeighborhoods />} />
            <Route path="/blog/apartment-checklist" element={<ApartmentChecklist />} />
            <Route path="/blog/:slug" element={<BlogPost />} />
            <Route path="/faq" element={<FAQ />} />
            <Route path="/fee-free-finds" element={<FeeFreeFinds />} />
            <Route path="/neighborhoods" element={<Neighborhoods />} />
            <Route path="/apartments" element={<NeighborhoodsIndex />} />
            <Route path="/apartments/:slug" element={<NeighborhoodPage />} />
            <Route path="/brooklyn" element={<BrooklynPage />} />
            <Route path="/manhattan" element={<ManhattanPage />} />
            <Route path="/queens" element={<QueensPage />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/unit/:id"
              element={
                <ProtectedRoute>
                  <UnitDetails />
                </ProtectedRoute>
              }
            />
            <Route
              path="/favorites"
              element={
                <ProtectedRoute>
                  <Favorites />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute requireAdmin>
                  <AdminPanel />
                </ProtectedRoute>
              }
            />
          </Routes>
          <AISearchAgent />
        </BrowserRouter>
      </div>
    </HelmetProvider>
  );
}

export default App;
