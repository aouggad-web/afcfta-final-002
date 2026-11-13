/**
 * Notes de l'Appendice IV de la ligne appliquée : notes de source seulement,
 * la note 2.5 (déjà montrée avec le seuil applicable) n'est pas répétée.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import AppendixIvNotes from './AppendixIvNotes';

// Notes de bas de page 27 et 28 de l'Appendice IV (p. 68), mot pour mot.
const CH61 =
  "Le chapitre 61 doit encore être finalisé. La règle du chapitre a été approuvée, mais les États membres disposent d'une certaine souplesse pour soumettre des exceptions pour les rubriques et sous-rubriques";
const CH62 = 'Adopté par la 2ème réunion extraordinaire du Conseil des Ministres de la ZLECAf (mai 2023)';

const NOTE_25 =
  "Note 2.5 de l'Appendice IV: la valeur des matières non originaires sera automatiquement ramenée de 60 % à 55 % à la fin d'une période de cinq (5) ans à compter du 1er janvier 2021.";

describe("Notes de l'Appendice IV", () => {
  it('liste les notes de la ligne (chapitre 61, réponse de GET /api/rules-of-origin/610910)', () => {
    const roo = {
      rules: {
        threshold_note_fr: null,
        applicable_notes: [CH61],
      },
    };
    render(<AppendixIvNotes roo={roo} language="fr" />);

    expect(screen.getByText("Notes de l'Appendice IV")).toBeInTheDocument();
    expect(screen.getByText(CH61)).toBeInTheDocument();
  });

  it('ne répète pas la note 2.5, déjà montrée avec le seuil applicable (84.14)', () => {
    const roo = { rules: { threshold_note_fr: NOTE_25, applicable_notes: [NOTE_25] } };
    const { container } = render(<AppendixIvNotes roo={roo} language="fr" />);
    expect(container).toBeEmptyDOMElement();
  });

  it('titre traduit en anglais et en arabe, notes en français', () => {
    const roo = { rules: { applicable_notes: [CH62] } };
    const { rerender } = render(<AppendixIvNotes roo={roo} language="en" />);
    expect(screen.getByText('Appendix IV notes')).toBeInTheDocument();
    rerender(<AppendixIvNotes roo={roo} language="ar" />);
    expect(screen.getByText('ملاحظات التذييل الرابع')).toBeInTheDocument();
    expect(screen.getByText(CH62).closest('bdi')).toHaveAttribute('lang', 'fr');
  });
});
