"""Un libellé emprunté à un autre tarif n'est pas la désignation du pays.

Pour l'Angola, le Mozambique et l'Égypte, le socle ajoute à la désignation un
libellé SH6 français et anglais emprunté à d'autres tarifs (``langues_empruntees``).
``texte_designation`` lit la langue demandée d'abord : sans ``designation_publiee``,
l'emprunt passait pour le texte du tarif. AGO 10061000 se lisait « Riz en paille
(riz paddy) de semence », libellé du Sénégal, au lieu du texte angolais.
"""

from services.designation import designation_publiee, libelle_sh6_emprunte, texte_designation

# Forme réelle d'une position angolaise du socle (AGO 10061000).
AGO = {
    "pt": "Arroz com casca (arroz paddy)",
    "verbatim": "Arroz com casca (arroz paddy)",
    "fr": "Riz en paille (riz paddy) de semence",
    "fr_source": "SEN — Tarif extérieur commun CEDEAO (Sénégal)",
    "en": "- Rice in the husk (paddy or rough)",
    "en_source": "KEN — EAC Common External Tariff (kra.go.ke)",
    "langues_empruntees": ["fr", "en"],
    "niveau_libelle_emprunte": "SH6",
}

# Le tarif égyptien est publié en arabe, et son libellé est vide : seuls les
# libellés empruntés disent quelque chose du produit.
EGY = {
    "ar": "",
    "verbatim": "",
    "fr": "Chevaux reproducteurs de race pure",
    "fr_source": "SEN — Tarif extérieur commun CEDEAO (Sénégal)",
    "en": "Pure-bred breeding animals",
    "en_source": "KEN — EAC Common External Tariff (kra.go.ke)",
    "langues_empruntees": ["fr", "en"],
    "niveau_libelle_emprunte": "SH6",
}


def test_l_emprunt_ne_passe_pas_pour_la_designation_du_pays():
    # Le défaut : lu tel quel, le libellé du Sénégal est celui de la position angolaise.
    assert texte_designation(AGO, "fr") == "Riz en paille (riz paddy) de semence"
    # Le texte publié par le tarif angolais fait foi, dans chaque langue de l'écran.
    publiee = designation_publiee(AGO)
    for langue in ("fr", "en", "ar"):
        assert texte_designation(publiee, langue) == "Arroz com casca (arroz paddy)"


def test_sans_libelle_national_un_tarif_n_en_recoit_pas_un_autre():
    publiee = designation_publiee(EGY)
    for langue in ("fr", "en", "ar"):
        assert texte_designation(publiee, langue) == ""


def test_le_texte_publie_n_est_jamais_retire_et_la_source_n_est_pas_modifiee():
    publiee = designation_publiee(AGO)
    assert publiee["pt"] == AGO["pt"] and publiee["verbatim"] == AGO["verbatim"]
    assert "fr" not in publiee and "en" not in publiee
    # La désignation du socle, elle, garde ses emprunts : la fonction en rend une copie.
    assert AGO["fr"] and AGO["en"] and AGO["langues_empruntees"] == ["fr", "en"]


def test_sans_emprunt_la_designation_est_inchangee():
    publiee = {"fr": "De veaux", "en": "Of calves", "verbatim": "De veaux"}
    assert designation_publiee(publiee) == publiee
    assert designation_publiee({**publiee, "langues_empruntees": []}) == {**publiee, "langues_empruntees": []}
    assert designation_publiee("Texte simple") == "Texte simple"
    assert designation_publiee(None) is None


def test_une_seule_langue_empruntee_laisse_l_autre_au_tarif():
    partiel = {
        "verbatim": "Chevaux de race pure",
        "fr": "Chevaux de race pure",
        "en": "Pure-bred breeding animals",
        "en_source": "KEN — EAC Common External Tariff (kra.go.ke)",
        "langues_empruntees": ["en"],
        "niveau_libelle_emprunte": "SH6",
    }
    publiee = designation_publiee(partiel)
    assert texte_designation(publiee, "fr") == "Chevaux de race pure"
    # L'anglais emprunté ne se lit pas ici : le texte publié le remplace.
    assert texte_designation(publiee, "en") == "Chevaux de race pure"


def test_l_emprunt_se_declare_avec_sa_source_et_son_niveau():
    assert libelle_sh6_emprunte(AGO) == {
        "niveau": "SH6",
        "fr": "Riz en paille (riz paddy) de semence",
        "fr_source": "SEN — Tarif extérieur commun CEDEAO (Sénégal)",
        "en": "- Rice in the husk (paddy or rough)",
        "en_source": "KEN — EAC Common External Tariff (kra.go.ke)",
    }
    # L'Égypte : le libellé national est vide, l'emprunt reste lisible, déclaré comme tel.
    assert libelle_sh6_emprunte(EGY)["fr"] == "Chevaux reproducteurs de race pure"
    assert libelle_sh6_emprunte(EGY)["en_source"].startswith("KEN")


def test_rien_d_emprunte_rien_a_declarer():
    assert libelle_sh6_emprunte({"fr": "De veaux", "verbatim": "De veaux"}) is None
    assert libelle_sh6_emprunte({"fr": "De veaux", "langues_empruntees": []}) is None
    assert libelle_sh6_emprunte("Texte simple") is None
    assert libelle_sh6_emprunte(None) is None


def test_une_langue_empruntee_sans_texte_n_est_pas_declaree():
    emprunt = libelle_sh6_emprunte({
        "langues_empruntees": ["fr", "en"],
        "fr": "",
        "en": "Pure-bred breeding animals",
        "en_source": "KEN — EAC Common External Tariff (kra.go.ke)",
    })
    assert "fr" not in emprunt and "fr_source" not in emprunt
    assert emprunt["en"] == "Pure-bred breeding animals"
    # Le niveau déclaré par le socle manque : l'emprunt est au SH6 par construction.
    assert emprunt["niveau"] == "SH6"
