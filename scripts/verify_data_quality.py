#!/usr/bin/env python3
"""
Script de vérification de la qualité des données ZLECAf
"""
import numpy as np
import pandas as pd


def verify_data_quality():
    # Lire les données
    df = pd.read_csv("/app/ZLECAF_54_PAYS_DONNEES_COMPLETES.csv")

    print("=" * 80)
    print("🔍 ANALYSE DE QUALITÉ DES DONNÉES ZLECAF")
    print("=" * 80)

    # 1. Vérification cohérence PIB/Population/PIB par habitant
    print("\n1️⃣ VÉRIFICATION COHÉRENCE PIB/POPULATION/PIB_PAR_HABITANT")
    print("-" * 60)

    df["PIB_calc"] = (df["PIB_2024_Mds_USD"] * 1000) / df[
        "Population_2024_M"
    ]  # Conversion en USD par habitant
    df["ecart_pib"] = abs(df["PIB_calc"] - df["PIB_par_habitant_USD"])
    df["ecart_pct"] = (df["ecart_pib"] / df["PIB_par_habitant_USD"]) * 100

    # Pays avec écarts significatifs (>10%)
    incohérences_pib = df[df["ecart_pct"] > 10][
        [
            "Pays",
            "PIB_2024_Mds_USD",
            "Population_2024_M",
            "PIB_par_habitant_USD",
            "PIB_calc",
            "ecart_pct",
        ]
    ]

    if not incohérences_pib.empty:
        print("❌ INCOHÉRENCES DÉTECTÉES (écart > 10%):")
        for _, row in incohérences_pib.iterrows():
            print(
                f"   • {row['Pays']}: PIB/hab donné = {row['PIB_par_habitant_USD']:,.0f} USD, calculé = {row['PIB_calc']:,.0f} USD (écart: {row['ecart_pct']:.1f}%)"
            )
    else:
        print("✅ Cohérence PIB/Population/PIB par habitant : OK")

    # 2. Vérification secteurs économiques (somme = 100%)
    print("\n2️⃣ VÉRIFICATION SECTEURS ÉCONOMIQUES (somme doit = 100%)")
    print("-" * 60)

    df["somme_secteurs"] = (
        df["Part_Secteur_1_Pct"] + df["Part_Secteur_2_Pct"] + df["Part_Secteur_3_Pct"]
    )
    secteurs_incorrects = df[abs(df["somme_secteurs"] - 100) > 1][
        ["Pays", "Part_Secteur_1_Pct", "Part_Secteur_2_Pct", "Part_Secteur_3_Pct", "somme_secteurs"]
    ]

    if not secteurs_incorrects.empty:
        print("❌ SECTEURS INCORRECTS (somme ≠ 100%):")
        for _, row in secteurs_incorrects.iterrows():
            print(
                f"   • {row['Pays']}: {row['Part_Secteur_1_Pct']}% + {row['Part_Secteur_2_Pct']}% + {row['Part_Secteur_3_Pct']}% = {row['somme_secteurs']}%"
            )
    else:
        print("✅ Sommes secteurs économiques : OK")

    # 3. Vérification valeurs aberrantes
    print("\n3️⃣ DÉTECTION VALEURS ABERRANTES")
    print("-" * 60)

    # PIB par habitant extrêmes
    pib_median = df["PIB_par_habitant_USD"].median()
    pib_extremes = df[
        (df["PIB_par_habitant_USD"] > pib_median * 10)
        | (df["PIB_par_habitant_USD"] < pib_median * 0.1)
    ]

    if not pib_extremes.empty:
        print("⚠️ PIB/HABITANT EXTRÊMES:")
        for _, row in pib_extremes.iterrows():
            print(
                f"   • {row['Pays']}: {row['PIB_par_habitant_USD']:,.0f} USD/hab (médiane africaine: {pib_median:.0f})"
            )

    # IDH hors limites (0-1)
    idh_incorrect = df[(df["IDH_2024"] < 0) | (df["IDH_2024"] > 1)]
    if not idh_incorrect.empty:
        print("❌ IDH HORS LIMITES (doit être 0-1):")
        for _, row in idh_incorrect.iterrows():
            print(f"   • {row['Pays']}: IDH = {row['IDH_2024']}")

    # 4. Incohérences géographiques/économiques
    print("\n4️⃣ VÉRIFICATIONS GÉOGRAPHIQUES ET ÉCONOMIQUES")
    print("-" * 60)

    # Pays avec populations suspectes
    pop_suspectes = []
    pays_ref = {
        "Nigeria": 218,
        "Éthiopie": 125,
        "Égypte": 110,
        "RD Congo": 95,
        "Tanzanie": 67,
        "Afrique du Sud": 59,
        "Kenya": 55,
        "Ouganda": 48,
        "Algérie": 47,
        "Soudan": 46,
        "Angola": 38,
        "Maroc": 37,
        "Ghana": 33,
        "Mozambique": 33,
        "Madagascar": 30,
        "Cameroun": 29,
        "Côte d'Ivoire": 29,
        "Niger": 26,
        "Burkina Faso": 23,
        "Mali": 22,
    }

    for pays, pop_ref in pays_ref.items():
        pays_data = df[df["Pays"] == pays]
        if not pays_data.empty:
            pop_actuelle = pays_data.iloc[0]["Population_2024_M"]
            ecart = abs(pop_actuelle - pop_ref) / pop_ref * 100
            if ecart > 20:  # Plus de 20% d'écart
                pop_suspectes.append(
                    f"   • {pays}: {pop_actuelle:.1f}M (référence ~{pop_ref}M, écart: {ecart:.1f}%)"
                )

    if pop_suspectes:
        print("⚠️ POPULATIONS SUSPECTES (écart >20% vs références):")
        for p in pop_suspectes:
            print(p)

    # 5. Analyse des rangs IDH
    print("\n5️⃣ VÉRIFICATION RANGS IDH AFRIQUE")
    print("-" * 60)

    # Vérifier cohérence IDH vs rang
    df_sorted = df.sort_values("IDH_2024", ascending=False)
    df_sorted["rang_calcule"] = range(1, len(df_sorted) + 1)

    rangs_incorrects = []
    for _, row in df_sorted.iterrows():
        if abs(row["Rang_Afrique_IDH"] - row["rang_calcule"]) > 5:  # Tolérance de 5 rangs
            rangs_incorrects.append(
                f"   • {row['Pays']}: Rang donné = {row['Rang_Afrique_IDH']}, rang calculé = {row['rang_calcule']} (IDH: {row['IDH_2024']})"
            )

    if rangs_incorrects:
        print("⚠️ RANGS IDH INCOHÉRENTS:")
        for r in rangs_incorrects[:10]:  # Afficher les 10 premiers
            print(r)

    # 6. Résumé des pays à priorité haute pour validation
    print("\n6️⃣ SYNTHÈSE - PAYS NÉCESSITANT VALIDATION URGENTE")
    print("-" * 60)

    pays_problemes = set()

    # Ajouter pays avec incohérences PIB
    if not incohérences_pib.empty:
        pays_problemes.update(incohérences_pib["Pays"].tolist())

    # Ajouter pays avec secteurs incorrects
    if not secteurs_incorrects.empty:
        pays_problemes.update(secteurs_incorrects["Pays"].tolist())

    # Ajouter pays avec valeurs extrêmes
    if not pib_extremes.empty:
        pays_problemes.update(pib_extremes["Pays"].tolist())

    # Pays à compléter
    pays_incomplete = df[df["Notes_Validation"] == "À compléter"]["Pays"].tolist()

    print("🔴 PRIORITÉ CRITIQUE (données incohérentes):")
    for pays in sorted(pays_problemes):
        print(f"   • {pays}")

    print(f"\n🟡 PRIORITÉ HAUTE (22 pays à compléter):")
    print(f"   {', '.join(pays_incomplete[:10])}...")

    # 7. Recommandations
    print("\n7️⃣ RECOMMANDATIONS DE VALIDATION")
    print("-" * 60)
    print("1. Vérifiez en PRIORITÉ les pays avec incohérences détectées ci-dessus")
    print("2. Pour les pays 'À compléter', utilisez les sources officielles:")
    print("   • PNUD (undp.org) pour IDH")
    print("   • Banque Mondiale (worldbank.org) pour PIB et population")
    print("   • Instituts nationaux de statistiques pour les secteurs")
    print("3. Validez la cohérence PIB = (PIB/hab × Population)")
    print("4. Vérifiez que la somme des secteurs = 100%")
    print("5. Contrôlez les valeurs extrêmes identifiées")

    print("\n✅ ANALYSE TERMINÉE")
    print("=" * 80)

    return df


if __name__ == "__main__":
    verify_data_quality()
