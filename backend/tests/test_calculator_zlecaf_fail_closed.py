"""
Vérifie le principe « fail-closed » : une donnée NPF authentique ne constitue
jamais, à elle seule, une preuve de préférence ZLECAf.
"""

import pytest


@pytest.fixture()
def client(monkeypatch):
    from services.crawled_data_service import crawled_service

    # crawled_service.load() n'est appelé qu'au démarrage de server.py (event
    # de startup)
    crawled_service.load()


def test_gha_synthetic_zero_rate_rejected(client):
    """Ghana : `backend/data/crawled/GHA_tariffs.json` portait, sur 100 % de
    ses 5 387 lignes, la paire synthétique `zlecaf_rate=0.0`/
    `zlecaf_source="ZLECAf"` — fabriquée, non sourcée. Nettoyée physiquement
    (branche `claude/ghana-crawled-zlecaf-cleanup`) : la paire ne doit plus
    exister sur le fichier."""
    from services.crawled_data_service import crawled_service

    raw = crawled_service.lookup("GHA", "010121")
    assert raw is not None
    assert raw.get("zlecaf_rate") is None, (
        "régression : GHA_tariffs.json porte de nouveau un zlecaf_rate " "fabriqué sur cette ligne"
    )
    assert not raw.get("zlecaf_source"), (
        "régression : GHA_tariffs.json porte de nouveau un zlecaf_source "
        "fabriqué sur cette ligne"
    )


def test_gha_crawled_file_physically_clean_of_any_zlecaf_key():
    """Balayage exhaustif des 5 387 lignes de
    `backend/data/crawled/GHA_tariffs.json` : zéro clé `zlecaf_rate`/
    `zlecaf_source`/`zlecaf_total_taxes` restante, quelle que soit la valeur
    (pas seulement la paire 0.0/"ZLECAf" connue) — et les champs
    NPF/fiscalité (dd_rate, dd_source, vat_rate, taxes_detail) restent
    présents et non vides."""
    import json
    from pathlib import Path

    # Le fichier source, pas sa dérivée : CRAWLED_DIR désigne
    # crawled_normalized/, régénérable et au schéma unifié (« positions »).
    # Ce test porte sur la propreté physique de la source elle-même, comme
    # l'annonce son intitulé, et c'est la vérification la plus forte : une
    # clé fabriquée réintroduite ici contaminerait toutes ses dérivées.
    path = Path(__file__).resolve().parent.parent / "data" / "crawled" / "GHA_tariffs.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    lines = data["tariff_lines"]
    assert len(lines) == 5387, f"précondition invalidée : {len(lines)} lignes trouvées"

    lines_with_zlecaf_key = 0
    lines_missing_npf = 0
    for line in lines:
        if any(k in line for k in ("zlecaf_rate", "zlecaf_source", "zlecaf_total_taxes")):
            lines_with_zlecaf_key += 1
        if (
            line.get("dd_rate") is None
            or not line.get("dd_source")
            or line.get("vat_rate") is None
            or not line.get("taxes_detail")
        ):
            lines_missing_npf += 1

    assert lines_with_zlecaf_key == 0, (
        f"{lines_with_zlecaf_key} ligne(s) portent encore une clé zlecaf_* — " "nettoyage incomplet"
    )
    assert lines_missing_npf == 0, (
        f"{lines_missing_npf} ligne(s) ont perdu leurs champs NPF/fiscalité " "pendant le nettoyage"
    )


_FABRICATED_ZLECAF_MARKERS = {
    "ZLECAf",
    "ZLECAf (produit normal)",
    "ZLECAf (produit sensible)",
}


