from layout import *
C = S + 'charts/'

def ch_market():
    fl = [chapter(1, 'Le marché africain des produits de santé'),
          P("L'Afrique consomme des médicaments qu'elle ne produit pas. Elle importe plus de 70 % de ses médicaments et environ 99 % de ses vaccins, "
            "et le commerce pharmaceutique entre pays africains ne pèse qu'environ 5 % de ses importations. C'est la définition même d'un marché de substitution, "
            "que la ZLECAf, l'Agence africaine du médicament et les achats groupés cherchent à ouvrir aux producteurs du continent.", LEAD)]
    fl.append(kpis([('17-20 Md$', 'importations africaines de produits pharmaceutiques (SH 30) par an', 'UN Comtrade, calcul sur déclarations 2022-2024'),
                    ('≈ 5 %', 'part du commerce intra-africain dans ces importations (0,79 Md USD en 2024)', 'UN Comtrade, extraction 27/09/2026'),
                    ('70 % / 99 %', 'part importée des médicaments / des vaccins', 'Gavi (2025) ; OMS AFRO (22/07/2024)'),
                    ('9,0 Md$', 'importations de médicaments dosés SH 3004.90 seuls (2024)', 'BACI via SaaS, module Opportunités')], cols=4))
    fl.append(Spacer(1, 4))
    fl.append(figure(C + 'k1_market.png', 'Figure 1.1 — D\'où viennent les médicaments de l\'Afrique, et qui les achète',
                     'Source : UN Comtrade (données miroir et déclarations des pays africains, extraction du 27/09/2026, calcul ZLECAf Trade Intelligence). *Éthiopie : 2023. '
                     'Chine : 0,97 Md USD en 2023 (non disponible pour 2024), mais premier fournisseur de principes actifs.', maxh=70 * mm))
    fl.append(h2('1.1 Un marché mal mesuré, mais en forte croissance'))
    fl.append(P("Il n'existe pas de chiffre unique de la taille du marché africain du médicament : selon le périmètre (prix fabricant ou public, médicaments seuls ou avec dispositifs), "
                "les cabinets privés l'estiment entre <b>29 et 64 Md USD en 2025</b>, avec une croissance de 6 à 9 % par an jusqu'en 2030-2032 (Persistence Market Research, 2025 ; "
                "ResearchAndMarkets, 23/07/2025). L'Égypte en est le premier marché (8,4 Md USD en 2025, selon Zawya), devant l'Afrique du Sud, le Nigeria et l'Algérie (4 à 4,7 Md USD, selon Maghreb Pharma, 21/05/2025). "
                "IQVIA prévoit pour l'Afrique la plus forte croissance en volume au monde, portée par la démographie et l'élargissement de l'accès aux soins (10/2024)."))
    fl.append(P("<b>Les fournisseurs.</b> En valeur, l'Union européenne fournit 45 à 50 % des médicaments importés (France 17 %, Belgique 11 %, Allemagne 9 %), l'Inde 29 % et la Suisse 12 %. "
                "Le chiffre indien de « 40 % » souvent cité par la presse (AFP, 2026) correspond vraisemblablement aux volumes : l'Inde domine les génériques bon marché, l'Europe les spécialités. "
                "La Chine pèse peu dans les médicaments finis (7 %) mais fournit l'essentiel des principes actifs, y compris ceux de l'Inde, qui en dépend pour 65 à 70 % (ORF)."))
    fl.append(PageBreak())
    fl.append(h2('1.2 Qui produit en Afrique ?'))
    rows = [['Pays', 'Exportations pharma', 'Positionnement', 'Source'],
            ['Afrique du Sud', '538 M USD (SH 30, 2024), 41 % des exportations intra-africaines', 'Aspen (premier génériqueur du continent), Biovac (vaccins)', 'UN Comtrade ; Aspen ; Semafor, 02/07/2026'],
            ['Égypte', '1,3 Md USD en 2025 selon l\'EDA (0,45 Md USD en SH 30 strict) ; objectif 3 Md USD en 2030', '~80 % d\'autosuffisance ; Eva Pharma (licence Eli Lilly)', 'TV BRICS, 22/04/2026 ; Daily News Egypt, 24/08/2025'],
            ['Maroc', '171 M USD en 2025 ; déficit pharma de 1,1 Md USD', 'Objectif de 1 Md USD d\'exportations par an', 'Morocco World News, 09/2026'],
            ['Kenya', '175 M USD (SH 30, 2024), 22 % des exportations intra-africaines', 'Hub de la CAE', 'UN Comtrade'],
            ['Tunisie', '128 M USD (SH 30, 2024)', 'Génériques, sous-traitance européenne', 'UN Comtrade'],
            ['Algérie', '23,3 M USD de médicaments dosés (2024), dont 80,9 % vers l\'Arabie saoudite', '83 % de couverture du marché national ; 233 sites', 'BACI via SaaS ; ANPP, 22/02/2026']]
    fl.append(Paragraph('Tableau 1.1 — Les principaux producteurs africains', CAP))
    fl.append(table(rows, [26 * mm, 58 * mm, 52 * mm, 38 * mm]))
    fl.append(Paragraph('Les périmètres diffèrent (SH 30 strict, déclarations nationales, chiffres d\'agence) : les comparaisons entre pays sont des ordres de grandeur.', SRC))
    fl.append(P("<b>Un paradoxe algérien.</b> L'Algérie est le troisième importateur africain de produits pharmaceutiques au sens large (1,97 Md USD en SH 30 en 2024, UN Comtrade) alors que sa facture "
                "d'importation de « médicaments » n'est plus que de 515 M USD selon la presse nationale (Horizons, 01/02/2026). L'écart tient au périmètre : le SH 30 comprend les vaccins, les produits "
                "du sang, les insulines et les médicaments innovants, que les chiffres officiels de substitution ne couvrent pas tous. Pour un fournisseur africain, c'est ce segment de produits "
                "à forte valeur, encore importés, qui constitue le vrai marché algérien."))
    fl.append(h2('1.3 Vaccins, achats groupés et préqualification'))
    fl += bullets([
        '<b>Vaccins</b> : l\'Union africaine vise 60 % de production locale en 2040 ; le jalon de 10 % en 2025 n\'a pas été atteint. L\'accélérateur AVMA de Gavi (lancé en juin 2024) mobilise jusqu\'à 1,2 Md USD sur dix ans ; '
        'premiers décaissements attendus au second semestre 2026 (Gavi ; Semafor, 02/07/2026).',
        '<b>Achats groupés</b> : le premier appel d\'offres du Mécanisme africain d\'achats groupés d\'Africa CDC (résultats du 12/05/2026) a porté sur 10 produits de santé maternelle et infantile pour 10 pays, '
        'avec des <b>économies de 30 à 90 %</b> ; 5 des 10 produits impliquent des fabricants africains. Afreximbank et Africa CDC y adossent une facilité de 2 Md USD.',
        '<b>Préqualification OMS</b> : elle ouvre les achats des agences de l\'ONU et du Fonds mondial. Aucun décompte consolidé des fabricants africains préqualifiés n\'est publié ; '
        'MMV en a accompagné 3 pour les antipaludiques et en vise 7 d\'ici 2030.',
        '<b>Qualité</b> : environ 1 produit médical sur 10 est de qualité inférieure ou falsifié dans les pays à revenu faible et intermédiaire (OMS) ; les méta-analyses africaines avancent 18,7 à 22,6 %. '
        'L\'opération Pangea XVIII d\'Interpol (mars 2026, 90 pays) a saisi 6,42 millions de doses, dont des antibiotiques et antipaludiques dans 12 pays africains. Une production locale certifiée est aussi une réponse de santé publique.'])
    return fl

