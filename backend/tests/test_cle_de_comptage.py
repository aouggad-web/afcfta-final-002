"""Clé d'un visiteur pour les compteurs : IPv4 telle quelle, IPv6 par préfixe /64."""

import sys
from pathlib import Path

import pytest
from starlette.requests import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import geo_service  # noqa: E402


def _requete(xff):
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", xff.encode())],
        "client": ("10.0.0.2", 1234),
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _un_seul_relais(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "1")
    monkeypatch.delenv("CLOUDFLARE_EDGE_SECRET", raising=False)
    monkeypatch.delenv("TRUST_CLOUDFLARE_HEADERS", raising=False)


def test_une_ipv4_compte_telle_quelle():
    assert geo_service.cle_de_comptage(_requete("41.200.1.1")) == "41.200.1.1"


def test_les_adresses_d_un_meme_slash64_partagent_la_cle():
    a = geo_service.cle_de_comptage(_requete("2a01:e0a:1:2::1"))
    b = geo_service.cle_de_comptage(_requete("2a01:e0a:1:2:ffff::14"))
    assert a == b == "2a01:e0a:1:2::/64"
    assert geo_service.cle_de_comptage(_requete("2a01:e0a:1:3::1")) != a


def test_une_ipv4_notee_en_ipv6_n_est_pas_regroupee_avec_les_autres():
    a = geo_service.cle_de_comptage(_requete("::ffff:41.200.1.1"))
    b = geo_service.cle_de_comptage(_requete("::ffff:41.200.1.2"))
    assert (a, b) == ("41.200.1.1", "41.200.1.2")


def test_ip_inconnue_donne_aucune_cle():
    assert geo_service.cle_de_comptage(_requete("10.9.9.9")) is None
    assert geo_service.cle_de_comptage(_requete("pas-une-ip")) is None
