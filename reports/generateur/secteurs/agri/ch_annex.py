from layout import *
import json
D = json.load(open(S + 'saas_stats.json')); D2 = json.load(open(S + 'saas_stats2.json')); B2 = json.load(open(S + 'burden2.json'))
CS = D['countries']; VA = D2['agva']; ATR = D2['atr']['intra_african_trade_by_country']
SM = {p['code_iso2']: p for p in D['status_matrix']['pays']}
ISO2 = {'AGO': 'AO', 'BDI': 'BI', 'BEN': 'BJ', 'BFA': 'BF', 'BWA': 'BW', 'CAF': 'CF', 'CIV': 'CI', 'CMR': 'CM', 'COD': 'CD', 'COG': 'CG', 'COM': 'KM', 'CPV': 'CV',
        'DJI': 'DJ', 'DZA': 'DZ', 'EGY': 'EG', 'ERI': 'ER', 'ETH': 'ET', 'GAB': 'GA', 'GHA': 'GH', 'GIN': 'GN', 'GMB': 'GM', 'GNB': 'GW', 'GNQ': 'GQ', 'KEN': 'KE',
        'LBR': 'LR', 'LBY': 'LY', 'LSO': 'LS', 'MAR': 'MA', 'MDG': 'MG', 'MLI': 'ML', 'MOZ': 'MZ', 'MRT': 'MR', 'MUS': 'MU', 'MWI': 'MW', 'NAM': 'NA', 'NER': 'NE',
        'NGA': 'NG', 'RWA': 'RW', 'SDN': 'SD', 'SEN': 'SN', 'SLE': 'SL', 'SOM': 'SO', 'SSD': 'SS', 'STP': 'ST', 'SWZ': 'SZ', 'SYC': 'SC', 'TCD': 'TD', 'TGO': 'TG',
        'TUN': 'TN', 'TZA': 'TZ', 'UGA': 'UG', 'ZAF': 'ZA', 'ZMB': 'ZM', 'ZWE': 'ZW'}
NAMES = {'AGO': 'Angola', 'BDI': 'Burundi', 'BEN': 'Bénin', 'BFA': 'Burkina Faso', 'BWA': 'Botswana', 'CAF': 'Centrafrique', 'CIV': 'Côte d\'Ivoire', 'CMR': 'Cameroun',
         'COD': 'RD Congo', 'COG': 'Congo', 'COM': 'Comores', 'CPV': 'Cabo Verde', 'DJI': 'Djibouti', 'DZA': 'Algérie', 'EGY': 'Égypte', 'ERI': 'Érythrée', 'ETH': 'Éthiopie',
         'GAB': 'Gabon', 'GHA': 'Ghana', 'GIN': 'Guinée', 'GMB': 'Gambie', 'GNB': 'Guinée-Bissau', 'GNQ': 'Guinée équatoriale', 'KEN': 'Kenya', 'LBR': 'Liberia', 'LBY': 'Libye',
         'LSO': 'Lesotho', 'MAR': 'Maroc', 'MDG': 'Madagascar', 'MLI': 'Mali', 'MOZ': 'Mozambique', 'MRT': 'Mauritanie', 'MUS': 'Maurice', 'MWI': 'Malawi', 'NAM': 'Namibie',
         'NER': 'Niger', 'NGA': 'Nigeria', 'RWA': 'Rwanda', 'SDN': 'Soudan', 'SEN': 'Sénégal', 'SLE': 'Sierra Leone', 'SOM': 'Somalie', 'SSD': 'Soudan du Sud',
         'STP': 'São Tomé-et-Príncipe', 'SWZ': 'Eswatini', 'SYC': 'Seychelles', 'TCD': 'Tchad', 'TGO': 'Togo', 'TUN': 'Tunisie', 'TZA': 'Tanzanie', 'UGA': 'Ouganda',
         'ZAF': 'Afrique du Sud', 'ZMB': 'Zambie', 'ZWE': 'Zimbabwe'}
