"""Configuration des logs du backend, avec masquage des secrets passés en URL.

Plusieurs API amont exigent leur clé en paramètre d'URL (OEC : ``token``,
UN Comtrade : ``subscription-key``). Or ces URL atterrissent dans les journaux
par deux chemins :

1. httpx journalise chaque requête au niveau INFO, URL complète comprise ;
2. le texte d'une erreur httpx (``HTTPStatusError``…) contient l'URL, et le code
   le journalise tel quel (``logger.error(f"... {e}")``, ``exc_info=True``).

Le formateur ci-dessous masque ces paramètres dans la ligne finale, traceback
comprise : tout ce qui passe par le gestionnaire racine en profite, quel que
soit le module qui journalise. httpx et httpcore sont en outre relevés à
WARNING pour ne plus écrire une ligne par requête sortante.

Point 17 de l'audit (journal sans secret ni donnée personnelle) :

- les journaux d'uvicorn passent eux aussi par ce formateur, et sa ligne
  d'accès est coupée : elle écrivait l'adresse IP et la query string en clair.
  middlewares/access_log.py la remplace, sans IP ni query string ;
- chaque ligne porte l'identifiant de la requête en cours (``rid``) et une
  heure UTC à la milliseconde ;
- le masquage couvre aussi les jetons Bearer et Basic, les JWT, les clés à
  préfixe connu (Stripe, Supabase, GitHub), les identifiants dans une URL et
  d'autres paramètres d'URL (``token_hash`` des liens Supabase, ``code``,
  ``password``…), et réduit les adresses e-mail à leur domaine ;
- la ligne WebSocket d'uvicorn perd l'adresse du client et sa query string ;
- un retour à la ligne dans un message est échappé : un texte venu d'une
  requête ne peut pas fabriquer une fausse ligne de journal.
"""

import contextvars
import logging
import re
import time

# Uniquement dans une syntaxe de paramètre d'URL (précédé de ?, & ou #), pour
# ne pas toucher à une phrase ordinaire contenant « key= ».
_SECRET_QUERY_PARAM = re.compile(
    r"(?i)([?&#](?:token|access_token|refresh_token|api_key|apikey|key|subscription-key"
    r"|token_hash|code|password|secret|client_secret|signature|license_key)=)"
    r"[^&\s\"'#]+"
)
_BEARER = re.compile(r"(?i)\b((?:Bearer|Basic)\s+)[A-Za-z0-9._~+/-]{16,}=*")
# Clés brutes à préfixe connu : Stripe, Supabase, GitHub.
_CLE_BRUTE = re.compile(
    r"\b(?:[sr]k_(?:live|test)_[A-Za-z0-9]{8,}|whsec_[A-Za-z0-9]{8,}|sb_secret_[A-Za-z0-9_-]{8,}"
    r"|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"
)
# Identifiants dans une URL (redis://:motdepasse@hote, https://user:pass@hote).
_URL_IDENTIFIANTS = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^\s/@]*@")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*")
# Longueurs bornées : temps linéaire, même sur une ligne hostile. \w couvre
# l'Unicode (jöhn@exämple.dz, adresses en arabe) ; ni « / » ni « = » dans la
# partie locale, pour ne pas avaler un chemin ou un paramètre d'URL.
_EMAIL = re.compile(
    r"(?<![\w.!#$%&'*+^`{|}~-])[\w.!#$%&'*+^`{|}~-]{1,64}@((?:[\w-]{1,63}\.){1,8}[\w-]{2,63})"
)

_NIVEAUX = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_ALIAS = {"WARN": "WARNING", "FATAL": "CRITICAL"}

# Identifiant de la requête en cours, posé par middlewares/access_log.py.
request_id = contextvars.ContextVar("request_id", default="-")


def redact(text: str) -> str:
    """Masque les secrets (paramètres d'URL, Bearer, JWT) et réduit les e-mails au domaine."""
    text = _SECRET_QUERY_PARAM.sub(r"\1***", text)
    text = _BEARER.sub(r"\1***", text)
    text = _JWT.sub("***", text)
    text = _CLE_BRUTE.sub("***", text)
    text = _URL_IDENTIFIANTS.sub(r"\1***@", text)
    return _EMAIL.sub(r"***@\1", text)


class RedactingFormatter(logging.Formatter):
    """Formateur qui masque les secrets dans la ligne complète, traceback incluse."""

    converter = time.gmtime

    def formatMessage(self, record: logging.LogRecord) -> str:
        # En-tête et message seulement : la traceback, ajoutée ensuite par
        # format(), garde ses retours à la ligne.
        ligne = super().formatMessage(record).rstrip("\r\n")
        return ligne.replace("\r", "\\r").replace("\n", "\\n")

    def format(self, record: logging.LogRecord) -> str:
        record.rid = request_id.get()
        return redact(super().format(record))


def _niveau(level) -> str:
    """LOG_LEVEL accepté en minuscules (« info ») ; INFO si la valeur est inconnue."""
    valeur = str(level or "").strip().upper()
    valeur = _ALIAS.get(valeur, valeur)
    return valeur if valeur in _NIVEAUX else "INFO"


class SansAccesWebSocket(logging.Filter):
    """Retire l'adresse et la query string de la ligne WebSocket d'uvicorn.

    Uvicorn l'écrit sur « uvicorn.error » (« %s - "WebSocket %s" 403 »), et non
    sur « uvicorn.access » : la coupure de la ligne d'accès ne l'atteint pas.
    N'importe quel client la déclenche par une poignée de main sur /api/ws.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if (
            record.name.startswith("uvicorn")
            and isinstance(record.msg, str)
            and record.msg.startswith('%s - "WebSocket ')
            and isinstance(record.args, tuple)
            and len(record.args) >= 2
        ):
            chemin = str(record.args[1]).split("?", 1)[0]
            record.args = ("-", chemin, *record.args[2:])
        return True


def build_logging_config(level: str) -> dict:
    """Configuration ``dictConfig`` du backend (sortie console, secrets masqués)."""
    niveau = _niveau(level)
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": RedactingFormatter,
                "fmt": "%(asctime)s.%(msecs)03dZ [%(levelname)s] %(name)s rid=%(rid)s: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "filters": {
            "sans_acces_websocket": {"()": SansAccesWebSocket},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["sans_acces_websocket"],
            },
        },
        "loggers": {
            "httpx": {"level": "WARNING"},
            "httpx2": {"level": "WARNING"},
            "httpcore": {"level": "WARNING"},
            "httpcore2": {"level": "WARNING"},
            # En DEBUG, ces bibliothèques écriraient le corps des requêtes
            # (nom, e-mail, adresse de facturation).
            "pymongo": {"level": "INFO"},
            "stripe": {"level": "INFO"},
            "anthropic": {"level": "INFO"},
            "urllib3": {"level": "INFO"},
            # Sans gestionnaire propre : uvicorn et uvicorn.error remontent à
            # la racine, donc au formateur ci-dessus.
            "uvicorn": {"level": niveau, "propagate": True},
            # Ligne d'accès d'uvicorn coupée (adresse IP, query string) : sans
            # gestionnaire ni propagation, uvicorn ne l'écrit plus.
            "uvicorn.access": {"level": "WARNING", "propagate": False},
        },
        "root": {
            "level": niveau,
            "handlers": ["console"],
        },
    }
