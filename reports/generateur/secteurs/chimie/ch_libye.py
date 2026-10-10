from layout import *
import json
C = S + 'charts/'
CA = json.load(open(S + 'cases.json'))

def ch_libye():
    fl = [chapter(8, 'La Libye : premier marché de proximité'),
          P("La Libye importe chaque année plusieurs centaines de millions de dollars de produits d'hygiène, de cosmétiques, d'emballages et de peintures, à 588 milles nautiques d'Alger. "
            "Elle n'a pas ratifié la ZLECAf, mais les deux pays sont membres de la Grande zone arabe de libre-échange (GAFTA/ZALE). Le droit de douane n'y est pas l'obstacle : "
            "le vrai verrou est l'accès aux devises et aux lettres de crédit.", LEAD)]
    fl.append(kpis([('≈ 741 M$', 'importations 2024 sur 19 positions du périmètre', 'OEC/BACI, module Statistiques du SaaS (SH × pays)'),
                    ('4,5 %', 'droit NPF moyen libyen (chimie : 4,7 %) ; Libye non membre de l\'OMC', 'OMC, profil tarifaire 2025'),
                    ('42 M$', 'devises accordées pour des biens d\'origine algérienne, janv.-août 2026 (29e rang sur 102)', 'Banque centrale de Libye, 09/2026'),
                    ('6,39 / 9,63', 'dinars par USD : taux officiel et parallèle, fin septembre 2026', 'CBL ; Libya Herald, 09/2026')], cols=4))
    fl.append(Spacer(1, 4))
    fl.append(figure(C + 'k7_libye.png', 'Figure 8.1 — Importations libyennes par position, 2024 (M USD)',
                     'Source : OEC / BACI (HS 2017) via le module Statistiques du SaaS (recherche SH × pays). Données miroir : la Libye ne déclare pas toutes ses importations.', maxh=84 * mm))
    fl.append(PageBreak())
    fl.append(h2('8.1 Le cadre d\'accès : hors ZLECAf, dans la GAFTA'))
    rows = [['Élément', 'Situation au 27/09/2026', 'Source'],
            ['ZLECAf', 'Signée à Kigali (21/03/2018), non ratifiée : aucune préférence ZLECAf', 'tralac, liste du 07/09/2026'],
            ['GAFTA / ZALE', 'Exonération des droits entre membres (Algérie et Libye) sur certificat d\'origine arabe délivré par la CACI ; traitement de la redevance de service libyenne (4 à 5 %) non documenté', 'Ministère du Commerce (Algérie)'],
            ['Tarif libyen', 'Moyenne NPF 4,5 % ; taxe de production 2 % ; taxe de consommation de 25 ou 50 % sur certains produits ; 17 produits interdits (pas de cosmétiques ni de détergents)', 'OMC ; Lloyds Bank Trade'],
            ['Taxe sur les importations 2026', 'Taxe prélevée via les lettres de crédit à partir de fin février 2026 (12 % sur les produits de nettoyage), annulée en mars 2026 par la présidence de la Chambre des représentants ; réactivation possible', 'Libya Observer, 24/02/2026'],
            ['Devises', 'Dévaluation de 14,7 % le 18/01/2026 ; écart d\'environ 50 % avec le marché parallèle ; lettres de crédit en baisse de 11 % (janv.-août 2026) ; plafond lié à l\'impôt payé (20/08/2026)', 'CBL ; Libya Herald'],
            ['Nouvelles règles', 'Décision 449/2026 : importations commerciales hors circuit bancaire interdites à partir du 30/09/2026. Décret 465/2026 : enregistrement des fournisseurs étrangers sur la plateforme PTS (01/01/2027 au-delà de 1 M$/an ; 31/03/2027 au-delà de 100 000 $/an)', 'Libya Herald, 09/2026'],
            ['Conformité', 'Certificat d\'inspection pour toute importation sous lettre de crédit (résolution CBL 96/2015) ; cosmétiques enregistrés auprès du ministère de la Santé', 'TÜV'],
            ['Frontière terrestre', 'Debdeb-Ghadamès fermé depuis 2014 ; réouverture annoncée puis reportée ; toujours fermé au trafic ordinaire fin 2025 ; commission mixte douanière à Tripoli (juillet 2026)', 'Al Wasat ; Libya Herald']]
    fl.append(Paragraph('Tableau 8.1 — Conditions d\'accès au marché libyen', CAP))
    fl.append(table(rows, [30 * mm, 104 * mm, 40 * mm]))
    fl.append(Paragraph('Recherche documentaire du 27/09/2026 ; chaque élément est daté et sourcé dans la base de faits du rapport.', SRC))
    fl.append(h2('8.2 Qui vend en Libye, et où se placer'))
    fl.append(P("Selon la Banque centrale de Libye, les devises accordées au secteur privé de janvier à août 2026 ont financé d'abord des biens d'origine turque (1,95 Md USD, 20,1 %), chinoise (1,57 Md), "
                "égyptienne (1,03 Md) et italienne ; la Tunisie est 8e (317 M USD) et l'Algérie 29e (42 M USD). Les Émirats sont le premier pays <b>bénéficiaire des paiements</b> (22,3 %) : "
                "une large part des achats y transite. Les catégories « produits de nettoyage » (163 M USD, plus 47 M USD sur une seconde ligne) et « produits d'hygiène » (14,5 M USD) "
                "pèsent autant que l'ensemble des exportations algériennes vers la Libye. La Libye produit en revanche de l'urée (Marsa el-Brega, environ 900 kt) : ce n'est pas un débouché pour les engrais azotés algériens."))
    rows = [['Origine', 'Coût de rendu à Tripoli (lessive, 40\')', 'Commentaire']]
    for o in CA['Tripoli']:
        x = CA['Tripoli'][o]
        rows.append([o, f"{x['per_t']} $/t ({x['pct']:.1f} %)".replace('.', ','), {'Algérie (Alger)': 'Avantage maximal, sous réserve de lignes maritimes régulières', 'Turquie (Mersin)': 'Premier fournisseur, écart d\'un point seulement',
                                                                                       'Émirats (Jebel Ali, via le Cap)': 'Pénalisé par la fermeture d\'Ormuz et la mer Rouge', 'Chine (Shanghai, via le Cap)': 'Idem'}.get(o, '')])
    fl.append(Paragraph('Tableau 8.2 — Coût de rendu à Tripoli par origine (hors prix du produit)', CAP))
    fl.append(table(rows, [60 * mm, 56 * mm, 58 * mm]))
    fl.append(Paragraph('Mêmes hypothèses que le tableau 7.5. La Tunisie livre par la route (Ras Jedir), via l\'axe côtier de Zawiya, exposé aux affrontements (mai et septembre 2026).', SRC))
    fl.append(PageBreak())
    fl.append(h2('8.3 Risques et parades'))
    fl += bullets([
        '<b>Politique</b> : deux gouvernements rivaux (Tripoli et l\'Est), sans budget unifié ; dialogue onusien clos en juin 2026 sans accord (Security Council Report, 08/2026).',
        '<b>Sécurité</b> : affrontements à Tripoli (mai 2025) et à Zawiya (mai 2026, plus de 30 selon ACLED) ; arrêt d\'une unité de raffinage le 26/09/2026 ; sud-ouest (Ghadamès, Ghat) fortement militarisé.',
        '<b>Paiement</b> : privilégier la <b>lettre de crédit confirmée</b> par une banque de premier rang ou le paiement d\'avance ; vérifier que le client libyen est éligible aux lettres de crédit et enregistré sur la plateforme PTS ; '
        'la position de la CAGEX sur la Libye n\'est pas publiée et doit être demandée avant tout contrat.',
        '<b>Informel</b> : la décision 449/2026 ferme le commerce frontalier hors circuit bancaire à partir du 30/09/2026 ; les flux « cabas » algériens et tunisiens sont directement visés.'])
    fl.append(h2('8.4 Ce que les opérateurs algériens peuvent viser'))
    rows = [['Cible', 'Produits', 'Voie d\'accès', 'Appui'],
            ['Grossistes d\'hygiène (Tripoli, Misrata, Benghazi, Sebha)', 'Lessives, liquides vaisselle, javel, couches (Faderco, Esquirol, Henkel)', 'Certificat d\'origine arabe ; lettre de crédit confirmée', 'Coût de rendu de 2,9 %'],
            ['Fabricants libyens de détergents', 'Matières premières : silicates, hypochlorite, puis LAB de Skikda (fin 2027)', 'Contrats d\'approvisionnement B2B', 'Plusieurs fabricants identifiés dans les données de la CBL'],
            ['Distribution cosmétique', 'Soins, capillaires, déodorants (Venus, Vague de Fraîcheur)', 'Enregistrement au ministère libyen de la Santé', 'Alternative aux réexportations des Émirats'],
            ['Ministère de la Santé', 'Médicaments : appel d\'offres d\'environ 950 M EUR (avril 2026)', 'Soumission publique ; protocole Saidal-Al-Louloua Al-Oula (05/10/2025)', 'Voir le rapport Pharmaceutique & Santé']]
    fl.append(Paragraph('Tableau 8.3 — Cibles prioritaires en Libye', CAP))
    fl.append(table(rows, [38 * mm, 52 * mm, 46 * mm, 38 * mm]))
    fl.append(Paragraph('Sources : Banque centrale de Libye (usages des devises, janv.-août 2026) ; L\'Algérie Aujourd\'hui (16/04/2026) ; Maghreb Émergent (05/06/2025). Aucun contrat algérien nommé dans les cosmétiques ou détergents n\'a été trouvé pour 2025-2026.', SRC))
    return fl
