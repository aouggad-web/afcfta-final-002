"""
Détection du pays de facturation à partir de l'IP client
========================================================

Sert au routage de paiement : une IP algérienne impose Chargily (contrôle des
changes), les autres partent vers Stripe.

Trois limites assumées, documentées ici pour éviter les fausses promesses :

1. **L'IP la plus à gauche de `X-Forwarded-For` est fournie par le client** et
   donc falsifiable. On lit la plus à droite, posée par le proxy de confiance —
   même convention que `middlewares/rate_limiter.py`. Cela suppose exactement un
   hop de confiance en frontal (`--forwarded-allow-ips` côté uvicorn).
2. **Aucune détection de VPN/proxy n'est faite ici.** Elle exige un service
   commercial (MaxMind Anonymous IP, IPQualityScore, IPinfo Privacy). On se
   contente d'enregistrer les signaux pour audit — voir `collect_signals()`.
3. **La source géo est optionnelle.** Si aucune n'est configurée, le pays est
   `None` et l'appelant retombe sur le choix explicite de l'utilisateur, plutôt
   que de bloquer un paiement sur une donnée absente.

Sources supportées, par ordre de priorité :
  - en-tête `CF-IPCountry` (Cloudflare en frontal — gratuit, fiable) ;
  - base MaxMind GeoLite2 locale si `GEOIP_DB_PATH` pointe vers un .mmdb
    (nécessite le paquet `geoip2`).
"""

from __future__ import annotations

import ipaddress
import logging
import os
from typing import Optional

from fastapi import Request

logger = logging.getLogger(__name__)

_reader = None
_reader_loaded = False


def client_ip(request: Request) -> Optional[str]:
    """IP client réelle, en ne faisant confiance qu'au dernier proxy.

    Retourne None si l'IP est absente, privée ou illisible — l'appelant doit
    traiter ce cas comme « pays inconnu », pas comme une fraude.
    """
    forwarded = request.headers.get("x-forwarded-for")
    raw = None
    if forwarded:
        # La plus à droite est posée par le proxy de confiance ; celles de
        # gauche sont contrôlées par le client et ne doivent pas être crues.
        raw = forwarded.split(",")[-1].strip()
    elif request.client:
        raw = request.client.host

    if not raw:
        return None
    try:
        parsed = ipaddress.ip_address(raw)
    except ValueError:
        return None
    if parsed.is_private or parsed.is_loopback or parsed.is_reserved:
        return None
    return str(parsed)


def _geoip_reader():
    """Charge (une seule fois) la base GeoLite2 si elle est configurée."""
    global _reader, _reader_loaded
    if _reader_loaded:
        return _reader
    _reader_loaded = True
    path = os.environ.get("GEOIP_DB_PATH")
    if not path or not os.path.exists(path):
        return None
    try:
        import geoip2.database

        _reader = geoip2.database.Reader(path)
        logger.info("GeoIP: base chargée depuis %s", path)
    except Exception as exc:
        logger.warning("GeoIP: base non chargée (%s) — détection pays désactivée", exc)
        _reader = None
    return _reader


def country_from_request(request: Request) -> Optional[str]:
    """Code pays ISO-2 en majuscules, ou None si indéterminable."""
    # 1. Cloudflare en frontal : en-tête posé par l'edge, non falsifiable par
    #    le client (Cloudflare écrase toute valeur entrante).
    cf = request.headers.get("cf-ipcountry")
    if cf and cf.upper() not in ("XX", "T1"):  # XX = inconnu, T1 = Tor
        return cf.upper()

    # 2. Base MaxMind locale, si configurée.
    reader = _geoip_reader()
    ip = client_ip(request)
    if reader and ip:
        try:
            return reader.country(ip).country.iso_code
        except Exception:
            return None
    return None


def collect_signals(request: Request, user: dict) -> dict:
    """Signaux conservés avec la tentative de paiement, pour audit a posteriori.

    Ne bloque rien : c'est une trace, pas un contrôle. Une incohérence entre le
    pays d'inscription et le pays de paiement mérite un coup d'œil humain, pas
    un refus automatique (voyage, expatriation, VPN d'entreprise sont légitimes).
    """
    ip = client_ip(request)
    detected = country_from_request(request)
    signup_country = user.get("signup_country")
    return {
        "ip": ip,
        "detected_country": detected,
        "signup_ip": user.get("signup_ip"),
        "signup_country": signup_country,
        "country_mismatch": bool(detected and signup_country and detected != signup_country),
        "via_cloudflare": bool(request.headers.get("cf-ipcountry")),
    }
