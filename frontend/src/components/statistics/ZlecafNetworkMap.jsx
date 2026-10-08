/**
 * ZlecafNetworkMap — carte « Réseau ZLECAf ».
 *
 * Un point par capitale (Natural Earth), un rond dont la SURFACE est
 * proportionnelle au PIB 2024 (Banque mondiale), une couleur par statut de
 * mise en œuvre, et une liaison entre deux États quand l'un applique la
 * préférence ZLECAf aux produits de l'autre. Statuts, preuves et liaisons
 * viennent de /api/zlecaf/network (backend/services/zlecaf_network.py) ;
 * la géographie de src/data/zlecafNetworkGeo.json
 * (scripts/build_zlecaf_network_geo.py).
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Network } from 'lucide-react';
import geo from '../../data/zlecafNetworkGeo.json';
import { montantCompact } from '../../utils/nombres';
import '../../styles/zlecafNetwork.css';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || '';
const API = `${BACKEND_URL}/api`;

// Les deux statuts « hors accord » sont gris (plein / pointillé) ; les quatre
// autres portent les seules teintes qui restent distinctes deux à deux sur une
// carte (voir zlecafNetwork.css).
const NIVEAUX = {
  non_signataire:    { fr: 'Non signataire',             en: 'Not signed' },
  signe_non_ratifie: { fr: 'Signé, non ratifié',         en: 'Signed, not ratified' },
  ratifie:           { fr: 'Ratifié',                    en: 'Ratified' },
  offre_tarifaire:   { fr: 'Offre tarifaire',            en: 'Tariff offer' },
  instrument_adopte: { fr: 'Instrument national adopté', en: 'National instrument adopted' },
  deploiement:       { fr: 'Déploiement',                en: 'Implementation' },
};

const TEXTS = {
  fr: {
    title: 'Réseau ZLECAf',
    subtitle: 'Mise en œuvre de l’accord, pays par pays',
    loading: 'Chargement du réseau…',
    error: 'Impossible de charger le réseau ZLECAf.',
    hint: 'Survolez ou sélectionnez une capitale. Cliquez une étiquette de la légende pour isoler un statut.',
    link: 'Liaison : un État applique la préférence ZLECAf aux produits de l’autre',
    size: 'PIB {year} (Md $), surface du rond',
    sizeFloor: 'Taille minimale sous {min} Md $ ; anneau pointillé autour du rond : PIB non disponible.',
    gdp: 'PIB {year}',
    gdpNa: 'PIB {year} non disponible',
    out: 'applique la préférence à {n} État(s)',
    in: 'préférence reçue de {n} État(s)',
    proofs: 'Pourquoi ce statut',
    table: 'Voir les données ({n} États)',
    country: 'État',
    capital: 'Capitale',
    status: 'Statut',
    links: 'Liaisons (accordées / reçues)',
    source: 'Source principale',
    noPoint: 'pas de point sur la carte',
    sources: 'Sources',
    limits: 'Limites des données',
    asOf: 'Statuts au {date}.',
    close: 'Fermer',
    gdpSource: 'Banque mondiale (API WDI), PIB en dollars US courants',
    limitsList: [
      'La source continentale compte 48 offres vérifiées et 25 États en application effective sans les nommer : seuls les États nommés par une source du dépôt sont classés à ces niveaux.',
      '« Déploiement » : l’État applique lui-même la préférence par un instrument en vigueur. Être nommé dans la liste de partenaires d’un autre État crée une liaison, pas un déploiement.',
      '« Offre tarifaire » : liste provisoire soumise (Annexe 1 de la Directive 1/2021, octobre 2021, révision annuelle non retrouvée) ou barème officiel archivé ; ni l’un ni l’autre ne prouve l’application.',
      'Pour l’EAC, la liste d’origines admises est un plafond, pas la liste des États ayant effectivement commencé.',
      'Seul le contour des terres est tracé : aucune frontière intérieure. Terres au sud de 40° S hors cadre.',
      'Sahara occidental : Natural Earth ne lui donne qu’une capitale « alt » disputée ; pas de point. Burundi : Natural Earth classe Bujumbura en capitale.',
    ],
  },
  en: {
    title: 'AfCFTA network',
    subtitle: 'Implementation of the agreement, country by country',
    loading: 'Loading the network…',
    error: 'Unable to load the AfCFTA network.',
    hint: 'Hover or select a capital. Click a legend label to isolate a status.',
    link: 'Link: one State applies the AfCFTA preference to the other’s goods',
    size: 'GDP {year} (USD bn), circle area',
    sizeFloor: 'Minimum size below USD {min} bn; dashed ring around the circle: GDP not available.',
    gdp: 'GDP {year}',
    gdpNa: 'GDP {year} not available',
    out: 'grants the preference to {n} State(s)',
    in: 'preference received from {n} State(s)',
    proofs: 'Why this status',
    table: 'Show the data ({n} States)',
    country: 'State',
    capital: 'Capital',
    status: 'Status',
    links: 'Links (granted / received)',
    source: 'Main source',
    noPoint: 'no point on the map',
    sources: 'Sources',
    limits: 'Data limitations',
    asOf: 'Statuses as of {date}.',
    close: 'Close',
    gdpSource: 'World Bank (WDI API), GDP in current US dollars',
    limitsList: [
      'The continental source counts 48 verified offers and 25 States implementing without naming them: only States named by a source in the repository are placed at these levels.',
      '“Implementation”: the State itself applies the preference through an instrument in force. Being named in another State’s partner list creates a link, not an implementation.',
      '“Tariff offer”: provisional schedule submitted (Annex 1 of Directive 1/2021, October 2021, annual revision not found) or official schedule archived; neither proves application.',
      'For the EAC, the list of admitted origins is a ceiling, not the list of States that have actually started.',
      'Only the land outline is drawn: no interior borders. Land south of 40° S is out of frame.',
      'Western Sahara: Natural Earth only gives it a disputed “alt” capital; no point. Burundi: Natural Earth lists Bujumbura as the capital.',
    ],
  },
};

const fill = (s, vars) => s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? ''));
const color = (niveau) => `var(--zn-${niveau})`;
const creuxNiveau = (niveau) => niveau === 'non_signataire';

// Surface du rond proportionnelle au PIB : r = K·√(PIB en Md $), en degrés,
// avec un plancher de lisibilité R_MIN (annoncé dans la légende des tailles).
const K = 0.2;
const R_MIN = 0.55;
const PIB_PLANCHER = Math.round((R_MIN / K) ** 2); // ≈ 8 Md $
const rayon = (pib) => (pib == null ? R_MIN : Math.max(R_MIN, K * Math.sqrt(pib / 1e9)));
const TAILLES = [10, 100, 400];

// Le cadre de la géographie, élargi du rayon du plus grand rond possible
// (≈ 4,5° pour 500 Md $) : Alger, Tunis ou Le Caire ne sont jamais coupés.
const MARGE = 4.5;
const [VB_X, VB_Y, VB_W, VB_H] = (() => {
  const [x, y, w, h] = geo.viewBox.map(Number);
  return [x - MARGE, y - MARGE, w + 2 * MARGE, h + 2 * MARGE];
})();
const VIEWBOX = `${VB_X} ${VB_Y} ${VB_W} ${VB_H}`;

const dateLongue = (iso, lang) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString(lang === 'en' ? 'en-GB' : 'fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  });

function courbe(a, b) {
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const k = 0.12;
  return `M${a.x} ${a.y}Q${mx - dy * k} ${my + dx * k} ${b.x} ${b.y}`;
}

// Largeur affichée de la carte, pour dessiner la légende des tailles à la
// même échelle que les ronds.
function useLargeur(ref, pret) {
  const [largeur, setLargeur] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const mesurer = () => setLargeur(el.getBoundingClientRect().width);
    mesurer();
    if (typeof ResizeObserver === 'undefined') return undefined;
    const obs = new ResizeObserver(mesurer);
    obs.observe(el);
    return () => obs.disconnect();
  }, [ref, pret]); // la carte est (re)montée à chaque jeu de données
  return largeur;
}

export default function ZlecafNetworkMap({ language = 'fr' }) {
  const lang = language === 'en' ? 'en' : 'fr';
  const txt = TEXTS[lang];
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);
  const [hover, setHover] = useState(null);
  const [pinned, setPinned] = useState(null);
  const [focusNiveau, setFocusNiveau] = useState(null);
  const wrapRef = useRef(null);
  const nodeRefs = useRef({});
  const largeur = useLargeur(wrapRef, error ? null : data);
  const tipRef = useRef(null);
  const clavierRef = useRef(false);

  // Épinglée au clavier : le focus entre dans l'infobulle (liens, « Fermer »).
  useEffect(() => {
    if (pinned && clavierRef.current) {
      tipRef.current?.querySelector('a, [data-close]')?.focus();
    }
    clavierRef.current = false;
  }, [pinned]);

  // Un clic ou un toucher hors d'un point et de l'infobulle désépingle.
  useEffect(() => {
    if (!pinned) return undefined;
    const surPointerDown = (e) => {
      if (e.target.closest?.('.zn-node, .zn-tooltip')) return;
      setPinned(null);
      setHover(null);
    };
    document.addEventListener('pointerdown', surPointerDown);
    return () => document.removeEventListener('pointerdown', surPointerDown);
  }, [pinned]);

  useEffect(() => {
    let alive = true;
    setError(false);
    axios
      .get(`${API}/zlecaf/network?lang=${lang}`)
      .then((res) => { if (alive) setData(res.data); })
      .catch(() => { if (alive) setError(true); });
    return () => { alive = false; };
  }, [lang]);

  const model = useMemo(() => {
    if (!data) return null;
    const pays = Object.fromEntries(data.pays.map((p) => [p.iso3, p]));
    const sortantes = {};
    const recues = {};
    for (const l of data.liaisons) {
      (sortantes[l.importateur] ||= new Set()).add(l.origine);
      (recues[l.origine] ||= new Set()).add(l.importateur);
    }
    // Une courbe par paire d'États, quel que soit le sens.
    const paires = new Map();
    for (const l of data.liaisons) {
      const [a, b] = [l.importateur, l.origine].sort();
      if (geo.capitals[a] && geo.capitals[b]) paires.set(`${a}-${b}`, [a, b]);
    }
    const noeuds = data.pays
      .filter((p) => geo.capitals[p.iso3])
      .map((p) => ({ ...p, cap: geo.capitals[p.iso3], r: rayon(p.pib_usd) }))
      .sort((a, b) => b.r - a.r); // les grands ronds dessous
    const compte = {};
    for (const p of data.pays) compte[p.statut] = (compte[p.statut] || 0) + 1;
    return { pays, sortantes, recues, paires: [...paires.values()], noeuds, compte };
  }, [data]);

  const actif = pinned || hover;

  if (error) {
    return (
      <Card><CardContent className="py-10 text-center text-sm" role="alert">{txt.error}</CardContent></Card>
    );
  }
  if (!model) {
    return (
      <Card><CardContent className="py-10 text-center text-sm">{txt.loading}</CardContent></Card>
    );
  }

  const year = data.pib_annee;
  const pib = (v) => montantCompact(v, lang, { B: 1, M: 0 }, { max: true });
  const pibTexte = (p) =>
    p.pib_usd == null ? fill(txt.gdpNa, { year }) : `${fill(txt.gdp, { year })} : ${pib(p.pib_usd)}`;
  const capitale = (iso3) => {
    const c = geo.capitals[iso3];
    return c ? (lang === 'fr' ? c.name_fr : c.name) : null;
  };
  const lie = (iso3) =>
    iso3 === actif || model.sortantes[actif]?.has(iso3) || model.recues[actif]?.has(iso3);
  const estAttenue = (p) =>
    p.iso3 !== actif && ((focusNiveau && p.statut !== focusNiveau) || (actif && !lie(p.iso3)));

  const choisir = (iso3) => setPinned((cur) => (cur === iso3 ? null : iso3));
  const fermer = () => {
    const iso3 = pinned;
    setPinned(null);
    if (iso3) nodeRefs.current[iso3]?.focus();
    // Le focus rendu au point ne doit pas rouvrir l'infobulle.
    setHover(null);
  };
  const onKey = (e, iso3) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      clavierRef.current = pinned !== iso3;
      choisir(iso3);
    }
    if (e.key === 'Escape') setPinned(null);
  };

  const tip = actif && model.pays[actif] && geo.capitals[actif] ? model.pays[actif] : null;
  const tipCap = tip ? geo.capitals[tip.iso3] : null;
  const tipLeft = tipCap ? ((tipCap.x - VB_X) / VB_W) * 100 : 0;
  const tipTop = tipCap ? ((tipCap.y - VB_Y) / VB_H) * 100 : 0;
  const echelle = largeur ? largeur / VB_W : 0; // px par degré

  const lignes = [...data.pays].sort(
    (a, b) => data.niveaux.indexOf(b.statut) - data.niveaux.indexOf(a.statut)
      || a.nom.localeCompare(b.nom, lang),
  );

  const swatch = (niveau) => (
    <span
      className={`zn-swatch${creuxNiveau(niveau) ? ' is-hollow' : ''}`}
      style={{ background: color(niveau) }}
    />
  );

  return (
    <Card data-testid="zlecaf-network">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5" style={{ color: 'var(--gold)' }} />
          {txt.title}
        </CardTitle>
        <CardDescription>
          {txt.subtitle}. {fill(txt.asOf, { date: dateLongue(data.date, lang) })} {txt.hint}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="zn-canvas">
          <div className="zn-map-wrap" ref={wrapRef}>
            <svg
              viewBox={VIEWBOX}
              role="group"
              aria-label={txt.title}
              onClick={(e) => { if (!e.target.closest('.zn-node')) { setPinned(null); setHover(null); } }}
            >
              <defs>
                <linearGradient id="zn-rim" gradientUnits="userSpaceOnUse" x1="0" y1={VB_Y} x2="0" y2={VB_Y + VB_H}>
                  <stop offset="0" stopColor="#FFD27A" />
                  <stop offset=".45" stopColor="#E9A23B" />
                  <stop offset="1" stopColor="#DE7A49" />
                </linearGradient>
                <radialGradient id="zn-core" cx="50%" cy="42%" r="60%">
                  <stop offset="0" stopColor="#11281C" />
                  <stop offset=".6" stopColor="#0A1610" />
                  <stop offset="1" stopColor="#070C0A" />
                </radialGradient>
                <filter id="zn-halo" x="-10%" y="-10%" width="120%" height="120%">
                  <feGaussianBlur stdDeviation="1.1" />
                </filter>
              </defs>

              <path d={geo.coast} fill="none" stroke="#E9A23B" strokeWidth="1.6" strokeOpacity=".45" filter="url(#zn-halo)" />
              <path d={geo.land} fill="url(#zn-core)" />
              <path d={geo.coast} fill="none" stroke="url(#zn-rim)" strokeWidth=".28" strokeLinejoin="round" />

              <g fill="none" strokeLinecap="round">
                {model.paires.map(([a, b]) => {
                  const on = actif && (a === actif || b === actif);
                  return (
                    <path
                      key={`${a}-${b}`}
                      d={courbe(geo.capitals[a], geo.capitals[b])}
                      stroke="#E8B04A"
                      strokeWidth={on ? 0.22 : 0.12}
                      strokeOpacity={actif ? (on ? 0.9 : 0.05) : (focusNiveau ? 0.08 : 0.28)}
                    />
                  );
                })}
              </g>

              {model.noeuds.map((p) => {
                const { x, y } = p.cap;
                const creux = creuxNiveau(p.statut);
                const sansPib = p.pib_usd == null;
                const label = `${p.nom} — ${NIVEAUX[p.statut][lang]} — ${pibTexte(p)}`;
                return (
                  <g
                    key={p.iso3}
                    ref={(el) => { nodeRefs.current[p.iso3] = el; }}
                    className="zn-node"
                    role="button"
                    tabIndex={0}
                    aria-label={label}
                    aria-pressed={pinned === p.iso3}
                    data-testid={`zn-node-${p.iso3}`}
                    opacity={estAttenue(p) ? 0.18 : 1}
                    onMouseEnter={() => setHover(p.iso3)}
                    onMouseLeave={() => setHover(null)}
                    onFocus={() => setHover(p.iso3)}
                    onBlur={() => setHover(null)}
                    onClick={() => choisir(p.iso3)}
                    onKeyDown={(e) => onKey(e, p.iso3)}
                  >
                    {/* Cible un peu plus grande que la marque, sans recouvrir les voisins. */}
                    <circle cx={x} cy={y} r={p.r + 0.4} fill="transparent" />
                    <circle
                      className="zn-node-ring"
                      cx={x}
                      cy={y}
                      r={p.r}
                      fill={creux ? 'none' : color(p.statut)}
                      fillOpacity=".88"
                      stroke={creux ? color(p.statut) : 'var(--zn-surface)'}
                      strokeWidth={creux ? '.3' : '.22'}
                    />
                    {sansPib && (
                      <circle
                        cx={x}
                        cy={y}
                        r={p.r + 0.4}
                        fill="none"
                        stroke="var(--zn-muted)"
                        strokeWidth=".12"
                        strokeDasharray=".35 .25"
                        data-testid={`zn-nogdp-${p.iso3}`}
                      />
                    )}
                    <circle cx={x} cy={y} r=".26" fill="#F7F1E6" />
                  </g>
                );
              })}
            </svg>

            {tip && (
              <div
                ref={tipRef}
                className={`zn-tooltip${pinned ? ' is-pinned' : ''}`}
                role="status"
                data-testid="zn-tooltip"
                onKeyDown={(e) => { if (e.key === 'Escape') fermer(); }}
                style={{
                  left: `${tipLeft}%`,
                  top: `${tipTop}%`,
                  // À droite du point, ou à gauche s'il est dans le tiers est ;
                  // sous le point dans le tiers nord, au-dessus dans le tiers sud.
                  transform: `translate(${tipLeft > 62 ? 'calc(-100% - 14px)' : '14px'}, ${
                    tipTop < 30 ? '-12px' : tipTop > 70 ? 'calc(-100% + 12px)' : '-50%'
                  })`,
                }}
              >
                <h4>{tip.nom}</h4>
                <div className="zn-muted">{capitale(tip.iso3)}</div>
                <div style={{ marginTop: 6 }}>
                  {swatch(tip.statut)}
                  {NIVEAUX[tip.statut][lang]}
                </div>
                <div>{pibTexte(tip)}</div>
                <div className="zn-muted">
                  {fill(txt.out, { n: model.sortantes[tip.iso3]?.size || 0 })} ·{' '}
                  {fill(txt.in, { n: model.recues[tip.iso3]?.size || 0 })}
                </div>
                <div style={{ marginTop: 6, fontWeight: 600 }}>{txt.proofs}</div>
                <ul style={{ margin: '2px 0 0 14px', listStyle: 'disc' }}>
                  {tip.preuves
                    .filter((p) => p.niveau === tip.statut)
                    .map((p, i) => (
                      <li key={i}>
                        {p.url && pinned ? (
                          <a href={p.url} target="_blank" rel="noopener noreferrer">{p.source}</a>
                        ) : p.source}
                        {pinned && p.note && <div className="zn-muted zn-note">{p.note}</div>}
                      </li>
                    ))}
                </ul>
                {pinned && (
                  <button type="button" className="zn-close" onClick={fermer} data-close>
                    {txt.close}
                  </button>
                )}
              </div>
            )}
          </div>

          <div className="zn-legend" role="group" aria-label={txt.status}>
            {data.niveaux.map((n) => (
              <button
                key={n}
                type="button"
                aria-pressed={focusNiveau === n}
                onClick={() => setFocusNiveau((cur) => (cur === n ? null : n))}
                data-testid={`zn-legend-${n}`}
              >
                {swatch(n)}
                <b>{model.compte[n] || 0}</b>
                {NIVEAUX[n][lang]}
              </button>
            ))}
          </div>

          <div className="zn-sizes" data-testid="zn-sizes">
            <span>{fill(txt.size, { year })}</span>
            {echelle > 0 && TAILLES.map((v) => {
              const d = 2 * rayon(v * 1e9) * echelle;
              return (
                <span key={v} className="zn-size">
                  <i style={{ width: d, height: d }} />
                  {v}
                </span>
              );
            })}
            <span className="zn-muted">{fill(txt.sizeFloor, { min: PIB_PLANCHER })}</span>
          </div>

          <div className="zn-footnote">
            <span className="zn-link-swatch" />
            {txt.link}
          </div>

          <details className="zn-details">
            <summary>{fill(txt.table, { n: data.pays.length })}</summary>
            <div style={{ overflowX: 'auto' }}>
              <table className="zn-table">
                <thead>
                  <tr>
                    <th>{txt.country}</th>
                    <th>{txt.capital}</th>
                    <th>{txt.status}</th>
                    <th style={{ textAlign: 'right' }}>{fill(txt.gdp, { year })}</th>
                    <th style={{ textAlign: 'right' }}>{txt.links}</th>
                    <th>{txt.source}</th>
                  </tr>
                </thead>
                <tbody>
                  {lignes.map((p) => {
                    const principale = p.preuves.find((q) => q.niveau === p.statut);
                    return (
                      <tr key={p.iso3} data-testid={`zn-row-${p.iso3}`}>
                        <td>{p.nom}</td>
                        <td>{capitale(p.iso3) || <span className="zn-muted">{txt.noPoint}</span>}</td>
                        <td>
                          {swatch(p.statut)}
                          {NIVEAUX[p.statut][lang]}
                        </td>
                        <td className="zn-num">{p.pib_usd == null ? '—' : pib(p.pib_usd)}</td>
                        <td className="zn-num">
                          {model.sortantes[p.iso3]?.size || 0} / {model.recues[p.iso3]?.size || 0}
                        </td>
                        <td>{principale?.source}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </details>

          <div className="zn-footnote">
            <strong>{txt.limits}</strong>
            <ul>
              {txt.limitsList.map((l, i) => <li key={i}>{l}</li>)}
            </ul>
            <strong>{txt.sources}</strong>
            <ul>
              <li>{txt.gdpSource}, {year}.</li>
              {geo.sources.map((s) => (
                <li key={s.url}>{lang === 'en' ? s.label.replace('domaine public', 'public domain') : s.label}</li>
              ))}
            </ul>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
