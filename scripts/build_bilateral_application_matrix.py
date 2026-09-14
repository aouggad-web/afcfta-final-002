#!/usr/bin/env python3
"""Tableau de l'état d'application de la ZLECAf entre pays, couple par couple.

La ratification est continentale, l'application est bilatérale : un pays qui a
ratifié n'accorde pas pour autant la préférence à tous les autres. Chaque
destination notifie sa propre liste d'origines admises, au titre de la
réciprocité. Répondre « la ZLECAf s'applique » sans dire entre qui et qui
n'aide aucun opérateur.

Ce script généralise à toutes les destinations la méthode établie pour le
Maroc :

  1. un acte national d'application, lu en source primaire ;
  2. la liste nominative des origines que cet acte admet ;
  3. la confrontation à la carte continentale du e-Tariff Book de l'UA.

Chaque liste est lue à sa source d'autorité dans le dépôt — module de service
ou fiche de détermination. Aucune n'est recopiée ici : une liste recopiée
finit par diverger du texte qui l'établit.

Une case n'est jamais remplie par défaut. L'absence de recherche se lit
DESTINATION_NON_ETABLIE et ne se confond pas avec un refus de préférence.

Sorties : reports/ETAT_APPLICATION_BILATERAL.json (données)
          docs/ETAT_APPLICATION_BILATERAL.md      (lecture)
"""

from __future__ import annotations

import json
import sys
from datetime import date, timezone, datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "backend"))

FICHES = RACINE / "backend" / "data" / "legal_refs" / "zlecaf_application"
SORTIE = RACINE / "reports" / "ETAT_APPLICATION_BILATERAL.json"
SORTIE_MD = RACINE / "docs" / "ETAT_APPLICATION_BILATERAL.md"
CHANTIER = FICHES / "chantier_collecte_2026-09-14.json"

NOMS = {
    "DZA": "Algérie", "EGY": "Égypte", "KEN": "Kenya",
    "MAR": "Maroc", "TUN": "Tunisie", "ZAF": "Afrique du Sud",
}
SYMBOLES = {
    "ACCORDEE": "✅",
    "NON_ACCORDEE": "❌",
    "MEME_PAYS": "—",
    "ORIGINE_NON_RATIFIANTE": "🚫",
    "DESTINATION_NON_ETABLIE": "·",
}

# --- États d'une case ---------------------------------------------------
ACCORDEE = "ACCORDEE"
NON_ACCORDEE = "NON_ACCORDEE"
ORIGINE_NON_RATIFIANTE = "ORIGINE_NON_RATIFIANTE"
DESTINATION_NON_ETABLIE = "DESTINATION_NON_ETABLIE"
MEME_PAYS = "MEME_PAYS"

LEGENDE = {
    ACCORDEE: (
        "L'acte national de la destination nomme cette origine parmi celles "
        "qui bénéficient du tarif ZLECAf."
    ),
    NON_ACCORDEE: (
        "La destination publie une liste nominative vérifiée et cette origine "
        "n'y figure pas : la préférence ne lui est pas accordée à ce jour."
    ),
    ORIGINE_NON_RATIFIANTE: (
        "L'origine n'a pas déposé ses instruments de ratification : aucune "
        "préférence ZLECAf ne peut lui être accordée, quelle que soit la "
        "destination."
    ),
    DESTINATION_NON_ETABLIE: (
        "Aucune liste d'origines admises n'a été vérifiée pour cette "
        "destination. Absence de recherche, PAS un refus de préférence."
    ),
    MEME_PAYS: "Origine et destination confondues.",
}


def _fiche(nom: str) -> dict:
    return json.loads((FICHES / nom).read_text(encoding="utf-8"))


