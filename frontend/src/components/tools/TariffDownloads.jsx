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

const CHAPTER_LABELS = {
  fr: {
    "01-10": "Animaux, Produits animaux",
    "11-20": "Produits végétaux, Graisses",
    "21-30": "Industries alimentaires, Boissons, Tabacs",
    "31-40": "Produits chimiques, Plastiques",
    "41-50": "Peaux, Cuirs, Bois, Textiles",
    "51-60": "Matières textiles",
    "61-70": "Vêtements, Chaussures, Verre",
    "71-80": "Métaux précieux, Métaux communs",
    "81-90": "Métaux, Machines, Véhicules",
    "91-99": "Instruments, Armes, Divers",
  },
  en: {
    "01-10": "Animals, Animal products",
    "11-20": "Vegetable products, Fats",
    "21-30": "Food industries, Beverages, Tobacco",
    "31-40": "Chemical products, Plastics",
    "41-50": "Hides, Leather, Wood, Textiles",
    "51-60": "Textile materials",
    "61-70": "Clothing, Footwear, Glass",
    "71-80": "Precious metals, Base metals",
    "81-90": "Metals, Machinery, Vehicles",
    "91-99": "Instruments, Arms, Miscellaneous",
  },
};

export default function TariffDownloads({ language = 'fr' }) {
  const [downloadData, setDownloadData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState({});
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [expandedCountry, setExpandedCountry] = useState(null);

  const t = language === 'fr' ? {
    title: "Téléchargement des Tarifs NPF (Droit Commun)",
    subtitle: "54 pays - Droits et taxes NPF avec sous-positions nationales",
    loading: "Chargement...",
    allRegions: "Toutes les régions",
    download: "Télécharger",
    downloading: "...",
    chapters: "Chapitres",
    files: "fichiers",
    total: "Total",
    separator: "Séparateur: point-virgule (;)",
    encoding: "Encodage: UTF-8 (compatible Excel)",
    format: "HS6 + sous-positions nationales (HS8/HS10/HS12)",
    columnsDetail: "Code, Niveau, Description FR/EN, Taxes spécifiques au pays (DD, TVA, etc.), Formalités, Total%",
    error: "Erreur de chargement",
    clickToExpand: "Cliquez pour voir les fichiers par chapitres",
  } : {
    title: "MFN Tariff Data Download (Common Law)",
    subtitle: "54 countries - MFN duties and taxes with national sub-positions",
    loading: "Loading...",
    allRegions: "All regions",
    download: "Download",
    downloading: "...",
    chapters: "Chapters",
    files: "files",
    total: "Total",
    separator: "Separator: semicolon (;)",
    encoding: "Encoding: UTF-8 (Excel compatible)",
    format: "HS6 + national sub-positions (HS8/HS10/HS12)",
    columnsDetail: "Code, Level, Description FR/EN, Country-specific taxes (DD, VAT, etc.), Formalities, Total%",
    error: "Loading error",
    clickToExpand: "Click to see files by chapters",
  };

  const chapterLabels = CHAPTER_LABELS[language] || CHAPTER_LABELS.fr;

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

  const handleDownload = async (downloadUrl, filename, key) => {
    setDownloading(prev => ({ ...prev, [key]: true }));
    try {
      const res = await axios.get(`${API}${downloadUrl}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
    } finally {
      setDownloading(prev => ({ ...prev, [key]: false }));
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
            <Badge variant="outline" className="text-sm">{t.format}</Badge>
            <Badge variant="outline" className="text-sm">{t.separator}</Badge>
            <Badge variant="outline" className="text-sm">{t.encoding}</Badge>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {t.columnsDetail}
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

      <div className="space-y-2">
        {displayedCountries.map((country) => (
          <Card key={country.code} className="hover:shadow-md transition-shadow">
            <CardContent className="p-0">
              <button
                className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 rounded-lg transition-colors"
                onClick={() => setExpandedCountry(expandedCountry === country.code ? null : country.code)}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm">{country.name}</p>
                  <p className="text-xs text-gray-500">
                    {country.code} - {country.file_count} {t.files} - {t.total}: {country.total_size_kb} KB
                  </p>
                </div>
                <span className="text-gray-400 text-lg ml-2">
                  {expandedCountry === country.code ? "▲" : "▼"}
                </span>
              </button>

              {expandedCountry === country.code && country.files && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3">
                    {country.files.map((file) => {
                      const dlKey = `${country.code}_${file.group}`;
                      return (
                        <div
                          key={file.group}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded border border-gray-200"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium">{t.chapters} {file.group}</p>
                            <p className="text-xs text-gray-500 truncate">
                              {chapterLabels[file.group] || ""} - {file.size_kb} KB
                            </p>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            className="ml-2 shrink-0 hover:bg-green-50 hover:border-green-500 hover:text-green-700"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownload(
                                file.download_url,
                                `Tarifs_NPF_${country.name}_${country.code}_ch${file.group}.csv`,
                                dlKey
                              );
                            }}
                            disabled={downloading[dlKey]}
                          >
                            {downloading[dlKey] ? t.downloading : "📥"}
                          </Button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
