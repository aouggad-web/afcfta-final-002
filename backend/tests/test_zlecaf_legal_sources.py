"""
Les fiches de vérification ZLECAf citent des documents que le dépôt contient.

Une détermination juridique qui renvoie à une URL est fragile : le lien meurt,
l'administration réorganise son site, le portail devient injoignable — ce qui
s'est produit pour l'Algérie au moment même de la collecte. Les sources
primaires sont donc archivées dans `sources/`, et ces tests interdisent l'écart
entre ce qu'une fiche affirme et ce que le dépôt porte réellement :

* un SHA-256 cité doit correspondre au fichier archivé, sinon la fiche
  s'appuierait sur un document différent de celui qui a été lu ;
* une fiche déclarée vérifiée en primaire doit avoir ses documents archivés ;
* les listes d'origines admises doivent rester cohérentes — pas de doublon
  entre groupes de démantèlement, pas de pays classé deux fois.
"""

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REFS_DIR = REPO_ROOT / "backend" / "data" / "legal_refs" / "zlecaf_application"
SOURCES_DIR = REFS_DIR / "sources"

# Toute fiche juridique du répertoire, pas seulement celles d'application.
# Le glob précédent ne retenait que « *_application_* » : une fiche portant sur
# l'assiette de la TVA, par exemple, citait des empreintes que rien ne
# vérifiait. Une fiche qui échappe au contrôle de provenance est précisément
# celle où une empreinte fausse passerait.
FICHES = sorted(p for p in REFS_DIR.glob("*.json"))


def _archived_hashes() -> dict:
    """
    Empreintes de toutes les preuves archivées, quel que soit leur format.

    Une preuve n'est pas toujours un PDF : la circulaire algérienne pèse
    8,5 Mo et son texte extrait suffit à fonder la détermination, tandis que
    le README du répertoire n'est pas une preuve. On indexe donc tout sauf
    la documentation.
    """
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(SOURCES_DIR.iterdir())
        if path.is_file() and path.suffix.lower() != ".md"
    }


