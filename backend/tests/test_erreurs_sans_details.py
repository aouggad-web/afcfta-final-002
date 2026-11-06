"""Aucun texte d'exception interne dans les réponses de l'API (constat M9 de l'audit).

Le message d'une exception imprévue peut contenir un chemin du serveur, une
requête, une adresse de service tiers avec sa clé, ou le texte d'une erreur
de base de données. Il va au journal du serveur ; le client reçoit un message
générique.

Le test lit le code des modules qui servent réellement une route de
l'application. Il signale tout gestionnaire d'exception « fourre-tout »
(`except Exception`, `except BaseException`, `except:`) ou d'erreur
d'entrée-sortie (réseau, fichiers, base) dont la variable atteint une
réponse : `HTTPException`, `JSONResponse`, un `return`, ou une valeur rangée
dans un dictionnaire. Une exception propre au projet, au message rédigé pour
l'utilisateur, peut toujours être relayée.
"""

import ast
import inspect
import sys
from pathlib import Path

from backend.tests.routes_effectives import routes_api

# Erreurs dont le texte vient d'une bibliothèque ou du système, jamais du projet.
_TYPES_SYSTEME = {
    "Exception",
    "BaseException",
    "OSError",
    "IOError",
    "EnvironmentError",
    "ConnectionError",
    "TimeoutError",
    "FileNotFoundError",
    "PermissionError",
}
_MODULES_TIERS = {
    "httpx",
    "requests",
    "aiohttp",
    "pymongo",
    "motor",
    "redis",
    "urllib",
    "urllib3",
    "socket",
    "ssl",
    "sqlalchemy",
    "asyncio",
    "anthropic",
    "openai",
    "stripe",
}
_REPONSES = {"HTTPException", "JSONResponse", "Response", "PlainTextResponse", "HTMLResponse"}


def _racine(expr):
    while isinstance(expr, ast.Attribute):
        expr = expr.value
    return expr.id if isinstance(expr, ast.Name) else None


def _type_risque(expr):
    if expr is None:
        return True  # except:
    if isinstance(expr, ast.Tuple):
        return any(_type_risque(e) for e in expr.elts)
    if isinstance(expr, ast.Name):
        return expr.id in _TYPES_SYSTEME
    if isinstance(expr, ast.Attribute):
        return _racine(expr) in _MODULES_TIERS
    return False


def _nom_appele(appel):
    f = appel.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def _cite(noeud, nom):
    return any(isinstance(n, ast.Name) and n.id == nom for n in ast.walk(noeud))


def _fuites(source):
    """(ligne, extrait) de chaque endroit où l'exception atteint la réponse."""
    trouvees = []
    for gest in ast.walk(ast.parse(source)):
        if not (isinstance(gest, ast.ExceptHandler) and gest.name and _type_risque(gest.type)):
            continue
        for instr in gest.body:
            for n in ast.walk(instr):
                cible = None
                if isinstance(n, ast.Call) and _nom_appele(n) in _REPONSES:
                    cible = n
                elif isinstance(n, ast.Return) and n.value is not None:
                    cible = n.value
                elif isinstance(n, ast.Assign) and any(
                    isinstance(t, ast.Subscript) for t in n.targets
                ):
                    cible = n.value
                if cible is not None and _cite(cible, gest.name):
                    trouvees.append((n.lineno, ast.get_source_segment(source, n)[:120]))
    return trouvees


def _fichiers_servis():
    from server import app

    fichiers = set()
    for route in routes_api(app):
        endpoint = route.original_route.endpoint
        module = sys.modules.get(getattr(endpoint, "__module__", ""))
        if module is not None:
            fichiers.add(Path(inspect.getfile(module)).resolve())
        # Fichier de la fonction elle-même : couvre aussi un module chargé sans
        # passer par sys.modules (api/v2/endpoints.py, routes/__init__.py).
        source = inspect.getsourcefile(inspect.unwrap(endpoint))
        if source:
            fichiers.add(Path(source).resolve())
    return fichiers


def test_le_detecteur_reconnait_les_fuites():
    source = """
try:
    pass
except Exception as exc:
    raise HTTPException(status_code=500, detail=str(exc))
try:
    pass
except httpx.HTTPError as e:
    raise HTTPException(503, f"Service indisponible : {e}")
try:
    pass
except:
    pass
try:
    pass
except (ValueError, Exception) as err:
    return {"success": False, "error": str(err)}
try:
    pass
except Exception as e:
    canal["error"] = repr(e)
"""
    assert [ligne for ligne, _ in _fuites(source)] == [5, 9, 17, 21]


def test_le_detecteur_laisse_passer_les_erreurs_maitrisees():
    source = """
try:
    pass
except Exception as exc:
    logger.error("échec : %s", exc, exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
try:
    pass
except CalculInvalide as exc:
    raise HTTPException(status_code=422, detail=str(exc))
"""
    assert _fuites(source) == []


def test_aucune_route_ne_renvoie_le_texte_d_une_exception():
    fichiers = _fichiers_servis()
    # Garde-fou : la liste ne doit pas être vide ni réduite à server.py.
    assert len(fichiers) > 20, fichiers
    racine = Path(__file__).resolve().parents[2]
    fuites = [
        f"{f.relative_to(racine)}:{ligne}  {extrait}"
        for f in sorted(fichiers)
        for ligne, extrait in _fuites(f.read_text(encoding="utf-8"))
    ]
    assert fuites == [], "\n" + "\n".join(fuites)
