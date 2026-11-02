import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Ship, Plane, Truck, Train, Loader2, Layers, Award, Zap, Leaf, Construction, Sparkles, TrendingUp, Building2 } from 'lucide-react';
import { PDFExportButton } from '../common/ExportTools';
import { montant } from '../../utils/nombres';
import { pick } from '../../i18n/lang';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

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
  COM:'Comores', GIN:'Guinée', GMB:'Gambie', GNB:'Guinée-Bissau',
  GNQ:'Guinée équatoriale', LBR:'Liberia', MRT:'Mauritanie', SDN:'Soudan',
  SLE:'Sierra Leone', SOM:'Somalie', SYC:'Seychelles',
};

const COUNTRY_NAMES_AR = {
  AGO:'أنغولا', BDI:'بوروندي', BEN:'بنين', BFA:'بوركينا فاسو',
  BWA:'بوتسوانا', CAF:'جمهورية أفريقيا الوسطى', CIV:'كوت ديفوار', CMR:'الكاميرون',
  COD:'جمهورية الكونغو الديمقراطية', COG:'الكونغو', DJI:'جيبوتي', DZA:'الجزائر',
  EGY:'مصر', ETH:'إثيوبيا', GAB:'الغابون', GHA:'غانا',
  KEN:'كينيا', LBY:'ليبيا', LSO:'ليسوتو', MAR:'المغرب',
  MDG:'مدغشقر', MLI:'مالي', MOZ:'موزمبيق', MUS:'موريشيوس',
  MWI:'ملاوي', NAM:'ناميبيا', NER:'النيجر', NGA:'نيجيريا',
  RWA:'رواندا', SEN:'السنغال', SSD:'جنوب السودان', SWZ:'إسواتيني',
  TCD:'تشاد', TGO:'توغو', TUN:'تونس', TZA:'تنزانيا',
  UGA:'أوغندا', ZAF:'جنوب أفريقيا', ZMB:'زامبيا', ZWE:'زيمبابوي',
  COM:'جزر القمر', GIN:'غينيا', GMB:'غامبيا', GNB:'غينيا بيساو',
  GNQ:'غينيا الاستوائية', LBR:'ليبيريا', MRT:'موريتانيا', SDN:'السودان',
  SLE:'سيراليون', SOM:'الصومال', SYC:'سيشل',
};

const MODE_META = {
  sea:        { icon: Ship,  color: 'text-[var(--info)]',    bg: 'bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))]',    label: 'Maritime' },
  air:        { icon: Plane, color: 'text-[var(--atlantic)]',    bg: 'bg-[color-mix(in_srgb,var(--atlantic)_10%,var(--afcfta-card))]',    label: 'Aérien' },
  land:       { icon: Truck, color: 'text-[var(--terra)]',  bg: 'bg-[color-mix(in_srgb,var(--terra)_10%,var(--afcfta-card))]',  label: 'Terrestre' },
  road:       { icon: Truck, color: 'text-[var(--terra)]',  bg: 'bg-[color-mix(in_srgb,var(--terra)_10%,var(--afcfta-card))]',  label: 'Route' },
  rail:       { icon: Train, color: 'text-[var(--success)]', bg: 'bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))]', label: 'Rail' },
  multimodal: { icon: Layers, color: 'text-[var(--violet)]', bg: 'bg-[color-mix(in_srgb,var(--violet)_10%,var(--afcfta-card))]',  label: 'Multimodal' },
};

const PHASE_META = {
  operational:         { label: 'Opérationnel', label_ar: 'قيد التشغيل',          cls: 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]' },
  under_construction:  { label: 'En construction', label_ar: 'قيد الإنشاء',       cls: 'bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))]  text-[var(--gold)]  border-[color-mix(in_srgb,var(--gold)_30%,transparent)]'  },
  planned:             { label: 'Planifié', label_ar: 'مخطَّط له',              cls: 'bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))]    text-[var(--info)]    border-[color-mix(in_srgb,var(--info)_30%,transparent)]'    },
  study:               { label: "Étude de faisabilité", label_ar: 'دراسة جدوى', cls: 'bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] text-[var(--violet)] border-[color-mix(in_srgb,var(--violet)_30%,transparent)]' },
};

// « 12 345 $ » en français, « $12,345 » en anglais.
function fmtUsd(v, language) {
  if (v == null) return '—';
  return montant(v, language, 3);
}

