/**
 * AfricaTradeMap - Carte des indicateurs économiques africains
 *
 * Carte à symboles proportionnels (leaflet) des 54 pays de la ZLECAf.
 * Chaque pays est représenté par un cercle dont la taille et la couleur
 * dépendent de l'indicateur sélectionné (PIB, PIB/habitant, population,
 * indice de développement, croissance). Données: Banque Mondiale (WDI 2024).
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Map as MapIcon, RefreshCw } from 'lucide-react';
import { getCountryFlag } from '../../utils/countryCodes';
import { AFRICA_CENTROIDS } from '../../utils/africaCentroids';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const TEXTS = {
  fr: {
    title: 'Carte économique de l’Afrique',
    subtitle: 'Indicateurs 2024 des 54 pays de la ZLECAf — Banque Mondiale',
    metric: 'Indicateur',
    loading: 'Chargement de la carte…',
    error: 'Impossible de charger les données.',
    rank: 'Rang Afrique',
    hint: 'La taille et la couleur des cercles reflètent la valeur de l’indicateur. Survolez un pays pour le détail.',
    metrics: {
      gdp: 'PIB (Mds USD)',
      gdpPerCapita: 'PIB par habitant (USD)',
      population: 'Population (millions)',
      hdi: 'Indice de développement',
      growth: 'Croissance PIB 2024 (%)',
    },
  },
  en: {
    title: 'Africa economic map',
    subtitle: '2024 indicators for the 54 AfCFTA countries — World Bank',
    metric: 'Indicator',
    loading: 'Loading map…',
    error: 'Unable to load data.',
    rank: 'Africa rank',
    hint: 'Circle size and colour reflect the indicator value. Hover a country for details.',
    metrics: {
      gdp: 'GDP (USD bn)',
      gdpPerCapita: 'GDP per capita (USD)',
      population: 'Population (millions)',
      hdi: 'Development index',
      growth: 'GDP growth 2024 (%)',
    },
  },
};

const METRIC_CONFIG = {
  gdp: { field: 'gdp_2024_billion_usd', diverging: false, fmt: (v) => `$${v.toFixed(1)} Mds` },
  gdpPerCapita: { field: 'gdp_per_capita_2024_usd', diverging: false, fmt: (v) => `$${v.toLocaleString('en-US')}` },
  population: { field: 'population_2024', diverging: false, fmt: (v) => `${(v / 1e6).toFixed(1)} M` },
  hdi: { field: 'development_index', diverging: false, fmt: (v) => v.toFixed(3) },
  growth: { field: 'growth_forecast_2024_pct', diverging: true, fmt: (v) => `${v.toFixed(1)} %` },
};

// Interpolation linéaire entre deux couleurs hex
const lerpColor = (a, b, t) => {
  const ah = parseInt(a.slice(1), 16);
  const bh = parseInt(b.slice(1), 16);
  const ar = ah >> 16, ag = (ah >> 8) & 0xff, ab = ah & 0xff;
  const br = bh >> 16, bg = (bh >> 8) & 0xff, bb = bh & 0xff;
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return `#${((1 << 24) + (r << 16) + (g << 8) + bl).toString(16).slice(1)}`;
};

export default function AfricaTradeMap({ language = 'fr' }) {
  const txt = TEXTS[language] || TEXTS.fr;
  const [metric, setMetric] = useState('gdp');
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`${API}/countries/economic-indicators?lang=${language}`);
        if (!cancelled && res.data?.success) setCountries(res.data.countries || []);
      } catch (err) {
        console.error('AfricaTradeMap: error loading indicators', err);
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [language]);

  const cfg = METRIC_CONFIG[metric];

  // Préparer les points: valeur, rayon (∝ √valeur), couleur
  const points = useMemo(() => {
    const rows = countries
      .map((c) => ({ ...c, value: c[cfg.field], coords: AFRICA_CENTROIDS[c.iso3] }))
      .filter((c) => c.coords && c.value != null);

    if (!rows.length) return [];

    const values = rows.map((r) => r.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const maxAbs = Math.max(...values.map((v) => Math.abs(v))) || 1;

    return rows.map((r) => {
      // Rayon proportionnel à la racine de la magnitude (surface ∝ valeur)
      const radius = 6 + Math.sqrt(Math.abs(r.value) / maxAbs) * 26;
      // Couleur
      let color;
      if (cfg.diverging) {
        // rouge (négatif) -> gris -> vert (positif)
        color = r.value < 0
          ? lerpColor('#9CA3AF', '#C0392B', Math.min(Math.abs(r.value) / maxAbs, 1))
          : lerpColor('#9CA3AF', '#1A7A4A', Math.min(r.value / maxAbs, 1));
      } else {
        const t = max > min ? (r.value - min) / (max - min) : 0.5;
        color = lerpColor('#F5D9B8', '#C8531A', t);
      }
      return { ...r, radius, color };
    });
  }, [countries, cfg]);

  return (
    <Card className="border-none shadow-xl overflow-hidden" data-testid="africa-trade-map">
      <CardHeader className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white pb-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-amber-500 rounded-xl flex items-center justify-center shadow-lg">
              <MapIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold">{txt.title}</CardTitle>
              <CardDescription className="text-slate-300 mt-0.5">{txt.subtitle}</CardDescription>
            </div>
          </div>
          <Badge className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1">
            WDI · 2024
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-5 space-y-4">
        {/* ── Sélecteur d'indicateur ──────────────────────────── */}
        <div className="max-w-xs">
          <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.metric}</label>
          <Select value={metric} onValueChange={setMetric}>
            <SelectTrigger data-testid="map-metric-select"><SelectValue /></SelectTrigger>
            <SelectContent>
              {Object.keys(METRIC_CONFIG).map((m) => (
                <SelectItem key={m} value={m}>{txt.metrics[m]}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* ── Carte ───────────────────────────────────────────── */}
        <div className="relative rounded-lg overflow-hidden border border-slate-200" style={{ height: 520 }}>
          {loading ? (
            <div className="flex items-center justify-center h-full text-slate-500 gap-2">
              <RefreshCw className="w-5 h-5 animate-spin" /> {txt.loading}
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full text-red-500">{txt.error}</div>
          ) : (
            <MapContainer center={[2, 18]} zoom={3} style={{ height: '100%', width: '100%' }} className="z-0" scrollWheelZoom={false}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              {points.map((p) => (
                <CircleMarker
                  key={p.iso3}
                  center={p.coords}
                  radius={p.radius}
                  fillColor={p.color}
                  color="#0a0e14"
                  weight={1}
                  fillOpacity={0.78}
                >
                  <Tooltip direction="top" offset={[0, -4]} opacity={0.95}>
                    <div className="text-center">
                      <strong className="text-sm">{getCountryFlag(p.iso3)} {p.name}</strong>
                      <br />
                      <span className="text-xs">{txt.metrics[metric]}: <strong>{cfg.fmt(p.value)}</strong></span>
                      {p.africa_rank != null && (
                        <>
                          <br />
                          <span className="text-xs text-gray-600">{txt.rank}: #{p.africa_rank}</span>
                        </>
                      )}
                    </div>
                  </Tooltip>
                </CircleMarker>
              ))}
            </MapContainer>
          )}
        </div>

        <p className="text-xs text-slate-400">{txt.hint}</p>
      </CardContent>
    </Card>
  );
}
