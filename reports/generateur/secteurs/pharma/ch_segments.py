from layout import *

def ch_segments():
    fl = [PageBreak(), chapter(6, 'Opportunités par segment'),
          P("En croisant la demande africaine (BACI, module Opportunités du SaaS), le niveau des droits NPF, le statut dans les offres et la règle d'origine, "
            "huit segments se distinguent.", LEAD)]
    rows = [['Segment (SH)', 'Demande africaine 2024', 'Droits NPF', 'Offres ZLECAf', 'Règle d\'origine', 'Opportunité'],
            ['Médicaments dosés (3004.90)', '9,0 Md USD ; Égypte, Afr. du Sud, Maroc, Kenya', '0 % dans 31 barèmes ; 5 % CEMAC, DZA, ETH ; ≤ 25 % MAR', 'Cat. A partout', 'CTH : API importé admis',
             'Génériques essentiels pour les achats groupés (APPM) ; marge tarifaire au Maroc et en CEMAC'],
            ['Antibiotiques dosés (3004.10)', '0,78 Md USD ; Égypte, Nigeria, Afr. du Sud, Tanzanie', 'Idem', 'Cat. A', 'CTH', 'Injectables et formes pédiatriques, où la qualité fait la différence'],
            ['Vitamines dosées (3004.50)', '0,23 Md USD ; Nigeria, Côte d\'Ivoire, Afr. du Sud, Ghana', 'Idem', 'Cat. A', 'CTH', 'Produits grand public en officine ; marques régionales'],
            ['Vaccins vétérinaires (3002.30)', '0,35 Md USD ; Égypte, Afr. du Sud, Maroc, Mozambique', '0 à 5 %', 'Cat. A', 'CTH ou 60 %', 'Élevage sahélien et maghrébin ; chaîne du froid courte'],
            ['Instruments médicaux (9018.90)', '1,35 Md USD ; Afr. du Sud, Égypte, Maroc, Tunisie', '0 à 10 % ; Algérie 5 à 30 %', 'Cat. A', 'CTH ou 60 %', 'Consommables et dispositifs de classe I-II ; forte marge en Algérie'],
            ['Gants chirurgicaux (4015.11)', '0,13 Md USD ; Égypte, Afr. du Sud, Maroc, Éthiopie', '2 à 30 %', 'Cat. A', 'CTH (latex 40.01)', 'Latex africain (Côte d\'Ivoire, Liberia, Nigeria) transformé localement'],
            ['Hygiène (9619)', '0,87 Md USD ; Afr. du Sud, Libye, Maroc, Zimbabwe', '0 à 43 %', 'B ou C : CEMAC, Éthiopie, Égypte', 'CTH', 'Marchés protégés : préférence différée ou nulle ; produire sur place'],
            ['Emballages (7010.90, 3923.30)', '0,52 et 0,43 Md USD ; Afr. du Sud, Maroc, Libye', '7 à 43 %', 'B ou C : CEMAC, Éthiopie, Tunisie', 'CTH', 'Verre et plastique pharmaceutiques : intrant stratégique des formulateurs']]
    fl.append(Paragraph('Tableau 6.1 — Matrice des opportunités par segment', CAP))
    fl.append(table(rows, [30 * mm, 34 * mm, 30 * mm, 22 * mm, 22 * mm, 36 * mm], font=7))
    fl.append(Paragraph('Sources : BACI (CEPII) via le SaaS (importations 2024 des pays africains hors Algérie) ; barèmes, offres et règles d\'origine du SaaS.', SRC))
    fl.append(h2('6.1 Trois opportunités où la ZLECAf fait la différence'))
    fl += bullets([
        '<b>Dispositifs et consommables vers l\'Algérie.</b> Les droits de 30 % sur les seringues, cathéters et gants, auxquels s\'ajoute le DAPS de 30 % sur les lits médicaux et les flacons plastiques, '
        'tombent à 0 % pour les neuf origines admises (Égypte, Maurice, Tunisie, Tanzanie, Rwanda ; −60 % pour l\'Afrique du Sud, le Cameroun, le Ghana et le Kenya). C\'est la marge préférentielle '
        'la plus élevée du champ santé parmi les destinations appliquées.',
        '<b>Médicaments vers le Maroc</b> pour les origines P1 (dont l\'Égypte, la Tunisie, Maurice et l\'Algérie) : 0 % contre 10 à 25 % sur les spécialités fabriquées localement. Le marché reste fermé de fait '
        'aux produits algériens pour des raisons politiques (chapitre 9).',
        '<b>Principes actifs vers l\'Algérie</b> : 15 % de droit NPF sur les antibiotiques en vrac, 0 % pour les origines admises. Un producteur égyptien ou tunisien d\'API, ou un chimiste mauricien, dispose d\'une marge de 14,7 % de prix.'])
    fl.append(h2('6.2 Trois opportunités où la ZLECAf ne joue pas, mais le marché si'))
    fl += bullets([
        '<b>Achats groupés continentaux</b> : le premier appel d\'offres APPM (12/05/2026) a produit des économies de 30 à 90 % et retenu des fabricants africains pour 5 produits sur 10. '
        'La préférence n\'est pas tarifaire mais contractuelle.',
        '<b>Relais des financements américains</b> : les budgets nationaux reprennent l\'achat d\'antirétroviraux, de tests et d\'antipaludiques (protocoles de 2026).',
        '<b>Sécurité d\'approvisionnement</b> : fret aérien depuis l\'Inde en hausse de 350 à 400 %, délais allongés de 10 à 20 jours, pénuries au Kenya et au Nigeria (Pharmaceutical Commerce, 15/06/2026).'])
    return fl
