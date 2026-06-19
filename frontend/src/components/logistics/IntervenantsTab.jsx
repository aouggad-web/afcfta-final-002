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
    badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    desc: 'Grandes compagnies de transport maritime opérant sur les routes africaines',
  },
  port_operators: {
    label: 'Opérateurs portuaires',
    icon: Anchor,
    color: 'cyan',
    bg: 'rgba(6,182,212,0.1)',
    border: 'rgba(6,182,212,0.3)',
    badge: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
    desc: 'Gestionnaires de terminaux à conteneurs et ports africains',
  },
  transitaires: {
    label: 'Transitaires & Freight Forwarders',
    icon: Package,
    color: 'amber',
    bg: 'rgba(245,158,11,0.1)',
    border: 'rgba(245,158,11,0.3)',
    badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    desc: 'Commissionnaires de transport, organisateurs de fret, dédouanement',
  },
  rail_operators: {
    label: 'Opérateurs ferroviaires',
    icon: Train,
    color: 'green',
    bg: 'rgba(34,197,94,0.1)',
    border: 'rgba(34,197,94,0.3)',
    badge: 'bg-green-500/20 text-green-300 border-green-500/30',
    desc: 'Compagnies ferroviaires nationales et régionales africaines',
  },
  trucking_companies: {
    label: 'Transporteurs routiers',
    icon: Truck,
    color: 'orange',
    bg: 'rgba(249,115,22,0.1)',
    border: 'rgba(249,115,22,0.3)',
    badge: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    desc: 'Compagnies de transport routier et de distribution',
  },
  air_cargo: {
    label: 'Cargo aérien',
    icon: Plane,
    color: 'purple',
    bg: 'rgba(168,85,247,0.1)',
    border: 'rgba(168,85,247,0.3)',
    badge: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    desc: 'Compagnies cargo aérien opérant sur le continent africain',
  },
  customs_agents: {
    label: 'Douanes & Commissionnaires',
    icon: ShieldCheck,
    color: 'red',
    bg: 'rgba(239,68,68,0.1)',
    border: 'rgba(239,68,68,0.3)',
    badge: 'bg-red-500/20 text-red-300 border-red-500/30',
    desc: 'Autorités douanières et commissionnaires agréés',
  },
  regulatory_bodies: {
    label: 'Organismes de régulation',
    icon: Globe,
    color: 'slate',
    bg: 'rgba(100,116,139,0.1)',
    border: 'rgba(100,116,139,0.3)',
    badge: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
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
  TUN: '🇹🇳 Tunisie',
};

