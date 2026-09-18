# Collecte des données manquantes — état au 2026-09-17

Relevé sur `backend/socle/MANIFESTE.json` et les fichiers pays du socle, pas
sur une impression. Tous les chiffres ci-dessous sont reproductibles.

**État global :** 54 pays, 359 108 positions, 1 085 056 droits, dont
**975 589 liquidables**. Reste **109 467 droits non liquidables**, concentrés
sur 25 pays — et la cause dominante n'est pas le taux, c'est **l'assiette**.

---

## 1. Ce qui manque, par ordre de coût

| Pays | Droits non liquidables | Prélèvement(s) en cause | Cause | TVA à la source |
|---|---:|---|---|---|
| **NGA** | 12 778 / 25 452 | `IAT`, `EXC` | assiette absente (6 350 ch.) + 501 taux | oui |
| **SOM** | 11 545 / 11 545 | `DD` | assiette absente — **100 %** | non |
| **LBY** | 10 776 / 16 164 | `TSP`, `TP` | assiette absente (5 388 ch.) | non |
| **SWZ** | 8 408 / 8 589 | `DD` | assiette absente | non |
| **NAM** | 8 408 / 8 589 | `DD` | assiette absente | non |
| **LSO** | 8 408 / 8 589 | `DD` | assiette absente | non |
| **BWA** | 8 408 / 8 589 | `DD` | assiette absente | non |
| **ETH** | 7 170 / 18 396 | — | assiette absente | oui |
| **SYC** | 5 396 / 10 792 | `TVA` | assiette absente | oui |
| **AGO, COM, MRT, SDN, STP** | 5 388 chacun | `TVA` | assiette absente | oui |
| **EGY** | 491 / 18 043 | — | 456 assiettes + 58 taux | oui |
| **DZA** | 250 / 69 332 | — | assiette absente | oui |
| **CIV** | 152 / 11 874 | — | assiette absente | oui |
| **UGA, TZA, SSD** | 48 chacun | — | taux absent | oui |
| **DJI, ERI** | — | **tout** | aucune position collectée | — |

### Les quatre familles de manque

**A. L'assiette d'un prélèvement nommé** — le plus gros poste, et le plus
facile à combler : une seule règle de droit couvre des milliers de lignes.
Exemple déjà traité : la directive UEMOA 02/98 fixe l'assiette de la TVA pour
huit pays d'un coup (`backend/data/legal_refs/zlecaf_application/UEMOA_assiette_TVA_2026-09-14.json`).

**B. Le taux de TVA** — 8 pays n'ont aucune ligne de TVA à la source :
`BWA`, `DJI`, `ERI`, `LBY`, `LSO`, `NAM`, `SOM`, `SWZ`.
(L'Afrique du Sud était la neuvième : comblée le 2026-09-17, voir
`ZAF_taux_TVA_2026-09-17.json`.)

**C. Les pays vides** — `DJI` et `ERI` : aucune position. Il faut le tarif
douanier national complet, pas un complément.

**D. Les 9 pays encore servis par une moyenne SH6 (WITS / UNCTAD-TRAINS)** —
`AGO COM MDG MRT MWI SDN STP SYC ZMB`.
Ce ne sont pas des tarifs nationaux : ce sont des moyennes SH6 de la Banque
mondiale. Elles donnent un ordre de grandeur, jamais le droit exigible sur une
position nationale. Les remplacer par le tarif publié par chaque douane est le
chantier de fond.

Quatre en sont sortis, sur le tarif publié par leur douane et avec la fiche
qui établit leurs assiettes : `LBY` (5 920 positions), `MUS` (6 941),
`MOZ` (5 822) et `ZWE` (6 637, SI 203 of 2022).

---

## 2. Règles non négociables

Elles ne sont pas décoratives : tout le calculateur repose dessus.

1. **Aucune valeur de mémoire.** Le taux doit être lu dans un document publié
   par l'autorité qui le perçoit. Contre-exemple vécu : l'Afrique du Sud a
   annoncé une TVA à 15,5 % puis 16 %, **les deux annulées**. Le taux réel est
   resté 15 %. Une réponse de mémoire aurait été fausse et crédible.
2. **Le verbatim prime sur le résumé.** On cite la phrase du texte, dans sa
   langue, sans la reformuler.
