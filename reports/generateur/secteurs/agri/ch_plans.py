"""Chapitres propres aux quatre plans d'action (producteurs, industriels, négoce, intrants).

Les chiffres externes proviennent des notes de recherche datées (recherche/*.md) ; les cibles et les
taux proviennent exclusivement de cibles.json (voir ch_verif.py).
"""
from layout import *
from ch_verif import *
from contradictions import ref, code_nomenclature
import json
import statistics as stt

SECT = json.load(open(S + 'saas_stats.json'))['sectors_def']


def sid_of(hs):
    for sid, _, pre in SECT:
        if hs.startswith(tuple(pre)):
            return sid
    return None


def cibles_filiere(sid, n=4):
    """Puces « Cibles & opportunités » d'une fiche filière, générées depuis cibles.json."""
    sel = [x for x in filtre(CB['classement'], verdicts=('RETENUE',), n=400) if sid_of(x['hs']) == sid][:n]
    out = []
    for x in sel:
        alt = autres_origines(CB['classement'], x, 2)
        v = vigilance(x)
        out.append(f"<b>{PAYS.get(x['o'], x['o'])}{' (et ' + ', '.join(alt) + ')' if alt else ''} → {DEST.get(x['d'], PAYS.get(x['d'], x['d']))}</b> : "
                   f"{lib(x['hs']).lower()} ({sh(x['hs'])}), {fmt_t(x['npf'])} % → <b>{fmt_t(x['pref'])} %</b> ; marché de {fmt_m(x['imp_dest'])} M$/an"
                   + (f" ; <i>{v}</i>" if v else '') + '.')
    nich = [x for x in CB['classement'] if x['verdict'] == 'CRÉNEAU' and sid_of(x['hs']) == sid][:1]
    for x in nich:
        out.append(f"<b>Créneau seulement</b> — {PAYS.get(x['o'], x['o'])} → {DEST.get(x['d'], PAYS.get(x['d'], x['d']))}, {lib(x['hs']).lower()} : {fr(x['motifs'][0])}.")
    faux = [x for x in CB['audit'] if x['verdict'] == 'REJETÉE' and sid_of(x['hs']) == sid][:1]
    for x in faux:
        c = code_nomenclature(x['d'], x['hs'])
        if c:  # SH6 citée marginale mais position SH4 importante : contradiction exposée, pas « fausse piste »
            out.append(f"<b><font color='#C0493D'>Contradiction</font></b> — {PAYS.get(x['o'], x['o'])} → {DEST.get(x['d'], PAYS.get(x['d'], x['d']))}, {lib(x['hs']).lower()} : "
                       f"{fmt_m(x['imp_dest'])} M$ importés en {sh(x['hs'])}, mais {fmt_m(x['sh4']['imp_dest'])} M$ pour la position {x['hs'][:4]}" + ref(c) + '.')
        else:
            out.append(f"<b><font color='#C0493D'>Fausse piste</font></b> — {PAYS.get(x['o'], x['o'])} → {DEST.get(x['d'], PAYS.get(x['d'], x['d']))}, {lib(x['hs']).lower()} : {fr(x['motifs'][0])}.")
    if not sel:
        out.insert(0, "Aucune cible de la filière ne passe en 2026 les trois filtres (marge servie, marché ≥ 5 M$, offre ≥ 5 M$) sur les cinq destinations appliquées : "
                      "l'enjeu est ailleurs (marchés sans préférence, catégorie B à partir de 2030, mesures non tarifaires).")
    return out


# ---------------------------------------------------------------- cibles par édition
PARAM = {
    'producteurs': dict(chap=('01', '14'), titre='Cibles vérifiées : produits bruts', lead=
                        "Les produits bruts (SH 01 à 14) bénéficient des règles d'origine les plus simples — « entièrement obtenu » — mais les marchés qui les protègent le plus "
                        "sont aussi ceux qui les produisent. Le filtre du marché réel élimine ici la plupart des fausses pistes : un taux à 0 % ne sert à rien sans acheteur."),
    'industriels': dict(chap=('15', '24'), titre='Cibles vérifiées : produits transformés', lead=
                        "Les produits transformés (SH 15 à 24) concentrent les droits les plus élevés — donc les marges préférentielles les plus fortes — mais aussi les exclusions "
                        "(listes B et C) et les règles d'origine les plus exigeantes. Chaque cible ci-dessous a une marge servie en 2026, un marché importateur réel et une offre d'origine réelle."),
    'negoce': dict(chap=('01', '24'), titre='Top 25 vérifié, créneaux et fausses pistes', lead=
                   "Pour un négociant, une cible n'est utile que si trois conditions sont réunies : un taux servi, un acheteur et un vendeur. Le classement ci-dessous les combine "
                   "dans un indicateur simple — la valeur annuelle de la marge sur le marché accessible (min(demande, offre) × marge) — et publie aussi les cibles écartées."),
    'intrants': dict(chap=None, titre='Cibles vérifiées : intrants et équipements', lead=
                     "Les droits sur les intrants sont déjà bas : la préférence ZLECAf compte surtout en Algérie (engrais, phytosanitaires) et au Kenya (semences). "
                     "Le filtre du marché réel est décisif : l'offre africaine de machines est quasi inexistante, les échanges portent sur les engrais, les tourteaux et les aliments."),
}


def ch_cibles(ed, num=7):
    p = PARAM[ed]
    liste = CB['intrants'] if ed == 'intrants' else CB['classement']
    fl = [chapter(num, p['titre']), P(p['lead'], LEAD)]
    n = 25 if ed == 'negoce' else 18
    sel = filtre(liste, chap=p['chap'], n=n)
    fl += tableau_cibles(sel, liste, f'Tableau {num}.1 — Cibles retenues : taux servi, marché réel, offre et vigilance')
    fl.append(PageBreak())
    nich = filtre(liste, chap=p['chap'], verdicts=('CRÉNEAU',), n=8)
    if nich:
        fl.append(h2(f'{num}.2 Créneaux : marchés exportateurs nets'))
        fl.append(P("Ces destinations exportent davantage le produit qu'elles ne l'importent. Une marge préférentielle y existe, mais le débouché se limite à la contre-saison, "
                    "à une gamme absente de la production locale ou à des volumes ponctuels. Les traiter comme des marchés prioritaires serait une erreur."))
        fl += tableau_cibles(nich, liste, f'Tableau {num}.2 — Créneaux (destination exportatrice nette)', avec_niche=True)
    if ed != 'intrants':
        fl.append(h2(f'{num}.3 Audit des cibles de l\'édition précédente'))
        fl.append(P("L'édition T3 2026 (rapport unique) publiait des cibles vérifiées sur le seul critère du taux servi. Toutes ont été repassées aux trois filtres. "
                    "Les cibles rejetées ne sont plus recommandées ; les motifs sont publiés pour que le lecteur puisse juger."))
        fl += errata(filtre_chap=None if ed == 'negoce' else p['chap'])
    return fl


