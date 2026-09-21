"""Lightweight tariff profile constants shared by services and socle build."""

# ── Per-country tax cascade profiles ──────────────────────────────────────────
# Each entry defines:
#   taxes_order: order in which taxes are applied
#   tax_bases:   {tax_code: ('BASE_FORMULA', [codes_already_computed_to_add])}
#     BASE_FORMULA = 'CIF'        → base = CIF value
#                   'DD_AMOUNT'   → base = the DD amount already computed (e.g. CAC)
#   source: official legal reference
#
# Rules are sourced from official customs legislation per country.
# ──────────────────────────────────────────────────────────────────────────────
_ECOWAS_CODED_CIF_DD = {  # shared coded profile; text-primary overrides live elsewhere
    "taxes_order": ["DD", "RS", "PCS", "TVA"],
    "tax_bases": {
        "DD": ("CIF", []),
        "RS": ("CIF", []),  # Redevance Statistique: base CIF (UEMOA)
        "PCS": ("CIF", []),  # Prélèvement Communautaire de Solidarité: base CIF
        "TVA": ("CIF", ["DD"]),  # TVA base = CIF + DD (OHADA/UEMOA practice)
    },
    "source": "TEC CEDEAO — TVA base = CIF+DD",
}
_CEMAC = {  # shared base profile for CEMAC members
    "taxes_order": ["DD", "TCI", "CAC", "TVA"],
    "tax_bases": {
        "DD": ("CIF", []),
        "TCI": ("CIF", []),  # Taxe Communautaire d'Intégration: base CIF
        "CAC": ("DD_AMOUNT", []),  # Centimes Additionnels Communaux: % of DD amount
        "TVA": ("CIF", ["DD", "TCI"]),  # Directive TVA CEMAC: base = CIF+DD+TCI
    },
    "source": "Tarif Extérieur Commun CEMAC — Directive TVA CEMAC art. 9",
}
_EAC = {  # EAC common profile (Kenya, Tanzania, Uganda, Rwanda, Burundi)
    "taxes_order": ["DD", "IDF", "RDL", "TVA"],
    "tax_bases": {
        "DD": ("CIF", []),
        "IDF": ("CIF", []),  # Import Declaration Fee: base CIF
        "RDL": ("CIF", []),  # Railway Development Levy: base CIF
        "TVA": ("CIF", ["DD"]),  # EAC Customs Management Act: base = CIF+DD
    },
    "source": "EAC Customs Management Act — VAT base = CIF+DD",
}
_IMPORT_VAT_CIF_DD = {
    "taxes_order": ["DD", "TVA"],
    "tax_bases": {
        "DD": ("CIF", []),
        "TVA": ("CIF", ["DD"]),
    },
}

#: Formule d'assiette exprimant une RÈGLE et non une énumération : la valeur en
#: douane augmentée de tous les droits et taxes perçus à l'entrée, la TVA seule
#: exclue de sa propre assiette. Énumérer les taxes concernées reviendrait à
#: réintroduire une liste qui se périme dès qu'un prélèvement apparaît — c'est
#: précisément ce qui rendait COUNTRY_TAX_PROFILES faux.
BASE_TVA_TOUTES_TAXES = "CIF_PLUS_TOUTES_TAXES_SAUF_TVA"

