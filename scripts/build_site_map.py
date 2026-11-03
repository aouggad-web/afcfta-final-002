"""Pré-rend la carte « Réseau ZLECAf » en SVG statique pour site/index.html.

Reprend à l'identique le dessin de frontend/src/components/statistics/
ZlecafNetworkMap.jsx (cadre, contour, liseré, courbes, ronds) à partir de la
géographie du dépôt et d'un instantané de /api/zlecaf/network.

Rafraîchir la carte de la vitrine (statuts et liaisons du jour) :

    curl -sS "$BACKEND/api/zlecaf/network" -o /tmp/network.json
    python scripts/build_site_map.py frontend/src/data/zlecafNetworkGeo.json \
        /tmp/network.json site/index.html

Remplace le bloc entre <!-- RESEAU:START --> et <!-- RESEAU:END -->.
"""

import html
import json
import math
import sys

geo_path, net_path, index_path = sys.argv[1:4]
geo = json.load(open(geo_path, encoding="utf-8"))
net = json.load(open(net_path, encoding="utf-8"))

COLORS = {
    "non_signataire": "#6B7688",
    "signe_non_ratifie": "#6B7688",
    "ratifie": "#9D6BFE",
    "offre_tarifaire": "#0C83AB",
    "instrument_adopte": "#C57D06",
    "deploiement": "#03A762",
}
LABELS = {
    "non_signataire": ("Non signataire", "Not signed", "غير موقِّعة"),
    "signe_non_ratifie": ("Signé, non ratifié", "Signed, not ratified", "موقِّعة، غير مصادِقة"),
    "ratifie": ("Ratifié", "Ratified", "مصادِقة"),
    "offre_tarifaire": ("Offre tarifaire", "Tariff offer", "عرض التعريفات الجمركية"),
    "instrument_adopte": (
        "Instrument national adopté",
        "National instrument adopted",
        "صك وطني معتمد",
    ),
    "deploiement": ("Déploiement", "Implementation", "قيد التطبيق"),
}
SURFACE = "#0C1219"
K, R_MIN, MARGE = 0.2, 0.55, 4.5


def rayon(pib):
    return R_MIN if pib is None else max(R_MIN, K * math.sqrt(pib / 1e9))


def n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def courbe(a, b):
    mx, my = (a["x"] + b["x"]) / 2, (a["y"] + b["y"]) / 2
    dx, dy = b["x"] - a["x"], b["y"] - a["y"]
    k = 0.12
    return f"M{n(a['x'])} {n(a['y'])}Q{n(mx - dy * k)} {n(my + dx * k)} {n(b['x'])} {n(b['y'])}"


def pib_txt(pib, annee):
    if pib is None:
        return f"PIB {annee} non disponible"
    md = pib / 1e9
    return (
        f"PIB {annee} : {md:,.0f} Md $".replace(",", " ")
        if md >= 10
        else f"PIB {annee} : {md:.1f} Md $".replace(".", ",")
    )


x, y, w, h = (float(v) for v in geo["viewBox"])
vb = f"{n(x - MARGE)} {n(y - MARGE)} {n(w + 2 * MARGE)} {n(h + 2 * MARGE)}"
caps = geo["capitals"]

paires = {}
for l in net["liaisons"]:
    a, b = sorted((l["importateur"], l["origine"]))
    if a in caps and b in caps:
        paires[f"{a}-{b}"] = (a, b)

noeuds = sorted(
    (dict(p, cap=caps[p["iso3"]], r=rayon(p["pib_usd"])) for p in net["pays"] if p["iso3"] in caps),
    key=lambda p: -p["r"],
)

annee = net["pib_annee"]
out = []
out.append(
    f'<svg viewBox="{vb}" role="img" aria-labelledby="zn-t zn-d" xmlns="http://www.w3.org/2000/svg">'
)
out.append('<title id="zn-t">Réseau ZLECAf — mise en œuvre de l’accord, pays par pays</title>')
out.append(
    f'<desc id="zn-d">{len(noeuds)} capitales africaines ; surface du rond selon le PIB {annee}, '
    f"couleur selon le statut de mise en œuvre ; {len(paires)} liaisons entre États appliquant "
    "la préférence ZLECAf.</desc>"
)
out.append(
    "<defs>"
    f'<linearGradient id="zn-rim" gradientUnits="userSpaceOnUse" x1="0" y1="{n(y - MARGE)}" x2="0" y2="{n(y + h + MARGE)}">'
    '<stop offset="0" stop-color="#FFD27A"/><stop offset=".45" stop-color="#E9A23B"/><stop offset="1" stop-color="#DE7A49"/>'
    "</linearGradient>"
    '<radialGradient id="zn-core" cx="50%" cy="42%" r="60%">'
    '<stop offset="0" stop-color="#11281C"/><stop offset=".6" stop-color="#0A1610"/><stop offset="1" stop-color="#070C0A"/>'
    "</radialGradient>"
    '<filter id="zn-halo" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="1.1"/></filter>'
    "</defs>"
)
out.append(
    f'<path d="{geo["coast"]}" fill="none" stroke="#E9A23B" stroke-width="1.6" stroke-opacity=".45" filter="url(#zn-halo)"/>'
)
out.append(f'<path d="{geo["land"]}" fill="url(#zn-core)"/>')
out.append(
    f'<path d="{geo["coast"]}" fill="none" stroke="url(#zn-rim)" stroke-width=".28" stroke-linejoin="round"/>'
)
out.append(
    '<g fill="none" stroke="#E8B04A" stroke-width=".12" stroke-opacity=".28" stroke-linecap="round">'
)
for a, b in paires.values():
    out.append(f'<path d="{courbe(caps[a], caps[b])}"/>')
