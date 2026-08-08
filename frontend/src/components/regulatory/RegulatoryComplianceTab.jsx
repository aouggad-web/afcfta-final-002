import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Alert, AlertTitle, AlertDescription } from '../ui/alert';
import { CSVExportButton, JSONExportButton } from '../common/ExportTools';
import RegulatoryQAPanel from './RegulatoryQAPanel';
import { regulatoryApi } from '../../services/api-v2';
import { AFRICAN_COUNTRIES } from '../../utils/countryCodes';
import { toast } from '../../hooks/use-toast';

// Statuts canoniques (issue #359/#361) → couleur distincte, jamais confondue
// avec une donnée active/vérifiée quand elle ne l'est pas.
const STATUS_STYLES = {
  DOCUMENTED: 'bg-emerald-600/20 text-emerald-300 border-emerald-500/40',
  VERIFIED_PRIMARY_TEXT: 'bg-emerald-600/20 text-emerald-300 border-emerald-500/40',
  PARTIAL: 'bg-amber-600/20 text-amber-300 border-amber-500/40',
  UNVERIFIED: 'bg-orange-600/20 text-orange-300 border-orange-500/40',
  REVIEW_REQUIRED: 'bg-red-600/20 text-red-300 border-red-500/40',
  NOT_AVAILABLE: 'bg-slate-600/20 text-slate-300 border-slate-500/40',
  NOT_APPLICABLE: 'bg-slate-600/20 text-slate-400 border-slate-600/40',
  TERMINATED: 'bg-red-700/20 text-red-300 border-red-600/40',
};

function StatusBadge({ status }) {
  if (!status) return null;
  const cls = STATUS_STYLES[status] || 'bg-slate-600/20 text-slate-300 border-slate-500/40';
  return (
    <Badge variant="outline" className={cls}>
      {status}
    </Badge>
  );
}

const TRANSPORT_MODE_LABELS = {
  fr: {
    MARITIME: 'Maritime',
    AERIEN: 'Aérien',
    ROUTIER: 'Routier',
    FERROVIAIRE: 'Ferroviaire',
    MULTIMODAL: 'Multimodal',
  },
  en: {
    MARITIME: 'Maritime',
    AERIEN: 'Air',
    ROUTIER: 'Road',
    FERROVIAIRE: 'Rail',
    MULTIMODAL: 'Multimodal',
  },
};

