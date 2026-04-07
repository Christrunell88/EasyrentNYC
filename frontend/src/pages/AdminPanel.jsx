import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../utils/axiosConfig';
import { useAuth, API } from '../App';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import {
  Building2, Home, Plus, Trash2, RefreshCw, Users,
  MapPin, BedDouble, Bath, Maximize, Download, ChevronLeft, ChevronRight,
  LogIn, Mail
} from 'lucide-react';

// Extracted tab components
import ImportTab from '../components/admin/ImportTab';
import StagingTab from '../components/admin/StagingTab';
import UnavailabilityTab from '../components/admin/UnavailabilityTab';
import RentedTab from '../components/admin/RentedTab';
import RejectedTab from '../components/admin/RejectedTab';

const AdminPanel = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // Shared data state
  const [buildings, setBuildings] = useState([]);
  const [units, setUnits] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  // Badge count state (updated by child components)
  const [stagingStats, setStagingStats] = useState({ pending: 0 });
  const [unavailStats, setUnavailStats] = useState({ pending: 0 });

  // Admin data state
  const [users, setUsers] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [subscribers, setSubscribers] = useState([]);

  // Units pagination
  const [unitsPage, setUnitsPage] = useState(1);
  const unitsPerPage = 50;

  // Production unit selection
  const [selectedProductionUnits, setSelectedProductionUnits] = useState(new Set());
  const [bulkDeletingProduction, setBulkDeletingProduction] = useState(false);

  // Dialog state
  const [buildingDialogOpen, setBuildingDialogOpen] = useState(false);
  const [unitDialogOpen, setUnitDialogOpen] = useState(false);
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    if (!user?.is_admin) { navigate('/'); return; }
    fetchData();
    fetchStats();
    fetchUsers();
    fetchContacts();
    fetchSubscribers();
  }, [user, navigate]);

  const fetchData = useCallback(async () => {
    try {
      const [buildingsRes, unitsRes] = await Promise.all([
        axios.get(`${API}/buildings`, { withCredentials: true }),
        axios.get(`${API}/units?limit=500`, { withCredentials: true })
      ]);
      setBuildings(buildingsRes.data);
      const unitsData = Array.isArray(unitsRes.data) ? unitsRes.data : (unitsRes.data.units || []);
      setUnits(unitsData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats`, { withCredentials: true });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`, { withCredentials: true });
      setUsers(response.data);
    } catch (error) { console.error('Error fetching users:', error); }
  };

  const fetchContacts = async () => {
    try {
      const response = await axios.get(`${API}/contact-requests`, { withCredentials: true });
      setContacts(Array.isArray(response.data) ? response.data : []);
    } catch (error) { console.error('Error fetching contacts:', error); }
  };

  const fetchSubscribers = async () => {
    try {
      const response = await axios.get(`${API}/admin/subscribers`, { withCredentials: true });
      setSubscribers(Array.isArray(response.data) ? response.data : response.data.subscribers || []);
    } catch (error) { console.error('Error fetching subscribers:', error); }
  };

  const exportToCSV = () => {
    const headers = ['Building Name', 'Address', 'Neighborhood', 'City', 'State', 'Zip', 'Unit #', 'Rent', 'Bedrooms', 'Bathrooms', 'Sq Ft', 'Available', 'Contact Email', 'Contact Phone'];
    const rows = units.map(unit => {
      const building = buildings.find(b => b.id === unit.building_id) || {};
      return [building.name, building.address, building.neighborhood, building.city, building.state, building.zip_code, unit.unit_number, unit.rent, unit.bedrooms, unit.bathrooms, unit.square_feet || 'N/A', unit.is_available ? 'Yes' : 'No', 'placesfirm@gmail.com', '646-408-8048'].map(field => `"${(field || '').toString().replace(/"/g, '""')}"`).join(',');
    });
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `nofeesapts_inventory_${new Date().toISOString().split('T')[0]}.csv`; a.click(); URL.revokeObjectURL(url);
    toast.success('CSV exported successfully!');
  };

  const handleAddBuilding = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    try {
      await axios.post(`${API}/buildings`, data, { withCredentials: true });
      toast.success('Building added!');
      setBuildingDialogOpen(false);
      e.target.reset();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add building');
    }
  };

  const handleAddUnit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      building_id: formData.get('building_id'),
      unit_number: formData.get('unit_number'),
      rent: parseInt(formData.get('rent')),
      bedrooms: parseInt(formData.get('bedrooms')),
      bathrooms: parseFloat(formData.get('bathrooms')),
      square_feet: formData.get('square_feet') ? parseInt(formData.get('square_feet')) : null,
      available_date: formData.get('available_date') || 'Immediate',
      amenities: formData.get('amenities')?.split(',').map(s => s.trim()).filter(Boolean) || [],
      images: formData.get('images')?.split(',').map(s => s.trim()).filter(Boolean) || [],
      description: formData.get('description') || ''
    };
    try {
      await axios.post(`${API}/units`, data, { withCredentials: true });
      toast.success('Unit added!');
      setUnitDialogOpen(false);
      e.target.reset();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add unit');
    }
  };

  const handleDeleteBuilding = async (id) => {
    if (!confirm('Delete this building and all its units?')) return;
    try {
      await axios.delete(`${API}/buildings/${id}`, { withCredentials: true });
      toast.success('Building deleted');
      fetchData();
    } catch (error) { toast.error('Failed to delete building'); }
  };

  const handleDeleteUnit = async (id) => {
    if (!confirm('Delete this unit?')) return;
    try {
      await axios.delete(`${API}/units/${id}`, { withCredentials: true });
      toast.success('Unit deleted');
      fetchData();
    } catch (error) { toast.error('Failed to delete unit'); }
  };

  const handleCrawlBuilding = async (id) => {
    try {
      toast.info('Crawling building...');
      await axios.post(`${API}/admin/crawl/${id}`, {}, { withCredentials: true });
      toast.success('Crawl complete!');
      fetchData();
    } catch (error) { toast.error('Crawl failed'); }
  };

  const toggleProductionSelection = (unitId) => {
    setSelectedProductionUnits(prev => {
      const newSet = new Set(prev);
      if (newSet.has(unitId)) newSet.delete(unitId);
      else newSet.add(unitId);
      return newSet;
    });
  };

  const handleBulkDeleteProduction = async () => {
    if (selectedProductionUnits.size === 0) return;
    if (!confirm(`Delete ${selectedProductionUnits.size} production unit(s)? This cannot be undone.`)) return;
    setBulkDeletingProduction(true);
    try {
      const ids = Array.from(selectedProductionUnits);
      await axios.post(`${API}/admin/units/bulk-delete`, { ids }, { withCredentials: true });
      toast.success(`${ids.length} unit(s) deleted`);
      setSelectedProductionUnits(new Set());
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete units');
    } finally {
      setBulkDeletingProduction(false);
    }
  };

  const handleResetPassword = async () => {
    if (!selectedUser || newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    try {
      await axios.post(`${API}/admin/reset-password`, {
        user_id: selectedUser.id, new_password: newPassword
      }, { withCredentials: true });
      toast.success(`Password reset for ${selectedUser.email}`);
      setResetPasswordDialogOpen(false);
      setSelectedUser(null);
      setNewPassword('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <RefreshCw className="w-8 h-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6" data-testid="admin-panel">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold warm-gradient-text">Admin Panel</h1>
            <p className="text-slate-400">NoFeesApts.com Management Dashboard</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => { fetchStats(); fetchData(); }} variant="outline" className="border-amber-500/30 text-amber-500 hover:bg-amber-500/10">
              <RefreshCw className="w-4 h-4 mr-2" /> Refresh Stats
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card className="shadow-xl bg-slate-800/50 backdrop-blur-sm border border-amber-500/20">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Buildings</p>
                  <p className="text-3xl font-bold warm-gradient-text">{stats.total_buildings || buildings.length}</p>
                </div>
                <Building2 className="w-12 h-12 text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-xl bg-slate-800/50 backdrop-blur-sm border border-amber-500/20">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Total Units</p>
                  <p className="text-3xl font-bold warm-gradient-text">{stats.total_units || units.length}</p>
                </div>
                <Home className="w-12 h-12 text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-xl bg-slate-800/50 backdrop-blur-sm border border-amber-500/20">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Available Units</p>
                  <p className="text-3xl font-bold warm-gradient-text">{stats.available_units || units.filter(u => u.is_available).length}</p>
                </div>
                <Badge className="warm-gradient text-slate-900 text-lg px-4 py-2">Active</Badge>
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-xl bg-slate-800/50 backdrop-blur-sm border border-amber-500/20">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Total Users</p>
                  <p className="text-3xl font-bold warm-gradient-text">{stats.total_users || users.length}</p>
                </div>
                <Users className="w-12 h-12 text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="shadow-xl bg-slate-800/50 backdrop-blur-sm border border-emerald-500/20">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Subscribers</p>
                  <p className="text-3xl font-bold text-emerald-400">{stats.total_subscribers || 0}</p>
                </div>
                <Mail className="w-12 h-12 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Card className="shadow-xl bg-slate-800/50 backdrop-blur-sm border border-amber-500/20">
          <Tabs defaultValue="dashboard" className="w-full">
            <CardHeader>
              <TabsList className="grid w-full grid-cols-12 bg-slate-700/50">
                <TabsTrigger value="import" data-testid="import-tab" className="data-[state=active]:bg-green-600 data-[state=active]:text-white col-span-1">
                  <Plus className="w-4 h-4 mr-1" /> Import
                </TabsTrigger>
                <TabsTrigger value="dashboard" data-testid="dashboard-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">All Units</TabsTrigger>
                <TabsTrigger value="staging" data-testid="staging-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500 relative">
                  Staging
                  {stagingStats.pending > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {stagingStats.pending > 99 ? '99+' : stagingStats.pending}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="unavailability" data-testid="unavailability-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-orange-400 relative">
                  Unavail
                  {unavailStats.pending > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-orange-500 text-white text-xs rounded-full flex items-center justify-center">
                      {unavailStats.pending > 99 ? '99+' : unavailStats.pending}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="directory" data-testid="directory-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Directory</TabsTrigger>
                <TabsTrigger value="buildings" data-testid="buildings-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Buildings</TabsTrigger>
                <TabsTrigger value="units" data-testid="units-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Units</TabsTrigger>
                <TabsTrigger value="rented" data-testid="rented-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-purple-400">Rented</TabsTrigger>
                <TabsTrigger value="rejected" data-testid="rejected-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-red-400">Rejected</TabsTrigger>
                <TabsTrigger value="users" data-testid="users-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Users</TabsTrigger>
                <TabsTrigger value="contacts" data-testid="contacts-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Contacts</TabsTrigger>
                <TabsTrigger value="subscribers" data-testid="subscribers-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-emerald-500">Subscribers</TabsTrigger>
              </TabsList>
            </CardHeader>

            <CardContent>
              {/* Import Tab (Extracted Component) */}
              <TabsContent value="import">
                <ImportTab fetchStagingStats={() => {}} />
              </TabsContent>

              {/* Dashboard Tab */}
              <TabsContent value="dashboard">
                <div className="space-y-6">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-100">Complete Unit Inventory</h3>
                      <p className="text-sm text-slate-400">All apartments with full details, pricing, and contact information</p>
                    </div>
                    <Button onClick={exportToCSV} className="warm-gradient text-slate-900 font-semibold" data-testid="export-units-csv-btn">
                      <Download className="w-4 h-4 mr-2" /> Export All Units
                    </Button>
                  </div>

                  <div className="bg-gradient-to-r from-amber-900/30 to-orange-900/30 border border-amber-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full warm-gradient flex items-center justify-center">
                        <MapPin className="w-6 h-6 text-slate-900" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-amber-400 mb-1">Master Contact Information</h4>
                        <div className="flex gap-6 text-slate-300 text-sm">
                          <span>placesfirm@gmail.com</span>
                          <span>646-408-8048</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    {selectedProductionUnits.size > 0 && (
                      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4 flex items-center justify-between">
                        <span className="text-red-400 font-medium">{selectedProductionUnits.size} approved unit(s) selected</span>
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm" onClick={() => setSelectedProductionUnits(new Set())} className="border-slate-600 text-slate-300 hover:bg-slate-700">Clear Selection</Button>
                          <Button variant="destructive" size="sm" onClick={handleBulkDeleteProduction} disabled={bulkDeletingProduction} className="bg-red-600 hover:bg-red-700">
                            <Trash2 className="w-4 h-4 mr-1" />
                            {bulkDeletingProduction ? 'Deleting...' : `Delete ${selectedProductionUnits.size} Unit(s)`}
                          </Button>
                        </div>
                      </div>
                    )}
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="w-12">
                            <Checkbox checked={units.length > 0 && selectedProductionUnits.size === units.length} onCheckedChange={() => {
                              if (selectedProductionUnits.size === units.length) setSelectedProductionUnits(new Set());
                              else setSelectedProductionUnits(new Set(units.map(u => u.id)));
                            }} className="border-slate-500" />
                          </TableHead>
                          <TableHead className="text-slate-300">Building</TableHead>
                          <TableHead className="text-slate-300">Address</TableHead>
                          <TableHead className="text-slate-300">Unit #</TableHead>
                          <TableHead className="text-slate-300">Price</TableHead>
                          <TableHead className="text-slate-300">Beds</TableHead>
                          <TableHead className="text-slate-300">Baths</TableHead>
                          <TableHead className="text-slate-300">Size</TableHead>
                          <TableHead className="text-slate-300">Neighborhood</TableHead>
                          <TableHead className="text-slate-300">Available</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {units.map((unit) => {
                          const building = buildings.find(b => b.id === unit.building_id);
                          return (
                            <TableRow key={unit.id} className={`border-slate-700 hover:bg-slate-700/30 ${selectedProductionUnits.has(unit.id) ? 'bg-red-500/10' : ''}`}>
                              <TableCell><Checkbox checked={selectedProductionUnits.has(unit.id)} onCheckedChange={() => toggleProductionSelection(unit.id)} className="border-slate-500" /></TableCell>
                              <TableCell className="font-medium text-slate-100">{building?.name || 'Unknown'}</TableCell>
                              <TableCell className="text-slate-300 text-sm">{building?.address}, {building?.city}, {building?.state}</TableCell>
                              <TableCell className="text-slate-300 font-mono">{unit.unit_number}</TableCell>
                              <TableCell className="text-amber-500 font-bold">${unit.rent?.toLocaleString()}</TableCell>
                              <TableCell className="text-slate-300"><div className="flex items-center gap-1"><BedDouble className="w-4 h-4" />{unit.bedrooms === 0 ? 'Studio' : unit.bedrooms}</div></TableCell>
                              <TableCell className="text-slate-300"><div className="flex items-center gap-1"><Bath className="w-4 h-4" />{unit.bathrooms}</div></TableCell>
                              <TableCell className="text-slate-300"><div className="flex items-center gap-1"><Maximize className="w-4 h-4" />{unit.square_feet || 'N/A'}</div></TableCell>
                              <TableCell className="text-slate-400 text-sm">{building?.neighborhood}</TableCell>
                              <TableCell><Badge className={unit.is_available ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}>{unit.is_available ? 'Yes' : 'No'}</Badge></TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>

                  <div className="grid grid-cols-4 gap-4 mt-6">
                    {[{ label: 'Studios', filter: u => u.bedrooms === 0 }, { label: '1 Bedrooms', filter: u => u.bedrooms === 1 }, { label: '2 Bedrooms', filter: u => u.bedrooms === 2 }].map(({ label, filter }) => (
                      <Card key={label} className="bg-slate-700/50 border-slate-600">
                        <CardContent className="p-4 text-center">
                          <p className="text-2xl font-bold warm-gradient-text">{units.filter(filter).length}</p>
                          <p className="text-xs text-slate-400">{label}</p>
                        </CardContent>
                      </Card>
                    ))}
                    <Card className="bg-slate-700/50 border-slate-600">
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold warm-gradient-text">
                          ${units.length > 0 ? Math.round(units.reduce((sum, u) => sum + (u.rent || 0), 0) / units.length).toLocaleString() : 0}
                        </p>
                        <p className="text-xs text-slate-400">Avg Rent</p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </TabsContent>

              {/* Staging Tab (Extracted Component) */}
              <TabsContent value="staging">
                <StagingTab buildings={buildings} fetchData={fetchData} onStatsUpdate={setStagingStats} />
              </TabsContent>

              {/* Unavailability Tab (Extracted Component) */}
              <TabsContent value="unavailability">
                <UnavailabilityTab fetchData={fetchData} onStatsUpdate={setUnavailStats} />
              </TabsContent>

              {/* Directory Tab */}
              <TabsContent value="directory">
                <div className="space-y-6">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-100">Complete Building Directory</h3>
                      <p className="text-sm text-slate-400">All building addresses and contact information for export</p>
                    </div>
                    <Button onClick={exportToCSV} className="warm-gradient text-slate-900 font-semibold" data-testid="export-csv-btn">Export to CSV</Button>
                  </div>
                  <div className="bg-slate-700/50 border border-amber-500/20 rounded-lg p-4 mb-4">
                    <h4 className="font-semibold text-amber-500 mb-2">Contact Information</h4>
                    <div className="space-y-1 text-slate-300">
                      <p>Email: <span className="text-amber-400 font-medium">placesfirm@gmail.com</span></p>
                      <p>Phone: <span className="text-amber-400 font-medium">646-408-8048</span></p>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="text-slate-300">Building Name</TableHead>
                          <TableHead className="text-slate-300">Full Address</TableHead>
                          <TableHead className="text-slate-300">Neighborhood</TableHead>
                          <TableHead className="text-slate-300">City, State</TableHead>
                          <TableHead className="text-slate-300">Zip</TableHead>
                          <TableHead className="text-slate-300">Total Units</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {buildings.map((building) => (
                          <TableRow key={building.id} className="border-slate-700">
                            <TableCell className="font-medium text-slate-100">{building.name}</TableCell>
                            <TableCell className="text-slate-300">{building.address}</TableCell>
                            <TableCell className="text-slate-300">{building.neighborhood}</TableCell>
                            <TableCell className="text-slate-300">{building.city}, {building.state}</TableCell>
                            <TableCell className="text-slate-300">{building.zip_code}</TableCell>
                            <TableCell className="text-amber-500 font-semibold">{units.filter(u => u.building_id === building.id).length}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </TabsContent>

              {/* Buildings Tab */}
              <TabsContent value="buildings">
                <div className="mb-4">
                  <Dialog open={buildingDialogOpen} onOpenChange={setBuildingDialogOpen}>
                    <DialogTrigger asChild>
                      <Button data-testid="add-building-btn"><Plus className="w-4 h-4 mr-2" />Add Building</Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Add New Building</DialogTitle>
                        <DialogDescription>Enter building details to add to the platform</DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleAddBuilding} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div><Label htmlFor="name">Building Name</Label><Input id="name" name="name" required data-testid="building-name-input" /></div>
                          <div><Label htmlFor="address">Address</Label><Input id="address" name="address" required data-testid="building-address-input" /></div>
                          <div><Label htmlFor="neighborhood">Neighborhood</Label><Input id="neighborhood" name="neighborhood" required data-testid="building-neighborhood-input" /></div>
                          <div><Label htmlFor="city">City</Label><Input id="city" name="city" required data-testid="building-city-input" /></div>
                          <div><Label htmlFor="state">State</Label><Input id="state" name="state" placeholder="NY" required data-testid="building-state-input" /></div>
                          <div><Label htmlFor="zip_code">Zip Code</Label><Input id="zip_code" name="zip_code" required data-testid="building-zip-input" /></div>
                        </div>
                        <div><Label htmlFor="source_url">Source URL</Label><Input id="source_url" name="source_url" type="url" required data-testid="building-url-input" /></div>
                        <Button type="submit" className="w-full" data-testid="building-submit-btn">Add Building</Button>
                      </form>
                    </DialogContent>
                  </Dialog>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700">
                      <TableHead className="text-slate-300">Name</TableHead>
                      <TableHead className="text-slate-300">Address</TableHead>
                      <TableHead className="text-slate-300">City</TableHead>
                      <TableHead className="text-slate-300">Last Crawled</TableHead>
                      <TableHead className="text-slate-300">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {buildings.map((building) => (
                      <TableRow key={building.id} className="border-slate-700">
                        <TableCell className="font-medium text-slate-100">{building.name}</TableCell>
                        <TableCell className="text-slate-300">{building.address}</TableCell>
                        <TableCell className="text-slate-300">{building.city}, {building.state}</TableCell>
                        <TableCell className="text-slate-300">{building.last_crawled ? new Date(building.last_crawled).toLocaleDateString() : 'Never'}</TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline" onClick={() => handleCrawlBuilding(building.id)} data-testid={`crawl-building-${building.id}`} className="border-amber-500/30 text-amber-500 hover:bg-slate-700"><RefreshCw className="w-4 h-4" /></Button>
                            <Button size="sm" variant="destructive" onClick={() => handleDeleteBuilding(building.id)} data-testid={`delete-building-${building.id}`} className="bg-red-900/50 hover:bg-red-900"><Trash2 className="w-4 h-4" /></Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TabsContent>

              {/* Units Tab */}
              <TabsContent value="units">
                <div className="mb-4">
                  <Dialog open={unitDialogOpen} onOpenChange={setUnitDialogOpen}>
                    <DialogTrigger asChild>
                      <Button data-testid="add-unit-btn"><Plus className="w-4 h-4 mr-2" />Add Unit</Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Add New Unit</DialogTitle>
                        <DialogDescription>Enter unit details</DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleAddUnit} className="space-y-4">
                        <div>
                          <Label htmlFor="building_id">Building</Label>
                          <select id="building_id" name="building_id" required className="w-full px-3 py-2 border rounded-md" data-testid="unit-building-select">
                            <option value="">Select building...</option>
                            {buildings.map(b => (<option key={b.id} value={b.id}>{b.name}</option>))}
                          </select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div><Label>Unit Number</Label><Input name="unit_number" required data-testid="unit-number-input" /></div>
                          <div><Label>Rent ($)</Label><Input name="rent" type="number" required data-testid="unit-rent-input" /></div>
                          <div><Label>Bedrooms (0 = Studio)</Label><Input name="bedrooms" type="number" min="0" required data-testid="unit-bedrooms-input" /></div>
                          <div><Label>Bathrooms</Label><Input name="bathrooms" type="number" step="0.5" required data-testid="unit-bathrooms-input" /></div>
                          <div><Label>Square Feet</Label><Input name="square_feet" type="number" data-testid="unit-sqft-input" /></div>
                          <div><Label>Available Date</Label><Input name="available_date" placeholder="Immediate" data-testid="unit-date-input" /></div>
                        </div>
                        <div><Label>Amenities (comma-separated)</Label><Input name="amenities" placeholder="Gym, Pool, Parking" data-testid="unit-amenities-input" /></div>
                        <div><Label>Image URLs (comma-separated)</Label><Input name="images" data-testid="unit-images-input" /></div>
                        <div><Label>Description</Label><Input name="description" data-testid="unit-description-input" /></div>
                        <Button type="submit" className="w-full" data-testid="unit-submit-btn">Add Unit</Button>
                      </form>
                    </DialogContent>
                  </Dialog>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Building</TableHead>
                      <TableHead>Unit #</TableHead>
                      <TableHead>BR/BA</TableHead>
                      <TableHead>Rent</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {units.slice((unitsPage - 1) * unitsPerPage, unitsPage * unitsPerPage).map((unit) => (
                      <TableRow key={unit.id}>
                        <TableCell>{unit.building?.name}</TableCell>
                        <TableCell>{unit.unit_number}</TableCell>
                        <TableCell>{unit.bedrooms}BR / {unit.bathrooms}BA</TableCell>
                        <TableCell>${unit.rent?.toLocaleString()}</TableCell>
                        <TableCell><Button size="sm" variant="destructive" onClick={() => handleDeleteUnit(unit.id)} data-testid={`delete-unit-${unit.id}`}><Trash2 className="w-4 h-4" /></Button></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="flex items-center justify-between mt-4 px-2">
                  <p className="text-sm text-gray-400">Showing {((unitsPage - 1) * unitsPerPage) + 1} - {Math.min(unitsPage * unitsPerPage, units.length)} of {units.length} units</p>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => setUnitsPage(p => Math.max(1, p - 1))} disabled={unitsPage === 1}><ChevronLeft className="w-4 h-4" />Previous</Button>
                    <span className="text-sm px-3">Page {unitsPage} of {Math.ceil(units.length / unitsPerPage)}</span>
                    <Button variant="outline" size="sm" onClick={() => setUnitsPage(p => Math.min(Math.ceil(units.length / unitsPerPage), p + 1))} disabled={unitsPage >= Math.ceil(units.length / unitsPerPage)}>Next<ChevronRight className="w-4 h-4" /></Button>
                  </div>
                </div>
              </TabsContent>

              {/* Rented Tab (Extracted Component) */}
              <TabsContent value="rented">
                <RentedTab fetchData={fetchData} />
              </TabsContent>

              {/* Rejected Tab (Extracted Component) */}
              <TabsContent value="rejected">
                <RejectedTab fetchData={fetchData} />
              </TabsContent>

              {/* Users Tab */}
              <TabsContent value="users">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Admin</TableHead>
                      <TableHead>Joined</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell className="font-medium">{user.name}</TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>{user.is_admin && <Badge>Admin</Badge>}</TableCell>
                        <TableCell>{user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</TableCell>
                        <TableCell>
                          <Button size="sm" onClick={() => { setSelectedUser(user); setResetPasswordDialogOpen(true); }} className="bg-amber-600 hover:bg-amber-700 text-white">
                            <LogIn className="w-4 h-4 mr-1" /> Reset Password
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TabsContent>

              {/* Contacts Tab */}
              <TabsContent value="contacts">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Phone</TableHead>
                      <TableHead>Message</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {contacts.map((contact) => (
                      <TableRow key={contact.id}>
                        <TableCell className="font-medium">{contact.name}</TableCell>
                        <TableCell>{contact.email}</TableCell>
                        <TableCell>{contact.phone || 'N/A'}</TableCell>
                        <TableCell className="max-w-xs truncate">{contact.message}</TableCell>
                        <TableCell>{new Date(contact.created_at).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TabsContent>

              {/* Subscribers Tab */}
              <TabsContent value="subscribers">
                <div className="space-y-4">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-100">Email Subscribers</h3>
                      <p className="text-sm text-slate-400">Users who signed up for apartment updates</p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-3 py-1">{subscribers.length} subscribers</Badge>
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Email</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Subscribed Date</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {subscribers.map((subscriber) => (
                        <TableRow key={subscriber.id}>
                          <TableCell className="font-medium"><div className="flex items-center gap-2"><Mail className="w-4 h-4 text-emerald-500" />{subscriber.email}</div></TableCell>
                          <TableCell><Badge variant="outline" className="text-slate-300 border-slate-600">{subscriber.source || 'landing_page'}</Badge></TableCell>
                          <TableCell>{subscriber.active ? <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge> : <Badge className="bg-red-500/20 text-red-400">Inactive</Badge>}</TableCell>
                          <TableCell>{new Date(subscriber.subscribed_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</TableCell>
                        </TableRow>
                      ))}
                      {subscribers.length === 0 && (
                        <TableRow><TableCell colSpan={4} className="text-center text-slate-400 py-8">No subscribers yet.</TableCell></TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>
            </CardContent>
          </Tabs>
        </Card>

        {/* Reset Password Dialog */}
        <Dialog open={resetPasswordDialogOpen} onOpenChange={setResetPasswordDialogOpen}>
          <DialogContent className="bg-slate-800 border-amber-500/20 text-slate-100">
            <DialogHeader>
              <DialogTitle className="text-slate-100">Reset User Password</DialogTitle>
              <DialogDescription className="text-slate-300">Set a new password for {selectedUser?.email}.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="new-password" className="text-slate-200">New Password</Label>
                <Input id="new-password" type="text" placeholder="Enter new password (min 6 characters)" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400" />
              </div>
              <div className="flex gap-3">
                <Button onClick={() => { setResetPasswordDialogOpen(false); setSelectedUser(null); setNewPassword(''); }} variant="outline" className="flex-1 border-slate-600 text-slate-200 hover:bg-slate-700">Cancel</Button>
                <Button onClick={handleResetPassword} className="flex-1 warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold">Reset Password</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AdminPanel;
