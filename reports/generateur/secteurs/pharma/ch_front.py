from layout import *
import json
SP = json.load(open(S + 'saas_pharma.json'))

def about_page():
    fl = [Paragraph('À PROPOS DE CE RAPPORT', KICK), Spacer(1, 3),
          Paragraph('Un rapport construit sur les données du SaaS ZLECAf, croisées avec les sources officielles et la presse les plus récentes', H2),
          P("Ce rapport sectoriel est produit par ZLECAf Trade Intelligence à partir de la plateforme SaaS ZLECAf : barèmes tarifaires nationaux, offres officielles de l'<i>e-Tariff Book</i> "
            "de l'Union africaine, règles d'origine de l'Appendice IV, registre d'application bilatérale, calculateurs de taux préférentiels, calculateur fiscal algérien et module "
            "Opportunités (dont le sous-module « Algérie · industrie et marchés »). Ces données sont croisées avec les sources publiques de référence (GAFI, OMS, Africa CDC, UN Comtrade, "
            "BACI, OMC, EUR-Lex, Secrétariat de la ZLECAf, Banque d'Algérie, EDB et MRA de Maurice) et avec la presse économique, citée dans le texte avec sa date, arrêtées au 27 septembre 2026."),
          P("Il s'adresse aux industriels du médicament et des dispositifs médicaux, aux distributeurs, aux centrales d'achat, aux investisseurs, aux banques et assureurs du commerce, "
            "ainsi qu'aux administrations. Il est mis à jour chaque trimestre."),
          Spacer(1, 4), Paragraph('Périmètre : 15 segments de santé', H3)]
    rows = [['N°', 'Segment', 'Positions SH']] + [[g[1:], n, ', '.join(p)] for g, n, p in SP['groups']]
    fl.append(table(rows, [12 * mm, 70 * mm, CW - 82 * mm]))
    fl.append(Spacer(1, 6))
    fl.append(callout('Comment lire les taux de ce rapport', [
        '<b>NPF</b> : droit de douane de la nation la plus favorisée, appliqué à toute origine sans préférence.',
        '<b>Offre ZLECAf</b> : calendrier publié dans l\'<i>e-Tariff Book</i>, indicatif tant que la destination ne l\'a pas mis en œuvre.',
        '<b>Taux servi</b> : taux calculé par les modules du SaaS lorsque la préférence est juridiquement opposable (acte national en vigueur, origine admise, ligne couverte). '
        'En 2026, cela concerne cinq destinations : Algérie, Égypte, Kenya, Maroc et SACU.',
        '<b>Charge hors TVA</b> : droit de douane et prélèvements définitifs ; la TVA, récupérable ou exonérée pour les médicaments, est présentée à part.'], bg=BLUE_L, bar=BLUE, title_color=BLUE))
    fl.append(Spacer(1, 6))
    fl.append(Paragraph('Avertissement', H3))
    fl.append(Paragraph("Ce document est une analyse économique et réglementaire. Il ne constitue ni un avis juridique, ni une décision de classement ou de valeur en douane, ni un avis médical. "
                        "Les taux doivent être confirmés ligne par ligne dans le calculateur ZLECAf et auprès de l'administration des douanes de destination avant toute opération. "
                        "Les informations de presse sont citées avec leur date ; celles qui n'ont pas pu être confirmées en source primaire sont signalées comme telles.", SMALL_J))
    fl.append(PageBreak())
    return fl

def toc_page():
    toc = TableOfContents()
    toc.levelStyles = [st('toc1', fontName='DMSans-Bold', fontSize=8.6, leading=11, leftIndent=0, textColor=INK, spaceBefore=1.5),
                       st('toc2', fontSize=7.2, leading=8.8, leftIndent=12, textColor=INK2)]
    toc.dotsMinLevel = 0
    return [Paragraph('SOMMAIRE', KICK), Spacer(1, 2), Paragraph('Table des matières', H1), Spacer(1, 4), toc, PageBreak()]

