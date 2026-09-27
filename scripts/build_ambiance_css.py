"""Génère frontend/src/styles/ambiance.css : zellige en trame de fond, velours du Kasaï dans les bandeaux.

Usage : python3 scripts/build_ambiance_css.py [frontend/src/styles/ambiance.css]

Les motifs sont des SVG en data URI, recolorés par thème (or saharien en
sombre, terre de Tlemcen en clair), avec une touche discrète du bleu et du
vert de Ghardaïa. Modifier ici les géométries, les couleurs et les opacités
(SOMBRE, CLAIR), puis régénérer.
"""

import math
import sys
import urllib.parse


def uri(w, h, corps):
    s = f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>{corps}</svg>"
    return 'url("data:image/svg+xml,' + urllib.parse.quote(s, safe="=:/,'() .") + '")'


T = 80  # côté du carreau de fond


def _etoile(cx, cy, r):
    """Étoile à 8 branches (deux carrés superposés) : 16 sommets alternant la
    pointe (r) et le creux entre deux pointes."""
    creux = r * math.cos(math.pi / 4) / math.cos(math.pi / 8)
    pts = []
    for k in range(16):
        a = math.pi / 8 * k - math.pi / 2
        rr = r if k % 2 == 0 else creux
        pts.append(f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}")
    return " ".join(pts)


def _octogone(cx, cy, r):
    return " ".join(
        f"{cx + r * math.cos(math.pi / 8 + math.pi / 4 * k):.2f},"
        f"{cy + r * math.sin(math.pi / 8 + math.pi / 4 * k):.2f}"
        for k in range(8)
    )


def khatam(ruban, fond_etoile, coeur):
    """Khatam de Tlemcen : étoiles à 8 branches dont les pointes se touchent,
    bordées d'un double ruban doré (effet d'entrelacs), un octogone bleu au
    cœur. Les croix apparaissent en creux entre les étoiles. Intensités basses :
    le motif doit rester lisible sans gêner la lecture des chiffres."""
    r = T / 4 * math.sqrt(2)  # pointes jointives sur les diagonales
    g = ""
    for x, y in ((T / 2, T / 2), (0, 0), (T, 0), (0, T), (T, T)):
        g += f"<polygon points='{_etoile(x, y, r)}' fill='{fond_etoile}' stroke='{ruban}' stroke-width='1.6'/>"
        g += f"<polygon points='{_etoile(x, y, r * 0.78)}' fill='none' stroke='{ruban}' stroke-width='1'/>"
        g += f"<polygon points='{_octogone(x, y, r * 0.36)}' fill='{coeur}' stroke='{ruban}' stroke-width='0.8'/>"
    return uri(T, T, g)


def kasai(fond, motif, bleu, vert):
    """Velours du Kasaï : losanges entrelacés sur une bande de 10 px. Les
    petits losanges intérieurs alternent le bleu et le vert de Ghardaïa."""
    g = f"<rect width='24' height='10' fill='{fond}'/>"
    g += f"<path d='M0 5L6 0L12 5L6 10Z M12 5L18 0L24 5L18 10Z' fill='none' stroke='{motif}' stroke-width='1.4'/>"
    g += f"<path d='M6 3L8 5L6 7L4 5Z' fill='{bleu}'/><path d='M18 3L20 5L18 7L16 5Z' fill='{vert}'/>"
    return uri(24, 10, g)


def kente(sens):
    """Tissage kente : blocs rouge, or, vert, orange séparés de fils noirs,
    avec un fil sombre au milieu de la bande pour l'effet de trame.
    `sens` : 90deg (bande horizontale) ou 180deg (lisière verticale)."""
    travers = "180deg" if sens == "90deg" else "90deg"
    return f"""linear-gradient({travers},
    transparent 46%, rgba(13,8,0,0.3) 46%, rgba(13,8,0,0.3) 54%, transparent 54%),
  repeating-linear-gradient({sens},
    #C8102E 0px, #C8102E 12px, #0D0800 12px, #0D0800 14px,
    #FCDD09 14px, #FCDD09 26px, #0D0800 26px, #0D0800 28px,
    #007A3D 28px, #007A3D 40px, #0D0800 40px, #0D0800 42px,
    #E8890C 42px, #E8890C 54px, #0D0800 54px, #0D0800 56px)"""


KENTE = kente("90deg")
KENTE_V = kente("180deg")
KENTE_H = 10  # épaisseur de la bande du haut (px)

# Or saharien en sombre, terre de Tlemcen en clair ; bleu et vert de Ghardaïa
# en retrait : pleins dans la bande, discrets dans le fond (ruban, fond
# d'étoile, cœur). Priorité à la lisibilité : ne monter ces opacités qu'en
# vérifiant le contraste du texte posé sur les cartes.
SOMBRE = {
    "fond": ("rgba(212,137,26,0.16)", "rgba(14,138,122,0.045)", "rgba(27,108,168,0.13)"),
    "bande": ("#1B1206", "#D4891A", "#4A90C8", "#3EA06E"),
}
CLAIR = {
    "fond": ("rgba(138,75,18,0.13)", "rgba(14,138,122,0.035)", "rgba(27,108,168,0.085)"),
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

   - Fond de page : khatam de Tlemcen, étoiles à 8 branches bordées d'un
     double ruban doré, octogone bleu au cœur, croix en creux.
   - Bandeaux (en-têtes de section, Statistiques, accueil) : aucun pavage
     derrière les titres, seulement une bande de velours du Kasaï sur le
     bord supérieur ; ses petits losanges alternent le bleu et le vert de
     Ghardaïa.
   - Tissage kente (couleurs panafricaines) sur les bordures, jamais
     derrière le texte : bande de 10 px en haut de l'écran, lisière verticale
     de la barre latérale, bas de la barre mobile, haut des fenêtres, et
     soulignés des titres de Statistiques.

   Fichier généré par scripts/build_ambiance_css.py : modifier le script,
   puis régénérer. */

/* Bande kente — en haut de chaque écran */
.kente-band {{
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 200;
  height: {KENTE_H}px;
  background: {KENTE};
  box-shadow: 0 1px 0 rgba(212,137,26,0.55);
  pointer-events: none;
}}

/* Lisière kente verticale sur le bord droit de la barre latérale */
.afcfta-sidebar::after {{
  content: "";
  position: absolute;
  top: 0; right: 0; bottom: 0;
  width: 5px;
  background: {KENTE_V};
  pointer-events: none;
}}

/* Barre du haut (mobile / tablette) : kente sous la barre */
.afcfta-topHeader {{
  border-bottom: 0;
}}
.afcfta-topHeader::after {{
  content: "";
  display: block;
  height: 5px;
  background: {KENTE};
}}

/* Fenêtres (connexion, Mon compte…) : kente en tête */
[role="dialog"]::before {{
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 6px;
  background: {KENTE};
  border-top-left-radius: inherit;
  border-top-right-radius: inherit;
  pointer-events: none;
}}

/* Soulignés kente des titres (Statistiques) : plus affirmés */
.stats-kente-bar {{
  height: 5px !important;
  background: {KENTE} !important;
}}

/* Fond de page : trame zellige sur le conteneur principal */
.zellige-najm {{
  background-image: {khatam(*SOMBRE['fond'])};
  background-size: {T}px {T}px;
}}
html.theme-light .zellige-najm {{
  background-image: {khatam(*CLAIR['fond'])};
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
