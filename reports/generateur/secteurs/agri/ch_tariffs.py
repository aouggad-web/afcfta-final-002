from layout import *
import json
D = json.load(open(S + 'saas_stats.json')); D2 = json.load(open(S + 'saas_stats2.json'))
ESC = json.load(open(S + 'escal.json')); B2 = json.load(open(S + 'burden2.json')); CATS = json.load(open(S + 'cats.json'))
CS = D['countries']; MG = D2['margins']
C = S + 'charts/'

def f1(x): return '—' if x is None else (f'{x:.1f}'.replace('.', ','))
def f0(x): return '—' if x is None else f'{x:.0f}'

def ch_tariffs():
    fl = []
    fl += [chapter(3, 'Le paysage tarifaire agricole'),
           P("Le tarif extérieur appliqué à l'agriculture africaine reste l'un des plus protecteurs du monde en développement. "
             "À partir des <b>35 240 lignes tarifaires agricoles (SH 01-24)</b> des 40 barèmes nationaux intégrés au SaaS, ce chapitre "
             "mesure le niveau, la structure et la progressivité de cette protection — c'est-à-dire le « coût d'entrée » que la ZLECAf "
             "doit démanteler.", LEAD)]
    fl.append(h2('3.1 Une protection agricole deux fois supérieure à celle de l\'industrie'))
    fl.append(P("Dans chaque union douanière et chaque régime national étudié, le droit moyen appliqué aux produits agricoles dépasse "
                "celui des produits non agricoles. L'écart est particulièrement marqué dans la CAE (24,7 % contre 10,6 %), au Maroc "
                "(25,6 % contre 9,3 %) et en Tunisie (31,9 % contre 16,6 %). À l'inverse, Maurice (1,1 %) et l'Union douanière d'Afrique "
                "australe — SACU (9,5 %) — ont fait le choix d'une ouverture agricole large, compensée par des instruments spécifiques "
                "(droits spécifiques sur le lait, la volaille ou le sucre)."))
    fl.append(figure(C + 'c1_ag_vs_nag.png', 'Figure 3.1 — Droit de douane moyen simple : agriculture vs reste de l\'économie',
                     'Source : SaaS ZLECAf, barèmes nationaux (droit de douane NPF appliqué, moyenne simple des lignes SH6). Égypte hors chapitre 22 '
                     '(boissons alcoolisées taxées jusqu\'à 3 000 %). Le chiffre entre parenthèses indique le nombre d\'États appliquant le tarif extérieur commun.', maxh=80 * mm))
    fl.append(P("<b>Lecture stratégique.</b> Quatre tarifs extérieurs communs (CEDEAO, CAE, CEMAC, SACU) couvrent 33 des 40 pays analysés : "
                "pour un exportateur, négocier l'accès à un seul de ces marchés revient à accéder à 5 à 15 États à la fois. La CEDEAO (cinq bandes : "
                "0-5-10-20-35 %) et la CAE (bandes 0-10-25-35 % depuis la révision de 2022) concentrent l'essentiel des pics sur les produits "
                "transformés finaux, là où la ZLECAf crée le plus de marge préférentielle.", BODY))
    fl.append(PageBreak())
    fl.append(h2('3.2 Cartographie : 11 régimes × 15 filières'))
    fl.append(P("La matrice ci-dessous synthétise le droit moyen par filière. Trois enseignements dominent : (i) les produits d'élevage "
                "(viandes, lait) et les conserves sont les plus protégés ; (ii) les matières premières industrielles (céréales, oléagineux) "
                "entrent à droits modérés, pour ne pas renchérir les intrants des industries locales ; (iii) le Maroc et la Tunisie "
                "appliquent les protections les plus élevées sur les viandes, laitiers et conserves, ce qui en fait des marchés à forte "
                "marge préférentielle mais à accès politique sensible."))
    fl.append(figure(C + 'c2_heatmap.png', 'Figure 3.2 — Droit NPF moyen par filière et par régime tarifaire (%)',
                     'Source : SaaS ZLECAf, barèmes nationaux. *Égypte, boissons : droits de 1 200 % à 3 000 % sur les vins et spiritueux (moyenne de la filière : 1 559 %). '
                     'n.d. : l\'Algérie n\'intègre pas les chapitres 22 et 24 dans la base consolidée.', maxh=140 * mm))
    fl.append(PageBreak())
    fl.append(h2('3.3 Le coût réel d\'entrée : droits, prélèvements et TVA'))
    fl.append(P("Le droit de douane n'est qu'une partie du coût d'accès. Les prélèvements communautaires (PCS UEMOA, PC CEDEAO, "
                "redevance statistique, IDF/RDL au Kenya, cess en Éthiopie) et la TVA à l'importation portent la charge théorique à plus de "
                "45 % de la valeur CAF dans 15 pays. La ZLECAf ne supprime que le droit de douane : <b>les prélèvements et la TVA restent dus</b> — "
                "un point systématiquement sous-estimé dans les business plans."))
    fl.append(figure(C + 'c3_total_burden.png', 'Figure 3.3 — Charge fiscale théorique à l\'importation, lignes agricoles hors boissons et tabac (% CAF)',
                     'Source : SaaS ZLECAf (droit de douane, prélèvements documentés, TVA au taux normal). Calcul : DD + prélèvements + TVA × (1 + DD + prélèvements). '
                     'Borne haute : de nombreux produits bruts (céréales, lait, intrants) sont exonérés ou à taux réduit de TVA. Algérie exclue (TVA par ligne non consolidée).', maxh=84 * mm))
    fl.append(callout('Ce que la ZLECAf change — et ne change pas — sur une facture à l\'import', [
        'Exemple : concentré de tomate égyptien importé au Kenya (SH 2002.90), valeur CAF 100. NPF : DD 35 + IDF/RDL 4,5 + TVA 16 % ≈ 22,3 → coût fiscal ≈ 62. '
        'Avec la préférence ZLECAf (avis EAC/321/2022, taux servi 2026) : DD ramené à 14, prélèvements inchangés, TVA recalculée ≈ 18,9 → économie d\'environ 24 points de valeur CAF, '
        'soit l\'équivalent d\'une marge nette complète dans l\'agro-industrie.',
        '<i>Conditions : origine prouvée (certificat ZLECAf), pays d\'origine figurant parmi les partenaires admis par la destination, ligne en catégorie A. '
        'Chiffres indicatifs à valider ligne par ligne dans le calculateur.</i>']))
    fl.append(PageBreak())
    fl.append(h2('3.4 L\'escalade tarifaire : le vrai frein à la transformation locale'))
    fl.append(P("L'escalade tarifaire — droits faibles sur la matière première, élevés sur le produit transformé — protège les "
                "transformateurs de chaque pays contre ceux de ses voisins. Elle est au cœur de l'enjeu ZLECAf : c'est précisément sur "
                "les produits transformés que la préférence continentale ouvre le plus de marge. Le tableau suivant, extrait des barèmes du SaaS, "
                "le montre sur six chaînes de valeur."))
    stages = [('Cacao', 'Fèves → pâte → chocolat'), ('Café', 'Vert → torréfié → soluble'), ('Blé', 'Grain → farine → pâtes'),
              ('Lait', 'Frais → poudre → fromage'), ('Tomate', 'Fraîche → concentré'), ('Sucre', 'Brut → confiserie'),
              ('Arachide/huile', 'Graines → huile'), ('Noix de cajou', 'En coque → amande')]
    regs = ['CEDEAO', 'CAE (EAC)', 'CEMAC', 'SACU', 'Algérie', 'Égypte', 'Maroc', 'Tunisie']
    hdr = ['Chaîne de valeur'] + regs
    rows = [hdr]
    for ch, lab in stages:
        r = [Paragraph(f'<b>{ch}</b><br/><font size=6.3 color="#5E6273">{lab}</font>', TD)]
        for g in regs:
            vals = [x[2] for x in ESC[g][ch]]
            r.append(' → '.join('–' if v is None else f'{v:.0f}' for v in vals))
        rows.append(r)
    fl.append(Paragraph('Tableau 3.1 — Escalade tarifaire : droit NPF moyen par stade de transformation (%)', CAP))
    fl.append(table(rows, [31 * mm] + [(CW - 31 * mm) / 8] * 8))
    fl.append(Paragraph('Source : SaaS ZLECAf, barèmes nationaux (moyenne des sous-positions SH6 de chaque stade : 1801/1803/1806 ; 090111/090121/2101 ; '
                        '1001/1101/1902 ; 0401/0402/0406 ; 0702/2002 ; 1701/1704 ; 1202/1508 ; 080131/080132). « – » : ligne non renseignée.', SRC))
    fl += bullets([
        '<b>Cacao-chocolat</b> : en CEDEAO, le droit passe de 5 % (fèves) à 35 % (chocolat) ; en Tunisie de 0 % à 50 %. '
        'Un chocolatier d\'Afrique de l\'Ouest qui vise Tunis, Casablanca ou Nairobi gagne 17 à 35 points de protection à la sortie du calendrier ZLECAf.',
        '<b>Blé-farine-pâtes</b> : le Maroc protège la meunerie nationale (farine : 70 %) ; en revanche l\'Égypte, premier importateur mondial de blé, garde des droits bas (2 à 15 %). '
        'La meunerie africaine est un marché d\'import-substitution de services, pas d\'échanges transfrontaliers de farine.',
        '<b>Lait</b> : la SACU applique des droits composites (500 c/kg) plafonnés à 96 % sur la poudre et 95 % sur les fromages ; la colonne AfCFTA les ramène à 180-200 c/kg plafonnés à ≈ 38 %. '
        'Ailleurs, les fromages restent parmi les lignes les plus exclues (liste C en Algérie, hors catégorie A au Kenya).',
        '<b>Cajou</b> : droits identiques sur la noix brute et l\'amande (CEDEAO 20 %, CAE 35 %) — aucune incitation tarifaire intra-africaine à la transformation ; '
        'celle-ci repose sur les taxes à l\'exportation de noix brute (Côte d\'Ivoire, Tanzanie, Bénin) et non sur le tarif d\'importation.'])
    return fl


