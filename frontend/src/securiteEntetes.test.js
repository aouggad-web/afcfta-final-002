/**
 * En-têtes de sécurité de `vite preview` (audit INFO-3) : une seule CSP
 * stricte pour tous les documents HTML, posée au départ de la réponse.
 */
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';

import { expect, it, vi } from 'vitest';

import { erreurSansDetails, middlewareEntetes, origine, politique } from '../securite/entetes.js';

const SUPABASE = 'https://projet.supabase.co';

function directive(csp, nom) {
  const d = csp.split('; ').find((x) => x.startsWith(`${nom} `));
  return d ? d.slice(nom.length + 1).split(' ') : null;
}

it('aucun script inline ni CDN, nonce pour le script de Cloudflare', () => {
  const csp = politique({ nonce: 'abc', supabaseUrl: SUPABASE });
  expect(directive(csp, 'script-src')).toEqual(["'self'", "'nonce-abc'"]);
  expect(directive(csp, 'connect-src')).toEqual(["'self'", SUPABASE]);
  expect(directive(csp, 'object-src')).toEqual(["'none'"]);
  expect(directive(csp, 'frame-ancestors')).toEqual(["'self'", 'https://app.emergent.sh']);
  expect(directive(csp, 'img-src')).not.toContain('https:');
  expect(csp).not.toContain("'unsafe-eval'");
});

it("connect-src : seulement l'origine, jamais un chemin ni un schéma non http(s)", () => {
  const csp = politique({ nonce: 'n', supabaseUrl: `${SUPABASE}/auth/v1`, backendUrl: SUPABASE });
  expect(directive(csp, 'connect-src')).toEqual(["'self'", SUPABASE]);
  expect(origine('javascript:alert(1)')).toBeNull();
  expect(origine('pas une url')).toBeNull();
  expect(origine('')).toBeNull();
  expect(origine('http://localhost:8000/api')).toBe('http://localhost:8000');
});