#: Assiette de la TVA à l'importation établie sur texte primaire archivé.
#:
#: Quatre textes ont été lus intégralement et disposent de la même règle, dans
#: des termes différents. Les profils ci-dessous appliquaient tous « CIF + DD »
#: à ces pays, ce qui ampute l'assiette de tous les autres prélèvements — dans
#: le cas tunisien en citant en référence l'article même qui les inclut.
#:
#: Les déterminations et leurs extraits sont archivés dans
#: backend/data/legal_refs/zlecaf_application/.
_TVA_TOUTES_TAXES = {
    "texte": (
        "Directive n° 02/98/CM/UEMOA du 22 décembre 1998, article 27 a) : "
        "« en ce qui concerne les importations par la valeur en douane majorée "
        "des droits et taxes perçus à l'entrée, à l'exception de la Taxe sur la "
        "Valeur Ajoutée elle-même »"
    ),
    "fiche": "UEMOA_assiette_TVA_2026-09-14.json",
}
ASSIETTE_TVA_ETABLIE = {
    iso: _TVA_TOUTES_TAXES
    for iso in (
        "BEN",
        "BFA",
        "CIV",
        "GNB",
        "MLI",
        "NER",
        "SEN",
        "TGO",
    )
}
ASSIETTE_TVA_ETABLIE["MRT"] = {
    "texte": (
        "Mauritanie, Code Général des Impôts, Livre II Titre I (TVA), chapitre 3 : "
        "« La base imposable pour les importations est constituée par la valeur "
        "définie par la législation douanière, y compris les taxes et prélèvements "
        "de toute nature perçus lors du franchissement du cordon douanier, à "
        "l'exception de la taxe sur la valeur ajoutée elle-même » — doctrine DGI "
        "(impots.gov.mr, Livre2-Titre1-TVA-20191010.pdf), texte lu et archivé"
    ),
    "fiche": "MRT_assiette_TVA_2026-09-17.json",
}
ASSIETTE_TVA_ETABLIE["MDG"] = {
    "texte": (
        "Madagascar, Code général des impôts, édition 2025 (CDI n° 2025-MEF/SG/DGI "
        "du 2025-02-06), article 06.01.11 : « La taxe est établie : 1° Sur la valeur "
        "des importations, y compris les frais et les taxes autres que la taxe sur la "
        "valeur ajoutée » — la TVA est donc assise sur la valeur en douane augmentée "
        "des droits et taxes d'entrée, TVA exclue de sa propre assiette"
    ),
    "fiche": "MDG_assiette_TVA_2026-09-21.json",
}
ASSIETTE_TVA_ETABLIE["KEN"] = {
    "texte": (
        "Kenya, Value Added Tax Act No. 35 of 2013, section 14 (1) (c) : « the "
        "amount of duty of customs », expression que la loi définit comme "
        "« import duty, excise duty, export duty, countervailing duty, levy, "
        "cess, tax or surtax charged under any law [...] relating to customs or "
        "excise » — la définition élargit l'alinéa bien au-delà du droit de douane"
    ),
    "fiche": "EAC_assiette_TVA_2026-09-14.json",
}
ASSIETTE_TVA_ETABLIE["UGA"] = {
    "texte": (
        "Ouganda, Value Added Tax Act Chapter 349, section 23 (b) : « the amount "
        "of customs duty, excise tax and any other fiscal charge other than tax "
        "payable on those goods », « tax » désignant la TVA elle-même"
    ),
    "fiche": "EAC_assiette_TVA_2026-09-14.json",
}
#: La Tunisie est délibérément ABSENTE de la table, bien que son texte soit lu
#: et archivé (Code de la TVA, article 6 § II-1 : « par la valeur en douane, tous
#: droits et taxes inclus à l'exclusion de la taxe sur la valeur ajoutée »,
#: fiche TUN_assiette_TVA_2026-09-14.json). Deux obstacles s'y opposent, et
#: chacun ferait servir une TVA sous-évaluée sous couvert d'un texte primaire :
#:
#:  1. Le même article soumet l'importateur NON ASSUJETTI à cette assiette
#:     majorée de 25 %. Le calculateur ne recueille pas le statut de
#:     l'importateur : il ne peut donc pas choisir la branche applicable.
#:  2. Les données tunisiennes portent 2 435 taxes à assiette QUANTITATIVE
#:     (droit sanitaire vétérinaire, prélèvements viande, taxe d'abattage —
#:     « 0.1 dinars » sur base QCS ou PN). Le moteur ne liquide que l'ad
#:     valorem : ces montants n'entrent pas dans computed_amounts, donc une
#:     assiette « tous droits et taxes inclus » les omettrait en silence.
#:     Aucun des dix autres pays de la table ne porte une seule de ces taxes,
#:     ce qui rend l'exception tunisienne mesurée et non prudentielle.
#:
#: Tant que l'un des deux tient, la règle ne peut pas être appliquée
#: honnêtement à la Tunisie : mieux vaut l'assiette codée, plus étroite mais
#: qui ne se réclame d'aucun texte, qu'une assiette qui cite l'article 6 en
#: en trahissant la portée.
ASSIETTE_TVA_NON_APPLICABLE = {
    "TUN": {
        "texte_lu": (
            "Tunisie, Code de la taxe sur la valeur ajoutée, article 6 § II-1 : "
            "« par la valeur en douane, tous droits et taxes inclus à l'exclusion "
            "de la taxe sur la valeur ajoutée »"
        ),
        "fiche": "TUN_assiette_TVA_2026-09-14.json",
        "obstacles": (
            "statut de l'importateur non recueilli (majoration de 25 % pour le "
            "non-assujetti) ; 2 435 taxes à assiette quantitative que le moteur "
            "ne liquide pas"
        ),
    }
}