# ---------------------------------------------------------------- PRODUCTEURS : froid, semences
def ch_froid(num=8):
    fl = [chapter(num, 'Chaîne du froid, semences et périssables'),
          P("Pour un producteur de fruits, de légumes, de viande, de lait ou de poisson, la préférence tarifaire ne vaut que si le produit arrive vendable. "
            "Le froid est la première condition d'accès aux marchés africains — et le premier poste de coût après le fret.", LEAD)]
    fl.append(kpis([('23,0 %', 'pertes entre récolte et détail en Afrique subsaharienne (2023) selon la FAO ; les agriculteurs déclarent 1,4 à 5,9 % pour le maïs (LSMS-ISA)' + ref('C01'), 'FAO, ODD 12.3.1 ; Banque mondiale'),
                    ('25,4 %', 'pertes mondiales sur les fruits et légumes (2023) ; céréales et légumineuses : 8,4 %', 'FAO, ODD 12.3.1'),
                    ('3 $/h', 'branchement d\'un reefer 40\' au port de Mombasa (≈ 72 $/jour), tarif du 15/09/2025', 'KPA, barème officiel'),
                    ('+58 %', 'surcharge reefer sur la manutention d\'un 40\' à Durban (2 271 ZAR + 3 917 ZAR), T1 2026', 'Transnet DGT, barème officiel')], cols=4))
    fl.append(h2(f'{num}.1 Ce que coûte le froid'))
    rows = [['Poste', 'Donnée', 'Date', 'Source (statut)'],
            ['Branchement reefer, Mombasa', '2 $/h (20\'), 3 $/h (40\') ; manutention export 60 / 90 $', '15/09/2025', 'KPA (primaire)'],
            ['Manutention reefer, Durban', '40\' : 3 917 ZAR + surcharge reefer 2 271 ZAR ; électricité 754 ZAR/jour', 'T1 2026', 'Transnet DGT (primaire)'],
            ['Surcoût reefer / conteneur sec', '+40 à 80 % sur les routes égyptiennes', '31/08/2026', 'Transitaire (secondaire)'],
            ['Surcharge de guerre, agrumes égyptiens', '3 000 à 5 000 $ par conteneur selon un exportateur ; 100 à 300 $ selon un transitaire', 'saison 2025/26', Paragraph('Presse (secondaire)' + ref('C02'), TD)],
            ['Transit Kenya → Europe', '18-20 jours avant la crise, 40-45 jours par le Cap (FPEAK) ; +10 à 14 jours seulement selon d\'autres sources', '09/2024 ; 2025-26', Paragraph('Presse (secondaire)' + ref('C03'), TD)],
            ['Pénurie de reefers', 'Jusqu\'à 55 % de la demande de pointe non couverte à Durban et Mombasa', '2024', 'ONE via presse (secondaire)'],
            ['Séjour des conteneurs à Mombasa', '104 h à l\'import (objectif 48 h) ; attente avant accostage > 50 h', 'S1 2025', 'Observatoire du corridor Nord (primaire)']]
    fl.append(Paragraph(f'Tableau {num}.1 — Les coûts du froid sur les corridors documentés', CAP))
    fl.append(table(rows, [42 * mm, 70 * mm, 20 * mm, CW - 132 * mm], font=7))
    fl.append(Paragraph('Aucun taux reefer 40\' n\'est publié pour Alexandrie–Mombasa, Tanger/Casablanca–Abidjan/Dakar ou Durban–Mombasa : le coût rendu d\'un périssable intra-africain '
                        'doit être établi sur devis. Repère mondial : Drewry WCI composite 4 468 $ par 40\' sec au 24/09/2026.', SRC))
    fl.append(h2(f'{num}.2 Capacités et investissements récents'))
    rows = [['Pays', 'Capacité frigorifique documentée', 'Projets 2024-2026'],
            ['Algérie', '2 984 chambres froides, 3,5 M m³ (ministère, 2021)', 'Crédit « Tabrid » à taux zéro jusqu\'à 150 M DZD pour des chambres de 300 à 5 000 m³ (2025)'],
            ['Maroc', '≈ 2,2 Mt (secondaire, sans source officielle)', 'Service Atlas DP World Agadir–Casablanca–Londres (1 000 reefers 40\', 11/2025) ; Ifria (IFC, 9,4 M$)'],
            ['Égypte', 'Capacité officielle non publiée', 'DP World × Elsewedy : 25 000 palettes, 29 M$, 6th of October City (2025-2026)'],
            ['Kenya', 'ARCH : 18 000 t ; Cold Solutions : ≈ 20 000 palettes', 'Cold Solutions : +19 M$ pour Mombasa (01/2026) ; ≈ 1 000 unités solaires (UNCDF)'],
            ['Afrique du Sud', Paragraph('400 000 à 600 000 positions palettes (estimation du secteur) ; 745 000 selon un autre modèle' + ref('C04'), TD), 'Maersk Belcon, Le Cap : 10 088 palettes, 240 prises reefer (10/2025)'],
            ['Nigeria', Paragraph('300 000 m³ (2023) ; < 1 000 camions frigorifiques opérationnels, pour un besoin de 25 000 (NAN) ou de 5 000 (OTACCWA)' + ref('C05'), TD), 'ColdHubs : > 50 chambres solaires, 42 000 t sauvées']]
    fl.append(Paragraph(f'Tableau {num}.2 — Froid : capacités et projets par pays', CAP))
    fl.append(table(rows, [26 * mm, 70 * mm, CW - 96 * mm], font=7))
    fl.append(Paragraph('Sources : ministère algérien de l\'Agriculture (2021) ; IIF/IIR (16/05/2025) ; BEI ; Engineering News (28/10/2025) ; Daily News Egypt (17/09/2025) ; The National (04/09/2025) ; ColdHubs (2025). '
                        'Les chiffres marqués secondaires n\'ont pas de source officielle.', SRC))
    fl.append(PageBreak())
    fl.append(h2(f'{num}.3 Les corridors routiers des périssables'))
    fl += bullets([
        '<b>Route atlantique Agadir–Dakar</b> : ≈ 3 500 km, 9 à 10 jours de camion. La ligne RoRo Agadir–Dakar (52-56 h, 120 camions par rotation, 45 000-50 000 MAD aller-retour) '
        'a été annoncée en décembre 2024 ; en janvier 2026, elle n\'était <b>toujours pas opérationnelle</b> selon Le360, alors que FreshPlaza la disait lancée en janvier 2025 — deux versions à confronter avant tout plan de transport' + ref('C06') + '.',
        '<b>El Guerguerat</b> : hausse de 171 % des taxes mauritaniennes de passage (dédouanement d\'un gros porteur de 70 000 à 190 000 MRU, 01/2024) et surtaxe saisonnière sur la tomate et l\'oignon.',
        '<b>Corridor Nord (Mombasa–Kampala)</b> : 70 h médianes de Mombasa à Malaba (observatoire, S1 2025) ; le gouvernement kényan cite 76-80 h (04/2026)' + ref('C27') + ' et vise 36-48 h par la suppression des barrages.',
        '<b>Beitbridge (Afrique du Sud–Zimbabwe)</b> : ≈ 38 h de traversée pour un poids lourd en septembre 2026 (+69,5 % en un mois ; secondaire).',
        '<b>Accord ATP</b> : seuls le Maroc et la Tunisie sont parties en Afrique — les certificats de transport sous température dirigée ne sont pas reconnus ailleurs.'], sym='●')
    fl.append(h2(f'{num}.4 Semences : un marché informel, des droits faibles, des homologations lourdes'))
    T = CB['intrants_tarifs']
    rows = [['Semence (SH)'] + [DEST.get(d, PAYS[d]) for d in ['DZA', 'EGY', 'KEN', 'MAR', 'ZAF']]]
    for hs in ['070110', '100510', '120991']:
        rows.append([f'{lib(hs)} ({sh(hs)})'] + [('n.d.' if T[hs][d]['npf'] is None else f"{fmt_t(T[hs][d]['npf'])} → {fmt_t(T[hs][d]['pref'])} %") for d in ['DZA', 'EGY', 'KEN', 'MAR', 'ZAF']])
    fl.append(Paragraph(f'Tableau {num}.3 — Droits NPF → ZLECAf 2026 sur les semences (origine admise représentative)', CAP))
    fl.append(table(rows, [52 * mm] + [(CW - 52 * mm) / 5] * 5, align_right_from=1))
    fl.append(Paragraph('Source : calculateurs du SaaS, toutes lignes nationales (origines : Tunisie pour l\'Algérie et l\'Égypte, Égypte pour le Kenya et le Maroc, Ghana pour la SACU). '
                        'Algérie, plants de pomme de terre : le registre du SaaS (tarif d\'usage 2020) porte un DAPS de 70 % sur 0701.10, alors que le relevé DGD du 29/08/2026 ne mentionne que DD 5 %, TVA, TCS et PRCT ; '
                        'les deux sources sont citées, sans arbitrage' + ref('C09') + '.', SRC))
    fl += bullets([
        '<b>Un marché de 3,15 Md$ (Mordor Intelligence) ou 3,28 Md$ (Research and Markets) en 2025</b> (secondaire)' + ref('C07') + ', mais les petits exploitants tirent <b>90,2 %</b> de leurs semences des circuits informels ; les agro-dealers en fournissent ≈ 2,5 % (McGuire & Sperling, republié par CRS en 12/2025).',
        '<b>Harmonisation régionale</b> : catalogue COMESA de 119 variétés, commercialisables dans les 21 États sans nouveaux essais (règlement transposé dans 11 États, 06/2025) ; catalogue SADC de 96 variétés ; règlement CEDEAO C/REG.4/05/2008.',
        '<b>Plants de pomme de terre</b> : l\'Égypte est le 2<super>e</super> importateur mondial (110-150 kt par saison) ; les volumes algériens importés divergent selon les sources (50 000 à 150 000 t par an ; « 80 % d\'autosuffisance » contre « 70 % importés »)' + ref('C08') + ' et la production locale de plants atteint 263 000 t (2024).',
        '<b>Vigilance</b> : les « exportations égyptiennes de plants » (0701.10) relevées par BACI doivent être lues avec prudence — l\'Égypte importe massivement cette position ; '
        'des plants réexportés ne sont pas originaires au sens de la ZLECAf.'], sym='●')
    return fl


