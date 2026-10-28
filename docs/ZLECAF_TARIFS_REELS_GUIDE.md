# ZLECAf — Données tarifaires réelles (54 pays)

Ce guide indique **où trouver les données réelles** et **comment lire l’arborescence complète** des positions tarifaires, avec:

1. l’arborescence,
2. les descriptions complètes,
3. les taux des droits et taxes,
4. les unités de mesure / de calcul,
5. les formalités administratives.

## 1) Source principale (par pays)

- Dossier: `backend/data/exports/socle/`
- Format: un CSV par pays (`XXX_NPF.csv`, séparateur « ; ») et son fichier de notes (`XXX_NPF_notes.csv`), décrits par `MANIFESTE.json`
- Exemple: `DZA_NPF.csv`, `NGA_NPF.csv`

Ces fichiers sont le tarif NPF tel que le calculateur l’applique (taux par prélèvement, total pour 100 CAF, restrictions). Ils sont servis par `GET /api/tariff-data/download-zip/<ISO>` (CSV + notes) et `GET /api/tariff-data/download-json/<ISO>` (JSON). Ils ont remplacé les anciens CSV par tranches de chapitres (`XXX_NPF_ch01-10.csv`…) et l’ancien JSON du collecteur.

**À chaque changement du tarif** (correction d’un pays, nouveau crawl, modification du moteur) :

```bash
python3 scripts/build_socle.py ISO        # reconstruit le socle du pays
python3 scripts/exporter_tarifs_socle.py ISO   # réécrit son CSV, ses notes et le manifeste
```

et versionner `backend/data/exports/socle/` dans la même PR. Le JSON n’a pas de fichier propre : il se lit sur le CSV archivé, il suit donc chaque réexport. `backend/tests/test_exports_socle.py` fait échouer la CI si un socle ou le moteur a changé sans réexport.

## 2) Source canonique (structure hiérarchique)

- Dossier: `engine/output/`
- Fichiers: `XXX_canonical.jsonl` (un fichier par pays ISO3)
- Exemples: `DZA_canonical.jsonl`, `EGY_canonical.jsonl`, `ZAF_canonical.jsonl`

Chaque ligne JSON décrit une position (HS6 + déclinaisons nationales), incluant les champs normalisés de droits/taxes/formalités.

## 3) Arborescence recommandée de lecture

Pour chaque pays:

- **Chapitre HS2** (2 chiffres)
  - **Position HS4** (4 chiffres)
    - **Sous-position HS6** (6 chiffres)
      - **Position nationale** (8/10/11+ chiffres selon pays)

Ordre de traitement conseillé:

1. charger `XXX_canonical.jsonl`,
2. regrouper par `hs6`,
3. rattacher les sous-positions nationales,
4. exposer les mesures/taxes/formalités au niveau national.

## 4) Champs à vérifier pour votre besoin

Selon le pays et la source, les champs peuvent varier légèrement. Les champs cibles à conserver sont:

- **Descriptions complètes**
  - `description_fr` / `description_en`
  - `national_description` (si présent)
- **Droits et taxes**
  - `duty_rate` (droit principal)
  - `additional_taxes` (TVA, accises, parafiscal, etc.)
- **Unités de mesure / calcul**
  - `unit_of_measure`
  - `calculation_basis` (ad valorem, spécifique, mixte)
- **Formalités administratives**
  - `administrative_formalities` (liste d’exigences/documents/contrôles)

## 5) Important — qualité et fiabilité

- Les fichiers `frontend/public/*_tarif_douanier_echantillon.csv` sont des **échantillons** de démonstration.
- Pour une extraction complète « réelle », utiliser `backend/data/exports/socle/` : c’est le tarif que le calculateur liquide.

## 6) Script utile pour les formalités au niveau sous-position

Le script suivant descend les formalités HS6 vers les sous-positions nationales:

- `backend/scripts/enrich_subposition_formalities.py`

Utilisation:

```bash
python backend/scripts/enrich_subposition_formalities.py
python backend/scripts/enrich_subposition_formalities.py DZA NGA
```

## 7) Couverture pays

Le référentiel couvre les 54 pays ciblés ZLECAf via:

- les fichiers `engine/output/*_canonical.jsonl`,
- les index `engine/output/indexes/countries_index.json`,
- les exports `backend/data/exports/socle/*`.

---

Si vous voulez, on peut ensuite ajouter un export unique `zlecaf_tarifs_reels_54_pays.json` consolidé avec un schéma strict (arborescence + champs obligatoires), prêt pour API/BI.