3. **Un conflit se consigne, il ne se tranche pas.** Cas ouvert : la page
   officielle de la BURS annonce une TVA botswanaise à **12 %** quand **14 %**
   est communément rapporté. Tant qu'un avis de taux daté ne départage pas, le
   pays reste en attente — on n'en choisit aucun.
4. **Une donnée générique n'est pas une donnée.** Une mention recopiée à
   l'identique sur toutes les lignes d'un pays est une affirmation de niveau
   national, pas une donnée de position. Elle se range au niveau du pays, ou
   elle ne se range pas.
5. **Un manque nommé vaut mieux qu'un trou comblé.** Le moteur sait dire
   « indisponible » ; il ne sait pas rattraper un chiffre inventé.

---

## 3. Le prompt à utiliser

À copier tel quel, en remplaçant les trois champs entre crochets.

```
Tu es chargé d'établir une donnée fiscale sur source primaire, pour un
calculateur de droits et taxes à l'importation en Afrique.

OBJET DE LA RECHERCHE
- Pays : [PAYS, code ISO3]
- Donnée cherchée : [ex. « le taux standard de la TVA à l'importation »
  ou « l'assiette légale du prélèvement IAT » ou « le tarif douanier national
  complet »]
- Autorité compétente : [ex. « Nigeria Customs Service — customs.gov.ng »]

CE QUI EST DEMANDÉ
Trouve le document officiel qui établit cette donnée : loi de finances, code
des douanes, code de la TVA, directive communautaire, avis de taux, ou page
publiée par l'administration qui perçoit l'impôt. Puis rends-moi :

1. L'URL exacte du document.
2. Le nom de l'institution qui le publie.
3. La date du document, et la date à laquelle tu l'as consulté.
4. Le VERBATIM de la phrase ou de l'article qui établit la donnée — dans la
   langue d'origine, recopié sans reformulation.
5. La référence précise : numéro d'article, d'alinéa, de loi ou de circulaire.
6. La valeur retenue (un nombre, ou une formule d'assiette).
7. Ce que le document NE tranche PAS : exonérations, taux réduits, régimes
   suspensifs, biens détaxés, cas particuliers.

RÈGLES ABSOLUES
- N'écris JAMAIS une valeur de mémoire ou « connue ». Si tu ne trouves pas de
  document, réponds « NON ÉTABLI » et dis ce que tu as cherché. C'est une
  réponse acceptable ; une valeur inventée ne l'est pas.
- Si deux sources se contredisent, rapporte LES DEUX avec leurs URL, et ne
  choisis pas. Signale le conflit explicitement.
- Distingue ce qui est en vigueur de ce qui a été annoncé, proposé, voté mais
  non promulgué, ou annulé. Beaucoup de taux annoncés ne sont jamais entrés en
  vigueur.
- Une source secondaire (cabinet de conseil, presse, agrégateur, encyclopédie)
  ne vaut pas preuve. Elle peut servir à TROUVER le texte officiel ; c'est le
  texte officiel qui est cité.
- Si la donnée varie selon le produit, dis-le et donne la règle générale sans
  prétendre couvrir chaque position.

FORMAT DE RÉPONSE
Un objet JSON de cette forme, et rien d'autre :

{
  "pays": "ISO3",
  "objet": "ce qui est établi, en une phrase",
  "etabli": true,
  "verified_at": "AAAA-MM-JJ",
  "source": {
    "url": "...",
    "institution": "...",
    "document": "titre et date du document",
    "reference": "article / alinéa / numéro"
  },
  "regle": {
    "valeur": "15.0  ou  CIF+DD  selon le cas",
    "verbatim": "la phrase exacte du texte, non reformulée",
    "portee": "à quoi elle s'applique"
  },
  "ne_tranche_pas": ["exonérations non couvertes", "..."],
  "conflits": ["source A dit X (url), source B dit Y (url)"],
  "doutes": "ce dont tu n'es pas certain, en clair"
}

Si la donnée n'est pas établie, renvoie le même objet avec "etabli": false,
"regle" à null, et le détail de ce que tu as cherché dans "doutes".
```

---

## 4. Ordre conseillé

Trier par nombre de lignes débloquées, pas par facilité.

1. **`SOM` — l'assiette du `DD`.** 11 545 droits, soit 100 % du pays, pour une
   seule règle. Le meilleur rapport effort/rendement du lot.
