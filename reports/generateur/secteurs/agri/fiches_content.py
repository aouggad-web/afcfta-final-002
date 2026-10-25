from fiche import *
from contradictions import ref

FAO = 'FAOSTAT QCL (MAJ 23/12/2025)'
F = []

F.append(dict(num=1, sid='S01', name='Animaux vivants & viandes', hs='01, 02, 16.01-16.02',
 lead="Un quart du cheptel bovin mondial, mais 6,5 % seulement de la viande produite : l'élevage africain est le cas d'école du potentiel inexploité — et la sécheresse au Maghreb ouvre en 2026 une fenêtre d'exportation inédite.",
 kp=[('398,7 M', 'bovins en 2024, soit 25,3 % du cheptel mondial', FAO), ('24,2 Mt', 'de viande produite en 2024 (6,5 % du monde)', FAO),
     ('1,74 Md$', 'de morceaux de poulet congelés importés en 2024 (SH 020714)', 'SaaS — CEPII BACI'), ('300 000', 'bovins importables en franchise au Maroc jusqu\'au 31/12/2026', 'Loi de finances 2026')],
 marche=["La production de poulet atteint 8,26 Mt (Égypte 2,60 Mt ; Afrique du Sud 1,92 Mt), mais le continent importe encore 1,74 Md$ de morceaux congelés, "
         "principalement au Ghana (328 M$), en Angola (213 M$), en Afrique du Sud (192 M$) et au Congo (139 M$). Les bovins vivants représentent 0,68 Md$ d'importations "
         "(Maroc 259 M$, Égypte 196 M$). L'Égypte importe en outre 1,25 Md$ de viandes transformées (UNIDO 2023).",
         "Le cheptel bovin marocain a reculé d'environ 30 % après plusieurs années de sécheresse : la loi de finances 2026 suspend droits et TVA sur 300 000 bovins et 10 000 camelins. "
         "L'Algérie ramène à 5 % le droit sur les bovins et ovins d'abattage, les viandes fraîches et les volailles congelées jusqu'à fin 2026 (LF 2026, art. 139-140)."],
 tarif="Viande bovine (0201) : 35 % en CEDEAO et CAE, 40 % en SACU, 200 % au Maroc, 0 % en Égypte. Volailles (0207) : 35 % en CEDEAO et CAE, 81 % au Maroc. "
       "La marge ZLECAf 2026 atteint 13 points dans la CAE et 17 en Tunisie, mais reste faible au Maroc (71 → 62 %) où l'essentiel des viandes est hors liste A.",
 origine="Règle : entièrement obtenu (chapitres 01-02). L'animal doit être né et élevé dans un État partie : un bovin importé d'Amérique latine puis engraissé en Afrique ne confère pas l'origine à sa viande.",
 cibles=["<b>Sahel → Maroc</b> : Tchad, Mali, Niger et Éthiopie figurent sur la liste P1 marocaine ; s'y ajoute la franchise nationale 2026 ouverte à toutes origines.",
         "<b>Afrique australe → Angola, RDC</b> : volaille sud-africaine (corridor maritime Afrique du Sud–Angola modélisé à ≈ 955 $/EVP, 6 jours).",
         "<b>Éthiopie, Soudan → Golfe et Égypte</b> : filière d'exportation d'ovins et caprins sur pied ; l'Égypte est un débouché si la préférence s'ouvre à ces origines.",
         "<b>Intégration verticale volaille</b> : couplage avec la filière maïs-soja-aliment (fiche 08) pour substituer les 1,74 Md$ d'importations de poulet."],
 risques=["Barrières sanitaires : fièvre aphteuse, grippe aviaire (suspension sud-africaine des volailles brésiliennes depuis mai 2025), zonage indemne rarement reconnu.",
          "Antidumping SACU sur la volaille, en réexamen en 2026 ; insécurité des couloirs sahéliens de transhumance."],
 sources='FAOSTAT 2024 ; SaaS ZLECAf (barèmes, BACI 2024, UNIDO IDSB 2023, fret modélisé) ; LF 2026 Maroc (le360) et Algérie (art. 139-140) ; BusinessDay (08/2026).'))

F.append(dict(num=2, sid='S02', name='Pêche & aquaculture', hs='03, 16.03-16.05',
 lead="Troisième poste d'exportation agricole du continent, la filière halieutique a déjà son champion industriel : le Maroc, qui exporte plus de poisson transformé que tout le reste de l'Afrique réunie.",
 kp=[('6,4 Md$', 'exportations africaines de poissons et crustacés (moyenne 2019-2023)', 'AATM 2025'), ('2,3 Mt', 'production aquacole 2022 (1,9 % du monde) ; 2,8 Mt attendues en 2032', 'FAO SOFIA 2024'),
     ('2,61 Md$', 'poisson transformé exporté par le Maroc (2023)', 'SaaS — UNIDO IDSB'), ('848 M$', 'importations de poisson transformé de la Côte d\'Ivoire (2023) ; conserves seules (SH 1604) : 46 M$ selon BACI' + ref('C25'), 'SaaS — UNIDO IDSB ; OEC/BACI')],
 marche=["Les captures continentales africaines (3,3 Mt, 29 % du total mondial des eaux intérieures) nourrissent les marchés locaux ; la valeur ajoutée se concentre dans la conserve "
         "(thon, sardine) et le congelé. Côte d'Ivoire (848 M$), Égypte (626 M$), Maroc (289 M$) et Ghana (214 M$) sont les premiers importateurs de poisson transformé.",
         "L'aquaculture égyptienne (tilapia) représenterait à elle seule 1,9 Mt en 2032 selon la FAO : c'est le seul pôle aquacole africain d'échelle industrielle."],
 tarif="Poisson frais (0302) : 10 % en CEDEAO, 25 % en CAE, 50 % en Égypte. Conserves (1604) : 20 % en CEDEAO, 30 % en CEMAC, 36 % en Tunisie, 40 % au Maroc. "
       "La marge 2026 atteint 14 à 15 points en CAE et en CEMAC ; au Maroc, les lignes halieutiques de la liste A sont quasiment à 0 %.",
 origine="Règle : entièrement obtenu (chapitre 03), avec des conditions cumulatives sur le navire (immatriculation, pavillon, propriété). Conserves 1604-1605 : jusqu'à 60 % de matières non originaires pendant 5 ans, puis poisson du chapitre 03 entièrement obtenu.",
 cibles=["<b>Conserves marocaines → Égypte</b> : le Maroc appartient au groupe « 5 ans » égyptien, liste A à 0 % depuis 2025.",
         "<b>Conserves marocaines → Afrique de l'Ouest</b> : Sénégal, Côte d'Ivoire (liaison Maroc–Sénégal modélisée à ≈ 790 $/EVP, 5 jours) ; préférence encore non opposable côté CEDEAO — l'avantage est logistique.",
         "<b>Thon ghanéen (Tema) → Kenya et SACU</b> : le Ghana est admis dans les cinq destinations appliquant la ZLECAf.",
         "<b>Tilapia égyptien → CAE</b> : l'Égypte figure sur la liste d'origines du Kenya (droit CAE de 25 %, réduit de 60 % en 2026)."],
 risques=["Origine du poisson : les prises de flottes étrangères sous licence ne sont pas originaires — à anticiper avant la fin de la période transitoire des conserves.",
          "Chaîne du froid, agréments sanitaires, piraterie dans le golfe de Guinée (chapitre 8)."],
 sources='FAO SOFIA 2024 ; AATM 2025 ; SaaS ZLECAf (UNIDO IDSB 2023, barèmes, registre d\'application, fret modélisé).'))

