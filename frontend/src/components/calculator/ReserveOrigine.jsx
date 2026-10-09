import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileCheck } from 'lucide-react';

/**
 * La réserve d'origine, jointe à toute préférence ZLECAf servie.
 *
 * Le taux préférentiel n'est dû que si la marchandise est originaire : sans
 * cette mention, l'écran présentait comme acquis un taux que le moteur ne peut
 * pas garantir. La règle SH6 vient du moteur (`regle_origine`, Appendice IV) ;
 * quand elle manque (chemin historique), seule la mention s'affiche — aucune
 * règle générique n'est inventée à sa place.
 */
export default function ReserveOrigine({ regle }) {
  const { t, i18n } = useTranslation();
  const lng = i18n.language === 'en' ? 'en' : 'fr';
  const etablie = regle?.regle && ['AGREED', 'PARTIAL'].includes(regle.statut);
  return (
    <div
      className="mb-6 p-4 rounded-xl flex items-start gap-3 border border-[color-mix(in_srgb,var(--info)_30%,transparent)] bg-[color-mix(in_srgb,var(--info)_8%,var(--afcfta-card))]"
      data-testid="reserve-origine"
    >
      <FileCheck className="w-5 h-5 text-[var(--info)] mt-0.5 flex-shrink-0" />
      <div className="min-w-0 space-y-1">
        <p className="text-[var(--info)] font-semibold text-sm">{t('calculator.origine.titre')}</p>
        <p className="text-[var(--text)] text-sm">{t('calculator.origine.reserve')}</p>
        {regle && (etablie ? (
          <>
            <p className="text-[var(--text)] text-sm font-medium">
              {t('calculator.origine.regle', {
                hs6: regle.hs6,
                niveau: t(`calculator.origine.niveaux.${regle.niveau}`),
                nom: regle.regle.nom[lng],
              })}
            </p>
            <p className="text-[var(--afcfta-muted)] text-xs">{regle.regle.explication[lng]}</p>
            {regle.regle_alternative && (
              <p className="text-[var(--afcfta-muted)] text-xs">
                {t('calculator.origine.alternative', { nom: regle.regle_alternative.nom[lng] })}
              </p>
            )}
            {typeof regle.contenu_regional_pct === 'number' && regle.regle.code !== 'WO' && (
              <p className="text-[var(--afcfta-muted)] text-xs">
                {t('calculator.origine.contenuRegional', { pct: regle.contenu_regional_pct })}
              </p>
            )}
          </>
        ) : (
          <p className="text-[var(--afcfta-muted)] text-xs">{t('calculator.origine.nonEtablie')}</p>
        ))}
      </div>
    </div>
  );
}
