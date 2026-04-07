import React, { useState, useCallback, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import { API } from '../../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

const UnavailabilityTab = ({ fetchData, onStatsUpdate }) => {
  const [unavailReviews, setUnavailReviews] = useState([]);
  const [unavailStats, setUnavailStats] = useState({ pending: 0, confirmed: 0, false_positive: 0, high_priority: 0 });
  const [unavailLoading, setUnavailLoading] = useState(false);
  const [selectedUnavailReviews, setSelectedUnavailReviews] = useState([]);
  const [unavailReviewDialogOpen, setUnavailReviewDialogOpen] = useState(false);
  const [selectedUnavailUnit, setSelectedUnavailUnit] = useState(null);
  const [unavailReviewNotes, setUnavailReviewNotes] = useState('');

  const fetchUnavailStats = useCallback(async () => {
    try {
      const timestamp = Date.now();
      const response = await axios.get(`${API}/admin/unavailability-reviews/stats?_t=${timestamp}`, { withCredentials: true });
      const newStats = {
        pending: response.data.total_pending || 0,
        confirmed: response.data.total_confirmed || 0,
        false_positive: response.data.total_false_positive || 0,
        high_priority: response.data.high_priority_count || 0
      };
      setUnavailStats(newStats);
      if (onStatsUpdate) onStatsUpdate(newStats);
    } catch (error) {
      console.error('Error fetching unavailability stats:', error);
    }
  }, [onStatsUpdate]);

  const fetchUnavailReviews = useCallback(async () => {
    setUnavailLoading(true);
    try {
      const timestamp = Date.now();
      const response = await axios.get(`${API}/admin/unavailability-reviews?status=pending&limit=100&_t=${timestamp}`, { withCredentials: true });
      setUnavailReviews(response.data.items || []);
      setSelectedUnavailReviews([]);
    } catch (error) {
      console.error('Error fetching unavailability reviews:', error);
      toast.error('Failed to load unavailability reviews');
    } finally {
      setUnavailLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUnavailReviews();
    fetchUnavailStats();
  }, [fetchUnavailReviews, fetchUnavailStats]);

  const handleUnavailReview = async (reviewId, status) => {
    try {
      await axios.put(`${API}/admin/unavailability-reviews/${reviewId}`, {
        review_status: status, reviewer_notes: unavailReviewNotes
      }, { withCredentials: true });
      toast.success(status === 'confirmed_unavailable' ? 'Unit marked as unavailable' : 'Flag dismissed');
      setUnavailReviewDialogOpen(false);
      setSelectedUnavailUnit(null);
      setUnavailReviewNotes('');
      fetchUnavailReviews();
      fetchUnavailStats();
      fetchData();
    } catch (error) {
      console.error('Error reviewing:', error);
      toast.error(error.response?.data?.detail || 'Failed to process review');
    }
  };

  const handleBulkUnavailReview = async (status) => {
    if (selectedUnavailReviews.length === 0) { toast.error('No items selected'); return; }
    try {
      await axios.post(`${API}/admin/unavailability-reviews/bulk-review`, {
        review_ids: selectedUnavailReviews, review_status: status,
        reviewer_notes: `Bulk review: ${selectedUnavailReviews.length} items`
      }, { withCredentials: true });
      toast.success(`${selectedUnavailReviews.length} items ${status === 'confirmed_unavailable' ? 'marked unavailable' : 'dismissed'}`);
      setSelectedUnavailReviews([]);
      fetchUnavailReviews();
      fetchUnavailStats();
      fetchData();
    } catch (error) {
      console.error('Error bulk reviewing:', error);
      toast.error(error.response?.data?.detail || 'Failed to process bulk review');
    }
  };

  const toggleUnavailSelection = (reviewId) => {
    setSelectedUnavailReviews(prev => prev.includes(reviewId) ? prev.filter(id => id !== reviewId) : [...prev, reviewId]);
  };

  const toggleSelectAllUnavail = () => {
    if (selectedUnavailReviews.length === unavailReviews.length) setSelectedUnavailReviews([]);
    else setSelectedUnavailReviews(unavailReviews.map(r => r.id));
  };

  return (
    <>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-400" /> Unavailability Review
            </h3>
            <p className="text-sm text-slate-400">Units not found in recent crawls - may be rented or temporarily unavailable</p>
            <div className="flex gap-4 mt-2 text-sm">
              <span className="text-orange-400">Pending: {unavailStats.pending}</span>
              <span className="text-red-400">Confirmed: {unavailStats.confirmed}</span>
              <span className="text-green-400">False Positives: {unavailStats.false_positive}</span>
              {unavailStats.high_priority > 0 && <span className="text-yellow-400 font-semibold">High Priority (3+ misses): {unavailStats.high_priority}</span>}
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={fetchUnavailReviews} variant="outline" className="border-slate-600 text-slate-200 hover:bg-slate-700" disabled={unavailLoading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${unavailLoading ? 'animate-spin' : ''}`} /> Refresh
            </Button>
            {selectedUnavailReviews.length > 0 && (
              <>
                <Button onClick={() => handleBulkUnavailReview('false_positive')} variant="outline" className="border-green-600 text-green-400 hover:bg-green-900/30">
                  <CheckCircle className="w-4 h-4 mr-2" /> Dismiss Selected ({selectedUnavailReviews.length})
                </Button>
                <Button onClick={() => handleBulkUnavailReview('confirmed_unavailable')} className="bg-red-600 hover:bg-red-700 text-white">
                  <XCircle className="w-4 h-4 mr-2" /> Mark Unavailable ({selectedUnavailReviews.length})
                </Button>
              </>
            )}
          </div>
        </div>

        {unavailLoading ? (
          <div className="flex items-center justify-center py-12"><RefreshCw className="w-8 h-8 animate-spin text-orange-400" /><span className="ml-3 text-slate-400">Loading...</span></div>
        ) : unavailReviews.length === 0 ? (
          <div className="text-center py-12 text-slate-400"><CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" /><p className="text-lg">No pending unavailability reviews</p></div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700 hover:bg-transparent">
                  <TableHead className="text-slate-300 w-10"><input type="checkbox" checked={selectedUnavailReviews.length === unavailReviews.length && unavailReviews.length > 0} onChange={toggleSelectAllUnavail} className="rounded border-slate-600" /></TableHead>
                  <TableHead className="text-slate-300">Unit</TableHead>
                  <TableHead className="text-slate-300">Building</TableHead>
                  <TableHead className="text-slate-300">Rent</TableHead>
                  <TableHead className="text-slate-300">Beds</TableHead>
                  <TableHead className="text-slate-300 text-center">Misses</TableHead>
                  <TableHead className="text-slate-300">First Detected</TableHead>
                  <TableHead className="text-slate-300 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {unavailReviews.map((review) => (
                  <TableRow key={review.id} className={`border-slate-700 hover:bg-slate-700/30 ${review.consecutive_misses >= 3 ? 'bg-orange-900/10' : ''}`}>
                    <TableCell><input type="checkbox" checked={selectedUnavailReviews.includes(review.id)} onChange={() => toggleUnavailSelection(review.id)} className="rounded border-slate-600" /></TableCell>
                    <TableCell className="text-slate-200 font-medium">#{review.unit_number}</TableCell>
                    <TableCell><div className="text-slate-200">{review.building_name}</div><div className="text-xs text-slate-400">{review.building_address}</div></TableCell>
                    <TableCell className="text-amber-400 font-medium">${review.rent?.toLocaleString()}/mo</TableCell>
                    <TableCell className="text-slate-300">{review.bedrooms === 0 ? 'Studio' : `${review.bedrooms} BR`}</TableCell>
                    <TableCell className="text-center">
                      <Badge className={`${review.consecutive_misses >= 3 ? 'bg-red-500/20 text-red-400 border-red-500/30' : review.consecutive_misses >= 2 ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' : 'bg-slate-600/50 text-slate-300 border-slate-500/30'}`}>{review.consecutive_misses}x</Badge>
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">{new Date(review.created_at).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button size="sm" variant="outline" className="border-green-600 text-green-400 hover:bg-green-900/30" onClick={() => handleUnavailReview(review.id, 'false_positive')}><CheckCircle className="w-4 h-4" /></Button>
                        <Button size="sm" className="bg-red-600 hover:bg-red-700" onClick={() => { setSelectedUnavailUnit(review); setUnavailReviewDialogOpen(true); }}><XCircle className="w-4 h-4" /></Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* Confirm Unavailability Dialog */}
      <Dialog open={unavailReviewDialogOpen} onOpenChange={setUnavailReviewDialogOpen}>
        <DialogContent className="bg-slate-800 border-orange-500/30">
          <DialogHeader>
            <DialogTitle className="text-slate-100 flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-orange-500" />Confirm Unit Unavailable</DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedUnavailUnit && (<>Mark unit <span className="text-amber-400">#{selectedUnavailUnit.unit_number}</span> at <span className="text-slate-200">{selectedUnavailUnit.building_name}</span> as unavailable?<br /><span className="text-orange-400">This unit was not found in {selectedUnavailUnit.consecutive_misses} consecutive crawl(s).</span></>)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedUnavailUnit && (
              <div className="bg-slate-700/30 rounded-lg p-4 space-y-2">
                <div className="flex justify-between"><span className="text-slate-400">Rent:</span><span className="text-amber-400 font-medium">${selectedUnavailUnit.rent?.toLocaleString()}/mo</span></div>
                <div className="flex justify-between"><span className="text-slate-400">Bedrooms:</span><span className="text-slate-200">{selectedUnavailUnit.bedrooms === 0 ? 'Studio' : `${selectedUnavailUnit.bedrooms} BR`}</span></div>
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="unavail-notes" className="text-slate-200">Notes (optional)</Label>
              <Textarea id="unavail-notes" placeholder="Add any notes..." value={unavailReviewNotes} onChange={(e) => setUnavailReviewNotes(e.target.value)} className="bg-slate-700/50 border-slate-600 text-slate-100 min-h-[80px]" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setUnavailReviewDialogOpen(false); setSelectedUnavailUnit(null); setUnavailReviewNotes(''); }} className="border-slate-600 text-slate-300">Cancel</Button>
            <Button variant="outline" onClick={() => { if (selectedUnavailUnit) handleUnavailReview(selectedUnavailUnit.id, 'false_positive'); }} className="border-green-600 text-green-400 hover:bg-green-900/30"><CheckCircle className="w-4 h-4 mr-2" />Dismiss Flag</Button>
            <Button onClick={() => { if (selectedUnavailUnit) handleUnavailReview(selectedUnavailUnit.id, 'confirmed_unavailable'); }} className="bg-red-600 hover:bg-red-700 text-white"><XCircle className="w-4 h-4 mr-2" />Confirm Unavailable</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default UnavailabilityTab;
