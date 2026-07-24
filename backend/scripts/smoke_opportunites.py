"""
Smoke-test du module Opportunités contre un backend démarré.

Déroule la chaîne complète pour un couple produit/producteur (par défaut :
noix de cajou brutes SH 080131, Guinée-Bissau) :

  1. ``GET /reports/health``        — disponibilité des briques de données ;
  2. ``GET /reports/oec-health``    — l'OEC répond-il (réseau/token) ;
  3. ``GET /reports/direct-export`` — S2 : marchés classés pour le producteur ;
  4. ``GET /reports/national-need`` — S3 : besoin national du meilleur marché ;
  5. ``GET /reports/opportunity``   — rapport bilatéral ultra-fin producteur → meilleur marché.

Chaque réponse JSON est sauvegardée dans ``--out-dir`` et un résumé lisible est
imprimé. Code retour 0 si tous les appels HTTP aboutissent (HTTP 200) ; l'OEC
injoignable n'est PAS une erreur (dégradation gracieuse assumée du module).

Usage (backend lancé sur :8000) :

    python -m scripts.smoke_opportunites
    python -m scripts.smoke_opportunites --hs-code 080132 --producer CIV --top-k 3
    python -m scripts.smoke_opportunites --destination DZA   # force GNB → Algérie
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional, Tuple


def _get(base_url: str, path: str, params: dict, timeout: int = 300) -> Tuple[int, dict]:
    """GET JSON ; retourne (status, payload). Lève en cas d'erreur réseau."""
    url = f"{base_url}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - hôte local/CI
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body[:2000]}
        return exc.code, payload


def _save(out_dir: Path, name: str, payload: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / name, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _fmt_score(value: Optional[float]) -> str:
    return f"{value:.3f}" if isinstance(value, (int, float)) else "indisponible"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000/api")
    parser.add_argument("--hs-code", default="080131", help="Produit (défaut : cajou brut)")
    parser.add_argument("--producer", default="GNB", help="Producteur ISO3 (défaut : GNB)")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--destination",
        default=None,
        help="Marché cible ISO3 pour S3 + bilatéral (défaut : meilleur marché classé par S2)",
    )
    parser.add_argument("--goods-value-usd", type=float, default=50000.0)
    parser.add_argument("--out-dir", default="test_reports/smoke_opportunites")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    failures = []

    def step(label: str, path: str, params: dict, filename: str) -> Optional[dict]:
        try:
            status, payload = _get(args.base_url, path, params)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"❌ {label}: connexion impossible ({exc})")
            failures.append(label)
            return None
        _save(out_dir, filename, payload)
        if status != 200:
            print(f"❌ {label}: HTTP {status}")
            failures.append(label)
            return None
        print(f"✅ {label}: HTTP 200 → {out_dir / filename}")
        return payload

    print(f"— Smoke-test Opportunités : {args.hs_code} depuis {args.producer} —\n")

    # 1) Santé des briques du moteur.
    step("Diagnostic moteur", "/reports/health", {}, "health.json")

    # 2) OEC joignable ? (informatif : le module dégrade proprement sans OEC)
    oec = step("Diagnostic OEC", "/reports/oec-health", {}, "oec_health.json")
    oec_reachable = bool(oec and oec.get("reachable"))
    print(f"   → OEC {'joignable' if oec_reachable else 'injoignable (dégradation gracieuse)'}\n")

    # 3) S2 — marchés classés pour le producteur.
    s2 = step(
        f"S2 direct-export {args.hs_code}/{args.producer}",
        "/reports/direct-export",
        {
            "hs_code": args.hs_code,
            "producer": args.producer,
            "top_k": args.top_k,
            "goods_value_usd": args.goods_value_usd,
        },
        "s2_direct_export.json",
    )

    best_market = None
    if s2:
        supply = s2.get("producer_supply", {})
        if supply.get("available"):
            detail = supply.get("detail", {})
            print(
                f"   → Production {args.producer} ({supply.get('commodity', '?')}) : "
                f"{detail.get('latest_value', '?')} {detail.get('unit', '')} "
                f"en {detail.get('latest_year', '?')} — rang Afrique {supply.get('rank', '?')}, "
                f"part continentale {supply.get('continental_share_pct', '?')} %"
            )
        else:
            print(f"   → Production {args.producer}: indisponible ({supply.get('reason', '?')})")
        ranked = s2.get("ranked_opportunities") or []
        for i, opp in enumerate(ranked[:3], start=1):
            need = opp.get("market_need", {})
            print(
                f"   {i}. {opp.get('destination_iso3')} — score "
                f"{_fmt_score(opp.get('end_to_end_score'))}, besoin estimé "
                f"{need.get('value', '?')} {need.get('unit', '')} (L{need.get('estimation_level', '?')})"
            )
        if ranked:
            best_market = ranked[0].get("destination_iso3")
        print()

    # Marché imposé par l'appelant (ex. --destination DZA) : prioritaire sur S2.
    if args.destination:
        best_market = args.destination.upper()

    # 4) S3 — besoin national du meilleur marché identifié.
    if best_market:
        s3 = step(
            f"S3 national-need {args.hs_code}/{best_market}",
            "/reports/national-need",
            {"hs_code": args.hs_code, "country": best_market},
            "s3_national_need.json",
        )
        if s3:
            est = s3.get("national_need", s3)
            print(
                f"   → Besoin {best_market}: {est.get('value', '?')} {est.get('unit', '')} "
                f"(niveau L{est.get('estimation_level', '?')}, "
                f"estimation : {est.get('is_estimation', '?')})\n"
            )

        # 5) Rapport bilatéral ultra-fin producteur → meilleur marché.
        ultra = step(
            f"Bilatéral ultra-fin {args.producer} → {best_market}",
            "/reports/opportunity",
            {
                "hs_code": args.hs_code,
                "origin": args.producer,
                "destination": best_market,
                "goods_value_usd": args.goods_value_usd,
                "mode": "ultra_fine",
            },
            "bilateral_ultra_fine.json",
        )
        if ultra:
            ci = ultra.get("composite_indicators", {})
            e2e = ci.get("end_to_end_score", {})
            summary = ultra.get("executive_summary", {})
            print(
                f"   → Score de bout en bout : {_fmt_score(e2e.get('score'))} "
                f"(couverture des poids : {e2e.get('weight_coverage', '?')})"
            )
            if summary:
                print(f"   → Priority tier : {summary.get('priority_tier', '?')}")
            print()
    else:
        print("⚠ Pas de marché classé par S2 → S3 et rapport bilatéral non déroulés.\n")

    if failures:
        print(f"❌ {len(failures)} étape(s) en échec : {', '.join(failures)}")
        return 1
    print(f"✅ Smoke-test terminé — réponses JSON dans {out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
