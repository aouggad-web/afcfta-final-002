from layout import *
import json
SP = json.load(open(S + 'saas_pharma.json')); CS = SP['countries']; OF = SP['offers']
SV = json.load(open(S + 'served.json'))
C = S + 'charts/'
GN = {g: n for g, n, _ in SP['groups']}
GP = {g: p for g, _, p in SP['groups']}
def f1(x): return '—' if x is None else (f'{x:.1f}'.replace('.', ','))
def f0(x): return '—' if x is None else f'{x:.0f}'

def ch_tariffs():
    fl = [chapter(3, 'Droits NPF sur les produits de santé'),
          P("Premier constat, contre-intuitif pour qui connaît les barèmes agricoles : l'Afrique taxe peu les médicaments à l'entrée. "
            "Sur les 40 barèmes nationaux du SaaS (<b>5 463 lignes SH6</b> relevant des 15 segments santé), 31 appliquent un droit nul "
            "sur les médicaments dosés. La protection se loge ailleurs : dans les <b>consommables</b> (gants, seringues, masques), "
            "<b>l'hygiène</b>, les <b>emballages</b> et les <b>désinfectants</b>, où les droits atteignent 30 à 50 %.", LEAD)]
    fl.append(h2('3.1 Cartographie : 10 régimes × 15 segments'))
    fl.append(figure(C + 'p1_heat.png', 'Figure 3.1 — Droit NPF moyen par segment de santé et par régime tarifaire (%)',
                     'Source : SaaS ZLECAf, barèmes nationaux (droit NPF appliqué, moyenne simple des lignes SH6 du segment). Le chiffre entre parenthèses indique le nombre d\'États '
                     'appliquant le tarif extérieur commun. « – » : aucune ligne publiée pour ce segment. Maroc : barème national du SaaS (sous-positions nationales, jusqu\'à 17,5 % sur les médicaments '
                     'fabriqués localement).', maxh=100 * mm))
    fl.append(P("<b>Trois familles de régimes se dessinent.</b> (i) <b>Franchise quasi totale</b> sur les médicaments : CEDEAO (TEC catégorie 0), "
                "CAE, SACU, Maurice, Tunisie et Égypte. (ii) <b>Droit plancher de 5 %</b> : CEMAC, Algérie, Éthiopie, niveau qui renchérit le médicament "
                "sans réelle fonction de protection. (iii) <b>Protection ciblée</b> : le Maroc module le droit selon que la spécialité est fabriquée "
                "localement (10 à 25 %) ou non (2,5 %), faisant du tarif un instrument de politique industrielle. Dans ce paysage, la valeur "
                "ajoutée de la ZLECAf ne se mesure pas au droit supprimé sur les médicaments (souvent déjà nul), mais sur les <b>intrants</b> "
                "(principes actifs, emballages) et les <b>dispositifs et consommables</b>."))
    fl.append(PageBreak())
    fl.append(h2('3.2 Structure par segment : où se trouvent les droits'))
    rows = [['Segment', 'Positions SH', 'Pays à 0 %', 'Moy. 40 pays', 'Maximum (pays)']]
    stats = {}
    for g, n, pre in SP['groups']:
        v = [(i, c['groups'][g]['avg']) for i, c in CS.items() if g in c['groups']]
        z = sum(1 for _, x in v if x == 0); mx = max(v, key=lambda t: t[1])
        stats[g] = (len(v), z, sum(x for _, x in v) / len(v), mx)
        rows.append([n, ', '.join(pre)[:40], f'{z}/{len(v)}', f1(sum(x for _, x in v) / len(v)) + ' %', f'{f1(mx[1])} % ({mx[0]})'])
    fl.append(Paragraph('Tableau 3.1 — Droits NPF par segment, 40 barèmes', CAP))
    fl.append(table(rows, [52 * mm, 44 * mm, 20 * mm, 22 * mm, 36 * mm], align_right_from=2))
    fl.append(Paragraph('Source : SaaS ZLECAf. Moyenne simple des moyennes nationales. Codes ISO3 : DZA Algérie, MAR Maroc, TUN Tunisie, ETH Éthiopie, BDI Burundi, BEN Bénin, CAF Centrafrique.', SRC))
    fl.append(P("<b>L'escalade à rebours.</b> La logique tarifaire classique veut qu'un pays taxe peu ses intrants et davantage ses produits finis. "
                "Dans la santé, plusieurs barèmes font l'inverse : l'<b>Algérie taxe les antibiotiques en vrac (SH 2941) à 15 %</b> et les médicaments finis "
                "à 5 %. La CEMAC et la CEDEAO appliquent 5 % aux principes actifs et 0 à 5 % aux médicaments. Cette <b>protection effective négative</b> "
                "pénalise la formulation locale face à l'importation de produits finis (calcul au chapitre 8)."))
    fl.append(figure(C + 'p2_escal.png', 'Figure 3.2 — Principes actifs, médicaments, seringues et gants : quatre niveaux de droit NPF (%)',
                     'Source : SaaS ZLECAf. Antibiotiques : moyenne des lignes SH 2941 ; seringues : SH 9018.31 ; gants : SH 4015.11/12/19 et 4014.', maxh=72 * mm))
    fl.append(PageBreak())
    fl.append(h2('3.3 « Produits exemptés » : trois réalités à ne pas confondre'))
    fl.append(P("Le terme recouvre trois mécanismes juridiques distincts, dont les effets économiques diffèrent radicalement :"))
    rows = [['Notion', 'Base juridique', 'Ce que cela signifie', 'Dans la santé'],
            ['Exclusion de la libéralisation (catégorie C)', 'Protocole commerce des marchandises, art. 7 ; Modalités (3 % des lignes, 10 % des importations)', 'La ligne conserve le droit NPF ; aucune préférence ZLECAf, jamais.',
             '<b>Aucun médicament, vaccin ni principe actif</b> dans les 10 offres étudiées. Seuls l\'alcool éthylique, les déchets pharmaceutiques (CEMAC), certains emballages et articles d\'hygiène.'],
            ['Produit sensible (catégorie B)', 'Idem (7 % des lignes) ; démantèlement en 10 à 13 ans', 'Préférence différée : 0 % atteint en 2030-2033 (pays en développement), 2035 (PMA).',
             'Alcool à usage médical (CEMAC, Égypte), flacons et bouchons plastiques (CEMAC, Éthiopie, Tunisie), tenues de protection (Égypte), articles d\'hygiène (Éthiopie, Égypte).'],
            ['Exonération nationale (droit NPF nul, TVA exonérée)', 'Tarif national, TEC, code des impôts', 'Le produit entre déjà à 0 % de droit, pour tous les pays du monde.',
             '31 barèmes sur 40 à 0 % sur les médicaments dosés. La ZLECAf n\'apporte alors aucune marge tarifaire.']]
    fl.append(table(rows, [34 * mm, 42 * mm, 42 * mm, 56 * mm]))
    fl.append(Paragraph('Source : Accord ZLECAf (Protocole sur le commerce des marchandises), Modalités de négociation tarifaire (2019), e-Tariff Book (UA), SaaS ZLECAf.', SRC))
    fl.append(callout('Implication pour un exportateur de médicaments', [
        'Sur la plupart des marchés africains, la ZLECAf ne crée <b>aucune marge tarifaire</b> sur le médicament fini : le concurrent indien, chinois ou européen paie déjà 0 %. '
        'L\'avantage compétitif africain doit donc venir d\'ailleurs : proximité (délai, stock, fret), reconnaissance réglementaire, achats groupés, prix et financement. '
        'Les exceptions où la préférence compte vraiment sont le <b>Maroc</b> (jusqu\'à 25 % de droit NPF), la <b>CEMAC</b>, l\'<b>Algérie</b> et l\'<b>Éthiopie</b> (5 %), '
        'ainsi que les <b>dispositifs et consommables</b> partout où ils sont taxés à 10-35 %.']))
    fl.append(PageBreak())
    return fl

