from layout import *
import json
C = S + 'charts/'
O = json.load(open(S + 'oec_africa.json'))

def ch_market():
    tot = sum(v['tot'] for v in O.values()) / 1e9
    fl = [chapter(1, 'Le marché africain de la chimie et de l\'hygiène'),
          P(f"L'Afrique a importé <b>{tot:.0f} Md USD</b> de produits chimiques, d'engrais, de plastiques, de cosmétiques et de détergents en 2024 (OEC/BACI). "
            "Deux mondes coexistent : une chimie de base et des plastiques massivement importés d'Asie et du Golfe, où le commerce intra-africain est marginal ; "
            "et une industrie de consommation (savons, détergents, cosmétiques) déjà très régionale, où un tiers des achats se font entre Africains.".replace('.0f', ''), LEAD)]
    fl.append(kpis([(f'{tot:.0f} Md$', 'importations africaines 2024, chapitres 28-29, 31-34, 38 et 39', 'OEC / BACI, API tesseract, extraction du 27/09/2026'),
                    ('31,2 Md$', 'dont plastiques (SH 39) : 9 % seulement d\'origine africaine', 'OEC / BACI 2024'),
                    ('43 %', 'part africaine des importations d\'engrais : le Maroc premier fournisseur (1,76 Md$)', 'OEC / BACI 2024'),
                    ('35 %', 'part africaine des importations de savons et détergents (SH 34)', 'OEC / BACI 2024')], cols=4))
    fl.append(Spacer(1, 4))
    fl.append(figure(C + 'k5_africa.png', 'Figure 1.1 — Importations africaines par chapitre et part d\'origine africaine, 2024 (Md USD)',
                     'Source : OEC (BACI, HS 2017), API tesseract, requête « Importer Continent = Afrique », 2024. Entre parenthèses : part des fournisseurs africains. '
                     'SH 33 : la part africaine est gonflée par les concentrés d\'arômes réexportés par l\'Eswatini (0,62 Md USD).', maxh=64 * mm))
    rows = [['Chapitre', 'Import. 2024', 'Part africaine', 'Trois premiers fournisseurs (Md USD)']]
    for k, v in O.items():
        rows.append([k, f"{v['tot']/1e9:.2f}".replace('.', ','), f"{100*v['intra']/v['tot']:.0f} %",
                     ' ; '.join(f"{n} {x/1e9:.2f}".replace('.', ',') for n, x in v['top'][:3])])
    fl.append(Paragraph('Tableau 1.1 — Fournisseurs de l\'Afrique par chapitre, 2024', CAP))
    fl.append(table(rows, [44 * mm, 22 * mm, 22 * mm, 86 * mm], align_right_from=1))
    fl.append(Paragraph('Source : OEC / BACI 2024. Noms de pays tels que publiés par l\'OEC. Contrôle croisé : UN Comtrade (déclarations de 31 pays africains en 2024, donc sous-estimé) donne 4,35 Md USD pour le SH 33 et 25,9 Md USD pour le SH 39.', SRC))
    fl.append(PageBreak())
    fl.append(h2('1.1 Chimie de base, engrais et pétrochimie'))
    fl += bullets([
        '<b>Engrais : l\'Afrique exporte plus qu\'elle n\'importe</b> (17,9 Md USD exportés contre 5,9 Md USD importés en 2024, UN Comtrade). OCP a réalisé 114 Md MAD de chiffre d\'affaires en 2025 (+17 %), dont 18 % en Afrique au premier semestre ; '
        'Dangote exporte environ 77 % de ses 3 Mt d\'urée et lance une usine en Éthiopie (octobre 2025) ; l\'Égypte a exporté 6,85 Md USD de chimie et d\'engrais sur neuf mois 2025.',
        '<b>Chimie organique et plastiques : dépendance structurelle.</b> L\'Afrique couvre environ 19 % de ses importations de chimie organique par ses exportations. La Chine (8,9 Md USD) et l\'Arabie saoudite (4,2 Md USD) dominent les plastiques. '
        'Les nouvelles capacités (polypropylène de Dangote : 830 kt/an ; PP d\'Arzew : 550 kt/an en 2027 ; LAB de Skikda : 100 kt/an fin 2027) vont changer la donne en Afrique du Nord et de l\'Ouest.',
        '<b>Choc d\'Ormuz.</b> L\'urée est passée d\'environ 400 à plus de 850 USD/t en avril 2026 avant de redescendre à 453 USD/t en juin ; le DAP de 580 à 770 USD/t. Selon l\'OMC (10/07/2026), le Golfe fournit 24,8 % des engrais azotés mondiaux, '
        'et huit pays d\'Afrique de l\'Est et australe y sont les plus exposés.'])
    fl.append(h2('1.2 Cosmétiques, savons et détergents : l\'industrie la plus régionale'))
    fl.append(P("Les tailles de marché publiées par les cabinets divergent fortement (Afrique : 16,2 Md USD en 2025 selon Technavio ; Moyen-Orient et Afrique : 44 Md USD selon Euromonitor). "
                "Les résultats des groupes donnent une mesure plus sûre de la dynamique : Unilever Nigeria +43 % de chiffre d'affaires en 2025, PZ Cussons Nigeria +22 % (exercice 2026), "
                "L'Oréal +11 % sur neuf mois 2025 dans sa zone Afrique subsaharienne-Moyen-Orient. En 2023, 95 % des exportations africaines de savons et 81 % de celles de détergents "
                "sont allées vers d'autres pays africains (UN Comtrade) : ce sont les produits où la ZLECAf peut produire le plus vite des effets."))
    fl.append(P("<b>Les pôles exportateurs</b> : Afrique du Sud (0,52 Md USD de savons et détergents vers l'Afrique), Égypte (0,16 Md USD), Côte d'Ivoire et Togo, qui fournissent 175 et 59 M USD de "
                "produits de soin (SH 3304.99) aux marchés ouest-africains (OEC/BACI 2024). Le Maghreb est quasi absent de ces flux."))
    return fl

