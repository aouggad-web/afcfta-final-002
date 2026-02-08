import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const REGION_LABELS = {
  fr: {
    afrique_nord: "Afrique du Nord / UMA",
    cedeao: "CEDEAO / ECOWAS",
    cemac: "CEMAC + RDC + STP",
    eac: "EAC (Communauté d'Afrique de l'Est)",
    sadc: "SADC / SACU",
    igad: "IGAD / Corne de l'Afrique",
  },
  en: {
    afrique_nord: "North Africa / UMA",
    cedeao: "ECOWAS / CEDEAO",
    cemac: "CEMAC + DRC + STP",
    eac: "EAC (East African Community)",
    sadc: "SADC / SACU",
    igad: "IGAD / Horn of Africa",
  }
};

const REGION_COLORS = {
  afrique_nord: "from-blue-500 to-blue-700",
  cedeao: "from-green-500 to-green-700",
  cemac: "from-yellow-500 to-yellow-700",
  eac: "from-purple-500 to-purple-700",
  sadc: "from-red-500 to-red-700",
  igad: "from-orange-500 to-orange-700",
};

const REGION_ICONS = {
  afrique_nord: "🏜️",
  cedeao: "🌴",
  cemac: "🌿",
  eac: "🏔️",
  sadc: "💎",
  igad: "🌅",
};

export default function TariffDownloads({ language = 'fr' }) {
  const [downloadData, setDownloadData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState({});
  const [selectedRegion, setSelectedRegion] = useState(null);

  const t = language === 'fr' ? {
    title: "Téléchargement des Données Tarifaires",
    subtitle: "54 pays - Format CSV compatible Excel",
    loading: "Chargement...",
    allRegions: "Toutes les régions",
    download: "Télécharger",
    downloading: "...",
    size: "Taille",
    lines: "lignes HS6",
    columns: "Colonnes",
    columnsDetail: "Code HS6, DD%, TVA%, Taxes détaillées, Avantages fiscaux, Formalités",
    separator: "Séparateur: point-virgule (;)",
    encoding: "Encodage: UTF-8 (compatible Excel)",
    totalCountries: "pays disponibles",
    downloadAll: "Tout télécharger",
    error: "Erreur de chargement",
  } : {
    title: "Tariff Data Download",
    subtitle: "54 countries - CSV format compatible with Excel",
    loading: "Loading...",
    allRegions: "All regions",
    download: "Download",
    downloading: "...",
    size: "Size",
    lines: "HS6 lines",
    columns: "Columns",
    columnsDetail: "HS6 Code, DD%, VAT%, Tax details, Fiscal advantages, Formalities",
    separator: "Separator: semicolon (;)",
    encoding: "Encoding: UTF-8 (Excel compatible)",
    totalCountries: "countries available",
    downloadAll: "Download all",
    error: "Loading error",
  };

  useEffect(() => {
    fetchDownloadList();
  }, []);

  const fetchDownloadList = async () => {
    try {
      const res = await axios.get(`${API}/tariff-data/download/list`);
      setDownloadData(res.data);
    } catch (err) {
      console.error('Error fetching download list:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (countryCode, countryName) => {
    setDownloading(prev => ({ ...prev, [countryCode]: true }));
    try {
      const res = await axios.get(`${API}/tariff-data/download/${countryCode}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Tarifs_${countryName}_${countryCode}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
    } finally {
      setDownloading(prev => ({ ...prev, [countryCode]: false }));
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="animate-spin text-4xl mb-4">🌍</div>
          <p className="text-gray-500">{t.loading}</p>
        </CardContent>
      </Card>
    );
  }

  if (!downloadData) {
    return (
      <Card>
        <CardContent className="p-8 text-center text-red-500">
          {t.error}
        </CardContent>
      </Card>
    );
  }

  const regions = downloadData.regions || {};
  const countries = downloadData.countries || [];
  const regionLabels = REGION_LABELS[language] || REGION_LABELS.fr;

  const getCountriesForRegion = (regionKey) => {
    const regionCountryCodes = regions[regionKey]?.countries || [];
    return countries.filter(c => regionCountryCodes.includes(c.code));
  };

  const displayedCountries = selectedRegion
    ? getCountriesForRegion(selectedRegion)
    : countries;

  return (
    <div className="space-y-6">
      <Card className="border-2 border-green-200">
        <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50">
          <CardTitle className="text-2xl flex items-center gap-3">
            📥 {t.title}
          </CardTitle>
          <p className="text-gray-600">{t.subtitle}</p>
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant="outline" className="text-sm">5 831 {t.lines}</Badge>
            <Badge variant="outline" className="text-sm">{t.separator}</Badge>
            <Badge variant="outline" className="text-sm">{t.encoding}</Badge>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {t.columns}: {t.columnsDetail}
          </p>
        </CardHeader>
      </Card>

      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedRegion === null ? "default" : "outline"}
          size="sm"
          onClick={() => setSelectedRegion(null)}
          className={selectedRegion === null ? "bg-gray-800 text-white" : ""}
        >
          🌍 {t.allRegions} ({countries.length})
        </Button>
        {Object.entries(regions).map(([key, region]) => (
          <Button
            key={key}
            variant={selectedRegion === key ? "default" : "outline"}
            size="sm"
            onClick={() => setSelectedRegion(key)}
            className={selectedRegion === key ? `bg-gradient-to-r ${REGION_COLORS[key]} text-white` : ""}
          >
            {REGION_ICONS[key]} {regionLabels[key]} ({region.countries.length})
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {displayedCountries.map((country) => (
          <Card key={country.code} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4 flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-sm truncate">{country.name}</p>
                <p className="text-xs text-gray-500">{country.code} - {country.size_kb} KB</p>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="ml-2 shrink-0 hover:bg-green-50 hover:border-green-500 hover:text-green-700"
                onClick={() => handleDownload(country.code, country.name)}
                disabled={downloading[country.code]}
              >
                {downloading[country.code] ? t.downloading : "📥"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