function ContactChip({ icon: Icon, value, href, color = 'gray' }) {
  if (!value) return null;
  const content = (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono
      bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 hover:text-white
      transition-colors cursor-pointer group`}
    >
      <Icon className="w-3 h-3 flex-shrink-0 text-gray-400 group-hover:text-white" />
      <span className="truncate max-w-[180px]">{value}</span>
    </span>
  );
  return href ? <a href={href} target="_blank" rel="noreferrer">{content}</a> : content;
}

function CountryBadge({ iso }) {
  const label = COUNTRY_LABELS[iso] || iso;
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px]
      bg-white/5 border border-white/10 text-gray-400">
      {label}
    </span>
  );
}

function ContactsBlock({ contacts }) {
  if (!contacts || Object.keys(contacts).length === 0) return null;
  const skip = ['website', 'portail', 'cargo_tracking', 'tracking'];
  const officeEntries = Object.entries(contacts).filter(([k]) => !skip.includes(k));

  return (
    <div className="space-y-2 mt-3">
      {contacts.website && (
        <a href={contacts.website} target="_blank" rel="noreferrer"
          className="inline-flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 underline underline-offset-2">
          <ExternalLink className="w-3 h-3" />
          {contacts.website.replace('https://', '').replace('http://', '')}
        </a>
      )}
      <div className="flex flex-wrap gap-1.5">
        {officeEntries.map(([key, val]) => {
          if (!val || typeof val !== 'object') return null;
          const { phone, email, address } = val;
          const label = key.replace(/_/g, ' ');
          return (
            <div key={key} className="flex-1 min-w-[200px] p-2 rounded-lg bg-white/3 border border-white/8">
              <div className="text-[10px] text-gray-500 uppercase tracking-wide mb-1 font-medium">{label}</div>
              <div className="flex flex-col gap-1">
                {phone && <ContactChip icon={Phone} value={phone} href={`tel:${phone}`} />}
                {email && <ContactChip icon={Mail} value={email} href={`mailto:${email}`} />}
                {address && <ContactChip icon={MapPin} value={address} />}
              </div>
            </div>
          );
        })}
      </div>
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
            <Icon className="w-4 h-4 text-gray-300" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h4 className="text-sm font-semibold text-white leading-tight">{operator.name}</h4>
                {operator.hq && (
                  <div className="flex items-center gap-1 mt-0.5">
                    <MapPin className="w-3 h-3 text-gray-500" />
                    <span className="text-xs text-gray-400">{operator.hq}</span>
                  </div>
                )}
              </div>
              <Badge className={`text-[10px] px-1.5 flex-shrink-0 border ${catMeta.badge}`}>
                {operator.type_label || operator.type}
              </Badge>
            </div>

            <div className="flex flex-wrap gap-2 mt-2">
              {operator.fleet_size && (
                <span className="text-[11px] text-gray-400 flex items-center gap-1">
                  <Truck className="w-3 h-3" /> {operator.fleet_size} véhicules
                </span>
              )}
              {operator.fleet_vessels && (
                <span className="text-[11px] text-gray-400 flex items-center gap-1">
                  <Ship className="w-3 h-3" /> {operator.fleet_vessels} navires
                </span>
              )}
              {operator.fleet_teu && (
                <span className="text-[11px] text-gray-400 flex items-center gap-1">
                  <Package className="w-3 h-3" /> {(operator.fleet_teu / 1000000).toFixed(1)}M TEU
                </span>
              )}
              {operator.fleet_freighters && (
                <span className="text-[11px] text-gray-400 flex items-center gap-1">
                  <Plane className="w-3 h-3" /> {operator.fleet_freighters} avions cargo
                </span>
              )}
              {operator.network_km && (
                <span className="text-[11px] text-gray-400 flex items-center gap-1">
                  <Train className="w-3 h-3" /> {operator.network_km.toLocaleString('fr-FR')} km
                </span>
              )}
              {operator.market_share_africa_pct && (
                <span className="text-[11px] text-amber-400 flex items-center gap-1">
                  <Star className="w-3 h-3" /> {operator.market_share_africa_pct}% part de marché Afrique
                </span>
              )}
              {operator.africa_offices_count && (
                <span className="text-[11px] text-gray-400 flex items-center gap-1">
                  <Building2 className="w-3 h-3" /> {operator.africa_offices_count} bureaux Afrique
                </span>
              )}
              {operator.iata_accredited && (
                <span className="text-[11px] text-green-400 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Agréé IATA
                </span>
              )}
              {operator.fiata_member && (
                <span className="text-[11px] text-blue-400 flex items-center gap-1">
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
                      bg-blue-500/10 border border-blue-500/20 text-blue-400 hover:text-blue-300 transition-colors">
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
                  <span className="text-[10px] text-gray-500 px-2 py-0.5">
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
            className="w-full mt-3 h-7 text-xs text-gray-400 hover:text-white border border-white/10 rounded-lg"
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
            <div className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Services</div>
            <div className="flex flex-wrap gap-1">
              {operator.services.map(s => (
                <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-gray-300">{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* Africa terminals for port operators */}
        {expanded && operator.africa_terminals && (
          <div className="mt-3">
            <div className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Terminaux africains</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
              {operator.africa_terminals.map((t, i) => (
                <div key={i} className="text-[11px] text-gray-400 flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/3">
                  <Anchor className="w-2.5 h-2.5 text-cyan-400 flex-shrink-0" />
                  <span>{t.port} ({t.country})</span>
                  {t.teu_capacity && <span className="text-gray-500">— {(t.teu_capacity/1000).toFixed(0)}K TEU</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Africa services for shipping lines */}
        {expanded && operator.africa_services && (
          <div className="mt-3">
            <div className="text-[10px] text-gray-500 uppercase tracking-wide mb-1">Services Afrique</div>
            <div className="flex flex-wrap gap-1">
              {operator.africa_services.map(s => (
                <span key={s} className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 border border-white/10 text-gray-300">{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* Certifications */}
        {expanded && operator.certifications && (
          <div className="mt-2 flex flex-wrap gap-1">
            {operator.certifications.map(c => (
              <span key={c} className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400">
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
        <div className="animate-spin w-8 h-8 border-2 border-[#D4AF37] border-t-transparent rounded-full" />
        <span className="ml-3 text-gray-400 text-sm">Chargement des intervenants logistiques...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16 text-red-400">
        <p>{error}</p>
        <Button onClick={fetchOperators} className="mt-3">Réessayer</Button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header Section - Compact */}
      <div className="flex items-center gap-3 bg-gradient-to-r from-[#1B232C] to-[#0F1419] border border-[rgba(212,175,55,0.2)] text-white p-4 rounded-xl shadow-lg">
        <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
          <Users className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold">
            {language === 'en' ? 'Logistics Operators' : 'Intervenants logistiques'}
          </h2>
          <p className="text-blue-100 text-sm">
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
                  <Icon className="w-4 h-4 text-gray-300" />
                  <span className="text-xl font-bold text-white">{count}</span>
                </div>
                <div className="text-[11px] text-gray-400 leading-tight">{meta.label}</div>
              </button>
            );
          })}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center p-3 rounded-xl border border-white/10 bg-white/3">
        <div className="flex-1 min-w-[200px] relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Rechercher un opérateur, une ville, un contact..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm rounded-lg bg-white/5 border border-white/10
              text-white placeholder-gray-500 focus:outline-none focus:border-[#D4AF37]/40"
          />
        </div>
        <select
          value={selectedCountry}
          onChange={e => setSelectedCountry(e.target.value)}
          className="px-3 py-2 text-sm rounded-lg bg-white/5 border border-white/10 text-gray-300
            focus:outline-none focus:border-[#D4AF37]/40 cursor-pointer"
        >
          {Object.entries(COUNTRY_LABELS).map(([iso, label]) => (
            <option key={iso} value={iso} className="bg-[#1B232C]">{label}</option>
          ))}
        </select>
        {(activeCategory !== 'ALL' || selectedCountry !== 'ALL' || searchQuery) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { setActiveCategory('ALL'); setSelectedCountry('ALL'); setSearchQuery(''); }}
            className="text-xs text-gray-400 hover:text-white border border-white/10"
          >
            Réinitialiser
          </Button>
        )}
        <span className="text-xs text-gray-500 ml-auto">
          {filtered.length} intervenant{filtered.length > 1 ? 's' : ''} trouvé{filtered.length > 1 ? 's' : ''}
        </span>
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveCategory('ALL')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border
            ${activeCategory === 'ALL'
              ? 'bg-[#D4AF37]/20 border-[#D4AF37]/40 text-[#D4AF37]'
              : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'}`}
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
                  ? 'text-white'
                  : 'bg-white/5 border-white/10 text-gray-400 hover:text-white'}`}
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
        <div className="text-center py-12 text-gray-500">
          <Users className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p>Aucun intervenant trouvé pour ces critères.</p>
        </div>
      ) : (
        Object.entries(groupedFiltered).map(([cat, ops]) => {
          const meta = CATEGORY_META[cat] || { label: cat, icon: Globe, bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)', badge: '' };
          const Icon = meta.icon;
          return (
            <div key={cat} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/10">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: meta.bg }}>
                  <Icon className="w-4 h-4 text-gray-300" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{meta.label}</h3>
                  <p className="text-xs text-gray-500">{meta.desc}</p>
                </div>
                <Badge className={`ml-auto text-[10px] border ${meta.badge}`}>
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
      <div className="text-center text-xs text-gray-600 pt-4 border-t border-white/5">
        Sources : Sites officiels des opérateurs · Lloyd's List · IATA · BIMCO · UNCTAD Maritime Transport Review 2024 · World Bank LPI 2023
        <br />Données mises à jour : Avril 2025 — Données réelles, aucune donnée générique
      </div>
    </div>
  );
}
