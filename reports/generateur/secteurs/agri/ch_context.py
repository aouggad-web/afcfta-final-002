from layout import *
import json
C = S + 'charts/'

def ch_context():
    fl = [chapter(1, 'L\'agriculture africaine face à la ZLECAf'),
          P("L'Afrique détient 65 % des terres arables non cultivées de la planète, emploie la moitié de sa population active dans l'agriculture — "
            "et reste pourtant importatrice nette de produits agricoles depuis 2006. La ZLECAf est le premier instrument continental capable de "
            "réorienter une partie de ces importations vers des fournisseurs africains.", LEAD)]
    fl.append(kpis([
        ('93,3 Md$', 'Exportations agricoles africaines (2023), ×3 en vingt ans', 'AATM 2025 (IFPRI/AKADEMIYA2063)'),
        ('≈ 118 Md$', 'Importations agricoles 2023 (pic : 122,9 Md$ en 2022)', 'AATM 2025, reconstitution'),
        ('19,6 Md$', 'Commerce agricole intra-africain 2023 — record historique', 'AATM 2025, ch. 2'),
        ('65 Md$', 'Facture alimentaire de l\'Afrique subsaharienne 2025 (prévision)', 'FAO Food Outlook, nov. 2025'),
        ('18,0 %', 'Part de l\'agriculture dans le PIB d\'Afrique subsaharienne (2024)', 'Banque mondiale, WDI'),
        ('49,8 %', 'Part de l\'emploi agricole en Afrique subsaharienne (2024)', 'Banque mondiale / OIT'),
        ('+49 %', 'Hausse attendue des exportations agricoles intra-africaines d\'ici 2035', 'Banque mondiale, 2020'),
        ('20,2 %', 'Population africaine sous-alimentée (2024)', 'SOFI 2025, via AATM 2025')], cols=4))
    fl.append(Spacer(1, 6))
    fl.append(h2('1.1 Un déficit structurel qui est aussi un marché'))
    fl.append(P("Entre 2019 et 2023, l'Afrique a importé en moyenne <b>108,1 milliards de dollars</b> de produits agricoles par an, dont 31,2 milliards "
                "de céréales, 12,3 milliards d'huiles et graisses et 8,2 milliards de sucres. Près de 99 milliards proviennent de l'extérieur du continent, "
                "soit <b>cinq fois</b> la valeur du commerce agricole intra-africain. L'Égypte (17,9 Md$ d'importations agricoles en 2023), le Maroc (9,9 Md$), "
                "l'Afrique du Sud (6,9 Md$) et le Nigeria (5,7 Md$) concentrent à eux seuls près de 40 % de cette demande."))
    fl.append(P("Chaque dollar importé hors du continent est une opportunité de substitution pour un producteur africain — à condition qu'il "
                "soit compétitif en prix, en qualité sanitaire et en logistique. Les filières où le potentiel est immédiat sont celles où l'Afrique "
                "est déjà exportatrice mondiale tout en important massivement : sucre, huiles végétales, riz, produits laitiers, poisson transformé."))
    fl.append(figure(C + 'c8_agva.png', 'Figure 1.1 — Valeur ajoutée agricole en % du PIB, 54 pays (dernière année disponible)',
                     'Source : SaaS ZLECAf — Banque mondiale, WDI (NV.AGR.TOTL.ZS), extraction du 21/09/2026 ; années 2023-2024.', maxh=74 * mm))
    fl.append(PageBreak())
    fl.append(h2('1.2 Le commerce agricole intra-africain : 19,6 Md$ et une dynamique de transformation'))
    fl.append(P("Le commerce agricole entre pays africains a triplé en vingt ans (6 Md$ en 2003, 19,6 Md$ en 2023). Deux caractéristiques en font "
                "le terrain naturel de l'agro-industrie : <b>85 %</b> de ces échanges portent sur des produits alimentaires, et <b>67 %</b> de leur valeur "
                "concerne des produits transformés ou semi-transformés — contre une exportation vers le reste du monde dominée par les matières "
                "premières (cacao, café, noix de cajou brute, thé). L'Afrique australe fournit à elle seule 36,1 % des exportations agricoles intra-africaines."))
    fl.append(P("La croissance récente reste toutefois tirée par les prix plus que par les volumes, et la part des fournisseurs africains dans les "
                "importations agricoles du continent a reculé de plus de 20 % au début des années 2000 à 15-17 % aujourd'hui : la ZLECAf doit inverser "
                "une tendance, pas seulement accompagner un mouvement."))
    fl.append(figure(C + 'c7_atr.png', 'Figure 1.2 — Commerce intra-africain total par pays, 2025 (Md USD, toutes marchandises) — les 15 premiers',
                     'Source : SaaS ZLECAf — Afreximbank, African Trade Report 2026 (tableau « Intra-African Trade by Country, 2021-2025 ») ; total continental 2025 : 213,8 Md$ (+5,5 %).', maxh=70 * mm))
    fl.append(h2('1.3 Ce que la ZLECAf peut rapporter à l\'agroalimentaire'))
    rows = [['Étude', 'Horizon', 'Effet sur l\'agroalimentaire', 'Message'],
            ['Banque mondiale (2020)', '2035', 'Exportations agricoles intra-africaines +49 % ; extra-africaines +10 %', 'Gains maximaux si les MNT sont réduites'],
            ['CEA-ONU / CEPII, MIRAGE-e (2021)', '2045', 'Commerce intra-africain agroalimentaire +41,1 %', 'Premier secteur gagnant, devant les services'],
            ['CEA-ONU (2021)', 'Moyen terme', '+20 % à +30 % par la seule suppression des droits', 'L\'effet tarif est réel mais borné'],
            ['CNUCED', 'Annuel', '20 Md$/an via les barrières non tarifaires vs 3,6 Md$ via les droits', 'Les MNT pèsent 5 fois plus'],
            ['MacLeod (2025)', 'Post-offres', '+5,4 % seulement sur la base des listes tarifaires publiées', 'Les exclusions agricoles limitent le potentiel']]
    fl.append(table(rows, [38 * mm, 18 * mm, 62 * mm, CW - 118 * mm]))
    fl.append(Paragraph('Sources : Banque mondiale, The AfCFTA: Economic and Distributional Effects (2020) ; CEA-ONU (2021) ; CNUCED ; MacLeod (2025) et Simola et al. (2021) cités par l\'AATM 2025.', SRC))
    fl.append(P("<b>Notre lecture.</b> L'écart entre les estimations (+5 % à +49 %) tient moins au tarif qu'à trois variables que l'entreprise peut en partie maîtriser : "
                "la conformité sanitaire (SPS), la preuve d'origine et le coût logistique. Les chapitres suivants les quantifient filière par filière."))
    return fl