# ---------------------------------------------------------------- INDUSTRIELS : coûts et champions
def ch_couts(num=8):
    fl = [chapter(num, 'Coûts opérationnels : énergie, emballages, choc pétrolier'),
          P("La marge préférentielle se gagne ou se perd dans l'usine : un écart de 10 cents par kWh ou de 200 $ par tonne de fer-blanc pèse plus que quelques points de droit de douane "
            "sur un produit transformé. Les données comparables restent rares ; celles qui existent sont datées et leurs contradictions sont signalées.", LEAD)]
    rows = [['Pays', 'Électricité entreprises ($/kWh, 12/2025)', 'Autres données 2026 (régulateur, presse)'],
            ['Algérie', '0,035', 'Fin de la subvention du gaz au-delà de 200 M m³/an (2025-2026), 100 M m³ en 2027-2028, 40 M m³ à partir de 2029'],
            ['Égypte', '0,038', Paragraph('Gaz industriel « autres industries » 6,50-6,75 $/MMBtu (05/2026) ; tarif commercial jusqu\'à 2,79 EGP/kWh (07/2026), contre 1,94 EGP pour GPP' + ref('C11'), TD)],
            ['Nigeria', '0,050', Paragraph('Band A NERC 209,5 NGN/kWh (≈ 0,14 $), contre 65,8 NGN pour GPP' + ref('C10') + ' ; diesel 1 800-1 900 NGN/l ; effondrements du réseau (01/2026)', TD)],
            ['Afrique du Sud', '0,105', '+8,76 % (Eskom, 04/2026) ; 476 jours consécutifs sans délestage'],
            ['Maroc', '0,110', 'Moyenne tension 0,74-1,42 DH/kWh selon la plage horaire ; refonte ANRE prévue au 01/03/2027'],
            ['Tunisie', '0,116', 'Haute tension : 179-332 millimes/kWh selon la plage (STEG, tarif 2022)'],
            ['Ghana', '0,137', Paragraph('+3,49 % au 01/07/2026 ; plan de délestage de 800 MW annoncé par la presse, démenti par ECG' + ref('C12'), TD)],
            ['Kenya', '0,175', 'Gazole 242,92 KES/l en mai-juin 2026, 222,86 en juillet-août'],
            ['Côte d\'Ivoire', '0,235', 'Plus haut niveau de l\'échantillon (à recouper avec la grille CIE/ANARE)']]
    fl.append(Paragraph(f'Tableau {num}.1 — Énergie industrielle : un écart de 1 à 7 entre pays selon GPP (les tarifs réglementaires divergent, voir la colonne de droite)', CAP))
    fl.append(table(rows, [26 * mm, 40 * mm, CW - 66 * mm], font=7))
    fl.append(Paragraph('Source : GlobalPetrolPrices, tarif « business » (1 GWh/an, taxes comprises), daté de décembre 2025 par les pages pays mais présenté comme une « moyenne 2023-2026 » sur d\'autres pages du site (ambiguïté non levée) ; régulateurs et presse cités (2026). À lire comme des ordres de grandeur.', SRC))
    fl.append(h2(f'{num}.1 Emballages et choc d\'Ormuz'))
    fl += bullets([
        '<b>Fer-blanc</b> : 850-1 200 $/t (moyenne mondiale, 06/2026) ; boîte alimentaire de 400 g : 0,20-0,35 $ l\'unité en Afrique (estimation commerciale, secondaire). '
        'Hors Afrique du Sud (ArcelorMittal SA, Nampak), aucune capacité africaine de fer-blanc n\'est documentée : forte dépendance aux importations (hypothèse).',
        '<b>PET</b> : 1,09 $/kg en Afrique (08/2026, +5,8 % ; secondaire). La part de l\'emballage dans le coût des conserves et des boissons africaines n\'est pas documentée ; '
        'pour la tomate transformée (Tiger Brands, 2023), transformation, emballage, énergie et main-d\'œuvre pèsent ensemble 30 % du coût.',
        '<b>Choc d\'Ormuz</b> : Brent de 72 à 118 $/b en mars 2026 (Banque mondiale, moyenne 2026 prévue à 86 $) ; un tiers du méthanol maritime mondial transite par Ormuz — risque sur les résines. '
        'Aucune étude ne chiffre encore l\'effet sur les conserveries ou les boissons africaines.'], sym='●')
    fl.append(PageBreak())
    fl.append(h2(f'{num}.2 Les champions africains et leurs chaînes de valeur'))
    rows = [['Groupe', 'Chiffre d\'affaires', 'Projection africaine', 'Source'],
            ['Dangote Sugar (Nigeria)', '829,2 Md NGN en 2025 (+24,6 %)', 'Fusion projetée avec NASCON et Dangote Rice', 'Nairametrics, 04/03/2026'],
            ['Juhayna (Égypte)', '29,98 Md EGP en 2025 (+23 %)', 'Exportations 2,2 Md EGP vers 48 pays', 'Communiqué 4T25'],
            ['Edita (Égypte)', '20,9 Md EGP en 2025 (+29,5 %)', 'Usine au Maroc, plateforme vers l\'Afrique de l\'Ouest', 'Daily News Egypt, 12/03/2026'],
            ['Lesieur Cristal (Maroc)', '5 378 M MAD en 2025 (−1 %)', 'Approche sélective en Afrique ; Cristal Tunisie', 'BourseNews'],
            ['Tiger Brands (Afrique du Sud)', '34,4 Md ZAR (exercice 09/2025)', 'Cession de Chococam (Cameroun)', 'Tiger Brands, 26/11/2025'],
            ['Brookside Uganda, Pearl Dairy, Amos', 'n.d.', 'Lait en poudre vers l\'Algérie : 2 100 t (8 M$) en 2025, accord-cadre ≈ 500 M$', 'Dairy Business MEA, 06/2025'],
            ['SIFCA, Bidco, Promasidor', 'Chiffres non vérifiés', 'Palme, huiles, lait en poudre ; 5 à 36 pays', 'À vérifier']]
    fl.append(table(rows, [36 * mm, 38 * mm, 58 * mm, CW - 132 * mm], font=7))
    fl += bullets([
        '<b>Cajou</b> : 732 000 t transformées en Afrique de l\'Ouest en 2025 (+51 %), dont ≈ 600 000 t en Côte d\'Ivoire selon l\'African Cashew Alliance, 659 579 t selon une autre source' + ref('C13') + ' (taux de transformation de 43 %).',
        '<b>Cacao</b> : ≈ 42 % des fèves ivoiriennes broyées localement (capacité ≈ 900 kt) ; broyage mondial en baisse à 4,60 Mt en 2024/25 (ICCO).',
        '<b>Huile de palme</b> : le Nigeria consomme 2,1-2,2 Mt d\'huiles pour ≈ 1,9 Mt produites ; Presco et Okomu investissent dans l\'extension des plantations.',
        '<b>Financements</b> : protocole Afreximbank-ZLECAf-PAM d\'au moins 2 Md$ sur 3 ans pour agro-transformateurs et négociants ; alliance SAPZ de 3 Md$ (BAD, Afreximbank).'], sym='●')
    fl.append(Paragraph('Sources : notes de recherche du 29/09/2026 (entreprises, ICCO, ACA, BAD) ; les chiffres d\'entreprises non vérifiés sont signalés.', SRC))
    return fl


