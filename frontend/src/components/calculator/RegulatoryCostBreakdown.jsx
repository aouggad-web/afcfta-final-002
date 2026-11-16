import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { AlertTriangle, Landmark, Info, ArrowUpRight, ArrowDownLeft } from 'lucide-react';
import { pick } from '../../i18n/lang';

// Composition du coût réglementaire — présente, en lignes distinctes, les droits
// et taxes PUBLICS puis les frais de formalité et de prestataire mandaté, et
// signale explicitement si le total reste partiel. Aucun montant inconnu n'est
// remplacé par zéro : il est affiché « montant à confirmer ».

const FEE_STATUS_STYLES = {
  CALCULABLE: 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]',
  DOCUMENTED_FIXED_AMOUNT: 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]',
  DOCUMENTED_PERCENTAGE: 'bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)]',
  PARTIAL: 'bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]',
  FEE_EXISTS_AMOUNT_NOT_AVAILABLE: 'bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]',
  NOT_AVAILABLE: 'bg-[var(--overlay)] text-[var(--text)] border-[var(--afcfta-border)]',
  NOT_APPLICABLE: 'bg-[var(--overlay)] text-[var(--afcfta-muted)] border-[var(--afcfta-border)]',
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
  return {
    title: pick(language, 'Composition du coût réglementaire', 'Regulatory cost composition', 'مكونات التكلفة التنظيمية'),
    desc: pick(language, 'Droits et taxes publics, puis frais de formalité et de prestataire mandaté — séparés.', 'Public duties and taxes, then formality and mandated-provider fees — kept separate.', 'الرسوم والضرائب العامة، ثم رسوم الإجراءات ومقدم الخدمة المفوَّض — كلٌّ على حدة.'),
    customs: pick(language, 'Droits & taxes publics', 'Public duties & taxes', 'الرسوم والضرائب العامة'),
    duty: pick(language, 'Droits de douane', 'Customs duties', 'الرسوم الجمركية'),
    vat: pick(language, 'Taxes intérieures (TVA)', 'Domestic taxes (VAT)', 'الضرائب الداخلية (ضريبة القيمة المضافة)'),
    other: pick(language, 'Autres prélèvements publics', 'Other public levies', 'رسوم عامة أخرى'),
    publicSubtotal: pick(language, 'Sous-total droits & taxes', 'Duties & taxes subtotal', 'المجموع الفرعي للرسوم والضرائب'),
    formalityFees: pick(language, 'Frais de formalités obligatoires', 'Mandatory formality fees', 'رسوم الإجراءات الإلزامية'),
    providerFees: pick(language, 'Frais du prestataire mandaté', 'Mandated-provider fees', 'رسوم مقدم الخدمة المفوَّض'),
    regulatoryTotal: pick(language, 'Coût réglementaire total', 'Total regulatory cost', 'التكلفة التنظيمية الإجمالية'),
    estimatedTotal: pick(language, 'Coût total estimé de l’opération', 'Estimated total cost', 'التكلفة الإجمالية التقديرية للعملية'),
    toConfirm: pick(language, 'montant à confirmer', 'amount to be confirmed', 'المبلغ قيد التأكيد'),
    partial: pick(language, 'Partiel', 'Partial', 'جزئي'),
    complete: pick(language, 'Complet', 'Complete', 'كامل'),
    incompleteNote: pick(language, "Cette opération est soumise à des frais dus au prestataire mandaté. Leur montant n’est pas disponible dans les sources actuellement vérifiées. Veuillez prendre attache avec le prestataire ou l’autorité compétente avant l’expédition.", 'This operation is subject to fees owed to the mandated provider. Their amount is not available in the currently verified sources. Please contact the provider or competent authority before shipping.', "تخضع هذه العملية لرسوم مستحقة لمقدم الخدمة المفوَّض. ومبلغها غير متاح في المصادر المُتحقَّق منها حاليًا. يُرجى التواصل مع مقدم الخدمة أو السلطة المختصة قبل الشحن."),
    mandatingAuthority: pick(language, 'Autorité mandante', 'Mandating authority', 'السلطة المفوِّضة'),
    provider: pick(language, 'Prestataire', 'Provider', 'مقدم الخدمة'),
    service: pick(language, 'Service', 'Service', 'الخدمة'),
    contact: pick(language, 'Lien / contact', 'Link / contact', 'الرابط / جهة الاتصال'),
    sideImport: pick(language, 'Import', 'Import', 'استيراد'),
    sideExport: pick(language, 'Export', 'Export', 'تصدير'),
    separatedNote: pick(language, 'Les frais du prestataire sont distincts des droits et taxes publics et ne sont jamais confondus avec eux.', 'Provider fees are distinct from public duties and taxes and never merged with them.', 'رسوم مقدم الخدمة مستقلة عن الرسوم والضرائب العامة ولا تُدمج معها أبدًا.'),
    verified: pick(language, 'VÉRIFIÉ (source primaire)', 'VERIFIED (primary source)', 'مُتحقَّق منه (مصدر أولي)'),
    adValoremUnit: pick(language, "dans l'unité de la valeur saisie", 'in the entered value unit', "بوحدة القيمة المُدخلة"),
    conditions: pick(language, 'Conditions', 'Conditions', 'الشروط'),
    source: pick(language, 'Source', 'Source', 'المصدر'),
    between: pick(language, 'entre', 'between', 'بين'),
    and: pick(language, 'et', 'and', 'و'),
    ofFob: pick(language, 'du FOB', 'of FOB', 'من القيمة فوب (FOB)'),
    // Volets import / export
    exportStageTitle: pick(language, "Formalités à l'export (amont — pays d'origine)", 'Export-side formalities (upstream — country of origin)', "إجراءات التصدير (المرحلة السابقة — بلد المنشأ)"),
    exportStageDesc: pick(language, "Accomplies avant embarquement dans le pays d'origine, à la charge de l'exportateur.", 'Completed before shipment in the country of origin, borne by the exporter.', "تُنجَز قبل الشحن في بلد المنشأ، على عاتق المصدِّر."),
    importStageTitle: pick(language, "Formalités à l'import (aval — pays de destination)", 'Import-side formalities (downstream — country of destination)', "إجراءات الاستيراد (المرحلة اللاحقة — بلد المقصد)"),
    importStageDesc: pick(language, "Acquittées à l'arrivée dans le pays de destination, à la charge de l'importateur.", 'Paid on arrival in the destination country, borne by the importer.', "تُؤدّى عند الوصول إلى بلد المقصد، على عاتق المستورد."),
    publicScope: pick(language, 'perçu public', 'public levy', 'تحصيل عام'),
    providerScope: pick(language, 'prestataire privé', 'private provider', 'مقدم خدمة خاص'),
    explainTitle: pick(language, "Import vs export : comment lire ces frais", 'Import vs export: how to read these fees', "الاستيراد مقابل التصدير: كيف تُقرأ هذه الرسوم"),
    explainBody: pick(language, "Les formalités déléguées se répartissent en deux étapes de l'opération. À l'EXPORT (amont), les programmes de conformité (VOC, PVoC, CBCA, PECAE, PROGEC, PCEC) sont exécutés dans le pays d'origine AVANT l'embarquement et payés par l'exportateur — même s'ils sont exigés par le pays de destination. À l'IMPORT (aval), d'autres frais sont acquittés à destination par l'importateur (ex. redevance OCC en RDC, certificat SONCAP au Nigeria). Les frais du prestataire PRIVÉ restent distincts des perçus PUBLICS (organismes d'État).", "Delegated formalities split into two stages of the operation. On the EXPORT side (upstream), conformity programmes (VOC, PVoC, CBCA, PECAE, PROGEC, PCEC) are carried out in the country of origin BEFORE shipment and paid by the exporter — even though required by the destination country. On the IMPORT side (downstream), other fees are paid at destination by the importer (e.g. OCC levy in DRC, SONCAP certificate in Nigeria). PRIVATE-provider fees remain distinct from PUBLIC levies (state bodies).", "تتوزع الإجراءات المفوَّضة على مرحلتين من العملية. في التصدير (المرحلة السابقة)، تُنفَّذ برامج المطابقة (VOC وPVoC وCBCA وPECAE وPROGEC وPCEC) في بلد المنشأ قبل الشحن ويدفعها المصدِّر — حتى وإن كان بلد المقصد هو من يشترطها. وفي الاستيراد (المرحلة اللاحقة)، يؤدي المستورد رسومًا أخرى في بلد المقصد (مثل إتاوة OCC في جمهورية الكونغو الديمقراطية، وشهادة SONCAP في نيجيريا). وتبقى رسوم مقدم الخدمة الخاص مستقلة عن التحصيلات العامة (الهيئات الحكومية)."),
    unconfirmedProvider: pick(language, 'prestataire non confirmé', 'provider unconfirmed', 'مقدم خدمة غير مؤكَّد'),
    unconfirmedProviderNote: pick(language, "Formalité obligatoire confirmée par une source, mais aucun prestataire actuellement actif ni frais n'est établi — l'absence de prestataire n'est pas démontrée pour autant. À ne pas confondre avec un frais nul.", 'Mandatory formality confirmed by a source, but no currently active provider or fee is established — the absence of a provider is not established either. Not to be read as a zero fee.', "إجراء إلزامي يؤكده مصدر، لكن لم يثبت وجود مقدم خدمة نشط حاليًا ولا رسوم — كما لم يثبت غياب مقدم الخدمة. لا يُفهم على أنه رسم منعدم."),
  };
}

