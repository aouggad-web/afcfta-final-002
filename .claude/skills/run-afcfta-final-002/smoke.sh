#!/usr/bin/env bash
# POST /api/calcul contre un backend déjà lancé, jeton CSRF compris.
#   .claude/skills/run-afcfta-final-002/smoke.sh [destination] [code] [origine] [cif]
# Sortie : statut HTTP, désignation, état, total, lignes NPF. Code de sortie ≠ 0 si HTTP ≠ 200.
set -euo pipefail
API=${API:-http://127.0.0.1:8000}
DEST=${1:-DZA} CODE=${2:-0201101100} ORIG=${3:-TUN} CIF=${4:-10000}
JAR=$(mktemp)
trap 'rm -f "$JAR" "$JAR.out"' EXIT

# Double soumission : le cookie csrf_token posé par n'importe quel GET doit revenir en en-tête.
curl -sf -c "$JAR" -o /dev/null "$API/api/health"
TOKEN=$(awk '$6 == "csrf_token" {print $7}' "$JAR")

STATUS=$(curl -s -o "$JAR.out" -w '%{http_code}' -b "$JAR" -H "X-CSRF-Token: $TOKEN" \
  -H 'Content-Type: application/json' -X POST "$API/api/calcul" \
  -d "{\"destination\":\"$DEST\",\"origine\":\"$ORIG\",\"code_sh\":\"$CODE\",\"valeur_cif\":$CIF,\"devise_cif\":\"USD\"}")
echo "HTTP $STATUS"
python3 - "$JAR.out" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
if "npf" not in d:
    print(json.dumps(d, ensure_ascii=False)[:600])
    sys.exit()
npf = d["npf"]
print(d["position"]["designation"])
print(f"{npf['etat']} — droits {npf['total_droits']} — à payer {npf['total_a_payer']}")
for l in npf["lignes"]:
    print(f"  {l['code']:<6} {l.get('taux_pct')!s:>6} %  {l.get('montant')}  ({l['statut']})")
for m in npf.get("manques", []):
    print(f"  manque : {json.dumps(m, ensure_ascii=False)[:160]}")
PY
[ "$STATUS" = 200 ]