def ch_offers():
    fl = [chapter(4, 'Offres ZLECAf et préférences réellement servies'),
          P("Les offres tarifaires déposées à l'Union africaine (e-Tariff Book) classent chaque ligne en catégorie A (démantèlement en 5 ans, "
            "10 ans pour les PMA), B (sensible) ou C (exclue). Mais une offre n'est pas une préférence : il faut encore que la destination "
            "l'ait transposée en droit interne et qu'elle admette l'origine de l'exportateur. Ce chapitre distingue les deux niveaux.", LEAD)]
    fl.append(h2('4.1 Les offres : la santé en catégorie A, sans exception'))
    order = ['CEMAC', 'EAC', 'ECOWAS', 'EGY', 'ETH', 'MAR', 'TUN', 'ZMB', 'ZWE']
    lab = {'CEMAC': 'CEMAC', 'EAC': 'CAE', 'ECOWAS': 'CEDEAO', 'EGY': 'Égypte', 'ETH': 'Éthiopie', 'MAR': 'Maroc', 'TUN': 'Tunisie', 'ZMB': 'Zambie', 'ZWE': 'Zimbabwe'}
    rows = [['Offre', 'Principes actifs', 'Vaccins, sang', 'Médic. vrac', 'Médic. dosés', 'Pansements', 'Instruments', 'Lignes B/C (santé)']]
    for o in order:
        v = list(OF[o]['sch'].values())[0]
        def cell(g):
            c = v['cat'].get(g)
            if not c: return 'hors extrait'
            t = sum(c.values()); a = c.get('A', 0)
            return f'{a}/{t} A'
        rows.append([lab[o], cell('G01'), cell('G02'), cell('G03'), cell('G04'), cell('G05'), cell('G09'), str(len(v['exc']))])
    fl.append(Paragraph('Tableau 4.1 — Catégorie des lignes de santé dans les offres e-Tariff Book', CAP))
    fl.append(table(rows, [22 * mm, 24 * mm, 22 * mm, 21 * mm, 21 * mm, 21 * mm, 21 * mm, 22 * mm], align_right_from=1))
    fl.append(Paragraph('Source : SaaS ZLECAf, instantanés e-Tariff Book (collectés les 17/08 et 13/09/2026). « n/t A » : n lignes en catégorie A sur t lignes du segment. '
                        'CEDEAO : 4 lignes de médicaments dosés sans catégorie renseignée. « Hors extrait » : chapitre 29 absent de l\'instantané (Maroc, Tunisie, Zambie).', SRC))
    fl.append(P("Sur 780 lignes de principes actifs, vaccins et médicaments recensées dans les offres, <b>776 sont en catégorie A et 4 ne sont pas "
                "renseignées ; aucune n'est sensible ou exclue</b>. Les lignes B et C du champ santé portent sur des produits à forte "
                "sensibilité fiscale ou industrielle :"))
    rows = [['Offre', 'Ligne', 'Cat.', 'NPF', 'Désignation']]
    for o in order:
        v = list(OF[o]['sch'].values())[0]
        for hs, c, m, d in v['exc']:
            rows.append([lab[o], hs, c, m + ' %', d[:62]])
    fl.append(Paragraph('Tableau 4.2 — Lignes du champ santé classées sensibles (B) ou exclues (C)', CAP))
    fl.append(table(rows, [18 * mm, 22 * mm, 10 * mm, 14 * mm, 110 * mm], font=7))
    fl.append(Paragraph('Source : SaaS ZLECAf, e-Tariff Book. Égypte, 2208.90 : droit NPF de 3 000 % (spiritueux). Les emballages plastiques et le verre restent protégés dans trois offres : '
                        'un surcoût direct pour le conditionnement pharmaceutique régional.', SRC))
    fl.append(PageBreak())
    fl.append(h2('4.2 Des offres aux préférences servies'))
    fl.append(P("Au 27 septembre 2026, cinq destinations appliquent la ZLECAf à des origines nommément admises et selon un barème vérifiable ligne par ligne "
                "(registre d'application du SaaS) : <b>Afrique du Sud (SACU), Algérie, Égypte, Kenya et Maroc</b>. La Tunisie, l'Éthiopie, la CEDEAO et la CEMAC ont déposé une offre, mais aucune liste officielle d'origines admises n'a été trouvée. Le tableau ci-dessous "
                "donne le droit moyen réellement servi en 2026, par destination et par origine, sur trois segments clés."))
    D = [('DZA', 'Algérie'), ('EGY', 'Égypte'), ('KEN', 'Kenya'), ('MAR', 'Maroc'), ('ZAF', 'SACU')]
    O = [('EGY', 'Égypte'), ('DZA', 'Algérie'), ('MUS', 'Maurice'), ('TUN', 'Tunisie'), ('ZAF', 'Afr. du Sud'), ('KEN', 'Kenya'), ('GHA', 'Ghana'), ('SEN', 'Sénégal')]
    rows = [['Destination (NPF)'] + [o[1] for o in O]]
    ex = []
    for g, gl in [('G01', 'Principes actifs'), ('G04', 'Médicaments dosés'), ('G09', 'Instruments médicaux')]:
        rows.append([f'<b>{gl}</b>'] + [''] * len(O)); ex.append(('BACKGROUND', (0, len(rows) - 1), (-1, len(rows) - 1), TEAL_L))
        for d, dl in D:
            k0 = next((SV[f'{d}|{o}'][g] for o, _ in O if f'{d}|{o}' in SV and g in SV[f'{d}|{o}']), None)
            if k0 is None: continue
            r = [f"{dl} ({f1(k0['npf'])} %)"]
            for o, _ in O:
                if o == d: r.append('—'); continue
                x = SV.get(f'{d}|{o}', {}).get(g)
                r.append('—' if not x else f1(x['pref']))
            rows.append(r)
    fl.append(Paragraph('Tableau 4.3 — Droit moyen servi en 2026 par destination et origine (%)', CAP))
    fl.append(table(rows, [36 * mm] + [17.2 * mm] * len(O), align_right_from=1, extra=ex, zebra=False))
    fl.append(Paragraph('Source : calculateurs du SaaS ZLECAf (compute_dza/egy/ken_zlecaf_rate, resolve_official_preferential_rate), barèmes 2026, moyenne simple des lignes SH6 du segment. '
                        'Un taux égal au NPF signale une origine non admise par la destination (ex. Sénégal vers l\'Algérie) ou une ligne hors liste servie. '
                        'Maroc : droit NPF et taux servi calculés sur les lignes de l\'offre (voir l\'encadré).', SRC))
    fl.append(callout('Anomalie de données détectée pendant la production de ce rapport', [
        'Pour le Maroc, les codes nationaux à 10 chiffres du barème NPF du SaaS ne correspondent pas à ceux de l\'offre ZLECAf (nomenclature LF 2025). Conséquence : '
        'le calculateur renvoie le droit NPF au lieu du taux préférentiel pour la plupart des médicaments (ex. 3004.90.00.10). Recalculé sur les lignes de l\'offre, '
        'le droit servi aux origines P1 (dont l\'Algérie, l\'Égypte, Maurice et la Tunisie) est de <b>0 %</b> depuis 2025, et de <b>40 % du NPF</b> en 2026 pour les origines P2 '
        '(Afrique du Sud, Ghana, Kenya, Nigeria...). Le correctif est transmis à l\'équipe technique.'], bg=RED_L, bar=RED, title_color=RED))
    fl.append(PageBreak())
    fl.append(h2('4.3 Lecture : où la préférence crée-t-elle une marge ?'))
    fl += bullets([
        '<b>Algérie</b> : c\'est la destination où la préférence pèse le plus. Principes actifs 15 % → 0 % (Égypte, Maurice, Tunisie, Tanzanie) ou 6 % (partenaires en réciprocité : '
        'Afrique du Sud, Ghana, Kenya, Cameroun) ; instruments 11,3 % → 0 % ou 4,5 %. En revanche, les origines non admises (Maroc, Nigeria, Sénégal, Côte d\'Ivoire) paient le NPF.',
        '<b>Maroc</b> : médicaments dosés 4,9 % en moyenne (jusqu\'à 25 %) → 0 % pour les origines P1. <b>C\'est la plus forte marge sur les médicaments finis</b> parmi les destinations appliquées.',
        '<b>Égypte</b> : médicaments déjà à 0 % ; la marge porte sur les instruments (4,4 % → 0 %) et quelques principes actifs.',
        '<b>Kenya, SACU</b> : droits NPF déjà nuls ou quasi nuls sur le médicament ; la préférence est marginale. Au Kenya, la marge existe sur les désinfectants (35 %), '
        'les emballages (17 %) et les masques (25 %).'])
    fl.append(P("<b>Conclusion opérationnelle.</b> Pour un industriel africain, le principal gain tarifaire de la ZLECAf dans la santé est <b>à l'importation d'intrants</b> "
                "(principes actifs, verre, plastiques, dispositifs) plutôt qu'à l'exportation de médicaments finis. Cette asymétrie oriente les stratégies : localiser la formulation "
                "et le conditionnement, et sécuriser un approvisionnement en intrants d'origine africaine là où les droits NPF sont élevés."))
    return fl

