import React from 'react';
import { pick } from '../../i18n/lang';

/**
 * Notes de l'Appendice IV attachées à la ligne appliquée (réponse de
 * GET /api/rules-of-origin/{code}, champ rules.applicable_notes) : notes
 * numérotées ou renvois à ces notes, notes de bas de page, ligne « Ex. » de
 * 2009.89. Les notes internes de construction du jeu de données et les
 * reformulations du texte de la ligne ne sont jamais servies. La note 2.5 est déjà
 * montrée avec le seuil applicable (55 %) : elle n'est pas répétée.
 */
export default function AppendixIvNotes({ roo, language = 'fr', className = '' }) {
  const thresholdNote = roo?.rules?.threshold_note_fr;
  const notes = (roo?.rules?.applicable_notes || []).filter((note) => note !== thresholdNote);
  if (!notes.length) return null;
  return (
    <div className={className} data-testid="appendix-iv-notes">
      <p className="font-semibold text-[var(--text)]">
        {pick(language, "Notes de l'Appendice IV", 'Appendix IV notes', 'ملاحظات التذييل الرابع')}
      </p>
      <ul className="list-disc ps-4 space-y-1">
        {notes.map((note) => (
          <li key={note}><bdi lang="fr" dir="ltr">{note}</bdi></li>
        ))}
      </ul>
    </div>
  );
}