REGIME = {}
for k in ['BEN', 'BFA', 'CIV', 'CPV', 'GHA', 'GIN', 'GMB', 'GNB', 'LBR', 'MLI', 'NER', 'NGA', 'SEN', 'SLE', 'TGO']: REGIME[k] = 'TEC CEDEAO'
for k in ['BDI', 'COD', 'KEN', 'RWA', 'SSD', 'TZA', 'UGA', 'SOM']: REGIME[k] = 'TEC CAE'
for k in ['CAF', 'CMR', 'COG', 'GAB', 'GNQ', 'TCD']: REGIME[k] = 'TEC CEMAC'
for k in ['BWA', 'LSO', 'NAM', 'SWZ', 'ZAF']: REGIME[k] = 'TEC SACU'
NOT_RAT = {'BEN', 'LBY', 'SSD', 'SDN'}
STAT = {'ADOPTE_ET_DIRECTIVE': 'Offre adoptée', 'ADOPTE_PROVISOIREMENT': 'Adoptée prov.', 'AUTRE_DECLARATION': 'Autre décl.', 'LISTE_PROVISOIRE_DIRECTIVE': 'Liste prov.', 'SOUMIS': 'Soumise'}
APPLIED = {'KEN': 'Appliquée', 'EGY': 'Appliquée', 'MAR': 'Appliquée', 'ZAF': 'Appliquée', 'DZA': 'Appliquée', 'ETH': 'Liste requise', 'ZMB': 'Liste requise', 'NGA': 'Liste requise', 'CIV': 'Liste requise'}

def ch_annex_countries():
    fl = [chapter('A1', 'Annexe 1 — Tableau de bord des 54 pays')]
    fl.append(P("Pour chaque État : régime tarifaire, statut ZLECAf, protection agricole moyenne mesurée par le SaaS, charge fiscale théorique à l'import, poids de "
                "l'agriculture et intensité du commerce intra-africain. Les 14 pays sans barème national intégré au SaaS sont signalés « n.i. » (non intégré) ; "
                "leur tarif est alors celui de leur régime lorsqu'il s'agit d'une union douanière.", BODY_L))
    hdr = ['Pays', 'Régime tarifaire', 'Ratif.', 'Offre (UA)', 'Application', 'DD agri moyen', 'Charge import*', 'Agri % PIB', 'Intra-Afr. 2025 (Md$)', 'Fiab.']
    rows = [hdr]
    for iso in sorted(NAMES, key=lambda k: NAMES[k]):
        c = CS.get(iso); b = B2.get(iso)
        sm = SM.get(ISO2[iso], {})
        rat = 'Non signé' if iso == 'ERI' else ('Non' if iso in NOT_RAT else 'Oui')
        va = VA.get(iso); atr = ATR.get(iso)
        rows.append([NAMES[iso], REGIME.get(iso, 'National'), rat, ('Via SACU' if sm.get('statut_declare')=='AUTRE_DECLARATION' and sm.get('union_douaniere')=='SACU' else STAT.get(sm.get('statut_declare'), '—')), APPLIED.get(iso, '—'),
                     (f"{c['avg_ag']:.1f}".replace('.', ',') if c and iso != 'EGY' else (str(json.load(open(S+'egy.json'))['egy_ex22']).replace('.', ',') + '**' if iso == 'EGY' else 'n.i.')),
                     (f"{b[0]:.0f}" if b else '—'), (f"{va[1]:.1f}".replace('.', ',') if va else '—'),
                     (f"{atr['intra_african_2025_busd']:.2f}".replace('.', ',') if atr else '—'), (c['reliability'] if c else '—')])
    ext = []
    for i, r in enumerate(rows[1:], 1):
        if r[4] == 'Appliquée': ext.append(('TEXTCOLOR', (4, i), (4, i), GREEN))
        if r[2] != 'Oui': ext.append(('TEXTCOLOR', (2, i), (2, i), RED))
        if r[5] == 'n.i.': ext.append(('TEXTCOLOR', (5, i), (5, i), MUTED))
    t = table(rows, [27 * mm, 20 * mm, 12 * mm, 21 * mm, 17 * mm, 15 * mm, 14 * mm, 13 * mm, 17 * mm, CW - 156 * mm], extra=ext, align_right_from=5)
    fl.append(t)
    fl.append(Paragraph('n.i. : barème national non intégré au SaaS. *Charge théorique : DD + prélèvements + TVA au taux normal, lignes SH 01-21 et 23 (% CAF). **Égypte hors chapitre 22. Fiabilité SaaS : A = barème national officiel vérifié ; '
                        'B = tarif extérieur commun ou source partielle. Sources : SaaS ZLECAf (barèmes, e-Tariff Book UA — statuts au 13/09/2026, registre d\'application), '
                        'tralac (ratifications au 04/09/2026), Banque mondiale WDI, Afreximbank ATR 2026.', SRC))
    return fl
