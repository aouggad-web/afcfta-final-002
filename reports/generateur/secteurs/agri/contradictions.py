"""Contradictions entre sources : exposées, jamais tranchées.

Règle éditoriale : quand deux sources (ou deux niveaux de nomenclature) donnent des valeurs incompatibles, le rapport
affiche les deux, décrit l'écart, liste les explications possibles sans en choisir une, et dit ce qui permettrait de trancher.

- REGISTRE : contradictions documentaires relevées dans les notes de recherche (recherche/*.md), codes C01…
- nomenclature() : contradictions calculées dans cibles.json — la SH6 citée est marginale alors que sa position SH4
  porte un vrai commerce (codes N01…). Le verdict sur la SH6 citée et celui de la sous-position voisine sont donnés tous deux.
- ref(code) : renvoi à l'annexe, affiché seulement dans les plans d'action (RG_EDITION), où l'annexe existe.
"""
import os

from layout import *
from ch_verif import CB, PAYS, DEST, lib, sh, fmt_m, fmt_t, fr

ED = os.environ.get('RG_EDITION')
FOCUS = os.environ.get('RG_PAYS_FOCUS', 'DZA').upper()
TOUTES = ('producteurs', 'industriels', 'negoce', 'intrants')
R = CB.get('reperes', {})


def _m(k):
    return fmt_m(R.get(k, 0))


