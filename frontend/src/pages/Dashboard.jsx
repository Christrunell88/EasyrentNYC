import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../utils/axiosConfig';
import { toast } from 'sonner';
import { API } from '../App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Building2, BedDouble, Bath, DollarSign, Heart, LogOut, User, Settings, Eye, Share2, Map } from 'lucide-react';
import Logo from '@/components/Logo';
import ShareDialog from '@/components/ShareDialog';
import SEO from '@/components/SEO';
import ApartmentMap from '@/components/ApartmentMap';
import ListingCard from '@/components/ListingCard';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { trackApartmentView, trackApartmentFavorite, trackMapView, trackFilterUsage } from '../utils/analytics';
import useAuthStore from '../store/authStore';

const Dashboard = () => {
  const navigate = useNavigate();
  // Use Zustand store for user state
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState(new Set());
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'map'
  
  // Track map view when it changes
  useEffect(() => {
    if (viewMode === 'map') {
      trackMapView();
    }
  }, [viewMode]);
  
  // Filters
  const [bedrooms, setBedrooms] = useState('');
  const [minRent, setMinRent] = useState('');
  const [maxRent, setMaxRent] = useState('');
  const [bathrooms, setBathrooms] = useState('');
  const [state, setState] = useState('');

  useEffect(() => {
    fetchUnits();
    fetchFavorites();
  }, [bedrooms, minRent, maxRent, bathrooms, state]);

  const fetchUnits = async () => {
    try {
      const params = new URLSearchParams();
      if (bedrooms) params.append('bedrooms', bedrooms);
      if (minRent) params.append('min_rent', minRent);
      if (maxRent) params.append('max_rent', maxRent);
      if (bathrooms) params.append('bathrooms', bathrooms);
      if (state) params.append('state', state);
      
      const response = await axios.get(`${API}/units?${params.toString()}`, { withCredentials: true });
      
      // Distribute apartments from different buildings evenly to show variety
      const diversifiedUnits = diversifyListings(response.data);
      setUnits(diversifiedUnits);
    } catch (error) {
      console.error('Error fetching units:', error);
      toast.error('Failed to load apartments');
    } finally {
      setLoading(false);
    }
  };

  const hasRealImages = (unit) => {
    // Check if unit has real images (not placeholder/unsplash)
    if (!unit.images || unit.images.length === 0) return false;
    const firstImage = unit.images[0];
    // Filter out Unsplash placeholders
    return !firstImage.includes('unsplash.com') && !firstImage.includes('photo-1556912173');
  };

  const diversifyListings = (units) => {
    // Separate featured units first
    const featuredUnits = units.filter(unit => unit.featured);
    const nonFeaturedUnits = units.filter(unit => !unit.featured);
    
    // Separate units with real images and without (only for non-featured)
    const unitsWithImages = nonFeaturedUnits.filter(hasRealImages);
    const unitsWithoutImages = nonFeaturedUnits.filter(unit => !hasRealImages(unit));

    // Group units with images by building
    const buildingGroups = {};
    unitsWithImages.forEach(unit => {
      const buildingId = unit.building?.id || 'unknown';
      if (!buildingGroups[buildingId]) {
        buildingGroups[buildingId] = [];
      }
      buildingGroups[buildingId].push(unit);
    });

    // Sort units within each building by price
    Object.keys(buildingGroups).forEach(buildingId => {
      buildingGroups[buildingId].sort((a, b) => a.rent - b.rent);
    });

    // Interleave units from different buildings (round-robin)
    const diversified = [];
    const buildingArrays = Object.values(buildingGroups);
    let hasMore = true;
    let index = 0;

    while (hasMore) {
      hasMore = false;
      buildingArrays.forEach(buildingUnits => {
        if (index < buildingUnits.length) {
          diversified.push(buildingUnits[index]);
          hasMore = true;
        }
      });
      index++;
    }

    // Prepend featured units at the top, then diversified units
    return [...featuredUnits, ...diversified];
  };

  const fetchFavorites = async () => {
    try {
      const response = await axios.get(`${API}/favorites`, { withCredentials: true });
      const favIds = new Set(response.data.map(f => f.unit.id));
      setFavorites(favIds);
    } catch (error) {
      console.error('Error fetching favorites:', error);
    }
  };

  const toggleFavorite = async (unitId) => {
    try {
      if (favorites.has(unitId)) {
        await axios.delete(`${API}/favorites/${unitId}`, { withCredentials: true });
        setFavorites(prev => {
          const newSet = new Set(prev);
          newSet.delete(unitId);
          return newSet;
        });
        toast.success('Removed from favorites');
      } else {
        await axios.post(`${API}/favorites/${unitId}`, {}, { withCredentials: true });
        setFavorites(prev => new Set(prev).add(unitId));
        toast.success('Added to favorites');
        
        // Track favorite addition
        const unit = units.find(u => u.id === unitId);
        if (unit) {
          trackApartmentFavorite(unitId, unit.building?.name || 'Unknown Building');
        }
      }
    } catch (error) {
      toast.error('Failed to update favorites');
    }
  };

  const clearFilters = () => {
    setBedrooms('');
    setMinRent('');
    setMaxRent('');
    setBathrooms('');
    setState('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <SEO
        title="Browse No-Fee Apartments"
        description={`Search ${units.length}+ no broker fee apartments in NYC & NJ. Filter by bedrooms, price, and location. Real photos, verified listings, zero fees.`}
        keywords="browse no fee apartments, search NYC apartments, apartment listings, no broker fee search, NYC rentals, NJ apartments"
        url="/dashboard"
        structuredData={{
          "@context": "https://schema.org",
          "@type": "ItemList",
          "name": "No-Fee Apartment Listings",
          "description": "Browse verified no broker fee apartments",
          "numberOfItems": units.length,
          "itemListElement": units.slice(0, 10).map((unit, index) => ({
            "@type": "ListItem",
            "position": index + 1,
            "item": {
              "@type": "Apartment",
              "name": `${unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`} at ${unit.building?.name}`,
              "offers": {
                "@type": "Offer",
                "price": unit.rent,
                "priceCurrency": "USD"
              }
            }
          }))
        }}
      />
      
      {/* Header */}
      <header className="glass-window border-b border-amber-500/20 sticky top-0 z-50 shadow-xl shadow-amber-500/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <Logo size="default" />
            
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/fee-free-finds')}
                className="text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 font-semibold"
              >
                #FeeFreeFinds
              </Button>
              
              <Button
                variant="ghost"
                onClick={() => navigate('/favorites')}
                data-testid="nav-favorites-btn"
                className="text-slate-300 hover:text-amber-500 hover:bg-slate-800/50"
              >
                <Heart className="w-5 h-5 mr-2" />
                Favorites
              </Button>
              
              {user?.is_admin && (
                <Button
                  variant="ghost"
                  onClick={() => navigate('/admin')}
                  data-testid="nav-admin-btn"
                  className="text-slate-300 hover:text-amber-500 hover:bg-slate-800/50"
                >
                  <Settings className="w-5 h-5 mr-2" />
                  Admin
                </Button>
              )}
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" data-testid="user-menu-btn" className="text-slate-300 hover:text-amber-500 hover:bg-slate-800/50">
                    <User className="w-5 h-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                  <DropdownMenuItem className="font-medium text-slate-200">{user?.name}</DropdownMenuItem>
                  <DropdownMenuItem className="text-sm text-slate-400">{user?.email}</DropdownMenuItem>
                  <DropdownMenuItem onClick={logout} data-testid="logout-btn" className="text-slate-300 hover:text-amber-500">
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section with Premium Feel */}
        {user && (
          <div className="mb-6 animate-fade-in">
            <div className="bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 border border-amber-500/30 rounded-xl p-6 shadow-2xl shadow-amber-500/10">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg">
                  <span className="text-slate-900 font-bold text-xl">
                    {user.name?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-amber-400 to-orange-500 bg-clip-text text-transparent">
                    Welcome back, {user.name?.split(' ')[0] || 'User'}
                  </h1>
                  <p className="text-slate-400 text-sm">
                    Discover your perfect no-fee apartment
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Filters */}
        <Card className="mb-8 shadow-2xl shadow-amber-500/5 bg-gradient-to-br from-slate-800/80 to-slate-900/80 backdrop-blur-sm border border-amber-500/30">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-200 mb-2">State</label>
                <Select value={state || "any"} onValueChange={(val) => setState(val === "any" ? "" : val)}>
                  <SelectTrigger data-testid="state-filter" className="bg-slate-700/50 border-slate-600 text-slate-100">
                    <SelectValue placeholder="All States" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="any" className="text-slate-200">All States</SelectItem>
                    <SelectItem value="NY" className="text-slate-200">New York (NY)</SelectItem>
                    <SelectItem value="NJ" className="text-slate-200">New Jersey (NJ)</SelectItem>
                    <SelectItem value="PA" className="text-slate-200">Pennsylvania (PA)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-200 mb-2">Bedrooms</label>
                <Select value={bedrooms || "any"} onValueChange={(val) => setBedrooms(val === "any" ? "" : val)}>
                  <SelectTrigger data-testid="bedrooms-filter" className="bg-slate-700/50 border-slate-600 text-slate-100">
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="any" className="text-slate-200">Any</SelectItem>
                    <SelectItem value="0" className="text-slate-200">Studio</SelectItem>
                    <SelectItem value="1" className="text-slate-200">1 BR</SelectItem>
                    <SelectItem value="2" className="text-slate-200">2 BR</SelectItem>
                    <SelectItem value="3" className="text-slate-200">3 BR</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-200 mb-2">Min Rent</label>
                <Input
                  type="number"
                  placeholder="$1,000"
                  value={minRent}
                  onChange={(e) => setMinRent(e.target.value)}
                  data-testid="min-rent-filter"
                  className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-200 mb-2">Max Rent</label>
                <Input
                  type="number"
                  placeholder="$5,000"
                  value={maxRent}
                  onChange={(e) => setMaxRent(e.target.value)}
                  data-testid="max-rent-filter"
                  className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-200 mb-2">Bathrooms</label>
                <Select value={bathrooms || "any"} onValueChange={(val) => setBathrooms(val === "any" ? "" : val)}>
                  <SelectTrigger data-testid="bathrooms-filter" className="bg-slate-700/50 border-slate-600 text-slate-100">
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="any" className="text-slate-200">Any</SelectItem>
                    <SelectItem value="1" className="text-slate-200">1 Bath</SelectItem>
                    <SelectItem value="1.5" className="text-slate-200">1.5 Bath</SelectItem>
                    <SelectItem value="2" className="text-slate-200">2 Bath</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {(bedrooms || minRent || maxRent || bathrooms || state) && (
              <div className="mt-4">
                <Button variant="outline" onClick={clearFilters} data-testid="clear-filters-btn" className="border-amber-500/30 text-amber-500 hover:bg-slate-700">
                  Clear Filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Header with View Toggle */}
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-slate-100">
            Available Apartments <span className="warm-gradient-text">({units.length})</span>
          </h2>
          
          <div className="flex gap-2">
            <Button
              onClick={() => setViewMode('list')}
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="sm"
              className={viewMode === 'list' ? 'warm-gradient text-slate-900' : 'border-amber-500/30 text-amber-500 hover:bg-slate-700'}
            >
              <Building2 className="w-4 h-4 mr-2" />
              List View
            </Button>
            <Button
              onClick={() => setViewMode('map')}
              variant={viewMode === 'map' ? 'default' : 'outline'}
              size="sm"
              className={viewMode === 'map' ? 'warm-gradient text-slate-900' : 'border-amber-500/30 text-amber-500 hover:bg-slate-700'}
            >
              <Map className="w-4 h-4 mr-2" />
              Map View
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="text-xl text-amber-500">Loading apartments...</div>
          </div>
        ) : units.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-xl text-slate-400">No apartments found. Try adjusting your filters.</div>
          </div>
        ) : viewMode === 'map' ? (
          <div className="mb-8">
            <ApartmentMap 
              apartments={units} 
              center={{ lat: 40.7128, lng: -74.0060 }}
              zoom={11}
            />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="units-grid">
            {units.map((unit) => (
              <ListingCard
                key={unit.id}
                unit={unit}
                user={user}
                isFavorite={favorites.has(unit.id)}
                onToggleFavorite={toggleFavorite}
                onShare={(u) => {
                  setSelectedUnit(u);
                  setShareDialogOpen(true);
                }}
                showBlur={!user}
              />
            ))}
          </div>
        )}
      </div>

      {/* Share Dialog */}
      {selectedUnit && (
        <ShareDialog
          open={shareDialogOpen}
          onOpenChange={setShareDialogOpen}
          unit={selectedUnit}
          building={selectedUnit.building}
        />
      )}
    </div>
  );
};

export default Dashboard;
