import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('axios', () => {
  const get = vi.fn(() =>
    Promise.resolve({
      data: {
        query: 'huile de palme',
        count: 1,
        source: 'OMD — Index alphabétique du Système Harmonisé (7e éd. 2022)',
        results: [
          {
            label: 'PALME — (HUILE DE)',
            term: 'PALME',
            qualifier: '(HUILE DE)',
            is_range: false,
            see_also: null,
            codes_display: '1511, 1516, 1520',
            codes: [
              { code: '1511', level: 'heading', official_label: '', chapter: '15', chapter_name: 'Graisses' },
              { code: '151190', level: 'subheading', official_label: 'Huile de palme', chapter: '15', chapter_name: 'Graisses' },
            ],
          },
        ],
      },
    })
  );
  return { default: { get } };
});

import axios from 'axios';
import ProductHSSearch from './ProductHSSearch';

beforeEach(() => axios.get.mockClear());

describe('ProductHSSearch', () => {
  it('ne cherche pas en dessous de 2 caractères', async () => {
    render(<ProductHSSearch lang="fr" />);
    await userEvent.type(screen.getByTestId('product-hs-input'), 'a');
    await new Promise((r) => setTimeout(r, 350));
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('affiche le produit et ses codes SH depuis l’index OMD', async () => {
    render(<ProductHSSearch lang="fr" />);
    await userEvent.type(screen.getByTestId('product-hs-input'), 'huile de palme');
    await waitFor(() => expect(screen.getByText('PALME — (HUILE DE)')).toBeInTheDocument());
    expect(screen.getByText('1511')).toBeInTheDocument();
    expect(screen.getByText('151190')).toBeInTheDocument();
  });

  it('appelle onSelect avec le code cliqué', async () => {
    const onSelect = vi.fn();
    render(<ProductHSSearch lang="fr" onSelect={onSelect} />);
    await userEvent.type(screen.getByTestId('product-hs-input'), 'huile de palme');
    await waitFor(() => expect(screen.getByText('151190')).toBeInTheDocument());
    await userEvent.click(screen.getByText('151190'));
    expect(onSelect).toHaveBeenCalledWith('151190', expect.objectContaining({ term: 'PALME' }));
  });
});
