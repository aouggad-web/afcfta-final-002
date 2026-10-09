import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * L'état du moteur, posé à côté de chaque total qu'il qualifie.
 *
 * Un total PARTIEL qui s'affiche comme un coût total est un montant faux :
 * il omet des droits sans le dire. Le toast de fin de calcul le signalait,
 * mais il disparaît en quelques secondes ; le badge, lui, reste là où le
 * montant se lit. Il nomme aussi ce qui manque — « 4 droits non calculés :
 * DSV, TMABATT… » — pour que l'opérateur sache quoi compléter.
 *
 * Sans état connu (chemin historique, qui n'en rend pas), rien n'est affiché :
 * le badge ne devine pas un état que le moteur n'a pas établi.
 */
const TONS = {
  COMPLET: 'var(--success)',
  INDICATIF: 'var(--info)',
  PARTIEL: 'var(--gold)',
  INDISPONIBLE: 'var(--danger)',
};

export default function EtatCalculBadge({ etat, manques = [], compact = false }) {
  const { t } = useTranslation();
  if (!TONS[etat]) return null;
  const ton = TONS[etat];
  const codes = [...new Set((manques || []).map((m) => m.code))];
  return (
    <span className="inline-flex flex-col gap-0.5" data-testid="etat-calcul">
      <span
        className="inline-flex w-fit items-center rounded-md border px-2 py-0.5 text-xs font-semibold"
        style={{
          color: ton,
          borderColor: `color-mix(in srgb, ${ton} 40%, transparent)`,
          background: `color-mix(in srgb, ${ton} 12%, var(--afcfta-card))`,
        }}
        title={t(`calculator.etat.aide.${etat}`)}
      >
        {t(`calculator.etat.${etat}`)}
      </span>
      {!compact && (
        <span className="text-xs text-[var(--afcfta-muted)]">{t(`calculator.etat.aide.${etat}`)}</span>
      )}
      {codes.length > 0 && (
        <span className="text-xs break-words" style={{ color: ton }}>
          {t('calculator.etat.nonCalcules', { count: codes.length, codes: codes.join(', ') })}
        </span>
      )}
    </span>
  );
}
