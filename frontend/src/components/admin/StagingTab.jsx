import React, { useState, useEffect, useCallback } from 'react';
import axios from '../../utils/axiosConfig';
import { API } from '../../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import {
  Building2, Home, Trash2, RefreshCw, MapPin, BedDouble, Bath,
  CheckCircle, XCircle, AlertTriangle, Edit, Clock, ExternalLink,
  Image as ImageIcon, Upload, X
} from 'lucide-react';

const StagingTab = ({ buildings, fetchData, onStatsUpdate }) => {
  const [stagingUnits, setStagingUnits] = useState([]);
  const [stagingStats, setStagingStats] = useState({ pending: 0, approved: 0, rejected: 0 });
  const [stagingLoading, setStagingLoading] = useState(false);
  const [selectedStagingUnit, setSelectedStagingUnit] = useState(null);
  const [editStagingDialogOpen, setEditStagingDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [uploadingImages, setUploadingImages] = useState(false);
  const [stagingUnitImages, setStagingUnitImages] = useState([]);
  const [imagePreviewOpen, setImagePreviewOpen] = useState(false);
  const [previewImages, setPreviewImages] = useState([]);
  const [selectedStagingUnits, setSelectedStagingUnits] = useState(new Set());
  const [bulkDeletingStaging, setBulkDeletingStaging] = useState(false);
  const [bulkApprovingStaging, setBulkApprovingStaging] = useState(false);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  const getDuplicateScoreBadge = (score) => {
    if (score >= 0.8) return 'bg-red-500/20 text-red-400 border-red-500/30';
    if (score >= 0.5) return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    if (score >= 0.3) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    return 'bg-green-500/20 text-green-400 border-green-500/30';
  };

  const getValidationFlagBadge = (flag) => {
    if (flag.includes('duplicate')) return 'bg-red-500/20 text-red-400';
    if (flag.includes('missing') || flag.includes('invalid')) return 'bg-orange-500/20 text-orange-400';
    if (flag.includes('suspicious')) return 'bg-yellow-500/20 text-yellow-400';
    return 'bg-slate-500/20 text-slate-400';
  };

  const fetchStagingUnits = useCallback(async () => {
    setStagingLoading(true);
    try {
      const timestamp = Date.now();
      const response = await axios.get(`${API}/admin/staging/units?status=pending&_t=${timestamp}`, { withCredentials: true });
      const sortedUnits = (response.data.items || []).sort((a, b) => {
        if (b.duplicate_score !== a.duplicate_score) return b.duplicate_score - a.duplicate_score;
        return new Date(b.created_at) - new Date(a.created_at);
      });
      setStagingUnits(sortedUnits);
      const newStats = {
        pending: response.data.pending || sortedUnits.length,
        approved: response.data.approved || 0,
        rejected: response.data.rejected || 0,
        total: response.data.total || sortedUnits.length
      };
      setStagingStats(newStats);
      if (onStatsUpdate) onStatsUpdate(newStats);
    } catch (error) {
      console.error('Error fetching staging units:', error);
      toast.error('Failed to load staging units');
    } finally {
      setStagingLoading(false);
    }
  }, [onStatsUpdate]);

  useEffect(() => {
    fetchStagingUnits();
  }, [fetchStagingUnits]);

  const handleApproveStaging = async (unitId) => {
    try {
      const response = await axios.post(`${API}/staging/approve/${unitId}`, {}, { withCredentials: true });
      toast.success(`Unit approved! ${response.data.action === 'updated' ? 'Production unit updated.' : 'New production unit created.'}`);
      fetchStagingUnits();
      fetchData();
    } catch (error) {
      console.error('Error approving unit:', error);
      toast.error(error.response?.data?.detail || 'Failed to approve unit');
    }
  };

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

  const handleQuickReject = async (stagingUnit) => {
    try {
      await axios.post(`${API}/staging/reject/${stagingUnit.id}?reason=Rejected`, {}, { withCredentials: true });
      toast.success('Unit rejected');
      fetchStagingUnits();
    } catch (error) {
      console.error('Error rejecting unit:', error);
      toast.error(error.response?.data?.detail || 'Failed to reject unit');
    }
  };

  const toggleStagingSelection = (unitId) => {
    setSelectedStagingUnits(prev => {
      const newSet = new Set(prev);
      if (newSet.has(unitId)) newSet.delete(unitId);
      else newSet.add(unitId);
      return newSet;
    });
  };

  const toggleAllStagingSelection = () => {
    if (selectedStagingUnits.size === stagingUnits.length) setSelectedStagingUnits(new Set());
    else setSelectedStagingUnits(new Set(stagingUnits.map(u => u.id)));
  };

  const handleBulkDeleteStaging = async () => {
    if (selectedStagingUnits.size === 0) return;
    if (!confirm(`Are you sure you want to delete ${selectedStagingUnits.size} staging unit(s)?`)) return;
    setBulkDeletingStaging(true);
    try {
      const ids = Array.from(selectedStagingUnits);
      await axios.post(`${API}/admin/staging/units/bulk-delete`, { ids }, { withCredentials: true });
      toast.success(`${ids.length} staging unit(s) deleted`);
      setSelectedStagingUnits(new Set());
      fetchStagingUnits();
    } catch (error) {
      console.error('Error bulk deleting:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete staging units');
    } finally {
      setBulkDeletingStaging(false);
    }
  };

  const handleBulkApproveStaging = async () => {
    if (selectedStagingUnits.size === 0) return;
    if (!confirm(`Approve ${selectedStagingUnits.size} staging unit(s)?`)) return;
    setBulkApprovingStaging(true);
    try {
      const ids = Array.from(selectedStagingUnits);
      const response = await axios.post(`${API}/admin/staging/units/bulk-approve`, { ids }, { withCredentials: true });
      toast.success(`${response.data.approved_count} unit(s) approved`);
      setSelectedStagingUnits(new Set());
      fetchStagingUnits();
      fetchData();
    } catch (error) {
      console.error('Error bulk approving:', error);
      toast.error(error.response?.data?.detail || 'Failed to approve staging units');
    } finally {
      setBulkApprovingStaging(false);
    }
  };

  const handleEditStagingUnit = async (e) => {
    e.preventDefault();
    if (!selectedStagingUnit) return;
    const formData = new FormData(e.target);
    const building_id = formData.get('building_id');
    if (!building_id) { toast.error('Please select a building'); return; }
    try {
      await axios.put(`${API}/admin/staging/units/${selectedStagingUnit.id}/edit`, {
        building_id, unit_number: formData.get('unit_number'),
        rent: parseFloat(formData.get('rent')),
        bedrooms: parseInt(formData.get('bedrooms')) || 0,
        bathrooms: parseFloat(formData.get('bathrooms')) || 1,
        square_feet: formData.get('square_feet') ? parseInt(formData.get('square_feet')) : null
      }, { withCredentials: true });
      await axios.post(`${API}/staging/approve/${selectedStagingUnit.id}?notes=Edited%20and%20approved`, {}, { withCredentials: true });
      toast.success('Unit edited and approved!');
      setEditStagingDialogOpen(false);
      setSelectedStagingUnit(null);
      fetchStagingUnits();
      fetchData();
    } catch (error) {
      console.error('Error editing/approving:', error);
      toast.error(error.response?.data?.detail || 'Failed to edit/approve unit');
    }
  };

  const handleImagePreview = (images) => {
    setPreviewImages(images || []);
    setImagePreviewOpen(true);
  };

  const handleStagingImageUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !selectedStagingUnit) return;
    setUploadingImages(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) formData.append('files', files[i]);
    try {
      const response = await axios.post(`${API}/admin/staging/units/${selectedStagingUnit.id}/upload-images`, formData, {
        withCredentials: true, headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(`Uploaded ${response.data.uploaded_urls.length} images`);
      setStagingUnitImages(prev => [...prev, ...response.data.uploaded_urls]);
      setSelectedStagingUnit(prev => ({ ...prev, images: [...(prev.images || []), ...response.data.uploaded_urls] }));
      e.target.value = '';
    } catch (error) {
      console.error('Error uploading:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload images');
    } finally {
      setUploadingImages(false);
    }
  };

  const handleDeleteStagingImage = async (imageUrl) => {
    if (!selectedStagingUnit) return;
    try {
      await axios.delete(`${API}/admin/staging/units/${selectedStagingUnit.id}/images`, {
        params: { image_url: imageUrl }, withCredentials: true
      });
      toast.success('Image deleted');
      setStagingUnitImages(prev => prev.filter(img => img !== imageUrl));
      setSelectedStagingUnit(prev => ({ ...prev, images: (prev.images || []).filter(img => img !== imageUrl) }));
    } catch (error) {
      console.error('Error deleting image:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete image');
    }
  };

  return (
    <>
      <div className="space-y-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">Staging Listings Review</h3>
            <p className="text-sm text-slate-400">
              Review and approve crawled listings before they go live
              {stagingStats.pending > 0 && <span className="ml-2 text-amber-400">({stagingStats.pending} pending)</span>}
            </p>
          </div>
          <Button onClick={fetchStagingUnits} variant="outline" className="border-amber-500/30 text-amber-500 hover:bg-amber-500/10" data-testid="refresh-staging-btn">
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
            {selectedStagingUnits.size > 0 && (
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 mb-4 flex items-center justify-between">
                <span className="text-amber-400 font-medium">{selectedStagingUnits.size} unit(s) selected</span>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => setSelectedStagingUnits(new Set())} className="border-slate-600 text-slate-300 hover:bg-slate-700">Clear Selection</Button>
                  <Button size="sm" onClick={handleBulkApproveStaging} disabled={bulkApprovingStaging} className="bg-green-600 hover:bg-green-700">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    {bulkApprovingStaging ? 'Approving...' : `Approve ${selectedStagingUnits.size} Unit(s)`}
                  </Button>
                  <Button variant="destructive" size="sm" onClick={handleBulkDeleteStaging} disabled={bulkDeletingStaging} className="bg-red-600 hover:bg-red-700">
                    <Trash2 className="w-4 h-4 mr-1" />
                    {bulkDeletingStaging ? 'Deleting...' : `Delete ${selectedStagingUnits.size}`}
                  </Button>
                </div>
              </div>
            )}
            <Table>
              <TableHeader>
                <TableRow className="border-b border-amber-500/20">
                  <TableHead className="w-12">
                    <Checkbox checked={stagingUnits.length > 0 && selectedStagingUnits.size === stagingUnits.length} onCheckedChange={toggleAllStagingSelection} className="border-slate-500" />
                  </TableHead>
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
                  <TableRow key={unit.id} className={`border-b border-slate-700/50 hover:bg-slate-700/30 ${selectedStagingUnits.has(unit.id) ? 'bg-amber-500/10' : ''}`}>
                    <TableCell><Checkbox checked={selectedStagingUnits.has(unit.id)} onCheckedChange={() => toggleStagingSelection(unit.id)} className="border-slate-500" /></TableCell>
                    <TableCell className="text-slate-200">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2"><Building2 className="w-4 h-4 text-amber-500" /><span className="font-medium">{unit.building_name || 'Unknown Building'}</span></div>
                        <div className="flex items-center gap-2 text-sm text-slate-400"><MapPin className="w-3 h-3" />{unit.building_address || 'Address not available'}</div>
                        <div className="flex items-center gap-2"><Home className="w-3 h-3 text-slate-500" /><span className="text-amber-400 font-semibold">Unit {unit.unit_number}</span></div>
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-200"><span className="text-lg font-bold text-green-400">${unit.rent?.toLocaleString()}</span><span className="text-slate-400 text-sm">/mo</span></TableCell>
                    <TableCell className="text-slate-200">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1"><BedDouble className="w-4 h-4 text-slate-500" />{unit.bedrooms === 0 ? 'Studio' : unit.bedrooms}</span>
                        <span className="flex items-center gap-1"><Bath className="w-4 h-4 text-slate-500" />{unit.bathrooms}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-300">
                      <a href={`https://${unit.crawler_source}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm">
                        {unit.crawler_source?.substring(0, 20) || 'Unknown'}<ExternalLink className="w-3 h-3" />
                      </a>
                    </TableCell>
                    <TableCell>
                      <Badge className={`${getDuplicateScoreBadge(unit.duplicate_score)} border`}>{(unit.duplicate_score * 100).toFixed(0)}%</Badge>
                      {unit.duplicate_score >= 0.5 && <AlertTriangle className="w-4 h-4 text-orange-400 inline ml-2" />}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1 max-w-[150px]">
                        {(unit.validation_flags || []).slice(0, 3).map((flag, idx) => (
                          <Badge key={idx} variant="outline" className={`${getValidationFlagBadge(flag)} text-xs`}>{flag.replace(/_/g, ' ')}</Badge>
                        ))}
                        {(unit.validation_flags || []).length > 3 && <Badge variant="outline" className="text-xs text-slate-400">+{unit.validation_flags.length - 3}</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      {unit.images && unit.images.length > 0 ? (
                        <Button variant="ghost" size="sm" onClick={() => handleImagePreview(unit.images)} className="text-slate-300 hover:text-amber-500">
                          <ImageIcon className="w-4 h-4 mr-1" />{unit.images.length}
                        </Button>
                      ) : <span className="text-slate-500 text-sm">No images</span>}
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm"><div className="flex items-center gap-1"><Clock className="w-3 h-3" />{formatDate(unit.created_at)}</div></TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="ghost" size="sm" onClick={() => { setSelectedStagingUnit(unit); setStagingUnitImages(unit.images || []); setEditStagingDialogOpen(true); }} className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10" data-testid={`edit-staging-${unit.id}`}><Edit className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => handleApproveStaging(unit.id)} className="text-green-400 hover:text-green-300 hover:bg-green-500/10" data-testid={`approve-staging-${unit.id}`}><CheckCircle className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="sm" onClick={() => handleQuickReject(unit)} className="text-red-400 hover:text-red-300 hover:bg-red-500/10" data-testid={`reject-staging-${unit.id}`}><XCircle className="w-4 h-4" /></Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent className="bg-slate-800 border-red-500/30">
          <DialogHeader>
            <DialogTitle className="text-slate-100 flex items-center gap-2"><XCircle className="w-5 h-5 text-red-500" />Reject Staging Unit</DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedStagingUnit && (<>Rejecting unit <span className="text-amber-400">{selectedStagingUnit.unit_number}</span> at {selectedStagingUnit.building_name}</>)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="reject-reason" className="text-slate-200">Rejection Reason *</Label>
              <Textarea id="reject-reason" placeholder="Enter reason for rejection..." value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} className="bg-slate-700/50 border-slate-600 text-slate-100 min-h-[100px]" data-testid="reject-reason-input" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setRejectDialogOpen(false); setSelectedStagingUnit(null); setRejectReason(''); }} className="border-slate-600 text-slate-300">Cancel</Button>
            <Button onClick={handleRejectStaging} disabled={!rejectReason.trim()} className="bg-red-600 hover:bg-red-700 text-white" data-testid="confirm-reject-btn">Reject Unit</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Staging Unit Dialog */}
      <Dialog open={editStagingDialogOpen} onOpenChange={setEditStagingDialogOpen}>
        <DialogContent className="bg-slate-800 border-amber-500/30 max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-slate-100 flex items-center gap-2"><Edit className="w-5 h-5 text-amber-500" />Review & Edit Before Approval</DialogTitle>
            <DialogDescription className="text-slate-400">Review the unit details and make any necessary changes before approving.</DialogDescription>
          </DialogHeader>
          {selectedStagingUnit && (
            <form onSubmit={handleEditStagingUnit} className="space-y-4 py-4">
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-building" className="text-slate-200">Building *</Label>
                  <select id="edit-building" name="building_id" defaultValue={selectedStagingUnit.building_id || ''} className="w-full bg-slate-700/50 border border-slate-600 text-slate-100 rounded-md px-3 py-2" required>
                    <option value="">-- Select Building --</option>
                    {buildings.map((b) => (<option key={b.id} value={b.id}>{b.name} - {b.address}, {b.city}</option>))}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2"><Label className="text-slate-200">Unit Number *</Label><Input name="unit_number" defaultValue={selectedStagingUnit.unit_number} required className="bg-slate-700/50 border-slate-600 text-slate-100" /></div>
                <div className="space-y-2"><Label className="text-slate-200">Rent ($) *</Label><Input name="rent" type="number" defaultValue={selectedStagingUnit.rent} required className="bg-slate-700/50 border-slate-600 text-slate-100" /></div>
                <div className="space-y-2"><Label className="text-slate-200">Bedrooms</Label><Input name="bedrooms" type="number" defaultValue={selectedStagingUnit.bedrooms} className="bg-slate-700/50 border-slate-600 text-slate-100" /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label className="text-slate-200">Bathrooms</Label><Input name="bathrooms" type="number" step="0.5" defaultValue={selectedStagingUnit.bathrooms} className="bg-slate-700/50 border-slate-600 text-slate-100" /></div>
                <div className="space-y-2"><Label className="text-slate-200">Square Feet</Label><Input name="square_feet" type="number" defaultValue={selectedStagingUnit.square_feet || ''} className="bg-slate-700/50 border-slate-600 text-slate-100" /></div>
              </div>
              <div className="bg-slate-700/30 p-4 rounded-lg space-y-2">
                <h4 className="text-sm font-medium text-slate-300">Crawl Metadata</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-slate-500">Source:</span> <span className="text-slate-300">{selectedStagingUnit.crawler_source}</span></div>
                  <div><span className="text-slate-500">Duplicate Score:</span> <Badge className={getDuplicateScoreBadge(selectedStagingUnit.duplicate_score)}>{(selectedStagingUnit.duplicate_score * 100).toFixed(0)}%</Badge></div>
                  <div className="col-span-2"><span className="text-slate-500">Flags:</span> <span className="text-slate-300">{selectedStagingUnit.validation_flags?.join(', ') || 'None'}</span></div>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-slate-200 flex items-center gap-2"><ImageIcon className="w-4 h-4 text-amber-500" />Images ({selectedStagingUnit.images?.length || 0})</Label>
                  <label className="cursor-pointer">
                    <input type="file" multiple accept="image/*" onChange={handleStagingImageUpload} className="hidden" disabled={uploadingImages} />
                    <Button type="button" size="sm" variant="outline" className="border-amber-500/50 text-amber-400 hover:bg-amber-500/10" disabled={uploadingImages} asChild>
                      <span>{uploadingImages ? (<><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Uploading...</>) : (<><Upload className="w-4 h-4 mr-2" />Upload Images</>)}</span>
                    </Button>
                  </label>
                </div>
                {selectedStagingUnit.images && selectedStagingUnit.images.length > 0 ? (
                  <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto p-2 bg-slate-700/30 rounded-lg">
                    {selectedStagingUnit.images.map((img, idx) => (
                      <div key={idx} className="relative group">
                        <img src={img.startsWith('/api') ? `${API.replace('/api', '')}${img}` : img} alt={`Unit image ${idx + 1}`} className="w-full h-20 object-cover rounded border border-slate-600" onError={(e) => { e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" fill="%23666"><rect width="80" height="80"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%23999" font-size="10">No Image</text></svg>'; }} />
                        <button type="button" onClick={() => handleDeleteStagingImage(img)} className="absolute -top-1 -right-1 bg-red-600 hover:bg-red-700 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"><X className="w-3 h-3" /></button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-slate-700/30 rounded-lg p-6 text-center"><ImageIcon className="w-10 h-10 text-slate-500 mx-auto mb-2" /><p className="text-slate-400 text-sm">No images yet</p></div>
                )}
              </div>
              <DialogFooter className="pt-4">
                <Button type="button" variant="outline" onClick={() => { setEditStagingDialogOpen(false); setSelectedStagingUnit(null); }} className="border-slate-600 text-slate-300">Cancel</Button>
                <Button type="button" variant="destructive" onClick={() => { handleQuickReject(selectedStagingUnit); setEditStagingDialogOpen(false); }} className="bg-red-600 hover:bg-red-700">Reject Instead</Button>
                <Button type="button" onClick={() => handleApproveStaging(selectedStagingUnit.id)} className="warm-gradient text-slate-900 font-semibold" data-testid="approve-from-edit-btn"><CheckCircle className="w-4 h-4 mr-2" />Approve Unit</Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Image Preview Dialog */}
      <Dialog open={imagePreviewOpen} onOpenChange={setImagePreviewOpen}>
        <DialogContent className="bg-slate-800 border-amber-500/30 max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-slate-100 flex items-center gap-2"><ImageIcon className="w-5 h-5 text-amber-500" />Unit Images ({previewImages.length})</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 py-4">
            {previewImages.map((img, idx) => (
              <div key={idx} className="relative aspect-video">
                <img src={img} alt={`Unit image ${idx + 1}`} className="w-full h-full object-cover rounded-lg border border-slate-600" onError={(e) => { e.target.src = 'https://via.placeholder.com/300x200?text=Image+Not+Found'; }} />
                <a href={img} target="_blank" rel="noopener noreferrer" className="absolute top-2 right-2 p-1 bg-slate-900/70 rounded hover:bg-slate-800"><ExternalLink className="w-4 h-4 text-slate-300" /></a>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default StagingTab;
