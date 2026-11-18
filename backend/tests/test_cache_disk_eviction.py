"""Éviction du cache disque (audit DoS, 17/11/2026).

La clé du cache disque est dérivée d'un paramètre client (ex. `hs_code` OEC) ;
sans plafond, des fichiers jamais réécrits s'accumulent et saturent le disque.
"""

from services import cache_service


def test_cache_disque_plafonne_le_nombre_de_fichiers(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_service, "_DISK_CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache_service, "_DISK_CACHE_ENABLED", True)
    monkeypatch.setattr(cache_service, "_DISK_CACHE_MAX_FILES", 5)

    for i in range(20):
        assert cache_service._disk_set(f"cle-client-{i}", {"v": i}, 3600) is True

    fichiers = list(tmp_path.glob("*.json"))
    assert 1 <= len(fichiers) <= 5
