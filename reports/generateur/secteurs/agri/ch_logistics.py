from layout import *
C = S + 'charts/'

def landed(fob, t_per_evp, freight_evp, thc_o, thc_d, other_evp, ins_rate, war_cargo, duty, levies, days, fin=0.10):
    """Coût rendu hors TVA récupérable, en $/t."""
    freight = (freight_evp + thc_o) / t_per_evp
    cif_base = fob + freight
    ins = cif_base * (ins_rate + war_cargo)
    cif = cif_base + ins
    dd = cif * duty; lev = cif * levies
    dest = (thc_d + other_evp) / t_per_evp
    finance = fob * fin * days / 365
    total = cif + dd + lev + dest + finance
    return dict(fob=fob, freight=freight, ins=ins, cif=cif, dd=dd, lev=lev, dest=dest, fin=finance, total=total)

def fmt(x, d=0): return f'{x:,.{d}f}'.replace(',', ' ').replace('.', ',').replace('-', '−')

def cost_table(cols, title, note):
    keys = [('fob', 'Prix FOB (hypothèse identique)'), ('freight', 'Fret maritime + manutention origine (surcharges incluses)'), ('ins', 'Assurance cargaison (dont surprime guerre)'),
            ('cif', 'Valeur CAF'), ('dd', 'Droit de douane'), ('lev', 'Prélèvements à l\'import'), ('dest', 'Manutention et frais de destination'),
            ('fin', 'Coût de portage financier (10 %/an sur la durée de transit)'), ('total', 'Coût rendu hors TVA récupérable')]
    rows = [[title] + [c[0] for c in cols]]
    for k, lab in keys:
        r = [Paragraph(f'<b>{lab}</b>' if k in ('cif', 'total') else lab, TD)] + [Paragraph(f'<b>{fmt(c[1][k])}</b>' if k in ('cif', 'total') else fmt(c[1][k]), TDR) for c in cols]
        rows.append(r)
    base = cols[0][1]['total']
    rows.append([Paragraph('<b>Écart vs concurrent extra-africain</b>', TD)] + [Paragraph('—' if i == 0 else f'<b><font color="#1E8C5A">{fmt(c[1]["total"] - base)} $/t ({(c[1]["total"] / base - 1) * 100:+.1f} %)</font></b>'.replace('-', '−'), TDR) for i, c in enumerate(cols)])
    ext = [('BACKGROUND', (0, 4), (-1, 4), GOLD_L), ('BACKGROUND', (0, 9), (-1, 9), GREEN_L)]
    t = table(rows, [70 * mm] + [(CW - 70 * mm) / len(cols)] * len(cols), extra=ext, zebra=False)
    return [t, Paragraph(note, SRC)]

