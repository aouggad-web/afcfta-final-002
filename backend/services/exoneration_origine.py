"""Prélèvements communautaires dont les marchandises originaires du bloc sont
exclues (fiche ORIGINE_prelevements_communautaires_2026-10-10.json) :

- PCS de l'UEMOA, acte additionnel n° 04/96, art. 17 : « Sont exclus de cette
  assiette : les produits originaires de l'Union » ;
- prélèvement communautaire de la CEDEAO (PCC, ECOWAS Levy), protocole
  A/P1/7/96, art. 4 : le champ « ne comprend pas a) les produits originaires de
  la CEDEAO » ;
- prélèvement de 0,2 % de l'Union africaine (PUA, AU Import Levy), décision
  Assembly/AU/Dec.605(XXVII) : « eligible goods originating from a non-Member
  State » ;
- prélèvement confédéral de l'AES (PC-AES), décision du Collège des Chefs
  d'État du 28/03/2025 (connue par la presse), art. 4 : sont exclues « les
  marchandises originaires de l'AES » et celles « obtenues ou produites dans un
  Etat membre d'une union douanière avec les pays de l'AES », donc de l'UEMOA ;
- contribution communautaire d'intégration de la CEEAC (CCI, 0,4 %), perçue sur
  les « marchandises importées des pays tiers » (DGDDI du Gabon) ;
- prélèvement OHADA (0,05 %), règlement n° 002/2003/CM : assis sur les
  « produits originaires des pays tiers à l'OHADA » (arrêté congolais n° 5808
  du 20/09/2005, art. 3) ; au Congo, les originaires des communautés dont il
  est membre (CEMAC, CEEAC) en sont aussi exonérés (même arrêté, art. 2).

Le socle marque ces lignes (« exoneration_origine ») ; la route les retire
quand l'origine déclarée appartient au bloc. Sans origine, elles restent dues,
comme pour un pays tiers."""

from constants import AFRICAN_COUNTRIES
from services.regional_blocs import ECOWAS, UEMOA

BLOCS = {
    "UEMOA": UEMOA,
    "CEDEAO": ECOWAS,
    "UA": frozenset(c["iso3"] for c in AFRICAN_COUNTRIES),
    "AES_UEMOA": frozenset({"BFA", "MLI", "NER"}) | UEMOA,
    # Le Rwanda s'est retiré de la CEEAC le 7 juin 2025.
    "CEEAC": frozenset({"AGO", "BDI", "CMR", "CAF", "COG", "COD", "GAB", "GNQ", "STP", "TCD"}),
    "OHADA": frozenset({
        "BEN", "BFA", "CMR", "CAF", "COM", "COG", "CIV", "GAB", "GIN", "GNB", "GNQ", "MLI", "NER", "COD", "SEN",
        "TCD", "TGO",
    }),
}
BLOCS["OHADA_CEEAC"] = BLOCS["OHADA"] | BLOCS["CEEAC"]


def appliquer(position: dict, origine):
    """Rendre (position, exonérations) : la position sans les prélèvements dont
    l'origine est exonérée, et la liste de ce qui a été retiré."""
    origine = (origine or "").strip().upper()
    if not origine:
        return position, []
    gardes, retires = [], []
    for droit in position.get("droits") or []:
        bloc = droit.get("exoneration_origine")
        if bloc and origine in BLOCS.get(bloc, ()):
            retires.append({"code": droit.get("code"), "bloc": bloc, "origine": origine})
        else:
            gardes.append(droit)
    if not retires:
        return position, []
    return {**position, "droits": gardes}, retires
