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
  const [expandedCountry, setExpandedCountry] = useState(null);

  const isFr = language === 'fr';
  const t = isFr ? {
    title: "Téléchargement des Tarifs NPF (Droit Commun)",
    subtitle: "54 pays - Droits et taxes NPF avec sous-positions nationales",
    loading: "Chargement des données...",
    downloadCountry: "Télécharger ZIP",
    downloadRegion: "Télécharger tout le groupe",
    chapters: "Chapitres",
    files: "fichiers",
    total: "Total",
    format: "HS6 + sous-positions nationales (HS8/HS10/HS12)",
    columnsDetail: "Code, Niveau, Description FR/EN, Taxes spécifiques au pays, Formalités, Total%",
    error: "Erreur de chargement",
    seeChapters: "Voir les chapitres",
    countries: "pays",
  } : {
    title: "MFN Tariff Data Download (Common Law)",
    subtitle: "54 countries - MFN duties and taxes with national sub-positions",
    loading: "Loading data...",
    downloadCountry: "Download ZIP",
    downloadRegion: "Download entire group",
    chapters: "Chapters",
    files: "files",
    total: "Total",
    format: "HS6 + national sub-positions (HS8/HS10/HS12)",
    columnsDetail: "Code, Level, Description FR/EN, Country-specific taxes, Formalities, Total%",
    error: "Loading error",
    seeChapters: "See chapters",
    countries: "countries",
  };

  const chapterLabels = CHAPTER_LABELS[language] || CHAPTER_LABELS.fr;
  const regionLabels = REGION_LABELS[language] || REGION_LABELS.fr;

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

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="animate-spin text-4xl mb-4">🌍</div>
          <span className="text-gray-500">{t.loading}</span>
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

  const getCountriesForRegion = (regionKey) => {
    const regionCountryCodes = regions[regionKey]?.countries || [];
    return countries.filter(c => regionCountryCodes.includes(c.code));
  };

  return (
    <div className="space-y-6">
      <Card className="border-2 border-green-200">
        <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50">
          <CardTitle className="text-2xl flex items-center gap-3">
            📥 {t.title}
          </CardTitle>
          <div className="text-gray-600 mt-1">{t.subtitle}</div>
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant="outline" className="text-sm">{t.format}</Badge>
            <Badge variant="outline" className="text-sm">{t.columnsDetail}</Badge>
          </div>
        </CardHeader>
      </Card>

      {Object.entries(regions).map(([regionKey, region]) => {
        const regionCountries = getCountriesForRegion(regionKey);
        const totalSizeKb = regionCountries.reduce((s, c) => s + (c.total_size_kb || 0), 0);

        return (
          <Card key={regionKey} className="border border-gray-200 overflow-hidden">
            <div className={`bg-gradient-to-r ${REGION_COLORS[regionKey]} text-white p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3`}>
              <div>
                <div className="text-lg font-bold flex items-center gap-2">
                  <span>{REGION_ICONS[regionKey]}</span>
                  <span>{regionLabels[regionKey]}</span>
                </div>
                <div className="text-sm opacity-90 mt-1">
                  {regionCountries.length} {t.countries} — {Math.round(totalSizeKb / 1024 * 10) / 10} MB
                </div>
              </div>
              <a
                href={`${API}/tariff-data/download-region-zip/${regionKey}`}
                download
                className="inline-flex items-center gap-2 bg-white text-gray-800 font-semibold px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors text-sm shadow-md no-underline"
              >
                📦 {t.downloadRegion}
              </a>
            </div>

            <CardContent className="p-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {regionCountries.map((country) => (
                  <div key={country.code} className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3 bg-gray-50">
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm truncate">{country.name}</div>
                        <div className="text-xs text-gray-500">{country.code} — {country.total_size_kb} KB</div>
                      </div>
                      <div className="flex items-center gap-1 ml-2">
                        <a
                          href={`${API}/tariff-data/download-zip/${country.code}`}
                          download
                          className="inline-flex items-center gap-1 bg-green-600 text-white font-medium px-3 py-1.5 rounded hover:bg-green-700 transition-colors text-xs no-underline"
                        >
                          📥 ZIP
                        </a>
                        <button
                          className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1.5"
                          onClick={() => setExpandedCountry(expandedCountry === country.code ? null : country.code)}
                          title={t.seeChapters}
                        >
                          {expandedCountry === country.code ? "▲" : "▼"}
                        </button>
                      </div>
                    </div>

                    {expandedCountry === country.code && country.files && (
                      <div className="p-2 border-t border-gray-100 space-y-1">
                        {country.files.map((file) => (
                          <div key={file.group} className="flex items-center justify-between p-1.5 text-xs">
                            <div className="flex-1 min-w-0">
                              <span className="font-medium">Ch. {file.group}</span>
                              <span className="text-gray-400 ml-1 hidden sm:inline">{chapterLabels[file.group]}</span>
                              <span className="text-gray-400 ml-1"> — {file.size_kb} KB</span>
                            </div>
                            <a
                              href={`${API}${file.download_url}`}
                              download
                              className="text-green-600 hover:text-green-800 font-medium no-underline ml-1"
                            >
                              CSV
                            </a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