const TEXTS = {
  fr: {
    title: 'Formalités particulières et prestataires mandatés',
    description:
      "Contrôles obligatoires à l'importation et prestataires officiellement mandatés, par pays — distinct du calcul tarifaire ZLECAf/NPF.",
    disclaimer:
      "Simulation informative — non opposable à l'administration douanière. Un prestataire privé est présenté uniquement comme acteur d'exécution dans la limite d'un mandat documenté.",
    selectPlaceholder: '🔍 Choisir un pays',
    selectAriaLabel: 'Choisir un pays',
    unavailableCountries: (n) =>
      `${n} pays supplémentaires suivis par le registre maître mais sans dataset encore publié (NOT_AVAILABLE).`,
    loadError: 'Impossible de charger les données réglementaires',
    searchLabel: 'Filtrer les formalités affichées',
    searchPlaceholder: 'Mesure, prestataire, document, code SH…',
    transportFilterLabel: 'Mode de transport',
    allTransportModes: 'Tous les modes',
    noMeasures: 'Aucune formalité ne correspond à ce filtre.',
    selectCountryFirst: 'Sélectionnez un pays pour afficher ses formalités.',
    authority: 'Autorité',
    platform: 'Plateforme',
    legalReference: 'Référence légale',
    documents: 'Documents',
    fees: 'Frais réglementaires',
    feesNotAvailable: 'Non disponible (non fabriqué)',
    mandatedActors: 'Prestataires mandatés',
    historicalActors: 'Mandats terminés / remplacés (historique)',
    mandatingAuthority: 'Autorité mandante',
    mandateStatus: 'Statut du mandat',
    mandateDuration: 'Durée',
    deliveredDocument: 'Document délivré',
    evidence: 'Preuves datées',
    exportCsv: 'Exporter CSV',
    exportJson: 'Exporter JSON',
    asOf: 'Situation au',
    scope: 'Portée',
    products: 'Produits',
    transport: 'Transport',
    mandatedActorStatus: 'Prestataire mandaté',
    mandatedActorStatusNotApplicable:
      "Aucun prestataire mandaté à ce jour : la source confirme que l'administration opère cette formalité directement.",
    mandatedActorStatusNotAvailable:
      "Aucun prestataire actuellement actif confirmé par une source — l'absence de prestataire n'est pas établie pour autant.",
    csvColumns: {
      country: 'Pays',
      record_id: 'Identifiant',
      measure_name: 'Mesure',
      scope_type: 'Type de portée',
      verification_status: 'Statut',
      mandated_actor_status: 'Prestataire mandaté',
      authority: 'Autorité',
      transport: 'Transport',
    },
  },
  en: {
    title: 'Special import formalities & mandated service providers',
    description:
      'Mandatory import controls and officially mandated service providers, by country — distinct from the ZLECAf/MFN tariff calculator.',
    disclaimer:
      'Informative simulation — not opposable to customs administration. A private provider is presented only as an execution actor within the limit of a documented mandate.',
    selectPlaceholder: '🔍 Choose a country',
    selectAriaLabel: 'Choose a country',
    unavailableCountries: (n) =>
      `${n} additional countries tracked by the master registry but with no dataset published yet (NOT_AVAILABLE).`,
    loadError: 'Unable to load regulatory-compliance data',
    searchLabel: 'Filter displayed formalities',
    searchPlaceholder: 'Measure, provider, document, HS code…',
    transportFilterLabel: 'Transport mode',
    allTransportModes: 'All modes',
    noMeasures: 'No formality matches this filter.',
    selectCountryFirst: 'Select a country to view its formalities.',
    authority: 'Authority',
    platform: 'Platform',
    legalReference: 'Legal reference',
    documents: 'Documents',
    fees: 'Regulatory fees',
    feesNotAvailable: 'Not available (never fabricated)',
    mandatedActors: 'Mandated providers',
    historicalActors: 'Terminated / replaced mandates (history)',
    mandatingAuthority: 'Mandating authority',
    mandateStatus: 'Mandate status',
    mandateDuration: 'Duration',
    deliveredDocument: 'Delivered document',
    evidence: 'Dated evidence',
    exportCsv: 'Export CSV',
    exportJson: 'Export JSON',
    asOf: 'As of',
    scope: 'Scope',
    products: 'Products',
    transport: 'Transport',
    mandatedActorStatus: 'Mandated provider',
    mandatedActorStatusNotApplicable:
      'No mandated provider to date: the source confirms the administration operates this formality directly.',
    mandatedActorStatusNotAvailable:
      "No currently active provider confirmed by a source — the absence of a provider isn't established either.",
    csvColumns: {
      country: 'Country',
      record_id: 'Record ID',
      measure_name: 'Measure',
      scope_type: 'Scope type',
      verification_status: 'Status',
      mandated_actor_status: 'Mandated provider',
      authority: 'Authority',
      transport: 'Transport',
    },
  },
};

function countryLabel(iso3, language) {
  const entry = AFRICAN_COUNTRIES[iso3];
  if (!entry) return iso3;
  return `${entry.flag} ${language === 'fr' ? entry.name_fr : entry.name_en}`;
}

// N'autorise que http(s) pour tout lien externe rendu depuis des données
// sourcées : évite qu'une URL malformée (javascript:, data:) dans un JSON de
// données ne devienne un vecteur XSS.
function safeHref(url) {
  if (!url) return undefined;
  try {
    const parsed = new URL(url, window.location.origin);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? url : undefined;
  } catch {
    return undefined;
  }
}

function matchesSearch(measure, query) {
  if (!query) return true;
  const q = query.toLowerCase();
  const haystacks = [
    measure.measure_name,
    measure.measure_category,
    measure.products,
    measure.authority,
    ...(measure.documents || []),
    ...(measure.hs_codes_explicit || []),
    ...(measure.mandated_actors || []).map((a) => a.actor_name),
  ].filter(Boolean);
  return haystacks.some((h) => String(h).toLowerCase().includes(q));
}

function matchesTransportFilter(measure, mode) {
  if (!mode || mode === 'ALL') return true;
  if (Array.isArray(measure.transport_modes) && measure.transport_modes.length) {
    return measure.transport_modes.includes(mode);
  }
  // Fallback: no structured transport_modes yet for this measure (LOT 4 not
  // applied to this country) — never guess, exclude from a specific-mode filter.
  return false;
}

