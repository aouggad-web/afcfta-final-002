# Ce que le calculateur ne sait pas — mesure du 23/09/2026

> Mesuré sur `main` à `f78405db`, socle reconstruit. **Aucune donnée n'est
> modifiée par ce document.** Le script qui produit chacun des chiffres
> ci-dessous est reproductible : il n'appelle que le socle versionné et les
> services du dépôt, sans réseau.
>
> La conclusion qui domine toutes les autres : **un calculateur ZLECAf qui ne
> sert aujourd'hui aucune préférence ZLECAf.**

---

## 1. La préférence ZLECAf ne se sert sur aucun couloir

`taux_preferentiels()` exécuté sur les **2 756 couples destination × origine**
que le socle permet de former (54 pays, moins les deux vides) :

| Ce que le moteur rend | couples |
|---|---|
| `NOT_AVAILABLE` — aucune preuve d'application bilatérale | 2 023 |
| `OFFER_ONLY` — offre tarifaire archivée, mise en œuvre non établie | 360 |
| `PARTNER_NOTICE_REQUIRED` — réciprocité non établie | 205 |
| **Préférence servie au titre d'une UNION DOUANIÈRE** | **148** |
| `PREFERENCE_NON_TRACEE` — couloir ouvert, aucun taux | 20 |
| **Préférence servie au titre de la ZLECAf** | **0** |

Les 148 préférences effectivement servies relèvent de la libre circulation
intra-bloc — EAC, SACU, CEMAC, UEMOA. Le moteur les nomme correctement
`UNION_DOUANIERE`, et elles sont **antérieures à la ZLECAf**. Aucune n'est une
préférence continentale.

### 1.1 Pourquoi : une intersection vide

Les deux verrous de `preference.py` ne s'ouvrent jamais ensemble.

**Verrou 1 — le couloir doit être autorisé.** `zlecaf_implementation_registry`
ne contient que **cinq pays**, dont **un seul `APPLIED`** :

```
CIV  PARTNER_NOTICE_REQUIRED
ETH  PARTNER_NOTICE_REQUIRED
KEN  APPLIED                   ← le seul
NGA  PARTNER_NOTICE_REQUIRED
ZMB  PARTNER_NOTICE_REQUIRED
```

**Verrou 2 — le taux doit être tracé.** **Neuf pays** portent une colonne
`AFCFTA` au socle : AGO, BWA, LSO, MUS, MWI, NAM, SWZ, SYC, ZAF.

**L'intersection des deux ensembles est vide.** Le seul couloir juridiquement
ouvert est celui dont le tarif ne porte aucun taux préférentiel : vérifié sur
les 5 935 positions kényanes, **aucune** ne porte de colonne `AFCFTA`. D'où les
20 `PREFERENCE_NON_TRACEE` — ce sont les origines admises par le Kenya, qui se
heurtent toutes à l'absence de barème.

Sur les 368 260 positions du socle, **68 954 portent un taux ZLECAf, soit
18,7 %** — et toutes appartiennent à des pays dont le couloir n'est pas
autorisé.

### 1.2 Ce que ce constat n'est PAS

**Le moteur ne fabrique rien.** Vérifié : `preference.py` est *fail-closed* et
refuse en nommant sa raison ; aucun taux n'est dérivé du NPF par un
coefficient ; `calcul.py` refuse de calculer une économie si l'un des deux
régimes n'est pas `COMPLET`. Un couloir non établi rend le régime NPF, annoncé
comme tel.

C'est donc une **carence de collecte**, des deux côtés à la fois : les
instruments d'application nationaux d'une part, les barèmes de démantèlement
de l'autre. Le code est prêt ; la donnée n'y est pas.

---

## 2. SACU — la donnée est là, un champ vide la rend muette

Botswana, Lesotho, Namibie et Eswatini portent **exactement le même tarif que
l'Afrique du Sud** : 8 589 positions, 8 589 droits, 8 361 taux chiffrés et 228
sans taux — distribution identique, octet pour octet, source `sars.gov.za`.

| | droits | liquidables | assiette |
|---|---|---|---|
| **ZAF** | 8 589 | **8 494 — 98,9 %** | `Customs and Excise Act 91/1964 s.65-67 + SARS SC-CR-A-03` |
| **BWA** | 8 589 | **227 — 2,6 %** | `""` · `source_seule` |
| **LSO** | 8 589 | **227 — 2,6 %** | `""` · `source_seule` |
| **NAM** | 8 589 | **227 — 2,6 %** | `""` · `source_seule` |
| **SWZ** | 8 589 | **227 — 2,6 %** | `""` · `source_seule` |

