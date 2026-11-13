import React from 'react';
import { pick } from '../../i18n/lang';

/**
 * Base légale et référence d'une règle d'origine (réponse de
 * GET /api/rules-of-origin/{code}) : rattachement de la position saisie à la
 * ligne de l'Appendice IV, instrument, articles de l'Annexe 2, notes, source.
 * Partagé par le calculateur et l'onglet Règles d'origine.
 */
const RATTACHEMENT = {
  subheading: [
    'règle propre à cette sous-position',
    'rule specific to this subheading',
    'قاعدة خاصة بهذا البند الفرعي',
  ],
  heading: [
    'aucune règle propre à la sous-position : règle de la position',
    'no subheading-specific rule: the heading rule applies',
    'لا توجد قاعدة خاصة بالبند الفرعي: تُطبَّق قاعدة البند',
  ],
  chapter: [
    'aucune règle propre à la position : règle par défaut du chapitre',
    'no heading-specific rule: the chapter default rule applies',
    'لا توجد قاعدة خاصة بالبند: تُطبَّق القاعدة الافتراضية للفصل',
  ],
};

export default function OriginLegalReference({ roo, language = 'fr', className = '' }) {
  const ref = roo?.legal_reference;
  if (!ref) return null;
  const rattachement = RATTACHEMENT[ref.match_type];
  return (
    <div className={`space-y-1 ${className}`} data-testid="origin-legal-reference">
      <p className="font-semibold text-[var(--text)]">
        {pick(language, 'Base légale et référence', 'Legal basis and reference', 'الأساس القانوني والمرجع')}
      </p>
      <p data-testid="origin-applied-to">
        {pick(language, 'Position', 'Code', 'الرمز')} <bdi dir="ltr">{roo.hs_code}</bdi> →{' '}
        <bdi lang="fr" dir="ltr">Appendice IV, {ref.location_fr}</bdi>
        {rattachement && <> ({pick(language, ...rattachement)})</>}
      </p>
      <p><bdi lang="fr" dir="ltr">{ref.instrument_fr}</bdi></p>
      {(ref.articles_fr || []).map((article) => (
        <p key={article}><bdi lang="fr" dir="ltr">{article}</bdi></p>
      ))}
      {(ref.notes_fr || []).map((note) => (
        <p key={note}><bdi lang="fr" dir="ltr">{note}</bdi></p>
      ))}
      <p>
        {pick(language, 'Source consultée', 'Source consulted', 'المصدر المعتمد')} ·{' '}
        <bdi lang="fr" dir="ltr">{ref.source_version}</bdi>
      </p>
    </div>
  );
}
