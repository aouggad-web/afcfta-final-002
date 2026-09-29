"""Tableaux de cibles vérifiées (tarif servi × marché réel × formalités), lus dans cibles.json.

Aucune cible n'est saisie à la main : tout provient de cibles.py (calculateurs du SaaS sur chaque ligne
nationale, flux OEC/BACI 2023-2024, F.A.P et formalités recensées par le SaaS).
"""
from layout import *
import json
import re

CB = json.load(open(S + 'cibles.json'))

PAYS = {'DZA': 'Algérie', 'EGY': 'Égypte', 'KEN': 'Kenya', 'MAR': 'Maroc', 'ZAF': 'Afrique du Sud', 'TUN': 'Tunisie', 'GHA': 'Ghana',
        'CMR': 'Cameroun', 'CIV': "Côte d'Ivoire", 'NGA': 'Nigeria', 'SEN': 'Sénégal', 'TZA': 'Tanzanie', 'RWA': 'Rwanda', 'MUS': 'Maurice',
        'UGA': 'Ouganda', 'ETH': 'Éthiopie', 'MWI': 'Malawi', 'ZMB': 'Zambie', 'MRT': 'Mauritanie'}
DEST = {'ZAF': 'SACU'}  # la préférence est servie par la SACU (union douanière)

# Libellés SH6 génériques (les libellés des tarifs nationaux décrivent des sous-positions, pas la SH6)
LIB = {
    '020130': 'Viande bovine désossée, fraîche', '020714': 'Morceaux de poulet congelés', '030389': 'Autres poissons congelés',
    '040221': 'Lait en poudre (> 1,5 % MG)', '040690': 'Fromages (autres)', '060311': 'Roses coupées', '070110': 'Pommes de terre de semence',
    '070190': 'Pommes de terre (consommation)', '070310': 'Oignons et échalotes', '071320': 'Pois chiches secs', '071331': 'Haricots mungo secs',
    '071340': 'Lentilles sèches', '080132': 'Noix de cajou décortiquées', '080390': 'Bananes (hors plantains)', '080410': 'Dattes',
    '080440': 'Avocats', '080510': 'Oranges', '090111': 'Café vert non décaféiné', '090210': 'Thé vert', '090240': 'Thé noir (vrac)',
    '090422': 'Piments broyés', '090961': 'Graines d\'anis, fenouil, carvi', '100199': 'Blé tendre', '100510': 'Maïs de semence',
    '100590': 'Maïs (grain)', '100630': 'Riz blanchi', '110100': 'Farine de blé', '120190': 'Fèves de soja', '120242': 'Arachides décortiquées',
    '120600': 'Graines de tournesol', '120991': 'Semences potagères', '150710': 'Huile de soja brute', '151190': 'Huile de palme raffinée et fractions',
    '151219': 'Huile de tournesol raffinée', '151790': 'Préparations de graisses végétales', '160414': 'Conserves de thon', '170114': 'Sucre de canne brut',
    '170199': 'Sucre raffiné', '170230': 'Glucose et sirop de glucose', '180310': 'Pâte de cacao', '180500': 'Poudre de cacao', '180632': 'Chocolat en tablettes non fourré',
    '180690': 'Préparations au chocolat', '190219': 'Pâtes alimentaires sèches', '190531': 'Biscuits sucrés', '200290': 'Concentré de tomate',
    '200911': 'Jus d\'orange congelé', '210111': 'Extraits et concentrés de café', '210210': 'Levures vivantes', '210410': 'Bouillons et potages',
    '210690': 'Préparations alimentaires n.d.a.', '220210': 'Boissons sucrées ou aromatisées', '220299': 'Autres boissons non alcooliques',
    '230400': 'Tourteaux de soja', '230990': 'Aliments composés pour animaux', '240120': 'Tabac écôté', '240220': 'Cigarettes', '310230': 'Nitrate d\'ammonium',
    '310520': 'Engrais NPK', '310590': 'Autres engrais composés', '380891': 'Insecticides', '380892': 'Fongicides', '380893': 'Herbicides',
    '030617': 'Crevettes congelées', '220300': 'Bière', '220421': 'Vins en bouteilles', '030374': 'Maquereaux congelés', '160413': 'Conserves de sardines',
}
L6 = json.load(open(os.environ['RG_REPO'] + '/backend/data/hs6_designations_fr_en.json'))['libelles']


def lib(hs):
    if hs in LIB:
        return LIB[hs]
    x = (L6.get(hs) or {}).get('fr') or hs
    return x[:48] + ('…' if len(x) > 48 else '')


