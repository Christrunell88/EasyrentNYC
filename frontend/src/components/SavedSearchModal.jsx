import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Bell, BellRing, Trash2, ToggleLeft, ToggleRight, Mail, Smartphone } from 'lucide-react';
import axios from '../utils/axiosConfig';
import { API } from '../App';
import { toast } from 'sonner';

const SavedSearchModal = ({ 
  open, 
  onOpenChange, 
  currentFilters = {},
  onSearchSaved 
}) => {
  const [name, setName] = useState('');
  const [alertFrequency, setAlertFrequency] = useState('daily');
  const [notifyEmail, setNotifyEmail] = useState(true);
  const [notifySms, setNotifySms] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [saving, setSaving] = useState(false);
  const [savedSearches, setSavedSearches] = useState([]);
  const [loadingSearches, setLoadingSearches] = useState(false);
  const [view, setView] = useState('save'); // 'save' or 'manage'
  const [servicesStatus, setServicesStatus] = useState({ sms_service: false });

  useEffect(() => {
    if (open) {
      fetchSavedSearches();
      fetchServicesStatus();
      // Generate default name based on filters
      generateDefaultName();
    }
  }, [open, currentFilters]);

  const fetchServicesStatus = async () => {
    try {
      const response = await axios.get(`${API}/services/status`);
      setServicesStatus(response.data);
    } catch (error) {
      console.error('Error fetching services status:', error);
    }
  };

  const generateDefaultName = () => {
    const parts = [];
    if (currentFilters.bedrooms !== undefined && currentFilters.bedrooms !== '') {
      parts.push(currentFilters.bedrooms === '0' ? 'Studio' : `${currentFilters.bedrooms} Bed`);
    }
    if (currentFilters.state) {
      parts.push(currentFilters.state);
    }
    if (currentFilters.maxRent) {
      parts.push(`Under $${parseInt(currentFilters.maxRent).toLocaleString()}`);
    } else if (currentFilters.minRent) {
      parts.push(`$${parseInt(currentFilters.minRent).toLocaleString()}+`);
    }
    
    if (parts.length > 0) {
      setName(parts.join(' • '));
    } else {
      setName('All No-Fee Apartments');
    }
  };

  const fetchSavedSearches = async () => {
    setLoadingSearches(true);
    try {
      const response = await axios.get(`${API}/saved-searches`, { withCredentials: true });
      setSavedSearches(response.data);
    } catch (error) {
      console.error('Error fetching saved searches:', error);
    } finally {
      setLoadingSearches(false);
    }
  };

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error('Please enter a name for your search');
      return;
    }

    if (notifySms && !phoneNumber.trim()) {
      toast.error('Please enter a phone number for SMS alerts');
      return;
    }

    if (!notifyEmail && !notifySms) {
      toast.error('Please select at least one notification method');
      return;
    }

    setSaving(true);
    try {
      const searchData = {
        name: name.trim(),
        bedrooms: currentFilters.bedrooms !== '' ? parseInt(currentFilters.bedrooms) : null,
        min_rent: currentFilters.minRent ? parseFloat(currentFilters.minRent) : null,
        max_rent: currentFilters.maxRent ? parseFloat(currentFilters.maxRent) : null,
        bathrooms: currentFilters.bathrooms ? parseFloat(currentFilters.bathrooms) : null,
        state: currentFilters.state || null,
        neighborhood: currentFilters.neighborhood || null,
        alert_frequency: alertFrequency,
        notify_email: notifyEmail,
        notify_sms: notifySms,
        phone_number: notifySms ? phoneNumber.trim() : null
      };

      const response = await axios.post(`${API}/saved-searches`, searchData, { withCredentials: true });
      toast.success(response.data.message);
      fetchSavedSearches();
      setView('manage');
      if (onSearchSaved) onSearchSaved();
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to save search';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (searchId) => {
    try {
      await axios.delete(`${API}/saved-searches/${searchId}`, { withCredentials: true });
      toast.success('Search deleted');
      fetchSavedSearches();
    } catch (error) {
      toast.error('Failed to delete search');
    }
  };

  const handleToggle = async (searchId) => {
    try {
      const response = await axios.put(`${API}/saved-searches/${searchId}/toggle`, {}, { withCredentials: true });
      toast.success(response.data.message);
      fetchSavedSearches();
    } catch (error) {
      toast.error('Failed to update search');
    }
  };

  const formatSearchCriteria = (search) => {
    const parts = [];
    if (search.bedrooms !== null) {
      parts.push(search.bedrooms === 0 ? 'Studio' : `${search.bedrooms} Bed`);
    }
    if (search.min_rent && search.max_rent) {
      parts.push(`$${search.min_rent.toLocaleString()}-$${search.max_rent.toLocaleString()}`);
    } else if (search.max_rent) {
      parts.push(`Under $${search.max_rent.toLocaleString()}`);
    } else if (search.min_rent) {
      parts.push(`$${search.min_rent.toLocaleString()}+`);
    }
    if (search.state) parts.push(search.state);
    if (search.neighborhood) parts.push(search.neighborhood);
    
    return parts.length > 0 ? parts.join(' • ') : 'All apartments';
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] bg-white">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-gray-900">
            <Bell className="w-5 h-5 text-amber-500" />
            {view === 'save' ? 'Save Search & Get Alerts' : 'Your Saved Searches'}
          </DialogTitle>
        </DialogHeader>

        {view === 'save' ? (
          <div className="space-y-6 py-4">
            {/* Current search summary */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <p className="text-sm text-amber-800 font-medium mb-2">Current Search Criteria:</p>
              <p className="text-sm text-gray-700">
                {currentFilters.bedrooms !== '' && (
                  <span className="inline-block bg-white px-2 py-1 rounded mr-2 mb-1">
                    {currentFilters.bedrooms === '0' ? 'Studio' : `${currentFilters.bedrooms} Bed`}
                  </span>
                )}
                {currentFilters.state && (
                  <span className="inline-block bg-white px-2 py-1 rounded mr-2 mb-1">
                    {currentFilters.state}
                  </span>
                )}
                {(currentFilters.minRent || currentFilters.maxRent) && (
                  <span className="inline-block bg-white px-2 py-1 rounded mr-2 mb-1">
                    {currentFilters.minRent && currentFilters.maxRent 
                      ? `$${parseInt(currentFilters.minRent).toLocaleString()}-$${parseInt(currentFilters.maxRent).toLocaleString()}`
                      : currentFilters.maxRent 
                        ? `Under $${parseInt(currentFilters.maxRent).toLocaleString()}`
                        : `$${parseInt(currentFilters.minRent).toLocaleString()}+`
                    }
                  </span>
                )}
                {!currentFilters.bedrooms && !currentFilters.state && !currentFilters.minRent && !currentFilters.maxRent && (
                  <span className="text-gray-500">All no-fee apartments</span>
                )}
              </p>
            </div>

            {/* Name input */}
            <div className="space-y-2">
              <Label htmlFor="search-name" className="text-gray-700">Search Name</Label>
              <Input
                id="search-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Manhattan under $4k"
                className="bg-white border-gray-300"
              />
            </div>

            {/* Alert frequency */}
            <div className="space-y-2">
              <Label className="text-gray-700">Alert Frequency</Label>
              <Select value={alertFrequency} onValueChange={setAlertFrequency}>
                <SelectTrigger className="bg-white border-gray-300">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  <SelectItem value="instant">Instant (as they're added)</SelectItem>
                  <SelectItem value="daily">Daily digest</SelectItem>
                  <SelectItem value="weekly">Weekly digest</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Notification methods */}
            <div className="space-y-3">
              <Label className="text-gray-700">How should we notify you?</Label>
              
              <div className="flex items-center space-x-2">
                <Checkbox 
                  id="notify-email" 
                  checked={notifyEmail}
                  onCheckedChange={setNotifyEmail}
                />
                <label htmlFor="notify-email" className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <Mail className="w-4 h-4 text-gray-500" />
                  Email alerts
                </label>
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="notify-sms" 
                    checked={notifySms}
                    onCheckedChange={setNotifySms}
                    disabled={!servicesStatus.sms_service}
                  />
                  <label htmlFor="notify-sms" className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                    <Smartphone className="w-4 h-4 text-gray-500" />
                    SMS alerts
                    {!servicesStatus.sms_service && (
                      <span className="text-xs text-gray-400">(coming soon)</span>
                    )}
                  </label>
                </div>
                
                {notifySms && servicesStatus.sms_service && (
                  <Input
                    type="tel"
                    placeholder="Phone number (e.g., +1 555 123 4567)"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    className="bg-white border-gray-300 mt-2"
                  />
                )}
              </div>
            </div>

            {savedSearches.length > 0 && (
              <Button
                variant="link"
                onClick={() => setView('manage')}
                className="text-amber-600 hover:text-amber-700 p-0 h-auto"
              >
                Manage {savedSearches.length} saved search{savedSearches.length !== 1 ? 'es' : ''} →
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-4 py-4 max-h-[400px] overflow-y-auto">
            {loadingSearches ? (
              <div className="text-center py-8 text-gray-500">Loading...</div>
            ) : savedSearches.length === 0 ? (
              <div className="text-center py-8">
                <BellRing className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No saved searches yet</p>
              </div>
            ) : (
              savedSearches.map((search) => (
                <div 
                  key={search.id} 
                  className={`border rounded-lg p-4 ${search.is_active ? 'border-amber-300 bg-amber-50/50' : 'border-gray-200 bg-gray-50'}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-900 truncate">{search.name}</h4>
                      <p className="text-sm text-gray-500 mt-1">
                        {formatSearchCriteria(search)}
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        Alerts: {search.alert_frequency} • {search.is_active ? 'Active' : 'Paused'}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggle(search.id)}
                        className={`p-2 rounded-lg transition-colors ${
                          search.is_active 
                            ? 'text-amber-600 hover:bg-amber-100' 
                            : 'text-gray-400 hover:bg-gray-100'
                        }`}
                        title={search.is_active ? 'Pause alerts' : 'Enable alerts'}
                      >
                        {search.is_active ? (
                          <ToggleRight className="w-5 h-5" />
                        ) : (
                          <ToggleLeft className="w-5 h-5" />
                        )}
                      </button>
                      <button
                        onClick={() => handleDelete(search.id)}
                        className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete search"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}

            <Button
              variant="link"
              onClick={() => setView('save')}
              className="text-amber-600 hover:text-amber-700 p-0 h-auto"
            >
              ← Save current search
            </Button>
          </div>
        )}

        <DialogFooter>
          {view === 'save' ? (
            <>
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                className="border-gray-300"
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving}
                className="bg-amber-500 hover:bg-amber-600 text-white"
              >
                {saving ? 'Saving...' : 'Save & Enable Alerts'}
              </Button>
            </>
          ) : (
            <Button
              onClick={() => onOpenChange(false)}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700"
            >
              Done
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default SavedSearchModal;