F.append(dict(num=3, sid='S03', name='Lait, œufs & miel', hs='04',
 lead="L'Afrique de l'Est est un bassin laitier de premier plan, tandis que l'Afrique du Nord et de l'Ouest dépendent de la poudre importée d'Europe : l'arbitrage continental est évident, mais la protection reste forte.",
 kp=[('55,1 Mt', 'de lait produit en 2024 (5,6 % du monde) ; Kenya 1er producteur africain', FAO), ('7,5 Md$', 'd\'importations laitières en 2023, dont 22 % pour l\'Algérie', 'Ecofin, nov. 2025'),
     ('0,76 Md$', 'de lait écrémé en poudre importé en 2024 (Égypte, Maroc, Nigeria)', 'SaaS — CEPII BACI'), ('38 %', 'plafond du droit ZLECAf SACU sur la poudre, contre 96 % au droit commun', 'SaaS — SARS Schedule 1')],
 marche=["Le Kenya (5,5 Mt de lait de vache en 2024), l'Égypte (4,8 Mt), la Tanzanie (4,1 Mt), l'Afrique du Sud (3,9 Mt) et l'Ouganda (3,85 Mt) dominent la production. "
         "Les importations (7,5 Md$) sont constituées à 76 % de poudres et de laits infantiles : Algérie 22 %, Égypte 10 %, Nigeria 9 %, Libye 8 %, Maroc 6,5 %, Sénégal 5 %.",
         "Dans les 18 pays couverts par l'UNIDO, l'industrie laitière importe 1,78 Md$ et n'exporte que 0,39 Md$ : la capacité de séchage est le goulet d'étranglement."],
 tarif="Poudre de lait (0402) : 5 % en CEMAC et en Algérie, 9 % en CEDEAO, 60,5 % au Maroc ; SACU : droit composite de 500 c/kg plafonné à 96 %, ramené à 180 c/kg plafonné à 38,4 % dans la colonne AfCFTA. "
       "Fromages (0406) : 30 % en CEMAC et en Algérie, 50 % en Tunisie. Les lignes laitières restent massivement hors liste A dans la CAE et au Maroc (marge 2026 d'environ 5 points ou moins).",
 origine="Lait (0401) : entièrement obtenu. Yaourts et fromages (0403, 0406) : jusqu'à 60 % de matières non originaires pendant 5 ans, puis lait africain obligatoire. Fromage fondu (040630) : 40 % maximum.",
 cibles=["<b>Ouganda → Égypte</b> : l'Ouganda appartient au groupe « 5 ans » égyptien (liste A à 0 %) et est déjà exportateur de poudre et d'UHT.",
         "<b>Kenya → Algérie</b> : le Kenya est l'un des 9 partenaires actifs de l'Algérie (liste A exonérée depuis 2025) ; le marché algérien importe 1,6 Md$ de laitiers par an.",
         "<b>Kenya, Ouganda → RDC, Soudan du Sud, Somalie</b> : marchés CAE en franchise communautaire, demande urbaine en forte croissance.",
         "<b>Miel éthiopien et tanzanien → Maghreb</b> : l'Éthiopie (1<super>er</super> producteur africain) figure sur la liste P1 marocaine."],
 risques=["Concurrence des poudres européennes et néo-zélandaises (FFMP) à bas prix ; offices publics d'importation (Algérie).",
          "Chaîne du froid, normes sanitaires (aflatoxine M1, résidus d'antibiotiques)."],
 sources='FAOSTAT 2024 ; Ecofin (11/2025) ; SaaS ZLECAf (BACI 2024, UNIDO IDSB 2023, SARS Schedule 1 colonnes générale et AfCFTA, registre d\'application).'))

F.append(dict(num=4, sid='S04', name='Horticulture & fleurs coupées', hs='06',
 lead="Une filière d'excellence mondiale — Kenya et Éthiopie parmi les premiers exportateurs de roses — presque entièrement tournée vers l'Europe. Le marché africain est petit mais à fort pouvoir d'achat, et désormais préférentiel.",
 kp=[('835 M$', 'exportations kényanes de fleurs en 2024 (108 Md KES)', 'Kenya Flower Council'), ('70 %', 'part de l\'Union européenne dans les recettes kényanes', 'Kenya Flower Council'),
     ('186 M$', 'exportations éthiopiennes sur 5 mois de l\'exercice 2024/25', 'Gouvernement éthiopien'), ('0 %', 'droit ZLECAf fin de calendrier en CEDEAO, CAE et CEMAC (vs 13-18 %)', 'SaaS — e-Tariff Book')],
 marche=["La filière repose sur le fret aérien depuis Nairobi et Addis-Abeba. Les volumes kényans ont reculé (≈ 102 500 t en 2024 contre 146 000 t en 2020, donnée de presse) "
         "sous l'effet des coûts de fret et de la concurrence ; les chiffres éthiopiens sont réputés surévalués. L'horticulture et les fleurs faisaient partie des produits échangés dans l'Initiative de commerce guidé.",
         "Les débouchés africains — hôtellerie, événementiel, grande distribution en Afrique du Sud, au Nigeria, en Égypte et au Maroc — offrent une diversification face à la volatilité européenne."],
 tarif="Fleurs coupées (0603) : 20 % en CEDEAO et SACU, 30 % en CEMAC et au Maroc, 35 % en CAE, 36 % en Tunisie, 3 % en Égypte. Les offres CEDEAO, CAE et CEMAC ramènent la filière à 0 % d'ici 2030 ; la Tunisie est déjà à 3 %.",
 origine="Règle : entièrement obtenu. Une fleur cultivée et récoltée dans un État partie est originaire, y compris à partir de boutures importées (produit « cultivé et récolté »).",
 cibles=["<b>Kenya, Éthiopie → Afrique du Sud</b> : les deux pays figurent parmi les 14 partenaires actifs de la SACU (colonne AfCFTA).",
         "<b>Kenya → Algérie et Maroc</b> : partenaire actif algérien (liste A à 0 %) et liste P2 marocaine (10 ans).",
         "<b>Éthiopie → Maroc</b> : liste P1 (calendrier 5 ans achevé) ; vols directs Addis–Casablanca.",
         "<b>Hub de réexportation</b> : Nairobi et Addis comme plateformes vers l'Afrique de l'Ouest dès l'ouverture des préférences CEDEAO."],
 risques=["Surcharges carburant du fret aérien (kérosène) : poste de coût dominant (chapitre 8).",
          "Dépendance au marché de l'UE et à ses exigences (résidus, due diligence) ; risque de change."],
 sources='Kenya Flower Council via Xinhua et Capital FM (02/2025) ; Xinhua (01/2025) ; FloralDaily ; tralac (GTI) ; SaaS ZLECAf (barèmes, offres, registre).'))

F.append(dict(num=5, sid='S05', name='Légumes, tubercules & légumineuses', hs='07',
 lead="L'Afrique produit les deux tiers du manioc et la quasi-totalité de l'igname du monde. La marge ZLECAf se joue moins sur le produit frais que sur la première transformation et les échanges entre communautés régionales.",
 kp=[('222,8 Mt', 'de manioc en 2024 (65,2 % du monde) ; Nigeria 1er producteur mondial', FAO), ('89,7 Mt', 'd\'igname en 2024 (97,1 % du monde)', FAO),
     ('17,0 Mt', 'd\'oignons secs en 2024 (Égypte, Niger, Algérie, Nigeria, Soudan)', FAO), ('> 58 %', 'part du Maroc dans les exportations africaines de légumes frais', 'AATM 2025')],
 marche=["Les échanges de légumes frais sont déjà intenses à l'intérieur des communautés régionales : oignons du Niger vers le Ghana, la Côte d'Ivoire et le Nigeria ; pommes de terre et oignons égyptiens ; "
         "tomates et haricots verts marocains. Au sein de la CEDEAO ou de la CAE, ces flux sont en franchise depuis longtemps : la ZLECAf n'apporte un gain tarifaire qu'entre communautés.",
         "Le potentiel réside dans la transformation : farine de manioc de haute qualité, amidon (produit échangé dans la GTI), légumineuses conditionnées."],
 tarif="Oignons (0703) : 20 % en CEDEAO, 35 % en CAE, 40 % au Maroc, 50 % en Tunisie. Légumineuses sèches (0713) : 7,5 % en CEDEAO, 27,5 % en CAE, 30 % en CEMAC, 2,5 % au Maroc. "
       "Marge 2026 : 15 points en CAE, 17 en CEMAC, 13 au Maroc.",
 origine="Règle : entièrement obtenu. Les farines de légumineuses et de tubercules (1105, 1106) exigent aussi des matières entièrement obtenues.",
 cibles=["<b>Égypte → Kenya</b> : oignons, pommes de terre, agrumes ; l'Égypte est admise par le Kenya (droit CAE de 35 % en baisse de 60 % en 2026).",
         "<b>Égypte, Tunisie → Maroc et Algérie</b> : listes P1 (Maroc) et partenaires actifs (Algérie).",
         "<b>Légumineuses éthiopiennes et tanzaniennes → Afrique du Nord</b> : Tanzanie (groupe 5 ans en Égypte, P1 au Maroc, partenaire algérien) — avantage surtout logistique, les droits NPF étant bas.",
         "<b>Manioc transformé (farine, amidon)</b> : Nigeria, Ghana → Afrique centrale et australe."],
 risques=["Pertes post-récolte élevées ; mesures phytosanitaires (nématodes, mouche des fruits).",
          "Interdictions d'exportation ponctuelles (oignons, céréales) et commerce informel dominant."],
 sources='FAOSTAT 2024 ; AATM 2025 ; tralac (GTI) ; SaaS ZLECAf (barèmes, offres, registre d\'application).'))