def test_tariffs_39_files_physically_clean_of_synthetic_zlecaf_markers():
    """Vérification EXHAUSTIVE post-assainissement (100 % des fichiers, 100 %
    des lignes, pas un sondage) : les 39 fichiers `backend/data/tariffs/*.json`
    restants après l'archivage P0 du 2026-09-01 (14 synthétiques `enhanced_v2`
    + 1 copie DZA périmée retirés du service — cf. audit
    `AUDIT_CALCULATEUR_DONNEES_TARIFAIRES_2026-09-01.md`) ne portent plus AUCUN des 3
    marqueurs fabriqués historiquement présents (`"ZLECAf"`,
    `"ZLECAf (produit normal)"`, `"ZLECAf (produit sensible)"` — cf. branche
    `claude/tariffs-zlecaf-synthetic-cleanup`) : ni `zlecaf_rate`, ni
    `zlecaf_source`, ni `zlecaf_total_taxes` ne doivent plus exister sur
    aucune des ~206 300 lignes couvertes. Aucun champ non-ZLECAf n'a été
    touché par ce nettoyage (dd_rate, vat_rate, taxes_detail, sous-positions,
    etc. strictement préservés — vérifié séparément par hash structurel
    avant/après lors du nettoyage, hors périmètre de ce test qui porte sur
    l'état final)."""
    import json

    # Réutilise DATA_DIR de tariff_data_service (source unique de vérité pour
    # ce chemin) plutôt qu'un chemin absolu codé en dur — robuste à tout
    # emplacement de checkout (CI, autre poste).
    #
    # P0-1 (audit 2026-09-01) : 54 → 39 fichiers — les 14 pays synthétiques
    # enhanced_v2 (AGO COM DJI ERI LBY MDG MOZ MRT MWI SDN STP SYC ZMB ZWE)
    # et la copie DZA périmée de juin 2026 (P0-2) ont été archivés hors
    # service dans backend/data/archive/ — doctrine : aucune donnée
    # estimée/synthétique servie.
    from services.tariff_data_service import DATA_DIR, tariff_service

    files = sorted(DATA_DIR.glob("*_tariffs.json"))
    assert len(files) == 39, (
        f"précondition invalidée : {len(files)} fichiers trouvés, 39 attendus "
        "(54 - 14 synthétiques archivés P0-1 - 1 copie DZA périmée P0-2)"
    )

    tariff_service.load()

    total_lines_checked = 0
    lines_with_any_zlecaf_key = 0
    lines_with_known_marker = 0

    for path in files:
        country_code = path.name.replace("_tariffs.json", "")
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        for line in raw.get("tariff_lines", []):
            total_lines_checked += 1
            hs6 = line.get("hs6", "")
            if any(k in line for k in ("zlecaf_rate", "zlecaf_source", "zlecaf_total_taxes")):
                lines_with_any_zlecaf_key += 1
            if line.get("zlecaf_source") in _FABRICATED_ZLECAF_MARKERS:
                lines_with_known_marker += 1
            # Le chemin runtime (get_zlecaf_rate) ne doit jamais renvoyer un
            # taux pour une ligne qui n'a plus de zlecaf_rate en source.
            rate, source = tariff_service.get_zlecaf_rate(country_code, hs6)
            assert (
                rate is None
            ), f"{country_code}/{hs6} : taux inattendu après nettoyage (rate={rate})"
            assert source == ""

    assert (
        total_lines_checked > 200_000
    ), f"précondition invalidée : seulement {total_lines_checked} lignes lues sur 39 fichiers (~206 300 attendues après archivage P0)"
    assert lines_with_any_zlecaf_key == 0, (
        f"{lines_with_any_zlecaf_key} ligne(s) sur {total_lines_checked} portent encore "
        f"une clé zlecaf_rate/zlecaf_source/zlecaf_total_taxes — nettoyage incomplet"
    )
    assert lines_with_known_marker == 0


def test_tariff_data_service_still_rejects_marker_if_reintroduced():
    """Test anti-réintroduction : le garde-fou runtime de
    `tariff_data_service.get_zlecaf_rate` (ajouté sur
    `claude/zlecaf-fail-closed-guard`, PR #321) doit continuer de rejeter les
    3 marqueurs fabriqués connus même après l'assainissement physique des
    données — deuxième ligne de défense si un futur script de régénération
    (ex. `upgrade_to_enhanced_v2.py`, déjà identifié comme fabricateur)
    réintroduisait accidentellement l'un de ces marqueurs sur une ligne."""
    from services.tariff_data_service import tariff_service

    tariff_service.load()
    for marker in _FABRICATED_ZLECAF_MARKERS:
        line = {"zlecaf_rate": 12.5, "zlecaf_source": marker}
        # Simule get_tariff_line() en injectant directement une ligne dans
        # l'index pour isoler la logique de rejet de get_zlecaf_rate, sans
        # dépendre d'une ligne réelle du dataset (qui n'en porte plus aucune).
        tariff_service._hs6_index.setdefault("_TEST_REINTRODUCTION", {})["999999"] = line
        rate, source = tariff_service.get_zlecaf_rate("_TEST_REINTRODUCTION", "999999")
        del tariff_service._hs6_index["_TEST_REINTRODUCTION"]
        assert (
            rate is None
        ), f"marqueur {marker!r} réintroduit accepté comme taux réel (rate={rate})"
        assert source == ""