def listes_verifiees() -> dict[str, dict]:
    """Les destinations dont la liste d'origines admises est établie.

    Chaque entrée porte : les origines, le rythme de démantèlement quand la
    source le distingue, l'instrument qui l'établit et le niveau de preuve.
    """
    from services.zlecaf_implementation_registry import RECORDS
    from services.zlecaf_schedule_dza import ACTIVE_PARTNERS
    from services.zlecaf_schedule_zaf import ACTIVE_PARTNERS_ZAF

    listes: dict[str, dict] = {}

    # --- Maroc : circulaire ADII, deux rythmes (P1 5 ans / P2 10 ans) -----
    mar = _fiche("MAR_application_2026-09-13.json")
    rythmes = {}
    for cle in ("P1", "P2"):
        groupe = mar["accepted_origins"][cle]
        for iso in groupe["iso3"]:
            rythmes[iso] = f"{groupe['dismantling_years']} ans"
    listes["MAR"] = {
        "origines": rythmes,
        "instrument": f"Circulaire ADII n° {mar['instrument']['id']} du {mar['instrument']['date']}",
        "preuve": "primaire — circulaire lue intégralement, SHA-256 consigné",
        "fiche": "MAR_application_2026-09-13.json",
    }

    # --- Égypte : circulaire Accords n° 38, deux groupes ------------------
    egy = _fiche("EGY_application_2026-09-14.json")
    rythmes = {}
    for cle in ("groupe_10_ans", "groupe_5_ans"):
        groupe = egy["accepted_origins"][cle]
        for iso in groupe["iso3"]:
            rythmes[iso] = f"{groupe['dismantling_years']} ans"
    listes["EGY"] = {
        "origines": rythmes,
        "instrument": egy["instrument"].get("title") or egy["instrument"].get("id"),
        "preuve": "primaire — PDF officiels douane égyptienne, OCR arabe",
        "fiche": "EGY_application_2026-09-14.json",
    }

    # --- Algérie : liste OPÉRATIVE d'admission, distincte du calendrier ---
    # La fiche algérienne avertit que confondre les treize pays du calendrier
    # de réciprocité avec les neuf admis accorderait la préférence à des pays
    # qui n'y ont pas droit. On prend la liste d'admission.
    listes["DZA"] = {
        "origines": {iso: None for iso in sorted(ACTIVE_PARTNERS)},
        "instrument": "Circulaire 482/DGD/SP/D.042/24 du 22 octobre 2024",
        "preuve": "primaire — texte intégral archivé",
        "fiche": "DZA_application_2026-09-14.json",
    }

    # --- Kenya : décision EAC + liste KRA --------------------------------
    ken = RECORDS["KEN"]
    listes["KEN"] = {
        "origines": {iso: None for iso in sorted(ken.accepted_origins)},
        "instrument": ken.instrument_id,
        "preuve": "primaire (revue antérieure du dépôt)",
        "fiche": None,
    }

    # --- Tunisie : origines publiées au tarif, sens du taux non tranché ---
    tun = _fiche("TUN_application_2026-09-13.json")
    listes["TUN"] = {
        "origines": {e["iso3"]: None for e in tun["accepted_origins"]["detail"]},
        "instrument": "Tarif Web 2026, douane.gov.tn",
        "preuve": "primaire — portail tarifaire officiel scellé dans le dépôt",
        "fiche": "TUN_application_2026-09-13.json",
        "reserve": (
            "Les origines sont établies, mais le SENS du taux préférentiel "
            "publié ne l'est pas (40 % affiché contre 36 % de NPF). Une case "
            "ACCORDEE dit ici que la Tunisie sert cette origine sous régime "
            "ZLECAf, pas quel droit en résulte."
        ),
    }

    # --- Afrique du Sud : partenaires actifs hors SACU/SADC ---------------
    listes["ZAF"] = {
        "origines": {iso: None for iso in sorted(ACTIVE_PARTNERS_ZAF)},
        "instrument": "« Update on the AfCFTA », the dtic / SARS, newsletter mars 2026",
        "preuve": "officielle — publication gouvernementale, non un acte réglementaire",
        "fiche": None,
        "reserve": (
            "Les membres de la SACU et de la SADC sont volontairement absents : "
            "l'Afrique du Sud échange avec eux sous ces régimes, pas sous la "
            "ZLECAf. Leur absence n'est donc pas un refus de préférence."
        ),
    }
    return listes


