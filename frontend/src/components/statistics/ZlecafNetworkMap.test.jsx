import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import geo from '../../data/zlecafNetworkGeo.json';

const RESEAU = {
  date: '2026-10-08',
  niveaux: [
    'non_signataire', 'signe_non_ratifie', 'ratifie', 'offre_tarifaire',
    'instrument_adopte', 'deploiement',
  ],
  pib_annee: 2024,
  pib_source: 'Banque mondiale (API WDI), PIB en dollars US courants',
  pays: [
    {
      iso3: 'DZA', iso2: 'DZ', nom: 'Algérie', statut: 'deploiement', pib_usd: 2.693e11,
      preuves: [{
        niveau: 'deploiement', source: 'Circulaire DGD n° 482/DGD/SP/D.042/24',
        url: 'https://example.org/482', note: 'Neuf origines admises.',
      }],
    },
    {
      iso3: 'TUN', iso2: 'TN', nom: 'Tunisie', statut: 'deploiement', pib_usd: 5.3e10,
      preuves: [{ niveau: 'deploiement', source: 'Texte TA n°016/2023' }],
    },
    {
      iso3: 'ERI', iso2: 'ER', nom: 'Érythrée', statut: 'non_signataire', pib_usd: null,
      preuves: [{ niveau: 'non_signataire', source: 'the dtic / SARS, mars 2026' }],
    },
    {
      iso3: 'ESH', iso2: 'EH', nom: 'RASD', statut: 'ratifie', pib_usd: null,
      preuves: [{ niveau: 'ratifie', source: 'the dtic / SARS, mars 2026' }],
    },
  ],
  liaisons: [
    { importateur: 'DZA', origine: 'TUN', source: 'Circulaire DGD n° 482/DGD/SP/D.042/24' },
    { importateur: 'TUN', origine: 'DZA', source: 'Texte TA n°016/2023' },
  ],
};

vi.mock('axios', () => ({ default: { get: vi.fn() } }));

import axios from 'axios';
import ZlecafNetworkMap from './ZlecafNetworkMap';

beforeEach(() => {
  axios.get.mockReset();
  axios.get.mockResolvedValue({ data: RESEAU });
});

describe('ZlecafNetworkMap', () => {
  it('la géographie couvre les 54 États signataires ou non, sauf la RASD', () => {
    expect(Object.keys(geo.capitals)).toHaveLength(54);
    expect(geo.capitals.ESH).toBeUndefined();
    expect(geo.without_capital).toEqual(['ESH']);
    expect(geo.capitals.DZA.name_fr).toBe('Alger');
  });

  it('interroge l’API réseau dans la langue de l’interface', async () => {
    render(<ZlecafNetworkMap language="en" />);
    await waitFor(() => expect(axios.get).toHaveBeenCalledWith('/api/zlecaf/network?lang=en'));
  });

  it('compte les États par statut dans la légende', async () => {
    render(<ZlecafNetworkMap language="fr" />);
    const legende = await screen.findByTestId('zn-legend-deploiement');
    expect(legende).toHaveTextContent('2');
    expect(screen.getByTestId('zn-legend-non_signataire')).toHaveTextContent('1');
    expect(screen.getByTestId('zn-legend-offre_tarifaire')).toHaveTextContent('0');
  });

  it('dessine un point par capitale connue, pas pour la RASD', async () => {
    render(<ZlecafNetworkMap language="fr" />);
    expect(await screen.findByTestId('zn-node-DZA')).toBeInTheDocument();
    expect(screen.getByTestId('zn-node-ERI')).toBeInTheDocument();
    expect(screen.queryByTestId('zn-node-ESH')).toBeNull();
    // La RASD reste dans le tableau, avec la raison de l'absence de point.
    expect(within(screen.getByTestId('zn-row-ESH')).getByText(/pas de point/)).toBeInTheDocument();
  });

  it('affiche statut, PIB, liaisons et preuve au survol', async () => {
    render(<ZlecafNetworkMap language="fr" />);
    fireEvent.mouseEnter(await screen.findByTestId('zn-node-DZA'));
    const tip = screen.getByTestId('zn-tooltip');
    expect(tip).toHaveTextContent('Algérie');
    expect(tip).toHaveTextContent('Alger');
    expect(tip).toHaveTextContent('Déploiement');
    expect(tip).toHaveTextContent(/269,3\s?Md\s?\$/);
    expect(tip).toHaveTextContent('applique la préférence à 1 État(s)');
    expect(tip).toHaveTextContent('Circulaire DGD');
  });

  it('dit « non disponible » plutôt que d’inventer un PIB', async () => {
    render(<ZlecafNetworkMap language="fr" />);
    fireEvent.focus(await screen.findByTestId('zn-node-ERI'));
    expect(screen.getByTestId('zn-tooltip')).toHaveTextContent('PIB 2024 non disponible');
  });

  it('épingle au clavier et ouvre le lien de la source', async () => {
    render(<ZlecafNetworkMap language="fr" />);
    const noeud = await screen.findByTestId('zn-node-DZA');
    fireEvent.keyDown(noeud, { key: 'Enter' });
    expect(noeud).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('link', { name: /Circulaire DGD/ })).toHaveAttribute('href', 'https://example.org/482');
    // Épinglée, l'infobulle montre aussi la note de la preuve.
    expect(screen.getByTestId('zn-tooltip')).toHaveTextContent('Neuf origines admises.');
    fireEvent.keyDown(noeud, { key: 'Escape' });
    expect(noeud).toHaveAttribute('aria-pressed', 'false');
  });

  it('« Fermer » rend le focus au point épinglé', async () => {
    render(<ZlecafNetworkMap language="fr" />);
    const noeud = await screen.findByTestId('zn-node-DZA');
    fireEvent.click(noeud);
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));
    expect(noeud).toHaveAttribute('aria-pressed', 'false');
    expect(document.activeElement).toBe(noeud);
  });

  it('un point sélectionné reste pleinement visible quand un statut est isolé', async () => {
    render(<ZlecafNetworkMap language="fr" />);
    fireEvent.click(await screen.findByTestId('zn-legend-non_signataire'));
    expect(screen.getByTestId('zn-node-DZA')).toHaveAttribute('opacity', '0.18');
    fireEvent.focus(screen.getByTestId('zn-node-DZA'));
    expect(screen.getByTestId('zn-node-DZA')).toHaveAttribute('opacity', '1');
  });

  it('en anglais, les limites et la source du PIB sont traduites', async () => {
    render(<ZlecafNetworkMap language="en" />);
    expect(await screen.findByText(/Data limitations/)).toBeInTheDocument();
    expect(screen.getByText(/World Bank \(WDI API\)/)).toBeInTheDocument();
    expect(screen.queryByText(/Banque mondiale/)).toBeNull();
    expect(screen.queryByText(/domaine public/)).toBeNull();
  });

  it('signale l’échec du chargement', async () => {
    axios.get.mockRejectedValueOnce(new Error('boom'));
    render(<ZlecafNetworkMap language="fr" />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Impossible de charger');
  });
});
