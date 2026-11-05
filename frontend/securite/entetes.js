// En-têtes de sécurité des pages servies par `vite preview` (audit INFO-3).
//
// Sur Emergent, l'interface est servie par `vite preview` (package.json,
// script start), qui n'envoie aucun en-tête de sécurité. Avec Supabase, la
// session est gardée dans localStorage : la CSP de la page est la première
// défense contre son vol par un script injecté.
//
// La politique dépend de la page :
// - l'application (index.html, et toute adresse servie par le repli SPA) et
//   les pages sans script propre ont une CSP stricte : aucun script inline,
//   aucun CDN ;
// - pricing.html, l'Atlas (tools/) et offline.html ont encore des scripts
//   inline : une politique compatible, limitée à ces fichiers exacts, en
//   attendant que leurs scripts passent dans des fichiers.
// Le nonce, tiré à chaque réponse, ne sert qu'au script que la bordure
// Cloudflare d'Emergent ajoute aux pages HTML : Cloudflare reprend le nonce
// de l'en-tête. Il n'est pas mis sur les pages compatibles, où il
// désactiverait 'unsafe-inline'.
//
// Seulement en preview : le serveur de développement a besoin de son
// préambule inline (plugin React), d'où configurePreviewServer et jamais
// server.headers, dont preview hérite.

import { randomBytes } from 'node:crypto';

// Tuiles des cartes Leaflet ({s} = a, b ou c).
const TUILES_OSM = [
  'https://a.tile.openstreetmap.org',
  'https://b.tile.openstreetmap.org',
  'https://c.tile.openstreetmap.org',
];
const POLICES_CSS = 'https://fonts.googleapis.com';
const POLICES = 'https://fonts.gstatic.com';
// Chart.js de l'Atlas, vérifié par son empreinte SRI dans la page.
const CHART_JS = 'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js';
// L'aperçu de la plateforme Emergent affiche l'application dans une iframe.
const APERCU_EMERGENT = 'https://app.emergent.sh';

// Origine (schéma, hôte, port) d'une URL absolue http(s), sinon null. Une
// source CSP avec un chemin n'autoriserait que ce chemin.
export function origine(url) {
  if (!url) return null;
  try {
    const u = new URL(url);
    return u.protocol === 'https:' || u.protocol === 'http:' ? u.origin : null;
  } catch {
    return null;
  }
}

function serialiser(directives) {
  return Object.entries(directives)
    .map(([nom, sources]) => [nom, ...sources].join(' '))
    .join('; ');
}

// Directives communes à toutes les pages.
function socle(connect) {
  return {
    'default-src': ["'self'"],
    'connect-src': connect,
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
    'frame-ancestors': ["'self'", APERCU_EMERGENT],
  };
}

// Pages par chemin exact (après décodage). Toute autre page HTML reçoit la
// politique de l'application, la plus stricte.
const PAGES = {
  '/pricing.html': 'compatible',
  '/offline.html': 'compatible',
  '/tools/afcfta_business_atlas.html': 'atlas',
  '/cgu.html': 'sans-script',
  '/confidentialite.html': 'sans-script',
  '/design-preview.html': 'sans-script',
};

export function politiquePour(chemin, { nonce, supabaseUrl, backendUrl } = {}) {
  const connect = ["'self'", origine(supabaseUrl), origine(backendUrl)]
    .filter((o, i, liste) => o && liste.indexOf(o) === i);
  const genre = PAGES[chemin] || 'application';
  const base = socle(connect);

  if (genre === 'application') {
    return serialiser({
      ...base,
      'script-src': ["'self'", `'nonce-${nonce}'`],
      // Radix (Select, Dialog) et html2canvas insèrent des <style> dont le
      // contenu varie (largeur de la barre de défilement).
      'style-src': ["'self'", "'unsafe-inline'", POLICES_CSS],
      'img-src': ["'self'", 'data:', ...TUILES_OSM],
      'font-src': ["'self'", POLICES],
      'frame-src': ["'self'"],
    });
  }
  if (genre === 'sans-script') {
    return serialiser({
      ...base,
      'script-src': ["'self'", `'nonce-${nonce}'`],
      'style-src': ["'self'", "'unsafe-inline'", POLICES_CSS],
      'img-src': ["'self'", 'data:'],
      'font-src': ["'self'", POLICES],
    });
  }
  return serialiser({
    ...base,
    'script-src': ["'self'", "'unsafe-inline'", ...(genre === 'atlas' ? [CHART_JS] : [])],
    'style-src': ["'self'", "'unsafe-inline'", POLICES_CSS],
    'img-src': ["'self'", 'data:'],
    'font-src': ["'self'", POLICES],
  });
}

// En-têtes envoyés avec toutes les réponses.
export const ENTETES_COMMUNS = {
  'X-Content-Type-Options': 'nosniff',
  // Pas no-referrer : les serveurs de tuiles OpenStreetMap refusent les
  // requêtes sans Referer.
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'geolocation=(), camera=(), microphone=()',
};

// Chemin comme le lit sirv : coupé au « ? », décodé, sans autre
// normalisation. Une adresse non canonique (« # », « .. », « // »), qu'un
// navigateur n'envoie jamais, ne correspond donc à aucune page compatible et
// reçoit la politique stricte.
function cheminDe(url) {
  try {
    return decodeURIComponent(String(url).split('?')[0]);
  } catch {
    return '';
  }
}

function typeDeContenu(res, args) {
  for (const arg of args) {
    if (arg && typeof arg === 'object' && !Array.isArray(arg)) {
      const cle = Object.keys(arg).find((k) => k.toLowerCase() === 'content-type');
      if (cle) return String(arg[cle]);
    }
  }
  return String(res.getHeader('Content-Type') || '');
}

// Middleware placé avant tous ceux de `vite preview`. La CSP est décidée au
// moment où la réponse part, d'après son type et l'adresse finale : une page
// servie par le repli SPA (adresse inconnue, réécrite en /index.html) reçoit
// donc toujours la politique de l'application, quelle que soit l'adresse
// demandée.
export function middlewareEntetes({ supabaseUrl, backendUrl, tirerNonce = () => randomBytes(16).toString('base64') } = {}) {
  return function entetesSecurite(req, res, next) {
    for (const [nom, valeur] of Object.entries(ENTETES_COMMUNS)) res.setHeader(nom, valeur);
    const writeHead = res.writeHead;
    res.writeHead = function (...args) {
      // Une CSP déjà posée (réponse du backend par le proxy /api, page
      // d'erreur de Vite) correspond à son propre contenu : elle reste.
      if (!res.hasHeader('Content-Security-Policy') && typeDeContenu(res, args.slice(1)).startsWith('text/html')) {
        const csp = politiquePour(cheminDe(req.url), { nonce: tirerNonce(), supabaseUrl, backendUrl });
        res.setHeader('Content-Security-Policy', csp);
      }
      return writeHead.apply(this, args);
    };
    next();
  };
}

export function entetesSecurite(options) {
  return {
    name: 'entetes-securite',
    configurePreviewServer(server) {
      server.middlewares.use(middlewareEntetes(options));
    },
  };
}
