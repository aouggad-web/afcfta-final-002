import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { AlertTriangle, FlaskConical, Info, ArrowUpRight, ArrowDownLeft } from 'lucide-react';
import { pick } from '../../i18n/lang';

// Couche « indications secondaires » : prestataires et frais REPORTÉS par une
// synthèse non vérifiée, pour les pays pas encore couverts par le registre
// conforme. Rendu volontairement distinct (bordure/teinte différentes), avec un
// avertissement fort. Aucun montant n'entre dans un total ; tout est « à confirmer ».

const PAYER_LABELS = {
  fr: {
    EXPORTER: "Exportateur (fournisseur à l'étranger)",
    IMPORTER: 'Importateur',
    IMPORTER_OR_FORWARDER: 'Importateur ou transitaire',
    IMPORTER_OR_DECLARANT: 'Importateur ou déclarant',
    FORWARDER_OR_IMPORTER: 'Transitaire ou importateur',
    SHIPPER: 'Chargeur',
    SHIPPER_EXPORTER: 'Chargeur / exportateur',
    TRANSPORTER_OR_FORWARDER: 'Transporteur ou transitaire',
    EXPORTER_AGENT: "Agent de l'exportateur",
    LOGISTICS_ACTORS: 'Acteurs logistiques locaux',
  },
  en: {
    EXPORTER: 'Exporter (foreign supplier)',
    IMPORTER: 'Importer',
    IMPORTER_OR_FORWARDER: 'Importer or forwarder',
    IMPORTER_OR_DECLARANT: 'Importer or declarant',
    FORWARDER_OR_IMPORTER: 'Forwarder or importer',
    SHIPPER: 'Shipper',
    SHIPPER_EXPORTER: 'Shipper / exporter',
    TRANSPORTER_OR_FORWARDER: 'Transporter or forwarder',
    EXPORTER_AGENT: "Exporter's agent",
    LOGISTICS_ACTORS: 'Local logistics actors',
  },
  ar: {
    EXPORTER: 'المصدِّر (المورِّد في الخارج)',
    IMPORTER: 'المستورد',
    IMPORTER_OR_FORWARDER: 'المستورد أو وكيل الشحن',
    IMPORTER_OR_DECLARANT: 'المستورد أو المصرِّح',
    FORWARDER_OR_IMPORTER: 'وكيل الشحن أو المستورد',
    SHIPPER: 'الشاحن',
    SHIPPER_EXPORTER: 'الشاحن / المصدِّر',
    TRANSPORTER_OR_FORWARDER: 'الناقل أو وكيل الشحن',
    EXPORTER_AGENT: 'وكيل المصدِّر',
    LOGISTICS_ACTORS: 'الفاعلون اللوجستيون المحليون',
  },
};