# ---------------------------------------------------------------- NÉGOCE : formalités
def ch_formalites(num=6):
    fl = [chapter(num, 'Formalités, conformité et paiements'),
          P("Une marge préférentielle ne se touche qu'avec une preuve d'origine acceptée, des certificats sanitaires en règle et un paiement qui arrive. "
            "Ce chapitre rassemble ce qui est documenté en septembre 2026 — et signale ce qui ne l'est pas.", LEAD)]
    rows = [['Pays', 'Qui délivre la preuve d\'origine ZLECAf', 'Dématérialisation', 'Délai documenté'],
            ['Égypte', 'GOEIC (formulaire « Form 8 bis exports »)', 'Portail en ligne ou dépôt physique', 'n.d.'],
            ['Maroc', 'ADII (douane)', 'Demandes dématérialisées depuis le 24/06/2024', 'n.d.'],
            ['Kenya', 'KRA (douane) ; la KNCCI délivre les CO non préférentiels', 'e-CO COMESA/KRA depuis le 02/10/2025', 'n.d.'],
            ['Afrique du Sud', 'SARS (enregistrement préalable)', 'Premiers envois certifiés le 31/01/2024', 'n.d.'],
            ['Ghana', 'Douane GRA + GNCCI (visite d\'usine si transformation)', 'Portail ICUMS', '≈ 5 jours ouvrés (produits entièrement obtenus)'],
            ['Nigeria', 'Nigeria Customs Service', 'Portail Nigeria Trade Hub', '24 h (09/2026, contre > 5 jours)'],
            ['Algérie', Paragraph('Deux versions : douane (DGD) ou CACI puis visa douanier' + ref('C23'), TD), 'n.d.', 'Validité 6 ou 12 mois selon les sources']]
    fl.append(Paragraph(f'Tableau {num}.1 — Preuve d\'origine : autorités et délais', CAP))
    fl.append(table(rows, [24 * mm, 64 * mm, 50 * mm, CW - 138 * mm], font=7))
    fl.append(Paragraph('Sources : tralac (guide Égypte, 07/2026) ; TelQuel (20/06/2024) ; KRA ; SARS ; ODI (09/2024) ; allAfrica (11/09/2026) ; DGD (site indisponible le 29/09/2026) et CACI. '
                        'La déclaration d\'origine par exportateur agréé est prévue par les textes (seuil de 5 000 $ pour les MPE) ; aucun chiffre de mise en œuvre en 2026 n\'a été trouvé.', SRC))
    fl.append(h2(f'{num}.1 SPS, frontières et paiements'))
    fl += bullets([
        '<b>ePhyto</b> : 96 pays utilisent la solution de la CIPV (10/2025), mais seuls <b>13 pays africains sur 54</b> l\'ont pleinement intégrée ; l\'initiative ePhyto Afrique vise 70 % en 3 ans.',
        '<b>Aflatoxines et lait</b> : plafond de 10 ppb sur le maïs dans la CAE ; baisse de 34 % des importations kényanes de maïs tanzanien du fait des BNT (secondaire, période à vérifier) ; blocage kényan des produits laitiers ougandais contesté en 01/2025.',
        '<b>Temps de frontière</b> : dernières données comparables de 2019 (Doing Business 2020) — conformité à l\'export 97 h et 603 $ en Afrique subsaharienne, 16 h au Kenya, 48 h en Égypte, 80 h en Algérie, 239 h en Côte d\'Ivoire. '
        'Aucune série plus récente en heures et en dollars n\'existe (B-READY publie des scores).',
        '<b>Initiative de commerce guidé (GTI)</b> : 39 pays à sa clôture (04/2025) ; thé, café, fruits secs, thon parmi les premiers envois ; aucun bilan officiel en valeur.',
        '<b>PAPSS</b> : plus de 30 pays, 24 banques centrales et plus de 200 banques (09/2026) ; volumes +1 000 % et valeurs +120 % sur un an, sans montant absolu publié.'], sym='●')
    # formalités recensées par le SaaS sur les cibles retenues
    rows = [['Destination', 'Cibles retenues', 'avec formalités recensées', 'dont formalité lourde', 'Formalités les plus fréquentes']]
    for d in ['DZA', 'EGY', 'KEN', 'MAR', 'ZAF']:
        xs = [x for x in CB['classement'] if x['d'] == d and x['verdict'] == 'RETENUE']
        if not xs:
            continue
        docs = {}
        for x in xs:
            for m in x['mnt']:
                docs[m] = docs.get(m, 0) + 1
        top = sorted(docs.items(), key=lambda z: -z[1])[:2]
        rows.append([DEST.get(d, PAYS[d]), str(len(xs)), str(sum(1 for x in xs if x['mnt'])), str(sum(1 for x in xs if x['mnt_graves'])),
                     Paragraph(' ; '.join(f'{k[:60]} ({v})' for k, v in top) or 'non recensées dans le SaaS', st('fq', fontSize=6.6, leading=8.2))])
    fl.append(Paragraph(f'Tableau {num}.2 — Formalités non tarifaires recensées par le SaaS sur les cibles retenues', CAP))
    fl.append(table(rows, [26 * mm, 18 * mm, 24 * mm, 22 * mm, CW - 90 * mm], align_right_from=1, font=7))
    fl.append(Paragraph('Source : SaaS ZLECAf — F.A.P algériennes (tarif d\'usage DGD, édition LF 2020) et formalités douanières égyptiennes. Le Maroc, le Kenya et la SACU ne sont pas encore couverts : '
                        '« non recensées » ne signifie pas « inexistantes ».', SRC))
    return fl


