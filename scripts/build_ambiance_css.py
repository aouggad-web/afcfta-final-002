"""Génère frontend/src/styles/ambiance.css : zellige de Tlemcen et kente, couleurs par thème.

Usage : python3 scripts/build_ambiance_css.py [frontend/src/styles/ambiance.css]

Les motifs sont des SVG en data URI, recolorés par thème (or saharien en
sombre, terre de Tlemcen en clair). Modifier ici les géométries, les couleurs
et les opacités (SOMBRE, CLAIR), puis régénérer.
"""

import math
import sys
import urllib.parse


def etoile(cx, cy, R, r, n=8, rot=-90):
    pts = []
    for k in range(2 * n):
        a = math.radians(rot + k * 180 / n)
        rr = R if k % 2 == 0 else r
        pts.append(f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}")
    return "<polygon points='" + " ".join(pts) + "'/>"


def carre45(cx, cy, c):
    return f"<rect x='{cx - c / 2:.2f}' y='{cy - c / 2:.2f}' width='{c:.2f}' height='{c:.2f}' transform='rotate(45 {cx} {cy})'/>"


def svg(w, h, corps, trait, epaisseur):
    s = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
        f"<g fill='none' stroke='{trait}' stroke-width='{epaisseur}' stroke-linejoin='round'>{corps}</g></svg>"
    )
    return 'url("data:image/svg+xml,' + urllib.parse.quote(s, safe="=:/,'() .") + '")'


T = 64


def pavage(trait, ep):
    c = T / 2
    corps = etoile(c, c, 22, 9) + carre45(c, c, 22) + f"<circle cx='{c}' cy='{c}' r='5'/>"
    for x, y in ((0, 0), (T, 0), (0, T), (T, T)):
        corps += etoile(x, y, 12, 5)
    # liens entre les pointes : le réseau continu du zellige
    corps += f"<path d='M{c} {c - 22}L{c} 0M{c} {c + 22}L{c} {T}M{c - 22} {c}L0 {c}M{c + 22} {c}L{T} {c}'/>"
    return svg(T, T, corps, trait, ep)


def rosace(trait, ep):
    corps = (
        etoile(140, 130, 70, 28)
        + carre45(140, 130, 70)
        + "<circle cx='140' cy='130' r='24'/>"
        + etoile(140, 130, 40, 16, rot=-67.5)
        + "<circle cx='140' cy='130' r='96'/>"
        + etoile(50, 40, 30, 12)
        + etoile(230, 40, 30, 12)
        + etoile(50, 220, 30, 12)
        + etoile(230, 220, 30, 12)
    )
    return svg(280, 260, corps, trait, ep)


def frise(trait, ep):
    corps = etoile(11, 6, 5, 2.2) + "<path d='M0 6L6 6M16 6L22 6'/>"
    return svg(22, 12, corps, trait, ep)


KENTE = """repeating-linear-gradient(90deg,
    #C8102E 0px, #C8102E 9px, #FCDD09 9px, #FCDD09 18px, #007A3D 18px, #007A3D 27px,
    #0D0800 27px, #0D0800 32px, #E8890C 32px, #E8890C 41px, #0D0800 41px, #0D0800 46px)"""

# (couleur du trait par thème) — or saharien en sombre, terre de Tlemcen en clair
SOMBRE = {
    "page": ("rgba(212,137,26,0.11)", 1),
    "bandeau": ("rgba(212,137,26,0.14)", 1),
    "frise": ("rgba(212,137,26,0.55)", 1),
}
CLAIR = {
    "page": ("rgba(156,63,21,0.10)", 1),
    "bandeau": ("rgba(156,63,21,0.12)", 1),
    "frise": ("rgba(134,86,8,0.50)", 1),
}

css = f"""/* ════════════════════════════════════════════════════════════════
   Ambiance — zellige de Tlemcen et kente panafricain
   ════════════════════════════════════════════════════════════════
   Couche ornementale seule, chargée après les thèmes : elle ne touche
   ni aux couleurs du texte, ni aux polices, ni aux composants. Les
   motifs se posent sous le contenu, jamais derrière un texte de carte
   (les cartes sont opaques). Généré par un script : pavage à étoiles à
   huit branches (najm) reliées en réseau, frise pour le bandeau
   d'accueil, bande kente en haut de l'écran.

   Le fichier design-system.css portait ces motifs depuis avril, mais
   son import a disparu de index.js le 05/09 (audit) : il n'est plus
   chargé. On n'en reprend que l'ornement, recoloré par thème ; ses
   classes génériques (.stat-label, .section-title…) auraient écrasé
   les thèmes actuels.

   Fichier généré par scripts/build_ambiance_css.py : modifier le script,
   puis régénérer. */

/* Bande kente — 4 px, en haut de chaque écran */
.kente-band {{
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 200;
  height: 4px;
  background: {KENTE};
  pointer-events: none;
}}

/* Fond de page : pavage zellige sur le conteneur principal */
.zellige-najm {{
  background-image: {pavage(*SOMBRE['page'])};
  background-size: {T}px {T}px;
}}
html.theme-light .zellige-najm {{
  background-image: {pavage(*CLAIR['page'])};
}}

/* Bandeaux (Statistiques) : le même pavage, un peu plus présent */
.stats-hero::before {{
  background-image: {pavage(*SOMBRE['bandeau'])};
  background-size: {T}px {T}px;
}}
html.theme-light .stats-hero::before {{
  background-image: {pavage(*CLAIR['bandeau'])};
}}

/* Frise zellige — bord supérieur d'un bandeau (classe zellige-frise).
   Posée dans la marge haute : elle ne passe derrière aucun texte. */
.zellige-frise {{
  position: relative;
}}
.zellige-frise::before {{
  content: "";
  position: absolute;
  top: 6px;
  left: 0;
  right: 0;
  height: 12px;
  background-image: {frise(*SOMBRE['frise'])};
  background-size: 22px 12px;
  background-repeat: repeat-x;
  pointer-events: none;
}}
html.theme-light .zellige-frise::before {{
  background-image: {frise(*CLAIR['frise'])};
}}
"""
sortie = sys.argv[1] if len(sys.argv) > 1 else "frontend/src/styles/ambiance.css"
open(sortie, "w", encoding="utf-8").write(css)
print("écrit", sortie, len(css), "octets")
