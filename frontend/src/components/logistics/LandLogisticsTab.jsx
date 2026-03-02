import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { toast } from '../../hooks/use-toast';
import CorridorMap from './CorridorMap';
import CorridorCard from './CorridorCard';
import CorridorDetailsModal from './CorridorDetailsModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function LandLogisticsTab({ language = 'fr' }) {
  const [corridors, setCorridors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCorridor, setSelectedCorridor] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedType, setSelectedType] = useState('ALL');
  const [selectedImportance, setSelectedImportance] = useState('ALL');
  const [viewMode, setViewMode] = useState('map'); // 'map' or 'list'

  const texts = {
    fr: {
      title: "Logistique Terrestre Panafricaine",
      description: "Cartographie des corridors PIDA majeurs (routes et rails) reliant les ports et les bassins de production",
      type: "Type",
      allTypes: "Tous types",
      road: "Routiers",
      rail: "Ferroviaires",
      multimodal: "Multimodaux",
      importance: "Importance",
      all: "Toutes",
      highPriority: "Haute priorité",
      medium: "Moyenne",
      map: "Carte",
      list: "Liste",
      corridor: "corridor",
      corridors: "corridors",
      error: "Erreur",
      loadError: "Impossible de charger les données des corridors",
      loading: "Chargement des corridors terrestres..."
    },
    en: {
      title: "Pan-African Land Logistics",
      description: "Mapping of major PIDA corridors (roads and rails) connecting ports and production areas",
      type: "Type",
      allTypes: "All types",
      road: "Road",
      rail: "Rail",
      multimodal: "Multimodal",
      importance: "Importance",
      all: "All",
      highPriority: "High priority",
      medium: "Medium",
      map: "Map",
      list: "List",
      corridor: "corridor",
      corridors: "corridors",
      error: "Error",
      loadError: "Unable to load corridor data",
      loading: "Loading land corridors..."
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchCorridors();
  }, [selectedType, selectedImportance]);

  const fetchCorridors = async () => {
    setLoading(true);
    try {
      let url = `${API}/logistics/land/corridors`;
      const params = [];
      if (selectedType && selectedType !== 'ALL') params.push(`corridor_type=${selectedType}`);
      if (selectedImportance && selectedImportance !== 'ALL') params.push(`importance=${selectedImportance}`);
      if (params.length > 0) url += '?' + params.join('&');
      
      const response = await axios.get(url);
      setCorridors(response.data.corridors || []);
    } catch (error) {
      console.error('Error fetching corridors:', error);
      toast({
        title: t.error,
        description: t.loadError,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCorridorClick = async (corridor) => {
    setSelectedCorridor(corridor);
    setIsModalOpen(true);
  };

  return (
    <div className="space-y-4">
      {/* Header Section - Compact */}
      <Card className="bg-gradient-to-r from-slate-700 to-gray-800 text-white shadow-lg">
        <CardHeader className="py-3">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <span>🚛🚂</span>
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="text-gray-200 text-sm">
            {t.description}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Controls Section */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            {/* Type Filter */}
            <div className="flex items-center gap-3 w-full md:w-auto">
              <span className="text-sm font-semibold text-gray-700">{t.type}:</span>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="px-4 py-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500"
              >
                <option value="ALL">🌍 {t.allTypes}</option>
                <option value="road">🛣️ {t.road}</option>
                <option value="rail">🚂 {t.rail}</option>
                <option value="multimodal">🚛🚂 {t.multimodal}</option>
              </select>
            </div>

            {/* Importance Filter */}
            <div className="flex items-center gap-3 w-full md:w-auto">
              <span className="text-sm font-semibold text-gray-700">{t.importance}:</span>
              <select
                value={selectedImportance}
                onChange={(e) => setSelectedImportance(e.target.value)}
                className="px-4 py-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500"
              >
                <option value="ALL">{t.all}</option>
                <option value="high">⭐ {t.highPriority}</option>
                <option value="medium">{t.medium}</option>
              </select>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setViewMode('map')}
                variant={viewMode === 'map' ? 'default' : 'outline'}
                className={viewMode === 'map' ? 'bg-slate-700 hover:bg-slate-800' : ''}
              >
                🗺️ {t.map}
              </Button>
              <Button
                onClick={() => setViewMode('list')}
                variant={viewMode === 'list' ? 'default' : 'outline'}
                className={viewMode === 'list' ? 'bg-slate-700 hover:bg-slate-800' : ''}
              >
                📋 {t.list}
              </Button>
            </div>

            {/* Corridor Count Badge */}
            <Badge variant="secondary" className="text-lg px-4 py-2">
              {corridors.length} {corridors.length > 1 ? t.corridors : t.corridor}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Map or List View */}
      {loading ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-slate-700"></div>
              <p className="mt-4 text-gray-600">{t.loading}</p>
            </div>
          </CardContent>
        </Card>
      ) : viewMode === 'map' ? (
        <CorridorMap
          onCorridorClick={handleCorridorClick}
          selectedType={selectedType === 'ALL' ? null : selectedType}
          selectedImportance={selectedImportance === 'ALL' ? null : selectedImportance}
          language={language}
        />
      ) : (
        <div className="max-h-[550px] overflow-y-auto rounded-lg border border-gray-200 p-4 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {corridors.map((corridor) => (
              <CorridorCard
                key={corridor.corridor_id}
                corridor={corridor}
                onOpenDetails={handleCorridorClick}
                language={language}
              />
            ))}
          </div>
        </div>
      )}

      {/* Corridor Details Modal */}
      <CorridorDetailsModal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        corridor={selectedCorridor}
        language={language}
      />
    </div>
  );
}