La règle de `build_socle.py:1196` est sans détour :

```python
elif d["assiette"] and (d["taux"] is not None or specifique_lisible):
    compteurs["droits_liquidables"] += 1
```

**Sans assiette, aucun droit ne se liquide**, si publié que soit son taux.
**33 448 droits** sont muets pour quatre champs vides.

C'est la carence la moins chère de toute cette liste : quatre références
légales. **Mais elle ne se comble pas en recopiant celle de l'Afrique du Sud**
— chaque État a sa propre loi douanière, et l'administration commune du tarif
extérieur ne dit rien de ce que chaque droit national prescrit comme valeur en
douane. Quatre recherches séparées, quatre textes, ou quatre articles de renvoi
identifiés. La collecte est engagée, pays par pays.

**Piège à signaler à qui la mènera :** le dépôt a déjà établi que la valeur en
douane de la SACU est la valeur **FOB**, jamais déduite du CIF (Act 91 of 1964,
s.65(1)) — 41 % des positions sud-africaines répondent déjà
`VALEUR_FOB_REQUISE`. Une assiette CIF posée par réflexe sur ces quatre pays
produirait des montants faux qui auraient l'air complets.

---

## 3. Les assiettes absentes — onze pays

```
BWA  COD  CPV  DJI  ERI  LBY  LSO  NAM  SDN  SSD  SWZ
```

Aucune entrée dans `assiettes_pays.json`. Le moteur rend
`ASSIETTE_INDISPONIBLE`, quels que soient les taux collectés. Les quatre de la
SACU sont traités au §2 ; les sept autres demandent chacun leur propre
recherche.

---

## 4. La TVA — neuf pays sans TVA ni repli

Douze pays ne portent **aucune ligne de TVA** au socle :

```
AGO  BWA  DJI  ERI  LBY  LSO  NAM  SOM  SWZ  SYC  ZAF  ZWE
```

La table nationale de repli `tva_nationale.json` n'en couvre que **trois** —
ZAF, DJI, AGO — et porte sa propre réserve, inscrite dans le fichier : c'est le
taux **standard**, qui ne distingue ni les biens détaxés ni les exonérés, et
toute ligne qu'il produit annonce cette réserve.

**Restent neuf pays sans TVA d'aucune sorte :**

```
BWA  ERI  LBY  LSO  NAM  SOM  SWZ  SYC  ZWE
```

L'Afrique du Sud, premier importateur du continent, n'est servie que par le
repli — donc avec sa réserve, sur toutes ses positions.

---

## 5. L'état de couverture

**23 `COMPLET`** · **29 `PARTIEL`** · **2 `VIDE`**.

**Djibouti et l'Érythrée portent zéro position.** Le calculateur ne connaît pas
ces deux pays ; il ne s'en cache pas, mais il ne peut rien en dire.

Les plus dégradés après la SACU :

| | liquidable | cause dominante |
|---|---|---|
| Libye | 33,0 % | pas de TVA, 11 849 droits sans taux |
| Malawi | 48,6 % | 15 032 droits sans taux |
| Soudan | 50,0 % | pas d'assiette, nomenclature SH6 seule |
| Éthiopie | 56,8 % | 8 538 droits sans taux |
| Égypte | 97,1 % | 530 droits — droits spécifiques, cf. rapport du 21/09 |

---

## 6. Les formalités — quasi inexistantes

**Aucune position du socle ne porte de formalités.** Deux fichiers dans
`data/` : le Kenya, et un échantillon de portail algérien. Le panneau
réglementaire n'a rien à afficher pour 52 pays sur 54.

---

## 7. Par coût croissant

1. **Les quatre assiettes SACU** — 33 448 droits débloqués. Quatre recherches
   séparées ; ne pas généraliser depuis l'Afrique du Sud, et se méfier du FOB.
2. **Les sept assiettes restantes** — COD, CPV, LBY, SDN, SSD, DJI, ERI.
3. **Le barème ZLECAf kényan** — le Kenya est le seul couloir autorisé. Son
   barème rendrait le produit capable de servir sa première vraie préférence
   continentale. C'est le geste au meilleur rapport entre coût et portée.
4. **Les neuf TVA manquantes**, chacune sur son texte fiscal national.
5. **Les instruments d'application nationaux de la ZLECAf** — le chantier de
   fond, et le seul qui change la nature du produit.

Aucun de ces postes ne se comble en devinant. Une assiette supposée, un barème
de démantèlement reconstruit depuis le NPF, une TVA prise au taux standard là
où le texte détaxe : chacun produirait des montants faux, et les trois auraient
l'air complets.