def _cited_hashes(payload) -> list:
    """Tout SHA-256 cité par une fiche, quel que soit son emplacement ET son nom.

    La clé n'est pas toujours « sha256 » : une fiche citant deux documents les
    nomme « pdf_sha256 » et « texte_sha256 », faute de quoi les deux valeurs
    entreraient en collision dans le même objet. N'accepter que l'orthographe
    exacte laissait ces empreintes hors contrôle — c'est la faute déjà relevée
    sur la fiche algérienne, et une fiche qui échappe au contrôle est
    précisément celle où une empreinte fausse passerait.
    """
    found = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.endswith("sha256") and isinstance(value, str) and value:
                found.append(value)
            else:
                found.extend(_cited_hashes(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_cited_hashes(item))
    return found


def test_des_fiches_existent():
    assert FICHES, "aucune fiche de vérification trouvée"


@pytest.mark.parametrize("fiche", FICHES, ids=[p.stem for p in FICHES])
def test_chaque_sha256_cite_correspond_a_un_document_archive(fiche):
    payload = json.loads(fiche.read_text(encoding="utf-8"))
    cited = _cited_hashes(payload)
    if not cited:
        pytest.skip(f"{fiche.stem} ne cite aucun document — niveau de preuve secondaire")

    archived = set(_archived_hashes().values())
    for digest in cited:
        assert digest in archived, (
            f"{fiche.stem} cite le SHA-256 {digest[:16]}… qu'aucun document de "
            f"sources/ ne porte : la fiche s'appuierait sur un document absent "
            f"du dépôt ou différent de celui qui a été lu"
        )


def _cited_artifacts(payload) -> list:
    """Artefacts du dépôt qu'une fiche invoque comme preuve."""
    found = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "artifact" and isinstance(value, str) and value:
                found.append(value)
            else:
                found.extend(_cited_artifacts(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_cited_artifacts(item))
    return found


@pytest.mark.parametrize("fiche", FICHES, ids=[p.stem for p in FICHES])
def test_une_fiche_primaire_archive_ses_documents(fiche):
    """
    Une preuve primaire doit être opposable, donc présente dans le dépôt.

    Elle prend deux formes selon la source : un acte publié, archivé en PDF
    dans `sources/` avec son empreinte ; ou un portail tarifaire officiel,
    dont l'artefact collecté et scellé tient lieu de preuve — c'est le cas de
    la Tunisie, dont le régime préférentiel se lit dans le tarif lui-même et
    non dans une circulaire. Les deux sont recevables, l'absence des deux ne
    l'est pas.
    """
    payload = json.loads(fiche.read_text(encoding="utf-8"))
    niveau = str(payload.get("evidence_level", ""))
    if not niveau.startswith("primaire"):
        pytest.skip(f"{fiche.stem} : niveau de preuve non primaire")

    hashes = _cited_hashes(payload)
    artifacts = [chemin for chemin in _cited_artifacts(payload) if (REPO_ROOT / chemin).exists()]
    assert hashes or artifacts, (
        f"{fiche.stem} se déclare vérifiée en primaire sans citer ni document "
        f"archivé ni artefact présent dans le dépôt — la déclaration ne serait "
        f"pas contrôlable"
    )


@pytest.mark.parametrize("fiche", FICHES, ids=[p.stem for p in FICHES])
def test_les_groupes_d_origines_ne_se_chevauchent_pas(fiche):
    """Un pays ne peut pas relever de deux calendriers de démantèlement."""
    payload = json.loads(fiche.read_text(encoding="utf-8"))
    origins = payload.get("accepted_origins") or {}

    groupes = {
        key: set(value["iso3"])
        for key, value in origins.items()
        if isinstance(value, dict) and isinstance(value.get("iso3"), list)
    }
    # Toutes les fiches ne rangent pas leurs origines en groupes nommés : la
    # Tunisie publie les siennes ligne à ligne dans `detail`, une origine par
    # entrée. Les ignorer faisait sauter la fiche entière — y compris le
    # contrôle du décompte déclaré, qui n'a pourtant rien à voir avec le
    # nombre de groupes.
    detail = origins.get("detail")
    if isinstance(detail, list):
        plates = {
            str(entry["iso3"])
            for entry in detail
            if isinstance(entry, dict) and entry.get("iso3")
        }
        if plates:
            groupes.setdefault("detail", set()).update(plates)

    if not groupes:
        pytest.skip(f"{fiche.stem} : aucune origine énumérée")

    _verifier_le_decompte_declare(fiche, origins, groupes)

    if len(groupes) < 2:
        return

    noms = sorted(groupes)
    for i, gauche in enumerate(noms):
        for droite in noms[i + 1 :]:
            commun = groupes[gauche] & groupes[droite]
            assert not commun, (
                f"{fiche.stem} : {sorted(commun)} figure à la fois dans "
                f"{gauche} et {droite} — un pays ne peut relever de deux "
                f"calendriers de démantèlement"
            )


def _verifier_le_decompte_declare(fiche, origins: dict, groupes: dict) -> None:
    """Le décompte annoncé par la fiche doit correspondre aux origines listées.

    Le décompte global ne suffit pas : chaque groupe — P1/P2 marocains,
    5 ans / 10 ans égyptiens — déclare le sien, et déplacer une origine d'un
    groupe à l'autre laisse la somme inchangée tout en rendant les deux
    décomptes de groupe faux. Or c'est précisément ce déplacement qui change
    le calendrier de démantèlement servi à un pays.
    """
    declared = origins.get("count")
    if isinstance(declared, int):
        total = len(set().union(*groupes.values()))
        assert total == declared, (
            f"{fiche.stem} : {total} origines distinctes dans les groupes, " f"{declared} déclarées"
        )

    for nom, valeur in origins.items():
        if not isinstance(valeur, dict) or not isinstance(valeur.get("iso3"), list):
            continue
        attendu = valeur.get("count")
        if isinstance(attendu, int):
            reel = len(set(valeur["iso3"]))
            assert reel == attendu, (
                f"{fiche.stem} : le groupe {nom} déclare {attendu} origines "
                f"et en énumère {reel}"
            )
