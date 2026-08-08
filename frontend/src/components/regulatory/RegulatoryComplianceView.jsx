import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Alert, AlertTitle, AlertDescription } from '../ui/alert';

// Composant PRÉSENTIEL réutilisable : rend un objet `compliance` déjà chargé
// (formalités d'importation + prestataires/mandataires + frais) sans effectuer
// lui-même d'appel réseau ni gérer de sélecteur de pays. Il est alimenté :
//   • par le calculateur, via result.regulatory_compliance (pays de destination) ;
//   • par l'onglet réglementation autonome, via le sélecteur de pays.
// Les frais y sont affichés à titre INFORMATIF et STRICTEMENT SÉPARÉ des droits
// et taxes : ce composant n'additionne jamais rien au coût douanier.

// Miroir du backend _ACTIVE_MANDATE_STATUSES (regulatory_compliance_service.py) :
// seuls ces statuts constituent un mandat confirmé et actuellement actif.
const ACTIVE_MANDATE_STATUSES = new Set(['CONFIRMED_TIME_LIMITED', 'CONFIRMED_UNDATED_END']);

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

const TRANSPORT_MODE_LABELS = {
  fr: { MARITIME: 'Maritime', AERIEN: 'Aérien', ROUTIER: 'Routier', FERROVIAIRE: 'Ferroviaire', MULTIMODAL: 'Multimodal' },
  en: { MARITIME: 'Maritime', AERIEN: 'Air', ROUTIER: 'Road', FERROVIAIRE: 'Rail', MULTIMODAL: 'Multimodal' },
};

const TEXTS = {
  fr: {
    disclaimer:
      "Simulation informative — non opposable à l'administration douanière. Un prestataire privé est présenté uniquement comme acteur d'exécution dans la limite d'un mandat documenté.",
    searchPlaceholder: 'Mesure, prestataire, document, code SH…',
    searchLabel: 'Filtrer les formalités affichées',
    transportFilterLabel: 'Mode de transport',
    allTransportModes: 'Tous les modes',
    noMeasures: 'Aucune formalité ne correspond à ce filtre.',
    noData: "Aucune formalité réglementaire source n'est encore publiée pour ce pays (NOT_AVAILABLE — jamais fabriquée).",
    authority: 'Autorité',
    platform: 'Plateforme',
    legalReference: 'Référence légale',
    documents: 'Documents',
    fees: 'Frais réglementaires',
    feesNotAvailable: 'Non disponible (non fabriqué)',
    mandatedActors: 'Prestataires mandatés',
    historicalActors: 'Mandats non actifs — terminés ou non confirmés (historique)',
    mandatingAuthority: 'Autorité mandante',
    mandateDuration: 'Durée',
    deliveredDocument: 'Document délivré',
    evidence: 'Preuves datées',
    asOf: 'Situation au',
    products: 'Produits',
    transport: 'Transport',
    mandatedActorStatus: 'Prestataire mandaté',
    authorizedFees: 'Frais autorisés du prestataire',
    mandatedActorStatusNotApplicable:
      "Aucun prestataire mandaté à ce jour : la source confirme que l'administration opère cette formalité directement.",
    mandatedActorStatusNotAvailable:
      "Aucun prestataire actuellement actif confirmé par une source — l'absence de prestataire n'est pas établie pour autant.",
  },
  en: {
    disclaimer:
      'Informative simulation — not opposable to customs administration. A private provider is presented only as an execution actor within the limit of a documented mandate.',
    searchPlaceholder: 'Measure, provider, document, HS code…',
    searchLabel: 'Filter displayed formalities',
    transportFilterLabel: 'Transport mode',
    allTransportModes: 'All modes',
    noMeasures: 'No formality matches this filter.',
    noData: 'No source-bound regulatory formality has been published yet for this country (NOT_AVAILABLE — never fabricated).',
    authority: 'Authority',
    platform: 'Platform',
    legalReference: 'Legal reference',
    documents: 'Documents',
    fees: 'Regulatory fees',
    feesNotAvailable: 'Not available (never fabricated)',
    mandatedActors: 'Mandated providers',
    historicalActors: 'Non-active mandates — terminated or unconfirmed (history)',
    mandatingAuthority: 'Mandating authority',
    mandateDuration: 'Duration',
    deliveredDocument: 'Delivered document',
    evidence: 'Dated evidence',
    asOf: 'As of',
    products: 'Products',
    transport: 'Transport',
    mandatedActorStatus: 'Mandated provider',
    authorizedFees: 'Provider authorized fees',
    mandatedActorStatusNotApplicable:
      'No mandated provider to date: the source confirms the administration operates this formality directly.',
    mandatedActorStatusNotAvailable:
      "No currently active provider confirmed by a source — the absence of a provider isn't established either.",
  },
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

// N'autorise que http(s) pour tout lien externe rendu depuis des données
// sourcées : évite qu'une URL malformée (javascript:, data:) ne devienne un
// vecteur XSS.
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
  return false;
}

