from layout import *

SECTORS_TABLE = [
 ('01', 'Animaux vivants & viandes', '01, 02, 16.01-16.02'), ('02', 'Pêche & aquaculture', '03, 16.03-16.05'), ('03', 'Lait, œufs & miel', '04'),
 ('04', 'Horticulture & fleurs coupées', '06'), ('05', 'Légumes, tubercules & légumineuses', '07'), ('06', 'Fruits & fruits à coque', '08'),
 ('07', 'Café, thé & épices', '09'), ('08', 'Céréales, minoterie & aliments du bétail', '10, 11, 23'), ('09', 'Oléagineux & huiles végétales', '12, 15'),
 ('10', 'Sucre & confiserie', '17'), ('11', 'Cacao & chocolat', '18'), ('12', 'Produits céréaliers & préparations alimentaires', '19, 21'),
 ('13', 'Conserves de fruits & légumes', '20'), ('14', 'Boissons', '22'), ('15', 'Tabac', '24')]

def about_page():
    fl = [Paragraph('À PROPOS DE CE RAPPORT', KICK), Spacer(1, 3),
          Paragraph('Un rapport construit sur les données du SaaS ZLECAf, actualisé avec les sources publiques les plus récentes', H2),
          P("Ce rapport sectoriel est produit par ZLECAf Trade Intelligence à partir de la plateforme SaaS ZLECAf : barèmes tarifaires nationaux, "
            "offres officielles de l'<i>e-Tariff Book</i> de l'Union africaine, règles d'origine de l'Appendice IV, registre d'application bilatérale "
            "et calculateurs de taux préférentiels. Ces données sont croisées avec les publications de référence (FAO, Banque mondiale, Afreximbank, "
            "IFPRI/AKADEMIYA2063, OMC, ICCO, OIC, CNUCED, FMI PortWatch) arrêtées au 27 septembre 2026."),
          P("Il s'adresse aux exportateurs et importateurs agroalimentaires, aux investisseurs, aux banques et assureurs du commerce, ainsi qu'aux "
            "administrations et organisations professionnelles qui préparent la mise en œuvre de la ZLECAf. Il est mis à jour chaque trimestre."),
          Spacer(1, 4), Paragraph('Périmètre : 15 filières, chapitres SH 01 à 24', H3)]
    rows = [['N°', 'Filière', 'Chapitres / positions SH']] + [list(r) for r in SECTORS_TABLE]
    fl.append(table(rows, [12 * mm, 90 * mm, CW - 102 * mm]))
    fl.append(Spacer(1, 6))
    fl.append(callout('Comment lire les taux de ce rapport', [
        '<b>NPF</b> : droit de douane de la nation la plus favorisée, appliqué à toute origine sans préférence.',
        '<b>Offre ZLECAf</b> : calendrier publié dans l\'<i>e-Tariff Book</i> — indicatif tant que la destination ne l\'a pas mis en œuvre.',
        '<b>Taux servi</b> : taux calculé par les modules du SaaS lorsque la préférence est juridiquement opposable (acte national en vigueur, origine admise, ligne couverte). '
        'En 2026, cela concerne cinq destinations : Algérie, Égypte, Kenya, Maroc et SACU.',
        '<b>Marge préférentielle</b> : écart, en points de pourcentage, entre le NPF et le taux ZLECAf. Elle ne porte que sur le droit de douane : TVA et prélèvements restent dus.'],
        bg=BLUE_L, bar=BLUE, title_color=BLUE))
    fl.append(Spacer(1, 6))
    fl.append(Paragraph('Avertissement', H3))
    fl.append(Paragraph("Ce document est une analyse économique et réglementaire. Il ne constitue ni un avis juridique ni une décision de classement ou de valeur en douane. "
                        "Les taux doivent être confirmés ligne par ligne dans le calculateur ZLECAf et auprès de l'administration des douanes de destination avant toute opération. "
                        "Les hypothèses de modélisation sont signalées (H) et les données non vérifiées en source primaire sont identifiées comme telles.", SMALL_J))
    fl.append(PageBreak())
    return fl

def toc_page():
    toc = TableOfContents()
    toc.levelStyles = [st('toc1', fontName='DMSans-Bold', fontSize=8.2, leading=10, leftIndent=0, textColor=INK, spaceBefore=0.5),
                       st('toc2', fontSize=6.8, leading=7.7, leftIndent=12, textColor=INK2)]
    toc.dotsMinLevel = 0
    return [Paragraph('SOMMAIRE', KICK), Spacer(1, 2), Paragraph('Table des matières', H1), Spacer(1, 2), toc, PageBreak()]

