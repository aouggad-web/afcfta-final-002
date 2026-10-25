# Générateur de rapports sectoriels ZLECAf

Produit les rapports PDF vendus sur la page Tarifs (`backend/pricing.py` : `report_agri`, `report_pharma`, …)
à partir des données du SaaS, de sources publiques (OEC/BACI, ONS…) et d'une recherche documentaire datée.
Les PDF publiés sont dans `reports/sectoriels/`.

| Secteur | Commande | Pages (T3 2026, focus Algérie) |
|---|---|---|
| Agriculture & agroalimentaire | `python reports/generateur/generer.py agri` | 55 |
| Pharmaceutique & santé | `python reports/generateur/generer.py pharma` | 41 |
| Chimie, cosmétiques & hygiène | `python reports/generateur/generer.py chimie` | 34 |

```bash
pip install -r reports/generateur/requirements.txt
python reports/generateur/generer.py pharma                    # focus Algérie (défaut)
python reports/generateur/generer.py chimie --pays-focus SEN   # focus Sénégal
python reports/generateur/generer.py agri --etapes pdf         # réassembler le PDF sans réextraire
python reports/generateur/generer.py agri --edition toutes     # 4 plans d'action par profil (agri)
python -m pytest reports/generateur/tests
cd reports/generateur && python -m commun.sources              # état des sources (gratuites / payantes)
```

Le PDF est écrit dans `reports/sectoriels/Rapport_<secteur>_ZLECAf_<édition>[_<ISO3>].pdf` (ou `--sortie`).
Les polices (DM Sans, Fraunces) sont téléchargées une fois depuis Google Fonts et instanciées dans `_cache/`.

## Pays focus

Chaque rapport contient un chapitre consacré au pays demandé par l'utilisateur (`--pays-focus`, code ISO3).

- **Algérie (DZA, défaut)** : module approfondi propre à chaque secteur (`secteurs/<secteur>/ch_algeria.py`) :
  fiscalité à l'import (DD, DAPS, PRCT, TCS, TIC), régime d'importation et autorisations, base productive,
  groupes exportateurs, presse fondue dans l'analyse, contexte politique.
- **Autre pays avec module** : `secteurs/<secteur>/ch_<iso3>.py` exposant `chapitre(num)` est utilisé s'il existe.
- **Tout autre pays** : chapitre générique (`commun/pays_focus.py`) construit sur les données : statut de l'offre ZLECAf,
  NPF par segment face à la médiane africaine, taux ZLECAf servis aux produits du pays par les calculateurs du SaaS,
  flux OEC par chapitre et premiers débouchés africains, puis la liste des recherches à mener avant diffusion.
  Le reste du rapport (synthèse, recommandations) garde la rédaction de l'édition : à relire pour un autre pays.

## Plans d'action par profil (agriculture)

`--edition producteurs|industriels|negoce|intrants|toutes` produit, à partir du même tronc commun, un plan d'action
par type d'opérateur (`Rapport_Agriculture_Agroalimentaire_Plan_<Profil>_ZLECAf_<édition>.pdf`) :

| Édition | Public | Contenu propre | Pages |
|---|---|---|---|
| 01-A Producteurs | cultures, élevage, pêche | fiches SH 01-14, cibles brutes, chaîne du froid et semences | 47 |
| 01-B Industriels | agro-industrie, transformation | fiches SH 15-24, cibles transformées, énergie, emballages, champions | 45 |
| 01-C Négoce | traders, distributeurs | offres, Top 25, formalités et paiements, logistique, annexe pays | 45 |
| 01-D Intrants | engrais, aliments, semences, machines | marchés, régimes et homologations, besoins, PPP et hubs | 29 |

Chaque édition garde le pays focus (`--pays-focus`) et renumérote ses chapitres (`secteurs/agri/editions.py`).

**Aucune cible n'est saisie à la main.** `secteurs/agri/cibles.py` (étape d'extraction) confronte chaque couple
origine × destination × SH6 à trois filtres (`commun/verif_cibles.py`) :

1. taux servi par les calculateurs du SaaS sur **toutes** les lignes nationales (préférence partielle signalée) ;
2. marché réel : importations de la destination ≥ 5 M$/an (OEC/BACI, moyenne 2023-2024 ; `RG_SEUIL_MARCHE`) ;
   si la destination exporte plus qu'elle n'importe, la cible est un « créneau », pas un débouché ;
3. offre réelle : exportations de l'origine ≥ 5 M$/an (`RG_SEUIL_OFFRE`) ; réexportation possible signalée.

Les formalités recensées par le SaaS (F.A.P algériennes, formalités égyptiennes) sont jointes à chaque cible.
Les cibles de l'édition précédente sont auditées (`AUDIT`) et le verdict est publié. Le pays focus est aussi vérifié
comme exportateur (`focus` dans `cibles.json`). Cas d'école : oranges égyptiennes au Maroc, 40 points de marge
mais 1,4 M$ importés par an : cible rejetée.

## Organisation

