/**
 * Onglet Analyse IA — le repli factuel doit ARRIVER À L'ÉCRAN.
 *
 * Ce test existe à cause d'une erreur précise, déjà commise dans ce chantier :
 * le repli sans clé d'API avait été vérifié au niveau du service, où il
 * fonctionnait, puis annoncé livré. La route le convertissait en HTTP 500, et
 * plus tard le composant n'affichait que `data.opportunities` — vide par
 * construction dans ce cas. La fonctionnalité n'atteignait aucun lecteur.
 *
 * Trois couches, trois tests ailleurs (service, route, ici). Vérifier une
 * couche ne vaut pas vérifier une fonctionnalité.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import AIAnalysis from './AIAnalysis';

vi.mock('axios');

vi.mock('../ui/select', async () => {
  const React = await import('react');
  const Ctx = React.createContext({ value: '', onValueChange: () => {} });
  const Select = ({ value = '', onValueChange, children }) => (
    <Ctx.Provider value={{ value, onValueChange }}>{children}</Ctx.Provider>
  );
  const SelectTrigger = React.forwardRef(({ children, ...p }, ref) => (
    <button ref={ref} type="button" role="combobox" {...p}>{children}</button>
  ));
  const SelectValue = ({ placeholder }) => {
    const { value } = React.useContext(Ctx);
    return <span>{value || placeholder}</span>;
  };
  const SelectContent = ({ children }) => <div>{children}</div>;
  const SelectItem = React.forwardRef(({ children, value, ...p }, ref) => {
    const { onValueChange } = React.useContext(Ctx);
    return (
      <button ref={ref} type="button" role="option" onClick={() => onValueChange(value)} {...p}>
        {children}
      </button>
    );
  });
  return { Select, SelectTrigger, SelectValue, SelectContent, SelectItem };
});

const DEGRADED = {
  country: 'Kenya',
  country_iso3: 'KEN',
  mode: 'export',
  ai_available: false,
  degraded: true,
  notice: "Analyse narrative indisponible : aucune clé d'API n'est configurée.",
  grounding: 'VERIFIED PRODUCTION OF Kenya — Tea (HS 0902): 2,687,200 tonnes',
  grounding_stats: { production_products: 20, oec_flows: 0, oec_year: null },
  opportunities: [],
};

const mockApi = (opportunitiesResponse) =>
  axios.get.mockImplementation((url) => {
    if (url.includes('/substitution/countries')) {
      return Promise.resolve({ data: { countries: [{ iso3: 'KEN', name: 'Kenya' }] } });
    }
    if (url.includes('/ai/health')) return Promise.resolve({ data: { ready: true } });
    if (url.includes('/ai/opportunities/')) return opportunitiesResponse();
    return Promise.resolve({ data: {} });
  });

async function lancerAnalyse() {
  await userEvent.click(await screen.findByRole('option', { name: /Kenya/ }));
  const boutons = screen.getAllByRole('button');
  const lancer = boutons.find((b) => /analyser/i.test(b.textContent || ''));
  await userEvent.click(lancer);
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('AIAnalysis', () => {
  it('affiche l’ancrage factuel quand l’analyse narrative est indisponible', async () => {
    mockApi(() => Promise.resolve({ data: DEGRADED }));
    render(<AIAnalysis language="fr" />);
    await lancerAnalyse();

    const bloc = await screen.findByTestId('ai-degraded');
    expect(bloc).toHaveTextContent(/aucune clé d'API n'est configurée/i);
    // Ce qui compte n'est pas l'avis d'indisponibilité mais la DONNÉE qui
    // reste servie malgré elle : sans cela, l'écran serait simplement vide.
    expect(screen.getByTestId('ai-degraded-grounding')).toHaveTextContent(/Tea \(HS 0902\)/);
    expect(bloc).toHaveTextContent(/20 produits de production réelle/);
  });

  it('montre l’erreur du service quand l’appel échoue vraiment', async () => {
    mockApi(() => Promise.reject({ response: { data: { detail: 'Service en panne' } } }));
    render(<AIAnalysis language="fr" />);
    await lancerAnalyse();
    expect(await screen.findByText('Service en panne')).toBeInTheDocument();
    expect(screen.queryByTestId('ai-degraded')).not.toBeInTheDocument();
  });

  it('ne laisse aucune clé i18n brute à l’écran', async () => {
    mockApi(() => Promise.resolve({ data: DEGRADED }));
    const { container } = render(<AIAnalysis language="fr" />);
    await lancerAnalyse();
    await screen.findByTestId('ai-degraded');
    expect(container.textContent).not.toMatch(/opportunities\.[a-zA-Z]+\./);
  });
});
