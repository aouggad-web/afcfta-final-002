#!/usr/bin/env python3
"""
Téléchargement / mise à jour de la base MaxMind GeoLite2-Country
================================================================

La détection du pays de facturation (routage Stripe/Chargily) peut s'appuyer
sur une base GeoLite2 locale au lieu des en-têtes Cloudflare — utile quand
l'ingress de l'hébergeur (ex. Emergent) ne garantit pas le passage des
en-têtes personnalisés.

Prérequis (gratuits) :
  1. Compte MaxMind : https://www.maxmind.com/en/geolite2/signup
  2. Clé de licence : My Account > Manage License Keys
  3. export MAXMIND_LICENSE_KEY=votre_clé

Usage :
  python scripts/geoip_update.py                    # télécharge vers data/geoip/
  python scripts/geoip_update.py --dest /app/data   # destination personnalisée

Puis dans .env :
  GEOIP_DB_PATH=<dest>/GeoLite2-Country.mmdb

La base est mise à jour par MaxMind deux fois par semaine ; relancez ce script
périodiquement (cron hebdomadaire suffisant pour un usage pays-seulement).
"""

from __future__ import annotations

import argparse
import os
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

DOWNLOAD_URL = (
    "https://download.maxmind.com/app/geoip_download"
    "?edition_id=GeoLite2-Country&license_key={key}&suffix=tar.gz"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Met à jour GeoLite2-Country.mmdb.")
    parser.add_argument(
        "--dest",
        default="data/geoip",
        help="Répertoire de destination du .mmdb (défaut: data/geoip)",
    )
    args = parser.parse_args()

    key = os.environ.get("MAXMIND_LICENSE_KEY")
    if not key:
        print(
            "Erreur : MAXMIND_LICENSE_KEY manquante.\n"
            "Créez un compte gratuit sur maxmind.com/en/geolite2/signup puis :\n"
            "  export MAXMIND_LICENSE_KEY=votre_clé",
            file=sys.stderr,
        )
        return 1

    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "GeoLite2-Country.mmdb"

    url = DOWNLOAD_URL.format(key=key)
    print("Téléchargement de GeoLite2-Country depuis MaxMind…")
    try:
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            with urllib.request.urlopen(url, timeout=120) as resp:
                tmp.write(resp.read())
            tmp_path = tmp.name
    except Exception as exc:
        print(f"Erreur de téléchargement : {exc}", file=sys.stderr)
        print("Vérifiez la clé de licence et la connectivité réseau.", file=sys.stderr)
        return 1

    # L'archive contient GeoLite2-Country_YYYYMMDD/GeoLite2-Country.mmdb
    extracted = False
    with tarfile.open(tmp_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith("GeoLite2-Country.mmdb"):
                member_file = tar.extractfile(member)
                if member_file is None:
                    continue
                dest_file.write_bytes(member_file.read())
                extracted = True
                break
    os.unlink(tmp_path)

    if not extracted:
        print("Erreur : .mmdb introuvable dans l'archive téléchargée.", file=sys.stderr)
        return 1

    size_mb = dest_file.stat().st_size / (1024 * 1024)
    print(f"OK : {dest_file} ({size_mb:.1f} Mo)")
    print("\nDans votre .env :")
    print(f"  GEOIP_DB_PATH={dest_file.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
