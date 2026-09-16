"""
Une empreinte de jeu de données ne doit pas diverger d'un registre à l'autre.

L'empreinte d'un fichier collecté est consignée à plusieurs endroits du dépôt,
qui remplissent des rôles différents : `source_registry_v2.json` sert de
manifeste à `verify_crawled_file`, et les fichiers `data/<pays>/legal_sources.json`
lient le jeu runtime à ses sources juridiques. Rien n'imposait qu'ils
s'accordent.

La reconstruction du tarif égyptien l'a démontré à ses dépens : le manifeste et
le sceau avaient été refaits, le fichier de sources juridiques ne l'avait pas
été, et l'écart n'est apparu qu'en intégration continue. Le module d'intégrité
prévient d'ailleurs lui-même du risque, en commentaire : « manifeste, registre —
avec autant d'occasions de désynchronisation ».

Ce test ferme cette porte : pour chaque fichier collecté, toutes les empreintes
enregistrées doivent valoir celle du fichier lui-même.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "backend" / "data" / "source_registry_v2.json"
LEGAL_SOURCES = sorted((REPO_ROOT / "data").glob("*/legal_sources.json"))


def _digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_entries() -> dict:
    """Chemin déclaré → empreinte, tel que le manifeste les publie."""
    registry = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = {}
    for iso, entry in (registry.get("countries") or {}).items():
        chemin, digest = entry.get("artifact_path"), entry.get("sha256")
        if chemin and digest:
            entries[chemin] = (iso, digest)
    return entries


def _legal_source_entries() -> list:
    """(fichier de sources, chemin déclaré, empreinte) pour les jeux runtime."""
    out = []
    for source_file in LEGAL_SOURCES:
        payload = json.loads(source_file.read_text(encoding="utf-8"))
        for source in payload.get("sources") or []:
            chemin, digest = source.get("registry_path"), source.get("sha256")
            if chemin and digest and chemin.startswith("backend/data/crawled/"):
                out.append((source_file, chemin, digest))
    return out


def test_le_manifeste_declare_l_empreinte_reelle():
    ecarts = []
    for chemin, (iso, declare) in sorted(_manifest_entries().items()):
        fichier = REPO_ROOT / chemin
        if not fichier.is_file():
            continue  # fichier non versionné dans ce clone : hors sujet ici
        reel = _digest(fichier)
        if reel != declare:
            ecarts.append(f"{iso} {chemin} : manifeste {declare[:16]}… ≠ fichier {reel[:16]}…")
    assert not ecarts, "empreintes divergentes :\n" + "\n".join(ecarts)


@pytest.mark.parametrize(
    "source_file,chemin,declare",
    _legal_source_entries(),
    ids=[f"{p.parent.name}:{c.split('/')[-1]}" for p, c, _ in _legal_source_entries()],
)
def test_les_sources_juridiques_declarent_l_empreinte_reelle(source_file, chemin, declare):
    fichier = REPO_ROOT / chemin
    if not fichier.is_file():
        pytest.skip(f"{chemin} absent de ce clone")
    reel = _digest(fichier)
    assert reel == declare, (
        f"{source_file.relative_to(REPO_ROOT)} déclare {declare[:16]}… pour "
        f"{chemin}, dont l'empreinte réelle est {reel[:16]}…"
    )


def test_les_deux_registres_s_accordent_entre_eux():
    """
    Là où les deux registres décrivent le même fichier, ils doivent coïncider.

    C'est le contrôle qui manquait : chacun pouvait être juste vis-à-vis du
    fichier à un instant donné et faux vis-à-vis de l'autre après une
    reconstruction ne touchant qu'un seul des deux.
    """
    manifeste = _manifest_entries()
    ecarts = []
    for source_file, chemin, declare in _legal_source_entries():
        if chemin not in manifeste:
            continue
        _, declare_manifeste = manifeste[chemin]
        if declare != declare_manifeste:
            ecarts.append(
                f"{chemin} : {source_file.parent.name} {declare[:16]}… ≠ "
                f"manifeste {declare_manifeste[:16]}…"
            )
    assert not ecarts, "registres désaccordés :\n" + "\n".join(ecarts)
