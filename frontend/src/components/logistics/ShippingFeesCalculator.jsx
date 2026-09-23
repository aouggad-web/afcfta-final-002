import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Ship, DollarSign, Clock, Anchor, BarChart3, Info, ExternalLink } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Fallback list used only if the /fees/ports endpoint is unavailable.
const FALLBACK_PORTS = [
  { locode: 'MAPTM', name: 'Tanger Med', country: 'Maroc', flag: '🇲🇦', region: 'Afrique du Nord' },
  { locode: 'SNDKR', name: 'Dakar', country: 'Sénégal', flag: '🇸🇳', region: "Afrique de l'Ouest" },
  { locode: 'NGAPP', name: 'Lagos (Apapa)', country: 'Nigeria', flag: '🇳🇬', region: "Afrique de l'Ouest" },
  { locode: 'KEMBA', name: 'Mombasa', country: 'Kenya', flag: '🇰🇪', region: "Afrique de l'Est" },
  { locode: 'ZADUR', name: 'Durban', country: 'Afrique du Sud', flag: '🇿🇦', region: 'Afrique Australe' },
];

const MAX_TABLE_ROWS = 250;

// Group a port list by region for optgroup rendering.
function groupByRegion(list) {
  const groups = {};
  list.forEach((p) => {
    const key = p.region || 'Ports';
    if (!groups[key]) groups[key] = [];
    groups[key].push(p);
  });
  return groups;
}

const CONTAINER_TYPES = [
  { value: 'teu', label: '20\' Standard (TEU)', labelEn: "20' Standard (TEU)" },
  { value: 'feu', label: '40\' Standard (FEU)', labelEn: "40' Standard (FEU)" },
  { value: 'feu_hc', label: '40\' High Cube (FEU HC)', labelEn: "40' High Cube (FEU HC)" },
];

const texts = {
  fr: {
    title: 'Calculateur de frais portuaires',
    subtitle: 'Données réelles 2024 — Tarifs publiés par les armateurs et autorités portuaires',
    origin: 'Port d\'origine',
    destination: 'Port de destination',
    containerType: 'Type de conteneur',
    calculate: 'Calculer les frais',
    loading: 'Calcul en cours…',
    result: 'Décomposition des coûts',
    oceanFreight: 'Fret maritime',
    originTHC: 'THC départ',
    destinationTHC: 'THC arrivée',
    totalCost: 'Coût total estimé',
    distance: 'Distance',
    transitTime: 'Délai de transit',
    carriers: 'Armateurs',
    frequency: 'Fréquence',
    days: 'jours',
    nm: 'milles nautiques',
    source: 'Source',
    notes: 'Notes',
    disclaimer: 'Avertissement',
    noRoute: 'Aucune route directe trouvée entre ces deux ports. Veuillez sélectionner une autre paire.',
    selectPorts: 'Sélectionnez un port d\'origine et un port de destination pour calculer les frais.',
    samePorts: 'Les ports d\'origine et de destination doivent être différents.',
    thcTitle: 'THC (Terminal Handling Charges)',
    thcDesc: 'Frais de manutention terminale facturés par le port, en sus du fret maritime.',
    dataYear: 'Année des données',
    allRoutes: 'Toutes les routes disponibles',
    routesCount: 'routes répertoriées',
    viewAllRoutes: 'Voir toutes les routes',
    hideAllRoutes: 'Masquer les routes',
    selectOriginFirst: 'Sélectionnez d\'abord un port d\'origine',
    availableFrom: 'Routes disponibles depuis',
  },
  en: {
    title: 'Port Shipping Fees Calculator',
    subtitle: 'Real 2024 Data — Rates from published carrier tariffs & port authorities',
    origin: 'Origin Port',
    destination: 'Destination Port',
    containerType: 'Container Type',
    calculate: 'Calculate Fees',
    loading: 'Calculating…',
    result: 'Cost Breakdown',
    oceanFreight: 'Ocean Freight',
    originTHC: 'Origin THC',
    destinationTHC: 'Destination THC',
    totalCost: 'Total Estimated Cost',
    distance: 'Distance',
    transitTime: 'Transit Time',
    carriers: 'Carriers',
    frequency: 'Frequency',
    days: 'days',
    nm: 'nautical miles',
    source: 'Source',
    notes: 'Notes',
    disclaimer: 'Disclaimer',
    noRoute: 'No direct route found between these two ports. Please select a different pair.',
    selectPorts: 'Select an origin and destination port to calculate shipping fees.',
    samePorts: 'Origin and destination ports must be different.',
    thcTitle: 'THC (Terminal Handling Charges)',
    thcDesc: 'Terminal handling charges billed by the port, in addition to ocean freight.',
    dataYear: 'Data Year',
    allRoutes: 'All Available Routes',
    routesCount: 'routes listed',
    viewAllRoutes: 'View all routes',
    hideAllRoutes: 'Hide routes',
    selectOriginFirst: 'Select an origin port first',
    availableFrom: 'Routes available from',
  },
};

