"""Un seul calcul des droits et taxes à l'importation : POST /api/calcul.

Les autres routes qui liquidaient une importation (`/authentic-tariffs/calculate`
en GET et POST, `/postgres-tariffs/calculate`, `/v2/calculations`,
`/v2/bulk/tariff-calculations`) ont été retirées : deux calculs finissent
toujours par rendre deux montants. Ce test empêche qu'un second chemin
revienne sans qu'on le voie.
"""

from fastapi.routing import APIRoute

#: Routes dont le chemin parle de calcul et qui restent légitimes : le calcul
#: lui-même, la couverture du socle, et les droits à l'EXPORTATION — un autre
#: impôt, sur une autre opération.
AUTORISEES = {
    ("POST", "/api/calcul"),
    ("GET", "/api/calcul/pays"),
    ("GET", "/api/authentic-tariffs/export-calculate/{country_iso3}/{hs_code}"),
    ("POST", "/api/authentic-tariffs/export-calculate"),
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