// La CSP n'autorise ni script inline ni gestionnaire onclick="…" : une page de
// public/ qui en contiendrait cesserait de fonctionner. public/index.html,
// gabarit de l'ancien Create React App, n'est jamais servi : Vite écrit
// l'index généré par-dessus lors du build.
it('les pages de public/ ne contiennent ni script inline ni gestionnaire on*', () => {
  const racine = path.resolve(__dirname, '../public');
  const pages = [];
  const parcourir = (dossier) => {
    for (const nom of readdirSync(dossier, { withFileTypes: true })) {
      const chemin = path.join(dossier, nom.name);
      if (nom.isDirectory()) parcourir(chemin);
      else if (nom.name.endsWith('.html') && chemin !== path.join(racine, 'index.html')) pages.push(chemin);
    }
  };
  parcourir(racine);
  expect(pages.length).toBeGreaterThanOrEqual(6);
  for (const page of pages) {
    const html = readFileSync(page, 'utf8');
    const nom = path.relative(racine, page);
    expect([nom, html.match(/<script(?![^>]*\ssrc=)[^>]*>/gi)]).toEqual([nom, null]);
    expect([nom, html.match(/\son[a-z]+\s*=/gi)]).toEqual([nom, null]);
    expect([nom, html.match(/<script[^>]*src="https?:/gi)]).toEqual([nom, null]);
  }
});

function reponse() {
  const entetes = {};
  return {
    entetes,
    setHeader: (nom, valeur) => { entetes[nom.toLowerCase()] = valeur; },
    getHeader: (nom) => entetes[nom.toLowerCase()],
    hasHeader: (nom) => nom.toLowerCase() in entetes,
    writeHead() { this.ecrit = true; return this; },
  };
}

function servir(url, typeAvant) {
  let n = 0;
  const mw = middlewareEntetes({ supabaseUrl: SUPABASE, tirerNonce: () => `n${++n}` });
  const req = { url };
  const res = reponse();
  mw(req, res, () => {});
  if (typeAvant) res.setHeader('Content-Type', typeAvant);
  return { req, res, mw };
}

it('documents HTML seulement : pas de CSP sur les scripts, ni sur le service worker', () => {
  const { res } = servir('/service-worker.js');
  res.writeHead(200, { 'Content-Type': 'text/javascript' });
  expect(res.entetes['content-security-policy']).toBeUndefined();
  expect(res.entetes['x-content-type-options']).toBe('nosniff');
  expect(res.entetes['referrer-policy']).toBe('strict-origin-when-cross-origin');
});

it('type lu dans les en-têtes posés (chaîne de vite preview) ou passé à writeHead', () => {
  const a = servir('/pricing.html', 'text/html;charset=utf-8');
  a.res.writeHead(200);
  expect(a.res.entetes['content-security-policy']).toContain("script-src 'self' 'nonce-n1'");

  const b = servir('/tools/afcfta_business_atlas.html');
  b.res.writeHead(200, { 'Content-Type': 'text/html' });
  expect(b.res.entetes['content-security-policy']).toContain("script-src 'self' 'nonce-n1'");
});

it('même politique stricte quelle que soit l’adresse (repli SPA, adresses non canoniques)', () => {
  for (const url of ['/', '/inconnue', '/pricing.html#/../index.html', '/x/../pricing.html', '/offline.html']) {
    const { res } = servir(url, 'text/html');
    res.writeHead(200);
    expect(directive(res.entetes['content-security-policy'], 'script-src')).toEqual(["'self'", "'nonce-n1'"]);
  }
});

it('une CSP déjà posée (backend par le proxy, page d’erreur) est conservée', () => {
  const { res } = servir('/api/inconnue', 'text/html');
  res.setHeader('Content-Security-Policy', "default-src 'none'");
  res.writeHead(500);
  expect(res.entetes['content-security-policy']).toBe("default-src 'none'");
});

it('un nonce neuf à chaque réponse', () => {
  const vus = new Set();
  const mw = middlewareEntetes();
  for (let i = 0; i < 5; i++) {
    const res = reponse();
    mw({ url: '/' }, res, () => {});
    res.writeHead(200, { 'content-type': 'text/html' });
    vus.add(/'nonce-([^']+)'/.exec(res.entetes['content-security-policy'])[1]);
  }
  expect(vus.size).toBe(5);
});

it('adresse mal encodée : 400 en texte simple, sans passer aux middlewares de Vite', () => {
  for (const url of ['/%', '/%E0%A4%A', '/tools/%ZZ', '/pricing.html%']) {
    const res = reponse();
    res.end = vi.fn();
    const next = vi.fn();
    middlewareEntetes()({ url }, res, next);
    expect(next).not.toHaveBeenCalled();
    expect(res.statusCode).toBe(400);
    expect(res.entetes['content-type']).toBe('text/plain; charset=utf-8');
    expect(res.end).toHaveBeenCalledWith('Adresse invalide.');
  }
  const next = vi.fn();
  middlewareEntetes()({ url: '/pricing.html?q=%ZZ' }, reponse(), next);
  expect(next).toHaveBeenCalled(); // seul le chemin compte, comme pour sirv
});

it("erreur d'un middleware : 500 générique, pile d'appels au journal seulement", () => {
  const journal = { error: vi.fn() };
  const gestionnaire = erreurSansDetails(journal);
  expect(gestionnaire.length).toBe(4); // reconnu comme gestionnaire d'erreurs par connect
  const res = reponse();
  res.end = vi.fn();
  const erreur = new URIError('URI malformed');
  gestionnaire(erreur, { url: '/x' }, res, vi.fn());
  expect(res.statusCode).toBe(500);
  expect(res.end).toHaveBeenCalledWith('Erreur interne du serveur.');
  expect(journal.error).toHaveBeenCalledWith(erreur.stack);
});
