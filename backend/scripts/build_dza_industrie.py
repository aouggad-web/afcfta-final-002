#!/usr/bin/env python3
"""
Industrie manufacturière algérienne 2016-2025 par branche de l'ONS
===================================================================
Construit data/json/dza_industrie.json à partir des comptes économiques de l'ONS
(data/sources/DZA/ons/comptes_economiques_2021_2024.json, extraits et contrôlés
par scripts/extract_ons_comptes_dza.py).

Chaque chiffre porte sa nature, jamais mélangée :
  • officiel         publié par l'ONS : comptes 2021-2024 (n° 1067), et total 2016-2020
                     repris tel quel par la Banque mondiale (WDI NV.IND.MANF.CN, identique
                     à l'ONS au million de DA près sur 2021-2024) ;
  • calcul_officiel  dérivé exactement de chiffres officiels : VA 2020 par branche =
                     VA 2021 aux prix de 2020 / (1 + croissance 2021) ; conversions en
                     dollars au taux de change moyen de la Banque mondiale ;
  • estimation       2025 seulement : croissance en volume par branche (fourchette et
                     confiance), valeurs aux prix et au taux de change de 2024 — aucune
                     hypothèse de prix 2025 n'est faite.
2016-2019 : seul le total est publié dans les sources disponibles ; la répartition par
branche n'est pas estimée.

Usage:
    python3 scripts/build_dza_industrie.py            # écrit le fichier
    python3 scripts/build_dza_industrie.py --dry-run  # contrôles seulement
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCE = os.path.join(RACINE, "data", "sources", "DZA", "ons", "comptes_economiques_2021_2024.json")
SORTIE = os.path.join(RACINE, "data", "json", "dza_industrie.json")

# Taux de change officiel moyen (DZD par USD), Banque mondiale WDI PA.NUS.FCRF
TAUX = {
    2016: 109.4431,
    2017: 110.973,
    2018: 116.5938,
    2019: 119.3536,
    2020: 126.7768,
    2021: 135.0641,
    2022: 141.995,
    2023: 135.8429,
    2024: 134.0532,
    2025: 131.6059,
}
# Total manufacturier 2016-2020 : ONS via Banque mondiale (NV.IND.MANF.CN, Md DA ; NV.IND.MANF.KD.ZG, %)
WDI_VA = {2016: 1364.762, 2017: 1545.515, 2018: 1605.422, 2019: 1478.683, 2020: 1313.154}
WDI_VOLUME = {2016: 4.7, 2017: 10.1, 2018: 2.4, 2019: 2.3, 2020: 3.4}
WDI_2024_MDA = 3413.452

SOURCES = {
    "ons_comptes": {
        "titre": "ONS, Les comptes économiques de 2021 à 2024, n° 1067 (août 2025)",
        "url": "https://www.ons.dz",
    },
    "wdi": {
        "titre": "Banque mondiale, World Development Indicators : NV.IND.MANF.CN, NV.IND.MANF.KD.ZG, PA.NUS.FCRF",
        "url": "https://api.worldbank.org/v2/country/DZA/indicator/NV.IND.MANF.CN?format=json",
    },
    "cnt_t1_2025": {
        "titre": "ONS, comptes nationaux trimestriels, 1er trimestre 2025 (n° 1063), repris par El Watan",
        "url": "https://elwatan.dz/etat-de-leconomie-nationale-au-1er-trimestre-2025-forte-hausse-des-importations-et-baisse-des-exportations/",
    },
    "cnt_t1_2025_bis": {
        "titre": "ONS, comptes nationaux trimestriels, 1er trimestre 2025, repris par Algérie Eco",
        "url": "https://algerie-eco.com/2025/07/14/croissance-economique-pib-hydrocarbures-exportations-importations-chiffres-premier-trimestre-2025/",
    },
    "cnt_t2_2025": {
        "titre": "ONS, comptes nationaux trimestriels, 2e trimestre 2025, repris par El Watan",
        "url": "https://elwatan.dz/situation-economique-au-deuxieme-trimestre-2025-recul-des-exportations-et-hausse-des-importations-selon-lons/",
    },
    "ipi_t2_2025": {
        "titre": "ONS, Indice de la production industrielle au 2e trimestre 2025 (secteur public national)",
        "url": "https://www.ons.dz",
    },
    "worldsteel": {
        "titre": "worldsteel, Steel Data Viewer : production d'acier brut, Algérie",
        "url": "https://worldsteel.org/mappingworld-api/?values=P1_crude_steel_total&lang=EN",
    },
    "opep": {
        "titre": "OPEP, Annual Statistical Bulletin 2026",
        "url": "https://publications.opec.org/ASSETS/assetdb/asb-2026.pdf",
    },
    "oica": {
        "titre": "OICA, 2025 Production Statistics",
        "url": "https://oica.net/wp-content/uploads/2025/11/prod-total-2025.pdf",
    },
    "usda": {
        "titre": "USDA, PSD Online : soja, Algérie",
        "url": "https://apps.fas.usda.gov/psdonline/downloads/psd_oilseeds_csv.zip",
    },
}

# (code, libellé FR, libellé EN, libellé de la branche dans la publication ONS, divisions CITI Rév. 4)
BRANCHES = [
    (
        "10-12",
        "Industries alimentaires et du tabac",
        "Food products, beverages and tobacco",
        "Industries alimentaires et du tabac",
        ["10", "11", "12"],
    ),
    (
        "13-14",
        "Textile, habillement et fourrures",
        "Textiles, wearing apparel and fur",
        "Industrie textile, de l'habillement et des fourrures",
        ["13", "14"],
    ),
    (
        "15",
        "Cuir et chaussure",
        "Leather and footwear",
        "Industrie du cuir et de la chaussure",
        ["15"],
    ),
    (
        "16-18",
        "Bois, papier et imprimerie",
        "Wood, paper and printing",
        "Fabrication d'articles en bois et en papier, imprimerie et reproduction",
        ["16", "17", "18"],
    ),
    (
        "19",
        "Raffinage et cokéfaction",
        "Coke and refined petroleum products",
        "Raffinage et cokéfaction",
        ["19"],
    ),
    (
        "20-22",
        "Chimie, pharmacie, caoutchouc et plastiques",
        "Chemicals, pharmaceuticals, rubber and plastics",
        "Industrie chimique, du caoutchouc et des plastiques",
        ["20", "21", "22"],
    ),
    (
        "23",
        "Ciment, verre, céramique et autres minéraux non métalliques",
        "Other non-metallic mineral products",
        "Fabrication d'autres produits minéraux non métalliques",
        ["23"],
    ),
    (
        "24-25",
        "Métallurgie et travail des métaux",
        "Basic metals and fabricated metal products",
        "Métallurgie, travail des métaux",
        ["24", "25"],
    ),
    (
        "28",
        "Machines et équipements",
        "Machinery and equipment",
        "Fabrication de machines et équipements",
        ["28"],
    ),
    (
        "26-bur",
        "Machines de bureau et matériel informatique",
        "Office machinery and computers",
        "Fabrication de machines de bureau et matériel informatique",
        ["26"],
    ),
    (
        "27",
        "Machines et appareils électriques",
        "Electrical equipment",
        "Fabrication de machines et appareils électriques",
        ["27"],
    ),
    (
        "26-com",
        "Équipements de communication et instruments médicaux",
        "Communication equipment and medical instruments",
        "Fabrication d'équipements de communication et d'instruments médicaux",
        ["26", "32"],
    ),
    (
        "29-33",
        "Autres industries manufacturières",
        "Other manufacturing",
        "Autres industries manufacturières",
        ["29", "30", "31", "32", "33"],
    ),
]
NOTE_CITI = (
    "Correspondance CITI indicative : la publication de l'ONS ne précise pas où est classé le "
    "matériel de transport (autres industries manufacturières ou machines et équipements)."
)

# Projection 2025 : croissance en volume (bas, central, haut), confiance, indicateurs et sources
P2025 = {
    "10-12": (
        2.5,
        5.5,
        7.5,
        "C",
        ["cnt_t1_2025", "ipi_t2_2025", "usda", "ons_comptes"],
        [
            "ONS, comptes trimestriels, T1 2025 : industries alimentaires et du tabac +5,6 %",
            "IPI du secteur public (40 % de la VA de la branche) : T1 2025 −10,1 %, T2 2025 −4,7 %",
            "USDA : trituration de soja 2025 +34,8 % (1 650 → 2 225 kt)",
            "Tendance officielle 2022-2024 : +9,8 %, +2,4 %, +5,2 %",
        ],
    ),
    "13-14": (
        4.0,
        7.3,
        10.0,
        "B",
        ["cnt_t1_2025_bis", "cnt_t2_2025", "ons_comptes"],
        [
            "ONS, comptes trimestriels : T1 2025 +5,9 %, T2 2025 +8,8 %",
            "Tendance officielle 2022-2024 : +6,7 %, +11,7 %, +10,3 %",
        ],
    ),
    "15": (
        8.0,
        12.5,
        15.5,
        "B",
        ["cnt_t1_2025", "cnt_t2_2025", "ons_comptes"],
        [
            "ONS, comptes trimestriels : T1 2025 +15,4 %, T2 2025 +9,6 %",
            "Tendance officielle 2022-2024 : +19,8 %, +6,5 %, +8,4 %",
        ],
    ),
    "16-18": (
        2.0,
        6.0,
        11.0,
        "C",
        ["ipi_t2_2025", "ons_comptes"],
        [
            "Pas de chiffre trimestriel 2025 publié dans les sources disponibles",
            "IPI du secteur public (22 % de la VA) : T1 2025 +91,1 %, T2 2025 +131,6 %, sur une base très faible",
            "Tendance officielle 2022-2024 : +10,9 %, +8,3 %, +5,8 %",
        ],
    ),
    "19": (
        -2.5,
        -1.0,
        2.0,
        "B",
        ["opep", "cnt_t1_2025", "cnt_t2_2025", "ipi_t2_2025"],
        [
            "OPEP : produits raffinés 2025 −2,2 % (681 → 666 kb/j)",
            "ONS, comptes trimestriels : T1 2025 −5,5 %, T2 2025 +9,0 %",
            "IPI raffinage (secteur public, 98 % de la VA) : T1 2025 −2,2 %, T2 2025 +6,2 %",
        ],
    ),
    "20-22": (
        0.0,
        5.0,
        11.0,
        "C",
        ["cnt_t2_2025", "ipi_t2_2025", "ons_comptes"],
        [
            "ONS, comptes trimestriels : T2 2025 +11,0 % (T1 2025 non repris par la presse)",
            "IPI chimie (secteur public, 66 % de la VA) : T1 2025 −11,1 %, T2 2025 +2,5 %",
            "IPI produits pharmaceutiques (public) : T1 2025 −15,1 %, T2 2025 +7,3 %",
            "Tendance officielle 2022-2024 : +9,3 %, +5,2 %, +4,5 %",
        ],
    ),
    "23": (
        7.0,
        9.9,
        12.5,
        "B",
        ["cnt_t1_2025_bis", "cnt_t2_2025", "ipi_t2_2025", "ons_comptes"],
        [
            "ONS, comptes trimestriels : T1 2025 +9,9 %, T2 2025 +9,9 %",
            "IPI liants hydrauliques (ciment, public) : T1 2025 +0,5 %, T2 2025 +15,3 %",
            "Tendance officielle 2022-2024 : +19,4 %, +8,2 %, +8,2 %",
        ],
    ),
    "24-25": (
        8.0,
        16.0,
        21.0,
        "C",
        ["worldsteel", "ipi_t2_2025", "ons_comptes"],
        [
            "worldsteel : acier brut 2025 +20,8 % (4 520 → 5 460 kt)",
            "IPI sidérurgie (secteur public) : T1 2025 −59,2 %, T2 2025 −0,1 %",
            "L'acier domine la branche (production brute 2024 : 2 762 M USD, du même ordre que 4,5 Mt d'acier) ; "
            "le travail des métaux (CITI 25) n'a pas d'indicateur 2025",
            "Tendance officielle 2022-2024 : +2,2 %, +6,1 %, +7,8 %",
        ],
    ),
    "28": (
        0.0,
        5.0,
        10.0,
        "C",
        ["ipi_t2_2025", "ons_comptes"],
        [
            "Pas d'indicateur 2025 propre à la branche",
            "IPI ISMMEE (secteur public) : T1 2025 −41,7 %, T2 2025 −1,8 %",
            "Tendance officielle 2022-2024 : +2,0 %, +11,1 %, +4,6 %",
        ],
    ),
    "26-bur": (
        -3.0,
        0.0,
        5.0,
        "C",
        ["cnt_t1_2025_bis", "ons_comptes"],
        [
            "ONS, comptes trimestriels : T1 2025 −0,6 %",
            "Tendance officielle 2022-2024 : +1,3 %, +12,7 %, +3,9 %",
        ],
    ),
    "27": (
        -5.0,
        2.0,
        8.0,
        "C",
        ["ons_comptes"],
        [
            "Pas d'indicateur 2025 propre à la branche ; 2024 : −4,8 %",
            "Tendance officielle 2022-2024 : +5,7 %, +10,9 %, −4,8 %",
        ],
    ),
    "26-com": (
        0.0,
        4.0,
        10.0,
        "C",
        ["ons_comptes"],
        [
            "Pas d'indicateur 2025 propre à la branche",
            "Tendance officielle 2022-2024 : +1,9 %, +16,5 %, +2,1 %",
        ],
    ),
    "29-33": (
        9.0,
        13.7,
        18.0,
        "B",
        ["cnt_t1_2025_bis", "cnt_t2_2025", "oica", "ons_comptes"],
        [
            "ONS, comptes trimestriels : T1 2025 +14,4 %, T2 2025 +13,0 %",
            "OICA : véhicules produits en 2025 +43,0 % (30 108 → 43 052), si la branche les inclut",
            "Tendance officielle 2022-2024 : +16,0 %, +9,1 %, +3,6 %",
        ],
    ),
}
METHODE_2025 = (
    "Croissance en volume 2025 par branche : comptes trimestriels 2025 de l'ONS (tous secteurs) quand la presse "
    "les reprend, sinon indicateurs physiques annuels (worldsteel, OPEP, OICA, USDA) et IPI du secteur public "
    "lu selon sa part dans la VA de la branche ; à défaut, tendance officielle 2022-2024. La fourchette couvre "
    "l'écart entre ces indicateurs. Valeurs aux prix et au taux de change de 2024 : aucune hypothèse de prix "
    "2025. Confiance B : deux trimestres 2025 publiés et concordants ; C : indicateurs partiels ou indirects. "
    "À remplacer par les comptes économiques 2025 de l'ONS dès leur parution."
)


def charger():
    with open(SOURCE, encoding="utf-8") as f:
        src = json.load(f)
    comptes = {}
    for r in src["comptes"]:
        comptes.setdefault((r["annee"], r["branche"]), {})[r["secteur"]] = r
    volume = {(r["annee"], r["branche"]): r for r in src["volume"]}
    return src["meta"], comptes, volume


def fourchette(base, bas, central, haut):
    return {
        "bas": round(base * (1 + bas / 100), 1),
        "central": round(base * (1 + central / 100), 1),
        "haut": round(base * (1 + haut / 100), 1),
    }


def construire():
    meta_ons, comptes, volume = charger()
    branches = []
    for code, fr, en, nom, citi in BRANCHES:
        annees = {}
        v21 = volume[(2021, nom)]
        va20 = v21["va_prix_prec"] / (1 + v21["volume_pct"] / 100)
        annees["2020"] = {
            "nature": "calcul_officiel",
            "sources": ["ons_comptes"],
            "va_mda": round(va20 / 1000, 1),
            "va_musd": round(va20 / TAUX[2020], 1),
            "methode": (
                f"VA 2021 aux prix de 2020 ({v21['va_prix_prec']:,} M DA) divisée par 1 + croissance "
                f"2021 ({v21['volume_pct']} %)"
            ).replace(",", " "),
        }
        for an in (2021, 2022, 2023, 2024):
            t = comptes[(an, nom)]
            tot, pub, pri = t["TOTAL"], t["SNF publiques"], t["Entreprises privées"]
            v = volume[(an, nom)]
            annees[str(an)] = {
                "nature": "officiel",
                "statut_ons": meta_ons["statut"][str(an)],
                "sources": ["ons_comptes"],
                "production_brute_mda": round(tot["PB"] / 1000, 1),
                "va_mda": round(tot["VA"] / 1000, 1),
                "va_publique_mda": round(pub["VA"] / 1000, 1),
                "va_privee_mda": round(pri["VA"] / 1000, 1),
                "part_privee_va_pct": round(pri["VA"] / tot["VA"] * 100, 1),
                "remuneration_salaries_mda": round(tot["RS"] / 1000, 1),
                "croissance_volume_pct": v["volume_pct"],
                "prix_va_pct": v["prix_pct"],
                "production_brute_musd": round(tot["PB"] / TAUX[an], 1),
                "va_musd": round(tot["VA"] / TAUX[an], 1),
            }
        bas, central, haut, conf, srcs, indicateurs = P2025[code]
        a24 = annees["2024"]
        annees["2025"] = {
            "nature": "estimation",
            "confiance": conf,
            "sources": srcs,
            "base_prix": "prix et taux de change de 2024",
            "croissance_volume_pct": {"bas": bas, "central": central, "haut": haut},
            "va_mda": fourchette(a24["va_mda"], bas, central, haut),
            "production_brute_mda": fourchette(a24["production_brute_mda"], bas, central, haut),
            "va_musd": fourchette(a24["va_musd"], bas, central, haut),
            "production_brute_musd": fourchette(a24["production_brute_musd"], bas, central, haut),
            "indicateurs": indicateurs,
        }
        branches.append(
            {
                "code": code,
                "libelle_fr": fr,
                "libelle_en": en,
                "branche_ons": nom,
                "citi_rev4": citi,
                "note_citi": NOTE_CITI if code in ("28", "29-33") else "",
                "annees": annees,
            }
        )

    total = {}
    for an in range(2016, 2020):
        total[str(an)] = {
            "nature": "officiel",
            "sources": ["wdi"],
            "va_mda": WDI_VA[an],
            "va_musd": round(WDI_VA[an] * 1000 / TAUX[an], 1),
            "croissance_volume_pct": WDI_VOLUME[an],
        }
    s20 = sum(b["annees"]["2020"]["va_mda"] for b in branches)
    total["2020"] = {
        "nature": "officiel",
        "sources": ["wdi", "ons_comptes"],
        "va_mda": WDI_VA[2020],
        "va_musd": round(WDI_VA[2020] * 1000 / TAUX[2020], 1),
        "croissance_volume_pct": WDI_VOLUME[2020],
        "detail_par_branche": "calcul_officiel",
    }
    raff = next(b for b in branches if b["code"] == "19")
    for an in ("2021", "2022", "2023", "2024"):
        va = sum(b["annees"][an]["va_mda"] for b in branches)
        pb = sum(b["annees"][an]["production_brute_mda"] for b in branches)
        total[an] = {
            "nature": "officiel",
            "sources": ["ons_comptes"],
            "va_mda": round(va, 1),
            "production_brute_mda": round(pb, 1),
            "va_musd": round(va * 1000 / TAUX[int(an)], 1),
            "production_brute_musd": round(pb * 1000 / TAUX[int(an)], 1),
            "va_hors_raffinage_mda": round(va - raff["annees"][an]["va_mda"], 1),
        }
    t25 = {
        k: round(sum(b["annees"]["2025"]["va_mda"][k] for b in branches), 1)
        for k in ("bas", "central", "haut")
    }
    total["2025"] = {
        "nature": "estimation",
        "base_prix": "prix et taux de change de 2024",
        "va_mda": t25,
        "va_musd": {k: round(v * 1000 / TAUX[2024], 1) for k, v in t25.items()},
        "croissance_volume_pct": {
            k: round((v / total["2024"]["va_mda"] - 1) * 100, 1) for k, v in t25.items()
        },
        "note": "Somme des projections par branche ; les bornes de toutes les branches ne se réalisent pas ensemble.",
    }

    # contrôles
    erreurs = []
    if abs(s20 - WDI_VA[2020]) > 0.5:
        erreurs.append(f"2020 : somme des branches {s20:.1f} ≠ total officiel {WDI_VA[2020]}")
    if abs(total["2024"]["va_mda"] - WDI_2024_MDA) > 0.2:
        erreurs.append(f"2024 : somme des branches {total['2024']['va_mda']} ≠ WDI {WDI_2024_MDA}")
    return {
        "meta": {
            "titre": "Industrie manufacturière de l'Algérie par branche, 2016-2025",
            "pays": "DZA",
            "genere_le": date.today().isoformat(),
            "script": "backend/scripts/build_dza_industrie.py",
            "unites": {
                "_mda": "milliards de DA courants",
                "_musd": "millions de USD courants",
                "_pct": "pourcentage",
            },
            "natures": {
                "officiel": "chiffre publié par l'ONS (ou repris tel quel par la Banque mondiale)",
                "calcul_officiel": "dérivé exactement de chiffres officiels",
                "estimation": "projection 2025, avec fourchette, confiance et méthode ; à remplacer par les comptes 2025 de l'ONS",
            },
            "perimetre": (
                "13 branches manufacturières de l'ONS, raffinage compris (comme la VA manufacturière "
                "de la Banque mondiale) ; la VA hors raffinage est donnée à part"
            ),
            "limites": [
                "2016-2019 : seul le total est publié dans les sources disponibles ; pas de détail par branche.",
                "La production brute n'est publiée qu'à partir de 2021.",
                "2025 : estimation aux prix de 2024, en attendant les comptes économiques 2025 de l'ONS.",
            ],
            "methode_2025": METHODE_2025,
            "taux_change_dzd_usd": {
                "source": "Banque mondiale, WDI PA.NUS.FCRF (moyenne annuelle)",
                "valeurs": TAUX,
            },
            "sources": SOURCES,
        },
        "total": total,
        "branches": branches,
    }, erreurs


def main():
    donnees, erreurs = construire()
    t = donnees["total"]
    for an in ("2020", "2021", "2022", "2023", "2024"):
        print(an, "VA", t[an]["va_mda"], "Md DA =", t[an]["va_musd"], "M USD")
    print("2025", t["2025"]["croissance_volume_pct"], t["2025"]["va_musd"])
    if erreurs:
        print("\n".join(erreurs))
        sys.exit(1)
    if "--dry-run" not in sys.argv:
        with open(SORTIE, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=1)
        print("écrit :", os.path.relpath(SORTIE, RACINE))


if __name__ == "__main__":
    main()
