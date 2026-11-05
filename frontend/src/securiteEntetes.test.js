/**
 * En-têtes de sécurité de `vite preview` (audit INFO-3) : CSP par page,
 * décidée au départ de la réponse d'après son type et son adresse finale.
 */
import { expect, it } from 'vitest';

import { middlewareEntetes, origine, politiquePour } from '../securite/entetes.js';

const SUPABASE = 'https://projet.supabase.co';

function directive(csp, nom) {
  const d = csp.split('; ').find((x) => x.startsWith(`${nom} `));
  return d ? d.slice(nom.length + 1).split(' ') : null;
}

it("l'application : aucun script inline ni CDN, nonce pour le script de Cloudflare", () => {
  const csp = politiquePour('/index.html', { nonce: 'abc', supabaseUrl: SUPABASE });
  expect(directive(csp, 'script-src')).toEqual(["'self'", "'nonce-abc'"]);
  expect(directive(csp, 'connect-src')).toEqual(["'self'", SUPABASE]);
  expect(directive(csp, 'object-src')).toEqual(["'none'"]);
  expect(directive(csp, 'frame-ancestors')).toEqual(["'self'", 'https://app.emergent.sh']);
  expect(directive(csp, 'img-src')).not.toContain('https:');
});

it('toute autre page HTML reçoit la politique de l’application', () => {
  for (const chemin of ['/', '/inconnue.html', '/tools/autre.html', '/PRICING.html']) {
    expect(directive(politiquePour(chemin, { nonce: 'n' }), 'script-src')).toEqual(["'self'", "'nonce-n'"]);
  }
});

it('pages encore à scripts inline : compatibles, sans nonce (il annulerait unsafe-inline)', () => {
  expect(directive(politiquePour('/pricing.html', { nonce: 'n' }), 'script-src')).toEqual(["'self'", "'unsafe-inline'"]);
  expect(directive(politiquePour('/tools/afcfta_business_atlas.html', { nonce: 'n' }), 'script-src')).toEqual([
    "'self'",
    "'unsafe-inline'",
    'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js',
  ]);
  expect(directive(politiquePour('/cgu.html', { nonce: 'n' }), 'script-src')).toEqual(["'self'", "'nonce-n'"]);
});

it("connect-src : seulement l'origine, jamais un chemin ni un schéma non http(s)", () => {
  const csp = politiquePour('/', { nonce: 'n', supabaseUrl: `${SUPABASE}/auth/v1`, backendUrl: SUPABASE });
  expect(directive(csp, 'connect-src')).toEqual(["'self'", SUPABASE]);
  expect(origine('javascript:alert(1)')).toBeNull();
  expect(origine('pas une url')).toBeNull();
  expect(origine('')).toBeNull();
  expect(origine('http://localhost:8000/api')).toBe('http://localhost:8000');
});

function reponse() {
  const entetes = {};
  return {
    entetes,
    setHeader: (nom, valeur) => { entetes[nom.toLowerCase()] = valeur; },
    getHeader: (nom) => entetes[nom.toLowerCase()],
    writeHead() { this.ecrit = true; return this; },
  };
}

function servir(url, typeDansWriteHead, typeAvant) {
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

it('type passé à writeHead (sirv) ou posé avant (repli SPA de Vite)', () => {
  const a = servir('/pricing.html');
  a.res.writeHead(200, { 'Content-Type': 'text/html;charset=utf-8' });
  expect(a.res.entetes['content-security-policy']).toContain("script-src 'self' 'unsafe-inline'");

  const b = servir('/x', null, 'text/html');
  b.req.url = '/index.html'; // réécriture du repli SPA
  b.res.writeHead(200);
  expect(b.res.entetes['content-security-policy']).toContain("script-src 'self' 'nonce-n1'");
});

it("adresse demandée qui imite une page compatible mais finit sur l'application", () => {
  const { req, res } = servir('/pricing.html/../nexiste', null, 'text/html');
  req.url = '/index.html';
  res.writeHead(200);
  expect(res.entetes['content-security-policy']).not.toContain("'unsafe-inline'; style-src");
  expect(res.entetes['content-security-policy']).toContain("'nonce-");
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
