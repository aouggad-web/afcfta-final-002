# Contrat de collecte — Comores, Madagascar, Soudan, São Tomé-et-Príncipe

> À remettre à qui collecte la donnée. Ce document dit **ce qui est attendu**,
> **dans quelle forme**, et **ce qui sera refusé**. Il ne dit pas où chercher :
> c'est au collecteur de citer sa source.

---

## 1. Pourquoi ces quatre pays

Ces quatre pays sont les seuls du socle dont **la totalité du droit de douane
provient d'une moyenne statistique** et non d'un tarif national.

| Pays | Positions | Source actuelle du droit | Source actuelle de la taxe intérieure |
|---|---|---|---|
| Comores (COM) | 5 388 | WITS / UNCTAD-TRAINS, MFN *SimpleAverage* 2021 | Société Générale International Trade Portal |
| Madagascar (MDG) | 5 624 | WITS / UNCTAD-TRAINS, MFN *SimpleAverage* 2022 | PwC Worldwide Tax Summaries (1 ligne sur LF 2025) |
| Soudan (SDN) | 5 388 | WITS / UNCTAD-TRAINS, MFN *SimpleAverage* 2021 | Trading Economics / CEIC |
| São Tomé (STP) | 5 388 | WITS / UNCTAD-TRAINS, MFN *SimpleAverage* 2019 | Lei n.º 02/2023 (source primaire — **à conserver**) |

Deux conséquences qui fondent la commande :

1. **Une moyenne n'est pas un taux.** `20,0 % (MFN, SimpleAverage, 2021)` est la
   moyenne des lignes nationales sous un SH6 ; aucune marchandise ne se liquide
   à ce taux. Servi tel quel, il produit un montant faux avec une apparence
   exacte — c'est exactement ce que la doctrine du dépôt interdit.
2. **Le code est un SH6, pas une position.** Ces quatre pays sont les seuls à
   n'avoir aucune position nationale. Le déclarant ne saisit pas un SH6 : il
   saisit la position du tarif de son pays.

La taxe intérieure de São Tomé (IVA, Lei n.º 02/2023) est correctement sourcée :
**ne la remplace pas**. Les trois autres (Société Générale, PwC, Trading
Economics) sont des agrégateurs et tombent sous la même règle que le droit.

---

## 2. Ce qui est livré : un fichier par pays

Un seul fichier JSON par pays, nommé `<ISO3>_tariffs.json`
(`COM_tariffs.json`, `MDG_tariffs.json`, `SDN_tariffs.json`,
`STP_tariffs.json`), déposé dans `backend/data/crawled/`.

Le modèle de référence est `backend/data/crawled/MRT_tariffs.json` (Mauritanie) :
en cas de doute sur un champ, c'est lui qui tranche.

### 2.1 En-tête du fichier

```json
{
  "country": "COM",
  "country_name": "Comores",
  "source": "Tarif des douanes de l'Union des Comores, édition <année>",
  "source_name": "<nom exact du document officiel>",
  "source_url": "<URL du document, telle qu'elle a servi à le télécharger>",
  "source_sha256": "<SHA-256 du fichier téléchargé, octet pour octet>",
  "extracted_at": "<date ISO 8601 de la collecte>",
  "source_quality": "crawled_authentic_national",
  "stats": { "positions": 0, "chapters": 0 },
  "calculation_rules": { "order": [...], "bases": {...}, "source": "..." },
  "regimes_registry": {},
  "sub_positions": [ ... ]
}
```

`source_sha256` est **l'empreinte du document source lui-même** (le PDF, le
fichier tarif), pas celle du JSON produit. Le document doit être conservé et
fourni avec le JSON : c'est lui qui permet de rejouer la lecture.

### 2.2 Une position

```json
{
  "hs_code": "0101210000",
  "chapter": "01",
  "name": "Reproducteurs de race pure",
  "description": "<libellé complet tel que publié>",
  "unit": "u",
  "taxes": {
    "DD": {
      "name": "Droit de douane (tarif national <année>)",
      "rate": 5.0,
      "raw": "5 %",
      "source": "<le même document que l'en-tête>",
      "source_url": "<URL>",
      "source_sha256": "<empreinte>"
    }
  }
}
```

Règles de forme, sans exception :

- `hs_code` est une **chaîne**, jamais un nombre : les zéros de tête sont
  significatifs. C'est la **position nationale complète** telle que le tarif la
  publie (8, 10 ou 12 chiffres selon le pays), pas un SH6 tronqué ni rallongé
  de zéros.
- `rate` est un nombre en **points de pourcentage** (`5.0` pour 5 %), jamais une
  fraction (`0.05`), jamais une chaîne.
- `raw` reprend la mention **telle qu'imprimée** (`"5 %"`, `"1,5 %"`,
  `"120 KMF/kg"`, `"exempt"`). C'est la trace qui permet de contester une
  lecture.
- Chaque taxe porte ses trois champs de provenance (`source`, `source_url`,
  `source_sha256`). Une taxe sans provenance est un taux fabriqué.
- Les codes de taxe sont ceux du pays (`DD`, `TVA`, `IVA`, `RS`, `PC`…), écrits
  une seule fois de la même façon dans tout le fichier.

