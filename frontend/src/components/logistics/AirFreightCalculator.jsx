import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Plane, DollarSign, Clock, Package, Info, Weight } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const FALLBACK_AIRPORTS = [
  { iata: 'CMN', name: 'Casablanca', country: 'Maroc', flag: '🇲🇦', region: 'Afrique du Nord' },
  { iata: 'LOS', name: 'Lagos', country: 'Nigeria', flag: '🇳🇬', region: "Afrique de l'Ouest" },
  { iata: 'NBO', name: 'Nairobi', country: 'Kenya', flag: '🇰🇪', region: "Afrique de l'Est" },
  { iata: 'JNB', name: 'Johannesburg', country: 'Afrique du Sud', flag: '🇿🇦', region: 'Afrique Australe' },
];

const FALLBACK_COMMODITIES = [
  { value: 'general', label_fr: 'Marchandise générale', label_en: 'General cargo' },
  { value: 'perishable', label_fr: 'Périssable (chaîne du froid)', label_en: 'Perishable (cold chain)' },
  { value: 'pharma', label_fr: 'Pharmaceutique', label_en: 'Pharma' },
  { value: 'dangerous', label_fr: 'Marchandise dangereuse', label_en: 'Dangerous goods' },
  { value: 'valuable', label_fr: 'Valeur / sécurisé', label_en: 'Valuable' },
  { value: 'live', label_fr: 'Animaux vivants', label_en: 'Live animals' },
];

const texts = {
  fr: {
    title: 'Calculateur de fret aérien',
    subtitle: 'Estimation 2024 — modèle calibré IATA TACT & tarifs cargo des compagnies africaines',
    origin: "Aéroport d'origine", destination: 'Aéroport de destination',
    weight: 'Poids brut (kg)', volume: 'Volume (m³, optionnel)', commodity: 'Nature de la marchandise',
    calculate: 'Calculer le fret', loading: 'Calcul en cours…', result: 'Décomposition des coûts',
    totalCost: 'Coût total estimé', airFreight: 'Fret aérien', fsc: 'Surcharge carburant (FSC)',
    ssc: 'Surcharge sûreté (SSC)', handling: 'Manutention + LTA', distance: 'Distance',
    transit: 'Délai de transit', carriers: 'Compagnies cargo', days: 'jours', km: 'km',
    chargeable: 'Poids taxable', actualW: 'Poids réel', volW: 'Poids volumétrique',
    ratePerKg: 'Taux', source: 'Source', disclaimer: 'Avertissement',
    selectAll: 'Sélectionnez les aéroports et le poids.', samePorts: 'Origine et destination doivent différer.',
    minCharge: 'Charge minimale appliquée', perKg: '/kg',
  },
  en: {
    title: 'Air Freight Calculator',
    subtitle: '2024 estimate — IATA TACT-calibrated model & African carrier cargo tariffs',
    origin: 'Origin airport', destination: 'Destination airport',
    weight: 'Gross weight (kg)', volume: 'Volume (m³, optional)', commodity: 'Commodity type',
    calculate: 'Calculate freight', loading: 'Calculating…', result: 'Cost breakdown',
    totalCost: 'Total estimated cost', airFreight: 'Air freight', fsc: 'Fuel surcharge (FSC)',
    ssc: 'Security surcharge (SSC)', handling: 'Handling + AWB', distance: 'Distance',
    transit: 'Transit time', carriers: 'Cargo carriers', days: 'days', km: 'km',
    chargeable: 'Chargeable weight', actualW: 'Actual weight', volW: 'Volumetric weight',
    ratePerKg: 'Rate', source: 'Source', disclaimer: 'Disclaimer',
    selectAll: 'Select airports and weight.', samePorts: 'Origin and destination must differ.',
    minCharge: 'Minimum charge applied', perKg: '/kg',
  },
};

function groupByRegion(list) {
  const groups = {};
  list.forEach((a) => {
    const key = a.region || 'Aéroports';
    if (!groups[key]) groups[key] = [];
    groups[key].push(a);
  });
  return groups;
}

