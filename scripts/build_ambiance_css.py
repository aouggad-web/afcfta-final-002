"""Génère frontend/src/styles/ambiance.css : zellige en trame de fond, velours du Kasaï dans les bandeaux.

Usage : python3 scripts/build_ambiance_css.py [frontend/src/styles/ambiance.css]

Les motifs sont des SVG en data URI, recolorés par thème (or saharien en
sombre, terre de Tlemcen en clair), avec une touche discrète du bleu et du
vert de Ghardaïa. Modifier ici les géométries, les couleurs et les opacités
(SOMBRE, CLAIR), puis régénérer.
"""

import sys
import urllib.parse


def uri(w, h, corps):
    s = f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>{corps}</svg>"
    return 'url("data:image/svg+xml,' + urllib.parse.quote(s, safe="=:/,'() .") + '")'


T = 56  # côté du carreau de fond


def etoile_croix(trait, bleu, vert):
    """Étoile et croix : deux carrés entrelacés au centre et aux coins, le
    réseau classique du zellige. Au cœur de chaque étoile, un petit carreau
    plein, bleu au centre, vert aux coins : la touche de Ghardaïa."""
    g = ""
    for x, y in ((T // 2, T // 2), (0, 0), (T, 0), (0, T), (T, T)):
        s = 14
        g += f"<rect x='{x - s}' y='{y - s}' width='{2 * s}' height='{2 * s}'/>"
        g += f"<rect x='{x - s}' y='{y - s}' width='{2 * s}' height='{2 * s}' transform='rotate(45 {x} {y})'/>"
    coeurs = f"<rect x='{T // 2 - 3}' y='{T // 2 - 3}' width='6' height='6' transform='rotate(45 {T // 2} {T // 2})' fill='{bleu}'/>"
    for x, y in ((0, 0), (T, 0), (0, T), (T, T)):
        coeurs += f"<rect x='{x - 3}' y='{y - 3}' width='6' height='6' transform='rotate(45 {x} {y})' fill='{vert}'/>"
    return uri(T, T, f"<g fill='none' stroke='{trait}' stroke-width='1'>{g}</g>{coeurs}")


def kasai(fond, motif, bleu, vert):
    """Velours du Kasaï : losanges entrelacés sur une bande de 10 px. Les
    petits losanges intérieurs alternent le bleu et le vert de Ghardaïa."""
    g = f"<rect width='24' height='10' fill='{fond}'/>"
    g += f"<path d='M0 5L6 0L12 5L6 10Z M12 5L18 0L24 5L18 10Z' fill='none' stroke='{motif}' stroke-width='1.4'/>"
    g += f"<path d='M6 3L8 5L6 7L4 5Z' fill='{bleu}'/><path d='M18 3L20 5L18 7L16 5Z' fill='{vert}'/>"
    return uri(24, 10, g)


KENTE = """repeating-linear-gradient(90deg,
    #C8102E 0px, #C8102E 9px, #FCDD09 9px, #FCDD09 18px, #007A3D 18px, #007A3D 27px,
    #0D0800 27px, #0D0800 32px, #E8890C 32px, #E8890C 41px, #0D0800 41px, #0D0800 46px)"""

# Or saharien en sombre, terre de Tlemcen en clair ; bleu et vert de Ghardaïa
# en retrait : pleins dans la bande, à peine visibles dans le fond.
SOMBRE = {
    "fond": ("rgba(212,137,26,0.10)", "rgba(74,144,200,0.16)", "rgba(62,160,110,0.14)"),
    "bande": ("#1B1206", "#D4891A", "#4A90C8", "#3EA06E"),
}
CLAIR = {
    "fond": ("rgba(156,63,21,0.10)", "rgba(36,104,160,0.12)", "rgba(40,120,80,0.11)"),
    "bande": ("#F3E6CC", "#8A4B12", "#2F6FA8", "#2E7D57"),
}

BANDEAUX = ".afcfta-sectionHead, .stats-hero, .zellige-frise"
APRES = ", ".join(f"{s}::after" for s in BANDEAUX.split(", "))
APRES_CLAIR = ", ".join(f"html.theme-light {s}::after" for s in BANDEAUX.split(", "))

css = f"""/* ════════════════════════════════════════════════════════════════
   Ambiance — zellige en trame de fond, velours du Kasaï dans les bandeaux
   ════════════════════════════════════════════════════════════════
   Couche ornementale seule, chargée après les thèmes : elle ne touche
   ni aux couleurs du texte, ni aux polices, ni aux composants.

   - Fond de page : réseau étoile-et-croix du zellige, filaire, avec au
     cœur des étoiles un petit carreau bleu ou vert de Ghardaïa.
   - Bandeaux (en-têtes de section, Statistiques, accueil) : aucun pavage
     derrière les titres, seulement une bande de velours du Kasaï sur le
     bord supérieur ; ses petits losanges alternent le bleu et le vert de
     Ghardaïa.
   - Bande kente de 4 px en haut de l'écran.

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

/* Fond de page : trame zellige sur le conteneur principal */
.zellige-najm {{
  background-image: {etoile_croix(*SOMBRE['fond'])};
  background-size: {T}px {T}px;
}}
html.theme-light .zellige-najm {{
  background-image: {etoile_croix(*CLAIR['fond'])};
}}

/* Bandeaux : pas de pavage derrière les titres, fond opaque */
.stats-hero::before {{
  background-image: none;
}}
{BANDEAUX} {{
  position: relative;
  overflow: hidden;
}}
.afcfta-sectionHead {{
  background-color: var(--afcfta-card);
}}
.afcfta-sectionHead, .stats-hero {{
  padding-top: 30px;
}}

/* Velours du Kasaï — bord supérieur de chaque bandeau, au-dessus du titre */
{APRES} {{
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 10px;
  background-image: {kasai(*SOMBRE['bande'])};
  background-size: 24px 10px;
  background-repeat: repeat-x;
  pointer-events: none;
}}
{APRES_CLAIR} {{
  background-image: {kasai(*CLAIR['bande'])};
}}
"""
sortie = sys.argv[1] if len(sys.argv) > 1 else "frontend/src/styles/ambiance.css"
open(sortie, "w", encoding="utf-8").write(css)
print("écrit", sortie, len(css), "octets")
