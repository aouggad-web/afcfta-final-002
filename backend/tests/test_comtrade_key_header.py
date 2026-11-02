"""La clé UN Comtrade part en en-tête, jamais dans l'URL (constat C2 de l'audit).

Une URL finit dans les journaux, les proxys et les messages d'erreur ; l'API
Comtrade (Azure API Management) accepte la clé dans l'en-tête
``Ocp-Apim-Subscription-Key`` — même usage que wto_service.py.
"""

from unittest.mock import MagicMock

import services.comtrade_service as mod
from services.comtrade_service import ComtradeService

PRIMAIRE = "CLE-PRIMAIRE-FACTICE"
SECONDAIRE = "CLE-SECONDAIRE-FACTICE"


def _reponse(code, corps=None):
    r = MagicMock()
    r.status_code = code
    r.json.return_value = corps or {}
    return r


def _service(monkeypatch, secondaire=""):
    monkeypatch.setenv("COMTRADE_API_KEY", PRIMAIRE)
    monkeypatch.setenv("COMTRADE_API_KEY_SECONDARY", secondaire)
    monkeypatch.setattr(mod.time, "sleep", lambda s: None)
    return ComtradeService()


def test_cle_dans_l_en_tete_et_absente_des_parametres(monkeypatch):
    service = _service(monkeypatch)
    appel = MagicMock(return_value=_reponse(200, {"data": [{"x": 1}]}))
    monkeypatch.setattr(mod.requests, "get", appel)

    assert service.fetch("504", "0", "2023") == [{"x": 1}]

    kwargs = appel.call_args.kwargs
    assert kwargs["headers"] == {"Ocp-Apim-Subscription-Key": PRIMAIRE}
    assert "subscription-key" not in kwargs["params"]
    assert PRIMAIRE not in str(kwargs["params"])


def test_bascule_sur_la_cle_secondaire_toujours_en_en_tete(monkeypatch):
    service = _service(monkeypatch, secondaire=SECONDAIRE)
    cles_envoyees = []

    def faux_get(url, params=None, headers=None, timeout=None):
        cles_envoyees.append(headers["Ocp-Apim-Subscription-Key"])
        assert "subscription-key" not in params
        return _reponse(401) if len(cles_envoyees) == 1 else _reponse(200, {"data": []})

    monkeypatch.setattr(mod.requests, "get", faux_get)

    assert service.fetch("504", "0", "2023") == []
    assert cles_envoyees == [PRIMAIRE, SECONDAIRE]
