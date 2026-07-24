import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Ship, Anchor, Waves, Loader2, Leaf, AlertTriangle, Package, TrendingUp } from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const fmtUsd = (v) => (v == null ? '—' : '$' + Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 }));
const fmtNum = (v, u = '') => (v == null ? '—' : Number(v).toLocaleString('fr-FR') + (u ? ' ' + u : ''));
const fmtDays = (min, max) => (min == null && max == null ? '—' : min === max || max == null ? `${min} j` : `${min}–${max} j`);

export default function VraquierLogisticsTab({ language = 'fr' }) {
  const fr = language !== 'en';
  const [ports, setPorts] = useState([]);
  const [classes, setClasses] = useState([]);
  const [market, setMarket] = useState(null);
  const [origin, setOrigin] = useState('ZACPT');
  const [destination, setDestination] = useState('DZORN');
  const [tonnes, setTonnes] = useState('25000');
  const [hsCode, setHsCode] = useState('1001');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API}/logistics/bulk/ports`).then((r) => setPorts(r.data.ports || [])).catch(() => {});
    axios
      .get(`${API}/logistics/bulk/vessel-classes`)
      .then((r) => {
        setClasses(r.data.vessel_classes || []);
        setMarket(r.data.market || null);
      })
      .catch(() => {});
  }, []);

  const portOptions = useMemo(
    () => ports.map((p) => ({ value: p.locode, label: `${p.name} (${p.locode})${p.max_draft_m ? ` · ${p.max_draft_m} m` : ''}` })),
    [ports]
  );

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const params = new URLSearchParams({ origin, destination, tonnes: String(tonnes) });
      if (hsCode.trim()) params.set('hs_code', hsCode.trim());
      const r = await axios.get(`${API}/logistics/bulk/cost?${params.toString()}`);
      setResult(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || (fr ? 'Calcul indisponible.' : 'Calculation unavailable.'));
    } finally {
      setLoading(false);
    }
  };

  const cost = result?.available ? result.cost : null;
  const override = cost?.freight_market_override;
  const isLive = override?.is_live;

  return (
    <div className="space-y-5" data-testid="vraquier-logistics-tab">
      {/* Header */}
      <Card className="border-0 shadow-sm" style={{ background: 'rgba(27,35,44,0.7)' }}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/15 flex items-center justify-center">
                <Ship className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <CardTitle className="text-white text-base">
                  {fr ? 'Fret vraquier (bulk carrier)' : 'Bulk carrier freight'}
                </CardTitle>
                <CardDescription className="text-gray-400 text-xs">
                  {fr
                    ? 'Cargaison homogène en vrac sec — coût USD/t par classe de navire, contraintes portuaires et voyages multiples.'
                    : 'Homogeneous dry-bulk cargo — USD/t cost per vessel class, port constraints and multiple voyages.'}
                </CardDescription>
              </div>
            </div>
            {market && (
              <Badge
                className={
                  market.is_live
                    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                    : 'bg-gray-500/15 text-gray-300 border-gray-500/30'
                }
                title={market.source || ''}
              >
                <TrendingUp className="w-3 h-3 mr-1" />
                {market.is_live
                  ? `${fr ? 'Marché' : 'Live'} · ${market.as_of}`
                  : fr
                  ? 'Calibré 2024'
                  : 'Calibrated 2024'}
              </Badge>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Inputs */}
      <Card className="border-0 shadow-sm" style={{ background: 'rgba(27,35,44,0.7)' }}>
        <CardContent className="py-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
            <div>
              <Label className="text-gray-300 text-xs">{fr ? 'Port de départ' : 'Origin port'}</Label>
              <Select value={origin} onValueChange={setOrigin}>
                <SelectTrigger data-testid="vraquier-origin"><SelectValue /></SelectTrigger>
                <SelectContent className="max-h-72">
                  {portOptions.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gray-300 text-xs">{fr ? "Port d'arrivée" : 'Destination port'}</Label>
              <Select value={destination} onValueChange={setDestination}>
                <SelectTrigger data-testid="vraquier-destination"><SelectValue /></SelectTrigger>
                <SelectContent className="max-h-72">
                  {portOptions.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gray-300 text-xs">{fr ? 'Tonnage (t)' : 'Tonnage (t)'}</Label>
              <Input
                type="number"
                value={tonnes}
                onChange={(e) => setTonnes(e.target.value)}
                data-testid="vraquier-tonnes"
                min="1"
              />
            </div>
            <div>
              <Label className="text-gray-300 text-xs">{fr ? 'Code SH (optionnel)' : 'HS code (optional)'}</Label>
              <Input
                value={hsCode}
                onChange={(e) => setHsCode(e.target.value)}
                data-testid="vraquier-hs"
                placeholder="1001"
              />
            </div>
            <Button onClick={run} disabled={loading} data-testid="vraquier-run" className="w-full">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Anchor className="w-4 h-4 mr-1" />}
              {fr ? 'Calculer' : 'Compute'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-0 shadow-sm border-l-4 border-l-red-500" style={{ background: 'rgba(60,20,20,0.5)' }}>
          <CardContent className="py-3 text-red-300 text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> {error}
          </CardContent>
        </Card>
      )}

      {/* Not available (below threshold / liquid) */}
      {result && !result.available && (
        <Card className="border-0 shadow-sm border-l-4 border-l-amber-500" style={{ background: 'rgba(50,40,15,0.5)' }}>
          <CardContent className="py-4 text-amber-200 text-sm flex items-start gap-2">
            <Package className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-semibold mb-1">
                {result.reason === 'liquid_bulk'
                  ? fr ? 'Vrac liquide — marché tanker' : 'Liquid bulk — tanker market'
                  : fr ? 'Sous le seuil vraquier' : 'Below bulk threshold'}
              </div>
              {result.note}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Result */}
      {cost && (
        <Card className="border-0 shadow-sm" style={{ background: 'rgba(27,35,44,0.7)' }} data-testid="vraquier-result">
          <CardContent className="py-5">
            <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
              <div className="flex items-center gap-2">
                <Badge className="bg-blue-500/15 text-blue-300 border-blue-500/30 capitalize">
                  🚢 {cost.vessel_class_label || cost.vessel_class}
                </Badge>
                {cost.is_modeled && (
                  <Badge className="bg-amber-500/15 text-amber-300 border-amber-500/40">
                    {fr ? 'Modélisé' : 'Modeled'}
                  </Badge>
                )}
                <Badge
                  className={isLive ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' : 'bg-gray-500/15 text-gray-300 border-gray-500/30'}
                  title={override?.source || ''}
                >
                  {isLive ? `${fr ? 'Marché' : 'Live'} · ${override.as_of}` : fr ? 'Calibré 2024' : 'Calibrated 2024'}
                </Badge>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-white">{fmtUsd(cost.total_cost_usd)}</div>
                <div className="text-xs text-gray-400">{fmtNum(cost.total_usd_per_t)} USD/t</div>
              </div>
            </div>

            {/* Cost breakdown */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              {[
                { label: fr ? 'Fret océanique' : 'Ocean freight', v: cost.ocean_freight_usd_per_t, icon: Waves },
                { label: fr ? 'Chargement' : 'Loading', v: cost.port_load_usd_per_t, icon: Anchor },
                { label: fr ? 'Déchargement' : 'Discharge', v: cost.port_discharge_usd_per_t, icon: Anchor },
                { label: 'Total USD/t', v: cost.total_usd_per_t, icon: TrendingUp },
              ].map((b, i) => (
                <div key={i} className="rounded-lg p-3" style={{ background: 'rgba(255,255,255,0.03)' }}>
                  <div className="text-[11px] text-gray-400 flex items-center gap-1">
                    <b.icon className="w-3 h-3" /> {b.label}
                  </div>
                  <div className="text-white font-semibold mt-1">{fmtNum(b.v)}</div>
                </div>
              ))}
            </div>

            {/* Meta row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <div className="text-[11px] text-gray-400">{fr ? 'Voyages' : 'Voyages'}</div>
                <div className="text-white font-medium">{cost.voyages_needed}</div>
              </div>
              <div>
                <div className="text-[11px] text-gray-400">{fr ? 'Délai' : 'Transit'}</div>
                <div className="text-white font-medium">{fmtDays(cost.transit_days_min, cost.transit_days_max)}</div>
              </div>
              <div>
                <div className="text-[11px] text-gray-400 flex items-center gap-1"><Leaf className="w-3 h-3" /> CO₂</div>
                <div className="text-white font-medium">{fmtNum(cost.co2_g_per_tkm)} g/t·km</div>
              </div>
              <div>
                <div className="text-[11px] text-gray-400">{fr ? 'Distance' : 'Distance'}</div>
                <div className="text-white font-medium">{fmtNum(cost.distance_nm)} nm</div>
              </div>
            </div>

            {/* Constraints */}
            {cost.constraints_notes?.length > 0 && (
              <div className="mt-4 space-y-1">
                {cost.constraints_notes.map((n, i) => (
                  <div key={i} className="text-xs text-amber-200/90 flex items-start gap-2">
                    <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" /> {n}
                  </div>
                ))}
              </div>
            )}

            <div className="mt-4 text-[11px] text-gray-500">
              {result.commodity?.label && <span>{result.commodity.label} · </span>}
              {override?.source || cost.disclaimer}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Vessel class reference */}
      {classes.length > 0 && (
        <Card className="border-0 shadow-sm" style={{ background: 'rgba(27,35,44,0.7)' }}>
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm">{fr ? 'Classes de navires vraquiers' : 'Bulk vessel classes'}</CardTitle>
          </CardHeader>
          <CardContent className="py-2 overflow-x-auto">
            <table className="w-full text-xs text-gray-300">
              <thead>
                <tr className="text-gray-500 text-left">
                  <th className="py-1 pr-3">Classe</th>
                  <th className="py-1 pr-3">DWT</th>
                  <th className="py-1 pr-3">{fr ? 'Emport max' : 'Max parcel'}</th>
                  <th className="py-1 pr-3">{fr ? 'Tirant (chargé)' : 'Draft (loaded)'}</th>
                  <th className="py-1 pr-3">CO₂</th>
                </tr>
              </thead>
              <tbody>
                {classes.map((c) => (
                  <tr key={c.id} className="border-t border-white/5">
                    <td className="py-1 pr-3 font-medium text-white">{c.label}</td>
                    <td className="py-1 pr-3">{fmtNum(c.min_dwt)}–{fmtNum(c.max_dwt)}</td>
                    <td className="py-1 pr-3">{fmtNum(c.max_parcel_t)} t</td>
                    <td className="py-1 pr-3">{c.loaded_draft_m} m</td>
                    <td className="py-1 pr-3">{c.co2_g_per_tkm} g/t·km</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