def ch_legal():
    fl = [PageBreak(), chapter(2, 'Cadre ZLECAf et régulation pharmaceutique'),
          P("Trois étages de règles déterminent l'accès d'un médicament à un marché africain : le droit de douane (ZLECAf et tarifs nationaux), l'origine (Annexe 2), "
            "et, surtout, l'autorisation de mise sur le marché, qui relève encore de 54 autorités nationales en voie d'harmonisation par l'Agence africaine du médicament.", LEAD)]
    fl.append(h2('2.1 Les engagements tarifaires'))
    fl.append(P("Les modalités de négociation prévoient la libéralisation de <b>90 % des lignes</b> (catégorie A) en 5 ans (10 ans pour les pays les moins avancés), de 7 % de lignes sensibles "
                "en 10 ans (13 pour les PMA) et l'exclusion d'au plus 3 % des lignes, dans la limite de 10 % des importations. Les produits pharmaceutiques figurent parmi les chaînes de valeur "
                "prioritaires de l'Accord et parmi les produits de l'Initiative de commerce guidé, passée de 7 à 39 pays participants en septembre 2024 (IISD, 2024). "
                "Aucun pays africain n'est membre de l'accord « zéro pour zéro » de l'OMC sur les produits pharmaceutiques (1995) ; plusieurs ont néanmoins supprimé leurs droits "
                "de façon autonome (Nigeria et Ghana dès 2018)."))
    fl.append(P("<b>La mise en œuvre reste partielle.</b> Au 27 septembre 2026, le registre d'application du SaaS n'identifie que cinq destinations où un taux préférentiel est opposable, "
                "ligne par ligne et pour des origines nommées : Afrique du Sud (SACU), Algérie, Égypte, Kenya et Maroc (chapitre 4). Le Protocole sur l'investissement, adopté en février 2023, "
                "attend encore ses ratifications."))
    fl.append(h2('2.2 L\'Agence africaine du médicament et la confiance réglementaire'))
    rows = [['Élément', 'Situation (septembre 2026)', 'Source'],
            ['Traité AMA', 'En vigueur depuis le 05/11/2021 ; 32 à 33 ratifications en 2026 selon les sources ; accord-cadre OMS-AMA signé le 21/05/2026', 'Site AMA ; Health Policy Watch ; OMS, 21/05/2026'],
            ['Siège et direction', 'Kigali ; Dr Delese Mimi Darko, directrice générale depuis juin 2025', 'UA, 04/06/2025'],
            ['Compétences transférées', 'Harmonisation réglementaire (AMRH) et surveillance de la sécurité, reprises d\'AUDA-NEPAD en janvier 2026', 'ACRN, 13/08/2026'],
            ['Régulateurs au niveau 3 de l\'OMS', '10 : Afrique du Sud, Égypte, Éthiopie, Ghana, Mozambique (08/2026), Nigeria, Rwanda, Sénégal, Tanzanie, Zimbabwe', 'OMS, 24/08/2026 et 30/09/2025'],
            ['Algérie', 'Ratification du traité AMA (2021) ; évaluation de l\'ANPP au niveau 3 engagée à partir de septembre 2026', 'El Watan, 10/06/2021 ; L\'Algérie Aujourd\'hui, 07/06/2026'],
            ['Maurice', 'Ratification du traité AMA ; pas d\'agence autonome du médicament', 'OMS AFRO, 25/07/2025 ; OMC 2021'],
            ['Capacité réglementaire', '40 des 47 autorités de la région AFRO n\'exercent pas toutes les fonctions réglementaires', 'OMS AFRO, 25/07/2025']]
    fl.append(Paragraph('Tableau 2.1 — Architecture réglementaire africaine', CAP))
    fl.append(table(rows, [34 * mm, 96 * mm, 44 * mm]))
    fl.append(Paragraph('Sources citées. La liste des régulateurs de niveau 3 est celle publiée par l\'OMS au 24/08/2026.', SRC))
    fl.append(callout('Pourquoi le niveau 3 de l\'OMS compte plus que la ZLECAf pour l\'exportateur', [
        'Un médicament ne franchit pas une frontière africaine sans autorisation de mise sur le marché. Un régulateur reconnu au niveau 3 ouvre la voie aux procédures fondées sur la confiance '
        '(« reliance ») : le pays importateur s\'appuie sur l\'évaluation d\'un régulateur de référence, ce qui ramène le délai d\'enregistrement de plusieurs années à quelques mois. '
        'Pour l\'Algérie, l\'aboutissement de l\'évaluation de l\'ANPP, engagée en septembre 2026, vaut davantage que tout point de droit de douane.'], bg=TEAL_L, bar=TEAL, title_color=TEAL))
    fl.append(h2('2.3 Les obstacles non tarifaires'))
    fl.append(P("Par ordre d'importance : l'<b>enregistrement</b> (dossiers CTD nationaux multiples, 12 à 36 mois, redevances) ; les <b>inspections BPF</b> redondantes ; les <b>prix administrés</b> "
                "(Algérie, Maroc, Égypte, Tunisie), qui fixent la rentabilité avant le droit de douane ; la <b>préférence nationale</b> dans les achats publics et les programmes d'importation ; "
                "enfin les <b>paiements</b> (délais publics de 90 à 180 jours, contrôle des changes, diligences renforcées dans les pays sous surveillance du GAFI)."))
    return fl
