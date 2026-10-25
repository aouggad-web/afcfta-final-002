from layout import *
import json
C = S + 'charts/'
SPC = json.load(open(S + 'oec_special.json'))

def ch_segments():
    fl = [PageBreak(), chapter(6, 'Opportunités par segment'),
          P("En croisant la demande africaine (OEC/BACI, module Opportunités du SaaS), les droits NPF, le statut dans les offres et la règle d'origine, dix segments se détachent. "
            "Les produits spécialement développés pour les consommateurs africains, les éclaircissants et les défrisants, font l'objet d'une section à part, car leur potentiel "
            "est aussi grand que leur risque réglementaire.", LEAD)]
    rows = [['Segment (SH)', 'Demande africaine 2024', 'Droits NPF', 'Offres ZLECAf', 'Opportunité'],
            ['Urée (31.02.10)', '1,3 Md USD ; Afr. du Sud, Zambie, Malawi, Togo', '0 à 5 %', 'A', 'Réorienter une partie des exportations d\'Europe (MACF) vers l\'Afrique australe et de l\'Ouest'],
            ['Ammoniac (28.14.10)', '1,7 Md USD ; Maroc (1,6), Afr. du Sud, Tunisie', '0 à 5 %', 'A', 'Tunisie (GCT) ; Maroc fermé de fait'],
            ['Polyéthylène, polypropylène (39.01, 39.02)', '2,2 et 2,2 Md USD ; Égypte, Nigeria, Maroc', '0 à 10 %', 'A', 'PP d\'Arzew (2027) : 430 kt/an exportables face à Dangote et au Golfe'],
            ['Méthanol (29.05.11)', '0,1 Md USD ; Égypte, Nigeria, Afr. du Sud', '0 à 10 %', 'A', 'Égypte déjà cliente (31 % des ventes algériennes)'],
            ['Soins, maquillage (33.04.99)', '1,1 Md USD ; Afr. du Sud, Maroc, Ghana, Nigeria', '20 à 43 %', 'B ou C dans 4 offres', 'Marques régionales conformes ; concurrence ivoirienne et togolaise'],
            ['Capillaires (33.05)', '0,23 Md USD (33.05.90)', '20 à 43 %', 'B ou C (Égypte, CEMAC, Tunisie)', 'Soins pour cheveux texturés (voir 6.2)'],
            ['Détergents au détail (34.02.20)', '0,56 Md USD ; RD Congo, Maroc, Libye, Afr. du Sud', '11 à 35 %', 'A ou B', 'Poudres et liquides en petits formats ; avantage logistique (7.6)'],
            ['Savons (34.01.19)', '0,31 Md USD ; Tanzanie, Mali, Soudan, Ghana', '20 à 35 %', 'C (CEMAC) ; B (Éthiopie)', 'Savons de ménage : marché très régional (95 % intra-africain)'],
            ['Couches, serviettes (96.19)', '0,87 Md USD ; Afr. du Sud, Libye, Maroc, Zimbabwe', '0 à 43 %', 'B (CEMAC, Éthiopie)', 'Faderco déjà exportateur ; Libye premier client proche'],
            ['Javel, désinfectants (28.28, 38.08)', 'Faible en valeur, forte en volume', '12 à 35 %', 'A', 'Produits volumineux : fabrication près des marchés']]
    fl.append(Paragraph('Tableau 6.1 — Matrice des opportunités par segment', CAP))
    fl.append(table(rows, [36 * mm, 42 * mm, 18 * mm, 26 * mm, 52 * mm], font=7))
    fl.append(Paragraph('Sources : BACI via le SaaS (importations 2024 des pays africains hors Algérie) ; barèmes, offres et règles d\'origine du SaaS.', SRC))
    return fl

