from layout import *
import json
from ch_verif import CB, filtre, tableau_cibles, lib, sh, fmt_m, fmt_t, fr, PAYS
C = S + 'charts/'

# Règle d'origine (Appendice IV) des produits algériens souvent cités
ORIGINE = {'080410': ('ok', 'entièrement obtenues'), '110311': ('ok', 'changement de position (blé importé admis)'), '110100': ('ok', 'changement de position'),
           '190219': ('ok', 'si la semoule est originaire'), '190531': ('ok', 'si la farine est originaire'), '070190': ('ok', 'entièrement obtenues'),
           '200290': ('si', 'si tomates algériennes'), '121292': ('ok', 'entièrement obtenue'), '220110': ('ok', 'entièrement obtenues'),
           '220210': ('non', 'non, sauf sucre africain'), '170199': ('non', 'non : raffiné à partir de brut importé'), '180690': ('non', 'non : cacao et sucre non africains')}
COUL = {'ok': '#1E8C5A', 'si': '#C8952B', 'non': '#C0493D'}


def tableau_focus_export():
    ex = CB['focus']['exportations']
    hs_l = list(dict.fromkeys(x['hs'] for x in ex if x['exp_orig'] >= 3e6 or x['hs'] in ORIGINE))
    dests = ['EGY', 'MAR', 'ZAF']
    rows = [['Produit algérien (SH)', 'Export. DZA (M$/an)', 'Égypte', 'Maroc*', 'SACU', 'Verdict', 'Origine']]
    col = {'RETENUE': '#1E8C5A', 'CRÉNEAU': '#C8952B', 'REJETÉE': '#C0493D'}
    for hs in hs_l:
        c = {x['d']: x for x in ex if x['hs'] == hs}
        cell = []
        for d in dests:
            x = c.get(d)
            if not x or x['npf'] is None:
                cell.append('n.d.'); continue
            t = f"{fmt_t(x['npf'])} → {fmt_t(x['pref'])} %" if x['pref'] < x['npf'] else f"{fmt_t(x['npf'])} % (aucune)"
            n, tot = x['lignes'].split('/')
            t += f" [{n}/{tot}]" if n != tot and n != '0' else ''
            cell.append(Paragraph(f"<font color='{col[x['verdict']]}'>{t}</font><br/><font size=5.8 color='#5E6273'>marché {fmt_m(x['imp_dest'])} M$</font>", TD))
        best = next((v for v in ('RETENUE', 'CRÉNEAU') if any(c[d]['verdict'] == v for d in dests if d in c)), 'REJETÉE')
        qui = ', '.join(('SACU' if d == 'ZAF' else PAYS[d]) for d in dests if d in c and c[d]['verdict'] == best) if best != 'REJETÉE' else ''
        motif = ''
        if best == 'REJETÉE':
            ms = [m for d in dests if d in c for m in c[d]['motifs']]
            motif = 'offre algérienne insuffisante' if any(m.startswith('offre') for m in ms) else ('marchés trop petits' if all('trop petit' in m or 'aucune' in m for m in ms) else fr(ms[0]))
            if all(m.startswith('aucune') for d in dests if d in c for m in c[d]['motifs'][:1]):
                motif = 'aucune marge servie'
        v = f"<b><font color='{col[best]}'>{best.capitalize()}</font></b>" + (f' : {qui}' if qui else f' — {motif}')
        o = ORIGINE.get(hs)
        rows.append([Paragraph(f"{lib(hs)} ({sh(hs)})", TD), fmt_m(c[dests[0]]['exp_orig']), *cell, Paragraph(v, TD),
                     Paragraph(f"<font color='{COUL[o[0]]}'>{o[1]}</font>" if o else '—', st('og', fontSize=6.4, leading=8))])
    return [Paragraph('Tableau 9.3 — Produits algériens : taux servis ligne par ligne en 2026, marché de destination et verdict', CAP),
            table(rows, [36 * mm, 15 * mm, 23 * mm, 23 * mm, 23 * mm, 27 * mm, CW - 147 * mm], font=7),
            Paragraph('Source : calculateurs du SaaS (toutes les lignes nationales ; [k/n] = lignes réduites sur lignes de la SH6), OEC/BACI moyenne 2023-2024, Appendice IV (règles d\'origine). '
                      'Mêmes seuils que les autres tableaux de cibles : marché ≥ 5 M$, offre ≥ 5 M$ ; « créneau » = destination exportatrice nette. '
                      '*Maroc : relations diplomatiques rompues depuis août 2021 et frontière terrestre fermée depuis 1994 : risque politique majeur.', SRC)]
