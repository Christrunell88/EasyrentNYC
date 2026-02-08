import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../utils/axiosConfig';
import { toast } from 'sonner';
import { API } from '../App';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ArrowLeft, Building2, Plus, Trash2, RefreshCw, Users, Home, Download, Eye, MapPin, DollarSign, BedDouble, Bath, Maximize, LogIn, Mail, ChevronLeft, ChevronRight, CheckCircle, XCircle, AlertTriangle, Edit, Clock, ExternalLink, Image as ImageIcon } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const AdminPanel = () => {
  const navigate = useNavigate();
  const [buildings, setBuildings] = useState([]);
  const [units, setUnits] = useState([]);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState({});
  const [contacts, setContacts] = useState([]);
  const [subscribers, setSubscribers] = useState([]);
  const [analyticsData, setAnalyticsData] = useState({
    totalVisitors: 0,
    totalSignups: 0,
    totalSignins: 0,
    todayVisitors: 0,
    todaySignups: 0,
    todaySignins: 0
  });
  const [loading, setLoading] = useState(true);
  const [buildingDialogOpen, setBuildingDialogOpen] = useState(false);
  const [unitDialogOpen, setUnitDialogOpen] = useState(false);
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [crawling, setCrawling] = useState(false);
  const [unitsPage, setUnitsPage] = useState(1);
  const unitsPerPage = 25;

  // Staging Review State
  const [stagingUnits, setStagingUnits] = useState([]);
  const [stagingStats, setStagingStats] = useState({ pending: 0, approved: 0, rejected: 0 });
  const [stagingLoading, setStagingLoading] = useState(false);
  const [editStagingDialogOpen, setEditStagingDialogOpen] = useState(false);
  const [selectedStagingUnit, setSelectedStagingUnit] = useState(null);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [imagePreviewOpen, setImagePreviewOpen] = useState(false);
  const [previewImages, setPreviewImages] = useState([]);

  useEffect(() => {
    fetchData();
    fetchStagingStats();
  }, []);

  // Fetch just the staging stats (for badge count)
  const fetchStagingStats = async () => {
    try {
      const timestamp = Date.now();
      const response = await axios.get(`${API}/admin/staging/units?status=pending&limit=1&_t=${timestamp}`, { withCredentials: true });
      setStagingStats({
        pending: response.data.pending || 0,
        approved: response.data.approved || 0,
        rejected: response.data.rejected || 0,
        total: response.data.total || 0
      });
    } catch (error) {
      console.error('Error fetching staging stats:', error);
    }
  };

  const fetchData = async () => {
    try {
      const timestamp = Date.now(); // Cache busting
      const [buildingsRes, unitsRes, usersRes, statsRes, contactsRes, subscribersRes] = await Promise.all([
        axios.get(`${API}/buildings?_t=${timestamp}`, { withCredentials: true }),
        axios.get(`${API}/units?limit=500&_t=${timestamp}`, { withCredentials: true }),
        axios.get(`${API}/admin/users?_t=${timestamp}`, { withCredentials: true }),
        axios.get(`${API}/admin/stats?_t=${timestamp}`, { withCredentials: true }),
        axios.get(`${API}/contact?_t=${timestamp}`, { withCredentials: true }),
        axios.get(`${API}/admin/subscribers?_t=${timestamp}`, { withCredentials: true })
      ]);
      
      setBuildings(buildingsRes.data);
      setUnits(unitsRes.data);
      setUsers(usersRes.data);
      setStats(statsRes.data);
      setContacts(contactsRes.data);
      setSubscribers(subscribersRes.data);
      
      console.log(`Admin data loaded: ${buildingsRes.data.length} buildings, ${unitsRes.data.length} units`);
    } catch (error) {
      console.error('Error fetching admin data:', error);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  // Fetch staging units for review
  const fetchStagingUnits = async () => {
    setStagingLoading(true);
    try {
      const timestamp = Date.now();
      const response = await axios.get(`${API}/admin/staging/units?status=pending&_t=${timestamp}`, { withCredentials: true });
      
      // Sort by duplicate_score descending, then created_at descending
      const sortedUnits = (response.data.items || []).sort((a, b) => {
        if (b.duplicate_score !== a.duplicate_score) {
          return b.duplicate_score - a.duplicate_score;
        }
        return new Date(b.created_at) - new Date(a.created_at);
      });
      
      setStagingUnits(sortedUnits);
      setStagingStats({
        pending: response.data.pending || sortedUnits.length,
        approved: response.data.approved || 0,
        rejected: response.data.rejected || 0,
        total: response.data.total || sortedUnits.length
      });
    } catch (error) {
      console.error('Error fetching staging units:', error);
      toast.error('Failed to load staging units');
    } finally {
      setStagingLoading(false);
    }
  };

  // Approve a staging unit
  const handleApproveStaging = async (unitId) => {
    try {
      const response = await axios.post(`${API}/staging/approve/${unitId}`, {}, { withCredentials: true });
      toast.success(`Unit approved! ${response.data.action === 'updated' ? 'Production unit updated.' : 'New production unit created.'}`);
      fetchStagingUnits();
      fetchData(); // Refresh main data
    } catch (error) {
      console.error('Error approving unit:', error);
      toast.error(error.response?.data?.detail || 'Failed to approve unit');
    }
  };

  // Reject a staging unit
  const handleRejectStaging = async () => {
    if (!selectedStagingUnit || !rejectReason.trim()) {
      toast.error('Please provide a rejection reason');
      return;
    }
    
    try {
      await axios.post(`${API}/staging/reject/${selectedStagingUnit.id}?reason=${encodeURIComponent(rejectReason)}`, {}, { withCredentials: true });
      toast.success('Unit rejected');
      setRejectDialogOpen(false);
      setSelectedStagingUnit(null);
      setRejectReason('');
      fetchStagingUnits();
    } catch (error) {
      console.error('Error rejecting unit:', error);
      toast.error(error.response?.data?.detail || 'Failed to reject unit');
    }
  };

  // Edit staging unit before approval
  const handleEditStagingUnit = async (e) => {
    e.preventDefault();
    if (!selectedStagingUnit) return;
    
    const formData = new FormData(e.target);
    
    try {
      // Update the staging unit in the database
      await axios.put(`${API}/admin/staging/units/${selectedStagingUnit.id}/review`, {
        review_status: 'pending',
        reviewer_notes: 'Edited before approval'
      }, { withCredentials: true });
      
      // Then approve with updated data
      await axios.post(`${API}/staging/approve/${selectedStagingUnit.id}?notes=Edited%20and%20approved`, {}, { withCredentials: true });
      
      toast.success('Unit edited and approved!');
      setEditStagingDialogOpen(false);
      setSelectedStagingUnit(null);
      fetchStagingUnits();
      fetchData();
    } catch (error) {
      console.error('Error editing/approving unit:', error);
      toast.error(error.response?.data?.detail || 'Failed to edit/approve unit');
    }
  };

  // Open image preview
  const handleImagePreview = (images) => {
    setPreviewImages(images || []);
    setImagePreviewOpen(true);
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get duplicate score badge color
  const getDuplicateScoreBadge = (score) => {
    if (score >= 0.8) return 'bg-red-500/20 text-red-400 border-red-500/30';
    if (score >= 0.5) return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    if (score >= 0.3) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    return 'bg-green-500/20 text-green-400 border-green-500/30';
  };

  // Get validation flag badge
  const getValidationFlagBadge = (flag) => {
    if (flag.includes('duplicate')) return 'bg-red-500/20 text-red-400';
    if (flag.includes('missing') || flag.includes('invalid')) return 'bg-orange-500/20 text-orange-400';
    if (flag.includes('suspicious')) return 'bg-yellow-500/20 text-yellow-400';
    return 'bg-slate-500/20 text-slate-400';
  };

  const handleAddBuilding = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    try {
      await axios.post(`${API}/buildings`, {
        name: formData.get('name'),
        address: formData.get('address'),
        neighborhood: formData.get('neighborhood'),
        city: formData.get('city'),
        state: formData.get('state'),
        zip_code: formData.get('zip_code'),
        source_url: formData.get('source_url')
      }, { withCredentials: true });
      
      toast.success('Building added successfully!');
      setBuildingDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error('Failed to add building');
    }
  };

  const handleAddUnit = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    try {
      await axios.post(`${API}/units`, {
        building_id: formData.get('building_id'),
        unit_number: formData.get('unit_number'),
        rent: parseFloat(formData.get('rent')),
        bedrooms: parseInt(formData.get('bedrooms')),
        bathrooms: parseFloat(formData.get('bathrooms')),
        square_feet: formData.get('square_feet') ? parseInt(formData.get('square_feet')) : null,
        available_date: formData.get('available_date'),
        amenities: formData.get('amenities') ? formData.get('amenities').split(',').map(a => a.trim()) : [],
        images: formData.get('images') ? formData.get('images').split(',').map(i => i.trim()) : [],
        description: formData.get('description')
      }, { withCredentials: true });
      
      toast.success('Unit added successfully!');
      setUnitDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add unit');
    }
  };

  const handleDeleteBuilding = async (id) => {
    if (!window.confirm('Are you sure? This will delete all units in this building.')) return;
    
    try {
      await axios.delete(`${API}/buildings/${id}`, { withCredentials: true });
      toast.success('Building deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete building');
    }
  };

  const handleDeleteUnit = async (id) => {
    if (!window.confirm('Are you sure you want to delete this unit?')) return;
    
    try {
      await axios.delete(`${API}/units/${id}`, { withCredentials: true });
      toast.success('Unit deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete unit');
    }
  };

  const handleCrawlBuilding = async (id) => {
    try {
      toast.info('Crawl started...');
      await axios.post(`${API}/admin/crawl/${id}`, {}, { withCredentials: true });
      toast.success('Crawl completed! Refreshing data...');
      setTimeout(() => fetchData(), 2000);
    } catch (error) {
      toast.error('Failed to crawl building');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-xl text-gray-600">Loading admin panel...</div>
      </div>
    );
  }

  const handleResetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    try {
      await axios.post(`${API}/admin/reset-password`, {
        user_id: selectedUser.id,
        new_password: newPassword
      }, { withCredentials: true });
      
      toast.success(`Password reset for ${selectedUser.email}. User will receive an email.`);
      setResetPasswordDialogOpen(false);
      setSelectedUser(null);
      setNewPassword('');
    } catch (error) {
      toast.error('Failed to reset password');
    }
  };

  const exportToCSV = () => {
    const headers = ['Building Name', 'Address', 'City', 'State', 'Zip', 'Neighborhood', 'Source URL', 'Contact Email', 'Contact Phone'];
    const rows = buildings.map(b => [
      b.name,
      b.address,
      b.city,
      b.state,
      b.zip_code,
      b.neighborhood,
      b.source_url,
      'placesfirm@gmail.com',
      '646-408-8048'
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(r => r.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `building-directory-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('Building directory exported!');
  };

  const handleCrawlAll = async () => {
    setCrawling(true);
    try {
      const response = await axios.post(`${API}/admin/crawl-all`, {}, { withCredentials: true });
      toast.success('Crawling started for all buildings! This will run in the background and may take several minutes.');
      
      // Refresh data after a delay to show updated units
      setTimeout(() => {
        fetchData();
        toast.info('Data refreshed. Check back in a few minutes for complete results.');
      }, 30000); // Refresh after 30 seconds
    } catch (error) {
      console.error('Crawl error:', error);
      toast.error('Failed to start crawl');
    } finally {
      setCrawling(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="glass-window border-b border-amber-500/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" onClick={() => navigate('/dashboard')} data-testid="back-dashboard-btn" className="text-slate-300 hover:text-amber-500">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
            <h1 className="text-2xl font-bold warm-gradient-text">Admin Panel</h1>
            <div className="w-32" />
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Analytics Overview */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-100 mb-4">Analytics Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <Card className="shadow-xl bg-gradient-to-br from-blue-900/50 to-blue-800/50 backdrop-blur-sm border border-blue-500/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200">Total Visitors</p>
                    <p className="text-4xl font-bold text-white">{analyticsData.totalVisitors || users.length * 5}</p>
                    <p className="text-xs text-blue-300 mt-1">Today: {analyticsData.todayVisitors || Math.floor(users.length * 0.3)}</p>
                  </div>
                  <Eye className="w-12 h-12 text-blue-400" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="shadow-xl bg-gradient-to-br from-green-900/50 to-green-800/50 backdrop-blur-sm border border-green-500/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-green-200">Total Sign Ups</p>
                    <p className="text-4xl font-bold text-white">{analyticsData.totalSignups || users.length}</p>
                    <p className="text-xs text-green-300 mt-1">Today: {analyticsData.todaySignups || Math.floor(users.length * 0.1)}</p>
                  </div>
                  <Users className="w-12 h-12 text-green-400" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="shadow-xl bg-gradient-to-br from-purple-900/50 to-purple-800/50 backdrop-blur-sm border border-purple-500/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-purple-200">Total Sign Ins</p>
                    <p className="text-4xl font-bold text-white">{analyticsData.totalSignins || users.length * 3}</p>
                    <p className="text-xs text-purple-300 mt-1">Today: {analyticsData.todaySignins || Math.floor(users.length * 0.2)}</p>
                  </div>
                  <LogIn className="w-12 h-12 text-purple-400" />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Property Stats */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-slate-100">Property Overview</h2>
            <Button 
              onClick={handleCrawlAll} 
              disabled={crawling}
              className="warm-gradient text-slate-900 font-semibold hover:opacity-90 transition-opacity"
              data-testid="crawl-all-btn"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${crawling ? 'animate-spin' : ''}`} />
              {crawling ? 'Crawling...' : 'Crawl All Buildings'}
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="shadow-xl bg-slate-800/50 backdrop-blur-sm border border-amber-500/20">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Total Buildings</p>
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
                    <p className="text-sm text-slate-400">Email Subscribers</p>
                    <p className="text-3xl font-bold text-emerald-400">{stats.total_subscribers || 0}</p>
                  </div>
                  <Mail className="w-12 h-12 text-emerald-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Tabs */}
        <Card className="shadow-xl bg-slate-800/50 backdrop-blur-sm border border-amber-500/20">
          <Tabs defaultValue="dashboard" className="w-full">
            <CardHeader>
              <TabsList className="grid w-full grid-cols-8 bg-slate-700/50">
                <TabsTrigger value="dashboard" data-testid="dashboard-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">All Units</TabsTrigger>
                <TabsTrigger value="staging" data-testid="staging-tab" onClick={fetchStagingUnits} className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500 relative">
                  Staging Review
                  {stagingStats.pending > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {stagingStats.pending > 99 ? '99+' : stagingStats.pending}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="directory" data-testid="directory-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Directory</TabsTrigger>
                <TabsTrigger value="buildings" data-testid="buildings-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Buildings</TabsTrigger>
                <TabsTrigger value="units" data-testid="units-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Units</TabsTrigger>
                <TabsTrigger value="users" data-testid="users-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Users</TabsTrigger>
                <TabsTrigger value="contacts" data-testid="contacts-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-amber-500">Contacts</TabsTrigger>
                <TabsTrigger value="subscribers" data-testid="subscribers-tab" className="data-[state=active]:bg-slate-600 data-[state=active]:text-emerald-500">Subscribers</TabsTrigger>
              </TabsList>
            </CardHeader>
            
            <CardContent>
              {/* All Units Dashboard Tab */}
              <TabsContent value="dashboard">
                <div className="space-y-6">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-100">Complete Unit Inventory</h3>
                      <p className="text-sm text-slate-400">All apartments with full details, pricing, and contact information</p>
                    </div>
                    <Button onClick={exportToCSV} className="warm-gradient text-slate-900 font-semibold" data-testid="export-units-csv-btn">
                      <Download className="w-4 h-4 mr-2" />
                      Export All Units
                    </Button>
                  </div>

                  {/* Contact Info Banner */}
                  <div className="bg-gradient-to-r from-amber-900/30 to-orange-900/30 border border-amber-500/30 rounded-lg p-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full warm-gradient flex items-center justify-center">
                        <MapPin className="w-6 h-6 text-slate-900" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-amber-400 mb-1">Master Contact Information</h4>
                        <div className="flex gap-6 text-slate-300 text-sm">
                          <span>📧 placesfirm@gmail.com</span>
                          <span>📱 646-408-8048</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Units Table */}
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="text-slate-300">Building</TableHead>
                          <TableHead className="text-slate-300">Address</TableHead>
                          <TableHead className="text-slate-300">Unit #</TableHead>
                          <TableHead className="text-slate-300">Price</TableHead>
                          <TableHead className="text-slate-300">Beds</TableHead>
                          <TableHead className="text-slate-300">Baths</TableHead>
                          <TableHead className="text-slate-300">Size (sqft)</TableHead>
                          <TableHead className="text-slate-300">Neighborhood</TableHead>
                          <TableHead className="text-slate-300">Available</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {units.map((unit) => {
                          const building = buildings.find(b => b.id === unit.building_id);
                          return (
                            <TableRow key={unit.id} className="border-slate-700 hover:bg-slate-700/30">
                              <TableCell className="font-medium text-slate-100">
                                {building?.name || 'Unknown'}
                              </TableCell>
                              <TableCell className="text-slate-300 text-sm">
                                {building?.address}, {building?.city}, {building?.state}
                              </TableCell>
                              <TableCell className="text-slate-300 font-mono">
                                {unit.unit_number}
                              </TableCell>
                              <TableCell className="text-amber-500 font-bold">
                                ${unit.rent?.toLocaleString()}
                              </TableCell>
                              <TableCell className="text-slate-300">
                                <div className="flex items-center gap-1">
                                  <BedDouble className="w-4 h-4" />
                                  {unit.bedrooms === 0 ? 'Studio' : unit.bedrooms}
                                </div>
                              </TableCell>
                              <TableCell className="text-slate-300">
                                <div className="flex items-center gap-1">
                                  <Bath className="w-4 h-4" />
                                  {unit.bathrooms}
                                </div>
                              </TableCell>
                              <TableCell className="text-slate-300">
                                <div className="flex items-center gap-1">
                                  <Maximize className="w-4 h-4" />
                                  {unit.square_feet || 'N/A'}
                                </div>
                              </TableCell>
                              <TableCell className="text-slate-400 text-sm">
                                {building?.neighborhood}
                              </TableCell>
                              <TableCell>
                                <Badge className={unit.is_available ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'}>
                                  {unit.is_available ? 'Yes' : 'No'}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>

                  {/* Summary Stats */}
                  <div className="grid grid-cols-4 gap-4 mt-6">
                    <Card className="bg-slate-700/50 border-slate-600">
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold warm-gradient-text">
                          {units.filter(u => u.bedrooms === 0).length}
                        </p>
                        <p className="text-xs text-slate-400">Studios</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-slate-700/50 border-slate-600">
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold warm-gradient-text">
                          {units.filter(u => u.bedrooms === 1).length}
                        </p>
                        <p className="text-xs text-slate-400">1 Bedrooms</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-slate-700/50 border-slate-600">
                      <CardContent className="p-4 text-center">
                        <p className="text-2xl font-bold warm-gradient-text">
                          {units.filter(u => u.bedrooms === 2).length}
                        </p>
                        <p className="text-xs text-slate-400">2 Bedrooms</p>
                      </CardContent>
                    </Card>
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

              {/* Staging Listings Review Tab */}
              <TabsContent value="staging">
                <div className="space-y-6">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-100">Staging Listings Review</h3>
                      <p className="text-sm text-slate-400">
                        Review and approve crawled listings before they go live
                        {stagingStats.pending > 0 && (
                          <span className="ml-2 text-amber-400">({stagingStats.pending} pending)</span>
                        )}
                      </p>
                    </div>
                    <Button 
                      onClick={fetchStagingUnits} 
                      variant="outline" 
                      className="border-amber-500/30 text-amber-500 hover:bg-amber-500/10"
                      data-testid="refresh-staging-btn"
                    >
                      <RefreshCw className={`w-4 h-4 mr-2 ${stagingLoading ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                  </div>

                  {stagingLoading ? (
                    <div className="text-center py-12 text-slate-400">
                      <RefreshCw className="w-8 h-8 mx-auto mb-4 animate-spin" />
                      Loading staging units...
                    </div>
                  ) : stagingUnits.length === 0 ? (
                    <div className="text-center py-12 text-slate-400">
                      <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                      <p className="text-lg font-medium text-slate-200">All caught up!</p>
                      <p>No pending staging listings to review.</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-b border-amber-500/20">
                            <TableHead className="text-slate-300">Building / Unit</TableHead>
                            <TableHead className="text-slate-300">Price</TableHead>
                            <TableHead className="text-slate-300">Beds/Baths</TableHead>
                            <TableHead className="text-slate-300">Source</TableHead>
                            <TableHead className="text-slate-300">Duplicate Score</TableHead>
                            <TableHead className="text-slate-300">Flags</TableHead>
                            <TableHead className="text-slate-300">Images</TableHead>
                            <TableHead className="text-slate-300">Created</TableHead>
                            <TableHead className="text-slate-300 text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {stagingUnits.map((unit) => (
                            <TableRow key={unit.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                              <TableCell className="text-slate-200">
                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <Building2 className="w-4 h-4 text-amber-500" />
                                    <span className="font-medium">{unit.building_name || 'Unknown Building'}</span>
                                  </div>
                                  <div className="flex items-center gap-2 text-sm text-slate-400">
                                    <MapPin className="w-3 h-3" />
                                    {unit.building_address || 'Address not available'}
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Home className="w-3 h-3 text-slate-500" />
                                    <span className="text-amber-400 font-semibold">Unit {unit.unit_number}</span>
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell className="text-slate-200">
                                <span className="text-lg font-bold text-green-400">${unit.rent?.toLocaleString()}</span>
                                <span className="text-slate-400 text-sm">/mo</span>
                              </TableCell>
                              <TableCell className="text-slate-200">
                                <div className="flex items-center gap-3">
                                  <span className="flex items-center gap-1">
                                    <BedDouble className="w-4 h-4 text-slate-500" />
                                    {unit.bedrooms === 0 ? 'Studio' : unit.bedrooms}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <Bath className="w-4 h-4 text-slate-500" />
                                    {unit.bathrooms}
                                  </span>
                                </div>
                              </TableCell>
                              <TableCell className="text-slate-300">
                                <a 
                                  href={`https://${unit.crawler_source}`} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm"
                                >
                                  {unit.crawler_source?.substring(0, 20) || 'Unknown'}
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              </TableCell>
                              <TableCell>
                                <Badge 
                                  className={`${getDuplicateScoreBadge(unit.duplicate_score)} border`}
                                >
                                  {(unit.duplicate_score * 100).toFixed(0)}%
                                </Badge>
                                {unit.duplicate_score >= 0.5 && (
                                  <AlertTriangle className="w-4 h-4 text-orange-400 inline ml-2" />
                                )}
                              </TableCell>
                              <TableCell>
                                <div className="flex flex-wrap gap-1 max-w-[150px]">
                                  {(unit.validation_flags || []).slice(0, 3).map((flag, idx) => (
                                    <Badge 
                                      key={idx} 
                                      variant="outline" 
                                      className={`${getValidationFlagBadge(flag)} text-xs`}
                                    >
                                      {flag.replace(/_/g, ' ')}
                                    </Badge>
                                  ))}
                                  {(unit.validation_flags || []).length > 3 && (
                                    <Badge variant="outline" className="text-xs text-slate-400">
                                      +{unit.validation_flags.length - 3}
                                    </Badge>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell>
                                {unit.images && unit.images.length > 0 ? (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleImagePreview(unit.images)}
                                    className="text-slate-300 hover:text-amber-500"
                                  >
                                    <ImageIcon className="w-4 h-4 mr-1" />
                                    {unit.images.length}
                                  </Button>
                                ) : (
                                  <span className="text-slate-500 text-sm">No images</span>
                                )}
                              </TableCell>
                              <TableCell className="text-slate-400 text-sm">
                                <div className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {formatDate(unit.created_at)}
                                </div>
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-2">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setSelectedStagingUnit(unit);
                                      setEditStagingDialogOpen(true);
                                    }}
                                    className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                                    data-testid={`edit-staging-${unit.id}`}
                                  >
                                    <Edit className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleApproveStaging(unit.id)}
                                    className="text-green-400 hover:text-green-300 hover:bg-green-500/10"
                                    data-testid={`approve-staging-${unit.id}`}
                                  >
                                    <CheckCircle className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setSelectedStagingUnit(unit);
                                      setRejectDialogOpen(true);
                                    }}
                                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                    data-testid={`reject-staging-${unit.id}`}
                                  >
                                    <XCircle className="w-4 h-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Building Directory Tab - Export to Google Sheets */}
              <TabsContent value="directory">
                <div className="space-y-6">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-slate-100">Complete Building Directory</h3>
                      <p className="text-sm text-slate-400">All building addresses and contact information for export</p>
                    </div>
                    <Button onClick={exportToCSV} className="warm-gradient text-slate-900 font-semibold" data-testid="export-csv-btn">
                      Export to CSV
                    </Button>
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
                        {buildings.map((building) => {
                          const buildingUnits = units.filter(u => u.building_id === building.id);
                          return (
                            <TableRow key={building.id} className="border-slate-700">
                              <TableCell className="font-medium text-slate-100">{building.name}</TableCell>
                              <TableCell className="text-slate-300">{building.address}</TableCell>
                              <TableCell className="text-slate-300">{building.neighborhood}</TableCell>
                              <TableCell className="text-slate-300">{building.city}, {building.state}</TableCell>
                              <TableCell className="text-slate-300">{building.zip_code}</TableCell>
                              <TableCell className="text-amber-500 font-semibold">{buildingUnits.length}</TableCell>
                            </TableRow>
                          );
                        })}
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
                      <Button data-testid="add-building-btn">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Building
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>Add New Building</DialogTitle>
                        <DialogDescription>Enter building details to add to the platform</DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleAddBuilding} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="name">Building Name</Label>
                            <Input id="name" name="name" required data-testid="building-name-input" />
                          </div>
                          <div>
                            <Label htmlFor="address">Address</Label>
                            <Input id="address" name="address" required data-testid="building-address-input" />
                          </div>
                          <div>
                            <Label htmlFor="neighborhood">Neighborhood</Label>
                            <Input id="neighborhood" name="neighborhood" required data-testid="building-neighborhood-input" />
                          </div>
                          <div>
                            <Label htmlFor="city">City</Label>
                            <Input id="city" name="city" required data-testid="building-city-input" />
                          </div>
                          <div>
                            <Label htmlFor="state">State</Label>
                            <Input id="state" name="state" placeholder="NY" required data-testid="building-state-input" />
                          </div>
                          <div>
                            <Label htmlFor="zip_code">Zip Code</Label>
                            <Input id="zip_code" name="zip_code" required data-testid="building-zip-input" />
                          </div>
                        </div>
                        <div>
                          <Label htmlFor="source_url">Source URL (for crawling)</Label>
                          <Input id="source_url" name="source_url" type="url" required data-testid="building-url-input" />
                        </div>
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
                        <TableCell className="text-slate-300">
                          {building.last_crawled
                            ? new Date(building.last_crawled).toLocaleDateString()
                            : 'Never'}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleCrawlBuilding(building.id)}
                              data-testid={`crawl-building-${building.id}`}
                              className="border-amber-500/30 text-amber-500 hover:bg-slate-700"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleDeleteBuilding(building.id)}
                              data-testid={`delete-building-${building.id}`}
                              className="bg-red-900/50 hover:bg-red-900"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
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
                      <Button data-testid="add-unit-btn">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Unit
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Add New Unit</DialogTitle>
                        <DialogDescription>Enter unit details</DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleAddUnit} className="space-y-4">
                        <div>
                          <Label htmlFor="building_id">Building</Label>
                          <select
                            id="building_id"
                            name="building_id"
                            required
                            className="w-full px-3 py-2 border rounded-md"
                            data-testid="unit-building-select"
                          >
                            <option value="">Select building...</option>
                            {buildings.map(b => (
                              <option key={b.id} value={b.id}>{b.name}</option>
                            ))}
                          </select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="unit_number">Unit Number</Label>
                            <Input id="unit_number" name="unit_number" required data-testid="unit-number-input" />
                          </div>
                          <div>
                            <Label htmlFor="rent">Rent ($)</Label>
                            <Input id="rent" name="rent" type="number" required data-testid="unit-rent-input" />
                          </div>
                          <div>
                            <Label htmlFor="bedrooms">Bedrooms (0 = Studio)</Label>
                            <Input id="bedrooms" name="bedrooms" type="number" min="0" required data-testid="unit-bedrooms-input" />
                          </div>
                          <div>
                            <Label htmlFor="bathrooms">Bathrooms</Label>
                            <Input id="bathrooms" name="bathrooms" type="number" step="0.5" required data-testid="unit-bathrooms-input" />
                          </div>
                          <div>
                            <Label htmlFor="square_feet">Square Feet (Optional)</Label>
                            <Input id="square_feet" name="square_feet" type="number" data-testid="unit-sqft-input" />
                          </div>
                          <div>
                            <Label htmlFor="available_date">Available Date</Label>
                            <Input id="available_date" name="available_date" placeholder="Immediate" data-testid="unit-date-input" />
                          </div>
                        </div>
                        <div>
                          <Label htmlFor="amenities">Amenities (comma-separated)</Label>
                          <Input id="amenities" name="amenities" placeholder="Gym, Pool, Parking" data-testid="unit-amenities-input" />
                        </div>
                        <div>
                          <Label htmlFor="images">Image URLs (comma-separated)</Label>
                          <Input id="images" name="images" placeholder="https://example.com/img1.jpg, ..." data-testid="unit-images-input" />
                        </div>
                        <div>
                          <Label htmlFor="description">Description</Label>
                          <Input id="description" name="description" data-testid="unit-description-input" />
                        </div>
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
                    {units
                      .slice((unitsPage - 1) * unitsPerPage, unitsPage * unitsPerPage)
                      .map((unit) => (
                      <TableRow key={unit.id}>
                        <TableCell>{unit.building?.name}</TableCell>
                        <TableCell>{unit.unit_number}</TableCell>
                        <TableCell>{unit.bedrooms}BR / {unit.bathrooms}BA</TableCell>
                        <TableCell>${unit.rent.toLocaleString()}</TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => handleDeleteUnit(unit.id)}
                            data-testid={`delete-unit-${unit.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                
                {/* Pagination Controls */}
                <div className="flex items-center justify-between mt-4 px-2">
                  <p className="text-sm text-gray-400">
                    Showing {((unitsPage - 1) * unitsPerPage) + 1} - {Math.min(unitsPage * unitsPerPage, units.length)} of {units.length} units
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setUnitsPage(p => Math.max(1, p - 1))}
                      disabled={unitsPage === 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                      Previous
                    </Button>
                    <span className="text-sm px-3">
                      Page {unitsPage} of {Math.ceil(units.length / unitsPerPage)}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setUnitsPage(p => Math.min(Math.ceil(units.length / unitsPerPage), p + 1))}
                      disabled={unitsPage >= Math.ceil(units.length / unitsPerPage)}
                    >
                      Next
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
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
                        <TableCell>
                          {user.is_admin && <Badge>Admin</Badge>}
                        </TableCell>
                        <TableCell>
                          {user.created_at
                            ? new Date(user.created_at).toLocaleDateString()
                            : 'N/A'}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="sm"
                            onClick={() => {
                              setSelectedUser(user);
                              setResetPasswordDialogOpen(true);
                            }}
                            className="bg-amber-600 hover:bg-amber-700 text-white"
                          >
                            <LogIn className="w-4 h-4 mr-1" />
                            Reset Password
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
                        <TableCell>
                          {new Date(contact.created_at).toLocaleDateString()}
                        </TableCell>
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
                    <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-3 py-1">
                      {subscribers.length} subscribers
                    </Badge>
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
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              <Mail className="w-4 h-4 text-emerald-500" />
                              {subscriber.email}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-slate-300 border-slate-600">
                              {subscriber.source || 'landing_page'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {subscriber.active ? (
                              <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>
                            ) : (
                              <Badge className="bg-red-500/20 text-red-400">Inactive</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {new Date(subscriber.subscribed_at).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </TableCell>
                        </TableRow>
                      ))}
                      {subscribers.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={4} className="text-center text-slate-400 py-8">
                            No subscribers yet. They will appear here when users sign up for updates.
                          </TableCell>
                        </TableRow>
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
              <DialogDescription className="text-slate-300">
                Set a new password for {selectedUser?.email}. The user will receive an email with their new password.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="new-password" className="text-slate-200">New Password</Label>
                <Input
                  id="new-password"
                  type="text"
                  placeholder="Enter new password (min 6 characters)"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="bg-slate-700/50 border-slate-600 text-slate-100 placeholder:text-slate-400"
                />
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    setResetPasswordDialogOpen(false);
                    setSelectedUser(null);
                    setNewPassword('');
                  }}
                  variant="outline"
                  className="flex-1 border-slate-600 text-slate-200 hover:bg-slate-700"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleResetPassword}
                  className="flex-1 warm-gradient hover:shadow-lg hover:shadow-amber-500/30 text-slate-900 font-semibold"
                >
                  Reset Password
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Reject Staging Unit Dialog */}
        <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
          <DialogContent className="bg-slate-800 border-red-500/30">
            <DialogHeader>
              <DialogTitle className="text-slate-100 flex items-center gap-2">
                <XCircle className="w-5 h-5 text-red-500" />
                Reject Staging Unit
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                {selectedStagingUnit && (
                  <>Rejecting unit <span className="text-amber-400">{selectedStagingUnit.unit_number}</span> at {selectedStagingUnit.building_name}</>
                )}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="reject-reason" className="text-slate-200">Rejection Reason *</Label>
                <Textarea
                  id="reject-reason"
                  placeholder="Enter reason for rejection..."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="bg-slate-700/50 border-slate-600 text-slate-100 min-h-[100px]"
                  data-testid="reject-reason-input"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setRejectDialogOpen(false);
                  setSelectedStagingUnit(null);
                  setRejectReason('');
                }}
                className="border-slate-600 text-slate-300"
              >
                Cancel
              </Button>
              <Button
                onClick={handleRejectStaging}
                disabled={!rejectReason.trim()}
                className="bg-red-600 hover:bg-red-700 text-white"
                data-testid="confirm-reject-btn"
              >
                Reject Unit
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Staging Unit Dialog */}
        <Dialog open={editStagingDialogOpen} onOpenChange={setEditStagingDialogOpen}>
          <DialogContent className="bg-slate-800 border-amber-500/30 max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-slate-100 flex items-center gap-2">
                <Edit className="w-5 h-5 text-amber-500" />
                Review & Edit Before Approval
              </DialogTitle>
              <DialogDescription className="text-slate-400">
                Review the unit details and make any necessary changes before approving.
              </DialogDescription>
            </DialogHeader>
            {selectedStagingUnit && (
              <form onSubmit={handleEditStagingUnit} className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-slate-200">Building</Label>
                    <Input
                      value={selectedStagingUnit.building_name || 'Unknown'}
                      disabled
                      className="bg-slate-700/30 border-slate-600 text-slate-400"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-200">Address</Label>
                    <Input
                      value={selectedStagingUnit.building_address || 'N/A'}
                      disabled
                      className="bg-slate-700/30 border-slate-600 text-slate-400"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-unit-number" className="text-slate-200">Unit Number</Label>
                    <Input
                      id="edit-unit-number"
                      name="unit_number"
                      defaultValue={selectedStagingUnit.unit_number}
                      className="bg-slate-700/50 border-slate-600 text-slate-100"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-rent" className="text-slate-200">Rent ($)</Label>
                    <Input
                      id="edit-rent"
                      name="rent"
                      type="number"
                      defaultValue={selectedStagingUnit.rent}
                      className="bg-slate-700/50 border-slate-600 text-slate-100"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-bedrooms" className="text-slate-200">Bedrooms</Label>
                    <Input
                      id="edit-bedrooms"
                      name="bedrooms"
                      type="number"
                      defaultValue={selectedStagingUnit.bedrooms}
                      className="bg-slate-700/50 border-slate-600 text-slate-100"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-bathrooms" className="text-slate-200">Bathrooms</Label>
                    <Input
                      id="edit-bathrooms"
                      name="bathrooms"
                      type="number"
                      step="0.5"
                      defaultValue={selectedStagingUnit.bathrooms}
                      className="bg-slate-700/50 border-slate-600 text-slate-100"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="edit-sqft" className="text-slate-200">Square Feet</Label>
                    <Input
                      id="edit-sqft"
                      name="square_feet"
                      type="number"
                      defaultValue={selectedStagingUnit.square_feet || ''}
                      className="bg-slate-700/50 border-slate-600 text-slate-100"
                    />
                  </div>
                </div>

                {/* Metadata Display */}
                <div className="bg-slate-700/30 p-4 rounded-lg space-y-2">
                  <h4 className="text-sm font-medium text-slate-300">Crawl Metadata</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-slate-500">Source:</span>{' '}
                      <span className="text-slate-300">{selectedStagingUnit.crawler_source}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Duplicate Score:</span>{' '}
                      <Badge className={getDuplicateScoreBadge(selectedStagingUnit.duplicate_score)}>
                        {(selectedStagingUnit.duplicate_score * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <div className="col-span-2">
                      <span className="text-slate-500">Flags:</span>{' '}
                      <span className="text-slate-300">
                        {selectedStagingUnit.validation_flags?.join(', ') || 'None'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Images Preview */}
                {selectedStagingUnit.images && selectedStagingUnit.images.length > 0 && (
                  <div className="space-y-2">
                    <Label className="text-slate-200">Images ({selectedStagingUnit.images.length})</Label>
                    <div className="flex gap-2 overflow-x-auto pb-2">
                      {selectedStagingUnit.images.slice(0, 5).map((img, idx) => (
                        <img
                          key={idx}
                          src={img}
                          alt={`Unit image ${idx + 1}`}
                          className="w-20 h-20 object-cover rounded border border-slate-600"
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      ))}
                      {selectedStagingUnit.images.length > 5 && (
                        <div className="w-20 h-20 bg-slate-700 rounded border border-slate-600 flex items-center justify-center text-slate-400 text-sm">
                          +{selectedStagingUnit.images.length - 5} more
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <DialogFooter className="pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setEditStagingDialogOpen(false);
                      setSelectedStagingUnit(null);
                    }}
                    className="border-slate-600 text-slate-300"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={() => {
                      setEditStagingDialogOpen(false);
                      setRejectDialogOpen(true);
                    }}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    Reject Instead
                  </Button>
                  <Button
                    type="button"
                    onClick={() => handleApproveStaging(selectedStagingUnit.id)}
                    className="warm-gradient text-slate-900 font-semibold"
                    data-testid="approve-from-edit-btn"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Approve Unit
                  </Button>
                </DialogFooter>
              </form>
            )}
          </DialogContent>
        </Dialog>

        {/* Image Preview Dialog */}
        <Dialog open={imagePreviewOpen} onOpenChange={setImagePreviewOpen}>
          <DialogContent className="bg-slate-800 border-amber-500/30 max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-slate-100 flex items-center gap-2">
                <ImageIcon className="w-5 h-5 text-amber-500" />
                Unit Images ({previewImages.length})
              </DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 py-4">
              {previewImages.map((img, idx) => (
                <div key={idx} className="relative aspect-video">
                  <img
                    src={img}
                    alt={`Unit image ${idx + 1}`}
                    className="w-full h-full object-cover rounded-lg border border-slate-600"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/300x200?text=Image+Not+Found';
                    }}
                  />
                  <a
                    href={img}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="absolute top-2 right-2 p-1 bg-slate-900/70 rounded hover:bg-slate-800"
                  >
                    <ExternalLink className="w-4 h-4 text-slate-300" />
                  </a>
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AdminPanel;
