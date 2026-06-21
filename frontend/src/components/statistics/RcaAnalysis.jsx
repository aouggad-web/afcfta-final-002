/**
 * RcaAnalysis - Avantage Comparatif Révélé (indice de Balassa)
 *
 * Pour un pays africain, calcule et visualise le RCA par produit aux niveaux
 * SH2, SH4 ou SH6, via l'API OEC/BACI en direct (/api/oec/rca).
 * RCA > 1 ⇒ le pays est relativement spécialisé (avantage révélé) dans le produit.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ReferenceLine, CartesianGrid,
} from 'recharts';
import { Award, RefreshCw } from 'lucide-react';
import { getCountryFlag } from '../../utils/countryCodes';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const AVAILABLE_YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018];
const HS_LEVELS = ['HS2', 'HS4', 'HS6'];

const TEXTS = {
  fr: {
    title: 'Avantage comparatif révélé (RCA)',
    subtitle: 'Indice de Balassa par produit — données OEC/BACI en direct',
    country: 'Pays',
    selectCountry: 'Choisir un pays',
    year: 'Année',
    level: 'Niveau SH',
    loading: 'Calcul du RCA…',
    error: 'Impossible de calculer le RCA pour cette sélection.',
    noData: 'Aucune donnée disponible.',
    summary: (n, total) => `${n} produit(s) à avantage révélé (RCA ≥ 1) sur ${total} analysés`,
    chartTitle: 'Top produits par RCA',
    product: 'Produit',
    code: 'Code',
    rca: 'RCA',
    countryShare: 'Part nationale',
    worldShare: 'Part mondiale',
    advantage: 'Avantage',
    yes: 'Oui',
    no: 'Non',
    methodology: 'RCA = (part du produit dans les exports du pays) ÷ (part du produit dans les exports mondiaux). Un RCA > 1 indique une spécialisation relative (avantage comparatif révélé).',
    levelHint: { HS2: 'Chapitres', HS4: 'Positions', HS6: 'Sous-positions' },
  },
  en: {
    title: 'Revealed Comparative Advantage (RCA)',
    subtitle: 'Balassa index by product — live OEC/BACI data',
    country: 'Country',
    selectCountry: 'Choose a country',
    year: 'Year',
    level: 'HS level',
    loading: 'Computing RCA…',
    error: 'Unable to compute RCA for this selection.',
    noData: 'No data available.',
    summary: (n, total) => `${n} product(s) with revealed advantage (RCA ≥ 1) out of ${total} analysed`,
    chartTitle: 'Top products by RCA',
    product: 'Product',
    code: 'Code',
    rca: 'RCA',
    countryShare: 'National share',
    worldShare: 'World share',
    advantage: 'Advantage',
    yes: 'Yes',
    no: 'No',
    methodology: 'RCA = (product share in the country exports) ÷ (product share in world exports). RCA > 1 indicates relative specialisation (revealed comparative advantage).',
    levelHint: { HS2: 'Chapters', HS4: 'Positions', HS6: 'Sub-positions' },
  },
};

const ADV_COLOR = '#1A7A4A';
const NOADV_COLOR = '#B0855A';

const fmtPct = (v) => (v != null ? `${v.toFixed(2)}%` : '—');

export default function RcaAnalysis({ language = 'fr' }) {
  const txt = TEXTS[language] || TEXTS.fr;

  const [countries, setCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState('NGA');
  const [year, setYear] = useState(2022);
  const [hsLevel, setHsLevel] = useState('HS4');

  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get(`${API}/oec/countries?lang=${language}`);
        if (!cancelled && res.data?.success) setCountries(res.data.countries || []);
      } catch (err) {
        console.error('RcaAnalysis: error loading countries', err);
      }
    })();
    return () => { cancelled = true; };
  }, [language]);

  const fetchRca = useCallback(async () => {
    if (!selectedCountry) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API}/oec/rca/${selectedCountry}`, {
        params: { year, hs_level: hsLevel, limit: 25 },
      });
      setResponse(res.data);
    } catch (err) {
      console.error('RcaAnalysis: error computing RCA', err);
      setError(err.response?.data?.detail || err.message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }, [selectedCountry, year, hsLevel]);

  useEffect(() => { fetchRca(); }, [fetchRca]);

  const rows = response?.data || [];

  // Données du graphique: top 12 par RCA (valeur visuelle plafonnée pour lisibilité)
  const chartData = useMemo(() => rows.slice(0, 12).map((d) => ({
    name: d.product?.length > 22 ? `${d.product.slice(0, 20)}…` : d.product,
    fullName: d.product,
    code: d.hs_code,
    rca: d.rca,
    rcaCapped: Math.min(d.rca, 20),
    hasAdvantage: d.has_advantage,
  })), [rows]);

  const RcaTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    const d = payload[0]?.payload;
    if (!d) return null;
    return (
      <div style={{ background: 'rgba(16,22,32,0.97)', border: '1px solid rgba(212,137,26,0.3)', borderRadius: 10, padding: '10px 14px', fontSize: '0.8rem', maxWidth: 260 }}>
        <p style={{ color: '#EAE0D0', fontWeight: 700, marginBottom: 4 }}>{d.code} · {d.fullName}</p>
        <p style={{ color: d.hasAdvantage ? '#34d399' : '#d4a373', margin: 0 }}>RCA = <strong>{d.rca.toFixed(2)}</strong></p>
      </div>
    );
  };

  return (
    <Card className="border-none shadow-xl overflow-hidden" data-testid="rca-analysis">
      <CardHeader className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white pb-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl flex items-center justify-center shadow-lg">
              <Award className="w-7 h-7 text-white" />
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.country}</label>
            <Select value={selectedCountry} onValueChange={setSelectedCountry}>
              <SelectTrigger data-testid="rca-country-select">
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
              <SelectTrigger data-testid="rca-year-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {AVAILABLE_YEARS.map((y) => (
                  <SelectItem key={y} value={String(y)}>{y}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.level}</label>
            <Select value={hsLevel} onValueChange={setHsLevel}>
              <SelectTrigger data-testid="rca-level-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {HS_LEVELS.map((l) => (
                  <SelectItem key={l} value={l}>{l} — {txt.levelHint[l]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* ── Résumé ──────────────────────────────────────────── */}
        {!loading && !error && response && (
          <div className="text-sm font-semibold text-slate-800">
            {txt.summary(response.products_with_advantage, response.total_products)}
          </div>
        )}

        {/* ── Graphique ───────────────────────────────────────── */}
        <div style={{ width: '100%', height: 420 }}>
          {loading ? (
            <div className="flex items-center justify-center h-full text-slate-500 gap-2">
              <RefreshCw className="w-5 h-5 animate-spin" /> {txt.loading}
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full text-red-500">{txt.error}</div>
          ) : !chartData.length ? (
            <div className="flex items-center justify-center h-full text-slate-500">{txt.noData}</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 30, left: 8, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(0,0,0,0.06)" />
                <XAxis type="number" tick={{ fontSize: 11 }} domain={[0, 20]} tickFormatter={(v) => (v >= 20 ? '20+' : v)} />
                <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 11 }} />
                <Tooltip content={<RcaTooltip />} />
                <ReferenceLine x={1} stroke="#C8531A" strokeDasharray="4 4" label={{ value: 'RCA=1', position: 'top', fontSize: 10, fill: '#C8531A' }} />
                <Bar dataKey="rcaCapped" radius={[0, 5, 5, 0]} barSize={16}>
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.hasAdvantage ? ADV_COLOR : NOADV_COLOR} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* ── Tableau détaillé ────────────────────────────────── */}
        {!loading && !error && rows.length > 0 && (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{txt.code}</TableHead>
                  <TableHead>{txt.product}</TableHead>
                  <TableHead className="text-right">{txt.rca}</TableHead>
                  <TableHead className="text-right">{txt.countryShare}</TableHead>
                  <TableHead className="text-right">{txt.worldShare}</TableHead>
                  <TableHead className="text-center">{txt.advantage}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((d, i) => (
                  <TableRow key={`${d.hs_code}-${i}`}>
                    <TableCell className="font-mono text-xs">{d.hs_code}</TableCell>
                    <TableCell className="max-w-xs truncate">{d.product}</TableCell>
                    <TableCell className="text-right font-semibold" style={{ color: d.has_advantage ? ADV_COLOR : '#92400e' }}>
                      {d.rca.toFixed(2)}
                    </TableCell>
                    <TableCell className="text-right">{fmtPct(d.country_share)}</TableCell>
                    <TableCell className="text-right">{fmtPct(d.world_share)}</TableCell>
                    <TableCell className="text-center">
                      {d.has_advantage
                        ? <span className="text-emerald-600 font-medium">{txt.yes}</span>
                        : <span className="text-slate-400">{txt.no}</span>}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        <p className="text-xs text-slate-400">{txt.methodology}</p>
      </CardContent>
    </Card>
  );
}
