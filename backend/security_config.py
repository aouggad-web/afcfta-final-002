"""Contrôle des secrets au démarrage (constat E3 de l'audit de sécurité).

Deux valeurs pilotent la sécurité des comptes :

- ``JWT_SECRET`` signe les sessions. S'il vaut une valeur d'exemple publiée
  dans le dépôt, ou s'il est trop court, n'importe qui peut fabriquer une
  session au nom de n'importe quel utilisateur. En production, le serveur
  refuse alors de démarrer.
- ``ADMIN_PASSWORD`` amorce le compte admin. Une valeur d'exemple ou trop
  courte n'est jamais appliquée, et le compte est verrouillé si c'est déjà
  son mot de passe (voir ``server._seed_admin_account``).
"""

import logging
from typing import Mapping, Optional

logger = logging.getLogger(__name__)

JWT_SECRET_MIN_LENGTH = 32
ADMIN_PASSWORD_MIN_LENGTH = 12

# Valeurs d'exemple publiées dans le dépôt (.env.example,
# docs/emergent.env.template), comparées en minuscules.
_EXEMPLES = {
    "your-jwt-secret-min-32-chars",
    "changez-moi-32-caracteres-minimum",
    "change-me-strong-password",
    "changez-moi-mot-de-passe-fort",
}

GENERER = 'python -c "import secrets; print(secrets.token_urlsafe(48))"'


def est_valeur_exemple(valeur: str) -> bool:
    v = valeur.strip().lower()
    return v in _EXEMPLES or "changez-moi" in v or "change-me" in v or v.startswith("your-")


def probleme_jwt_secret(secret: Optional[str]) -> Optional[str]:
    """Défaut de ``JWT_SECRET``, ou None. Absent : comptes déjà désactivés (503)."""
    if not secret:
        return None
    if est_valeur_exemple(secret):
        return "valeur d'exemple publique"
    if len(secret) < JWT_SECRET_MIN_LENGTH:
        return f"trop court ({len(secret)} caractères, minimum {JWT_SECRET_MIN_LENGTH})"
    return None


def probleme_mot_de_passe_admin(mot_de_passe: str) -> Optional[str]:
    if est_valeur_exemple(mot_de_passe):
        return "valeur d'exemple publique"
    if len(mot_de_passe) < ADMIN_PASSWORD_MIN_LENGTH:
        return f"trop court (minimum {ADMIN_PASSWORD_MIN_LENGTH} caractères)"
    return None


def imposer_jwt_secret(env: Mapping[str, str]) -> None:
    """Refuse de démarrer en production avec un ``JWT_SECRET`` faible."""
    probleme = probleme_jwt_secret(env.get("JWT_SECRET"))
    if probleme is None:
        return
    message = f"JWT_SECRET refusé : {probleme}. Générez-en un avec : {GENERER}"
    if env.get("APP_ENV", "development") == "production":
        raise RuntimeError(message)
    logger.critical(message)
