import React, { useEffect, useMemo, useState } from 'react';
import { pick, intlLocale, isRtl } from '../../i18n/lang';

/**
 * Tableau de bord de direction (maquette validée le 08/11/2026) : ligne des
 * dernières dépêches, cours clés des matières premières, bourses africaines
 * (points à l'ouverture et à la clôture), cours par famille et articles à la une.
 * Données : GET /api/marches/apercu (Banque mondiale, SGBV, BRVM, NGX, NSE) et
 * GET /api/news (fil publié par le rédacteur).
 */

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

const UNITES = {
  bbl: ['$/baril', '$/bbl', '$/برميل'],
  mmbtu: ['$/MMBtu', '$/MMBtu', '$/MMBtu'],
  t: ['$/tonne', '$/t', '$/طن'],
  oz: ['$/once', '$/oz', '$/أونصة'],
  kg: ['$/kg', '$/kg', '$/كغ'],
  dmtu: ['$/tonne sèche', '$/dmtu', '$/طن جاف'],
};

// clé : [français, anglais, arabe, unité, décimales]
export const PRODUITS = {
  brent: ['Pétrole Brent', 'Brent crude oil', 'نفط برنت', 'bbl', 1],
  gaz_europe: ['Gaz naturel, Europe', 'Natural gas, Europe', 'الغاز الطبيعي، أوروبا', 'mmbtu', 2],
  gnl_japon: ['GNL, Japon', 'LNG, Japan', 'الغاز المسال، اليابان', 'mmbtu', 2],
  charbon_afs: ['Charbon, Afrique du Sud', 'Coal, South Africa', 'فحم جنوب أفريقيا', 't', 1],
  or: ['Or', 'Gold', 'الذهب', 'oz', 0],
  cuivre: ['Cuivre', 'Copper', 'النحاس', 't', 0],
  minerai_fer: ['Minerai de fer', 'Iron ore', 'خام الحديد', 'dmtu', 1],
  aluminium: ['Aluminium', 'Aluminium', 'الألومنيوم', 't', 0],
  platine: ['Platine', 'Platinum', 'البلاتين', 'oz', 0],
  zinc: ['Zinc', 'Zinc', 'الزنك', 't', 0],
  cacao: ['Cacao', 'Cocoa', 'الكاكاو', 'kg', 2],
  cafe_robusta: ['Café robusta', 'Robusta coffee', 'بن روبوستا', 'kg', 2],
  coton: ['Coton', 'Cotton', 'القطن', 'kg', 2],
  the: ['Thé (Mombasa)', 'Tea (Mombasa)', 'الشاي (مومباسا)', 'kg', 2],
  huile_palme: ['Huile de palme', 'Palm oil', 'زيت النخيل', 't', 0],
  arachide: ['Arachide', 'Groundnuts', 'الفول السوداني', 't', 0],
  phosphate: ['Phosphate naturel', 'Phosphate rock', 'الفوسفات الخام', 't', 0],
  uree: ['Urée', 'Urea', 'اليوريا', 't', 1],
  dap: ['Phosphate diammonique (DAP)', 'Diammonium phosphate (DAP)', 'فوسفات ثنائي الأمونيوم', 't', 0],
};

const FAMILLES = {
  hydrocarbures: ['Hydrocarbures', 'Hydrocarbons', 'المحروقات'],
  minerais: ['Minerais et métaux', 'Minerals and metals', 'المعادن والفلزات'],
  agriculture: ['Agriculture', 'Agriculture', 'الزراعة'],
  engrais: ['Engrais', 'Fertilizers', 'الأسمدة'],
};

const CLES_BANDEAU = [
  ['brent', 'var(--terra)'],
  ['or', 'var(--gold)'],
  ['cuivre', '#3FA3C9'],
  ['cacao', 'var(--green)'],
  ['phosphate', '#9b7bd8'],
];

// clé : [nom, place (fr, en, ar), drapeau]
const INDICES = {
  dzair: ['DZAIR INDEX', ['Alger', 'Algiers', 'الجزائر'], '🇩🇿'],
  brvm_c: ['BRVM Composite', ['Abidjan · 8 pays de l’UEMOA', 'Abidjan · 8 WAEMU countries', 'أبيدجان · 8 دول من الاتحاد الاقتصادي والنقدي لغرب أفريقيا'], '🇨🇮'],
  ngx_asi: ['NGX All-Share', ['Lagos', 'Lagos', 'لاغوس'], '🇳🇬'],
  nse20: ['NSE 20', ['Nairobi', 'Nairobi', 'نيروبي'], '🇰🇪'],
};

