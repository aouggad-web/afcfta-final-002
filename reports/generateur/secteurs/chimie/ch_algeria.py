from layout import *
import json
C = S + 'charts/'
CA = json.load(open(S + 'cases.json'))
FAP = json.load(open(S + 'fap.json'))
H = json.load(open(S + 'oec_hs6.json'))
def f1(x): return '—' if x is None else (f'{x:.1f}'.replace('.', ','))
def fm(x): return f'{x:,.0f}'.replace(',', ' ')
def last(k, fld):
    r = H.get(k, {}).get('chart_rows', [])
    return r[-1][fld] / 1e6 if r else 0

def ch_algeria():
    fl = [chapter(7, 'Focus Algérie'),
          P("L'Algérie exporte plus d'un milliard de dollars d'urée, un demi-milliard d'hélium et d'ammoniac, mais moins de 2 M USD de cosmétiques et de détergents. "
            "Elle importe pour près de 3 Md USD de plastiques et 300 M USD de compositions parfumantes. Ce chapitre fait l'inventaire de l'appareil de production, "
            "décrit le système algérien d'importation (programmes prévisionnels, autorisations, DAPS), chiffre l'effet de la ZLECAf et oriente vers l'export.", LEAD)]
    fl.append(kpis([('1 383 M$', 'valeur ajoutée 2024 de la branche chimie, caoutchouc et plastiques (+4,5 % en volume)', 'ONS, comptes économiques 2021-2024 (n° 1067), via SaaS dza_industrie'),
                    ('66 %', 'part du secteur public dans cette valeur ajoutée (2024)', 'ONS, via SaaS'),
                    ('1 024 M$', 'exportations d\'urée en 2024, dont 0,7 % vers l\'Afrique', 'BACI via SaaS (dza_filieres)'),
                    ('2,98 Md$', 'importations de matières et produits plastiques en 2025', 'Algérie Eco, 02/03/2026')], cols=4))
    fl.append(h2('7.1 L\'appareil de production'))
    rows = [['Filière', 'Acteurs et capacités', 'Situation 2026', 'Source'],
            ['Engrais azotés', 'AOA, Arzew (Sonatrach 49 %, Suhail Bahwan 51 %) : 4 000 t/j d\'ammoniac, 7 000 t/j d\'urée ; Sorfert (OCI 51 %) : 1 259 kt/an d\'urée, 803 kt/an d\'ammoniac marchand ; Fertial (Asmidal) : ~1 Mt/an d\'ammoniac',
             'Extension d\'AOA de +50 % décidée le 23/08/2026 ; mesure des émissions pour le MACF chez Fertial (convention du 07/09/2026)', 'Fertiglobe 2025 ; Algérie Eco'],
            ['Phosphates intégrés', 'Tébessa, Souk Ahras, Annaba : 2,4 Mt/an d\'engrais phosphatés et 570 kt/an d\'azotés annoncés', 'Contrats EPC Saipem et CHEC (12/08/2026) ; premières pierres les 23-25/09/2026 ; production visée fin 2027', 'Algérie Eco, 25/09/2026'],
            ['Pétrochimie Sonatrach', 'Méthanol CP1Z (152 kt/an) ; MTBE Arzew (200 kt/an) ; PP Arzew (550 kt/an) ; LAB Skikda (100 kt/an) ; éthylène Skikda (850 kt/an)',
             'MTBE à 86 % en février 2026 ; PP et LAB fin 2027 ; le LAB, base des détergents, est aujourd\'hui importé à 100 %', 'EcoTimes, 22/02/2026 ; Horizons, 17/05/2026'],
            ['Détergents', 'Henkel Algérie (Réghaïa, Chelghoum Laïd ; Isis, Le Chat, Pril, Bref) ; Esquirol (Life, 5 unités, 1 300 salariés) ; ENAD/Shymeca (public : Noor, Teldj, Nada)',
             'ENAD en crise (moins de 200 cartons par jour à Sidet, nov. 2024) ; Esquirol exporte ~300 k EUR (2025)', 'El Watan ; Horizons, 07/02/2026'],
            ['Cosmétiques', 'Laboratoires Venus (Blida, ~32 % du marché, 500 salariés) ; Vague de Fraîcheur (Blida, 160 références) ; Azul, Exception\'elle, Ines Cosmetics, Skin Beauty',
             'Couverture locale ~70 % (2024) ; importations ramenées de 500 à 58 M USD', 'TSA ; Algérie360 ; Algérie Eco, 25/01/2025'],
            ['Hygiène papier, plastiques', 'Faderco (Sétif ; couches, ouate) ; SGT (préformes, bouchons) ; Chiali, ITP (tubes) ; OXXO-Cevital, ADOPEN (profilés)', 'Faderco : 36 camions exportés le 11/04/2026', 'Horizons ; SaaS dza_filieres']]
    fl.append(Paragraph('Tableau 7.1 — Appareil de production du périmètre', CAP))
    fl.append(table(rows, [26 * mm, 66 * mm, 50 * mm, 32 * mm]))
    fl.append(Paragraph('Sources citées ; fiches « Algérie · industrie et marchés » du SaaS (urée, ammoniac, méthanol, hélium, plastiques).', SRC))
    fl.append(PageBreak())
    fl.append(h2('7.2 ENAD et Henkel : ce que dit l\'histoire d\'une privatisation'))
    fl.append(P("En mai 2000, l'Entreprise nationale des détergents (ENAD) cède à Henkel 60 % du complexe d'Aïn Témouchent et de l'unité de Réghaïa, puis, en 2002, 60 % de Chelghoum Laïd. "
                "En décembre 2004, Henkel rachète les 40 % restants pour 800 M DA et détient alors 60 à 70 % du marché algérien des détergents (El Watan, 08/12/2004). En novembre 2016, "
                "le groupe cède l'usine d'Aïn Témouchent à des investisseurs algériens tout en y maintenant du façonnage, et investit 20 M EUR à Réghaïa et 6 M EUR à Chelghoum Laïd "
                "(Algérie Eco, 03/11/2016). À cette date, deux tiers de ses matières premières étaient importées, mais 80 % de l'hypochlorite était produit localement."))
    fl.append(P("Le secteur public restant, ENAD (groupe Shymeca), traverse une crise de matières premières et de trésorerie (El Watan, 14/11/2024). "
                "<b>Lecture</b> : la capacité exportable de la filière repose aujourd'hui sur Henkel (échelle, marques) et sur les privés déjà présents en Afrique (Esquirol, Venus, "
                "Vague de Fraîcheur, Faderco). Elle changera de nature fin 2027 avec le LAB de Skikda, qui intégrera en amont la principale matière active des lessives. "
                "Deux points restent à vérifier : aucune exportation récente de Henkel Algérie n'est documentée, et certaines sources décrivent encore une participation de 60 % "
                "dans une entité « Henkel ENAD Algérie », en contradiction avec le rachat total de 2004."))
    fl.append(h2('7.3 Le système algérien d\'importation : programmes, autorisations, DAPS'))
    fl.append(P("Trois étages de contrôle s'additionnent au tarif douanier."))
    fl += bullets([
        '<b>Programmes prévisionnels d\'importation (PPI)</b>. Instruction du ministère du Commerce extérieur du 09/07/2025 (effet au 01/07/2025), non publiée au Journal officiel : sans PPI validé, '
        'pas de domiciliation bancaire, et « un programme, une banque » (note ABEF, août 2025). Plateforme import.mcepe.gov.dz ; dépôts du premier semestre 2026 jusqu\'au 26/02, produits finis admis du 22/03 au 30/04, '
        'second semestre du 23/06 au 31/07/2026 ; visa de domiciliation porté de 45 à 90 jours le 06/08/2026. Huit textes en huit mois (Maghreb Émergent, 08/2026) : l\'instabilité est en soi un coût.',
        '<b>Autorisations préalables</b>. Cosmétiques et hygiène corporelle : autorisation du ministère du Commerce après avis du CACQE, décision sous 45 jours (décrets 97-37 et 10-114). '
        'Produits toxiques : décret 97-254. Produits chimiques dangereux : autorisation du ministère de l\'Énergie (décret 03-451 modifié).',
        '<b>Déclaration politique</b>. Le 22/01/2026, le ministre du Commerce extérieur a déclaré que l\'Algérie « n\'importe plus de cosmétiques ni de maquillage » (Algérie360). Aucun texte ne l\'accompagne : '
        'en droit, l\'importation reste soumise au PPI et à l\'autorisation préalable.'])
    rows = [['Formalité particulière (DGD)', 'Segments concernés (nombre de positions)']]
    for k, v in sorted(FAP.items(), key=lambda kv: -sum(kv[1]['groups'].values())):
        g = ', '.join(f'{x} ({n})' for x, n in sorted(v['groups'].items()))
        rows.append([v['title'][:95], g])
    fl.append(Paragraph('Tableau 7.2 — Formalités administratives particulières à l\'importation, par segment', CAP))
    fl.append(table(rows, [96 * mm, 78 * mm], font=7))
    fl.append(Paragraph('Source : SaaS ZLECAf, data/dza/legal_overrides.json (nomenclature F.A.P du tarif d\'usage DGD, édition LF 2020, publication douane.gov.dz). Segments : C01 chimie inorganique, C02-C03 chimie organique, C04 engrais, '
                        'C05 peintures, C06 parfums, C07 maquillage, C08 capillaires, C09 bucco-dentaire, C10 rasage-déodorants, C11 savons, C12 détergents, C13 javel-désinfectants, C14 chimie divers, C15 plastiques, C16 hygiène papier. '
                        'Les obligations générales (déclaration, domiciliation, PPI) s\'ajoutent sans figurer par position.', SRC))
    fl.append(PageBreak())
    fl.append(figure(C + 'k2_dza_tax.png', 'Figure 7.1 — Charge à l\'importation en Algérie hors TVA : NPF et ZLECAf (% de la valeur CAF)',
                     'Source : SaaS ZLECAf, calculateur fiscal algérien (DD, DAPS, PRCT, TCS ; circulaire 482/2024 ; daps_exempt). DAPS de 80 % sur les positions 33.03 à 33.07 selon le tarif d\'usage DGD (édition LF 2020, consolidée) : '
                     'taux à confirmer pour 2026. Listes : A, démantèlement standard à 0 % en 2026 ; B, −20 % en 2026.', maxh=98 * mm))
    fl.append(P("<b>Un paradoxe à 110 points.</b> Un shampooing importé d'Europe supporte 112 % de charge hors TVA (30 % de droit, 80 % de DAPS, 2 % de PRCT) ; le même produit fabriqué en Tunisie ou en Égypte "
                "et accompagné d'un certificat ZLECAf n'en supporte que 2 %, car la liste A est à 0 % et le DAPS est levé. Sur le papier, la ZLECAf ouvre donc le marché algérien des cosmétiques "
                "aux voisins bien plus largement que ne le laisse penser le discours sur l'arrêt des importations. Dans les faits, le PPI et l'autorisation préalable restent le filtre. "
                "<b>Attention</b> : un contingentement administratif appliqué à des produits originaires d'un partenaire ZLECAf peut être signalé comme obstacle non tarifaire sur la plateforme "
                "de la ZLECAf (tradebarriers.africa). L'argument joue dans les deux sens pour les exportateurs algériens."))
    fl.append(h2('7.4 Ce que l\'Algérie importe encore'))
    rows = [['Produit (SH)', 'Import. 2024', 'Export. 2024', 'Lecture']]
    for k, lab, com in [('3901', 'Polyéthylène (39.01)', 'Substitution attendue du vapocraqueur de Skikda'), ('3907', 'Polyesters, PET (39.07)', 'Exportations de PET en hausse (23 M USD)'),
                        ('3302', 'Compositions parfumantes (33.02)', 'Intrant clé des cosmétiques, détergents et boissons'), ('3902', 'Polypropylène (39.02)', 'PP d\'Arzew en 2027 (550 kt/an)'),
                        ('3904', 'PVC (39.04)', 'Aucune capacité locale'), ('3402', 'Détergents et tensioactifs (34.02)', 'LAB de Skikda fin 2027'),
                        ('3808', 'Insecticides, désinfectants (38.08)', 'Formulation locale possible'), ('3208', 'Peintures en solvant (32.08)', ''), ('3304', 'Maquillage et soins (33.04)', 'Couverture locale ~70 %'),
                        ('3401', 'Savons (34.01)', '')]:
        rows.append([lab, f1(last('DZA|' + k, 'imports')), f1(last('DZA|' + k, 'exports')), com])
    fl.append(Paragraph('Tableau 7.3 — Importations et exportations algériennes, 2024 (M USD)', CAP))
    fl.append(table(rows, [52 * mm, 24 * mm, 24 * mm, 74 * mm], align_right_from=1))
    fl.append(Paragraph('Source : OEC / BACI via le module Statistiques du SaaS (recherche SH × pays, oec_trade_service.get_country_hs6_history). Contrôle : importations de plastiques de 2,79 Md USD en 2024 selon Algérie Eco (02/03/2026) ; '
                        'importations de produits chimiques supérieures à 4,2 Md EUR par an (Maghreb Émergent, 30/09/2025).', SRC))
    fl.append(PageBreak())
    fl.append(h2('7.5 Exporter : engrais, plastiques, puis produits de consommation'))
    fl.append(figure(C + 'k3_dza_gap.png', 'Figure 7.2 — Exportations algériennes et importations africaines, 2024 (M USD)',
                     'Source : BACI via le module Opportunités du SaaS (dza_commerce_baci.json). Importations africaines hors Algérie.', maxh=70 * mm))
    fl.append(P("<b>Engrais : réorienter vers l'Afrique.</b> L'Afrique a importé 1,3 Md USD d'urée et 1,7 Md USD d'ammoniac en 2024 (le Maroc, à lui seul, 1,6 Md USD d'ammoniac pour OCP), mais seulement "
                "0,7 % de l'urée algérienne et 3,5 % de son ammoniac y sont allés. L'Algérie vend en Europe (France), aux Amériques et, depuis la crise d'Ormuz, en Inde (245 000 t d'avril à juin 2026, "
                "Algérie Eco, 16/08/2026) et en Norvège (43 % des importations norvégiennes d'ammoniac en juillet 2026, Awras, 24/08/2026). Les engrais et produits chimiques ont totalisé 1,5 Md USD "
                "d'exportations de janvier à juillet 2025 (+9 %)."))
    rows = [['Année', 'Part des émissions soumise au MACF', 'Coût par tonne d\'urée (ETS 70 EUR)', 'Coût par tonne (ETS 100 EUR)']]
    cb = CA['cbam']
    for y in (2026, 2030, 2034):
        a = [c for c in cb if c['year'] == y]
        rows.append([str(y), f"{a[0]['share']*100:.1f} %".replace('.', ','), f"{a[0]['cost']:.0f} EUR", f"{a[1]['cost']:.0f} EUR"])
    fl.append(Paragraph('Tableau 7.4 — Hypothèse de coût du MACF sur l\'urée exportée vers l\'UE', CAP))
    fl.append(table(rows, [24 * mm, 56 * mm, 47 * mm, 47 * mm], align_right_from=1))
    fl.append(Paragraph('Hypothèses ZLECAf Trade Intelligence : intensité de 2,0 t CO2e par tonne d\'urée (ammoniac amont inclus), calendrier de réduction des allocations gratuites du règlement (UE) 2023/956. '
                        'Ordre de grandeur de référence : coût théorique par défaut d\'environ 59-62 USD par tonne d\'ammoniac pour l\'Égypte et l\'Algérie (recherche du 27/09/2026). À recalculer avec les émissions réelles mesurées (Fertial, 2026).', SRC))
    fl.append(P("Avec une urée à 450-500 USD/t, le MACF ne pèse presque rien en 2026, mais 15 à 40 % du prix en 2034. <b>L'Afrique devient le débouché de repli naturel</b> : droits nuls sur les engrais dans la plupart des marchés, "
                "préférence ZLECAf servie en Égypte, au Maroc et dans la SACU, et proximité maritime avec l'Afrique de l'Ouest."))
    fl.append(PageBreak())
    fl.append(h2('7.6 Cas chiffré : lessive algérienne à Nouakchott, Dakar et Tripoli'))
    fl.append(P("Hypothèses : conteneur de 40' de 22 t de lessive en poudre à 1 100 USD/t (24 200 USD) ; droit identique pour toutes les origines (la Mauritanie, le Sénégal et la Libye n'appliquent pas "
                "de préférence ZLECAf à l'Algérie) ; coût du capital de 12 % ; stock de sécurité égal à la moitié du transit. Fret calculé avec le modèle distance-coût du SaaS pour toutes les origines."))
    rows = [['Origine', 'Nouakchott', 'Dakar', 'Tripoli']]
    for o in CA['Nouakchott']:
        rows.append([o] + [f"{CA[d][o]['per_t']} $/t ({f1(CA[d][o]['pct'])} %)" for d in ('Nouakchott', 'Dakar', 'Tripoli')])
    fl.append(Paragraph('Tableau 7.5 — Coût de rendu hors prix du produit (fret, surcharges, assurance, portage), USD par tonne et % de la valeur', CAP))
    fl.append(table(rows, [60 * mm, 38 * mm, 38 * mm, 38 * mm], align_right_from=1))
    fl.append(Paragraph('Source : logistics_fees_data du SaaS (FEU = 1,5 × (175 + 0,255 × milles nautiques)) ; distances hors Algérie et surcharge de conflit de 3 000 USD/FEU au départ du Golfe (CMA CGM, 02/03/2026) : hypothèses. '
                        'La ligne CNAN Alger-Nouakchott-Nouadhibou-Dakar (un départ tous les 30 jours, 6 jours de transit, Echos Plus, 20/08/2026) justifie le délai retenu, mais sa fréquence est un frein.', SRC))
    fl.append(P("<b>Conclusion.</b> Pour un produit pondéreux à faible valeur, la proximité vaut <b>3 à 25 points de prix</b> : l'Algérie devance la Turquie de 1 à 3 points et la Chine ou le Golfe de 20 à 28 points en 2026, "
                "contournement du cap de Bonne-Espérance compris. C'est l'inverse du médicament, où le fret ne pèse que 1 à 2 % de la valeur. Le levier est ici logistique et commercial : "
                "une fréquence maritime mensuelle ne suffit pas pour tenir des linéaires de distribution, d'où l'intérêt de dépôts à Nouakchott et Dakar et de la route Tindouf-Zouérate."))
    fl.append(h2('7.7 Les groupes exportateurs de produits de consommation'))
    rows = [['Groupe', 'Produits', 'Marchés d\'export documentés', 'Fait récent'],
            ['Laboratoires Venus (SAPECO), Blida', 'Cosmétiques, soins, hygiène corporelle', '16 pays dont France, Canada, Tunisie, Mauritanie, Sénégal, Côte d\'Ivoire', 'Opération d\'export vers l\'Afrique de l\'Ouest le 24/04/2026 (La Patrie News)'],
            ['Vague de Fraîcheur, Blida', 'Déodorants, shampooings, gels douche, eaux de Cologne, solaires (160 références)', 'Tunisie, Mauritanie, France', '43 ans d\'existence ; gamme solaire premium (TSA, 2025)'],
            ['Esquirol (Life), Boumerdès', 'Détergents, entretien (2 000 références)', 'France, Belgique, Espagne, Tunisie, Libye, Mauritanie, Sénégal, Bénin, Maurice, Qatar', '~300 k EUR exportés en 2025 ; unité dédiée à l\'export en projet (Horizons, 07/02/2026)'],
            ['Faderco, Sétif', 'Couches, lingettes, essuie-tout', 'Tunisie, Libye, Cap-Vert, Europe', '36 camions le 11/04/2026 (Horizons)'],
            ['Henkel Algérie', 'Lessives (Isis, Le Chat), vaisselle (Pril), javel (Bref)', 'Aucune exportation récente documentée', 'Deux usines, marques leaders']]
    fl.append(Paragraph('Tableau 7.6 — Exportateurs algériens de produits de consommation du périmètre', CAP))
    fl.append(table(rows, [36 * mm, 44 * mm, 50 * mm, 44 * mm]))
    fl.append(Paragraph('Sources citées. « Fabirco » : aucune entreprise de ce nom n\'a pu être identifiée (le nom le plus proche, Faderco, figure au tableau). Aucun chiffre d\'export de cosmétiques postérieur à 2022 '
                        '(2 M USD, 84 entreprises, 37 pays) n\'a été publié.', SRC))
    fl.append(P("<b>Conditions pour changer d'échelle.</b> (i) Des dossiers d'enregistrement par marché (autorisations cosmétiques, étiquetage) ; (ii) un certificat d'origine ZLECAf appuyé sur un dossier de fabrication "
                "(règle des mélanges, chapitre 5) pour les marchés qui appliquent la préférence ; (iii) l'assurance-crédit CAGEX pour porter à 180 jours le délai de rapatriement imposé par le règlement 26-02 "
                "(120 jours sinon) ; (iv) des relais bancaires (Algerian Union Bank à Nouakchott, Algerian Bank of Senegal à Dakar, succursale de Niamey prévue fin 2026)."))
    return fl