function T(language) {
  return {
    title: pick(language, 'Indications secondaires — prestataires & frais reportés', 'Secondary indications — reported providers & fees', 'مؤشرات ثانوية — مقدمو الخدمات والرسوم المُبلَّغ عنها'),
    desc: pick(language, 'Pays non encore couverts par le registre officiel. Données de synthèse à vérifier.', 'Countries not yet in the official registry. Synthesis data to be verified.', 'بلدان لم يشملها السجل الرسمي بعد. بيانات تجميعية تحتاج إلى تحقق.'),
    warning: pick(language, "Ces éléments proviennent d'une synthèse secondaire NON VÉRIFIÉE (backlog de collecte). Les montants sont approximatifs, non opposables, et n'entrent dans aucun total. À confirmer auprès du prestataire ou de l'autorité compétente avant toute décision.", 'These items come from an UNVERIFIED secondary synthesis (collection backlog). Amounts are approximate, non-binding, and enter no total. Confirm with the provider or competent authority before any decision.', "مصدر هذه العناصر تجميع ثانوي غير مُتحقَّق منه (قائمة جمع متأخرة). المبالغ تقريبية وغير ملزمة ولا تدخل في أي مجموع. يجب تأكيدها لدى مقدم الخدمة أو السلطة المختصة قبل أي قرار."),
    toConfirm: pick(language, 'à confirmer', 'to be confirmed', 'قيد التأكيد'),
    providers: pick(language, 'Prestataire(s)', 'Provider(s)', 'مقدم(و) الخدمة'),
    payer: pick(language, 'Payeur', 'Payer', 'الجهة الدافعة'),
    period: pick(language, 'Période', 'Period', 'الفترة'),
    reportedFee: pick(language, 'Frais reporté', 'Reported fee', 'الرسم المُبلَّغ عنه'),
    traceability: pick(language, 'Traçabilité', 'Traceability', 'قابلية التتبع'),
    sideImport: pick(language, 'Import', 'Import', 'استيراد'),
    sideExport: pick(language, 'Export', 'Export', 'تصدير'),
    unverified: pick(language, 'NON VÉRIFIÉ', 'UNVERIFIED', 'غير مُتحقَّق منه'),
    exportStageTitle: pick(language, "Formalités à l'export (amont — pays d'origine)", 'Export-side formalities (upstream — country of origin)', "إجراءات التصدير (المرحلة السابقة — بلد المنشأ)"),
    exportStageDesc: pick(language, "Accomplies avant embarquement dans le pays d'origine, à la charge de l'exportateur.", 'Completed before shipment in the country of origin, borne by the exporter.', "تُنجَز قبل الشحن في بلد المنشأ، على عاتق المصدِّر."),
    importStageTitle: pick(language, "Formalités à l'import (aval — pays de destination)", 'Import-side formalities (downstream — country of destination)', "إجراءات الاستيراد (المرحلة اللاحقة — بلد المقصد)"),
    importStageDesc: pick(language, "Acquittées à l'arrivée dans le pays de destination, à la charge de l'importateur.", 'Paid on arrival in the destination country, borne by the importer.', "تُؤدّى عند الوصول إلى بلد المقصد، على عاتق المستورد."),
    explainTitle: pick(language, "Import vs export : comment lire ces indications", 'Import vs export: how to read these indications', "الاستيراد مقابل التصدير: كيف تُقرأ هذه المؤشرات"),
    explainBody: pick(language, "Ces indications se répartissent selon l'étape de l'opération : à l'EXPORT (amont), les formalités concernent le pays d'origine, avant embarquement ; à l'IMPORT (aval), elles concernent le pays de destination, à l'arrivée. Dans les deux cas, ces montants restent NON VÉRIFIÉS et n'entrent dans aucun total.", "These indications are split by the stage of the operation: on the EXPORT side (upstream), formalities concern the country of origin, before shipment; on the IMPORT side (downstream), they concern the destination country, on arrival. In both cases, these amounts remain UNVERIFIED and enter no total.", "تتوزع هذه المؤشرات حسب مرحلة العملية: في التصدير (المرحلة السابقة) تخص الإجراءات بلد المنشأ قبل الشحن؛ وفي الاستيراد (المرحلة اللاحقة) تخص بلد المقصد عند الوصول. وفي الحالتين، تبقى هذه المبالغ غير مُتحقَّق منها ولا تدخل في أي مجموع."),
  };
}

function ReportedItem({ item, t, language }) {
  const payerLabels = PAYER_LABELS[language] || PAYER_LABELS.fr;
  const period = item.period ? `${item.period.start || '?'} → ${item.period.end || '?'}` : null;
  return (
    <div className="p-3 rounded-lg bg-[var(--overlay)] border border-dashed border-[var(--afcfta-border)] text-sm">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <p className="text-[var(--text)] font-medium">
            {item.country_name} — {item.program}
          </p>
          {!!(item.providers || []).length && (
            <p className="text-[var(--afcfta-muted)] text-xs mt-0.5">
              {t.providers}: <span className="text-[var(--text)]">{item.providers.join(', ')}</span>
            </p>
          )}
          {item.mission && <p className="text-[var(--afcfta-muted)] text-xs mt-0.5">{item.mission}</p>}
          {item.payer && (
            <p className="text-[var(--afcfta-muted)] text-xs mt-0.5">
              {t.payer}: <span className="text-[var(--text)]">{payerLabels[item.payer] || item.payer}</span>
            </p>
          )}
          {period && (
            <p className="text-[var(--afcfta-muted)] text-xs">
              {t.period}: <span className="text-[var(--text)]">{period}</span>
            </p>
          )}
          {item.traceability && (
            <p className="text-[var(--afcfta-muted)] text-[11px] mt-1 italic">
              {t.traceability}: {item.traceability}
            </p>
          )}
        </div>
        <div className="text-right shrink-0">
          <Badge variant="outline" className="bg-[var(--overlay)] text-[var(--text)] border-[var(--afcfta-border)]">
            {item.side === 'export' ? t.sideExport : t.sideImport}
          </Badge>
          <p className="mt-1 text-xs text-[var(--gold)]">
            {t.reportedFee}: <span className="italic">{item.reported_fee_range || t.toConfirm}</span>
          </p>
          <p className="text-[11px] text-[var(--afcfta-muted)] mt-0.5">{t.toConfirm}</p>
        </div>
      </div>
    </div>
  );
}