F.append(dict(num=6, sid='S06', name='Fruits & fruits à coque', hs='08',
 lead="Premier poste d'exportation agricole africain (15,1 Md$). La révolution de la transformation du cajou ivoirien et l'essor de l'avocat kényan déplacent la valeur vers l'aval — et vers de nouveaux marchés africains.",
 kp=[('2,58 Mt', 'de noix de cajou brutes en 2024 (60,8 % du monde)', FAO), ('≈ 600 kt', 'de noix transformées en Côte d\'Ivoire en 2025 (+67 %)', 'N\'kalô / African Cashew Alliance'),
     ('1,66 Mt', 'd\'oranges exportées par l\'Égypte en 2024/25, 1er exportateur mondial', 'FreshPlaza'), ('128 kt', 'd\'avocats exportés par le Kenya en 2024 (159 M$)', 'USDA GAIN (secondaire)')],
 marche=["La Côte d'Ivoire compte 37 unités de transformation du cajou pour 830 000 t de capacité ; ses exportations d'amandes ont atteint 72 000 t (440,5 M$) en 2024 et l'Afrique de l'Ouest a transformé 732 000 t en 2025. "
         "L'Afrique du Sud a exporté un record de 203,4 millions de cartons d'agrumes en 2025 (+22 %).",
         "Le Maroc importe 245 M$ de dattes (BACI 2024) alors que l'Égypte (1,70 Mt), l'Algérie et la Tunisie en sont de grands producteurs."],
 tarif="Agrumes (0805) : 20 % en CEDEAO, 35 % en CAE, 40 % au Maroc, 38,6 % en Égypte, 50 % en Tunisie. Dattes, avocats, mangues (0804) : 17 % en CEDEAO, 31 % en CAE, 28 % au Maroc. "
       "Amandes de cajou (080132) : catégorie A en CEDEAO et CAE, B en Égypte, C en Tunisie. Marge 2026 : 14 points en CAE, 18 en CEMAC.",
 origine="Règle : entièrement obtenu. Les fruits préparés et jus (chapitre 20, 2009) exigent également des fruits entièrement obtenus.",
 cibles=["<b>Dattes égyptiennes, algériennes, tunisiennes → Maroc</b> : les trois origines sont sur la liste P1 (calendrier 5 ans achevé) ; 245 M$ d'importations marocaines à capter.",
         "<b>Amandes de cajou ivoiriennes → Kenya et Maroc</b> : Côte d'Ivoire admise au Kenya (35 % en baisse de 60 %) et en liste P2 marocaine ; relais : Tanzanie → Maroc (liste P1).",
         "<b>Avocats kényans → Afrique du Sud, Algérie, Égypte</b> : Kenya partenaire actif de la SACU et de l'Algérie, groupe 10 ans en Égypte.",
         "<b>Agrumes égyptiens → Kenya</b> : l'Égypte est admise, le droit CAE sur les agrumes est de 35 %."],
 risques=["Exigences phytosanitaires (fausse teigne, mouches des fruits) ; prix bord champ du cajou volatils (400-425 FCFA/kg en 2025-2026).",
          "Concurrence vietnamienne dans le cajou ; transit par la mer Rouge pour les flux Est–Nord (chapitre 8)."],
 sources='FAOSTAT 2024 ; AATM 2025 ; African Cashew Alliance (02/2026) ; Ecofin (11/2025) ; FreshPlaza ; Fruitnet ; USDA GAIN ; SaaS ZLECAf (BACI 2024, barèmes, offres, registre).'))

F.append(dict(num=7, sid='S07', name='Café, thé & épices', hs='09',
 lead="Le boom des prix a fait de l'Éthiopie et de l'Ouganda des exportateurs de café à plus de 2 milliards de dollars. Le prochain gisement est africain : torréfaction régionale et thé kényan vers l'Afrique du Nord.",
 kp=[('1,18 Mt', 'de café exportées par l\'Afrique en 2024/25 (record, 19,7 M sacs)', 'OIC, via Ecofin'), ('2,65 Md$', 'exportations de café de l\'Éthiopie en 2024/25', 'ECTA, via Xinhua'),
     ('594,5 M kg', 'de thé exportés par le Kenya en 2024 ; l\'Égypte est son 2e client', 'Tea Board of Kenya'), ('8,47 $/kg', 'prix moyen de l\'arabica en 2025 (record, +87 % sur 2023)', 'Banque mondiale, Pink Sheet')],
 marche=["L'Ouganda a doublé ses recettes caféières à 2,2 Md$ en 2024/25. Le marché mondial repasse en excédent en 2025/26 (3,0 M sacs, OIC août 2026), ce qui plaide pour sécuriser des débouchés régionaux. "
         "L'Afrique du Nord est le grand consommateur continental de café et de thé ; l'Algérie exonère de TVA le café vert jusqu'à fin 2026.",
         "Le thé kényan (1<super>er</super> client : Pakistan, 34,7 % des volumes) et la vanille malgache (prix effondrés sous 20 $/kg pour les qualités basses) complètent la filière."],
 tarif="Café (0901) : 16 % en CEDEAO, 25 % en CEMAC, 30 % en Algérie, 35 % en CAE. Thé (0902) : 30 % en Algérie et en CEMAC, 35 % en CAE, 2 % en Égypte. "
       "Escalade marquée : café torréfié à 30 % au Maroc et en Algérie. Marge 2026 : 13 points en CAE, 16 en CEMAC.",
 origine="Règle : entièrement obtenu. Extraits et café soluble (2101) : café du chapitre 09 entièrement obtenu — un soluble fabriqué à partir de robusta asiatique n'est pas originaire.",
 cibles=["<b>Thé kényan → Algérie</b> : le Kenya est partenaire actif de l'Algérie (liste A à 0 % depuis 2025) face à un droit NPF de 30 %.",
         "<b>Café ougandais → Égypte, Maroc, Afrique du Sud</b> : groupe 5 ans en Égypte (0 %), liste P1 marocaine, partenaire actif SACU.",
         "<b>Café éthiopien → Maroc et SACU</b> : Éthiopie en liste P1 marocaine et partenaire actif sud-africain.",
         "<b>Torréfaction régionale</b> (Kenya, Rwanda, Tanzanie) pour les marchés urbains de la CAE et de la CEDEAO."],
 risques=["Volatilité des prix (arabica record, puis excédent 2025/26) ; règlement européen sur la déforestation qui réoriente les flux.",
          "Le thé kényan vers l'Égypte transite par la mer Rouge : surprime de guerre ou reroutage (chapitre 8)."],
 sources='OIC (CMR 08/2026) ; Ecofin ; Xinhua (06/2026) ; Tea Board of Kenya ; Banque mondiale Pink Sheet ; LF 2026 Algérie ; SaaS ZLECAf (barèmes, offres, registre).'))

