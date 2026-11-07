// Bascule clair / sombre, mémorisée pour toute l'application.
function toggleTheme() {
  const light = document.documentElement.classList.toggle('theme-light');
  try { localStorage.setItem('zlecaf_theme', light ? 'light' : 'dark'); } catch (e) {}
}

let annual = false;

// Repli affiché tant que /api/billing/pricing n'a pas répondu (ou en cas
// d'échec réseau) — doit rester synchronisé avec backend/pricing.py, mais
// n'est plus la source de vérité : loadPricing() ci-dessous le remplace par
// la grille serveur dès que possible, pour qu'un changement de pricing.py
// n'exige plus d'édition manuelle de cette page.
// prices : montants EUR (Stripe, hors DZ). pricesDZD : montants DZD
// (Chargily, DZ) — un seul jeu est affiché à la fois selon la géolocalisation.
let prices = {
  starter: { m: 10,  y: 110  },
  pro:     { m: 25,  y: 275  },
  biz:     { m: 125, y: 1375 }
};
let pricesDZD = {
  starter: { m: 1500,  y: 16500  },
  pro:     { m: 3750,  y: 41250  },
  biz:     { m: 18750, y: 206250 }
};
// 'EUR' (Stripe) ou 'DZD' (Chargily) — fixé par loadPaymentContext() selon le
// prestataire imposé par le serveur ; EUR tant qu'il n'a pas répondu.
let currentCurrency = 'EUR';
// Produits hors formule (API, options, rapports, formation) : id → {eur, dzd},
// rempli par loadPricing() depuis pricing.PRODUCTS. Vide = prix EUR statiques.
let productPrices = {};
let dzdPerEur = 150;

