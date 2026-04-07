import React, { useState, useCallback, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import { API } from '../../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Home, RefreshCw, CheckCircle, RotateCcw } from 'lucide-react';

const RentedTab = ({ fetchData }) => {
  const [unavailableUnits, setUnavailableUnits] = useState([]);
  const [unavailableUnitsLoading, setUnavailableUnitsLoading] = useState(false);
  const [selectedUnavailableUnits, setSelectedUnavailableUnits] = useState([]);
  const [relistDialogOpen, setRelistDialogOpen] = useState(false);
  const [selectedRelistUnit, setSelectedRelistUnit] = useState(null);
  const [relistRent, setRelistRent] = useState('');
  const [relistNotes, setRelistNotes] = useState('');

  const fetchUnavailableUnits = useCallback(async () => {
    setUnavailableUnitsLoading(true);
    try {
      const timestamp = Date.now();
      const response = await axios.get(`${API}/admin/units/unavailable?limit=100&_t=${timestamp}`, { withCredentials: true });
      setUnavailableUnits(response.data.items || []);
      setSelectedUnavailableUnits([]);
    } catch (error) {
      console.error('Error fetching unavailable units:', error);
      toast.error('Failed to load unavailable units');
    } finally {
      setUnavailableUnitsLoading(false);
    }
  }, []);

  useEffect(() => { fetchUnavailableUnits(); }, [fetchUnavailableUnits]);

  const handleRelistUnit = async () => {
    if (!selectedRelistUnit) return;
    try {
      await axios.put(`${API}/admin/units/${selectedRelistUnit.id}/relist`, {
        rent: relistRent ? parseInt(relistRent) : null, notes: relistNotes || null
      }, { withCredentials: true });
      toast.success(`Unit ${selectedRelistUnit.unit_number} has been re-listed!`);
      setRelistDialogOpen(false); setSelectedRelistUnit(null); setRelistRent(''); setRelistNotes('');
      fetchUnavailableUnits(); fetchData();
    } catch (error) {
      console.error('Error re-listing:', error);
      toast.error(error.response?.data?.detail || 'Failed to re-list unit');
    }
  };

  const handleBulkRelist = async () => {
    if (selectedUnavailableUnits.length === 0) { toast.error('No units selected'); return; }
    try {
      await axios.post(`${API}/admin/units/bulk-relist`, { unit_ids: selectedUnavailableUnits, notes: 'Bulk re-listed from admin panel' }, { withCredentials: true });
      toast.success(`${selectedUnavailableUnits.length} units re-listed!`);
      setSelectedUnavailableUnits([]); fetchUnavailableUnits(); fetchData();
    } catch (error) {
      console.error('Error bulk re-listing:', error);
      toast.error(error.response?.data?.detail || 'Failed to re-list units');
    }
  };

  const toggleUnavailableSelection = (unitId) => {
    setSelectedUnavailableUnits(prev => prev.includes(unitId) ? prev.filter(id => id !== unitId) : [...prev, unitId]);
  };

  const toggleSelectAllUnavailable = () => {
    if (selectedUnavailableUnits.length === unavailableUnits.length) setSelectedUnavailableUnits([]);
    else setSelectedUnavailableUnits(unavailableUnits.map(u => u.id));
  };

  return (
    <>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2"><Home className="w-5 h-5 text-purple-400" />Rented / Unavailable Units</h3>
            <p className="text-sm text-slate-400">Units currently marked as rented or unavailable. Re-list them when they become available again.</p>
            <p className="text-sm text-purple-400 mt-1">Total: {unavailableUnits.length} units</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={fetchUnavailableUnits} variant="outline" className="border-slate-600 text-slate-200 hover:bg-slate-700" disabled={unavailableUnitsLoading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${unavailableUnitsLoading ? 'animate-spin' : ''}`} /> Refresh
            </Button>
            {selectedUnavailableUnits.length > 0 && (
              <Button onClick={handleBulkRelist} className="bg-green-600 hover:bg-green-700 text-white">
                <RotateCcw className="w-4 h-4 mr-2" /> Re-list Selected ({selectedUnavailableUnits.length})
              </Button>
            )}
          </div>
        </div>

        {unavailableUnitsLoading ? (
          <div className="flex items-center justify-center py-12"><RefreshCw className="w-8 h-8 animate-spin text-purple-400" /><span className="ml-3 text-slate-400">Loading...</span></div>
        ) : unavailableUnits.length === 0 ? (
          <div className="text-center py-12 text-slate-400"><Home className="w-12 h-12 mx-auto mb-4 text-slate-600" /><p className="text-lg">No unavailable units</p></div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700 hover:bg-transparent">
                  <TableHead className="text-slate-300 w-10"><input type="checkbox" checked={selectedUnavailableUnits.length === unavailableUnits.length && unavailableUnits.length > 0} onChange={toggleSelectAllUnavailable} className="rounded border-slate-600" /></TableHead>
                  <TableHead className="text-slate-300">Unit</TableHead>
                  <TableHead className="text-slate-300">Building</TableHead>
                  <TableHead className="text-slate-300">Rent</TableHead>
                  <TableHead className="text-slate-300">Beds</TableHead>
                  <TableHead className="text-slate-300">Status</TableHead>
                  <TableHead className="text-slate-300">Marked Off</TableHead>
                  <TableHead className="text-slate-300 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {unavailableUnits.map((unit) => (
                  <TableRow key={unit.id} className="border-slate-700 hover:bg-slate-700/30">
                    <TableCell><input type="checkbox" checked={selectedUnavailableUnits.includes(unit.id)} onChange={() => toggleUnavailableSelection(unit.id)} className="rounded border-slate-600" /></TableCell>
                    <TableCell className="text-slate-200 font-medium">#{unit.unit_number}</TableCell>
                    <TableCell><div className="text-slate-200">{unit.building_name}</div><div className="text-xs text-slate-400">{unit.building_address}</div></TableCell>
                    <TableCell className="text-amber-400 font-medium">${unit.rent?.toLocaleString()}/mo</TableCell>
                    <TableCell className="text-slate-300">{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`}</TableCell>
                    <TableCell><Badge className={`${unit.lifecycle_status === 'rented' ? 'bg-purple-500/20 text-purple-400 border-purple-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'}`}>{unit.lifecycle_status || 'unavailable'}</Badge></TableCell>
                    <TableCell className="text-slate-400 text-sm">{unit.unavailable_confirmed_at ? new Date(unit.unavailable_confirmed_at).toLocaleDateString() : unit.updated_at ? new Date(unit.updated_at).toLocaleDateString() : 'Unknown'}</TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => { setSelectedRelistUnit(unit); setRelistRent(unit.rent?.toString() || ''); setRelistDialogOpen(true); }}>
                        <RotateCcw className="w-4 h-4 mr-1" /> Re-list
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      {/* Re-list Dialog */}
      <Dialog open={relistDialogOpen} onOpenChange={setRelistDialogOpen}>
        <DialogContent className="bg-slate-800 border-green-500/30">
          <DialogHeader>
            <DialogTitle className="text-slate-100 flex items-center gap-2"><RotateCcw className="w-5 h-5 text-green-500" />Re-list Unit</DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedRelistUnit && (<>Re-list unit <span className="text-amber-400">#{selectedRelistUnit.unit_number}</span> at <span className="text-slate-200">{selectedRelistUnit.building_name}</span></>)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {selectedRelistUnit && (
              <div className="bg-slate-700/30 rounded-lg p-4 space-y-2">
                <div className="flex justify-between"><span className="text-slate-400">Current Status:</span><Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">{selectedRelistUnit.lifecycle_status || 'unavailable'}</Badge></div>
                <div className="flex justify-between"><span className="text-slate-400">Bedrooms:</span><span className="text-slate-200">{selectedRelistUnit.bedrooms === 0 ? 'Studio' : `${selectedRelistUnit.bedrooms} BR`}</span></div>
              </div>
            )}
            <div className="space-y-2">
              <Label className="text-slate-200">New Rent Price (optional)</Label>
              <Input type="number" placeholder="Leave empty to keep current rent" value={relistRent} onChange={(e) => setRelistRent(e.target.value)} className="bg-slate-700/50 border-slate-600 text-slate-100" />
              <p className="text-xs text-slate-400">Current rent: ${selectedRelistUnit?.rent?.toLocaleString()}/mo</p>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-200">Notes (optional)</Label>
              <Textarea placeholder="Add any notes..." value={relistNotes} onChange={(e) => setRelistNotes(e.target.value)} className="bg-slate-700/50 border-slate-600 text-slate-100 min-h-[80px]" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setRelistDialogOpen(false); setSelectedRelistUnit(null); setRelistRent(''); setRelistNotes(''); }} className="border-slate-600 text-slate-300">Cancel</Button>
            <Button onClick={handleRelistUnit} className="bg-green-600 hover:bg-green-700 text-white"><RotateCcw className="w-4 h-4 mr-2" />Re-list Unit</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default RentedTab;