F.append(dict(num=8, sid='S08', name='Céréales, minoterie & aliments du bétail', hs='10, 11, 23',
 lead="Premier poste de la facture alimentaire africaine. La substitution du blé est structurellement limitée ; les vrais leviers sont le maïs régional, la meunerie — où l'origine se gagne par la mouture — et l'alimentation animale.",
 kp=[('31,2 Md$', 'd\'importations céréalières par an (29 % des importations agricoles)', 'AATM 2025'), ('≈ 58 Mt', 'de blé importées par l\'Afrique en 2025/26 (Égypte ≈ 12,7 Mt)', 'FAO Food Outlook 06/2026 ; USDA'),
     ('15 Mt', 'de riz importées par an, 34 % des importations mondiales', 'AATM 2025'), ('−54 %', 'récolte de maïs de la Zambie en 2024 (sécheresse El Niño)', FAO)],
 marche=["Le maïs (96,3 Mt en 2024) est la céréale de l'intégration régionale : Afrique du Sud, Éthiopie, Nigeria et Tanzanie en produisent chacun plus de 10 Mt. La sécheresse de 2024 (−22 % en Afrique australe) a fait de la Tanzanie et de l'Ouganda des fournisseurs de la Zambie, du Zimbabwe et du Malawi. "
         "Le blé africain (26,1 Mt) est produit par des importateurs nets (Égypte, Éthiopie, Algérie, Maroc).",
         "Demande d'aval : 0,92 Md$ de farine importée (Soudan 252 M$, Somalie 119 M$, Madagascar, Djibouti) et 1,02 Md$ d'aliments pour animaux (BACI 2024)."],
 tarif="Blé (1001) : 5 % en CEDEAO, droit CAE réduit à 10 % au Kenya, en Ouganda et en Tanzanie et à 0 % au Rwanda et au Burundi (JO de la CAE du 30/06/2026). Riz : Kenya 35 % ou 200 $/t. "
       "Farine (1101) : 20 % en CEDEAO, 30 % en Algérie, 70 % au Maroc — et largement hors liste A (C en CEMAC et en Éthiopie, non spécifiée en CEDEAO, CAE et au Maroc).",
 origine="Céréales : entièrement obtenues. Farine de blé (1101) : changement de position — la mouture de blé importé confère l'origine (réexamen à 5 ans). Aliments du bétail (2309) : 60 % de matières non originaires pendant 3 ans.",
 cibles=["<b>Maïs tanzanien, ougandais, zambien → Kenya, Zimbabwe, Malawi</b> : la Zambie et le Malawi sont admis au Kenya ; flux CAE/SADC déjà ouverts.",
         "<b>Minoteries égyptiennes et algériennes → marchés non protégés</b> : Soudan, Somalie, Madagascar, Djibouti (0,51 Md$ de farine importée par ces quatre pays en 2024).",
         "<b>Aliments du bétail</b> (soja d'Afrique du Sud, de Zambie, du Nigeria, du Bénin + maïs) → filières volaille du Ghana, de l'Angola et du Kenya.",
         "<b>Riz</b> : Tanzanie → Kenya (franchise CAE), face à un droit extérieur de 35 %."],
 risques=["Interdictions d'exportation de maïs (Zambie, Tanzanie en 2024), aflatoxines, réexamen de la règle « farine » à 5 ans.",
          "Blé de la mer Noire : prix, primes de guerre et routes maritimes (chapitre 8) ; suspensions CAE revues chaque année."],
 sources='AATM 2025 ; FAOSTAT 2024 ; FAO Food Outlook (06/2026) et GIEWS ; USDA FAS ; Journal officiel CAE (30/06/2026, EAC/160-161/2026) ; SaaS ZLECAf (BACI 2024, barèmes, offres).'))

F.append(dict(num=9, sid='S09', name='Oléagineux & huiles végétales', hs='12, 15',
 lead="Le plus grand déficit agro-industriel du continent. Une fenêtre de trois ans des règles d'origine permet de raffiner de l'huile brute importée : c'est le moment d'investir dans le raffinage et la trituration.",
 kp=[('12,3 Md$', 'd\'importations d\'huiles et graisses par an (11,3 % du total agricole)', 'AATM 2025'), ('5,73 Md$', 'd\'huile de palme raffinée importée en 2024 (Égypte 1,18 Md$)', 'SaaS — CEPII BACI'),
     ('3,48 Mt', 'de sésame en 2024, soit 52,1 % de la production mondiale', FAO), ('7,77 Md$', 'd\'importations contre 2,21 Md$ d\'exportations d\'huiles (18 pays, 2023)', 'SaaS — UNIDO IDSB')],
 marche=["L'Afrique produit 3,54 Mt d'huile de palme (Nigeria 1,46 Mt ; Côte d'Ivoire 0,56 Mt) mais en importe l'équivalent de près de 7 Mt (estimation secondaire). "
         "Importateurs d'huile de palme raffinée : Égypte 1,18 Md$, Djibouti 505 M$, Afrique du Sud 492 M$, Togo 355 M$ ; d'huile de soja brute : Maroc 462 M$, Zimbabwe 215 M$.",
         "Le sésame (Soudan, Nigeria, Éthiopie, Tchad, Tanzanie) et l'arachide (17,0 Mt) sont exportés bruts vers l'Asie ; le soja africain a presque doublé depuis 2019."],
 tarif="Huile de palme (1511) : 5 % en CAE, 7,5 % en CEDEAO, 20 % en CEMAC, 36 % en Tunisie ; raffinée : Tanzanie 35 % ou 300 $/t, Rwanda 25 % (JO CAE 2026). "
       "Tournesol (1512) : 22,5 % en CAE, 30 % en CEMAC et en Algérie. Graines (1207) : 5 à 15 %.",
 origine="Graines : entièrement obtenues. Huiles de soja, palme, tournesol, colza (1507-1518) : jusqu'à 60 % de matières non originaires pendant 3 ans, puis entièrement obtenues sous réserve de réexamen. Margarine (1517) : changement de position.",
 cibles=["<b>Huile de palme ouest-africaine → Kenya</b> : Côte d'Ivoire, Ghana, Cameroun et Nigeria sont tous admis ; le Kenya est le 1<super>er</super> importateur africain d'huile de palme (≈ 835 kt).",
         "<b>Trituration de soja</b> (Afrique du Sud, Zambie) → Zimbabwe, Mozambique, Maroc (la Zambie est sur la liste P1 marocaine).",
         "<b>Tahini et sésame décortiqué</b> : Nigeria, Éthiopie → Égypte et Maroc.",
         "<b>Raffinage</b> au Togo et au Bénin pour le Sahel enclavé (Burkina Faso, Niger)."],
 risques=["Fin de la fenêtre VA60 : l'huile raffinée à partir de palme d'Asie cessera d'être originaire.",
          "Volatilité (huiles végétales au plus haut depuis juin 2022 en août 2026, FAO) ; taxes à l'export indonésiennes ; déforestation."],
 sources='AATM 2025 ; FAOSTAT 2023-2024 ; IndexBox (secondaire) ; FAO FPI (09/2026) ; JO CAE (30/06/2026) ; SaaS ZLECAf (BACI 2024, UNIDO IDSB 2023, barèmes, Appendice IV).'))

