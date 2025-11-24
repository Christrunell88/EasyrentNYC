import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { API, useAuth } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Building2, BedDouble, Bath, DollarSign, Heart } from 'lucide-react';

const Favorites = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      const response = await axios.get(`${API}/favorites`, { withCredentials: true });
      setFavorites(response.data);
    } catch (error) {
      console.error('Error fetching favorites:', error);
      toast.error('Failed to load favorites');
    } finally {
      setLoading(false);
    }
  };

  const removeFavorite = async (unitId, e) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API}/favorites/${unitId}`, { withCredentials: true });
      setFavorites(favorites.filter(f => f.unit.id !== unitId));
      toast.success('Removed from favorites');
    } catch (error) {
      toast.error('Failed to remove favorite');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/90 backdrop-blur-sm border-b border-amber-500/20 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            data-testid="back-to-dashboard-btn"
            className="text-slate-200 hover:text-amber-500"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold warm-gradient-text mb-2">My Favorites</h1>
          <p className="text-slate-300">Apartments you've saved for later</p>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="text-xl text-slate-300">Loading favorites...</div>
          </div>
        ) : favorites.length === 0 ? (
          <Card className="shadow-2xl border border-amber-500/20 bg-slate-800/90 backdrop-blur-sm">
            <CardContent className="p-12 text-center">
              <Heart className="w-16 h-16 text-amber-500/30 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-100 mb-2">No favorites yet</h3>
              <p className="text-slate-300 mb-6">
                Start exploring apartments and add them to your favorites!
              </p>
              <Button 
                onClick={() => navigate('/dashboard')} 
                data-testid="start-searching-btn"
                className="warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold"
              >
                Start Searching
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="favorites-grid">
            {favorites.map((favorite) => {
              const unit = favorite.unit;
              return (
                <Card
                  key={unit.id}
                  className="overflow-hidden hover:shadow-xl transition-all cursor-pointer border-0 shadow-lg"
                  onClick={() => navigate(`/unit/${unit.id}`)}
                  data-testid={`favorite-card-${unit.id}`}
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
                      onClick={(e) => removeFavorite(unit.id, e)}
                      className="absolute top-3 right-3 w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-transform"
                      data-testid={`remove-favorite-btn-${unit.id}`}
                    >
                      <Heart className="w-5 h-5 fill-red-500 text-red-500" />
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
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Favorites;