function ScopeTag({ item, t }) {
  if (item.provider_status === 'UNCONFIRMED') {
    return (
      <span className="text-[11px] px-1.5 py-0.5 rounded border bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
        {t.unconfirmedProvider}
      </span>
    );
  }
  const isPublic = item.scope === 'formality' || item.collector_type === 'STATE_BODY';
  return (
    <span
      className={`text-[11px] px-1.5 py-0.5 rounded border ${
        isPublic
          ? 'bg-[var(--overlay)] text-[var(--text)] border-[var(--afcfta-border)]'
          : 'bg-[color-mix(in_srgb,var(--violet)_12%,var(--afcfta-card))] text-[var(--violet)] border-[color-mix(in_srgb,var(--violet)_30%,transparent)]'
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
        <p className="text-sm font-semibold text-[var(--gold)] flex items-center gap-2">
          <Icon className="w-4 h-4" /> {title}
        </p>
        <p className="text-[11px] text-[var(--afcfta-muted)] ml-6">{desc}</p>
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
    <div className="p-3 rounded-lg bg-[var(--overlay)] border border-[var(--afcfta-border)] text-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[var(--text)] font-medium truncate">{item.measure_name}</p>
          {item.actor_name && (
            <p className="text-[var(--afcfta-muted)] text-xs mt-0.5">
              {t.provider}: <span className="text-[var(--text)]">{item.actor_name}</span>
            </p>
          )}
          {item.mandating_authority && (
            <p className="text-[var(--afcfta-muted)] text-xs">
              {t.mandatingAuthority}: <span className="text-[var(--text)]">{item.mandating_authority}</span>
            </p>
          )}
          {item.service && <p className="text-[var(--afcfta-muted)] text-xs mt-0.5">{item.service}</p>}
          {href && (
            <p className="text-xs mt-0.5">
              {t.contact}:{' '}
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-[var(--gold)] underline break-all">
                {item.contact}
              </a>
            </p>
          )}
          {item.conditions && (
            <p className="text-[var(--afcfta-muted)] text-[11px] mt-1 italic">
              {t.conditions}: {item.conditions}
            </p>
          )}
          {item.provider_status === 'UNCONFIRMED' && (
            <p className="text-[var(--gold)] text-[11px] mt-1 italic">{t.unconfirmedProviderNote}</p>
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
              <Badge variant="outline" className="bg-[color-mix(in_srgb,var(--success)_12%,var(--afcfta-card))] text-[var(--success)] border-[color-mix(in_srgb,var(--success)_30%,transparent)] text-[11px]">
                {t.verified}
              </Badge>
            )}
          </div>
          <p className="mt-1 font-semibold">
            {range ? (
              <span className="text-[var(--success)]">{range}</span>
            ) : amount ? (
              <span className="text-[var(--success)]">{amount}</span>
            ) : (
              <span className="text-[var(--gold)] italic">{t.toConfirm}</span>
            )}
          </p>
          {item.is_range && rateBracket(item, t) && (
            <p className="text-[11px] text-[var(--afcfta-muted)]">{rateBracket(item, t)}</p>
          )}
          {item.ad_valorem && (range || amount) && (
            <p className="text-[11px] text-[var(--afcfta-muted)]">{t.adValoremUnit}</p>
          )}
          <p className="text-[11px] text-[var(--afcfta-muted)] font-mono mt-0.5">{item.fee_status}</p>
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
    <Card className="bg-[image:var(--card-grad)] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
              <Landmark className="w-5 h-5 text-[var(--gold)]" />
            </div>
            <div>
              <CardTitle className="text-lg text-[var(--text)]">{t.title}</CardTitle>
              <CardDescription className="text-[var(--afcfta-muted)]">{t.desc}</CardDescription>
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
        <div className="rounded-lg border border-[var(--afcfta-border)] divide-y divide-[var(--afcfta-border)]">
          <Row label={t.duty} value={fmt(duty, '')} />
          {result?.normal_vat_amount != null && <Row label={t.vat} value={fmt(vat, '')} />}
          <Row label={t.other} value={fmt(other, '')} />
          <Row label={t.publicSubtotal} value={fmt(publicSubtotal, '')} strong />
        </div>

        {/* Encadré explicatif import vs export */}
        <div className="rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[color-mix(in_srgb,var(--info)_5%,var(--afcfta-card))] p-3">
          <p className="text-sm font-semibold text-[var(--info)] flex items-center gap-2">
            <Info className="w-4 h-4" /> {t.explainTitle}
          </p>
          <p className="text-xs text-[var(--text)]/90 mt-1">{t.explainBody}</p>
          <p className="text-[11px] text-[var(--afcfta-muted)] mt-2 flex items-start gap-2">
            <Info className="w-3.5 h-3.5 text-[var(--afcfta-muted)] shrink-0 mt-0.5" />
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
        <div className="rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_5%,var(--afcfta-card))] p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-[var(--text)]">{t.regulatoryTotal}</span>
            <span className="text-sm font-bold text-[var(--gold)]">
              {regTotal != null ? fmt(regTotal, regCcy) : <span className="italic">{t.toConfirm}</span>}
            </span>
          </div>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-sm font-semibold text-[var(--text)]">{t.estimatedTotal}</span>
            <span className="text-right">
              <span className="text-base font-bold text-[var(--text)]">{fmt(publicSubtotal, '')}</span>
              {regTotal != null && complete ? (
                <span className="text-[var(--success)]"> + {fmt(regTotal, regCcy)}</span>
              ) : (
                <span className="block text-xs text-[var(--gold)] italic">
                  + {t.providerFees.toLowerCase()} : {t.toConfirm}
                </span>
              )}
            </span>
          </div>
        </div>

        {/* Message d'incomplétude (frais existants non chiffrés) */}
        {rc.has_unpriced_fees && (
          <div className="flex items-start gap-3 p-3 rounded-lg bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
            <AlertTriangle className="w-5 h-5 text-[var(--gold)] shrink-0 mt-0.5" />
            <p className="text-sm text-[var(--gold)]">{t.incompleteNote}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Row({ label, value, strong }) {
  return (
    <div className="flex items-center justify-between px-3 py-2">
      <span className={`text-sm ${strong ? 'font-semibold text-[var(--text)]' : 'text-[var(--afcfta-muted)]'}`}>{label}</span>
      <span className={`text-sm ${strong ? 'font-bold text-[var(--text)]' : 'text-[var(--text)]'}`}>{value}</span>
    </div>
  );
}