def exec_summary():
    fl = [chapter(None, 'Synthèse exécutive', 'synth')]
    fl[0]._toctext = 'Synthèse exécutive'
    fl.append(P("L'agriculture est le secteur où la ZLECAf a le plus à gagner — et celui que les États ont le plus protégé. En septembre 2026, "
                "la préférence continentale est juridiquement opposable dans cinq marchés, dans un contexte de guerres qui renchérissent le fret, "
                "l'assurance et le carburant. Dix messages pour décider.", LEAD))
    fl.append(kpis([
        ('≈ 118 Md$', 'importations agricoles de l\'Afrique (2023) — un marché de substitution', 'AATM 2025'),
        ('19,6 Md$', 'commerce agricole intra-africain (2023), dont 67 % de produits transformés', 'AATM 2025'),
        ('5', 'destinations où la préférence est opposable : Algérie, Égypte, Kenya, Maroc, SACU', 'Registre SaaS'),
        ('5,7 %', 'droit agricole moyen servi par l\'Algérie à ses partenaires « standard » (contre 26,6 % NPF)', 'Calculateur SaaS')], cols=4))
    fl.append(Spacer(1, 6))
    msgs = [
        ('1. Un déficit qui est un marché.', "L'Afrique importe ≈ 118 Md$ de produits agricoles (2023) — céréales 31 Md$, huiles 12 Md$, sucres 8 Md$ — soit cinq fois son commerce agricole intra-continental."),
        ('2. La protection agricole est deux fois plus forte que l\'industrielle.', "Droit moyen agricole de 16 % (CEDEAO) à 32 % (Tunisie), contre 7 à 17 % hors agriculture ; l'escalade tarifaire pénalise la transformation (chocolat à 35 % contre 5 % pour les fèves en CEDEAO)."),
        ('3. Offre publiée ≠ préférence servie.', "Sur 54 États, 50 ont ratifié et 26 ont publié leur barème ; mais le SaaS n'identifie que cinq destinations où la préférence est chiffrable avec certitude, pour des listes d'origines précises."),
        ('4. L\'Algérie et le Kenya sont les portes les plus larges.', "Algérie : 91 % des lignes agricoles réduites (0 % sur la liste A pour l'Égypte, Maurice, le Rwanda, la Tanzanie et la Tunisie). Kenya : 87 % des lignes réduites pour 28 origines, droit moyen de 24,7 % à 11,0 %."),
        ('5. Les règles d\'origine agricoles sont stabilisées — et exigeantes.', "Chapitres 01-24 intégralement agréés ; « entièrement obtenu » dans 20 chapitres sur 24 ; fenêtres transitoires (60 % de non-originaire) sur les huiles, les laitiers, les conserves de poisson et les aliments du bétail."),
        ('6. Deux pièges majeurs.', "Le sucre raffiné à partir de brut importé n'est pas originaire ; le chocolat exige du cacao et du sucre africains. À l'inverse, la mouture de blé importé confère l'origine à la farine, aux pâtes et aux biscuits."),
        ('7. Le paradoxe central.', "Les produits les plus substituables (sucre, huiles, poulet, farine, laitiers) sont les plus souvent exclus : 25 à 40 % des lignes agricoles hors liste A dans plusieurs offres. Le démantèlement de la catégorie B, ouvert en janvier 2026, est le vrai calendrier agroalimentaire (2030-2034)."),
        ('8. La guerre redessine la logistique.', "Bab el-Mandeb −65 %, Ormuz −96 %, Cap +76 % de navires ; kérosène +107 % ; surprimes de 0,2 à 10 % de la valeur de coque. Les flux Nord-Est (Égypte/Maroc ↔ Kenya) sont les plus exposés ; l'Afrique de l'Ouest et le cacao le sont peu."),
        ('9. La proximité est un avantage même sans préférence.', "Sardines marocaines à Abidjan : ≈ 110 $/t d'avantage sur la Thaïlande au même droit NPF. Concentré égyptien à Mombasa : ≈ 355 $/t d'avantage sur la Chine avec la préférence, même en supportant la surprime de guerre."),
        ('10. Six stratégies d\'investissement.', "Raffinage-trituration d'huiles, minoterie-pâtes en Afrique du Nord, chocolaterie « cacao + sucre africains », transformation du cajou, hub halieutique, filière avicole intégrée maïs-soja.")]
    cells = [[Paragraph(t, st('mt', fontName='DMSans-Bold', fontSize=8.8, leading=11.5, textColor=INK, spaceAfter=2)),
              Paragraph(b, st('mb', fontSize=8.2, leading=11.3, alignment=TA_JUSTIFY))] for t, b in msgs]
    grid = Table([[cells[i], cells[i + 1]] for i in range(0, 10, 2)], colWidths=[CW / 2] * 2)
    grid.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEABOVE', (0, 0), (-1, -1), 0.8, LINE),
                              ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 10), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    fl.append(grid)
    fl.append(PageBreak())
    fl.append(Paragraph('Les 10 cibles prioritaires 2026 (taux servis, vérifiés ligne par ligne)', H2))
    rows = [['Cible', 'Produit', 'NPF → ZLECAf 2026', 'Pourquoi maintenant'],
            ['Égypte, Tunisie → Maroc', 'Pâtes, biscuits (19.02, 19.05)', '21-50 % → 0 %', 'Liste P1 achevée ; minoterie = origine'],
            ['Égypte → Maroc', 'Oranges, pommes de terre', '40 % → 0 %', 'Premier exportateur mondial d\'oranges'],
            ['Égypte → Algérie', 'Poulet congelé (0207.14)', '30 % → 0 %', '2,6 Mt produites ; substitution d\'importations'],
            ['Tanzanie → Algérie', 'Cajou, huile de tournesol, roses', '30 % → 0 %', 'Calendrier standard ; 1er producteur africain de tournesol'],
            ['Rwanda, Tanzanie → Algérie', 'Thé noir (0902.40)', '30 % → 0 %', 'Marché de consommation majeur'],
            ['Ghana, Cameroun → Kenya, SACU', 'Chocolat (18.06)', '35 % → 14 % ; 20 % → 8 %', 'Admis dans les 5 destinations'],
            ['Côte d\'Ivoire → Kenya', 'Amandes de cajou (0801.32)', '35 % → 14 %', '600 kt transformées en 2025'],
            ['Égypte → Kenya', 'Concentré de tomate, jus, biscuits', '35 % → 14 %', 'Seul corridor ouvert pour le concentré'],
            ['Côte d\'Ivoire, Ghana, Cameroun → Kenya', 'Huile de palme raffinée', '10 % → 4 %', 'Fenêtre VA60 de 3 ans'],
            ['Malawi, Zambie → Kenya ; Malawi → Maroc', 'Tabac écôté (2401.20)', '35 % → 14 % ; 17,5 % → 0 %', 'Recettes record au Malawi']]
    fl.append(table(rows, [46 * mm, 44 * mm, 36 * mm, CW - 126 * mm]))
    fl.append(Paragraph('Source : SaaS ZLECAf — calculateurs d\'application au 27/09/2026 (voir chapitre 7). Sous réserve du respect de la règle d\'origine et de la production d\'un certificat d\'origine ZLECAf.', SRC))
    fl.append(Spacer(1, 4))
    fl.append(callout('Focus Algérie (chapitre 9)', [
        '<b>Importer</b> : pour les 5 partenaires « standard » (Égypte, Maurice, Rwanda, Tanzanie, Tunisie), la liste A est à 0 % et le DAPS (30 à 200 %) est exonéré sur les listes A et B : sucre raffiné 135 % → 29 %, pâtes 85 % → 29 %, thé 35 % → 5 % (hors TVA).',
        '<b>Exporter</b> : Égypte (liste A à 0 % : dattes, semoule, pommes de terre, caroube), SACU (caroube) ; attention à l\'origine du sucre raffiné, des boissons sucrées et de la pâte à tartiner (non originaires en l\'état).',
        '<b>Champions</b> : Cevital et Madar (sucre, trituration), Soummam, Bimo, et des marques à forte notoriété comme El Mordjene — originaire en sourçant cacao et sucre en Afrique (SACU : 17 → 6,8 %).',
        '<b>Carte maîtresse 2026</b> : l\'urée — 1,3 Md$ de demande africaine, 0,5 % captée par l\'Algérie ; plus compétitive que le Golfe dès que la surprime d\'Ormuz dépasse ≈ 1,9 %.'],
        bg=GREEN_L, bar=GREEN, title_color=GREEN))
    fl.append(Paragraph('Recommandations clés', H2))
    rec = [('Exportateurs', 'Cibler d\'abord les corridors opposables (Algérie, Kenya, Maroc P1) ; vérifier la ligne à 8-10 chiffres ; sécuriser la preuve d\'origine et le sourcing africain des intrants critiques (sucre, lait, poisson).'),
           ('Investisseurs', 'Localiser la transformation dans les pays admis dans le plus de destinations (Ghana, Cameroun, Égypte, Kenya, Tanzanie, Tunisie) ; dimensionner les projets pour l\'ouverture de la catégorie B (2030-2034) et la règle d\'origine définitive.'),
           ('Logisticiens et financeurs', 'Intégrer au coût rendu les surprimes de guerre, le détour par le Cap et les surcharges carburant ; mobiliser les instruments de crise (Afreximbank GCRP 10 Md$, BAD 5,1 Md$) et l\'assurance risque politique (ATIDI).'),
           ('Décideurs publics', 'Publier les listes d\'origines admises (Éthiopie, Zambie, Nigeria, Côte d\'Ivoire) ; basculer les lignes agroalimentaires stratégiques de B vers A ; traiter les MNT et les procédures SPS, qui pèsent plus que les droits.')]
    for t, b in rec:
        fl.append(Paragraph(f'<b>{t}.</b> {b}', BUL, bulletText='▸'))
    fl.append(PageBreak())
    return fl

