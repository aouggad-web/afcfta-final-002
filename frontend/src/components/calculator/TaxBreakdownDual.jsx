/**
 * TaxBreakdownDual
 * Affiche le détail COMPLET des droits et taxes du calculateur :
 *  - ventilation NPF vs ZLECAf, taxe par taxe (base déclarée + montants)
 *  - bi-devise : bascule USD / monnaie locale du pays de destination
 *  - récapitulatif par régime + économie
 *
 * Consomme les champs backend : taxes_breakdown, taxes_summary, currency.
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { Layers, TrendingDown, ArrowLeftRight } from 'lucide-react';

const CATEGORY_LABEL = {
  droit_douane: { fr: 'Droit de douane', en: 'Customs duty' },
  tva: { fr: 'TVA', en: 'VAT' },
  autre_taxe: { fr: 'Prélèvement', en: 'Levy' },
};

export default function TaxBreakdownDual({ breakdown, summary, currency, language = 'fr' }) {
  const fr = language === 'fr';
  const hasLocal = !!(currency && currency.available && currency.usd_to_local_rate);
  const [mode, setMode] = useState('USD'); // 'USD' | 'LOCAL'
  const useLocal = mode === 'LOCAL' && hasLocal;

  if (!breakdown || breakdown.length === 0) return null;

  const fmt = (amountUsd, amountLocal) => {
    if (useLocal) {
      const v = (amountLocal !== undefined && amountLocal !== null) ? amountLocal : null;
      if (v === null) return '—';
      const n = v.toLocaleString('fr-FR', { maximumFractionDigits: 0 });
      return `${n} ${currency.local_symbol || currency.local_code}`;
    }
    if (amountUsd === undefined || amountUsd === null) return '—';
    return `$${amountUsd.toLocaleString('fr-FR', { maximumFractionDigits: 0 })}`;
  };

  const s = summary || {};
  const npf = s.npf || {};
  const zlc = s.zlecaf || {};
  const sl = (currency && currency.summary_local) || {};
  const slNpf = sl.npf || {};
  const slZlc = sl.zlecaf || {};

  return (
    <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20">
              <Layers className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <CardTitle className="text-lg text-white">
                {fr ? 'Détail des droits et taxes — NPF vs ZLECAf' : 'Duties & taxes — MFN vs AfCFTA'}
              </CardTitle>
              <CardDescription className="text-slate-400">
                {fr
                  ? 'Chaque taxe calculée sur sa base (assiette) déclarée'
                  : 'Each tax computed on its declared base'}
                {currency && currency.local_code && (
                  <span className="ml-1 text-slate-500">
                    · {currency.local_code}
                    {hasLocal
                      ? ` @ ${Number(currency.usd_to_local_rate).toLocaleString('fr-FR', { maximumFractionDigits: 2 })}/USD`
                      : ` (${fr ? 'taux indisponible' : 'rate unavailable'})`}
                  </span>
                )}
              </CardDescription>
            </div>
          </div>
          {hasLocal && (
            <button
              type="button"
              onClick={() => setMode(useLocal ? 'USD' : 'LOCAL')}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-600 bg-slate-700/40 text-slate-200 text-sm hover:border-indigo-500/40 transition-colors"
            >
              <ArrowLeftRight className="w-4 h-4" />
              {useLocal ? (currency.local_code) : 'USD'}
            </button>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {/* En-tête de colonnes */}
        <div className="hidden md:grid grid-cols-12 gap-2 px-3 pb-2 text-xs uppercase tracking-wide text-slate-500">
          <div className="col-span-5">{fr ? 'Taxe / Base' : 'Tax / Base'}</div>
          <div className="col-span-3 text-right">{fr ? 'NPF' : 'MFN'}</div>
          <div className="col-span-4 text-right">ZLECAf</div>
        </div>

        <div className="space-y-2">
          {breakdown.map((b, idx) => {
            const cat = CATEGORY_LABEL[b.category] || { fr: b.category, en: b.category };
            const reduced = b.affected_by_zlecaf && b.amount_zlecaf < b.amount_npf;
            return (
              <div
                key={idx}
                className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center p-3 bg-slate-700/30 rounded-lg border border-slate-700"
              >
                <div className="md:col-span-5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-white font-semibold">{b.name}</span>
                    <Badge variant="outline" className="text-[10px] border-slate-600 text-slate-300">
                      {b.code}
                    </Badge>
                    {b.cap && (
                      <Badge variant="outline" className="text-[10px] border-amber-500/40 text-amber-300">
                        {fr ? 'plafond' : 'cap'} {b.cap.amount.toLocaleString('fr-FR')} {b.cap.currency}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {fr ? cat.fr : cat.en} · {fr ? 'base' : 'base'}: {b.base_expr}
                  </p>
                </div>

                <div className="md:col-span-3 flex md:block items-center justify-between md:text-right">
                  <span className="md:hidden text-xs text-slate-500">{fr ? 'NPF' : 'MFN'}</span>
                  <div>
                    <span className="text-white font-bold">{fmt(b.amount_npf, b.amount_npf_local)}</span>
                    <span className="text-slate-500 text-xs ml-1">({b.rate_npf_pct}%)</span>
                  </div>
                </div>

                <div className="md:col-span-4 flex md:block items-center justify-between md:text-right">
                  <span className="md:hidden text-xs text-slate-500">ZLECAf</span>
                  <div>
                    <span className={`font-bold ${reduced ? 'text-emerald-400' : 'text-slate-200'}`}>
                      {fmt(b.amount_zlecaf, b.amount_zlecaf_local)}
                    </span>
                    <span className="text-slate-500 text-xs ml-1">({b.rate_zlecaf_pct}%)</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Récapitulatif */}
        {summary && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            <SummaryCard
              title={fr ? 'Total NPF' : 'Total MFN'}
              s={npf}
              sLocal={slNpf}
              useLocal={useLocal}
              currency={currency}
              language={language}
              tone="red"
            />
            <SummaryCard
              title={fr ? 'Total ZLECAf' : 'Total AfCFTA'}
              s={zlc}
              sLocal={slZlc}
              useLocal={useLocal}
              currency={currency}
              language={language}
              tone="emerald"
            />
          </div>
        )}

        {summary && (
          <div className="mt-3 flex items-center justify-between p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <div className="flex items-center gap-2 text-emerald-300">
              <TrendingDown className="w-4 h-4" />
              <span className="font-semibold">{fr ? 'Économie totale ZLECAf' : 'Total AfCFTA savings'}</span>
            </div>
            <span className="text-emerald-400 font-bold text-lg">
              {useLocal
                ? `${(sl.economie_totale ?? 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} ${currency.local_symbol || currency.local_code}`
                : `$${(s.economie_totale ?? 0).toLocaleString('fr-FR', { maximumFractionDigits: 0 })}`}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SummaryCard({ title, s, sLocal, useLocal, currency, language, tone }) {
  const fr = language === 'fr';
  const color = tone === 'emerald' ? 'text-emerald-400' : 'text-red-400';
  const val = (k) => {
    if (useLocal) {
      const v = sLocal[k];
      if (v === undefined || v === null) return '—';
      return `${v.toLocaleString('fr-FR', { maximumFractionDigits: 0 })} ${currency.local_symbol || currency.local_code}`;
    }
    const v = s[k];
    if (v === undefined || v === null) return '—';
    return `$${v.toLocaleString('fr-FR', { maximumFractionDigits: 0 })}`;
  };
  const Row = ({ label, k }) => (
    <div className="flex items-center justify-between text-sm">
      <span className="text-slate-400">{label}</span>
      <span className="text-slate-100 font-mono">{val(k)}</span>
    </div>
  );
  return (
    <div className="p-3 rounded-lg bg-slate-700/30 border border-slate-700 space-y-1.5">
      <p className={`font-semibold ${color}`}>{title}</p>
      <Row label={fr ? 'Droit de douane' : 'Customs duty'} k="droit_douane" />
      <Row label={fr ? 'Autres taxes' : 'Other levies'} k="autres_taxes" />
      <Row label="TVA" k="tva" />
      <div className="border-t border-slate-600 my-1" />
      <Row label={fr ? 'Coût total' : 'Total cost'} k="cout_total" />
    </div>
  );
}
