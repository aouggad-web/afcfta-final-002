import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import TableauManager, { EVENEMENT_FIL } from './TableauManager';

const serie = (debut, avantDernier, dernier) => [debut, ...Array(10).fill(debut), avantDernier, dernier];

const APERCU = {
  cours: {
    mois: '2026-10',
    mois_serie: [],
    produits: {
      brent: { famille: 'hydrocarbures', serie: serie(64.7, 116.8, 125) },
      or: { famille: 'minerais', serie: serie(4058, 4319, 4105) },
      cuivre: { famille: 'minerais', serie: serie(10740, 14474, 14508) },
      phosphate: { famille: 'engrais', serie: serie(152.5, 170, 170) },
      gaz_europe: { famille: 'hydrocarbures', serie: serie(10.89, 25.42, 28.5) },
      minerai_fer: { famille: 'minerais', serie: serie(103.5, 97.7, 90.8) },
      uree: { famille: 'engrais', serie: serie(394.4, 407.5, 420) },
    },
  },
  indices: [
    { cle: 'dzair', ouverture: 3809.446, cloture: 3812.105, date: '2026-11-08', variation_pct: 0.07, a_jour: true },
    { cle: 'brvm_c', ouverture: 520.22, cloture: 520.74, date: null, variation_pct: 0.1, a_jour: false },
    { cle: 'ngx_asi', ouverture: null, cloture: 248877.22, date: null, variation_pct: null, a_jour: true },
  ],
};

const ARTICLES = [
  { id: 'a1', title: 'Sonatrach signe un contrat gazier', link: 'https://p/1', source: 'Agence Ecofin', category: 'Énergie', published_at: new Date().toISOString(), has_image: false },
  { id: 'a2', title: 'La BAD finance un corridor', link: 'https://p/2', source: 'Financial Afrik', category: 'Finance', published_at: new Date().toISOString(), has_image: false },
  { id: 'a3', title: 'Récolte de cacao en hausse', link: 'https://p/3', source: 'Africanews', category: 'Agriculture', published_at: new Date().toISOString(), has_image: false },
];

const espaces = (t) => t.replace(/[\s  ]+/g, ' ').trim();

function servir({ marches = APERCU, news = { articles: ARTICLES } } = {}) {
  global.fetch = vi.fn((url) => {
    if (url.endsWith('/marches/apercu')) {
      return marches ? Promise.resolve({ ok: true, json: () => Promise.resolve(marches) }) : Promise.reject(new Error('panne'));
    }
    if (url.endsWith('/news')) return Promise.resolve({ ok: true, json: () => Promise.resolve(news) });
    return Promise.reject(new Error(url));
  });
}

