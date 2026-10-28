import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { entitlementNoticeText, entitlementRefusal } from './entitlementNotice';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
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

function DownloadButton({ url, label, icon, className, size = "normal" }) {
  const [status, setStatus] = useState('idle');

  const handleClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (status === 'loading') return;
    setStatus('loading');
    try {
      const res = await fetch(`${API}${url}`);
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const disposition = res.headers.get('content-disposition') || '';
      let filename = 'download.zip';
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match) filename = match[1];
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = filename;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);
      }, 200);
      setStatus('done');
      setTimeout(() => setStatus('idle'), 3000);
    } catch (err) {
      console.error('Download error:', err);
      setStatus('error');
      setTimeout(() => setStatus('idle'), 3000);
    }
  };

  const sizeClasses = size === "small"
    ? "px-2 py-1 text-xs"
    : "px-4 py-2 text-sm";

  const statusLabel = status === 'loading'
    ? "⏳"
    : status === 'done'
    ? "✅"
    : status === 'error'
    ? "❌"
    : `${icon} ${label}`;

  return (
    <button
      onClick={handleClick}
      disabled={status === 'loading'}
      className={`inline-flex items-center gap-1 font-semibold rounded-lg transition-all ${sizeClasses} ${className} ${status === 'loading' ? 'opacity-70 cursor-wait' : 'hover:opacity-90 cursor-pointer'}`}
    >
      {statusLabel}
    </button>
  );
}

export default function TariffDownloads({ language = 'fr' }) {
  const [downloadData, setDownloadData] = useState(null);
  const [subscriptionNotice, setSubscriptionNotice] = useState(null);
  const [loading, setLoading] = useState(true);

  const isFr = language === 'fr';
  const t = isFr ? {
    title: "Téléchargement des Tarifs NPF (Droit Commun)",
    subtitle: (n) => `${n} pays — tarif NPF tel que le calculateur l'applique`,
    loading: "Chargement des données...",
    downloadCountry: "CSV",
    downloadJson: "JSON",
    downloadRegion: "Télécharger tout le groupe",
    format: "Une ligne par position nationale : CSV (« ; ») + fichier de notes, ou JSON",
    columnsDetail: "Taux par prélèvement, total pour 100 CAF, état du calcul, manques, restrictions",
    error: "Erreur de chargement",
    subscriptionTitle: "Module réservé aux abonnés",
    countries: "pays",
  } : {
    title: "MFN Tariff Data Download (Common Law)",
    subtitle: (n) => `${n} countries — MFN tariff as applied by the calculator`,
    loading: "Loading data...",
    downloadCountry: "CSV",
    downloadJson: "JSON",
    downloadRegion: "Download entire group",
    format: "One row per national tariff line: CSV (« ; ») + notes file, or JSON",
    columnsDetail: "Rate per levy, total per 100 CIF, calculation status, missing inputs, restrictions",
    error: "Loading error",
    subscriptionTitle: "Subscribers-only module",
    countries: "countries",
  };

  const regionLabels = REGION_LABELS[language] || REGION_LABELS.fr;

  useEffect(() => {
    fetchDownloadList();
  }, []);

  const fetchDownloadList = async () => {
    try {
      const res = await axios.get(`${API}/tariff-data/download/list`);
      setDownloadData(res.data);
      setSubscriptionNotice(null);
    } catch (err) {
      // Un refus d'abonnement (403 upgrade_required) est une réponse normale,
      // pas une panne : l'annoncer comme condition d'accès plutôt que comme
      // « Erreur de chargement ».
      const refusal = entitlementRefusal(err);
      setSubscriptionNotice(refusal ? entitlementNoticeText(refusal, language) : null);
      if (!refusal) console.error('Error fetching download list:', err);
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

  if (subscriptionNotice) {
    return (
      <Card className="border-2 border-amber-200">
        <CardContent className="p-8 text-center">
          <div className="text-4xl mb-3" aria-hidden="true">🔒</div>
          <div className="font-semibold text-gray-800 mb-1">{t.subscriptionTitle}</div>
          <p className="text-gray-600 max-w-xl mx-auto">{subscriptionNotice}</p>
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
          <div className="text-gray-600 mt-1">{t.subtitle(countries.length)}</div>
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
              <DownloadButton
                url={`/tariff-data/download-region-zip/${regionKey}`}
                label={t.downloadRegion}
                icon="📦"
                className="bg-white text-gray-800 shadow-md"
              />
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
                        <DownloadButton
                          url={country.download_url}
                          label={t.downloadCountry}
                          icon="📥"
                          className="bg-green-600 text-white"
                          size="small"
                        />
                        {country.json_ready && (
                          <DownloadButton
                            url={`/tariff-data/download-json/${country.code}`}
                            label={t.downloadJson}
                            icon="📋"
                            className="bg-blue-600 text-white"
                            size="small"
                          />
                        )}
                      </div>
                    </div>
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
