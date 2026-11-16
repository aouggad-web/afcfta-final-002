"""Aucun code Python du dépôt ne désactive la vérification TLS (audit INFO-7).

Une donnée tarifaire ou juridique lue sans vérification TLS peut avoir été
substituée en chemin, et rien ne la distingue ensuite d'une donnée saine. Un
serveur qui n'envoie pas son certificat intermédiaire se traite en fournissant
celui-ci (data/dza/sectigo_dv_r36.crt), jamais en coupant la vérification.

Le test lit l'arbre syntaxique : un commentaire ou une docstring qui explique
pourquoi on n'utilise plus `verify=False` n'est pas signalé.
"""

import ast
import os
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
_IGNORES = {".git", "node_modules", "__pycache__", "build", "dist", ".venv", "venv"}


def _desactivations(source):
    """(ligne, motif) de chaque désactivation de la vérification TLS."""
    trouvees = []
    for n in ast.walk(ast.parse(source)):
        if isinstance(n, ast.keyword) and n.arg == "verify":
            if isinstance(n.value, ast.Constant) and n.value.value is False:
                trouvees.append((n.value.lineno, "verify=False"))
        elif isinstance(n, (ast.Name, ast.Attribute)):
            nom = n.id if isinstance(n, ast.Name) else n.attr
            if nom in ("CERT_NONE", "_create_unverified_context"):
                trouvees.append((n.lineno, nom))
        elif isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant):
            if n.value.value is False and any(
                isinstance(t, ast.Attribute) and t.attr == "check_hostname" for t in n.targets
            ):
                trouvees.append((n.lineno, "check_hostname = False"))
    return trouvees


def _fichiers_python():
    for dossier, sous_dossiers, fichiers in os.walk(RACINE):
        sous_dossiers[:] = [
            d for d in sous_dossiers if d not in _IGNORES and not d.startswith(".venv")
        ]
        for nom in fichiers:
            if nom.endswith(".py"):
                yield Path(dossier) / nom


def test_le_detecteur_reconnait_les_desactivations():
    source = """
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
requests.get(url, verify=False)
httpx.Client(verify=False)
ssl._create_unverified_context()
"""
    assert [ligne for ligne, _ in _desactivations(source)] == [3, 4, 5, 6, 7]


def test_le_detecteur_laisse_passer_les_explications_et_la_verification():
    source = '''
"""Elle portait verify=False et CERT_NONE : rétablie."""
# check_hostname = False était là
ctx = ssl.create_default_context()
ctx.load_verify_locations(cafile="intermediaire.crt")
requests.get(url, verify=True)
requests.get(url, verify="bundle.pem")
'''
    assert _desactivations(source) == []


def test_aucun_code_ne_desactive_la_verification_tls():
    fichiers = list(_fichiers_python())
    assert len(fichiers) > 500, len(fichiers)  # garde-fou : le parcours voit le dépôt
    trouvees = []
    for f in fichiers:
        try:
            source = f.read_text(encoding="utf-8")
            desactivations = _desactivations(source)
        except (SyntaxError, UnicodeDecodeError):
            continue
        trouvees += [f"{f.relative_to(RACINE)}:{ligne}  {motif}" for ligne, motif in desactivations]
    assert trouvees == [], "\n" + "\n".join(trouvees)