const T = {
  eyebrow: ['Tableau de bord · Direction', 'Dashboard · Management', 'لوحة القيادة · الإدارة'],
  titre: ["Marchés africains en un coup d'œil", 'African markets at a glance', 'الأسواق الأفريقية في لمحة'],
  chapeau: [
    "Matières premières, bourses et actualités économiques : l'essentiel pour décider.",
    'Commodities, stock exchanges and business news: what you need to decide.',
    'المواد الأولية والبورصات والأخبار الاقتصادية: الأساسي لاتخاذ القرار.',
  ],
  coursDe: ['Cours Banque mondiale', 'World Bank prices', 'أسعار البنك الدولي'],
  depeches: ['Dernières dépêches', 'Latest news', 'آخر الأخبار'],
  sur12: ['sur 12 mois', 'over 12 months', 'على 12 شهرًا'],
  bourses: ['Bourses africaines', 'African stock exchanges', 'البورصات الأفريقية'],
  boursesSous: [
    "Points à l'ouverture et à la clôture de la dernière séance",
    'Points at the open and close of the last session',
    'النقاط عند الافتتاح والإغلاق في آخر جلسة',
  ],
  indice: ['Indice', 'Index', 'المؤشر'],
  ouverture: ['Ouverture', 'Open', 'الافتتاح'],
  cloture: ['Clôture', 'Close', 'الإغلاق'],
  variation: ['Variation', 'Change', 'التغير'],
  seance: ['Séance', 'Session', 'الجلسة'],
  derniere: ['dernière séance', 'last session', 'آخر جلسة'],
  ouvertureAVenir: [
    "Ouverture connue à partir de la prochaine séance",
    'Open known from the next session',
    'يُعرف الافتتاح ابتداءً من الجلسة القادمة',
  ],
  ancienne: ['Source momentanément indisponible : dernière valeur lue', 'Source temporarily unavailable: last value read', 'المصدر غير متاح مؤقتًا: آخر قيمة مقروءة'],
  cours: ['Cours des matières premières', 'Commodity prices', 'أسعار المواد الأولية'],
  coursSous: ['Moyennes mensuelles, variation sur un mois', 'Monthly averages, change over one month', 'متوسطات شهرية، التغير على شهر'],
  tout: ['Tout', 'All', 'الكل'],
  une: ['À la une', 'Top stories', 'أبرز الأخبار'],
  toutes: ['Toutes', 'All', 'الكل'],
  sources: [
    'Sources : Banque mondiale, Pink Sheet (CC BY 4.0), cours moyens mensuels en dollars US · Bourses d’Alger (SGBV), d’Abidjan (BRVM), de Lagos (NGX) et de Nairobi (NSE)',
    'Sources: World Bank, Pink Sheet (CC BY 4.0), monthly average prices in US dollars · Algiers (SGBV), Abidjan (BRVM), Lagos (NGX) and Nairobi (NSE) stock exchanges',
    'المصادر: البنك الدولي، النشرة الوردية (CC BY 4.0)، متوسط الأسعار الشهرية بالدولار الأمريكي · بورصات الجزائر (SGBV) وأبيدجان (BRVM) ولاغوس (NGX) ونيروبي (NSE)',
  ],
};

const CATEGORIES_AR = {
  Finance: 'المالية',
  Commerce: 'التجارة',
  Énergie: 'الطاقة',
  Agriculture: 'الزراعة',
  Mines: 'المناجم',
  Télécoms: 'الاتصالات',
  Infrastructure: 'البنية التحتية',
  Gouvernance: 'الحوكمة',
  Économie: 'الاقتصاد',
};

const tr = (lang, [fr, en, ar]) => pick(lang, fr, en, ar);
const nombre = (v, lang, d = 2) =>
  new Intl.NumberFormat(intlLocale(lang), { minimumFractionDigits: d, maximumFractionDigits: d }).format(v);
const ecart = (avant, apres) => (avant ? ((apres - avant) / avant) * 100 : null);