function fmtKg(v, language) {
  if (v == null) return '—';
  if (v >= 1000) return (v / 1000).toFixed(1) + pick(language, ' t CO₂', ' t CO₂', ' طن CO₂');
  return v.toFixed(1) + ' kg CO₂';
}

function fmtDays(min, max, language) {
  const d = pick(language, 'j', 'j', 'يوم');
  if (min == null && max == null) return '—';
  if (min === max || max == null) return `${min} ${d}`;
  return `${min}–${max} ${d}`;
}

function OptionCard({ opt, language }) {
  // Pick icon by corridor mode when available (so rail uses Train, not Truck)
  const iconKey = opt.corridor_mode || opt.mode;
  const meta = MODE_META[iconKey] || MODE_META[opt.mode] || MODE_META.sea;
  const Icon = meta.icon;
  const phaseMeta = PHASE_META[opt.phase] || PHASE_META.operational;

  const badges = [];
  if (opt.is_cheapest) badges.push({ icon: Award, label: pick(language, 'Le moins cher', 'Le moins cher', 'الأقل تكلفة'), cls: 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]' });
  if (opt.is_fastest)  badges.push({ icon: Zap,    label: pick(language, 'Le plus rapide', 'Le plus rapide', 'الأسرع'), cls: 'bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]' });
  if (opt.is_greenest) badges.push({ icon: Leaf,   label: pick(language, 'Le plus vert', 'Le plus vert', 'الأقل تلويثًا'),   cls: 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]' });
  if (opt.is_future_cheapest)  badges.push({ icon: Sparkles, label: pick(language, 'Futur · le moins cher', 'Futur · le moins cher', 'مستقبلي · الأقل تكلفة'), cls: 'bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)]' });
  if (opt.is_future_greenest)  badges.push({ icon: Sparkles, label: pick(language, 'Futur · le plus vert', 'Futur · le plus vert', 'مستقبلي · الأقل تلويثًا'), cls: 'bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)]' });

  const cardBorder = opt.is_future
    ? 'border border-dashed border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[var(--afcfta-card2)]'
    : 'border border-[var(--overlay-border)] bg-[var(--afcfta-card)]';

  return (
    <Card className={cardBorder} data-testid={`multimodal-option-${opt.mode}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className={`w-10 h-10 rounded-lg ${meta.bg} flex items-center justify-center flex-shrink-0`}>
              <Icon className={`w-5 h-5 ${meta.color}`} />
            </div>
            <div>
              <CardTitle className="text-base text-[var(--text)] flex items-center gap-2 flex-wrap">
                {opt.label}
                {opt.is_future && (
                  <Badge variant="outline" className={`text-[11px] ${phaseMeta.cls}`}>
                    <Construction className="w-3 h-3 mr-1" />{pick(language, phaseMeta.label, phaseMeta.label, phaseMeta.label_ar)}
                  </Badge>
                )}
              </CardTitle>
              {opt.via_port && (
                <CardDescription className="text-xs mt-1 text-[var(--afcfta-muted)]">
                  {pick(language, 'Transit via', 'Transit via', 'عبور عبر')} <span className="text-[var(--text)]">{opt.via_port}</span>
                  {opt.corridor_name && <> · {pick(language, 'Corridor', 'Corridor', 'ممر')} <span className="text-[var(--text)]">{opt.corridor_name}</span></>}
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
          <div className="rounded-lg bg-[var(--overlay)] px-3 py-2">
            <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">{pick(language, 'Coût total', 'Coût total', 'التكلفة الإجمالية')}</div>
            <div className="font-display text-2xl text-[var(--text)]">{fmtUsd(opt.total_cost_usd, language)}</div>
          </div>
          <div className="rounded-lg bg-[var(--overlay)] px-3 py-2">
            <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">{pick(language, 'Délai', 'Délai', 'المدة')}</div>
            <div className="font-display text-2xl text-[var(--text)]">{fmtDays(opt.transit_days_min, opt.transit_days_max, language)}</div>
          </div>
          <div className="rounded-lg bg-[var(--overlay)] px-3 py-2">
            <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">{pick(language, 'Empreinte CO₂', 'Empreinte CO₂', 'البصمة الكربونية CO₂')}</div>
            <div className="font-display text-2xl text-[var(--text)]">{fmtKg(opt.co2_kg, language)}</div>
          </div>
        </div>

        {/* Segments */}
        {opt.segments && opt.segments.length > 0 && (
          <div className="border-t border-[var(--overlay-border)] pt-3">
            <div className="text-[11px] text-[var(--afcfta-muted)] mb-2">
              {opt.segments.length === 1
                ? pick(language, 'Trajet', 'Trajet', 'المسار')
                : pick(language, `${opt.segments.length} segments`, `${opt.segments.length} segments`, `${opt.segments.length} مقاطع`)}
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
                      <div className="text-[var(--text)]">
                        <span className="font-medium">{seg.from}</span>
                        {' → '}
                        <span className="font-medium">{seg.to}</span>
                      </div>
                      <div className="text-xs text-[var(--afcfta-muted)] mt-0.5">
                        {seg.distance_km != null && <span>{seg.distance_km.toLocaleString('en-US')} km</span>}
                        {seg.transit_days_min != null && <span> · {fmtDays(seg.transit_days_min, seg.transit_days_max, language)}</span>}
                        {seg.cost_usd != null && <span> · {fmtUsd(seg.cost_usd, language)}</span>}
                        {seg.corridor_name && <span> · {seg.corridor_name}</span>}
                      </div>
                      {seg.carriers && seg.carriers.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1 mt-1">
                          <Building2 className="w-3 h-3 text-[var(--afcfta-muted)] flex-shrink-0" />
                          {seg.carriers.map((c, ci) => (
                            <span
                              key={ci}
                              className="text-[11px] px-1.5 py-0.5 rounded bg-[var(--overlay)] text-[var(--text)] border border-[var(--overlay-border)]"
                            >
                              {c}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {opt.notes && (
          <div className="text-xs text-[var(--afcfta-muted)] italic border-t border-[var(--overlay-border)] pt-2">
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
    axios.get(`${API}/logistics/multimodal/countries`)
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
      const res = await axios.get(`${API}/logistics/multimodal/compare`, {
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
      <div className="flex items-center gap-3 bg-[image:var(--card-grad)] border border-[var(--afcfta-border)] text-[var(--text)] p-4 rounded-xl shadow-lg">
        <div className="w-10 h-10 bg-[var(--overlay)] rounded-lg flex items-center justify-center">
          <Layers className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold">{pick(language, 'Comparateur Multimodal', 'Comparateur Multimodal', 'المقارن المتعدد الوسائط')}</h2>
          <p className="text-[var(--info)] text-sm">
            {pick(
              language,
              'Compare maritime · aérien · terrestre · combinaisons port+corridor pour les pays enclavés',
              'Compare maritime · aérien · terrestre · combinaisons port+corridor pour les pays enclavés',
              'مقارنة بين الشحن البحري · الجوي · البري · وتركيبات ميناء+ممر للبلدان غير الساحلية'
            )}
          </p>
        </div>
      </div>

      {/* Form */}
      <Card className="border border-[var(--overlay-border)] bg-[var(--afcfta-card)]">
        <CardContent className="pt-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-[var(--text)] text-sm mb-1.5 block">{pick(language, "Pays d'origine", "Pays d'origine", 'بلد المنشأ')}</Label>
              <Select value={origin} onValueChange={setOrigin}>
                <SelectTrigger data-testid="multimodal-origin-select"><SelectValue /></SelectTrigger>
                <SelectContent className="max-h-[280px]">
                  {countryOptions.map(iso => (
                    <SelectItem key={iso} value={iso}>
                      {pick(language, COUNTRY_NAMES_FR[iso], COUNTRY_NAMES_FR[iso], COUNTRY_NAMES_AR[iso]) || iso} ({iso})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-[var(--text)] text-sm mb-1.5 block">
                {pick(language, 'Pays de destination', 'Pays de destination', 'بلد المقصد')}
                {isLandlockedDest && (
                  <Badge className="ml-2 text-[11px] bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                    {pick(language, 'Enclavé', 'Enclavé', 'غير ساحلي')}
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
                        {pick(language, COUNTRY_NAMES_FR[iso], COUNTRY_NAMES_FR[iso], COUNTRY_NAMES_AR[iso]) || iso} ({iso}){landlocked ? pick(language, ' • enclavé', ' • enclavé', ' • غير ساحلي') : ''}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <Label className="text-[var(--text)] text-sm mb-1.5 block">{pick(language, 'Poids (kg)', 'Poids (kg)', 'الوزن (kg)')}</Label>
              <Input
                type="number" min={1}
                value={weightKg}
                onChange={e => setWeightKg(Number(e.target.value) || 0)}
                data-testid="multimodal-weight-input"
              />
            </div>
            <div>
              <Label className="text-[var(--text)] text-sm mb-1.5 block">{pick(language, 'Volume (m³, optionnel)', 'Volume (m³, optionnel)', 'الحجم (m³، اختياري)')}</Label>
              <Input
                type="number" min={0} step="0.1"
                value={volumeM3}
                onChange={e => setVolumeM3(Number(e.target.value) || 0)}
              />
            </div>
            <div>
              <Label className="text-[var(--text)] text-sm mb-1.5 block">{pick(language, 'Conteneur (maritime)', 'Conteneur (maritime)', 'الحاوية (بحري)')}</Label>
              <Select value={containerType} onValueChange={setContainerType}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="teu">{pick(language, "20' Standard (TEU)", "20' Standard (TEU)", '20 قدمًا قياسية (TEU)')}</SelectItem>
                  <SelectItem value="feu">{pick(language, "40' Standard (FEU)", "40' Standard (FEU)", '40 قدمًا قياسية (FEU)')}</SelectItem>
                  <SelectItem value="feu_hc">{pick(language, "40' High-Cube", "40' High-Cube", '40 قدمًا مرتفعة (High-Cube)')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-[var(--text)] text-sm mb-1.5 block">{pick(language, 'Nature marchandise (air)', 'Nature marchandise (air)', 'طبيعة البضاعة (جوي)')}</Label>
              <Select value={airCommodity} onValueChange={setAirCommodity}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">{pick(language, 'Marchandise générale', 'Marchandise générale', 'بضائع عامة')}</SelectItem>
                  <SelectItem value="perishable">{pick(language, 'Périssable', 'Périssable', 'قابلة للتلف')}</SelectItem>
                  <SelectItem value="pharma">{pick(language, 'Pharmaceutique', 'Pharmaceutique', 'منتجات صيدلانية')}</SelectItem>
                  <SelectItem value="dangerous">{pick(language, 'Dangereuse (DGR)', 'Dangereuse (DGR)', 'خطرة (DGR)')}</SelectItem>
                  <SelectItem value="valuable">{pick(language, 'Valeur / sécurisé', 'Valeur / sécurisé', 'ثمينة / مؤمَّنة')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="pt-2">
            <Button
              onClick={handleCompare}
              disabled={loading || origin === destination}
              className="bg-[var(--violet)] hover:bg-[var(--violet)] text-[var(--bg)]"
              data-testid="multimodal-compare-btn"
            >
              {loading ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />{pick(language, 'Calcul en cours…', 'Calcul en cours…', 'جارٍ الحساب…')}</>
              ) : (
                <><Layers className="w-4 h-4 mr-2" />{pick(language, 'Comparer les modes', 'Comparer les modes', 'مقارنة الوسائط')}</>
              )}
            </Button>
            {origin === destination && (
              <span className="ml-3 text-xs text-[var(--gold)]">{pick(language, 'Origine et destination doivent être différentes.', 'Origine et destination doivent être différentes.', 'يجب أن يختلف المنشأ عن المقصد.')}</span>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border border-[color-mix(in_srgb,var(--danger)_30%,transparent)] bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))]">
          <CardContent className="pt-4 text-sm text-[var(--danger)]">⚠ {error}</CardContent>
        </Card>
      )}

      {result && result.options_count === 0 && (
        <Card className="border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))]">
          <CardContent className="pt-4 text-sm text-[var(--gold)]">
            {pick(language, 'Aucune option de fret disponible dans la base de données pour ce trajet.', 'Aucune option de fret disponible dans la base de données pour ce trajet.', 'لا يوجد أي خيار شحن متاح في قاعدة البيانات لهذا المسار.')}
          </CardContent>
        </Card>
      )}

      {result && result.options_count > 0 && (
        <div ref={reportRef} className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="text-lg font-display text-[var(--text)]">
              {pick(
                language,
                <>{result.operational_count} option{result.operational_count > 1 ? 's' : ''} opérationnelle{result.operational_count > 1 ? 's' : ''}</>,
                <>{result.operational_count} option{result.operational_count > 1 ? 's' : ''} opérationnelle{result.operational_count > 1 ? 's' : ''}</>,
                <>خيارات قيد التشغيل: {result.operational_count}</>
              )}
              {result.future_count > 0 && (
                <span className="text-[var(--info)] text-base ml-2">
                  {pick(
                    language,
                    <>· {result.future_count} option{result.future_count > 1 ? 's' : ''} future{result.future_count > 1 ? 's' : ''} (planifiées / en construction)</>,
                    <>· {result.future_count} option{result.future_count > 1 ? 's' : ''} future{result.future_count > 1 ? 's' : ''} (planifiées / en construction)</>,
                    <>· خيارات مستقبلية: {result.future_count} (مخططة / قيد الإنشاء)</>
                  )}
                </span>
              )}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              {result.is_destination_landlocked && (
                <Badge className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
                  {pick(language, 'Destination enclavée — combinaisons port + corridor proposées', 'Destination enclavée — combinaisons port + corridor proposées', 'مقصد غير ساحلي — تُقترح تركيبات ميناء + ممر')}
                </Badge>
              )}
              <PDFExportButton
                targetRef={reportRef}
                filename={`comparaison_multimodale_${origin}_${destination}`}
                title={pick(language, `Comparaison multimodale ${origin} → ${destination}`, `Comparaison multimodale ${origin} → ${destination}`, `مقارنة متعددة الوسائط ${origin} ← ${destination}`)}
                subtitle={`${weightKg/1000} t · ${containerType.toUpperCase()} · ZLECAf Analytics`}
                language={language}
                data-testid="multimodal-pdf-btn"
              />
            </div>
          </div>

          {/* ROI Infrastructure card */}
          {result.roi_infrastructure && (
            <Card className="border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-gradient-to-br from-sky-500/10 to-purple-500/10">
              <CardHeader className="pb-3">
                <div className="flex items-start gap-3">
                  <div className="w-11 h-11 rounded-xl bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] flex items-center justify-center flex-shrink-0">
                    <TrendingUp className="w-5 h-5 text-[var(--info)]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base text-[var(--text)]">
                      {pick(language, 'ROI Infrastructure — projection si les routes planifiées étaient opérationnelles', 'ROI Infrastructure — projection si les routes planifiées étaient opérationnelles', 'العائد على الاستثمار في البنية التحتية — توقعات في حال تشغيل الطرق المخططة')}
                    </CardTitle>
                    <CardDescription className="text-xs mt-1 text-[var(--text)]">
                      {pick(
                        language,
                        "Compare la meilleure option opérationnelle d'aujourd'hui avec la meilleure route future.",
                        "Compare la meilleure option opérationnelle d'aujourd'hui avec la meilleure route future.",
                        'مقارنة أفضل خيار قيد التشغيل اليوم بأفضل طريق مستقبلي.'
                      )}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="rounded-lg bg-[var(--overlay)] p-3 border border-[var(--overlay-border)]">
                    <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">{pick(language, "Aujourd'hui", "Aujourd'hui", 'اليوم')}</div>
                    <div className="text-sm text-[var(--text)] mb-2">
                      {result.roi_infrastructure.reference_operational.label}
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div><span className="text-[var(--afcfta-muted)] text-[11px]">{pick(language, 'Coût', 'Coût', 'التكلفة')}</span><div className="font-display text-base text-[var(--text)]">{fmtUsd(result.roi_infrastructure.reference_operational.cost_usd, language)}</div></div>
                      <div><span className="text-[var(--afcfta-muted)] text-[11px]">{pick(language, 'Délai', 'Délai', 'المدة')}</span><div className="font-display text-base text-[var(--text)]">{result.roi_infrastructure.reference_operational.transit_days_avg} {pick(language, 'j', 'j', 'يوم')}</div></div>
                      <div><span className="text-[var(--afcfta-muted)] text-[11px]">CO₂</span><div className="font-display text-base text-[var(--text)]">{(result.roi_infrastructure.reference_operational.co2_kg / 1000).toFixed(1)} {pick(language, 't', 't', 'طن')}</div></div>
                    </div>
                  </div>
                  <div className="rounded-lg bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] p-3 border border-dashed border-[color-mix(in_srgb,var(--info)_30%,transparent)]">
                    <div className="text-[11px] text-[var(--info)] mb-1">
                      🚧 {pick(language, 'Futur', 'Futur', 'مستقبلي')} · {result.roi_infrastructure.best_future_cost.status}
                    </div>
                    <div className="text-sm text-[var(--text)] mb-2">
                      {result.roi_infrastructure.best_future_cost.label}
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <div><span className="text-[var(--afcfta-muted)] text-[11px]">{pick(language, 'Coût', 'Coût', 'التكلفة')}</span><div className="font-display text-base text-[var(--info)]">{fmtUsd(result.roi_infrastructure.best_future_cost.cost_usd, language)}</div></div>
                      <div><span className="text-[var(--afcfta-muted)] text-[11px]">{pick(language, 'Délai', 'Délai', 'المدة')}</span><div className="font-display text-base text-[var(--info)]">{result.roi_infrastructure.best_future_cost.transit_days_avg} {pick(language, 'j', 'j', 'يوم')}</div></div>
                      <div><span className="text-[var(--afcfta-muted)] text-[11px]">CO₂</span><div className="font-display text-base text-[var(--info)]">{(result.roi_infrastructure.best_future_cost.co2_kg / 1000).toFixed(1)} {pick(language, 't', 't', 'طن')}</div></div>
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
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-[var(--overlay-border)]">
                        <div className="text-center">
                          <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">
                            {costPositive ? pick(language, 'Économie par expédition', 'Économie par expédition', 'الوفر لكل شحنة') : pick(language, 'Surcoût par expédition', 'Surcoût par expédition', 'التكلفة الإضافية لكل شحنة')}
                          </div>
                          <div className={`font-display text-2xl ${costPositive ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                            {costPositive ? '' : '+'}{fmtUsd(Math.abs(ps.cost_savings_usd ?? 0), language)}
                          </div>
                          <div className={`text-[11px] ${costPositive ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                            {Math.abs(ps.cost_savings_pct ?? 0)}%
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">
                            {co2Positive ? pick(language, 'CO₂ évité', 'CO₂ évité', 'CO₂ المتجنَّب') : pick(language, 'CO₂ supplémentaire', 'CO₂ supplémentaire', 'CO₂ الإضافي')}
                          </div>
                          <div className={`font-display text-2xl ${co2Positive ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                            {Math.abs(ps.co2_savings_kg ?? 0).toLocaleString('en-US')} kg
                          </div>
                          <div className={`text-[11px] ${co2Positive ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                            {Math.abs(ps.co2_savings_pct ?? 0)}%
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">
                            {ps.time_savings_days >= 0 ? pick(language, 'Temps gagné', 'Temps gagné', 'الوقت الموفَّر') : pick(language, 'Délai allongé', 'Délai allongé', 'مدة أطول')}
                          </div>
                          <div className="font-display text-2xl text-[var(--gold)]">
                            {Math.abs(ps.time_savings_days ?? 0)} {pick(language, 'j', 'j', 'يوم')}
                          </div>
                          <div className="text-[11px] text-[var(--gold)]">{pick(language, '/ expédition', '/ expédition', '/ شحنة')}</div>
                        </div>
                        <div className="text-center">
                          <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">{pick(language, 'vs aérien', 'vs aérien', 'مقارنة بالجوي')}</div>
                          <div className="font-display text-2xl text-[var(--violet)]">
                            {fmtUsd(ps.cost_savings_vs_air_usd, language)}
                          </div>
                          <div className="text-[11px] text-[var(--violet)]">{pick(language, 'économisés', 'économisés', 'وفر')} {ps.cost_savings_vs_air_pct}%</div>
                        </div>
                      </div>

                      <div className={`border rounded-lg p-3 flex items-start gap-3 ${costPositive ? 'bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--success)_30%,transparent)]' : 'bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--danger)_30%,transparent)]'}`}>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`text-[11px] ${costPositive ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>{pick(language, 'Projection annuelle', 'Projection annuelle', 'التوقعات السنوية')}</span>
                            <Label htmlFor="teu-yr" className="text-[11px] text-[var(--afcfta-muted)] ml-2">{pick(language, 'TEU/an :', 'TEU/an :', 'TEU/سنة:')}</Label>
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
                              <div className="text-[11px] text-[var(--afcfta-muted)]">{costPositive ? pick(language, 'Économie annuelle', 'Économie annuelle', 'الوفر السنوي') : pick(language, 'Surcoût annuel', 'Surcoût annuel', 'التكلفة الإضافية السنوية')}</div>
                              <div className={`font-display text-2xl ${costPositive ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                                {fmtUsd(Math.abs(annualCost), language)}
                              </div>
                            </div>
                            <div>
                              <div className="text-[11px] text-[var(--afcfta-muted)]">{co2Positive ? pick(language, 'CO₂ évité annuel', 'CO₂ évité annuel', 'CO₂ المتجنَّب سنويًا') : pick(language, 'CO₂ supplémentaire annuel', 'CO₂ supplémentaire annuel', 'CO₂ الإضافي سنويًا')}</div>
                              <div className={`font-display text-2xl ${co2Positive ? 'text-[var(--success)]' : 'text-[var(--danger)]'}`}>
                                {Math.abs(annualCo2).toFixed(1)} {pick(language, 't', 't', 'طن')}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </>
                  );
                })()}

                <div className="text-xs text-[var(--text)] italic border-t border-[var(--overlay-border)] pt-2">
                  {result.roi_infrastructure.interpretation}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Operational routes */}
          {result.options.filter(o => !o.is_future).length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {result.options.filter(o => !o.is_future).map((opt, i) => (
                <OptionCard key={`op-${i}`} opt={opt} language={language} />
              ))}
            </div>
          )}

          {/* Future routes section */}
          {result.options.filter(o => o.is_future).length > 0 && (
            <>
              <div className="border-t border-dashed border-[color-mix(in_srgb,var(--info)_30%,transparent)] pt-4 mt-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] flex items-center justify-center">
                    <Construction className="w-4 h-4 text-[var(--info)]" />
                  </div>
                  <div>
                    <h3 className="text-base font-display text-[var(--text)]">
                      {pick(
                        language,
                        'Routes futures — Transsaharienne · Train Alger-Tamanrasset · Lagos-Calabar',
                        'Routes futures — Transsaharienne · Train Alger-Tamanrasset · Lagos-Calabar',
                        'الطرق المستقبلية — الطريق العابر للصحراء · قطار الجزائر-تمنراست · لاغوس-كالابار'
                      )}
                    </h3>
                    <p className="text-xs text-[var(--afcfta-muted)]">
                      {pick(
                        language,
                        <>
                      Infrastructures planifiées ou en construction (PIDA / BAD / SNTF / CCECC).
                      Coûts modélisés pour anticiper l&apos;impact sur vos chaînes logistiques.
                        </>,
                        <>
                      Infrastructures planifiées ou en construction (PIDA / BAD / SNTF / CCECC).
                      Coûts modélisés pour anticiper l&apos;impact sur vos chaînes logistiques.
                        </>,
                        <>
                      بنى تحتية مخططة أو قيد الإنشاء (PIDA / بنك التنمية الأفريقي / SNTF / CCECC).
                      تكاليف مُنمذَجة لاستباق الأثر على سلاسلكم اللوجستية.
                        </>
                      )}
                    </p>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {result.options.filter(o => o.is_future).map((opt, i) => (
                  <OptionCard key={`fut-${i}`} opt={opt} language={language} />
                ))}
              </div>
            </>
          )}

          <div className="text-xs text-[var(--afcfta-muted)] text-center pt-2">
            {pick(
              language,
              <>
            Facteurs CO₂ (g/t·km) : Maritime {result.co2_methodology?.factors_g_per_tkm?.sea} ·
            Rail {result.co2_methodology?.factors_g_per_tkm?.rail} ·
            Route {result.co2_methodology?.factors_g_per_tkm?.road} ·
            Aérien {result.co2_methodology?.factors_g_per_tkm?.air}.
            &nbsp;Source : {result.co2_methodology?.source}.
              </>,
              <>
            Facteurs CO₂ (g/t·km) : Maritime {result.co2_methodology?.factors_g_per_tkm?.sea} ·
            Rail {result.co2_methodology?.factors_g_per_tkm?.rail} ·
            Route {result.co2_methodology?.factors_g_per_tkm?.road} ·
            Aérien {result.co2_methodology?.factors_g_per_tkm?.air}.
            &nbsp;Source : {result.co2_methodology?.source}.
              </>,
              <>
            معاملات CO₂ (g/t·km): البحري {result.co2_methodology?.factors_g_per_tkm?.sea} ·
            السكك الحديدية {result.co2_methodology?.factors_g_per_tkm?.rail} ·
            الطريق {result.co2_methodology?.factors_g_per_tkm?.road} ·
            الجوي {result.co2_methodology?.factors_g_per_tkm?.air}.
            &nbsp;المصدر: {result.co2_methodology?.source}.
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
