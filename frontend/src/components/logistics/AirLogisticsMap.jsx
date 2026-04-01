import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Component to update map view when country selection changes
function MapController({ center, zoom }) {
  const map = useMap();
  
  useEffect(() => {
    if (center) {
      map.setView(center, zoom);
    }
  }, [map, center, zoom]);
  
  return null;
}

export default function AirLogisticsMap({ onAirportClick, selectedCountry, language = 'fr' }) {
  const [airports, setAirports] = useState([]);
  const [mapCenter, setMapCenter] = useState([0, 20]); // Center of Africa
  const [mapZoom, setMapZoom] = useState(3);

  const texts = {
    fr: {
      legend: "Légende",
      majorHub: "Hub Majeur (>400k tonnes)",
      largeHub: "Hub Large (200-400k tonnes)",
      mediumHub: "Hub Moyen (100-200k tonnes)",
      regional: "Régional (<100k tonnes)",
      freight: "Fret",
      mail: "Courrier",
      cargoMovements: "Mouvements Cargo",
      viewDetails: "Voir détails complets",
      tons: "tonnes"
    },
    en: {
      legend: "Legend",
      majorHub: "Major Hub (>400k tons)",
      largeHub: "Large Hub (200-400k tons)",
      mediumHub: "Medium Hub (100-200k tons)",
      regional: "Regional (<100k tons)",
      freight: "Freight",
      mail: "Mail",
      cargoMovements: "Cargo Movements",
      viewDetails: "View full details",
      tons: "tons"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchAirports();
  }, [selectedCountry]);

  const fetchAirports = async () => {
    try {
      const url = selectedCountry && selectedCountry !== 'ALL'
        ? `${API}/logistics/air/airports?country_iso=${selectedCountry}`
        : `${API}/logistics/air/airports`;
      
      const response = await axios.get(url);
      const airportsData = response.data.airports || [];
      setAirports(airportsData);

      // Update map center based on selected country
      if (selectedCountry && selectedCountry !== 'ALL' && airportsData.length > 0) {
        const firstAirport = airportsData[0];
        setMapCenter([firstAirport.geo_lat, firstAirport.geo_lon]);
        setMapZoom(6);
      } else {
        setMapCenter([0, 20]);
        setMapZoom(3);
      }
    } catch (error) {
      console.error('Error fetching airports:', error);
    }
  };

  // Calculate marker radius based on cargo throughput
  const getMarkerRadius = (airport) => {
    const stats = airport.historical_stats?.[0];
    if (!stats || !stats.cargo_throughput_tons) return 5;
    
    const cargo = stats.cargo_throughput_tons;
    if (cargo > 400000) return 18;
    if (cargo > 200000) return 14;
    if (cargo > 100000) return 10;
    if (cargo > 50000) return 7;
    return 5;
  };

  // Get marker color based on cargo volume
  const getMarkerColor = (airport) => {
    const stats = airport.historical_stats?.[0];
    if (!stats || !stats.cargo_throughput_tons) return '#94a3b8';
    
    const cargo = stats.cargo_throughput_tons;
    if (cargo > 400000) return '#dc2626'; // Red - Major hub
    if (cargo > 200000) return '#ea580c'; // Orange - Large hub
    if (cargo > 100000) return '#0284c7'; // Sky blue - Medium hub
    return '#06b6d4'; // Cyan - Regional
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
            <div className="w-4 h-4 rounded-full bg-[#dc2626]"></div>
            <span>{t.majorHub}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#ea580c]"></div>
            <span>{t.largeHub}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#0284c7]"></div>
            <span>{t.mediumHub}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#06b6d4]"></div>
            <span>{t.regional}</span>
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
        
        {airports.map((airport) => {
          const stats = airport.historical_stats?.[0] || {};
          return (
            <CircleMarker
              key={airport.airport_id}
              center={[airport.geo_lat, airport.geo_lon]}
              radius={getMarkerRadius(airport)}
              fillColor={getMarkerColor(airport)}
              color="white"
              weight={2}
              opacity={1}
              fillOpacity={0.8}
              eventHandlers={{
                click: () => onAirportClick(airport)
              }}
            >
              <Popup>
                <div className="p-2 min-w-[250px]">
                  <h3 className="font-bold text-lg mb-1 flex items-center gap-2">
                    <span>✈️</span>
                    {airport.airport_name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">
                    {airport.country_name} • {airport.iata_code}
                  </p>
                  
                  <div className="space-y-2 text-sm">
                    <div className="bg-sky-50 p-2 rounded">
                      <p className="font-semibold text-sky-800">📦 {t.freight} {stats.year}</p>
                      <p className="text-sky-600 font-bold">{formatNumber(stats.cargo_throughput_tons)} {t.tons}</p>
                    </div>
                    
                    <div className="bg-amber-50 p-2 rounded">
                      <p className="font-semibold text-amber-800">📬 {t.mail} {stats.year}</p>
                      <p className="text-amber-600 font-bold">{formatNumber(stats.mail_throughput_tons)} {t.tons}</p>
                    </div>
                    
                    <div className="bg-green-50 p-2 rounded">
                      <p className="font-semibold text-green-800">🛩️ {t.cargoMovements}</p>
                      <p className="text-green-600 font-bold">{formatNumber(stats.cargo_aircraft_movements)}</p>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => onAirportClick(airport)}
                    className="mt-3 w-full bg-sky-600 text-white px-3 py-2 rounded hover:bg-sky-700 text-sm font-semibold"
                  >
                    {t.viewDetails}
                  </button>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