const Chiffre = ({ children, className = '' }) => (
  <bdi dir="ltr" className={className}>
    {children}
  </bdi>
);

export function Variation({ pct, language }) {
  if (pct == null || Number.isNaN(pct)) return <span className="text-[var(--afcfta-muted)]">—</span>;
  const sens = pct > 0.05 ? 'hausse' : pct < -0.05 ? 'baisse' : 'stable';
  const couleur = { hausse: 'var(--green)', baisse: 'var(--danger)', stable: 'var(--afcfta-muted)' }[sens];
  const fleche = { hausse: '▲', baisse: '▼', stable: '■' }[sens];
  return (
    <span
      data-sens={sens}
      className="inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-bold"
      style={{ color: couleur, background: `color-mix(in srgb, ${couleur} 14%, transparent)` }}
    >
      {fleche} <Chiffre>{nombre(Math.abs(pct), language, 1)} %</Chiffre>
    </span>
  );
}

function Courbe({ serie, largeur, hauteur, couleur }) {
  const v = (serie || []).filter((x) => x != null);
  if (v.length < 2) return null;
  const min = Math.min(...v);
  const max = Math.max(...v);
  const pts = v.map((y, i) => [
    (i * largeur) / (v.length - 1),
    hauteur - 2 - ((y - min) / (max - min || 1)) * (hauteur - 4),
  ]);
  const trace = pts.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ');
  const [dx, dy] = pts[pts.length - 1];
  return (
    <svg width={largeur} height={hauteur} viewBox={`0 0 ${largeur} ${hauteur}`} aria-hidden="true" className="block max-w-full">
      <path d={`${trace} L${largeur} ${hauteur} L0 ${hauteur}Z`} fill={couleur} opacity="0.12" />
      <path d={trace} fill="none" stroke={couleur} strokeWidth="2" strokeLinejoin="round" />
      <circle cx={dx} cy={dy} r="3" fill={couleur} />
    </svg>
  );
}

const unite = (cle, lang) => {
  const [fr, en, ar] = UNITES[PRODUITS[cle][3]];
  return pick(lang, fr, en, ar);
};

