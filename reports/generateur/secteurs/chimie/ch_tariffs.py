from layout import *
import json
SP = json.load(open(S + 'saas_chimie.json')); CS = SP['countries']; OF = SP['offers']
SV = json.load(open(S + 'served.json'))
C = S + 'charts/'
def f1(x): return '—' if x is None else (f'{x:.1f}'.replace('.', ','))

def ch_tariffs():
    fl = [chapter(3, 'Droits NPF : l\'escalade tarifaire'),
          P("Sur les 40 barèmes nationaux du SaaS (<b>30 958 lignes SH6</b> dans les 16 segments étudiés), la chimie de base et les engrais entrent à droits faibles, "
            "tandis que les cosmétiques, les savons, les détergents et les articles d'hygiène atteignent 20 à 43 %, et jusqu'à 112 % en Algérie avec le DAPS. "
            "C'est l'exact inverse du profil pharmaceutique : ici, la ZLECAf ouvre des marges considérables sur les produits de consommation.", LEAD)]
    fl.append(h2('3.1 Cartographie : 10 régimes × 16 segments'))
    fl.append(figure(C + 'k1_heat.png', 'Figure 3.1 — Droit NPF moyen par segment et par régime tarifaire (%)',
                     'Source : SaaS ZLECAf, barèmes nationaux (droit NPF appliqué, moyenne simple des lignes SH6). Hors DAPS algérien (voir chapitre 7). '
                     '*Égypte, parfums et huiles essentielles : moyenne tirée par les eaux de toilette alcoolisées (jusqu\'à 1 950 %). « – » : aucune ligne publiée.', maxh=100 * mm))
    fl.append(P("<b>Trois constats.</b> (i) L'<b>escalade tarifaire</b> est la règle : 0 à 5 % sur les produits chimiques de base, 5 à 15 % sur les intermédiaires, 20 à 43 % sur les produits "
                "finis de consommation (cosmétiques, savons, détergents, papier hygiénique). (ii) Les tarifs extérieurs communs structurent le continent : CEDEAO (20 % sur les cosmétiques, "
                "35 % sur certains savons et détergents), CAE (35 %), CEMAC (30 %). (iii) <b>Maurice et le Maroc font exception</b> : le Maroc applique 2,5 % aux cosmétiques et 25 % aux savons, "
                "Maurice une quasi-franchise."))
    fl.append(PageBreak())
    fl.append(h2('3.2 Structure par segment'))
    rows = [['Segment', 'Positions SH', 'Pays à 0 %', 'Moy. 40 pays', 'Maximum (pays)']]
    for g, n, pre in SP['groups']:
        v = [(i, c['groups'][g]['avg']) for i, c in CS.items() if g in c['groups']]
        z = sum(1 for _, x in v if x == 0); mx = max(v, key=lambda t: t[1])
        pos = ', '.join(pre) if len(pre) < 6 else f'{pre[0][:2]}.{pre[0][2:]} à {pre[-1][:2]}.{pre[-1][2:]}'
        rows.append([n, pos[:34], f'{z}/{len(v)}', f1(sum(x for _, x in v) / len(v)) + ' %', f'{f1(mx[1])} % ({mx[0]})'])
    fl.append(Paragraph('Tableau 3.1 — Droits NPF par segment, 40 barèmes', CAP))
    fl.append(table(rows, [56 * mm, 40 * mm, 20 * mm, 22 * mm, 36 * mm], align_right_from=2))
    fl.append(Paragraph('Source : SaaS ZLECAf. Moyenne simple des moyennes nationales. Égypte : maximum lié aux parfums alcoolisés. Principes actifs pharmaceutiques (29.36-29.41) traités dans le rapport Pharmaceutique & Santé.', SRC))
    fl.append(callout('Lecture pour l\'investisseur', [
        'La protection effective d\'un fabricant de détergents ou de cosmétiques africain est très élevée : il paie 0 à 5 % sur ses intrants chimiques (tensioactifs de base, soude, glycérine) '
        'et bénéficie de 20 à 35 % sur son produit fini. <b>C\'est ce qui explique la multiplication des usines de savons et de détergents sur le continent</b>, souvent au service d\'un seul marché national. '
        'La ZLECAf remet en cause ce modèle : un producteur efficace pourra servir plusieurs marchés à droit nul, et les usines sous-dimensionnées perdront leur rente tarifaire.']))
    fl.append(PageBreak())
    return fl