def ch_offers():
    fl = [chapter(4, 'Offres ZLECAf et marges préférentielles 2026'),
          P("Dix barèmes préférentiels officiels sont archivés dans le SaaS : neuf offres extraites du <i>e-Tariff Book</i> de l'Union africaine "
            "(CEDEAO, CAE, CEMAC, Égypte, Éthiopie, Maroc, Tunisie, Zambie, Zimbabwe) et la colonne « AfCFTA » du barème SARS de la SACU. "
            "Ce chapitre mesure leur ambition sur l'agriculture et la marge préférentielle théorique disponible en 2026.", LEAD)]
    fl.append(h2('4.1 Structure des offres : ce qui est libéralisé, sensible ou exclu'))
    fl.append(P("Les modalités de la ZLECAf prévoient 90 % de lignes libéralisées (catégorie A, sur 5 ans — 10 ans pour les PMA), 7 % de produits "
                "sensibles (catégorie B, sur 10 à 13 ans) et 3 % d'exclusions (catégorie C), dans la limite de 10 % de la valeur des importations. "
                "Sur le seul périmètre agricole, les offres s'écartent nettement de ces moyennes : les États concentrent leurs lignes sensibles et exclues "
                "sur l'alimentation, et plusieurs offres ne publient pas la catégorie d'une partie de leurs lignes."))
    fl.append(figure(C + 'c5_categories.png', 'Figure 4.1 — Répartition des lignes agricoles par catégorie de libéralisation',
                     'Source : SaaS ZLECAf — AfCFTA e-Tariff Book (instantanés collectés en août-septembre 2026). « Non spécifiée » : ligne sans catégorie publiée, '
                     'généralement B ou C non divulguées — à traiter comme non libéralisée.', maxh=74 * mm))
    fl.append(P("<b>À retenir.</b> La CEMAC, l'Égypte, l'Éthiopie et la Tunisie publient des catégories B et C explicites ; la CEDEAO, la CAE, la Zambie, "
                "le Zimbabwe et le Maroc laissent 8 % à 40 % des lignes agricoles sans catégorie publiée. Pour le Maroc, la circulaire ADII 6530/223 "
                "confirme que seule la liste A est mise en œuvre : tout produit hors liste A reste au droit commun."))
    fl.append(PageBreak())
    fl.append(h2('4.2 Marge préférentielle disponible en 2026'))
    fl.append(P("En appliquant le calendrier publié (année 1 = 2021 ; 2026 = année 6) aux seules lignes de catégorie A, et en maintenant le droit NPF pour les "
                "autres (hypothèse prudente), le SaaS estime la réduction moyenne du droit agricole offerte aux partenaires éligibles."))
    fl.append(figure(C + 'c4_margins.png', 'Figure 4.2 — Droit moyen agricole : NPF de base, taux ZLECAf 2026 et fin de calendrier',
                     'Source : SaaS ZLECAf — e-Tariff Book UA (offres), SARS Schedule 1 colonne AfCFTA (SACU, comparée au taux général). Moyennes simples sur les lignes nationales SH 01-24. '
                     'Éthiopie exclue : la publication e-Tariff Book comporte des taux annuels supérieurs au NPF de base sur plusieurs lignes (incohérence de source signalée).', maxh=64 * mm))
    # table by sector: marge moyenne par filière (moyenne des 9 barèmes)
    SEC = {sid: name for sid, name, _ in D['sectors_def']}
    keys = ['TUN', 'CEMAC', 'MAR', 'ZWE', 'EAC', 'ZMB', 'ECOWAS', 'EGY', 'SACU (ZAF)']
    labs = ['Tunisie', 'CEMAC', 'Maroc', 'Zimbabwe', 'CAE', 'Zambie', 'CEDEAO', 'Égypte', 'SACU']
    rows = [['Filière'] + labs]
    for sid in SEC:
        r = [SEC[sid]]
        for k in keys:
            m = MG[k].get(sid)
            r.append('–' if not m else f"{max(0, m['mfn'] - m['y2026']):.0f}")
        rows.append(r)
    ext = []
    for i in range(1, len(rows)):
        for j in range(1, len(rows[0])):
            try:
                v = float(rows[i][j])
                if v >= 15: ext.append(('BACKGROUND', (j, i), (j, i), GREEN_L)); ext.append(('TEXTCOLOR', (j, i), (j, i), GREEN))
            except ValueError: pass
    fl.append(Paragraph('Tableau 4.1 — Marge préférentielle moyenne 2026 par filière (points de pourcentage de droit en moins)', CAP))
    fl.append(table(rows, [44 * mm] + [(CW - 44 * mm) / 9] * 9, extra=ext, align_right_from=1))
    fl.append(Paragraph('Source : calcul SaaS ZLECAf. En vert : marge ≥ 15 points — gisements prioritaires. Une marge publiée n\'est exploitable que si la destination applique '
                        'effectivement son barème à l\'origine considérée (voir chapitre 2).', SRC))
    fl.append(callout('Lecture opérationnelle', [
        '<b>Tunisie</b> (−24 points en moyenne) et <b>Zimbabwe</b> (−16) publient les marges agricoles les plus fortes, grâce à un calendrier de 5 ans déjà arrivé à terme — mais ces offres ne sont pas encore opposables (voir le chapitre 7 pour les taux effectivement servis).',
        '<b>CEMAC, CAE, CEDEAO, Zambie</b> : la moitié de la baisse est acquise ; l\'autre moitié interviendra d\'ici 2030 (catégorie A, 10 ans). Les contrats pluriannuels signés en 2026 bénéficieront mécaniquement de marges croissantes.',
        '<b>Maroc</b> (préférence opposable) : marge limitée (−7,5 points) car 40 % des lignes agricoles ne relèvent pas de la liste A ; les viandes et produits laitiers restent protégés à plus de 55 %.'],
        bg=GREEN_L, bar=GREEN, title_color=GREEN))
    return fl


