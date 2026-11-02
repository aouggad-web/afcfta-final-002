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
import { montant } from '../../utils/nombres';
import { pick } from '../../i18n/lang';

const usd = (v, language) => {
  if (v === null || v === undefined || v === '-') return '—';
  if (typeof v === 'string') return v;
  return montant(v, language);
};

function JournalTable({ steps, language }) {
  if (!steps || steps.length === 0) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-[var(--afcfta-muted)] border-b border-[var(--afcfta-border)]">
            <th className="text-left py-2 pr-2 font-medium">{pick(language, 'Étape', 'Step', 'المرحلة')}</th>
            <th className="text-right py-2 px-2 font-medium">{pick(language, 'Base', 'Base', 'الوعاء')}</th>
            <th className="text-right py-2 px-2 font-medium">{pick(language, 'Taux', 'Rate', 'المعدل')}</th>
            <th className="text-right py-2 px-2 font-medium">{pick(language, 'Montant', 'Amount', 'المبلغ')}</th>
            <th className="text-right py-2 pl-2 font-medium">{pick(language, 'Cumul', 'Cumulative', 'المجموع التراكمي')}</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((s, idx) => (
            <tr key={idx} className="border-b border-[var(--afcfta-border)] last:border-0">
              <td className="py-2 pr-2">
                <span className="text-[var(--text)]">{s.component}</span>
                {s.legal_ref && (
                  <span className="block text-[11px] text-[var(--afcfta-muted)]">
                    {s.legal_ref_url ? (
                      <a
                        href={s.legal_ref_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 hover:text-[var(--violet)]"
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
              <td className="py-2 px-2 text-right font-mono text-[var(--afcfta-muted)]">{usd(s.base, language)}</td>
              <td className="py-2 px-2 text-right font-mono text-[var(--afcfta-muted)]">{s.rate ?? '—'}</td>
              <td className="py-2 px-2 text-right font-mono text-[var(--text)] font-semibold">{usd(s.amount, language)}</td>
              <td className="py-2 pl-2 text-right font-mono text-[var(--text)]">{usd(s.cumulative, language)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function CalculationJournal({ normalJournal, zlecafJournal, language = 'fr' }) {
  const [tab, setTab] = useState('npf');
  const hasNpf = normalJournal && normalJournal.length > 0;
  const hasZlc = zlecafJournal && zlecafJournal.length > 0;
  if (!hasNpf && !hasZlc) return null;

  const active = tab === 'npf' ? normalJournal : zlecafJournal;

  const TabBtn = ({ id, label, tone }) => {
    const on = tab === id;
    const onColor = tone === 'emerald' ? 'border-[color-mix(in_srgb,var(--success)_30%,transparent)] text-[var(--success)] bg-[color-mix(in_srgb,var(--success)_10%,var(--afcfta-card))]'
                                       : 'border-[color-mix(in_srgb,var(--danger)_30%,transparent)] text-[var(--danger)] bg-[color-mix(in_srgb,var(--danger)_10%,var(--afcfta-card))]';
    return (
      <button
        type="button"
        onClick={() => setTab(id)}
        className={`px-3 py-1.5 rounded-lg border text-sm transition-colors ${
          on ? onColor : 'border-[var(--afcfta-border)] text-[var(--text)] bg-[var(--overlay)] hover:border-[var(--afcfta-border)]'
        }`}
      >
        {label}
      </button>
    );
  };

  return (
    <Card className="bg-[var(--overlay)] border-[var(--afcfta-border)] overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] rounded-lg border border-[color-mix(in_srgb,var(--gold)_30%,transparent)]">
              <ScrollText className="w-5 h-5 text-[var(--gold)]" />
            </div>
            <div>
              <CardTitle className="text-lg text-[var(--text)]">
                {pick(language, 'Journal de calcul', 'Calculation journal', 'سجل الحساب')}
              </CardTitle>
              <CardDescription className="text-[var(--afcfta-muted)]">
                {pick(language, 'Étapes détaillées avec base, taux et références légales (USD)', 'Step-by-step with base, rate and legal references (USD)', 'مراحل مفصلة مع الوعاء والمعدل والمراجع القانونية (USD)')}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasNpf && <TabBtn id="npf" label={pick(language, 'NPF', 'MFN', 'NPF')} tone="red" />}
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
