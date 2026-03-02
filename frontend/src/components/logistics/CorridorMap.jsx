import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Component to update map view
function MapController({ center, zoom }) {
  const map = useMap();
  
  useEffect(() => {
    if (center) {
      map.setView(center, zoom);
    }
  }, [map, center, zoom]);
  
  return null;
}

export default function CorridorMap({ onCorridorClick, selectedType, selectedImportance, language = 'fr' }) {
  const [corridors, setCorridors] = useState([]);
  const [mapCenter, setMapCenter] = useState([0, 20]);
  const [mapZoom, setMapZoom] = useState(3);

  const texts = {
    fr: {
      legend: "Légende",
      road: "Route",
      rail: "Rail",
      multimodal: "Multimodal",
      highImportance: "Importance Haute",
      osbp: "OSBP",
      border: "Frontière",
      type: "Type",
      length: "Longueur",
      status: "Statut",
      freight: "Fret",
      tons: "tonnes",
      viewDetails: "Voir détails complets"
    },
    en: {
      legend: "Legend",
      road: "Road",
      rail: "Rail",
      multimodal: "Multimodal",
      highImportance: "High Importance",
      osbp: "OSBP",
      border: "Border",
      type: "Type",
      length: "Length",
      status: "Status",
      freight: "Freight",
      tons: "tons",
      viewDetails: "View full details"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchCorridors();
  }, [selectedType, selectedImportance]);

  const fetchCorridors = async () => {
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
    }
  };

  // Get corridor color based on type
  const getCorridorColor = (corridor) => {
    const type = corridor.corridor_type;
    if (type === 'rail') return '#ef4444'; // Red
    if (type === 'road') return '#3b82f6'; // Blue
    if (type === 'multimodal') return '#8b5cf6'; // Purple
    return '#6b7280'; // Gray
  };

  // Get corridor weight based on importance
  const getCorridorWeight = (corridor) => {
    return corridor.importance === 'high' ? 4 : 2;
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return language === 'en'
      ? new Intl.NumberFormat('en-US').format(num)
      : new Intl.NumberFormat('fr-FR').format(num);
  };

  return (
    <div className="relative">
      {/* Map Legend */}
      <div className="absolute top-4 right-4 z-[1000] bg-white p-4 rounded-lg shadow-lg">
        <h4 className="font-bold text-sm mb-2">{t.legend}</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 bg-[#3b82f6]"></div>
            <span>{t.road}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 bg-[#ef4444]"></div>
            <span>{t.rail}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 bg-[#8b5cf6]"></div>
            <span>{t.multimodal}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-1 bg-gray-900" style={{height: '3px'}}></div>
            <span>{t.highImportance}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-600"></div>
            <span>{t.osbp}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-600"></div>
            <span>{t.border}</span>
          </div>
        </div>
      </div>

      <MapContainer 
        center={mapCenter} 
        zoom={mapZoom} 
        style={{ height: '550px', width: '100%' }}
        className="rounded-lg shadow-lg"
      >
        <MapController center={mapCenter} zoom={mapZoom} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Draw corridor polylines */}
        {corridors.map((corridor) => {
          if (!corridor.coordinates || corridor.coordinates.length < 2) return null;
          
          return (
            <Polyline
              key={corridor.corridor_id}
              positions={corridor.coordinates}
              color={getCorridorColor(corridor)}
              weight={getCorridorWeight(corridor)}
              opacity={0.8}
              eventHandlers={{
                click: () => onCorridorClick(corridor)
              }}
            >
              <Popup>
                <div className="p-2 min-w-[250px]">
                  <h3 className="font-bold text-base mb-1">
                    {corridor.corridor_name}
                  </h3>
                  <p className="text-xs text-gray-600 mb-2">
                    {corridor.countries_spanned?.join(' → ')}
                  </p>
                  
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-600">{t.type}:</span>
                      <span className="font-semibold capitalize">{corridor.corridor_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">{t.length}:</span>
                      <span className="font-semibold">{formatNumber(corridor.length_km)} km</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">{t.status}:</span>
                      <span className="font-semibold">{corridor.status}</span>
                    </div>
                    {corridor.stats?.freight_throughput_tons && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">{t.freight}:</span>
                        <span className="font-semibold">{formatNumber(corridor.stats.freight_throughput_tons)} {t.tons}</span>
                      </div>
                    )}
                  </div>
                  
                  <button 
                    onClick={() => onCorridorClick(corridor)}
                    className="mt-3 w-full bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 text-xs font-semibold"
                  >
                    {t.viewDetails}
                  </button>
                </div>
              </Popup>
            </Polyline>
          );
        })}
        
        {/* Draw nodes as circle markers */}
        {corridors.map((corridor) => {
          return corridor.nodes?.map((node) => (
            <CircleMarker
              key={node.node_id}
              center={[node.geo_lat, node.geo_lon]}
              radius={node.is_osbp ? 6 : 4}
              fillColor={node.is_osbp ? '#16a34a' : '#ea580c'}
              color="white"
              weight={2}
              opacity={1}
              fillOpacity={0.9}
            >
              <Popup>
                <div className="text-xs">
                  <p className="font-bold">{node.node_name}</p>
                  <p className="text-gray-600">{node.node_type}</p>
                  {node.is_osbp && <p className="text-green-600 font-semibold">✓ OSBP</p>}
                </div>
              </Popup>
            </CircleMarker>
          ));
        })}
      </MapContainer>
    </div>
  );
}