#: Les trois orthographes sous lesquelles la TVA apparaît dans les profils.
_ALIAS_TVA = ("TVA", "T.V.A", "VAT")


COUNTRY_TAX_PROFILES = {
    # ── Algérie — DGD (douane.gov.dz / conformepro.dz) ───────────────────────
    # DAPS, DD : droits de douane (base CIF) — réduits sous ZLECAf
    # TCS : base CIF
    # TVA : base = CIF + DAPS + DD  (art. 21 CTCA)
    # PRCT (Précompte 2%) : calculé APRÈS la TVA, sur la valeur globale de la
    #   marchandise TVA incluse mais HORS DAPS = CIF + DD + TCS + TVA
    "DZA": {
        "taxes_order": ["DAPS", "DD", "TCS", "TVA", "PRCT"],
        "tax_bases": {
            "DAPS": ("CIF", []),
            "DD": ("CIF", []),
            "TCS": ("CIF", []),
            "TVA": ("CIF", ["DAPS", "DD"]),  # art. 21 CTCA
            "PRCT": (
                "CIF",
                ["DD", "TCS", "TVA"],
            ),  # Précompte : valeur globale TVA incluse, hors DAPS
        },
        "source": "douane.gov.dz — TVA base=CIF+DAPS+DD (art. 21 CTCA) ; Précompte 2% base=valeur globale TVA incluse hors DAPS",
    },
    # ── Maroc — ADII (douane.gov.ma) ──────────────────────────────────────────
    # DD, TPI : base = CIF
    # TVA : base = CIF + DD + TPI  (CGI Maroc art. 96)
    "MAR": {
        "taxes_order": ["DD", "TPI", "TVA"],
        "tax_bases": {
            "DD": ("CIF", []),
            "TPI": ("CIF", []),
            "TVA": ("CIF", ["DD", "TPI"]),  # CGI Maroc art. 96
        },
        "source": "douane.gov.ma — CGI Maroc art. 96 (TVA base = CIF+DD+TPI)",
    },
    # ── Ghana — UNIPASS/ICUMS (external.unipassghana.com) ────────────────────
    # DD, ECOWAS Levy : base = CIF
    # GETFUND, NHIL, VAT : base = CIF + DD + ECOWAS  (VAT Act 870)
    "GHA": {
        "taxes_order": ["DD", "CEDEAO", "TVA", "NHIL", "GETFUND"],
        "tax_bases": {
            "DD": ("CIF", []),
            "CEDEAO": ("CIF", []),
            "TVA": ("CIF", ["DD", "CEDEAO"]),  # VAT Act 870 s.7
            "NHIL": ("CIF", ["DD", "CEDEAO"]),  # NHIL Act
            "GETFUND": ("CIF", ["DD", "CEDEAO"]),  # GETFUND Act
        },
        "source": "UNIPASS Ghana — VAT Act 870 (VAT/NHIL/GETFUND base = CIF+DD+ECOWAS)",
    },
    # ── Nigeria — NCS (customs.gov.ng, ECOWAS CET) ───────────────────────────
    # DD, ECOWAS, CISS : base = CIF
    # VAT : base = CIF + DD  (VAITA Nigeria s.2)
    "NGA": {
        "taxes_order": ["DD", "CEDEAO", "CISS", "TVA"],
        "tax_bases": {
            "DD": ("CIF", []),
            "CEDEAO": ("CIF", []),
            "CISS": ("CIF", []),
            "TVA": ("CIF", ["DD"]),  # VAITA s.2
        },
        "source": "customs.gov.ng — VAITA Nigeria s.2 (VAT base = CIF+DD)",
    },
    # ── Afrique du Sud — SARS (sars.gov.za) ──────────────────────────────────
    # VAT : base = CIF + DD  (VAT Act s.13(2))
    # ── Afrique du Sud / SACU ─────────────────────────────────────────────────
    # Le droit de douane SACU s'assoit sur la valeur FOB — fret et assurance
    # internationaux exclus (Customs and Excise Act 91/1964, s.65-67 ;
    # corroboré par la politique SARS SC-CR-A-03 rév. 5). Le poser « CIF »
    # surestimait la base du fret et de l'assurance internationaux. La valeur
    # FOB ne se déduit pas de la valeur CIF : compute_tax_cascade exige
    # `fob_value` et refuse de liquider sans elle (fail-closed).
    # Voir backend/data/legal_refs/zlecaf_application/SACU_assiette_DD_2026-09-17.json.
    "ZAF": {
        "taxes_order": ["DD", "TVA"],
        "tax_bases": {
            "DD": ("FOB", []),
            "TVA": ("CIF", ["DD"]),  # VAT Act s.13(2) : base TVA = CIF+DD
        },
        "source": "Customs and Excise Act 91/1964 s.65-67 + SARS SC-CR-A-03 (DD base = FOB) ; VAT Act s.13(2) (TVA base = CIF+DD)",
    },
    # ── Afrique australe et océan Indien ─────────────────────────────────────
    # Les fichiers tarifaires de ces pays fournissent DD + TVA/IVA par ligne.
    # La taxe à la consommation à l'importation est assise sur CIF + DD.
    "ZMB": {**_IMPORT_VAT_CIF_DD, "source": "Zambia Revenue Authority — VAT on imports"},
    "ZWE": {**_IMPORT_VAT_CIF_DD, "source": "ZIMRA — VAT on imported goods"},
    "MOZ": {
        **_IMPORT_VAT_CIF_DD,
        "source": "Autoridade Tributária de Moçambique — IVA na importação",
    },
    "MUS": {**_IMPORT_VAT_CIF_DD, "source": "Mauritius Revenue Authority — VAT on imports"},
    "MDG": {
        **_IMPORT_VAT_CIF_DD,
        "source": "Direction Générale des Impôts Madagascar — TVA à l'importation",
    },
    # ── Malawi — RETIRÉ DE CETTE TABLE, ET C'EST VOULU ────────────────────────
    # L'entrée portait le profil génerique « TVA sur CIF+DD » sous la seule
    # mention « Malawi Revenue Authority — import VAT » : un nom d'autorité, pas
    # un article. Le Customs and Excise (Tariffs) (No. 3) Order, 2022 publie les
    # TAUX de l'accise, de la TVA et de l'Advance Income Tax (colonnes 10, 11 et
    # 12) et ne dit rien de leur assiette ; aucun texte malawien lu — Customs and
    # Excise Act (Cap. 42:01), s.111(2) et Schedule A — ne l'établit non plus.
    # Voir backend/data/legal_refs/zlecaf_application/
    # MWI_colonnes_remises_et_prix_normal_2026-09-19.json.
    # Laisser le profil ici faisait liquider la TVA malawienne sur une assiette
    # que personne n'a lue : un montant crédible et faux. Le droit de douane, lui,
    # tient son assiette du décret même et n'a jamais eu besoin de cette table.
    # ── Kenya / EAC — KRA (kra.go.ke) ────────────────────────────────────────
    # IDF (3.5%): base CIF  (Finance Act 2022)
    # VAT (16%): base = CIF + DD  (VAT Act Cap 476)
    "KEN": {**_EAC, "source": "kra.go.ke — VAT Act Cap 476 / Finance Act 2022"},
    # ── Tanzanie / EAC — TRA ──────────────────────────────────────────────────
    "TZA": {**_EAC, "source": "TRA Tanzania — VAT Act Cap 148"},
    # ── Ouganda / EAC — URA ───────────────────────────────────────────────────
    "UGA": {**_EAC, "source": "URA Uganda — VAT Act Cap 349"},
    # ── Rwanda / EAC — RRA ────────────────────────────────────────────────────
    "RWA": {**_EAC, "source": "RRA Rwanda — VAT Act Cap 349"},
    # ── Burundi / EAC — OBR ───────────────────────────────────────────────────
    "BDI": {**_EAC, "source": "OBR Burundi — EAC CMA"},
    # ── Égypte — ECA (customs.gov.eg/Services/Tarif) ───────────────────────────
    # TVA : base = CIF uniquement  (Loi n°67/2016 art. 29)
    "EGY": {
        "taxes_order": ["DD", "TVA"],
        "tax_bases": {
            "DD": ("CIF", []),
            "TVA": ("CIF", []),  # Loi 67/2016 art. 29: TVA base = CIF (pas CIF+DD)
        },
        "source": "Egyptian Customs Authority (customs.gov.eg/Services/Tarif) — Loi TVA n°67/2016 art. 29 (TVA base = CIF)",
    },
    # ── Éthiopie — ECC (customs.erca.gov.et) ─────────────────────────────────
    # SUR (Excise): base = CIF + DD
    # TVA (15%): base = CIF + DD + SUR  (Ethiopian Customs/Tax Authority)
    "ETH": {
        "taxes_order": ["DD", "SUR", "TVA"],
        "tax_bases": {
            "DD": ("CIF", []),
            "SUR": ("CIF", ["DD"]),  # Excise base = CIF + DD
            "TVA": ("CIF", ["DD", "SUR"]),  # VAT base = CIF + DD + Excise
        },
        "source": "customs.erca.gov.et — ERCA (TVA base = CIF+DD+SUR)",
    },
    # ── Tunisie — DGD (douane.gov.tn) ────────────────────────────────────────
    # TCL : base CIF
    # TVA : base = CIF + DD  (CTVA Tunisie art. 6)
    "TUN": {
        "taxes_order": ["DD", "TCL", "TVA"],
        "tax_bases": {
            "DD": ("CIF", []),
            "TCL": ("CIF", []),
            "TVA": ("CIF", ["DD"]),  # CTVA art. 6
        },
        "source": "douane.gov.tn — CTVA art. 6 (TVA base = CIF+DD)",
    },
    # ── UEMOA / CEDEAO members ────────────────────────────────────────────────
    "SEN": {**_ECOWAS_CODED_CIF_DD, "source": "douanes.sn / TEC CEDEAO — CGI Sénégal"},
    "CIV": {**_ECOWAS_CODED_CIF_DD, "source": "guce.gouv.ci / TEC CEDEAO — CGI Côte d'Ivoire"},
    "BEN": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO — CGI Bénin"},
    "BFA": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO — CGI Burkina Faso"},
    "MLI": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO — CGI Mali"},
    "NER": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO — CGI Niger"},
    "TGO": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO — CGI Togo"},
    "GIN": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO — CGI Guinée"},
    "GNB": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO — CGI Guinée-Bissau"},
    "GMB": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO"},
    "SLE": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO"},
    "LBR": {**_ECOWAS_CODED_CIF_DD, "source": "TEC CEDEAO"},
    # ── CEMAC members ─────────────────────────────────────────────────────────
    "CMR": {**_CEMAC, "source": "douanes.cm — Directive TVA CEMAC art. 9"},
    "GAB": {**_CEMAC, "source": "CEMAC Tarif des Douanes"},
    "COG": {**_CEMAC, "source": "CEMAC Tarif des Douanes"},
    "CAF": {**_CEMAC, "source": "CEMAC Tarif des Douanes"},
    "GNQ": {**_CEMAC, "source": "CEMAC Tarif des Douanes"},
    "TCD": {**_CEMAC, "source": "CEMAC Tarif des Douanes"},
}
