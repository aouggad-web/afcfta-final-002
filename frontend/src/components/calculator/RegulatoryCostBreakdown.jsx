import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { AlertTriangle, Landmark, Building2, Info } from 'lucide-react';

// Composition du coût réglementaire — présente, en lignes distinctes, les droits
// et taxes PUBLICS puis les frais de formalité et de prestataire mandaté, et
// signale explicitement si le total reste partiel. Aucun montant inconnu n'est
// remplacé par zéro : il est affiché « montant à confirmer ».

const FEE_STATUS_STYLES = {
  CALCULABLE: 'bg-emerald-600/20 text-emerald-300 border-emerald-500/40',
  DOCUMENTED_FIXED_AMOUNT: 'bg-emerald-600/20 text-emerald-300 border-emerald-500/40',
  DOCUMENTED_PERCENTAGE: 'bg-emerald-600/20 text-emerald-300 border-emerald-500/40',
  PARTIAL: 'bg-amber-600/20 text-amber-300 border-amber-500/40',
  FEE_EXISTS_AMOUNT_NOT_AVAILABLE: 'bg-amber-600/20 text-amber-300 border-amber-500/40',
  NOT_AVAILABLE: 'bg-slate-600/20 text-slate-300 border-slate-500/40',
  NOT_APPLICABLE: 'bg-slate-600/20 text-slate-400 border-slate-600/40',
};

const COMPUTED = new Set(['CALCULABLE', 'DOCUMENTED_FIXED_AMOUNT', 'DOCUMENTED_PERCENTAGE']);

function safeHref(url) {
  if (!url) return undefined;
  try {
    const p = new URL(url, window.location.origin);
    return p.protocol === 'http:' || p.protocol === 'https:' ? url : undefined;
  } catch {
    return undefined;
  }
}

function fmt(amount, currency) {
  if (amount === null || amount === undefined) return null;
  const n = Number(amount).toLocaleString('fr-FR', { maximumFractionDigits: 2 });
  return currency ? `${n} ${currency}` : n;
}

function T(language) {
  const fr = language !== 'en';
  return {
    title: fr ? 'Composition du coût réglementaire' : 'Regulatory cost composition',
    desc: fr
      ? 'Droits et taxes publics, puis frais de formalité et de prestataire mandaté — séparés.'
      : 'Public duties and taxes, then formality and mandated-provider fees — kept separate.',
    customs: fr ? 'Droits & taxes publics' : 'Public duties & taxes',
    duty: fr ? 'Droits de douane' : 'Customs duties',
    vat: fr ? 'Taxes intérieures (TVA)' : 'Domestic taxes (VAT)',
    other: fr ? 'Autres prélèvements publics' : 'Other public levies',
    publicSubtotal: fr ? 'Sous-total droits & taxes' : 'Duties & taxes subtotal',
    formalityFees: fr ? 'Frais de formalités obligatoires' : 'Mandatory formality fees',
    providerFees: fr ? 'Frais du prestataire mandaté' : 'Mandated-provider fees',
    regulatoryTotal: fr ? 'Coût réglementaire total' : 'Total regulatory cost',
    estimatedTotal: fr ? 'Coût total estimé de l’opération' : 'Estimated total cost',
    toConfirm: fr ? 'montant à confirmer' : 'amount to be confirmed',
    partial: fr ? 'Partiel' : 'Partial',
    complete: fr ? 'Complet' : 'Complete',
    incompleteNote: fr
      ? "Cette opération est soumise à des frais dus au prestataire mandaté. Leur montant n’est pas disponible dans les sources actuellement vérifiées. Veuillez prendre attache avec le prestataire ou l’autorité compétente avant l’expédition."
      : 'This operation is subject to fees owed to the mandated provider. Their amount is not available in the currently verified sources. Please contact the provider or competent authority before shipping.',
    mandatingAuthority: fr ? 'Autorité mandante' : 'Mandating authority',
    provider: fr ? 'Prestataire' : 'Provider',
    service: fr ? 'Service' : 'Service',
    contact: fr ? 'Lien / contact' : 'Link / contact',
    sideImport: fr ? 'Import' : 'Import',
    sideExport: fr ? 'Export' : 'Export',
    separatedNote: fr
      ? 'Les frais du prestataire sont distincts des droits et taxes publics et ne sont jamais confondus avec eux.'
      : 'Provider fees are distinct from public duties and taxes and never merged with them.',
  };
}

