"""Un seul calcul des droits et taxes à l'importation : POST /api/calcul.

Les autres routes qui liquidaient une importation (`/authentic-tariffs/calculate`
en GET et POST, `/postgres-tariffs/calculate`, `/v2/calculations`,
`/v2/bulk/tariff-calculations`) ont été retirées : deux calculs finissent
toujours par rendre deux montants. Ce test empêche qu'un second chemin
revienne sans qu'on le voie.
"""

from fastapi.routing import APIRoute

#: Routes dont le chemin parle de calcul et qui restent légitimes : le calcul
#: lui-même, le calcul des droits de sortie (un autre impôt, liquidé par le même
#: moteur sur le socle) et leur couverture.
AUTORISEES = {
    ("POST", "/api/calcul"),
    ("GET", "/api/calcul/pays"),
    ("POST", "/api/calcul/export"),
    ("GET", "/api/calcul/export/pays"),
}


def test_post_calcul_est_le_seul_calcul():
    from server import app

    routes = {
        (methode, route.path)
        for route in app.routes
        if isinstance(route, APIRoute) and "calcul" in route.path.lower()
        for methode in route.methods
    }
    assert routes == AUTORISEES


def _porte_le_quota(route):
    """La route dépend-elle de `require_calculations_quota` ?"""
    pile = list(route.dependant.dependencies)
    while pile:
        dependance = pile.pop()
        if getattr(dependance.call, "__qualname__", "").startswith("require_calculations_quota."):
            return True
        pile.extend(dependance.dependencies)
    return False


def test_seul_le_calcul_decompte_le_quota():
    """Le quota de calculs se décompte sur POST /api/calcul, et sur lui seul :
    lister les pays servis (écran « Comparaison multi-pays », à l'ouverture)
    ne liquide rien."""
    from server import app

    routes = {
        (methode, route.path): route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/calcul")
        for methode in route.methods
    }
    assert _porte_le_quota(routes[("POST", "/api/calcul")])
    assert not _porte_le_quota(routes[("GET", "/api/calcul/pays")])
    assert _porte_le_quota(routes[("POST", "/api/calcul/export")])
    assert not _porte_le_quota(routes[("GET", "/api/calcul/export/pays")])
