from layout import *
C = S + 'charts/'

def ch_politique():
    fl = [chapter(9, 'Turbulences politiques et chaînes d\'approvisionnement'),
          P("Dans la santé, le risque politique ne se mesure pas seulement en droits de douane. Il se traduit par des frontières fermées, des espaces aériens interdits, "
            "des blocus routiers, des sanctions et des guerres maritimes qui décident de la disponibilité d'un médicament. Pour l'exportateur algérien, 2026 est "
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
    fl.append(P("<b>Ce que cela change pour le médicament algérien.</b> La session de 2016 de la commission mixte algéro-malienne comprenait déjà un volet santé : c'est le cadre naturel "
                "pour négocier une reconnaissance des enregistrements de l'ANPP et un accès aux achats publics maliens. L'espace aérien rouvert rend possible le fret aérien direct Alger-Bamako "
                "pour les produits de la chaîne du froid (insuline, vaccins). Mais trois réserves pèsent : (i) <b>aucun accord commercial ou pharmaceutique chiffré</b> n'a été publié avec le Mali "
                "(Maliexpress, 17/09/2026) ; (ii) la réouverture des postes frontières terrestres n'est confirmée par aucune source ; (iii) le <b>blocus du JNIM</b> autour de Bamako, réimposé le "
                "28 avril 2026 et toujours actif fin août, rend incertaine toute logistique routière vers le Mali par le sud. La presse sahélienne parle d'ailleurs d'un « voisinage négocié » plutôt que d'une réconciliation (Sahel Tribune, 2026) : "
                "le risque de réversibilité plaide pour des contrats courts, couverts par l'assurance-crédit. Avec le Niger, la normalisation se traduit déjà dans la santé : mémorandum entre agences du médicament "
                "en finalisation (Horizons, 24/03/2026) et groupe de travail Saidal sur l'approvisionnement et le transfert de technologie (Algérie Patriotique, 02/09/2026)."))
    fl.append(PageBreak())
    fl.append(h2('9.2 Voisinage et grands partenaires : une carte en recomposition'))
    rows = [['Relation', 'État au 27/09/2026', 'Conséquence pour la santé'],
            ['Maroc', 'Relations rompues depuis le 24/08/2021, espace aérien fermé, frontière fermée depuis 1994, gazoduc GME arrêté (ICG ; Al Jazeera, 22/07/2026)',
             'Le seul marché où la ZLECAf donne une marge au médicament algérien (0 % contre jusqu\'à 25 %) reste fermé de fait ; l\'axe terrestre vers l\'Afrique de l\'Ouest passe par la Mauritanie.'],
            ['Mauritanie', 'Route Tindouf-Zouérate ouverte à la circulation (piste en partie non revêtue), postes frontières fixes, zone franche de Tindouf (décret 24-169)',
             'Premier débouché naturel : ~220 produits Saidal ciblés, Algerian Union Bank à Nouakchott, contrats King Pharma avec filiales au Mali et au Sénégal (Algérie Eco, 29/11/2025).'],
            ['Tunisie, Libye', 'Mécanisme tripartite Égypte-Algérie-Tunisie relancé en janvier 2026 ; Libye divisée, affrontements à Zawiya (mai et septembre 2026)',
             'Tunisie : partenaire admis par l\'Algérie (0 % sur les API tunisiens). Libye : marché de 237 M USD de médicaments (BACI 2024), non ratifiant de la ZLECAf.'],
            ['France', 'Dégel partiel : retour de l\'ambassadeur en mai 2026, visites ministérielles de février à juin ; relation qualifiée de « rupture structurelle » (France 24, 08/05/2026)',
             'Aucune restriction visant les produits pharmaceutiques français identifiée ; Sanofi reste le premier site du groupe en Afrique.'],
            ['Espagne', 'Reprise des échanges en novembre 2024, traité d\'amitié réactivé en mars 2026, visite de P. Sánchez le 20/07/2026 (France 24)',
             'Réouverture d\'une source d\'équipements et de consommables européens.'],
            ['Émirats arabes unis', 'Rupture des relations diplomatiques le 10/09/2026 (Bloomberg ; Al Jazeera ; AP)',
             'Risque sur les hubs de Dubaï et Jebel Ali (déjà perturbés par Ormuz) pour les flux de réexportation et les paiements ; impact commercial non encore documenté.'],
            ['Chine', 'Levée des droits chinois sur les importations algériennes jusqu\'en 2028 annoncée à compter du 01/05/2026 (source unique, à vérifier)',
             'Sans effet direct sur la pharmacie ; la Chine reste le premier fournisseur mondial de principes actifs.']]
    fl.append(Paragraph('Tableau 9.1 — Relations extérieures de l\'Algérie et effets sur la filière santé', CAP))
    fl.append(table(rows, [24 * mm, 74 * mm, 76 * mm]))
    fl.append(Paragraph('Sources citées dans le tableau. Synthèse et lecture : ZLECAf Trade Intelligence.', SRC))
    fl.append(PageBreak())
    fl.append(h2('9.3 Instabilité en Afrique : où le risque politique touche le médicament'))
    rows = [['Pays', 'Événement', 'Effet sur l\'accès aux produits de santé'],
            ['Mali, Niger, Burkina Faso', 'Suspendus de l\'UA ; sortis de la CEDEAO (janv. 2025) ; prélèvement AES de 0,5 % sur les importations CEDEAO, aide humanitaire exemptée (Premium Times, 03/2025)',
             'Ils appliquent encore le TEC CEDEAO (médicaments à 0 %). Négociation CEDEAO-AES jusqu\'à fin 2026 : l\'origine algérienne n\'est pas pénalisée par ce prélèvement.'],
            ['Madagascar', 'Coup d\'État du 12/10/2025 ; suspendu de l\'UA', 'Marché de 93 M USD (SH 3004.90, BACI 2024) ; risque de paiement.'],
            ['Guinée-Bissau', 'Coup d\'État du 26/11/2025 ; élections annoncées pour le 06/12/2026', 'Marché marginal ; risque de rupture de contrats publics.'],
            ['Bénin', 'Tentative de coup d\'État déjouée le 07/12/2025', 'Stabilité maintenue ; corridor Cotonou-Niamey inchangé.'],
            ['Tanzanie', 'Violences post-électorales (oct. 2025) : 518 morts selon la commission, bilan contesté', 'Partenaire admis par l\'Algérie ; frontières kényanes renforcées.'],
            ['Cameroun', 'Crise post-électorale (au moins 48 morts, ONU) ; liste grise du GAFI', 'Marché CEMAC à 5 % de droit NPF ; paiements sous diligence renforcée.'],
            ['Soudan', 'Guerre depuis avril 2023 ; 37 % des établissements de santé à l\'arrêt (OMS, 09/01/2026)', 'Besoin humanitaire massif ; accès par les agences de l\'ONU uniquement.'],
            ['RD Congo (Est)', 'Accords de Doha et de Washington enlisés ; pourparlers de Genève (09/2026)', 'Liste grise du GAFI ; logistique vers l\'Est très coûteuse.'],
            ['Éthiopie-Érythrée', 'Risque de guerre élevé en 2026 (The New Humanitarian, 23/02/2026)', 'Premier marché d\'Afrique de l\'Est par la population ; droit NPF de 5 % sur les médicaments.']]
    fl.append(Paragraph('Tableau 9.2 — Foyers d\'instabilité 2025-2026 et accès aux produits de santé', CAP))
    fl.append(table(rows, [28 * mm, 76 * mm, 70 * mm]))
    fl.append(Paragraph('Sources : Union africaine (communiqués des 27/11 et 07/12/2025), Amani Africa (26/02/2026), The Citizen (2026), OMS, Al Jazeera, Chatham House, BACI via SaaS. Suspensions UA au 26/02/2026 : Burkina Faso, Guinée-Bissau, Madagascar, Mali, Niger, Soudan.', SRC))
    fl.append(h2('9.4 Chocs extérieurs : quatre décisions qui redessinent le marché'))
    fl += bullets([
        '<b>Fin de l\'USAID et nouvelle stratégie sanitaire américaine.</b> Les protocoles « America First Global Health Strategy » signés avec 24 pays africains prévoient que Washington finance 100 % '
        'des produits en 2026, puis une part décroissante (Kenya : 2,5 Md USD dont 1,6 Md USD américains ; Nigeria : 2 Md USD américains contre ~3 Md USD nationaux sur 2026-2030 ; KFF, Semafor 09/03/2026). '
        '<b>Un marché de substitution s\'ouvre à mesure que les budgets nationaux prennent le relais</b> : antirétroviraux, antipaludiques, tests.',
        '<b>Droits de douane américains.</b> Section 232 : 100 % sur les médicaments et API brevetés depuis le 31/07 ou le 29/09/2026 selon les entreprises ; génériques et biosimilaires exemptés pour l\'instant. '
        'Section 301 (« travail forcé ») : <b>12,5 % sur les importations d\'origine algérienne depuis le 24/07/2026</b> (Al Jazeera, 24/07/2026). Le marché américain n\'est pas une cible pour le générique algérien ; '
        'l\'Afrique et le Golfe le sont d\'autant plus.',
        '<b>AGOA</b> renouvelé rétroactivement le 03/02/2026 jusqu\'au 31/12/2026 seulement (USTR) : les fabricants d\'Afrique subsaharienne qui visent les États-Unis restent dans l\'incertitude ; l\'Algérie n\'y est pas éligible.',
        '<b>Ormuz et mer Rouge.</b> Ormuz est de fait fermé depuis le 28/02/2026 ; les Houthis ont repris leurs attaques en juillet et atteint l\'île de Perim en septembre. Les principes actifs indiens et chinois renchérissent '
        '(fret, assurance, délais) ; les <b>ports méditerranéens algériens et la route transsaharienne</b>, qui ne dépendent ni de Suez ni d\'Ormuz, gagnent un avantage relatif pour desservir l\'Afrique de l\'Ouest.'])
    fl.append(PageBreak())
    fl.append(h2('9.5 Matrice de risque des marchés cibles pour l\'exportateur algérien'))
    rows = [['Marché', 'Relation avec l\'Algérie', 'Stabilité intérieure', 'Accès ZLECAf (orig. DZA)', 'GAFI (juin 2026)', 'Logistique depuis l\'Algérie', 'Appréciation']]
    data = [
        ('Mauritanie', 'Très bonne', 'Stable', 'NPF (non appliquée)', '—', 'Route Tindouf-Zouérate, mer', 'Priorité 1'),
        ('Tunisie', 'Très bonne', 'Stable', 'NPF 0 % ; partenaire admis', '—', 'Route, mer', 'Priorité 1'),
        ('Niger', 'Normalisée (fév. 2026)', 'Transition militaire', 'NPF 0 % (TEC CEDEAO)', '—', 'Transsaharienne', 'Priorité 2'),
        ('Sénégal', 'Bonne', 'Stable ; Coface dégradé à C (17/02/2026)', 'NPF 0 %', '—', 'Mer, Tindouf-Zouérate', 'Priorité 2'),
        ('Mali', 'Normalisée (juil. 2026)', 'Blocus JNIM de Bamako', 'NPF 0 %', '—', 'Air ; route incertaine', 'Opportuniste'),
        ('Côte d\'Ivoire', 'Bonne', 'Stable', 'NPF 0 %', 'Liste grise', 'Mer', 'Priorité 2'),
        ('Nigeria', 'Bonne (gazoduc TSGP)', 'Tensions sécuritaires', 'NPF 0 % ; hors partenaires admis', '—', 'Mer', 'Priorité 2'),
        ('Cameroun', 'Partenaire en réciprocité', 'Crise post-électorale', 'NPF 5 % (offre non appliquée)', 'Liste grise', 'Mer', 'Priorité 3'),
        ('Libye', 'Bonne', 'Division, affrontements', 'Non ratifiante', '—', 'Route, mer', 'Opportuniste'),
        ('Égypte', 'Bonne', 'Stable', '0 % (appliquée, NPF déjà nul)', '—', 'Mer', 'Concurrent direct'),
        ('Kenya', 'Partenaire en réciprocité', 'Manifestations récurrentes', 'Origine DZA non admise', 'Liste grise', 'Mer (via Suez perturbé)', 'Priorité 3'),
        ('Maroc', 'Rompue', 'Stable', '0 % (P1) mais marché fermé de fait', '—', 'Fermée', 'Bloqué')]
    for r in data: rows.append(list(r))
    ext = []
    for i, r in enumerate(rows[1:], 1):
        col = {'Priorité 1': GREEN, 'Priorité 2': TEAL, 'Priorité 3': GOLD_D, 'Opportuniste': GOLD_D, 'Bloqué': RED, 'Concurrent direct': MUTED}.get(r[6])
        if col: ext.append(('TEXTCOLOR', (6, i), (6, i), col))
    fl.append(Paragraph('Tableau 9.3 — Matrice de risque des marchés cibles (septembre 2026)', CAP))
    fl.append(table(rows, [22 * mm, 26 * mm, 30 * mm, 30 * mm, 18 * mm, 28 * mm, 20 * mm], extra=ext))
    fl.append(Paragraph('Appréciation qualitative de ZLECAf Trade Intelligence, fondée sur les chapitres 4, 7, 8 et 9. Coface (baromètre du 17/02/2026) : seule la note du Sénégal a été vérifiée. '
                        'Les notes de risque d\'autres organismes (ACLED, assureurs-crédit) sont à consulter avant tout engagement.', SRC))
    return fl