def fr(txt):
    """Décimales à la française dans les motifs calculés (« 1.4 M$ » → « 1,4 M$ »)."""
    return re.sub(r'(\d)\.(\d)', r'\1,\2', txt)


def fmt_m(v):
    return f'{v / 1e6:,.1f}'.replace(',', ' ').replace('.', ',') if v >= 1e5 else '< 0,1'


def fmt_t(x):
    return '—' if x is None else (f'{x:.1f}'.replace('.', ',').replace(',0', ''))


def sh(hs):
    return f'{hs[:4]}.{hs[4:]}'


def filtre(liste, chap=None, verdicts=('RETENUE',), dest=None, orig=None, n=25, uniq=True):
    out, vus = [], set()
    for x in liste:
        if x['verdict'] not in verdicts:
            continue
        if chap and not (chap[0] <= x['hs'][:2] <= chap[1]):
            continue
        if dest and x['d'] not in dest:
            continue
        if orig and x['o'] not in orig:
            continue
        cle = (x['d'], x['hs'])
        if uniq and cle in vus:  # un seul couple par marché × produit (le meilleur fournisseur), les autres en note
            continue
        vus.add(cle)
        out.append(x)
        if len(out) >= n:
            break
    return out


def autres_origines(liste, x, k=3):
    o = [PAYS.get(y['o'], y['o']) for y in liste if y['d'] == x['d'] and y['hs'] == x['hs'] and y['o'] != x['o'] and y['verdict'] == x['verdict']]
    return o[:k]


COURT = {'NFSA': 'licence de l\'autorité sanitaire NFSA (et quarantaine vétérinaire pour surgelés et laitiers)',
         'usines enregistr': 'usines enregistrées exigées (titulaires de la marque)',
         'Autorisation technique prealable': 'autorisation technique préalable d\'importation (phytosanitaire)'}


def vigilance(x):
    v = []
    for m in x['motifs']:
        if m.startswith('réexportation'):
            v.append(f"origine à prouver (l'origine importe {x['imp_orig'] / 1e6:.0f} M$ pour {x['exp_orig'] / 1e6:.0f} M$ exportés)")
        elif m.startswith('préférence partielle'):
            v.append(f"préférence partielle ({x['lignes']} lignes)")
        elif not m.startswith('destination exportatrice'):
            v.append(m)
    for g in x.get('mnt_graves', [])[:1]:
        g = next((c for k, c in COURT.items() if k in g), g[:70])
        v.append('formalité lourde : ' + g)
    return fr(' ; '.join(v))


def tableau_cibles(sel, liste, titre, source_note=None, avec_niche=False):
    rows = [['Origine → marché', 'Produit (SH)', 'NPF → ZLECAf 2026', 'Marché importé (M$/an)', 'Offre origine (M$/an)', 'Déjà échangé (M$)', 'Vigilance']]
    for x in sel:
        alt = autres_origines(liste, x)
        orig = PAYS.get(x['o'], x['o']) + (f" <font size=6 color='#5E6273'>(aussi : {', '.join(alt)})</font>" if alt else '')
        taux = f"{fmt_t(x['npf'])} % → <b>{fmt_t(x['pref'])} %</b>" + (f" <font size=6 color='#5E6273'>[{x['lignes']} lignes]</font>" if x['lignes'].split('/')[0] != x['lignes'].split('/')[1] else '')
        vig = vigilance(x)
        if avec_niche and x['verdict'] == 'CRÉNEAU':
            vig = f"<b>Créneau</b> : la destination exporte {fmt_m(x['exp_dest'])} M$" + (' ; ' + vig if vig else '')
        rows.append([Paragraph(f"{orig} → <b>{DEST.get(x['d'], PAYS.get(x['d'], x['d']))}</b>", TD), Paragraph(f"{lib(x['hs'])} ({sh(x['hs'])})", TD),
                     Paragraph(taux, TD), fmt_m(x['imp_dest']), fmt_m(x['exp_orig']), fmt_m(x['bilat']), Paragraph(vig or '—', st('vg', fontSize=6.6, leading=8.2, textColor=INK2))])
    fl = [Paragraph(titre, CAP),
          table(rows, [34 * mm, 36 * mm, 26 * mm, 17 * mm, 17 * mm, 15 * mm, CW - 145 * mm], align_right_from=3, font=7),
          Paragraph(source_note or ('Méthode : taux servis par les calculateurs du SaaS sur toutes les lignes nationales de la SH6 (au 27/09/2026) ; marché et offre : moyennes OEC/BACI 2023-2024 '
                                    '(importations mondiales de la destination, exportations mondiales de l\'origine) ; « déjà échangé » : flux bilatéral observé. Seuils : marché ≥ 5 M$ et offre ≥ 5 M$. '
                                    'Une seule origine par couple marché × produit (la mieux placée) ; les autres origines vérifiées sont citées entre parenthèses.'), SRC)]
    return fl


