/**
 * CalculationJournal
 * Affiche le journal de calcul pas-à-pas (NPF et ZLECAf) renvoyé par le backend
 * (normal_calculation_journal / zlecaf_calculation_journal). Chaque étape porte
 * sa base (assiette réelle), le taux, le montant, le cumul et la référence
 * légale. Montants en USD (trace de calcul officielle).
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollText, ExternalLink } from 'lucide-react';

const usd = (v) => {
  if (v === null || v === undefined || v === '-') return '—';
  if (typeof v === 'string') return v;
  return `$${v.toLocaleString('fr-FR', { maximumFractionDigits: 0 })}`;
};

function JournalTable({ steps, language }) {
  const fr = language === 'fr';
  if (!steps || steps.length === 0) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs uppercase tracking-wide text-slate-500 border-b border-slate-700">
            <th className="text-left py-2 pr-2 font-medium">{fr ? 'Étape' : 'Step'}</th>
            <th className="text-right py-2 px-2 font-medium">{fr ? 'Base' : 'Base'}</th>
            <th className="text-right py-2 px-2 font-medium">{fr ? 'Taux' : 'Rate'}</th>
            <th className="text-right py-2 px-2 font-medium">{fr ? 'Montant' : 'Amount'}</th>
            <th className="text-right py-2 pl-2 font-medium">{fr ? 'Cumul' : 'Cumulative'}</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((s, idx) => (
            <tr key={idx} className="border-b border-slate-700/50 last:border-0">
              <td className="py-2 pr-2">
                <span className="text-slate-200">{s.component}</span>
                {s.legal_ref && (
                  <span className="block text-[11px] text-slate-500">
                    {s.legal_ref_url ? (
                      <a
                        href={s.legal_ref_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 hover:text-indigo-400"
                      >
                        {s.legal_ref}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      s.legal_ref
                    )}
                  </span>
                )}
              </td>
              <td className="py-2 px-2 text-right font-mono text-slate-400">{usd(s.base)}</td>
              <td className="py-2 px-2 text-right font-mono text-slate-400">{s.rate ?? '—'}</td>
              <td className="py-2 px-2 text-right font-mono text-white font-semibold">{usd(s.amount)}</td>
              <td className="py-2 pl-2 text-right font-mono text-slate-300">{usd(s.cumulative)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function CalculationJournal({ normalJournal, zlecafJournal, language = 'fr' }) {
  const fr = language === 'fr';
  const [tab, setTab] = useState('npf');
  const hasNpf = normalJournal && normalJournal.length > 0;
  const hasZlc = zlecafJournal && zlecafJournal.length > 0;
  if (!hasNpf && !hasZlc) return null;

  const active = tab === 'npf' ? normalJournal : zlecafJournal;

  const TabBtn = ({ id, label, tone }) => {
    const on = tab === id;
    const onColor = tone === 'emerald' ? 'border-emerald-500/50 text-emerald-300 bg-emerald-500/10'
                                       : 'border-red-500/50 text-red-300 bg-red-500/10';
    return (
      <button
        type="button"
        onClick={() => setTab(id)}
        className={`px-3 py-1.5 rounded-lg border text-sm transition-colors ${
          on ? onColor : 'border-slate-600 text-slate-300 bg-slate-700/40 hover:border-slate-500'
        }`}
      >
        {label}
      </button>
    );
  };

  return (
    <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">
              <ScrollText className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <CardTitle className="text-lg text-white">
                {fr ? 'Journal de calcul' : 'Calculation journal'}
              </CardTitle>
              <CardDescription className="text-slate-400">
                {fr
                  ? 'Étapes détaillées avec base, taux et références légales (USD)'
                  : 'Step-by-step with base, rate and legal references (USD)'}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasNpf && <TabBtn id="npf" label={fr ? 'NPF' : 'MFN'} tone="red" />}
            {hasZlc && <TabBtn id="zlecaf" label="ZLECAf" tone="emerald" />}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <JournalTable steps={active} language={language} />
      </CardContent>
    </Card>
  );
}
