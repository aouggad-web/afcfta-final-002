import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import ExpeditionSacuQuestion from './ExpeditionSacuQuestion';
import { expeditionSacuRequise, paysExpeditionPour } from './unifiedCalculator';

describe('ExpeditionSacuQuestion', () => {
  it('affiche la spécificité et son cadre réglementaire', () => {
    render(<ExpeditionSacuQuestion />);
    expect(screen.getByLabelText('Je ne sais pas')).toBeChecked();
    const cadre = screen.getByTestId('expedition-sacu-cadre');
    expect(cadre).toHaveTextContent('majorée de 10 %');
    expect(cadre).toHaveTextContent('Value-Added Tax Act 89 of 1991, s.13(2)(a) et (b)');
    expect(cadre).toHaveTextContent('CE-G06');
  });

  it('remonte la réponse choisie', async () => {
    const onChange = vi.fn();
    render(<ExpeditionSacuQuestion onChange={onChange} />);
    await userEvent.click(screen.getByLabelText('Oui'));
    expect(onChange).toHaveBeenCalledWith('yes');
  });
});

describe('paysExpeditionPour', () => {
  it('ne concerne que la destination ZAF et une origine BWA/LSO/NAM/SWZ', () => {
    expect(expeditionSacuRequise('ZAF', 'BWA')).toBe(true);
    expect(expeditionSacuRequise('ZAF', 'KEN')).toBe(false);
    expect(expeditionSacuRequise('NAM', 'BWA')).toBe(false);
  });

  it('oui → l’origine ; non → AUTRE ; inconnu → rien', () => {
    expect(paysExpeditionPour('ZAF', 'NAM', 'yes')).toBe('NAM');
    expect(paysExpeditionPour('ZAF', 'NAM', 'no')).toBe('AUTRE');
    expect(paysExpeditionPour('ZAF', 'NAM', 'unknown')).toBeUndefined();
    expect(paysExpeditionPour('ZAF', 'KEN', 'yes')).toBeUndefined();
  });
});