def ch_offers():
    fl = [chapter(4, 'Offres ZLECAf et taux servis'),
          P("À la différence des médicaments, entièrement libéralisés dans les offres, les cosmétiques, les savons et les articles d'hygiène sont le premier réservoir de lignes "
            "sensibles (B) et exclues (C) du champ étudié. Sur 337 lignes de parfums, cosmétiques, savons et détergents recensées dans les offres, <b>64 sont classées B ou C</b>.", LEAD)]
    fl.append(h2('4.1 Où se concentrent les lignes sensibles et exclues'))
    fl.append(figure(C + 'k4_offers.png', 'Figure 4.1 — Lignes classées B (sensibles) ou C (exclues) dans les offres e-Tariff Book, par segment',
                     'Source : SaaS ZLECAf, instantanés e-Tariff Book (17/08 et 13/09/2026). « n/t » : n lignes B ou C sur t lignes. « n.r. » : catégorie non renseignée dans l\'offre (CAE et CEDEAO '
                     'n\'ont pas publié leurs listes B et C sur ces lignes). Maroc : toutes les lignes de l\'extrait sont en liste A.', maxh=78 * mm))
    fl += bullets([
        '<b>CEMAC et Éthiopie</b> protègent intégralement le maquillage et les savons (5/5 et 6/6 lignes en B ou C) : l\'accès préférentiel à ces marchés sera nul (C) ou différé à 2030-2035 (B).',
        '<b>Égypte</b> : shampooings et capillaires en exclusion (3 lignes C), savons partiellement protégés ; l\'essentiel de la chimie de base est en A.',
        '<b>CAE et CEDEAO</b> : les lignes de cosmétiques et de savons ne portent aucune catégorie dans l\'offre publiée, signe que ces blocs n\'ont pas encore arrêté leurs listes sensibles. Prudence sur toute projection.',
        '<b>Chimie de base, engrais et plastiques</b> : presque tout est en catégorie A (plus de 97 % des lignes).'])
    fl.append(PageBreak())
    fl.append(h2('4.2 Les taux réellement servis en 2026'))
    D = [('DZA', 'Algérie'), ('EGY', 'Égypte'), ('KEN', 'Kenya'), ('MAR', 'Maroc'), ('ZAF', 'SACU')]
    O = [('EGY', 'Égypte'), ('DZA', 'Algérie'), ('TUN', 'Tunisie'), ('MUS', 'Maurice'), ('ZAF', 'Afr. du Sud'), ('KEN', 'Kenya'), ('NGA', 'Nigeria'), ('SEN', 'Sénégal')]
    rows = [['Destination (NPF)'] + [o[1] for o in O]]; ex = []
    for g, gl in [('C04', 'Engrais'), ('C07', 'Maquillage et soins de la peau'), ('C11', 'Savons'), ('C12', 'Détergents')]:
        rows.append([f'<b>{gl}</b>'] + [''] * len(O)); ex.append(('BACKGROUND', (0, len(rows) - 1), (-1, len(rows) - 1), TEAL_L))
        for d, dl in D:
            k0 = next((SV[f'{d}|{o}'][g] for o, _ in O if f'{d}|{o}' in SV and g in SV[f'{d}|{o}']), None)
            if k0 is None: continue
            r = [f"{dl} ({f1(k0['npf'])} %)"]
            for o, _ in O:
                x = SV.get(f'{d}|{o}', {}).get(g)
                r.append('—' if (o == d or not x) else f1(x['pref']))
            rows.append(r)
    fl.append(Paragraph('Tableau 4.1 — Droit moyen servi en 2026 par destination et origine (%), hors DAPS', CAP))
    fl.append(table(rows, [38 * mm] + [17 * mm] * len(O), align_right_from=1, extra=ex, zebra=False))
    fl.append(Paragraph('Source : calculateurs du SaaS ZLECAf, barèmes 2026. Taux égal au NPF : origine non admise par la destination ou ligne non servie. Maroc : calcul sur les lignes de l\'offre. '
                        'Algérie : le DAPS (80 % sur les cosmétiques) est levé pour les origines ZLECAf admises, ce qui double l\'écart (chapitre 7).', SRC))
    fl.append(P("<b>Lecture.</b> L'<b>Algérie</b> est de loin la destination la plus ouverte aux partenaires qu'elle admet : 30 % sur les cosmétiques, savons et détergents ramenés à 0 % pour l'Égypte, "
                "la Tunisie et Maurice, et à 12 % pour l'Afrique du Sud et le Kenya. Le <b>Kenya</b> démantèle lentement (35 % → 30,8 % en 2026 pour les cosmétiques) et n'admet pas l'origine algérienne. "
                "La <b>SACU</b> ramène les cosmétiques de 20 à 12,8 %. L'<b>Égypte</b> sert les savons (13,3 → 0,75 %) mais pas les détergents. Les origines ouest-africaines, non admises par l'Algérie, "
                "paient partout le NPF."))
    return fl

