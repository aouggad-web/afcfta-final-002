import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Ship, Plane, Truck, Train, Loader2, Layers, Award, Zap, Leaf, Construction, Sparkles, TrendingUp } from 'lucide-react';
import { PDFExportButton } from '../common/ExportTools';

const API = import.meta.env.VITE_BACKEND_URL;

const COUNTRY_NAMES_FR = {
  AGO:'Angola', BDI:'Burundi', BEN:'Bénin', BFA:'Burkina Faso', BWA:'Botswana',
  CAF:'République centrafricaine', CIV:"Côte d'Ivoire", CMR:'Cameroun',
  COD:'RD Congo', COG:'Congo', DJI:'Djibouti', DZA:'Algérie', EGY:'Égypte',
  ETH:'Éthiopie', GAB:'Gabon', GHA:'Ghana', KEN:'Kenya', LBY:'Libye',
  LSO:'Lesotho', MAR:'Maroc', MDG:'Madagascar', MLI:'Mali', MOZ:'Mozambique',
  MUS:'Maurice', MWI:'Malawi', NAM:'Namibie', NER:'Niger', NGA:'Nigeria',
  RWA:'Rwanda', SEN:'Sénégal', SSD:'Soudan du Sud', SWZ:'Eswatini',
  TCD:'Tchad', TGO:'Togo', TUN:'Tunisie', TZA:'Tanzanie', UGA:'Ouganda',
  ZAF:'Afrique du Sud', ZMB:'Zambie', ZWE:'Zimbabwe',
};

const MODE_META = {
  sea:        { icon: Ship,  color: 'text-blue-400',    bg: 'bg-blue-500/10',    label: 'Maritime' },
  air:        { icon: Plane, color: 'text-cyan-400',    bg: 'bg-cyan-500/10',    label: 'Aérien' },
  land:       { icon: Truck, color: 'text-orange-400',  bg: 'bg-orange-500/10',  label: 'Terrestre' },
  road:       { icon: Truck, color: 'text-orange-400',  bg: 'bg-orange-500/10',  label: 'Route' },
  rail:       { icon: Train, color: 'text-emerald-400', bg: 'bg-emerald-500/10', label: 'Rail' },
  multimodal: { icon: Layers, color: 'text-purple-400', bg: 'bg-purple-500/10',  label: 'Multimodal' },
};

