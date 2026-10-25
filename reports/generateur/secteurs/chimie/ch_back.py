from layout import *

def ch_method():
    fl = [chapter('A2', 'Annexe 2 — Note méthodologique')]
    items = [
        ('Périmètre produit', "16 segments définis par préfixes SH (tableau 3.1) : chimie inorganique (28), chimie organique de base (29.01-29.15) et fine (29.16-29.35, 29.42), engrais (31), peintures (32), "
         "huiles essentielles et parfums (33.01-33.03), maquillage et soins (33.04), capillaires (33.05), bucco-dentaire (33.06), rasage et déodorants (33.07), savons (34.01), détergents (34.02), "
         "javel, désinfectants et entretien (28.28, 38.08, 34.05), chimie divers (38), plastiques primaires (39.01-39.14), articles d'hygiène (48.18, 96.19, 9603.21). Rattachement au préfixe le plus long. "
         "Les principes actifs pharmaceutiques (29.36-29.41) relèvent du rapport Pharmaceutique & Santé."),
        ('Droits NPF', "40 barèmes nationaux du SaaS (30 958 lignes SH6 dans le périmètre), moyenne simple. DAPS algérien exclu des moyennes, traité au chapitre 7."),
        ('Offres et taux servis', "Instantanés e-Tariff Book (17/08 et 13/09/2026) ; calculateurs du SaaS au 27/09/2026 pour l'année 2026 ; taux servi seulement si la destination applique la ZLECAf et admet l'origine ; Maroc calculé sur les lignes de l'offre."),
        ('Charge fiscale algérienne', "Calculateur du SaaS : DD (ou taux ZLECAf) + DAPS (levé pour les listes A/B sous ZLECAf) + PRCT 2 % + TCS 3 % selon la ligne ; TVA exclue des comparaisons."),
        ('Statistiques de commerce', "OEC (BACI, HS 2017) : (i) API tesseract pour les agrégats africains par chapitre ; (ii) module Statistiques du SaaS, recherche SH × pays (oec_trade_service.get_country_hs6_history), pour l'Algérie, la Libye et les marchés cibles ; "
         "(iii) module Opportunités du SaaS (dza_commerce_baci.json) pour la demande africaine par SH6. Contrôle croisé avec UN Comtrade (déclarations de 31 pays africains en 2024)."),
        ('Statistiques nationales', "ONS, comptes économiques 2021-2024 (n° 1067, août 2025) et indicateurs trimestriels 2025, via le fichier dza_industrie.json du SaaS (branche « chimie, caoutchouc et plastiques ») ; estimation 2025 signalée comme telle."),
        ('Formalités', "Nomenclature F.A.P du tarif d'usage DGD (édition LF 2020), via data/dza/legal_overrides.json : l'absence de formalité par position est un constat de la source (échantillon de contrôle du 21/09/2026)."),
        ('Coût rendu (cas 7.6)', "Conteneur de 40' de 22 t à 1 100 USD/t ; fret : modèle du SaaS (FEU = 1,5 × (175 + 0,255 × milles)) appliqué à toutes les origines ; surcharge Golfe de 3 000 USD/FEU ; assurance 0,4 % ; coût du capital 12 % ; stock de sécurité = moitié du transit."),
        ('MACF (tableau 7.4)', "Intensité hypothétique de 2,0 t CO2e par tonne d'urée ; prix ETS de 70 et 100 EUR ; part soumise selon le calendrier du règlement (UE) 2023/956. Ordre de grandeur, pas une facture."),
        ('Presse', "Faits datés et sourcés, intégrés au texte ; les annonces sont distinguées des réalisations ; les chiffres contradictoires sont signalés."),
        ('Limites', "Pas de chiffre consolidé fiable du marché chimique africain ; tailles de marché des cosmétiques divergentes ; DAPS 2026 par position à confirmer au Journal officiel ; aucun chiffre public de capacité ni de taux d'utilisation pour les détergents et cosmétiques algériens.")]
    rows = [['Élément', 'Méthode et hypothèses']] + [[a, b] for a, b in items]
    fl.append(table(rows, [34 * mm, CW - 34 * mm]))
    return fl

