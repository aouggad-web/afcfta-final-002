import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { useAuth } from '../../context/AuthContext';
import { csrfFetch } from '../../services/csrf';
import NewsDashboard from './NewsDashboard';
import { EVENEMENT_FIL } from './TableauManager';

vi.mock('../../context/AuthContext', () => ({ useAuth: vi.fn() }));
vi.mock('../../services/csrf', () => ({ csrfFetch: vi.fn() }));

const ARTICLES = [
  {
    id: 'a1',
    title: 'Corridor Alger-Lagos',
    summary: 'Résumé illustré.',
    link: 'https://presse.exemple/1',
    source: 'APS',
    category: 'Commerce',
    region: 'Afrique',
    published_at: '2026-11-07T08:00:00',
    has_image: true,
    pinned: true,
  },
  {
    id: 'a2',
    title: 'Récolte record',
    summary: 'Résumé sans image.',
    link: 'https://presse.exemple/2',
    source: 'Ecofin',
    category: 'Agriculture',
    region: 'Afrique',
    published_at: '2026-11-06T08:00:00',
    has_image: false,
    pinned: false,
  },
];

const ETAT_REDACTION = {
  a_valider: [{ ...ARTICLES[1], id: 'q1', title: 'Dépêche en attente', has_image: false }],
  publies: ARTICLES,
  masques: [],
  ecartes: [],
  regles: [],
};

function repondre(url) {
  const corps = url.includes('/news/redaction')
    ? ETAT_REDACTION
    : url.includes('/news/by-region')
      ? { articles_by_region: {} }
      : url.includes('/news/by-category')
        ? { articles_by_category: {} }
        : url.includes('/country-of-the-week')
          ? { success: false }
          : { success: true, articles: ARTICLES, last_update: '2026-11-07T08:00:00' };
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(corps) });
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(repondre));
  csrfFetch.mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe('NewsDashboard — illustrations et une', () => {
  it('affiche la vignette copiée, son crédit et l’illustration maison sinon', async () => {
    useAuth.mockReturnValue({ user: null });
    const { container } = render(<NewsDashboard language="fr" />);

    await screen.findAllByText('Corridor Alger-Lagos');
    const image = container.querySelector('img[src$="/api/news/images/a1"]');
    expect(image).not.toBeNull();
    expect(image.getAttribute('loading')).toBe('lazy');
    expect(screen.getAllByText('© APS').length).toBeGreaterThan(0);
    expect(container.querySelector('img[src$="/api/news/images/a2"]')).toBeNull();
    expect(screen.getAllByTestId('illustration-maison').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/À la une/).length).toBeGreaterThan(0);
  });

  it('ne montre pas la rédaction à un visiteur ni à un abonné', async () => {
    useAuth.mockReturnValue({ user: { role: 'user' } });
    render(<NewsDashboard language="fr" />);
    await screen.findAllByText('Corridor Alger-Lagos');
    expect(screen.queryByTestId('redaction')).toBeNull();
    expect(fetch.mock.calls.some(([url]) => url.includes('/news/redaction'))).toBe(false);
  });
});

describe('NewsRedaction — panneau du rédacteur en chef', () => {
  it('montre la file à valider au compte admin et publie un article', async () => {
    useAuth.mockReturnValue({ user: { role: 'admin' } });
    render(<NewsDashboard language="fr" />);

    expect(await screen.findByTestId('redaction')).toBeInTheDocument();
    expect(await screen.findByText('Dépêche en attente')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Publier' }));
    await waitFor(() => expect(csrfFetch).toHaveBeenCalled());
    const [url, options] = csrfFetch.mock.calls[0];
    expect(url).toMatch(/\/api\/news\/redaction\/decision$/);
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({ id: 'q1', action: 'publier' });
  });

  it('épingle à la une et cherche l’image d’un article', async () => {
    useAuth.mockReturnValue({ user: { role: 'admin' } });
    render(<NewsDashboard language="fr" />);
    await screen.findByText('Dépêche en attente');

    fireEvent.click(screen.getByRole('button', { name: 'Publier à la une' }));
    await waitFor(() => expect(csrfFetch).toHaveBeenCalledTimes(1));
    expect(csrfFetch.mock.calls[0][0]).toMatch(/\/redaction\/epingle$/);

    // Pendant une action, le panneau désactive ses boutons (un clic serait
    // ignoré) : attendre qu'il ait rechargé la file avant le clic suivant.
    const chercher = screen.getByRole('button', { name: 'Chercher l’image' });
    await waitFor(() => expect(chercher).not.toBeDisabled());
    fireEvent.click(chercher);
    await waitFor(() => expect(csrfFetch).toHaveBeenCalledTimes(2));
    expect(csrfFetch.mock.calls[1][0]).toMatch(/\/redaction\/image$/);
    expect(JSON.parse(csrfFetch.mock.calls[1][1].body)).toEqual({ id: 'q1' });
  });

  it('lance la recherche des images manquantes depuis « Publiés »', async () => {
    useAuth.mockReturnValue({ user: { role: 'admin' } });
    csrfFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ok: true, recherches: 1 }),
    });
    render(<NewsDashboard language="fr" />);
    await screen.findByText('Dépêche en attente');

    fireEvent.click(screen.getByRole('tab', { name: /Publiés/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Chercher les images manquantes' }));
    await waitFor(() => expect(csrfFetch).toHaveBeenCalledTimes(1));
    expect(csrfFetch.mock.calls[0][0]).toMatch(/\/redaction\/images-manquantes$/);
    expect(await screen.findByRole('status')).toHaveTextContent('Recherche lancée pour 1 article(s)');
  });

  it('affiche le refus du serveur au rédacteur', async () => {
    useAuth.mockReturnValue({ user: { role: 'admin' } });
    csrfFetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({ detail: { error: 'image_refusee', message: 'aucune image d’aperçu dans la page' } }),
    });
    render(<NewsDashboard language="fr" />);
    await screen.findByText('Dépêche en attente');

    fireEvent.click(screen.getByRole('button', { name: 'Chercher l’image' }));
    expect(await screen.findByRole('status')).toHaveTextContent('aucune image d’aperçu dans la page');
  });
});