function FeeLine({ item, t, language }) {
  const computed = COMPUTED.has(item.fee_status);
  const amount = computed ? fmt(item.calculated_amount, item.currency) : null;
  const href = safeHref(item.contact);
  return (
    <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-slate-200 font-medium truncate">{item.measure_name}</p>
          {item.actor_name && (
            <p className="text-slate-400 text-xs mt-0.5">
              {t.provider}: <span className="text-slate-300">{item.actor_name}</span>
            </p>
          )}
          {item.mandating_authority && (
            <p className="text-slate-400 text-xs">
              {t.mandatingAuthority}: <span className="text-slate-300">{item.mandating_authority}</span>
            </p>
          )}
          {item.service && <p className="text-slate-500 text-xs mt-0.5">{item.service}</p>}
          {href && (
            <p className="text-xs mt-0.5">
              {t.contact}:{' '}
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-amber-400 underline break-all">
                {item.contact}
              </a>
            </p>
          )}
        </div>
        <div className="text-right shrink-0">
          <Badge
            variant="outline"
            className={FEE_STATUS_STYLES[item.fee_status] || FEE_STATUS_STYLES.NOT_AVAILABLE}
          >
            {item.side === 'export' ? t.sideExport : t.sideImport}
          </Badge>
          <p className="mt-1 font-semibold">
            {amount ? (
              <span className="text-emerald-300">{amount}</span>
            ) : (
              <span className="text-amber-300 italic">{t.toConfirm}</span>
            )}
          </p>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5">{item.fee_status}</p>
        </div>
      </div>
    </div>
  );
}

export default function RegulatoryCostBreakdown({ result, language = 'fr' }) {
  const t = T(language);
  const rc = result?.regulatory_cost;
  if (!rc || !(rc.line_items || []).length) return null;

  const value = Number(result?.value) || 0;
  const duty = Number(result?.normal_tariff_amount) || 0;
  const vat = Number(result?.normal_vat_amount) || 0;
  const other =
    (Number(result?.normal_statistical_fee) || 0) +
    (Number(result?.normal_community_levy) || 0) +
    (Number(result?.normal_ecowas_levy) || 0) +
    (Number(result?.normal_other_taxes_total) || 0);
  const publicSubtotal = Number(result?.normal_total_cost) || duty + vat + other;

  const formalityLines = rc.line_items.filter((i) => i.scope === 'formality');
  const providerLines = rc.line_items.filter((i) => i.scope === 'provider');

  const regTotal = rc.regulatory_cost_total;
  const regCcy = rc.regulatory_cost_currency;
  const complete = rc.complete;

  return (
    <Card className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 border border-amber-500/30">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
              <Landmark className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <CardTitle className="text-lg text-white">{t.title}</CardTitle>
              <CardDescription className="text-slate-400">{t.desc}</CardDescription>
            </div>
          </div>
          <Badge
            variant="outline"
            className={complete ? FEE_STATUS_STYLES.CALCULABLE : FEE_STATUS_STYLES.PARTIAL}
          >
            {complete ? t.complete : t.partial}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Droits & taxes publics */}
        <div className="rounded-lg border border-slate-700 divide-y divide-slate-700/60">
          <Row label={t.duty} value={fmt(duty, '')} />
          {result?.normal_vat_amount != null && <Row label={t.vat} value={fmt(vat, '')} />}
          <Row label={t.other} value={fmt(other, '')} />
          <Row label={t.publicSubtotal} value={fmt(publicSubtotal, '')} strong />
        </div>

        {/* Séparation explicite (règle 7) */}
        <div className="flex items-start gap-2 text-xs text-slate-400">
          <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <span>{t.separatedNote}</span>
        </div>

        {/* Frais de formalités obligatoires */}
        {formalityLines.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-semibold text-amber-300 flex items-center gap-2">
              <Landmark className="w-4 h-4" /> {t.formalityFees}
            </p>
            {formalityLines.map((item, idx) => (
              <FeeLine key={`f-${idx}`} item={item} t={t} language={language} />
            ))}
          </div>
        )}

        {/* Frais du prestataire mandaté */}
        {providerLines.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-semibold text-amber-300 flex items-center gap-2">
              <Building2 className="w-4 h-4" /> {t.providerFees}
            </p>
            {providerLines.map((item, idx) => (
              <FeeLine key={`p-${idx}`} item={item} t={t} language={language} />
            ))}
          </div>
        )}

        {/* Coût réglementaire total */}
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-200">{t.regulatoryTotal}</span>
            <span className="text-sm font-bold text-amber-300">
              {regTotal != null ? fmt(regTotal, regCcy) : <span className="italic">{t.toConfirm}</span>}
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-sm font-semibold text-white">{t.estimatedTotal}</span>
            <span className="text-right">
              <span className="text-base font-bold text-white">{fmt(publicSubtotal, '')}</span>
              {regTotal != null && complete ? (
                <span className="text-emerald-300"> + {fmt(regTotal, regCcy)}</span>
              ) : (
                <span className="block text-xs text-amber-300 italic">
                  + {t.providerFees.toLowerCase()} : {t.toConfirm}
                </span>
              )}
            </span>
          </div>
        </div>

        {/* Message d'incomplétude (frais existants non chiffrés) */}
        {rc.has_unpriced_fees && (
          <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <p className="text-sm text-amber-200/90">{t.incompleteNote}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Row({ label, value, strong }) {
  return (
    <div className="flex items-center justify-between px-3 py-2">
      <span className={`text-sm ${strong ? 'font-semibold text-slate-200' : 'text-slate-400'}`}>{label}</span>
      <span className={`text-sm ${strong ? 'font-bold text-white' : 'text-slate-300'}`}>{value}</span>
    </div>
  );
}