F.append(dict(num=10, sid='S10', name='Sucre & confiserie', hs='17',
 lead="Grande demande et double verrou : la ligne est exclue ou non libéralisée presque partout, et le sucre raffiné à partir de brut brésilien n'est pas originaire. Seul le sucre de canne africain peut circuler sous préférence.",
 kp=[('8,2 Md$', 'd\'importations de sucres et sucreries par an', 'AATM 2025'), ('8,1 Md$', 'de sucre raffiné (4,76 Md$) et brut (3,37 Md$) importés en 2024', 'SaaS — CEPII BACI'),
     ('10,9 Mt', 'de sucre brut produit en 2023 (5,8 % du monde)', 'FAOSTAT 2023'), ('785 $/t', 'nouveau prix de référence SACU (août 2026), droit porté à 4,80 ZAR/kg', 'ITAC / Global Trade Alert')],
 marche=["Producteurs : Égypte (2,85 Mt), Afrique du Sud (2,08 Mt), Eswatini (0,59 Mt, 93 % des importations sud-africaines), Ouganda, Kenya, Zambie. "
         "Importateurs de sucre raffiné : Soudan 525 M$, Libye 483 M$, Somalie 334 M$, Mauritanie 275 M$ ; de sucre brut : Maroc 950 M$, Égypte 934 M$, Nigeria 717 M$.",
         "Les raffineries d'Algérie (Cevital), du Maroc (Cosumar) et du Nigeria (Dangote, BUA) — environ 6,6 Mt de capacité cumulée — travaillent du brut importé."],
 tarif="Sucre (1701) : 16 % en CEDEAO, 30 % en CEMAC, 38 % au Maroc, 17 % en Égypte ; CAE : 100 % ou 460 $/t, avec suspensions 2026/27 (Rwanda 25 %, Burundi 0 % pour le sucre industriel, Tanzanie 35 %). "
       "Confiserie (1704) : 30 à 50 %. Sucre raffiné (170199) : exclu en CEMAC, Tunisie et Éthiopie, non spécifié en CEDEAO, CAE, Maroc, Zambie et Zimbabwe ; catégorie A en Égypte uniquement.",
 origine="Règle : entièrement obtenu, sauf 1702 et 1704 (60 % de matières non originaires maximum). Le raffinage de sucre brut importé ne confère pas l'origine ; la confiserie tolère du sucre importé dans la limite de 60 %.",
 cibles=["<b>Sucre du Malawi → Égypte</b> : le Malawi appartient au groupe « 5 ans » égyptien et le sucre raffiné (170199) est en liste A dans l'offre égyptienne — droit ramené de 17 % à 0 %.",
         "<b>Eswatini, Afrique du Sud → Égypte</b> (groupe 10 ans, −60 % en 2026) et <b>→ Kenya</b> via le quota CAE.",
         "<b>Confiserie égyptienne → Kenya</b> (Égypte admise, droit de 35 %) et <b>→ Maroc</b> (liste P1).",
         "<b>Sucre africain pour les chocolatiers ouest-africains</b> (fiche 11) : condition d'origine du chocolat."],
 risques=["Protection maximale (SACU, CAE) et exclusions ; concurrence brésilienne ; prix mondial en baisse de 28 % entre 2023 et 2025 mais rebond en 2026.",
          "Détroit d'Ormuz et coût de l'énergie pour les raffineries (chapitre 8)."],
 sources='AATM 2025 ; FAOSTAT 2023 ; USDA GAIN ; Global Trade Alert ; Bloomberg (08/2026) ; JO CAE (30/06/2026) ; SaaS ZLECAf (BACI 2024, industrial capacity, offres, Appendice IV).'))

F.append(dict(num=11, sid='S11', name='Cacao & chocolat', hs='18',
 lead="Deux pays produisent la moitié du cacao mondial et l'Afrique en broie déjà près du quart. Après le choc de prix 2024-2025, l'enjeu est de vendre du chocolat africain aux consommateurs africains.",
 kp=[('3,42 Mt', 'de fèves en 2024 (65,4 % du monde)', FAO), ('≈ 50,6 %', 'part de la Côte d\'Ivoire et du Ghana dans la production mondiale', 'ICCO, 02/2025'),
     ('1,076 Mt', 'broyées en Afrique en 2024/25 (23,1 % du monde)', 'ICCO QBCS'), ('7,80 $/kg', 'prix moyen du cacao en 2025, ×2,4 par rapport à 2023', 'Banque mondiale, Pink Sheet')],
 marche=["La Côte d'Ivoire est le premier broyeur mondial (730 kt ; capacité ≈ 1 Mt), le Ghana broie 210 kt. L'industrie cacao-chocolat-confiserie des pays couverts par l'UNIDO exporte 3,80 Md$ (Côte d'Ivoire 2,49 Md$) pour 0,60 Md$ importés. "
         "Le marché est passé d'un déficit record en 2023/24 (−494 kt) à un léger excédent en 2024/25 (+48 kt).",
         "Les cours ont culminé à ≈ 12 646 $/t en décembre 2024, sont retombés vers 2 850 $/t au printemps 2026 puis remontés vers 6 500 $/t (données de marché, secondaires)."],
 tarif="Fèves (1801) : 0 à 10 % partout sauf CEMAC (30 %). Chocolat (1806) : 35 % en CEDEAO et CAE, 30 % en CEMAC et en Algérie, 50 % en Tunisie, 19 % en SACU, 17,5 % au Maroc. "
       "Préparations au chocolat (180690) : non spécifiées en CEDEAO, exclues en CEMAC, sensibles en Égypte, Tunisie et Éthiopie.",
 origine="Règle : les matières des chapitres 17 et 18 utilisées doivent être entièrement obtenues. Un chocolat fabriqué avec du sucre brésilien perd l'origine : il faut coupler cacao ouest-africain et sucre austral ou égyptien.",
 cibles=["<b>Chocolat ghanéen → Kenya, Algérie, Afrique du Sud, Maroc</b> : le Ghana est admis dans les cinq destinations appliquant la ZLECAf.",
         "<b>Chocolat et produits semi-finis ivoiriens → Kenya et Maroc</b> (Annexe 1 kényane, liste P2 marocaine).",
         "<b>Cameroun → Algérie, SACU, Égypte</b> : le Cameroun est lui aussi admis dans les cinq destinations.",
         "<b>Libye, Maroc, Afrique du Sud</b> : 0,38 Md$ d'importations de préparations au chocolat (BACI 2024) à capter."],
 risques=["Volatilité extrême des prix ; maladie du swollen shoot et vieillissement des vergers.",
          "Règlement européen sur la déforestation ; origine du sucre ; exclusions sur le chocolat dans plusieurs offres."],
 sources='FAOSTAT 2024 ; ICCO QBCS (02/2025, 11/2025, 05/2026) ; Banque mondiale Pink Sheet ; Confectionery News ; Trading Economics ; SaaS ZLECAf (UNIDO IDSB, BACI 2024, barèmes, offres, registre).'))

F.append(dict(num=12, sid='S12', name='Produits céréaliers & préparations alimentaires', hs='19, 21',
 lead="Pâtes, biscuits, bouillons, aliments infantiles : les produits de marque sont le cœur du commerce intra-africain transformé. Les règles d'origine y sont souples et les écarts tarifaires élevés.",
 kp=[('2,37 Md$', 'de préparations alimentaires diverses (210690) importées en 2024', 'SaaS — CEPII BACI'), ('1,54 Md$', 'de préparations à base de céréales et de lait (190190)', 'SaaS — CEPII BACI'),
     ('0,81 Md$', 'de pâtes alimentaires importées (190219)', 'SaaS — CEPII BACI'), ('67 %', 'part des produits transformés et semi-transformés dans le commerce agricole intra-africain', 'AATM 2025')],
 marche=["Les importations africaines de préparations sont dispersées (Nigeria 290 M$, Égypte 264 M$, Afrique du Sud 229 M$ pour le 210690 ; Sénégal 288 M$ et Nigeria 239 M$ pour le 190190). "
         "Biscuits : 0,60 Md$ (RDC 92 M$) ; aliments infantiles : 0,67 Md$. Pâtes, farines et semoules faisaient partie des produits de l'Initiative de commerce guidé.",
         "Les grands groupes régionaux (semouleries algériennes, pastiers égyptiens et tunisiens, agro-industriels nigérians et kényans) disposent déjà des capacités."],
 tarif="Pâtes (1902) : 15 % en Égypte, 20 % en CEDEAO, 25 % en CAE, 30 % en SACU, CEMAC et Algérie, 50 % au Maroc. Biscuits (1905) : 21,7 % en SACU, 30 % en CEDEAO, 50 % en Tunisie. "
       "Marge 2026 : 10 points en CAE, 17 en Égypte, 24 en Tunisie, 6 en SACU.",
 origine="Chapitre 19 : changement de position, à condition que les produits à base de blé du chapitre 11 soient originaires — une farine moulue en Afrique à partir de blé importé suffit. Chapitre 21 : changement de position ou 60 % de valeur maximum.",
 cibles=["<b>Pâtes égyptiennes, tunisiennes, algériennes → Maroc</b> : liste P1 (calendrier 5 ans achevé) face à un droit de 50 %.",
         "<b>Mêmes origines → Afrique du Sud</b> : partenaires actifs de la SACU, droit de 30 % sur les pâtes.",
         "<b>Égypte → Kenya</b> : pâtes, biscuits, confiserie (Égypte admise, droits CAE de 25 à 35 %).",
         "<b>Nigeria → SACU, Kenya</b> : bouillons, assaisonnements, biscuits (Nigeria admis dans les deux)."],
 risques=["Étiquetage, normes nationales et enregistrement des produits (enfance) ; concurrence turque et asiatique.",
          "Prix du blé et de l'énergie ; réexamen à 5 ans de la règle « farine »."],
 sources='AATM 2025 ; tralac (GTI) ; SaaS ZLECAf (BACI 2024, barèmes, offres, registre d\'application, Appendice IV).'))

