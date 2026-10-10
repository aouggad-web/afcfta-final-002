from layout import *
import json
SP = json.load(open(S + 'saas_chimie.json'))

def about_page():
    fl = [Paragraph('À PROPOS DE CE RAPPORT', KICK), Spacer(1, 3),
          Paragraph('Un rapport construit sur les données du SaaS ZLECAf, croisées avec les sources officielles et la presse les plus récentes', H2),
          P("Ce rapport sectoriel est produit par ZLECAf Trade Intelligence à partir de la plateforme SaaS ZLECAf : barèmes tarifaires nationaux, offres officielles de l'<i>e-Tariff Book</i> "
            "de l'Union africaine, règles d'origine de l'Appendice IV, registre d'application bilatérale, calculateurs de taux préférentiels, calculateur fiscal algérien et module "
            "Opportunités (dont le sous-module « Algérie · industrie et marchés ») et module Statistiques (recherche SH × pays, données OEC). Ces données sont croisées avec les sources publiques de référence (OEC/BACI, ONS, UN Comtrade, "
            "USGS, OMC, PNUE, EUR-Lex, Secrétariat de la ZLECAf, Banque d'Algérie, DGD) et avec la presse économique, citée dans le texte avec sa date, arrêtées au 27 septembre 2026."),
          P("Il s'adresse aux industriels de la chimie, des engrais, des plastiques, des cosmétiques et des détergents, aux distributeurs, aux investisseurs, aux banques et assureurs du commerce, "
            "ainsi qu'aux administrations. Il est mis à jour chaque trimestre."),
          Spacer(1, 4), Paragraph('Périmètre : 16 segments', H3)]
    rows = [['N°', 'Segment', 'Positions SH']] + [[g[1:], n, (', '.join(p) if len(p) < 6 else f'{p[0][:2]}.{p[0][2:]} à {p[-1][:2]}.{p[-1][2:]}' + (', 29.42' if g == 'C03' else ''))] for g, n, p in SP['groups']]
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
    fl.append(Paragraph("Ce document est une analyse économique et réglementaire. Il ne constitue ni un avis juridique, ni une décision de classement ou de valeur en douane, ni un avis de sécurité des produits. "
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
    fl.append(P("La chimie africaine est coupée en deux : une chimie de base et des plastiques importés d'Asie et du Golfe, et une industrie de consommation "
                "(savons, détergents, cosmétiques) déjà régionale et fortement protégée. C'est là que la ZLECAf ouvre les plus grandes marges, et que l'Algérie a le plus à gagner, ou à perdre.", LEAD))
    fl.append(kpis([
        ('80 Md$', 'importations africaines 2024 dans le périmètre (chimie, engrais, plastiques, cosmétiques, détergents)', 'OEC / BACI'),
        ('20-43 %', 'droits NPF sur cosmétiques, savons et détergents (TEC CEDEAO, CAE, CEMAC, Tunisie)', 'SaaS ZLECAf'),
        ('112 % → 2 %', 'charge à l\'import des cosmétiques en Algérie : NPF contre ZLECAf (Tunisie, Égypte)', 'Calculateur SaaS'),
        ('0,7 %', 'part de l\'Afrique dans les exportations algériennes d\'urée (1 024 M$ en 2024)', 'BACI via SaaS')], cols=4))
    fl.append(Spacer(1, 6))
    msgs = [
        ('1. Deux chimies africaines.', "Plastiques (31 Md USD importés, 9 % d'Afrique) et chimie organique (9 Md USD, 3 %) sont importés ; engrais (43 %), savons et détergents (35 %) circulent déjà entre Africains."),
        ('2. L\'escalade tarifaire est la règle.', "0 à 5 % sur la chimie de base, 20 à 43 % sur les produits finis de consommation : la ZLECAf crée les plus grandes marges sur les cosmétiques et les lessives."),
        ('3. Les cosmétiques, première réserve de lignes protégées.', "64 lignes sur 337 en catégorie B ou C dans les offres (CEMAC, Éthiopie, Égypte, Tunisie) ; CAE et CEDEAO n'ont pas encore classé ces lignes."),
        ('4. La règle des mélanges ouvre l\'origine.', "La note 8 de l'Appendice IV admet le mélange contrôlé pour les chapitres 33 à 38 : une vraie formulation est originaire, un reconditionnement ne l'est jamais."),
        ('5. L\'Algérie ouvre plus qu\'elle n\'obtient.', "Cosmétiques tunisiens et égyptiens : 2 % de charge contre 112 % ; cosmétiques algériens : 20 à 43 % dans la plupart des marchés africains, faute de réciprocité appliquée."),
        ('6. Le vrai filtre algérien est administratif.', "Programmes prévisionnels d'importation (huit textes en huit mois), autorisations préalables, annonce d'arrêt des importations de cosmétiques (janvier 2026)."),
        ('7. Engrais : cap sur l\'Afrique.', "L'Afrique importe 3 Md USD d'urée et d'ammoniac ; le MACF européen (définitif depuis 2026) et la crise d'Ormuz plaident pour réorienter une partie des volumes."),
        ('8. Pour les pondéreux, la proximité paie.', "Lessive rendue à Tripoli, Nouakchott ou Dakar : 3 à 5 % de coût de rendu depuis l'Algérie, contre 22 à 33 % depuis la Chine ou le Golfe en 2026."),
        ('9. La Libye, premier marché de proximité.', "Environ 741 M USD d'importations dans le périmètre (2024), hors ZLECAf mais dans la GAFTA ; risque politique et de paiement à couvrir."),
        ('10. Éclaircissants et défrisants : potentiel et danger.', "Demande massive, marchés inondés de produits illicites (mercure, hydroquinone) : une offre conforme et enregistrée est un avantage concurrentiel, pas une contrainte.")]
    for t, b in msgs:
        fl.append(Paragraph(f'<b>{t}</b> {b}', st('m', fontSize=8.5, leading=11.8, spaceAfter=3.4, alignment=TA_JUSTIFY)))
    fl.append(PageBreak())
    fl.append(callout('Focus Algérie : ce qu\'il faut retenir', [
        '<b>Appareil de production</b> : branche chimie, caoutchouc et plastiques à 1 383 M USD de valeur ajoutée (ONS, 2024) ; engrais AOA, Sorfert, Fertial ; pétrochimie en construction (PP d\'Arzew, LAB de Skikda fin 2027) ; '
        'détergents Henkel (ex-ENAD), Esquirol, ENAD en crise ; cosmétiques Venus, Vague de Fraîcheur ; hygiène papier Faderco.',
        '<b>Importations</b> : PPI et autorisations préalables filtrent davantage que le tarif ; plastiques 2,98 Md USD (2025), compositions parfumantes 299 M USD.',
        '<b>Exportations</b> : urée, hélium, ammoniac, méthanol vers l\'Europe et l\'Asie ; produits de consommation vers la Tunisie, la Libye, la Mauritanie, le Sénégal (quelques millions de dollars).',
        '<b>Priorités</b> : Libye, Tunisie, Mauritanie, puis Sénégal et Niger ; dossier d\'origine « mélange contrôlé » ; CAGEX ; réciprocité ZLECAf élargie.'], bg=GREEN_L, bar=GREEN, title_color=GREEN))
    fl.append(PageBreak())
    return fl