TAX = {t['lab']: t for t in json.load(open(S + 'dza_tax.json'))}

def fmt(x, d=0):
    s = f'{x:,.{d}f}'.replace(',', ' ').replace('.', ',')
    return s.replace('-', '−')

def cif_cost(fob, t_evp, freight_evp, days, ins=0.003, fin=0.10):
    fr = freight_evp / t_evp
    cif = (fob + fr) * (1 + ins)
    return fr, cif, fob * fin * days / 365

# ---------------- Cas DZ-1 : urée vers Durban ----------------
def urea_case(prem=7.0, fob=450, mult=1.3415, hull=28e6, t=55000):
    f_dza = (7 + 0.004 * 6365) * 0.82 * mult
    f_gulf = (7 + 0.004 * 4200) * 0.82 * mult
    war = hull * prem / 100 / t
    ins = 0.002
    dza = fob + f_dza + (fob + f_dza) * ins + fob * 0.10 * 19 / 365
    gulf = fob + f_gulf + war + (fob + f_gulf) * ins + fob * 0.10 * 12.5 / 365
    return dict(f_dza=f_dza, f_gulf=f_gulf, war=war, dza=dza, gulf=gulf)

# ---------------- Cas DZ-3 : pâtes vers Niamey ----------------
def pasta_case(fob=800, t_evp=22, road_dza=9083, sea_dza=1120, turk_sea=1600, corridor=2395, fuel=265):
    duty = 0.20 + 0.025 + 0.005
    opts = {'Algérie — Transsaharienne (coût modélisé SaaS)': (road_dza, 10),
            'Algérie — mer jusqu\'à Cotonou + corridor Cotonou-Niamey': (sea_dza + fuel + corridor, 20),
            'Turquie — mer jusqu\'à Cotonou + corridor': (turk_sea + fuel + corridor, 22)}
    out = {}
    for k, (evp, days) in opts.items():
        fr = evp / t_evp; cif = (fob + fr) * 1.003
        out[k] = dict(fr=fr, cif=cif, taxes=cif * duty, fin=fob * 0.10 * days / 365, total=cif * (1 + duty) + fob * 0.10 * days / 365, days=days)
    return out

