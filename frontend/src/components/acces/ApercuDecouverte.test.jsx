/**
 * Listes en aperçu, formule Découverte (audit D6, décision de l'exploitant du
 * 17/11/2026).
 *
 * Sans pays choisi, le serveur ne sert plus que l'identité et la position des
 * ports, aéroports, zones franches, corridors, intervenants et banques
 * (`apercu: true`). Les écrans doivent alors : le dire (bandeau), ne pas
 * planter sur les champs absents, et lire la fiche au serveur quand on
 * l'ouvre, puisque la liste ne la contient plus. La recherche par nom du
 * registre des banques filtre la liste reçue : envoyée au serveur, chaque
 * frappe comptait une recherche.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';

import { ApercuDecouverte } from './AccesModules';
import PortCard from '../logistics/PortCard';
import FreeZonesTab from '../logistics/FreeZonesTab';
import LandLogisticsTab from '../logistics/LandLogisticsTab';
import IntervenantsTab from '../logistics/IntervenantsTab';
import BankingInfoPanel from '../banking/BankingInfoPanel';

vi.mock('axios');
vi.mock('react-leaflet', () => {
  const Enveloppe = ({ children }) => <div>{children}</div>;
  const Rien = () => null;
  return {
    MapContainer: Enveloppe, Marker: Enveloppe, Popup: Enveloppe,
    TileLayer: Rien, Tooltip: Rien, Polyline: Rien, CircleMarker: Rien,
    useMap: () => ({ fitBounds: () => {}, setView: () => {} }),
  };
});

/** Répond à axios.get selon le début du chemin demandé. */
function repondre(table) {
  axios.get.mockImplementation((url) => {
    const chemin = url.replace(/^.*\/api/, '');
    const cle = Object.keys(table)
      .filter((c) => chemin.startsWith(c))
      .sort((a, b) => b.length - a.length)[0];
    return cle ? Promise.resolve({ data: table[cle] }) : Promise.resolve({ data: {} });
  });
}

const appels = () => axios.get.mock.calls.map(([url]) => url.replace(/^.*\/api/, ''));

beforeEach(() => {
  vi.clearAllMocks();
});

describe('bandeau et cartes', () => {
  it("explique l'aperçu et renvoie aux formules", () => {
    render(<ApercuDecouverte language="fr" />);
    expect(screen.getByRole('note').textContent).toMatch(/en choisissant un pays ou en ouvrant une fiche/);
    expect(screen.getByRole('link', { name: 'Voir les formules' }).getAttribute('href')).toBe('/pricing.html');
  });

  it("une carte de port en aperçu n'affiche que l'identité et le bouton de la fiche", () => {
    const port = { port_id: 'MAR-CAS-001', port_name: 'Port de Casablanca', country_name: 'Maroc', port_type: 'Hub Regional' };
    const ouvrir = vi.fn();
    render(<PortCard port={port} onOpenDetails={ouvrir} language="fr" apercu />);

    expect(screen.queryByText('📦 TEU')).toBeNull();
    expect(screen.queryByText('N/A')).toBeNull();
    fireEvent.click(screen.getByRole('button'));
    expect(ouvrir).toHaveBeenCalledWith(port);
  });
});

describe('zones franches', () => {
  it("s'affichent en aperçu sans planter sur les champs retirés", async () => {
    repondre({
      '/logistics/free-zones': {
        count: 1,
        apercu: true,
        zones: [{ id: 'tmsa', name: 'Tanger Med Zones', country: 'Maroc', country_iso: 'MAR', type: 'Zone franche', status: 'Opérationnel', location: { lat: 35.7, lon: -5.9 } }],
      },
    });
    render(<FreeZonesTab language="fr" />);

    expect(await screen.findByTestId('apercu-decouverte')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Liste/ }));
    expect(screen.getAllByText('Tanger Med Zones').length).toBeGreaterThan(0);
  });
});

describe('corridors terrestres', () => {
  it('lisent la fiche au serveur quand on ouvre un corridor', async () => {
    const apercu = { corridor_id: 'CORR-1', corridor_name: 'Corridor Abidjan-Ouagadougou', corridor_type: 'road', countries_spanned: ['CIV', 'BFA'], length_km: 1420, status: 'Opérationnel', importance: 'high', coordinates: [] };
    repondre({
      '/logistics/land/corridors/CORR-1': { ...apercu, nodes: [], operators: [], stats: {}, description: 'Fiche complète' },
      '/logistics/land/corridors': { count: 1, apercu: true, corridors: [apercu] },
    });
    render(<LandLogisticsTab language="fr" />);

    expect(await screen.findByTestId('apercu-decouverte')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Liste/ }));
    const carte = (await screen.findAllByText('Corridor Abidjan-Ouagadougou'))[0].closest('.shadow-lg');
    fireEvent.click(carte.querySelector('button'));
    await waitFor(() => expect(appels()).toContain('/logistics/land/corridors/CORR-1'));
  });
});

describe('intervenants logistiques', () => {
  it("ouvrent leur fiche au serveur, avec les contacts absents de l'aperçu", async () => {
    repondre({
      '/logistics/operators/msc': { id: 'msc', name: 'MSC', type_label: 'Armateur mondial', contacts: { website: 'https://www.msc.com' } },
      '/logistics/operators': {
        apercu: true,
        operators: { armateurs: [{ id: 'msc', name: 'MSC', type: 'armateur', type_label: 'Armateur mondial', hq: 'Genève' }] },
        summary: { total_operators: 1, by_category: { armateurs: 1 }, categories: ['armateurs'] },
      },
    });
    render(<IntervenantsTab language="fr" />);

    expect(await screen.findByTestId('apercu-decouverte')).toBeTruthy();
    expect(screen.queryByText('https://www.msc.com')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: /Voir la fiche/ }));
    expect(await screen.findAllByText(/msc\.com/)).not.toHaveLength(0);
    expect(appels()).toContain('/logistics/operators/msc');
  });
});

describe('registre des banques', () => {
  it('filtre par nom sans interroger le serveur', async () => {
    repondre({
      '/banking/countries': [],
      '/banking/trade-finance/instruments': [],
      '/banking/register': {
        total: 2,
        apercu: true,
        results: [
          { type: 'central', country_code: 'MA', country_name: 'Maroc', name: 'Bank Al-Maghrib' },
          { type: 'commercial', country_code: 'NG', country_name: 'Nigeria', name: 'Ecobank Nigeria' },
        ],
      },
    });
    render(<BankingInfoPanel language="fr" />);
    fireEvent.click(screen.getByRole('button', { name: /Registre/ }));

    expect(await screen.findByText('Ecobank Nigeria')).toBeTruthy();
    expect(screen.getByTestId('apercu-decouverte')).toBeTruthy();
    const avant = appels().filter((u) => u.startsWith('/banking/register')).length;

    fireEvent.change(screen.getByPlaceholderText(/Rechercher/), { target: { value: 'ecob' } });

    expect(screen.queryByText('Bank Al-Maghrib')).toBeNull();
    expect(screen.getByText('Ecobank Nigeria')).toBeTruthy();
    const registre = appels().filter((u) => u.startsWith('/banking/register'));
    expect(registre).toHaveLength(avant);
    expect(registre.some((u) => u.includes('search='))).toBe(false);
  });
});
