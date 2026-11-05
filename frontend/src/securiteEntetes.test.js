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
  expect(a.res.entetes['content-security-policy']).toContain("script-src 'self' 'unsafe-inline'");

  const b = servir('/pricing.html');
  b.res.writeHead(200, { 'Content-Type': 'text/html' });
  expect(b.res.entetes['content-security-policy']).toContain("script-src 'self' 'unsafe-inline'");
});

it("politique décidée sur l'adresse finale : page compatible demandée, application servie", () => {
  const { req, res } = servir('/pricing.html', 'text/html');
  req.url = '/index.html'; // réécriture par le repli SPA avant l'envoi
  res.writeHead(200);
  expect(res.entetes['content-security-policy']).toContain("script-src 'self' 'nonce-n1'");
});

it("adresses non canoniques (« # » brut, « .. ») : politique stricte, même si sirv sert l'application", () => {
  for (const url of ['/pricing.html#/../index.html', '/tools/afcfta_business_atlas.html#/../../index.html', '/x/../pricing.html']) {
    const { res } = servir(url, 'text/html');
    res.writeHead(200);
    expect(res.entetes['content-security-policy']).toContain("'nonce-n1'");
    expect(res.entetes['content-security-policy']).not.toContain("script-src 'self' 'unsafe-inline'");
  }
  const { res } = servir('/pricing.html?checkout=success', 'text/html');
  res.writeHead(200);
  expect(res.entetes['content-security-policy']).toContain("script-src 'self' 'unsafe-inline'");
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
