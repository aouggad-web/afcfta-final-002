#!/usr/bin/env bash
# Éthiopie — récupérer les 1 368 droits de douane perdus à la collecte.
#
# IL N'Y A AUCUN CODE À ÉCRIRE. Le collecteur éthiopien a DÉJÀ été corrigé
# (commit 322ea63, 18/09/2026) : il écartait les taux « non strictement
# positifs » (`tax_values[i] > 0`), ce qui supprimait chaque 0 % publié par le
# portail. Le test distingue désormais un zéro publié d'une cellule vide.
#
# Ce qui est périmé, c'est le CRAWL : `ETH_tariffs.json` a été extrait le
# 05/07/2026, soit AVANT la correction. Il suffit donc de relancer la collecte.
#
# POURQUOI CE SCRIPT S'EXÉCUTE AILLEURS. `customs.erca.gov.et` n'est joignable
# ni en direct depuis l'environnement d'intégration (connexion réinitialisée),
# ni par le relais de lecture (délai dépassé). Il faut une machine qui atteigne
# le portail éthiopien.
#
#     bash scripts/relancer_crawl_eth.sh            # collecte + contrôles
#     bash scripts/relancer_crawl_eth.sh --essai    # 5 chapitres, pour vérifier
#
# Le script NE COMMITTE RIEN et NE PUBLIE RIEN. Il collecte, mesure, et vous
# laisse juge : si le compte des zéros reste à 0, c'est que le portail a changé
# et il ne faut surtout pas publier.

set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRAWL="$RACINE/backend/data/crawled/ETH_tariffs.json"
ESSAI=""
[ "${1:-}" = "--essai" ] && ESSAI="--max-positions 200"

echo "── 0. Sauvegarde du crawl actuel ──"
cp "$CRAWL" "$CRAWL.avant" && echo "   $CRAWL.avant"

echo "── 1. Collecte au portail officiel (customs.erca.gov.et) ──"
cd "$RACINE/backend"
python3 -m crawlers.scrapling_engine.runner --country ETH $ESSAI

echo "── 2. Le zéro est-il revenu ? ──"
cd "$RACINE"
python3 - <<'PY'
import json, pathlib
avant = json.loads(pathlib.Path("backend/data/crawled/ETH_tariffs.json.avant").read_text())
apres = json.loads(pathlib.Path("backend/data/crawled/ETH_tariffs.json").read_text())

def compte(d):
    z = n = t = 0
    for x in d["sub_positions"]:
        dr = (x.get("taxes") or {}).get("DR")
        if dr is None:
            n += 1
            continue
        t += 1
        if dr.get("rate") == 0.0:
            z += 1
    return z, n, t

za, na, ta = compte(avant)
zb, nb, tb = compte(apres)
print(f"   avant : {za} droits à 0 % | {na} sans droit | {ta} captés | {len(avant['sub_positions'])} positions")
print(f"   après : {zb} droits à 0 % | {nb} sans droit | {tb} captés | {len(apres['sub_positions'])} positions")
if zb == 0:
    raise SystemExit(
        "\n   ✗ ARRÊT. Aucun droit à 0 % après la collecte : le portail a changé,\n"
        "     ou la session n'a pas abouti. NE PAS PUBLIER. Restaurer avec :\n"
        "     mv backend/data/crawled/ETH_tariffs.json.avant "
        "backend/data/crawled/ETH_tariffs.json"
    )
if len(apres["sub_positions"]) < len(avant["sub_positions"]) * 0.95:
    raise SystemExit(
        "\n   ✗ ARRÊT. La collecte a rendu nettement moins de positions qu'avant :\n"
        "     collecte incomplète. NE PAS PUBLIER, relancer."
    )
print(f"\n   ✓ {zb} droits à 0 % récupérés.")
PY

echo "── 3. Gate qualité ──"
cd "$RACINE/backend"
python3 -m crawlers.scrapling_engine.quality_gate \
    --candidate data/crawled/ETH_tariffs.json \
    --reference data/crawled/ETH_tariffs.json.avant || \
    echo "   (gate non concluant — lire sa sortie avant de publier)"

echo "── 4. Reconstruction du socle et diagnostic ──"
cd "$RACINE"
python3 scripts/build_socle.py | tail -3
python3 scripts/diagnostic_zeros_perdus.py --pays ETH

echo "── 5. Empreinte à reporter au registre ──"
python3 - <<'PY'
import hashlib, json, pathlib
chemin = pathlib.Path("backend/data/crawled/ETH_tariffs.json")
empreinte = hashlib.sha256(chemin.read_bytes()).hexdigest()
registre = pathlib.Path("backend/data/source_registry_v2.json")
d = json.loads(registre.read_text(encoding="utf-8"))
e = d["countries"]["ETH"]
e["sha256"] = empreinte
e["positions_count"] = len(json.loads(chemin.read_text())["sub_positions"])
e["retrieved_at"] = __import__("datetime").date.today().isoformat()
registre.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"   sha256 ETH : {empreinte}")
print(f"   positions  : {e['positions_count']}")
PY

echo "── 6. Tests ──"
python3 -m pytest backend/tests/test_dataset_hash_stores_agree.py \
                  backend/tests/test_taux_zero_est_une_donnee.py -q | tail -3

cat <<'FIN'

── TERMINÉ ──
Le diagnostic doit désormais classer ETH en LACUNE_REELLE, pas en
ZERO_IMPOSSIBLE. Si ce n'est pas le cas, ne publiez pas : dites-le.

À committer :
    backend/data/crawled/ETH_tariffs.json
    backend/data/source_registry_v2.json
    backend/socle/MANIFESTE.json

À supprimer avant de committer :
    backend/data/crawled/ETH_tariffs.json.avant
FIN
