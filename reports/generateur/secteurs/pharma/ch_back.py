from layout import *

def ch_method():
    fl = [chapter('A2', 'Annexe 2 — Note méthodologique')]
    items = [
        ('Périmètre produit', "15 segments de santé définis par préfixes SH (tableau 3.1) : principes actifs (29.36-29.41), produits du sang et vaccins (30.01-30.02), médicaments en vrac (30.03) et dosés (30.04), "
         "pansements et articles pharmaceutiques (30.05-30.06), réactifs (38.22), désinfectants (3808.94, 2207.10, 2208.90), gants (40.14-40.15), instruments (90.18-90.20), orthopédie (90.21), "
         "imagerie (90.22), mobilier (94.02), hygiène (96.19), emballages (70.10, 39.23) et textiles médicaux (6307.90, 6210.10). Rattachement d'une ligne au préfixe le plus long."),
        ('Droits NPF', "40 barèmes nationaux du SaaS (5 463 lignes SH6 dans le périmètre). Moyenne simple des lignes, sans pondération par les échanges. Lorsqu'une ligne SH6 comporte des sous-positions nationales à taux différents, "
         "le taux retenu est celui de la ligne SH6 (ou de la première sous-position, pour l'Algérie et le Maroc). Le Maroc est présenté soit sur son barème national (chapitre 3), soit sur les lignes de son offre (chapitres 4 et 8), comme indiqué."),
        ('Catégories d\'offre', "Instantanés e-Tariff Book (UA) collectés les 17/08 et 13/09/2026 : CEMAC, CAE, CEDEAO, Égypte, Éthiopie, Maroc, Tunisie, Zambie, Zimbabwe (plus le barème SARS pour la SACU). Une offre est « OFFER_ONLY » tant "
         "qu'aucun acte national et aucune liste d'origines admises ne sont vérifiés."),
        ('Taux servis', "Calculateurs du SaaS (compute_dza_zlecaf_rate, compute_egy_zlecaf_rate, compute_ken_zlecaf_rate, resolve_official_preferential_rate) au 27/09/2026, année 2026. Un taux n'est servi que si la destination a un acte "
         "d'application en vigueur, admet l'origine et couvre la ligne ; à défaut, le NPF est retenu. Le taux servi est plafonné au NPF."),
        ('Charge fiscale algérienne', "Calculateur du SaaS : DD (ou taux ZLECAf) + DAPS (levé pour les listes A/B sous ZLECAf) + PRCT 2 % + TCS 3 % (lignes concernées) ; TVA calculée sur la base majorée, mais exclue des comparaisons "
         "(récupérable pour un industriel ; exonération de principe des médicaments à usage humain)."),
        ('Protection effective', "TPE = (t<sub>p</sub> − a·t<sub>i</sub>)/(1 − a), avec t<sub>p</sub> = 7 % (médicament fini, DD + PRCT) et t<sub>i</sub> = 17 %, 8 % ou 2 % selon l'origine de l'API. Un seul intrant importé ; hypothèse prudente."),
        ('Coût rendu (cas 8.5)', "Valeur FOB 300 000 USD par conteneur de 40' ; fret Inde 4 000 USD (sensibilité 3 000-6 000) ; Alger-Dakar 1 430 USD (SaaS, 955 USD par EVP × 1,5) ; assurance 0,35 % et 0,25 % ; coût du capital 12 % ; "
         "stock de sécurité égal à la moitié du transit. L'avantage calculé est l'écart de prix FOB maximal supportable par l'origine Algérie à droits égaux."),
        ('Demande', "BACI (CEPII) via le module Opportunités du SaaS (dza_commerce_baci.json), importations 2024 des pays africains hors Algérie, en USD courants. Les exportations algériennes proviennent du même fichier "
         "et du sous-module « Algérie · industrie et marchés » (dza_filieres.json), qui signale ses propres contradictions de sources."),
        ('Sources externes', "Chaque chiffre externe est daté et sourcé : GAFI, EUR-Lex, Secrétariat ZLECAf (Annexe 2, règlement 1/2023), OMC (TPR Maurice 2021), EDB, MRA, PwC, US ITA, Banque d'Algérie, ANPP, MIPH, APS et presse économique. "
         "Les informations non confirmées en source primaire sont signalées dans le texte."),
        ('Limites', "Les taux ne tiennent pas compte des exonérations au cas par cas (marchés publics, dons, programmes nationaux), des prix administrés ni des délais d'enregistrement, souvent plus déterminants que le droit de douane "
         "dans la santé. Les scénarios sont des ordres de grandeur conditionnels, pas des prévisions.")]
    rows = [['Élément', 'Méthode et hypothèses']] + [[a, b] for a, b in items]
    fl.append(table(rows, [34 * mm, CW - 34 * mm]))
    return fl

