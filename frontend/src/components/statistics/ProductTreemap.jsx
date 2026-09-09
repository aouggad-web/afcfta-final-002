/**
 * ProductTreemap - Cartographie des exportations/importations par produit (SH)
 *
 * Visualisation en treemap de la structure du commerce d'un pays africain,
 * branchée sur l'API OEC/BACI en direct (mêmes endpoints que OECTradeStats).
 * Chaque rectangle = un produit (chapitre SH2, position SH4 ou sous-position SH6),
 * sa surface est proportionnelle à la valeur échangée.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { ResponsiveContainer, Treemap, Tooltip } from 'recharts';
import { LayoutGrid, RefreshCw, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { getCountryFlag } from '../../utils/countryCodes';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const AVAILABLE_YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018];

const HS_LEVELS = [
  { value: 'HS2', digits: 2 },
  { value: 'HS4', digits: 4 },
  { value: 'HS6', digits: 6 },
];

// Palette chaude/terre cohérente avec le thème de la plateforme
const PALETTE = [
  '#C8531A', '#D4891A', '#1A7A4A', '#1A6B8A', '#8A5A1A',
  '#A03C12', '#34853A', '#2A8A9A', '#B5701A', '#6A4A8A',
  '#C0392B', '#27AE60', '#2980B9', '#D68910', '#7D6608',
];

const formatUSD = (v) => {
  if (!v && v !== 0) return '—';
  if (v >= 1e9) return `$${(v / 1e9).toFixed(2)} Mds`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(1)} M`;
  if (v >= 1e3) return `$${(v / 1e3).toFixed(1)} k`;
  return `$${v.toFixed(0)}`;
};

const TEXTS = {
  fr: {
    title: 'Cartographie des produits',
    subtitle: 'Structure du commerce par produit (SH) — données OEC/BACI en direct',
    country: 'Pays',
    selectCountry: 'Choisir un pays',
    year: 'Année',
    flow: 'Flux',
    exports: 'Exportations',
    imports: 'Importations',
    level: 'Niveau SH',
    loading: 'Chargement des données…',
    error: 'Impossible de charger les données pour cette sélection.',
    noData: 'Aucune donnée disponible pour cette sélection.',
    others: 'Autres produits',
    share: 'Part',
    total: 'Total',
    products: 'produits',
    hint: 'La surface de chaque bloc est proportionnelle à la valeur échangée. Survolez un bloc pour le détail.',
    levelHint: { HS2: 'Chapitres (2 chiffres)', HS4: 'Positions (4 chiffres)', HS6: 'Sous-positions (6 chiffres)' },
  },
  en: {
    title: 'Product map',
    subtitle: 'Trade structure by product (HS) — live OEC/BACI data',
    country: 'Country',
    selectCountry: 'Choose a country',
    year: 'Year',
    flow: 'Flow',
    exports: 'Exports',
    imports: 'Imports',
    level: 'HS level',
    loading: 'Loading data…',
    error: 'Unable to load data for this selection.',
    noData: 'No data available for this selection.',
    others: 'Other products',
    share: 'Share',
    total: 'Total',
    products: 'products',
    hint: 'Each block area is proportional to the traded value. Hover a block for details.',
    levelHint: { HS2: 'Chapters (2 digits)', HS4: 'Positions (4 digits)', HS6: 'Sub-positions (6 digits)' },
  },
};

/* ── Contenu personnalisé d'une cellule du treemap ─────────────── */
const TreemapCell = (props) => {
  const { x, y, width, height, index, name, share, colorIndex } = props;
  const fill = PALETTE[(colorIndex ?? index) % PALETTE.length];
  const showLabel = width > 64 && height > 30;
  const showShare = width > 64 && height > 48;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        rx={3}
        style={{ fill, stroke: 'rgba(10,14,20,0.65)', strokeWidth: 1.5 }}
      />
      {showLabel && (
        <text x={x + 7} y={y + 18} fill="#fff" fontSize={11} fontWeight={600}>
          {name?.length > Math.floor(width / 7) ? `${name.slice(0, Math.floor(width / 7))}…` : name}
        </text>
      )}
      {showShare && (
        <text x={x + 7} y={y + 34} fill="rgba(255,255,255,0.85)" fontSize={10}>
          {share != null ? `${share.toFixed(1)}%` : ''}
        </text>
      )}
    </g>
  );
};

/* ── Tooltip ───────────────────────────────────────────────────── */
const makeTooltip = (txt) => ({ active, payload }) => {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div
      style={{
        background: 'rgba(16,22,32,0.97)',
        border: '1px solid rgba(212,137,26,0.3)',
        borderRadius: 10,
        padding: '10px 14px',
        fontSize: '0.8rem',
        maxWidth: 280,
      }}
    >
      <p style={{ color: '#EAE0D0', fontWeight: 700, marginBottom: 4 }}>
        {d.hsId ? `${d.hsId} · ` : ''}{d.fullName}
      </p>
      <p style={{ color: '#D4891A', margin: 0 }}>
        <strong>{formatUSD(d.size)}</strong>
      </p>
      {d.share != null && (
        <p style={{ color: 'rgba(142,155,174,0.85)', margin: '2px 0 0' }}>
          {txt.share}: {d.share.toFixed(2)}%
        </p>
      )}
    </div>
  );
};