def ch_roo():
    R = json.load(open(S + 'roo_counts.json'))
    fl = [chapter(5, 'Règles d\'origine : la vraie porte d\'entrée'),
          P("Aucune préférence n'est accordée sans preuve d'origine. Pour l'agriculture, l'Appendice IV de l'Annexe 2 (règles spécifiques par produit, "
            "adoptées lors du 12<super>e</super> Conseil des ministres, décembre 2023) est <b>intégralement agréé</b> sur les chapitres 01 à 24 : "
            "l'incertitude qui pèse encore sur le textile ou l'automobile ne concerne pas l'agroalimentaire.", LEAD)]
    fl.append(figure(C + 'c6_roo.png', 'Figure 5.1 — Critères d\'origine applicables aux chapitres SH 01-24',
                     'Source : SaaS ZLECAf — AfCFTA Appendix IV (PSR), décembre 2023 ; 24 règles de chapitre, 45 règles de position et 10 règles de sous-position (statut AGREED).', maxh=58 * mm))
    fl.append(P("Le critère de l'<b>entièrement obtenu</b> (WO) gouverne 20 des 24 chapitres : un produit agricole brut n'est originaire que s'il est né, cultivé, "
                "récolté ou pêché dans un État partie. Les assouplissements se concentrent sur la première transformation (huiles, laitiers, conserves de poisson, "
                "aliments du bétail), sous forme d'une règle de valeur transitoire (au plus 60 % de matières non originaires), le plus souvent limitée à 3 ou 5 ans."))
    fl.append(callout('Quatre réflexes de conformité', [
        '1. <b>Cartographier la nomenclature des intrants</b> : pour chaque intrant non africain, vérifier s\'il relève d\'une position différente (CTH) et son poids dans le prix départ usine (critère de valeur).',
        '2. <b>Dater les périodes transitoires</b> : les règles « 3 ans / 5 ans puis WO » se durcissent ; un investissement de transformation doit être rentable sous la règle définitive.',
        '3. <b>Utiliser le cumul</b> : les matières originaires de tout État partie comptent comme originaires (cumul diagonal) — un chocolatier ghanéen peut utiliser du sucre eswatinien.',
        '4. <b>Documenter</b> : certificat d\'origine ZLECAf délivré par l\'autorité compétente du pays d\'exportation (ou déclaration d\'origine lorsque la destination l\'admet) ; conserver les pièces justificatives au moins cinq ans.'], bg=BLUE_L, bar=BLUE, title_color=BLUE))
    fl.append(PageBreak())
    rows = [['Produit (SH)', 'Règle ZLECAf', 'Portée pratique pour l\'opérateur'],
            ['Farine de blé (1101)', 'Changement de position (CTH), réexamen à 5 ans', 'La mouture de blé importé (Russie, UE, Argentine) confère l\'origine : les minoteries africaines exportent en franchise.'],
            ['Pâtes, biscuits (ch. 19)', 'CTH, à condition que les produits du blé du ch. 11 soient originaires', 'Chaîne gagnante : blé importé → farine originaire → pâtes/biscuits originaires.'],
            ['Huiles végétales (1507, 1511, 1512, 1514)', 'Valeur non originaire ≤ 60 % pendant 3 ans, puis WO', 'Le raffinage d\'huile brute importée (palme d\'Asie, soja d\'Amérique) qualifie temporairement ; fenêtre à exploiter avant durcissement.'],
            ['Sucre (ch. 17 hors 1702/1704)', 'Entièrement obtenu', 'Le sucre raffiné à partir de brut importé (Brésil) n\'est PAS originaire.'],
            ['Chocolat (ch. 18)', 'Matières des ch. 17 et 18 entièrement obtenues', 'Piège majeur : un chocolat africain fabriqué avec du sucre brésilien perd l\'origine. Sourcer le sucre en Afrique (Eswatini, Afrique du Sud, Égypte, Zambie).'],
            ['Confiserie sans cacao (1704)', 'Valeur non originaire ≤ 60 %, réexamen à 5 ans', 'Plus souple que le chocolat : autorise le sucre importé dans la limite de 60 %.'],
            ['Yaourts, fromages (0403, 0406)', '≤ 60 % pendant 5 ans, puis lait (0401/0402) WO', 'La poudre de lait importée (UE, Nouvelle-Zélande) est tolérée jusqu\'à fin de période transitoire.'],
            ['Conserves de poisson (1604, 1605)', '≤ 60 % pendant 5 ans, puis poisson du ch. 3 WO', 'Le thon pêché par des navires non africains doit être anticipé : l\'origine du poisson dépend du pavillon et de l\'équipage.'],
            ['Jus de fruits (2009)', 'Fruits entièrement obtenus', 'Les concentrés importés (orange du Brésil) disqualifient le jus.'],
            ['Café soluble, extraits (2101)', 'Matières du ch. 9 entièrement obtenues', 'Solubilisation de café africain uniquement : prime à l\'intégration Éthiopie-Ouganda-Kenya.'],
            ['Aliments du bétail (2301, 2309)', '≤ 60 % pendant 3 ans, puis matières des ch. 2, 3, 4, 10, 11, 12, 17 originaires', 'Le tourteau de soja et le maïs importés sont tolérés à court terme.'],
            ['Cigarettes (2402, 2403)', 'Valeur non originaire ≤ 60 %', 'Critère de valeur : tabac africain (Zimbabwe, Malawi) favorisé mais non exigé.'],
            ['Vins, spiritueux (2204-2208)', 'CTH + raisin entièrement obtenu', 'Seul le raisin africain (Afrique du Sud, Maghreb) qualifie.']]
    fl.append(Paragraph('Tableau 5.1 — Règles d\'origine critiques pour l\'agro-industrie', CAP))
    fl.append(table(rows, [36 * mm, 50 * mm, CW - 86 * mm]))
    fl.append(Paragraph('Source : SaaS ZLECAf — Appendice IV (PSR) de l\'Annexe 2, règles au niveau chapitre/position/sous-position. Analyse ZLECAf Trade Intelligence.', SRC))
    R = json.load(open(S + 'saas_stats.json'))['roo']['chapters']
    LBL = {'WO': 'Entièrement obtenu', 'CTH': 'Changement de position', 'VA60': '≤ 60 % non originaire'}
    rows = [['Ch.', 'Intitulé', 'Règle', 'Ch.', 'Intitulé', 'Règle']]
    chs = [f'{i:02d}' for i in range(1, 25)]
    for i in range(12):
        row = []
        for c2 in (chs[i], chs[i + 12]):
            r = R[c2]; lab = LBL.get(r['code'], r['code']) + (' ou ' + LBL.get(r['alt_code'], r['alt_code']) if r.get('alt_code') else '')
            row += [c2, Paragraph(f'<font size=6.8>{r["description_fr"][:62]}</font>', TD), Paragraph(f'<font size=6.8>{lab}</font>', TD)]
        rows.append(row)
    fl.append(Paragraph('Tableau 5.2 — Règle générale par chapitre (SH 01-24), avant règles spécifiques de position', CAP))
    fl.append(table(rows, [9 * mm, 52 * mm, 26 * mm, 9 * mm, 52 * mm, CW - 148 * mm]))
    fl.append(Paragraph('Source : SaaS ZLECAf — Appendice IV (statut AGREED pour les 24 chapitres). Les règles de position et de sous-position (tableau 5.1) priment sur la règle de chapitre.', SRC))
    return fl