LEXIQUE = [
    ('AMA', 'Agence africaine du médicament, créée par traité (en vigueur depuis novembre 2021), siège à Kigali.'),
    ('AMM', 'Autorisation de mise sur le marché d\'un médicament, délivrée par l\'autorité nationale (ANPP en Algérie).'),
    ('ANPP', 'Agence nationale des produits pharmaceutiques (Algérie).'),
    ('API / principe actif', 'Substance active d\'un médicament (SH 29 pour l\'essentiel), par opposition aux excipients.'),
    ('Biosimilaire', 'Médicament biologique similaire à un produit de référence dont le brevet a expiré.'),
    ('CAGEX', 'Compagnie algérienne d\'assurance et de garantie des exportations.'),
    ('Catégorie A / B / C', 'Classement des lignes dans les offres ZLECAf : libéralisées (90 %), sensibles (7 %), exclues (3 %).'),
    ('Certificat d\'origine', 'Document prouvant qu\'un produit est originaire au sens de l\'Annexe 2 ; condition du taux préférentiel.'),
    ('CTH', 'Changement de position tarifaire (4 chiffres) entre les matières non originaires et le produit fini.'),
    ('Cumul', 'Possibilité de compter comme originaires les matières d\'un autre État partie.'),
    ('DAPS', 'Droit additionnel provisoire de sauvegarde (Algérie, 30 à 200 %), levé pour les listes A/B sous ZLECAf.'),
    ('DCI', 'Dénomination commune internationale d\'une substance (ex. amoxicilline).'),
    ('Dispositif médical', 'Instrument, appareil ou matériel à usage médical (SH 90.18 à 90.22 surtout), classé de I à III selon le risque.'),
    ('e-Tariff Book', 'Base officielle de l\'UA des offres tarifaires ZLECAf.'),
    ('EOE', 'Export Oriented Enterprise : statut des anciennes entreprises EPZ mauriciennes depuis 2006.'),
    ('EPZ', 'Export Processing Zone : zone franche d\'exportation (Maurice, 1970-2006).'),
    ('Freeport', 'Zone franche douanière de Maurice (1992 ; Freeport Act 2004).'),
    ('GAFI / FATF', 'Groupe d\'action financière ; sa « liste grise » recense les juridictions sous surveillance renforcée.'),
    ('GAFTA / ZALE', 'Grande zone arabe de libre-échange ; distincte du GAFI.'),
    ('GMP / BPF', 'Bonnes pratiques de fabrication, condition d\'agrément des usines.'),
    ('Liste A (Algérie)', 'Lignes démantelées selon la circulaire DGD 482/2024 : 0 % en 2026 (calendrier standard).'),
    ('Niveau de maturité 3 (OMS)', 'Niveau de l\'outil GBT de l\'OMS attestant un système de réglementation stable et fonctionnel.'),
    ('NPF', 'Nation la plus favorisée : droit appliqué à toute origine hors préférence.'),
    ('Opérations insuffisantes', 'Opérations (conditionnement, mélange, étiquetage…) qui ne confèrent jamais l\'origine.'),
    ('P1 / P2 (Maroc)', 'Listes d\'origines admises par le Maroc : démantèlement en 5 ans (P1) ou 10 ans (P2) depuis 2021.'),
    ('Perfectionnement actif', 'Régime douanier suspendant les droits sur des intrants transformés puis réexportés.'),
    ('PCH', 'Pharmacie centrale des hôpitaux (Algérie).'),
    ('Pilier 2 / QDMTT', 'Impôt minimum mondial de 15 % pour les groupes > 750 M EUR ; version domestique qualifiée.'),
    ('PRCT', 'Prélèvement de 2 % à l\'importation en Algérie.'),
    ('Préqualification OMS', 'Évaluation de l\'OMS ouvrant l\'accès aux achats des agences des Nations unies.'),
    ('Protection effective', 'Protection de la valeur ajoutée d\'un producteur, compte tenu des droits sur ses intrants.'),
    ('Réciprocité (Algérie)', 'Calendrier plus lent appliqué à l\'Afrique du Sud, au Cameroun, au Ghana et au Kenya.'),
    ('Règlement 1/2023', 'Règlement ministériel ZLECAf sur le traitement des produits des zones économiques spéciales.'),
    ('SH', 'Système harmonisé de désignation et de codification des marchandises (OMD).'),
    ('TCS', 'Taxe de solidarité de 3 % à l\'importation sur certaines lignes en Algérie.'),
    ('TEC', 'Tarif extérieur commun d\'une union douanière (CEDEAO, CAE, CEMAC, SACU).'),
    ('TPE', 'Taux de protection effective (voir Protection effective).'),
    ('ZES', 'Zone économique spéciale : partie du territoire à régime douanier, fiscal ou réglementaire dérogatoire.'),
    ('Zone franche', 'Espace réputé hors du territoire douanier national : les ventes vers le marché intérieur y sont des importations.'),
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
    fl.append(P("Les recommandations sont hiérarchisées par acteur. Elles découlent des calculs des chapitres 3 à 9 et visent un horizon de 12 à 24 mois.", LEAD))
    rows = [['Acteur', 'Recommandation', 'Levier chiffré', 'Horizon'],
            ['Industriel algérien', 'Sourcer les principes actifs et le verre auprès d\'origines ZLECAf du calendrier standard (Égypte, Tunisie) ; à défaut, activer le perfectionnement actif pour la production exportée',
             'Jusqu\'à 14,7 % de prime de prix supportable sur l\'API ; TPE de −3 % à +12 % (a = 50 %)', '6-12 mois'],
            ['Industriel algérien', 'Cibler d\'abord les produits volumineux à faible valeur (solutés, sirops, pansements, consommables) en Afrique de l\'Ouest, où la proximité pèse le plus',
             'Avantage de coût rendu de 1,3 à 3 % (jusqu\'à 5,8 % pour un conteneur de 100 000 USD)', '12 mois'],
            ['Industriel algérien', 'Adosser chaque contrat africain à une assurance-crédit CAGEX pour porter le délai de rapatriement à 180 jours', 'Règl. 26-02 : 120 jours sans assurance', 'Immédiat'],
            ['ANPP et MIPH', 'Obtenir le niveau de maturité 3 de l\'OMS et négocier des procédures d\'enregistrement fondées sur la confiance réglementaire avec la Mauritanie, le Sénégal, le Mali et le Niger',
             'Délai d\'enregistrement : premier obstacle, avant le droit de douane', '2026-2027'],
            ['Pouvoirs publics algériens', 'Corriger l\'escalade à rebours : aligner les API (15 %) sur le médicament fini (5 %) ou les exonérer sous condition de fabrication locale', 'Supprime la protection effective négative', 'LF 2027'],
            ['Pouvoirs publics algériens', 'Élargir la liste des partenaires admis (neuf origines aujourd\'hui) aux pays d\'Afrique de l\'Ouest pour obtenir la réciprocité sur les marchés d\'export', 'Condition d\'accès aux préférences servies', '12 mois'],
            ['Opérateur mauricien', 'Enregistrer l\'entreprise Freeport au titre du règlement 1/2023, documenter l\'origine (critère des 60 % pour les dispositifs de 90.18) et cibler l\'Algérie et le Maroc',
             'Marge de 30 points sur les cathéters en Algérie ; 0 % au Maroc (P1)', '6 mois'],
            ['Investisseur (tous pays)', 'Évaluer une implantation en zone franche sous l\'angle de l\'origine ZLECAf, pas seulement de la fiscalité : un simple reconditionnement ne crée pas d\'origine', 'Préférence nulle sans transformation suffisante', 'Avant investissement'],
            ['Banques et assureurs', 'Intégrer la sortie de la liste grise du GAFI (Algérie, juin 2026) dans les politiques de risque pays, et suivre le retrait de la liste de l\'UE', 'Coût de confirmation des crédits documentaires', 'Immédiat'],
            ['Centrales d\'achat africaines', 'Utiliser les préférences ZLECAf sur les dispositifs et consommables (droits de 10 à 35 %) dans les achats groupés', 'Économie directe sur le coût rendu', '12 mois']]
    fl.append(table(rows, [30 * mm, 76 * mm, 48 * mm, 20 * mm]))
    fl.append(Paragraph('Source : ZLECAf Trade Intelligence, à partir des calculs du rapport.', SRC))
    return fl
