import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import {
  Ship, Plane, Truck, Train, Building2, Globe, Phone, Mail,
  MapPin, ExternalLink, Users, Search, Filter, ChevronDown,
  ChevronUp, Anchor, Package, ShieldCheck, Star
} from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const CATEGORY_META = {
  armateurs: {
    label: 'Armateurs / Compagnies maritimes',
    icon: Ship,
    color: 'blue',
    bg: 'rgba(59,130,246,0.1)',
    border: 'rgba(59,130,246,0.3)',
    badge: 'bg-[color-mix(in_srgb,var(--info)_12%,var(--afcfta-card))] text-[var(--info)] border-[color-mix(in_srgb,var(--info)_30%,transparent)]',
    desc: 'Grandes compagnies de transport maritime opérant sur les routes africaines',
  },
  port_operators: {
    label: 'Opérateurs portuaires',
    icon: Anchor,
    color: 'cyan',
    bg: 'rgba(6,182,212,0.1)',
    border: 'rgba(6,182,212,0.3)',
    badge: 'bg-[color-mix(in_srgb,var(--atlantic)_12%,var(--afcfta-card))] text-[var(--atlantic)] border-[color-mix(in_srgb,var(--atlantic)_30%,transparent)]',
    desc: 'Gestionnaires de terminaux à conteneurs et ports africains',
  },
  transitaires: {
    label: 'Transitaires & Freight Forwarders',
    icon: Package,
    color: 'amber',
    bg: 'rgba(245,158,11,0.1)',
    border: 'rgba(245,158,11,0.3)',
    badge: 'bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]',
    desc: 'Commissionnaires de transport, organisateurs de fret, dédouanement',
  },
  rail_operators: {
    label: 'Opérateurs ferroviaires',
    icon: Train,
    color: 'green',
    bg: 'rgba(34,197,94,0.1)',
    border: 'rgba(34,197,94,0.3)',
    badge: 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]',
    desc: 'Compagnies ferroviaires nationales et régionales africaines',
  },
  trucking_companies: {
    label: 'Transporteurs routiers',
    icon: Truck,
    color: 'orange',
    bg: 'rgba(249,115,22,0.1)',
    border: 'rgba(249,115,22,0.3)',
    badge: 'bg-[color-mix(in_srgb,var(--terra)_12%,var(--afcfta-card))] text-[var(--terra)] border-[color-mix(in_srgb,var(--terra)_30%,transparent)]',
    desc: 'Compagnies de transport routier et de distribution',
  },
  air_cargo: {
    label: 'Cargo aérien',
    icon: Plane,
    color: 'purple',
    bg: 'rgba(168,85,247,0.1)',
    border: 'rgba(168,85,247,0.3)',
    badge: 'bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] text-[var(--violet)] border-[color-mix(in_srgb,var(--violet)_30%,transparent)]',
    desc: 'Compagnies cargo aérien opérant sur le continent africain',
  },
  customs_agents: {
    label: 'Douanes & Commissionnaires',
    icon: ShieldCheck,
    color: 'red',
    bg: 'rgba(239,68,68,0.1)',
    border: 'rgba(239,68,68,0.3)',
    badge: 'bg-[color-mix(in_srgb,var(--danger)_12%,var(--afcfta-card))] text-[var(--danger)] border-[color-mix(in_srgb,var(--danger)_30%,transparent)]',
    desc: 'Autorités douanières et commissionnaires agréés',
  },
  regulatory_bodies: {
    label: 'Organismes de régulation',
    icon: Globe,
    color: 'slate',
    bg: 'rgba(100,116,139,0.1)',
    border: 'rgba(100,116,139,0.3)',
    badge: 'bg-slate-500/20 text-[var(--text)] border-[var(--afcfta-border)]',
    desc: 'Organisations et associations internationales du secteur logistique',
  },
};