describe('TableauManager', () => {
  const fetchOriginal = global.fetch;
  beforeEach(() => servir());
  afterEach(() => {
    global.fetch = fetchOriginal;
  });

  it('affiche les cours clés avec leur variation sur un mois', async () => {
    render(<TableauManager language="fr" />);
    const brent = await screen.findByTestId('tuile-brent');
    expect(espaces(brent.textContent)).toContain('125,0');
    expect(espaces(brent.textContent)).toContain('7,0 %');
    expect(within(brent).getByText(/7,0/).closest('[data-sens]').dataset.sens).toBe('hausse');
    expect(within(screen.getByTestId('tuile-or')).getByText(/5,0/).closest('[data-sens]').dataset.sens).toBe('baisse');
    // Cacao absent de l'aperçu : pas de tuile vide.
    expect(screen.queryByTestId('tuile-cacao')).toBeNull();
    expect(screen.getByText(/octobre 2026/)).toBeTruthy();
  });

  it("donne les points d'ouverture et de clôture de chaque bourse", async () => {
    render(<TableauManager language="fr" />);
    const dzair = await screen.findByTestId('indice-dzair');
    const [nom, ouverture, cloture, , seance] = dzair.querySelectorAll('td');
    expect(espaces(nom.textContent)).toContain('DZAIR INDEX');
    expect(espaces(ouverture.textContent)).toBe('3 809,45');
    expect(espaces(cloture.textContent)).toBe('3 812,11');
    expect(espaces(seance.textContent)).toBe('8 nov.');
    // NGX sans clôture de la veille : ouverture vide, expliquée.
    const ngx = screen.getByTestId('indice-ngx_asi').querySelectorAll('td');
    expect(ngx[1].querySelector('[aria-hidden="true"]').textContent).toBe('—');
    expect(ngx[1].textContent).toContain('Clôture de la séance précédente non disponible');
    expect(espaces(ngx[4].textContent)).toBe('dernière séance');
    // Source en panne : dernière valeur lue, signalée à l'écran et aux lecteurs d'écran.
    const brvm = screen.getByTestId('indice-brvm_c').querySelectorAll('td');
    expect(brvm[2].textContent).toContain('dernière valeur lue');
    expect(screen.getByText(/^\* Source momentanément indisponible/)).toBeTruthy();
    expect(screen.getByText(/^— Clôture de la séance précédente/)).toBeTruthy();
    expect(screen.queryByText(/Casablanca/)).toBeNull();
  });

  it('filtre les cours par famille sans répéter le bandeau', async () => {
    render(<TableauManager language="fr" />);
    await screen.findByTestId('cours-gaz_europe');
    expect(screen.queryByTestId('cours-brent')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Engrais' }));
    expect(screen.getByTestId('cours-uree')).toBeTruthy();
    expect(screen.getByTestId('cours-phosphate')).toBeTruthy();
    expect(screen.queryByTestId('cours-gaz_europe')).toBeNull();
  });

  it('fait défiler les dépêches et met un article à la une, filtrable par rubrique', async () => {
    render(<TableauManager language="fr" />);
    const ligne = await screen.findByRole('region', { name: 'Dernières dépêches' });
    expect(within(ligne).getAllByText('Sonatrach signe un contrat gazier')).toHaveLength(2);
    expect(screen.getByTestId('article-une').textContent).toContain('Sonatrach');
    fireEvent.click(screen.getByRole('button', { name: 'Finance' }));
    expect(screen.getByTestId('article-une').textContent).toContain('La BAD finance');
  });

  it('parle arabe et garde les chiffres de gauche à droite', async () => {
    render(<TableauManager language="ar" />);
    const dzair = await screen.findByTestId('indice-dzair');
    expect(dzair.textContent).toContain('الجزائر');
    expect(dzair.textContent).not.toMatch(/[٠-٩۰-۹]/);
    expect(dzair.querySelectorAll('td')[2].textContent).toMatch(/3,812\.11/);
    expect(screen.getByText('البورصات الأفريقية')).toBeTruthy();
    expect(screen.getByRole('region', { name: 'آخر الأخبار' }).getAttribute('dir')).toBe('rtl');
    expect(dzair.querySelector('bdi[dir="ltr"]')).toBeTruthy();
  });

  it('reste affiché quand les marchés ne répondent pas', async () => {
    servir({ marches: null });
    render(<TableauManager language="fr" />);
    await screen.findByTestId('article-une');
    expect(screen.queryByText('Bourses africaines')).toBeNull();
    expect(screen.getByText("Marchés africains en un coup d'œil")).toBeTruthy();
  });
});

describe('TableauManager — cas limites', () => {
  const fetchOriginal = global.fetch;
  afterEach(() => {
    global.fetch = fetchOriginal;
  });

  it("un mois non publié laisse la variation vide au lieu de la calculer contre un autre mois", async () => {
    const brent = [60, 70, 70, 70, 70, 70, 70, 70, 70, 70, 100, null, 125];
    const cuivre = [null, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11];
    servir({
      marches: {
        ...APERCU,
        cours: { ...APERCU.cours, produits: { brent: { famille: 'hydrocarbures', serie: brent }, cuivre: { famille: 'minerais', serie: cuivre } } },
      },
    });
    render(<TableauManager language="fr" />);
    const tuile = await screen.findByTestId('tuile-brent');
    expect(espaces(tuile.textContent)).not.toContain('25,0 %');
    expect(espaces(tuile.textContent)).toContain('sur 12 mois +108 %');
    const cuivreTuile = screen.getByTestId('tuile-cuivre');
    expect(espaces(cuivreTuile.textContent)).toContain('10,0 %');
    expect(espaces(cuivreTuile.textContent)).toContain('sur 12 mois —');
  });

  it("la pastille suit le chiffre affiché : 0,04 % est « stable », 0,06 % une hausse de 0,1 %", async () => {
    servir({
      marches: {
        ...APERCU,
        indices: [
          { cle: 'dzair', ouverture: 1000, cloture: 1000.4, date: null, variation_pct: 0.04, a_jour: true },
          { cle: 'nse20', ouverture: 1000, cloture: 1000.6, date: null, variation_pct: 0.06, a_jour: true },
        ],
      },
    });
    render(<TableauManager language="fr" />);
    const stable = (await screen.findByTestId('indice-dzair')).querySelector('[data-sens]');
    expect(stable.dataset.sens).toBe('stable');
    expect(espaces(stable.textContent)).toContain('0,0 %');
    expect(screen.getByTestId('indice-nse20').querySelector('[data-sens]').dataset.sens).toBe('hausse');
  });

  it('la ligne des dépêches se met en pause au bouton', async () => {
    servir();
    render(<TableauManager language="fr" />);
    const ligne = await screen.findByRole('region', { name: 'Dernières dépêches' });
    const bouton = screen.getByRole('button', { name: 'Mettre en pause le défilement' });
    fireEvent.click(bouton);
    expect(ligne.className).toContain('en-pause');
    expect(screen.getByRole('button', { name: 'Reprendre le défilement' }).getAttribute('aria-pressed')).toBe('true');
  });

  it('relit le fil quand le rédacteur retire un article', async () => {
    servir();
    render(<TableauManager language="fr" />);
    await screen.findByTestId('article-une');
    const appels = () => global.fetch.mock.calls.filter(([u]) => u.endsWith('/news')).length;
    expect(appels()).toBe(1);
    window.dispatchEvent(new Event(EVENEMENT_FIL));
    await waitFor(() => expect(appels()).toBe(2));
  });

  it("lit l'heure des articles en UTC (le fil la donne sans fuseau)", async () => {
    const ilYaDeuxHeures = new Date(Date.now() - 2 * 3600000).toISOString().slice(0, 19); // sans « Z »
    servir({ news: { articles: [{ ...ARTICLES[0], published_at: ilYaDeuxHeures }] } });
    render(<TableauManager language="fr" />);
    expect((await screen.findByTestId('article-une')).textContent).toContain('il y a 2 heures');
  });
});
