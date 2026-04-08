import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from '../../utils/axiosConfig';
import { API } from '../../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Building2, Plus, RefreshCw, Download, ExternalLink, Sparkles, Trash2, Image as ImageIcon, Zap, XCircle, CheckCircle2, AlertTriangle } from 'lucide-react';

const ImportTab = ({ fetchStagingStats }) => {
  const [propertySearchQuery, setPropertySearchQuery] = useState('');
  const [propertySearchResults, setPropertySearchResults] = useState([]);
  const [propertySearching, setPropertySearching] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [crawlingProperty, setCrawlingProperty] = useState(false);
  const [managementCompanies, setManagementCompanies] = useState([]);
  const [discoveryArea, setDiscoveryArea] = useState('all');
  const [discovering, setDiscovering] = useState(false);

  // Import preview state
  const [previewOpen, setPreviewOpen] = useState(false);
  const [crawledBuilding, setCrawledBuilding] = useState(null);
  const [crawledUnits, setCrawledUnits] = useState([]);
  const [crawledImages, setCrawledImages] = useState([]);
  const [importing, setImporting] = useState(false);

  // Batch crawl state
  const [batchJobId, setBatchJobId] = useState(null);
  const [batchStatus, setBatchStatus] = useState(null);
  const batchPollRef = useRef(null);

  useEffect(() => {
    fetchManagementCompanies();
    return () => { if (batchPollRef.current) clearInterval(batchPollRef.current); };
  }, []);

  const fetchManagementCompanies = async () => {
    try {
      const response = await axios.get(`${API}/admin/management-companies`, { withCredentials: true });
      setManagementCompanies(response.data.companies || []);
    } catch (error) {
      console.error('Error fetching management companies:', error);
    }
  };

  const pollBatchStatus = useCallback(async (jobId) => {
    try {
      const response = await axios.get(`${API}/admin/batch-crawl/status/${jobId}`, { withCredentials: true });
      setBatchStatus(response.data);
      if (response.data.status === 'completed' || response.data.status === 'cancelled') {
        if (batchPollRef.current) clearInterval(batchPollRef.current);
        batchPollRef.current = null;
        fetchStagingStats();
        toast.success(`Batch crawl finished: ${response.data.total_units} units from ${response.data.total_buildings} buildings`);
      }
    } catch (error) {
      console.error('Error polling batch status:', error);
    }
  }, [fetchStagingStats]);

  const handleStartBatchCrawl = async () => {
    try {
      const response = await axios.post(`${API}/admin/batch-crawl/start`, {}, { withCredentials: true });
      const jobId = response.data.job_id;
      setBatchJobId(jobId);
      setBatchStatus({ status: 'queued', total: response.data.total_companies, completed: 0, results: [] });
      toast.success(`Batch crawl started for ${response.data.total_companies} companies`);
      batchPollRef.current = setInterval(() => pollBatchStatus(jobId), 4000);
    } catch (error) {
      console.error('Batch crawl error:', error);
      toast.error(error.response?.data?.detail || 'Failed to start batch crawl');
    }
  };

  const handleCancelBatchCrawl = async () => {
    if (!batchJobId) return;
    try {
      await axios.post(`${API}/admin/batch-crawl/cancel/${batchJobId}`, {}, { withCredentials: true });
      toast.info('Batch crawl cancellation requested');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to cancel');
    }
  };

  const handlePropertySearch = async (searchType = "all") => {
    if (searchType === "all" && !propertySearchQuery.trim()) {
      toast.error('Please enter a search query');
      return;
    }
    setPropertySearching(true);
    setPropertySearchResults([]);
    try {
      const response = await axios.post(`${API}/admin/property-search`,
        { query: propertySearchQuery || "no fee apartments NYC", search_type: searchType },
        { withCredentials: true }
      );
      setPropertySearchResults(response.data.results || []);
      if (response.data.results?.length === 0) {
        toast.info('No building websites found. Try a different search query.');
      } else {
        const priorityCount = response.data.priority_count || 0;
        if (priorityCount > 0) {
          toast.success(`Found ${response.data.results.length} buildings (${priorityCount} from major management companies)`);
        } else {
          toast.success(`Found ${response.data.results.length} potential buildings`);
        }
      }
    } catch (error) {
      console.error('Property search error:', error);
      toast.error('Search failed. Please try again.');
    } finally {
      setPropertySearching(false);
    }
  };

  const handleBrowseManagementCompanies = () => {
    setPropertySearchResults(managementCompanies.map(company => ({
      name: company.name,
      url: company.availability_url,
      domain: company.website.replace("https://", "").replace("http://", ""),
      snippet: `${company.description}. Areas: ${company.neighborhoods.join(", ")}`,
      source: "curated_management_company",
      is_management_company: true
    })));
    toast.success(`Showing ${managementCompanies.length} major management companies`);
  };

  const handleDiscoverySearch = async () => {
    setDiscovering(true);
    setPropertySearchResults([]);
    try {
      const response = await axios.post(`${API}/admin/property-discovery`,
        { area: discoveryArea, search_new_construction: true, search_net_effective: true },
        { withCredentials: true }
      );
      setPropertySearchResults(response.data.results || []);
      const { new_discovery_count, known_company_count, total_found } = response.data;
      if (total_found > 0) {
        toast.success(`Discovery found ${total_found} results: ${new_discovery_count} new sources, ${known_company_count} known companies`);
      } else {
        toast.info('No new sources found. Try a different area.');
      }
    } catch (error) {
      console.error('Discovery error:', error);
      toast.error('Discovery search failed. Please try again.');
    } finally {
      setDiscovering(false);
    }
  };

  const handlePropertyCrawl = async (property) => {
    setSelectedProperty(property);
    setCrawlingProperty(true);
    try {
      const response = await axios.post(`${API}/admin/property-crawl`,
        { url: property.url, building_name: property.name },
        { withCredentials: true, timeout: 60000 }
      );

      const building = response.data.building || {};
      const units = response.data.units || [];
      const images = response.data.raw_images || [];
      const isMultiBuilding = response.data.is_multi_building || false;

      // Always show preview dialog - let user review/edit/add units manually
      setCrawledBuilding({
        name: building.name || property.name || '',
        address: building.address || '',
        neighborhood: building.neighborhood || '',
        city: building.city || 'New York',
        state: building.state || 'NY',
        zip_code: building.zip_code || '',
        source_url: property.url,
        images: images,
        is_multi_building: isMultiBuilding
      });
      setCrawledUnits(units.map((u, i) => ({
        ...u,
        _key: `unit-${i}-${Date.now()}`,
        unit_number: u.unit_number || `Unit-${i + 1}`,
        rent: u.rent || 0,
        bedrooms: u.bedrooms ?? 1,
        bathrooms: u.bathrooms ?? 1,
        square_feet: u.square_feet || null,
        images: u.images || [],
        building_address: u.building_address || building.address || ''
      })));
      setCrawledImages(images);
      setPreviewOpen(true);

      if (units.length > 0) {
        toast.success(`Found ${units.length} units! Review and import below.`);
      } else {
        toast.info(response.data.message || 'No units auto-extracted. Add units manually below.');
      }
    } catch (error) {
      console.error('Property crawl error:', error);
      // Even on error, open the preview so user can manually enter data
      setCrawledBuilding({
        name: property.name || '',
        address: '',
        neighborhood: '',
        city: 'New York',
        state: 'NY',
        zip_code: '',
        source_url: property.url
      });
      setCrawledUnits([]);
      setCrawledImages([]);
      setPreviewOpen(true);
      toast.error('Crawl had issues. You can add building and units manually.');
    } finally {
      setCrawlingProperty(false);
    }
  };

  const addCrawledUnit = () => {
    setCrawledUnits(prev => [...prev, {
      _key: `unit-new-${Date.now()}`,
      unit_number: '',
      rent: 0,
      bedrooms: 1,
      bathrooms: 1,
      square_feet: null,
      images: []
    }]);
  };

  const updateCrawledUnit = (index, field, value) => {
    setCrawledUnits(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const removeCrawledUnit = (index) => {
    setCrawledUnits(prev => prev.filter((_, i) => i !== index));
  };

  const updateCrawledBuilding = (field, value) => {
    setCrawledBuilding(prev => ({ ...prev, [field]: value }));
  };

  const handleImport = async () => {
    if (!crawledBuilding?.name?.trim()) {
      toast.error('Building name is required');
      return;
    }
    if (crawledUnits.length === 0) {
      toast.error('Add at least one unit before importing');
      return;
    }
    // Validate units
    for (let i = 0; i < crawledUnits.length; i++) {
      if (!crawledUnits[i].unit_number?.trim()) {
        toast.error(`Unit ${i + 1}: Unit number is required`);
        return;
      }
      if (!crawledUnits[i].rent || crawledUnits[i].rent <= 0) {
        toast.error(`Unit ${i + 1}: Valid rent is required`);
        return;
      }
    }

    setImporting(true);
    try {
      const response = await axios.post(`${API}/admin/property-import`, {
        building: crawledBuilding,
        units: crawledUnits.map(u => ({
          unit_number: u.unit_number,
          rent: Number(u.rent),
          bedrooms: Number(u.bedrooms),
          bathrooms: Number(u.bathrooms),
          square_feet: u.square_feet ? Number(u.square_feet) : null,
          images: u.images || [],
          building_address: u.building_address || ''
        }))
      }, { withCredentials: true });

      toast.success(response.data.message || `Imported ${crawledUnits.length} units to staging!`);
      setPreviewOpen(false);
      setCrawledBuilding(null);
      setCrawledUnits([]);
      setCrawledImages([]);
      fetchStagingStats();
    } catch (error) {
      console.error('Import error:', error);
      toast.error(error.response?.data?.detail || 'Failed to import. Please try again.');
    } finally {
      setImporting(false);
    }
  };

  return (
    <>
      <div className="space-y-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">Import New Properties</h3>
            <p className="text-sm text-slate-400">Search for building websites and import listings to staging</p>
          </div>
        </div>

        {/* Management Companies Quick Access */}
        <div className="bg-gradient-to-r from-amber-900/30 to-orange-900/30 border border-amber-500/30 rounded-lg p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <Label className="text-amber-300 font-semibold text-lg">Major Management Companies</Label>
              <p className="text-slate-400 text-sm mt-1">Quick access to known no-fee building operators</p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={handleStartBatchCrawl}
                disabled={crawlingProperty || (batchStatus && batchStatus.status === 'running')}
                className="bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700 text-white font-semibold"
                data-testid="batch-crawl-btn"
              >
                <Zap className="w-4 h-4 mr-2" /> Batch Crawl All ({managementCompanies.length})
              </Button>
              <Button onClick={handleBrowseManagementCompanies} className="bg-amber-600 hover:bg-amber-700 text-white">
                <Building2 className="w-4 h-4 mr-2" /> Browse All ({managementCompanies.length})
              </Button>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {managementCompanies.slice(0, 8).map((company, index) => (
              <button
                key={index}
                onClick={() => handlePropertyCrawl({
                  name: company.name,
                  url: company.availability_url,
                  domain: company.website.replace("https://", ""),
                  snippet: company.description,
                  is_management_company: true
                })}
                disabled={crawlingProperty}
                className="text-left p-3 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-amber-500/50 hover:bg-slate-800 transition-all group disabled:opacity-50"
              >
                <p className="text-slate-200 font-medium text-sm group-hover:text-amber-400 truncate">{company.name}</p>
                <p className="text-slate-500 text-xs truncate">{company.neighborhoods.join(", ")}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Batch Crawl Progress Panel */}
        {batchStatus && (batchStatus.status === 'running' || batchStatus.status === 'queued' || batchStatus.status === 'completed' || batchStatus.status === 'cancelled') && (
          <div className={`border rounded-lg p-6 ${
            batchStatus.status === 'completed' ? 'bg-green-900/20 border-green-500/30' :
            batchStatus.status === 'cancelled' ? 'bg-slate-800/50 border-slate-600' :
            'bg-gradient-to-r from-red-900/20 to-orange-900/20 border-orange-500/30'
          }`} data-testid="batch-crawl-panel">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center gap-3">
                {(batchStatus.status === 'running' || batchStatus.status === 'queued') && (
                  <RefreshCw className="w-5 h-5 text-orange-400 animate-spin" />
                )}
                {batchStatus.status === 'completed' && <CheckCircle2 className="w-5 h-5 text-green-400" />}
                {batchStatus.status === 'cancelled' && <XCircle className="w-5 h-5 text-slate-400" />}
                <div>
                  <h4 className="text-slate-100 font-semibold">
                    Batch Crawl {batchStatus.status === 'completed' ? 'Complete' : batchStatus.status === 'cancelled' ? 'Cancelled' : 'In Progress'}
                  </h4>
                  {batchStatus.current_company && batchStatus.status === 'running' && (
                    <p className="text-orange-300 text-sm">Currently crawling: {batchStatus.current_company}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-slate-300 text-sm font-mono">{batchStatus.completed}/{batchStatus.total}</span>
                {(batchStatus.status === 'running' || batchStatus.status === 'queued') && (
                  <Button size="sm" variant="outline" onClick={handleCancelBatchCrawl} className="border-red-500/50 text-red-400 hover:bg-red-500/10" data-testid="batch-cancel-btn">
                    <XCircle className="w-4 h-4 mr-1" /> Cancel
                  </Button>
                )}
                {(batchStatus.status === 'completed' || batchStatus.status === 'cancelled') && (
                  <Button size="sm" variant="ghost" onClick={() => { setBatchStatus(null); setBatchJobId(null); }} className="text-slate-400 hover:text-slate-200">
                    Dismiss
                  </Button>
                )}
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-700/50 rounded-full h-2.5 mb-4">
              <div
                className={`h-2.5 rounded-full transition-all duration-500 ${batchStatus.status === 'completed' ? 'bg-green-500' : 'bg-gradient-to-r from-orange-500 to-red-500'}`}
                style={{ width: `${batchStatus.total > 0 ? (batchStatus.completed / batchStatus.total) * 100 : 0}%` }}
              />
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-5 gap-4 mb-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-400">{batchStatus.successful}</p>
                <p className="text-xs text-slate-400">Successful</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-400">{batchStatus.failed}</p>
                <p className="text-xs text-slate-400">Failed</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-400">{batchStatus.no_units || 0}</p>
                <p className="text-xs text-slate-400">No Units</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-400">{batchStatus.total_units}</p>
                <p className="text-xs text-slate-400">Units Found</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-amber-400">{batchStatus.total_buildings}</p>
                <p className="text-xs text-slate-400">Buildings</p>
              </div>
            </div>

            {/* Results log */}
            {batchStatus.results && batchStatus.results.length > 0 && (
              <div className="max-h-48 overflow-y-auto space-y-1 bg-slate-900/50 rounded-lg p-3">
                {batchStatus.results.map((r, i) => (
                  <div key={i} className="flex items-center justify-between text-sm py-1 border-b border-slate-800 last:border-0">
                    <div className="flex items-center gap-2">
                      {r.status === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />}
                      {r.status === 'error' && <XCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />}
                      {r.status === 'no_units' && <AlertTriangle className="w-3.5 h-3.5 text-yellow-400 flex-shrink-0" />}
                      <span className="text-slate-300 truncate max-w-[200px]">{r.name}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      {r.status === 'success' && (
                        <span className="text-green-400">{r.units_found} units / {r.buildings_created} bldg</span>
                      )}
                      {r.status === 'no_units' && <span className="text-yellow-400">No units found</span>}
                      {r.status === 'error' && <span className="text-red-400 truncate max-w-[200px]">{r.error || 'Error'}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* AI Discovery Search */}
        <div className="bg-gradient-to-r from-purple-900/30 to-indigo-900/30 border border-purple-500/30 rounded-lg p-6">
          <div className="flex flex-col gap-4">
            <div className="flex justify-between items-start">
              <div>
                <Label className="text-purple-300 font-semibold text-lg">AI Discovery Search</Label>
                <p className="text-slate-400 text-sm mt-1">Find NEW buildings & management companies using pattern recognition</p>
              </div>
            </div>
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <Label className="text-slate-400 text-xs mb-1 block">Target Area</Label>
                <select
                  value={discoveryArea}
                  onChange={(e) => setDiscoveryArea(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 text-slate-100 rounded-md px-3 py-2"
                >
                  <option value="all">All Areas (NYC + NJ)</option>
                  <option value="Manhattan NYC">Manhattan</option>
                  <option value="Brooklyn NYC">Brooklyn</option>
                  <option value="Queens NYC">Queens</option>
                  <option value="Jersey City NJ">Jersey City</option>
                  <option value="Hoboken NJ">Hoboken</option>
                </select>
              </div>
              <Button onClick={handleDiscoverySearch} disabled={discovering} className="bg-purple-600 hover:bg-purple-700 text-white">
                {discovering ? (
                  <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Discovering...</>
                ) : (
                  <><Sparkles className="w-4 h-4 mr-2" /> Discover New Sources</>
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Manual Search Box */}
        <div className="bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-500/30 rounded-lg p-6">
          <div className="flex flex-col gap-4">
            <Label className="text-green-300 font-semibold">Manual Search</Label>
            <div className="flex gap-3">
              <Input
                placeholder="e.g., New no fee luxury buildings in Manhattan, Brooklyn and Queens"
                value={propertySearchQuery}
                onChange={(e) => setPropertySearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handlePropertySearch("all")}
                className="flex-1 bg-slate-800 border-slate-600 text-slate-100"
                data-testid="property-search-input"
              />
              <Button onClick={() => handlePropertySearch("all")} disabled={propertySearching} className="bg-green-600 hover:bg-green-700 text-white">
                {propertySearching ? (
                  <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Searching...</>
                ) : (
                  <><RefreshCw className="w-4 h-4 mr-2" /> Search</>
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Crawling indicator */}
        {crawlingProperty && (
          <div className="bg-amber-900/20 border border-amber-500/30 rounded-lg p-6 text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-amber-400 mx-auto mb-3" />
            <p className="text-amber-300 font-medium">Crawling {selectedProperty?.name || 'property'}...</p>
            <p className="text-slate-400 text-sm mt-1">Using headless browser to render and extract data. This may take 30-60 seconds.</p>
          </div>
        )}

        {/* Search Results */}
        {propertySearchResults.length > 0 && (
          <div className="space-y-4">
            <h4 className="text-slate-200 font-semibold">Found {propertySearchResults.length} Results</h4>
            <div className="grid gap-4">
              {propertySearchResults.map((property, index) => (
                <div key={index} className={`bg-slate-800/50 border rounded-lg p-4 flex justify-between items-start ${
                  property.is_management_company || property.is_known_company ? 'border-amber-500/50' :
                  property.source === 'discovery' ? 'border-purple-500/30' : 'border-slate-700'
                }`}>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h5 className="text-slate-100 font-semibold">{property.name}</h5>
                      {(property.is_management_company || property.is_known_company) && (
                        <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded">Known Company</span>
                      )}
                      {property.source === 'discovery' && !property.is_known_company && (
                        <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-0.5 rounded">New Discovery</span>
                      )}
                    </div>
                    <p className="text-slate-400 text-sm mb-2">{property.snippet}</p>
                    <a href={property.url} target="_blank" rel="noopener noreferrer" className="text-blue-400 text-sm hover:underline flex items-center gap-1">
                      <ExternalLink className="w-3 h-3" /> {property.domain}
                    </a>
                  </div>
                  <Button
                    onClick={() => handlePropertyCrawl(property)}
                    disabled={crawlingProperty}
                    size="sm"
                    className="bg-amber-600 hover:bg-amber-700 text-white ml-4"
                    data-testid={`crawl-property-${index}`}
                  >
                    {crawlingProperty && selectedProperty?.url === property.url ? (
                      <><RefreshCw className="w-4 h-4 mr-1 animate-spin" /> Crawling...</>
                    ) : (
                      <><Download className="w-4 h-4 mr-1" /> Crawl & Import</>
                    )}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Import Preview / Manual Add Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="bg-slate-800 border-amber-500/30 max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-slate-100 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-amber-500" />
              Import Preview - {crawledBuilding?.name || 'Building'}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Review and edit building details and units before importing to staging.
              {crawledUnits.length === 0 && (
                <span className="block text-amber-400 mt-1">No units were auto-extracted. Add them manually below.</span>
              )}
            </DialogDescription>
          </DialogHeader>

          {crawledBuilding && (
            <div className="space-y-6 py-4">
              {/* Building Details */}
              <div className="space-y-4">
                <h4 className="text-sm font-semibold text-amber-400 uppercase tracking-wider">Building Details</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <Label className="text-slate-300 text-xs">Building Name *</Label>
                    <Input value={crawledBuilding.name} onChange={(e) => updateCrawledBuilding('name', e.target.value)}
                      className="bg-slate-700/50 border-slate-600 text-slate-100" data-testid="import-building-name" />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-slate-300 text-xs">Address</Label>
                    <Input value={crawledBuilding.address} onChange={(e) => updateCrawledBuilding('address', e.target.value)}
                      className="bg-slate-700/50 border-slate-600 text-slate-100" data-testid="import-building-address" />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-slate-300 text-xs">Neighborhood</Label>
                    <Input value={crawledBuilding.neighborhood} onChange={(e) => updateCrawledBuilding('neighborhood', e.target.value)}
                      className="bg-slate-700/50 border-slate-600 text-slate-100" />
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="space-y-1">
                      <Label className="text-slate-300 text-xs">City</Label>
                      <Input value={crawledBuilding.city} onChange={(e) => updateCrawledBuilding('city', e.target.value)}
                        className="bg-slate-700/50 border-slate-600 text-slate-100" />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-slate-300 text-xs">State</Label>
                      <Input value={crawledBuilding.state} onChange={(e) => updateCrawledBuilding('state', e.target.value)}
                        className="bg-slate-700/50 border-slate-600 text-slate-100" />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-slate-300 text-xs">Zip</Label>
                      <Input value={crawledBuilding.zip_code} onChange={(e) => updateCrawledBuilding('zip_code', e.target.value)}
                        className="bg-slate-700/50 border-slate-600 text-slate-100" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Crawled Images Preview */}
              {crawledImages.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold text-amber-400 uppercase tracking-wider">
                    <ImageIcon className="w-4 h-4 inline mr-1" /> Crawled Images ({crawledImages.length})
                  </h4>
                  <div className="flex gap-2 overflow-x-auto py-2">
                    {crawledImages.slice(0, 10).map((img, idx) => (
                      <img key={idx} src={img} alt={`Building ${idx + 1}`}
                        className="w-20 h-14 object-cover rounded border border-slate-600 flex-shrink-0"
                        onError={(e) => { e.target.style.display = 'none'; }} />
                    ))}
                  </div>
                </div>
              )}

              {/* Units Section */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-semibold text-amber-400 uppercase tracking-wider">
                    Units ({crawledUnits.length})
                    {crawledBuilding?.is_multi_building && (
                      <span className="ml-2 text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded normal-case font-normal">
                        Multi-building detected — units grouped by address
                      </span>
                    )}
                  </h4>
                  <Button size="sm" onClick={addCrawledUnit} className="bg-green-600 hover:bg-green-700 text-white" data-testid="add-unit-manually-btn">
                    <Plus className="w-4 h-4 mr-1" /> Add Unit Manually
                  </Button>
                </div>

                {crawledUnits.length === 0 && (
                  <div className="bg-slate-700/30 rounded-lg p-8 text-center">
                    <Building2 className="w-10 h-10 text-slate-500 mx-auto mb-3" />
                    <p className="text-slate-300 font-medium">No units extracted</p>
                    <p className="text-slate-400 text-sm mt-1">Click "Add Unit Manually" to enter apartment details</p>
                  </div>
                )}

                {/* Group units by building_address for display */}
                {(() => {
                  const grouped = {};
                  crawledUnits.forEach((unit, index) => {
                    const addr = unit.building_address || crawledBuilding?.address || 'Unknown Address';
                    if (!grouped[addr]) grouped[addr] = [];
                    grouped[addr].push({ ...unit, _originalIndex: index });
                  });
                  const addresses = Object.keys(grouped);
                  const showGroupHeaders = addresses.length > 1;

                  return addresses.map((addr) => (
                    <div key={addr}>
                      {showGroupHeaders && (
                        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg px-4 py-2 mt-4 mb-2 flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-blue-400" />
                          <span className="text-blue-300 font-medium text-sm">{addr}</span>
                          <span className="text-slate-500 text-xs">({grouped[addr].length} units)</span>
                        </div>
                      )}
                      {grouped[addr].map((unit) => {
                        const index = unit._originalIndex;
                        return (
                          <div key={unit._key} className="bg-slate-700/30 border border-slate-600 rounded-lg p-4 space-y-3">
                            <div className="flex justify-between items-center">
                              <span className="text-slate-300 font-medium text-sm">Unit {index + 1}</span>
                              <Button size="sm" variant="ghost" onClick={() => removeCrawledUnit(index)} className="text-red-400 hover:text-red-300 hover:bg-red-500/10 h-7 w-7 p-0">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                            <div className="grid grid-cols-6 gap-3">
                              <div className="space-y-1">
                                <Label className="text-slate-400 text-xs">Unit # *</Label>
                                <Input value={unit.unit_number} onChange={(e) => updateCrawledUnit(index, 'unit_number', e.target.value)}
                                  placeholder="e.g., 12A" className="bg-slate-800/50 border-slate-600 text-slate-100 h-9"
                                  data-testid={`import-unit-number-${index}`} />
                              </div>
                              <div className="space-y-1">
                                <Label className="text-slate-400 text-xs">Rent ($) *</Label>
                                <Input type="number" value={unit.rent || ''} onChange={(e) => updateCrawledUnit(index, 'rent', e.target.value)}
                                  placeholder="3500" className="bg-slate-800/50 border-slate-600 text-slate-100 h-9"
                                  data-testid={`import-unit-rent-${index}`} />
                              </div>
                              <div className="space-y-1">
                                <Label className="text-slate-400 text-xs">Beds (0=Studio)</Label>
                                <Input type="number" min="0" value={unit.bedrooms} onChange={(e) => updateCrawledUnit(index, 'bedrooms', e.target.value)}
                                  className="bg-slate-800/50 border-slate-600 text-slate-100 h-9" />
                              </div>
                              <div className="space-y-1">
                                <Label className="text-slate-400 text-xs">Baths</Label>
                                <Input type="number" min="1" step="0.5" value={unit.bathrooms} onChange={(e) => updateCrawledUnit(index, 'bathrooms', e.target.value)}
                                  className="bg-slate-800/50 border-slate-600 text-slate-100 h-9" />
                              </div>
                              <div className="space-y-1">
                                <Label className="text-slate-400 text-xs">Sq Ft</Label>
                                <Input type="number" value={unit.square_feet || ''} onChange={(e) => updateCrawledUnit(index, 'square_feet', e.target.value)}
                                  placeholder="opt" className="bg-slate-800/50 border-slate-600 text-slate-100 h-9" />
                              </div>
                              <div className="space-y-1">
                                <Label className="text-slate-400 text-xs">Address</Label>
                                <Input value={unit.building_address || ''} onChange={(e) => updateCrawledUnit(index, 'building_address', e.target.value)}
                                  placeholder="Address" className="bg-slate-800/50 border-slate-600 text-slate-100 h-9 text-xs"
                                  data-testid={`import-unit-address-${index}`} />
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ));
                })()}
              </div>
            </div>
          )}

          <DialogFooter className="gap-2 pt-4 border-t border-slate-700">
            <Button variant="outline" onClick={() => setPreviewOpen(false)} className="border-slate-600 text-slate-300">
              Cancel
            </Button>
            <Button onClick={handleImport} disabled={importing || crawledUnits.length === 0}
              className="warm-gradient text-slate-900 font-semibold" data-testid="confirm-import-btn">
              {importing ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Importing...</>
              ) : (
                <><Download className="w-4 h-4 mr-2" /> Import {crawledUnits.length} Unit(s) to Staging</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ImportTab;
