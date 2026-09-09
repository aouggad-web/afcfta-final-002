import React from 'react';

const STATUS_LABELS = {
  CALCULATION_UNAVAILABLE: 'Calcul indisponible — donnée indispensable manquante',
  REVIEW_REQUIRED: 'Revue requise — simulation à confirmer',
  INFORMATIVE_PARTIAL: 'Information documentaire partielle',
  INFORMATIVE_COMPLETE: 'Information documentaire complète',
};

// Compatibility for responses persisted before the documentary vocabulary migration.
const STATUS_ALIASES = {
  BLOCKED_BASE_TARIFF: 'CALCULATION_UNAVAILABLE',
  UNVERIFIED_SOURCE: 'REVIEW_REQUIRED',
  CONFLICT_REVIEW: 'REVIEW_REQUIRED',
  VERIFIED_COMPLETE: 'INFORMATIVE_COMPLETE',
  VERIFIED_PARTIAL: 'INFORMATIVE_PARTIAL',
  SOURCE_VERIFIED: 'OFFICIAL_SOURCE_IDENTIFIED',
  LEGALLY_DATED: 'EFFECTIVE_DATE_DOCUMENTED',
  PRODUCTION_READY: 'DOCUMENTED_SCOPE_READY',
};

const DIMENSION_LABELS = {
  source: 'Source',
  temporal_validity: 'Temporalité',
  classification: 'Classement',
  taxes_and_levies: 'Fiscalité',
  preference_and_origin: 'Préférence et origine',
  formalities: 'Formalités',
};

const DIMENSION_VALUE_LABELS = {
  DOCUMENTED: 'Documenté',
  PARTIAL: 'Partiel',
  UNVERIFIED: 'Non vérifié',
  NOT_AVAILABLE: 'Non disponible',
  NOT_APPLICABLE: 'Non applicable',
};

const DIMENSION_KEYS = Object.keys(DIMENSION_LABELS);
const DEFAULT_QUALITY_DIMENSIONS = {
  source: 'PARTIAL',
  temporal_validity: 'PARTIAL',
  classification: 'DOCUMENTED',
  taxes_and_levies: 'PARTIAL',
  preference_and_origin: 'UNVERIFIED',
  formalities: 'NOT_AVAILABLE',
};

const statusBadgeClass = (status) => {
  if (status === 'CALCULATION_UNAVAILABLE') return 'border-red-400/50 text-red-200';
  if (status === 'REVIEW_REQUIRED') return 'border-orange-400/50 text-orange-200';
  if (status === 'INFORMATIVE_COMPLETE') return 'border-emerald-400/40 text-emerald-200';
  return 'border-amber-400/40 text-amber-200';
};

const dimensionColor = (value) => {
  if (value === 'DOCUMENTED') return 'text-emerald-300';
  if (value === 'PARTIAL') return 'text-amber-300';
  if (value === 'UNVERIFIED') return 'text-amber-300';
  return 'text-slate-300';
};

const amountFor = (legal, key) => {
  const value = legal?.[key];
  if (value == null) return null;
  if (typeof value === 'number' || typeof value === 'string') return value;
  const direct = value.calculated_amount ?? value.amount ?? value.total;
  if (direct != null) return direct;
  if (typeof value === 'object') {
    const amounts = Object.values(value).map((item) => item?.calculated_amount ?? item?.amount).filter((item) => item != null);
    if (amounts.length) return amounts.reduce((sum, item) => sum + Number(item), 0);
  }
  return null;
};

