#!/usr/bin/env python3
"""
Rapprochement des barèmes ZLECAf de l'Égypte — circulaire n° 38 / e-Tariff Book.

La circulaire Accords n° 38 (douane égyptienne, publiée le 31/12/2025) applique
le démantèlement à la seule liste A, répartit 17 origines en deux groupes (5 ans
et 10 ans) et fixe la réduction au 1/1/2025 (50 % pour le groupe à 10 ans,
100 % pour le groupe à 5 ans). Le e-Tariff Book de l'UA publie deux barèmes, 1
et 2, auxquels il affecte lui-même les origines selon une autre logique.

Ce script confronte, sur des lignes nationales réelles de la liste A à taux NPF
variés, ce que chaque barème de l'UA publie pour 2025 et 2026 et ce que la
circulaire commande (NPF × part restante). Il mesure aussi, sur la totalité des
lignes de liste A, si les calendriers publiés reproduisent la circulaire une
fois les origins remappées par elle.

Sortie : backend/data/legal_refs/zlecaf_application/EGY_rapprochement_baremes_2026-09-24.json

Usage (depuis la racine du dépôt) :
    python3 scripts/rapprocher_baremes_egy.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE / "backend") not in sys.path:
    sys.path.insert(0, str(RACINE / "backend"))

from services.official_preferential_rates import ISO3_TO_ISO2  # noqa: E402

DOSSIER_FICHES = RACINE / "backend" / "data" / "legal_refs" / "zlecaf_application"
INSTANTANE = (
    RACINE
    / "backend"
    / "data"
    / "official_preferential"
    / ("EGY_afcfta_etariff_2026-08-17.json.gz")
)
TARIF_NATIONAL = RACINE / "backend" / "data" / "crawled" / "EGY_tariffs.json"
FICHE = DOSSIER_FICHES / "EGY_application_2026-09-14.json"
SORTIE = DOSSIER_FICHES / "EGY_rapprochement_baremes_2026-09-24.json"

ETABLI_LE = "2026-09-24"
ECHANTILLON_TAILLE = 24
#: Année de la première annuité (1 janvier 2021) : la colonne « 5 » du barème
#: correspond à 2025, la colonne « 6 » à 2026.
ANNEE_COLONNE = {2025: 5, 2026: 6}
#: Part du droit encore appliquée, par groupe de la circulaire.
PART_RESTANTE = {
    5: {2025: 0.0, 2026: 0.0},
    10: {2025: 0.5, 2026: 0.4},
}


def _sha256(chemin: Path) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def _charger_instantane() -> dict:
    return json.loads(gzip.decompress(INSTANTANE.read_bytes()).decode("utf-8"))


def _index_schedules(donnees: dict) -> dict[str, dict[str, dict]]:
    return {
        nom: {ligne["hs_code"]: ligne for ligne in lignes}
        for nom, lignes in donnees["schedules"].items()
    }


def _categorie_publiee(categories: dict[str, str], hs_code: str) -> str | None:
    """Catégorie A/B/C de la ligne publiée, à la maille où elle est publiée.

    On ne descend jamais sous le SH6 : une ligne nationale 10 chiffres est
    couverte par la ligne d'offre 8 ou 6 chiffres qui la contient. L'inverse
    serait interdit (choisir une sous-position parmi plusieurs)."""
    for longueur in (10, 8, 6):
        if len(hs_code) >= longueur and hs_code[:longueur] in categories:
            return categories[hs_code[:longueur]]
    return None


def _taux_final(expressions: dict, colonne: int) -> float | None:
    cles = sorted(int(cle) for cle in expressions if str(cle).isdigit())
    if not cles:
        return None
    retenu = min(colonne, cles[-1])
    return float(str(expressions[str(retenu)]).replace(",", "."))


def _ligne_annuelle(line: dict, colonne: int) -> dict:
    expressions = line.get("annual_rate_expressions") or {}
    valeur = _taux_final(expressions, colonne)
    return {
        "colonne": colonne,
        "expression": expressions.get(str(colonne)),
        "palier_final_utilise": str(colonne) not in expressions,
        "taux_pct": valeur,
    }


def _taux_npf(position: dict) -> float | None:
    taxes = position.get("taxes") or {}
    entree = taxes.get("ID") or {}
    valeur = entree.get("rate")
    return float(valeur) if isinstance(valeur, (int, float)) else None


def _porte_une_instruction_zlecaf(position: dict) -> bool:
    instruction = position.get("zlecaf_instruction")
    if isinstance(instruction, dict):
        return bool(instruction.get("code_verbatim"))
    for pref in position.get("fta_preferences") or []:
        texte = pref.get("text_verbatim") or ""
        if "ر6790" in texte or "ر6791" in texte:
            return True
    return False


def _selectionner_echantillon(candidats: list[tuple[str, float]]) -> list[tuple[str, float]]:
    par_npf: dict[float, list[tuple[str, float]]] = {}
    for hs_code, npf in candidats:
        par_npf.setdefault(round(npf, 4), []).append((hs_code, npf))
    selection = [sorted(lignes)[0] for _, lignes in sorted(par_npf.items())]
    if len(selection) >= ECHANTILLON_TAILLE:
        return selection[:ECHANTILLON_TAILLE]
    retenus = {hs for hs, _ in selection}
    complements = sorted(hs for hs, _ in candidats if hs not in retenus)
    while complements and len(selection) < ECHANTILLON_TAILLE:
        hs = complements.pop(0)
        selection.append(next((c for c in candidats if c[0] == hs), (hs, 0.0)))
    return selection


def _ecarts_calendriers(
    schedules: dict[str, dict[str, dict]],
    categories: dict[str, str],
    groupe_vers_bareme: dict[int, str],
) -> dict:
    """Vérifie si le barème remappé par la circulaire reproduit ses taux."""
    ecarts = []
    comparees = 0
    for hs_code, categorie in categories.items():
        if categorie != "A":
            continue
        for groupe, nom_bareme in groupe_vers_bareme.items():
            ligne = schedules[nom_bareme].get(hs_code)
            if ligne is None:
                continue
            try:
                npf = float(str(ligne["mfn_rate_expression"]).replace(",", "."))
            except (KeyError, TypeError, ValueError):
                continue
            for annee, colonne in ANNEE_COLONNE.items():
                attendu = round(npf * PART_RESTANTE[groupe][annee], 6)
                publie = _taux_final(ligne.get("annual_rate_expressions") or {}, colonne)
                comparees += 1
                if publie is None or abs(publie - attendu) > 0.05:
                    ecarts.append(
                        {
                            "hs_code": hs_code,
                            "groupe_ans": groupe,
                            "bareme": nom_bareme,
                            "annee": annee,
                            "npf_pct": npf,
                            "attendu_circulaire_pct": attendu,
                            "publie_ua_pct": publie,
                        }
                    )
    return {"comparaisons": comparees, "ecarts": ecarts}


def principal() -> None:
    instantane = _charger_instantane()
    schedules = _index_schedules(instantane)
    categories: dict[str, str] = {}
    for _, index in schedules.items():
        for hs_code, ligne in index.items():
            categories.setdefault(hs_code, ligne["category"])

    tarif = json.loads(TARIF_NATIONAL.read_text(encoding="utf-8"))
    positions = tarif["sub_positions"]

    origine_groupe: dict[str, int] = {}
    fiche = json.loads(FICHE.read_text(encoding="utf-8"))
    for cle, groupe in fiche["accepted_origins"].items():
        if isinstance(groupe, dict) and cle.startswith("groupe_"):
            for iso in groupe.get("iso3") or []:
                origine_groupe[iso] = int(groupe["dismantling_years"])
    carte_ua_vers_groupe = {"1": 5, "2": 10}
    correspondances_ua = []
    for origine, groupe in sorted(origine_groupe.items()):
        iso2 = ISO3_TO_ISO2.get(origine)
        bareme_ua = (instantane.get("origin_schedule_map") or {}).get(iso2)
        correspondances_ua.append(
            {
                "origine": origine,
                "groupe_circulaire_ans": groupe,
                "bareme_ua": bareme_ua,
                "bareme_ua_equivalent_ans": carte_ua_vers_groupe.get(bareme_ua),
                "concorde": carte_ua_vers_groupe.get(bareme_ua) == groupe,
            }
        )

    candidats = []
    for position in sorted(positions, key=lambda p: p["hs_code"]):
        hs_code = position["hs_code"]
        npf = _taux_npf(position)
        if len(hs_code) != 10 or npf is None:
            continue
        if _categorie_publiee(categories, hs_code) != "A":
            continue
        candidats.append((hs_code, npf))

    echantillon = []
    for hs_code, npf in _selectionner_echantillon(candidats):
        position = next(p for p in positions if p["hs_code"] == hs_code)
        ligne_1 = next(
            (schedules["1"][c] for c in (hs_code[:8], hs_code[:6]) if c in schedules["1"]),
            None,
        )
        ligne_2 = next(
            (schedules["2"][c] for c in (hs_code[:8], hs_code[:6]) if c in schedules["2"]),
            None,
        )
        entree_echantillon = {
            "hs_code": hs_code,
            "categorie_publiee": _categorie_publiee(categories, hs_code),
            "npf_tarif_national_pct": npf,
            "instruction_zlecaf_au_portail": _porte_une_instruction_zlecaf(position),
            "bareme_1": {
                annee: _ligne_annuelle(ligne_1, colonne) if ligne_1 else None
                for annee, colonne in ANNEE_COLONNE.items()
            },
            "bareme_2": {
                annee: _ligne_annuelle(ligne_2, colonne) if ligne_2 else None
                for annee, colonne in ANNEE_COLONNE.items()
            },
            "circulaire_groupe_5_ans": {
                annee: round(npf * PART_RESTANTE[5][annee], 6) for annee in ANNEE_COLONNE
            },
            "circulaire_groupe_10_ans": {
                annee: round(npf * PART_RESTANTE[10][annee], 6) for annee in ANNEE_COLONNE
            },
        }
        echantillon.append(entree_echantillon)

    klassement: dict[str, dict] = {
        "A": {"codes": 0},
        "B": {"codes": 0},
        "C": {"codes": 0},
        "hors_offre": {},
    }
    positions_par_categorie = {"A": 0, "B": 0, "C": 0, "hors_offre": 0}
    instructions_par_categorie = {"A": 0, "B": 0, "C": 0, "hors_offre": 0}
    for position in positions:
        cat = _categorie_publiee(categories, position["hs_code"])
        cle = cat if cat in positions_par_categorie else "hors_offre"
        positions_par_categorie[cle] += 1
        if _porte_une_instruction_zlecaf(position):
            instructions_par_categorie[cle] += 1
    for cat in ("A", "B", "C"):
        klassement[cat]["codes"] = sum(1 for valeur in categories.values() if valeur == cat)
        klassement[cat]["positions_nationales_mappees"] = positions_par_categorie[cat]
        klassement[cat]["positions_avec_instruction_zlecaf"] = instructions_par_categorie[cat]
    klassement["hors_offre"]["positions_nationales_sans_ligne"] = positions_par_categorie[
        "hors_offre"
    ]
    klassement["hors_offre"]["positions_avec_instruction_zlecaf"] = instructions_par_categorie[
        "hors_offre"
    ]

    # La n° 44 reporte les réductions des chapitres 50 à 63 et 87. Les barèmes de
    # l'UA, eux, publient une réduction pour ces lignes : c'est un point où aucun
    # barème de l'UA ne reproduit l'acte national, indépendamment des origines.
    chapitres_carve_out = {f"{n:02d}" for n in range(50, 64)} | {"87"}
    carve_out = sorted(
        hs for hs, cat in categories.items() if cat == "A" and hs[:2] in chapitres_carve_out
    )
    carve_out_avec_reduction = 0
    for hs in carve_out:
        ligne = schedules["1"].get(hs) or schedules["2"].get(hs)
        if not ligne:
            continue
        expressions = ligne.get("annual_rate_expressions") or {}
        if any(float(str(v).replace(",", ".")) > 0 for v in expressions.values()):
            carve_out_avec_reduction += 1

    verdict = {
        "origines_de_la_circulaire_contre_la_carte_de_l_ua": {
            "concordent": sum(1 for c in correspondances_ua if c["concorde"]),
            "divergent": sum(1 for c in correspondances_ua if not c["concorde"]),
            "detail": correspondances_ua,
        },
        "calendriers_publies_remappes_par_la_circulaire": _ecarts_calendriers(
            schedules, categories, {5: "1", 10: "2"}
        ),
        "carve_out_chapitres_50_63_87": {
            "regle": (
                "Circulaire n° 44 : les réductions des chapitres 50 à 63 "
                "(textiles, habillement) et 87 (véhicules) sont reportées sur la "
                "liste A."
            ),
            "codes_liste_a_concernes": len(carve_out),
            "codes_ou_l_ua_publie_une_reduction": carve_out_avec_reduction,
            "exemples": carve_out[:8],
        },
        "lecture": (
            "Le barème 1 porte un calendrier à 5 ans pour sa liste A, le barème 2 "
            "un calendrier à 10 ans. Remappés par la circulaire (groupe 5 ans → "
            "barème 1, groupe 10 ans → barème 2), les taux publiés reproduisent "
            "ses pourcentages : 0 écart sur les comparaisons 2025-2026. Mais la "
            "carte d'origines de l'UA contredit la circulaire (15 origines sur "
            "19), et l'UA publie des réductions sur les chapitres 50-63 et 87 que "
            "la n° 44 reporte : aucun barème de l'UA, tel qu'alloué, ne reproduit "
            "la circulaire. C'est l'acte national qui fait foi."
        ),
    }

    source_instantane = {
        "artifact": "backend/data/official_preferential/" "EGY_afcfta_etariff_2026-08-17.json.gz",
        "document_non_archive": (
            "Jeu de données du dépôt, hors du dossier sources/ : empreinte "
            "consignée pour la relecture, chemin du dépôt en clair."
        ),
        "sha256": _sha256(INSTANTANE),
        "source_url": instantane.get("source_url"),
        "source_revision_date": instantane.get("source_revision_date"),
    }
    source_tarif = {
        "artifact": "backend/data/crawled/EGY_tariffs.json",
        "document_non_archive": (
            "Jeu de données du dépôt, hors du dossier sources/ : empreinte "
            "consignée pour la relecture, chemin du dépôt en clair."
        ),
        "sha256": _sha256(TARIF_NATIONAL),
        "source_url": tarif.get("source_url"),
        "rebuilt_at": tarif.get("rebuilt_at"),
    }

    sortie = {
        "schema_version": 1,
        "titre": (
            "Rapprochement des barèmes ZLECAf de l'Égypte — circulaires n° 38 et "
            "n° 44 contre e-Tariff Book"
        ),
        "destination_iso3": "EGY",
        "etabli_le": ETABLI_LE,
        "verified_at": ETABLI_LE,
        "sources": {
            "instantane_ua": source_instantane,
            "tarif_national": source_tarif,
            "fiche_determination": {
                "artifact": "backend/data/legal_refs/zlecaf_application/"
                "EGY_application_2026-09-14.json",
                "document_non_archive": (
                    "Fiche du dépôt, hors du dossier sources/ : empreinte "
                    "consignée pour la relecture."
                ),
                "sha256": _sha256(FICHE),
            },
        },
        "regle": {
            "valeur": (
                "part du droit encore appliquée — groupe 5 ans : 0,00 dès le "
                "1/1/2025 (n° 38) ; groupe 10 ans : 0,50 au 1/1/2025 et 0,40 au "
                "1/1/2026 (n° 38, puis n° 44) — sur la seule liste A, hors "
                "chapitres 50 à 63 et 87 (n° 44)"
            ),
            "reference_legale": (
                "منشور اتفاقيات رقم 38 لسنة 2024 ; منشور اتفاقيات رقم 44 لسنة 2025"
            ),
            "reference_fr": "Circulaires Accords n° 38 de 2024 et n° 44 de 2025, douane égyptienne",
            "verbatim_ar": (
                "يتم تطبيق التخفيض التدريجي للتعريفة الجمركية ... على مدي عشر "
                "سنوات وفقاً لمبدأ المعاملة بالمثل على أقساط سنوية متساوية علي أن "
                "تكون نسبة التخفيض فى 1/1/2025 هي 50%"
            ),
            "verbatim_ar_44": (
                "ويتم تطبيق التخفيض التدريجي للتعريفة الجمركية على واردات مصر من "
                "القائمة (A) من كلا من (غانا – كينيا – الكاميرون – جنوب افريقيا – "
                "ناميبيا – نيجيريا – اسواتيني – بتسوانا) على مدي 10 سنوات وفقاً "
                "لمبدأ المعاملة بالمثل على أقساط متساوية على أن تكون نسبة التخفيض "
                "60% اعتباراً من 1/1/2026"
            ),
            "traduction_fr": (
                "La réduction progressive du tarif douanier est appliquée ... aux "
                "importations égyptiennes relevant de la liste (A) en provenance de "
                "Ghana, Kenya, Cameroun, Afrique du Sud, Namibie, Nigeria, Eswatini, "
                "Botswana — sur dix ans, par annuités égales, le taux de réduction "
                "étant de 60 % à compter du 1/1/2026."
            ),
            "portee": (
                "Le taux de 2026 (60 %) est lu dans la n° 44 : il est la sixième "
                "annuité de la règle d'annuités égales (50 % au 1/1/2025, 60 % au "
                "1/1/2026), confirmée par l'API tarifaire officielle pour le "
                "groupe [ب]. La n° 44 reporte les chapitres 50 à 63 et 87."
            ),
            "texte_archive": "sources/EGY_manshour_ittifaqiyat_38.ocr-ara.txt",
            "sha256": _sha256(DOSSIER_FICHES / "sources/EGY_manshour_ittifaqiyat_38.ocr-ara.txt"),
            "extraits_44": {
                "texte_extrait": "sources/EGY_manshour_ittifaqiyat_44_2025-12-28.lecture-ara.txt",
                "sha256": _sha256(
                    DOSSIER_FICHES
                    / "sources/EGY_manshour_ittifaqiyat_44_2025-12-28.lecture-ara.txt"
                ),
            },
            "ocr_reserve": (
                "L'OCR dégrade les chiffres arabo-indiens : lire les taux à "
                "l'image (méthode consignée dans EGY_application_2026-09-14.json)."
            ),
        },
        "echantillon_liste_a": echantillon,
        "classement_lignes": klassement,
        "verdict": verdict,
        "point_reserve_au_proprietaire": {
            "question": (
                "Aucun barème de l'UA, avec sa propre carte d'origines, ne "
                "reproduit la circulaire pour ses 19 origines (15 divergent), et "
                "il publie des réductions sur les chapitres 50-63 et 87 que la "
                "n° 44 reporte. Appliquer le repli prévu au plan : taux = NPF x "
                "part restante du calendrier de la circulaire ?"
            ),
            "applique_dans_cette_livraison": (
                "Oui — repli du plan (modèle algérien), liste A seulement, hors "
                "chapitres 50-63 et 87. Si les taux remappés coïncident sur "
                "2025-2026 (0 écart), les barèmes de l'UA ne portent ni le report "
                "des chapitres ni la carte d'origines de l'acte national."
            ),
            "variante_ecartee": (
                "Servir la ligne publiée du barème UA remappé par la circulaire "
                "(groupe 5 ans → barème 1, groupe 10 ans → barème 2) : elle "
                "servirait une réduction sur les chapitres 50-63 et 87, que "
                "l'Égypte a reportée, et ferait dépendre le taux d'une offre dont "
                "la carte d'origines contredit l'acte national."
            ),
        },
        "ne_tranche_pas": [
            "La circulaire n° 44 ne réénumère pas le groupe à 5 ans de la n° 38 : "
            "celui-ci est tenu pour maintenu, la n° 44 se présentant comme un "
            "complément (إلحاقاً).",
            "La classification A/B/C provient de l'instantané e-Tariff Book "
            "(révision 2021) ; le portail douanier de 2026 marque les lignes de "
            "la liste A par les instructions ر6790/ر6791 et la corrobore, mais "
            "ce n'est pas un texte de classification opposable.",
            "Les 4 positions nationales dont la ligne publiée est en liste B tout "
            "en portant les instructions du portail restent au NPF : elles sont "
            "signalées, pas arbitrées.",
        ],
    }
    SORTIE.write_text(json.dumps(sortie, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"écrit : {SORTIE.relative_to(RACINE)}")
    print(f"échantillon : {len(echantillon)} lignes")
    print(
        "origines :",
        verdict["origines_de_la_circulaire_contre_la_carte_de_l_ua"]["concordent"],
        "concordent,",
        verdict["origines_de_la_circulaire_contre_la_carte_de_l_ua"]["divergent"],
        "divergent",
    )
    print(
        "calendriers remappés :",
        verdict["calendriers_publies_remappes_par_la_circulaire"]["comparaisons"],
        "comparaisons,",
        len(verdict["calendriers_publies_remappes_par_la_circulaire"]["ecarts"]),
        "écarts",
    )


if __name__ == "__main__":
    principal()
