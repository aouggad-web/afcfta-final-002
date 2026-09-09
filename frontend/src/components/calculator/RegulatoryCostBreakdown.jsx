import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { AlertTriangle, Landmark, Info, ArrowUpRight, ArrowDownLeft } from 'lucide-react';

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
    verified: fr ? 'VÉRIFIÉ (source primaire)' : 'VERIFIED (primary source)',
    adValoremUnit: fr ? "dans l'unité de la valeur saisie" : 'in the entered value unit',
    conditions: fr ? 'Conditions' : 'Conditions',
    source: fr ? 'Source' : 'Source',
    between: fr ? 'entre' : 'between',
    and: fr ? 'et' : 'and',
    ofFob: fr ? 'du FOB' : 'of FOB',
    // Volets import / export
    exportStageTitle: fr
      ? "Formalités à l'export (amont — pays d'origine)"
      : 'Export-side formalities (upstream — country of origin)',
    exportStageDesc: fr
      ? "Accomplies avant embarquement dans le pays d'origine, à la charge de l'exportateur."
      : 'Completed before shipment in the country of origin, borne by the exporter.',
    importStageTitle: fr
      ? "Formalités à l'import (aval — pays de destination)"
      : 'Import-side formalities (downstream — country of destination)',
    importStageDesc: fr
      ? "Acquittées à l'arrivée dans le pays de destination, à la charge de l'importateur."
      : 'Paid on arrival in the destination country, borne by the importer.',
    publicScope: fr ? 'perçu public' : 'public levy',
    providerScope: fr ? 'prestataire privé' : 'private provider',
    explainTitle: fr ? "Import vs export : comment lire ces frais" : 'Import vs export: how to read these fees',
    explainBody: fr
      ? "Les formalités déléguées se répartissent en deux étapes de l'opération. À l'EXPORT (amont), les programmes de conformité (VOC, PVoC, CBCA, PECAE, PROGEC, PCEC) sont exécutés dans le pays d'origine AVANT l'embarquement et payés par l'exportateur — même s'ils sont exigés par le pays de destination. À l'IMPORT (aval), d'autres frais sont acquittés à destination par l'importateur (ex. redevance OCC en RDC, certificat SONCAP au Nigeria). Les frais du prestataire PRIVÉ restent distincts des perçus PUBLICS (organismes d'État)."
      : "Delegated formalities split into two stages of the operation. On the EXPORT side (upstream), conformity programmes (VOC, PVoC, CBCA, PECAE, PROGEC, PCEC) are carried out in the country of origin BEFORE shipment and paid by the exporter — even though required by the destination country. On the IMPORT side (downstream), other fees are paid at destination by the importer (e.g. OCC levy in DRC, SONCAP certificate in Nigeria). PRIVATE-provider fees remain distinct from PUBLIC levies (state bodies).",
    unconfirmedProvider: fr ? 'prestataire non confirmé' : 'provider unconfirmed',
    unconfirmedProviderNote: fr
      ? "Formalité obligatoire confirmée par une source, mais aucun prestataire actuellement actif ni frais n'est établi — l'absence de prestataire n'est pas démontrée pour autant. À ne pas confondre avec un frais nul."
      : 'Mandatory formality confirmed by a source, but no currently active provider or fee is established — the absence of a provider is not established either. Not to be read as a zero fee.',
  };
}

function ScopeTag({ item, t }) {
  if (item.provider_status === 'UNCONFIRMED') {
    return (
      <span className="text-[9px] px-1.5 py-0.5 rounded border bg-amber-600/15 text-amber-300 border-amber-500/40">
        {t.unconfirmedProvider}
      </span>
    );
  }
  const isPublic = item.scope === 'formality' || item.collector_type === 'STATE_BODY';
  return (
    <span
      className={`text-[9px] px-1.5 py-0.5 rounded border ${
        isPublic
          ? 'bg-slate-600/20 text-slate-300 border-slate-500/40'
          : 'bg-indigo-500/15 text-indigo-300 border-indigo-500/40'
      }`}
    >
      {isPublic ? t.publicScope : t.providerScope}
    </span>
  );
}