def ch_roo():
    fl = [PageBreak(), chapter(5, 'Règles d\'origine : ce qui rend un médicament « africain »'),
          P("Pour bénéficier du taux ZLECAf, le produit doit être originaire au sens de l'Annexe 2 et de son Appendice IV (règles par produit, "
            "agréées pour tous les chapitres étudiés ici). Dans la santé, les règles sont parmi les plus souples de l'Accord : elles admettent qu'un médicament formulé "
            "en Afrique à partir de principes actifs importés d'Inde ou de Chine soit originaire.", LEAD)]
    rows = [['Chapitre / position', 'Règle (Appendice IV, texte adopté)', 'Conséquence pratique'],
            ['29 — Chimie organique (principes actifs)', 'Changement de position (CTH) ou matières non originaires ≤ 60 % du prix départ usine, ou règle de réaction chimique (note 8)',
             'Une synthèse locale (réaction chimique) confère l\'origine, même à partir d\'intermédiaires importés.'],
            ['30 — Produits pharmaceutiques', 'CTH, ou matières non originaires ≤ 60 % du prix départ usine, ou règle de réaction chimique',
             'API importé (SH 29xx) transformé en comprimé (SH 3004) : changement de position, <b>originaire</b>.'],
            ['38.22 — Réactifs de diagnostic', 'CTH ou ≤ 60 % de matières non originaires (règle du chapitre 38)', 'Assemblage de kits à partir de réactifs importés d\'autres positions : originaire.'],
            ['39 / 40 — Plastiques, gants', 'Ex-chapitre : CTH ou ≤ 60 %', 'Gants à partir de latex (4001) : originaires ; seringues (9018) : voir chapitre 90.'],
            ['90 — Instruments et dispositifs', 'CTH ou valeur des matières non originaires ≤ 60 %', 'Assemblage à partir de composants de positions différentes : généralement originaire.'],
            ['96.19 — Hygiène', 'Ex-chapitre 96 : CTH', 'Couches et serviettes à partir de pâte et non-tissés importés : originaires.']]
    fl.append(Paragraph('Tableau 5.1 — Règles d\'origine applicables aux produits de santé', CAP))
    fl.append(table(rows, [42 * mm, 66 * mm, 66 * mm]))
    fl.append(Paragraph('Source : SaaS ZLECAf, fichier zlecaf_rules_of_origin.json (Appendice IV, version de décembre 2023, statut AGREED pour les chapitres cités).', SRC))
    fl.append(h2('5.1 Trois pièges à éviter'))
    fl += bullets([
        '<b>Opérations insuffisantes (Annexe 2)</b> : le simple conditionnement, la mise en boîte, le mélange ou la division de lots ne confèrent jamais l\'origine, '
        'même si le code SH change. Le passage d\'un médicament en vrac (SH 3003) à une présentation dosée (SH 3004) par simple mise sous blister d\'un produit fini importé '
        'reste une opération à risque : il faut une <b>vraie formulation</b> (granulation, compression, stérilisation, remplissage aseptique).',
        '<b>Règle des 60 %</b> : pour un produit à forte valeur d\'API importé (biologiques, anticancéreux), l\'alternative « valeur » peut échouer si l\'API dépasse 60 % du prix départ usine ; '
        'la règle CTH reste alors la voie à privilégier.',
        '<b>Zones économiques spéciales</b> : la règle d\'origine est satisfaite, mais le produit fabriqué en zone franche relève d\'un régime particulier (Annexe 2, art. 9) '
        'traité au chapitre 7 à partir du cas de Maurice.'])
    fl.append(callout('Le cumul africain : un levier sous-utilisé', [
        'L\'Annexe 2 (cumul de l\'origine) permet de compter comme originaires les matières d\'un autre État partie. Exemple : un API égyptien ou sud-africain incorporé dans un médicament '
        'algérien, puis un flacon tunisien : tout est originaire. Dans la santé, le cumul permet surtout de sécuriser la règle des 60 % sur les produits à forte valeur d\'intrants.'], bg=GREEN_L, bar=GREEN, title_color=GREEN))
    return fl