const COUNTRY_LABELS = {
  ALL: 'Tous les pays',
  DZA: '🇩🇿 Algérie', MAR: '🇲🇦 Maroc', EGY: '🇪🇬 Égypte',
  NGA: '🇳🇬 Nigéria', ZAF: '🇿🇦 Afrique du Sud', KEN: '🇰🇪 Kenya',
  TZA: '🇹🇿 Tanzanie', CIV: "🇨🇮 Côte d'Ivoire", GHA: '🇬🇭 Ghana',
  SEN: '🇸🇳 Sénégal', CMR: '🇨🇲 Cameroun', ETH: '🇪🇹 Éthiopie',
  DJI: '🇩🇯 Djibouti', MOZ: '🇲🇿 Mozambique', AGO: '🇦🇴 Angola',
  TUN: '🇹🇳 Tunisie', LBY: '🇱🇾 Libye', SDN: '🇸🇩 Soudan',
  SSD: '🇸🇸 Soudan du Sud', COD: '🇨🇩 RD Congo', COG: '🇨🇬 Congo',
  GAB: '🇬🇦 Gabon', TCD: '🇹🇩 Tchad', CAF: '🇨🇫 Centrafrique',
  TGO: '🇹🇬 Togo', BEN: '🇧🇯 Bénin', BFA: '🇧🇫 Burkina Faso',
  MLI: '🇲🇱 Mali', NER: '🇳🇪 Niger', GIN: '🇬🇳 Guinée',
  MRT: '🇲🇷 Mauritanie', UGA: '🇺🇬 Ouganda', RWA: '🇷🇼 Rwanda',
  SOM: '🇸🇴 Somalie', ZMB: '🇿🇲 Zambie', ZWE: '🇿🇼 Zimbabwe',
  MWI: '🇲🇼 Malawi', NAM: '🇳🇦 Namibie', BWA: '🇧🇼 Botswana',
  SWZ: '🇸🇿 Eswatini', MDG: '🇲🇬 Madagascar', MUS: '🇲🇺 Maurice',
};