def ch_algeria():
    fl = [chapter(9, 'Focus Algérie : importer, exporter, investir'),
          P("L'Algérie applique la ZLECAf depuis la circulaire DGD 482/2024 et fait partie des marchés agricoles les plus protégés du continent (droit moyen de 26,6 %, "
            "auxquels s'ajoutent le DAPS, la TCS et la PRCT). Pour ses partenaires activés, c'est désormais l'un des marchés les plus ouverts. Ce chapitre, calculé ligne par ligne "
            "avec les modules algériens du SaaS, s'adresse aux importateurs, exportateurs et industriels algériens.", LEAD)]
    fl.append(kpis([
        ('5,7 %', 'droit agricole moyen servi aux partenaires « standard » en 2026 (26,6 % NPF)', 'Calculateur DZA du SaaS'),
        ('9', 'partenaires activés : 5 au calendrier standard, 4 en réciprocité', 'Circulaire DGD 482/2024'),
        ('30-200 %', 'DAPS exonéré pour les listes A et B importées sous ZLECAf', 'Circ. 482/2024 ; LFC 2018 art. 2'),
        ('16,5 mois', 'couverture des importations par les réserves (2024)', 'SaaS — Banque mondiale WDI')], cols=4))
    fl.append(Spacer(1, 4))
    fl.append(h2('9.1 Le régime ZLECAf algérien en pratique'))
    rows = [['Année', '2021', '2022', '2023', '2024', '2025', '2026', '2027', '2028', '2029', '2030', '2031-32', '2033'],
            ['Liste A — standard', '80 %', '60 %', '40 %', '20 %', '0', '0', '0', '0', '0', '0', '0', '0'],
            ['Liste A — réciprocité', '90 %', '80 %', '70 %', '60 %', '50 %', '40 %', '30 %', '20 %', '10 %', '0', '0', '0'],
            ['Liste B — standard', '100 %', '100 %', '100 %', '100 %', '100 %', '80 %', '60 %', '40 %', '20 %', '0', '0', '0'],
            ['Liste B — réciprocité', '100 %', '100 %', '100 %', '100 %', '100 %', '87,5 %', '75 %', '62,5 %', '50 %', '37,5 %', '25-12,5 %', '0'],
            ['Liste C', '100 %', '100 %', '100 %', '100 %', '100 %', '100 %', '100 %', '100 %', '100 %', '100 %', '100 %', '100 %']]
    fl.append(Paragraph('Tableau 9.1 — Part du droit de base encore appliquée, selon la liste et le calendrier (circulaire DGD 482/2024)', CAP))
    fl.append(table(rows, [34 * mm] + [(CW - 34 * mm) / 12] * 12, align_right_from=1))
    fl.append(Paragraph('Standard : Égypte, Maurice, Rwanda, Tanzanie, Tunisie. Réciprocité (pays en développement membres de CER au calendrier PMA) : Afrique du Sud, Cameroun, Ghana, Kenya. '
                        'Liste B : droit de base 2019 lorsqu\'il est fixé par la circulaire. Positions textiles et automobiles « gelées » faute de règles d\'origine (sans objet pour l\'agroalimentaire). '
                        'Source : SaaS ZLECAf — circular_482_schedule.json, zlecaf_schedule_dza.py.', SRC))
    fl.append(figure(C + 'a1_lists.png', 'Figure 9.1 — Lignes agricoles algériennes (positions à 10 chiffres) par liste de démantèlement et par filière',
                     'Source : SaaS ZLECAf — barème DZA (DGD) et listes B/C de la circulaire 482/2024 ; total SH 01-24 : 2 150 lignes en A, 445 en B, 225 en C.', maxh=74 * mm))
    fl.append(PageBreak())
    fl.append(P("<b>Le levier caché : le DAPS.</b> Le droit additionnel provisoire de sauvegarde frappe 165 positions agricoles : viandes (30 %), beurre (120 %), légumes frais (70 %), "
                "fruits frais (50 %), conserves (60 %), sucres (100 %), pâtes et produits de boulangerie (50 %), boissons (30 à 200 %), tabacs (100 %). La circulaire 482/2024 exonère "
                "de DAPS les produits des listes A et B importés sous régime ZLECAf depuis un partenaire actif. Pour ces lignes, la marge réelle d'un importateur algérien dépasse "
                "largement le seul droit de douane : sucre raffiné 135 % → 29 %, pâtes 85 % → 29 %, viande bovine 65 % → 29 % (hors TVA)."))
    fl.append(h2('9.2 L\'Algérie importatrice : sourcer en Afrique'))
    fl.append(figure(C + 'a2_tax.png', 'Figure 9.2 — Charge fiscale totale à l\'importation en Algérie (hors TVA), NPF contre ZLECAf 2026',
                     'Source : SaaS ZLECAf — calculateur DZA (DD, DAPS et exonération, PRCT 2 %, TCS 3 %, TIC) ; TVA à 9 % ou 19 %, récupérable, exclue. '
                     'Hors mesures temporaires des lois de finances (LF 2026 : DD de 5 % sur viandes et volailles, café vert exonéré de TVA et de TIC jusqu\'au 31/12/2026). '
                     'Les régimes particuliers (industries de transformation) peuvent modifier le DAPS du sucre brut.', maxh=100 * mm))
    fl += tableau_cibles(filtre(CB['classement'], dest=['DZA'], n=12), CB['classement'],
                         'Tableau 9.2 — Sourcings africains vérifiés pour l\'Algérie : droit de douane NPF → ZLECAf 2026, marché et offre réels')
    fl.append(Paragraph('Le DAPS éventuel est en outre exonéré sous ZLECAf (listes A et B). La Côte d\'Ivoire, l\'Éthiopie et l\'Ouganda ne sont pas activés en Algérie : leurs produits (café, cacao, bananes) restent au NPF. '
                        'Écarts exposés, non tranchés : les cibles publiées dans l\'édition précédente sur le thé noir en vrac (0902.40) et les morceaux de poulet congelés (0207.14) '
                        f"visaient des sous-positions que l\'Algérie importe peu, alors que la position entière pèse davantage (thé : {fmt_m(CB['reperes']['DZA_imp_0902'])} M$, surtout du thé vert, que les fournisseurs africains activés n\'exportent presque pas). "
                        'Les deux lectures sont données en annexe 4 (codes N). L\'huile de tournesol raffinée (1512.19) reste sous le seuil même pour la position entière (4,6 M$).', SRC))
    fl.append(PageBreak())
    fl.append(h2('9.3 Une industrie agroalimentaire en essor et ses champions'))
    fl.append(kpis([
        ('5,08 Md$', 'valeur ajoutée des industries alimentaires et du tabac en 2024 (+5,2 % en volume)', 'ONS, comptes 2024 (provisoires)'),
        ('19,6 Md$', 'production brute de la branche en 2024 ; 20,6 Md$ estimés en 2025', 'ONS ; estimation SaaS (confiance C)'),
        ('43 %', 'part de la branche dans la valeur ajoutée manufacturière hors raffinage (2024)', 'Calcul SaaS sur données ONS'),
        ('60 %', 'part du secteur privé dans la valeur ajoutée de la branche (2024)', 'ONS')], cols=4))
    fl.append(Spacer(1, 4))
    fl.append(P("L'agroalimentaire est la première industrie manufacturière algérienne hors hydrocarbures. Son essor repose sur des groupes privés intégrés (Cevital, Soummam, Bimo, Cebon) "
                "et sur la montée en puissance du holding public Madar, qui a repris la raffinerie de sucre de Larbaâtache (Tafadis) et le complexe de trituration de Jijel (Kotama Agri Food). "
                "Ces capacités, dimensionnées pour substituer les importations, dépassent désormais la demande intérieure sur plusieurs produits et cherchent des débouchés africains."))
    rows = [['Groupe', 'Filière', 'Capacité ou position', 'Projection africaine'],
            ['Cevital (Béjaïa)', 'Sucre, huiles, trituration', 'Raffinerie de 2 Mt/an ; trituration de 22 000 t/j de graines (dont 11 000 t de soja)', '40 000 t de sucre blanc vers la Tunisie (2025)'],
            ['Madar Holding — Tafadis (Larbaâtache)', 'Sucre raffiné', '2 000 t/j (sucre blanc, liquide, roux) ; reprise en 2023', 'Contrat de 180 M$ de sucre vers la Libye (2025)'],
            ['Madar Holding — Kotama Agri Food (Jijel)', 'Trituration de soja', '1,65 Mt/an de graines : 1,32 Mt de tourteaux, 300 000 t d\'huile brute', 'Aliments du bétail et huiles pour le Sahel'],
            ['Laiterie Soummam (Akbou)', 'Produits laitiers', '2 000 t/j ; ≈ 65 % du marché des produits laitiers (2023)', '—'],
            ['Giplait (public, 16 unités)', 'Lait', '2,6 Md de litres/an', '—'],
            ['Bimo (Baba Ali) ; Sai — Kaada (El Bordj)', 'Biscuits, gaufrettes', '≈ 35 % et ≈ 25 % du marché national', 'Bimo vise explicitement le marché africain'],
            ['Cebon — El Mordjene (Tipaza)', 'Pâte à tartiner', '8 → 80 t/j (2024-2025) ; 10 % vers le Golfe', 'Voir encadré'],
            ['Kawa-Food — Optila', 'Confiserie', '> 1 000 salariés', 'Exporte déjà vers la Libye et la Tunisie'],
            ['Boublenza (Tlemcen)', 'Caroube', '47,6 M$/an d\'exportations vers 25 pays (2020-2022)', 'Caroube : 20 → 8 % en SACU, 2 → 0 % en Égypte'],
            ['411 minoteries + 145 semouleries', 'Farine, semoule, pâtes', '556 unités (2022)', 'Niger : 94 % des exportations de pâtes et semoule']]
    fl.append(Paragraph('Tableau 9.4 — Les champions de l\'agroalimentaire algérien', CAP))
    fl.append(table(rows, [42 * mm, 26 * mm, 58 * mm, CW - 126 * mm]))
    fl.append(Paragraph('Source : SaaS ZLECAf — module Opportunités, sous-module « Algérie · industrie et marchés » (dza_filieres.json : relevés de collecte du 23/09/2026, fiabilité B = presse reprenant un chiffre officiel ou d\'entreprise ; dza_industrie.json : comptes de l\'ONS).', SRC))
    fl.append(callout('Encadré — El Mordjene : de la notoriété virale à la conquête africaine', [
        '<b>Une marque devenue phénomène</b> : la pâte à tartiner de Cebon est passée de 8 à 80 t par jour après un engouement viral sur les réseaux sociaux (2024-2025). L\'Union européenne en a bloqué l\'importation fin 2024, faute d\'agrément sanitaire pour le lait algérien ; la marque s\'est tournée vers le Moyen-Orient.',
        '<b>Les marchés africains où l\'Algérie est absente</b> (préparations au chocolat, 2024) : Libye 87 M$, Maroc 53 M$, Afrique du Sud 52 M$, Maurice 17 M$, Égypte 14 M$, Nigeria 11 M$.',
        '<b>Rendre le produit originaire</b> : la règle du chapitre 18 n\'impose l\'origine qu\'au cacao et au sucre — pas aux noisettes ni au lait. En sourçant la pâte de cacao au Ghana ou au Cameroun (15 → 6 % en Algérie) et le sucre en Afrique (brut mauricien ou tanzanien à 0 %, DAPS exonéré, puis raffiné en Algérie — originaire par cumul, sous réserve de la documentation d\'origine), '
        'El Mordjene accède à la SACU à 6,8 % au lieu de 17 % (taux vérifié ligne par ligne).',
        '<b>Vigilance</b> : cible prospective — l\'Algérie n\'exportait que 0,4 M$ de préparations au chocolat par an en 2023-2024 (OEC) ; l\'Égypte classe cette ligne en liste B (10 % maintenus) ; la Libye n\'a pas ratifié l\'Accord ; le Maroc reste fermé politiquement. La notoriété d\'une marque se protège : dépôt de marque dans les pays cibles (OAPI pour l\'Afrique francophone, ARIPO pour l\'anglophone).'],
        bg=GOLD_L, bar=GOLD))
    fl.append(PageBreak())
    # ---- 9.3 export
    fl.append(h2('9.4 L\'Algérie exportatrice : où et quoi vendre'))
    fl.append(P("L'Algérie est admise comme origine en <b>Égypte</b>, au <b>Maroc</b> et dans la <b>SACU</b> ; elle n'est pas sur la liste d'origines du Kenya. "
                "Le tableau ci-dessous confronte ses principales exportations agricoles (et les produits souvent cités) au taux réellement servi, ligne par ligne, et au marché de chaque destination. "
                "Le résultat corrige l'édition précédente : l'Égypte, premier débouché préférentiel, est exportatrice nette de dattes, de sucre et de farine ; "
                "le Maroc maintient 40 % sur les dattes ; pâtes et biscuits n'y sont libéralisés que sur une partie des lignes, et l'offre algérienne (3 M$ par an) reste marginale."))
    fl += tableau_focus_export()
    fl.append(figure(C + 'a3_demand.png', 'Figure 9.3 — Demande d\'importation africaine 2024 et part captée par l\'Algérie',
                     'Source : SaaS ZLECAf — CEPII BACI via OEC (dza_commerce_baci.json), importations africaines hors Algérie ; flux avec la Libye sous-estimés.', maxh=56 * mm))
    ABS = json.load(open(S + 'dza_absent.json'))
    NM = {'LBY': 'Libye', 'MAR': 'Maroc', 'ZAF': 'Afr. du Sud', 'MUS': 'Maurice', 'EGY': 'Égypte', 'NGA': 'Nigeria', 'COD': 'RD Congo', 'MRT': 'Mauritanie', 'SDN': 'Soudan', 'SOM': 'Somalie', 'CMR': 'Cameroun', 'GHA': 'Ghana', 'SEN': 'Sénégal',
          'CIV': 'Côte d\'Ivoire', 'TZA': 'Tanzanie', 'MLI': 'Mali', 'DJI': 'Djibouti', 'KEN': 'Kenya', 'NAM': 'Namibie', 'ZMB': 'Zambie', 'MWI': 'Malawi', 'TGO': 'Togo', 'MOZ': 'Mozambique', 'BFA': 'Burkina Faso', 'BWA': 'Botswana'}
    LB = {'310210': 'Urée', '170199': 'Sucre raffiné', '190531': 'Biscuits', '220210': 'Boissons sucrées', '190219': 'Pâtes', '151219': 'Huile de tournesol', '110311': 'Semoule', '080410': 'Dattes', '180690': 'Préparations au chocolat'}
    rows = [['Produit algérien', 'Marchés africains où l\'Algérie pèse moins de 1 % (importations 2024, M$ ; évolution 2019-2024)']]
    for hs, lab in LB.items():
        rows.append([lab, Paragraph(' · '.join(f"{NM.get(x['iso3'], x['iso3'])} {x['importations_2024_usd'] / 1e6:,.0f} ({x['evolution_2019_2024_pct']:+.0f} %)".replace(',', ' ').replace('-', '−') for x in ABS[hs][:5]), TD)])
    fl.append(Paragraph('Tableau 9.5 — Où l\'Algérie est absente : marchés cibles africains par produit', CAP))
    fl.append(table(rows, [34 * mm, CW - 34 * mm]))
    fl.append(Paragraph('Source : SaaS ZLECAf — sous-module « Algérie · industrie et marchés » (fiche produit, filtre : importations > 1 M$ et part algérienne < 1 %), CEPII BACI 2024.', SRC))
    fl.append(PageBreak())
    # ---- 9.4 cas chiffrés
    fl.append(h2('9.5 Deux cas chiffrés, hypothèses et sensibilités'))
    fl.append(Paragraph('Cas DZ-1 — Urée algérienne livrée à Durban face à l\'urée du Golfe (hors préférence : droits nuls pour tous)', H3))
    u = urea_case(7.0)
    rows = [['$/tonne (vraquier Supramax, 55 000 t)', 'Algérie (Arzew) via Gibraltar et le Cap', 'Golfe via Ormuz'],
            ['Prix FOB (hypothèse identique, niveau de juin 2026)', '450', '450'],
            ['Distance (nm) / durée à 14 nœuds', '≈ 6 365 / 19 j', '≈ 4 200 / 12,5 j'],
            ['Fret (modèle vrac du SaaS × multiplicateur 1,3415)', fmt(u['f_dza'], 1), fmt(u['f_gulf'], 1)],
            ['Surprime de guerre (7 % d\'une coque de 28 M$)', '0', fmt(u['war'], 1)],
            ['Assurance cargaison (0,2 %) et portage (10 %/an)', fmt(u['dza'] - 450 - u['f_dza'], 1), fmt(u['gulf'] - 450 - u['f_gulf'] - u['war'], 1)],
            [Paragraph('<b>Coût rendu Durban</b>', TD), Paragraph(f"<b>{fmt(u['dza'], 1)}</b>", TD), Paragraph(f"<b>{fmt(u['gulf'], 1)}</b>", TD)],
            [Paragraph('<b>Avantage algérien</b>', TD), Paragraph(f"<b><font color='#1E8C5A'>{fmt(u['gulf'] - u['dza'], 1)} $/t ({(u['gulf'] / u['dza'] - 1) * 100:.1f} %)</font></b>".replace('.', ','), TD), '']]
    fl.append(table(rows, [80 * mm, 48 * mm, CW - 128 * mm], extra=[('BACKGROUND', (0, 6), (-1, 6), GREEN_L)]))
    fl.append(figure(C + 'a4_urea.png', 'Figure 9.4 — Sensibilité : avantage de l\'urée algérienne selon la surprime de guerre à Ormuz',
                     'Hypothèses (H) : coque Supramax 28 M$ ; distances par tronçons searoute (±5 %) ; fret : formule vrac du SaaS (7 + 0,004 × nm) × 0,82 × 1,3415 (multiplicateur au 13/08/2026). '
                     'Au-delà d\'une surprime de ≈ 1,9 %, l\'urée algérienne est moins chère rendue en Afrique australe — sans compter la sécurité d\'approvisionnement. '
                     'Débouchés 2024 : Afrique du Sud 325 M$, Zambie 182 M$, Malawi 104 M$, Togo 78 M$, Mozambique 75 M$, Tanzanie 63 M$ ; part algérienne : 0,5 %.', maxh=56 * mm))
    fl.append(PageBreak())
    fl.append(Paragraph('Cas DZ-3 — Pâtes livrées à Niamey : Transsaharienne, voie maritime par Cotonou ou concurrent turc (même droit pour tous)', H3))
    pc = pasta_case(); keys = list(pc)
    rows = [['$/tonne (22 t par EVP, FOB 800 $/t)'] + [Paragraph(f'<b>{k}</b>', TH) for k in keys]]
    for lab, k in [('Transport porte-à-porte', 'fr'), ('Valeur CAF', 'cif'), ('Droits et prélèvements Niger (TEC 20 % + 2,5 % + AES 0,5 %)', 'taxes'), ('Portage financier', 'fin'), ('Coût rendu Niamey', 'total')]:
        rows.append([Paragraph(f'<b>{lab}</b>' if k == 'total' else lab, TD)] + [Paragraph(f'<b>{fmt(pc[x][k])}</b>' if k == 'total' else fmt(pc[x][k]), TDR) for x in keys])
    rows.append(['Délai indicatif (jours)'] + [str(pc[x]['days']) for x in keys])
    fl.append(table(rows, [60 * mm] + [(CW - 60 * mm) / 3] * 3, zebra=False, extra=[('BACKGROUND', (0, 5), (-1, 5), GREEN_L)]))
    fl.append(Paragraph('Hypothèses (H) : coûts du SaaS (Transsaharienne Algérie→Niger 9 083 $/EVP ; Algérie→golfe de Guinée ≈ 1 120 $/EVP ; corridor Cotonou-Niamey 2 395 $/EVP) ; Mersin→Cotonou 1 600 $/EVP (H) ; '
                        'Niger : préférence ZLECAf non opposable, prélèvement AES de 0,5 % applicable aux deux origines.', SRC))
    fl.append(callout('Lecture pour les exportateurs algériens', [
        'Par le modèle du SaaS, la voie maritime par Cotonou bat la Transsaharienne de ≈ 240 $/t. Pourtant, l\'Algérie exporte déjà 8,1 M$ de pâtes et de semoule au Niger (94 % de ses exportations du produit, BACI 2024), essentiellement par la route : '
        'le modèle ne capte ni le coût du gazole algérien, ni les frets de retour, ni les délais (≈ 10 jours contre 20). Il faut calibrer ce corridor sur des devis réels de transporteurs.',
        'Face à la Turquie, l\'avantage algérien par Cotonou est de l\'ordre de 20 à 25 $/t : il tient à la distance maritime et reste fragile. La différenciation (semoule de blé dur, marques, délais) compte plus que le prix.',
        'Risques : insécurité sur les axes sahéliens (blocus du JNIM au Mali), prélèvement AES, tensions diplomatiques entre l\'Algérie et les pays de l\'AES depuis avril 2025 — à suivre avant tout engagement de volume.'],
        bg=BLUE_L, bar=BLUE, title_color=BLUE))
    fl.append(h2('9.6 Feuille de route pour les opérateurs algériens'))
    imp_dz = [x for x in filtre(CB['classement'], dest=['DZA'], n=40) if not any(m.startswith('réexportation') for m in x['motifs'])][:6]  # origines productrices
    fl += bullets([
        '<b>Importateurs</b> : sourcer en Afrique les produits où la préférence, le marché et l\'offre sont vérifiés — ' +
        ', '.join(f"{lib(x['hs']).lower()} ({PAYS[x['o']]})" for x in imp_dz) +
        ' — en exigeant le certificat d\'origine ZLECAf, seul moyen d\'obtenir à la fois la baisse du droit et l\'exonération du DAPS. '
        'Le thé mérite une lecture double : l\'Algérie n\'importe que 0,7 M$ de thé noir en vrac, la sous-position citée dans l\'édition précédente, mais ' + f"{fmt_m(CB['reperes']['DZA_imp_0902'])} M$ de thé au total, surtout du thé vert, que le Kenya, le Rwanda et la Tanzanie n\'exportent presque pas. " + 'Même écart pour le poulet congelé : 0,2 M$ en morceaux, 10 M$ en poulets entiers (sans marge servie, annexe 4). L\'huile de tournesol reste sous le seuil même pour la position entière (4,6 M$ par an).',
        '<b>Exportateurs</b> : la seule cible directe vérifiée est l\'Égypte pour les boissons sucrées (30 → 0 %, sous réserve d\'un sucre originaire). Dattes, sucre et farine vers l\'Égypte sont des créneaux '
        '(l\'Égypte est exportatrice nette) ; le Maroc maintient 40 % sur les dattes et ne libéralise qu\'une partie des lignes de pâtes et de biscuits. Les débouchés de volume restent hors préférence : '
        'Niger, Mauritanie, Libye, Tunisie, et l\'urée en Afrique australe et de l\'Est.',
        '<b>Industriels</b> : sécuriser des matières africaines pour rendre originaires les produits sucrés (sucre brut sud-africain ou mauricien) et chocolatés (pâte de cacao du Cameroun ou du Ghana) ; '
        'l\'urée et les engrais azotés constituent la meilleure carte algérienne de 2026 sur les marchés d\'Afrique australe et de l\'Est.',
        '<b>Logistique</b> : utiliser les lignes maritimes vers Abidjan, Lomé et Cotonou pour l\'Afrique de l\'Ouest, le poste frontalier ouvert en 2018 et la route Tindouf-Zouérate (en construction) vers la Mauritanie, et suivre le chantier de la ligne ferroviaire Alger-Tamanrasset (livraison annoncée vers 2030).'])
    return fl
