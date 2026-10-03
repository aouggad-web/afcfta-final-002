#!/usr/bin/env python3
"""Coefficients ZLECAf publiés par la douane tunisienne au Tarif Web 2026.

Le Tarif Web range sous la zone « ZLECAf », ligne par ligne et pays par pays,
un pourcentage (« 40 % », « 87.5 % », « 80 % », « 0 % »). Ce n'est pas un
droit : c'est le coefficient de l'année que le texte TA n°016/2023 applique
au droit de base 2019 (fiche TUN_rapprochement_baremes_2026-09-29.json).

Le script lit la collecte du dépôt (backend/data/crawled/TUN_tariffs.json) et
écrit backend/data/zlecaf_tun/coefficients_tarifweb_2026.json : une table des
motifs distincts {ISO3: coefficient} et, pour chaque position à 10 chiffres
(clé de contrôle ôtée), le numéro de son motif.

Il écrit aussi backend/data/zlecaf_tun/zale_tarifweb_2026.json, de même forme :
les taux que le Tarif Web publie sous la zone « ZALE » pour les trois
partenaires africains (Algérie, Égypte, Maroc). Ils ne sont pas calculés ; ils
nourrissent une note d'information.

    python3 backend/scripts/extraire_coefficients_tun.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SOURCE = RACINE / "data" / "crawled" / "TUN_tariffs.json"
SORTIE = RACINE / "data" / "zlecaf_tun" / "coefficients_tarifweb_2026.json"
SORTIE_ZALE = RACINE / "data" / "zlecaf_tun" / "zale_tarifweb_2026.json"

#: Noms des partenaires tels que le Tarif Web les écrit (code pays numérique
#: ISO 3166 entre parenthèses).
PARTENAIRES = {
    "CAMEROUN": "CMR",  # 120
    "GHANA": "GHA",  # 288
    "KENYA": "KEN",  # 404
    "TANZANIE": "TZA",  # 834
    "NIGERIA": "NGA",  # 566
    "AFRIQUE DU SUD": "ZAF",  # 710
    "MAURICE": "MUS",  # 480
    "RUANDA": "RWA",  # 646
}

#: Partenaires africains de la zone « ZALE » du Tarif Web.
PARTENAIRES_ZALE = {"ALGERIE": "DZA", "EGYPTE": "EGY", "MAROC": "MAR"}


def _table(sub_positions, zone, partenaires):
    """Motifs distincts {ISO3: taux} et numéro de motif par position, plus les
    accords que la source nomme pour chaque partenaire."""
    motifs: list[dict] = []
    index: dict[str, int] = {}
    positions: dict[str, int] = {}
    accords: dict[str, list] = {}
    for ligne in sub_positions:
        motif = {}
        for pref in ligne.get("preferences", []):
            if pref.get("zone") != zone or pref["country_name"] not in partenaires:
                continue
            iso3 = partenaires[pref["country_name"]]
            motif[iso3] = float(pref["rate"].replace("%", "").strip())
            accords.setdefault(iso3, pref.get("accords", []))
        if not motif:
            continue
        cle = json.dumps(motif, sort_keys=True)
        if cle not in index:
            index[cle] = len(motifs)
            motifs.append(dict(sorted(motif.items())))
        positions[ligne["hs_code"][:10]] = index[cle]
    return motifs, dict(sorted(positions.items())), accords


def main() -> None:
    octets = SOURCE.read_bytes()
    tarif = json.loads(octets)
    # Partenaire inconnu sous la zone ZLECAf : KeyError, plutôt qu'un oubli.
    inconnus = {
        pref["country_name"]
        for ligne in tarif["sub_positions"]
        for pref in ligne.get("preferences", [])
        if pref.get("zone") == "ZLECAf" and pref["country_name"] not in PARTENAIRES
    }
    if inconnus:
        raise KeyError(f"partenaires ZLECAf inconnus : {sorted(inconnus)}")
    motifs, positions, _ = _table(tarif["sub_positions"], "ZLECAf", PARTENAIRES)
    motifs_zale, positions_zale, accords_zale = _table(tarif["sub_positions"], "ZALE", PARTENAIRES_ZALE)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    resultat = {
        "_objet": (
            "Coefficients ZLECAf 2026 publiés par la douane tunisienne au Tarif "
            "Web 2026, zone « ZLECAf » : pourcentage du droit de base 2019 à "
            "appliquer, par position et par origine. Une position absente ne "
            "porte aucune préférence ZLECAf publiée."
        ),
        "_source": "https://www.douane.gov.tn/tarifweb2026/",
        "_artefact": "backend/data/crawled/TUN_tariffs.json",
        "_artefact_sha256": hashlib.sha256(octets).hexdigest(),
        "_collecte_le": tarif.get("extracted_at"),
        "_annee": 2026,
        "_partenaires": PARTENAIRES,
        "motifs": motifs,
        "positions": positions,
    }
    SORTIE.write_text(
        json.dumps(resultat, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"{len(positions)} positions, {len(motifs)} motifs -> {SORTIE}")

    zale = {
        "_objet": (
            "Taux publiés par la douane tunisienne au Tarif Web 2026 sous la zone "
            "« ZALE » pour l'Algérie, l'Égypte et le Maroc. Information seulement : "
            "ces régimes ne sont pas calculés."
        ),
        "_source": "https://www.douane.gov.tn/tarifweb2026/",
        "_artefact": "backend/data/crawled/TUN_tariffs.json",
        "_artefact_sha256": resultat["_artefact_sha256"],
        "_collecte_le": tarif.get("extracted_at"),
        "accords": accords_zale,
        "motifs": motifs_zale,
        "positions": positions_zale,
    }
    SORTIE_ZALE.write_text(json.dumps(zale, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(positions_zale)} positions ZALE, {len(motifs_zale)} motifs -> {SORTIE_ZALE}")


if __name__ == "__main__":
    main()
