import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { toast } from '../../hooks/use-toast';
import LogisticsMap from './LogisticsMap';
import PortCard from './PortCard';
import PortDetailsModal from './PortDetailsModal';
import UNCTADDataPanel from './UNCTADDataPanel';
import { 
  FilterBar, 
  SearchFilter, 
  SelectFilter, 
  ViewModeToggle, 
  ResultsCounter,
  FilterDivider 
} from '../common/FilterComponents';
import { Anchor, Ship, MapPin, BarChart3 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MaritimeLogisticsTab({ language = 'fr' }) {
  const [ports, setPorts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPort, setSelectedPort] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('map');

  const texts = {
    fr: {
      title: "Logistique Maritime",
      subtitle: "68 ports africains avec statistiques TRS et connectivité",
      filterByCountry: "Pays",
      allCountries: "Tous les pays",
      search: "Rechercher un port...",
      portsLabel: "port(s)",
      loading: "Chargement...",
      errorTitle: "Erreur",
      errorLoad: "Impossible de charger les données",
      noResults: "Aucun port trouvé",
      stats: {
        totalPorts: "Ports totaux",
        withTRS: "Avec données TRS",
        avgDwell: "Temps moyen",
        topRegion: "Région principale"
      }
    },
    en: {
      title: "Maritime Logistics",
      subtitle: "68 African ports with TRS statistics and connectivity",
      filterByCountry: "Country",
      allCountries: "All countries",
      search: "Search a port...",
      portsLabel: "port(s)",
      loading: "Loading...",
      errorTitle: "Error",
      errorLoad: "Unable to load data",
      noResults: "No ports found",
      stats: {
        totalPorts: "Total ports",
        withTRS: "With TRS data",
        avgDwell: "Avg. dwell time",
        topRegion: "Top region"
      }
    }
  };

  const t = texts[language];

  // Country options for filter
  const countryOptions = [
    { value: 'ALL', label: t.allCountries, icon: '🌍' },
    { value: 'DZA', label: language === 'fr' ? 'Algérie' : 'Algeria', icon: '🇩🇿' },
    { value: 'MAR', label: language === 'fr' ? 'Maroc' : 'Morocco', icon: '🇲🇦' },
    { value: 'EGY', label: language === 'fr' ? 'Égypte' : 'Egypt', icon: '🇪🇬' },
    { value: 'ZAF', label: language === 'fr' ? 'Afrique du Sud' : 'South Africa', icon: '🇿🇦' },
    { value: 'NGA', label: language === 'fr' ? 'Nigéria' : 'Nigeria', icon: '🇳🇬' },
    { value: 'KEN', label: 'Kenya', icon: '🇰🇪' },
    { value: 'TZA', label: language === 'fr' ? 'Tanzanie' : 'Tanzania', icon: '🇹🇿' },
    { value: 'CIV', label: language === 'fr' ? "Côte d'Ivoire" : 'Ivory Coast', icon: '🇨🇮' },
    { value: 'GHA', label: 'Ghana', icon: '🇬🇭' },
    { value: 'SEN', label: language === 'fr' ? 'Sénégal' : 'Senegal', icon: '🇸🇳' },
    { value: 'AGO', label: 'Angola', icon: '🇦🇴' },
    { value: 'CMR', label: language === 'fr' ? 'Cameroun' : 'Cameroon', icon: '🇨🇲' },
    { value: 'DJI', label: 'Djibouti', icon: '🇩🇯' }
  ];

  useEffect(() => {
    fetchPorts(selectedCountry);
  }, [selectedCountry]);

  const fetchPorts = async (countryIso) => {
    setLoading(true);
    try {
      const url = countryIso && countryIso !== 'ALL'
        ? `${API}/logistics/ports?country_iso=${countryIso}`
        : `${API}/logistics/ports`;
      
      const response = await axios.get(url);
      setPorts(response.data.ports || []);
    } catch (error) {
      console.error('Error fetching ports:', error);
      toast({
        title: t.errorTitle,
        description: t.errorLoad,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePortClick = async (port) => {
    try {
      const response = await axios.get(`${API}/logistics/ports/${port.port_id}`);
      setSelectedPort(response.data);
      setIsModalOpen(true);
    } catch (error) {
      console.error('Error fetching port details:', error);
      toast({
        title: t.errorTitle,
        description: t.errorLoad,
        variant: "destructive",
      });
    }
  };

  // Filter ports by search query
  const filteredPorts = ports.filter(port => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      port.port_name?.toLowerCase().includes(query) ||
      port.country_name?.toLowerCase().includes(query) ||
      port.port_id?.toLowerCase().includes(query)
    );
  });

  // Calculate stats
  const portsWithTRS = ports.filter(p => p.trs_analysis?.container_dwell_time_days && p.trs_analysis.container_dwell_time_days !== 'NA').length;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Compact Header */}
      <div className="flex items-center justify-between bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-4 rounded-xl shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
            <Ship className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold">{t.title}</h2>
            <p className="text-blue-100 text-sm">{t.subtitle}</p>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="hidden md:flex items-center gap-4">
          <div className="text-center px-4 border-r border-white/20">
            <p className="text-2xl font-bold">{ports.length}</p>
            <p className="text-xs text-blue-100">{t.stats.totalPorts}</p>
          </div>
          <div className="text-center px-4">
            <p className="text-2xl font-bold">{portsWithTRS}</p>
            <p className="text-xs text-blue-100">{t.stats.withTRS}</p>
          </div>
        </div>
      </div>

      {/* Unified Filter Bar */}
      <FilterBar>
        <SearchFilter
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder={t.search}
          size="default"
        />
        
        <FilterDivider />
        
        <SelectFilter
          label={t.filterByCountry}
          value={selectedCountry}
          onChange={setSelectedCountry}
          options={countryOptions}
          placeholder={t.allCountries}
        />
        
        <FilterDivider />
        
        <ViewModeToggle
          value={viewMode}
          onChange={setViewMode}
          modes={['map', 'grid']}
        />
        
        <div className="flex-1" />
        
        <ResultsCounter
          count={filteredPorts.length}
          total={ports.length}
          label={t.portsLabel}
        />
      </FilterBar>

      {/* Main Content */}
      {loading ? (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="skeleton skeleton-card" />
          ))}
        </div>
      ) : filteredPorts.length === 0 ? (
        <Card className="py-12">
          <div className="no-results">
            <Anchor className="no-results-icon" />
            <p className="text-lg font-medium">{t.noResults}</p>
          </div>
        </Card>
      ) : viewMode === 'map' ? (
        <div className="map-list-layout">
          <Card className="overflow-hidden" style={{ minHeight: '500px' }}>
            <LogisticsMap 
              ports={filteredPorts} 
              onPortClick={handlePortClick}
              language={language}
            />
          </Card>
          <Card className="hidden lg:block">
            <CardHeader className="py-3 border-b">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                {language === 'fr' ? 'Liste des ports' : 'Port list'}
              </CardTitle>
            </CardHeader>
            <div className="scroll-container" style={{ maxHeight: '450px' }}>
              <div className="p-2 space-y-2">
                {filteredPorts.slice(0, 20).map((port) => (
                  <div
                    key={port.port_id}
                    className="p-3 rounded-lg border border-gray-100 hover:border-blue-200 hover:bg-blue-50/50 cursor-pointer transition-all"
                    onClick={() => handlePortClick(port)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{port.port_name}</p>
                        <p className="text-xs text-gray-500">{port.country_name}</p>
                      </div>
                      {port.trs_analysis?.container_dwell_time_days && 
                       port.trs_analysis.container_dwell_time_days !== 'NA' && (
                        <Badge variant="secondary" className="text-xs">
                          {port.trs_analysis.container_dwell_time_days}j
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      ) : (
        <div className="cards-grid stagger-animation">
          {filteredPorts.map((port) => (
            <PortCard
              key={port.port_id}
              port={port}
              onClick={() => handlePortClick(port)}
              language={language}
            />
          ))}
        </div>
      )}

      {/* UNCTAD Data Panel */}
      <UNCTADDataPanel language={language} />

      {/* Port Details Modal */}
      <PortDetailsModal
        port={selectedPort}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        language={language}
      />
    </div>
  );
}