function TuileCours({ cle, produit, couleur, language }) {
  const [fr, en, ar, , d] = PRODUITS[cle];
  const s = produit.serie.filter((x) => x != null);
  const dernier = s[s.length - 1];
  const sur12 = ecart(s[0], dernier);
  return (
    <div
      data-testid={`tuile-${cle}`}
      className="relative overflow-hidden rounded-2xl border p-4 pb-2"
      style={{ background: 'var(--lift)', borderColor: 'var(--lift-border)', boxShadow: 'var(--lift-shadow)' }}
    >
      <div className="absolute inset-x-0 top-0 h-[3px]" style={{ background: couleur }} />
      <div className="flex items-center justify-between gap-2 text-xs font-semibold text-[var(--afcfta-muted)]">
        <span>{pick(language, fr, en, ar)}</span>
        <Variation pct={ecart(s[s.length - 2], dernier)} language={language} />
      </div>
      <div
        className="mt-2 font-bold text-[var(--text)]"
        style={{ fontSize: 'clamp(26px, 2.4vw, 34px)', fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)", lineHeight: 1.1 }}
      >
        <Chiffre>{nombre(dernier, language, d)}</Chiffre>
      </div>
      <div className="text-xs text-[var(--afcfta-muted)]">
        {unite(cle, language)} · {tr(language, T.sur12)}{' '}
        <Chiffre>{sur12 == null ? '—' : `${sur12 > 0 ? '+' : ''}${nombre(sur12, language, 0)} %`}</Chiffre>
      </div>
      <div className="mt-1">
        <Courbe serie={produit.serie} largeur={220} hauteur={40} couleur={couleur} />
      </div>
    </div>
  );
}

function LigneDepeches({ articles, language }) {
  if (!articles.length) return null;
  const elements = (copie) =>
    articles.map((a) => (
      <a
        key={`${copie}-${a.id || a.link}`}
        href={a.link}
        target="_blank"
        rel="noopener noreferrer"
        tabIndex={copie ? -1 : undefined}
        className="inline-flex items-center gap-2 text-sm text-[var(--text)] hover:underline"
      >
        <span className="font-bold text-[var(--gold)]">{a.source}</span>
        <span>{a.title}</span>
      </a>
    ));
  return (
    <div
      className="flex items-center gap-3 rounded-xl border px-3 py-2"
      style={{ background: 'var(--overlay)', borderColor: 'var(--overlay-border)' }}
    >
      <span className="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-white" style={{ background: 'var(--terra)' }}>
        {tr(language, T.depeches)}
      </span>
      <div className="ligne-depeches min-w-0 flex-1" dir={isRtl(language) ? 'rtl' : 'ltr'} role="region" aria-label={tr(language, T.depeches)}>
        <div className="ligne-depeches__piste">
          {elements(0)}
          <span aria-hidden="true" className="contents">
            {elements(1)}
          </span>
        </div>
      </div>
    </div>
  );
}

const dateCourte = (iso, lang) =>
  new Intl.DateTimeFormat(intlLocale(lang), { day: 'numeric', month: 'short', timeZone: 'UTC' }).format(new Date(`${iso}T00:00:00Z`));

function Bourses({ indices, language }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" style={{ fontVariantNumeric: 'tabular-nums' }}>
        <thead>
          <tr className="text-[11px] uppercase tracking-wide text-[var(--afcfta-muted)]">
            <th className="py-2 pe-2 text-start font-semibold">{tr(language, T.indice)}</th>
            <th className="py-2 px-2 text-end font-semibold">{tr(language, T.ouverture)}</th>
            <th className="py-2 px-2 text-end font-semibold">{tr(language, T.cloture)}</th>
            <th className="py-2 px-2 text-end font-semibold">{tr(language, T.variation)}</th>
            <th className="py-2 ps-2 text-end font-semibold">{tr(language, T.seance)}</th>
          </tr>
        </thead>
        <tbody>
          {indices.map((i) => {
            const [nom, place, drapeau] = INDICES[i.cle] || [i.cle, ['', '', ''], ''];
            return (
              <tr key={i.cle} data-testid={`indice-${i.cle}`} className="border-t" style={{ borderColor: 'var(--lift-border)' }}>
                <td className="py-3 pe-2">
                  <div className="font-bold text-[var(--text)]">
                    <span aria-hidden="true" className="me-2">{drapeau}</span>
                    {nom}
                  </div>
                  <div className="text-xs text-[var(--afcfta-muted)]">{tr(language, place)}</div>
                </td>
                <td className="py-3 px-2 text-end" title={i.ouverture == null ? tr(language, T.ouvertureAVenir) : undefined}>
                  <Chiffre>{i.ouverture == null ? '—' : nombre(i.ouverture, language)}</Chiffre>
                </td>
                <td className="py-3 px-2 text-end font-bold text-[var(--text)]" title={i.a_jour === false ? tr(language, T.ancienne) : undefined}>
                  <Chiffre>{nombre(i.cloture, language)}</Chiffre>
                  {i.a_jour === false && <span className="ms-1 text-[var(--afcfta-muted)]">*</span>}
                </td>
                <td className="py-3 px-2 text-end">
                  <Variation pct={i.variation_pct} language={language} />
                </td>
                <td className="py-3 ps-2 text-end text-xs text-[var(--afcfta-muted)] whitespace-nowrap">
                  {i.date ? dateCourte(i.date, language) : tr(language, T.derniere)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Pastilles({ options, choisi, choisir }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map(([valeur, libelle]) => (
        <button
          key={valeur}
          type="button"
          aria-pressed={choisi === valeur}
          onClick={() => choisir(valeur)}
          className="rounded-full border px-3 py-1 text-xs transition-colors"
          style={
            choisi === valeur
              ? { background: 'var(--terra)', borderColor: 'var(--terra)', color: '#fff' }
              : { borderColor: 'var(--lift-border)', color: 'var(--text-soft)' }
          }
        >
          {libelle}
        </button>
      ))}
    </div>
  );
}

function CoursParFamille({ produits, language }) {
  const [famille, setFamille] = useState('tout');
  const options = [['tout', tr(language, T.tout)], ...Object.entries(FAMILLES).map(([k, l]) => [k, tr(language, l)])];
  const bandeau = new Set(CLES_BANDEAU.map(([c]) => c));
  return (
    <>
      <Pastilles options={options} choisi={famille} choisir={setFamille} />
      <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-x-6">
        {Object.keys(FAMILLES)
          .filter((f) => famille === 'tout' || famille === f)
          .map((f) => {
            const cles = Object.keys(PRODUITS).filter(
              (c) => produits[c]?.famille === f && (famille !== 'tout' || !bandeau.has(c))
            );
            if (!cles.length) return null;
            return (
              <React.Fragment key={f}>
                <div className="col-span-full mt-2 text-[11px] font-bold uppercase tracking-wider text-[var(--gold)]">
                  {tr(language, FAMILLES[f])}
                </div>
                {cles.map((c) => {
                  const s = produits[c].serie.filter((x) => x != null);
                  const hausse = s[s.length - 1] >= s[s.length - 2];
                  return (
                    <div
                      key={c}
                      data-testid={`cours-${c}`}
                      className="grid items-center gap-3 border-b py-2"
                      style={{ gridTemplateColumns: 'minmax(0,1fr) auto 56px auto', borderColor: 'var(--lift-border)' }}
                    >
                      <div className="min-w-0">
                        <div className="font-semibold text-[var(--text)] leading-tight">{pick(language, ...PRODUITS[c].slice(0, 3))}</div>
                        <div className="text-[11px] text-[var(--afcfta-muted)]">{unite(c, language)}</div>
                      </div>
                      <div className="font-bold text-[var(--text)]" style={{ fontVariantNumeric: 'tabular-nums' }}>
                        <Chiffre>{nombre(s[s.length - 1], language, PRODUITS[c][4])}</Chiffre>
                      </div>
                      <Courbe serie={produits[c].serie} largeur={56} hauteur={24} couleur={hausse ? 'var(--green)' : 'var(--danger)'} />
                      <div className="text-end">
                        <Variation pct={ecart(s[s.length - 2], s[s.length - 1])} language={language} />
                      </div>
                    </div>
                  );
                })}
              </React.Fragment>
            );
          })}
      </div>
    </>
  );
}

const ilYa = (iso, lang) => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const heures = Math.round((date.getTime() - Date.now()) / 3600000);
  const rtf = new Intl.RelativeTimeFormat(intlLocale(lang), { numeric: 'auto' });
  return heures > -24 ? rtf.format(Math.min(heures, 0), 'hour') : rtf.format(Math.round(heures / 24), 'day');
};

const libelleCategorie = (c, lang) => pick(lang, c, c, CATEGORIES_AR[c] || c);

function ALaUne({ articles, language }) {
  const [categorie, setCategorie] = useState('toutes');
  const categories = [...new Set(articles.map((a) => a.category).filter(Boolean))];
  const choix = articles.filter((a) => categorie === 'toutes' || a.category === categorie).slice(0, 5);
  const [une, ...autres] = choix;
  const options = [['toutes', tr(language, T.toutes)], ...categories.map((c) => [c, libelleCategorie(c, language)])];
  const meta = (a) => [a.source, ilYa(a.published_at, language)].filter(Boolean).join(' · ');
  return (
    <section className="rounded-2xl border p-5" style={{ background: 'var(--panel)', borderColor: 'var(--panel-border)' }}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-2xl font-bold text-[var(--text)]" style={{ fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
          {tr(language, T.une)}
        </h3>
        <Pastilles options={options} choisi={categorie} choisir={setCategorie} />
      </div>
      {une && (
        <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr_1fr] gap-3">
          <a
            href={une.link}
            target="_blank"
            rel="noopener noreferrer"
            data-testid="article-une"
            className="relative flex min-h-[260px] flex-col justify-end overflow-hidden rounded-2xl p-5 lg:row-span-2"
            style={{ background: 'linear-gradient(160deg, color-mix(in srgb, var(--terra) 60%, #000), #0d1b2a)', color: '#F7F1E6' }}
          >
            {une.has_image && (
              <img
                src={`${API}/news/images/${encodeURIComponent(une.id)}`}
                alt=""
                loading="lazy"
                className="absolute inset-0 h-full w-full object-cover opacity-45"
              />
            )}
            <div className="relative">
              <div className="text-[11px] font-bold uppercase tracking-wide" style={{ color: '#F2C46D' }}>
                {[libelleCategorie(une.category, language), meta(une)].filter(Boolean).join(' · ')}
              </div>
              <h4 className="my-2 text-2xl font-bold leading-tight" style={{ fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
                {une.title}
              </h4>
              {une.summary && <p className="line-clamp-2 text-sm opacity-90">{une.summary}</p>}
            </div>
          </a>
          {autres.map((a) => (
            <a
              key={a.id || a.link}
              href={a.link}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl border p-4 hover:opacity-90"
              style={{ background: 'var(--lift)', borderColor: 'var(--lift-border)' }}
            >
              <div className="text-[11px] font-bold uppercase tracking-wide text-[var(--gold)]">{libelleCategorie(a.category, language)}</div>
              <h4 className="my-1.5 font-semibold leading-snug text-[var(--text)]">{a.title}</h4>
              <div className="text-xs text-[var(--afcfta-muted)]">{meta(a)}</div>
            </a>
          ))}
        </div>
      )}
    </section>
  );
}

const Panneau = ({ titre, sous, children }) => (
  <section className="rounded-2xl border p-5" style={{ background: 'var(--panel)', borderColor: 'var(--panel-border)', boxShadow: 'var(--panel-shadow)' }}>
    <div className="mb-3">
      <h3 className="text-2xl font-bold text-[var(--text)]" style={{ fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
        {titre}
      </h3>
      {sous && <p className="text-xs text-[var(--afcfta-muted)]">{sous}</p>}
    </div>
    {children}
  </section>
);

export default function TableauManager({ language = 'fr' }) {
  const [marches, setMarches] = useState(null);
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    let actif = true;
    fetch(`${API}/marches/apercu`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => actif && setMarches(d))
      .catch(() => actif && setMarches(null));
    fetch(`${API}/news`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => actif && setArticles(d?.articles || []))
      .catch(() => actif && setArticles([]));
    return () => {
      actif = false;
    };
  }, []);

  const produits = marches?.cours?.produits || {};
  const indices = marches?.indices || [];
  const moisCours = useMemo(() => {
    const mois = marches?.cours?.mois;
    if (!mois) return null;
    return new Intl.DateTimeFormat(intlLocale(language), { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(
      new Date(`${mois}-01T00:00:00Z`)
    );
  }, [marches, language]);
  const aujourdhui = new Intl.DateTimeFormat(intlLocale(language), { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }).format(new Date());
  const bandeau = CLES_BANDEAU.filter(([c]) => produits[c]);

  return (
    <div className="space-y-4" data-testid="tableau-manager">
      <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="text-xs font-bold uppercase tracking-widest text-[var(--gold)]">{tr(language, T.eyebrow)}</div>
          <h2 className="mt-1 text-3xl md:text-4xl font-bold text-[var(--text)]" style={{ fontFamily: "var(--font-display, 'Cormorant Garamond', Georgia, serif)" }}>
            {tr(language, T.titre)}
          </h2>
          <p className="text-sm text-[var(--text-soft)]">{tr(language, T.chapeau)}</p>
        </div>
        <div className="text-sm md:text-end">
          <div className="font-bold first-letter:uppercase text-[var(--text)]">{aujourdhui}</div>
          {moisCours && (
            <div className="text-xs text-[var(--afcfta-muted)]">
              {tr(language, T.coursDe)} : {moisCours}
            </div>
          )}
        </div>
      </header>

      <LigneDepeches articles={articles.slice(0, 12)} language={language} />

      {bandeau.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
          {bandeau.map(([c, couleur]) => (
            <TuileCours key={c} cle={c} produit={produits[c]} couleur={couleur} language={language} />
          ))}
        </div>
      )}

      {(indices.length > 0 || Object.keys(produits).length > 0) && (
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] gap-4 items-start">
          {indices.length > 0 && (
            <Panneau titre={tr(language, T.bourses)} sous={tr(language, T.boursesSous)}>
              <Bourses indices={indices} language={language} />
            </Panneau>
          )}
          {Object.keys(produits).length > 0 && (
            <Panneau titre={tr(language, T.cours)} sous={tr(language, T.coursSous)}>
              <CoursParFamille produits={produits} language={language} />
            </Panneau>
          )}
        </div>
      )}

      {articles.length > 0 && <ALaUne articles={articles} language={language} />}

      {marches && <p className="text-[11px] text-[var(--afcfta-muted)]">{tr(language, T.sources)}</p>}
    </div>
  );
}
