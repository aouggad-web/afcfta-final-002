/**
 * PreferenceMargin - Profil de marge préférentielle ZLECAf
 *
 * Pour un pays, agrège son fichier tarifaire national en un profil de marge
 * préférentielle (NPF − ZLECAf) : marge moyenne, part des lignes bénéficiant
 * d'une préférence, ventilation par sensibilité, secteurs à plus forte marge.
 * Source: fichiers tarifaires nationaux ({ISO3}_tariffs.json).
 *
 * Mesure le *potentiel* préférentiel offert (données tarifaires réelles), non
 * le taux d'utilisation douanier effectif (qui exige des données d'origine).
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';
import { Percent, RefreshCw } from 'lucide-react';
import { getCountryFlag } from '../../utils/countryCodes';
import { CSVExportButton } from '../common/ExportTools';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const TEXTS = {
  fr: {
    title: 'Marge préférentielle ZLECAf',
    subtitle: 'Potentiel préférentiel par pays (NPF − ZLECAf) — tarifs nationaux',
    country: 'Pays',
    loading: 'Chargement du profil tarifaire…',
    error: 'Aucune donnée tarifaire pour ce pays.',
    avgNpf: 'NPF moyen',
    avgZlecaf: 'ZLECAf moyen',
    avgMargin: 'Marge moyenne',
    benefiting: 'Lignes avec préférence',
    dutyFree: 'Déjà en franchise',
    lines: 'lignes analysées',
    sensitivity: 'Ventilation par sensibilité',
    sensCount: 'Lignes',
    sensShare: 'Part',
    sensMargin: 'Marge moy.',
    topSectors: 'Secteurs à plus forte marge préférentielle',
    sector: 'Secteur',
    count: 'Lignes',
    margin: 'Marge moy. (pts)',
    sensLabels: { normal: 'Normal', sensitive: 'Sensible', excluded: 'Exclu', unknown: 'Inconnu' },
    methodology: 'Marge préférentielle = NPF − ZLECAf par ligne SH6. Mesure le potentiel préférentiel offert (tarifs réels), non le taux d’utilisation douanier effectif (qui requiert des données de demandes d’origine).',
  },
  en: {
    title: 'AfCFTA preference margin',
    subtitle: 'Preference potential by country (MFN − AfCFTA) — national tariffs',
    country: 'Country',
    loading: 'Loading tariff profile…',
    error: 'No tariff data for this country.',
    avgNpf: 'Avg MFN',
    avgZlecaf: 'Avg AfCFTA',
    avgMargin: 'Avg margin',
    benefiting: 'Lines with preference',
    dutyFree: 'Already duty-free',
    lines: 'lines analysed',
    sensitivity: 'Breakdown by sensitivity',
    sensCount: 'Lines',
    sensShare: 'Share',
    sensMargin: 'Avg margin',
    topSectors: 'Sectors with highest preference margin',
    sector: 'Sector',
    count: 'Lines',
    margin: 'Avg margin (pts)',
    sensLabels: { normal: 'Normal', sensitive: 'Sensitive', excluded: 'Excluded', unknown: 'Unknown' },
    methodology: 'Preference margin = MFN − AfCFTA per HS6 line. Measures the preference potential offered (real tariffs), not the actual customs utilisation rate (which requires rules-of-origin claim data).',
  },
};

const Kpi = ({ label, value, suffix, color }) => (
  <div className="rounded-xl bg-slate-50 p-3 text-center">
    <div className="text-2xl font-bold" style={{ color: color || '#1e293b' }}>
      {value != null ? value : '—'}{value != null && suffix ? suffix : ''}
    </div>
    <div className="text-xs text-slate-500 mt-0.5">{label}</div>
  </div>
);

const SENS_COLOR = { normal: '#1A7A4A', sensitive: '#D4891A', excluded: '#C0392B', unknown: '#94a3b8' };

export default function PreferenceMargin({ language = 'fr' }) {
  const txt = TEXTS[language] || TEXTS.fr;

  const [countries, setCountries] = useState([]);
  const [country, setCountry] = useState('AGO');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await axios.get(`${API}/oec/countries?lang=${language}`);
        if (!cancelled && res.data?.success) setCountries(res.data.countries || []);
      } catch (err) {
        console.error('PreferenceMargin: error loading countries', err);
      }
    })();
    return () => { cancelled = true; };
  }, [language]);

  const fetchProfile = useCallback(async () => {
    if (!country) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API}/dismantlement/preference-profile/${country}`);
      setData(res.data);
    } catch (err) {
      console.error('PreferenceMargin: error loading profile', err);
      setError(err.response?.data?.detail || err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [country]);

  useEffect(() => { fetchProfile(); }, [fetchProfile]);

  const sectorChart = (data?.top_sectors_by_margin || []).map((s) => ({
    name: s.sector?.length > 18 ? `${s.sector.slice(0, 16)}…` : s.sector,
    fullName: s.sector,
    margin: s.avg_preference_margin,
    count: s.count,
  }));

  return (
    <Card className="border-none shadow-xl overflow-hidden" data-testid="preference-margin">
      <CardHeader className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white pb-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
              <Percent className="w-7 h-7 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold">{txt.title}</CardTitle>
              <CardDescription className="text-slate-300 mt-0.5">{txt.subtitle}</CardDescription>
            </div>
          </div>
          <Badge className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-3 py-1">
            ZLECAf · tarifs nationaux
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-5 space-y-4">
        {/* ── Sélecteur pays ──────────────────────────────────── */}
        <div className="max-w-xs">
          <label className="text-xs font-medium text-slate-500 mb-1 block">{txt.country}</label>
          <Select value={country} onValueChange={setCountry}>
            <SelectTrigger data-testid="pref-country-select"><SelectValue /></SelectTrigger>
            <SelectContent>
              {countries.map((c) => (
                <SelectItem key={c.iso3} value={c.iso3}>
                  <span className="flex items-center gap-2"><span>{getCountryFlag(c.iso3)}</span><span>{c.name}</span></span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-10 text-slate-500 gap-2">
            <RefreshCw className="w-5 h-5 animate-spin" /> {txt.loading}
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-10 text-red-500">{txt.error}</div>
        ) : data ? (
          <>
            {/* ── KPI ─────────────────────────────────────────── */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <Kpi label={txt.avgNpf} value={data.avg_npf_rate} suffix="%" />
              <Kpi label={txt.avgZlecaf} value={data.avg_zlecaf_rate} suffix="%" />
              <Kpi label={txt.avgMargin} value={data.avg_preference_margin} suffix=" pts" color="#C8531A" />
              <Kpi label={txt.benefiting} value={data.lines_with_preference_pct} suffix="%" color="#1A7A4A" />
              <Kpi label={txt.dutyFree} value={data.lines_already_duty_free_pct} suffix="%" color="#1A6B8A" />
            </div>
            <div className="text-xs text-slate-400">
              {data.total_lines_analyzed?.toLocaleString(language === 'fr' ? 'fr-FR' : 'en-US')} {txt.lines}
            </div>

            {/* ── Ventilation par sensibilité ─────────────────── */}
            {data.sensitivity_breakdown && Object.keys(data.sensitivity_breakdown).length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-slate-700 mb-2">{txt.sensitivity}</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{txt.country}</TableHead>
                      <TableHead className="text-right">{txt.sensCount}</TableHead>
                      <TableHead className="text-right">{txt.sensShare}</TableHead>
                      <TableHead className="text-right">{txt.sensMargin}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(data.sensitivity_breakdown).map(([k, v]) => (
                      <TableRow key={k}>
                        <TableCell>
                          <span className="inline-flex items-center gap-2">
                            <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: SENS_COLOR[k] || SENS_COLOR.unknown }} />
                            {txt.sensLabels[k] || k}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">{v.count?.toLocaleString(language === 'fr' ? 'fr-FR' : 'en-US')}</TableCell>
                        <TableCell className="text-right">{v.share_pct}%</TableCell>
                        <TableCell className="text-right">{v.avg_preference_margin} pts</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* ── Top secteurs ────────────────────────────────── */}
            {sectorChart.length > 0 && (
              <div>
                <div className="flex items-center justify-between gap-3 flex-wrap mb-2">
                  <h4 className="text-sm font-semibold text-slate-700">{txt.topSectors}</h4>
                  <CSVExportButton
                    rows={data.top_sectors_by_margin || []}
                    columns={[
                      { key: 'sector', label: txt.sector },
                      { key: 'count', label: txt.count },
                      { key: 'avg_preference_margin', label: txt.margin },
                    ]}
                    filename={`preference_${country}`}
                    language={language}
                  />
                </div>
                <div style={{ width: '100%', height: 320 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={sectorChart} layout="vertical" margin={{ top: 4, right: 30, left: 8, bottom: 4 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(0,0,0,0.06)" />
                      <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}`} />
                      <YAxis type="category" dataKey="name" width={140} tick={{ fontSize: 11 }} />
                      <Tooltip
                        formatter={(v, n, p) => [`${v} pts`, txt.margin]}
                        labelFormatter={(l, p) => p?.[0]?.payload?.fullName || l}
                      />
                      <Bar dataKey="margin" radius={[0, 5, 5, 0]} barSize={15}>
                        {sectorChart.map((_, i) => (<Cell key={i} fill="#C8531A" />))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </>
        ) : null}

        <p className="text-xs text-slate-400">{txt.methodology}</p>
      </CardContent>
    </Card>
  );
}
