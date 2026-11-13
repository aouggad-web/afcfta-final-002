/**
 * Notes de l'Appendice IV de la ligne appliquée : notes de source seulement,
 * la note 2.5 (déjà montrée comme seuil à confirmer) n'est pas répétée.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import AppendixIvNotes from './AppendixIvNotes';

const NOTE_25 =
  "Note 2.5 de l'Appendice IV: la valeur des matières non originaires sera automatiquement ramenée de 60 % à 55 % à la fin d'une période de cinq (5) ans à compter du 1er janvier 2021.";

describe("Notes de l'Appendice IV", () => {
  it('liste les notes de la ligne (ex-chapitre 19, réponse de GET /api/rules-of-origin/190219)', () => {
    const roo = {
      rules: {
        threshold_note_fr: null,
        applicable_notes: ['Condition: les produits à base de blé du chapitre 11 utilisés doivent être originaires'],
      },
    };
    render(<AppendixIvNotes roo={roo} language="fr" />);

    expect(screen.getByText("Notes de l'Appendice IV")).toBeInTheDocument();
    expect(
      screen.getByText('Condition: les produits à base de blé du chapitre 11 utilisés doivent être originaires')
    ).toBeInTheDocument();
  });

  it('ne répète pas la note 2.5, déjà montrée comme seuil à confirmer (84.14)', () => {
    const roo = { rules: { threshold_note_fr: NOTE_25, applicable_notes: [NOTE_25] } };
    const { container } = render(<AppendixIvNotes roo={roo} language="fr" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('titre traduit en anglais et en arabe, notes en français', () => {
    const roo = { rules: { applicable_notes: ['Couvre 41.07 à 41.13'] } };
    const { rerender } = render(<AppendixIvNotes roo={roo} language="en" />);
    expect(screen.getByText('Appendix IV notes')).toBeInTheDocument();
    rerender(<AppendixIvNotes roo={roo} language="ar" />);
    expect(screen.getByText('ملاحظات التذييل الرابع')).toBeInTheDocument();
    expect(screen.getByText('Couvre 41.07 à 41.13').closest('bdi')).toHaveAttribute('lang', 'fr');
  });
});