def ch_roo():
    fl = [PageBreak(), chapter(5, 'Règles d\'origine de la chimie'),
          P("Les chapitres 28 à 38 partagent une règle à trois options : changement de position (CTH), matières non originaires plafonnées à 60 % du prix départ usine, "
            "ou <b>règles de traitement chimique</b> de la note introductive 8 de l'Appendice IV. Les plastiques (39) et le papier (48) n'ont que les deux premières options.", LEAD)]
    rows = [['Règle de la note 8', 'Chapitres', 'Ce qui confère l\'origine'],
            ['1. Réaction chimique', '28 à 38', 'Toute réaction créant une molécule de structure nouvelle. Ne comptent pas : dissolution, élimination de solvant, ajout ou retrait d\'eau de cristallisation.'],
            ['2. Purification', '28 à 38', 'Réduction des impuretés rendant le produit apte à un usage pharmaceutique, <b>cosmétique</b>, alimentaire ou analytique. Le seuil en pourcentage reste entre crochets (non convenu).'],
            ['3. Mélanges', '30, 31, 33 à 38 (sauf 38.08)', 'Mélange délibéré et proportionnellement contrôlé, selon des spécifications prédéterminées, donnant un produit aux caractéristiques différentes de ses intrants.'],
            ['4. Granulométrie', '30, 31, 33', 'Modification contrôlée de la taille des particules (hors simple broyage ou pressage).'],
            ['5 à 7', '28 à 38', 'Matériaux de référence, séparation d\'isomères ; interdiction de la séparation d\'un mélange artificiel sans réaction chimique.']]
    fl.append(Paragraph('Tableau 5.1 — Les règles de traitement chimique (Appendice IV, note 8)', CAP))
    fl.append(table(rows, [34 * mm, 34 * mm, 106 * mm]))
    fl.append(Paragraph('Source : Appendice IV à l\'Annexe 2 (texte officiel, note 8, § 8.1 à 8.12) ; SaaS ZLECAf, zlecaf_rules_of_origin.json (statut AGREED pour les chapitres 28 à 39 et 48).', SRC))
    rows = [['Cas pratique', 'Voie d\'origine', 'Verdict'],
            ['Urée (31.02) à partir d\'ammoniac (28.14) importé', 'CTH, ou réaction chimique', 'Originaire'],
            ['Crème (33.04) par simple dilution ou mise en pot d\'une crème 33.04 importée', 'Aucune (même position, opération insuffisante)', '<b>Non originaire</b>'],
            ['Crème (33.04) formulée selon une fiche technique à partir de bases, actifs et parfums, y compris importés', 'Règle 3 (mélange contrôlé)', 'Originaire, sur preuve du procédé'],
            ['Lessive (34.02) à partir de LAS (34.02) importé, silicates et enzymes', 'Règle 3 (mélange contrôlé) ou ≤ 60 %', 'Originaire, sur preuve du procédé'],
            ['LAS par sulfonation de LAB importé', 'Règle 1 (réaction chimique)', 'Originaire'],
            ['Savon par saponification d\'huile (15.xx)', 'CTH et règle 1', 'Originaire'],
            ['Insecticide ménager (38.08) par mélange de principes actifs importés', 'Règle 3 exclue pour 38.08 : CTH ou ≤ 60 %', 'Selon les intrants'],
            ['Polyéthylène (39.01) à partir d\'éthylène (29.01)', 'CTH', 'Originaire'],
            ['Papier hygiénique (48.18) à partir de bobines mères (48.03)', 'CTH', 'Originaire']]
    fl.append(Paragraph('Tableau 5.2 — Application aux produits du périmètre', CAP))
    fl.append(table(rows, [80 * mm, 56 * mm, 38 * mm]))
    fl.append(Paragraph('Verdicts indicatifs, à confirmer par une décision anticipée de l\'administration des douanes. Les huiles végétales (15.xx), intrants des savons et cosmétiques, figuraient encore parmi les lignes « à convenir » dans la version consultée.', SRC))
    fl.append(callout('Ce que cela change pour les formulateurs de cosmétiques et de détergents', [
        'La règle des mélanges (note 8, règle 3) est plus favorable qu\'on ne le croit souvent : une <b>vraie formulation</b>, documentée par une fiche de fabrication, des spécifications et des contrôles '
        'qualité, confère l\'origine même si les matières sont importées et même sans changement de position. En revanche, la dilution, le reconditionnement ou la mise en flacon d\'un produit fini importé '
        'restent des opérations insuffisantes. <b>La preuve se fait par le dossier de fabrication</b> : c\'est lui que l\'administration du pays importateur pourra demander en vérification.'], bg=GREEN_L, bar=GREEN, title_color=GREEN))
    fl.append(P("<b>Cumul.</b> Les matières d'un autre État partie comptent comme originaires : un LAS égyptien, une huile de palme ivoirienne, un karité burkinabè ou une huile d'argan "
                "marocaine sécurisent en outre le critère des 60 %."))
    return fl
