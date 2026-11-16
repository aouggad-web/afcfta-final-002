// En-têtes de sécurité des pages servies par `vite preview` (audit INFO-3).
//
// Sur Emergent, l'interface est servie par `vite preview` (package.json,
// script start), qui n'envoie aucun en-tête de sécurité. Avec Supabase, la
// session est gardée dans localStorage : la CSP de la page est la première
// défense contre son vol par un script injecté.
//
// Une seule politique pour toutes les pages HTML (l'application et les pages
// de public/) : aucune ne contient de script inline ni de gestionnaire
// onclick="…", et aucune ne charge de script depuis un CDN. Le nonce, tiré à
// chaque réponse, ne sert qu'au script que la bordure Cloudflare d'Emergent
// ajoute aux pages HTML : Cloudflare reprend le nonce de l'en-tête.
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

export function politique({ nonce, supabaseUrl, backendUrl } = {}) {
  const connect = ["'self'", origine(supabaseUrl), origine(backendUrl)]
    .filter((o, i, liste) => o && liste.indexOf(o) === i);
  return serialiser({
    'default-src': ["'self'"],
    'script-src': ["'self'", `'nonce-${nonce}'`],
    // Radix (Select, Dialog) et html2canvas insèrent des <style> dont le
    // contenu varie (largeur de la barre de défilement) ; les pages de
    // public/ gardent leurs styles dans la page.
    'style-src': ["'self'", "'unsafe-inline'", POLICES_CSS],
    'img-src': ["'self'", 'data:', ...TUILES_OSM],
    'font-src': ["'self'", POLICES],
    'connect-src': connect,
    'frame-src': ["'self'"],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
    'form-action': ["'self'"],
    'frame-ancestors': ["'self'", APERCU_EMERGENT],
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

function typeDeContenu(res, args) {
  for (const arg of args) {
    if (arg && typeof arg === 'object' && !Array.isArray(arg)) {
      const cle = Object.keys(arg).find((k) => k.toLowerCase() === 'content-type');
      if (cle) return String(arg[cle]);
    }
  }
  return String(res.getHeader('Content-Type') || '');
}

// Middleware placé avant tous ceux de `vite preview`. La CSP est posée au
// moment où la réponse part, d'après son type : tout document HTML la reçoit,
// y compris l'application servie par le repli SPA sous une adresse inconnue.
export function middlewareEntetes({ supabaseUrl, backendUrl, tirerNonce = () => randomBytes(16).toString('base64') } = {}) {
  return function entetesSecurite(req, res, next) {
    for (const [nom, valeur] of Object.entries(ENTETES_COMMUNS)) res.setHeader(nom, valeur);
    // Adresse mal encodée (« /% », « /%E0%A4%A ») : le repli SPA de Vite
    // lèverait une URIError, affichée avec la pile d'appels et les chemins du
    // serveur. Refusée ici, avant lui.
    try {
      decodeURIComponent(String(req.url).split('?')[0]);
    } catch {
      repondreTexte(res, 400, 'Adresse invalide.');
      return;
    }
    const writeHead = res.writeHead;
    res.writeHead = function (...args) {
      // Une CSP déjà posée (réponse du backend par le proxy /api, page
      // d'erreur de Vite) correspond à son propre contenu : elle reste.
      if (!res.hasHeader('Content-Security-Policy') && typeDeContenu(res, args.slice(1)).startsWith('text/html')) {
        res.setHeader('Content-Security-Policy', politique({ nonce: tirerNonce(), supabaseUrl, backendUrl }));
      }
      return writeHead.apply(this, args);
    };
    next();
  };
}

function repondreTexte(res, statut, texte) {
  res.statusCode = statut;
  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.end(texte);
}

// Dernier recours pour les erreurs des middlewares de preview : le
// gestionnaire de connect afficherait la pile d'appels (il lit NODE_ENV avant
// que Vite ne le fixe). L'erreur reste écrite dans le journal du serveur.
export function erreurSansDetails(journal = console) {
  // Quatre paramètres : connect le traite comme un gestionnaire d'erreurs.
  return function erreurSansDetails(err, req, res, next) {
    journal.error(err && err.stack ? err.stack : String(err));
    if (res.headersSent) {
      res.end();
      return;
    }
    repondreTexte(res, 500, 'Erreur interne du serveur.');
  };
}

// Les origines viennent de l'environnement que Vite a résolu pour ce mode
// (fichiers .env du mode et variables du shell) : le même que celui compilé
// dans l'interface, y compris avec --mode. La synchronisation Emergent
// recompile avant de redémarrer preview.
export function entetesSecurite() {
  return {
    name: 'entetes-securite',
    configurePreviewServer(server) {
      const env = server.config.env;
      server.middlewares.use(
        middlewareEntetes({ supabaseUrl: env.VITE_SUPABASE_URL, backendUrl: env.VITE_BACKEND_URL })
      );
      // Après les middlewares de preview (repli SPA compris).
      return () => server.middlewares.use(erreurSansDetails(server.config.logger));
    },
  };
}