F.append(dict(num=13, sid='S13', name='Conserves de fruits & légumes', hs='20',
 lead="L'Afrique produit 14 % des tomates du monde mais achète son concentré en Chine. La règle d'origine « fruits et légumes entièrement obtenus » récompense précisément ceux qui transforment la récolte locale.",
 kp=[('≈ 70 %', 'part de la Chine dans les achats africains de concentré de tomate', 'Tomato News'), ('26,4 Mt', 'de tomates produites en 2024 (14 % du monde)', FAO),
     ('1,61 Md$', 'de fruits et légumes transformés exportés par l\'Égypte (2023)', 'SaaS — UNIDO IDSB'), ('> 61 %', 'part de l\'Afrique de l\'Ouest dans les importations africaines de concentré', 'Tomato News')],
 marche=["L'Égypte (7,5 Mt de tomates) et le Nigeria (3,7 Mt) sont de grands producteurs aux pertes post-récolte élevées ; le Nigeria dépenserait 350 à 400 M$ par an en concentré importé (chiffre non vérifié en source primaire). "
         "Exportateurs de fruits et légumes transformés : Égypte 1,61 Md$, Maroc 359 M$, Côte d'Ivoire 230 M$, Kenya 182 M$.",
         "Jus d'agrumes et conserves de fruits (Afrique du Sud, Égypte, Maroc) complètent la filière."],
 tarif="Concentré de tomate (2002) : 12,5 % en Égypte, 22,5 % en CEDEAO, 28,5 % en SACU, 30 % en CEMAC et en Algérie, 35 % en CAE, 40 % au Maroc, 50 % en Tunisie. Jus (2009) : 35 % en CAE, 50 % en Tunisie. "
       "Marge 2026 : 13 points en CAE, 11 en CEMAC, 30 en Égypte.",
 origine="Règle : tous les légumes, fruits et noix utilisés doivent être entièrement obtenus. Le reconditionnement de triple concentré chinois ne confère pas l'origine.",
 cibles=["<b>Concentré et conserves égyptiens → Maroc</b> (liste P1, droit de 40 %), <b>→ Algérie</b> (partenaire actif, 30 %), <b>→ SACU</b> (28,5 %), <b>→ Kenya</b> (35 %).",
         "<b>Jus d'orange égyptien et sud-africain → Kenya et Maroc</b>.",
         "<b>Transformation de tomate au Nigeria et au Ghana</b> pour substituer les importations chinoises (avantage d'origine vers le Kenya et la SACU).",
         "<b>Conserves de fruits sud-africaines → Égypte</b> (groupe 10 ans)."],
 risques=["Fraude au reconditionnement et contrôles d'origine renforcés ; saisonnalité et coût de l'énergie des usines.",
          "Qualité et standards (Codex, étiquetage) ; concurrence chinoise à bas prix."],
 sources='Tomato News ; HortiDaily ; FAOSTAT 2024 ; SaaS ZLECAf (UNIDO IDSB 2023, barèmes, offres, registre d\'application, Appendice IV).'))

F.append(dict(num=14, sid='S14', name='Boissons', hs='22',
 lead="Seule région du monde où la production de bière progresse, l'Afrique est un marché de marques. Les accises nationales et les exclusions pèsent plus lourd que le droit de douane.",
 kp=[('160,5 M hl', 'de bière produite en 2024 (record, +6,7 %)', 'BarthHaas 2025, via Ecofin'), ('306 M l', 'de vin sud-africain exporté en 2024 (≈ 562 M$)', 'SAWIS / WOSA'),
     ('0,81 Md$', 'd\'eaux sucrées et aromatisées importées en 2024 (RDC 164 M$)', 'SaaS — CEPII BACI'), ('1 200-3 000 %', 'droits égyptiens sur bières, vins et spiritueux', 'SaaS — barème Égypte')],
 marche=["Afrique du Sud (37 M hl), Nigeria (19,1 M hl), Angola et Éthiopie (13,7 M hl) tirent la production de bière. Le vin et les agrumes sont les deux premiers produits d'exportation agricole sud-africains.",
         "Les boissons non alcoolisées (eaux, jus, sodas) sont le segment le plus accessible aux échanges régionaux : l'Afrique importe 0,81 Md$ d'eaux sucrées (RDC 164 M$, Afrique du Sud 129 M$)."],
 tarif="Eaux sucrées (2202) : 20 % en CEDEAO, 35 % en CAE, 40 % au Maroc, 50 % en Tunisie. Bière (2203) : 5 % en SACU (plus accises), 35 % en CAE, 1 200 % en Égypte. Vin (2204) : 49 % au Maroc, 1 800 % en Égypte. "
       "La Tunisie et la SACU offrent les marges 2026 les plus nettes ; l'Égypte et le Maroc restent quasi fermés.",
 origine="Eaux (2201) et vin de palme : entièrement obtenus. Vins, vermouths et alcools (2204-2208) : changement de position et raisin entièrement obtenu. Bière sans alcool (220291) : changement de position.",
 cibles=["<b>Boissons non alcoolisées et jus égyptiens → Kenya</b> (Égypte admise, droit de 35 %).",
         "<b>Eaux et sodas → RDC</b> depuis l'Ouganda, le Kenya et la Tanzanie (marché CAE en franchise communautaire).",
         "<b>Vins sud-africains → Maroc et Algérie</b> (liste P2 et partenaire actif) sous réserve des régimes nationaux sur l'alcool.",
         "<b>Brasseries</b> : approvisionnement local en sorgho, maïs et manioc pour réduire la dépendance au malt importé."],
 risques=["Accises, licences et restrictions sur l'alcool, non couvertes par la ZLECAf ; lignes fréquemment classées en catégorie C.",
          "Coût du verre et de l'aluminium, énergie ; risque de change sur les intrants."],
 sources='BarthHaas 2025 via Ecofin ; SAWIS / Just Drinks ; AATM 2025 ; SaaS ZLECAf (BACI 2024, barèmes, offres, registre d\'application, Appendice IV).'))

F.append(dict(num=15, sid='S15', name='Tabac', hs='24',
 lead="Filière d'exportation majeure pour le Zimbabwe et le Malawi, le tabac en feuilles part surtout vers la Chine et l'Europe. Le marché africain des cigarettiers (Égypte, Kenya, Nigeria) est accessible sous préférence.",
 kp=[('0,71 Mt', 'de tabac brut en 2024 (11,7 % du monde)', FAO), ('1,3 Md$', 'd\'exportations de tabac du Zimbabwe en 2024 (record)', 'TIMB, via Equity Axis'),
     ('540 M$', 'recettes du tabac au Malawi en 2025 (record, 221 000 t)', 'Ecofin'), ('60 %', 'plafond de matières non originaires pour les cigarettes (2402)', 'Appendice IV ZLECAf')],
 marche=["Le Zimbabwe (0,24 Mt), le Malawi, la Tanzanie et le Mozambique concentrent la production. La campagne zimbabwéenne 2025 a atteint un record de 352,7 M kg (≈ 1,2 Md$). "
         "Les cigarettiers implantés en Égypte (Eastern Company), au Kenya et au Nigeria constituent les débouchés industriels africains."],
 tarif="Tabac brut (2401) : 5 % en CEDEAO, 8 % en Égypte, 17,5 % au Maroc, 35 % en CAE, 50 % en SACU. Cigarettes (2402) : 20 à 45 % selon les régimes, 116,7 % en Égypte, auxquels s'ajoutent les accises.",
 origine="Tabac brut : entièrement obtenu. Cigares, cigarettes et tabacs fabriqués (2402, 2403) : jusqu'à 60 % de matières non originaires.",
 cibles=["<b>Tabac malawite et zambien → Kenya</b> : les deux pays sont admis (droit CAE de 35 % réduit de 60 % en 2026).",
         "<b>Malawi, Tanzanie → Égypte</b> : groupe « 5 ans » égyptien (liste A à 0 %).",
         "<b>Malawi, Tanzanie, Zambie → Maroc</b> (liste P1) ; <b>Tanzanie → Algérie</b> (partenaire actif)."],
 risques=["Politiques antitabac (Convention-cadre de l'OMS), hausse des accises, contrebande ; critères ESG des financeurs.",
          "Dépendance aux acheteurs chinois ; volatilité des volumes (campagne 2026 du Malawi en retrait)."],
 sources='FAOSTAT 2024 ; Equity Axis (TIMB) ; Ecofin ; allAfrica (06/2026) ; SaaS ZLECAf (barèmes, offres, registre d\'application, Appendice IV).'))