def ch_legal():
    fl = [chapter(2, 'Cadre ZLECAf 2026 : ce qui est réellement applicable'),
          P("Une offre tarifaire publiée n'est pas une préférence douanière appliquée. Entre les deux s'intercalent la ratification, l'acte national "
            "d'application, la liste des partenaires admis et la preuve d'origine. Le SaaS ZLECAf ne sert un taux préférentiel qu'au terme de "
            "ces quatre vérifications : c'est la même discipline qu'un opérateur doit appliquer avant de chiffrer un contrat.", LEAD)]
    fl.append(kpis([
        ('54 / 55', 'États de l\'UA signataires (Érythrée non signataire)', 'tralac ; dtic/SARS, mars 2026'),
        ('50', 'Ratifications déposées (Bénin, Libye, Soudan, Soudan du Sud en attente)', 'tralac, 4 sept. 2026'),
        ('26', 'Barèmes provisoires publiés au journal officiel (sur 50 soumis, 40 adoptés)', 'Secrétariat ZLECAf, juin 2026'),
        ('> 12 000', 'Certificats d\'origine ZLECAf délivrés à fin juin 2026', 'Secrétariat ZLECAf, juin 2026')], cols=4))
    fl.append(h2('2.1 Les modalités de libéralisation'))
    rows = [['Catégorie', 'Part des lignes', 'Non-PMA', 'PMA', 'G6*', 'Statut 2026'],
            ['A — non sensible', '90 %', '5 ans (2021-2025)', '10 ans (2021-2030)', '15 ans', 'Non-PMA : à 0 % ; PMA : réduction de 60 %'],
            ['B — sensible', '7 %', '10 ans', '13 ans', '—', 'Démantèlement ouvert au 1er janvier 2026'],
            ['C — exclue', '3 % (≤ 10 % des importations)', 'Pas de réduction', 'Pas de réduction', '—', 'Révision quinquennale prévue']]
    fl.append(table(rows, [28 * mm, 30 * mm, 26 * mm, 27 * mm, 14 * mm, CW - 125 * mm]))
    fl.append(Paragraph('*G6 : Éthiopie, Madagascar, Malawi, Soudan, Zambie, Zimbabwe. Les unions douanières comptant toutes au moins un PMA, elles suivent en pratique le calendrier PMA. '
                        'Sources : tralac, AfCFTA FAQ (mai 2025) ; ISS African Futures.', SRC))
    fl.append(h2('2.2 Registre d\'application : où la préférence est-elle opposable ?'))
    rows = [['Destination', 'Instrument national', 'En vigueur', 'Origines admises', 'Statut SaaS'],
            ['Kenya', 'Avis EAC/321/2022 (barème CAE cat. A)', '06/09/2022', 'Annexe 1 de la Directive 1/2021 (28 parties, plafond)', 'APPLIQUÉ'],
            ['Égypte', 'Circulaires 38/2024 et 44/2025', '01/01/2025', '19 origines en deux groupes (5 et 10 ans) ; liste A seule', 'APPLIQUÉ'],
            ['Maroc', 'Circulaire ADII 6530/223 + avenant 6627/223', '2024-2025', '40 origines (listes P1 5 ans / P2 10 ans) ; liste A seule', 'APPLIQUÉ'],
            ['Afrique du Sud (SACU)', 'SARS Schedule 1, colonne AfCFTA', 'En vigueur', '14 partenaires actifs (dont Ghana, Nigeria, Kenya, Égypte, Maroc, Tunisie)', 'APPLIQUÉ'],
            ['Algérie', 'Circulaire DGD 482/2024 + module dédié', 'En vigueur', '9 partenaires actifs (Afrique du Sud, Cameroun, Égypte, Ghana, Kenya, Maurice, Rwanda, Tanzanie, Tunisie)', 'APPLIQUÉ'],
            ['Éthiopie', 'Règlement 574/2025', '14/08/2025', 'Liste notifiée séparément (art. 3-2), non publiée', 'LISTE REQUISE'],
            ['Zambie', 'SI 92/2024', '30/12/2024', 'Aucune liste exhaustive publiée', 'LISTE REQUISE'],
            ['Nigeria', 'Barème provisoire publié au JO (avril 2025)', 'Non établie', '« États parties » sans liste nominative', 'LISTE REQUISE'],
            ['Côte d\'Ivoire', 'Ordonnance 2025-260 du 23/04/2025', 'Décrets en attente', 'Aucune', 'LISTE REQUISE'],
            ['Cameroun, Ghana, Rwanda, Tunisie, Zimbabwe', 'Offre e-Tariff Book archivée', '—', 'Non vérifiées', 'OFFRE SEULE']]
    ext = []
    for i, r in enumerate(rows[1:], 1):
        col = GREEN if r[-1] == 'APPLIQUÉ' else (GOLD_D if r[-1] == 'LISTE REQUISE' else MUTED)
        ext.append(('TEXTCOLOR', (4, i), (4, i), col))
    rows2 = [rows[0]] + [r[:-1] + [Paragraph(f'<b>{r[-1]}</b>', st('x', fontSize=7, leading=9, textColor=(GREEN if r[-1] == 'APPLIQUÉ' else (GOLD_D if r[-1] == 'LISTE REQUISE' else MUTED))))] for r in rows[1:]]
    fl.append(table(rows2, [30 * mm, 42 * mm, 20 * mm, CW - 116 * mm, 24 * mm]))
    fl.append(Paragraph('Source : SaaS ZLECAf — registre d\'application bilatérale (zlecaf_implementation_registry, zlecaf_schedule_zaf, zlecaf_schedule_dza), revue du 27/09/2026. '
                        '« Liste requise » : l\'acte est adopté mais la liste des origines bénéficiaires n\'est pas publiée — la préférence n\'est pas chiffrable avec certitude.', SRC))
    fl.append(PageBreak())
    fl.append(h2('2.3 Corridors préférentiels ouverts : qui peut exporter où, dès aujourd\'hui'))
    fl.append(P("En croisant les listes d'origines admises par les cinq destinations où la préférence est opposable, le SaaS identifie 43 pays "
                "d'origine bénéficiant d'au moins un corridor ouvert. <b>Le Cameroun et le Ghana</b> sont admis dans les cinq destinations ; "
                "l'Égypte, la Gambie, le Kenya, Maurice, le Nigeria, le Rwanda et la Tunisie dans quatre. Pour un investisseur agro-industriel, "
                "implanter une unité de transformation dans l'un de ces pays maximise l'accès préférentiel aux marchés d'Afrique du Nord (Égypte : "
                "17,9 Md$ d'importations agricoles ; Maroc : 9,9 Md$), à la SACU (6,9 Md$ pour l'Afrique du Sud) et au Kenya (3,6 Md$)."))
    fl.append(figure(S + 'charts/c10_corridors.png', 'Figure 2.1 — Matrice des corridors ZLECAf opposables : destinations × origines admises (chiffre en tête : nombre de destinations ouvertes)',
                     'Source : SaaS ZLECAf — registre d\'application (Égypte : circulaires 38/2024 et 44/2025 ; Maroc : circulaire 6530/223 ; Kenya : Annexe 1 de la Directive 1/2021 ; '
                     'SACU : partenaires actifs selon dtic/SARS, mars 2026 ; Algérie : circulaire DGD 482/2024). Importations agricoles 2023 : OMC, World Tariff Profiles 2025.'))
    fl.append(callout('Mises à jour 2025-2026 à intégrer dans vos contrats', [
        '<b>Catégorie B</b> : le démantèlement des produits sensibles — où se concentrent viandes, laitiers, sucre et huiles — a démarré le 1<super>er</super> janvier 2026 ; les gains apparaîtront progressivement jusqu\'en 2031-2034.',
        '<b>Règles d\'origine</b> : en juin 2026, le Conseil des ministres a adopté une directive amendée ouvrant une fenêtre provisoire de 2 ans pour le textile ; l\'automobile reste en révision. Les chapitres agricoles 01-24 ne sont pas concernés : ils sont intégralement agréés.',
        '<b>Initiative de commerce guidé (GTI)</b> : lancée en octobre 2022 avec 8 pays, clôturée en avril 2025 après avoir fait circuler thé, café, avocats, fleurs, huile de palme, pâtes, sucre et farines ; les échanges relèvent désormais du régime général.',
        '<b>Sahel</b> : la sortie du Burkina Faso, du Mali et du Niger de la CEDEAO (janvier 2025) n\'affecte pas leur statut d\'États parties à la ZLECAf, mais rend incertaine l\'application du TEC et des règles communautaires à leurs frontières.'],
        bg=GOLD_L, bar=GOLD))
    return fl
