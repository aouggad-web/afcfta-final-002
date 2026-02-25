import React, { useState, useMemo } from 'react';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '../ui/select';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';

// Tous les pays africains regroupés par région
const AFRICAN_COUNTRIES_BY_REGION = {
  "Afrique du Nord": [
    { code: 'DZA', name: 'Algérie', flag: '🇩🇿' },
    { code: 'EGY', name: 'Égypte', flag: '🇪🇬' },
    { code: 'LBY', name: 'Libye', flag: '🇱🇾' },
    { code: 'MAR', name: 'Maroc', flag: '🇲🇦' },
    { code: 'ESH', name: 'RASD (Sahara Occ.)', flag: '🇪🇭', hasTradeData: false, note: 'Membre UA - Pas de statistiques' },
    { code: 'TUN', name: 'Tunisie', flag: '🇹🇳' },
  ],
  "Afrique de l'Ouest": [
    { code: 'BEN', name: 'Bénin', flag: '🇧🇯' },
    { code: 'BFA', name: 'Burkina Faso', flag: '🇧🇫' },
    { code: 'CPV', name: 'Cap-Vert', flag: '🇨🇻' },
    { code: 'CIV', name: 'Côte d\'Ivoire', flag: '🇨🇮' },
    { code: 'GMB', name: 'Gambie', flag: '🇬🇲' },
    { code: 'GHA', name: 'Ghana', flag: '🇬🇭' },
    { code: 'GIN', name: 'Guinée', flag: '🇬🇳' },
    { code: 'GNB', name: 'Guinée-Bissau', flag: '🇬🇼' },
    { code: 'LBR', name: 'Libéria', flag: '🇱🇷' },
    { code: 'MLI', name: 'Mali', flag: '🇲🇱' },
    { code: 'MRT', name: 'Mauritanie', flag: '🇲🇷' },
    { code: 'NER', name: 'Niger', flag: '🇳🇪' },
    { code: 'NGA', name: 'Nigéria', flag: '🇳🇬' },
    { code: 'SEN', name: 'Sénégal', flag: '🇸🇳' },
    { code: 'SLE', name: 'Sierra Leone', flag: '🇸🇱' },
    { code: 'TGO', name: 'Togo', flag: '🇹🇬' },
  ],
  "Afrique Centrale": [
    { code: 'AGO', name: 'Angola', flag: '🇦🇴' },
    { code: 'CMR', name: 'Cameroun', flag: '🇨🇲' },
    { code: 'CAF', name: 'République Centrafricaine', flag: '🇨🇫' },
    { code: 'TCD', name: 'Tchad', flag: '🇹🇩' },
    { code: 'COG', name: 'République du Congo', flag: '🇨🇬' },
    { code: 'COD', name: 'RD Congo', flag: '🇨🇩' },
    { code: 'GNQ', name: 'Guinée Équatoriale', flag: '🇬🇶' },
    { code: 'GAB', name: 'Gabon', flag: '🇬🇦' },
    { code: 'STP', name: 'São Tomé-et-Príncipe', flag: '🇸🇹' },
  ],
  "Afrique de l'Est": [
    { code: 'BDI', name: 'Burundi', flag: '🇧🇮' },
    { code: 'COM', name: 'Comores', flag: '🇰🇲' },
    { code: 'DJI', name: 'Djibouti', flag: '🇩🇯' },
    { code: 'ERI', name: 'Érythrée', flag: '🇪🇷' },
    { code: 'ETH', name: 'Éthiopie', flag: '🇪🇹' },
    { code: 'KEN', name: 'Kenya', flag: '🇰🇪' },
    { code: 'MDG', name: 'Madagascar', flag: '🇲🇬' },
    { code: 'MWI', name: 'Malawi', flag: '🇲🇼' },
    { code: 'MUS', name: 'Maurice', flag: '🇲🇺' },
    { code: 'MOZ', name: 'Mozambique', flag: '🇲🇿' },
    { code: 'RWA', name: 'Rwanda', flag: '🇷🇼' },
    { code: 'SYC', name: 'Seychelles', flag: '🇸🇨' },
    { code: 'SOM', name: 'Somalie', flag: '🇸🇴' },
    { code: 'SSD', name: 'Soudan du Sud', flag: '🇸🇸' },
    { code: 'SDN', name: 'Soudan', flag: '🇸🇩' },
    { code: 'TZA', name: 'Tanzanie', flag: '🇹🇿' },
    { code: 'UGA', name: 'Ouganda', flag: '🇺🇬' },
  ],
  "Afrique Australe": [
    { code: 'BWA', name: 'Botswana', flag: '🇧🇼' },
    { code: 'LSO', name: 'Lesotho', flag: '🇱🇸' },
    { code: 'NAM', name: 'Namibie', flag: '🇳🇦' },
    { code: 'ZAF', name: 'Afrique du Sud', flag: '🇿🇦' },
    { code: 'SWZ', name: 'Eswatini', flag: '🇸🇿' },
    { code: 'ZMB', name: 'Zambie', flag: '🇿🇲' },
    { code: 'ZWE', name: 'Zimbabwe', flag: '🇿🇼' },
  ],
};

