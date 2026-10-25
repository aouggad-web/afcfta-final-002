from layout import *
C = S + 'charts/'

def ch_mauritius():
    fl = [chapter(7, 'Étude de cas : Maurice, zones franches et ZLECAf'),
          P("Maurice est le laboratoire africain des zones franches. Dès 1970, sa loi sur les zones franches d'exportation (EPZ) a fondé le décollage "
            "industriel de l'île. Aujourd'hui, son Freeport, son régime d'entreprises exportatrices et son secteur financier offshore en font un cas d'école "
            "pour trois questions que tout investisseur se pose : un produit fabriqué en zone franche bénéficie-t-il de la ZLECAf ? Que deviennent les "
            "avantages fiscaux et de change ? Et quel risque de réputation depuis le passage de Maurice sur la liste grise du GAFI ?", LEAD)]
    fl.append(kpis([('1970', 'Loi EPZ : fondation du modèle industriel exportateur', 'OMC, TPR WT/TPR/S/417 (2021)'),
                    ('268', 'opérateurs Freeport, ~5 500 emplois ; 797 M USD d\'échanges (2023)', 'EDB Mauritius, consulté le 27/09/2026'),
                    ('3 %', 'taux d\'IS sur les bénéfices d\'exportation et en Freeport (15 % sinon)', 'PwC Tax Summaries, 15/06/2026'),
                    ('49 M USD', 'exportations de dispositifs médicaux en 2024 (60 % vers la France)', 'US ITA, 19/02/2026')], cols=4))
    fl.append(Spacer(1, 4))
    fl.append(figure(C + 'm1_mus.png', 'Figure 7.1 — Maurice : cinquante ans de zones franches, de fiscalité et de conformité (frise non proportionnelle)',
                     'Sources : OMC TPR 2021 ; EDB ; Bank of Mauritius ; EUR-Lex (règl. délégués 2020/855 et 2022/229) ; Secrétariat ZLECAf (règl. 1/2023) ; Commission européenne (10/06/2026) ; EDB (ESAAMLG 2027).', maxh=50 * mm))
    fl.append(h2('7.1 De l\'EPZ au Freeport : un modèle qui s\'est normalisé'))
    fl.append(P("Le régime EPZ a disparu en tant que tel le <b>1er octobre 2006</b> : la Finance Act 2006 a mis fin aux certificats industriels, et les anciennes "
                "entreprises EPZ sont devenues des <b>entreprises exportatrices (EOE)</b> soumises au droit commun, avec un taux réduit de 3 % sur les bénéfices "
                "d'exportation. En 2019, les 239 EOE manufacturières employaient environ 44 000 personnes et pesaient un tiers de la valeur ajoutée manufacturière, "
                "avec une contraction continue depuis 2014 (textile surtout). Les <b>dispositifs médicaux et produits pharmaceutiques</b> figurent parmi les branches EOE citées par l'OMC."))
    fl.append(P("Le <b>Freeport</b> (1992, Freeport Act n° 43 de 2004) est la vraie zone franche au sens douanier : importations en franchise de droits et de TVA, "
                "achats locaux à TVA zéro, frais portuaires réduits d'environ 50 %. Son exonération totale d'impôt sur les sociétés a été <b>supprimée en juin 2018</b> "
                "(taux de 3 % pour les nouveaux opérateurs ; maintien à 0 % jusqu'au 30 juin 2021 pour les certificats antérieurs), afin de se conformer aux standards "
                "OCDE, OMC et UE sur les régimes fiscaux dommageables. Depuis la Finance Act 2025, un <b>impôt minimum domestique (QDMTT, Pilier 2)</b> porte à 15 % "
                "l'imposition effective des groupes réalisant plus de 750 M EUR de chiffre d'affaires : l'avantage fiscal mauricien ne joue plus pour les grands laboratoires "
                "multinationaux, mais reste entier pour les PME et ETI."))
    fl.append(P("Le budget 2026-2027 (19/06/2026) oriente l'île vers la recherche clinique : amendement du Clinical Trials Act pour attirer les CRO et les biotechs, cellule « Healthcare Innovation & AI », "
                "et renforcement des lois anti-blanchiment (FIAMLA, Banking Act). La synthèse budgétaire de l'EDB recense <b>139 certificats Freeport actifs</b>, contre 268 opérateurs « enregistrés » selon la page de l'EDB : "
                "l'écart entre opérateurs inscrits et actifs mesure la part de structures dormantes."))
    fl.append(PageBreak())
    fl.append(h2('7.2 La santé à Maurice : un hub de dispositifs, pas (encore) de médicaments'))
    rows = [['Indicateur', 'Valeur', 'Source'],
            ['Fabricants de dispositifs médicaux', '6 entreprises, ~1 200 emplois (stents, cathéters d\'angioplastie, implants)', 'US ITA, 19/02/2026'],
            ['Exportations d\'équipements médicaux (2024)', '49 M USD (France 60 %, Inde 24 %, États-Unis 5 %) ; importations 41 M USD', 'US ITA, 19/02/2026'],
            ['Exemple d\'entreprise', 'Natec Medical (2000), cathéters à ballonnet ; CA 2021 ≈ 16,9 M USD ; extension au Biotech Park de Côte d\'Or', 'PNUD SDG Investor Platform ; GBC, 2023'],
            ['Fabrication pharmaceutique', 'Une seule usine (filiale d\'un groupe indien selon plusieurs sources)', 'US ITA, 19/02/2026'],
            ['Dépendance à l\'import', '~75 % des médicaments importés par 48 grossistes ; Inde 39 %, France 11 %, Allemagne 7 %', 'US ITA, 19/02/2026'],
            ['Droits NPF', '0 % sur 100 % des lignes des chapitres 30 et 90 étudiées', 'SaaS ZLECAf, tarif MRA HS 2022'],
            ['Politique industrielle', '1 Md MUR (PSIP 2025/26-2029/30) pour les vaccins et la pharmacie ; congé fiscal de 8 ans', 'US ITA ; PNUD'],
            ['Régulation', 'Pharmacy Act 1983 (Pharmacy Board) ; Pharmacy Council Act 2015 ; pas d\'agence autonome', 'OMC TPR 2021']]
    fl.append(Paragraph('Tableau 7.1 — Profil santé de Maurice', CAP))
    fl.append(table(rows, [46 * mm, 88 * mm, 40 * mm]))
    fl.append(Paragraph('Données 2024-2026. Les chiffres du Freeport diffèrent selon les sources : EDB (797 M USD et 259 007 t en 2023) et Département d\'État américain (817 M USD en 2023, 842 M USD en 2024). '
                        'Nous retenons l\'EDB, source primaire.', SRC))
    fl.append(P("<b>Lecture.</b> Maurice a réussi une spécialisation de niche, celle des <b>dispositifs de classe III à forte valeur par kilo</b> (stents, cathéters), exportés par avion "
                "vers l'Europe. C'est exactement le profil de produit pour lequel une zone franche est optimale : intrants importés en franchise, valeur ajoutée technique, "
                "fret aérien marginal dans le coût. En revanche, l'île n'a pas de base de production de médicaments et reste un marché d'importation (154 M USD de "
                "médicaments dosés en 2024 selon BACI)."))
    fl.append(PageBreak())
    fl.append(h2('7.3 La ZLECAf exclut-elle les zones franches ? Non, elle les encadre'))
    fl.append(P("Une idée répandue veut que la ZLECAf, « comme les autres accords de libre-échange », exclue les zones franches de son champ d'application. "
                "<b>Les textes disent l'inverse.</b> Il faut distinguer trois plans :"))
    rows = [['Plan', 'Ce que prévoient les textes', 'Référence'],
            ['Champ territorial', 'Le « territoire » d\'un État partie inclut sa mer territoriale ; <b>aucune exclusion des zones franches</b>. Les ZES sont définies comme des parties du territoire à régime plus libéral.',
             'Annexe 2 (version janv. 2024), art. 1(u) et 1(w)'],
            ['Origine', 'Les produits de ZES sont <b>originaires</b> s\'ils respectent les règles de l\'Annexe 2. Les produits en transit dans une ZES restent sous contrôle douanier ; en cas de transformation, un nouveau certificat est délivré.',
             'Annexe 2, art. 9 ; Protocole commerce des marchandises, art. 23'],
            ['Préférence tarifaire', 'Chaque État applique les <b>tarifs préférentiels</b> de sa liste aux produits de ZES. <b>Aucune condition de paiement du droit NPF sur les intrants</b> n\'est posée.',
             'Règlement ministériel 1/2023 (Gaborone, 11-12/02/2023), § 3 et 6'],
            ['Garde-fous', 'Mesures correctives commerciales (antidumping, compensatoires, sauvegardes), protocole concurrence, clause des industries naissantes ; anti-contournement porté au règlement des différends.',
             'Règl. 1/2023, § 7, 13 et 14 ; Annexe 9'],
            ['Transparence', 'Notification de toutes les ZES au Secrétariat (registre), <b>enregistrement obligatoire</b> des entreprises exportatrices, rapport annuel, réexamen après 5 ans. Les freeports sont expressément visés.',
             'Règl. 1/2023, § 8 à 12 et 15, note 1'],
            ['Fiscalité et change', 'Hors du champ de l\'Accord : le règlement reconnaît le pouvoir souverain des États d\'accorder des incitations fiscales. Le traitement de change relève du droit national.',
             'Règl. 1/2023, préambule'],
            ['Points encore ouverts', 'Les « critères et questions relatifs aux ZES » de l\'art. 9 figurent toujours parmi les travaux en suspens.', 'Annexe 2, art. 42']]
    fl.append(Paragraph('Tableau 7.2 — Le régime ZLECAf des zones économiques spéciales', CAP))
    fl.append(table(rows, [30 * mm, 100 * mm, 44 * mm]))
    fl.append(Paragraph('Sources : Annexe 2 mise à jour (au-afcfta.org, janv. 2024) ; Règlement ministériel 1/2023, texte signé (tralac). Aucune décision postérieure du Conseil des ministres sur les ZES n\'a été identifiée au 27/09/2026.', SRC))
    fl.append(callout('Pourquoi la confusion ? Deux notions de « territoire »', [
        '<b>En droit douanier national</b>, une zone franche est traitée comme hors du territoire douanier (Convention de Kyoto révisée, annexe spécifique D) : une marchandise qui en sort vers le marché '
        'intérieur est une <b>importation</b>, taxée comme telle. C\'est vrai à Maurice comme en Algérie (loi 22-15).',
        '<b>En droit de la ZLECAf</b>, la zone franche fait partie du territoire de l\'État partie : le produit qui en sort vers un <b>autre</b> État partie peut revendiquer l\'origine et la préférence. '
        'Ces deux logiques se cumulent ; elles ne se contredisent pas.']))
    fl.append(PageBreak())
    fl.append(h2('7.4 Les autres accords de Maurice : même logique d\'encadrement'))
    rows = [['Accord', 'En vigueur', 'Traitement des zones franches', 'Statut de vérification'],
            ['ZLECAf', 'ratifiée le 30/09/2019', 'Admises sous conditions (art. 9, règl. 1/2023)', 'Texte lu'],
            ['ALE Maurice-Chine', '01/01/2021', 'Aucune clause spécifique ; règles d\'origine générales (valeur régionale ≥ 40 %), transit ≤ 6 mois', 'Texte intégral recherché'],
            ['CECPA Maurice-Inde', '01/04/2021', 'Les autorités des ZES indiennes sont habilitées à délivrer les certificats d\'origine : produits de ZES admis s\'ils sont originaires', 'Texte lu'],
            ['APE intérimaire UE (AfOA)', '14/05/2012 ; approfondissement conclu le 10/06/2026', 'Protocoles d\'origine UE : article type « zones franches » (contrôle douanier, non-substitution)', 'Clause type ; texte APE non relu'],
            ['SADC, COMESA', '—', 'Clauses de traitement des EPZ', 'Non vérifié']]
    fl.append(Paragraph('Tableau 7.3 — Zones franches et accords commerciaux de Maurice', CAP))
    fl.append(table(rows, [34 * mm, 34 * mm, 72 * mm, 34 * mm]))
    fl.append(Paragraph('Sources : textes des accords (MCCI, MRA), Commission européenne, OMC TPR 2021.', SRC))
    fl.append(P("<b>Ce qui change vraiment pour l'opérateur en zone franche</b>, c'est la <b>discipline de preuve</b> : comptabilité matières séparée, traçabilité des intrants "
                "non originaires, respect de la règle de produit (CTH ou 60 %), enregistrement auprès de l'autorité compétente. Un opérateur Freeport qui se contente "
                "de stocker, reconditionner et réexporter des produits asiatiques <b>ne crée pas d'origine</b> (opérations insuffisantes) et n'obtient aucune préférence."))
    fl.append(h2('7.5 Fiscalité et change : l\'avantage mauricien face à la ZLECAf'))
    fl += bullets([
        '<b>Change</b> : l\'Exchange Control Act est suspendu depuis <b>juillet 1994</b> ; aucune restriction sur les opérations courantes ni en capital, roupie flottante. Un opérateur peut facturer, '
        'encaisser et conserver des devises sans délai de rapatriement. C\'est l\'écart le plus net avec l\'Algérie (délai de rapatriement ramené à 120 jours par le règlement 26-02 du 23/07/2026).',
        '<b>Fiscalité</b> : 3 % sur les bénéfices d\'exportation (maintenu par le budget 2026-2027), 80 % d\'exonération partielle sur certains revenus étrangers, mais QDMTT à 15 % pour les grands groupes '
        'et « Fair Share Contribution » temporaire (2 % pour les sociétés au taux réduit, 2025-2028).',
        '<b>Risque ZLECAf</b> : un avantage fiscal <b>subordonné à l\'exportation</b> est, par nature, susceptible d\'être contesté par des droits compensateurs (Annexe 9, règl. 1/2023 § 13). '
        'Le risque est aujourd\'hui théorique pour les dispositifs médicaux (droits NPF nuls dans la plupart des destinations), mais il existe sur les marchés à droits élevés.'])
    fl.append(PageBreak())
    fl.append(h2('7.6 GAFI : la sortie de liste grise, un actif de conformité'))
    fl.append(P("Maurice a été placée sous <b>surveillance renforcée du GAFI en février 2020</b> et en est sortie le <b>21 octobre 2021</b>. L'Union européenne l'avait inscrite sur sa liste "
                "des pays tiers à haut risque (applicable au 1er octobre 2020) et l'en a retirée par le règlement délégué (UE) 2022/229 (en vigueur le 13 mars 2022). "
                "Au 27 septembre 2026, Maurice ne figure ni sur la liste grise du GAFI (plénière de juin 2026, 22 juridictions), ni sur les listes fiscales de l'UE "
                "(annexes I et II, mise à jour du 17/02/2026). Sa prochaine évaluation mutuelle par l'ESAAMLG commencera en <b>2027</b>, après une mission préparatoire du 14 au 18 décembre 2026 (L'Express, repris par allAfrica, 15/09/2026) ; la ministre des Services financiers y voit « un test important de notre juridiction » (Le Mauricien, 25/03/2026)."))
    fl.append(figure(C + 'g1_gafi.png', 'Figure 7.2 — Pays africains sous surveillance renforcée du GAFI, 2020-2026',
                     'Sources : communiqués du GAFI (plénières de février, juin et octobre), Bank of Mauritius, Trésor sud-africain (24/10/2025), ComplyAdvantage (22/06/2026). '
                     'Dates de plénière ; la page officielle du GAFI de juin 2026 a été consultée par recoupement.', maxh=78 * mm))
    fl.append(P("<b>Pourquoi c'est important dans la pharmacie.</b> Un pays en liste grise subit des diligences renforcées de ses banques correspondantes : lettres de crédit plus chères "
                "et plus lentes, refus de certaines opérations, surcoût de conformité. Pour un laboratoire qui répond à des appels d'offres de centrales d'achat (UNICEF, Fonds mondial, "
                "centrales nationales), ces frictions pèsent directement sur la compétitivité. Six pays africains restent sur la liste en septembre 2026 : Angola, Cameroun, "
                "Côte d'Ivoire, RD Congo, Kenya et Soudan du Sud. <b>L'Algérie en est sortie le 19 juin 2026</b>, mais reste sur la liste européenne des pays à haut risque "
                "(règlement délégué 2025/1184) tant que la Commission ne l'a pas retirée : aucun retrait n'était confirmé au 27/09/2026."))
    fl.append(callout('Note terminologique', [
        'GAFI (Groupe d\'action financière, FATF en anglais) : organe intergouvernemental de lutte contre le blanchiment et le financement du terrorisme ; sa « liste grise » '
        'recense les juridictions sous surveillance renforcée. À ne pas confondre avec la <b>GAFTA/ZALE</b> (Grande zone arabe de libre-échange), accord commercial dont l\'Algérie '
        'est membre, mais pas Maurice.'], bg=BLUE_L, bar=BLUE, title_color=BLUE))
    fl.append(PageBreak())
    fl.append(h2('7.7 Scénario chiffré : un cathéter mauricien vers l\'Algérie'))
    fl.append(P("Maurice figure parmi les neuf origines admises par l'Algérie (calendrier standard). Un cathéter fabriqué à Maurice (SH 9018.39), originaire, entre donc en Algérie "
                "en liste A, à droit nul en 2026. Le calcul ci-dessous, établi avec le calculateur fiscal algérien du SaaS, compare deux fournisseurs pour une valeur en douane de 100."))
    rows = [['Élément (base : valeur CAF = 100)', 'Origine hors ZLECAf (NPF)', 'Origine Maurice (ZLECAf)'],
            ['Droit de douane', '30,0', '0,0'], ['DAPS', '0,0', '0,0'], ['PRCT (2 %)', '2,0', '2,0'],
            ['<b>Charge hors TVA (coût définitif)</b>', '<b>32,0</b>', '<b>2,0</b>'],
            ['TVA 19 % (récupérable par un assujetti)', '25,1', '19,4'], ['Charge totale à l\'importation', '57,1', '21,4']]
    fl.append(Paragraph('Tableau 7.4 — Cathéter (SH 9018.39.10) importé en Algérie, septembre 2026', CAP))
    fl.append(table(rows, [80 * mm, 47 * mm, 47 * mm], align_right_from=1))
    fl.append(Paragraph('Source : SaaS ZLECAf (compute_dza_zlecaf_rate, relevé DGD, circulaire 482/2024). Hypothèses : produit originaire (règle du chapitre 90 : CTH ou ≤ 60 % de matières non originaires), '
                        'certificat d\'origine ZLECAf, opérateur Freeport enregistré conformément au règlement 1/2023.', SRC))
    fl += bullets([
        '<b>Marge préférentielle : 30 points de valeur CAF.</b> Un fabricant mauricien peut vendre jusqu\'à <b>29 % plus cher</b> (132/102 − 1) qu\'un concurrent hors ZLECAf et rester au même coût rendu hors TVA.',
        '<b>Piège de la règle d\'origine</b> : les parties de cathéters relèvent elles-mêmes de la position 90.18. Un assemblage à partir de composants importés de 90.18 ne satisfait pas le changement de position : '
        'il faut alors respecter le critère des 60 % de matières non originaires, ce qui exige un calcul de prix de revient documenté.',
        '<b>Barrière réelle</b> : l\'enregistrement du dispositif auprès de l\'ANPP et le programme d\'importation du ministère algérien, plus déterminants que le droit de douane.'])
    return fl