# valeurs : (valeur, source, date, statut)
REGISTRE = [
    dict(code='C01', editions=('producteurs',), sujet='Pertes après récolte en Afrique subsaharienne',
         valeurs=[('23,0 % (récolte → détail, toutes denrées)', 'FAO, indicateur ODD 12.3.1', '2023', 'primaire'),
                  ('37 % (toute la nourriture)', 'FAO', '2011', 'primaire, ancien'),
                  ('10-12 % au stockage ; 12-20 % pour le maïs avant vente', 'APHLIS via Banque mondiale', '2014', 'primaire'),
                  ('1,4 % (Malawi) à 5,9 % (Ouganda) pour le maïs, déclaré par les agriculteurs', 'Enquêtes LSMS-ISA via Banque mondiale', '2014', 'primaire')],
         ecart='De 1,4 % à 37 % selon la source, le produit et le périmètre : les pertes déclarées par les exploitants sont 4 à 26 fois plus faibles que les estimations institutionnelles.',
         hypotheses=['Périmètres différents : exploitation seule contre chaîne complète jusqu\'au détail.',
                     'Mesure déclarative contre modélisation ; pertes de qualité non perçues comme des pertes par l\'agriculteur.',
                     'Années et produits différents (maïs contre toutes denrées).'],
         traitement='Le chiffre FAO est affiché en indicateur, accompagné des pertes déclarées par les agriculteurs.',
         trancher='Mesures APHLIS par pays, produit et étape de la chaîne, pour la même année.'),
    dict(code='C02', editions=('producteurs',), sujet='Surcoût « risque de guerre » sur les agrumes égyptiens (saison 2025/26)',
         valeurs=[('3 000 à 5 000 $ par conteneur', 'Exportateur cité par FreshPlaza', '≈ 09/2026', 'secondaire'),
                  ('100 à 300 $ par conteneur', 'Transitaire Seagate', '31/08/2026', 'secondaire')],
         ecart='Rapport de 10 à 50.',
         hypotheses=['Surcoût total du voyage (détour, fret, surcharges) contre prime de risque seule.',
                     'Destinations différentes (Europe du Nord, Golfe, Asie) et dates différentes dans la saison.'],
         traitement='Les deux fourchettes sont données dans le tableau des coûts du froid.',
         trancher='Devis détaillés (fret de base, surcharge de guerre, carburant) sur une même route et une même semaine.'),
    dict(code='C03', editions=('producteurs', 'negoce'), sujet='Allongement du transit Kenya → Europe par le cap de Bonne-Espérance',
         valeurs=[('De 18-20 jours à 40-45 jours', 'FPEAK, cité par Xinhua', '07/09/2024', 'secondaire'),
                  ('+10 à 14 jours (jusqu\'à 25 jours sur certaines rotations)', 'LogUpdate Africa', '2025-2026', 'secondaire')],
         ecart='+20 à 27 jours contre +10 à 14 jours.',
         hypotheses=['Délai porte-à-porte (transbordements, attente de place reefer) contre temps de mer seul.',
                     'Période de crise aiguë (2024) contre rotations réorganisées (2025-2026).'],
         traitement='Les deux valeurs sont citées.',
         trancher='Horaires des armateurs sur Mombasa–Rotterdam, avec et sans transbordement.'),
    dict(code='C04', editions=('producteurs',), sujet='Capacité frigorifique commerciale de l\'Afrique du Sud',
         valeurs=[('400 000 à 600 000 positions palettes', 'Estimation du secteur (Cold Chain SA)', '2025-2026', 'secondaire'),
                  ('745 000 positions palettes (955 000 en projection)', 'Autre modèle, même publication', '2025-2026', 'secondaire')],
         ecart='+24 à +86 %.',
         hypotheses=['Entrepôts commerciaux seuls contre capacités captives des industriels et distributeurs.', 'Méthodes d\'estimation différentes.'],
         traitement='La fourchette et le modèle sont affichés.',
         trancher='Recensement des opérateurs (CCH, Vector, Maersk…) et des capacités captives.'),
    dict(code='C05', editions=('producteurs',), sujet='Besoin en camions frigorifiques au Nigeria',
         valeurs=[('25 000 camions (moins de 1 000 en service)', 'NAN', '2025', 'secondaire'),
                  ('5 000 camions', 'OTACCWA', '2025', 'secondaire')],
         ecart='Facteur 5.',
         hypotheses=['Périmètres différents (tous les produits périssables ou seulement certaines filières).', 'Horizons de besoin différents.'],
         traitement='Les deux besoins sont cités à côté du parc en service.',
         trancher='Étude de besoin publiée avec sa méthode (produits, distances, rotations).'),
    dict(code='C06', editions=('producteurs', 'negoce'), sujet='Statut de la ligne RoRo Agadir–Dakar',
         valeurs=[('« Lancée »', 'FreshPlaza', '03/01/2025', 'secondaire'),
                  ('« Toujours pas opérationnelle », aucun progrès concret', 'Le360', '13/01/2026', 'secondaire')],
         ecart='Lancement annoncé contre service inexistant un an plus tard.',
         hypotheses=['Annonce ou signature (protocole du 11/12/2024) présentée comme un lancement.', 'Service ouvert puis suspendu.'],
         traitement='Les deux affirmations sont citées ; la ligne n\'est pas intégrée aux coûts.',
         trancher='Horaire publié par l\'armateur ou confirmation de l\'autorité portuaire d\'Agadir.'),
    dict(code='C07', editions=('producteurs', 'intrants'), sujet='Taille du marché africain des semences (2025)',
         valeurs=[('3,15 Md$', 'Mordor Intelligence', '2025', 'secondaire'), ('3,28 Md$', 'Research and Markets', '2025', 'secondaire'),
                  ('5,22 Md$ (Moyen-Orient et Afrique)', 'Research and Markets', '2025', 'secondaire')],
         ecart='≈ 4 % entre les deux estimations africaines ; la troisième couvre un autre périmètre.',
         hypotheses=['Périmètres (semences certifiées seules, inclusion des plants) et méthodes propres à chaque cabinet.'],
         traitement='Les deux valeurs africaines sont données.', trancher='Aucune source publique : ces estimations restent indicatives.'),
    dict(code='C08', editions=('producteurs', 'intrants'), sujet='Importations algériennes de plants de pomme de terre',
         valeurs=[('90 000 t (2023), ≈ 25 % des besoins', 'Ministre, via Algérie Patriotique', '28/11/2024', 'secondaire'),
                  ('De 140 000 t (2020) à 50 000 t', 'Observ\'Algérie', '25/11/2025', 'secondaire'),
                  ('120 000 à 150 000 t par an', 'FreshPlaza.fr', '≈ 2019', 'secondaire, ancien'),
                  ('Autosuffisance de 80 %, ≈ 120 000 t importées', 'Ecotimes', '23/05/2021', 'secondaire'),
                  ('≈ 70 % des plants importés', 'Potatopedia', 'non daté', 'secondaire')],
         ecart='De 50 000 à 150 000 t ; « 80 % d\'autosuffisance » contre « 70 % importés ».',
         hypotheses=['Années différentes (2019 à 2025) dans un marché en recul rapide.', 'Plants certifiés importés contre ensemble des plants (y compris fermiers).',
                     'Tonnage contre valeur.'],
         traitement='La fourchette est donnée sans être réduite.', trancher='Statistiques douanières algériennes (0701.10) par année, et CNCC pour la production certifiée.'),
    dict(code='C09', editions=('producteurs', 'intrants'), sujet='DAPS algérien sur les plants de pomme de terre (0701.10)',
         valeurs=[('DAPS de 70 %', 'Registre du SaaS (tarif d\'usage 2020)', '2020', 'donnée interne'),
                  ('DD 5 %, TVA, TCS, PRCT — pas de DAPS', 'Relevé conformepro.dz et DGD', '29/08/2026', 'primaire (relevé)')],
         ecart='Charge à l\'import hors TVA de ≈ 10 % contre ≈ 80 %.',
         hypotheses=['Le DAPS vise la pomme de terre de consommation (0701.90) et le registre l\'applique à toute la position 0701.',
                     'Exonération des semences prévue par un texte non codé dans le registre.', 'Évolution des listes DAPS depuis 2020.'],
         traitement='Les deux sources sont citées sous le tableau des semences ; le taux ZLECAf affiché est le droit de douane seul.',
         trancher='Liste DAPS en vigueur (loi de finances) et tarif d\'usage 2026 de la DGD.'),
    dict(code='C10', editions=('industriels',), sujet='Prix de l\'électricité industrielle au Nigeria',
         valeurs=[('0,050 $/kWh (65,77 NGN)', 'GlobalPetrolPrices, tarif « business »', '12/2025', 'secondaire'),
                  ('209,5 NGN/kWh (≈ 0,14 $ à 1 500 NGN/$, taux non sourcé)', 'NERC, bande A', '2026', 'primaire'),
                  ('100 à 230 NGN/kWh selon la DisCo', 'Billsguide (clients industriels MD)', '2026', 'secondaire')],
         ecart='Facteur 1,5 à 3,5 en monnaie locale.',
         hypotheses=['Moyenne de GPP sur toutes les bandes de service, contre tarif de la bande la mieux desservie.', 'Dates et taux de change différents.',
                     'Coût réel des industriels augmenté par l\'autoproduction au gazole (non comptée dans les deux cas).'],
         traitement='Le chiffre GPP est affiché à côté du tarif de la bande A.', trancher='Factures d\'industriels par bande et DisCo, au même mois.'),
    dict(code='C11', editions=('industriels',), sujet='Prix de l\'électricité commerciale en Égypte',
         valeurs=[('0,038 $/kWh (1,94 EGP)', 'GlobalPetrolPrices', '12/2025', 'secondaire'),
                  ('1,62 à 2,79 EGP/kWh au-delà de 1 000 kWh', 'Egypt Independent (grille commerciale)', '09/07/2026', 'secondaire')],
         ecart='Jusqu\'à +44 % en monnaie locale.',
         hypotheses=['Hausses tarifaires de 2026 postérieures au relevé GPP.', 'Tarif commercial par tranches contre tarif industriel moyen.'],
         traitement='Les deux sont affichés.', trancher='Grille EgyptERA d\'avril 2026 (inaccessible le 29/09/2026).'),
    dict(code='C12', editions=('industriels',), sujet='Délestages au Ghana (avril-mai 2026)',
         valeurs=[('Plan de délestage de 800 MW du 25/04 au 01/05/2026', '3News', '04/2026', 'secondaire'),
                  ('Aucun programme officiel de délestage', 'ECG (démenti)', '2026', 'primaire')],
         ecart='Délestage planifié contre démenti.', hypotheses=['Coupures réelles non officialisées.', 'Calendrier non validé repris par la presse.'],
         traitement='Les deux versions sont citées.', trancher='Données de l\'opérateur de réseau (GRIDCo) sur l\'énergie non servie.'),
    dict(code='C13', editions=('industriels',), sujet='Cajou transformé en Côte d\'Ivoire en 2025',
         valeurs=[('≈ 600 000 t (+67 %)', 'African Cashew Alliance', '2026', 'secondaire'),
                  ('659 579 t (+91,7 % sur 344 028 t)', 'Autre source de presse', '2026', 'secondaire')],
         ecart='≈ 10 %.', hypotheses=['Campagne commerciale contre année civile.', 'Chiffre arrondi contre chiffre officiel du Conseil coton-anacarde.'],
         traitement='Les deux sont cités.', trancher='Bilan officiel du Conseil du coton et de l\'anacarde.'),
    dict(code='C14', editions=('intrants',), sujet='Prix de l\'urée en 2026',
         valeurs=[('≈ 400 → 850 $/t en avril, 453 $/t en juin', 'OMC (10/07/2026) ; Banque mondiale', '2026', 'primaire'),
                  ('630 $/t (Moyen-Orient FOB)', 'IFDC', '02/06/2026', 'primaire'),
                  ('« moins de 500 puis plus de 700 $/t »', 'ISS', '28/04/2026', 'secondaire'),
                  ('933 à 1 059 $/t rendu en Tanzanie, au Malawi et en Afrique du Sud', 'AMIS', '07/2026', 'à vérifier')],
         ecart='En juin, 453 $/t contre 630 $/t ; le prix rendu double le prix FOB.',
         hypotheses=['Indices différents : moyenne mensuelle mondiale contre FOB Moyen-Orient.', 'Prix FOB contre prix rendu (fret, surprime, marges).', 'Dates différentes dans un marché très volatil.'],
         traitement='Les séries sont citées avec leur définition.', trancher='Comparer à indice, origine et date identiques.'),
    dict(code='C15', editions=('intrants',), sujet='Prix du DAP en 2026',
         valeurs=[('≈ 580 → 770 $/t au pic', 'OMC', '10/07/2026', 'primaire'), ('658,3 $/t en mars', 'Banque mondiale, Pink Sheet', '04/2026', 'à vérifier'),
                  ('869-875 $/t (MAP : 907-927 $/t)', 'IFDC', '02/06/2026', 'primaire')],
         ecart='Jusqu\'à +33 % entre la valeur de mars et celle de juin.', hypotheses=['Produits de référence et ports différents.', 'Dates différentes.'],
         traitement='Non repris en chiffre unique.', trancher='Même indice et même port.'),
    dict(code='C16', editions=('intrants',), sujet='Capacité d\'urée de l\'Algérie (Sorfert)',
         valeurs=[('Sorfert 1,2 Mt/an ; total Algérie 3,6 Mt/an', 'Argus', 'n.d.', 'secondaire, à vérifier'),
                  ('Sorfert 0,8 Mt/an d\'urée (1 Mt d\'ammoniac) ; total implicite 3,2 Mt/an', 'Fertiglobe', 'n.d.', 'primaire (entreprise)')],
         ecart='0,4 Mt/an.', hypotheses=['Capacité nominale contre production déclarée.', 'Urée granulée contre urée totale.'],
         traitement='La capacité algérienne est donnée comme 3,2 à 3,6 Mt/an.', trancher='Rapport annuel de Sorfert ou de Fertiglobe.'),
    dict(code='C17', editions=('intrants',), sujet='Investissement de Dangote à Gode (Éthiopie)',
         valeurs=[('2,5 Md$', 'Presse', '10/2025', 'secondaire'), ('4 Md$', 'IFDC', '02/06/2026', 'primaire')],
         ecart='+60 %.', hypotheses=['Révision du budget du projet.', 'Périmètre (usine seule ou avec infrastructures gazières).'],
         traitement='Aucun montant n\'est repris dans le texte.', trancher='Accord d\'investissement publié.'),
    dict(code='C18', editions=('intrants',), sujet='Parc de tracteurs en Afrique',
         valeurs=[('Moins de 2 tracteurs pour 1 000 ha', 'FAO, cité par Africa Renewal', '2019', 'secondaire, ancien'),
                  ('≈ 28 tracteurs pour 1 000 ha (contre 241 ailleurs)', 'Étude sur ResearchGate', 'n.d.', 'à vérifier')],
         ecart='Facteur 14.', hypotheses=['Unité différente (par exemple pour 100 km²).', 'Données anciennes ou périmètre régional différent.'],
         traitement='Aucune des deux valeurs n\'est retenue ; les deux sont exposées.', trancher='Série FAO récente (SOFA 2022, mécanisation motorisée).'),
    dict(code='C19', editions=('intrants',), sujet='Taille du marché africain des machines agricoles (2025)',
         valeurs=[('5,2 Md$', 'Mordor Intelligence', '2025', 'secondaire'), ('3,52 à 4,65 Md$', 'Autres cabinets', '2025', 'secondaire')],
         ecart='Jusqu\'à +48 %.', hypotheses=['Périmètres (irrigation, pièces, occasion) et méthodes propres à chaque cabinet.'],
         traitement='La fourchette 3,5-5,2 Md$ est affichée.', trancher='Aucune source publique.'),
    dict(code='C20', editions=('intrants',), sujet='Fonds levés par TROTRO Tractor (Ghana)',
         valeurs=[('22,2 M$', 'PitchBook', 'n.d.', 'secondaire'), ('50 000 $', 'Tracxn', 'n.d.', 'secondaire')],
         ecart='Facteur 444.', hypotheses=['Confusion avec un autre acteur ou inclusion de financements de partenaires.'],
         traitement='Aucun montant n\'est repris.', trancher='Communication de l\'entreprise.'),
    dict(code='C21', editions=('intrants',), sujet='Irrigation économe en eau en Algérie',
         valeurs=[('15 % des superficies irriguées (> 2 M ha)', 'algerie-eco', '27/10/2025', 'secondaire'),
                  ('850 000 ha au goutte-à-goutte (> 40 %)', 'Autre extrait', 'n.d.', 'à vérifier')],
         ecart='≈ 300 000 ha contre 850 000 ha.', hypotheses=['Surfaces équipées contre surfaces effectivement irriguées.', 'Inclusion de l\'aspersion.'],
         traitement='Aucune valeur n\'est reprise.', trancher='Statistiques du ministère de l\'Agriculture.'),
    dict(code='C22', editions=('intrants',), sujet='Production d\'aliments composés en Afrique (2025)',
         valeurs=[('64,2 Mt (+11,5 %)', 'Alltech Agri-Food Outlook 2026', '2026', 'primaire'),
                  ('102,5 Mt pour Afrique + Moyen-Orient, Afrique « +12 % »', 'Extrait de la même édition', '2026', 'à vérifier')],
         ecart='+11,5 % contre +12 %.', hypotheses=['Arrondi ou périmètre régional différent.'],
         traitement='Le chiffre africain est affiché.', trancher='Rapport PDF complet d\'Alltech.'),
    dict(code='C23', editions=('negoce',), sujet='Certificat d\'origine ZLECAf en Algérie',
         valeurs=[('Délivré par la douane', 'DGD', '2026', 'primaire'), ('Délivré par la CACI puis visé par la douane', 'CACI ; ministère du Commerce', '2026', 'primaire'),
                  ('Validité de 12 mois', 'B&FT (Ghana)', '07/03/2023', 'secondaire'), ('Validité de 6 mois', 'Résumé de recherche', 'n.d.', 'à vérifier')],
         ecart='Deux autorités de délivrance ; 6 ou 12 mois de validité.',
         hypotheses=['Procédure ZLECAf (douane) confondue avec le certificat d\'origine non préférentiel (CACI).', 'Règles nationales différentes des règles de l\'Annexe 2.'],
         traitement='Le tableau des formalités affiche les deux.', trancher='Annexe 2 de l\'Accord (validité) et note de la DGD (site indisponible le 29/09/2026).'),
    dict(code='C24', editions=('negoce',), sujet='Couverture de PAPSS',
         valeurs=[('Plus de 30 pays', 'Presse', '2026', 'secondaire'), ('24 banques centrales', 'Presse', '2026', 'secondaire')],
         ecart='30 contre 24.', hypotheses=['Pays connectés contre pays opérationnels.'],
         traitement='Les deux chiffres sont cités.', trancher='Liste officielle d\'Afreximbank.'),
    dict(code='C25', editions=('producteurs', 'negoce'), sujet='Importations de poisson de la Côte d\'Ivoire',
         valeurs=[('848 M$ de « poisson transformé »', 'UNIDO IDSB (SaaS)', '2023', 'primaire'),
                  (f'{_m("CIV_imp_1604")} M$ de préparations et conserves (SH 1604)', 'OEC/BACI, moyenne 2023-2024', '2023-2024', 'primaire'),
                  (f'{_m("CIV_imp_0303")} M$ de poisson congelé (SH 0303)', 'OEC/BACI, moyenne 2023-2024', '2023-2024', 'primaire')],
         ecart='848 M$ contre 46 M$ pour les seules conserves.',
         hypotheses=['La branche UNIDO « transformation du poisson » (CITI 1020) couvre le poisson congelé, alors que la SH 1604 ne couvre que les conserves.',
                     'Classements statistiques différents (activité industrielle contre produit).'],
         traitement='Les deux sources sont citées ; le débouché des conserves est mesuré en SH 1604.',
         trancher='Table de passage CITI 1020 → SH pour la Côte d\'Ivoire.'),
    dict(code='C26', editions=TOUTES, sujet='Exportations d\'agrumes du Maroc',
         valeurs=[(f'{_m("MAR_exp_080510")} M$ d\'oranges (SH 0805.10)', 'OEC/BACI, moyenne 2023-2024', '2023-2024', 'primaire'),
                  (f'{_m("MAR_exp_0805")} M$ d\'agrumes (SH 0805, dont clémentines et mandarines)', 'OEC/BACI, moyenne 2023-2024', '2023-2024', 'primaire')],
         ecart='Facteur 11 selon le niveau de nomenclature.',
         hypotheses=['Le Maroc exporte surtout des petits agrumes (clémentines, mandarines), pas des oranges.'],
         traitement='L\'exemple des oranges utilise la SH6 0805.10, celle de la cible publiée ; le total des agrumes est donné à côté.',
         trancher='Sans objet : les deux chiffres sont exacts, ils ne mesurent pas le même produit.'),
    dict(code='C27', editions=('producteurs', 'negoce'), sujet='Temps de trajet Mombasa–Malaba (corridor Nord)',
         valeurs=[('70 h (médiane)', 'Observatoire du corridor Nord', 'S1 2025', 'primaire'), ('76 à 80 h', 'Gouvernement kényan', '21/04/2026', 'primaire')],
         ecart='+6 à 10 h.', hypotheses=['Médiane contre moyenne ; périodes différentes.'],
         traitement='Les deux sont cités.', trancher='Série mensuelle de l\'observatoire.'),
    dict(code='C28', editions=('industriels',), sujet='Résultat 2025 de Juhayna (Égypte)',
         valeurs=[('RN part du groupe 1,91 Md EGP, −30 %', 'Communiqué 4T25', '03/2026', 'primaire'), ('« −20 % »', 'Presse', '03/2026', 'secondaire')],
         ecart='10 points.', hypotheses=['Résultat net total contre part du groupe.'], traitement='Le chiffre d\'affaires seul est repris.', trancher='États financiers audités.'),
]