def construire() -> dict:
    from services.zlecaf_membership_status import (
        NOT_SIGNED,
        SIGNED_NOT_RATIFIED,
        ratification_status,
        STATUS_RATIFIED,
    )

    etat = json.loads(
        (FICHES / "etat_application_54_pays_2026-09-13.json").read_text(encoding="utf-8")
    )
    tous = sorted(etat["pays"])
    listes = listes_verifiees()

    # Une destination peut nommer, dans son acte, une origine que le registre
    # continental dit non ratifiante. Les deux sont primaires : le silence
    # serait le pire traitement. La ratification prime pour la case — aucune
    # préférence n'est accordée — mais la contradiction est publiée.
    contradictions: list[dict] = []

    couples: dict[str, dict[str, dict]] = {}
    for destination in tous:
        ligne: dict[str, dict] = {}
        liste = listes.get(destination)
        for origine in tous:
            if origine == destination:
                ligne[origine] = {"etat": MEME_PAYS}
                continue
            if ratification_status(origine) != STATUS_RATIFIED:
                motif = (
                    "non signataire" if origine in NOT_SIGNED
                    else "signataire, ratification non déposée"
                )
                case = {"etat": ORIGINE_NON_RATIFIANTE, "motif": motif}
                if liste is not None and origine in liste["origines"]:
                    case["contradiction"] = (
                        f"{liste['instrument']} nomme cette origine, que le "
                        f"registre continental donne pour {motif}. Aucune "
                        "préférence n'est accordée ; la divergence est à "
                        "instruire."
                    )
                    contradictions.append({
                        "destination": destination,
                        "origine": origine,
                        "instrument": liste["instrument"],
                        "statut_continental": motif,
                    })
                ligne[origine] = case
                continue
            if liste is None:
                ligne[origine] = {"etat": DESTINATION_NON_ETABLIE}
                continue
            if origine in liste["origines"]:
                case = {"etat": ACCORDEE, "fondement": liste["instrument"]}
                if liste["origines"][origine]:
                    case["demantelement"] = liste["origines"][origine]
                ligne[origine] = case
            else:
                ligne[origine] = {"etat": NON_ACCORDEE, "fondement": liste["instrument"]}
        couples[destination] = ligne

    # --- Réciprocité : ce que le croisement révèle et qu'aucune liste seule
    #     ne dit. L'accord la pose en principe ; les listes la démentent
    #     parfois.
    etablies = sorted(listes)
    reciproques, asymetries = [], []
    for i, a in enumerate(etablies):
        for b in etablies[i + 1:]:
            a_vers_b = couples[a][b]["etat"] == ACCORDEE
            b_vers_a = couples[b][a]["etat"] == ACCORDEE
            if a_vers_b and b_vers_a:
                reciproques.append(f"{a}<->{b}")
            elif a_vers_b != b_vers_a:
                donneur, receveur = (a, b) if a_vers_b else (b, a)
                asymetries.append({
                    "accorde_par": donneur,
                    "non_accorde_par": receveur,
                    "lecture": (
                        f"{donneur} admet {receveur} à son tarif ZLECAf, "
                        f"{receveur} n'admet pas {donneur}."
                    ),
                })

    compte: dict[str, int] = {}
    for ligne in couples.values():
        for case in ligne.values():
            compte[case["etat"]] = compte.get(case["etat"], 0) + 1

    total = len(tous) * len(tous)
    return {
        "schema_version": 1,
        "titre": "État d'application de la ZLECAf entre pays, couple par couple",
        "genere_le": date.today().isoformat(),
        "genere_par": "scripts/build_bilateral_application_matrix.py",
        "avertissement": (
            "La ratification est continentale, l'application est bilatérale. "
            "Une case ACCORDEE atteste que l'acte national de la destination "
            "nomme cette origine ; elle ne dispense ni de la preuve d'origine "
            "ZLECAf ni de la vérification en douane."
        ),
        "methode": (
            "Trois conditions, dans cet ordre : acte national d'application lu "
            "en source primaire ; liste nominative des origines qu'il admet ; "
            "confrontation à la carte continentale du e-Tariff Book. Les "
            "listes sont lues à leur source d'autorité dans le dépôt, jamais "
            "recopiées."
        ),
        "legende": LEGENDE,
        "pays_couverts": len(tous),
        "couples_possibles": total,
        "destinations_etablies": {
            iso: {
                "origines_admises": len(liste["origines"]),
                "instrument": liste["instrument"],
                "niveau_de_preuve": liste["preuve"],
                "fiche": liste["fiche"],
                **({"reserve": liste["reserve"]} if liste.get("reserve") else {}),
            }
            for iso, liste in sorted(listes.items())
        },
        "destinations_non_etablies": sorted(set(tous) - set(listes)),
        "repartition_des_couples": dict(sorted(compte.items())),
        "couverture_pct": round(
            100 * sum(v for k, v in compte.items() if k in (ACCORDEE, NON_ACCORDEE)) / total, 2
        ),
        "contradictions_ratification": {
            "note": (
                "Origines nommées par l'acte d'une destination alors que le "
                "registre continental les donne pour non ratifiantes. Aucune "
                "préférence n'est accordée dans ce cas ; la case le dit et la "
                "divergence entre deux sources primaires reste visible."
            ),
            "cas": contradictions,
        },
        "reciprocite": {
            "note": (
                "Croiser les listes vérifiées met la réciprocité à l'épreuve. "
                "Une asymétrie n'est pas nécessairement une faute : une liste "
                "peut simplement être plus ancienne que l'autre."
            ),
            "confirmees": reciproques,
            "asymetries": asymetries,
        },
        "chantier_de_collecte": (
            json.loads(CHANTIER.read_text(encoding="utf-8")) if CHANTIER.exists() else None
        ),
        "couples": couples,
    }