function StageBlock({ title, desc, icon: Icon, items, t, language }) {
  if (!items.length) return null;
  return (
    <div className="space-y-2">
      <div>
        <p className="text-sm font-semibold text-amber-300 flex items-center gap-2">
          <Icon className="w-4 h-4" /> {title}
        </p>
        <p className="text-[11px] text-slate-500 ml-6">{desc}</p>
      </div>
      {items.map((item, idx) => (
        <div key={idx} className="relative">
          <div className="absolute right-3 top-3 z-10">
            <ScopeTag item={item} t={t} />
          </div>
          <FeeLine item={item} t={t} language={language} />
        </div>
      ))}
    </div>
  );
}

function rangeText(item, t) {
  // Fourchette de montants (route-dépendante). Ad valorem → pas de devise imposée.
  const lo = fmt(item.calculated_amount_min, item.ad_valorem ? '' : item.currency);
  const hi = fmt(item.calculated_amount_max, item.ad_valorem ? '' : item.currency);
  if (lo == null || hi == null) return null;
  return `${t.between} ${lo} ${t.and} ${hi}`;
}

function pct(rate) {
  if (rate == null) return null;
  // Évite les artefacts de virgule flottante (0.0045*100 = 0.4500…07).
  return (rate * 100)
    .toFixed(4)
    .replace(/\.?0+$/, '')
    .replace('.', ',');
}

function rateBracket(item, t) {
  const rmin = pct(item.rate_min);
  const rmax = pct(item.rate_max);
  if (rmin == null || rmax == null) return null;
  return `${rmin}%–${rmax}% ${t.ofFob}`;
}

function FeeLine({ item, t, language }) {
  const computed = COMPUTED.has(item.fee_status);
  const amount = computed && !item.is_range ? fmt(item.calculated_amount, item.ad_valorem ? '' : item.currency) : null;
  const range = computed && item.is_range ? rangeText(item, t) : null;
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
          {item.conditions && (
            <p className="text-slate-500 text-[11px] mt-1 italic">
              {t.conditions}: {item.conditions}
            </p>
          )}
          {item.provider_status === 'UNCONFIRMED' && (
            <p className="text-amber-400/90 text-[11px] mt-1 italic">{t.unconfirmedProviderNote}</p>
          )}
        </div>
        <div className="text-right shrink-0">
          <div className="flex flex-col items-end gap-1">
            <Badge
              variant="outline"
              className={FEE_STATUS_STYLES[item.fee_status] || FEE_STATUS_STYLES.NOT_AVAILABLE}
            >
              {item.side === 'export' ? t.sideExport : t.sideImport}
            </Badge>
            {item.tier === 'VERIFIED_PRIMARY' && (
              <Badge variant="outline" className="bg-emerald-600/15 text-emerald-300 border-emerald-500/40 text-[9px]">
                {t.verified}
              </Badge>
            )}
          </div>
          <p className="mt-1 font-semibold">
            {range ? (
              <span className="text-emerald-300">{range}</span>
            ) : amount ? (
              <span className="text-emerald-300">{amount}</span>
            ) : (
              <span className="text-amber-300 italic">{t.toConfirm}</span>
            )}
          </p>
          {item.is_range && rateBracket(item, t) && (
            <p className="text-[10px] text-slate-400">{rateBracket(item, t)}</p>
          )}
          {item.ad_valorem && (range || amount) && (
            <p className="text-[10px] text-slate-500">{t.adValoremUnit}</p>
          )}
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

  // Regroupement par ÉTAPE logistique : export (amont) vs import (aval).
  const exportLines = rc.line_items.filter((i) => i.stage === 'export');
  const importLines = rc.line_items.filter((i) => i.stage !== 'export');

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

        {/* Encadré explicatif import vs export */}
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 p-3">
          <p className="text-sm font-semibold text-sky-200 flex items-center gap-2">
            <Info className="w-4 h-4" /> {t.explainTitle}
          </p>
          <p className="text-xs text-slate-300/90 mt-1">{t.explainBody}</p>
          <p className="text-[11px] text-slate-400 mt-2 flex items-start gap-2">
            <Info className="w-3.5 h-3.5 text-slate-500 shrink-0 mt-0.5" />
            <span>{t.separatedNote}</span>
          </p>
        </div>

        {/* Volet EXPORT (amont, pays d'origine) */}
        <StageBlock
          title={t.exportStageTitle}
          desc={t.exportStageDesc}
          icon={ArrowUpRight}
          items={exportLines}
          t={t}
          language={language}
        />

        {/* Volet IMPORT (aval, pays de destination) */}
        <StageBlock
          title={t.importStageTitle}
          desc={t.importStageDesc}
          icon={ArrowDownLeft}
          items={importLines}
          t={t}
          language={language}
        />

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
