import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import DedouanementSacuQuestion from './DedouanementSacuQuestion';
import { buildCalculRequestBody, dedouanementSacuPropose } from './unifiedCalculator';

describe('DedouanementSacuQuestion', () => {
  it('décochée par défaut, avec son cadre réglementaire', () => {
    render(<DedouanementSacuQuestion />);
    expect(screen.getByRole('checkbox')).not.toBeChecked();
    const cadre = screen.getByTestId('dedouanement-sacu-cadre');
    expect(cadre).toHaveTextContent('art. 19 et 31.4');
    expect(cadre).toHaveTextContent('transit sous douane');
  });

  it('remonte la case cochée', async () => {
    const onChange = vi.fn();
    render(<DedouanementSacuQuestion onChange={onChange} />);
    await userEvent.click(screen.getByRole('checkbox'));
    expect(onChange).toHaveBeenCalledWith(true);
  });
});

describe('deja_dedouane_sacu', () => {
  it('proposé pour une destination SACU seulement', () => {
    expect(['ZAF', 'BWA', 'LSO', 'NAM', 'SWZ'].every(dedouanementSacuPropose)).toBe(true);
    expect(dedouanementSacuPropose('KEN')).toBe(false);
  });

  it('envoyé coché et vers la SACU, jamais ailleurs', () => {
    const base = { hsCode: '33030090', cifValue: 1000 };
    expect(buildCalculRequestBody({ ...base, destinationISO3: 'BWA', dejaDedouaneSacu: true }))
      .toHaveProperty('deja_dedouane_sacu', true);
    expect(buildCalculRequestBody({ ...base, destinationISO3: 'BWA', dejaDedouaneSacu: false }))
      .not.toHaveProperty('deja_dedouane_sacu');
    expect(buildCalculRequestBody({ ...base, destinationISO3: 'KEN', dejaDedouaneSacu: true }))
      .not.toHaveProperty('deja_dedouane_sacu');
  });
});
