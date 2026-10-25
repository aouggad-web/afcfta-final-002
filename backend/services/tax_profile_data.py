"""Lightweight tariff profile constants shared by services and socle build."""

#: Taux de TVA que la loi du pays connaît, quand ils sont établis sur texte.
#: Un taux collecté hors de cette liste n'est servi nulle part : socle
#: (scripts/build_socle.py), données normalisées
#: (scripts/normalize_crawled.py). Il reste à compléter, avec ce texte en note.
TAUX_TVA_LEGAUX = {
    "NGA": {
        "taux": (7.5, 0.0),
        "loi": "Le Nigeria Tax Act 2025 ne connaît que 7,5 % (s.148) et 0 % (s.187)",
        "fiche": "NGA_taux_TVA_2026-10-08.json",
    },
}


#: Gambie, Liberia, Sierra Leone : assiette de la TVA/GST à
#: l'importation selon la loi de chaque pays (fiche
#: CEDEAO_hors_UEMOA_prelevements_2026-10-12.json).
TVA_CEDEAO_HORS_UEMOA = {
    "GMB": (15.0, "Income and Value Added Tax Act 2012, s.142(3) et 171(1) : valeur en douane augmentée du droit "
                  "de douane, du droit d'accise « and any other fiscal charge (other than VAT) payable on the import »."),
    "LBR": (12.0, "Revenue Code, s.1004(d) : CIF augmenté du droit de douane, du customs service fee, de l'ECOWAS "
                  "Trade Levy et de l'accise ; taux 12 % (Tax Amendment Act 2024, appliqué depuis le 1er avril 2025). "
                  "La LRA annonce 13 % depuis le 1er mai 2026 pour les services ; pour les biens, le texte de la loi "
                  "de décembre 2025 n'a pas été obtenu."),
    "SLE": (15.0, "Goods and Services Tax Act 2009, s.14(3) et 26(1) : valeur en douane augmentée du droit de "
                  "douane, du customs service charge « or other tax or fiscal charge (other than GST) ». La NRA "
                  "(Tax Guide 2022) calcule la GST sur CIF + droit + accise seulement : la lettre de la loi est "
                  "retenue."),
}
#: Prélèvements nationaux ajoutés, avec leur réserve (code, libellé, taux, note).
PRELEVEMENTS_CEDEAO_HORS_UEMOA = {
    "LBR": [("CUF", "Customs User Fee", 1.5,
             "Revenue Code, s.1822(a) : « 1.5% of the CIF for all imports whether duty paid or not ». Réserve : "
             "l'OMC (WT/TPR/S/441, 2023, §3.32) décrit en pratique des frais forfaitaires au Freeport de Monrovia "
             "et 1,2 % du CIF aux autres points d'entrée, sans texte trouvé.")],
    "GMB": [("FT", "Processing Fee", 1.55,
             "Liste officielle de la GRA (FAQ douane) : « Processing Fee 1.55% of CIF ». Réserve : seul texte "
             "trouvé, la reg. 308 des Customs and Excise Regulations 2013, qui ne fixe ce taux que pour les "
             "véhicules importés en franchise."),
            ("PUA", "Prélèvement de l'Union africaine", 0.2,
             "Liste officielle de la GRA (FAQ douane) : « AU Levy- 0.20% of CIF ». Réserve : base légale "
             "nationale non trouvée ; non dû pour une origine de l'UA (décision de Kigali, 2016).")],
    "SLE": [("PUA", "Prélèvement de l'Union africaine", 0.2,
             "Finance Act 2017, s.38(1) : « a levy at the rate of 0.2% of their value […] Provided that this levy "
             "shall not apply to imports from African Union countries ». Réserve : absent du Tax Guide 2022 de la "
             "NRA et de l'examen OMC 2025, perception actuelle non confirmée.")],
}
