import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { AlertTriangle, FlaskConical, Info, ArrowUpRight, ArrowDownLeft } from 'lucide-react';

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
};

function T(language) {
  const fr = language !== 'en';
  return {
    title: fr ? 'Indications secondaires — prestataires & frais reportés' : 'Secondary indications — reported providers & fees',
    desc: fr
      ? 'Pays non encore couverts par le registre officiel. Données de synthèse à vérifier.'
      : 'Countries not yet in the official registry. Synthesis data to be verified.',
    warning: fr
      ? "Ces éléments proviennent d'une synthèse secondaire NON VÉRIFIÉE (backlog de collecte). Les montants sont approximatifs, non opposables, et n'entrent dans aucun total. À confirmer auprès du prestataire ou de l'autorité compétente avant toute décision."
      : 'These items come from an UNVERIFIED secondary synthesis (collection backlog). Amounts are approximate, non-binding, and enter no total. Confirm with the provider or competent authority before any decision.',
    toConfirm: fr ? 'à confirmer' : 'to be confirmed',
    providers: fr ? 'Prestataire(s)' : 'Provider(s)',
    payer: fr ? 'Payeur' : 'Payer',
    period: fr ? 'Période' : 'Period',
    reportedFee: fr ? 'Frais reporté' : 'Reported fee',
    traceability: fr ? 'Traçabilité' : 'Traceability',
    sideImport: fr ? 'Import' : 'Import',
    sideExport: fr ? 'Export' : 'Export',
    unverified: fr ? 'NON VÉRIFIÉ' : 'UNVERIFIED',
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
    explainTitle: fr ? "Import vs export : comment lire ces indications" : 'Import vs export: how to read these indications',
    explainBody: fr
      ? "Ces indications se répartissent selon l'étape de l'opération : à l'EXPORT (amont), les formalités concernent le pays d'origine, avant embarquement ; à l'IMPORT (aval), elles concernent le pays de destination, à l'arrivée. Dans les deux cas, ces montants restent NON VÉRIFIÉS et n'entrent dans aucun total."
      : "These indications are split by the stage of the operation: on the EXPORT side (upstream), formalities concern the country of origin, before shipment; on the IMPORT side (downstream), they concern the destination country, on arrival. In both cases, these amounts remain UNVERIFIED and enter no total.",
  };
}

function ReportedItem({ item, t, language }) {
  const payerLabels = PAYER_LABELS[language !== 'en' ? 'fr' : 'en'];
  const period = item.period ? `${item.period.start || '?'} → ${item.period.end || '?'}` : null;
  return (
    <div className="p-3 rounded-lg bg-slate-800/40 border border-dashed border-slate-600 text-sm">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="min-w-0">
          <p className="text-slate-200 font-medium">
            {item.country_name} — {item.program}
          </p>
          {!!(item.providers || []).length && (
            <p className="text-slate-400 text-xs mt-0.5">
              {t.providers}: <span className="text-slate-300">{item.providers.join(', ')}</span>
            </p>
          )}
          {item.mission && <p className="text-slate-500 text-xs mt-0.5">{item.mission}</p>}
          {item.payer && (
            <p className="text-slate-400 text-xs mt-0.5">
              {t.payer}: <span className="text-slate-300">{payerLabels[item.payer] || item.payer}</span>
            </p>
          )}
          {period && (
            <p className="text-slate-400 text-xs">
              {t.period}: <span className="text-slate-300">{period}</span>
            </p>
          )}
          {item.traceability && (
            <p className="text-slate-500 text-[11px] mt-1 italic">
              {t.traceability}: {item.traceability}
            </p>
          )}
        </div>
        <div className="text-right shrink-0">
          <Badge variant="outline" className="bg-slate-600/20 text-slate-300 border-slate-500/40">
            {item.side === 'export' ? t.sideExport : t.sideImport}
          </Badge>
          <p className="mt-1 text-xs text-amber-300/90">
            {t.reportedFee}: <span className="italic">{item.reported_fee_range || t.toConfirm}</span>
          </p>
          <p className="text-[10px] text-slate-500 mt-0.5">{t.toConfirm}</p>
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
        <p className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Icon className="w-4 h-4" /> {title}
        </p>
        <p className="text-[11px] text-slate-500 ml-6">{desc}</p>
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
    <Card className="bg-slate-900/40 border border-dashed border-slate-600">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-slate-500/10 rounded-lg border border-slate-500/20">
            <FlaskConical className="w-5 h-5 text-slate-300" />
          </div>
          <div>
            <CardTitle className="text-base text-slate-200 flex items-center gap-2">
              {t.title}
              <Badge variant="outline" className="bg-amber-600/15 text-amber-300 border-amber-500/40 text-[10px]">
                {t.unverified}
              </Badge>
            </CardTitle>
            <CardDescription className="text-slate-400">{t.desc}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-200/90">{t.warning}</p>
        </div>

        {/* Encadré explicatif import vs export */}
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 p-3">
          <p className="text-sm font-semibold text-sky-200 flex items-center gap-2">
            <Info className="w-4 h-4" /> {t.explainTitle}
          </p>
          <p className="text-xs text-slate-300/90 mt-1">{t.explainBody}</p>
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
