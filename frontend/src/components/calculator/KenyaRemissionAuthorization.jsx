import React from 'react';
import { pick } from '../../i18n/lang';

const emptyValue = {
  answer: 'unknown',
  reference: '',
  validFrom: '',
  validTo: '',
  authorizedTariffLines: '',
  authorizedGoods: '',
};

export default function KenyaRemissionAuthorization({ value = emptyValue, onChange, language = 'fr' }) {
  const update = (field, next) => onChange?.({ ...emptyValue, ...value, [field]: next });
  return (
    <fieldset className="rounded-xl border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] p-4 space-y-3">
      <legend className="px-2 text-sm font-semibold text-[var(--gold)]">
        {pick(
          language,
          <>
            Disposez-vous d’une autorisation ou d’une allocation officielle couvrant cette
            marchandise au titre de cette remission ?
          </>,
          'Do you hold an official authorization or allocation covering these goods under this remission?',
          'هل لديكم ترخيص أو حصة رسمية تشمل هذه البضاعة في إطار هذا الإعفاء؟',
        )}
      </legend>
      <div className="flex flex-wrap gap-4" role="radiogroup" aria-label={pick(language, 'Éligibilité à la remission', 'Remission eligibility', 'الأهلية للإعفاء')}>
        {[
          ['no', pick(language, 'Non', 'No', 'لا')],
          ['yes', pick(language, 'Oui', 'Yes', 'نعم')],
          ['unknown', pick(language, 'Je ne sais pas', "I don't know", 'لا أعرف')],
        ].map(([answer, label]) => (
          <label key={answer} className="flex items-center gap-2 text-sm text-[var(--text)]">
            <input
              type="radio"
              name="kenya-remission-authorization"
              value={answer}
              checked={value.answer === answer}
              onChange={() => update('answer', answer)}
            />
            {label}
          </label>
        ))}
      </div>
      {value.answer === 'yes' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="kenya-authorization-details">
          <label className="text-xs text-[var(--text)]">
            {pick(language, 'Référence officielle', 'Official reference', 'المرجع الرسمي')}
            <input
              className="mt-1 w-full rounded border border-[var(--afcfta-border)] bg-[var(--overlay)] p-2"
              value={value.reference}
              onChange={(event) => update('reference', event.target.value)}
            />
          </label>
          <label className="text-xs text-[var(--text)]">
            {pick(language, 'Début de validité', 'Valid from', 'بداية الصلاحية')}
            <input
              type="date"
              className="mt-1 w-full rounded border border-[var(--afcfta-border)] bg-[var(--overlay)] p-2"
              value={value.validFrom}
              onChange={(event) => update('validFrom', event.target.value)}
            />
          </label>
          <label className="text-xs text-[var(--text)]">
            {pick(language, 'Fin de validité', 'Valid until', 'نهاية الصلاحية')}
            <input
              type="date"
              className="mt-1 w-full rounded border border-[var(--afcfta-border)] bg-[var(--overlay)] p-2"
              value={value.validTo}
              onChange={(event) => update('validTo', event.target.value)}
            />
          </label>
          <label className="text-xs text-[var(--text)]">
            {pick(language, 'Lignes tarifaires exactes autorisées, séparées par des virgules', 'Exact authorized tariff lines, comma-separated', 'البنود التعريفية المرخَّصة بدقة، مفصولة بفواصل')}
            <input
              className="mt-1 w-full rounded border border-[var(--afcfta-border)] bg-[var(--overlay)] p-2 font-mono"
              value={value.authorizedTariffLines}
              onChange={(event) => update('authorizedTariffLines', event.target.value)}
              placeholder="10019910, 10019990"
            />
          </label>
          <label className="text-xs text-[var(--text)] md:col-span-2">
            {pick(language, 'Marchandises détaillées figurant sur l’autorisation', 'Detailed goods listed on the authorization', 'البضائع المفصَّلة الواردة في الترخيص')}
            <textarea
              className="mt-1 w-full rounded border border-[var(--afcfta-border)] bg-[var(--overlay)] p-2"
              value={value.authorizedGoods}
              onChange={(event) => update('authorizedGoods', event.target.value)}
            />
          </label>
        </div>
      )}
      <p className="text-xs text-[var(--gold)]">
        {pick(
          language,
          'Sans autorisation vérifiable couvrant la ligne exacte, la remission n’est pas appliquée.',
          'Without a verifiable authorization covering the exact line, the remission is not applied.',
          'في غياب ترخيص يمكن التحقق منه يشمل البند بدقة، لا يُطبَّق الإعفاء.',
        )}
      </p>
    </fieldset>
  );
}