---

## 3. Les cinq refus

Ce qui fait rejeter la livraison, en entier :

1. **Un taux inventé, arrondi, moyenné ou repris d'un pays voisin.** Aucune
   estimation, aucune interpolation, aucun « taux courant du chapitre ».
2. **Un agrégateur comme source d'un taux** : WITS, UNCTAD-TRAINS, PwC, Trading
   Economics, CEIC, Société Générale, Wikipédia, un cabinet, un article de
   presse. Ils peuvent servir à *repérer* un texte ; jamais à le remplacer.
3. **Un zéro mis à la place d'une absence.** Un taux que le tarif ne publie pas
   est `null` — jamais `0`. Inversement, **un zéro publié est une donnée** : il
   se livre à `0.0` avec son `raw` (`"0 %"`, `"exempt"`, `"franc"`), il ne
   s'omet pas. Les deux cas sont distincts et doivent le rester.
4. **Un droit spécifique converti en pourcentage.** `120 KMF/kg` reste
   `120 KMF/kg` : `raw` porte la mention, l'unité est conservée, `rate` reste
   `null` si le droit n'est pas ad valorem. Une conversion suppose un prix : ce
   prix serait inventé.
5. **Un code mal lu « reconstitué ».** Si un chiffre de la position est
   illisible, la position est **écartée et déclarée**, pas devinée. Un droit
   réel sous un mauvais code se liquide sur une autre marchandise.

---

## 4. Les assiettes — le point qui décide si la collecte sert à quelque chose

Un taux sans assiette ne se liquide pas. État vérifié au
`backend/socle/assiettes_pays.json` (43 pays y figurent) :

| Pays | Droit de douane | Taxe intérieure | À faire |
|---|---|---|---|
| **COM** | `CIF` — Code des douanes, Loi n°15-016/AU, art. 36 et 40.1 e) | `CIF+TOUS_SAUF_TVA` — CGI éd. 2023, art. 140 4° | rien : les deux assiettes tiennent sur texte primaire |
| **STP** | `CIF`, **origine `profil_code`** | `CIF+TOUS_SAUF_TVA` — Lei n.º 02/2023 | établir l'assiette du droit sur le texte douanier |
| **MDG** | `CIF`, **origine `profil_code`** | `CIF+DD`, **origine `profil_code`** | établir **les deux** sur texte primaire |
| **SDN** | **aucune entrée** | **aucune entrée** | tout établir : ordre des prélèvements + assiette de chacun |

`origine_assiette: "profil_code"` signifie que l'assiette vient d'un profil
générique du code, pas d'un article de loi lu : elle est plausible, elle n'est
pas établie.

Pour Madagascar et le Soudan, **collecter les taux sans établir l'assiette ne
produit aucun montant liquidable.** Si un seul effort doit être priorisé sur ces
deux pays, c'est l'assiette avant les taux.

Ce qui est attendu pour une assiette : l'article du code des douanes ou du code
général des impôts qui définit la base de chaque prélèvement, avec l'extrait
archivé et son SHA-256 (fiche dans
`backend/data/legal_refs/zlecaf_application/`, extrait dans son sous-dossier
`sources/` — `scripts/verifier_fiche.py` contrôle la chaîne).

---

## 5. Ce qu'on fait du fichier une fois livré

Côté dépôt, rien ne se modifie à la main. Le fichier entre par le haut de la
chaîne et tout le reste se régénère :

```
backend/data/crawled/<ISO3>_tariffs.json      ← le fichier livré
        │  python3 scripts/normalize_crawled.py     (~8 min)
        ▼
backend/data/crawled_normalized/               ← gitignoré
        │  python3 scripts/build_socle.py           (~1 min)
        ▼
backend/socle/                                 ← gitignoré sauf 4 fichiers
```

Puis, dans le même commit, les **trois registres d'empreintes** doivent
concorder (`test_dataset_hash_stores_agree.py` échoue sinon) :

1. `backend/socle/MANIFESTE.json` — écrit par `build_socle.py` ;
2. `backend/data/source_registry_v2.json` — empreinte + `positions_count` ;
3. `data/<pays>/legal_sources.json` — empreinte + notes.

Le fichier livré porte en outre un `_integrity_seal` posé par
`seal_crawled_file()` (`backend/crawlers/integrity.py`). **Toute modification
ultérieure du fichier passe par un script qui repose le sceau** ; une retouche
manuelle casse le `content_hash` et le socle devient inerte — ce qui est le
comportement voulu.

---

## 6. Livraison minimale acceptable

Un pays peut être livré **partiellement** : mieux vaut 800 positions lues sur le
texte officiel que 5 388 moyennes. Ce qui compte :

- chaque position livrée porte sa provenance et son `raw` ;
- ce qui n'a pas été collecté est **absent du fichier**, pas rempli de `null`
  décoratifs ni de zéros ;
- un court relevé accompagne la livraison : le document source (avec son
  SHA-256), les chapitres couverts, les positions écartées et pourquoi.

Tant que la collecte n'a pas eu lieu, le calculateur signalera ces pays comme
reposant sur une base statistique — c'est la contrepartie de ne pas les avoir
déclarés exacts.
