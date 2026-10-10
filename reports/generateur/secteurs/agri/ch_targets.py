from layout import *
import json
SC = json.load(open(S + 'scan.json'))

TOP = [  # produit, SH, origine(s), destination, NPF, ZLECAf 2026, base, contexte
 ('Pommes de terre', '0701.90', 'Égypte', 'Maroc', '40', '0', 'Liste P1 (5 ans)', 'Égypte : 8,1 Mt produites (2024)'),
 ('Oranges', '0805.10', 'Égypte', 'Maroc', '40', '0', 'Liste P1', '1er exportateur mondial (1,66 Mt)'),
 ('Pâtes, biscuits', '1902.19 / 1905.31', 'Égypte, Tunisie', 'Maroc', '21-50', '0', 'Liste P1', 'Maroc : droits parmi les plus élevés'),
 ('Morceaux de poulet congelés', '0207.14', 'Égypte', 'Algérie', '30', '0', 'Liste A, standard', 'Égypte : 2,6 Mt de poulet (2024)'),
 ('Amandes de cajou', '0801.32', 'Tanzanie', 'Algérie', '30', '0', 'Liste A, standard', 'Tanzanie : 0,53 Mt de noix brute'),
 ('Thé noir', '0902.40', 'Rwanda, Tanzanie', 'Algérie', '30', '0', 'Liste A, standard', 'Algérie : grand consommateur'),
 ('Huile de tournesol', '1512.19', 'Tanzanie', 'Algérie', '30', '0', 'Liste A, standard', 'Tanzanie : 1er producteur africain'),
 ('Roses', '0603.11', 'Tanzanie', 'Algérie', '30', '0', 'Liste A, standard', 'Fret aérien via Doha ou Addis'),
 ('Tabac écôté', '2401.20', 'Malawi', 'Maroc', '17,5', '0', 'Liste P1', 'Malawi : 540 M$ de recettes (2025)'),
 ('Aliments du bétail', '2309.90', 'Tunisie', 'Algérie', '15', '0', 'Liste A, standard', 'Filières avicoles algériennes'),
 ('Chocolat', '1806.90', 'Ghana, Cameroun', 'Kenya', '35', '14', 'CAE cat. A (Annexe 1)', 'Couplage sucre africain requis'),
 ('Amandes de cajou', '0801.32', 'Côte d\'Ivoire', 'Kenya', '35', '14', 'CAE cat. A', '600 kt transformées en 2025'),
 ('Biscuits', '1905.31', 'Égypte', 'Kenya', '35', '14', 'CAE cat. A', 'Égypte admise par le Kenya'),
 ('Concentré de tomate, jus d\'orange', '2002.90 / 2009.11', 'Égypte', 'Kenya', '35', '14', 'CAE cat. A', 'Seul corridor ouvert pour le concentré'),
 ('Oignons', '0703.10', 'Égypte', 'Kenya', '35', '14', 'CAE cat. A', 'Égypte : 3,4 Mt (2024)'),
 ('Morceaux de poulet congelés', '0207.14', 'Égypte', 'Kenya', '35', '14', 'CAE cat. A', 'Demande urbaine croissante'),
 ('Tabac écôté', '2401.20', 'Malawi, Zambie', 'Kenya', '35', '14', 'CAE cat. A', 'Cigarettiers implantés au Kenya'),
 ('Thé noir', '0902.40', 'Kenya', 'Algérie', '30', '12', 'Liste A, réciprocité', 'Kenya : 594,5 M kg exportés'),
 ('Avocats', '0804.40', 'Kenya', 'Algérie', '30', '12', 'Liste A, réciprocité', 'Kenya : 1er producteur africain'),
 ('Poisson congelé, thon en conserve', '0303 / 1604.14', 'Mauritanie, Ghana, Égypte', 'Kenya', '25', '10', 'CAE cat. A', '100 % des lignes réduites'),
 ('Bouillons, assaisonnements', '2104.10', 'Nigeria', 'Kenya / SACU', '25 / 20', '10 / 8', 'CAE cat. A / col. AfCFTA', 'Marques nigérianes'),
 ('Chocolat', '1806.32', 'Ghana, Cameroun', 'SACU', '20', '8', 'Colonne AfCFTA', 'SACU : 0,05 Md$ de préparations importées'),
 ('Boissons non alcoolisées', '2202.99', 'Égypte', 'SACU', '21', '8,4', 'Colonne AfCFTA', '85 % des lignes boissons réduites'),
 ('Jus d\'orange', '2009.11', 'Afrique du Sud', 'Égypte', '17', '6,8', 'Liste A, groupe 10 ans', '−60 % en 2026'),
 ('Poisson congelé', '0303.89', 'Sénégal', 'Maroc', '10', '0', 'Liste P1', 'Maroc : liaison maritime directe'),
]

