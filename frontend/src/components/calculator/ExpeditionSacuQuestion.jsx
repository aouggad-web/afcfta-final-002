import React from 'react';

/**
 * Afrique du Sud — VAT Act 89/1991, s.13(2)(b).
 *
 * La TVA à l'importation porte sur la valeur en douane majorée de 10 %, plus
 * les droits (s.13(2)(a)). La majoration ne s'applique pas à une marchandise
 * ORIGINAIRE du Botswana, du Lesotho, de la Namibie ou de l'Eswatini ET
 * EXPÉDIÉE depuis l'un de ces pays. Le calculateur connaît l'origine, pas le
 * pays d'expédition : il le demande ici, et seulement dans ce cas.
 */
export default function ExpeditionSacuQuestion({ value = 'unknown', onChange, language = 'fr' }) {
  const fr = language === 'fr';
  const choix = fr
    ? [['yes', 'Oui'], ['no', 'Non'], ['unknown', 'Je ne sais pas']]
    : [['yes', 'Yes'], ['no', 'No'], ['unknown', "I don't know"]];
  return (
    <fieldset
      data-testid="expedition-sacu-question"
      className="rounded-xl border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))] p-4 space-y-3"
    >
      <legend className="px-2 text-sm font-semibold text-[var(--info)]">
        {fr
          ? 'La marchandise est-elle expédiée vers l’Afrique du Sud depuis ce même pays (Botswana, Lesotho, Namibie ou Eswatini) ?'
          : 'Is the shipment dispatched to South Africa from that same country (Botswana, Lesotho, Namibia or Eswatini)?'}
      </legend>
      <div className="flex flex-wrap gap-4" role="radiogroup" aria-label={fr ? 'Pays d’expédition' : 'Dispatch country'}>
        {choix.map(([answer, label]) => (
          <label key={answer} className="flex items-center gap-2 text-sm text-[var(--text)]">
            <input
              type="radio"
              name="expedition-sacu"
              value={answer}
              checked={value === answer}
              onChange={() => onChange?.(answer)}
            />
            {label}
          </label>
        ))}
      </div>
      <div className="text-xs text-[var(--afcfta-muted)] space-y-1" data-testid="expedition-sacu-cadre">
        <p>
          {fr
            ? 'Spécificité sud-africaine : la TVA à l’importation (15 %) est assise sur la valeur en douane majorée de 10 %, plus les droits. Cette majoration ne s’applique pas aux marchandises originaires du Botswana, du Lesotho, de la Namibie ou de l’Eswatini ET expédiées depuis l’un de ces pays. Une marchandise de ces pays expédiée d’ailleurs reste majorée.'
            : 'South African specificity: import VAT (15%) is levied on the customs value plus 10%, plus duties. The 10% uplift does not apply to goods originating in Botswana, Lesotho, Namibia or Eswatini AND dispatched from one of those countries. Goods from those countries dispatched from elsewhere remain uplifted.'}
        </p>
        <p>
          {fr ? 'Cadre réglementaire : ' : 'Legal framework: '}
          Value-Added Tax Act 89 of 1991, s.13(2)(a) et (b) ; SARS, guide CE-G06
          « Value-Added Tax Levied on the Importation of Goods into South Africa », § 5.1.
        </p>
        <p>
          {fr
            ? 'Sans réponse, la TVA n’est pas calculée : elle reste indiquée « à compléter » plutôt que supposée.'
            : 'Without an answer, VAT is not computed: it is shown as “to be completed” rather than assumed.'}
        </p>
      </div>
    </fieldset>
  );
}
