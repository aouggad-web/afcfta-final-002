# Kenya — lacunes de données juridiques

État au 2026-07-24.

## Résultat de la collecte

- 14 sources enregistrées.
- 365 mesures VAT.
- 122 mesures d'excise.
- 24 prélèvements d'importation principaux.
- 62 exemptions/régimes douaniers et 19 formalités.
- 412 correspondances `DIRECT_HS`; 364 lignes nécessitent une validation humaine, dont 2 propositions `MAPPED_HS`.

## Blocages empêchant un calcul juridiquement fiable

1. **EACCMA Amendment Act 2025 — SOURCE_PENDING.** Métadonnées et date d'effet vérifiées sur le portail EAC, mais le PDF direct renvoie HTTP 403 au terminal. Aucun amendement n'a été reconstruit.
2. **Gazettes EAC postérieures au CET de juin 2025.** Les stays of application, duty remissions, corrigenda et mesures propres au Kenya ne sont pas encore exhaustivement intégrés; un droit CET ne doit donc pas être calculé uniquement depuis le PDF de base.
3. **Dates historiques des schedules.** La date de la forme courante est dérivée de la dernière disposition modificative citée lorsque celle-ci est identifiable. Les lignes sans date individuelle certaine restent des instantanés de consolidation et exigent une revue avant calcul rétroactif.
4. **VAT temporaire 2026.** Les trois taux à 8 % issus de l'Act No. 10 of 2026 sont limités à 90 jours. La date de fin est calculée et toute prorogation par Gazette doit être vérifiée avant usage.
5. **Version SH.** Les codes repris littéralement sont sûrs comme texte légal, mais leur version SH exacte doit être confirmée pour les dispositions anciennes.
6. **Descriptions sans code.** Elles sont conservées en `LEGAL_DESCRIPTION`; aucune classification tarifaire automatique ne doit les convertir en taux produit sans revue.
7. **Restrictions sectorielles.** Les permis et restrictions d'importation par organisme (KEBS, AFA, Pharmacy and Poisons Board, vétérinaire, phytosanitaire, etc.) ne sont pas encore exhaustifs.
8. **Jurisprudence et contentieux constitutionnels.** La validité contentieuse éventuelle de chaque prélèvement n'a pas été auditée; le registre reflète les textes publiés et consolidés, non une opinion juridique finale.

## Sources bloquées ou partielles

- Portail EAC : PDF direct EACCMA 2025 bloqué (HTTP 403), page officielle accessible.
- Certaines copies PDF Kenya Law antérieurement téléchargées étaient des rendus courts; les extractions présentes reposent sur les HTML consolidés complets.
- KRA : guide administratif archivé mais taux obsolètes exclus des tables de mesures.
