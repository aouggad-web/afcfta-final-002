import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { entitlementNoticeText, entitlementRefusal } from './entitlementNotice';
import { pick } from '../../i18n/lang';
import { nombre } from '../../utils/nombres';

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
  },
  ar: {
    afrique_nord: "شمال أفريقيا / اتحاد المغرب العربي",
    cedeao: "إيكواس / CEDEAO",
    cemac: "سيماك + جمهورية الكونغو الديمقراطية + ساو تومي وبرينسيب",
    eac: "EAC (مجموعة شرق أفريقيا)",
    sadc: "سادك / SACU",
    igad: "إيغاد / القرن الأفريقي",
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

/* Aucun téléchargement de tarif, quelle que soit la formule (décision du
   responsable produit, 03/11/2026) : l'écran n'affiche que le nombre de
   positions tarifaires nationales de chaque pays. */
export default function TariffDownloads({ language = 'fr' }) {
  const [downloadData, setDownloadData] = useState(null);
  const [subscriptionNotice, setSubscriptionNotice] = useState(null);
  const [loading, setLoading] = useState(true);

  const t = pick(language, {
    title: "Tarifs NPF (droit commun) : positions nationales",
    subtitle: (n) => `${n} pays — nombre de positions du tarif national tel que le calculateur l'applique`,
    loading: "Chargement des données...",
    positions: (n) => `${nombre(n, 'fr')} positions tarifaires nationales`,
    error: "Erreur de chargement",
    subscriptionTitle: "Module réservé aux abonnés",
    countries: "pays",
  }, {
    title: "MFN tariffs (common law): national tariff lines",
    subtitle: (n) => `${n} countries — number of national tariff lines as applied by the calculator`,
    loading: "Loading data...",
    positions: (n) => `${nombre(n, 'en')} national tariff lines`,
    error: "Loading error",
    subscriptionTitle: "Subscribers-only module",
    countries: "countries",
  }, {
    title: "تعريفات الدولة الأولى بالرعاية (NPF) (النظام العام): البنود الوطنية",
    subtitle: (n) => `عدد البلدان: ${n} — عدد بنود التعريفة الوطنية كما تطبّقها الحاسبة`,
    loading: "جارٍ تحميل البيانات…",
    positions: (n) => `عدد البنود التعريفية الوطنية: ${nombre(n, 'ar')}`,
    error: "خطأ في التحميل",
    subscriptionTitle: "وحدة مخصّصة للمشتركين",
    countries: "بلدًا",
  });

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
            📊 {t.title}
          </CardTitle>
          <div className="text-gray-600 mt-1">{t.subtitle(countries.length)}</div>
        </CardHeader>
      </Card>

      {Object.entries(regions).map(([regionKey, region]) => {
        const regionCountries = getCountriesForRegion(regionKey);

        return (
          <Card key={regionKey} className="border border-gray-200 overflow-hidden">
            <div className={`bg-gradient-to-r ${REGION_COLORS[regionKey]} text-white p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3`}>
              <div>
                <div className="text-lg font-bold flex items-center gap-2">
                  <span>{REGION_ICONS[regionKey]}</span>
                  <span>{regionLabels[regionKey]}</span>
                </div>
                <div className="text-sm opacity-90 mt-1">
                  {regionCountries.length} {t.countries}
                </div>
              </div>
            </div>

            <CardContent className="p-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {regionCountries.map((country) => (
                  <div key={country.code} className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between p-3 bg-gray-50">
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-sm truncate">{country.name}</div>
                        <div className="text-xs text-gray-500">{country.code}</div>
                        <div className="text-sm text-gray-700 mt-1" data-testid="positions-nationales">
                          {t.positions(country.positions)}
                        </div>
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