def ch_targets():
    fl = [chapter(7, 'Cibles & opportunités : où la préférence paie en 2026'),
          P("Les moyennes d'offres donnent une orientation ; les taux effectivement servis décident d'un contrat. Ce chapitre repose sur un balayage "
            "exhaustif des lignes agricoles des cinq destinations qui appliquent la ZLECAf, recalculées une à une par les modules du SaaS pour chaque groupe "
            "d'origines (7 270 couples ligne × corridor). Il en ressort une hiérarchie nette — et plusieurs fausses pistes.", LEAD)]
    fl.append(h2('7.1 Carte des marges réellement servies'))
    fl.append(figure(S + 'charts/c11_served.png', 'Figure 7.1 — Réduction moyenne du droit de douane effectivement servie en 2026, par corridor et par filière (points de pourcentage)',
                     'Source : SaaS ZLECAf — calculateurs zlecaf_schedule_dza, zlecaf_schedule_egy, zlecaf_schedule_ken, official_preferential_rates (Maroc, SACU), exécutés le 27/09/2026 sur toutes les lignes SH 01-24 des barèmes nationaux. '
                     'Entre parenthèses : droit agricole moyen NPF → ZLECAf. Égypte : moyennes tirées par les droits sur l\'alcool (non affichées). n.d. : chapitres non consolidés.', maxh=122 * mm))
    rows = [['Corridor (exemple d\'origine)', 'Lignes agricoles', 'dont réduites', 'Droit moyen NPF', 'Droit moyen ZLECAf 2026']]
    for k in ['DZA|TUN', 'KEN|GHA', 'DZA|GHA', 'MAR|EGY', 'MAR|GHA', 'EGY|TUN', 'EGY|GHA', 'ZAF|GHA']:
        v = SC[k]
        rows.append([v['label'], str(v['n']), f"{v['n_red']} ({v['share']:.0f} %)".replace('.', ','), f"{v['avg_npf']:.1f} %".replace('.', ','), f"{v['avg_pref']:.1f} %".replace('.', ',')])
    fl.append(table(rows, [66 * mm, 24 * mm, 28 * mm, 28 * mm, CW - 146 * mm], align_right_from=1))
    fl.append(Paragraph('Égypte : moyennes incluant les droits de 1 200 à 3 000 % sur les boissons alcoolisées (hors ces lignes, le droit agricole moyen est de 10,3 %).', SRC))
    fl.append(PageBreak())
    fl.append(h2('7.2 Quatre enseignements pour les exportateurs'))
    fl += bullets([
        '<b>L\'Algérie est le marché le plus ouvert du continent pour ses partenaires activés</b> : 91 % des lignes agricoles réduites, droit moyen ramené de 26,6 % à 5,7 % pour '
        'l\'Égypte, Maurice, le Rwanda, la Tanzanie et la Tunisie (liste A à 0 % depuis 2025). Le Kenya, le Ghana, le Cameroun et l\'Afrique du Sud, soumis au calendrier de réciprocité, '
        'bénéficient d\'une réduction de 60 % en 2026 et de la franchise en 2030. Mais la liste C algérienne exclut des produits clés (concentré de tomate, oignons, raisins, fromages, sardines).',
        '<b>Le Kenya est la porte d\'entrée la plus large de l\'Afrique de l\'Est</b> : 87 % des lignes réduites pour les 28 origines de l\'Annexe 1 (CEDEAO, CEMAC, Égypte…), '
        'droit moyen de 24,7 % à 11,0 %. C\'est le seul marché CAE où la préférence est opposable — et un tremplin vers l\'Ouganda, la Tanzanie et la RDC par les règles communautaires.',
        '<b>Le Maroc est sélectif</b> : 57 % des lignes réduites, mais les viandes, produits laitiers, dattes, concentré de tomate, chocolat et fleurs restent hors liste A. '
        'Les gains se concentrent sur la pêche, les légumes, les fruits (oranges), les pâtes et biscuits et le tabac.',
        '<b>La SACU n\'est pas un eldorado tarifaire</b> : son droit agricole est déjà bas (9,5 %) et la colonne AfCFTA ne réduit que 28 % des lignes. L\'intérêt réside dans le chocolat, les boissons, '
        'les bouillons et le tabac, et dans la taille du marché sud-africain.'], sym='●')
    fl.append(Spacer(1, 4))
    fl.append(callout('Fausses pistes fréquentes — vérifiées ligne par ligne', [
        'Concentré de tomate égyptien vers le Maroc (hors liste A), l\'Algérie (liste C) ou la SACU (37 % maintenus) ; seul le Kenya (35 % → 14 %) est ouvert.',
        'Pâtes égyptiennes vers le Kenya (hors catégorie A) ou la SACU (40 % maintenus) ; en Algérie, liste B (30 % → 24 %).',
        'Roses kényanes ou éthiopiennes vers la SACU (20 % maintenus) ; dattes vers le Maroc (hors liste A) ; sardines en conserve vers l\'Algérie (liste C) ou l\'Égypte (liste B).',
        'Viande bovine vers le Maroc : 200 % maintenus au titre de la ZLECAf ; seule la suspension nationale 2026 (300 000 têtes de bétail vif) ouvre le marché.'],
        bg=RED_L, bar=RED, title_color=RED))
    fl.append(Spacer(1, 8))
    fl.append(h2('7.3 Top 25 des cibles opérationnelles 2026'))
    rows = [['#', 'Produit (SH)', 'Origine(s)', 'Destination', 'NPF %', 'ZLECAf 2026 %', 'Base juridique', 'Contexte']]
    for i, t in enumerate(TOP, 1):
        rows.append([str(i), Paragraph(f'<b>{t[0]}</b><br/><font size=6.3 color="#5E6273">{t[1]}</font>', TD), t[2], t[3], t[4],
                     Paragraph(f'<b><font color="#1E8C5A">{t[5]}</font></b>', TD), t[6], Paragraph(f'<font size=6.6>{t[7]}</font>', TD)])
    fl.append(table(rows, [6 * mm, 34 * mm, 26 * mm, 18 * mm, 12 * mm, 15 * mm, 27 * mm, CW - 138 * mm]))
    fl.append(Paragraph('Source : SaaS ZLECAf — taux calculés ligne par ligne (position nationale à 8 ou 10 chiffres) au 27/09/2026 par les modules d\'application (Algérie : circulaire 482/2024 ; Égypte : '
                        'circulaires 38/2024 et 44/2025 ; Kenya : avis EAC/321/2022 ; Maroc : circulaire 6530/223 ; SACU : SARS Schedule 1, colonne AfCFTA). Contextes : FAOSTAT 2024, AATM 2025, BACI 2024, sources des fiches filières. '
                        'Conditions : certificat d\'origine ZLECAf et respect de la règle d\'origine de l\'Appendice IV.', SRC))
    fl.append(Spacer(1, 8))
    fl.append(h2('7.4 Six stratégies d\'investissement agro-industriel'))
    plays = [
        ('1. Raffinage et trituration d\'huiles', 'Déficit de 7,77 Md$ d\'importations contre 2,21 Md$ d\'exportations (18 pays UNIDO). Fenêtre VA60 de 3 ans sur les huiles 1507-1518. '
         'Sites : Côte d\'Ivoire, Ghana, Cameroun (palme, cibles Kenya 10 % → 4 %) ; Tanzanie (tournesol, cible Algérie 30 % → 0 %).'),
        ('2. Minoterie-pâtes-biscuiterie en Afrique du Nord', 'La mouture confère l\'origine (1101 CTH) et le chapitre 19 exige seulement une farine originaire. '
         'Égypte et Tunisie → Maroc à 0 % (pâtes et biscuits) ; Égypte → Kenya (biscuits 35 % → 14 %).'),
        ('3. Chocolaterie panafricaine « cacao + sucre africains »', 'Le Ghana et le Cameroun sont admis dans les 5 destinations. Chocolat → Kenya (35 % → 14 %) et SACU (20 % → 8 %) ; '
         'sucre à sourcer en Eswatini, en Zambie ou au Malawi pour satisfaire la règle du chapitre 18.'),
        ('4. Transformation de cajou ouest et est-africaine', 'Côte d\'Ivoire → Kenya (35 % → 14 %) et Maroc (10 % → 4 %) ; Tanzanie → Algérie (30 % → 0 %). '
         'Capacité ivoirienne de 830 kt ; objectif de plus de 50 % de noix transformées en 2030.'),
        ('5. Hub halieutique et aquacole', 'Pêche : 100 % des lignes réduites au Kenya, marge de 27 points en Algérie (standard). Mauritanie, Sénégal, Ghana, Égypte (tilapia), Maroc (conserves de thon → Égypte à 0 %).'),
        ('6. Filière avicole intégrée maïs-soja-aliment', 'Substituer 1,74 Md$ de poulet congelé importé ; Égypte → Algérie (0 %) et Kenya (14 %) ; aliments du bétail tunisiens → Algérie (0 %).')]
    cells = []
    for t, b in plays:
        cells.append([Paragraph(t, st('pt', fontName='DMSans-Bold', fontSize=9, leading=12, textColor=INK, spaceAfter=3)),
                      Paragraph(b, st('pb', fontSize=8.2, leading=11.4, alignment=TA_JUSTIFY))])
    grid = Table([[cells[0], cells[1]], [cells[2], cells[3]], [cells[4], cells[5]]], colWidths=[CW / 2] * 2)
    grid.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BACKGROUND', (0, 0), (-1, -1), ZEBRA), ('LINEABOVE', (0, 0), (-1, -1), 1.6, GOLD),
                              ('INNERGRID', (0, 0), (-1, -1), 4, colors.white), ('BOX', (0, 0), (-1, -1), 4, colors.white),
                              ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 9)]))
    fl.append(grid)
    fl.append(Spacer(1, 6))
    fl.append(P("<b>Le paradoxe central.</b> Les produits les plus substituables — sucre, huiles, poulet, farine, laitiers — sont aussi ceux que les États ont le plus souvent placés "
                "hors catégorie A : 39,7 % des lignes agricoles du Maroc, 29,7 % de la Tunisie, 25,1 % de la CEDEAO et 22,5 % de la CEMAC ne relèvent pas de la liste libéralisée, "
                "contre ≈ 11 % toutes lignes confondues. L'ouverture de la catégorie B (2026-2034) est le vrai calendrier de l'agroalimentaire."))
    return fl
