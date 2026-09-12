"""Les sceaux d'intégrité doivent rester vérifiables après un clone du dépôt.

``backend/data/crawled/`` est exclu par ``.gitignore`` et seuls les JSON y sont
forcés : les ``.sha256`` adjacents ne sont donc pas versionnés et manquent après
un clone. ``verify_crawled_file`` se rabat alors sur le manifeste, qui porte la
même empreinte. Ces tests couvrent ce repli, qu'aucun appelant n'exerçait.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
INTEGRITY = REPO_ROOT / "backend" / "crawlers" / "integrity.py"
CRAWLED = REPO_ROOT / "backend" / "data" / "crawled"


@pytest.fixture(scope="module")
def integrity():
    # Import direct du fichier : le paquet crawlers importe motor au chargement,
    # dont ce module n'a aucun besoin.
    spec = importlib.util.spec_from_file_location("crawlers_integrity", INTEGRITY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fichier_scelle():
    candidat = CRAWLED / "DZA_tariffs.json"
    if not candidat.exists():
        pytest.skip("aucun fichier scellé dans ce checkout")
    return str(candidat)


def test_le_fichier_se_verifie_tel_quel(integrity, fichier_scelle):
    resultat = integrity.verify_crawled_file(fichier_scelle)
    assert resultat["valid"], resultat
    assert resultat["reference"] in ("sidecar", "manifest")


def test_verification_possible_sans_sceau_adjacent(integrity, fichier_scelle):
    """Situation d'un clone neuf : le .sha256 n'existe pas.

    Le repli passe par l'``artifact_path`` du manifeste, qui désigne
    l'emplacement réel du fichier : on retire donc le sceau en place le temps
    du test plutôt que de travailler sur une copie, qu'aucune entrée du
    manifeste ne désignerait.
    """
    sidecar = pathlib.Path(integrity.sidecar_path(fichier_scelle))
    sauvegarde = sidecar.read_text(encoding="utf-8") if sidecar.exists() else None
    if sauvegarde is not None:
        sidecar.unlink()
    try:
        resultat = integrity.verify_crawled_file(fichier_scelle)
        assert resultat["reference"] == "manifest", (
            "sans sceau adjacent, le manifeste doit servir de référence"
        )
        assert resultat["valid"], resultat
    finally:
        if sauvegarde is not None:
            sidecar.write_text(sauvegarde, encoding="utf-8")


def test_une_alteration_est_rejetee_meme_sans_sceau(integrity, fichier_scelle):
    """Le repli doit vérifier réellement, pas seulement trouver une référence."""
    chemin = pathlib.Path(fichier_scelle)
    sidecar = pathlib.Path(integrity.sidecar_path(fichier_scelle))
    octets = chemin.read_bytes()
    sauvegarde = sidecar.read_text(encoding="utf-8") if sidecar.exists() else None
    if sauvegarde is not None:
        sidecar.unlink()
    try:
        chemin.write_bytes(octets + b" ")
        resultat = integrity.verify_crawled_file(fichier_scelle)
        assert not resultat["valid"], "une altération d'un octet passe inaperçue"
        assert not resultat["file_hash_match"]
    finally:
        chemin.write_bytes(octets)
        if sauvegarde is not None:
            sidecar.write_text(sauvegarde, encoding="utf-8")


def test_un_fichier_hors_manifeste_ne_pretend_pas_etre_verifie(integrity, tmp_path):
    """Sans référence, le résultat doit dire « rien à quoi comparer »."""
    etranger = tmp_path / "INCONNU_tariffs.json"
    etranger.write_text('{"country": "XXX", "_integrity_seal": {"content_hash": "x"}}',
                        encoding="utf-8")
    resultat = integrity.verify_crawled_file(str(etranger))
    assert resultat["reference"] is None
    assert not resultat["valid"]


def test_le_cache_du_manifeste_suit_ses_modifications(integrity, tmp_path):
    """Un cache qui ne verrait pas une mise à jour ferait mentir la vérification.

    La table {chemin → empreinte} est construite une fois puis réutilisée :
    sans invalidation, un rescellement suivi d'une mise à jour du manifeste
    continuerait d'être confronté à l'ancienne valeur, et la vérification
    validerait des octets qui ne sont plus les bons.
    """
    manifeste = REPO_ROOT / "backend" / "data" / "source_registry_v2.json"
    octets = manifeste.read_bytes()

    premiere = integrity._manifest_table()
    assert premiere, "table du manifeste vide"
    assert integrity._manifest_table() is premiere, "la table devrait être réutilisée"

    try:
        # Réécriture à l'identique : seule la date de modification change.
        manifeste.write_bytes(octets)
        seconde = integrity._manifest_table()
        assert seconde is not premiere, "une modification du manifeste doit invalider le cache"
        assert seconde == premiere, "le contenu identique doit produire la même table"
    finally:
        manifeste.write_bytes(octets)
