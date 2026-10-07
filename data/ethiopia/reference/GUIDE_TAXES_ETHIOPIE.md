# Éthiopie — Ensemble des taxes, droits de douane et accises (par position tarifaire nationale)

Date de collecte : octobre 2026. Base légale : tarif douanier national (SH 2022), livre officiel du
Ministère des Finances (« Tariff Reform Book », édition révisée août 2021, 372 p.) — **6 154
positions à 8 chiffres extraites directement du PDF complet** (96 chapitres couverts).

## Fichiers livrés

1. **ethiopia_tariff_national_complet.csv** — les 6 154 positions à 8 chiffres :
   code HS-8, description, unité statistique, **droit d'importation (ad valorem)**,
   et accise (Proc. 1186/2020) si applicable.
2. **resume_par_chapitre.csv** — distribution des taux par chapitre HS.
3. `sources/` — PDF officiels (tarif, proclamation accises).

## 1. Droits de douane à l'importation (par ligne tarifaire)

Barème national (BF/SDR) :
- **Free (0 %)** — 1 057 lignes (biens d'équipement, intrants, produits agricoles de base)
- **5 %** — 1 357 lignes (intrants et matières premières)
- **15 %** — 849 lignes (biens intermédiaires)
- **25 %** — 808 lignes (biens finaux)
- **35 %** — 610 lignes (biens de consommation, produits protégés)
- Cas particuliers : 1302.1100 (opium) = **Prohibited** ; quelques lignes à double valeur de
  l'imprimé officiel (à vérifier manuellement, voir ci-dessous).

## 2. Accises à l'importation ET à la production locale (Proc. 1186/2020, 1er annexe)

Assise à l'import = **valeur en douane + droit de douane** (art. 9(2) de la Proc. 1186/2020 —
la valeur en douane étant déterminée selon la Proc. douanière) ; production locale = **prix
sortie usine**. Principales lignes :

| Produit | Codes HS | Taux |
|---|---|---|
| Huiles/fats saturées ≥40 g/100 g | 15.01–15.15 | 30 % |
| Huiles hydrogénées / trans | 15.16 | 40 % |
| Margarine | 15.17 | 50 % |
| Sucre (toutes formes) | 1701.1200/1400/9100/9900, 1702.2000 | 20 % |
| Chewing-gum | 1704.1000/9000 | 30 % |
| Confiserie, chocolat (hors aliments infantiles) | 1806, 2106.9040 | 30 % / 25 % |
| Eaux en bouteille sans sucre | 2201.9000 | 10 % |
| Boissons sucrées/gazeuses | 2202.1000/9100/9990 | 25 % |
| Bière (malt) | 2203.0000 | 40 % ou 11 Birr/L (le plus élevé) |
| Bière matière locale ≥75 % | 2203.0000 | 30 % ou 8 Birr/L |
| Bière non alcoolisée / barley locale | — | 35 % ou 9 Birr/L |
| Vin de raisin/fruits | 2204.1000–2204.3000 | 40 % |
| Vin matière locale ≥75 % | 2205.1000/9000 | 30 % |
| Spiritueux, fermentés, cidre | 2206–2208 | 80 % |
| Alcool pur | 2207.1000/2000 | 60 % |
| Tabac en feuille | 2401 | 20 % |
| Cigarettes | 2402.2000 | 30 % + 8 Birr/paquet (20) |
| Cigares, pipe, autres tabacs | 2402.1000/9000, 2403 | 30 % + 250 Birr/kg |
| Sel | 2501.0010/0090 | 25 % |
| Carburants (essence, jet fuel…) | 2710.1200–2710.2050 | 30 % ou 40 Birr/kg |
| Parfums, eaux de toilette | 3303.0000 | 100 % |
| Cosmétiques (hors crème solaire/shampoing) | 3304, 3305 | 40 Birr/kg |
| Sacs plastiques | 3923.2110/2910/2920 | 5 % |
| Pneus en caoutchouc | 4011.1000–4013.9090 | 5 % |
| Tissus textiles (soie, rayonne, nylon, laine, coton écrû/blanc/imprimé) | 50.07–58.11 (liste détaillée) | 8 % |
| Tapis et moquettes | 5701.1000–5705.0000 | 30 % |
| Vêtements | 6201.1100–6217.9000, 6310.1000–6304.9990 | 8 % |
| Fleurs artificielles | 6702–6703 | 10 % |
| Perruques/postiches | 6704 | 40 % |
| Machines à sous/jeux | 9504.2000–9505.9000 | 200 % |
| Pipes, chichas, fumeurs | 9614.0010/0090 | 20 % |
| **Véhicules neufs (CBU)** — voitures | 8703 | 100 % (≤1800 cc) à 200 % (>) — voir PDF |
| Véhicules **d'occasion** selon âge | 8703/8704/8705 | ≤4 ans : 100 % ; 4–7 ans : 200 % ; >7 ans : 400 % |
| Camions/berces/ bétonnières d'occasion | 8704.9023, 8705.1021–4023 | 100/200/400 % |
| Motos CKD/SKD à assembler localement | 8711.xx11/12/13 | 5 % |
| Motos d'occasion (y compris électriques) | 8711.xx20 | 200 % |
| Remorques d'occasion | 8716.3120 | 200 % |

