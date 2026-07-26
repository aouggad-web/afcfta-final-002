# Guinée-Bissau — collecte vérifiée (UEMOA)

Consultation : 2026-07-26. Corrige une collecte initiale fabriquée (statut `PENDING_OFFICIAL_CONSOLIDATION`, `sha256: pending_collection`, domaine inexistant `impots.gnb` — le vrai ccTLD de la Guinée-Bissau est `.gw`, pas `.gnb`).

## Découverte importante : le taux réel n'est PAS 18%

L'hypothèse d'harmonisation UEMOA (18% partout) supposée par le placeholder est **fausse pour la Guinée-Bissau** : le pays a introduit son IVA (Imposto sobre o Valor Acrescentado) récemment, avec un barème propre.

## Ce qui a été vérifié sur texte primaire

- **IVA taux standard 19%** (importations hors Annexe I) — Código do IVA, approuvé par la Lei nº 4/22 du 25 février 2022, Article 18º-1 : « As taxas do imposto são as seguintes […] para as restantes importações, a taxa é 19%. » Cité verbatim sur la page officielle de l'Alfândegas da Guiné-Bissau (autorité douanière, sous le Ministério da Economia e Finanças), archivée le 2026-07-26 (`alfandegas.mef.gw`).
- **IVA taux réduit 10%** pour les importations listées à l'Annexe I du Code (liste de produits non extraite dans ce cycle).
- **Taux zéro (0%)** sur les exportations — même article.
- **Base taxable** (Article 17º) : valeur en douane + droits/taxes dus (hors IVA lui-même) + frais accessoires (commissions, emballage, transport, assurance).

## Point de vigilance : date d'entrée en vigueur

La loi a été **approuvée en février 2022** mais n'est entrée en vigueur — et n'a commencé à être collectée — que le **1er janvier 2025** (remplaçant l'ancien Imposto Geral sobre Vendas, IGV). Cette date de mise en application est corroborée par plusieurs articles de presse indépendants citant une annonce du Directeur Général des Contributions et Impôts, mais la page d'annonce du Ministère des Finances (`mef.gw`) elle-même était injoignable depuis cet environnement (connexion réinitialisée) — non archivée directement.

## Ce qui n'a PAS été collecté

- Le texte intégral consolidé du Código do IVA (au-delà des articles cités par la page Alfândegas).
- La liste des produits de l'Annexe I (taux réduit 10%).
- Finance Law 2026 / droits d'accises.

## État de l'enregistrement

**Non** enregistrée dans `SUPPORTED_JURISDICTIONS`. **Pas** d'offre ZLECAf dans `NATIONAL_OFFER_REGISTRY`.