export default function ProductTreemap({ language = 'fr' }) {
  const txt = TEXTS[language] || TEXTS.fr;

  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('NGA');
  const [year, setYear] = useState(2024);
  const [flow, setFlow] = useState('exports');
  const [hsLevel, setHsLevel] = useState('HS2');

  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Charger la liste des pays africains
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get(`${API}/oec/countries?lang=${language}`);
        if (!cancelled && res.data?.success) setCountries(res.data.countries || []);
      } catch (err) {
        console.error('ProductTreemap: error loading countries', err);
      }
    })();
    return () => { cancelled = true; };
  }, [language]);

  // Charger les données commerciales
  const fetchData = useCallback(async () => {
    if (!selectedCountry) return;
    setLoading(true);
    setError(null);
    try {
      const endpoint = flow === 'exports'
        ? `${API}/oec/exports/${selectedCountry}`
        : `${API}/oec/imports/${selectedCountry}`;
      const res = await axios.get(endpoint, {
        params: { year, limit: 40, hs_level: hsLevel },
      });
      setResponse(res.data);
    } catch (err) {
      console.error('ProductTreemap: error loading trade data', err);
      setError(err.message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }, [selectedCountry, year, flow, hsLevel]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Préparer les données du treemap (top N + agrégat "Autres")
  const treemapData = useMemo(() => {
    if (!response?.data?.length) return [];
    const total = response.total_value || response.data.reduce((s, r) => s + (r['Trade Value'] || 0), 0);
    if (!total) return [];

    const nodes = response.data.map((item, i) => {
      const fullName = item[hsLevel] || `${txt.products} #${i + 1}`;
      const value = item['Trade Value'] || 0;
      return {
        name: fullName,
        fullName,
        hsId: item[`${hsLevel} ID`] != null ? String(item[`${hsLevel} ID`]).slice(-HS_LEVELS.find(l => l.value === hsLevel).digits) : '',
        size: value,
        share: (value / total) * 100,
        colorIndex: i,
      };
    });

    const displayedSum = nodes.reduce((s, n) => s + n.size, 0);
    const remainder = total - displayedSum;
    if (remainder > total * 0.005) {
      nodes.push({
        name: txt.others,
        fullName: txt.others,
        hsId: '',
        size: remainder,
        share: (remainder / total) * 100,
        colorIndex: PALETTE.length - 1,
      });
    }
    return nodes;
  }, [response, hsLevel, txt]);

  const total = response?.total_value || 0;
  const TooltipContent = useMemo(() => makeTooltip(txt), [txt]);

  return (
    <Card className="border-none shadow-xl overflow-hidden" data-testid="product-treemap">
      <CardHeader className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white pb-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-amber-500 rounded-xl flex items-center justify-center shadow-lg">
              <LayoutGrid className="w-7 h-7 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold">{txt.title}</CardTitle>
              <CardDescription className="text-slate-300 mt-0.5">{txt.subtitle}</CardDescription>
            </div>
          </div>
          <Badge className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-3 py-1">
            OEC/BACI · {year}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-5 space-y-4">
        {/* ── Contrôles ───────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.country}</label>
            <Select value={selectedCountry} onValueChange={setSelectedCountry}>
              <SelectTrigger data-testid="treemap-country-select">
                <SelectValue placeholder={txt.selectCountry} />
              </SelectTrigger>
              <SelectContent>
                {countries.map((c) => (
                  <SelectItem key={c.iso3} value={c.iso3}>
                    <span className="flex items-center gap-2">
                      <span>{getCountryFlag(c.iso3)}</span>
                      <span>{c.name}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.year}</label>
            <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
              <SelectTrigger data-testid="treemap-year-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {AVAILABLE_YEARS.map((y) => (
                  <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.flow}</label>
            <Select value={flow} onValueChange={setFlow}>
              <SelectTrigger data-testid="treemap-flow-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="exports">
                  <span className="flex items-center gap-2"><ArrowUpRight className="w-3.5 h-3.5 text-emerald-600" />{txt.exports}</span>
                </SelectItem>
                <SelectItem value="imports">
                  <span className="flex items-center gap-2"><ArrowDownRight className="w-3.5 h-3.5 text-blue-600" />{txt.imports}</span>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.level}</label>
            <Select value={hsLevel} onValueChange={setHsLevel}>
              <SelectTrigger data-testid="treemap-level-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {HS_LEVELS.map((l) => (
                  <SelectItem key={l.value} value={l.value}>
                    {l.value} — {txt.levelHint[l.value]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* ── Résumé ──────────────────────────────────────────── */}
        {!loading && !error && response && (
          <div className="flex items-center gap-4 text-sm text-slate-600 flex-wrap">
            <span className="font-semibold text-slate-800">
              {flow === 'exports' ? txt.exports : txt.imports} {year} · {formatUSD(total)}
            </span>
            <span>{response.total_products || treemapData.length} {txt.products}</span>
          </div>
        )}

        {/* ── Treemap ─────────────────────────────────────────── */}
        <div style={{ width: '100%', height: 460 }}>
          {loading ? (
            <div className="flex items-center justify-center h-full text-slate-500 gap-2">
              <RefreshCw className="w-5 h-5 animate-spin" /> {txt.loading}
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full text-red-500">{txt.error}</div>
          ) : !treemapData.length ? (
            <div className="flex items-center justify-center h-full text-slate-500">{txt.noData}</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <Treemap
                data={treemapData}
                dataKey="size"
                nameKey="name"
                stroke="#fff"
                isAnimationActive={false}
                content={<TreemapCell />}
              >
                <Tooltip content={TooltipContent} />
              </Treemap>
            </ResponsiveContainer>
          )}
        </div>

        <p className="text-xs text-slate-400">{txt.hint}</p>
      </CardContent>
    </Card>
  );
}