2. **`BWA` `LSO` `NAM` `SWZ` — l'assiette du `DD`.** 33 632 droits pour quatre
   pays qui partagent le tarif extérieur de la SACU : la règle est probablement
   commune, à vérifier.
3. **`NGA` — l'assiette de `IAT` et `EXC`.** 12 700 droits, une seule douane,
   un seul texte à trouver.
4. **`LBY` — l'assiette de `TSP` et `TP`.** 10 776 droits.
5. **`AGO` `COM` `MRT` `SDN` `STP` `SYC` — l'assiette de la `TVA`.** ~32 000
   droits, six textes nationaux distincts (une union ne les harmonise pas).
6. **Les taux de TVA** des 8 pays qui n'en ont aucun.
7. **`DJI` et `ERI`** — tarif complet. Le plus lourd, et le plus incertain.

---

## 5. Où déposer le résultat

- Le document source (texte extrait ou PDF) →
  `backend/data/legal_refs/zlecaf_application/sources/`
- La fiche JSON → `backend/data/legal_refs/zlecaf_application/`
  nommée `ISO3_objet_AAAA-MM-JJ.json`
- Empreinte : `sha256sum` du fichier source, reportée dans la fiche.

Modèles à imiter, du plus complet au plus simple :
`UEMOA_assiette_TVA_2026-09-14.json`, `ZAF_taux_TVA_2026-09-17.json`,
`TUN_assiette_TVA_2026-09-14.json`.

## 6. Vérifier la fiche avant de l'intégrer

```
python3 scripts/verifier_fiche.py <chemin de la fiche>
python3 scripts/verifier_fiche.py --toutes
```

Le script ne dit pas si la donnée est **vraie** — aucun programme ne le peut.
Il dit si elle est **vérifiable** : source nommée, verbatim présent, valeur
retenue, et empreinte des textes archivés conforme.

**Portée exacte du contrôle d'empreinte**, pour ne pas le surestimer : il
porte sur chaque texte réellement archivé dans le dépôt, à quelque
profondeur qu'il se trouve dans la fiche (`source.`, `determinations[].`,
`instrument.`…). Là, un seul octet modifié fait échouer la fiche. En
revanche, une citation **sans** texte archivé, ou archivée sans empreinte
déclarée, ne peut pas être contrôlée : le script le dit en réserve plutôt
que de valider en silence. Le nombre d'empreintes effectivement vérifiées
est affiché.

Il accepte `"etabli": false` comme réponse valable, à condition que le champ
`doutes` dise ce qui a été cherché — refuser une collecte infructueuse
pousserait à inventer.

Le rapport distingue trois marques : `✓` une fiche établissant une valeur,
`–` un autre document (relevé d'application, plan de collecte) dont les
empreintes sont tout de même contrôlées, `○` une fiche déclarée non établie.
`✗` signale une anomalie et rend un code de retour non nul.

## 7. Comment la fiche entre dans le calcul

Deux chemins, selon la nature de la donnée. Aucun des deux ne demande
d'écrire du code : ce sont des tables.

**Un taux** (ex. la TVA d'un pays qui n'en a aucune à la source) →
`backend/socle/tva_nationale.json`, lu par `services/socle.py`, appliqué par
`routes/calcul.py`. La règle est stricte : le complément ne joue que si la
famille est **entièrement absente** de la source et qu'une fiche établit le
taux ; il ne remplace jamais une donnée collectée position par position. Il
est toujours annoncé dans `complements_nationaux`, jamais en silence, et
la confiance affichée retombe à « partielle ».

**Une assiette** (le gros des manques) → `backend/socle/assiettes_pays.json`,
sous `pays.<ISO3>.taxes.<CODE>`, puis `python3 scripts/build_socle.py <ISO3>`.
Le constructeur applique une précédence claire, vérifiée : assiette portée
par la ligne source → règle globale du fichier collecté → **cette table** →
`assiettes_indisponibles`. L'entrée porte son `origine_assiette`, qui suit la
donnée jusqu'à l'affichage.

Deux exemples mesurés de ce que cela débloque : le Nigeria figure déjà dans
la table mais sans `IAT` ni `EXC` — les deux prélèvements dont les 12 700
droits sont non liquidables. La Somalie en est absente, d'où 11 545 droits
sans assiette, soit 100 % du pays.

C'est le chemin suivi pour l'Afrique du Sud, et il est reproductible tel quel.