function CostBar({ label, value, total, color }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-600">{label}</span>
        <span className="font-semibold">${value.toLocaleString()}</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function AirFreightCalculator({ language = 'fr' }) {
  const t = texts[language];

  const [airports, setAirports] = useState(FALLBACK_AIRPORTS);
  const [commodities, setCommodities] = useState(FALLBACK_COMMODITIES);
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [weight, setWeight] = useState('1000');
  const [volume, setVolume] = useState('');
  const [commodity, setCommodity] = useState('general');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    axios.get(`${API}/logistics/air/fees/airports`)
      .then(res => { if (res.data?.airports?.length) setAirports(res.data.airports); })
      .catch(() => {});
    axios.get(`${API}/logistics/air/fees/commodities`)
      .then(res => { if (res.data?.commodities?.length) setCommodities(res.data.commodities); })
      .catch(() => {});
  }, []);

  const destinationOptions = useMemo(
    () => airports.filter(a => a.iata !== origin),
    [airports, origin]
  );

  const handleOriginChange = (value) => {
    setOrigin(value);
    if (value === destination) setDestination('');
    setResult(null);
    setError('');
  };

  const handleCalculate = async () => {
    if (!origin || !destination || !weight) { setError(t.selectAll); return; }
    if (origin === destination) { setError(t.samePorts); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.get(`${API}/logistics/air/fees/cost`, {
        params: {
          origin, destination,
          weight_kg: parseFloat(weight),
          volume_m3: volume ? parseFloat(volume) : undefined,
          commodity,
        },
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || t.selectAll);
    } finally {
      setLoading(false);
    }
  };

  const commodityLabel = (c) => (language === 'fr' ? c.label_fr : c.label_en);

  return (
    <div className="space-y-4" data-testid="air-freight-calculator">
      <Card className="border border-sky-200 bg-gradient-to-r from-sky-50 to-blue-50">
        <CardHeader className="py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-sky-600 rounded-lg flex items-center justify-center">
              <Plane className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-gray-800">{t.title}</CardTitle>
              <CardDescription className="text-xs text-sky-700">{t.subtitle}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.origin}</label>
              <select
                value={origin}
                onChange={e => handleOriginChange(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-sky-400"
                data-testid="air-origin-select"
              >
                <option value="">— {t.origin} —</option>
                {Object.entries(groupByRegion(airports)).map(([region, list]) => (
                  <optgroup key={region} label={region}>
                    {list.map(a => (
                      <option key={a.iata} value={a.iata}>{a.flag} {a.name} ({a.iata})</option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.destination}</label>
              <select
                value={destination}
                onChange={e => { setDestination(e.target.value); setResult(null); setError(''); }}
                disabled={!origin}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-sky-400 disabled:opacity-50"
                data-testid="air-destination-select"
              >
                <option value="">— {t.destination} —</option>
                {Object.entries(groupByRegion(destinationOptions)).map(([region, list]) => (
                  <optgroup key={region} label={region}>
                    {list.map(a => (
                      <option key={a.iata} value={a.iata}>{a.flag} {a.name} ({a.iata})</option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.weight}</label>
              <input
                type="number" min="1" value={weight}
                onChange={e => setWeight(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-sky-400"
                data-testid="air-weight-input"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.volume}</label>
              <input
                type="number" min="0" step="0.1" value={volume}
                onChange={e => setVolume(e.target.value)}
                placeholder="0"
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-sky-400"
                data-testid="air-volume-input"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">{t.commodity}</label>
              <select
                value={commodity}
                onChange={e => setCommodity(e.target.value)}
                className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-sky-400"
                data-testid="air-commodity-select"
              >
                {commodities.map(c => (
                  <option key={c.value} value={c.value}>{commodityLabel(c)}</option>
                ))}
              </select>
            </div>
          </div>

          <Button
            onClick={handleCalculate}
            disabled={loading || !origin || !destination || !weight}
            className="bg-sky-600 hover:bg-sky-700 text-white px-6 py-2 rounded-lg text-sm font-medium w-full md:w-auto"
            data-testid="air-calculate-btn"
          >
            <Plane className="w-4 h-4 mr-2" />
            {loading ? t.loading : t.calculate}
          </Button>

          {error && (
            <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 flex items-start gap-2">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <Card className="border border-green-200 bg-gradient-to-r from-green-50 to-emerald-50" data-testid="air-result-card">
          <CardHeader className="py-4 border-b border-green-100">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-gray-800">{t.result}</CardTitle>
              <Badge className="bg-amber-100 text-amber-800 text-xs">{language === 'fr' ? 'Estimé' : 'Modeled'} · {result.data_year}</Badge>
            </div>
            <div className="flex flex-wrap gap-2 mt-1">
              <Badge variant="outline" className="text-xs"><Plane className="w-3 h-3 mr-1" />{result.origin_iata} → {result.destination_iata}</Badge>
              <Badge variant="outline" className="text-xs">{result.distance_km.toLocaleString()} {t.km}</Badge>
              <Badge variant="outline" className="text-xs"><Clock className="w-3 h-3 mr-1" />{result.transit_days_min}–{result.transit_days_max} {t.days}</Badge>
              <Badge variant="outline" className="text-xs"><Package className="w-3 h-3 mr-1" />{result.commodity_label}</Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-5">
            <div className="text-center py-4 bg-white rounded-xl border border-green-200 shadow-sm">
              <p className="text-xs text-gray-500 mb-1">{t.totalCost}</p>
              <p className="text-4xl font-bold text-green-700" data-testid="air-total-cost">${result.total_cost_usd.toLocaleString()}</p>
              <p className="text-xs text-gray-400 mt-1">
                USD · {result.rate_per_kg_usd}{t.perKg} × {result.chargeable_weight_kg.toLocaleString()} kg
                {result.min_charge_applied ? ` · ${t.minCharge}` : ''}
              </p>
            </div>

            {/* Chargeable weight breakdown */}
            <div className="grid grid-cols-3 gap-2">
              <div className="text-center p-2 bg-gray-50 rounded-lg border border-gray-100">
                <p className="text-xs text-gray-500">{t.actualW}</p>
                <p className="font-bold text-gray-800">{result.actual_weight_kg.toLocaleString()} kg</p>
              </div>
              <div className="text-center p-2 bg-gray-50 rounded-lg border border-gray-100">
                <p className="text-xs text-gray-500">{t.volW}</p>
                <p className="font-bold text-gray-800">{result.volumetric_weight_kg.toLocaleString()} kg</p>
              </div>
              <div className="text-center p-2 bg-sky-50 rounded-lg border border-sky-100">
                <p className="text-xs text-sky-600 flex items-center justify-center gap-1"><Weight className="w-3 h-3" />{t.chargeable}</p>
                <p className="font-bold text-sky-800">{result.chargeable_weight_kg.toLocaleString()} kg</p>
              </div>
            </div>

            <div className="space-y-3">
              <CostBar label={t.airFreight} value={result.air_freight_usd} total={result.total_cost_usd} color="bg-sky-500" />
              <CostBar label={t.fsc} value={result.fuel_surcharge_usd} total={result.total_cost_usd} color="bg-orange-400" />
              <CostBar label={t.ssc} value={result.security_surcharge_usd} total={result.total_cost_usd} color="bg-purple-400" />
              <CostBar label={t.handling} value={result.handling_awb_usd} total={result.total_cost_usd} color="bg-emerald-400" />
            </div>

            <div className="p-3 bg-white rounded-lg border border-gray-100">
              <p className="text-xs font-semibold text-gray-500 mb-1">{t.carriers}</p>
              <div className="flex flex-wrap gap-1">
                {result.carriers.map(c => (<Badge key={c} variant="secondary" className="text-xs">{c}</Badge>))}
              </div>
            </div>

            <div className="space-y-2">
              <div className="p-3 bg-white rounded-lg border border-gray-100 text-xs">
                <span className="font-semibold text-gray-600">{t.source}: </span>
                <span className="text-gray-600">{result.source}</span>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-xs text-gray-500">
                <span className="font-semibold">{t.disclaimer}: </span>{result.disclaimer}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
