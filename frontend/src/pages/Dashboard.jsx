import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { API, useAuth } from '../App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Building2, BedDouble, Bath, DollarSign, Heart, LogOut, User, Settings } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [units, setUnits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState(new Set());
  
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
                <Building2 className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900">NoFeesApts.com</h1>
            </div>
            
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/favorites')}
                data-testid="nav-favorites-btn"
              >
                <Heart className="w-5 h-5 mr-2" />
                Favorites
              </Button>
              
              {user?.is_admin && (
                <Button
                  variant="ghost"
                  onClick={() => navigate('/admin')}
                  data-testid="nav-admin-btn"
                >
                  <Settings className="w-5 h-5 mr-2" />
                  Admin
                </Button>
              )}
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" data-testid="user-menu-btn">
                    <User className="w-5 h-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem className="font-medium">{user?.name}</DropdownMenuItem>
                  <DropdownMenuItem className="text-sm text-gray-500">{user?.email}</DropdownMenuItem>
                  <DropdownMenuItem onClick={logout} data-testid="logout-btn">
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
        {/* Filters */}
        <Card className="mb-8 shadow-lg border-0">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Bedrooms</label>
                <Select value={bedrooms || "any"} onValueChange={(val) => setBedrooms(val === "any" ? "" : val)}>
                  <SelectTrigger data-testid="bedrooms-filter">
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="any">Any</SelectItem>
                    <SelectItem value="0">Studio</SelectItem>
                    <SelectItem value="1">1 BR</SelectItem>
                    <SelectItem value="2">2 BR</SelectItem>
                    <SelectItem value="3">3 BR</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Min Rent</label>
                <Input
                  type="number"
                  placeholder="$1,000"
                  value={minRent}
                  onChange={(e) => setMinRent(e.target.value)}
                  data-testid="min-rent-filter"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Max Rent</label>
                <Input
                  type="number"
                  placeholder="$5,000"
                  value={maxRent}
                  onChange={(e) => setMaxRent(e.target.value)}
                  data-testid="max-rent-filter"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Bathrooms</label>
                <Select value={bathrooms || "any"} onValueChange={(val) => setBathrooms(val === "any" ? "" : val)}>
                  <SelectTrigger data-testid="bathrooms-filter">
                    <SelectValue placeholder="Any" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="any">Any</SelectItem>
                    <SelectItem value="1">1 Bath</SelectItem>
                    <SelectItem value="1.5">1.5 Bath</SelectItem>
                    <SelectItem value="2">2 Bath</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {(bedrooms || minRent || maxRent || bathrooms) && (
              <div className="mt-4">
                <Button variant="outline" onClick={clearFilters} data-testid="clear-filters-btn">
                  Clear Filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            Available Apartments <span className="text-gray-500">({units.length})</span>
          </h2>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="text-xl text-gray-600">Loading apartments...</div>
          </div>
        ) : units.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-xl text-gray-600">No apartments found. Try adjusting your filters.</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="units-grid">
            {units.map((unit) => (
              <Card
                key={unit.id}
                className="overflow-hidden hover:shadow-xl transition-all cursor-pointer border-0 shadow-lg"
                onClick={() => navigate(`/unit/${unit.id}`)}
                data-testid={`unit-card-${unit.id}`}
              >
                <div className="relative h-48 bg-gray-200">
                  {unit.images && unit.images.length > 0 ? (
                    <img
                      src={unit.images[0]}
                      alt={`Unit ${unit.unit_number}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-indigo-100 to-purple-100">
                      <Building2 className="w-16 h-16 text-indigo-300" />
                    </div>
                  )}
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleFavorite(unit.id);
                    }}
                    className="absolute top-3 right-3 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-transform"
                    data-testid={`favorite-btn-${unit.id}`}
                  >
                    <Heart
                      className={`w-5 h-5 ${favorites.has(unit.id) ? 'fill-red-500 text-red-500' : 'text-gray-600'}`}
                    />
                  </button>
                  
                  <Badge className="absolute bottom-3 left-3 bg-indigo-600">
                    No Fee
                  </Badge>
                </div>
                
                <CardContent className="p-5">
                  <div className="mb-3">
                    <h3 className="font-semibold text-lg text-gray-900">{unit.building?.name}</h3>
                    <p className="text-sm text-gray-600">{unit.building?.neighborhood}, {unit.building?.city}</p>
                  </div>
                  
                  <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <BedDouble className="w-4 h-4" />
                      <span>{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Bath className="w-4 h-4" />
                      <span>{unit.bathrooms} BA</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1 text-2xl font-bold text-indigo-600">
                      <DollarSign className="w-6 h-6" />
                      <span>{unit.rent.toLocaleString()}</span>
                    </div>
                    <span className="text-sm text-gray-500">/month</span>
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