def ch_recos():
    fl = [chapter(10, 'Feuille de route : que faire en 2026-2027 ?')]
    fl.append(P("Les recommandations suivantes découlent directement des chapitres précédents. Elles sont classées par horizon et par type d'acteur.", LEAD))
    rows = [['Horizon', 'Exportateurs & industriels', 'Investisseurs & financeurs', 'Pouvoirs publics & organisations professionnelles'],
            ['0-6 mois', '• Contrôler chaque ligne dans le calculateur (8-10 chiffres)\n• Obtenir le statut d\'exportateur et les certificats d\'origine ZLECAf\n• Prospecter les 25 cibles opérationnelles (chap. 7)',
             '• Stress-tester les plans d\'affaires : Cap, surprimes, kérosène ×2\n• Recourir aux lignes de crise Afreximbank et BAD\n• Couvrir le risque politique (ATIDI)',
             '• Publier les listes d\'origines admises (Éthiopie, Zambie, Nigeria)\n• Prendre les décrets d\'application (Côte d\'Ivoire)\n• Numériser les certificats d\'origine'],
            ['6-18 mois', '• Sécuriser le sourcing africain des intrants (sucre, lait, poisson)\n• Préparer la fin des périodes transitoires (VA60)\n• Diversifier les routes (Tanger Med, Walvis Bay, Abidjan)',
             '• Financer la transformation dans les pays « multi-corridors »\n• Chaîne du froid et entrepôts frigorifiques (donnée absente des bases portuaires)\n• Hubs de soutage et de transbordement',
             '• Basculer des lignes agroalimentaires de B vers A\n• Reconnaissance mutuelle SPS, zonage sanitaire\n• Corridors sécurisés au Sahel'],
            ['2028-2034', '• Tirer parti de l\'ouverture de la catégorie B (viandes, laitiers, sucre, huiles)\n• Positionner des marques régionales',
             '• Plateformes régionales de transformation (chocolat, huiles, pâtes)\n• Consolidation des filières avicoles et aquacoles',
             '• Révision quinquennale des exclusions (catégorie C)\n• Mise en œuvre du plan de Kampala (CAADP 2026-2035)']]
    rows = [rows[0]] + [[r[0]] + [Paragraph(x.replace('\n', '<br/>'), TD) for x in r[1:]] for r in rows[1:]]
    fl.append(table(rows, [20 * mm] + [(CW - 20 * mm) / 3] * 3))
    fl.append(Spacer(1, 8))
    fl.append(callout('Indicateurs de suivi pour la prochaine édition (T4 2026)', [
        'Nouvelles destinations appliquant la préférence (actes nationaux, listes d\'origines) ; premier calendrier de la catégorie B par pays.',
        'Évolution des surprimes mer Rouge, Ormuz et mer Noire ; retour éventuel des lignes conteneurs par Suez ; prix du kérosène et de l\'urée.',
        'Récoltes 2026/27 (cacao, café, maïs d\'Afrique australe) et risque « super El Niño » ; indice FAO des prix alimentaires.',
        'Intégration dans le SaaS des surprimes de guerre et du routage par le Cap dans le moteur de fret.'], bg=GOLD_L, bar=GOLD))
    fl.append(PageBreak())
    return fl

