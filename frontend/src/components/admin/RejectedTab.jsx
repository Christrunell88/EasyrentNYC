import React, { useState, useCallback, useEffect } from 'react';
import axios from '../../utils/axiosConfig';
import { API } from '../../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { RefreshCw, CheckCircle, XCircle, RotateCcw } from 'lucide-react';

const RejectedTab = ({ fetchData }) => {
  const [rejectedStagingUnits, setRejectedStagingUnits] = useState([]);
  const [rejectedStagingLoading, setRejectedStagingLoading] = useState(false);

  const fetchRejectedStagingUnits = useCallback(async () => {
    setRejectedStagingLoading(true);
    try {
      const timestamp = Date.now();
      const response = await axios.get(`${API}/admin/staging/rejected?limit=100&_t=${timestamp}`, { withCredentials: true });
      setRejectedStagingUnits(response.data.items || []);
    } catch (error) {
      console.error('Error fetching rejected units:', error);
      toast.error('Failed to load rejected staging units');
    } finally {
      setRejectedStagingLoading(false);
    }
  }, []);

  useEffect(() => { fetchRejectedStagingUnits(); }, [fetchRejectedStagingUnits]);

  const handleReconsiderRejected = async (stagingId) => {
    try {
      await axios.put(`${API}/admin/staging/rejected/${stagingId}/reconsider`, {}, { withCredentials: true });
      toast.success('Unit moved back to pending review');
      fetchRejectedStagingUnits();
    } catch (error) {
      console.error('Error reconsidering:', error);
      toast.error(error.response?.data?.detail || 'Failed to reconsider unit');
    }
  };

  const handleApproveRejectedDirectly = async (stagingId) => {
    try {
      await axios.put(`${API}/admin/staging/rejected/${stagingId}/approve-direct`, {}, { withCredentials: true });
      toast.success('Unit approved and added to production!');
      fetchRejectedStagingUnits();
      fetchData();
    } catch (error) {
      console.error('Error approving:', error);
      toast.error(error.response?.data?.detail || 'Failed to approve unit');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2"><XCircle className="w-5 h-5 text-red-400" />Rejected Staging Units</h3>
          <p className="text-sm text-slate-400">Units rejected during staging review. You can reconsider or approve them later.</p>
          <p className="text-sm text-red-400 mt-1">Total: {rejectedStagingUnits.length} rejected units</p>
        </div>
        <Button onClick={fetchRejectedStagingUnits} variant="outline" className="border-slate-600 text-slate-200 hover:bg-slate-700" disabled={rejectedStagingLoading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${rejectedStagingLoading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {rejectedStagingLoading ? (
        <div className="flex items-center justify-center py-12"><RefreshCw className="w-8 h-8 animate-spin text-red-400" /><span className="ml-3 text-slate-400">Loading...</span></div>
      ) : rejectedStagingUnits.length === 0 ? (
        <div className="text-center py-12 text-slate-400"><CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" /><p className="text-lg">No rejected units</p></div>
      ) : (
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-slate-700 hover:bg-transparent">
                <TableHead className="text-slate-300">Unit</TableHead>
                <TableHead className="text-slate-300">Building</TableHead>
                <TableHead className="text-slate-300">Rent</TableHead>
                <TableHead className="text-slate-300">Beds</TableHead>
                <TableHead className="text-slate-300">Rejection Reason</TableHead>
                <TableHead className="text-slate-300">Rejected On</TableHead>
                <TableHead className="text-slate-300 text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rejectedStagingUnits.map((unit) => (
                <TableRow key={unit.id} className="border-slate-700 hover:bg-slate-700/30">
                  <TableCell className="text-slate-200 font-medium">#{unit.unit_number}</TableCell>
                  <TableCell><div className="text-slate-200">{unit.building_name}</div><div className="text-xs text-slate-400">{unit.building_address}</div></TableCell>
                  <TableCell className="text-amber-400 font-medium">${unit.rent?.toLocaleString()}/mo</TableCell>
                  <TableCell className="text-slate-300">{unit.bedrooms === 0 ? 'Studio' : `${unit.bedrooms} BR`}</TableCell>
                  <TableCell className="text-red-400 text-sm max-w-[200px] truncate">{unit.rejection_reason || 'No reason provided'}</TableCell>
                  <TableCell className="text-slate-400 text-sm">{unit.rejected_at ? new Date(unit.rejected_at).toLocaleDateString() : 'Unknown'}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex gap-2 justify-end">
                      <Button size="sm" variant="outline" className="border-amber-600 text-amber-400 hover:bg-amber-900/30" onClick={() => handleReconsiderRejected(unit.id)}>
                        <RotateCcw className="w-4 h-4 mr-1" /> Reconsider
                      </Button>
                      <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => handleApproveRejectedDirectly(unit.id)}>
                        <CheckCircle className="w-4 h-4 mr-1" /> Approve
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
  );
};

export default RejectedTab;