function ContactChip({ icon: Icon, value, href, color = 'gray' }) {
  if (!value) return null;
  const content = (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono max-w-full min-w-0
      bg-[var(--overlay)] border border-[var(--overlay-border)] text-[var(--text)] hover:bg-[var(--overlay)] hover:text-[var(--text)]
      transition-colors cursor-pointer group`}
    >
      <Icon className="w-3 h-3 flex-shrink-0 text-[var(--afcfta-muted)] group-hover:text-[var(--text)]" />
      <span className="truncate min-w-0">{value}</span>
    </span>
  );
  return href ? (
    <a href={href} target="_blank" rel="noreferrer" className="inline-flex max-w-full min-w-0">{content}</a>
  ) : content;
}

function CountryBadge({ iso }) {
  const label = COUNTRY_LABELS[iso] || iso;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px]
      bg-[var(--overlay)] border border-[var(--overlay-border)] text-[var(--afcfta-muted)]">
      {label}
    </span>
  );
}

const isUrl = (v) => typeof v === 'string' && /^https?:\/\//i.test(v);
const isEmail = (v) => typeof v === 'string' && v.includes('@') && !v.includes(' ');
const isPhone = (v) => typeof v === 'string' && /^[+0-9][0-9\s()\-./]{5,}$/.test(v);
const GENERIC_CONTACT_KEYS = new Set(['phone', 'email', 'address', 'fax']);

function ContactRow({ icon: Icon, label, value, href, mono = false }) {
  if (!value) return null;
  const textClass = `min-w-0 flex-1 ${mono ? 'font-mono' : ''}`;
  const anywhere = { overflowWrap: 'anywhere', wordBreak: 'break-word' };
  return (
    <div className="flex items-start gap-1.5 text-xs text-[var(--text)] min-w-0">
      <Icon className="w-3 h-3 flex-shrink-0 mt-0.5 text-[var(--afcfta-muted)]" />
      <div className={textClass} style={anywhere}>
        {label && <span className="text-[var(--afcfta-muted)] mr-1">{label} :</span>}
        {href ? (
          <a href={href} target="_blank" rel="noreferrer"
            className="text-[var(--text)] hover:text-[var(--text)] underline-offset-2 hover:underline">
            {value}
          </a>
        ) : (
          <span>{value}</span>
        )}
      </div>
    </div>
  );
}

function FlatContactRow({ contactKey, value }) {
  const label = GENERIC_CONTACT_KEYS.has(contactKey) ? null : contactKey.replace(/_/g, ' ');
  if (isUrl(value)) {
    return <ContactRow icon={ExternalLink} label={label} value={value.replace(/^https?:\/\//i, '')} href={value} />;
  }
  if (isEmail(value)) {
    return <ContactRow icon={Mail} label={label} value={value} href={`mailto:${value}`} mono />;
  }
  if (isPhone(value)) {
    return <ContactRow icon={Phone} label={label} value={value} href={`tel:${value.replace(/\s/g, '')}`} mono />;
  }
  return <ContactRow icon={MapPin} label={label} value={value} />;
}

function ContactsBlock({ contacts }) {
  if (!contacts || Object.keys(contacts).length === 0) return null;
  const entries = Object.entries(contacts);
  const flatEntries = entries.filter(([k, v]) => k !== 'website' && typeof v === 'string' && v);
  const officeEntries = entries.filter(([, v]) => v && typeof v === 'object');

  return (
    <div className="space-y-2 mt-3 min-w-0">
      {contacts.website && (
        <ContactRow
          icon={ExternalLink}
          value={contacts.website.replace(/^https?:\/\//i, '')}
          href={contacts.website}
        />
      )}
      {flatEntries.length > 0 && (
        <div className="space-y-1">
          {flatEntries.map(([key, val]) => (
            <FlatContactRow key={key} contactKey={key} value={val} />
          ))}
        </div>
      )}
      {officeEntries.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {officeEntries.map(([key, val]) => {
            const { phone, email, address, website } = val;
            if (!phone && !email && !address && !website) return null;
            const label = key.replace(/_/g, ' ');
            return (
              <div key={key} className="p-2 rounded-lg bg-[var(--overlay)] border border-[var(--overlay-border)] min-w-0">
                <div className="text-[11px] text-[var(--afcfta-muted)] mb-1 font-medium"
                  style={{ overflowWrap: 'anywhere' }}>{label}</div>
                <div className="space-y-1">
                  <ContactRow icon={Phone} value={phone} href={phone ? `tel:${phone.replace(/\s/g, '')}` : null} mono />
                  <ContactRow icon={Mail} value={email} href={email ? `mailto:${email}` : null} mono />
                  <ContactRow icon={MapPin} value={address} />
                  <ContactRow icon={ExternalLink} value={website ? website.replace(/^https?:\/\//i, '') : null} href={website} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function OperatorCard({ operator, catMeta }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = catMeta.icon;

  const presenceList = operator.africa_presence
    || operator.countries
    || (operator.country_iso ? [operator.country_iso] : []);

  const hasContacts = operator.contacts && Object.keys(operator.contacts).length > 0;

  return (
    <div className="rounded-xl border transition-all duration-200"
      style={{ background: catMeta.bg, borderColor: catMeta.border }}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
            style={{ background: catMeta.bg, border: `1px solid ${catMeta.border}` }}>
            <Icon className="w-4 h-4 text-[var(--text)]" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="text-sm font-semibold text-[var(--text)] leading-tight">{operator.name}</h4>
                {operator.hq && (
                  <div className="flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3 h-3 text-[var(--afcfta-muted)]" />
                    <span className="text-xs text-[var(--afcfta-muted)]">{operator.hq}</span>
                  </div>
                )}
              </div>
              <Badge className={`text-[11px] px-1.5 flex-shrink-0 border ${catMeta.badge}`}>
                {operator.type_label || operator.type}
              </Badge>
            </div>

            <div className="flex flex-wrap gap-2 mt-2">
              {operator.fleet_size && (
                <span className="text-[11px] text-[var(--afcfta-muted)] flex items-center gap-1">
                  <Truck className="w-3 h-3" /> {operator.fleet_size} véhicules
                </span>
              )}
              {operator.fleet_vessels && (
                <span className="text-[11px] text-[var(--afcfta-muted)] flex items-center gap-1">
                  <Ship className="w-3 h-3" /> {operator.fleet_vessels} navires
                </span>
              )}
              {operator.fleet_teu && (
                <span className="text-[11px] text-[var(--afcfta-muted)] flex items-center gap-1">
                  <Package className="w-3 h-3" /> {(operator.fleet_teu / 1000000).toFixed(1)}M TEU
                </span>
              )}
              {operator.fleet_freighters && (
                <span className="text-[11px] text-[var(--afcfta-muted)] flex items-center gap-1">
                  <Plane className="w-3 h-3" /> {operator.fleet_freighters} avions cargo
                </span>
              )}
              {operator.network_km && (
                <span className="text-[11px] text-[var(--afcfta-muted)] flex items-center gap-1">
                  <Train className="w-3 h-3" /> {operator.network_km.toLocaleString('fr-FR')} km
                </span>
              )}
              {operator.market_share_africa_pct && (
                <span className="text-[11px] text-[var(--gold)] flex items-center gap-1">
                  <Star className="w-3 h-3" /> {operator.market_share_africa_pct}% part de marché Afrique
                </span>
              )}
              {operator.africa_offices_count && (
                <span className="text-[11px] text-[var(--afcfta-muted)] flex items-center gap-1">
                  <Building2 className="w-3 h-3" /> {operator.africa_offices_count} bureaux Afrique
                </span>
              )}
              {operator.iata_accredited && (
                <span className="text-[11px] text-[var(--success)] flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Agréé IATA
                </span>
              )}
              {operator.fiata_member && (
                <span className="text-[11px] text-[var(--info)] flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Membre FIATA
                </span>
              )}
            </div>

            {/* Quick contacts row */}
            {hasContacts && !expanded && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {operator.contacts.phone && (
                  <ContactChip icon={Phone} value={operator.contacts.phone} href={`tel:${operator.contacts.phone}`} />
                )}
                {operator.contacts.email && (
                  <ContactChip icon={Mail} value={operator.contacts.email} href={`mailto:${operator.contacts.email}`} />
                )}
                {operator.contacts.website && (
                  <a href={operator.contacts.website} target="_blank" rel="noreferrer">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs
                      bg-[color-mix(in_srgb,var(--info)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--info)_30%,transparent)] text-[var(--info)] hover:text-[var(--info)] transition-colors">
                      <ExternalLink className="w-3 h-3" />
                      Site web
                    </span>
                  </a>
                )}
              </div>
            )}

            {/* Presence countries (first 6) */}
            {presenceList.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {presenceList.slice(0, expanded ? 50 : 6).map(iso => (
                  <CountryBadge key={iso} iso={iso} />
                ))}
                {!expanded && presenceList.length > 6 && (
                  <span className="text-[11px] text-[var(--afcfta-muted)] px-2 py-0.5">
                    +{presenceList.length - 6} pays
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Expand button */}
        {hasContacts && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setExpanded(!expanded)}
            className="w-full mt-3 h-7 text-xs text-[var(--afcfta-muted)] hover:text-[var(--text)] border border-[var(--overlay-border)] rounded-lg"
          >
            {expanded ? (
              <><ChevronUp className="w-3 h-3 mr-1" />Masquer contacts</>
            ) : (
              <><ChevronDown className="w-3 h-3 mr-1" />Voir tous les contacts</>
            )}
          </Button>
        )}

        {/* Full contacts when expanded */}
        {expanded && hasContacts && (
          <ContactsBlock contacts={operator.contacts} />
        )}

        {/* Services list */}
        {expanded && operator.services && (
          <div className="mt-3">
            <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">Services</div>
            <div className="flex flex-wrap gap-1">
              {operator.services.map(s => (
                <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-[var(--overlay)] border border-[var(--overlay-border)] text-[var(--text)]">{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* Africa terminals for port operators */}
        {expanded && operator.africa_terminals && (
          <div className="mt-3">
            <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">Terminaux africains</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
              {operator.africa_terminals.map((t, i) => (
                <div key={i} className="text-[11px] text-[var(--afcfta-muted)] flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--overlay)]">
                  <Anchor className="w-2.5 h-2.5 text-[var(--atlantic)] flex-shrink-0" />
                  <span>{t.port} ({t.country})</span>
                  {t.teu_capacity && <span className="text-[var(--afcfta-muted)]">— {(t.teu_capacity/1000).toFixed(0)}K TEU</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Africa services for shipping lines */}
        {expanded && operator.africa_services && (
          <div className="mt-3">
            <div className="text-[11px] text-[var(--afcfta-muted)] mb-1">Services Afrique</div>
            <div className="flex flex-wrap gap-1">
              {operator.africa_services.map(s => (
                <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-[var(--overlay)] border border-[var(--overlay-border)] text-[var(--text)]">{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* Certifications */}
        {expanded && operator.certifications && (
          <div className="mt-2 flex flex-wrap gap-1">
            {operator.certifications.map(c => (
              <span key={c} className="text-[11px] px-2 py-0.5 rounded-full bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--success)_30%,transparent)] text-[var(--success)]">
                <ShieldCheck className="w-2.5 h-2.5 inline mr-0.5" />{c}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function IntervenantsTab({ language = 'fr' }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeCategory, setActiveCategory] = useState('ALL');
  const [selectedCountry, setSelectedCountry] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchOperators();
  }, []);

  const fetchOperators = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/logistics/operators`);
      setData(res.data.operators);
      setSummary(res.data.summary);
    } catch (err) {
      console.error('Erreur chargement intervenants:', err);
      setError('Impossible de charger les intervenants logistiques.');
    } finally {
      setLoading(false);
    }
  };

  const getAllOperators = () => {
    if (!data) return [];
    const all = [];
    Object.entries(data).forEach(([cat, ops]) => {
      ops.forEach(op => all.push({ ...op, category: cat }));
    });
    return all;
  };

  const getFilteredOperators = () => {
    const all = getAllOperators();
    return all.filter(op => {
      const matchCat = activeCategory === 'ALL' || op.category === activeCategory;
      const presence = op.africa_presence || op.countries || (op.country_iso ? [op.country_iso] : []);
      const matchCountry = selectedCountry === 'ALL' || presence.includes(selectedCountry);
      const q = searchQuery.toLowerCase();
      const matchSearch = !q
        || op.name?.toLowerCase().includes(q)
        || op.hq?.toLowerCase().includes(q)
        || op.type_label?.toLowerCase().includes(q)
        || JSON.stringify(op.contacts || {}).toLowerCase().includes(q);
      return matchCat && matchCountry && matchSearch;
    });
  };

  const filtered = getFilteredOperators();

  // Group by category for display
  const groupedFiltered = {};
  filtered.forEach(op => {
    const cat = op.category;
    if (!groupedFiltered[cat]) groupedFiltered[cat] = [];
    groupedFiltered[cat].push(op);
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-2 border-[var(--gold)] border-t-transparent rounded-full" />
        <span className="ml-3 text-[var(--afcfta-muted)] text-sm">Chargement des intervenants logistiques...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16 text-[var(--danger)]">
        <p>{error}</p>
        <Button onClick={fetchOperators} className="mt-3">Réessayer</Button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header Section - Compact */}
      <div className="flex items-center gap-3 bg-[image:var(--card-grad)] border border-[var(--afcfta-border)] text-[var(--text)] p-4 rounded-xl shadow-lg">
        <div className="w-10 h-10 bg-[var(--overlay)] rounded-lg flex items-center justify-center">
          <Users className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold">
            {language === 'en' ? 'Logistics Operators' : 'Intervenants logistiques'}
          </h2>
          <p className="text-[var(--info)] text-sm">
            {language === 'en'
              ? 'Operators and stakeholders of the African logistics chain'
              : 'Opérateurs et acteurs de la chaîne logistique africaine'}
          </p>
        </div>
      </div>

      {/* Summary banner */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Object.entries(summary.by_category).map(([cat, count]) => {
            const meta = CATEGORY_META[cat];
            if (!meta) return null;
            const Icon = meta.icon;
            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(activeCategory === cat ? 'ALL' : cat)}
                className={`p-3 rounded-xl border text-left transition-all duration-150 hover:scale-[1.02]
                  ${activeCategory === cat ? 'ring-1 ring-white/20' : ''}`}
                style={{
                  background: meta.bg,
                  borderColor: activeCategory === cat ? 'rgba(212,175,55,0.4)' : meta.border,
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Icon className="w-4 h-4 text-[var(--text)]" />
                  <span className="text-xl font-bold text-[var(--text)]">{count}</span>
                </div>
                <div className="text-[11px] text-[var(--afcfta-muted)] leading-tight">{meta.label}</div>
              </button>
            );
          })}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center p-3 rounded-xl border border-[var(--overlay-border)] bg-[var(--overlay)]">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--afcfta-muted)]" />
          <input
            type="text"
            placeholder="Rechercher un opérateur, une ville, un contact..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg bg-[var(--overlay)] border border-[var(--overlay-border)]
              text-[var(--text)] placeholder:text-[var(--afcfta-muted)] focus:outline-none focus:border-[color-mix(in_srgb,var(--gold)_40%,transparent)]"
          />
        </div>
        <select
          value={selectedCountry}
          onChange={e => setSelectedCountry(e.target.value)}
          className="px-3 py-2 text-sm rounded-lg bg-[var(--overlay)] border border-[var(--overlay-border)] text-[var(--text)]
            focus:outline-none focus:border-[color-mix(in_srgb,var(--gold)_40%,transparent)] cursor-pointer"
        >
          {Object.entries(COUNTRY_LABELS).map(([iso, label]) => (
            <option key={iso} value={iso} className="bg-[var(--afcfta-card)]">{label}</option>
          ))}
        </select>
        {(activeCategory !== 'ALL' || selectedCountry !== 'ALL' || searchQuery) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setActiveCategory('ALL'); setSelectedCountry('ALL'); setSearchQuery(''); }}
            className="text-xs text-[var(--afcfta-muted)] hover:text-[var(--text)] border border-[var(--overlay-border)]"
          >
            Réinitialiser
          </Button>
        )}
        <span className="text-xs text-[var(--afcfta-muted)] ml-auto">
          {filtered.length} intervenant{filtered.length > 1 ? 's' : ''} trouvé{filtered.length > 1 ? 's' : ''}
        </span>
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveCategory('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border
            ${activeCategory === 'ALL'
              ? 'bg-[color-mix(in_srgb,var(--gold)_14%,var(--afcfta-card))] border-[color-mix(in_srgb,var(--gold)_40%,transparent)] text-[var(--gold)]'
              : 'bg-[var(--overlay)] border-[var(--overlay-border)] text-[var(--afcfta-muted)] hover:text-[var(--text)]'}`}
        >
          <Globe className="w-3 h-3 inline mr-1" />
          Tous
        </button>
        {Object.entries(CATEGORY_META).map(([key, meta]) => {
          const Icon = meta.icon;
          return (
            <button
              key={key}
              onClick={() => setActiveCategory(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border
                ${activeCategory === key
                  ? 'text-[var(--text)]'
                  : 'bg-[var(--overlay)] border-[var(--overlay-border)] text-[var(--afcfta-muted)] hover:text-[var(--text)]'}`}
              style={activeCategory === key ? { background: meta.bg, borderColor: meta.border } : {}}
            >
              <Icon className="w-3 h-3 inline mr-1" />
              {meta.label.split(' / ')[0].split(' &')[0]}
            </button>
          );
        })}
      </div>

      {/* Operators list */}
      {Object.keys(groupedFiltered).length === 0 ? (
        <div className="text-center py-12 text-[var(--afcfta-muted)]">
          <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p>Aucun intervenant trouvé pour ces critères.</p>
        </div>
      ) : (
        Object.entries(groupedFiltered).map(([cat, ops]) => {
          const meta = CATEGORY_META[cat] || { label: cat, icon: Globe, bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)', badge: '' };
          const Icon = meta.icon;
          return (
            <div key={cat} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-[var(--overlay-border)]">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: meta.bg }}>
                  <Icon className="w-4 h-4 text-[var(--text)]" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text)]">{meta.label}</h3>
                  <p className="text-xs text-[var(--afcfta-muted)]">{meta.desc}</p>
                </div>
                <Badge className={`ml-auto text-[11px] border ${meta.badge}`}>
                  {ops.length} opérateur{ops.length > 1 ? 's' : ''}
                </Badge>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {ops.map(op => (
                  <OperatorCard key={op.id || op.name} operator={op} catMeta={meta} />
                ))}
              </div>
            </div>
          );
        })
      )}

      {/* Data sources footer */}
      <div className="text-center text-xs text-[var(--afcfta-muted)] pt-4 border-t border-[var(--overlay-border)]">
        Sources : Sites officiels des opérateurs · Lloyd's List · IATA · BIMCO · UNCTAD Maritime Transport Review 2024 · World Bank LPI 2023
        <br />Données mises à jour : Avril 2025 — Données réelles, aucune donnée générique
      </div>
    </div>
  );
}