# ---------------------------------------------------------------- INTRANTS
FAM = [('Engrais', ('31',)), ('Aliments et tourteaux', ('2309', '2304')), ('Semences', ('1209', '070110', '100510', '100710', '100310', '100110', '100191')),
       ('Phytosanitaires', ('3808',)), ('Machines et tracteurs', ('84', '87'))]


def ch_intrants_marche(num=1):
    fl = [chapter(num, 'Le marché africain des facteurs de production'),
          P("L'Afrique produit de l'engrais mais en utilise peu, importe son maïs et son soja pour nourrir une filière avicole en forte croissance, et mécanise lentement. "
            "Le choc d'Ormuz de 2026 a rappelé la dépendance du continent aux intrants importés du Golfe.", LEAD)]
    fl.append(kpis([('< 25 kg/ha', 'engrais utilisés en Afrique (2024), contre 135 kg/ha dans le monde ; 17-19 kg/ha en Afrique subsaharienne', 'UA, sommet de Nairobi (05/2024)'),
                    ('64,2 Mt', 'aliments composés produits en Afrique en 2025 (+11,5 % ; « +12 % » dans un autre extrait)' + ref('C22'), 'Alltech Agri-Food Outlook 2026'),
                    ('3,5-5,2 Md$', 'marché africain des machines agricoles (2025), selon les cabinets' + ref('C19'), 'Mordor et autres (secondaire)'),
                    ('< 170 M$', 'levées de l\'agtech africaine en 2025 (−20 %)', 'Briter, 03/2026')], cols=4))
    fl.append(Spacer(1, 4))
    M = CB['intrants_marches']
    pays = sorted(M, key=lambda d: -sum(M[d].values()))
    rows = [['Pays'] + [f for f, _ in FAM] + ['Total']]
    for d in pays:
        v = [sum(x for h, x in M[d].items() if h.startswith(pre)) for _, pre in FAM]
        rows.append([PAYS.get(d, d)] + [fmt_m(x) for x in v] + [Paragraph(f'<b>{fmt_m(sum(v))}</b>', TDR)])
    fl.append(Paragraph(f'Tableau {num}.1 — Importations d\'intrants agricoles, moyenne 2023-2024 (M$/an)', CAP))
    fl.append(table(rows, [26 * mm] + [(CW - 46 * mm) / 5] * 5 + [20 * mm], align_right_from=1, font=7))
    fl.append(Paragraph('Source : OEC/BACI (HS 2017), positions strictement agricoles : 31 (hors engrais non agricoles), 23.09 et 23.04, semences (12.09, 07.01.10, 10.05.10…), 38.08.91-93, '
                        '84.32-84.36, 84.24.41/49/82 et tracteurs 87.01.10/30/91-95. Exclus : 87.01.20 (tracteurs routiers), 84.24.10 (extincteurs), 84.33.11/19 (tondeuses à gazon).', SRC))
    fl.append(h2(f'{num}.1 Engrais : production africaine et choc d\'Ormuz'))
    fl += bullets([
        '<b>Objectifs</b> : 50 kg/ha est la cible d\'Abuja (2006) ; le sommet de Nairobi (05/2024) vise le triplement de la production et de l\'utilisation d\'engrais d\'ici 2034.',
        '<b>Producteurs</b> : OCP (114 Md MAD de CA en 2025, Afrique = 18 % du CA engrais au S1 2025) ; Dangote (3 Mt/an d\'urée au Nigeria, projet de 3 Mt à Gode en Éthiopie) ; '
        'Égypte (3,54 Mt d\'azotés exportés en 2024, taxe à l\'export en 05/2026) ; Algérie (3,2 à 3,6 Mt/an de capacité d\'urée selon la capacité attribuée à Sorfert' + ref('C16') + ' ; 3,53 Mt d\'azotés exportés en 2023).',
        '<b>Prix</b> : fermeture d\'Ormuz le 28/02/2026 ; urée de ≈ 400 à 850 $/t en avril (OMC), puis 453 $/t en juin (moyenne OMC) contre 630 $/t (FOB Moyen-Orient, IFDC)' + ref('C14') + ' ; ' '933 à 1 059 $/t rendue en Tanzanie, au Malawi et en Afrique du Sud en juillet (AMIS, à vérifier). '
        '8 pays africains parmi les 18 économies les plus vulnérables (OMC, 10/07/2026).',
        '<b>Subventions</b> : Kenya (sac de 50 kg à 2 500 puis 2 000 KES ; 32,2 millions de sacs en 4 saisons) ; Nigeria (1,1 Mt visées en 2026) ; Éthiopie (plafond de 84 Md ETB en 2025/26).'], sym='●')
    return fl


