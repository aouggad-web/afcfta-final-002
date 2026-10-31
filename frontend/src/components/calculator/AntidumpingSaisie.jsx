import React from 'react';

/**
 * Droit antidumping (défense commerciale) : son taux dépend du producteur, et
 * la mesure vise les marchandises originaires OU expédiées des pays qu'elle
 * nomme (Afrique du Sud, R.7991 : « imported from or originating in »). Sans
 * ces réponses, le moteur laisse le droit à établir plutôt que de le supposer
 * ou de le retirer.
 *
 * Le pays d'expédition n'est demandé ici que si la question SACU ne le pose
 * pas déjà (`avecExpedition`).
 */
export default function AntidumpingSaisie({
  producteur = '',
  onProducteurChange,
  expedition = '',
  onExpeditionChange,
  avecExpedition = true,
  onRecalculer,
  disabled = false,
  language = 'fr',
}) {
  const fr = language === 'fr';
  const champ = 'px-3 py-2 bg-[var(--field)] border border-[var(--field-border)] rounded-lg text-[var(--text)] text-sm';
  return (
    <fieldset
      data-testid="antidumping-saisie"
      className="mb-6 rounded-xl border border-[color-mix(in_srgb,var(--gold)_30%,transparent)] bg-[color-mix(in_srgb,var(--gold)_10%,var(--afcfta-card))] p-4 space-y-3"
    >
      <legend className="px-2 text-sm font-semibold text-[var(--gold)]">
        {fr ? 'Droit antidumping : producteur et pays d’expédition' : 'Anti-dumping duty: producer and dispatch country'}
      </legend>
      <p className="text-xs text-[var(--afcfta-muted)]">
        {fr
          ? 'Le taux dépend du producteur nommé dans l’avis ; un producteur non nommé paie le taux des autres producteurs. La mesure vise les marchandises originaires ou expédiées des pays qu’elle nomme. Sans réponse, le droit reste à établir.'
          : 'The rate depends on the producer named in the notice; an unnamed producer pays the all-other-producers rate. The measure covers goods originating in or dispatched from the countries it names. Without an answer, the duty remains to be determined.'}
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-[var(--text)]">
          {fr ? 'Producteur ou exportateur' : 'Producer or exporter'}
          <input
            type="text"
            data-testid="antidumping-producteur"
            value={producteur}
            onChange={(e) => onProducteurChange?.(e.target.value)}
            className={champ}
          />
        </label>
        {avecExpedition && (
          <label className="flex flex-col gap-1 text-xs text-[var(--text)]">
            {fr ? 'Pays d’expédition (ISO-3)' : 'Dispatch country (ISO-3)'}
            <input
              type="text"
              data-testid="antidumping-expedition"
              value={expedition}
              maxLength={3}
              onChange={(e) => onExpeditionChange?.(e.target.value.toUpperCase())}
              className={`${champ} w-24 uppercase`}
            />
          </label>
        )}
        <button
          type="button"
          data-testid="antidumping-recalculer"
          onClick={() => onRecalculer?.()}
          disabled={disabled}
          className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm disabled:opacity-50"
        >
          {fr ? 'Recalculer' : 'Recalculate'}
        </button>
      </div>
    </fieldset>
  );
}
