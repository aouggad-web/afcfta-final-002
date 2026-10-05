// Pilote le calculateur dans un Chromium sans écran (Playwright).
//
//   node .claude/skills/run-afcfta-final-002/driver.mjs calcul [origine] [destination] [code] [cif]
//   node .claude/skills/run-afcfta-final-002/driver.mjs page [onglet]
//
// origine / destination : début du nom affiché dans la liste (« Tunisie », « Alg »).
// Captures dans $SHOTS (défaut /tmp/afcfta-shots). Frontend : $APP_URL (défaut
// http://127.0.0.1:5000, le serveur Vite qui relaie /api vers le backend).
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';

const require = createRequire(import.meta.url);
let playwright;
try {
  playwright = require('playwright');
} catch {
  // Playwright n'est pas une dépendance du frontend : on prend l'installation globale.
  playwright = require(`${execSync('npm root -g').toString().trim()}/playwright`);
}

const APP = process.env.APP_URL || 'http://127.0.0.1:5000';
const SHOTS = process.env.SHOTS || '/tmp/afcfta-shots';
mkdirSync(SHOTS, { recursive: true });

const [cmd = 'calcul', ...args] = process.argv.slice(2);
const browser = await playwright.chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } });
const erreurs = [];
const appels = [];
page.on('console', (m) => { if (m.type() === 'error') erreurs.push(m.text()); });
page.on('response', (r) => { if (r.url().includes('/api/')) appels.push(`${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}`); });
page.on('requestfailed', (r) => erreurs.push(`échec ${r.url().slice(0, 120)} : ${r.failure()?.errorText}`));
page.on('response', (r) => { if (r.status() >= 500 && !r.url().includes('/api/')) erreurs.push(`${r.status()} ${r.url().slice(0, 120)}`); });

async function ouvrir(onglet) {
  await page.goto(APP, { waitUntil: 'networkidle', timeout: 90000 });
  if (onglet) {
    await page.click(`[data-testid=sidebar-nav-${onglet}]`);
    await page.waitForLoadState('networkidle');
  }
}

async function choisir(testid, nom) {
  await page.click(`[data-testid=${testid}]`);
  await page.getByRole('option', { name: new RegExp(`^\\S*\\s*${nom}`) }).first().click();
}

try {
  if (cmd === 'page') {
    await ouvrir(args[0]);
    await page.screenshot({ path: `${SHOTS}/page.png`, fullPage: true });
    console.log(`capture : ${SHOTS}/page.png`);
  } else if (cmd === 'calcul') {
    const [origine = 'Tunisie', destination = 'Alg', code = '0201101100', cif = '10000'] = args;
    await ouvrir('calculator');
    await choisir('origin-country-select', origine);
    await choisir('destination-country-select', destination);
    // « Mode simple » : saisie directe du code. La recherche intelligente ne
    // retrouve un code national que pour l'Algérie.
    await page.getByText('Mode simple').click();
    await page.fill('[data-testid=hs-code-simple-input]', code);
    await page.fill('[data-testid=cif-value-input]', cif);
    await page.screenshot({ path: `${SHOTS}/saisie.png` });
    // Selon le pays, l'écran liquide par POST /api/calcul (socle) ou par
    // GET /api/authentic-tariffs/calculate (chemin historique).
    const reponse = page.waitForResponse((r) => /\/api\/(calcul$|authentic-tariffs\/calculate\/)/.test(new URL(r.url()).pathname), { timeout: 60000 });
    await page.click('[data-testid=calculate-tariff-button]');
    await reponse;
    // Le bouton reste désactivé (« Calcul en cours… ») jusqu'à la fin de tous les appels.
    await page.waitForSelector('[data-testid=calculate-tariff-button]:not([disabled])', { timeout: 60000 });
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: `${SHOTS}/resultat.png`, fullPage: true });
    console.log(`captures : ${SHOTS}/saisie.png ${SHOTS}/resultat.png`);
  } else {
    throw new Error(`commande inconnue : ${cmd} (calcul | page)`);
  }
} finally {
  console.log('appels /api :\n  ' + appels.join('\n  '));
  console.log(`erreurs console : ${erreurs.length}`);
  erreurs.slice(0, 10).forEach((e) => console.log('  ' + e.slice(0, 300)));
  await browser.close();
}