def ch_intrants_regimes(num=2):
    fl = [chapter(num, 'Régimes tarifaires, normes et homologations'),
          P("Les droits de douane sur les intrants sont bas partout sauf exceptions ; les vraies barrières sont l'homologation pays par pays, les autorisations techniques "
            "et les restrictions à l'export des pays producteurs.", LEAD)]
    T = CB['intrants_tarifs']
    D5 = ['DZA', 'EGY', 'KEN', 'MAR', 'ZAF']
    rows = [['Intrant (SH)'] + [DEST.get(d, PAYS[d]) for d in D5]]
    for hs, lab in [('310210', 'Urée'), ('310530', 'DAP'), ('310520', 'Engrais NPK'), ('310420', 'Chlorure de potassium'), ('230990', 'Aliments composés'), ('230400', 'Tourteaux de soja'),
                    ('100510', 'Maïs de semence'), ('070110', 'Plants de pomme de terre'), ('120991', 'Semences potagères'), ('380891', 'Insecticides'), ('380893', 'Herbicides'),
                    ('870192', 'Tracteurs agricoles 37-75 kW'), ('843351', 'Moissonneuses-batteuses'), ('842482', 'Pulvérisateurs et irrigation agricoles')]:
        rows.append([f'{lab} ({sh(hs)})'] + [('n.d.' if T[hs][d]['npf'] is None else
                                              (f"{fmt_t(T[hs][d]['npf'])} %" if T[hs][d]['npf'] == T[hs][d]['pref'] else f"{fmt_t(T[hs][d]['npf'])} → <b>{fmt_t(T[hs][d]['pref'])}</b> %")) for d in D5])
    rows = [rows[0]] + [[r[0]] + [Paragraph(c, TDR) for c in r[1:]] for r in rows[1:]]
    fl.append(Paragraph(f'Tableau {num}.1 — Droit NPF → taux ZLECAf servi en 2026 sur les intrants clés', CAP))
    fl.append(table(rows, [52 * mm] + [(CW - 52 * mm) / 5] * 5, align_right_from=1, font=7))
    fl.append(Paragraph('Source : calculateurs du SaaS sur toutes les lignes nationales, pour une origine admise représentative (Tunisie → Algérie et Égypte ; Égypte → Kenya et Maroc ; Ghana → SACU). '
                        'Un seul taux affiché : NPF déjà nul ou non réduit. n.d. : position absente du barème du SaaS.', SRC))
    fl += bullets([
        '<b>Où la préférence compte</b> : en Algérie, les engrais (15 % → 0 %) et les phytosanitaires (≈ 22-23 % → 0 %) ; au Kenya, les semences de maïs et les plants (25 % → 10 %). '
        'Ailleurs, les droits NPF sont déjà nuls ou très bas.',
        '<b>Pesticides</b> : liste du Comité sahélien des pesticides de 607 produits autorisés (2025) ; première session d\'homologation du COAHP (CEDEAO-UEMOA-CILSS, 17 pays) en 12/2025 ; lignes directrices SADC et CAE.',
        '<b>Engrais</b> : règlement CEDEAO C/REG.13/12/12 (libre circulation, étiquetage, métaux lourds) et comité de contrôle WACoFeC (10/2023).',
        '<b>Barrières relevées</b> : ré-homologation pays par pays ; autorisation technique préalable algérienne sur les phytosanitaires et les plants (F.A.P du SaaS) ; '
        'taxe égyptienne à l\'export des azotés (90 $/t puis 10 % FOB, 2026) ; limite d\'âge du matériel agricole d\'occasion importé en Algérie (moins de 7 ans).',
        '<b>Machines</b> : aucune référence africaine de certification des machines agricoles (AFRISTAN/ARSO) n\'a été trouvée pour 2024-2026.'], sym='●')
    return fl


def ch_intrants_besoins(num=3):
    fl = [chapter(num, 'Besoins des filières et modèles d\'implantation'),
          P("La demande d'intrants suit la volaille, l'aquaculture et l'irrigation. Les modèles qui marchent combinent distribution de proximité, financement et service.", LEAD)]
    rows = [['Filière', 'Donnée clé', 'Source']]
    rows += [['Aliments volaille (chair)', '> 20 Mt en 2025 (+12,7 %) ; pondeuses 9,69 Mt', 'Alltech 2026'],
             ['Aliments laitiers, bovins', '10 Mt (+13,5 %) ; 7 Mt (+8,4 %)', 'Alltech 2026'],
             ['Aquaculture', '2,1 Mt (+27,5 %) ; Égypte +36 %', 'Alltech 2026'],
             ['Maïs fourrager, Égypte', '9,5 Mt importées en 2025/26, record de 13,2 Mt prévu en 2026/27', 'USDA GAIN, 03/2026'],
             ['Maïs et soja, Algérie', '≈ 4 Mt de maïs et ≈ 1,25 Mt de tourteau par an (à vérifier) ; OEC : 1 042 M$ de maïs et 140 M$ de tourteaux importés', 'TSA ; OEC 2023-2024'],
             ['Mécanisation, Nigeria', '5 000 tracteurs/an en kit (Brésil, 10 ans) ; 2 000/an (John Deere, 5 ans)', 'Présidence, 2025 ; Nairametrics, 2024'],
             ['Mécanisation, Afrique du Sud', '7 176 tracteurs vendus de janvier à novembre 2025 (+19 %)', 'SAAMA via Business Report'],
             ['Irrigation localisée', 'Maroc : > 600 000 ha au goutte-à-goutte ; SunCulture : > 85 000 systèmes solaires', 'Agrimaroc ; Ecofin, 09/2026']]
    fl.append(Paragraph(f'Tableau {num}.1 — Où se trouve la demande d\'intrants', CAP))
    fl.append(table(rows, [40 * mm, 92 * mm, CW - 132 * mm], font=7))
    fl.append(Paragraph('Parc de tracteurs : « moins de 2 pour 1 000 ha » (FAO, 2019) et « 28 pour 1 000 ha » (autre étude) sont incompatibles ; les deux sont exposés, sans arbitrage' + ref('C18') + '.', SRC))
    fl.append(h2(f'{num}.1 Hubs de distribution et partenariats public-privé'))
    fl += bullets([
        '<b>Zones spéciales de transformation agro-industrielle (SAPZ)</b> : 538 M$ pour la phase 1 au Nigeria (BAD 210 M$, BID 150 M$, FIDA 100 M$, FVC 60 M$) ; 28 États candidats à la phase 2 ; alliance SAPZ de 3 Md$.',
        '<b>Réseaux de distribution</b> : AFAP (571 M$ investis depuis 2012 via ≈ 5 000 agro-dealers « hub », à vérifier) ; OCP Africa (plus de 35 pays, plus de 40 unités de mélange réhabilitées au Nigeria) ; AGRA (25 000 agro-dealers).',
        '<b>Location et paiement à l\'usage</b> : Hello Tractor (John Deere au capital, financement de 500 M KES avec Absa Kenya) ; TROTRO Tractor au Ghana.',
        '<b>Financement</b> : facilité BAD de 500 M$ pour mobiliser 10 Md$ vers les petits exploitants et les PME agricoles ; ≈ 700 M$ de mécanismes annoncés à l\'AFSF de Kigali (09/2026).'], sym='●')
    return fl