export default function RegulatoryComplianceTab({ language = 'fr' }) {
  const t = TEXTS[language] || TEXTS.fr;
  const transportLabels = TRANSPORT_MODE_LABELS[language] || TRANSPORT_MODE_LABELS.fr;

  const [supportedCountries, setSupportedCountries] = useState([]);
  const [totalTrackedCountries, setTotalTrackedCountries] = useState(0);
  const [selectedCountry, setSelectedCountry] = useState('');
  const [compliance, setCompliance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [transportFilter, setTransportFilter] = useState('ALL');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [countriesResp, registryCountriesResp] = await Promise.all([
          regulatoryApi.getSupportedCountries(),
          regulatoryApi.getMasterRegistryCountries().catch(() => null),
        ]);
        if (cancelled) return;
        setSupportedCountries(countriesResp?.countries || []);
        if (registryCountriesResp) {
          setTotalTrackedCountries(registryCountriesResp.total || 0);
        }
      } catch (error) {
        console.error('Error loading regulatory-compliance countries:', error);
        toast({
          title: t.loadError,
          description: String(error?.message || error),
          variant: 'destructive',
        });
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSelectCountry = async (iso3) => {
    setSelectedCountry(iso3);
    setCompliance(null);
    setLoading(true);
    try {
      const resp = await regulatoryApi.getCountryCompliance(iso3);
      setCompliance(resp?.regulatory_compliance || null);
    } catch (error) {
      console.error('Error loading country compliance:', error);
      toast({
        title: t.loadError,
        description: String(error?.message || error),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredMeasures = useMemo(() => {
    if (!compliance) return [];
    return compliance.measures.filter(
      (m) => matchesSearch(m, searchQuery) && matchesTransportFilter(m, transportFilter)
    );
  }, [compliance, searchQuery, transportFilter]);

  const csvRows = useMemo(
    () =>
      filteredMeasures.map((m) => ({
        country: selectedCountry,
        record_id: m.record_id,
        measure_name: m.measure_name,
        scope_type: m.scope_type || 'NOT_AVAILABLE',
        verification_status: m.verification_status,
        mandated_actor_status: m.mandated_actor_status || 'NOT_AVAILABLE',
        authority: m.authority,
        transport: (m.transport_modes || []).join(' / ') || m.transport,
      })),
    [filteredMeasures, selectedCountry]
  );

  const notYetPublished = Math.max(0, totalTrackedCountries - supportedCountries.length);

  return (
    <div className="space-y-6">
      <RegulatoryQAPanel language={language} />

      <Card className="shadow-xl border border-[rgba(212,175,55,0.2)] bg-gradient-to-br from-slate-800 to-slate-900">
        <CardHeader className="bg-gradient-to-r from-[#1B232C] to-[#15202A] border-b border-[rgba(212,175,55,0.14)]">
          <CardTitle className="text-2xl font-bold text-amber-400 flex items-center gap-2">
            <span>🛂</span>
            <span>{t.title}</span>
          </CardTitle>
          <CardDescription className="font-semibold text-slate-400">
            {t.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <AlertTitle>{language === 'fr' ? 'Avertissement' : 'Disclaimer'}</AlertTitle>
            <AlertDescription>{t.disclaimer}</AlertDescription>
          </Alert>

          <Select value={selectedCountry} onValueChange={handleSelectCountry}>
            <SelectTrigger
              aria-label={t.selectAriaLabel}
              className="text-lg font-semibold border border-[rgba(212,175,55,0.25)] focus:border-[rgba(212,175,55,0.5)]"
            >
              <SelectValue placeholder={t.selectPlaceholder} />
            </SelectTrigger>
            <SelectContent>
              {supportedCountries.map((iso3) => (
                <SelectItem key={iso3} value={iso3}>
                  {countryLabel(iso3, language)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {notYetPublished > 0 && (
            <p className="text-xs text-slate-400">{t.unavailableCountries(notYetPublished)}</p>
          )}
        </CardContent>
      </Card>

      {!selectedCountry && (
        <p className="text-slate-400 text-sm italic">{t.selectCountryFirst}</p>
      )}

      {loading && <p className="text-slate-400 text-sm">…</p>}

      {compliance && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-3 flex-1 min-w-[240px]">
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t.searchPlaceholder}
                aria-label={t.searchLabel}
                className="max-w-sm"
              />
              <Select value={transportFilter} onValueChange={setTransportFilter}>
                <SelectTrigger className="w-56" aria-label={t.transportFilterLabel}>
                  <SelectValue placeholder={t.transportFilterLabel} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">{t.allTransportModes}</SelectItem>
                  {Object.keys(transportLabels).map((mode) => (
                    <SelectItem key={mode} value={mode}>
                      {transportLabels[mode]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <CSVExportButton
                rows={csvRows}
                columns={Object.entries(t.csvColumns).map(([key, label]) => ({ key, label }))}
                filename={`regulatory-compliance-${selectedCountry}`}
                language={language}
              />
              <JSONExportButton
                data={compliance}
                filename={`regulatory-compliance-${selectedCountry}`}
                language={language}
              />
            </div>
          </div>

          {compliance.as_of && (
            <p className="text-xs text-slate-500">
              {t.asOf} {compliance.as_of}
            </p>
          )}

          {filteredMeasures.length === 0 && (
            <p className="text-slate-400 text-sm italic">{t.noMeasures}</p>
          )}

          {filteredMeasures.map((measure) => {
            const activeActors = (measure.mandated_actors || []).filter(
              (a) => a.mandate_status !== 'TERMINATED'
            );
            const historicalActors = (measure.mandated_actors || []).filter(
              (a) => a.mandate_status === 'TERMINATED'
            );

            return (
              <Card key={measure.record_id} className="border border-slate-700 bg-slate-900/60">
                <CardHeader>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <CardTitle className="text-lg text-amber-300">{measure.measure_name}</CardTitle>
                    <div className="flex gap-2 flex-wrap">
                      {measure.scope_type && <StatusBadge status={measure.scope_type} />}
                      <StatusBadge status={measure.verification_status} />
                    </div>
                  </div>
                  <CardDescription className="text-slate-300">{measure.scope}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-slate-300">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <span className="font-semibold text-slate-400">{t.authority}: </span>
                      {measure.authority}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-400">{t.products}: </span>
                      {measure.products}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-400">{t.mandatedActorStatus}: </span>
                      <StatusBadge status={measure.mandated_actor_status} />
                    </div>
                    <div>
                      <span className="font-semibold text-slate-400">{t.transport}: </span>
                      {(measure.transport_modes || []).map((m) => transportLabels[m] || m).join(', ') ||
                        measure.transport}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-400">{t.fees}: </span>
                      {measure.fees_status === 'NOT_AVAILABLE'
                        ? t.feesNotAvailable
                        : measure.fees}
                    </div>
                  </div>

                  {measure.platform && (
                    <div>
                      <span className="font-semibold text-slate-400">{t.platform}: </span>
                      {safeHref(measure.platform) ? (
                        <a
                          href={safeHref(measure.platform)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-amber-400 underline"
                        >
                          {measure.platform}
                        </a>
                      ) : (
                        measure.platform
                      )}
                    </div>
                  )}

                  <div>
                    <span className="font-semibold text-slate-400">{t.legalReference}: </span>
                    {measure.legal_reference}
                  </div>

                  {!!(measure.documents || []).length && (
                    <div>
                      <span className="font-semibold text-slate-400">{t.documents}: </span>
                      {measure.documents.join(' · ')}
                    </div>
                  )}

                  {!!activeActors.length && (
                    <div className="border-t border-slate-700 pt-3">
                      <p className="font-semibold text-amber-300 mb-2">{t.mandatedActors}</p>
                      {activeActors.map((actor) => (
                        <ActorCard key={actor.actor_name} actor={actor} t={t} />
                      ))}
                    </div>
                  )}

                  {!activeActors.length && measure.mandated_actor_status === 'NOT_APPLICABLE' && (
                    <p className="border-t border-slate-700 pt-3 text-xs text-slate-400 italic">
                      {t.mandatedActorStatusNotApplicable}
                    </p>
                  )}

                  {!activeActors.length && measure.mandated_actor_status === 'NOT_AVAILABLE' && (
                    <p className="border-t border-slate-700 pt-3 text-xs text-slate-400 italic">
                      {t.mandatedActorStatusNotAvailable}
                    </p>
                  )}

                  {!!historicalActors.length && (
                    <div className="border-t border-slate-700 pt-3">
                      <p className="font-semibold text-slate-400 mb-2">{t.historicalActors}</p>
                      {historicalActors.map((actor) => (
                        <ActorCard key={actor.actor_name} actor={actor} t={t} />
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function ActorCard({ actor, t }) {
  return (
    <div className="mb-3 p-3 rounded-lg bg-slate-800/60 border border-slate-700 text-xs text-slate-300 space-y-1">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold text-slate-200">{actor.actor_name}</span>
        <StatusBadge status={actor.mandate_status} />
      </div>
      <div>
        <span className="font-semibold text-slate-400">{t.mandatingAuthority}: </span>
        {actor.mandating_authority}
      </div>
      <div>
        <span className="font-semibold text-slate-400">{t.mandateDuration}: </span>
        {actor.mandate_duration}
      </div>
      <div>
        <span className="font-semibold text-slate-400">{t.deliveredDocument}: </span>
        {actor.delivered_document}
      </div>
      {!!(actor.mandate_evidence || []).length && (
        <div>
          <span className="font-semibold text-slate-400">{t.evidence}: </span>
          {actor.mandate_evidence.map((ev, idx) => (
            <React.Fragment key={ev.url || idx}>
              {idx > 0 && ' · '}
              {safeHref(ev.url) ? (
                <a
                  href={safeHref(ev.url)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-400 underline"
                >
                  {ev.date} — {ev.title}
                </a>
              ) : (
                <span>
                  {ev.date} — {ev.title}
                </span>
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
}
