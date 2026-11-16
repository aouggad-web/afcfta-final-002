"""Routes effectives d'une application FastAPI, pour les tests qui les inspectent.

Avec FastAPI 0.162, `app.routes` garde chaque routeur inclus sous la forme d'un
objet imbriqué : les routes /api/... n'y figurent plus à plat. Un test qui
parcourt `app.routes` ne les voit plus, et une vérification « aucune route
ne… » passerait sans rien vérifier. `iter_route_contexts` déplie les routeurs
inclus : chaque route y porte son chemin complet et ses dépendances
effectives, celles posées à l'inclusion du routeur comprises.
"""

from fastapi.routing import APIRoute, iter_route_contexts


def routes_effectives(app):
    routes = list(iter_route_contexts(app.routes))
    # Garde-fou : si FastAPI change encore la façon d'exposer ses routes, les
    # tests doivent échouer ici plutôt que passer sur une liste vide.
    assert any(isinstance(r.original_route, APIRoute) for r in routes), "aucune route API trouvée"
    return routes


def routes_api(app):
    return [r for r in routes_effectives(app) if isinstance(r.original_route, APIRoute)]
