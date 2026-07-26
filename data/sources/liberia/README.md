# Liberia — collecte (partielle, taux potentiellement obsolète)

Consultation : 2026-07-25.

Collecte délibérément incomplète et signalée à risque : la base légale (goods tax / services tax, équivalent TVA) est vérifiée sur le Liberia Revenue Code As Amended (consolidation 2020), mais des amendements plus récents (décembre 2024, décembre 2025) n'ont **pas pu être vérifiés** en raison d'un blocage technique — voir ci-dessous.

## Ce qui a été vérifié sur texte primaire (consolidation 2020)

- **Goods tax taux standard 10%** — Section 1000(b)(3) : « The rate of goods tax is 10 percent... except that if the supply is an export of goods, the rate of tax is zero (0) percent. »
- **Services tax taux standard 10%** — Section 1021(b)(1).
- **Surtaxe télécommunications +5%** (soit 15% combiné sur les services télécom) — Section 1021(b)(2).
- **Exportations taux zéro** — Section 1000(b)(3).
- **Structure du régime d'accises** (Sections 1108-1114) : cadre confirmé (taux spécifiques/ad valorem/hybrides, exportations à taux zéro, base d'imposition), mais le barème réel des taux (« Schedule I ») **n'apparaît pas** dans l'extraction texte du document consolidé — probablement une annexe distincte non incluse dans ce PDF.

## Alerte sincérité : taux potentiellement obsolète

Une source secondaire (vatcalc.com) affirme que le taux goods/services tax est passé de 10% à **12%** à compter d'avril 2025, dans le cadre d'une transition prévue vers un système de TVA à 15% en janvier 2027. **Cette affirmation n'a pas pu être vérifiée sur texte primaire** :

- Les deux amendements les plus récents identifiés sur le portail officiel LRA (`TAX-AMENDMENT-ACT-OF-DECEMBER-2024...pdf` et `LRC-Amendment-December-2025.pdf`) sont des **PDF scannés/image** — seule la page de couverture s'extrait en texte, le corps du texte est illisible par `pdftotext`.
- Aucun outil OCR (`tesseract`) n'est disponible dans cet environnement de collecte — même blocage que rencontré pour le Togo (CGI scanné).
- Conformément à la règle de sincérité, les taux publiés dans `vat_measures.json` sont ceux de la **dernière consolidation vérifiable sur texte primaire (2020, 10%)**, avec une note explicite sur chaque enregistrement signalant le risque d'obsolescence.

**Action de suivi requise** : obtenir un accès OCR ou une version texte des amendements 2024/2025 pour confirmer ou infirmer le taux actuel avant tout enregistrement dans `SUPPORTED_JURISDICTIONS`.

## Ce qui n'a PAS été collecté

- **Barème détaillé des accises** (Schedule I) : cadre structurel vérifié, taux par produit non trouvés dans le texte accessible.
- **Tarif Extérieur Commun (TEC) CEDEAO** : non archivé.
- **Confirmation du taux actuel** (10% vs 12% potentiel) : voir alerte ci-dessus.

## État de l'enregistrement

Juridiction LBR : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` — taux 2020 vérifié mais signalé à risque d'obsolescence, barème accises manquant. ZLECAf : **pas** d'offre nationale encore enregistrée dans `NATIONAL_OFFER_REGISTRY`.