// Charge la grille tarifaire publique depuis le backend (source unique
// pricing.py) et re-rend les cartes. En cas d'échec, on garde silencieusement
// le repli ci-dessus : la page reste utilisable, juste potentiellement
// obsolète de quelques jours au pire.
async function loadPricing() {
  try {
    const res = await fetch('/api/billing/pricing', { credentials: 'include' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const byPlan = {};
    (data.plans || []).forEach(function (p) { byPlan[p.plan] = p; });
    if (!byPlan.starter || !byPlan.pro || !byPlan.business) {
      throw new Error('grille incomplète');
    }
    prices = {
      starter: { m: byPlan.starter.eur.monthly, y: byPlan.starter.eur.annual },
      pro:     { m: byPlan.pro.eur.monthly,     y: byPlan.pro.eur.annual },
      biz:     { m: byPlan.business.eur.monthly, y: byPlan.business.eur.annual }
    };
    pricesDZD = {
      starter: { m: byPlan.starter.dzd.monthly, y: byPlan.starter.dzd.annual },
      pro:     { m: byPlan.pro.dzd.monthly,     y: byPlan.pro.dzd.annual },
      biz:     { m: byPlan.business.dzd.monthly, y: byPlan.business.dzd.annual }
    };
    (data.products || []).forEach(function (p) { productPrices[p.product] = p; });
    if (data.dzd_per_eur) dzdPerEur = data.dzd_per_eur;
    renderPrices();
  } catch (e) {
    console.warn('Grille tarifaire serveur indisponible, repli statique conservé:', e);
  }
}
document.addEventListener('DOMContentLoaded', loadPricing);

// Libellés FR des modules `entitlements.MODULES` (backend/entitlements.py),
// dans l'ordre où ils doivent apparaître dans la liste de fonctionnalités.
const MODULE_LABELS = {
  stats: 'Statistiques commerciales',
  production: 'Données de production',
  logistics: 'Données logistiques (ports, corridors)',
  roo: "Règles d'origine",
  tools: 'Outils (positions tarifaires nationales, suivi de la collecte)',
  reports: 'Rapports d\'opportunités'
};
const PLAN_TO_ITEMS_ID = { free: 'items-free', starter: 'items-starter', pro: 'items-pro', business: 'items-business' };

function formatQuota(quota, period) {
  if (quota === null || quota === undefined) return 'illimité';
  const perFr = { day: 'jour', month: 'mois', cycle: 'cycle de facturation' };
  return quota + ' / ' + (perFr[period] || period);
}

// Génère la liste de fonctionnalités de chaque formule à partir de
// `/api/billing/entitlements` (source unique backend/entitlements.py), pour
// que cette page ne puisse plus diverger de ce qui est réellement appliqué
// par `entitlement_guard.require_module` sur les routes. En cas d'échec, la
// liste statique déjà présente dans le HTML reste affichée telle quelle.
async function loadEntitlements() {
  try {
    const res = await fetch('/api/billing/entitlements', { credentials: 'include' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    Object.keys(PLAN_TO_ITEMS_ID).forEach(function (tier) {
      const ent = data[tier];
      const container = document.getElementById(PLAN_TO_ITEMS_ID[tier]);
      if (!ent || !container) return;

      const items = [];
      items.push({
        ok: true,
        text: ent.daily_calculations === null
          ? 'Calculs de tarifs illimités'
          : ent.daily_calculations + ' calculs de tarifs par jour'
      });
      items.push({
        ok: ent.export_formats.length > 0,
        text: ent.export_formats.length > 0
          ? 'Export ' + ent.export_formats.map(function (f) { return f.toUpperCase(); }).join(' + ')
          : 'Export PDF'
      });
      items.push({
        ok: ent.api_access,
        text: ent.api_access
          ? 'Accès API REST' + (ent.api_monthly_quota != null ? ' — ' + ent.api_monthly_quota + ' req/mois' : '')
          : 'Accès API'
      });
      if (ent.seats_included > 1) {
        items.push({ ok: true, text: ent.seats_included + ' utilisateurs inclus' });
      }
      Object.keys(MODULE_LABELS).forEach(function (moduleId) {
        const access = ent.modules[moduleId];
        if (!access) return;
        const label = MODULE_LABELS[moduleId];
        items.push({
          ok: access.enabled,
          text: access.enabled
            ? label + (access.quota !== null ? ' (' + formatQuota(access.quota, access.quota_period) + ')' : '')
            : label
        });
      });

      container.innerHTML = items.map(function (item) {
        return '<div class="plan-item ' + (item.ok ? 'ok' : 'no') + '">' + item.text + '</div>';
      }).join('');
    });
  } catch (e) {
    console.warn('Entitlements serveur indisponibles, liste statique conservée:', e);
  }
}
document.addEventListener('DOMContentLoaded', loadEntitlements);

function toggleFaq(el) {
  const open = el.classList.toggle('open');
  el.setAttribute('aria-expanded', open ? 'true' : 'false');
}

// Le moyen de paiement est imposé par le serveur selon le pays d'inscription :
// Algérie → Chargily (DZD), étranger → Stripe (EUR). L'utilisateur n'a pas de
// choix ; on se contente d'afficher la bonne devise et le moyen utilisé.
async function loadPaymentContext() {
  try {
    const res = await fetch('/api/billing/payment-context', { credentials: 'include' });
    if (!res.ok) return;
    const ctx = await res.json();
    const note = document.getElementById('country-note');
    if (ctx.provider === 'chargily' || ctx.provider === null) {
      // Pays non détecté : affichage Algérie / Chargily par défaut, mais le
      // serveur refuse le paiement tant que le pays n'est pas établi — on
      // invite donc à nous contacter.
      document.body.classList.add('region-dz');
      currentCurrency = 'DZD';
      renderPrices();
      if (note) {
        if (ctx.provider === null) {
          note.innerHTML = 'Pays non détecté : pour souscrire, contactez-nous à '
            + '<a href="mailto:contact@afcfta-zlecaf.com" style="color:inherit">contact@afcfta-zlecaf.com</a>.';
        } else {
          note.textContent = 'Paiement en dinars via Chargily (CIB / Edahabia).';
        }
      }
    } else if (ctx.provider === 'stripe') {
      document.body.classList.add('region-intl');
      if (note) note.textContent = 'Paiement par carte bancaire via Stripe (EUR).';
    }
  } catch (e) {
    // Contexte indisponible : affichage en EUR par défaut, le serveur tranche au checkout.
  }
}
document.addEventListener('DOMContentLoaded', loadPaymentContext);

// Retour du checkout Stripe : ?checkout=success ou ?checkout=cancel. Affiche
// une bannière d'état, puis nettoie l'URL pour ne pas la rejouer au reload.
document.addEventListener('DOMContentLoaded', function () {
  var params = new URLSearchParams(window.location.search);
  var status = params.get('checkout');
  if (!status) return;
  var el = document.getElementById('checkout-banner');
  if (!el) return;
  if (status === 'success') {
    el.style.background = 'var(--grn-bg)';
    el.style.border = '1px solid var(--grn-b)';
    el.style.color = 'var(--grn)';
    el.textContent = '✓ Paiement enregistré. L\'activation de votre abonnement se fait via notre webhook — vous recevrez un email de confirmation dans quelques secondes.';
  } else if (status === 'cancel') {
    el.style.background = 'var(--gold-bg)';
    el.style.border = '1px solid var(--gold-b)';
    el.style.color = 'var(--gold)';
    el.textContent = 'Paiement annulé. Vous pouvez reprendre à tout moment ci-dessous.';
  }
  el.style.display = 'block';
  // Nettoyage ciblé : on ne retire QUE `checkout`, pour préserver d'éventuels
  // paramètres de suivi (utm_*, gclid…) que le client viendrait de traverser.
  params.delete('checkout');
  var qs = params.toString();
  var clean = window.location.pathname + (qs ? '?' + qs : '') + window.location.hash;
  window.history.replaceState(null, '', clean);
});

// Nom du cookie CSRF : __Host-csrf_token en HTTPS, csrf_token en http local
// (audit INFO-4, même règle que frontend/src/services/csrf.js).
function csrfCookieName() {
  return location.protocol === 'https:' ? '__Host-csrf_token' : 'csrf_token';
}

// Lecture du cookie CSRF côté JS (double-submit).
function readCsrfCookie() {
  const prefix = csrfCookieName() + '=';
  const c = document.cookie.split(';').map(function (s) { return s.trim(); })
    .find(function (s) { return s.indexOf(prefix) === 0; });
  return c ? decodeURIComponent(c.slice(prefix.length)) : null;
}

// Persiste le jeton comme cookie lisible. Indispensable dans l'iframe de
// prévisualisation Emergent, où le Set-Cookie du serveur est abandonné
// (SameSite=None; Secure; Partitioned requis, sinon Lax en HTTP local).
// Reproduit frontend/src/services/csrf.js pour cette page statique.
function persistCsrf(token) {
  const isHttps = location.protocol === 'https:';
  const attrs = isHttps ? 'SameSite=None; Secure; Partitioned' : 'SameSite=Lax';
  document.cookie = csrfCookieName() + '=' + encodeURIComponent(token) +
    '; Path=/; ' + attrs + '; Max-Age=3600';
}

// Garantit un couple cookie+jeton cohérent avant toute mutation. Sans la
// persistance ci-dessous, le POST partait avec l'en-tête mais SANS cookie
// → « CSRF token missing ».
async function ensureCsrf(forceRefresh) {
  if (!forceRefresh) {
    const existing = readCsrfCookie();
    if (existing) return existing;
  }
  const res = await fetch('/api/health?_csrf=' + Date.now(), {
    credentials: 'include', cache: 'no-store'
  });
  const token = res.headers.get('X-CSRF-Token') || readCsrfCookie();
  if (!token) throw new Error('CSRF non initialisé');
  if (readCsrfCookie() !== token) persistCsrf(token);
  return token;
}

// Lance le paiement pour le plan choisi (Stripe hors DZ, Chargily pour DZ,
// selon le pays d'inscription).
// Nécessite une session (cookie JWT) : sinon, redirection vers la connexion.
// Le cycle suit le toggle mensuel/annuel. Les prix sont résolus côté serveur.
async function startCheckout(plan) {
  const cycle = annual ? 'annual' : 'monthly';
  // Le prestataire (Stripe / Chargily) est choisi côté serveur selon le pays
  // d'inscription du compte : rien à envoyer ici.
  return launchCheckout('/api/billing/checkout', { plan: plan, cycle: cycle });
}

// Produits hors formule (API, options, rapports, formation) : même parcours,
// prix et prestataire décidés côté serveur (pricing.PRODUCTS).
async function startProductCheckout(product) {
  return launchCheckout('/api/billing/product-checkout', { product: product });
}

async function launchCheckout(url, payload) {
  const body = JSON.stringify(payload);

  // Safari/iOS perd le "geste utilisateur" dès qu'un await sépare le clic de
  // la navigation : window.location.href après un fetch y est alors ignoré
  // silencieusement (aucune erreur, aucun changement de page). Ouvrir un
  // onglet vide de façon SYNCHRONE, avant tout await, conserve l'autorisation
  // de navigation ; on y redirige une fois l'URL connue. Si le popup est
  // bloqué (w === null), on retombe sur l'onglet courant.
  const w = window.open('', '_blank');

  async function postCheckout(token) {
    return fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': token },
      body: body
    });
  }

  try {
    let csrf = await ensureCsrf(false);
    let res = await postCheckout(csrf);

    // Cookie perdu/expiré côté navigateur : réamorcer une fois et rejouer.
    if (res.status === 403) {
      const err = await res.clone().json().catch(function () { return {}; });
      if (err.detail === 'CSRF token missing' || err.detail === 'CSRF token invalid') {
        csrf = await ensureCsrf(true);
        res = await postCheckout(csrf);
      }
    }

    if (res.status === 401) {
      // Pas connecté : renvoyer vers l'app avec un fragment qui ouvrira la
      // modale d'authentification. On utilise un hash (jamais 404) plutôt
      // qu'une route dédiée, l'app n'ayant pas de routage par URL.
      if (w) w.close();
      window.location.href = '/#auth=login&next=pricing';
      return;
    }
    if (!res.ok) {
      if (w) w.close();
      const err = await res.json().catch(function () { return {}; });
      alert(err.detail || "Paiement momentanément indisponible. Réessayez plus tard.");
      return;
    }
    const data = await res.json();
    if (data && data.url) {
      if (w) {
        w.location.href = data.url;
      } else {
        window.location.href = data.url;
      }
    } else if (w) {
      w.close();
    }
  } catch (e) {
    if (w) w.close();
    alert("Erreur réseau — vérifiez votre connexion et réessayez.");
  }
}

function toggleBilling() {
  annual = !annual;
  const track = document.getElementById('toggle-track');
  track.classList.toggle('on', annual);
  const sw = document.getElementById('billing-switch');
  if (sw) sw.setAttribute('aria-checked', annual ? 'true' : 'false');
  document.getElementById('bill-monthly').style.color = annual ? 'var(--muted)' : 'var(--txt)';
  document.getElementById('bill-annual').style.color  = annual ? 'var(--txt)' : 'var(--muted)';
  renderPrices();
}

// Rend les 3 cartes payantes depuis l'objet `prices` courant (repli statique
// ou grille serveur une fois loadPricing() résolue). Appelée au chargement
// (via loadPricing) et à chaque bascule mensuel/annuel (toggleBilling).
function renderPrices() {
  const pStarter = document.getElementById('price-starter');
  const perStarter = document.getElementById('per-starter');
  const annStarter = document.getElementById('annual-starter');

  const pPro = document.getElementById('price-pro');
  const perPro = document.getElementById('per-pro');
  const annPro = document.getElementById('annual-pro');

  const pBiz = document.getElementById('price-biz');
  const perBiz = document.getElementById('per-biz');
  const annBiz = document.getElementById('annual-biz');

  // Source affichée selon la devise courante : DZD pour l'Algérie (Chargily),
  // EUR sinon (Stripe). Un seul jeu à la fois — c'est ce que l'utilisateur paiera.
  const source = currentCurrency === 'DZD' ? pricesDZD : prices;
  const symbol = currentCurrency === 'DZD' ? ' DZD' : '€';
  // Formatage FR : séparateur de milliers en DZD (18 750 DZD lisible), rien en EUR.
  const fmt = (n) => currentCurrency === 'DZD' ? n.toLocaleString('fr-FR') : String(n);
  document.getElementById('price-free').innerHTML = '0' + symbol + '<span>/mois</span>';
  const productAmount = (id) => {
    const p = productPrices[id];
    return p ? (currentCurrency === 'DZD' ? p.dzd : p.eur) : null;
  };
  document.querySelectorAll('[data-product]').forEach(function (el) {
    const amount = productAmount(el.dataset.product);
    if (amount !== null) el.textContent = fmt(amount) + symbol;
  });
  document.querySelectorAll('[data-strike]').forEach(function (el) {
    const amounts = el.dataset.strike.split(',').map(productAmount);
    if (amounts.every(function (a) { return a !== null; })) {
      el.textContent = fmt(amounts.reduce(function (a, b) { return a + b; }, 0)) + symbol;
    }
  });
  document.querySelectorAll('[data-strike-eur]').forEach(function (el) {
    const eur = Number(el.dataset.strikeEur);
    el.textContent = fmt(currentCurrency === 'DZD' ? eur * dzdPerEur : eur) + symbol;
  });

  // Équivalent mensuel exact : EUR à 2 décimales (110/12 = 9,17 € — se
  // réconcilie avec le total annuel, contrairement à un arrondi entier
  // 9×12≠110). DZD arrondi à l'entier (les fractions de dinar n'ont pas de
  // sens en pratique, min. Chargily = 75 DZD).
  const perMonthAnnual = (y) => currentCurrency === 'DZD'
    ? Math.round(y / 12).toLocaleString('fr-FR')
    : (y / 12).toFixed(2).replace('.', ',');

  if (annual) {
    pStarter.innerHTML = perMonthAnnual(source.starter.y) + symbol + '<span>/mois</span>';
    perStarter.textContent = 'facturé ' + fmt(source.starter.y) + symbol + ' / an';
    annStarter.innerHTML = '<span style="color:var(--grn);font-size:12px">✓ Économisez ' + fmt(source.starter.m * 12 - source.starter.y) + symbol + ' vs mensuel</span>';

    pPro.innerHTML = perMonthAnnual(source.pro.y) + symbol + '<span>/mois</span>';
    perPro.textContent = 'facturé ' + fmt(source.pro.y) + symbol + ' / an';
    annPro.innerHTML = '<span style="color:var(--grn);font-size:12px">✓ Économisez ' + fmt(source.pro.m * 12 - source.pro.y) + symbol + ' vs mensuel</span>';

    pBiz.innerHTML = perMonthAnnual(source.biz.y) + symbol + '<span>/mois</span>';
    perBiz.textContent = 'facturé ' + fmt(source.biz.y) + symbol + ' / an';
    annBiz.innerHTML = '<span style="color:var(--grn);font-size:12px">✓ Économisez ' + fmt(source.biz.m * 12 - source.biz.y) + symbol + ' vs mensuel</span>';
  } else {
    pStarter.innerHTML = fmt(source.starter.m) + symbol + '<span>/mois</span>';
    perStarter.textContent = 'facturé mensuellement';
    annStarter.innerHTML = '';

    pPro.innerHTML = fmt(source.pro.m) + symbol + '<span>/mois</span>';
    perPro.textContent = 'facturé mensuellement';
    annPro.innerHTML = '';

    pBiz.innerHTML = fmt(source.biz.m) + symbol + '<span>/mois</span>';
    perBiz.textContent = 'facturé mensuellement';
    annBiz.innerHTML = '';
  }
}

// Actions des boutons, déclarées par des attributs data-* au lieu de
// gestionnaires onclick="…" : la CSP de la page n'autorise aucun script inline
// (audit INFO-3). Seules les actions de cette liste peuvent être déclenchées.
var ACTIONS = {
  toggleTheme: function () { toggleTheme(); },
  toggleBilling: function () { toggleBilling(); },
  toggleFaq: function (el) { toggleFaq(el); },
  startCheckout: function (el) { startCheckout(el.dataset.plan); },
  startProductCheckout: function (el) { startProductCheckout(el.dataset.produit); }
};
document.addEventListener('click', function (e) {
  var el = e.target.closest('[data-href], [data-action]');
  if (!el) return;
  if (el.hasAttribute('data-href')) {
    window.location.href = el.getAttribute('data-href');
    return;
  }
  var action = ACTIONS[el.dataset.action];
  if (action) action(el);
});
// Éléments role="button" ou "switch" : Entrée et Espace, comme un clic.
document.addEventListener('keydown', function (e) {
  if (e.key !== 'Enter' && e.key !== ' ') return;
  var el = e.target.closest('[data-clavier]');
  if (!el) return;
  e.preventDefault();
  var action = ACTIONS[el.dataset.action];
  if (action) action(el);
});
