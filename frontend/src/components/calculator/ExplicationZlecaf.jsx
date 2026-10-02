import React from 'react';
import { expliquerZlecaf } from './zlecafExplication';

const couleurNiveau = (niveau) => {
  if (niveau === 'APPLICATION_DOCUMENTEE') return 'var(--success)';
  if (niveau === 'NON_CALCULABLE') return 'var(--afcfta-muted)';
  return 'var(--gold)';
};

/** « Comment ce résultat ZLECAf a été obtenu » — quatre questions fixes. */
export default function ExplicationZlecaf({ result, language = 'fr' }) {
  if (!result) return null;
  const { niveau, titre, lignes } = expliquerZlecaf(result, language);
  const couleur = couleurNiveau(niveau);

  return (
    <div
      className="mt-4 rounded-xl border border-[var(--afcfta-border)] bg-[var(--overlay)] p-4"
      data-testid="explication-zlecaf"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold text-[var(--text)]">
          {language === 'fr'
            ? 'Comment ce résultat ZLECAf a été obtenu'
            : 'How this AfCFTA result was obtained'}
        </p>
        <span
          className="rounded border px-2 py-1 text-xs font-semibold"
          style={{ color: couleur, borderColor: `color-mix(in srgb, ${couleur} 30%, transparent)` }}
          data-testid="explication-zlecaf-niveau"
        >
          {titre}
        </span>
      </div>
      <dl className="mt-3 space-y-2 text-sm">
        {lignes.map((ligne) => (
          <div key={ligne.cle} className="sm:flex sm:gap-3">
            <dt className="shrink-0 font-medium text-[var(--afcfta-muted)] sm:w-48">{ligne.label}</dt>
            <dd className="text-[var(--text)]">
              {ligne.texte}
              {ligne.lien && (
                <>
                  {' '}
                  <a
                    href={ligne.lien}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[var(--info)] underline"
                  >
                    {language === 'fr' ? 'Voir la source' : 'View source'}
                  </a>
                </>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
