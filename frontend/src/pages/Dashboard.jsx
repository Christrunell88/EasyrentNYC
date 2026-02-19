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
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { Building2, BedDouble, Bath, DollarSign, Heart, LogOut, User, Settings, Eye, Share2, Map, SlidersHorizontal, X, ChevronDown } from 'lucide-react';
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
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);
  const [sortBy, setSortBy] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [activeRecommendation, setActiveRecommendation] = useState('');

  // Count active filters
  const activeFilterCount = [bedrooms, minRent, maxRent, bathrooms, state].filter(Boolean).length;

  useEffect(() => {
    fetchUnits();
    fetchFavorites();
    fetchRecommendations();
  }, [bedrooms, minRent, maxRent, bathrooms, state]);

  const fetchRecommendations = async () => {
    try {
      const response = await axios.get(`${API}/recommendations`);
      setRecommendations(response.data.recommendations || []);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    }
  };

  const applyRecommendation = (rec) => {
    // Clear existing filters first
    clearFilters();
    setActiveRecommendation(rec.id);
    
    // Apply the recommendation's filters
    if (rec.filter) {
      if (rec.filter.bedrooms !== undefined) setBedrooms(String(rec.filter.bedrooms));
      if (rec.filter.min_bedrooms !== undefined) setBedrooms(String(rec.filter.min_bedrooms));
      if (rec.filter.min_rent) setMinRent(String(rec.filter.min_rent));
      if (rec.filter.max_rent) setMaxRent(String(rec.filter.max_rent));
      if (rec.filter.sort) setSortBy(rec.filter.sort);
      if (rec.filter.new) setSortBy('newest');
    }
  };

  const fetchUnits = async () => {
    try {
      const params = new URLSearchParams();
      if (bedrooms) params.append('bedrooms', bedrooms);
      if (minRent) params.append('min_rent', minRent);
      if (maxRent) params.append('max_rent', maxRent);
      if (bathrooms) params.append('bathrooms', bathrooms);
      if (state) params.append('state', state);
      
      const response = await axios.get(`${API}/units?limit=500&${params.toString()}`, { withCredentials: true });
      
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
    setSortBy('');
    setActiveRecommendation('');
  };

  // Recommendation icon mapping
  const getRecommendationIcon = (iconName) => {
    switch(iconName) {
      case 'building': return <Building2 className="w-4 h-4" />;
      case 'dollar': return <DollarSign className="w-4 h-4" />;
      case 'sparkle': return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2L9.19 8.63L2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2z"/>
        </svg>
      );
      case 'crown': return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm0 2h14v2H5v-2z"/>
        </svg>
      );
      case 'bed': return <BedDouble className="w-4 h-4" />;
      case 'piggy': return (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M19 10c0-1.1-.9-2-2-2V6c0-1.1-.9-2-2-2H9C7.9 4 7 4.9 7 6v2c-1.1 0-2 .9-2 2v3c0 .55.45 1 1 1h1v3c0 1.1.9 2 2 2h6c1.1 0 2-.9 2-2v-3h1c.55 0 1-.45 1-1v-3zM9 6h6v2H9V6z"/>
        </svg>
      );
      case 'users': return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
        </svg>
      );
      default: return <Building2 className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <SEO
        title="Browse No-Fee Apartments"
        description={`Search ${units.length}+ no broker fee apartments in NYC & NJ. Filter by bedrooms, price, and location. Real photos, verified listings, zero fees.`}
        keywords="browse no fee apartments, search NYC apartments, apartment listings, no broker fee search, NYC rentals, NJ apartments, no fee apartments near me, affordable apartments NYC, luxury no fee rentals, studio apartments no broker fee, 1 bedroom no fee NYC, pet friendly no fee apartments, doorman building no fee"
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
        
        {/* Responsive Filter Bar */}
        <div className="mb-6 space-y-4">
          {/* Desktop Filter Bar - Hidden on mobile */}
          <div className="hidden md:flex flex-wrap items-center gap-3 p-4 bg-[#1a1a1a] border border-[#D4AF37]/20 rounded-lg">
            {/* Location */}
            <div className="flex items-center gap-2">
              <Map className="w-4 h-4 text-[#D4AF37]" />
              <Select value={state || "any"} onValueChange={(val) => setState(val === "any" ? "" : val)}>
                <SelectTrigger data-testid="state-filter" className="w-[130px] h-9 bg-[#0a0a0a] border-[#333] text-[#F5F5F5] text-sm">
                  <SelectValue placeholder="All Areas" />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-[#333]">
                  <SelectItem value="any" className="text-[#F5F5F5]">All Areas</SelectItem>
                  <SelectItem value="NY" className="text-[#F5F5F5]">New York</SelectItem>
                  <SelectItem value="NJ" className="text-[#F5F5F5]">New Jersey</SelectItem>
                  <SelectItem value="PA" className="text-[#F5F5F5]">Pennsylvania</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-px h-6 bg-[#333]" />
            
            {/* Beds */}
            <div className="flex items-center gap-2">
              <BedDouble className="w-4 h-4 text-[#D4AF37]" />
              <Select value={bedrooms || "any"} onValueChange={(val) => setBedrooms(val === "any" ? "" : val)}>
                <SelectTrigger data-testid="bedrooms-filter" className="w-[100px] h-9 bg-[#0a0a0a] border-[#333] text-[#F5F5F5] text-sm">
                  <SelectValue placeholder="Beds" />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-[#333]">
                  <SelectItem value="any" className="text-[#F5F5F5]">Any Beds</SelectItem>
                  <SelectItem value="0" className="text-[#F5F5F5]">Studio</SelectItem>
                  <SelectItem value="1" className="text-[#F5F5F5]">1 Bed</SelectItem>
                  <SelectItem value="2" className="text-[#F5F5F5]">2 Beds</SelectItem>
                  <SelectItem value="3" className="text-[#F5F5F5]">3+ Beds</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Baths */}
            <div className="flex items-center gap-2">
              <Bath className="w-4 h-4 text-[#D4AF37]" />
              <Select value={bathrooms || "any"} onValueChange={(val) => setBathrooms(val === "any" ? "" : val)}>
                <SelectTrigger data-testid="bathrooms-filter" className="w-[100px] h-9 bg-[#0a0a0a] border-[#333] text-[#F5F5F5] text-sm">
                  <SelectValue placeholder="Baths" />
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-[#333]">
                  <SelectItem value="any" className="text-[#F5F5F5]">Any Baths</SelectItem>
                  <SelectItem value="1" className="text-[#F5F5F5]">1 Bath</SelectItem>
                  <SelectItem value="1.5" className="text-[#F5F5F5]">1.5 Bath</SelectItem>
                  <SelectItem value="2" className="text-[#F5F5F5]">2+ Baths</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="w-px h-6 bg-[#333]" />
            
            {/* Price Range */}
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-[#D4AF37]" />
              <Input
                type="number"
                placeholder="Min"
                value={minRent}
                onChange={(e) => setMinRent(e.target.value)}
                data-testid="min-rent-filter"
                className="w-[90px] h-9 bg-[#0a0a0a] border-[#333] text-[#F5F5F5] text-sm placeholder:text-[#666]"
              />
              <span className="text-[#666]">—</span>
              <Input
                type="number"
                placeholder="Max"
                value={maxRent}
                onChange={(e) => setMaxRent(e.target.value)}
                data-testid="max-rent-filter"
                className="w-[90px] h-9 bg-[#0a0a0a] border-[#333] text-[#F5F5F5] text-sm placeholder:text-[#666]"
              />
            </div>
            
            {/* Clear Filters */}
            {(bedrooms || minRent || maxRent || bathrooms || state) && (
              <>
                <div className="w-px h-6 bg-[#333]" />
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={clearFilters} 
                  data-testid="clear-filters-btn" 
                  className="text-[#888] hover:text-[#D4AF37] hover:bg-transparent text-sm h-9"
                >
                  Clear
                </Button>
              </>
            )}
          </div>

          {/* Mobile Filter Bar - Visible only on mobile */}
          <div className="md:hidden">
            {/* Quick Access Buttons */}
            <div className="flex gap-2 mb-3">
              {/* Main Filter & Sort Button */}
              <Sheet open={mobileFilterOpen} onOpenChange={setMobileFilterOpen}>
                <SheetTrigger asChild>
                  <Button 
                    variant="outline" 
                    className="flex-1 h-11 bg-[#1a1a1a] border-[#D4AF37]/30 text-[#F5F5F5] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]"
                  >
                    <SlidersHorizontal className="w-4 h-4 mr-2 text-[#D4AF37]" />
                    Filter & Sort
                    {activeFilterCount > 0 && (
                      <Badge className="ml-2 bg-[#D4AF37] text-[#0a0a0a] text-xs px-1.5 py-0">
                        {activeFilterCount}
                      </Badge>
                    )}
                  </Button>
                </SheetTrigger>
                <SheetContent side="bottom" className="bg-[#1a1a1a] border-t border-[#D4AF37]/30 rounded-t-2xl h-[85vh]">
                  <SheetHeader className="pb-4 border-b border-[#333]">
                    <div className="flex items-center justify-between">
                      <SheetTitle className="text-[#F5F5F5] font-philosopher text-xl">Filter & Sort</SheetTitle>
                      {activeFilterCount > 0 && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={clearFilters}
                          className="text-[#D4AF37] hover:text-[#E5C158] hover:bg-transparent"
                        >
                          Clear all
                        </Button>
                      )}
                    </div>
                  </SheetHeader>
                  
                  <div className="py-6 space-y-6 overflow-y-auto max-h-[calc(85vh-140px)]">
                    {/* Price Range - Most Used */}
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 text-[#F5F5F5] font-medium">
                        <DollarSign className="w-5 h-5 text-[#D4AF37]" />
                        Price Range
                      </label>
                      <div className="flex items-center gap-3">
                        <div className="flex-1">
                          <Input
                            type="number"
                            placeholder="Min price"
                            value={minRent}
                            onChange={(e) => setMinRent(e.target.value)}
                            className="h-12 bg-[#0a0a0a] border-[#333] text-[#F5F5F5] text-base placeholder:text-[#666]"
                          />
                        </div>
                        <span className="text-[#666]">to</span>
                        <div className="flex-1">
                          <Input
                            type="number"
                            placeholder="Max price"
                            value={maxRent}
                            onChange={(e) => setMaxRent(e.target.value)}
                            className="h-12 bg-[#0a0a0a] border-[#333] text-[#F5F5F5] text-base placeholder:text-[#666]"
                          />
                        </div>
                      </div>
                      {/* Quick Price Presets */}
                      <div className="flex flex-wrap gap-2">
                        {[
                          { label: 'Under $3k', max: '3000' },
                          { label: 'Under $4k', max: '4000' },
                          { label: 'Under $5k', max: '5000' },
                          { label: '$5k+', min: '5000' },
                        ].map((preset) => (
                          <Button
                            key={preset.label}
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setMinRent(preset.min || '');
                              setMaxRent(preset.max || '');
                            }}
                            className={`h-8 rounded-full text-xs ${
                              (preset.max && maxRent === preset.max && !minRent) || (preset.min && minRent === preset.min && !maxRent)
                                ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]'
                                : 'border-[#333] text-[#888] hover:border-[#D4AF37] hover:text-[#D4AF37]'
                            }`}
                          >
                            {preset.label}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Bedrooms - Most Used */}
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 text-[#F5F5F5] font-medium">
                        <BedDouble className="w-5 h-5 text-[#D4AF37]" />
                        Bedrooms
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {[
                          { label: 'Any', value: '' },
                          { label: 'Studio', value: '0' },
                          { label: '1 Bed', value: '1' },
                          { label: '2 Beds', value: '2' },
                          { label: '3+ Beds', value: '3' },
                        ].map((option) => (
                          <Button
                            key={option.label}
                            variant="outline"
                            onClick={() => setBedrooms(option.value)}
                            className={`h-11 px-5 rounded-lg ${
                              bedrooms === option.value
                                ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]'
                                : 'border-[#333] text-[#F5F5F5] hover:border-[#D4AF37] hover:text-[#D4AF37]'
                            }`}
                          >
                            {option.label}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Location - Most Used */}
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 text-[#F5F5F5] font-medium">
                        <Map className="w-5 h-5 text-[#D4AF37]" />
                        Location
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {[
                          { label: 'All Areas', value: '' },
                          { label: 'New York', value: 'NY' },
                          { label: 'New Jersey', value: 'NJ' },
                          { label: 'Pennsylvania', value: 'PA' },
                        ].map((option) => (
                          <Button
                            key={option.label}
                            variant="outline"
                            onClick={() => setState(option.value)}
                            className={`h-11 px-5 rounded-lg ${
                              state === option.value
                                ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]'
                                : 'border-[#333] text-[#F5F5F5] hover:border-[#D4AF37] hover:text-[#D4AF37]'
                            }`}
                          >
                            {option.label}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Bathrooms */}
                    <div className="space-y-3">
                      <label className="flex items-center gap-2 text-[#F5F5F5] font-medium">
                        <Bath className="w-5 h-5 text-[#D4AF37]" />
                        Bathrooms
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {[
                          { label: 'Any', value: '' },
                          { label: '1 Bath', value: '1' },
                          { label: '1.5 Bath', value: '1.5' },
                          { label: '2+ Baths', value: '2' },
                        ].map((option) => (
                          <Button
                            key={option.label}
                            variant="outline"
                            onClick={() => setBathrooms(option.value)}
                            className={`h-11 px-5 rounded-lg ${
                              bathrooms === option.value
                                ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]'
                                : 'border-[#333] text-[#F5F5F5] hover:border-[#D4AF37] hover:text-[#D4AF37]'
                            }`}
                          >
                            {option.label}
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Apply Button - Fixed at bottom */}
                  <div className="absolute bottom-0 left-0 right-0 p-4 bg-[#1a1a1a] border-t border-[#333]">
                    <Button 
                      onClick={() => setMobileFilterOpen(false)}
                      className="w-full h-12 bg-[#D4AF37] hover:bg-[#E5C158] text-[#0a0a0a] font-semibold text-base"
                    >
                      Show {units.length} Apartments
                    </Button>
                  </div>
                </SheetContent>
              </Sheet>

              {/* Quick Beds Button */}
              <Select value={bedrooms || "any"} onValueChange={(val) => setBedrooms(val === "any" ? "" : val)}>
                <SelectTrigger className="w-auto h-11 bg-[#1a1a1a] border-[#D4AF37]/30 text-[#F5F5F5] hover:border-[#D4AF37]">
                  <BedDouble className="w-4 h-4 mr-1.5 text-[#D4AF37]" />
                  <span className="text-sm">{bedrooms === '' ? 'Beds' : bedrooms === '0' ? 'Studio' : `${bedrooms} Bed`}</span>
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-[#333]">
                  <SelectItem value="any" className="text-[#F5F5F5]">Any Beds</SelectItem>
                  <SelectItem value="0" className="text-[#F5F5F5]">Studio</SelectItem>
                  <SelectItem value="1" className="text-[#F5F5F5]">1 Bed</SelectItem>
                  <SelectItem value="2" className="text-[#F5F5F5]">2 Beds</SelectItem>
                  <SelectItem value="3" className="text-[#F5F5F5]">3+ Beds</SelectItem>
                </SelectContent>
              </Select>

              {/* Quick Area Button */}
              <Select value={state || "any"} onValueChange={(val) => setState(val === "any" ? "" : val)}>
                <SelectTrigger className="w-auto h-11 bg-[#1a1a1a] border-[#D4AF37]/30 text-[#F5F5F5] hover:border-[#D4AF37]">
                  <Map className="w-4 h-4 mr-1.5 text-[#D4AF37]" />
                  <span className="text-sm">{state || 'Area'}</span>
                </SelectTrigger>
                <SelectContent className="bg-[#1a1a1a] border-[#333]">
                  <SelectItem value="any" className="text-[#F5F5F5]">All Areas</SelectItem>
                  <SelectItem value="NY" className="text-[#F5F5F5]">New York</SelectItem>
                  <SelectItem value="NJ" className="text-[#F5F5F5]">New Jersey</SelectItem>
                  <SelectItem value="PA" className="text-[#F5F5F5]">Pennsylvania</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Active Filter Pills - Mobile */}
            {activeFilterCount > 0 && (
              <div className="flex flex-wrap gap-2">
                {state && (
                  <Badge className="bg-[#D4AF37]/20 text-[#D4AF37] border border-[#D4AF37]/40 px-3 py-1 flex items-center gap-1.5">
                    {state === 'NY' ? 'New York' : state === 'NJ' ? 'New Jersey' : 'Pennsylvania'}
                    <X className="w-3 h-3 cursor-pointer" onClick={() => setState('')} />
                  </Badge>
                )}
                {bedrooms && (
                  <Badge className="bg-[#D4AF37]/20 text-[#D4AF37] border border-[#D4AF37]/40 px-3 py-1 flex items-center gap-1.5">
                    {bedrooms === '0' ? 'Studio' : `${bedrooms} Bed`}
                    <X className="w-3 h-3 cursor-pointer" onClick={() => setBedrooms('')} />
                  </Badge>
                )}
                {(minRent || maxRent) && (
                  <Badge className="bg-[#D4AF37]/20 text-[#D4AF37] border border-[#D4AF37]/40 px-3 py-1 flex items-center gap-1.5">
                    {minRent && maxRent ? `$${minRent}-$${maxRent}` : minRent ? `$${minRent}+` : `Under $${maxRent}`}
                    <X className="w-3 h-3 cursor-pointer" onClick={() => { setMinRent(''); setMaxRent(''); }} />
                  </Badge>
                )}
                {bathrooms && (
                  <Badge className="bg-[#D4AF37]/20 text-[#D4AF37] border border-[#D4AF37]/40 px-3 py-1 flex items-center gap-1.5">
                    {bathrooms} Bath
                    <X className="w-3 h-3 cursor-pointer" onClick={() => setBathrooms('')} />
                  </Badge>
                )}
              </div>
            )}
          </div>
          
          {/* Quick Filter Chips - Desktop Only */}
          <div className="hidden md:flex flex-wrap items-center gap-2">
            <span className="text-[#888] text-sm mr-1">Quick filters:</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setState('NY'); setMaxRent('4000'); setBedrooms(''); setBathrooms(''); setMinRent(''); setActiveRecommendation(''); }}
              className={`h-8 px-4 rounded-full text-xs font-medium transition-all ${
                state === 'NY' && maxRent === '4000' && !bedrooms
                  ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]' 
                  : 'bg-transparent border-[#D4AF37]/40 text-[#D4AF37] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]'
              }`}
            >
              NYC under $4k
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setBedrooms('0'); setState(''); setMinRent(''); setMaxRent(''); setBathrooms(''); setActiveRecommendation(''); }}
              className={`h-8 px-4 rounded-full text-xs font-medium transition-all ${
                bedrooms === '0' && !state && !maxRent
                  ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]' 
                  : 'bg-transparent border-[#D4AF37]/40 text-[#D4AF37] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]'
              }`}
            >
              Studios only
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setState('NJ'); setMinRent('3500'); setBedrooms(''); setBathrooms(''); setMaxRent(''); setActiveRecommendation(''); }}
              className={`h-8 px-4 rounded-full text-xs font-medium transition-all ${
                state === 'NJ' && minRent === '3500' && !bedrooms
                  ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]' 
                  : 'bg-transparent border-[#D4AF37]/40 text-[#D4AF37] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]'
              }`}
            >
              NJ luxury
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setBedrooms('2'); setState(''); setMinRent(''); setMaxRent(''); setBathrooms(''); setActiveRecommendation(''); }}
              className={`h-8 px-4 rounded-full text-xs font-medium transition-all ${
                bedrooms === '2' && !state && !maxRent
                  ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]' 
                  : 'bg-transparent border-[#D4AF37]/40 text-[#D4AF37] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]'
              }`}
            >
              2 Bedrooms
            </Button>
          </div>

          {/* Smart Recommendations - Based on Current Inventory */}
          {recommendations.length > 0 && (
            <div className="mt-4 p-4 bg-gradient-to-r from-[#1a1a1a] to-[#0f0f0f] border border-[#D4AF37]/20 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <svg className="w-4 h-4 text-[#D4AF37]" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L9.19 8.63L2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2z"/>
                </svg>
                <span className="text-[#D4AF37] text-sm font-medium">Recommended for you</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {recommendations.slice(0, 5).map((rec) => (
                  <Button
                    key={rec.id}
                    variant="outline"
                    size="sm"
                    onClick={() => applyRecommendation(rec)}
                    className={`h-9 px-4 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
                      activeRecommendation === rec.id
                        ? 'bg-[#D4AF37] text-[#0a0a0a] border-[#D4AF37]' 
                        : 'bg-[#0a0a0a] border-[#333] text-[#F5F5F5] hover:border-[#D4AF37] hover:text-[#D4AF37]'
                    }`}
                    title={rec.description}
                  >
                    <span className={activeRecommendation === rec.id ? 'text-[#0a0a0a]' : 'text-[#D4AF37]'}>
                      {getRecommendationIcon(rec.icon)}
                    </span>
                    <span>{rec.label}</span>
                    {rec.count > 0 && (
                      <Badge className={`ml-1 text-[10px] px-1.5 py-0 ${
                        activeRecommendation === rec.id 
                          ? 'bg-[#0a0a0a]/20 text-[#0a0a0a]' 
                          : 'bg-[#D4AF37]/20 text-[#D4AF37]'
                      }`}>
                        {rec.count}
                      </Badge>
                    )}
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Trust Strip */}
        <div className="mb-6 py-4 px-6 bg-[#0a0a0a] border border-[#D4AF37]/20 rounded-lg">
          <div className="flex flex-wrap justify-center items-center gap-x-8 gap-y-3 text-sm">
            <div className="flex items-center gap-2 text-[#B8B8B8]">
              <svg className="w-5 h-5 text-[#4ade80]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>100% verified no-fee buildings</span>
            </div>
            <div className="hidden sm:block w-px h-4 bg-[#333]" />
            <div className="flex items-center gap-2 text-[#B8B8B8]">
              <svg className="w-5 h-5 text-[#D4AF37]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Updated daily</span>
            </div>
            <div className="hidden sm:block w-px h-4 bg-[#333]" />
            <div className="flex items-center gap-2 text-[#B8B8B8]">
              <svg className="w-5 h-5 text-[#60a5fa]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              <span>Direct from owners & landlords</span>
            </div>
          </div>
        </div>

        {/* Results Header with View Toggle */}
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-xl font-philosopher font-bold text-[#F5F5F5]">
            {units.length} Apartments Available
          </h2>
          
          <div className="flex gap-2">
            <Button
              onClick={() => setViewMode('list')}
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="sm"
              className={viewMode === 'list' 
                ? 'bg-[#D4AF37] text-[#0a0a0a] hover:bg-[#E5C158]' 
                : 'border-[#D4AF37]/40 text-[#D4AF37] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]'}
            >
              <Building2 className="w-4 h-4 mr-2" />
              List
            </Button>
            <Button
              onClick={() => setViewMode('map')}
              variant={viewMode === 'map' ? 'default' : 'outline'}
              size="sm"
              className={viewMode === 'map' 
                ? 'bg-[#D4AF37] text-[#0a0a0a] hover:bg-[#E5C158]' 
                : 'border-[#D4AF37]/40 text-[#D4AF37] hover:bg-[#D4AF37]/10 hover:border-[#D4AF37]'}
            >
              <Map className="w-4 h-4 mr-2" />
              Map
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="text-xl text-[#D4AF37]">Loading apartments...</div>
          </div>
        ) : units.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-xl text-[#888]">No apartments found. Try adjusting your filters.</div>
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
          <div className="space-y-12" data-testid="units-grid">
            {/* Group units into sections of 9 (3x3 grid) */}
            {Array.from({ length: Math.ceil(units.length / 9) }, (_, groupIndex) => {
              const startIndex = groupIndex * 9;
              const groupUnits = units.slice(startIndex, startIndex + 9);
              const isLastGroup = groupIndex === Math.ceil(units.length / 9) - 1;
              
              return (
                <div key={groupIndex} className="relative">
                  {/* Section Header */}
                  {groupIndex > 0 && (
                    <div className="flex items-center gap-4 mb-8">
                      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[#D4AF37]/30 to-transparent" />
                      <span className="text-[#666] text-xs font-philosopher tracking-widest uppercase">
                        {startIndex + 1}–{Math.min(startIndex + 9, units.length)} of {units.length}
                      </span>
                      <div className="flex-1 h-px bg-gradient-to-r from-transparent via-[#D4AF37]/30 to-transparent" />
                    </div>
                  )}
                  
                  {/* Cards Grid with increased gap */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {groupUnits.map((unit) => (
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
                  
                  {/* Back to Top / Filters button after each group (except last if small) */}
                  {!isLastGroup && (
                    <div className="flex justify-center mt-10">
                      <button
                        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                        className="group flex items-center gap-2 px-5 py-2.5 bg-[#1a1a1a] border border-[#D4AF37]/30 rounded-full text-sm text-[#888] hover:text-[#D4AF37] hover:border-[#D4AF37]/60 transition-all duration-300"
                      >
                        <svg 
                          className="w-4 h-4 transform group-hover:-translate-y-0.5 transition-transform" 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                        </svg>
                        Back to Filters
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
            
            {/* Final Back to Top button */}
            {units.length > 9 && (
              <div className="flex justify-center pt-4 pb-8">
                <button
                  onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                  className="group flex items-center gap-2 px-6 py-3 bg-[#D4AF37]/10 border border-[#D4AF37]/40 rounded-full text-sm font-medium text-[#D4AF37] hover:bg-[#D4AF37]/20 hover:border-[#D4AF37] transition-all duration-300"
                >
                  <svg 
                    className="w-4 h-4 transform group-hover:-translate-y-1 transition-transform" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                  Back to Top
                </button>
              </div>
            )}
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