# ---------------------------------------------------------------- feuilles de route
ROUTES = {
    'producteurs': [
        ('Dans les 3 mois', ['Vérifier la ligne nationale à 8-10 chiffres de chaque produit dans le calculateur du SaaS et écarter les cibles marquées « créneau » ou « fausse piste ».',
                             'Faire enregistrer l\'exploitation ou la coopérative comme exportateur auprès de l\'autorité compétente et documenter l\'« entièrement obtenu » (parcelles, lots, élevage).',
                             'Obtenir des devis reefer réels sur le corridor choisi : aucun taux intra-africain publié ne permet de s\'en passer.']),
        ('Dans les 12 mois', ['Mutualiser le froid (chambres solaires, crédit « Tabrid » en Algérie, opérateurs privés au Kenya et en Afrique du Sud) et viser la réduction des pertes plutôt que le volume.',
                              'Inscrire les variétés dans les catalogues régionaux (COMESA, SADC, CEDEAO) avant d\'exporter semences ou plants.',
                              'Préparer l\'ePhyto et les dossiers SPS du marché cible ; anticiper les contrôles aflatoxines sur les grains et l\'arachide.']),
        ('2027 et au-delà', ['Préparer l\'ouverture de la catégorie B (2030-2034) sur les viandes, laitiers et huiles, aujourd\'hui largement exclus.',
                             'Monter en gamme vers la première transformation (séchage, conditionnement, calibrage) pour sortir des marchés où la destination est exportatrice nette.'])],
    'industriels': [
        ('Dans les 3 mois', ['Classer chaque produit dans le tableau des cibles vérifiées et vérifier que la préférence couvre bien toutes ses lignes nationales (préférences partielles fréquentes).',
                             'Cartographier l\'origine des intrants : sucre, cacao, lait et huiles non africains font perdre l\'origine ; la mouture et le changement de position peuvent la conférer.',
                             'Comparer le coût énergétique et d\'emballage du site avec les pays concurrents du tableau des coûts.']),
        ('Dans les 12 mois', ['Sécuriser des matières originaires sur contrat pluriannuel (sucre SADC, pâte de cacao ouest-africaine, lait est-africain).',
                              'Obtenir le statut d\'exportateur agréé pour la déclaration d\'origine sur facture et dématérialiser les certificats (Maroc, Kenya, Nigeria).',
                              'Négocier des contrats de gaz ou d\'électricité avant les échéances connues (Algérie : fin de la subvention au-delà de 200 M m³, puis 100 M m³ en 2027).']),
        ('2027 et au-delà', ['Dimensionner les investissements pour la catégorie B et la règle d\'origine définitive ; s\'appuyer sur les SAPZ et les financements Afreximbank.',
                             'Consolider des plateformes régionales là où la préférence et le marché coïncident, pas seulement là où le droit NPF est élevé.'])],
    'negoce': [
        ('Dans les 3 mois', ['Remplacer toute cible reprise de l\'édition précédente par le Top 25 vérifié ; ne traiter les « créneaux » qu\'en opportunités ponctuelles.',
                             'Chiffrer le coût rendu intégral (fret, surprime de guerre, carburant, portage) avec les paramètres du modèle du SaaS et des devis réels.',
                             'Contrôler pour chaque flux les formalités recensées (licences, autorisations techniques) avant d\'engager un contrat.']),
        ('Dans les 12 mois', ['Ouvrir un compte PAPSS avec une banque participante pour réduire les coûts de change ; documenter la preuve d\'origine de chaque fournisseur.',
                              'Construire des accords de fourniture avec les origines qui exportent réellement (offre ≥ 5 M$) et se méfier des origines réexportatrices.',
                              'Suivre le retour des services maritimes par Suez (septembre 2026) et renégocier les surcharges.']),
        ('2027 et au-delà', ['Étendre le portefeuille aux destinations qui publieront leurs listes d\'origines admises ; se préparer aux e-certificats (ADAPT).'])],
    'intrants': [
        ('Dans les 3 mois', ['Cibler d\'abord les marchés où la préférence compte : Algérie (engrais, phytosanitaires), Kenya (semences), et les flux de tourteaux et d\'aliments vérifiés.',
                             'Lancer les dossiers d\'homologation dans les zones de référence (CSP/COAHP en Afrique de l\'Ouest, SADC, CAE) : c\'est le chemin critique.']),
        ('Dans les 12 mois', ['S\'associer aux réseaux de distribution existants (agro-dealers hub, unités de mélange, programmes de subvention) plutôt que de créer un réseau propre.',
                              'Proposer financement et service : location, paiement à l\'usage, leasing — le prix d\'achat n\'est pas le premier frein.',
                              'Pour les machines, étudier l\'assemblage local (Algérie, Nigeria, Éthiopie) : l\'offre africaine exportatrice est quasi inexistante et les droits sont déjà bas.']),
        ('2027 et au-delà', ['Suivre les nouvelles capacités (phosphate intégré algérien, Dangote Éthiopie) qui redessineront la concurrence sur les engrais en 2027-2028.'])],
}


def ch_feuille(ed, num=10):
    fl = [chapter(num, 'Feuille de route 2026-2027')]
    for titre, items in ROUTES[ed]:
        fl.append(Paragraph(titre, H3))
        fl += bullets(items, sym='▸')
    return fl