def ch_logistics():
    fl = [chapter(8, 'Logistique, guerres & coût rendu intégral'),
          P("En 2026, le coût d'accès à un marché africain ne se lit plus seulement dans le tarif douanier. Deux crises maritimes se superposent — la mer Rouge, "
            "où les Houthis contrôlent désormais la rive yéménite de Bab el-Mandeb, et Ormuz, quasiment fermé depuis la guerre du 28 février 2026 — et font flamber "
            "l'assurance, le carburant et les délais. Ce chapitre intègre ces paramètres, que le moteur de fret du SaaS (tarifs 2024, routage par Suez) ne modélise pas encore.", LEAD)]
    fl.append(h2('8.1 Le grand détour : Suez et Bab el-Mandeb contournés par le Cap'))
    fl.append(figure(C + 'c12_routes.png', 'Figure 8.1 — Routes Asie–Europe via Suez et via le Cap, zones listées par le Joint War Committee et ports africains gagnants (▲) ou perdants (▼)',
                     'Sources : distances calculées avec searoute (réseau MARNET, ±3 %) ; trafic FMI PortWatch (1-20 sept. 2026 vs janv.-oct. 2023) ; zones JWC : circulaires JWLA-033 (03/03/2026), -034 (29/07/2026), -035 (16/09/2026) — tracé schématique. '
                     'Fond de carte : Natural Earth.', maxh=150 * mm))
    fl.append(PageBreak())
    fl.append(kpis([
        ('−65 %', 'navires/jour à Bab el-Mandeb en sept. 2026 vs 2023 (25,9 contre 74,6)', 'FMI PortWatch'),
        ('+76 %', 'navires/jour au cap de Bonne-Espérance (86,1 contre 48,9)', 'FMI PortWatch'),
        ('0,5-7 %', 'surprime guerre de la valeur de coque par transit (Bab el-Mandeb → ports saoudiens)', 'Al Jazeera ; Insurance Journal, 2026'),
        ('+107 %', 'kérosène en sept. 2026 vs moyenne 2025 (184 $/b)', 'EIA via FRED')], cols=4))
    fl.append(Spacer(1, 4))
    fl.append(Spacer(1, 4))
    rows = [['Liaison', 'Via Suez / Bab el-Mandeb', 'Via le Cap', 'Écart', 'Jours en plus (14 nœuds)'],
            ['Singapour – Rotterdam', '8 367 nm', '11 855 nm', '+42 %', '+10,4'], ['Mombasa – Rotterdam (thé, avocats)', '6 393 nm', '8 771 nm', '+37 %', '+7,1'],
            ['Mombasa – Alexandrie (thé vers l\'Égypte)', '3 266 nm', '9 503 nm', '+191 %', '+18,6'], ['Djibouti – Rotterdam (café éthiopien)', '4 669 nm', '10 365 nm', '+122 %', '+17,0'],
            ['Tanger Med – Mombasa (commerce Nord-Est ZLECAf)', '5 017 nm', '7 706 nm', '+54 %', '+8,0'], ['Novorossiïsk – Mombasa (blé)', '4 337 nm', '9 940 nm', '+129 %', '+16,7'],
            ['Durban – Rotterdam ; Singapour – Lagos', 'non exposées', '—', '0', '—']]
    fl.append(Paragraph('Tableau 8.1 — Coût en distance du contournement pour les flux agroalimentaires africains', CAP))
    fl.append(table(rows, [66 * mm, 32 * mm, 26 * mm, 18 * mm, CW - 142 * mm], align_right_from=1))
    fl.append(Paragraph('Source : calculs searoute (±3 %), note logistique ZLECAf Trade Intelligence (27/09/2026).', SRC))
    fl.append(figure(C + 'c13_chokepoints.png', 'Figure 8.2 — Trafic journalier aux points de passage stratégiques', 'Source : FMI PortWatch, Daily Chokepoints Data (estimations AIS), extraction du 27/09/2026.', maxh=52 * mm))
    fl.append(h2('8.2 Surprimes « risque de guerre » et zones listées'))
    rows = [['Zone', 'Surprime (en % de la valeur de coque, par transit)', 'Flux agroalimentaires exposés'],
            ['Mer Rouge / Bab el-Mandeb', '0,05 % avant oct. 2023 → 0,7-1 % (2024) → 0,2-0,3 % (sept. 2026, navires non saoudiens) ; 0,5 % à Bab el-Mandeb (juil. 2026)', 'Blé vers Djibouti, l\'Éthiopie, le Soudan ; thé kényan vers l\'Égypte ; huiles vers l\'Égypte'],
            ['Ports saoudiens (Yanbu, Jizan)', '≈ 3 % à Yanbu, jusqu\'à 7 % à Jizan (sept. 2026)', 'Bétail de la Corne de l\'Afrique vers Jeddah (escales −74 %)'],
            ['Ormuz / golfe Persique', '6-10 % (juil.-sept. 2026)', 'Engrais (≈ 1/3 du commerce maritime mondial), carburants, débouchés du Golfe'],
            ['Mer Noire (zone étendue le 16/09/2026)', '≈ 1 % pour les ports ukrainiens (+0,10-0,20 %) ; ≈ 2-3 $/t de blé', 'Blé pour l\'Égypte, l\'Algérie, la Libye, le Soudan'],
            ['Golfe de Guinée (Bénin, Nigeria, Togo)', 'Zone listée malgré 2 incidents seulement au S1 2026', 'Riz, blé, sucre à Lagos, Cotonou, Lomé ; Abidjan, San Pedro, Tema hors zone'],
            ['Djibouti (ajouté le 03/03/2026), Somalie, Soudan, Libye, Cabo Delgado', 'Négociée voyage par voyage', 'Café éthiopien, gomme arabique, sésame, cajou de Mtwara']]
    fl.append(table(rows, [44 * mm, 70 * mm, CW - 114 * mm]))
    fl.append(Paragraph('Sources : S&P Global, Al Jazeera (23/07/2026), Insurance Journal (25/09/2026), Beinsure (23/09/2026), UkrAgroConsult, circulaires LMA/JWC, IMB (S1 2026), FMI PortWatch.', SRC))
    fl.append(PageBreak())
    fl.append(h2('8.3 Le choc carburant : kérosène et soutes'))
    fl.append(figure(C + 'c14_fuel.png', 'Figure 8.3 — Brent et kérosène, T1 2024 – sept. 2026 ($/baril)',
                     'Source : EIA via FRED (DCOILBRENTEU, DJFUELUSGULF), extraction du 27/09/2026 ; *moyenne du 1er au 22/09/2026. Projection EIA (STEO sept. 2026) : Brent 91 $/b en moyenne 2026, 74 $/b en 2027.', maxh=60 * mm))
    fl += bullets([
        '<b>Fret aérien des périssables</b> : les fleurs kényanes sont passées de ≈ 2,5 $/kg à <b>5-5,8 $/kg</b> vers l\'Europe (mars 2026), avec des pertes allant jusqu\'à 1,4 M$ par semaine ; Ethiopian Airlines a relevé de 20 % ses tarifs périssables (avril-décembre 2026). '
        'La surcharge carburant du SaaS (0,65 $/kg, figée) devrait être portée à ≈ 1,3 $/kg si elle suit le kérosène.',
        '<b>Maritime</b> : surcharges carburant d\'urgence de 150 à 265 $/EVP (CMA CGM), surcharge soutes d\'urgence Maersk sur tout le réseau (dont l\'Afrique) depuis le 25/03/2026 ; '
        'surcharges « conflit » Golfe de 1 500 à 4 000 $ par conteneur (reefers) ; ETS européen (100 % des émissions en 2026, 50 % sur les liaisons Afrique–UE).',
        '<b>Le Cap coûte cher en carburant</b> : ≈ +1 210 t de VLSFO et +0,9 à 1,0 M$ par voyage aller pour un porte-conteneurs de 15 000 EVP (Singapour–Rotterdam, +8 jours à 18 nœuds).'])
    fl.append(h2('8.4 Ports africains : gagnants et perdants'))
    rows = [['Port', 'Escales/jour 2023 → août-sept. 2026', 'Lecture'],
            ['Tanger Med', '13,5 → 12,2 ; 11,1 M EVP en 2025 (record)', 'Gagnant : transbordement Atlantique-Méditerranée'],
            ['Walvis Bay', '1,4 → 2,0 (volumes +78 %)', 'Gagnant : soutage navire à navire'],
            ['Port-Louis (Maurice)', 'soutage ×2 (≈ 1 Mt en 2025)', 'Gagnant : escale de soutage sur la route du Cap'],
            ['Abidjan', '4,4 → 5,2 (volumes +59 %)', 'Gagnant : hub de transbordement ouest-africain'],
            ['Djibouti', '3,8 → 3,5 ; EVP −10,5 % (S1 2025), −17,5 % (S2 2025)', 'Perdant : zone JWC depuis mars 2026 ; 96,7 % du trafic éthiopien'],
            ['Jeddah (référence)', '11,3 → 2,9 (−74 %)', 'Effondrement : bétail de la Corne de l\'Afrique menacé'],
            ['Mombasa', '4,0 → 4,4 mais porte-conteneurs 1,8 → 1,5', 'Fiabilité des rotations dégradée'],
            ['Dakar', '4,2 → 3,9', 'Recul : blocus du JNIM vers le Mali (> 2 000 conteneurs bloqués fin 2025)']]
    fl.append(table(rows, [34 * mm, 62 * mm, CW - 96 * mm]))
    fl.append(Paragraph('Sources : FMI PortWatch (Daily Ports Data, au 18/09/2026) ; TMPA (02/02/2026) ; Banque mondiale, MPO Djibouti (avril 2026) ; ISS Africa (06/2026).', SRC))
    fl.append(callout('Deux chocs symétriques à ne pas surinterpréter', [
        '<b>Thé kényan vers l\'Égypte</b> : le détour par le Cap coûte +1 600 à 1 850 $/EVP (+18,6 jours), soit +0,08-0,09 $/kg (≈ +4 % du prix de Mombasa). Mais les thés de Sri Lanka et d\'Inde vers l\'Égypte subissent le même détour : la position concurrentielle relative du Kenya n\'est pas dégradée.',
        '<b>Cacao ivoirien et ghanéen vers l\'Europe</b> : aucune exposition à Suez, ports hors zone JWC ; les surcharges carburant et ETS ne représentent que 0,2-0,3 % de la valeur.',
        '<b>À l\'inverse, le blé de la mer Noire vers l\'Afrique de l\'Est</b> cumule surprime (≈ 1 %), détour possible (+16,7 jours vers Mombasa) et hausse des prix (+15 % sur un an) : il avantage les céréales régionales (maïs, sorgho, riz).'],
        bg=BLUE_L, bar=BLUE, title_color=BLUE))
    fl.append(PageBreak())
    # ---- 8.5 modèle de coût rendu
    fl.append(h2('8.5 Modèle de coût rendu intégral : tous les paramètres'))
    rows = [['Paramètre', 'Valeur 2026 retenue', 'Source', 'Dans le SaaS ?'],
            ['Droit de douane NPF / ZLECAf', 'Ligne nationale ; taux servi par corridor', 'Barèmes nationaux, modules d\'application', 'Oui'],
            ['Prélèvements (RS, PCS, PCC, PUA, IDF, RDL, cess…)', '0 à 14,5 % selon le pays', 'Barèmes nationaux', 'Oui'],
            ['TVA à l\'importation', '7,5 à 20 % (récupérable par l\'importateur assujetti)', 'Barèmes nationaux', 'Oui'],
            ['Fret maritime de base', 'Intra-africain 2024 : 195-1 850 $/EVP ; Asie→Mombasa 5 130-6 270 $/FEU (juil. 2026)', 'SaaS ; transitaires', 'Partiel (2024)'],
            ['Détour par le Cap', '+2 400 à +6 200 nm ; +7 à +19 jours', 'searoute', 'Non'],
            ['Surprime guerre (coque) répercutée', '0,2-1 % mer Rouge ; ≈ 1 % mer Noire ; 6-10 % Ormuz', 'Assureurs, presse spécialisée', 'Non'],
            ['Surcharges armateurs (guerre, urgence carburant, PSS)', '150-265 $/EVP (carburant) ; 1 000-4 000 $/boîte (guerre, haute saison)', 'Lloyd\'s List, Maersk, CMA CGM', 'Non'],
            ['ETS (liaisons avec l\'UE)', '≈ 59 €/EVP Asie-Europe ; 50 % des émissions Afrique-UE', 'Maersk, Hapag-Lloyd', 'Non'],
            ['Fret aérien périssables', '5-5,8 $/kg Nairobi-Europe (mars 2026)', 'AP ; Hortidaily', 'Partiel (surcharge figée)'],
            ['Assurance cargaison', '0,2-0,5 % de la valeur (+ risque guerre)', 'Pratique de marché (H)', 'Non'],
            ['Frais portuaires (THC, séjour)', 'THC 155-230 $/EVP ; séjour 2,7-16 jours', 'SaaS (ports)', 'Oui'],
            ['Corridors terrestres', 'Abidjan-Lagos 146 $/t ; Dakar-Bamako 128 $/t (hors insécurité)', 'SaaS (corridors)', 'Oui (hors escorte)'],
            ['Portage financier', '10 %/an × jours de transit (H)', 'Hypothèse', 'Non'],
            ['Change, MNT, conformité SPS', 'Non chiffrés ici — équivalents ad valorem des MNT de 5 à 27 %', 'CNUCED', 'Non']]
    fl.append(table(rows, [52 * mm, 60 * mm, 38 * mm, CW - 150 * mm]))
    fl.append(Paragraph('(H) : hypothèse de modélisation. Les paramètres non couverts par le SaaS sont ajoutés hors modèle dans les cas ci-dessous.', SRC))
    # Cas 1
    fl.append(PageBreak())
    fl.append(Paragraph('Cas 1 — Concentré de tomate livré à Mombasa (Kenya) : préférence ZLECAf + proximité face à la Chine', H3))
    china = landed(1000, 20, 2850 + 1000 + 265, 150, 200, 150, 0.003, 0.0, 0.35, 0.045, 32)
    egy_rs = landed(1000, 20, 720 + 265 + 1500, 160, 200, 150, 0.003, 0.001, 0.14, 0.045, 13)
    egy_cap = landed(1000, 20, 2600 + 265, 160, 200, 150, 0.003, 0.0, 0.14, 0.045, 31)
    fl += cost_table([('Chine (Tianjin), NPF 35 %', china), ('Égypte via mer Rouge, ZLECAf 14 %', egy_rs), ('Égypte via le Cap, ZLECAf 14 %', egy_cap)], '$/tonne',
                     'Hypothèses (H) : FOB identique 1 000 $/t pour isoler les autres facteurs ; 20 t par EVP. Chine : 2 850 $/EVP (moitié du fret FEU Asie-Mombasa, juil. 2026) + surcharge haute saison 1 000 $ + carburant 265 $. '
                     'Égypte : benchmark SaaS Port-Saïd–Mombasa 720 $/EVP (2024) + carburant 265 $ + surcharge guerre 1 500 $ (mer Rouge) ou ≈ 2 600 $/EVP par le Cap. IDF 2,5 % + RDL 2 % ; TVA 16 % récupérable non incluse. '
                     'Taux ZLECAf : avis EAC/321/2022 (35 % → 14 % en 2026), vérifié dans le SaaS pour la ligne 2002.90.')
    def g1(fobc=1000, fm=1.0, war=1500, fin=0.10, tev=20):
        c = landed(fobc, tev, (2850 + 1000 + 265) * fm, 150, 200, 150, 0.003, 0.0, 0.35, 0.045, 32, fin)
        e = landed(1000, tev, (720 + 265) * fm + war, 160, 200, 150, 0.003, 0.001, 0.14, 0.045, 13, fin)
        return c['total'] - e['total']
    rows = [['Sensibilité — avantage égyptien via mer Rouge ($/t)', 'Valeur']] + [[a_, Paragraph(f'<b>{fmt(b_)}</b>', TDR)] for a_, b_ in [
        ('Scénario central', g1()), ('Concentré chinois 15 % moins cher (FOB 850 $/t)', g1(fobc=850)), ('Fret +30 % sur toutes les routes', g1(fm=1.3)), ('Fret −30 %', g1(fm=0.7)),
        ('Surcharge guerre mer Rouge nulle (retour à la normale)', g1(war=0)), ('Surcharge guerre doublée (3 000 $/EVP)', g1(war=3000)), ('Portage 15 %/an', g1(fin=0.15)), ('Conteneur chargé à 16 t', g1(tev=16))]]
    fl.append(table(rows, [120 * mm, CW - 120 * mm]))
    gap1 = china['total'] - egy_rs['total']
    fl.append(P(f"<b>Lecture.</b> À prix FOB égal, le concentré égyptien arrive à Mombasa avec un avantage de ≈ {fmt(gap1)} $/t par la mer Rouge et de ≈ {fmt(china['total'] - egy_cap['total'])} $/t même par le Cap. "
                f"Le fournisseur chinois devrait vendre ≈ {fmt(gap1 / 1.4)} $/t moins cher départ usine pour compenser — soit plus de {int(gap1 / 1.4 / 10)} % de son prix. "
                "La préférence (21 points de droit) pèse davantage que le surcoût de guerre. <b>Taille du marché</b> : le Kenya n'importe que ≈ 7,6 M$ de concentré par an "
                "(l'Égypte en exporte 108 M$ ; OEC/BACI, moyenne 2023-2024) — une cible vérifiée mais modeste, à combiner avec l'Afrique de l'Ouest (Nigeria 64 M$, Ghana 59 M$, hors préférence)."))
    # Cas 2
    fl.append(Paragraph('Cas 2 — Sardines en conserve livrées à Abidjan : sans préférence (NPF pour tous), l\'avantage de la proximité', H3))
    tha = landed(2400, 18, 2100 + 265, 150, 185, 150, 0.003, 0.0, 0.20, 0.0722, 38)
    mar = landed(2400, 18, 780 + 265, 170, 185, 150, 0.003, 0.0, 0.20, 0.0722, 8)
    fl += cost_table([('Thaïlande (Laem Chabang), NPF 20 %', tha), ('Maroc (Tanger Med / Agadir), NPF 20 %', mar)], '$/tonne',
                     'Hypothèses (H) : FOB identique 2 400 $/t ; 18 t par EVP. Thaïlande : ≈ 60 % d\'un FEU Asie-Afrique de l\'Ouest (3 150-3 850 $/FEU, juin 2026) + carburant 265 $ ; ≈ 38 jours. '
                     'Maroc : benchmark SaaS Tanger Med–Abidjan 780 $/EVP + carburant 265 $ ; ≈ 8 jours. Droit TEC CEDEAO 20 % et prélèvements documentés dans le SaaS pour la Côte d\'Ivoire (7,22 %). TVA 18 % récupérable non incluse. '
                     'La préférence ZLECAf n\'est pas opposable en Côte d\'Ivoire (décrets d\'application en attente) : les deux origines paient le NPF.')
    def g2(fobt=2400, fm=1.0, fin=0.10, tev=18, days_t=38):
        th = landed(fobt, tev, (2100 + 265) * fm, 150, 185, 150, 0.003, 0.0, 0.20, 0.0722, days_t, fin)
        ma = landed(2400, tev, (780 + 265) * fm, 170, 185, 150, 0.003, 0.0, 0.20, 0.0722, 8, fin)
        return th['total'] - ma['total']
    rows = [['Sensibilité — avantage marocain ($/t)', 'Valeur']] + [[a_, Paragraph(f'<b>{fmt(b_)}</b>', TDR)] for a_, b_ in [
        ('Scénario central', g2()), ('Sardines thaïlandaises 5 % moins chères', g2(fobt=2280)), ('Fret +30 %', g2(fm=1.3)), ('Fret −30 %', g2(fm=0.7)),
        ('Portage 15 %/an', g2(fin=0.15)), ('Transit asiatique de 45 jours', g2(days_t=45)), ('Conteneur chargé à 15 t', g2(tev=15))]]
    fl.append(table(rows, [120 * mm, CW - 120 * mm]))
    fl.append(Paragraph(f"Point mort : l'avantage marocain disparaît si les sardines thaïlandaises sont ≈ {fmt(g2() / 1.28)} $/t moins chères départ usine (≈ {g2() / 1.28 / 24:.1f} % du prix).".replace('.', ',', 1) if False else f"Point mort : l'avantage marocain disparaît si les sardines thaïlandaises sont ≈ {fmt(g2() / 1.28)} $/t moins chères départ usine (≈ {fmt(g2() / 1.28 / 24, 1)} % du prix).", SRC))
    fl.append(P(f"<b>Lecture.</b> Sans aucun avantage tarifaire, le fournisseur marocain gagne ≈ {fmt(tha['total'] - mar['total'])} $/t "
                f"({(1 - mar['total'] / tha['total']) * 100:.1f} % du coût rendu) grâce au fret, à l'assurance, au portage financier et aux droits prélevés sur une valeur CAF plus faible — sans compter "
                "30 jours de délai en moins, des séries plus courtes et un réassort plus fréquent. C'est l'avantage structurel des fournisseurs africains de proximité, que la ZLECAf viendra amplifier. "
                "<b>Marché réel</b> : la Côte d'Ivoire n'importe que ≈ 11,5 M$ de sardines en conserve par an, dont ≈ 8,2 M$ déjà marocaines — l'avantage est acquis ; "
                "le débouché à conquérir est le Ghana (≈ 50 M$, dont 15 M$ marocains). Source : OEC/BACI, moyenne 2023-2024."))
    fl.append(h2('8.6 Opportunités hors préférence : l\'avantage compétitif africain'))
    fl.append(P("Même lorsque la destination applique le droit NPF à toutes les origines, un fournisseur africain peut l'emporter par la distance, le délai, le coût "
                "de production ou la défaillance d'un concurrent pris dans une zone de conflit. Ces flux sont à saisir dès 2026, sans attendre l'ouverture des préférences."))
    rows = [['Flux', 'Régime à destination', 'Concurrent', 'Avantage africain', 'Indicateur'],
            ['Conserves de poisson marocaines → Côte d\'Ivoire, Sénégal, Ghana', 'NPF CEDEAO pour tous (20 %)', 'Thaïlande, Chine', 'Distance (≈ 2 700-3 250 nm contre > 8 500), délai −30 j', 'Conserves (SH 1604) : Ghana 80 M$, Côte d\'Ivoire 46 M$, Sénégal 14 M$ ; le Maroc y vend déjà 27 M$ (BACI 2023-2024)'],
            ['Concentré de tomate égyptien → Nigeria, Ghana', 'NPF CEDEAO', 'Chine (≈ 70 % du marché africain)', 'Port-Saïd–Lagos ≈ 5 100 nm contre ≈ 10 500 depuis Shanghai ; tomate locale abondante', 'Afrique de l\'Ouest : > 61 % des importations africaines de concentré'],
            ['Maïs, riz de Tanzanie, d\'Ouganda, de Zambie → Kenya, Malawi, Zimbabwe', 'Franchise CAE / SADC ; TEC de 35-50 % pour les tiers', 'Mer Noire, Asie, Amériques', 'Transport terrestre ; pas de surprime mer Noire ni de détour', 'Maïs de la Zambie −54 % en 2024 : flux régionaux à sécuriser'],
            ['Engrais phosphatés (Maroc) et urée (Nigeria, Égypte) → Afrique de l\'Est et de l\'Ouest', 'Droits nuls ou faibles', 'Golfe (Ormuz fermé)', 'Aucune exposition à Ormuz ; l\'Afrique est exportatrice nette (14,7 Md$)', 'Urée : 455 → 850 $/t (avril 2026)'],
            ['Fruits et légumes marocains → Mauritanie, Sénégal, Mali (route)', 'NPF CEDEAO (Maroc non membre)', 'Espagne, Pays-Bas', 'Transport routier direct ; fraîcheur', 'Maroc : > 58 % des exportations africaines de légumes frais'],
            ['Sucre d\'Eswatini, de Zambie, du Malawi → Kenya, Tanzanie, RDC', 'TEC CAE 100 % ou 460 $/t, sauf suspensions (Rwanda 25 %)', 'Brésil', 'Proximité (corridors Nacala, Beira, Dar) ; origine africaine utile au chocolat', 'Importations africaines de sucre raffiné : 4,76 Md$'],
            ['Poisson congelé mauritanien et namibien → RDC, Côte d\'Ivoire, Nigeria', 'NPF', 'Chine, UE', 'Chaîne du froid plus courte', 'Nigeria, Côte d\'Ivoire : premiers importateurs de poisson'],
            ['Huile de palme de Côte d\'Ivoire et du Ghana → Burkina Faso, Mali, Niger', 'Franchise CEDEAO / prélèvement AES de 0,5 %', 'Malaisie, Indonésie', 'Pas de double rupture de charge ; route directe', 'Risque : blocus du JNIM sur les axes maliens']]
    fl.append(table(rows, [40 * mm, 30 * mm, 24 * mm, 44 * mm, CW - 138 * mm]))
    fl.append(Paragraph('Sources : SaaS ZLECAf (barèmes, UNIDO, BACI, fret modélisé), searoute, AATM 2025, FAOSTAT, Tomato News, Banque mondiale, presse spécialisée 2026. Distances : calculs par tronçons (±5 %).', SRC))
    return fl