def exec_summary():
    fl = [chapter(None, 'Synthèse exécutive', 'synth')]
    fl[0]._toctext = 'Synthèse exécutive'
    fl.append(P("Dans la santé, la ZLECAf ne se joue pas là où on l'attend. Les médicaments entrent déjà presque partout à droit nul ; la préférence continentale compte surtout "
                "sur les intrants, les dispositifs et les consommables. Le vrai verrou est réglementaire et financier. Dix messages pour décider.", LEAD))
    fl.append(kpis([
        ('17-20 Md$', 'importations africaines de produits pharmaceutiques par an ; ≈ 5 % seulement viennent d\'Afrique', 'UN Comtrade 2022-2024'),
        ('31 / 40', 'barèmes nationaux à droit nul sur les médicaments dosés', 'SaaS ZLECAf'),
        ('0', 'médicament ou principe actif en liste d\'exclusion dans les 10 offres étudiées', 'e-Tariff Book via SaaS'),
        ('83 %', 'couverture du marché algérien par la production locale (fin 2025)', 'ANPP, 22/02/2026')], cols=4))
    fl.append(Spacer(1, 6))
    msgs = [
        ('1. Un marché de substitution.', "L'Afrique importe plus de 70 % de ses médicaments et 99 % de ses vaccins ; l'Inde (29 %) et l'Europe (45-50 %) la fournissent, le commerce intra-africain ne pèse que 0,79 Md USD."),
        ('2. Le médicament fini est déjà détaxé.', "31 barèmes sur 40 appliquent 0 % aux médicaments dosés ; la ZLECAf n'y crée aucune marge. Les exceptions : Maroc (jusqu'à 25 %), CEMAC, Algérie et Éthiopie (5 %)."),
        ('3. Pas de médicament « exempté » de la ZLECAf.', "Sur 780 lignes pharma des offres, 776 sont en catégorie A (4 non renseignées). Les exclusions visent l'alcool, les emballages plastiques et verre, l'hygiène."),
        ('4. La marge est dans les intrants et les dispositifs.', "En Algérie, les antibiotiques en vrac (15 %) sont plus taxés que le médicament fini (5 %) ; seringues, gants et lits médicaux paient 32 à 65 % hors TVA, ramenés à 2-5 % sous ZLECAf."),
        ('5. L\'origine est accessible.', "Un comprimé formulé en Afrique avec un API indien ou chinois est originaire (changement de position). Le simple reconditionnement ne l'est jamais."),
        ('6. Les zones franches ne sont pas exclues.', "Contrairement à une idée répandue, l'Annexe 2 (art. 9) et le règlement 1/2023 admettent les produits de ZES aux préférences, sous conditions de notification, d'enregistrement et de garde-fous."),
        ('7. Maurice : un hub de dispositifs, pas de médicaments.', "6 fabricants, 49 M USD d'exportations de dispositifs (2024), IS de 3 %, pas de contrôle des changes depuis 1994 ; sortie de la liste grise du GAFI dès octobre 2021."),
        ('8. L\'Algérie change de statut.', "Sortie de la liste grise du GAFI le 19/06/2026, niveau 3 de l'OMS en cours d'évaluation, normalisation avec le Niger (février) et le Mali (juillet 2026) : l'export devient crédible."),
        ('9. La proximité vaut 1,3 à 3 % du prix.', "Face à l'Inde à Dakar, l'avantage logistique algérien ne compense pas un écart de prix industriel ; il décide sur les produits volumineux et en temps de crise maritime."),
        ('10. Le verrou est réglementaire et financier.', "Enregistrement, délai de rapatriement de 120 jours, liste UE des pays à haut risque : ce sont eux, plus que le tarif, qui fixent le rythme de l'export.")]
    for t, b in msgs:
        fl.append(Paragraph(f'<b>{t}</b> {b}', st('m', fontSize=8.5, leading=11.8, spaceAfter=3.4, alignment=TA_JUSTIFY)))
    fl.append(PageBreak())
    fl.append(callout('Focus Algérie : ce qu\'il faut retenir', [
        '<b>Industrie</b> : 233 sites, 83 % de couverture, facture d\'import ramenée de 2 Md USD (2019) à 515 M USD (2024) ; exportations de médicaments dosés de 23,3 M USD en 2024, '
        'surtout vers l\'Arabie saoudite (insuline de Boufarik).',
        '<b>Importer mieux</b> : un API d\'origine égyptienne ou tunisienne peut coûter jusqu\'à 14,7 % de plus qu\'un API asiatique avant de perdre son avantage ; la protection effective de la '
        'formulation passe de −3 % à +12 % (API = 50 % du prix).',
        '<b>Exporter</b> : cibles prioritaires Mauritanie, Tunisie, puis Niger, Sénégal, Côte d\'Ivoire ; le Maroc, seul marché à forte marge ZLECAf, reste fermé ; le Kenya n\'admet pas l\'origine algérienne.',
        '<b>Conditions</b> : niveau 3 de l\'OMS pour l\'ANPP, assurance-crédit CAGEX pour porter le rapatriement à 180 jours, élargissement de la liste des partenaires ZLECAf admis.'],
        bg=GREEN_L, bar=GREEN, title_color=GREEN))
    fl.append(Spacer(1, 6))
    fl.append(callout('Focus Maurice et zones franches', [
        'La ZLECAf traite la zone franche comme une partie du territoire : le produit qui en sort vers un autre État partie peut être originaire et préférentiel. En droit national, la même sortie '
        'vers le marché intérieur est une importation. Fiscalité et change restent souverains, mais un avantage lié à l\'exportation s\'expose aux droits compensateurs (Annexe 9).',
        'Exemple : un cathéter mauricien (SH 9018.39) entre en Algérie à 2 % de charge hors TVA contre 32 % pour une origine tierce, soit une marge de 30 points.'], bg=TEAL_L, bar=TEAL, title_color=TEAL))
    fl.append(PageBreak())
    return fl
