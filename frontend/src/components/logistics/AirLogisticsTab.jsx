import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { toast } from '../../hooks/use-toast';
import AirLogisticsMap from './AirLogisticsMap';
import AirportCard from './AirportCard';
import AirportDetailsModal from './AirportDetailsModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

export default function AirLogisticsTab({ language = 'fr' }) {
  const [airports, setAirports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAirport, setSelectedAirport] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState('ALL');
  const [viewMode, setViewMode] = useState('map');

  const texts = {
    fr: {
      title: "Logistique Aérienne Panafricaine",
      subtitle: "Visualisez les principaux aéroports cargo d'Afrique avec leurs statistiques de trafic, acteurs et routes régulières",
      filterByCountry: "Filtrer par pays:",
      allCountries: "Tous les pays (64 aéroports)",
      map: "Carte",
      list: "Liste",
      airports: "aéroport",
      airportsPlural: "aéroports",
      loading: "Chargement des données aéroportuaires...",
      errorTitle: "Erreur",
      errorLoad: "Impossible de charger les données aéroportuaires",
      errorDetails: "Impossible de charger les détails de l'aéroport",
      // Regions
      northAfrica: "Afrique du Nord",
      westAfrica: "Afrique de l'Ouest",
      centralAfrica: "Afrique Centrale",
      eastAfrica: "Afrique de l'Est",
      southernAfrica: "Afrique Australe"
    },
    en: {
      title: "Pan-African Air Logistics",
      subtitle: "View the main African cargo airports with traffic statistics, operators and regular routes",
      filterByCountry: "Filter by country:",
      allCountries: "All countries (64 airports)",
      map: "Map",
      list: "List",
      airports: "airport",
      airportsPlural: "airports",
      loading: "Loading airport data...",
      errorTitle: "Error",
      errorLoad: "Unable to load airport data",
      errorDetails: "Unable to load airport details",
      // Regions
      northAfrica: "North Africa",
      westAfrica: "West Africa",
      centralAfrica: "Central Africa",
      eastAfrica: "East Africa",
      southernAfrica: "Southern Africa"
    }
  };

  const t = texts[language];

  useEffect(() => {
    fetchAirports(selectedCountry);
  }, [selectedCountry]);

  const fetchAirports = async (countryIso) => {
    setLoading(true);
    try {
      const url = countryIso && countryIso !== 'ALL'
        ? `${API}/logistics/air/airports?country_iso=${countryIso}`
        : `${API}/logistics/air/airports`;
      
      const response = await axios.get(url);
      setAirports(response.data.airports || []);
    } catch (error) {
      console.error('Error fetching airports:', error);
      toast({
        title: t.errorTitle,
        description: t.errorLoad,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAirportClick = async (airport) => {
    try {
      const response = await axios.get(`${API}/logistics/air/airports/${airport.airport_id}`);
      setSelectedAirport(response.data);
      setIsModalOpen(true);
    } catch (error) {
      console.error('Error fetching airport details:', error);
      toast({
        title: t.errorTitle,
        description: t.errorDetails,
        variant: "destructive",
      });
    }
  };

  // Country options with translations
  const countryOptions = {
    fr: {
      northAfrica: [
        { value: "DZA", label: "🇩🇿 Algérie (3)" },
        { value: "EGY", label: "🇪🇬 Égypte (2)" },
        { value: "LBY", label: "🇱🇾 Libye" },
        { value: "MAR", label: "🇲🇦 Maroc (3)" },
        { value: "TUN", label: "🇹🇳 Tunisie" }
      ],
      westAfrica: [
        { value: "BEN", label: "🇧🇯 Bénin" },
        { value: "BFA", label: "🇧🇫 Burkina Faso" },
        { value: "CPV", label: "🇨🇻 Cap-Vert" },
        { value: "CIV", label: "🇨🇮 Côte d'Ivoire" },
        { value: "GMB", label: "🇬🇲 Gambie" },
        { value: "GHA", label: "🇬🇭 Ghana" },
        { value: "GIN", label: "🇬🇳 Guinée" },
        { value: "LBR", label: "🇱🇷 Libéria" },
        { value: "MLI", label: "🇲🇱 Mali" },
        { value: "MRT", label: "🇲🇷 Mauritanie" },
        { value: "NER", label: "🇳🇪 Niger" },
        { value: "NGA", label: "🇳🇬 Nigéria (3)" },
        { value: "SEN", label: "🇸🇳 Sénégal" },
        { value: "SLE", label: "🇸🇱 Sierra Leone" },
        { value: "TGO", label: "🇹🇬 Togo" }
      ],
      centralAfrica: [
        { value: "AGO", label: "🇦🇴 Angola" },
        { value: "CMR", label: "🇨🇲 Cameroun" },
        { value: "CAF", label: "🇨🇫 Rép. Centrafricaine" },
        { value: "TCD", label: "🇹🇩 Tchad" },
        { value: "COG", label: "🇨🇬 Congo" },
        { value: "COD", label: "🇨🇩 RD Congo (2)" },
        { value: "GNQ", label: "🇬🇶 Guinée Équatoriale" },
        { value: "GAB", label: "🇬🇦 Gabon" },
        { value: "STP", label: "🇸🇹 São Tomé-et-Príncipe" }
      ],
      eastAfrica: [
        { value: "BDI", label: "🇧🇮 Burundi" },
        { value: "COM", label: "🇰🇲 Comores" },
        { value: "DJI", label: "🇩🇯 Djibouti" },
        { value: "ERI", label: "🇪🇷 Érythrée" },
        { value: "ETH", label: "🇪🇹 Éthiopie" },
        { value: "KEN", label: "🇰🇪 Kenya (2)" },
        { value: "MDG", label: "🇲🇬 Madagascar" },
        { value: "MWI", label: "🇲🇼 Malawi" },
        { value: "MUS", label: "🇲🇺 Maurice" },
        { value: "RWA", label: "🇷🇼 Rwanda" },
        { value: "SYC", label: "🇸🇨 Seychelles" },
        { value: "SOM", label: "🇸🇴 Somalie" },
        { value: "SSD", label: "🇸🇸 Soudan du Sud" },
        { value: "SDN", label: "🇸🇩 Soudan" },
        { value: "TZA", label: "🇹🇿 Tanzanie (2)" },
        { value: "UGA", label: "🇺🇬 Ouganda" }
      ],
      southernAfrica: [
        { value: "BWA", label: "🇧🇼 Botswana" },
        { value: "LSO", label: "🇱🇸 Lesotho" },
        { value: "MOZ", label: "🇲🇿 Mozambique" },
        { value: "NAM", label: "🇳🇦 Namibie" },
        { value: "ZAF", label: "🇿🇦 Afrique du Sud (2)" },
        { value: "SWZ", label: "🇸🇿 Eswatini" },
        { value: "ZMB", label: "🇿🇲 Zambie" },
        { value: "ZWE", label: "🇿🇼 Zimbabwe" }
      ]
    },
    en: {
      northAfrica: [
        { value: "DZA", label: "🇩🇿 Algeria (3)" },
        { value: "EGY", label: "🇪🇬 Egypt (2)" },
        { value: "LBY", label: "🇱🇾 Libya" },
        { value: "MAR", label: "🇲🇦 Morocco (3)" },
        { value: "TUN", label: "🇹🇳 Tunisia" }
      ],
      westAfrica: [
        { value: "BEN", label: "🇧🇯 Benin" },
        { value: "BFA", label: "🇧🇫 Burkina Faso" },
        { value: "CPV", label: "🇨🇻 Cape Verde" },
        { value: "CIV", label: "🇨🇮 Côte d'Ivoire" },
        { value: "GMB", label: "🇬🇲 Gambia" },
        { value: "GHA", label: "🇬🇭 Ghana" },
        { value: "GIN", label: "🇬🇳 Guinea" },
        { value: "LBR", label: "🇱🇷 Liberia" },
        { value: "MLI", label: "🇲🇱 Mali" },
        { value: "MRT", label: "🇲🇷 Mauritania" },
        { value: "NER", label: "🇳🇪 Niger" },
        { value: "NGA", label: "🇳🇬 Nigeria (3)" },
        { value: "SEN", label: "🇸🇳 Senegal" },
        { value: "SLE", label: "🇸🇱 Sierra Leone" },
        { value: "TGO", label: "🇹🇬 Togo" }
      ],
      centralAfrica: [
        { value: "AGO", label: "🇦🇴 Angola" },
        { value: "CMR", label: "🇨🇲 Cameroon" },
        { value: "CAF", label: "🇨🇫 Central African Rep." },
        { value: "TCD", label: "🇹🇩 Chad" },
        { value: "COG", label: "🇨🇬 Congo" },
        { value: "COD", label: "🇨🇩 DR Congo (2)" },
        { value: "GNQ", label: "🇬🇶 Equatorial Guinea" },
        { value: "GAB", label: "🇬🇦 Gabon" },
        { value: "STP", label: "🇸🇹 São Tomé & Príncipe" }
      ],
      eastAfrica: [
        { value: "BDI", label: "🇧🇮 Burundi" },
        { value: "COM", label: "🇰🇲 Comoros" },
        { value: "DJI", label: "🇩🇯 Djibouti" },
        { value: "ERI", label: "🇪🇷 Eritrea" },
        { value: "ETH", label: "🇪🇹 Ethiopia" },
        { value: "KEN", label: "🇰🇪 Kenya (2)" },
        { value: "MDG", label: "🇲🇬 Madagascar" },
        { value: "MWI", label: "🇲🇼 Malawi" },
        { value: "MUS", label: "🇲🇺 Mauritius" },
        { value: "RWA", label: "🇷🇼 Rwanda" },
        { value: "SYC", label: "🇸🇨 Seychelles" },
        { value: "SOM", label: "🇸🇴 Somalia" },
        { value: "SSD", label: "🇸🇸 South Sudan" },
        { value: "SDN", label: "🇸🇩 Sudan" },
        { value: "TZA", label: "🇹🇿 Tanzania (2)" },
        { value: "UGA", label: "🇺🇬 Uganda" }
      ],
      southernAfrica: [
        { value: "BWA", label: "🇧🇼 Botswana" },
        { value: "LSO", label: "🇱🇸 Lesotho" },
        { value: "MOZ", label: "🇲🇿 Mozambique" },
        { value: "NAM", label: "🇳🇦 Namibia" },
        { value: "ZAF", label: "🇿🇦 South Africa (2)" },
        { value: "SWZ", label: "🇸🇿 Eswatini" },
        { value: "ZMB", label: "🇿🇲 Zambia" },
        { value: "ZWE", label: "🇿🇼 Zimbabwe" }
      ]
    }
  };

  const countries = countryOptions[language];

  return (
    <div className="space-y-4">
      {/* Header Section - Compact */}
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 text-white shadow-lg">
        <CardHeader className="py-3">
          <CardTitle className="text-lg font-bold flex items-center gap-2">
            <span>✈️</span>
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="text-blue-100 text-sm">
            {t.subtitle}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Controls Section */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            {/* Country Filter */}
            <div className="flex items-center gap-3 w-full md:w-auto">
              <span className="text-sm font-semibold text-gray-700">{t.filterByCountry}</span>
              <select
                value={selectedCountry}
                onChange={(e) => setSelectedCountry(e.target.value)}
                className="px-4 py-2 border rounded-lg shadow-sm focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
              >
                <option value="ALL">🌍 {t.allCountries}</option>
                <optgroup label={t.northAfrica}>
                  {countries.northAfrica.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </optgroup>
                <optgroup label={t.westAfrica}>
                  {countries.westAfrica.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </optgroup>
                <optgroup label={t.centralAfrica}>
                  {countries.centralAfrica.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </optgroup>
                <optgroup label={t.eastAfrica}>
                  {countries.eastAfrica.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </optgroup>
                <optgroup label={t.southernAfrica}>
                  {countries.southernAfrica.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </optgroup>
              </select>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setViewMode('map')}
                variant={viewMode === 'map' ? 'default' : 'outline'}
                className={viewMode === 'map' ? 'bg-sky-600 hover:bg-sky-700' : ''}
              >
                🗺️ {t.map}
              </Button>
              <Button
                onClick={() => setViewMode('list')}
                variant={viewMode === 'list' ? 'default' : 'outline'}
                className={viewMode === 'list' ? 'bg-sky-600 hover:bg-sky-700' : ''}
              >
                📋 {t.list}
              </Button>
            </div>

            {/* Airport Count Badge */}
            <Badge variant="secondary" className="text-lg px-4 py-2">
              {airports.length} {airports.length > 1 ? t.airportsPlural : t.airports}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Map or List View */}
      {loading ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-600"></div>
              <p className="mt-4 text-gray-600">{t.loading}</p>
            </div>
          </CardContent>
        </Card>
      ) : viewMode === 'map' ? (
        <AirLogisticsMap
          onAirportClick={handleAirportClick}
          selectedCountry={selectedCountry}
          language={language}
        />
      ) : (
        <div className="max-h-[550px] overflow-y-auto rounded-lg border border-gray-200 p-4 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {airports.map((airport) => (
              <AirportCard
                key={airport.airport_id}
                airport={airport}
                onOpenDetails={handleAirportClick}
                language={language}
              />
            ))}
          </div>
        </div>
      )}

      {/* Airport Details Modal */}
      <AirportDetailsModal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        airport={selectedAirport}
        language={language}
      />
    </div>
  );
}
