import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Ship, Plane, Truck, Loader2, Layers, Award, Zap, Leaf } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

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
  multimodal: { icon: Layers, color: 'text-purple-400', bg: 'bg-purple-500/10',  label: 'Multimodal' },
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
  const meta = MODE_META[opt.mode] || MODE_META.sea;
  const Icon = meta.icon;

  const badges = [];
  if (opt.is_cheapest) badges.push({ icon: Award, label: 'Le moins cher', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' });
  if (opt.is_fastest)  badges.push({ icon: Zap,    label: 'Le plus rapide', cls: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30' });
  if (opt.is_greenest) badges.push({ icon: Leaf,   label: 'Le plus vert',   cls: 'bg-lime-500/15 text-lime-300 border-lime-500/30' });

  return (
    <Card className="border border-white/10 bg-[#1B232C]" data-testid={`multimodal-option-${opt.mode}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className={`w-10 h-10 rounded-lg ${meta.bg} flex items-center justify-center flex-shrink-0`}>
              <Icon className={`w-5 h-5 ${meta.color}`} />
            </div>
            <div>
              <CardTitle className="text-base text-white">{opt.label}</CardTitle>
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

  const [supportedCountries, setSupportedCountries] = useState({ all_supported: [], landlocked_countries: [] });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-display text-white">
              {result.options_count} option{result.options_count > 1 ? 's' : ''} de fret disponibles
            </h3>
            {result.is_destination_landlocked && (
              <Badge className="bg-amber-500/15 text-amber-300 border-amber-500/40">
                Destination enclavée — combinaisons port + corridor proposées
              </Badge>
            )}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {result.options.map((opt, i) => (
              <OptionCard key={i} opt={opt} />
            ))}
          </div>
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
