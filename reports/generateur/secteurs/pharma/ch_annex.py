import os
from layout import *
import json
CS = json.load(open(S + 'saas_pharma.json'))['countries']
SM = {p['code_iso2']: p for p in json.load(open(os.environ['RG_REPO'] + '/backend/data/official_preferential/afcfta_status_matrix_2026-09-13.json'))['pays']}
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

GAFI = {'AGO', 'CMR', 'CIV', 'COD', 'KEN', 'SSD'}

def ch_annex_countries():
    fl = [chapter('A1', 'Annexe 1 — Tableau de bord santé des 54 pays')]
    fl.append(P("Pour chaque État : régime tarifaire, statut ZLECAf, droit NPF moyen mesuré par le SaaS sur quatre segments de santé, et statut GAFI après la plénière de juin 2026. "
                "Les 14 pays sans barème national intégré au SaaS sont signalés « n.i. » ; leur tarif est alors celui de leur union douanière, le cas échéant.", BODY_L))
    hdr = ['Pays', 'Régime tarifaire', 'Ratif.', 'Offre (UA)', 'Application', 'Médic. dosés', 'Principes actifs', 'Instruments', 'Gants', 'GAFI']
    rows = [hdr]
    def g(c, k):
        v = c['groups'].get(k) if c else None
        return 'n.i.' if not c else ('—' if not v else f"{v['avg']:.1f}".replace('.', ','))
    for iso in sorted(NAMES, key=lambda k: NAMES[k]):
        c = CS.get(iso); sm = SM.get(ISO2[iso], {})
        rat = 'Non signé' if iso == 'ERI' else ('Non' if iso in NOT_RAT else 'Oui')
        rows.append([NAMES[iso], REGIME.get(iso, 'National'), rat, ('Via SACU' if sm.get('statut_declare') == 'AUTRE_DECLARATION' and sm.get('union_douaniere') == 'SACU' else STAT.get(sm.get('statut_declare'), '—')),
                     APPLIED.get(iso, '—'), g(c, 'G04'), g(c, 'G01'), g(c, 'G09'), g(c, 'G08'), 'Liste grise' if iso in GAFI else '—'])
    ext = []
    for i, r in enumerate(rows[1:], 1):
        if r[4] == 'Appliquée': ext.append(('TEXTCOLOR', (4, i), (4, i), GREEN))
        if r[2] != 'Oui': ext.append(('TEXTCOLOR', (2, i), (2, i), RED))
        if r[9] != '—': ext.append(('TEXTCOLOR', (9, i), (9, i), RED))
        for j in range(5, 9):
            if r[j] == 'n.i.': ext.append(('TEXTCOLOR', (j, i), (j, i), MUTED))
    fl.append(table(rows, [27 * mm, 20 * mm, 12 * mm, 21 * mm, 17 * mm, 15 * mm, 15 * mm, 15 * mm, 13 * mm, CW - 155 * mm], extra=ext, align_right_from=5, font=7))
    fl.append(Paragraph('n.i. : barème national non intégré au SaaS. Droits NPF moyens en % (moyenne simple des lignes SH6 : médicaments dosés 30.04 ; principes actifs 29.36-29.41 ; instruments 90.18-90.20 ; gants 40.14-40.15). '
                        'GAFI : juridictions sous surveillance renforcée après la plénière du 19/06/2026. Sources : SaaS ZLECAf (barèmes, e-Tariff Book UA, statuts au 13/09/2026, registre d\'application), tralac, GAFI.', SRC))
    return fl
