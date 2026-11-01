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
"""

import logging
import re

# Uniquement dans une syntaxe de paramètre d'URL (précédé de ?, & ou #), pour
# ne pas toucher à une phrase ordinaire contenant « key= ».
_SECRET_QUERY_PARAM = re.compile(
    r"(?i)([?&#](?:token|access_token|refresh_token|api_key|apikey|key|subscription-key)=)"
    r"[^&\s\"'#]+"
)


def redact(text: str) -> str:
    """Remplace la valeur des paramètres d'URL secrets par ``***``."""
    return _SECRET_QUERY_PARAM.sub(r"\1***", text)


class RedactingFormatter(logging.Formatter):
    """Formateur qui masque les secrets dans la ligne complète, traceback incluse."""

    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def build_logging_config(level: str) -> dict:
    """Configuration ``dictConfig`` du backend (sortie console, secrets masqués)."""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": RedactingFormatter,
                "fmt": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            "httpx": {"level": "WARNING"},
            "httpcore": {"level": "WARNING"},
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }
