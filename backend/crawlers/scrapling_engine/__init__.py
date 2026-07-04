"""
Moteur de crawl Scrapling des tarifs douaniers africains.

Plan : docs/PLAN_SCRAPLING_CRAWLERS.md. Contrat de sortie v2 :
data/crawled/{ISO3}_tariffs.json (taux + dénominations exactes, méthodes de
calcul, formalités {document, autorité}, avantages fiscaux tous régimes).

Modules :
  - normalizer    : brut → contrat v2 (sans perte : texte brut conservé)
  - quality_gate  : verdict PASS/FAIL contre étalon + pivots (Algérie d'abord)
  - runner        : CLI par pays (specs/{iso3}.py, Scrapling)
"""
