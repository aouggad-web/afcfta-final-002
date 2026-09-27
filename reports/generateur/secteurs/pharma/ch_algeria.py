from layout import *
import json
C = S + 'charts/'
CA = json.load(open(S + 'cases.json'))
DM = json.load(open(S + 'demand.json'))
SP = json.load(open(S + 'saas_pharma.json'))['countries']
def f1(x): return '—' if x is None else (f'{x:.1f}'.replace('.', ','))
def fm(x): return f'{x:,.0f}'.replace(',', ' ')

def ch_algeria():
    fl = [chapter(8, 'Focus Algérie : de la substitution à l\'export'),
          P("En quinze ans, l'Algérie est passée d'une couverture de 40 % à <b>83 % de ses besoins en médicaments</b> par la production locale, et sa facture "
            "d'importation a été divisée par quatre depuis 2019. La question stratégique n'est plus « produire pour le marché national » mais "
            "« exporter vers un continent qui importe 9 milliards de dollars de médicaments dosés par an ». Ce chapitre chiffre les leviers "
            "et les obstacles, avec les outils du SaaS (calculateur fiscal DGD, barèmes ZLECAf, module Opportunités, sous-module « Algérie · industrie et marchés »).", LEAD)]
    fl.append(kpis([('83 %', 'couverture des besoins en médicaments par la production nationale (fin 2025)', 'ANPP, 22/02/2026 ; projet de politique pharmaceutique nationale, août 2026 (82 %)'),
                    ('233', 'établissements de production pharmaceutique, dont 138 fabriquent des médicaments', 'Ministère de l\'Industrie pharmaceutique, nov. 2025'),
                    ('515 M USD', 'importations de médicaments en 2024 (2 000 M USD en 2019)', 'Horizons, 01/02/2026'),
                    ('23,3 M USD', 'exportations de médicaments dosés en 2024, dont 18,8 % vers l\'Afrique', 'BACI via SaaS (dza_filieres.json)')], cols=4))
    fl.append(figure(C + 'a1_dza_imp.png', 'Figure 8.1 — Substitution aux importations : facture d\'import et taux de couverture locale',
                     'Sources : Horizons (01/02 et 19/06/2026), ANPP (22/02/2026). *2025 : ordre de grandeur cité par la presse, pas de chiffre définitif des Douanes.', maxh=62 * mm))
    fl.append(h2('8.1 Une base industrielle devenue significative'))
    rows = [['Acteur', 'Statut', 'Capacité ou fait marquant', 'Source'],
            ['Saidal', 'Public', '144 M d\'unités de vente produites en 2025 ; exporte vers 10 pays (Tunisie, Libye, Mauritanie, Sénégal, Tchad, Mali, Burkina Faso…) ; ~220 produits ciblés en Mauritanie ; accord de 100 M USD avec un groupe nigérian (IATF 2025)', 'SaaS dza_filieres ; La Voie d\'Algérie'],
            ['Saidal (suite)', 'Public', 'Accords de fabrication avec Boehringer Ingelheim (fibrose pulmonaire, 08/06/2026) et Novo Nordisk (GLP-1, 30/06/2026) ; relance de l\'unité de solvants de Médéa après 20 ans d\'arrêt ; 6e fabricant africain, CA estimé à 320-360 M USD', 'Algérie Eco ; Just-InfoDZ, 24/09/2026 ; Maghreb Emergent, 27/09/2026'],
            ['Biopharm', 'Privé', '65,8 M de boîtes produites en 2024 ; 7e fabricant africain (CA estimé à 300-350 M USD)', 'Rapport annuel 2024 ; Maghreb Emergent, 27/09/2026'],
            ['Novo Nordisk (Boufarik, Tizi Ouzou)', 'Filiale', '17 M de stylos à insuline en 2023 (capacité 45 M) ; 2,5 M de stylos exportés vers l\'Arabie saoudite en 2024', 'SaaS dza_filieres ; Algérie Eco'],
            ['Biothéra (Biocare Biotech)', 'Privé', '10 M de boîtes de 5 stylos d\'insuline glargine par an (capacité) ; protocole d\'export d\'insulines vers le tunisien Dorcas (20/05/2026)', 'MIPH ; Esseha, 22/05/2026'],
            ['Frater-Razes et Sanofi', 'Privé', 'Transfert technologique complet pour des insulines de nouvelle génération ; l\'insuline importée coûtait ~420 M EUR par an', 'Maghreb Emergent, 30/04/2026'],
            ['Hikma Pharma Algérie', 'Filiale', '5 sites dont injectables (Staouéli) et oncologie', 'Algérie Eco, 17/06/2025'],
            ['Sanofi (Sidi Abdellah)', 'Filiale', 'Plus de 100 M d\'unités par an, premier site du groupe en Afrique', 'L\'Usine Nouvelle'],
            ['El Kendi (MS Pharma), Frater-Razes, Merinal', 'Privés', 'Objectif d\'export de 5 M USD en 2026 (El Kendi) ; présence déclarée dans 22 pays (Frater-Razes)', 'APS ; Esseha']]
    fl.append(Paragraph('Tableau 8.1 — Principaux industriels', CAP))
    fl.append(table(rows, [34 * mm, 15 * mm, 90 * mm, 35 * mm]))
    fl.append(Paragraph('Sources : SaaS, sous-module « Algérie · industrie et marchés » (fiches SH 3004), complété par la presse économique algérienne. Chiffres d\'entreprise non audités par nos soins.', SRC))
    fl.append(P("<b>Annonces et réalisations : lire la presse avec méthode.</b> Le nombre d'usines varie de 178 (liste officielle d'agréments, déc. 2025) à 200 (L'Algérie Aujourd'hui, 16/04/2026), "
                "218 (El Watan, 08/09/2025), 233 (ministre, nov. 2025) et « environ 250 » (Horizons, 14/07/2026) ; le taux de couverture de 79 à 83 %. Les exportations pharmaceutiques 2024 sont de "
                "<b>23,3 M USD selon BACI</b> (médicaments dosés) et de <b>46 M USD selon El Watan (08/09/2025) et Horizons (19/06/2026)</b>, qui retiennent un périmètre plus large ; aucun chiffre 2025 n'est publié. "
                "En face, les annonces sont d'un autre ordre : 400 M USD de contrats pharmaceutiques « attendus » à l'IATF 2025 (El Watan), 11,4 Md USD d'accords algériens tous secteurs selon Afreximbank "
                "(Le Jeune Indépendant, 06/09/2026). Les calendriers glissent : le niveau 3 de l'OMS, « attendu en octobre 2025 » (El Watan), est désormais en évaluation depuis septembre 2026 ; les usines de vaccins "
                "d'Annaba et d'anticancéreux de Constantine sont repoussées à fin 2027, et Saidal a nommé un second directeur général le 14/07/2026 pour « rattraper les retards » (Le Matin d'Algérie, 16/08/2026 ; "
                "Algérie Eco, 14/07/2026). <b>Nos calculs retiennent les chiffres réalisés, jamais les annonces.</b>"))
    fl.append(PageBreak())
    fl.append(h2('8.2 Le régime à l\'importation : ce que la ZLECAf change pour l\'industriel algérien'))
    fl.append(P("Toutes les lignes de santé étudiées sont en <b>liste A</b> de la circulaire DGD 482/2024 : droit nul en 2026 pour les origines du calendrier standard (Égypte, Maurice, "
                "Rwanda, Tanzanie, Tunisie), réduit de 60 % pour les partenaires en réciprocité (Afrique du Sud, Cameroun, Ghana, Kenya). Le <b>DAPS</b> (30 % sur les flacons plastiques et "
                "le mobilier médical) est levé pour les produits originaires des partenaires."))
    fl.append(P("Le cadre administratif pèse autant que la fiscalité. Au printemps 2026, 52 médicaments étaient en tension (La Nouvelle République, 06/04/2026) et le ministre a donné de 48 heures à 5 jours "
                "aux fabricants et importateurs pour libérer leurs stocks, sous peine de retrait d'agrément (TSA, 04/04/2026) ; le média relie ce risque à l'instabilité au Moyen-Orient. La plateforme des programmes "
                "prévisionnels d'importation a rouvert pour le second semestre du 23/06 au 31/07/2026 (TSA, 23/06/2026). Enfin, l'ANPP propose de plafonner l'enregistrement à trois génériques et deux biosimilaires "
                "par spécialité, ce que l'association des producteurs (SAARPE) juge porteur de monopoles et de désinvestissement (TSA, 14/09/2026)."))
    rows = [['Produit (SH)', 'DD NPF', 'Charge NPF hors TVA', 'ZLECAf standard', 'ZLECAf réciprocité', 'Commentaire'],
            ['Antibiotiques en vrac (2941.90)', '15 %', '17,0 %', '2,0 %', '8,0 %', 'Intrant clé ; plus taxé que le médicament fini'],
            ['Médicaments dosés (3004.90)', '5 %', '7,0 %', '2,0 %', '4,0 %', 'Importation encadrée : programme prévisionnel, interdiction des produits fabriqués localement'],
            ['Insuline dosée (3004.31)', '5 %', '7,0 %', '2,0 %', '4,0 %', 'Production locale (Boufarik, Biothéra)'],
            ['Seringues (9018.31)', '30 %', '32,0 %', '2,0 %', '14,0 %', 'Forte protection des producteurs locaux'],
            ['Cathéters, perfusion (9018.39)', '30 %', '32,0 %', '2,0 %', '14,0 %', 'Voir le cas mauricien (§ 7.7)'],
            ['Gants chirurgicaux (4015.12)', '30 %', '35,0 %', '5,0 %', '17,0 %', 'TCS 3 % maintenue'],
            ['Réactifs de diagnostic (3822.19)', '5 %', '10,0 %', '5,0 %', '7,0 %', ''],
            ['Flacons plastiques (3923.30)', '30 % + DAPS 30 %', '65,0 %', '5,0 %', '17,0 %', 'DAPS levé sous ZLECAf'],
            ['Flacons verre ≤ 0,15 l (7010.90)', '15 %', '20,0 %', '5,0 %', '11,0 %', 'Conditionnement des injectables'],
            ['Lits médicaux (9402.90)', '30 % + DAPS 30 %', '65,0 %', '5,0 %', '17,0 %', 'DAPS levé sous ZLECAf']]
    fl.append(Paragraph('Tableau 8.2 — Charge fiscale à l\'importation en Algérie, en % de la valeur CAF, septembre 2026', CAP))
    fl.append(table(rows, [36 * mm, 20 * mm, 20 * mm, 19 * mm, 20 * mm, 59 * mm], align_right_from=1))
    fl.append(Paragraph('Source : SaaS ZLECAf, calculateur fiscal algérien (relevé DGD, LF 2026, circulaire 482/2024 ; compute_dza_zlecaf_rate, daps_exempt). Charge hors TVA = DD + DAPS + PRCT (2 %) + TCS (3 %, si applicable). '
                        'TVA exclue : récupérable pour un industriel assujetti ; les médicaments à usage humain bénéficient en principe d\'une exonération (le relevé affiche 9 % sur les lignes vétérinaires). '
                        'Réciprocité : DD réduit de 60 % en 2026.', SRC))
    fl.append(h2('8.3 Hypothèse de travail n° 1 : la protection effective négative'))
    fl.append(P("Le taux de protection effective (TPE) mesure la protection de la <b>valeur ajoutée</b> d'un producteur, et non celle du prix : TPE = (t<sub>produit</sub> − a × t<sub>intrant</sub>) / (1 − a), "
                "où <i>a</i> est la part de l'intrant importé dans le prix du produit. Avec 7 % de charge sur le médicament fini et 17 % sur l'API importé hors ZLECAf :"))
    rows = [['Part de l\'API dans le prix (a)', 'API hors ZLECAf (17 %)', 'API ZLECAf réciprocité (8 %)', 'API ZLECAf standard (2 %)']]
    for e in CA['erp']:
        rows.append([f"{int(e['a'] * 100)} %", f1(e['npf']) + ' %', f1(e['rcp']) + ' %', f1(e['std']) + ' %'])
    fl.append(Paragraph('Tableau 8.3 — Protection effective de la formulation locale selon l\'origine de l\'API', CAP))
    fl.append(table(rows, [52 * mm, 40 * mm, 42 * mm, 40 * mm], align_right_from=1))
    fl.append(Paragraph('Calcul : ZLECAf Trade Intelligence, sur les charges hors TVA du tableau 8.2. Hypothèse simplificatrice : un seul intrant importé ; les emballages (20 à 65 % de charge) aggravent le résultat.', SRC))
    fl.append(P(f"<b>Lecture.</b> Pour les produits où l'API pèse la moitié du prix (antibiotiques injectables, génériques de spécialité), le formulateur algérien est <b>moins protégé que l'importateur "
                f"du produit fini (TPE de −3 % à −8 %)</b>. S'approvisionner en API d'origine ZLECAf retourne la situation : la TPE monte à +12 à +15 %. En prix, un API originaire d'un partenaire du calendrier standard "
                f"peut coûter jusqu'à <b>{f1(CA['be_std'])} % de plus</b> que l'API indien ou chinois avant de perdre son avantage ({f1(CA['be_rcp'])} % pour un partenaire en réciprocité). "
                "Deux correctifs existent hors ZLECAf : le régime de <b>perfectionnement actif</b> (suspension des droits sur les intrants réexportés) et une révision du tarif des API, qui relève de la loi de finances."))
    fl.append(P("<b>Une escalade à rebours peut-être assumée.</b> L'Algérie importe 98 % de ses principes actifs (Maghreb Emergent, 30/04/2026) et environ 3 Md USD de matières premières pharmaceutiques "
                "par an ; le gouvernement vise 2,7 Md USD d'économies d'ici 2028 grâce à onze unités, dont cinq de Saidal en construction (Observ'Algérie, 08/04/2026). L'unité de solvants de Médéa, qui produit "
                "l'acétate de butyle nécessaire à la pénicilline G, a redémarré en septembre (Just-InfoDZ, 24/09/2026), et un mémorandum prévoit d'exporter vers la Tunisie des matières premières pour le paracétamol "
                "et les antibiotiques (Algérie Eco, 03/02/2026). Le droit de 15 % sur les API protège donc aussi une filière chimique naissante. Le dilemme est réel : chaque point de protection des futurs "
                "producteurs d'API est payé par les formulateurs d'aujourd'hui. La ZLECAf permet de le desserrer sans toucher au tarif NPF, en admettant à 0 % les API des partenaires africains."))
    fl.append(PageBreak())
    fl.append(h2('8.4 Les marchés d\'exportation : où la demande et la préférence se rencontrent'))
    imp = DM['imp300490']
    FR = {'EGY': 'Égypte', 'ZAF': 'Afrique du Sud', 'MAR': 'Maroc', 'KEN': 'Kenya', 'NGA': 'Nigeria', 'TUN': 'Tunisie', 'CIV': 'Côte d\'Ivoire', 'LBY': 'Libye', 'UGA': 'Ouganda', 'GHA': 'Ghana',
          'TZA': 'Tanzanie', 'SEN': 'Sénégal', 'ZMB': 'Zambie', 'CMR': 'Cameroun'}
    SERV = {'EGY': ('0', 'oui (5 ans)'), 'ZAF': ('0', 'oui (réciprocité)'), 'MAR': ('0 (P1)', 'oui (P1)'), 'KEN': ('0 (NPF)', 'non (hors annexe 1)'), 'NGA': ('0 (NPF)', 'offre seule'),
            'TUN': ('0 (NPF)', 'offre seule'), 'CIV': ('0 (NPF)', 'offre seule'), 'LBY': ('n.d.', 'non ratifiée'), 'UGA': ('0 (NPF)', 'non appliquée'), 'GHA': ('0 (NPF)', 'offre seule'),
            'TZA': ('0 (NPF)', 'non appliquée'), 'SEN': ('0 (NPF)', 'offre seule'), 'ZMB': ('n.d.', 'offre seule'), 'CMR': ('5 (NPF)', 'offre seule')}
    GAFI = {'KEN': 'liste grise', 'CIV': 'liste grise', 'CMR': 'liste grise'}
    rows = [['Marché', 'Import. 2024 (M USD)', 'Part Algérie', 'Droit NPF médic.', 'Droit servi (orig. DZA)', 'Application ZLECAf', 'GAFI (juin 2026)']]
    for r in imp[:14]:
        iso = r[0]; c = SP.get(iso)
        rows.append([FR.get(iso, r[1]), fm(r[2] / 1e6), (f1(r[4]) + ' %') if r[4] else '0 %', ('4,9 % (≤ 25 %)' if iso == 'MAR' else ((f1(c['groups']['G04']['avg']) + ' %') if c else 'n.d.')), SERV[iso][0], SERV[iso][1], GAFI.get(iso, '—')])
    fl.append(Paragraph('Tableau 8.4 — Quatorze premiers marchés africains des médicaments dosés (SH 3004.90) et accès pour l\'origine Algérie', CAP))
    fl.append(table(rows, [26 * mm, 22 * mm, 18 * mm, 22 * mm, 26 * mm, 34 * mm, 26 * mm], align_right_from=1))
    fl.append(Paragraph('Sources : BACI (CEPII) via le module Opportunités du SaaS (dza_commerce_baci.json, importations des pays africains, hors Algérie) ; barèmes et calculateurs du SaaS ; GAFI (plénière de juin 2026). '
                        'Maroc : droit NPF moyen de l\'offre (4,9 %, jusqu\'à 25 %). « Offre seule » : offre déposée à l\'UA, sans liste d\'origines admises vérifiée.', SRC))
    fl.append(P("<b>Trois constats.</b> (i) La demande africaine de médicaments dosés atteint <b>9,0 Md USD en 2024</b> (SH 3004.90 seul), concentrée à 60 % sur six marchés ; l'Algérie en détient "
                "une part infime. (ii) Sur les marchés où la ZLECAf s'applique, la préférence n'apporte une marge qu'au <b>Maroc</b>, marché fermé de fait par la rupture diplomatique de 2021. "
                "(iii) Partout ailleurs, l'Algérie concourt à armes tarifaires égales avec l'Inde : la compétitivité se jouera sur le coût rendu, le délai, l'enregistrement et le financement."))
    fl.append(P("<b>Ce que révèlent les contrats signés.</b> La presse dessine une géographie de proximité, cohérente avec notre matrice de risque (chapitre 9). "
                "<b>Mauritanie</b> : cinq contrats de 10 M USD avec le distributeur King Pharma et ses filiales au Mali et au Sénégal (Algérie Eco, 29/11/2025), accord Saidal-Chinguitty Pharma (Maghreb Emergent, 24/05/2025), "
                "27 accords à la foire de Nouakchott, où le ministre mauritanien de la Santé s'est engagé à débloquer les enregistrements en retard de Saidal (Algérie Patriotique, 08/05/2026 ; Le Jour d'Algérie, 05/2026). "
                "<b>Libye</b> : appel d'offres de 950 M EUR pour l'importation de médicaments, auquel le ministère invite les producteurs algériens (L'Algérie Aujourd'hui, 16/04/2026). "
                "<b>Niger</b> : mémorandum ANPP-agence nigérienne en finalisation et étude d'unités de production au Niger (Horizons, 24/03/2026), groupe de travail Saidal-ambassade (Algérie Patriotique, 02/09/2026). "
                "<b>Tunisie</b> : export d'insulines Biocare vers Dorcas (Esseha, 22/05/2026). <b>Égypte</b> : mémorandum ANPP-EDA ouvrant la voie à une reconnaissance mutuelle (L'Écho d'Algérie, 15/06/2026). "
                "Point commun : <b>le levier est réglementaire (enregistrement) et commercial (distributeur local), jamais tarifaire</b>, ce que confirment nos calculs."))
    fl.append(figure(C + 'p3_demand.png', 'Figure 8.2 — Importations africaines de médicaments dosés (SH 3004.90), 2024, M USD',
                     'Source : BACI (CEPII) via le SaaS, module Opportunités. Six premiers marchés en couleur foncée.', maxh=66 * mm))
    fl.append(PageBreak())
    fl.append(h2('8.5 Cas chiffré : génériques algériens contre génériques indiens à Dakar'))
    c = CA['c2']
    fl.append(P("Hypothèses : conteneur de 40' de génériques secs (comprimés, gélules) d'une valeur FOB de 300 000 USD ; droit NPF sénégalais nul pour les deux origines (TEC CEDEAO, catégorie 0) ; "
                "coût du capital de l'importateur de 12 % par an ; stock de sécurité égal à la moitié du délai de transit. L'hypothèse d'une desserte maritime régulière Alger-Dakar s'appuie sur les nouvelles "
                "lignes CNAN et GATMA vers Nouakchott et Dakar (Horizons, 19/03/2026) ; Air Algérie Cargo dessert Nouakchott, Dakar et N'Djamena, avec un fret aérien en hausse de plus de 25 % en 2025 (Algérie Eco, 10/04/2026)."))
    rows = [['Poste', 'Inde (Nhava Sheva → Dakar)', 'Algérie (Alger → Dakar)', 'Écart'],
            ['Fret maritime, surcharges 2026 comprises', f"{fm(c['ind']['freight'])} $", f"{fm(c['dza']['freight'])} $", f"{fm(c['ind']['freight'] - c['dza']['freight'])} $"],
            ['Délai de transit, jours (stock de sécurité)', '32 (16)', '12 (6)', '−20 (−10)'],
            ['Assurance transport (0,35 % / 0,25 %)', f"{fm(c['ind']['ins'])} $", f"{fm(c['dza']['ins'])} $", f"{fm(c['ind']['ins'] - c['dza']['ins'])} $"],
            ['Portage financier du stock en transit et de sécurité', f"{fm(c['ind']['fin'])} $", f"{fm(c['dza']['fin'])} $", f"{fm(c['ind']['fin'] - c['dza']['fin'])} $"],
            ['Droits de douane (NPF = ZLECAf)', '0 $', '0 $', '0 $'],
            ['<b>Total des coûts de rendu hors prix</b>', f"<b>{fm(c['ind']['total'])} $</b>", f"<b>{fm(c['dza']['total'])} $</b>", f"<b>{fm(c['adv'])} $ ({f1(c['adv_pct'])} %)</b>"]]
    fl.append(Paragraph('Tableau 8.5 — Coût rendu Dakar d\'un conteneur de génériques', CAP))
    fl.append(table(rows, [64 * mm, 38 * mm, 38 * mm, 34 * mm], align_right_from=1))
    fl.append(Paragraph('Hypothèses : fret Inde → Afrique de l\'Ouest 2026 de l\'ordre de 3 000 à 4 000 USD par conteneur de 40\' (transitaires), plus surcharges de conflit et de carburant ; Alger → Dakar modélisé par le SaaS '
                        '(logistics_fees_data, 955 USD par EVP, soit ×1,5 pour un 40\') avec transbordement. Calcul : ZLECAf Trade Intelligence.', SRC))
    rows = [['Fret Inde → Dakar (USD / 40\')', 'Transit 25 j', 'Transit 32 j', 'Transit 40 j']]
    for f, r in CA['c2_sens']:
        rows.append([fm(f)] + [f1(x) + ' %' for x in r])
    fl.append(Paragraph('Tableau 8.6 — Sensibilité : avantage de coût rendu de l\'origine Algérie (% de la valeur FOB)', CAP))
    fl.append(table(rows, [64 * mm, 36 * mm, 36 * mm, 38 * mm], align_right_from=1))
    fl.append(P(f"<b>Conclusion.</b> La proximité vaut <b>1,3 à 3 % de la valeur</b> : c'est l'écart de prix FOB maximal que le génériqueur algérien peut se permettre face à l'Inde, à tarif égal. "
                f"L'avantage triple pour un conteneur de 100 000 USD ({f1(CA['c2_V'][0][1])} %) et se dilue à {f1(CA['c2_V'][2][1])} % pour 600 000 USD : il est décisif sur les produits "
                "volumineux et à faible valeur (solutés, sirops, pansements, consommables), marginal sur les spécialités. Or les génériques indiens sont souvent 20 à 40 % moins chers : "
                "<b>la proximité ne compense pas un écart de prix industriel</b>. Elle se valorise surtout en fiabilité (délais courts, réassort, moindre exposition aux crises maritimes de 2026)."))
    fl.append(PageBreak())
    fl.append(h2('8.6 Contraintes financières et de conformité'))
    rows = [['Dimension', 'Situation au 27/09/2026', 'Effet pour l\'exportateur'],
            ['GAFI', 'Sortie de la liste grise le <b>19/06/2026</b> (inscrite en oct. 2024)', 'Allègement progressif des diligences bancaires ; argument commercial auprès des centrales d\'achat'],
            ['Liste UE des pays à haut risque', 'Inscription par le règl. délégué (UE) 2025/1184 ; retrait non confirmé', 'Diligences renforcées maintenues par les banques européennes (financement, confirmation de crédits documentaires)'],
            ['Rapatriement des recettes', 'Règl. Banque d\'Algérie 26-02 du 23/07/2026 : <b>120 jours</b> (180 avec assurance-crédit CAGEX), contre 360 auparavant', 'Incompatible avec les délais de paiement publics africains (90 à 180 jours) sans assurance-crédit'],
            ['Disposition des devises', 'Instruction 06-2021 : 100 % des recettes hors hydrocarbures à disposition de l\'exportateur (maintien sous 26-02 à confirmer)', 'Permet de financer les intrants importés'],
            ['Assurance-crédit', 'CAGEX : couverture obligatoire entre 120 et 180 jours (Algérie Eco, 23/08/2026) ; engagements > 46 Md DA, dont 15 % en Afrique ; mémorandums avec COTUNACE, ECIC et SONAC', 'La prime doit être intégrée au prix export'],
            ['Réseau bancaire', 'Algerian Union Bank (Nouakchott, 3 agences), Algerian Bank of Senegal (Dakar) ; succursale au Niger demandée pour fin 2026-début 2027, Côte d\'Ivoire envisagée (L\'Express DZ, 10/05/2026)', 'Encaissement local ; commerce Algérie-Mauritanie d\'environ 500 M USD par an'],
            ['Zones franches', 'Loi 22-15 ; zone franche commerciale de Tindouf (décret 24-169), réception attendue en 2026', 'Plateforme vers la Mauritanie ; zones prévues avec la Tunisie, la Libye, le Mali et le Niger non créées'],
            ['Régulation', 'Évaluation OMS « niveau de maturité 3 » de l\'ANPP à partir de sept. 2026', 'Condition des procédures accélérées d\'enregistrement dans les pays tiers'],
            ['Importations', 'Suspension des nouveaux agréments d\'importation (23/04/2026)', 'Aucune (export) ; freine les partenariats d\'import-substitution croisés']]
    fl.append(Paragraph('Tableau 8.7 — Environnement financier et réglementaire de l\'exportateur pharmaceutique algérien', CAP))
    fl.append(table(rows, [30 * mm, 76 * mm, 68 * mm]))
    fl.append(Paragraph('Sources : GAFI ; Commission européenne (IP/25/1378) ; Banque d\'Algérie (règl. 26-02, instr. 06-2021) ; CAGEX (27/03/2026) ; APS ; Ministère des Finances ; décret 24-169 ; L\'Algérie Aujourd\'hui (07/06/2026) ; Algérie Eco (25/04/2026).', SRC))
    fl.append(h2('8.7 Scénarios 2027 pour les exportations pharmaceutiques'))
    rows = [['Scénario', 'Hypothèses', 'Exportations 2027 (ordre de grandeur)'],
            ['Tendanciel', 'Croissance 2023-2024 amortie ; Arabie saoudite et Maghreb dominants ; pas de niveau 3 OMS', '30 à 50 M USD'],
            ['Africain', 'Niveau 3 OMS obtenu ; enregistrements accélérés en Afrique de l\'Ouest (Mauritanie, Sénégal, Mali via l\'axe Tindouf) ; contrats IATF exécutés à 20 %', '80 à 150 M USD'],
            ['Intégré ZLECAf', 'Scénario africain + API d\'origine africaine, perfectionnement actif, assurance-crédit généralisée, présence dans les appels d\'offres groupés', '150 à 250 M USD']]
    fl.append(Paragraph('Tableau 8.8 — Scénarios d\'exportation', CAP))
    fl.append(table(rows, [26 * mm, 106 * mm, 42 * mm]))
    fl.append(Paragraph('Scénarios construits par ZLECAf Trade Intelligence : ce sont des ordres de grandeur conditionnels, pas des prévisions. Base 2024 : 23,3 M USD (BACI), 46 M USD selon la presse (périmètre large). Intentions IATF 2025 annoncées : plus de 725 M USD, non ventilées.', SRC))
    return fl