LE = {'DZA': ('l\'Algérie', 'en Algérie'), 'EGY': ('l\'Égypte', 'en Égypte'), 'KEN': ('le Kenya', 'au Kenya'), 'MAR': ('le Maroc', 'au Maroc'),
      'ZAF': ('la SACU', 'dans la SACU')}


def _ed_nomenclature(hs):
    return ('producteurs', 'negoce') if hs[:2] < '15' else ('industriels', 'negoce')


def nomenclature():
    """Cibles dont la SH6 citée est marginale (< seuil) alors que la position SH4 dépasse le seuil de marché."""
    seuil = CB['seuils']['marche']
    groupes = {}
    for a in CB['audit']:
        if a['verdict'] == 'RETENUE' or not any('trop petit' in x for x in a['motifs']) or a.get('sh4', {}).get('imp_dest', 0) < seuil:
            continue
        groupes.setdefault((a['d'], a['hs']), []).append(a)
    out = []
    for i, ((d, hs), lst) in enumerate(sorted(groupes.items()), 1):
        a = lst[0]
        dn = DEST.get(d, PAYS.get(d, d))
        le, en = LE.get(d, (dn, 'à ' + dn))
        orig = ', '.join(PAYS.get(x['o'], x['o']) for x in lst)
        princ = ' ; '.join(f"{sh(h)} {fmt_m(v)} M$" for h, v in a['sh4']['principales'])
        vals = [(f"{fmt_m(a['imp_dest'])} M$ importés en {sh(hs)} ({lib(hs)})", 'OEC/BACI, moyenne 2023-2024', '2023-2024', 'primaire'),
                (f"{fmt_m(a['sh4']['imp_dest'])} M$ importés pour la position {hs[:4]} ({princ})", 'OEC/BACI, moyenne 2023-2024', '2023-2024', 'primaire')]
        hyp = [f'La cible publiée visait un produit de la position {hs[:4]}, mais sous une sous-position que {le} importe peu : codage à revoir.',
               f'Le produit cité est réellement marginal {en} ; le commerce de la position porte sur un autre produit, pour lequel les origines citées ne sont pas forcément compétitives.']
        vv = []
        for x in lst:
            w = x.get('voisine')
            if w:
                vv.append(f"{PAYS.get(x['o'], x['o'])} → {dn} en {sh(w['hs'])} : <b>{w['verdict'].lower()}</b> ({fmt_t(w['npf'])} → {fmt_t(w['pref'])} % ; "
                          f"offre de l'origine {fmt_m(w['exp_orig'])} M$" + (f" ; {fr(w['motifs'][0])}" if w['motifs'] else '') + ')')
        out.append(dict(code=f'N{i:02d}', editions=TOUTES if FOCUS in (d, a['o']) or any(FOCUS == x['o'] for x in lst) else _ed_nomenclature(hs),
                        sujet=f"{lib(hs)} ({orig} → {dn}) : sous-position citée ou position entière ?", valeurs=vals,
                        ecart=f"{fmt_m(a['imp_dest'])} M$ contre {fmt_m(a['sh4']['imp_dest'])} M$ selon le niveau de nomenclature.",
                        hypotheses=hyp,
                        traitement=f"Verdict « {a['verdict'].lower()} » sur la SH6 citée (tableau d'audit). La sous-position voisine est vérifiée séparément : "
                                   + ('; '.join(vv) if vv else 'aucune sous-position voisine ne dépasse le seuil de marché') + '.',
                        trancher='Retrouver le produit visé par la cible publiée (fiche d\'origine, facture type) et le classer à 8-10 chiffres.',
                        cle=(d, hs)))
    return out