# ---------------------------------------------------------------- pages d'ouverture des éditions
FILIERES = {'producteurs': ['S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S08'],
            'industriels': ['S09', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15']}

MESSAGES = {
    'producteurs': [
        ('Le taux ne suffit pas.', "Une préférence de 40 points ne vaut rien sans acheteur : le Maroc n'importe que 1,4 M$ d'oranges par an (et en exporte 51 M$). Chaque cible de cette édition a passé trois filtres : taux servi, marché importateur réel, offre réelle."),
        ('L\'origine est simple, la logistique ne l\'est pas.', "Les produits bruts sont « entièrement obtenus » : la règle d'origine est rarement le frein. Le froid, les délais portuaires et les certificats SPS le sont."),
        ('Les marchés les plus protégés produisent eux-mêmes.', "Viandes, laitiers et oignons restent largement en listes B et C (Algérie) ou hors catégorie A (Kenya) : la préférence y viendra à partir de 2030."),
        ('Les vrais débouchés 2026 sont ciblés.', "Café est-africain vers le Maghreb, bananes camerounaises et ghanéennes vers l'Algérie, légumineuses et semences : la liste complète est au chapitre des cibles.")],
    'industriels': [
        ('Là où les droits sont élevés, la marge est forte.', "Les produits transformés (SH 15-24) portent les droits les plus élevés du continent ; la préférence y crée les marges les plus fortes, par exemple sur les préparations alimentaires en Algérie (≈ 40 % → 0 % pour l'Égypte et la Tunisie)."),
        ('Mais l\'origine se construit.', "Sucre, cacao, lait et huiles non africains font perdre l'origine ; sourcer les matières en Afrique est souvent la condition de la préférence."),
        ('Les préférences partielles piègent.', "Une SH6 peut n'être libéralisée que sur une partie de ses lignes nationales (fromages en Algérie : 1 ligne sur 9) : vérifier la ligne à 8-10 chiffres."),
        ('Le coût de l\'énergie et de l\'emballage pèse plus que le droit.', "Électricité, gaz et emballages (renchéris par le choc d'Ormuz) décident de la compétitivité rendue.")],
    'negoce': [
        ('Trois conditions, pas une.', "Un taux servi, un acheteur, un vendeur : le Top 25 de cette édition les combine dans la valeur annuelle de la marge sur le marché accessible."),
        ('Méfiance envers les origines réexportatrices.', "Quand une origine importe plus de la moitié de ce qu'elle exporte, la preuve d'origine est à documenter avant tout contrat."),
        ('Les formalités sont recensées.', "Autorisations techniques phytosanitaires en Algérie, formalités égyptiennes : elles figurent dans la colonne vigilance de chaque cible."),
        ('Le coût rendu décide.', "Fret, surprimes de guerre, carburant et portage peuvent effacer la marge : le modèle de coût rendu du chapitre logistique les chiffre.")],
    'intrants': [
        ('Les droits sont déjà bas.', "La plupart des engrais, semences et machines entrent déjà à 0-5 % : la préférence compte surtout en Algérie (engrais, phytosanitaires) et au Kenya (semences)."),
        ('Le marché est réel, l\'offre africaine inégale.', "Engrais, tourteaux et aliments composés s'échangent entre pays africains ; les machines viennent presque toutes d'ailleurs."),
        ('L\'homologation est le chemin critique.', "Semences et phytosanitaires exigent des enregistrements nationaux ou régionaux avant toute vente."),
        ('Le service vend autant que le produit.', "Financement, location, distribution de proximité : les modèles qui fonctionnent associent l'intrant et le crédit.")],
}


def about_edition(ed):
    from editions import EDITIONS
    e = EDITIONS[ed]
    fl = [Paragraph('À PROPOS DE CE PLAN D\'ACTION', KICK), Spacer(1, 3),
          Paragraph(f'Plan d\'action sectoriel {e["num"]} — {" ".join(e["titre"])}', H2),
          P(f"Ce document est l'une des quatre éditions par profil d'opérateur du rapport Agriculture & agroalimentaire ZLECAf (T3 2026). Il s'adresse aux {e['public']}. "
            "Les quatre éditions partagent un tronc commun (cadre ZLECAf, tarifs, règles d'origine) et une même base de cibles vérifiées ; chacune ne garde que ce qui est utile à son public."),
          P("Les données proviennent de la plateforme SaaS ZLECAf (barèmes nationaux, offres de l'<i>e-Tariff Book</i>, règles d'origine de l'Appendice IV, calculateurs des taux servis, "
            "formalités recensées) et des flux OEC/BACI 2023-2024, croisés avec des sources publiques datées. Les chiffres de source secondaire sont signalés comme tels. "
            "Quand deux sources divergent, les deux valeurs sont données et la contradiction est exposée en annexe 4, sans être tranchée.")]
    if ed in FILIERES:
        from ch_front import SECTORS_TABLE
        rows = [['N°', 'Filière', 'Chapitres / positions SH']] + [list(r) for r in SECTORS_TABLE if f'S{r[0]}' in FILIERES[ed]]
        fl += [Paragraph('Périmètre de cette édition', H3), table(rows, [12 * mm, 90 * mm, CW - 102 * mm])]
    fl += [Spacer(1, 6), methode_verif(), Spacer(1, 6), Paragraph('Avertissement', H3),
           Paragraph("Ce document est une analyse économique et réglementaire. Il ne constitue ni un avis juridique ni une décision de classement ou de valeur en douane. "
                     "Les taux doivent être confirmés ligne par ligne dans le calculateur ZLECAf et auprès de l'administration des douanes de destination avant toute opération.", SMALL_J),
           PageBreak()]
    return fl


def synthese(ed):
    from editions import EDITIONS
    p = PARAM[ed]
    liste = CB['intrants'] if ed == 'intrants' else CB['classement']
    ret = filtre(liste, chap=p['chap'], n=1000)
    nich = filtre(liste, chap=p['chap'], verdicts=('CRÉNEAU',), n=1000)
    (au, nau) = stats_audit()
    fl = [chapter(None, 'Synthèse', 'synth')]
    fl[0]._toctext = 'Synthèse'
    fl.append(P(f"Plan d'action pour les {EDITIONS[ed]['public']}. En septembre 2026, la préférence ZLECAf est opposable dans cinq marchés (Algérie, Égypte, Kenya, Maroc, SACU). "
                "Ce plan ne retient que des cibles vérifiées : taux servi sur les lignes nationales, marché importateur réel, offre réelle, formalités recensées.", LEAD))
    top = ret[0] if ret else None
    fl.append(kpis([(str(len(ret)), 'couples marché × produit retenus après vérification', 'cibles.py, 27/09/2026'),
                    (str(len(nich)), 'créneaux : la destination est exportatrice nette du produit', 'OEC/BACI 2023-2024'),
                    (f"{au['REJETÉE']} / {nau}", 'cibles de l\'édition précédente rejetées à l\'audit', 'Audit des cibles') if ed != 'intrants' else
                    (f"{sum(1 for v in CB['intrants_tarifs'].values() for x in v.values() if x['npf'] == 0)} / {sum(1 for v in CB['intrants_tarifs'].values() for x in v.values() if x['npf'] is not None)}",
                     'couples intrant clé × destination déjà à 0 % de droit NPF', 'Calculateurs du SaaS'),
                    (score_txt(top) if top else '—', 'valeur annuelle de la marge de la première cible' + (f" ({lib(top['hs']).lower()})" if top else ''), 'min(demande, offre) × marge')], cols=4))
    fl.append(Spacer(1, 4))
    for t, b in MESSAGES[ed]:
        fl.append(Paragraph(f'<b>{t}</b> {b}', st('msg', fontSize=8.8, leading=12, spaceAfter=4, alignment=TA_JUSTIFY)))
    fl.append(Paragraph('Les cinq premières cibles vérifiées', H3))
    for x in ret[:5]:
        fl.append(Paragraph(f"<b>{PAYS.get(x['o'], x['o'])} → {DEST.get(x['d'], PAYS.get(x['d'], x['d']))}</b> : {lib(x['hs']).lower()} ({sh(x['hs'])}), "
                            f"{fmt_t(x['npf'])} % → <b>{fmt_t(x['pref'])} %</b> ; marché {fmt_m(x['imp_dest'])} M$/an, offre {fmt_m(x['exp_orig'])} M$/an"
                            + (f" — <i>{vigilance(x)}</i>" if vigilance(x) else '') + '.', st('tc', fontSize=8.4, leading=11.4, leftIndent=8, spaceAfter=2), bulletText='▸'))
    fl.append(PageBreak())
    return fl