def ch_special():
    fl = [PageBreak(), h2('6.2 Produits conçus pour l\'Afrique : éclaircissants, défrisants, cheveux texturés')]
    fl.append(P("Deux familles de produits ont été développées spécifiquement pour les consommateurs africains : les <b>éclaircissants</b> (ou « unifiants ») de la peau, "
                "et les <b>défrisants et lisseurs</b> capillaires, auxquels s'ajoute l'immense marché des mèches et perruques. La demande est massive, mais c'est aussi le terrain "
                "où les interdictions, les saisies et les contentieux se multiplient."))
    rows = [['Produit (SH 2017)', 'Import. africaines 2024', 'Premiers importateurs', 'Premiers fournisseurs']]
    lab = {'Défrisants, permanentes (330520)': 'Défrisants, permanentes (33.05.20)', 'Autres capillaires (330590)': 'Autres capillaires (33.05.90)',
           'Soins, maquillage n.d.a. (330499)': 'Soins de la peau, dont éclaircissants (33.04.99)', 'Perruques en cheveux humains (670420)': 'Perruques et postiches en cheveux humains (67.04.20)',
           'Mèches et postiches synthétiques (670419)': 'Mèches et postiches synthétiques (67.04.19)'}
    FR = {'South Africa': 'Afr. du Sud', 'Morocco': 'Maroc', 'Ghana': 'Ghana', 'Nigeria': 'Nigeria', 'Tanzania': 'Tanzanie', 'Libya': 'Libye', 'Egypt': 'Égypte', 'Tunisia': 'Tunisie',
          'Democratic Republic of the Congo': 'RD Congo', 'Burkina Faso': 'Burkina', 'Mali': 'Mali', 'Namibia': 'Namibie', 'Benin': 'Bénin', 'Cameroon': 'Cameroun', "Cote d'Ivoire": 'Côte d\'Ivoire',
          'Uganda': 'Ouganda', 'China': 'Chine', 'France': 'France', 'Italy': 'Italie', 'Togo': 'Togo', 'Spain': 'Espagne', 'Poland': 'Pologne', 'United States': 'États-Unis', 'India': 'Inde', 'Kenya': 'Kenya', 'Senegal': 'Sénégal', 'Mozambique': 'Mozambique', 'Brazil': 'Brésil', 'Algeria': 'Algérie'}
    for k, l in lab.items():
        v = SPC.get(k)
        if not v: continue
        imp = ', '.join(f"{FR.get(n, n)} {x/1e6:.0f}" for n, x in v['imp'][:4]); exp = ', '.join(f"{FR.get(n, n)} {x/1e6:.0f}" for n, x in v['exp'][:4])
        rows.append([l, f"{v['tot']/1e6:,.0f} M$".replace(',', ' '), imp, exp])
    fl.append(Paragraph('Tableau 6.2 — Commerce africain des produits capillaires et de soin, 2024 (M USD)', CAP))
    fl.append(table(rows, [52 * mm, 24 * mm, 50 * mm, 48 * mm], font=7))
    fl.append(Paragraph('Source : OEC / BACI (HS 2017), API tesseract, importations des pays africains en 2024. Le code 33.04.99 regroupe tous les soins de la peau : les éclaircissants n\'y sont pas isolés. '
                        'Les données déclarées sont fragiles : WITS donne 1,9 M USD d\'importations nigérianes de perruques synthétiques en 2023, contre 139 M USD en 2022 selon l\'OEC.', SRC))
    fl.append(h2('Éclaircissants : un marché à reconquérir par la conformité'))
    fl += bullets([
        '<b>Demande</b> : selon l\'OMS, 77 % des femmes au Nigeria, 59 % au Togo, 35 % en Afrique du Sud, 27 % au Sénégal et 25 % au Mali utilisent ou ont utilisé des produits éclaircissants (données anciennes, années 2000, '
        'toujours citées) ; l\'OMS projette le marché mondial à 16,4 Md USD en 2032 (05/05/2026). La <b>Côte d\'Ivoire</b> est le hub régional (175 M USD de soins de la peau exportés vers l\'Afrique en 2024, OEC) ; '
        'les crèmes au mercure viennent surtout d\'Asie et se vendent en ligne.',
        '<b>Interdictions</b> : mercure banni par la Convention de Minamata (l\'Algérie y est Partie depuis le 28/02/2023) ; hydroquinone interdite ou plafonnée en Côte d\'Ivoire (décret 2015-288, 2 % ; l\'AIRP réclame '
        'l\'interdiction totale, juillet 2026), au Ghana (0 % depuis 2016), au Rwanda, au Kenya (131 marques interdites par le KEBS en 2022), au Gabon (arrêté du 24/10/2023, jusqu\'à 5 ans de prison) et au Nigeria '
        '(2 % ; la NAFDAC a qualifié la dépigmentation d\'urgence de santé publique en février 2024 et mené des raids sur 137 camions en 2025). Les corticoïdes sont proscrits dans les cosmétiques.',
        '<b>Actifs admis</b> (référence européenne, règlement (UE) 2024/996) : alpha-arbutine jusqu\'à 2 % pour le visage et 0,5 % pour le corps, acide kojique jusqu\'à 1 % ; niacinamide, vitamine C, réglisse.'])
    fl.append(h2('Défrisants et lisseurs : un risque juridique en hausse'))
    fl += bullets([
        '<b>Marché</b> : soins capillaires en Afrique estimés à 3,5 Md USD en 2025 (Technavio), avec un basculement vers le cheveu naturel (environ 66 % des Sud-Africaines sans défrisant). Les défrisants (33.05.20) '
        'pèsent 32 M USD d\'importations africaines, fournies par l\'Afrique du Sud, la Côte d\'Ivoire (Gandour : Teknika ; SIVOP : Clair-Liss) et l\'Ouganda ; les perruques en cheveux humains 700 M USD, presque '
        'entièrement chinoises (OEC 2024).',
        '<b>Réglementation</b> : dans l\'UE, soude caustique limitée à 2 % (usage général) et 4,5 % (usage professionnel), formaldéhyde interdit dans les lisseurs depuis 2019 ; aux États-Unis, le projet d\'interdiction du formaldéhyde '
        'par la FDA a manqué ses échéances (publication visée en novembre 2026) ; au Brésil, l\'ANVISA a exclu l\'acide glyoxylique (juillet 2025).',
        '<b>Santé et contentieux</b> : l\'étude NIH Sister Study (2022) associe l\'usage fréquent de défrisants à un risque de cancer de l\'utérus de 4,05 % à 70 ans contre 1,64 % ; aux États-Unis, environ 11 900 plaintes '
        'sont regroupées (MDL 3060), sans procès avant 2027 (sources : cabinets d\'avocats).'])
    fl.append(callout('Positionnement recommandé pour un fabricant algérien', [
        'Aucun fabricant algérien de défrisants ou d\'éclaircissants orienté vers l\'Afrique n\'a été identifié : le créneau est ouvert, mais il faut y entrer par la <b>conformité</b>. '
        '(i) Formules « éclat, anti-taches, unifiant » à 0 % d\'hydroquinone, sans mercure ni corticoïdes, conformes aux listes européennes reprises par la réglementation algérienne (décret 10-114) ; '
        'pas d\'allégation « blanchissant », interdite en Afrique du Sud. (ii) Priorité aux soins pour cheveux naturels et texturés (beurres, huiles, crèmes coiffantes), plutôt qu\'aux défrisants. '
        '(iii) Certification halal (IANOR, OIC-SMIIC 4:2018) et dossiers d\'enregistrement par marché : NAFDAC au Nigeria (représentant local, certificat de libre vente, rapport BPF, validité 5 ans), '
        'AIRP en Côte d\'Ivoire. (iv) Filières africaines d\'actifs (karité burkinabè, argan, huile de palme) pour sécuriser l\'origine par cumul.'], bg=TEAL_L, bar=TEAL, title_color=TEAL))
    fl.append(Paragraph('Sources : OMS (05/05/2026), OEC/BACI, WITS, NAFDAC, KEBS, AIRP, règlement (UE) 2024/996, FDA, ANVISA, NIH, recherche documentaire du 27/09/2026. À vérifier avant toute décision : '
                        'statut de l\'hydroquinone dans les annexes algériennes, textes applicables au Sénégal et en Mauritanie.', SRC))
    return fl
