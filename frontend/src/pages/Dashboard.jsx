import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { API } from '../App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Building2, BedDouble, Bath, DollarSign, Heart, LogOut, User, Settings, Filter, X, MapPin, Calendar, Maximize2 } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState(new Set());
  const [showFilters, setShowFilters] = useState(false);
  
  // Filters
  const [bedrooms, setBedrooms] = useState('');
  const [minRent, setMinRent] = useState('');
  const [maxRent, setMaxRent] = useState('');
  const [bathrooms, setBathrooms] = useState('');

  useEffect(() => {
    fetchUser();
    fetchUnits();
    fetchFavorites();
  }, [bedrooms, minRent, maxRent, bathrooms]);
  
  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };
  
  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const fetchUnits = async () => {
    try {
      const params = new URLSearchParams();
      if (bedrooms) params.append('bedrooms', bedrooms);
      if (minRent) params.append('min_rent', minRent);
      if (maxRent) params.append('max_rent', maxRent);
      if (bathrooms) params.append('bathrooms', bathrooms);
      
      const response = await axios.get(`${API}/units?${params.toString()}`, { withCredentials: true });
      setUnits(response.data);
    } catch (error) {
      console.error('Error fetching units:', error);
      toast.error('Failed to load apartments');
    } finally {
      setLoading(false);
    }
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

  const toggleFavorite = async (unitId, e) => {
    e.stopPropagation();
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
  };

  const hasActiveFilters = bedrooms || minRent || maxRent || bathrooms;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">NoFeesApts.com</h1>
                <p className="text-xs text-gray-500">NYC & Northern NJ</p>
              </div>
            </div>
            
            <div className=\"flex items-center gap-3\">
              <Button
                variant=\"ghost\"
                onClick={() => navigate('/favorites')}
                className=\"relative\"
                data-testid=\"nav-favorites-btn\"
              >
                <Heart className=\"w-5 h-5\" />
                {favorites.size > 0 && (
                  <span className=\"absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center\">
                    {favorites.size}
                  </span>
                )}
              </Button>
              
              {user?.is_admin && (
                <Button
                  variant=\"ghost\"
                  onClick={() => navigate('/admin')}
                  data-testid=\"nav-admin-btn\"
                >
                  <Settings className=\"w-5 h-5\" />
                </Button>
              )}
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant=\"ghost\" size=\"icon\" className=\"rounded-full\" data-testid=\"user-menu-btn\">
                    <div className=\"w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center\">
                      <User className=\"w-4 h-4 text-white\" />
                    </div>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align=\"end\" className=\"w-56\">
                  <div className=\"px-2 py-2\">
                    <p className=\"font-medium text-sm\">{user?.name}</p>
                    <p className=\"text-xs text-gray-500\">{user?.email}</p>
                  </div>
                  <DropdownMenuItem onClick={logout} data-testid=\"logout-btn\" className=\"text-red-600\">
                    <LogOut className=\"w-4 h-4 mr-2\" />
                    Logout
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      <div className=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8\">
        {/* Filter Bar */}
        <div className=\"mb-8\">
          <div className=\"flex items-center justify-between mb-4\">
            <div>
              <h2 className=\"text-3xl font-bold text-gray-900\">Discover Your Home</h2>
              <p className=\"text-gray-600 mt-1\">
                {loading ? 'Loading...' : `${units.length} apartments available`}
              </p>
            </div>
            
            <Button
              onClick={() => setShowFilters(!showFilters)}
              variant=\"outline\"
              className=\"gap-2\"
            >
              <Filter className=\"w-4 h-4\" />
              Filters
              {hasActiveFilters && (
                <Badge className=\"ml-1 bg-blue-600\">Active</Badge>
              )}
            </Button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <Card className=\"border-0 shadow-lg\">
              <CardContent className=\"pt-6\">
                <div className=\"grid grid-cols-1 md:grid-cols-4 gap-4 mb-4\">
                  <div>
                    <label className=\"block text-sm font-medium text-gray-700 mb-2\">Bedrooms</label>
                    <Select value={bedrooms || \"any\"} onValueChange={(val) => setBedrooms(val === \"any\" ? \"\" : val)}>
                      <SelectTrigger data-testid=\"bedrooms-filter\" className=\"bg-white\">
                        <SelectValue placeholder=\"Any\" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value=\"any\">Any</SelectItem>
                        <SelectItem value=\"0\">Studio</SelectItem>
                        <SelectItem value=\"1\">1 BR</SelectItem>
                        <SelectItem value=\"2\">2 BR</SelectItem>
                        <SelectItem value=\"3\">3 BR</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <label className=\"block text-sm font-medium text-gray-700 mb-2\">Min Rent</label>
                    <Input
                      type=\"number\"
                      placeholder=\"$1,000\"
                      value={minRent}
                      onChange={(e) => setMinRent(e.target.value)}
                      data-testid=\"min-rent-filter\"
                      className=\"bg-white\"
                    />
                  </div>
                  
                  <div>
                    <label className=\"block text-sm font-medium text-gray-700 mb-2\">Max Rent</label>
                    <Input
                      type=\"number\"
                      placeholder=\"$5,000\"
                      value={maxRent}
                      onChange={(e) => setMaxRent(e.target.value)}
                      data-testid=\"max-rent-filter\"
                      className=\"bg-white\"
                    />
                  </div>
                  
                  <div>
                    <label className=\"block text-sm font-medium text-gray-700 mb-2\">Bathrooms</label>
                    <Select value={bathrooms || \"any\"} onValueChange={(val) => setBathrooms(val === \"any\" ? \"\" : val)}>
                      <SelectTrigger data-testid=\"bathrooms-filter\" className=\"bg-white\">
                        <SelectValue placeholder=\"Any\" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value=\"any\">Any</SelectItem>
                        <SelectItem value=\"1\">1 Bath</SelectItem>
                        <SelectItem value=\"1.5\">1.5 Bath</SelectItem>
                        <SelectItem value=\"2\">2 Bath</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {hasActiveFilters && (
                  <Button variant=\"ghost\" onClick={clearFilters} data-testid=\"clear-filters-btn\" className=\"gap-2\">
                    <X className=\"w-4 h-4\" />
                    Clear All Filters
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Apartments Grid */}
        {loading ? (
          <div className=\"text-center py-20\">
            <div className=\"inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4\"></div>
            <p className=\"text-gray-600\">Loading apartments...</p>
          </div>
        ) : units.length === 0 ? (
          <div className=\"text-center py-20\">
            <div className=\"text-6xl mb-4\">🏠</div>
            <h3 className=\"text-2xl font-bold text-gray-900 mb-2\">No apartments found</h3>
            <p className=\"text-gray-600 mb-6\">Try adjusting your filters</p>
            {hasActiveFilters && (
              <Button onClick={clearFilters} variant=\"outline\">Clear Filters</Button>
            )}
          </div>
        ) : (
          <div className=\"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6\" data-testid=\"units-grid\">
            {units.map((unit) => (
              <Card
                key={unit.id}
                className=\"group overflow-hidden hover:shadow-2xl transition-all duration-500 cursor-pointer border-0 shadow-lg bg-white\"
                onClick={() => navigate(`/unit/${unit.id}`)}
                data-testid={`unit-card-${unit.id}`}
              >
                <div className=\"relative h-56 bg-gradient-to-br from-blue-100 to-indigo-100 overflow-hidden\">
                  {unit.images && unit.images.length > 0 ? (
                    <img
                      src={unit.images[0]}
                      alt={`Unit ${unit.unit_number}`}
                      className=\"w-full h-full object-cover group-hover:scale-110 transition-transform duration-700\"
                    />
                  ) : (
                    <div className=\"w-full h-full flex items-center justify-center\">
                      <Building2 className=\"w-20 h-20 text-indigo-300\" />
                    </div>
                  )}
                  
                  {/* Favorite Button */}
                  <button
                    onClick={(e) => toggleFavorite(unit.id, e)}
                    className=\"absolute top-3 right-3 w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-transform duration-300 z-10\"
                    data-testid={`favorite-btn-${unit.id}`}
                  >
                    <Heart
                      className={`w-5 h-5 transition-colors ${
                        favorites.has(unit.id)
                          ? 'fill-red-500 text-red-500'
                          : 'text-gray-600 hover:text-red-500'
                      }`}
                    />
                  </button>
                  
                  {/* No Fee Badge */}
                  <div className=\"absolute bottom-3 left-3\">
                    <Badge className=\"bg-emerald-500 text-white border-0 shadow-lg\">
                      No Fee
                    </Badge>
                  </div>

                  {/* Overlay Gradient */}
                  <div className=\"absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500\"></div>
                </div>
                
                <CardContent className=\"p-5\">
                  <div className=\"mb-3\">
                    <h3 className=\"font-bold text-lg text-gray-900 mb-1 group-hover:text-blue-600 transition-colors\">
                      {unit.building?.name}
                    </h3>
                    <div className=\"flex items-center gap-1 text-sm text-gray-600\">
                      <MapPin className=\"w-3 h-3\" />
                      <span>{unit.building?.neighborhood}, {unit.building?.city}</span>
                    </div>
                  </div>
                  
                  {/* Features */}
                  <div className=\"flex items-center gap-4 mb-4 text-sm text-gray-700\">
                    <div className=\"flex items-center gap-1.5\">
                      <div className=\"w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center\">
                        <BedDouble className=\"w-4 h-4 text-blue-600\" />
                      </div>
                      <span className=\"font-medium\">
                        {unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`}
                      </span>
                    </div>
                    <div className=\"flex items-center gap-1.5\">
                      <div className=\"w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center\">
                        <Bath className=\"w-4 h-4 text-indigo-600\" />
                      </div>
                      <span className=\"font-medium\">{unit.bathrooms} BA</span>
                    </div>
                    {unit.square_feet && (
                      <div className=\"flex items-center gap-1.5\">
                        <div className=\"w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center\">
                          <Maximize2 className=\"w-4 h-4 text-purple-600\" />
                        </div>
                        <span className=\"font-medium\">{unit.square_feet} sqft</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Price */}
                  <div className=\"flex items-center justify-between pt-4 border-t border-gray-100\">
                    <div>
                      <div className=\"flex items-baseline gap-1\">
                        <span className=\"text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent\">
                          ${unit.rent.toLocaleString()}
                        </span>
                        <span className=\"text-sm text-gray-500\">/mo</span>
                      </div>
                      {unit.available_date && unit.available_date !== 'Immediate' && (
                        <div className=\"flex items-center gap-1 mt-1 text-xs text-gray-500\">
                          <Calendar className=\"w-3 h-3\" />
                          <span>{unit.available_date}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
"}