def score_txt(x):
    return f"{x['score'] / 1e6:,.1f} M$".replace(',', ' ').replace('.', ',')


def methode_verif():
    s = CB['seuils']
    return callout('Comment chaque cible de cette édition a été vérifiée', [
        '<b>1. Le taux servi, ligne par ligne.</b> Chaque SH6 est évaluée sur toutes ses lignes nationales (8 à 10 chiffres) par les calculateurs du SaaS. '
        'Une préférence qui ne couvre qu\'une partie des lignes est signalée (exemple : pâtes au Maroc, seules les 2 lignes déjà à 2,5 % sont libéralisées, les 2 lignes à 40 % restent au NPF).',
        f'<b>2. Un marché réel.</b> La destination doit importer au moins {s["marche"] / 1e6:.0f} M$ par an du produit (moyenne OEC/BACI {s["annees"][0]}-{s["annees"][-1]}). '
        'Exemple : oranges égyptiennes au Maroc — 40 points de marge, mais 1,4 M$ importés par an (et 51 M$ exportés) : cible rejetée. '
        'Si la destination exporte davantage qu\'elle n\'importe, la cible est classée « créneau » et non « débouché » (exemple : dattes algériennes en Égypte, 17 M$ importés contre 101 M$ exportés).',
        f'<b>3. Une offre réelle.</b> L\'origine doit exporter au moins {s["offre"] / 1e6:.0f} M$ par an du produit ; une origine qui importe plus de la moitié de ce qu\'elle exporte est signalée (réexportation possible, origine à prouver).',
        '<b>4. Les barrières non tarifaires.</b> Les formalités recensées par le SaaS (F.A.P algériennes, formalités douanières égyptiennes) sont affichées ; les plus lourdes (licences, autorisations techniques, monopoles) sont signalées.',
        '<b>5. Le motif « pourquoi maintenant » est calculé</b> (taux 2026 du calendrier), jamais saisi à la main.'],
        bg=GREEN_L, bar=GREEN, title_color=GREEN)


def errata(n=None, filtre_chap=None):
    """Audit des cibles publiées dans l'édition T3 2026 (rapport unique) : verdict et motif."""
    rows = [['Cible publiée (édition précédente)', 'Taux servi 2026', 'Verdict', 'Motif']]
    col = {'RETENUE': '#1E8C5A', 'CRÉNEAU': '#C8952B', 'REJETÉE': '#C0493D'}
    lst = [x for x in CB['audit'] if not filtre_chap or filtre_chap[0] <= x['hs'][:2] <= filtre_chap[1]]
    for x in lst[:n]:
        mot = fr('; '.join(x['motifs'])) or 'confirmée'
        rows.append([Paragraph(f"{PAYS.get(x['o'], x['o'])} → {DEST.get(x['d'], PAYS.get(x['d'], x['d']))} : {lib(x['hs'])} ({sh(x['hs'])})", TD),
                     Paragraph(f"{fmt_t(x['npf'])} → {fmt_t(x['pref'])} % [{x['lignes']}]", TD),
                     Paragraph(f"<b><font color='{col[x['verdict']]}'>{x['verdict'].capitalize()}</font></b>", TD), Paragraph(mot, st('er', fontSize=6.6, leading=8.2))])
    ok = sum(1 for x in lst if x['verdict'] == 'RETENUE')
    return [Paragraph(f'Audit des cibles de l\'édition précédente : {ok} confirmées sur {len(lst)}', CAP),
            table(rows, [62 * mm, 28 * mm, 18 * mm, CW - 108 * mm], font=7),
            Paragraph('Source : cibles.py (mêmes données et seuils que ci-dessus). Les cibles rejetées ne sont plus recommandées ; les « créneaux » restent possibles pour des volumes limités.', SRC)]


def stats_audit():
    a = CB['audit']
    return {v: sum(1 for x in a if x['verdict'] == v) for v in ('RETENUE', 'CRÉNEAU', 'REJETÉE')}, len(a)