// Grandes économies à mettre en avant
const MAJOR_ECONOMIES = ['ZAF', 'NGA', 'EGY', 'KEN', 'GHA', 'ETH', 'MAR', 'DZA', 'TZA', 'CIV'];

function CountrySelector({ value, onChange, label = "Sélectionner un pays", showStats = false }) {
  const [searchTerm, setSearchTerm] = useState('');

  // Obtenir tous les pays dans une liste plate
  const allCountries = useMemo(() => {
    const countries = [];
    Object.values(AFRICAN_COUNTRIES_BY_REGION).forEach(region => {
      countries.push(...region);
    });
    return countries;
  }, []);

  // Trouver le pays sélectionné
  const selectedCountry = useMemo(() => {
    return allCountries.find(c => c.code === value);
  }, [value, allCountries]);

  // Filtrer les pays selon la recherche
  const filteredRegions = useMemo(() => {
    if (!searchTerm) return AFRICAN_COUNTRIES_BY_REGION;

    const filtered = {};
    Object.entries(AFRICAN_COUNTRIES_BY_REGION).forEach(([region, countries]) => {
      const matchedCountries = countries.filter(country =>
        country.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        country.code.toLowerCase().includes(searchTerm.toLowerCase())
      );
      if (matchedCountries.length > 0) {
        filtered[region] = matchedCountries;
      }
    });
    return filtered;
  }, [searchTerm]);

  // Grandes économies filtrées
  const majorEconomiesFiltered = useMemo(() => {
    const majors = allCountries.filter(c => MAJOR_ECONOMIES.includes(c.code));
    if (!searchTerm) return majors;
    return majors.filter(country =>
      country.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      country.code.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [searchTerm, allCountries]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-4">
        <label className="text-sm font-semibold text-gray-700 whitespace-nowrap">
          {label}:
        </label>
        
        <Select value={value} onValueChange={onChange}>
          <SelectTrigger className="w-full max-w-md bg-white shadow-sm hover:shadow-md transition-shadow">
            <SelectValue>
              {selectedCountry ? (
                <span className="flex items-center gap-2">
                  <span className="text-2xl">{selectedCountry.flag}</span>
                  <span className="font-medium">{selectedCountry.name}</span>
                  <Badge variant="outline" className="text-xs">{selectedCountry.code}</Badge>
                </span>
              ) : (
                "Choisir un pays..."
              )}
            </SelectValue>
          </SelectTrigger>
          
          <SelectContent className="max-h-96">
            {/* Barre de recherche */}
            <div className="p-2 border-b sticky top-0 bg-white z-10">
              <Input
                type="text"
                placeholder="🔍 Rechercher un pays..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>

            {/* Grandes économies en premier */}
            {majorEconomiesFiltered.length > 0 && !searchTerm && (
              <SelectGroup>
                <SelectLabel className="text-xs font-bold text-purple-700 bg-purple-50 py-2">
                  ⭐ Grandes Économies
                </SelectLabel>
                {majorEconomiesFiltered.map(country => (
                  <SelectItem key={country.code} value={country.code} className="cursor-pointer hover:bg-purple-50">
                    <div className="flex items-center gap-2 py-1">
                      <span className="text-xl">{country.flag}</span>
                      <span className="font-medium">{country.name}</span>
                      <Badge variant="outline" className="text-xs ml-auto">{country.code}</Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectGroup>
            )}

            {/* Pays par région */}
            {Object.entries(filteredRegions).map(([region, countries]) => (
              <SelectGroup key={region}>
                <SelectLabel className="text-xs font-bold text-gray-700 bg-gray-50 py-2">
                  {region} ({countries.length})
                </SelectLabel>
                {countries.map(country => (
                  <SelectItem key={country.code} value={country.code} className="cursor-pointer hover:bg-gray-50">
                    <div className="flex items-center gap-2 py-1">
                      <span className="text-xl">{country.flag}</span>
                      <span>{country.name}</span>
                      <Badge variant="outline" className="text-xs ml-auto">{country.code}</Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectGroup>
            ))}

            {/* Aucun résultat */}
            {Object.keys(filteredRegions).length === 0 && (
              <div className="p-4 text-center text-gray-500">
                Aucun pays trouvé pour "{searchTerm}"
              </div>
            )}
          </SelectContent>
        </Select>

        {showStats && selectedCountry && (
          <div className="flex gap-2">
            <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-200">
              {selectedCountry.flag} {selectedCountry.name}
            </Badge>
          </div>
        )}
      </div>

      {/* Info sur le nombre total de pays */}
      <div className="text-xs text-gray-500 flex items-center gap-2">
        <span>📊 {allCountries.length} pays africains disponibles</span>
        {searchTerm && (
          <span>• {Object.values(filteredRegions).flat().length} pays trouvés</span>
        )}
      </div>
    </div>
  );
}

export default CountrySelector;