describe('Retrait d’articles du fil public', () => {
  it('le rédacteur retire un article depuis sa carte (après confirmation)', async () => {
    useAuth.mockReturnValue({ user: { role: 'admin' } });
    vi.stubGlobal('confirm', vi.fn(() => true));
    render(<NewsDashboard language="fr" />);
    await screen.findByText('Dépêche en attente');

    const boutons = await screen.findAllByRole('button', { name: 'Retirer du fil public' });
    fireEvent.click(boutons[0]);
    await waitFor(() => expect(csrfFetch).toHaveBeenCalledTimes(1));
    const [url, options] = csrfFetch.mock.calls[0];
    expect(url).toMatch(/\/api\/news\/redaction\/decision$/);
    expect(JSON.parse(options.body)).toEqual({ id: 'a1', action: 'masquer' });
  });

  it('prévient le tableau de bord de direction quand un article est retiré', async () => {
    useAuth.mockReturnValue({ user: { role: 'admin' } });
    vi.stubGlobal('confirm', vi.fn(() => true));
    const recus = [];
    const ecouter = (e) => recus.push(e.type);
    window.addEventListener(EVENEMENT_FIL, ecouter);
    try {
      render(<NewsDashboard language="fr" />);
      const boutons = await screen.findAllByRole('button', { name: 'Retirer du fil public' });
      fireEvent.click(boutons[0]);
      await waitFor(() => expect(recus).toEqual([EVENEMENT_FIL]));
    } finally {
      window.removeEventListener(EVENEMENT_FIL, ecouter);
    }
  });

  it('rien n’est retiré si le rédacteur annule', async () => {
    useAuth.mockReturnValue({ user: { role: 'admin' } });
    vi.stubGlobal('confirm', vi.fn(() => false));
    render(<NewsDashboard language="fr" />);
    const boutons = await screen.findAllByRole('button', { name: 'Retirer du fil public' });
    fireEvent.click(boutons[0]);
    expect(csrfFetch).not.toHaveBeenCalled();
  });

  it('un visiteur ne voit aucun bouton de retrait', async () => {
    useAuth.mockReturnValue({ user: { role: 'user' } });
    render(<NewsDashboard language="fr" />);
    await screen.findAllByText('Corridor Alger-Lagos');
    expect(screen.queryByRole('button', { name: 'Retirer du fil public' })).toBeNull();
  });

  it('dans « Publiés », retire plusieurs articles sélectionnés d’un coup', async () => {
    useAuth.mockReturnValue({ user: { role: 'admin' } });
    render(<NewsDashboard language="fr" />);
    await screen.findByText('Dépêche en attente');

    fireEvent.click(screen.getByRole('tab', { name: /Publiés/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Tout sélectionner' }));
    const retirer = screen.getByRole('button', { name: 'Retirer la sélection du fil public (2)' });
    fireEvent.click(retirer);
    await waitFor(() => expect(csrfFetch).toHaveBeenCalledTimes(2));
    expect(csrfFetch.mock.calls.map(([, o]) => JSON.parse(o.body))).toEqual([
      { id: 'a1', action: 'masquer' },
      { id: 'a2', action: 'masquer' },
    ]);
    expect(await screen.findByRole('status')).toHaveTextContent('2 article(s) retiré(s) du fil public');
  });
});

