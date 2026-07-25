# Cameroun — collecte

Consultation : 2026-07-25 (Africa/Algiers).

Premier pays CEMAC collecté. Contrairement à l'EAC (AfricanLII) et à la RDC (LEGANET.CD), la CEMAC n'a pas d'écosystème de base légale consolidée équivalent. La Direction Générale des Impôts publie néanmoins directement le **Code Général des Impôts** en PDF téléchargeable sur son propre portail (`impots.cm`), ce qui a permis une collecte à la même rigueur que le Kenya/la RDC : texte primaire, article précis, HS codes explicites.

## Source primaire

**Code Général des Impôts, édition 2021** — https://impots.cm/sites/default/files/documents/CGI%202021.pdf (968 pages, 8,2 Mo).

Le PDF complet dépasse la politique de poids du dépôt (le plus gros PDF déjà archivé, le CET EAC, fait 4,6 Mo). Décision : archiver l'**extrait textuel** des parties juridiquement opérantes — Article 142 (taux) et Annexe II (liste des produits soumis aux droits d'accises) — et conserver le SHA-256 du PDF source complet pour permettre une vérification par re-téléchargement (`source_document_sha256` dans `legal_sources.json`).

## Faits vérifiés sur texte primaire (Article 142 du CGI 2021)

- **TVA taux général : 17,5%** (Art. 142 (1) a). Taux zéro sur les exportations (Art. 142 (1) a, (4)).
- **Centimes additionnels communaux (CAC) : 10%** du montant de la TVA due — porté au taux général (Art. 142 (2)). Taux effectif combiné confirmé à **19,25%** par l'arrêté de retenue à la source reproduit dans le même Code. Assiette distincte (10% de la TVA, pas de la valeur en douane) : non branchable tel quel sur `DEFAULT_LEVY_TABLES` du moteur, qui calcule `rate × customs_value` pour toutes ses entrées — voir note dans `import_levies.json`.
- **Droit d'accises — barème complet et affectation par position tarifaire** (Art. 142 (1) b, (5)-(6)) :
  - Taux super élevé (50%) : hydroquinone (2907.22.00.000) et cosmétiques importés en contenant (chapitre 33)
  - Taux élevé (30%) : tabacs (chapitre 24), pipes (2403.11, 2403.19.90, 9614.00)
  - Taux moyen (12,5%) : motocycles >250cm³, pièces de motocycles, cheveux/perruques, friperie, pneumatiques d'occasion
  - Taux réduit (5%) : sucreries, chocolats, préparations pour consommation, glaces, gruaux de maïs importés, mayonnaise importée
  - Taux général (25%) : tout le reste de l'Annexe II
  - Taux super réduit : chiffre d'affaires des opérateurs télécom/internet (non un droit ad valorem sur produit)
- **Droits spécifiques (non calculables sans donnée de quantité)** : plancher tabac (5000 XAF/1000 tiges), bières (75 XAF/65cl, 37,5 XAF/33cl), vins/spiritueux/whiskies/champagnes locaux (2 à 25 XAF/cl). Ces entrées sont dans une section séparée (`excise_specific_duties_pending_quantity_data`) car `NationalFiscalStore.excise_rates()` ne lit que `excise_rates` (ad valorem) — les remonter en `missing_elements` nécessite une extension du moteur, pas encore faite.

## Ce qui reste à collecter

- **Tarif Extérieur Commun (TEC) CEMAC** : indispensable pour tout calcul douanier de bout en bout — pas encore archivé dans ce dépôt (contrairement au CET EAC déjà présent pour le Kenya).
- Édition du CGI postérieure à 2021 et lois de finances annuelles (`impots.cm/fr/documentation`, accessible mais non explorée en profondeur).
- Taux d'accises exacts sur vins/spiritueux/whiskies **importés** (le texte extrait ne couvre explicitement que les taux additionnels sur la production **locale** à l'Article 142 (8)).
- Formalités douanières et régimes économiques particuliers (Direction Générale des Douanes, `douanes.cm`, accessible mais non explorée).
- Confirmation d'une éventuelle offre tarifaire ZLECAf nationale (niveau 2) déposée par le Cameroun.

## Règles d'archivage

Politique de poids adaptée : le Kenya archive des PDF jusqu'à 4,6 Mo tels quels. Le CGI camerounais (8,2 Mo, 968 pages) la dépasse largement ; seul l'extrait des dispositions opérantes est archivé, avec le hash du document source complet conservé pour traçabilité et vérification indépendante.

## État de l'enregistrement

Juridiction CMR : **non** enregistrée dans `SUPPORTED_JURISDICTIONS` (`backend/services/national_legal_calculation_service.py`). Bien que TVA, accises et CAC soient vérifiés sur texte primaire, il manque : (1) le TEC CEMAC pour calculer un `base_cet_rate`, (2) le branchement du CAC comme prélèvement asis sur la TVA plutôt que sur la valeur en douane (le moteur générique ne le permet pas en l'état). ZLECAf : **pas** d'offre nationale encore registrée dans `NATIONAL_OFFER_REGISTRY`.