Le détail complet (y compris toutes les positions véhicules 8703.xx par cylindrée/âge) figure dans
`sources/excise_1186.pdf` (pages 12309–12337 de la gazette) et partiellement dans la colonne
« accise » du CSV principal.

## 3. Autres taxes à l'importation (transversales, toutes positions)

| Taxe | Taux | Assise | Base légale |
|---|---|---|---|
| Surtaxe (import sur-tax) | **10 %** | CIF + droits de douane | Règlement 133/2007 (à re-vérifier, régime pouvant avoir évolué) |
| Taxe sociale (Social Welfare Levy) | **3 %** | CIF | Règlement 519/2022 (à re-vérifier, exemptions art. 6) |
| TVA | **15 %** | CIF + droits + surtaxe + accises + SWL | **Proc. 1341/2024** (remplace la 285/2002) |
| Accise | voir tableau | valeur en douane + droit de douane (art. 9(2) Proc. 1186/2020) | Proc. 1186/2020 |
| Précompte/acompte impôt sur revenu | **3 %** | CIF (pour importateurs enregistrés) | Proc. 979/2016 art. 77 |
| Redevances douanières | variables | — | Proc. douane 1160/2019 |

Ordre de calcul : CIF → droit de douane → surtaxe (10 % × (CIF+droit)) → accise → SWL → TVA sur le cumul.

## 4. Taxes à l'exportation

- **Café (HS 0901)** : **6,5 % du prix FOB** — Proclamation 99/1998 (a abrogé les droits
  à l'exportation du 3e annexe du règlement tarifaire 42/1976).
- **Chat/khat** : taxation par bons (vouchers), Proc. 767/2012 ; taxe intérieure 5 Birr/kg ;
  pénalité de 25 % pour non-exportation ; taxes régionales additionnelles (17–35 Birr/kg à divers
  postes de contrôle, hors droit fédéral).
- **Les autres produits** (graines oléagineuses, légumineuses, fleurs, or, khat, bétail…) :
  droits à l'exportation **abolis** (le tarif douanier national ne prévoit plus de droits à
  l'exportation par position — colonne unique « Duty Rate » à l'import dans le livre officiel).
  Restrictions/licences et prix de rapatriement minimum (FRP) de la Banque nationale s'appliquent,
  mais ne sont pas des droits.

## 5. Réserves et vérifications recommandées

- Extraction refaite intégralement depuis le PDF (2e passe) : 6 154 positions uniques,
  96 chapitres, taux renseigné sur 100 % des lignes (1 ligne « Prohibited » : opium 1302.1100 ;
  occasion et textile usagé 6309/6310 également « Prohibited »).
- Comparaison livre 2021 vs portail douanier (collecte 2026) : ~7 % d'écarts (véhicules, papier,
  machines) — **le portail est la référence courante** ; marquer les taux du livre
  « peut avoir été modifié » pour les lignes divergentes.
- Incidences récentes possibles (réforme fiscale 2024–2026, nouveaux décrets d'accises, mesures
  ETF/FRP) : confirmer avec le Ministère des Revenus (morer.gov.et) ou le service douane avant
  toute opération.
- Préférences : COMESA, AGOA (export vers USA), CEDEAO non applicable ; DGFT/accord trépied avec
  l'UE — réductions non intégrées dans ce barème national MFN.

## Sources

- Livre tarifaire officiel : mofed.gov.et (Tariff Reform Book English, 372 p.)
- Excise Tax Proclamation 1186/2020 : ethiodata.et / lawethiopia.com
- Social Welfare Levy Reg. 519/2022 : justice.gov.et
- Coffee Export Tax Proc. 99/1998 : justice.gov.et
- Import Sur-Tax Reg. 133/2007 : justice.gov.et
- Chat Tax Proc. 767/2012 : mesfinbelachew.net