out.append("</g>")
for p in noeuds:
    cx, cy, r = n(p["cap"]["x"]), n(p["cap"]["y"]), p["r"]
    creux = p["statut"] == "non_signataire"
    col = COLORS[p["statut"]]
    tip = html.escape(f"{p['nom']} — {LABELS[p['statut']][0]} — {pib_txt(p['pib_usd'], annee)}")
    out.append(f"<g><title>{tip}</title>")
    if creux:
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{n(r)}" fill="none" stroke="{col}" stroke-width=".3"/>'
        )
    else:
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{n(r)}" fill="{col}" fill-opacity=".88" stroke="{SURFACE}" stroke-width=".22"/>'
        )
    if p["pib_usd"] is None:
        out.append(
            f'<circle cx="{cx}" cy="{cy}" r="{n(r + 0.4)}" fill="none" stroke="#9AA6B6" stroke-width=".12" stroke-dasharray=".35 .25"/>'
        )
    out.append(f'<circle cx="{cx}" cy="{cy}" r=".26" fill="#F7F1E6"/></g>')
out.append("</svg>")
svg = "\n".join(out)

compte = {}
for p in net["pays"]:
    compte[p["statut"]] = compte.get(p["statut"], 0) + 1
legende = []
for niveau in reversed(net["niveaux"]):
    if not compte.get(niveau):
        continue
    fr, en, ar = LABELS[niveau]
    sw = (
        '<i class="sw hollow"></i>'
        if niveau == "non_signataire"
        else f'<i class="sw" style="background:{COLORS[niveau]}"></i>'
    )
    legende.append(
        f'<li>{sw}<b>{compte[niveau]}</b> {fr} <span class="en">· {en}</span>'
        f' <span class="ar">·&nbsp;<span lang="ar" dir="rtl">{ar}</span></span></li>'
    )
legende.append(
    '<li><i class="link-sw"></i>Liaison : un État applique la préférence ZLECAf aux produits de l’autre'
    ' <span class="en">· Link: one State applies the AfCFTA preference to the other’s goods</span>'
    ' <span class="ar">·&nbsp;<span lang="ar" dir="rtl">الرابط: دولة تطبق تفضيل زليكاف على سلع الدولة الأخرى</span></span></li>'
)

mois = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]
an, mo, jo = (int(v) for v in net["date"].split("-"))
date_fr = f"{'1ᵉʳ' if jo == 1 else jo} {mois[mo - 1]} {an}"
mois_ar = [
    "يناير",
    "فبراير",
    "مارس",
    "أبريل",
    "مايو",
    "يونيو",
    "يوليو",
    "أغسطس",
    "سبتمبر",
    "أكتوبر",
    "نوفمبر",
    "ديسمبر",
]
date_ar = f"{jo} {mois_ar[mo - 1]} {an}"
mois_en = (
    "January February March April May June July August September October November December".split()
)
date_en = f"{mois_en[mo - 1]} {jo}, {an}"

bloc = f"""<!-- RESEAU:START -->
<section class="network" aria-labelledby="reseau-titre">
  <h2 id="reseau-titre">Le réseau ZLECAf en un coup d’œil
    <span class="en" lang="en"><span class="sr-only"> · </span>The AfCFTA network at a glance</span>
    <span class="ar" lang="ar" dir="rtl"><span class="sr-only"> · </span>شبكة زليكاف في لمحة</span></h2>
  <p class="network-sub">
    Chaque rond est une capitale : sa surface suit le PIB {annee}, sa couleur le stade de mise en œuvre
    de l’accord. Les traits relient deux États quand l’un applique la préférence ZLECAf aux produits de
    l’autre. Survolez une capitale pour son détail.
    <span class="en">Each circle is a capital, sized by {annee} GDP and coloured by implementation status;
    lines link States that apply the AfCFTA preference to each other’s goods.</span>
    <span class="ar" lang="ar" dir="rtl">تمثل كل دائرة عاصمةً: تتناسب مساحتها مع الناتج المحلي الإجمالي لعام {annee}،
    ويدل لونها على مرحلة تنفيذ الاتفاقية. تربط الخطوط بين دولتين عندما تطبق إحداهما تفضيل زليكاف على سلع الأخرى.</span>
  </p>
  <div class="map">
{svg}
  </div>
  <ul class="legend">
    {chr(10).join("    " + li for li in legende).strip()}
  </ul>
  <p class="network-note">
    Statuts au {date_fr}, établis à partir des sources officielles citées dans la plateforme
    ({len(paires)} liaisons entre {len(noeuds)} États). PIB : {html.escape(net["pib_source"])}.
    <span class="en" lang="en">Statuses as of {date_en}, from the official sources cited in the platform
    ({len(paires)} links between {len(noeuds)} States). GDP: World Bank (WDI API), current US dollars.</span>
    <span class="ar" lang="ar" dir="rtl">الحالات بتاريخ {date_ar}، استنادًا إلى المصادر الرسمية المذكورة في المنصة
    ({len(paires)} رابطًا بين {len(noeuds)} دولة). الناتج المحلي الإجمالي: البنك الدولي (واجهة WDI)، بالدولار الأمريكي الجاري.</span>
  </p>
</section>
<!-- RESEAU:END -->"""

page = open(index_path, encoding="utf-8").read()
debut, fin = page.index("<!-- RESEAU:START -->"), page.index("<!-- RESEAU:END -->") + len(
    "<!-- RESEAU:END -->"
)
open(index_path, "w", encoding="utf-8").write(page[:debut] + bloc + page[fin:])
print(
    f"OK : {len(noeuds)} capitales, {len(paires)} liaisons, {len(svg) // 1024} Ko de SVG, statuts au {date_fr}"
)