def ch_method(edition=False):
    fl = [chapter('A2', 'Annexe 2 — Note de méthodologie')]
    blocks = [
        ('1. Périmètre', "15 filières couvrant les chapitres 01 à 24 du Système harmonisé (tableau p. 2). 54 pays : 40 disposent d'un barème national intégré au SaaS "
                          "(dont 33 via quatre tarifs extérieurs communs — CEDEAO, CAE, CEMAC, SACU — et 7 barèmes nationaux : Algérie, Égypte, Éthiopie, Maroc, Maurice, Somalie, Tunisie) ; "
                          "14 sont couverts par les données continentales (statut ZLECAf, FAOSTAT, Banque mondiale, Afreximbank). Date d'arrêt des données : 27/09/2026."),
        ('2. Données tarifaires du SaaS', "35 240 lignes agricoles (SH6) issues des barèmes nationaux (sources officielles des douanes ou TEC régionaux ; fiabilité A = barème national vérifié, B = TEC ou source partielle). "
                                          "Les moyennes sont des moyennes simples de lignes, non pondérées par les échanges. Les droits spécifiques ou composites sont traités à leur équivalent publié ou signalés (SACU : plafonds de droits composites)."),
        ('3. Offres et marges théoriques', "Neuf offres de l'AfCFTA e-Tariff Book (instantanés août-septembre 2026) et la colonne AfCFTA du barème SARS. Marge théorique 2026 : calendrier publié, année 1 = 2021, 2026 = année 6, "
                                             "appliqué aux seules lignes de catégorie A ; les lignes B, C et non spécifiées restent au NPF (hypothèse prudente) ; taux plafonnés au NPF. "
                                             "L'offre éthiopienne est exclue des comparaisons (taux annuels supérieurs au NPF sur plusieurs lignes)."),
        ('4. Taux effectivement servis', "Les taux des chapitres 2, 6 et 7 sont calculés par les modules d'application du SaaS, qui ne servent une préférence que si quatre conditions sont réunies : "
                                           "acte national en vigueur, origine admise, ligne couverte, preuve d'origine. Algérie : circulaire DGD 482/2024 (calendriers standard et de réciprocité, listes A/B/C) ; "
                                           "Égypte : circulaires 38/2024 et 44/2025 (liste A, groupes 5 et 10 ans) ; Kenya : avis EAC/321/2022 (catégorie A, origines de l'Annexe 1 de la Directive 1/2021) ; "
                                           "Maroc : circulaire ADII 6530/223 et avenant 6627/223 (listes P1/P2) ; SACU : SARS Schedule 1, colonne AfCFTA (14 partenaires). "
                                           "Le balayage du chapitre 7 porte sur 7 270 couples ligne × corridor."),
        ('5. Règles d\'origine', "Appendice IV de l'Annexe 2 (règles spécifiques par produit, 12e Conseil des ministres, décembre 2023), telles qu'intégrées au SaaS : 24 règles de chapitre, 45 de position, 10 de sous-position pour les chapitres 01-24."),
        ('6. Production et commerce', "Production : FAOSTAT QCL, fichier complet mis à jour le 23/12/2025 (année 2024 ; 2023 pour le sucre, l'huile de palme et la bière). Les valeurs FAOSTAT atypiques "
                                        "(café de Centrafrique et de Guinée) sont écartées. Commerce : AATM 2025 (IFPRI/AKADEMIYA2063), Afreximbank ATR 2026, CEPII BACI 2024 (module Opportunités du SaaS, 56 lignes), UNIDO IDSB 2023 (18 pays)."),
        ('7. Logistique et coût rendu', "Distances : searoute (réseau MARNET, ±3 %) ; trafic : FMI PortWatch (AIS) ; carburant : EIA via FRED ; surprimes : presse spécialisée et circulaires du Joint War Committee. "
                                         "Le moteur de fret du SaaS (tarifs 2024, routage par Suez) est complété hors modèle. Le modèle de coût rendu retient un prix FOB identique pour isoler les autres facteurs ; "
                                         "les hypothèses (H) sont explicitées sous chaque tableau. La TVA, récupérable par l'importateur assujetti, est exclue du coût rendu."),
        ('8. Qualité des données et limites', "Le module Opportunités du SaaS contient des éléments non sourcés (profils de repli, potentiels générés par IA, fichiers de zones franches de type gabarit) : ils n'ont pas été utilisés comme données. "
                                                 "Les chiffres provenant de sources secondaires sont signalés. Les moyennes de lignes ne mesurent pas les flux réels ; une marge préférentielle ne garantit ni la compétitivité ni le respect des MNT et des normes SPS. "
                                                 "Les listes d'origines sont traitées comme des plafonds (révision annuelle non publiée).")]
    if edition:  # plans d'action : les cibles ne viennent plus du balayage du rapport unique mais de cibles.py (encadré)
        blocks = [(t, b.replace("Les taux des chapitres 2, 6 et 7 sont calculés", "Les taux servis sont calculés").replace(
            "Le balayage du chapitre 7 porte sur 7 270 couples ligne × corridor.", "Les cibles sont vérifiées selon la méthode de l'encadré ci-dessus.")) for t, b in blocks]
    for t, b in blocks:
        fl.append(Paragraph(t, st('mh', fontName='DMSans-Bold', fontSize=8.8, leading=11, textColor=INK, spaceBefore=4, spaceAfter=1))); fl.append(Paragraph(b, st('mbd', fontSize=8, leading=10.8, alignment=TA_JUSTIFY, spaceAfter=2)))
    fl.append(Paragraph('Principales sources', H3))
    src = ("SaaS ZLECAf (barèmes nationaux, e-Tariff Book UA, SARS Schedule 1, Appendice IV, registre d'application, module Opportunités) · FAO (FAOSTAT, Food Outlook, SOFIA 2024, FFPI) · "
           "IFPRI/AKADEMIYA2063 (AATM 2025) · Banque mondiale (WDI, Pink Sheet, The AfCFTA: Economic and Distributional Effects 2020) · Afreximbank (ATR 2026) · OMC/ITC/CNUCED (World Tariff Profiles 2025) · "
           "CEA-ONU · CNUCED (RMT 2025) · ICCO (QBCS) · OIC (CMR 08/2026) · tralac · Secrétariat de la ZLECAf · Journal officiel de la CAE (30/06/2026) · FMI PortWatch · EIA/FRED · Drewry · Lloyd's Market Association (JWC) · "
           "presse spécialisée (Ecofin, Lloyd's List, Insurance Journal, Al Jazeera, BusinessDay…).")
    fl.append(Paragraph(src, SMALL_J))
    return fl