LEXIQUE = [
    ('AOA', 'Algerian Omani Fertilizer Company, complexe d\'ammoniac et d\'urée d\'Arzew.'),
    ('CACQE', 'Centre algérien du contrôle de la qualité et de l\'emballage.'),
    ('CAGEX', 'Compagnie algérienne d\'assurance et de garantie des exportations.'),
    ('Catégorie A / B / C', 'Classement des lignes dans les offres ZLECAf : libéralisées, sensibles, exclues.'),
    ('CTH', 'Changement de position tarifaire (4 chiffres).'),
    ('Cumul', 'Prise en compte comme originaires des matières d\'un autre État partie.'),
    ('DAPS', 'Droit additionnel provisoire de sauvegarde (Algérie, 30 à 200 %), levé pour les listes A/B sous ZLECAf.'),
    ('Défrisant / lisseur', 'Préparation pour défriser ou lisser les cheveux (SH 33.05.20).'),
    ('Éclaircissant', 'Produit cosmétique destiné à éclaircir la peau ; mercure interdit, hydroquinone interdite ou plafonnée dans de nombreux pays.'),
    ('ENAD', 'Entreprise nationale des détergents et produits d\'entretien (Algérie), dont trois unités ont été reprises par Henkel (2000-2004).'),
    ('F.A.P', 'Formalités administratives particulières exigées à l\'importation, par position tarifaire (DGD).'),
    ('GAFTA / ZALE', 'Grande zone arabe de libre-échange, dont l\'Algérie et la Libye sont membres.'),
    ('LAB / LAS', 'Alkylbenzène linéaire et son dérivé sulfoné, matières actives des détergents.'),
    ('MACF / CBAM', 'Mécanisme d\'ajustement carbone aux frontières de l\'UE, définitif depuis 2026.'),
    ('Minamata', 'Convention sur le mercure ; interdit les cosmétiques éclaircissants au mercure.'),
    ('Note 8', 'Règles de traitement chimique de l\'Appendice IV (réaction, purification, mélanges, granulométrie…).'),
    ('NPF', 'Nation la plus favorisée : droit appliqué à toute origine hors préférence.'),
    ('OEC', 'Observatory of Economic Complexity, diffuseur des données BACI (CEPII).'),
    ('ONS', 'Office national des statistiques (Algérie).'),
    ('Opérations insuffisantes', 'Opérations qui ne confèrent jamais l\'origine (dilution, conditionnement, étiquetage…).'),
    ('PPI', 'Programme prévisionnel d\'importation (Algérie, depuis juillet 2025), préalable à la domiciliation bancaire.'),
    ('PRCT', 'Prélèvement de 2 % à l\'importation (Algérie).'),
    ('SGH', 'Système général harmonisé de classification et d\'étiquetage des produits chimiques.'),
    ('SH', 'Système harmonisé de désignation et de codification des marchandises.'),
    ('TCS', 'Taxe de solidarité de 3 % à l\'importation sur certaines lignes (Algérie).'),
    ('TEC', 'Tarif extérieur commun d\'une union douanière.'),
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

def ch_recos():
    fl = [chapter(10, 'Recommandations')]
    fl.append(P("Recommandations hiérarchisées par acteur, à horizon 12 à 24 mois.", LEAD))
    rows = [['Acteur', 'Recommandation', 'Levier chiffré', 'Horizon'],
            ['Producteurs d\'engrais', 'Réserver une part des volumes d\'urée et d\'ammoniac à l\'Afrique (Afrique australe, Tunisie, Afrique de l\'Ouest) ; mesurer les émissions réelles', 'MACF de 3 à 5 EUR/t en 2026, 140 à 200 EUR/t en 2034 (hypothèse)', '2026-2028'],
            ['Formulateurs (cosmétiques, détergents)', 'Tenir un dossier de fabrication prouvant le mélange contrôlé (note 8) pour obtenir le certificat d\'origine ZLECAf', 'Origine accessible sans changement de position', 'Immédiat'],
            ['Exportateurs de lessives et d\'hygiène', 'Cibler Libye, Mauritanie, Sénégal, Tunisie ; ouvrir des dépôts à Nouakchott et Dakar', 'Coût de rendu de 3 à 5 % contre 22 à 33 % pour l\'Asie et le Golfe', '12 mois'],
            ['Cosmétiques pour peaux et cheveux africains', 'Formules sans hydroquinone, mercure ni corticoïdes ; défrisants dans les limites de soude ; enregistrement NAFDAC, FDA Ghana, KEBS', 'Accès aux distributeurs qui redoutent les saisies', '12-18 mois'],
            ['Tous exportateurs', 'Couvrir les créances par la CAGEX pour porter le rapatriement à 180 jours', 'Règlement 26-02 : 120 jours sinon', 'Immédiat'],
            ['Pouvoirs publics algériens', 'Stabiliser le PPI (texte publié, calendrier annuel) ; publier la liste DAPS 2026', 'Réduit le coût d\'incertitude des industriels', 'LF 2027'],
            ['Pouvoirs publics algériens', 'Élargir la liste des partenaires admis aux pays d\'Afrique de l\'Ouest pour obtenir la réciprocité', 'Sans réciprocité, 20 à 43 % de droit subsistent sur les cosmétiques algériens', '12 mois'],
            ['Pétrochimie (PP, LAB)', 'Préparer dès 2026 les contrats africains du PP d\'Arzew et du LAB de Skikda', '430 kt/an de PP exportables ; LAB importé à 100 % aujourd\'hui', '2027'],
            ['Opérateurs tunisiens et égyptiens', 'Exploiter l\'écart de 110 points sur les cosmétiques en Algérie, sous réserve du PPI et de l\'autorisation préalable', 'Charge de 2 % contre 112 %', '12 mois']]
    fl.append(table(rows, [34 * mm, 72 * mm, 48 * mm, 20 * mm]))
    fl.append(Paragraph('Source : ZLECAf Trade Intelligence, à partir des calculs du rapport.', SRC))
    return fl