def ch_legal():
    fl = [PageBreak(), chapter(2, 'Réglementation : du SGH au mercure'),
          P("Dans la chimie et les cosmétiques, l'accès à un marché dépend autant de l'enregistrement des produits, de l'étiquetage des dangers et des listes de substances "
            "interdites que du droit de douane. L'Afrique avance en ordre dispersé.", LEAD)]
    rows = [['Thème', 'Situation 2026', 'Source'],
            ['SGH (classification et étiquetage des dangers)', 'En vigueur dans 3 pays seulement : Afrique du Sud, Zambie, Maurice ; projet pilote au Ghana, Kenya, Nigeria, Côte d\'Ivoire (2022-2026)', 'UNITAR ; recherche du 27/09/2026'],
            ['Cadre mondial sur les produits chimiques', 'Remplace la SAICM depuis Bonn (2023) : 28 cibles, la plupart à l\'horizon 2030', 'PNUE'],
            ['Mercure dans les cosmétiques', 'Amendement Minamata : interdiction des éclaircissants au mercure depuis le 25/04/2025 ; engagement de Libreville (janv. 2025) ; COP-6 (nov. 2025) associe Interpol et l\'OMD', 'PNUE ; IISD'],
            ['Hydroquinone', 'Interdite ou plafonnée dans au moins 10 pays : Afrique du Sud (2 %), Côte d\'Ivoire (2015), Ghana (2016), Rwanda, Kenya, Nigeria, Ouganda, Tanzanie, Cameroun, Soudan du Sud', 'Recherche documentaire (sources nationales)'],
            ['Cosmétiques : autorisations', 'Algérie : autorisation préalable du ministère du Commerce (décret 10-114). Maroc : enregistrement (loi 17-04) auprès de l\'AMMPS. Pas d\'harmonisation régionale CAE, CEDEAO ou SADC', 'commerce.gov.dz ; presse'],
            ['Plastiques à usage unique', '34 pays africains ont une interdiction totale ou partielle (Rwanda 2008, Kenya 2017, Tanzanie 2019)', 'Greenpeace Afrique'],
            ['REACH (UE)', 'La révision « REACH 2.0 » a été abandonnée en avril 2026 ; priorité aux restrictions PFAS et aux contrôles aux frontières', 'Commission européenne (ENVI)'],
            ['MACF / CBAM (UE)', 'Phase définitive depuis le 01/01/2026 pour l\'ammoniac, l\'urée, l\'acide nitrique et les engrais azotés et mixtes', 'Règlement (UE) 2023/956']]
    fl.append(Paragraph('Tableau 2.1 — Cadre réglementaire applicable au périmètre', CAP))
    fl.append(table(rows, [40 * mm, 94 * mm, 40 * mm]))
    fl.append(callout('Pourquoi c\'est un sujet commercial', [
        'L\'Afrique de l\'Ouest et centrale est inondée de cosmétiques non conformes (mercure, hydroquinone, corticoïdes). Un fabricant qui démontre la conformité de ses formules, '
        'étiquette selon les règles du pays et s\'enregistre auprès des autorités (NAFDAC au Nigeria, FDA au Ghana, KEBS au Kenya) dispose d\'un argument décisif auprès des '
        'distributeurs et des centrales d\'achat, qui redoutent les saisies. Le chapitre 6 détaille le cas des éclaircissants et des défrisants.'], bg=TEAL_L, bar=TEAL, title_color=TEAL))
    return fl
