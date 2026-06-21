/**
 * TradeComplementarity - Indice de complémentarité commerciale (TCI)
 *
 * Mesure dans quelle mesure le profil d'exportation d'un pays correspond au
 * profil d'importation d'un autre, aux niveaux SH2/SH4/SH6, via l'API OEC/BACI.
 * TCI élevé ⇒ fort potentiel d'échange (utile pour le commerce intra-ZLECAf).
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { Link2, RefreshCw, ArrowRight } from 'lucide-react';
import { getCountryFlag } from '../../utils/countryCodes';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const AVAILABLE_YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018];
const HS_LEVELS = ['HS2', 'HS4', 'HS6'];

const TEXTS = {
  fr: {
    title: 'Complémentarité commerciale (TCI)',
    subtitle: 'Potentiel d’échange entre deux pays — données OEC/BACI en direct',
    exporter: 'Exportateur',
    importer: 'Importateur',
    year: 'Année',
    level: 'Niveau SH',
    loading: 'Calcul de la complémentarité…',
    error: 'Impossible de calculer la complémentarité pour cette sélection.',
    noData: 'Aucune donnée disponible.',
    score: 'Indice TCI',
    interpretation: (v) => v >= 50 ? 'Forte complémentarité' : v >= 30 ? 'Complémentarité modérée' : 'Faible complémentarité',
    opportunities: 'Principales opportunités (offre ↔ demande)',
    product: 'Produit',
    code: 'Code',
    expShare: 'Part export',
    impShare: 'Part import',
    match: 'Recouvrement',
    matchingProducts: (n) => `${n} produits en recouvrement`,
    methodology: 'TCI = 100·(1 − Σ|part import du partenaire − part export|/2). Un TCI élevé signifie que ce que l’exportateur vend correspond à ce que l’importateur achète.',
    levelHint: { HS2: 'Chapitres', HS4: 'Positions', HS6: 'Sous-positions' },
    sameCountry: 'Choisissez deux pays différents.',
  },
  en: {
    title: 'Trade complementarity (TCI)',
    subtitle: 'Trade potential between two countries — live OEC/BACI data',
    exporter: 'Exporter',
    importer: 'Importer',
    year: 'Year',
    level: 'HS level',
    loading: 'Computing complementarity…',
    error: 'Unable to compute complementarity for this selection.',
    noData: 'No data available.',
    score: 'TCI index',
    interpretation: (v) => v >= 50 ? 'Strong complementarity' : v >= 30 ? 'Moderate complementarity' : 'Weak complementarity',
    opportunities: 'Top opportunities (supply ↔ demand)',
    product: 'Product',
    code: 'Code',
    expShare: 'Export share',
    impShare: 'Import share',
    match: 'Overlap',
    matchingProducts: (n) => `${n} overlapping products`,
    methodology: 'TCI = 100·(1 − Σ|partner import share − export share|/2). A high TCI means what the exporter sells matches what the importer buys.',
    levelHint: { HS2: 'Chapters', HS4: 'Positions', HS6: 'Sub-positions' },
    sameCountry: 'Choose two different countries.',
  },
};

const scoreColor = (v) => (v >= 50 ? '#1A7A4A' : v >= 30 ? '#D4891A' : '#B0855A');

export default function TradeComplementarity({ language = 'fr' }) {
  const txt = TEXTS[language] || TEXTS.fr;

  const [countries, setCountries] = useState([]);
  const [exporter, setExporter] = useState('NGA');
  const [importer, setImporter] = useState('ZAF');
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
        console.error('TradeComplementarity: error loading countries', err);
      }
    })();
    return () => { cancelled = true; };
  }, [language]);

  const fetchTci = useCallback(async () => {
    if (!exporter || !importer || exporter === importer) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API}/oec/complementarity/${exporter}/${importer}`, {
        params: { year, hs_level: hsLevel, limit: 20 },
      });
      setResponse(res.data);
    } catch (err) {
      console.error('TradeComplementarity: error computing TCI', err);
      setError(err.response?.data?.detail || err.message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }, [exporter, importer, year, hsLevel]);

  useEffect(() => { fetchTci(); }, [fetchTci]);

  const rows = response?.top_opportunities || [];
  const tci = response?.tci;

  return (
    <Card className="border-none shadow-xl overflow-hidden" data-testid="trade-complementarity">
      <CardHeader className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white pb-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
              <Link2 className="w-7 h-7 text-white" />
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
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.exporter}</label>
            <Select value={exporter} onValueChange={setExporter}>
              <SelectTrigger data-testid="tci-exporter-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {countries.map((c) => (
                  <SelectItem key={c.iso3} value={c.iso3}>
                    <span className="flex items-center gap-2"><span>{getCountryFlag(c.iso3)}</span><span>{c.name}</span></span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.importer}</label>
            <Select value={importer} onValueChange={setImporter}>
              <SelectTrigger data-testid="tci-importer-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {countries.map((c) => (
                  <SelectItem key={c.iso3} value={c.iso3}>
                    <span className="flex items-center gap-2"><span>{getCountryFlag(c.iso3)}</span><span>{c.name}</span></span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.year}</label>
            <Select value={String(year)} onValueChange={(v) => setYear(Number(v))}>
              <SelectTrigger data-testid="tci-year-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {AVAILABLE_YEARS.map((y) => (<SelectItem key={y} value={String(y)}>{y}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.level}</label>
            <Select value={hsLevel} onValueChange={setHsLevel}>
              <SelectTrigger data-testid="tci-level-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {HS_LEVELS.map((l) => (<SelectItem key={l} value={l}>{l} — {txt.levelHint[l]}</SelectItem>))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {exporter === importer ? (
          <div className="flex items-center justify-center py-10 text-amber-600">{txt.sameCountry}</div>
        ) : loading ? (
          <div className="flex items-center justify-center py-10 text-slate-500 gap-2">
            <RefreshCw className="w-5 h-5 animate-spin" /> {txt.loading}
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-10 text-red-500">{txt.error}</div>
        ) : !response ? (
          <div className="flex items-center justify-center py-10 text-slate-500">{txt.noData}</div>
        ) : (
          <>
            {/* ── Score TCI ─────────────────────────────────────── */}
            <div className="flex flex-col items-center justify-center py-4 rounded-xl bg-slate-50">
              <div className="flex items-center gap-3 text-sm text-slate-600 mb-2">
                <span className="flex items-center gap-1 font-medium">
                  {getCountryFlag(exporter)} {response.exporter?.name_fr || response.exporter?.name_en || exporter}
                </span>
                <ArrowRight className="w-4 h-4 text-slate-400" />
                <span className="flex items-center gap-1 font-medium">
                  {getCountryFlag(importer)} {response.importer?.name_fr || response.importer?.name_en || importer}
                </span>
              </div>
              <div className="text-5xl font-bold" style={{ color: scoreColor(tci) }}>{tci}</div>
              <div className="text-xs text-slate-500 mt-1">{txt.score} · {txt.interpretation(tci)}</div>
              <div className="text-xs text-slate-400 mt-1">{txt.matchingProducts(response.matching_products)}</div>
            </div>

            {/* ── Opportunités ──────────────────────────────────── */}
            {rows.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-2">{txt.opportunities}</h4>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{txt.code}</TableHead>
                        <TableHead>{txt.product}</TableHead>
                        <TableHead className="text-right">{txt.expShare}</TableHead>
                        <TableHead className="text-right">{txt.impShare}</TableHead>
                        <TableHead className="text-right">{txt.match}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rows.map((o, i) => (
                        <TableRow key={`${o.hs_code}-${i}`}>
                          <TableCell className="font-mono text-xs">{o.hs_code}</TableCell>
                          <TableCell className="max-w-xs truncate">{o.product}</TableCell>
                          <TableCell className="text-right">{o.exporter_export_share}%</TableCell>
                          <TableCell className="text-right">{o.importer_import_share}%</TableCell>
                          <TableCell className="text-right font-semibold text-cyan-700">{o.match_score}%</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </>
        )}

        <p className="text-xs text-slate-400">{txt.methodology}</p>
      </CardContent>
    </Card>
  );
}