/** Display the documentary-quality envelope returned by the calculator. */
export default function TariffDocumentationPanel({ result, language = 'fr' }) {
  const legal = result?.generic_legal_calculation || result?.kenya_legal_calculation || result?.legal_calculation || (result?.overall_status ? result : null);
  if (!legal) return null;

  const rawStatus = legal.overall_status || legal.status || legal.calculation_status || 'REVIEW_REQUIRED';
  const status = STATUS_ALIASES[rawStatus] || rawStatus;
  const blocked = status === 'CALCULATION_UNAVAILABLE';
  const amount = blocked
    ? null
    : status === 'REVIEW_REQUIRED'
      ? (legal.simulated_total ?? legal.verified_total ?? legal.total_payable)
      : (legal.verified_total ?? legal.total_payable);
  const base = legal.base_tariff || {};
  const components = legal.monetary_components || legal.amounts || [];
  const missing = legal.components_missing || legal.missing_elements || [];
  const source = legal.base_tariff_source_id || base.source_id || legal.source_id;
  const effective = legal.base_tariff_effective_from || base.effective_from;
  const remission = legal.remission_eligibility_status;
  const qualityDimensions = { ...DEFAULT_QUALITY_DIMENSIONS, ...(legal.quality_dimensions || {}) };

  return (
    <div className="mb-6 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4" data-testid="tariff-documentation-panel">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-semibold text-amber-300 text-sm">
          {language === 'fr' ? 'Qualité documentaire du calcul' : 'Calculation documentation quality'}
        </p>
        <span className={`rounded border px-2 py-1 text-xs font-semibold ${statusBadgeClass(status)}`}>
          {STATUS_LABELS[status] || status}
        </span>
      </div>
      <div className="mt-3 grid gap-2 text-xs text-amber-100/90 sm:grid-cols-2 lg:grid-cols-4">
        <span>Statut : <strong>{status}</strong></span>
        <span>Source : <strong>{source || 'non renseignée'}</strong></span>
        <span>Date d’effet : <strong>{effective || 'non établie'}</strong></span>
        <span>Niveau : <strong>{legal.technical_validation_status || base.status || 'STRUCTURE_VALIDATED'}</strong></span>
        {legal.base_cet_rate != null && <span>CET de base : <strong>{legal.base_cet_rate}%</strong></span>}
        {legal.override_applied != null && <span>Override : <strong>{legal.override_applied}%</strong></span>}
        {remission && <span>Remission : <strong>{remission}</strong></span>}
      </div>
      {blocked ? (
        <p className="mt-3 text-sm font-medium text-red-200">
          Donnée indispensable manquante : aucun total n’est affiché. {missing[0] || 'Le tarif de base n’est pas disponible.'}
        </p>
      ) : (
        <>
          {status === 'REVIEW_REQUIRED' && (
            <p className="mt-3 text-sm font-medium text-orange-200">
              Résultat affiché uniquement comme simulation à confirmer.
            </p>
          )}
          {amount != null && (
            <p className="mt-3 text-sm text-amber-100">
              Montant {status === 'REVIEW_REQUIRED' ? 'simulé — à confirmer' : 'informatif'} : <strong>{amount} {legal.currency_code || ''}</strong>
            </p>
          )}
        </>
      )}
      <p className="mt-2 text-xs font-medium text-amber-200">
        Simulation informative — non opposable à l’administration douanière.
      </p>
      {components.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs">
          {components.map((component, index) => {
            const rawComponentStatus = component.documentation_status || component.verification_status || component.status;
            const componentStatus = rawComponentStatus === 'VERIFIED' ? 'DOCUMENTED' : rawComponentStatus || 'UNVERIFIED';
            return (
              <span key={`${component.code || 'component'}-${index}`} className="rounded bg-slate-900/40 px-2 py-1 text-amber-100/80">
                {component.code || 'COMPOSANT'} : {componentStatus}
              </span>
            );
        })}
      </div>
      )}
      <p className="mt-3 text-xs text-amber-100/80">
        Simulation informative fondée sur les données disponibles. Elle ne remplace pas la confirmation administrative auprès de l’autorité compétente.
      </p>
      <details className="mt-4 rounded-lg border border-amber-400/20 bg-slate-900/20 p-3" open>
        <summary className="cursor-pointer text-sm font-semibold text-amber-100">Comprendre ce calcul</summary>
        <div className="mt-3 grid gap-2 text-xs text-amber-100/90 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ['Droits de douane', amountFor(legal, 'customs_duty')],
            ['VAT', amountFor(legal, 'vat')],
            ['Accises', amountFor(legal, 'excise')],
            ['Prélèvements', amountFor(legal, 'other_levies')],
            ['Préférence', legal.preference_status || legal.preferential_regime || 'non renseignée'],
            ['Origine déclarée', legal.origin || legal.exporting_country || 'non renseignée'],
            ['Date', legal.calculation_date || legal.source_date || 'non renseignée'],
          ].map(([label, value]) => (
            <span key={label}>{label} : <strong>{value == null ? 'non disponible' : String(value)}</strong></span>
          ))}
        </div>
        {(legal.sources_used || legal.source_authority || legal.source_title) && (
          <p className="mt-3 text-xs text-amber-100/80">
            Sources : <strong>{(legal.sources_used || [legal.source_authority, legal.source_title]).filter(Boolean).join(', ') || 'non renseignées'}</strong>
          </p>
        )}
        {legal.assumptions?.length > 0 && (
          <p className="mt-2 text-xs text-amber-100/80">Hypothèses : {legal.assumptions.join('; ')}</p>
        )}
      </details>
      <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-3">
        {DIMENSION_KEYS.map((key) => {
          const value = qualityDimensions[key] || 'NOT_AVAILABLE';
          return (
            <span key={key} className={dimensionColor(value)}>{DIMENSION_LABELS[key]} : <strong>{DIMENSION_VALUE_LABELS[value] || 'Non disponible'}</strong></span>
          );
        })}
      </div>
      {missing.length > 0 && (
        <div className="mt-3 text-xs text-amber-100/80">
          <p className="font-semibold">Éléments manquants</p>
          <ul className="mt-1 list-disc space-y-0.5 pl-5">
            {missing.slice(0, 6).map((item, index) => <li key={`${index}-${item}`}>{String(item)}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