def rendre_markdown(r: dict) -> str:
    """Le même contenu, en tableau lisible. Aucune donnée n'est recalculée ici."""
    etablies = sorted(r["destinations_etablies"])
    L: list[str] = []
    A = L.append

    A("# État d'application de la ZLECAf entre pays\n")
    A("> Généré par `scripts/build_bilateral_application_matrix.py` — ne pas éditer à la main.")
    A(f"> Données : `reports/ETAT_APPLICATION_BILATERAL.json`, générées le {r['genere_le']}.\n")

    A("## Ce que ce tableau répond\n")
    A("Un opérateur ne demande pas « la ZLECAf est-elle en vigueur ? » mais « **puis-je")
    A("l'invoquer, moi, sur ce flux-là ?** ». La ratification est continentale, l'application")
    A("est bilatérale : chaque destination notifie sa propre liste d'origines admises, au")
    A("titre de la réciprocité. Le sens du flux change donc le droit.\n")

    A("## Ce qui est établi, et ce qui ne l'est pas\n")
    A("| | |\n|---|---|")
    A(f"| Pays couverts | {r['pays_couverts']} |")
    A(f"| Couples possibles | {r['couples_possibles']} |")
    A(f"| Destinations à liste vérifiée | **{len(etablies)}** |")
    A(f"| Couples renseignés | **{r['couverture_pct']} %** |\n")

    A("| État | Couples | Sens |\n|---|---:|---|")
    for etat, n in r["repartition_des_couples"].items():
        A(f"| `{etat}` | {n} | {r['legende'][etat]} |")
    A("")
    non_etablis = r["repartition_des_couples"].get(DESTINATION_NON_ETABLIE, 0)
    A(f"Les {non_etablis} couples `DESTINATION_NON_ETABLIE` sont le déficit d'information que")
    A("ce travail vise à combler. Ils ne signifient **pas** qu'il n'y a pas de préférence :")
    A("ils signifient que personne ne l'a vérifié. Les afficher comme tels, plutôt que de les")
    A("remplir par défaut, est le seul traitement honnête.\n")

    A(f"## Les {len(etablies)} destinations établies\n")
    A("| Destination | Origines admises | Instrument | Niveau de preuve |\n|---|---:|---|---|")
    for iso in etablies:
        d = r["destinations_etablies"][iso]
        A(f"| **{NOMS.get(iso, iso)}** ({iso}) | {d['origines_admises']} | "
          f"{d['instrument']} | {d['niveau_de_preuve']} |")
    A("")
    for iso in etablies:
        reserve = r["destinations_etablies"][iso].get("reserve")
        if reserve:
            A(f"**Réserve — {NOMS.get(iso, iso)}** : {reserve}\n")

    A("## Le tableau, entre destinations établies\n")
    A("Lecture : la **ligne** est le pays d'importation, la **colonne** le pays d'origine.\n")
    A("| Destination \\ Origine | " + " | ".join(NOMS.get(o, o) for o in etablies) + " |")
    A("|---|" + "---|" * len(etablies))
    for dest in etablies:
        cases = []
        for org in etablies:
            case = r["couples"][dest][org]
            texte = SYMBOLES[case["etat"]]
            if case.get("demantelement"):
                texte += f" {case['demantelement']}"
            cases.append(texte)
        A(f"| **{NOMS.get(dest, dest)}** | " + " | ".join(cases) + " |")
    A("")
    A("✅ préférence accordée · ❌ origine absente de la liste vérifiée · — même pays\n")

    A("## Ce que le croisement révèle\n")
    confirmees = r["reciprocite"]["confirmees"]
    A(f"**{len(confirmees)} réciprocités confirmées** — les deux sens sont établis :\n")
    for paire in confirmees:
        a, b = paire.split("<->")
        A(f"- {NOMS.get(a, a)} ↔ {NOMS.get(b, b)}")
    A("")
    asymetries = r["reciprocite"]["asymetries"]
    A(f"**{len(asymetries)} asymétries** — un sens accorde, l'autre non :\n")
    for a in asymetries:
        A(f"- **{NOMS.get(a['accorde_par'], a['accorde_par'])} → "
          f"{NOMS.get(a['non_accorde_par'], a['non_accorde_par'])}** : {a['lecture']}")
    A("")

    # Le motif dominant, compté et non affirmé : le lecteur doit pouvoir le
    # recalculer depuis le tableau ci-dessus.
    receveurs: dict[str, int] = {}
    for a in asymetries:
        receveurs[a["non_accorde_par"]] = receveurs.get(a["non_accorde_par"], 0) + 1
    if receveurs:
        principal, combien = max(receveurs.items(), key=lambda kv: kv[1])
        if combien > 1:
            A(f"{NOMS.get(principal, principal)} est le receveur de {combien} de ces "
              f"{len(asymetries)} asymétries : ces pays l'admettent à leur tarif ZLECAf,")
            A("sa propre liste ne les admet pas. Un exportateur dans ce sens peut invoquer")
            A("la ZLECAf ; dans le sens inverse, en l'état des listes vérifiées, non.\n")
    A("Une asymétrie n'est pas nécessairement une faute : une liste peut simplement être")
    A("plus ancienne que l'autre. Elle signale où regarder ensuite.\n")

    cas = r["contradictions_ratification"]["cas"]
    A("## Contradictions entre sources primaires\n")
    if cas:
        A(r["contradictions_ratification"]["note"] + "\n")
        A("| Destination | Origine | Instrument | Statut continental |\n|---|---|---|---|")
        for c in cas:
            A(f"| {c['destination']} | {c['origine']} | {c['instrument']} | "
              f"{c['statut_continental']} |")
    else:
        A("Aucune : aucun acte national vérifié ne nomme une origine que le registre")
        A("continental donne pour non ratifiante.")
    A("")

    chantier = r.get("chantier_de_collecte")
    if chantier:
        A("## Ce qu'il reste à collecter\n")
        A(chantier["constat_de_methode"]["enonce"] + "\n")
        A(chantier["constat_de_methode"]["consequence"] + "\n")
        A("| Pays | Statut | Ce qui manque | Document à obtenir |\n|---|---|---|---|")
        for iso, d in chantier["pays"].items():
            A(f"| **{iso}** | `{d['statut']}` | {d['manque']} | {d['document_cible']} |")
        A("")
        prepare = chantier["ce_que_ce_chantier_prepare"]
        A(f"**Preuve recherchée** — {prepare['preuve_recherchee']}\n")
        A(f"**Pourquoi elle tranche** — {prepare['pourquoi_elle_tranche']}\n")
        A(f"**Précaution** — {prepare['precaution']}\n")

    A("## Méthode\n")
    A(r["methode"] + "\n")
    A("## Avertissement\n")
    A(r["avertissement"] + "\n")
    return "\n".join(L)


def main() -> int:
    rapport = construire()
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    SORTIE_MD.parent.mkdir(parents=True, exist_ok=True)
    SORTIE_MD.write_text(rendre_markdown(rapport), encoding="utf-8")
    print(f"écrit : {SORTIE.relative_to(RACINE)}")
    print(f"écrit : {SORTIE_MD.relative_to(RACINE)}")
    print(f"  destinations établies : {len(rapport['destinations_etablies'])} "
          f"/ {rapport['pays_couverts']}")
    print(f"  couples renseignés    : {rapport['couverture_pct']} %")
    for etat, n in rapport["repartition_des_couples"].items():
        print(f"    {etat:28s} {n:6d}")
    print(f"  réciprocités confirmées : {len(rapport['reciprocite']['confirmees'])}")
    print(f"  asymétries constatées   : {len(rapport['reciprocite']['asymetries'])}")
    print(f"  contradictions de ratification : "
          f"{len(rapport['contradictions_ratification']['cas'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