def synth_table(sids=None):
    import json as _j
    sc = _j.load(open(S + 'scan.json')); f24 = _j.load(open(S + 'fao2024.json'))
    LAB = {'DZA|TUN': 'Algérie (std)', 'DZA|GHA': 'Algérie (récipr.)', 'KEN|GHA': 'Kenya', 'MAR|EGY': 'Maroc P1', 'MAR|GHA': 'Maroc P2', 'EGY|TUN': 'Égypte 5 ans', 'EGY|GHA': 'Égypte 10 ans', 'ZAF|GHA': 'SACU'}
    RULE = {'S01': 'Entièrement obtenu', 'S02': 'WO ; conserves ≤ 60 % (5 ans)', 'S03': 'WO ; yaourts, fromages ≤ 60 % (5 ans)', 'S04': 'Entièrement obtenu', 'S05': 'Entièrement obtenu',
            'S06': 'Entièrement obtenu', 'S07': 'WO ; solubles : café africain', 'S08': 'WO ; farine CTH ; aliments ≤ 60 %', 'S09': 'WO ; huiles ≤ 60 % (3 ans)', 'S10': 'WO ; confiserie ≤ 60 %',
            'S11': 'Cacao et sucre africains', 'S12': 'CTH (farine originaire)', 'S13': 'Fruits et légumes WO', 'S14': 'CTH ; raisin WO', 'S15': 'WO ; cigarettes ≤ 60 %'}
    rows = [['Filière', 'Production africaine (part mondiale)', 'Règle d\'origine', 'Meilleurs corridors servis (marge moy.)']]
    for f in F:
        if sids and f['sid'] not in sids:
            continue
        sid = f['sid']; x = f24.get(sid)
        prod = '—'
        if x:
            u, dv = ('Mt', 1e6) if x['total'] > 5e6 else ('kt', 1e3)
            prod = f"{x['total']/dv:,.1f} {u}".replace(',', ' ').replace('.', ',') + (f" ({100*x['total']/x['world']:.0f} %)" if x.get('world') else '') + f" — {x['year']}"
        best = sorted([(v['bysec'][sid][2], LAB[k]) for k, v in sc.items() if sid in v['bysec']], reverse=True)[:2]
        rows.append([Paragraph(f"<b>{f['num']:02d}</b> {f['name']}", TD), prod, RULE[sid], ' ; '.join(f"{n} {m:.0f} pts".replace('.', ',') for m, n in best)])
    return table(rows, [52 * mm, 40 * mm, 44 * mm, CW - 136 * mm])

def ch_fiches(sids=None, verif=False):
    """sids : sous-ensemble de filières (éditions par profil) ; verif : cibles générées depuis cibles.json (verif_cibles)."""
    sel = [f for f in F if not sids or f['sid'] in sids]
    fl = [chapter(6, f'Fiches filières : {len(sel)} secteurs, marchés et cibles'),
          P("Chaque fiche croise les données du SaaS (barèmes, offres, règles d'origine, registre d'application, demande d'importation BACI, capacités UNIDO) avec les "
            "statistiques publiques les plus récentes (FAOSTAT 2024, ICCO, OIC, Banque mondiale, AATM 2025). Les <b>cibles</b> sont formulées comme des couples « origine vers destination » "
            "où la préférence est légalement opposable en 2026, avec le taux NPF et le taux ZLECAf effectivement servis, sauf mention contraire.", LEAD),
          callout('Clé de lecture des cibles', [
              '<b>Égypte</b> : liste A seulement. Groupe « 5 ans » à 0 % depuis 2025 (Algérie, Burundi, Gambie, Lesotho, Malawi, Maroc, Maurice, Ouganda, Rwanda, Tanzanie, Tunisie) ; groupe « 10 ans » réduit de 60 % en 2026 (Afrique du Sud, Botswana, Cameroun, Eswatini, Ghana, Kenya, Namibie, Nigeria).',
              '<b>Maroc</b> : liste A seulement. P1 (5 ans, 27 origines dont Égypte, Algérie, Tunisie, Éthiopie, Sénégal, Mali, Tanzanie, Ouganda, Zambie) ; P2 (10 ans, 13 origines dont Côte d\'Ivoire, Ghana, Nigeria, Kenya, Cameroun, Afrique du Sud).',
              '<b>Kenya (CAE)</b> : barème CAE catégorie A (−60 % en 2026) pour les 28 origines de l\'Annexe 1 (CEDEAO, CEMAC, Égypte, Madagascar, Malawi, Maurice, Seychelles, Zambie, RDC).',
              '<b>SACU</b> : colonne AfCFTA pour 14 partenaires actifs. <b>Algérie</b> (9 partenaires) : calendrier standard (Égypte, Maurice, Rwanda, Tanzanie, Tunisie) — liste A à 0 % depuis 2025, liste B −20 % en 2026 ; calendrier de réciprocité (Afrique du Sud, Cameroun, Ghana, Kenya) — liste A −60 %, liste B −12,5 % en 2026 ; liste C au droit commun.'],
              bg=BLUE_L, bar=BLUE, title_color=BLUE),
          Spacer(1, 2), Paragraph(f'Tableau 6.1 — Les {len(sel)} filières en un coup d\'œil', CAP), synth_table(sids),
          Paragraph('Sources : FAOSTAT 2024 (2023 pour le sucre et l\'huile de palme) ; SaaS ZLECAf (Appendice IV ; balayage des taux servis, chapitre 7). Marge : réduction moyenne servie sur l\'ensemble des lignes de la filière.', SRC),
          PageBreak()]
    if verif:
        from ch_plans import cibles_filiere
        fl[1] = P("Chaque fiche croise les données du SaaS (barèmes, offres, règles d'origine, demande d'importation BACI) avec les statistiques publiques les plus récentes. "
                  "Les <b>cibles</b> sont générées automatiquement : un couple « origine → destination » n'est retenu que si la préférence est servie en 2026 sur les lignes nationales, "
                  "si la destination importe au moins 5 M$ par an du produit et si l'origine en exporte au moins autant (OEC/BACI 2023-2024). Les créneaux et fausses pistes sont signalés.", LEAD)
    for f in sel:
        fl += fiche(**(dict(f, cibles=cibles_filiere(f['sid'])) if verif else f))
    return fl

