"""
Tests pour l'unité complémentaire (supplementary unit) par code HS6 —
demandée pour la recherche HS6, en complément de la valeur (poids/nombre/
litres/tonnes selon la position tarifaire).
"""

from etl.hs6_supplementary_units import get_supplementary_unit, get_unit_label
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_supplementary_unit_exact_hs6_match():
    assert get_supplementary_unit("180100") == "kg"  # Fèves de cacao
    assert get_supplementary_unit("100590") == "tonnes"  # Maïs
    assert get_supplementary_unit("220830") == "litres"  # Rhum
    assert get_supplementary_unit("620451") == "nombre"  # T-shirts
    # Aiguilles d'injection / seringues : mappées EXACTEMENT (pas par chapitre)
    assert get_supplementary_unit("901831") == "nombre"  # Seringues
    assert get_supplementary_unit("901832") == "nombre"  # Aiguilles tubulaires


def test_get_supplementary_unit_no_hs4_fallback():
    # PAS de repli sur le préfixe HS4 : au sein d'une même position, les
    # sous-positions peuvent avoir des unités différentes — hériter de l'unité
    # d'un cousin de chapitre serait trompeur (ex. aiguilles vs autres
    # instruments de la position 9018). Un code non mappé exactement → None.
    assert get_supplementary_unit("901835") is None  # sous-position non mappée
    assert get_supplementary_unit("9018") is None  # HS4 seul, pas d'unité


def test_get_supplementary_unit_none_when_unmapped():
    assert get_supplementary_unit("999999") is None
    assert get_supplementary_unit("") is None
    assert get_supplementary_unit(None) is None


def test_get_unit_label_localized():
    assert get_unit_label("kg", "fr") == "kilogrammes"
    assert get_unit_label("kg", "en") == "kilograms"
    assert get_unit_label("litres", "fr") == "litres"
    assert get_unit_label("nombre", "en") == "number of pieces"


def test_search_endpoint_includes_supplementary_unit():
    r = client.get("/api/hs-codes/search?q=cacao&limit=5")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] > 0
    # Au moins un résultat doit exposer les champs d'unité complémentaire
    assert all("supplementary_unit" in item for item in data["results"])
    assert all("supplementary_unit_label" in item for item in data["results"])
    cacao_beans = next((r for r in data["results"] if r["code"] == "180100"), None)
    assert cacao_beans is not None
    assert cacao_beans["supplementary_unit"] == "kg"
    assert cacao_beans["supplementary_unit_label"] == "kilogrammes"


def test_code_endpoint_includes_supplementary_unit():
    r = client.get("/api/hs-codes/code/220830")
    assert r.status_code == 200
    data = r.json()
    assert data["supplementary_unit"] == "litres"
    assert data["supplementary_unit_label"] == "litres"


def test_code_endpoint_unit_none_when_unmapped():
    # Code présent en base mais sans unité complémentaire mappée
    r = client.get("/api/hs-codes/code/180310")
    assert r.status_code == 200
    data = r.json()
    assert data.get("supplementary_unit") is None


def test_chapter_endpoint_includes_supplementary_unit():
    r = client.get("/api/hs-codes/chapter/18")  # Cacao
    assert r.status_code == 200
    data = r.json()
    assert data["count"] > 0
    assert all("supplementary_unit" in c for c in data["codes"])
    cacao_beans = next((c for c in data["codes"] if c["code"] == "180100"), None)
    assert cacao_beans is not None
    assert cacao_beans["supplementary_unit"] == "kg"