function StageBlock({ title, desc, icon: Icon, items, t, language }) {
  if (!items.length) return null;
  return (
    <div className="space-y-2">
      <div>
        <p className="text-sm font-semibold text-[var(--text)] flex items-center gap-2">
          <Icon className="w-4 h-4" /> {title}
        </p>
        <p className="text-[11px] text-[var(--afcfta-muted)] ml-6">{desc}</p>
      </div>
      {items.map((item, idx) => (
        <ReportedItem key={idx} item={item} t={t} language={language} />
      ))}
    </div>
  );
}

export default function RegulatoryReportedIndications({ result, language = 'fr' }) {
  const t = T(language);
  const layer = result?.regulatory_reported;
  if (!layer || !(layer.items || []).length) return null;

  // Regroupement par ÉTAPE logistique : export (amont, pays d'origine) vs
  // import (aval, pays de destination) — même logique que la couche vérifiée.
  const exportItems = layer.items.filter((i) => i.side === 'export');
  const importItems = layer.items.filter((i) => i.side !== 'export');

  return (
    <Card className="bg-[var(--overlay)] border border-dashed border-[var(--afcfta-border)]">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[var(--overlay)] rounded-lg border border-[var(--afcfta-border)]">
            <FlaskConical className="w-5 h-5 text-[var(--text)]" />
          </div>
          <div>
            <CardTitle className="text-base text-[var(--text)] flex items-center gap-2">
              {t.title}
              <Badge variant="outline" className="bg-[color-mix(in_srgb,var(--gold)_12%,var(--afcfta-card))] text-[var(--gold)] border-[color-mix(in_srgb,var(--gold)_30%,transparent)] text-[11px]">
                {t.unverified}
              </Badge>
            </CardTitle>
            <CardDescription className="text-[var(--afcfta-muted)]">{t.desc}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-start gap-3 p-3 rounded-lg bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
          <AlertTriangle className="w-5 h-5 text-[var(--gold)] shrink-0 mt-0.5" />
          <p className="text-sm text-[var(--gold)]">{t.warning}</p>
        </div>

        {/* Encadré explicatif import vs export */}
        <div className="rounded-lg border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[color-mix(in_srgb,var(--info)_5%,var(--afcfta-card))] p-3">
          <p className="text-sm font-semibold text-[var(--info)] flex items-center gap-2">
            <Info className="w-4 h-4" /> {t.explainTitle}
          </p>
          <p className="text-xs text-[var(--text)]/90 mt-1">{t.explainBody}</p>
        </div>

        {/* Volet EXPORT (amont, pays d'origine) */}
        <StageBlock
          title={t.exportStageTitle}
          desc={t.exportStageDesc}
          icon={ArrowUpRight}
          items={exportItems}
          t={t}
          language={language}
        />

        {/* Volet IMPORT (aval, pays de destination) */}
        <StageBlock
          title={t.importStageTitle}
          desc={t.importStageDesc}
          icon={ArrowDownLeft}
          items={importItems}
          t={t}
          language={language}
        />
      </CardContent>
    </Card>
  );
}
