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
            </div>\n            \n            <div className=\"flex items-center gap-3\">\n              <Button\n                variant=\"ghost\"\n                onClick={() => navigate('/favorites')}\n                className=\"relative\"\n                data-testid=\"nav-favorites-btn\"\n              >\n                <Heart className=\"w-5 h-5\" />\n                {favorites.size > 0 && (\n                  <span className=\"absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center\">\n                    {favorites.size}\n                  </span>\n                )}\n              </Button>\n              \n              {user?.is_admin && (\n                <Button\n                  variant=\"ghost\"\n                  onClick={() => navigate('/admin')}\n                  data-testid=\"nav-admin-btn\"\n                >\n                  <Settings className=\"w-5 h-5\" />\n                </Button>\n              )}\n              \n              <DropdownMenu>\n                <DropdownMenuTrigger asChild>\n                  <Button variant=\"ghost\" size=\"icon\" className=\"rounded-full\" data-testid=\"user-menu-btn\">\n                    <div className=\"w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center\">\n                      <User className=\"w-4 h-4 text-white\" />\n                    </div>\n                  </Button>\n                </DropdownMenuTrigger>\n                <DropdownMenuContent align=\"end\" className=\"w-56\">\n                  <div className=\"px-2 py-2\">\n                    <p className=\"font-medium text-sm\">{user?.name}</p>\n                    <p className=\"text-xs text-gray-500\">{user?.email}</p>\n                  </div>\n                  <DropdownMenuItem onClick={logout} data-testid=\"logout-btn\" className=\"text-red-600\">\n                    <LogOut className=\"w-4 h-4 mr-2\" />\n                    Logout\n                  </DropdownMenuItem>\n                </DropdownMenuContent>\n              </DropdownMenu>\n            </div>\n          </div>\n        </div>\n      </header>\n\n      <div className=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8\">\n        {/* Filter Bar */}\n        <div className=\"mb-8\">\n          <div className=\"flex items-center justify-between mb-4\">\n            <div>\n              <h2 className=\"text-3xl font-bold text-gray-900\">Discover Your Home</h2>\n              <p className=\"text-gray-600 mt-1\">\n                {loading ? 'Loading...' : `${units.length} apartments available`}\n              </p>\n            </div>\n            \n            <Button\n              onClick={() => setShowFilters(!showFilters)}\n              variant=\"outline\"\n              className=\"gap-2\"\n            >\n              <Filter className=\"w-4 h-4\" />\n              Filters\n              {hasActiveFilters && (\n                <Badge className=\"ml-1 bg-blue-600\">Active</Badge>\n              )}\n            </Button>\n          </div>\n\n          {/* Filters Panel */}\n          {showFilters && (\n            <Card className=\"border-0 shadow-lg\">\n              <CardContent className=\"pt-6\">\n                <div className=\"grid grid-cols-1 md:grid-cols-4 gap-4 mb-4\">\n                  <div>\n                    <label className=\"block text-sm font-medium text-gray-700 mb-2\">Bedrooms</label>\n                    <Select value={bedrooms || \"any\"} onValueChange={(val) => setBedrooms(val === \"any\" ? \"\" : val)}>\n                      <SelectTrigger data-testid=\"bedrooms-filter\" className=\"bg-white\">\n                        <SelectValue placeholder=\"Any\" />\n                      </SelectTrigger>\n                      <SelectContent>\n                        <SelectItem value=\"any\">Any</SelectItem>\n                        <SelectItem value=\"0\">Studio</SelectItem>\n                        <SelectItem value=\"1\">1 BR</SelectItem>\n                        <SelectItem value=\"2\">2 BR</SelectItem>\n                        <SelectItem value=\"3\">3 BR</SelectItem>\n                      </SelectContent>\n                    </Select>\n                  </div>\n                  \n                  <div>\n                    <label className=\"block text-sm font-medium text-gray-700 mb-2\">Min Rent</label>\n                    <Input\n                      type=\"number\"\n                      placeholder=\"$1,000\"\n                      value={minRent}\n                      onChange={(e) => setMinRent(e.target.value)}\n                      data-testid=\"min-rent-filter\"\n                      className=\"bg-white\"\n                    />\n                  </div>\n                  \n                  <div>\n                    <label className=\"block text-sm font-medium text-gray-700 mb-2\">Max Rent</label>\n                    <Input\n                      type=\"number\"\n                      placeholder=\"$5,000\"\n                      value={maxRent}\n                      onChange={(e) => setMaxRent(e.target.value)}\n                      data-testid=\"max-rent-filter\"\n                      className=\"bg-white\"\n                    />\n                  </div>\n                  \n                  <div>\n                    <label className=\"block text-sm font-medium text-gray-700 mb-2\">Bathrooms</label>\n                    <Select value={bathrooms || \"any\"} onValueChange={(val) => setBathrooms(val === \"any\" ? \"\" : val)}>\n                      <SelectTrigger data-testid=\"bathrooms-filter\" className=\"bg-white\">\n                        <SelectValue placeholder=\"Any\" />\n                      </SelectTrigger>\n                      <SelectContent>\n                        <SelectItem value=\"any\">Any</SelectItem>\n                        <SelectItem value=\"1\">1 Bath</SelectItem>\n                        <SelectItem value=\"1.5\">1.5 Bath</SelectItem>\n                        <SelectItem value=\"2\">2 Bath</SelectItem>\n                      </SelectContent>\n                    </Select>\n                  </div>\n                </div>\n                \n                {hasActiveFilters && (\n                  <Button variant=\"ghost\" onClick={clearFilters} data-testid=\"clear-filters-btn\" className=\"gap-2\">\n                    <X className=\"w-4 h-4\" />\n                    Clear All Filters\n                  </Button>\n                )}\n              </CardContent>\n            </Card>\n          )}\n        </div>\n\n        {/* Apartments Grid */}\n        {loading ? (\n          <div className=\"text-center py-20\">\n            <div className=\"inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4\"></div>\n            <p className=\"text-gray-600\">Loading apartments...</p>\n          </div>\n        ) : units.length === 0 ? (\n          <div className=\"text-center py-20\">\n            <div className=\"text-6xl mb-4\">🏠</div>\n            <h3 className=\"text-2xl font-bold text-gray-900 mb-2\">No apartments found</h3>\n            <p className=\"text-gray-600 mb-6\">Try adjusting your filters</p>\n            {hasActiveFilters && (\n              <Button onClick={clearFilters} variant=\"outline\">Clear Filters</Button>\n            )}\n          </div>\n        ) : (\n          <div className=\"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6\" data-testid=\"units-grid\">\n            {units.map((unit) => (\n              <Card\n                key={unit.id}\n                className=\"group overflow-hidden hover:shadow-2xl transition-all duration-500 cursor-pointer border-0 shadow-lg bg-white\"\n                onClick={() => navigate(`/unit/${unit.id}`)}\n                data-testid={`unit-card-${unit.id}`}\n              >\n                <div className=\"relative h-56 bg-gradient-to-br from-blue-100 to-indigo-100 overflow-hidden\">\n                  {unit.images && unit.images.length > 0 ? (\n                    <img\n                      src={unit.images[0]}\n                      alt={`Unit ${unit.unit_number}`}\n                      className=\"w-full h-full object-cover group-hover:scale-110 transition-transform duration-700\"\n                    />\n                  ) : (\n                    <div className=\"w-full h-full flex items-center justify-center\">\n                      <Building2 className=\"w-20 h-20 text-indigo-300\" />\n                    </div>\n                  )}\n                  \n                  {/* Favorite Button */}\n                  <button\n                    onClick={(e) => toggleFavorite(unit.id, e)}\n                    className=\"absolute top-3 right-3 w-10 h-10 bg-white/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-transform duration-300 z-10\"\n                    data-testid={`favorite-btn-${unit.id}`}\n                  >\n                    <Heart\n                      className={`w-5 h-5 transition-colors ${\n                        favorites.has(unit.id)\n                          ? 'fill-red-500 text-red-500'\n                          : 'text-gray-600 hover:text-red-500'\n                      }`}\n                    />\n                  </button>\n                  \n                  {/* No Fee Badge */}\n                  <div className=\"absolute bottom-3 left-3\">\n                    <Badge className=\"bg-emerald-500 text-white border-0 shadow-lg\">\n                      No Fee\n                    </Badge>\n                  </div>\n\n                  {/* Overlay Gradient */}\n                  <div className=\"absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500\"></div>\n                </div>\n                \n                <CardContent className=\"p-5\">\n                  <div className=\"mb-3\">\n                    <h3 className=\"font-bold text-lg text-gray-900 mb-1 group-hover:text-blue-600 transition-colors\">\n                      {unit.building?.name}\n                    </h3>\n                    <div className=\"flex items-center gap-1 text-sm text-gray-600\">\n                      <MapPin className=\"w-3 h-3\" />\n                      <span>{unit.building?.neighborhood}, {unit.building?.city}</span>\n                    </div>\n                  </div>\n                  \n                  {/* Features */}\n                  <div className=\"flex items-center gap-4 mb-4 text-sm text-gray-700\">\n                    <div className=\"flex items-center gap-1.5\">\n                      <div className=\"w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center\">\n                        <BedDouble className=\"w-4 h-4 text-blue-600\" />\n                      </div>\n                      <span className=\"font-medium\">\n                        {unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`}\n                      </span>\n                    </div>\n                    <div className=\"flex items-center gap-1.5\">\n                      <div className=\"w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center\">\n                        <Bath className=\"w-4 h-4 text-indigo-600\" />\n                      </div>\n                      <span className=\"font-medium\">{unit.bathrooms} BA</span>\n                    </div>\n                    {unit.square_feet && (\n                      <div className=\"flex items-center gap-1.5\">\n                        <div className=\"w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center\">\n                          <Maximize2 className=\"w-4 h-4 text-purple-600\" />\n                        </div>\n                        <span className=\"font-medium\">{unit.square_feet} sqft</span>\n                      </div>\n                    )}\n                  </div>\n                  \n                  {/* Price */}\n                  <div className=\"flex items-center justify-between pt-4 border-t border-gray-100\">\n                    <div>\n                      <div className=\"flex items-baseline gap-1\">\n                        <span className=\"text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent\">\n                          ${unit.rent.toLocaleString()}\n                        </span>\n                        <span className=\"text-sm text-gray-500\">/mo</span>\n                      </div>\n                      {unit.available_date && unit.available_date !== 'Immediate' && (\n                        <div className=\"flex items-center gap-1 mt-1 text-xs text-gray-500\">\n                          <Calendar className=\"w-3 h-3\" />\n                          <span>{unit.available_date}</span>\n                        </div>\n                      )}\n                    </div>\n                  </div>\n                </CardContent>\n              </Card>\n            ))}\n          </div>\n        )}\n      </div>\n    </div>\n  );\n};\n\nexport default Dashboard;\n"}