LEXIQUE = [
 ('AATM', 'Africa Agriculture Trade Monitor — rapport annuel d\'IFPRI et d\'AKADEMIYA2063 sur le commerce agricole africain.'),
 ('AES', 'Alliance des États du Sahel (Burkina Faso, Mali, Niger), sortie de la CEDEAO en janvier 2025.'),
 ('Annexe 1 (Directive 1/2021)', 'Liste des États parties dont le barème provisoire est appliqué ; sert de liste d\'origines admises par le Kenya.'),
 ('Appendice IV', 'Règles d\'origine spécifiques par produit de l\'Annexe 2 de l\'Accord ZLECAf.'),
 ('BAF', 'Bunker Adjustment Factor — surcharge carburant des armateurs.'),
 ('BACI', 'Base du CEPII de commerce international réconcilié (flux bilatéraux par position SH6).'),
 ('CAF (CIF)', 'Coût, assurance, fret : valeur de la marchandise rendue au port de destination, base des droits de douane.'),
 ('Calendrier de réciprocité', 'En Algérie, calendrier plus long appliqué aux pays en développement membres de CER au calendrier PMA (Afrique du Sud, Cameroun, Ghana, Kenya).'),
 ('Catégories A, B, C', 'A : produits non sensibles libéralisés (90 % des lignes) ; B : sensibles, calendrier long (7 %) ; C : exclus (3 %).'),
 ('CER', 'Communauté économique régionale (CEDEAO, CAE, CEMAC, SADC, COMESA…).'),
 ('Certificat d\'origine ZLECAf', 'Document délivré par l\'autorité compétente du pays d\'exportation attestant l\'origine, condition de la préférence.'),
 ('CTH / CTSH', 'Changement de position (4 chiffres) / de sous-position (6 chiffres) tarifaire : critère d\'ouvraison suffisante.'),
 ('Cumul', 'Faculté de considérer comme originaires les matières d\'un autre État partie.'),
 ('DAPS', 'Droit additionnel provisoire de sauvegarde (Algérie), de 30 à 200 %, exonéré pour les listes A et B sous ZLECAf.'),
 ('DD', 'Droit de douane.'),
 ('Entièrement obtenu (WO)', 'Produit né, cultivé, récolté, pêché ou extrait dans un État partie, sans matière non originaire.'),
 ('EVP / FEU', 'Équivalent vingt pieds (conteneur de 20\') / conteneur de 40\'.'),
 ('e-Tariff Book', 'Portail de l\'Union africaine publiant les barèmes provisoires de concessions tarifaires.'),
 ('ETS', 'Système européen d\'échange de quotas d\'émission, appliqué au transport maritime depuis 2024.'),
 ('FOB', 'Franco à bord : valeur de la marchandise chargée au port d\'origine.'),
 ('G6', 'Six pays bénéficiant d\'un calendrier de 15 ans : Éthiopie, Madagascar, Malawi, Soudan, Zambie, Zimbabwe.'),
 ('GTI', 'Initiative de commerce guidé de la ZLECAf (2022-2025).'),
 ('IDF / RDL', 'Import Declaration Fee (2,5 %) et Railway Development Levy (2 %) perçus au Kenya.'),
 ('JWC', 'Joint War Committee du marché de l\'assurance de Londres, qui liste les zones à risque de guerre.'),
 ('Liste P1 / P2', 'Au Maroc, origines démantelant sur 5 ans (P1) ou 10 ans (P2) ; seule la liste A est mise en œuvre.'),
 ('MNT / BNT', 'Mesures / barrières non tarifaires (normes, licences, procédures, SPS, OTC).'),
 ('NPF', 'Nation la plus favorisée : droit appliqué à toute origine sans accord préférentiel.'),
 ('OTC', 'Obstacles techniques au commerce (normes et réglementations techniques).'),
 ('PMA', 'Pays les moins avancés, bénéficiant de calendriers plus longs.'),
 ('Portage financier', 'Coût du capital immobilisé pendant le transport (taux annuel × durée).'),
 ('PRCT', 'Prélèvement à la compensation du transport (Algérie), 2 % de la valeur en douane.'),
 ('PSTC', 'Provisional Schedule of Tariff Concessions — barème provisoire de concessions tarifaires.'),
 ('SACU', 'Union douanière d\'Afrique australe (Afrique du Sud, Botswana, Eswatini, Lesotho, Namibie).'),
 ('SH', 'Système harmonisé de désignation et de codification des marchandises (OMD).'),
 ('SPS', 'Mesures sanitaires et phytosanitaires.'),
 ('Surprime de guerre', 'Prime d\'assurance additionnelle exprimée en % de la valeur de la coque par transit en zone listée.'),
 ('Taux servi', 'Taux ZLECAf calculé par le SaaS lorsque la préférence est juridiquement opposable pour l\'origine et la ligne considérées.'),
 ('TCS', 'Taxe de contrôle sanitaire (Algérie), 3 % sur les produits alimentaires et agricoles.'),
 ('TEC', 'Tarif extérieur commun d\'une union douanière.'),
 ('TIC', 'Taxe intérieure de consommation (Algérie), perçue à l\'importation sur certains produits.'),
 ('VA60 / VA40', 'Règle de valeur : matières non originaires limitées à 60 % / 40 % du prix départ usine.'),
 ('ZLECAf (AfCFTA)', 'Zone de libre-échange continentale africaine, entrée en vigueur le 30 mai 2019, échanges ouverts le 1er janvier 2021.'),
]

def ch_lexique():
    fl = [chapter('A3', 'Annexe 3 — Lexique')]
    half = (len(LEXIQUE) + 1) // 2
    def col(items):
        return [Paragraph(f'<b>{a}</b> — {b}', st('lx', fontSize=7.6, leading=10.2, spaceAfter=3.2, alignment=TA_LEFT)) for a, b in items]
    t = Table([[col(LEXIQUE[:half]), col(LEXIQUE[half:])]], colWidths=[CW / 2, CW / 2])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 10)]))
    fl.append(t)
    return fl