function CostBar({ label, value, total, color }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-[var(--afcfta-muted)]">{label}</span>
        <span className="font-semibold">${value.toLocaleString()}</span>
      </div>
      <div className="h-2 bg-[var(--afcfta-card2)] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function ShippingFeesCalculator({ language = 'fr' }) {
  const t = texts[language];

  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [containerType, setContainerType] = useState('teu');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [allRoutes, setAllRoutes] = useState([]);
  const [showAllRoutes, setShowAllRoutes] = useState(false);
  const [ports, setPorts] = useState(FALLBACK_PORTS);

  // Load the full African port list (≈55 ports) for the selectors
  useEffect(() => {
    axios.get(`${API}/logistics/fees/ports`)
      .then(res => {
        if (res.data?.ports?.length) setPorts(res.data.ports);
      })
      .catch(() => {});
  }, []);

  // Load all routes on mount to populate destination options based on origin
  useEffect(() => {
    axios.get(`${API}/logistics/fees/routes`)
      .then(res => setAllRoutes(res.data.routes || []))
      .catch(() => {});
  }, []);

  // Destinations reachable from the selected origin (derived, no effect)
  const availableDestinations = useMemo(() => {
    if (!origin) return [];
    const dests = new Set();
    allRoutes.forEach(r => {
      if (r.origin_locode === origin) dests.add(r.destination_locode);
      if (r.destination_locode === origin) dests.add(r.origin_locode);
    });
    return ports.filter(p => dests.has(p.locode) && p.locode !== origin);
  }, [origin, allRoutes, ports]);

  const handleOriginChange = (value) => {
    setOrigin(value);
    setDestination('');
    setResult(null);
    setError('');
  };

  const handleCalculate = async () => {
    if (!origin || !destination) {
      setError(t.selectPorts);
      return;
    }
    if (origin === destination) {
      setError(t.samePorts);
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await axios.get(`${API}/logistics/fees/cost`, {
        params: { origin, destination, container_type: containerType },
      });
      setResult(res.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError(t.noRoute);
      } else {
        setError(err.response?.data?.detail || t.noRoute);
      }
    } finally {
      setLoading(false);
    }
  };

  const containerLabel = (type) => {
    const ct = CONTAINER_TYPES.find(c => c.value === type);
    return ct ? (language === 'fr' ? ct.label : ct.labelEn) : type;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card className="border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]">
        <CardHeader className="py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-[var(--text)]" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-[var(--text)]">{t.title}</CardTitle>
              <CardDescription className="text-xs text-[var(--info)]">{t.subtitle}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {/* Selectors */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            {/* Origin */}
            <div>
              <label className="block text-xs font-medium text-[var(--text)] mb-1">{t.origin}</label>
              <select
                value={origin}
                onChange={e => handleOriginChange(e.target.value)}
                className="w-full text-sm border border-[var(--afcfta-border)] rounded-lg px-3 py-2 bg-[var(--afcfta-card)] focus:outline-none focus:ring-2 focus:ring-blue-400"
                data-testid="fees-origin-select"
              >
                <option value="">— {t.origin} —</option>
                {Object.entries(groupByRegion(ports)).map(([region, list]) => (
                  <optgroup key={region} label={region}>
                    {list.map(p => (
                      <option key={p.locode} value={p.locode}>
                        {p.flag} {p.name} ({p.country})
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>

            {/* Destination */}
            <div>
              <label className="block text-xs font-medium text-[var(--text)] mb-1">{t.destination}</label>
              <select
                value={destination}
                onChange={e => setDestination(e.target.value)}
                disabled={!origin}
                className="w-full text-sm border border-[var(--afcfta-border)] rounded-lg px-3 py-2 bg-[var(--afcfta-card)] focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50"
                data-testid="fees-destination-select"
              >
                <option value="">
                  {origin ? `— ${t.destination} —` : t.selectOriginFirst}
                </option>
                {Object.entries(groupByRegion(availableDestinations)).map(([region, list]) => (
                  <optgroup key={region} label={region}>
                    {list.map(p => (
                      <option key={p.locode} value={p.locode}>
                        {p.flag} {p.name} ({p.country})
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>

            {/* Container type */}
            <div>
              <label className="block text-xs font-medium text-[var(--text)] mb-1">{t.containerType}</label>
              <select
                value={containerType}
                onChange={e => setContainerType(e.target.value)}
                className="w-full text-sm border border-[var(--afcfta-border)] rounded-lg px-3 py-2 bg-[var(--afcfta-card)] focus:outline-none focus:ring-2 focus:ring-blue-400"
              >
                {CONTAINER_TYPES.map(ct => (
                  <option key={ct.value} value={ct.value}>
                    {language === 'fr' ? ct.label : ct.labelEn}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <Button
            onClick={handleCalculate}
            disabled={loading || !origin || !destination}
            className="bg-[var(--info)] hover:bg-[var(--info)] text-[var(--bg)] px-6 py-2 rounded-lg text-sm font-medium w-full md:w-auto"
            data-testid="fees-calculate-btn"
          >
            <Ship className="w-4 h-4 mr-2" />
            {loading ? t.loading : t.calculate}
          </Button>

          {error && (
            <div className="mt-3 p-3 bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] rounded-lg text-sm text-[var(--gold)] flex items-start gap-2">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Result */}
      {result && (
        <Card className="border border-[color-mix(in_srgb,var(--success)_30%,transparent)] bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))]">
          <CardHeader className="py-4 border-b border-[color-mix(in_srgb,var(--success)_30%,transparent)]">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-bold text-[var(--text)]">{t.result}</CardTitle>
              <Badge className="bg-[color-mix(in_srgb,var(--success)_8%,var(--afcfta-card))] text-[var(--success)] text-xs">
                {t.dataYear}: {result.data_year}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-2 mt-1">
              <Badge variant="outline" className="text-xs">
                <Anchor className="w-3 h-3 mr-1" />
                {result.origin_port} → {result.destination_port}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {containerLabel(containerType)}
              </Badge>
              <Badge variant="outline" className="text-xs">
                <Ship className="w-3 h-3 mr-1" />
                {result.distance_nm.toLocaleString()} {t.nm}
              </Badge>
              <Badge variant="outline" className="text-xs">
                <Clock className="w-3 h-3 mr-1" />
                {result.transit_days_min}–{result.transit_days_max} {t.days}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-4 space-y-5">
            {/* Total */}
            <div className="text-center py-4 bg-[var(--afcfta-card)] rounded-xl border border-[color-mix(in_srgb,var(--success)_30%,transparent)] shadow-sm">
              <p className="text-xs text-[var(--afcfta-muted)] mb-1">{t.totalCost}</p>
              <p className="text-4xl font-bold text-[var(--success)]">
                ${result.total_cost_usd.toLocaleString()}
              </p>
              <p className="text-xs text-[var(--afcfta-muted)] mt-1">USD / {containerLabel(containerType)}</p>
            </div>

            {/* Cost bars */}
            <div className="space-y-3">
              <CostBar
                label={t.oceanFreight}
                value={result.ocean_freight_usd}
                total={result.total_cost_usd}
                color="bg-blue-500"
              />
              {result.origin_thc_usd > 0 && (
                <CostBar
                  label={`${t.originTHC} (${result.origin_port})`}
                  value={result.origin_thc_usd}
                  total={result.total_cost_usd}
                  color="bg-orange-400"
                />
              )}
              {result.destination_thc_usd > 0 && (
                <CostBar
                  label={`${t.destinationTHC} (${result.destination_port})`}
                  value={result.destination_thc_usd}
                  total={result.total_cost_usd}
                  color="bg-purple-400"
                />
              )}
            </div>

            {/* Numeric breakdown */}
            <div className="grid grid-cols-3 gap-2">
              <div className="text-center p-2 bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                <p className="text-xs text-[var(--info)]">{t.oceanFreight}</p>
                <p className="font-bold text-[var(--info)]">${result.ocean_freight_usd.toLocaleString()}</p>
              </div>
              <div className="text-center p-2 bg-[color-mix(in_srgb,var(--terra)_8%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--terra)_30%,transparent)]">
                <p className="text-xs text-[var(--terra)]">{t.originTHC}</p>
                <p className="font-bold text-[var(--terra)]">${result.origin_thc_usd.toLocaleString()}</p>
              </div>
              <div className="text-center p-2 bg-[color-mix(in_srgb,var(--violet)_8%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--violet)_30%,transparent)]">
                <p className="text-xs text-[var(--violet)]">{t.destinationTHC}</p>
                <p className="font-bold text-[var(--violet)]">${result.destination_thc_usd.toLocaleString()}</p>
              </div>
            </div>

            {/* Carriers & Frequency */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-3 bg-[var(--afcfta-card)] rounded-lg border border-[var(--afcfta-border)]">
                <p className="text-xs font-semibold text-[var(--afcfta-muted)] mb-1">{t.carriers}</p>
                <div className="flex flex-wrap gap-1">
                  {result.carriers.map(c => (
                    <Badge key={c} variant="secondary" className="text-xs">{c}</Badge>
                  ))}
                </div>
              </div>
              <div className="p-3 bg-[var(--afcfta-card)] rounded-lg border border-[var(--afcfta-border)]">
                <p className="text-xs font-semibold text-[var(--afcfta-muted)] mb-1">{t.frequency}</p>
                <p className="text-sm font-medium text-[var(--text)]">{result.frequency}</p>
              </div>
            </div>

            {/* Source & Notes */}
            <div className="space-y-2">
              {result.source && (
                <div className="p-3 bg-[var(--afcfta-card)] rounded-lg border border-[var(--afcfta-border)] text-xs">
                  <span className="font-semibold text-[var(--afcfta-muted)]">{t.source}: </span>
                  <span className="text-[var(--afcfta-muted)]">{result.source}</span>
                </div>
              )}
              {result.notes && (
                <div className="p-3 bg-[color-mix(in_srgb,var(--gold)_8%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] text-xs text-[var(--gold)]">
                  <span className="font-semibold">{t.notes}: </span>
                  {result.notes}
                </div>
              )}
              <div className="p-3 bg-[var(--afcfta-card2)] rounded-lg border border-[var(--afcfta-border)] text-xs text-[var(--afcfta-muted)]">
                <span className="font-semibold">{t.disclaimer}: </span>
                {result.disclaimer}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* All routes table (collapsible) */}
      <Card className="border border-[var(--afcfta-border)]">
        <CardHeader className="py-3 cursor-pointer" onClick={() => setShowAllRoutes(v => !v)}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[var(--afcfta-muted)]" />
              <CardTitle className="text-sm font-semibold text-[var(--text)]">{t.allRoutes}</CardTitle>
              <Badge variant="secondary" className="text-xs">{allRoutes.length} {t.routesCount}</Badge>
            </div>
            <Button variant="ghost" size="sm" className="text-xs">
              {showAllRoutes ? t.hideAllRoutes : t.viewAllRoutes}
            </Button>
          </div>
        </CardHeader>
        {showAllRoutes && allRoutes.length > 0 && (
          <CardContent className="pt-0">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b bg-[var(--afcfta-card2)]">
                    <th className="text-left p-2 font-semibold text-[var(--afcfta-muted)]">Origine</th>
                    <th className="text-left p-2 font-semibold text-[var(--afcfta-muted)]">Destination</th>
                    <th className="text-right p-2 font-semibold text-[var(--afcfta-muted)]">TEU (USD)</th>
                    <th className="text-right p-2 font-semibold text-[var(--afcfta-muted)]">FEU (USD)</th>
                    <th className="text-right p-2 font-semibold text-[var(--afcfta-muted)]">Distance (nm)</th>
                    <th className="text-right p-2 font-semibold text-[var(--afcfta-muted)]">Transit</th>
                    <th className="text-left p-2 font-semibold text-[var(--afcfta-muted)]">Type</th>
                    <th className="text-left p-2 font-semibold text-[var(--afcfta-muted)]">Armateurs</th>
                  </tr>
                </thead>
                <tbody>
                  {allRoutes.slice(0, MAX_TABLE_ROWS).map(r => (
                    <tr key={r.route_id} className="border-b hover:bg-[var(--afcfta-card2)] transition-colors">
                      <td className="p-2 font-medium text-[var(--text)]">{r.origin_port}</td>
                      <td className="p-2 text-[var(--text)]">{r.destination_port}</td>
                      <td className="p-2 text-right font-semibold text-[var(--info)]">
                        ${r.teu_usd.toLocaleString()}
                      </td>
                      <td className="p-2 text-right text-[var(--text)]">
                        ${r.feu_usd.toLocaleString()}
                      </td>
                      <td className="p-2 text-right text-[var(--afcfta-muted)]">
                        {r.distance_nm.toLocaleString()}
                      </td>
                      <td className="p-2 text-right text-[var(--afcfta-muted)]">
                        {r.transit_days_min}–{r.transit_days_max}j
                      </td>
                      <td className="p-2">
                        <Badge
                          variant="outline"
                          className={`text-[11px] py-0 ${r.is_modeled ? 'text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]' : 'text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]'}`}
                        >
                          {r.is_modeled ? (language === 'fr' ? 'Estimé' : 'Modeled') : (language === 'fr' ? 'Publié' : 'Published')}
                        </Badge>
                      </td>
                      <td className="p-2">
                        <div className="flex flex-wrap gap-1">
                          {r.carriers.slice(0, 2).map(c => (
                            <Badge key={c} variant="outline" className="text-xs py-0">{c}</Badge>
                          ))}
                          {r.carriers.length > 2 && (
                            <Badge variant="outline" className="text-xs py-0">+{r.carriers.length - 2}</Badge>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-[var(--afcfta-muted)] italic">
              {allRoutes.length > MAX_TABLE_ROWS && (
                <span className="block not-italic text-[var(--afcfta-muted)] mb-1">
                  {language === 'fr'
                    ? `Affichage des ${MAX_TABLE_ROWS} premières routes sur ${allRoutes.length}. Utilisez le calculateur ci-dessus pour une paire précise.`
                    : `Showing first ${MAX_TABLE_ROWS} of ${allRoutes.length} routes. Use the calculator above for a specific pair.`}
                </span>
              )}
              {language === 'fr'
                ? 'Sources : Drewry Maritime Research 2024, UNCTAD MRTS 2024, tarifs publiés CMA CGM / Maersk / MSC / Hapag-Lloyd. « Publié » = tarif armateur publié ; « Estimé » = modèle distance-coût calibré.'
                : 'Sources: Drewry Maritime Research 2024, UNCTAD MRTS 2024, published CMA CGM / Maersk / MSC / Hapag-Lloyd tariffs. "Published" = carrier-published rate; "Modeled" = calibrated distance-cost model.'}
            </p>
          </CardContent>
        )}
      </Card>
    </div>
  );
}
