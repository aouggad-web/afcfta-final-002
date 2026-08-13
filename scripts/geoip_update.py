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
    # Sources alternatives : en fournir deux serait ambigu, argparse tranche.
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--url",
        help=(
            "URL d'archive .tar.gz à utiliser à la place de la clé de licence. "
            "Le portail MaxMind propose un lien de téléchargement à jeton "
            "(« Download GZIP ») : collez-le ici, entre guillemets. Pratique "
            "quand aucune clé de licence n'a été générée — mais le jeton expire, "
            "donc préférez MAXMIND_LICENSE_KEY pour les mises à jour régulières."
        ),
    )
    source.add_argument(
        "--from-file",
        help="Archive .tar.gz déjà téléchargée localement (aucun réseau requis).",
    )
    args = parser.parse_args()

    key = os.environ.get("MAXMIND_LICENSE_KEY")
    if not (key or args.url or args.from_file):
        print(
            "Erreur : aucune source indiquée. Trois possibilités :\n"
            "  1. export MAXMIND_LICENSE_KEY=votre_clé   (recommandé, réutilisable)\n"
            '  2. --url "<lien Download GZIP du portail MaxMind>"\n'
            "  3. --from-file GeoLite2-Country.tar.gz    (archive déjà récupérée)\n"
            "Compte gratuit : maxmind.com/en/geolite2/signup",
            file=sys.stderr,
        )
        return 1

    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / "GeoLite2-Country.mmdb"

    # Archive locale : rien à télécharger, on la lit sur place. `downloaded`
    # distingue les deux cas pour ne supprimer que ce que le script a créé —
    # effacer l'archive fournie par l'utilisateur serait une surprise.
    downloaded = False
    if args.from_file:
        # expanduser : « ~/GeoLite2.tar.gz » est une saisie naturelle en ligne de
        # commande. isfile plutôt qu'exists : un répertoire passerait le test et
        # échouerait plus loin sur un message d'extraction bien moins parlant.
        tmp_path = os.path.expanduser(args.from_file)
        if not os.path.isfile(tmp_path):
            print(f"Erreur : archive introuvable ou non lisible ({tmp_path})", file=sys.stderr)
            return 1
        print(f"Lecture de l'archive locale {tmp_path}…")
    else:
        url = args.url or DOWNLOAD_URL.format(key=key)
        origin = "le lien fourni" if args.url else "MaxMind"
        print(f"Téléchargement de GeoLite2-Country depuis {origin}…")
        # tmp_path est fixé AVANT le téléchargement : si urlopen échoue, le
        # fichier temporaire existe déjà (delete=False) et doit être supprimé.
        # Sans cela, un cron qui échoue régulièrement accumule des fichiers vides.
        tmp_fd = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
        tmp_path = tmp_fd.name
        try:
            with tmp_fd as tmp:
                with urllib.request.urlopen(url, timeout=120) as resp:
                    tmp.write(resp.read())
            downloaded = True
        except Exception as exc:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            print(f"Erreur de téléchargement : {exc}", file=sys.stderr)
            if args.url:
                print(
                    "Le jeton du lien MaxMind a pu expirer : régénérez-le depuis "
                    "le portail, ou utilisez une clé de licence.",
                    file=sys.stderr,
                )
            else:
                print("Vérifiez la clé de licence et la connectivité réseau.", file=sys.stderr)
            return 1

    # L'archive contient GeoLite2-Country_YYYYMMDD/GeoLite2-Country.mmdb
    # Écriture atomique : on écrit à côté puis on remplace d'un seul coup, pour
    # qu'une interruption ne laisse jamais un .mmdb tronqué que le backend
    # chargerait au démarrage suivant.
    staging = dest_file.with_suffix(".mmdb.part")
    extracted = False
    try:
        with tarfile.open(tmp_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("GeoLite2-Country.mmdb"):
                    member_file = tar.extractfile(member)
                    if member_file is None:
                        continue
                    staging.write_bytes(member_file.read())
                    extracted = True
                    break
        if extracted:
            os.replace(staging, dest_file)
    except (tarfile.TarError, OSError) as exc:
        print(f"Erreur d'extraction : {exc}", file=sys.stderr)
        return 1
    finally:
        # Nettoyage systématique, y compris si l'extraction a échoué. L'archive
        # fournie via --from-file appartient à l'utilisateur : on n'y touche pas.
        leftovers = [staging]
        if downloaded:
            leftovers.append(tmp_path)
        for leftover in leftovers:
            try:
                os.unlink(leftover)
            except OSError:
                pass

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
