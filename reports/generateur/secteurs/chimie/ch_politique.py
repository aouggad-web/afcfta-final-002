from layout import *
C = S + 'charts/'

def ch_politique():
    fl = [chapter(9, 'Turbulences politiques et logistique'),
          P("Pour des produits pondéreux comme les engrais, les plastiques ou les lessives, le risque politique se lit d'abord sur la carte : frontières fermées, "
            "routes sahariennes, blocus, sanctions et guerres maritimes décident du coût rendu bien plus que le tarif. Pour l'exportateur algérien, 2026 est "
            "une année de bascule : la normalisation avec le Sahel rouvre des corridors, tandis que les crises d'Ormuz et de la mer Rouge rebattent la géographie du fret.", LEAD)]
    fl.append(h2('9.1 Algérie-Sahel : du gel d\'avril 2025 à la normalisation de 2026'))
    fl.append(figure(C + 's1_sahel.png', 'Figure 9.1 — Relations de l\'Algérie avec les États de l\'AES, avril 2025 à septembre 2026',
                     'Sources : Al Jazeera (11/07/2026), Bloomberg (10/07/2026), ISS Africa (16/03/2026), Atalayar (13/02/2026), ActuNiger (02/2026), Military Africa (04/2026), La Nouvelle Tribune (09/2026), Maliexpress (17/09/2026). '
                     'Burkina Faso : programme de ~88 M USD selon une source unique ; retour formel des ambassadeurs non documenté.', maxh=66 * mm))
    fl.append(P("La crise s'ouvre dans la nuit du 31 mars au 1er avril 2025, quand l'armée algérienne abat un drone malien près de Tinzaouatène (La Nouvelle Tribune, 09/2026). "
                "Le Mali, le Niger et le Burkina Faso rappellent leurs ambassadeurs par solidarité au sein de l'AES ; Alger ferme son espace aérien au Mali le 7 avril 2025. "
                "La sortie de crise se fait pays par pays. Avec le <b>Niger</b>, les ambassadeurs reviennent le 12 février 2026 (Atalayar, 13/02/2026) ; la visite du général Tiani à Alger "
                "(15-16 février) relance le gazoduc transsaharien, la route transsaharienne et la fibre optique, et Sonelgaz s'engage sur une centrale de 40 MW à Niamey (ActuNiger, 02/2026). "
                "À Niamey, les 23-24 mars, une vingtaine d'accords sont signés, dont un volet <b>santé</b> dont le contenu n'a pas été publié (Military Africa, 04/2026). "
                "Avec le <b>Mali</b>, la normalisation est plus tardive : ambassadeurs et espace aérien rétablis les 10-12 juillet 2026 (Bloomberg, 10/07/2026), visite à Alger du Premier ministre "
                "Abdoulaye Maïga les 24-25 août (Algérie Patriotique, 23/08/2026), puis 13e Grande Commission mixte à Bamako en septembre, la première depuis 2016 (La Nouvelle Tribune, 09/2026)."))
    fl.append(P("<b>Ce que cela change pour la chimie et l'hygiène algériennes.</b> Le Mali et le Niger importent chaque année 72 et 6 M USD de cosmétiques, savons et détergents (OEC/BACI 2024), "
                "des engrais et des insecticides pour leurs campagnes agricoles. La Transsaharienne et le gazoduc TSGP relancés avec le Niger ouvrent un corridor terrestre pour ces produits. "
                "Mais trois réserves pèsent : (i) <b>aucun accord commercial ou pharmaceutique chiffré</b> n'a été publié avec le Mali "
                "(Maliexpress, 17/09/2026) ; (ii) la réouverture des postes frontières terrestres n'est confirmée par aucune source ; (iii) le <b>blocus du JNIM</b> autour de Bamako, réimposé le "
                "28 avril 2026 et toujours actif fin août, rend incertaine toute logistique routière vers le Mali par le sud. La presse sahélienne parle d'ailleurs d'un « voisinage négocié » plutôt que d'une réconciliation (Sahel Tribune, 2026) : "
                "le risque de réversibilité plaide pour des contrats courts, couverts par l'assurance-crédit. L'Algerian Bank of Senegal prévoit une succursale à Niamey d'ici fin 2026 ou début 2027 (Horizons, 10/05/2026), condition pratique des paiements."))
    fl.append(PageBreak())
    fl.append(h2('9.2 Voisinage et grands partenaires : une carte en recomposition'))
    rows = [['Relation', 'État au 27/09/2026', 'Conséquence pour la santé'],
            ['Maroc', 'Relations rompues depuis le 24/08/2021, espace aérien fermé, frontière fermée depuis 1994, gazoduc GME arrêté (ICG ; Al Jazeera, 22/07/2026)',
             'Premier importateur africain d\'ammoniac (1,6 Md USD pour OCP) et de cosmétiques du Maghreb (152 M USD de soins et 157 M USD de détergents) : marché fermé de fait ; l\'axe terrestre vers l\'Afrique de l\'Ouest passe par la Mauritanie.'],
            ['Mauritanie', 'Route Tindouf-Zouérate ouverte à la circulation (piste en partie non revêtue), postes frontières fixes, zone franche de Tindouf (décret 24-169)',
             'Commerce bilatéral de 352 M USD en 2025 (Algérie Eco, 07/04/2026) ; accords cosmétiques, détergents et plastiques à la foire de Nouakchott (mai 2025) ; 63 M USD d\'importations de cosmétiques, savons et détergents.'],
            ['Tunisie, Libye', 'Mécanisme tripartite Égypte-Algérie-Tunisie relancé en janvier 2026 ; Libye divisée, affrontements à Zawiya (mai et septembre 2026)',
             'Tunisie : partenaire admis par l\'Algérie, dont les cosmétiques entrent à 2 % contre 112 %. Libye : voir le chapitre 8.'],
            ['France', 'Dégel partiel : retour de l\'ambassadeur en mai 2026, visites ministérielles de février à juin ; relation qualifiée de « rupture structurelle » (France 24, 08/05/2026)',
             'La France reste le premier client de l\'urée et de l\'hélium algériens : le MACF pèse davantage que la relation politique.'],
            ['Espagne', 'Reprise des échanges en novembre 2024, traité d\'amitié réactivé en mars 2026, visite de P. Sánchez le 20/07/2026 (France 24)',
             'L\'Espagne est le premier fournisseur de chimie de l\'Algérie (plus de 600 M EUR par an, Maghreb Émergent).'],
            ['Émirats arabes unis', 'Rupture des relations diplomatiques le 10/09/2026 (Bloomberg ; Al Jazeera ; AP)',
             'Risque sur les hubs de Dubaï et Jebel Ali (déjà perturbés par Ormuz) pour les flux de réexportation et les paiements ; impact commercial non encore documenté.'],
            ['Chine', 'Levée des droits chinois sur les importations algériennes jusqu\'en 2028 annoncée à compter du 01/05/2026 (source unique, à vérifier)',
             'La Chine reste le premier fournisseur de plastiques de l\'Afrique (8,9 Md USD en 2024).']]
    fl.append(Paragraph('Tableau 9.1 — Relations extérieures de l\'Algérie et effets sur la filière', CAP))
    fl.append(table(rows, [24 * mm, 74 * mm, 76 * mm]))
    fl.append(Paragraph('Sources citées dans le tableau. Synthèse et lecture : ZLECAf Trade Intelligence.', SRC))
    fl.append(PageBreak())
    fl.append(h2('9.3 Instabilité en Afrique : les marchés sous tension'))
    rows = [['Pays', 'Événement', 'Effet sur le commerce du périmètre'],
            ['Mali, Niger, Burkina Faso', 'Suspendus de l\'UA ; sortis de la CEDEAO (janv. 2025) ; prélèvement AES de 0,5 % sur les importations CEDEAO', 'Ils appliquent encore le TEC CEDEAO (20 % sur les cosmétiques, 35 % sur certains savons) ; l\'origine algérienne n\'est pas visée par le prélèvement AES.'],
            ['Mali', 'Blocus du JNIM autour de Bamako (réimposé le 28/04/2026)', 'Logistique routière du sud paralysée ; demande d\'engrais et d\'insecticides perturbée.'],
            ['Libye', 'Division des institutions, affrontements à Zawiya (mai et septembre 2026)', 'Premier marché de proximité (741 M USD dans le périmètre) : voir le chapitre 8.'],
            ['Soudan', 'Guerre depuis avril 2023', 'Marché des savons de ménage (21 M USD) accessible surtout par l\'aide humanitaire.'],
            ['Cameroun, RD Congo, Côte d\'Ivoire, Kenya', 'Liste grise du GAFI (juin 2026) ; crises post-électorales (Cameroun)', 'Diligences bancaires renforcées ; RD Congo : premier importateur africain de lessives (82 M USD).'],
            ['Madagascar, Guinée-Bissau', 'Coups d\'État (oct. et nov. 2025) ; suspendus de l\'UA', 'Risque de paiement élevé.'],
            ['Éthiopie-Érythrée', 'Risque de guerre élevé en 2026', 'Premier projet d\'urée de Dangote hors Nigeria (Éthiopie, lancé en oct. 2025).']]
    fl.append(Paragraph('Tableau 9.2 — Foyers d\'instabilité 2025-2026', CAP))
    fl.append(table(rows, [34 * mm, 70 * mm, 70 * mm]))
    fl.append(Paragraph('Sources : Union africaine, Amani Africa (26/02/2026), GAFI, OEC/BACI 2024 (via le SaaS), recherche documentaire du 27/09/2026.', SRC))
    fl.append(h2('9.4 Chocs extérieurs : ce qui redessine le marché'))
    fl += bullets([
        '<b>Ormuz et mer Rouge.</b> Ormuz fermé de fait depuis le 28/02/2026 ; le Golfe fournit 24,8 % des engrais azotés mondiaux (OMC, 10/07/2026). L\'urée a dépassé 850 USD/t en avril avant de revenir à 453 USD/t en juin. '
        'Les polymères et le méthanol du Golfe renchérissent pour l\'Afrique : c\'est une fenêtre pour les producteurs méditerranéens.',
        '<b>MACF européen.</b> Phase définitive depuis le 01/01/2026 sur l\'ammoniac, l\'urée et les engrais azotés : coût croissant jusqu\'en 2034 (tableau 7.4), qui incite à diversifier les débouchés.',
        '<b>Droits américains.</b> 12,5 % sur les importations d\'origine algérienne depuis le 24/07/2026 au titre de la section 301 (Al Jazeera, 24/07/2026) : les États-Unis, client de l\'urée algérienne (15 % des ventes en 2024), deviennent moins accessibles.',
        '<b>Rupture Algérie-Émirats (10/09/2026).</b> Les Émirats sont un fournisseur majeur de cosmétiques contrefaits saisis en Algérie (45,5 % des saisies d\'origine connue en 2023, DGD) et un hub de réexportation vers l\'Afrique : leur recul libère de la place pour les producteurs locaux.'])
    fl.append(PageBreak())
    fl.append(h2('9.5 Matrice de risque des marchés cibles pour l\'exportateur algérien'))
    rows = [['Marché', 'Relation', 'Stabilité', 'Accès (orig. DZA)', 'Import. 2024*', 'Logistique', 'Appréciation']]
    data = [('Libye', 'Bonne', 'Division, affrontements', 'Non ratifiante ; GAFTA', '741 M$', 'Mer (588 nm), route', 'Priorité 1'),
            ('Tunisie', 'Très bonne', 'Stable', 'NPF (offre non appliquée)', '118 M$**', 'Route, mer', 'Priorité 1'),
            ('Mauritanie', 'Très bonne', 'Stable', 'NPF', '63 M$**', 'Mer (CNAN), Tindouf-Zouérate', 'Priorité 1'),
            ('Sénégal', 'Bonne', 'Stable ; Coface C', 'NPF (TEC CEDEAO)', '77 M$**', 'Mer (CNAN)', 'Priorité 2'),
            ('Niger', 'Normalisée (fév. 2026)', 'Transition militaire', 'NPF (TEC CEDEAO)', '6 M$**', 'Transsaharienne', 'Priorité 2'),
            ('Mali', 'Normalisée (juil. 2026)', 'Blocus JNIM', 'NPF', '72 M$**', 'Air ; route incertaine', 'Opportuniste'),
            ('Égypte', 'Bonne', 'Stable', 'Préférence servie (savons 0,75 %)', '239 M$**', 'Mer', 'Concurrent direct'),
            ('Afrique du Sud', 'Réciprocité', 'Stable', 'Cosmétiques 20 → 12,8 %', '—', 'Mer (Le Cap)', 'Engrais : priorité 2'),
            ('Maroc', 'Rompue', 'Stable', '0 % (P1) mais fermé de fait', '354 M$**', 'Fermée', 'Bloqué')]
    for r in data: rows.append(list(r))
    ext = []
    for i, r in enumerate(rows[1:], 1):
        col = {'Priorité 1': GREEN, 'Priorité 2': TEAL, 'Opportuniste': GOLD_D, 'Bloqué': RED, 'Concurrent direct': MUTED}.get(r[6])
        if col: ext.append(('TEXTCOLOR', (6, i), (6, i), col))
    fl.append(Paragraph('Tableau 9.3 — Matrice de risque des marchés cibles (septembre 2026)', CAP))
    fl.append(table(rows, [22 * mm, 26 * mm, 28 * mm, 34 * mm, 18 * mm, 28 * mm, 18 * mm], extra=ext))
    fl.append(Paragraph('*Importations 2024 (OEC/BACI via le module Statistiques du SaaS) : Libye, total des 25 positions suivies ; **cosmétiques, savons et détergents (33.04, 34.01, 34.02) seulement. Appréciation qualitative de ZLECAf Trade Intelligence.', SRC))
    return fl