function ActorCard({ actor, t }) {
  const feesUnknown = !actor.authorized_fees || actor.authorized_fees_status === 'NOT_AVAILABLE';
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
      <div>
        <span className="font-semibold text-slate-400">{t.authorizedFees}: </span>
        {feesUnknown ? (
          <span className="italic text-slate-500">{t.feesNotAvailable}</span>
        ) : (
          <span className="text-slate-200">{actor.authorized_fees}</span>
        )}
      </div>
      {!!(actor.mandate_evidence || []).length && (
        <div>
          <span className="font-semibold text-slate-400">{t.evidence}: </span>
          {actor.mandate_evidence.map((ev, idx) => (
            <React.Fragment key={ev.url || idx}>
              {idx > 0 && ' · '}
              {safeHref(ev.url) ? (
                <a href={safeHref(ev.url)} target="_blank" rel="noopener noreferrer" className="text-amber-400 underline">
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

function MeasureCard({ measure, t, transportLabels }) {
  const activeActors = (measure.mandated_actors || []).filter((a) => ACTIVE_MANDATE_STATUSES.has(a.mandate_status));
  const historicalActors = (measure.mandated_actors || []).filter((a) => !ACTIVE_MANDATE_STATUSES.has(a.mandate_status));

  return (
    <Card className="border border-slate-700 bg-slate-900/60">
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
            {(measure.transport_modes || []).map((m) => transportLabels[m] || m).join(', ') || measure.transport}
          </div>
          <div>
            <span className="font-semibold text-slate-400">{t.fees}: </span>
            {measure.fees_status === 'NOT_AVAILABLE' ? (
              <span className="italic text-slate-500">{t.feesNotAvailable}</span>
            ) : (
              measure.fees
            )}
          </div>
        </div>

        {measure.platform && (
          <div>
            <span className="font-semibold text-slate-400">{t.platform}: </span>
            {safeHref(measure.platform) ? (
              <a href={safeHref(measure.platform)} target="_blank" rel="noopener noreferrer" className="text-amber-400 underline">
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
}

export default function RegulatoryComplianceView({ compliance, language = 'fr', showFilters = true }) {
  const t = TEXTS[language] || TEXTS.fr;
  const transportLabels = TRANSPORT_MODE_LABELS[language] || TRANSPORT_MODE_LABELS.fr;
  const [searchQuery, setSearchQuery] = useState('');
  const [transportFilter, setTransportFilter] = useState('ALL');

  const measures = compliance?.measures || [];

  const filteredMeasures = useMemo(
    () =>
      measures.filter(
        (m) => matchesSearch(m, searchQuery) && matchesTransportFilter(m, transportFilter)
      ),
    [measures, searchQuery, transportFilter]
  );

  if (!compliance || measures.length === 0) {
    return <p className="text-slate-400 text-sm italic">{t.noData}</p>;
  }

  return (
    <div className="space-y-4">
      <Alert>
        <AlertTitle>{language === 'fr' ? 'Avertissement' : 'Disclaimer'}</AlertTitle>
        <AlertDescription>{compliance.disclaimer || t.disclaimer}</AlertDescription>
      </Alert>

      {showFilters && (
        <div className="flex flex-wrap gap-3">
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
      )}

      {compliance.as_of && (
        <p className="text-xs text-slate-500">
          {t.asOf} {compliance.as_of}
        </p>
      )}

      {filteredMeasures.length === 0 && <p className="text-slate-400 text-sm italic">{t.noMeasures}</p>}

      {filteredMeasures.map((measure) => (
        <MeasureCard key={measure.record_id} measure={measure} t={t} transportLabels={transportLabels} />
      ))}
    </div>
  );
}