const PHASE_META = {
  operational:         { label: 'Opérationnel',          cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  under_construction:  { label: 'En construction',       cls: 'bg-amber-500/15  text-amber-300  border-amber-500/40'  },
  planned:             { label: 'Planifié',              cls: 'bg-sky-500/15    text-sky-300    border-sky-500/40'    },
  study:               { label: "Étude de faisabilité", cls: 'bg-purple-500/15 text-purple-300 border-purple-500/40' },
};

function fmtUsd(v) {
  if (v == null) return '—';
  return '$' + Number(v).toLocaleString('en-US');
}

function fmtKg(v) {
  if (v == null) return '—';
  if (v >= 1000) return (v / 1000).toFixed(1) + ' t CO₂';
  return v.toFixed(1) + ' kg CO₂';
}

function fmtDays(min, max) {
  if (min == null && max == null) return '—';
  if (min === max || max == null) return `${min} j`;
  return `${min}–${max} j`;
}

function OptionCard({ opt }) {
  // Pick icon by corridor mode when available (so rail uses Train, not Truck)
  const iconKey = opt.corridor_mode || opt.mode;
  const meta = MODE_META[iconKey] || MODE_META[opt.mode] || MODE_META.sea;
  const Icon = meta.icon;
  const phaseMeta = PHASE_META[opt.phase] || PHASE_META.operational;

  const badges = [];
  if (opt.is_cheapest) badges.push({ icon: Award, label: 'Le moins cher', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' });
  if (opt.is_fastest)  badges.push({ icon: Zap,    label: 'Le plus rapide', cls: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30' });
  if (opt.is_greenest) badges.push({ icon: Leaf,   label: 'Le plus vert',   cls: 'bg-lime-500/15 text-lime-300 border-lime-500/30' });
  if (opt.is_future_cheapest)  badges.push({ icon: Sparkles, label: 'Futur · le moins cher', cls: 'bg-sky-500/15 text-sky-300 border-sky-500/40' });
  if (opt.is_future_greenest)  badges.push({ icon: Sparkles, label: 'Futur · le plus vert', cls: 'bg-sky-500/15 text-sky-300 border-sky-500/40' });

  const cardBorder = opt.is_future
    ? 'border border-dashed border-sky-500/40 bg-[#1B232C]/70'
    : 'border border-white/10 bg-[#1B232C]';

  return (
    <Card className={cardBorder} data-testid={`multimodal-option-${opt.mode}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className={`w-10 h-10 rounded-lg ${meta.bg} flex items-center justify-center flex-shrink-0`}>
              <Icon className={`w-5 h-5 ${meta.color}`} />
            </div>
            <div>
              <CardTitle className="text-base text-white flex items-center gap-2 flex-wrap">
                {opt.label}
                {opt.is_future && (
                  <Badge variant="outline" className={`text-[10px] ${phaseMeta.cls}`}>
                    <Construction className="w-3 h-3 mr-1" />{phaseMeta.label}
                  </Badge>
                )}
              </CardTitle>
              {opt.via_port && (
                <CardDescription className="text-xs mt-1 text-gray-400">
                  Transit via <span className="text-white">{opt.via_port}</span>
                  {opt.corridor_name && <> · Corridor <span className="text-white">{opt.corridor_name}</span></>}
                </CardDescription>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-1 justify-end">
            {badges.map((b, i) => {
              const BIcon = b.icon;
              return (
                <Badge key={i} variant="outline" className={`text-[11px] ${b.cls}`}>
                  <BIcon className="w-3 h-3 mr-1" />{b.label}
                </Badge>
              );
            })}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-lg bg-white/5 px-3 py-2">
            <div className="text-[11px] uppercase tracking-wide text-gray-400 mb-1">Coût total</div>
            <div className="font-display text-2xl text-white">{fmtUsd(opt.total_cost_usd)}</div>
          </div>
          <div className="rounded-lg bg-white/5 px-3 py-2">
            <div className="text-[11px] uppercase tracking-wide text-gray-400 mb-1">Délai</div>
            <div className="font-display text-2xl text-white">{fmtDays(opt.transit_days_min, opt.transit_days_max)}</div>
          </div>
          <div className="rounded-lg bg-white/5 px-3 py-2">
            <div className="text-[11px] uppercase tracking-wide text-gray-400 mb-1">Empreinte CO₂</div>
            <div className="font-display text-2xl text-white">{fmtKg(opt.co2_kg)}</div>
          </div>
        </div>

        {/* Segments */}
        {opt.segments && opt.segments.length > 0 && (
          <div className="border-t border-white/10 pt-3">
            <div className="text-[11px] uppercase tracking-wide text-gray-400 mb-2">
              {opt.segments.length === 1 ? 'Trajet' : `${opt.segments.length} segments`}
            </div>
            <div className="space-y-2">
              {opt.segments.map((seg, idx) => {
                const segMeta = MODE_META[seg.mode] || MODE_META.sea;
                const SegIcon = segMeta.icon;
                return (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <div className={`w-7 h-7 rounded ${segMeta.bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                      <SegIcon className={`w-3.5 h-3.5 ${segMeta.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-gray-200">
                        <span className="font-medium">{seg.from}</span>
                        {' → '}
                        <span className="font-medium">{seg.to}</span>
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {seg.distance_km != null && <span>{seg.distance_km.toLocaleString('en-US')} km</span>}
                        {seg.transit_days_min != null && <span> · {fmtDays(seg.transit_days_min, seg.transit_days_max)}</span>}
                        {seg.cost_usd != null && <span> · {fmtUsd(seg.cost_usd)}</span>}
                        {seg.corridor_name && <span> · {seg.corridor_name}</span>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {opt.notes && (
          <div className="text-xs text-gray-400 italic border-t border-white/5 pt-2">
            {opt.notes}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function MultimodalComparator({ language = 'fr' }) {
  const [origin, setOrigin] = useState('MAR');
  const [destination, setDestination] = useState('MLI');
  const [weightKg, setWeightKg] = useState(20000);
  const [volumeM3, setVolumeM3] = useState(0);
  const [containerType, setContainerType] = useState('teu');
  const [airCommodity, setAirCommodity] = useState('general');
  const [landCargoType, setLandCargoType] = useState('container');
  const [teuPerYear, setTeuPerYear] = useState(100);

  const [supportedCountries, setSupportedCountries] = useState({ all_supported: [], landlocked_countries: [] });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Ref for PDF export — wraps the entire results area
  const reportRef = useRef(null);

  useEffect(() => {
    axios.get(`${API}/api/logistics/multimodal/countries`)
      .then(res => setSupportedCountries(res.data))
      .catch(err => console.error('Failed to load supported countries', err));
  }, []);

  const isLandlockedDest = useMemo(
    () => supportedCountries.landlocked_countries?.includes(destination),
    [destination, supportedCountries.landlocked_countries],
  );

  const handleCompare = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await axios.get(`${API}/api/logistics/multimodal/compare`, {
        params: {
          origin, destination,
          weight_kg: weightKg,
          volume_m3: volumeM3,
          container_type: containerType,
          air_commodity: airCommodity,
          land_cargo_type: landCargoType,
        },
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const countryOptions = supportedCountries.all_supported || [];

  return (
    <div className="space-y-5" data-testid="multimodal-comparator">
      {/* Header */}
      <Card className="border border-purple-500/30 bg-gradient-to-r from-[#1B232C] to-[#0F1419]">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-purple-500/15 flex items-center justify-center">
              <Layers className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-xl text-white">Comparateur Multimodal</CardTitle>
              <CardDescription className="text-gray-400 mt-1">
                Compare maritime · aérien · terrestre · combinaisons port+corridor pour les pays enclavés
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Form */}
      <Card className="border border-white/10 bg-[#1B232C]">
        <CardContent className="pt-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-gray-300 text-sm mb-1.5 block">Pays d&apos;origine</Label>
              <Select value={origin} onValueChange={setOrigin}>
                <SelectTrigger data-testid="multimodal-origin-select"><SelectValue /></SelectTrigger>
                <SelectContent className="max-h-[280px]">
                  {countryOptions.map(iso => (
                    <SelectItem key={iso} value={iso}>
                      {COUNTRY_NAMES_FR[iso] || iso} ({iso})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gray-300 text-sm mb-1.5 block">
                Pays de destination
                {isLandlockedDest && (
                  <Badge className="ml-2 text-[10px] bg-amber-500/20 text-amber-300 border-amber-500/40">
                    Enclavé
                  </Badge>
                )}
              </Label>
              <Select value={destination} onValueChange={setDestination}>
                <SelectTrigger data-testid="multimodal-dest-select"><SelectValue /></SelectTrigger>
                <SelectContent className="max-h-[280px]">
                  {countryOptions.map(iso => {
                    const landlocked = supportedCountries.landlocked_countries?.includes(iso);
                    return (
                      <SelectItem key={iso} value={iso}>
                        {COUNTRY_NAMES_FR[iso] || iso} ({iso}){landlocked ? ' • enclavé' : ''}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Label className="text-gray-300 text-sm mb-1.5 block">Poids (kg)</Label>
              <Input
                type="number" min={1}
                value={weightKg}
                onChange={e => setWeightKg(Number(e.target.value) || 0)}
                data-testid="multimodal-weight-input"
              />
            </div>
            <div>
              <Label className="text-gray-300 text-sm mb-1.5 block">Volume (m³, optionnel)</Label>
              <Input
                type="number" min={0} step="0.1"
                value={volumeM3}
                onChange={e => setVolumeM3(Number(e.target.value) || 0)}
              />
            </div>
            <div>
              <Label className="text-gray-300 text-sm mb-1.5 block">Conteneur (maritime)</Label>
              <Select value={containerType} onValueChange={setContainerType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="teu">20&apos; Standard (TEU)</SelectItem>
                  <SelectItem value="feu">40&apos; Standard (FEU)</SelectItem>
                  <SelectItem value="feu_hc">40&apos; High-Cube</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-gray-300 text-sm mb-1.5 block">Nature marchandise (air)</Label>
              <Select value={airCommodity} onValueChange={setAirCommodity}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">Marchandise générale</SelectItem>
                  <SelectItem value="perishable">Périssable</SelectItem>
                  <SelectItem value="pharma">Pharmaceutique</SelectItem>
                  <SelectItem value="dangerous">Dangereuse (DGR)</SelectItem>
                  <SelectItem value="valuable">Valeur / sécurisé</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="pt-2">
            <Button
              onClick={handleCompare}
              disabled={loading || origin === destination}
              className="bg-purple-500 hover:bg-purple-600 text-white"
              data-testid="multimodal-compare-btn"
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Calcul en cours…</>
              ) : (
                <><Layers className="w-4 h-4 mr-2" />Comparer les modes</>
              )}
            </Button>
            {origin === destination && (
              <span className="ml-3 text-xs text-amber-400">Origine et destination doivent être différentes.</span>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border border-red-500/40 bg-red-500/10">
          <CardContent className="pt-4 text-sm text-red-300">⚠ {error}</CardContent>
        </Card>
      )}

      {result && result.options_count === 0 && (
        <Card className="border border-amber-500/40 bg-amber-500/10">
          <CardContent className="pt-4 text-sm text-amber-300">
            Aucune option de fret disponible dans la base de données pour ce trajet.
          </CardContent>
        </Card>
      )}

      {result && result.options_count > 0 && (
        <div ref={reportRef} className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="text-lg font-display text-white">
              {result.operational_count} option{result.operational_count > 1 ? 's' : ''} opérationnelle{result.operational_count > 1 ? 's' : ''}
              {result.future_count > 0 && (
                <span className="text-sky-300 text-base ml-2">
                  · {result.future_count} option{result.future_count > 1 ? 's' : ''} future{result.future_count > 1 ? 's' : ''} (planifiées / en construction)
                </span>
              )}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              {result.is_destination_landlocked && (
                <Badge className="bg-amber-500/15 text-amber-300 border-amber-500/40">
                  Destination enclavée — combinaisons port + corridor proposées
                </Badge>
              )}
              <PDFExportButton
                targetRef={reportRef}
                filename={`comparaison_multimodale_${origin}_${destination}`}
                title={`Comparaison multimodale ${origin} → ${destination}`}
                subtitle={`${weightKg/1000} t · ${containerType.toUpperCase()} · ZLECAf Analytics`}
                language={language}
                data-testid="multimodal-pdf-btn"
              />
            </div>
          </div>

          {/* ROI Infrastructure card */}
          {result.roi_infrastructure && (
            <Card className="border border-sky-500/40 bg-gradient-to-br from-sky-500/10 to-purple-500/10">
              <CardHeader className="pb-3">
                <div className="flex items-start gap-3">
                  <div className="w-11 h-11 rounded-xl bg-sky-500/20 flex items-center justify-center flex-shrink-0">
                    <TrendingUp className="w-5 h-5 text-sky-300" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base text-white">
                      ROI Infrastructure — projection si les routes planifiées étaient opérationnelles
                    </CardTitle>
                    <CardDescription className="text-xs mt-1 text-gray-300">
                      Compare la meilleure option opérationnelle d&apos;aujourd&apos;hui avec la meilleure route future.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="rounded-lg bg-white/5 p-3 border border-white/10">
                    <div className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">Aujourd&apos;hui</div>
                    <div className="text-sm text-gray-200 mb-2">
                      {result.roi_infrastructure.reference_operational.label}
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div><span className="text-gray-400 text-[10px]">Coût</span><div className="font-display text-base text-white">${result.roi_infrastructure.reference_operational.cost_usd?.toLocaleString('en-US')}</div></div>
                      <div><span className="text-gray-400 text-[10px]">Délai</span><div className="font-display text-base text-white">{result.roi_infrastructure.reference_operational.transit_days_avg} j</div></div>
                      <div><span className="text-gray-400 text-[10px]">CO₂</span><div className="font-display text-base text-white">{(result.roi_infrastructure.reference_operational.co2_kg / 1000).toFixed(1)} t</div></div>
                    </div>
                  </div>
                  <div className="rounded-lg bg-sky-500/10 p-3 border border-dashed border-sky-500/40">
                    <div className="text-[10px] uppercase tracking-wide text-sky-300 mb-1">
                      🚧 Futur · {result.roi_infrastructure.best_future_cost.status}
                    </div>
                    <div className="text-sm text-gray-200 mb-2">
                      {result.roi_infrastructure.best_future_cost.label}
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div><span className="text-gray-400 text-[10px]">Coût</span><div className="font-display text-base text-sky-200">${result.roi_infrastructure.best_future_cost.cost_usd?.toLocaleString('en-US')}</div></div>
                      <div><span className="text-gray-400 text-[10px]">Délai</span><div className="font-display text-base text-sky-200">{result.roi_infrastructure.best_future_cost.transit_days_avg} j</div></div>
                      <div><span className="text-gray-400 text-[10px]">CO₂</span><div className="font-display text-base text-sky-200">{(result.roi_infrastructure.best_future_cost.co2_kg / 1000).toFixed(1)} t</div></div>
                    </div>
                  </div>
                </div>

                {(() => {
                  const ps = result.roi_infrastructure.per_shipment;
                  const costPositive = (ps.cost_savings_usd ?? 0) >= 0;
                  const co2Positive = (ps.co2_savings_kg ?? 0) >= 0;
                  const annualCost = (ps.cost_savings_usd || 0) * teuPerYear;
                  const annualCo2 = ((ps.co2_savings_kg || 0) * teuPerYear) / 1000;
                  return (
                    <>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-white/10">
                        <div className="text-center">
                          <div className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">
                            {costPositive ? 'Économie par expédition' : 'Surcoût par expédition'}
                          </div>
                          <div className={`font-display text-2xl ${costPositive ? 'text-emerald-300' : 'text-red-300'}`}>
                            {costPositive ? '$' : '+$'}{Math.abs(ps.cost_savings_usd ?? 0).toLocaleString('en-US')}
                          </div>
                          <div className={`text-[11px] ${costPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                            {Math.abs(ps.cost_savings_pct ?? 0)}%
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">
                            {co2Positive ? 'CO₂ évité' : 'CO₂ supplémentaire'}
                          </div>
                          <div className={`font-display text-2xl ${co2Positive ? 'text-lime-300' : 'text-red-300'}`}>
                            {Math.abs(ps.co2_savings_kg ?? 0).toLocaleString('en-US')} kg
                          </div>
                          <div className={`text-[11px] ${co2Positive ? 'text-lime-400' : 'text-red-400'}`}>
                            {Math.abs(ps.co2_savings_pct ?? 0)}%
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">
                            {ps.time_savings_days >= 0 ? 'Temps gagné' : 'Délai allongé'}
                          </div>
                          <div className="font-display text-2xl text-yellow-300">
                            {Math.abs(ps.time_savings_days ?? 0)} j
                          </div>
                          <div className="text-[11px] text-yellow-400">/ expédition</div>
                        </div>
                        <div className="text-center">
                          <div className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">vs Aérien</div>
                          <div className="font-display text-2xl text-purple-300">
                            ${ps.cost_savings_vs_air_usd?.toLocaleString('en-US') ?? '—'}
                          </div>
                          <div className="text-[11px] text-purple-400">économisés {ps.cost_savings_vs_air_pct}%</div>
                        </div>
                      </div>

                      <div className={`border rounded-lg p-3 flex items-start gap-3 ${costPositive ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-[11px] uppercase tracking-wide ${costPositive ? 'text-emerald-300' : 'text-red-300'}`}>Projection annuelle</span>
                            <Label htmlFor="teu-yr" className="text-[10px] text-gray-400 ml-2">TEU/an :</Label>
                            <Input
                              id="teu-yr"
                              type="number" min={1}
                              value={teuPerYear}
                              onChange={e => setTeuPerYear(Math.max(1, Number(e.target.value) || 100))}
                              className="h-7 w-20 text-xs"
                              data-testid="roi-teu-input"
                            />
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <div className="text-[10px] text-gray-400">{costPositive ? 'Économie annuelle' : 'Surcoût annuel'}</div>
                              <div className={`font-display text-2xl ${costPositive ? 'text-emerald-200' : 'text-red-200'}`}>
                                ${Math.abs(annualCost).toLocaleString('en-US')}
                              </div>
                            </div>
                            <div>
                              <div className="text-[10px] text-gray-400">{co2Positive ? 'CO₂ évité annuel' : 'CO₂ supplémentaire annuel'}</div>
                              <div className={`font-display text-2xl ${co2Positive ? 'text-lime-200' : 'text-red-200'}`}>
                                {Math.abs(annualCo2).toFixed(1)} t
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </>
                  );
                })()}

                <div className="text-xs text-gray-300 italic border-t border-white/5 pt-2">
                  {result.roi_infrastructure.interpretation}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Operational routes */}
          {result.options.filter(o => !o.is_future).length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {result.options.filter(o => !o.is_future).map((opt, i) => (
                <OptionCard key={`op-${i}`} opt={opt} />
              ))}
            </div>
          )}

          {/* Future routes section */}
          {result.options.filter(o => o.is_future).length > 0 && (
            <>
              <div className="border-t border-dashed border-sky-500/30 pt-4 mt-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-sky-500/15 flex items-center justify-center">
                    <Construction className="w-4 h-4 text-sky-300" />
                  </div>
                  <div>
                    <h3 className="text-base font-display text-white">
                      Routes futures — Transsaharienne · Train Alger-Tamanrasset · Lagos-Calabar
                    </h3>
                    <p className="text-xs text-gray-400">
                      Infrastructures planifiées ou en construction (PIDA / BAD / SNTF / CCECC).
                      Coûts modélisés pour anticiper l&apos;impact sur vos chaînes logistiques.
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {result.options.filter(o => o.is_future).map((opt, i) => (
                  <OptionCard key={`fut-${i}`} opt={opt} />
                ))}
              </div>
            </>
          )}

          <div className="text-xs text-gray-500 text-center pt-2">
            Facteurs CO₂ (g/t·km) : Maritime {result.co2_methodology?.factors_g_per_tkm?.sea} ·
            Rail {result.co2_methodology?.factors_g_per_tkm?.rail} ·
            Route {result.co2_methodology?.factors_g_per_tkm?.road} ·
            Aérien {result.co2_methodology?.factors_g_per_tkm?.air}.
            &nbsp;Source : {result.co2_methodology?.source}.
          </div>
        </div>
      )}
    </div>
  );
}
