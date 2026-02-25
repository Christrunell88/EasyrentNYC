import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../utils/axiosConfig';
import { toast } from 'sonner';
import { API, useAuth } from '../App';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Building2, BedDouble, Bath, DollarSign, Heart } from 'lucide-react';
import SEO from '@/components/SEO';

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
    <div className="min-h-screen bg-white">
      <SEO
        title="My Favorite Apartments"
        description={`View your ${favorites.length} saved no-fee apartments in NYC & NJ. Compare your favorites and schedule viewings. Never lose track of your dream apartment.`}
        keywords="saved apartments, favorite listings, saved searches, apartment wishlist"
        url="/favorites"
      />
      
      {/* Header - Light Theme */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Button
            variant="ghost"
            onClick={() => navigate('/dashboard')}
            data-testid="back-to-dashboard-btn"
            className="text-gray-600 hover:text-amber-600 hover:bg-gray-100"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-amber-500 to-orange-500 bg-clip-text text-transparent mb-2">My Favorites</h1>
          <p className="text-gray-600">Apartments you've saved for later</p>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="text-xl text-amber-600">Loading favorites...</div>
          </div>
        ) : favorites.length === 0 ? (
          <Card className="shadow-lg border border-gray-200 bg-white">
            <CardContent className="p-12 text-center">
              <Heart className="w-16 h-16 text-amber-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">No favorites yet</h3>
              <p className="text-gray-600 mb-6">
                Start exploring apartments and add them to your favorites!
              </p>
              <Button 
                onClick={() => navigate('/dashboard')} 
                data-testid="start-searching-btn"
                className="bg-amber-500 hover:bg-amber-600 text-white font-semibold"
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
                  className="overflow-hidden hover:shadow-xl hover:shadow-amber-100/50 transition-all cursor-pointer border border-gray-200 shadow-md bg-white hover:-translate-y-1"
                  onClick={() => navigate(`/unit/${unit.id}`)}
                  data-testid={`favorite-card-${unit.id}`}
                >
                  <div className="relative h-48 bg-gray-100">
                    {unit.images && unit.images.length > 0 ? (
                      <img
                        src={unit.images[0]}
                        alt={`${unit.bedrooms === 0 ? 'Studio' : unit.bedrooms === 1 ? 'One bedroom' : `${unit.bedrooms} bedroom`} apartment at ${unit.building?.name || 'luxury building'}, ${unit.building?.neighborhood || unit.building?.city || 'NYC'}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
                        <Building2 className="w-16 h-16 text-amber-300" />
                      </div>
                    )}
                    
                    <button
                      onClick={(e) => removeFavorite(unit.id, e)}
                      className="absolute top-3 right-3 w-10 h-10 bg-white/90 rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-transform border border-amber-300"
                      data-testid={`remove-favorite-btn-${unit.id}`}
                    >
                      <Heart className="w-5 h-5 fill-red-500 text-red-500" />
                    </button>
                    
                    <Badge className="absolute bottom-3 left-3 bg-amber-500 text-white font-semibold">
                      No Fee
                    </Badge>
                  </div>
                  
                  <CardContent className="p-5">
                    <div className="mb-3">
                      <h3 className="font-semibold text-lg text-gray-900">{unit.building?.name}</h3>
                      <p className="text-sm text-gray-500">{unit.building?.neighborhood}, {unit.building?.city}</p>
                    </div>
                    
                    <div className="flex items-center gap-4 mb-3 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <BedDouble className="w-4 h-4 text-amber-500" />
                        <span>{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Bath className="w-4 h-4 text-amber-500" />
                        <span>{unit.bathrooms} BA</span>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1 text-2xl font-bold text-amber-600">
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