# --- Cibles recalculées ligne par ligne avec les calculateurs du SaaS (taux servis au 27/09/2026) ---
CIBLES = {
 'S01': ["<b>Volailles égyptiennes → Algérie</b> : morceaux congelés (0207.14) 30 % → <b>0 %</b> (liste A, calendrier standard) ; 93 % des lignes de la filière sont réduites, marge moyenne de 20 points.",
         "<b>Volailles égyptiennes → Kenya</b> : 35 % → <b>14 %</b> (barème CAE, catégorie A).",
         "<b>Viande bovine tanzanienne → Algérie</b> : liste B, 30 % → 24 % en 2026 puis 0 % en 2030.",
         "<b>Maroc</b> : viandes hors liste A (viande bovine du Botswana : 200 % maintenus) ; seule joue la suspension nationale 2026 sur 300 000 bovins, ouverte à toutes origines."],
 'S02': ["<b>Poisson ghanéen, mauritanien, égyptien → Kenya</b> : 25 % → <b>10 %</b> (thon en conserve 1604.14, poisson congelé 0303, tilapia 0302.71) ; 100 % des lignes réduites.",
         "<b>Conserves de thon marocaines → Égypte</b> : 3,75 % → <b>0 %</b> (groupe 5 ans) ; les sardines (1604.13) restent en liste B.",
         "<b>Poisson congelé sénégalais → Maroc</b> : 10 % → <b>0 %</b> (liste P1).",
         "<b>Algérie</b> : 91 % des lignes réduites (marge moyenne de 27 points pour la Tunisie) mais sardines en conserve en liste C (30 % maintenus)."],
 'S03': ["<b>Lait en poudre kényan → Algérie</b> : 5 % → 2 % (réciprocité) ; marge faible, l'enjeu est l'accès aux achats publics de poudre.",
         "<b>Fromages</b> : liste C en Algérie (30 % maintenus) et hors catégorie A au Kenya — la sous-filière la plus fermée du continent.",
         "<b>Égypte</b> : droit NPF déjà nul sur la poudre et les fromages — la concurrence y porte sur le prix et la qualité.",
         "<b>Kenya, Ouganda → RDC, Soudan du Sud, Somalie</b> : franchise communautaire CAE ; UHT et poudre."],
 'S04': ["<b>Roses tanzaniennes → Algérie</b> : 30 % → <b>0 %</b> (calendrier standard) ; <b>roses kényanes → Algérie</b> : 30 % → <b>12 %</b> (réciprocité).",
         "<b>SACU</b> : la colonne AfCFTA maintient 20 % sur les roses — aucune marge pour le Kenya ou l'Éthiopie.",
         "<b>Égypte</b> : fleurs coupées en liste B (3 % maintenus) ; <b>Maroc</b> : non servi.",
         "<b>Nigeria, Ghana</b> : préférences non encore opposables — l'avantage se joue sur le fret aérien direct."],
 'S05': ["<b>Oignons égyptiens → Kenya</b> : 35 % → <b>14 %</b> ; 99 % des lignes de légumes réduites au Kenya (marge moyenne de 18 points).",
         "<b>Pommes de terre égyptiennes → Maroc</b> : 40 % → <b>0 %</b> (liste P1).",
         "<b>Légumineuses</b> : tanzaniennes → Algérie (5 % → 0 %), éthiopiennes → Maroc (2,5 % → 0 %).",
         "<b>Algérie</b> : oignons en liste C (30 % maintenus) — cible à écarter."],
 'S06': ["<b>Amandes de cajou</b> : Côte d'Ivoire → Kenya 35 % → <b>14 %</b> ; → Maroc 10 % → 4 % (P2) ; Tanzanie → Algérie 30 % → <b>0 %</b>.",
         "<b>Avocats kényans → Algérie</b> : 30 % → <b>12 %</b> ; → SACU : 5 % → 2 %.",
         "<b>Oranges égyptiennes → Maroc</b> : 40 % → <b>0 %</b> (P1) ; au Kenya la ligne reste hors catégorie A (35 %).",
         "<b>Raisins</b> : liste C en Algérie et en Égypte — cible à écarter."],
 'S07': ["<b>Thé et café rwandais et tanzaniens → Algérie</b> : thé 30 % → <b>0 %</b>, café vert 5 % → 0 % (calendrier standard).",
         "<b>Thé kényan → Algérie</b> : 30 % → <b>12 %</b> (réciprocité) ; 100 % des lignes de la filière réduites en Algérie.",
         "<b>Café éthiopien et ougandais → Maroc</b> : 2,5 % → 0 % (P1) ; thé kényan → Maroc : 1 % (P2).",
         "<b>SACU</b> : café torréfié sous droit spécifique (2,4 c/kg) — marge négligeable."],
 'S08': ["<b>Riz et légumineuses tanzaniens → Algérie</b> : 5 % → <b>0 %</b> ; 100 % des lignes céréales/minoterie réduites.",
         "<b>Aliments du bétail tunisiens → Algérie</b> : 15 % → <b>0 %</b> (2309, liste A).",
         "<b>Farine égyptienne → Algérie</b> : liste B, 30 % → 24 % en 2026 et 0 % en 2030 ; au Kenya, la farine reste hors catégorie A.",
         "<b>Maïs zambien → Kenya</b> : ligne sensible hors barème — le commerce passe par le COMESA et les remises CAE."],
 'S09': ["<b>Huile de palme raffinée ivoirienne, ghanéenne, camerounaise → Kenya</b> : 10 % → <b>4 %</b>.",
         "<b>Tournesol tanzanien → Algérie</b> : huile 30 % → <b>0 %</b>, graines 5 % → 0 % (la Tanzanie est le 1<super>er</super> producteur africain de tournesol).",
         "<b>Sésame nigérian → SACU</b> : 7,4 % → 3 %.",
         "<b>Kenya</b> : huile de tournesol égyptienne hors catégorie A (35 % maintenus)."],
 'S10': ["<b>Sucre du Malawi → Égypte</b> : 5 % → <b>0 %</b> (groupe 5 ans) ; <b>d'Eswatini</b> : 5 % → 2 % (groupe 10 ans).",
         "<b>Algérie</b> : sucre et confiserie en liste B (30 % → 24 % en 2026, 0 % en 2030) pour la Tanzanie, Maurice et l'Égypte.",
         "<b>Kenya</b> : confiserie égyptienne hors catégorie A (35 %) ; <b>SACU</b> : aucune ligne sucre réduite.",
         "<b>Sucre africain pour les chocolatiers ouest-africains</b> (fiche 11) : condition d'origine du chocolat."],
 'S11': ["<b>Chocolat ghanéen et camerounais → Kenya</b> : 35 % → <b>14 %</b> ; <b>→ SACU</b> : 20 % → <b>8 %</b>.",
         "<b>Chocolat → Algérie</b> : liste B (30 % → 26,25 % pour le Ghana, 24 % pour l'Égypte en 2026).",
         "<b>Beurre de cacao ghanéen → Égypte</b> : 2 % → 0,8 % ; déjà à 0 % au Kenya.",
         "<b>Maroc</b> : chocolat non servi (hors liste A) — cible à reporter."],
 'S12': ["<b>Pâtes et biscuits égyptiens et tunisiens → Maroc</b> : <b>0 %</b> (liste P1) face à des droits de 21 à 50 %.",
         "<b>Biscuits égyptiens → Kenya</b> : 35 % → <b>14 %</b> ; <b>bouillons nigérians</b> → Kenya 25 % → 10 %, → SACU 20 % → 8 %.",
         "<b>Algérie</b> : pâtes et biscuits en liste B (30 % → 24 % en 2026).",
         "<b>Pâtes égyptiennes</b> : hors catégorie A au Kenya et sans réduction en SACU (40 %)."],
 'S13': ["<b>Concentré de tomate égyptien → Kenya</b> : 35 % → <b>14 %</b> ; en revanche : hors liste A au Maroc, liste C en Algérie, 37 % maintenus en SACU.",
         "<b>Jus d'orange égyptien → Kenya</b> : 35 % → <b>14 %</b> ; → Algérie : 15 % → 12 % (liste B).",
         "<b>Jus sud-africain → Égypte</b> : 17 % → 6,8 % (groupe 10 ans).",
         "<b>Égypte (groupe 5 ans)</b> : 85 % des lignes de conserves réduites, marge moyenne de 14 points."],
 'S14': ["<b>Boissons non alcoolisées égyptiennes → SACU</b> : 21 % → <b>8,4 %</b> (2202.99) ; 85 % des lignes de boissons réduites en SACU.",
         "<b>Kenya</b> : eaux sucrées hors catégorie A (35 %) ; <b>Maroc</b> : non servi.",
         "<b>Vins sud-africains → Égypte</b> : liste C (1 800 %) — marché fermé.",
         "<b>Eaux et sodas → RDC</b> depuis l'Ouganda, le Kenya et la Tanzanie (franchise communautaire CAE)."],
 'S15': ["<b>Tabac zambien et malawite → Kenya</b> : 35 % → <b>14 %</b>.",
         "<b>Tabac du Malawi → Maroc</b> : 17,5 % → <b>0 %</b> (liste P1).",
         "<b>Égypte</b> : tabac brut en liste C ; <b>SACU</b> : droit composite (6 % ou 344 c/kg moins 34 %).",
         "<b>Kenya</b> : 77 % des lignes de la filière réduites, marge moyenne de 16 points."],
}
for f in F:
    f['cibles'] = CIBLES[f['sid']]
    f['tarif'] = f['tarif'].replace('Marge 2026', 'Marge théorique 2026 (offres publiées)').replace('La marge ZLECAf 2026', 'La marge théorique 2026 (offres publiées)').replace('La marge 2026', 'La marge théorique 2026 (offres publiées)')
