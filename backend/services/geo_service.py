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

import hmac
import ipaddress
import logging
import os
from typing import Optional

from fastapi import Request

logger = logging.getLogger(__name__)

_reader = None
_reader_loaded = False


def trusted_proxy_hops() -> int:
    """Nombre de relais de confiance placés devant l'application.

    Détermine quelle entrée de `X-Forwarded-For` porte l'IP du visiteur. La
    valeur dépend de l'hébergement et se règle **empiriquement** :
    appelez `/api/billing/geo-diagnostic` et comparez le `client_ip` renvoyé à
    votre adresse publique réelle (par ex. via api.ipify.org), en incrémentant
    `TRUSTED_PROXY_HOPS` jusqu'à ce que les deux coïncident.

    Défaut 1 : un seul relais, cas des déploiements simples.
    """
    try:
        return max(1, int(os.environ.get("TRUSTED_PROXY_HOPS", "1")))
    except (TypeError, ValueError):
        logger.warning("TRUSTED_PROXY_HOPS invalide — valeur 1 utilisée")
        return 1


def client_ip(request: Request) -> Optional[str]:
    """IP client réelle, en ne faisant confiance qu'aux relais en frontal.

    L'adresse est lue à `TRUSTED_PROXY_HOPS` positions de la fin de
    `X-Forwarded-For` — et non systématiquement à la dernière, qui n'est la
    bonne que derrière un unique relais. Voir `trusted_proxy_hops()` pour
    calibrer ce nombre.

    Retourne None si l'IP est absente, privée ou illisible — l'appelant doit
    traiter ce cas comme « pays inconnu », pas comme une fraude.
    """
    # Cloudflare prouvé : `CF-Connecting-IP` porte l'IP client réelle et est
    # posé par l'edge, donc plus sûr que de dénouer X-Forwarded-For.
    if cloudflare_is_trusted(request):
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            try:
                parsed_cf = ipaddress.ip_address(cf_ip.strip())
            except ValueError:
                parsed_cf = None
            if parsed_cf and not (
                parsed_cf.is_private or parsed_cf.is_loopback or parsed_cf.is_reserved
            ):
                return str(parsed_cf)

    forwarded = request.headers.get("x-forwarded-for")
    raw = None
    if forwarded:
        # Chaque proxy traversé ajoute à droite l'adresse dont il a reçu la
        # requête. Avec N relais de confiance en frontal, l'IP du visiteur est
        # donc à N positions de la fin — et non à la dernière, qui n'est la
        # bonne que s'il y a exactement un relais.
        #
        # Prendre systématiquement la dernière sur un hébergement à plusieurs
        # relais (cas d'Emergent, 3 hops) renvoie une adresse d'infrastructure,
        # identique pour tous les visiteurs : la géolocalisation devient fausse
        # et le compteur de débit se retrouve partagé par tout le monde.
        #
        # Les entrées à gauche de cette position sont fournies par le client et
        # ne doivent jamais être crues : l'index est borné pour qu'un client qui
        # rallonge la chaîne ne puisse pas se désigner lui-même.
        entries = [part.strip() for part in forwarded.split(",") if part.strip()]
        if entries:
            index = max(0, len(entries) - trusted_proxy_hops())
            raw = entries[index]
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
    if not path:
        # Aucune source géo voulue : silence normal, le sélecteur manuel prend
        # le relais.
        return None
    if not os.path.exists(path):
        # Intention explicite mais fichier absent : c'est une PANNE, pas une
        # configuration par défaut. Sans base, le pays retombe sur la valeur
        # déclarée par le client et le verrou Algérie devient contournable.
        # Cas typique : base téléchargée hors du dépôt puis effacée par le
        # `git clean` d'un déploiement.
        logger.error(
            "CRITIQUE: GEOIP_DB_PATH=%s est configurée mais le fichier est INTROUVABLE. "
            "La détection de pays est inactive : le verrou Algérie ne s'applique plus "
            "et le pays déclaré par le client fait foi. "
            "Réinstallez la base : python scripts/geoip_update.py --dest <dossier>",
            path,
        )
        return None
    try:
        import geoip2.database

        _reader = geoip2.database.Reader(path)
        logger.info("GeoIP: base chargée depuis %s", path)
    except Exception as exc:
        logger.error(
            "CRITIQUE: base GeoIP présente mais illisible (%s) — détection de pays "
            "inactive, le verrou Algérie ne s'applique plus.",
            exc,
        )
        _reader = None
    return _reader


def cloudflare_is_trusted(request: Request) -> bool:
    """Dit si les en-têtes `CF-*` de cette requête peuvent être crus.

    Cloudflare écrase bien `CF-IPCountry` pour le trafic qui passe par son
    edge — mais rien n'empêche quelqu'un d'appeler l'origine **directement** en
    forgeant l'en-tête. Le faire confiance sans preuve reviendrait à laisser
    n'importe qui déclarer son pays, et donc à contourner le verrou Algérie.

    Deux preuves acceptées, par ordre de robustesse :

    1. `CLOUDFLARE_EDGE_SECRET` : un secret partagé injecté par une Transform
       Rule Cloudflare dans l'en-tête `X-Edge-Secret`. Recommandé — il ne
       dépend d'aucune liste d'IP à tenir à jour.
    2. `TRUST_CLOUDFLARE_HEADERS=true` : à n'utiliser que si l'origine est
       réellement inaccessible hors de Cloudflare (pare-feu / Tunnel), car
       cette option fait confiance à l'en-tête sans le vérifier.

    Sans l'une des deux, les en-têtes `CF-*` sont ignorés : le pays devient
    indéterminé et l'on retombe sur le choix explicite de l'utilisateur.
    """
    secret = os.environ.get("CLOUDFLARE_EDGE_SECRET")
    if secret:
        provided = request.headers.get("x-edge-secret")
        return bool(provided) and hmac.compare_digest(provided, secret)
    return os.environ.get("TRUST_CLOUDFLARE_HEADERS", "false").lower() == "true"


def country_from_request(request: Request) -> Optional[str]:
    """Code pays ISO-2 en majuscules, ou None si indéterminable."""
    # 1. Cloudflare en frontal — uniquement si la provenance est prouvée.
    if cloudflare_is_trusted(request):
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
        "via_cloudflare": cloudflare_is_trusted(request),
    }