```
generer.py              CLI : secteur, --pays-focus, --edition, --etapes extraction,graphiques,pdf
commun/polices.py       polices statiques instanciées (noms internes distincts : le gras s'affiche)
commun/oec.py           client OEC tesseract (BACI HS 2017) avec cache disque, codage SH du module Statistiques
commun/sources.py       registre des sources gratuites et payantes, clés lues dans l'environnement
commun/pays_focus.py    chapitre pays focus (module approfondi ou générique)
commun/verif_cibles.py  verdict des cibles : taux servi × marché réel × offre réelle (OEC/BACI)
secteurs/<secteur>/     scripts d'extraction, graphiques, chapitres (ch_*.py), layout.py, cover.py, build.py
secteurs/<secteur>/figees/     données figées de l'édition (extractions ponctuelles, fond de carte, graphique repris)
secteurs/<secteur>/recherche/  notes de recherche documentaire datées et sourcées (base de faits des chapitres)
```

Les scripts sont copiés dans `_travail/<secteur>/` et exécutés dans l'ordre défini par `PIPELINES` (`generer.py`),
avec `RG_DIR` (dossier de travail), `RG_REPO`, `RG_RACINE`, `RG_POLICES` et `RG_PAYS_FOCUS`.

## Méthodologie

1. **Périmètre** : segments définis par préfixes SH (`analyze_groups.py`, ou `SECTORS` pour l'agriculture).
2. **Tarifs** : NPF des 40 barèmes du SaaS ; offres e-Tariff Book (catégories A/B/C, calendriers) ; taux effectivement
   servis par les calculateurs appliqués (DZA, EGY, KEN, MAR, ZAF), comparés au NPF.
3. **Origine** : règles de l'annexe 2 par position et notes de l'appendice IV (transformations chimiques).
4. **Commerce** : OEC/BACI (agrégats africains, SH × pays via le module Statistiques), ONS et module Opportunités pour l'Algérie.
5. **Coût de revient** : fret conteneur (modèle logistique du SaaS) + droits et taxes à l'import par origine.
6. **Recherche documentaire** : textes officiels, presse, institutions ; chaque fait est daté et sourcé dans `recherche/`.

## Consolidation des statistiques

- Chaque chiffre publié porte sa source et sa date (légende de tableau ou de figure).
- Deux sources qui divergent sont citées toutes les deux, avec l'écart ; le rapport n'arbitre pas, ni en silence ni ouvertement.
  Dans les plans d'action, chaque contradiction est exposée en annexe 4 (`secteurs/agri/contradictions.py`) : valeurs, sources,
  dates et statuts côte à côte, écart, explications possibles non tranchées, et ce qui permettrait de trancher.
  Les codes C viennent des notes de recherche ; les codes N sont calculés par `cibles.py` quand la SH6 citée est marginale
  alors que sa position SH4 pèse plus que le seuil de marché (ex. thé en Algérie : 0,7 M$ en 0902.40, 63 M$ pour la position 0902).
- Les données miroir (BACI) sont signalées quand le pays ne déclare pas ses importations.
- Ce qui n'est pas vérifié est marqué « à confirmer » (par exemple, un taux de DAPS dont l'édition de la loi de finances n'est pas retrouvée).

## Mise à jour trimestrielle

1. Rafraîchir les données du SaaS (barèmes, offres, matrice des statuts) par les workflows habituels.
2. Mettre à jour `EDITION` (`generer.py`) et `EDITION`/`RUNNING` dans chaque `layout.py`.
3. Relancer `generer.py <secteur>` ; contrôler les écarts de chiffres avec l'édition précédente.
4. Refaire la recherche documentaire (presse, textes, politique) et mettre à jour `recherche/` puis les chapitres.
5. Régénérer les extractions figées si leur source a bougé (fichiers de `figees/`).

## Sources payantes (feuille de route)

`commun/sources.py` déclare chaque source et la variable d'environnement de sa clé. Aucune clé n'est stockée dans le dépôt.

| Source | Apport | Variable |
|---|---|---|
| OEC Pro | SH6 récent, volumes | `OEC_API_TOKEN` (déjà pris en charge par `commun/oec.py`) |
| ITC Trade Map | commerce mensuel, SH8/SH10 national | `ITC_TRADEMAP_KEY` |
| Argus / CRU | prix engrais, ammoniac, chimie | `ARGUS_API_KEY` |
| Drewry / Xeneta | fret conteneur par corridor | `XENETA_API_KEY` |
| Euromonitor | marchés cosmétiques, hygiène, OTC | `EUROMONITOR_API_KEY` |
| Fitch Solutions (BMI) | risque pays, prévisions sectorielles | `FITCH_API_KEY` |
| Coface / Allianz Trade | risque acheteur | `COFACE_API_KEY` |
| S&P Global | entreprises, capacités, prix | `SPGLOBAL_API_KEY` |

Sources gratuites à intégrer ensuite : UN Comtrade (contrôle des flux déclarés), Banque mondiale WDI, FAOSTAT, FRED.