def registre(ed=ED):
    return [c for c in REGISTRE + nomenclature() if ed is None or ed in c['editions']]


def code_nomenclature(d, hs):
    return next((c['code'] for c in nomenclature() if c['cle'] == (d, hs)), None)


def ref(code):
    """Renvoi vers l'annexe des contradictions (plans d'action seulement)."""
    return f' <font color="#C0493D">[contradiction {code}, annexe]</font>' if ED and any(c['code'] == code for c in registre()) else ''


def annexe(ed=ED):
    fl = [chapter('A4', 'Annexe 4 — Contradictions entre sources'),
          P("Quand deux sources, ou deux niveaux de la nomenclature, donnent des valeurs incompatibles, ce plan d'action ne choisit pas : il affiche les deux valeurs, "
            "décrit l'écart, liste les explications possibles <b>sans en retenir une</b>, et indique ce qui permettrait de trancher. "
            "Les codes C renvoient aux sources documentaires, les codes N aux écarts de nomenclature relevés par la vérification des cibles.", LEAD)]
    body = st('ctb', fontSize=7.6, leading=10, alignment=TA_JUSTIFY)
    for c in registre(ed):
        rows = [['Valeur', 'Source', 'Date', 'Statut']] + [[Paragraph(v, TD), Paragraph(s, TD), d, s2] for v, s, d, s2 in c['valeurs']]
        bloc = [Paragraph(f"<font color='#C0493D'>{c['code']}</font> — {c['sujet']}", H3),
                table(rows, [72 * mm, 52 * mm, 22 * mm, CW - 146 * mm], font=7),
                Paragraph(f"<b>Écart.</b> {c['ecart']}", body),
                Paragraph('<b>Explications possibles (non tranchées).</b> ' + ' '.join(f'({i}) {h}' for i, h in enumerate(c['hypotheses'], 1)), body),
                Paragraph(f"<b>Dans ce plan.</b> {c['traitement']}", body),
                Paragraph(f"<b>Pour trancher.</b> {c['trancher']}", body), Spacer(1, 5)]
        fl.append(KeepTogether(bloc))
    return fl

