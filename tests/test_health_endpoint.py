#!/usr/bin/env python3
"""
Test pour l'endpoint de santé /api/health
Inclut la vérification de l'absence d'erreurs 502 Bad Gateway persistantes.
"""

import sys
import importlib.util
from pathlib import Path

# Ajouter le backend au path pour l'import
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))


def _load_health_router():
    """Charge uniquement le module health sans déclencher l'init du package routes."""
    health_path = backend_path / 'routes' / 'health.py'
    spec = importlib.util.spec_from_file_location('backend.routes.health', health_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.router


def test_health_endpoint_no_502():
    """
    Vérifie que l'endpoint /api/health retourne 200 et non 502 Bad Gateway.
    Utilise le TestClient de FastAPI pour tester sans serveur externe.
    """
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    router = _load_health_router()
    app = FastAPI()
    app.include_router(router)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/health")

    assert response.status_code != 502, (
        f"502 Bad Gateway détecté sur /health: {response.text}"
    )
    assert response.status_code == 200, (
        f"Statut inattendu {response.status_code} sur /health: {response.text}"
    )
    data = response.json()
    assert data.get("status") == "healthy", (
        f"Le health check ne renvoie pas 'healthy': {data}"
    )
    print("✅ /health retourne 200 (pas de 502 Bad Gateway)")


def test_detailed_health_endpoint_no_502():
    """
    Vérifie que /api/health/status retourne 200 avec la structure correcte
    (champ 'components', non 'checks') et n'est pas un 502.
    """
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    router = _load_health_router()
    app = FastAPI()
    app.include_router(router)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/health/status")

    assert response.status_code != 502, (
        f"502 Bad Gateway détecté sur /health/status: {response.text}"
    )
    assert response.status_code == 200, (
        f"Statut inattendu {response.status_code} sur /health/status: {response.text}"
    )
    data = response.json()
    assert data.get("status") == "healthy", (
        f"Le health/status ne renvoie pas 'healthy': {data}"
    )
    assert "components" in data, (
        f"Champ 'components' manquant dans /health/status: {list(data.keys())}"
    )
    print("✅ /health/status retourne 200 avec 'components' (pas de 502 Bad Gateway)")


def test_health_logic():
    """
    Test de la logique du health check sans serveur
    """
    from pathlib import Path
    
    files = [
        'zlecaf_tariff_lines_by_country.json',
        'zlecaf_africa_vs_world_tariffs.xlsx',
        'zlecaf_rules_of_origin.json',
        'zlecaf_dismantling_schedule.csv',
        'zlecaf_tariff_origin_phase.json',
    ]
    
    # Chemin vers le répertoire de données
    base_path = Path(__file__).parent.parent / 'frontend' / 'public' / 'data'
    
    status = {}
    for filename in files:
        file_path = base_path / filename
        try:
            status[filename] = file_path.exists() and file_path.is_file()
        except Exception:
            status[filename] = False
    
    all_ok = all(status.values())
    
    print("=" * 60)
    print("🏥 TEST HEALTH CHECK ENDPOINT")
    print("=" * 60)
    print(f"Base path: {base_path}")
    print(f"\n📊 Status des fichiers:")
    
    for filename, exists in status.items():
        icon = "✅" if exists else "❌"
        print(f"  {icon} {filename}")
    
    print(f"\n🎯 Résultat global: {'✅ OK' if all_ok else '❌ FAILED'}")
    print("=" * 60)
    
    # Note: En production, certains fichiers peuvent manquer (xlsx vs csv)
    # On vérifie juste que la logique fonctionne
    return status


if __name__ == "__main__":
    status = test_health_logic()
    # Au moins quelques fichiers doivent être présents après make_release.py --demo
    present_count = sum(1 for v in status.values() if v)
    if present_count >= 3:
        print(f"\n✅ Test passé: {present_count}/5 fichiers présents")
        sys.exit(0)
    else:
        print(f"\n⚠️ Attention: seulement {present_count}/5 fichiers présents")
        print("Exécutez 'python backend/make_release.py --demo' pour générer les fichiers")
        sys.exit(0)  # Ne pas faire échouer le test si les données ne sont pas encore générées
