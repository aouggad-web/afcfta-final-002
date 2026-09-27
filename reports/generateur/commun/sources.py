"""Registre des sources de recherche et de consolidation statistique.

Chaque source est déclarée avec son accès (gratuit / payant), la variable d'environnement
qui porte sa clé éventuelle, et ce qu'elle apporte au rapport. Aucun secret n'est stocké
ici : les clés sont lues dans l'environnement au moment de la génération.

    python -m commun.sources          # état de chaque source (configurée ou non)
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    cle: str
    nom: str
    acces: str            # 'saas', 'gratuit', 'payant'
    apport: str
    env: str = ''         # variable d'environnement de la clé (vide : aucune clé requise)
    implementee: bool = False

    def configuree(self) -> bool:
        return not self.env or bool(os.environ.get(self.env))

    def statut(self) -> str:
        if not self.implementee:
            return 'à intégrer'
        if self.acces == 'payant' and not self.configuree():
            return 'non configurée'
        return 'disponible'


SOURCES = [
    # Données internes du SaaS (lues directement dans backend/)
    Source('saas_tarifs', 'SaaS · barèmes NPF (40 pays) et offres e-Tariff Book', 'saas', 'Droits NPF, taxes à l\'import, taux ZLECAf servis', implementee=True),
    Source('saas_calculateurs', 'SaaS · calculateurs DZA/EGY/KEN/MAR/ZAF', 'saas', 'Taux préférentiels effectivement servis', implementee=True),
    Source('saas_origine', 'SaaS · règles d\'origine (annexe 2, appendice IV)', 'saas', 'Règles par position, notes chimiques', implementee=True),
    Source('saas_opportunites', 'SaaS · module Opportunités (Algérie : BACI, filières, industrie ONS)', 'saas', 'Commerce, filières, valeur ajoutée', implementee=True),
    Source('saas_statuts', 'SaaS · matrice des statuts de mise en œuvre', 'saas', 'Ratification, offre, application par pays', implementee=True),
    # Sources publiques gratuites
    Source('oec', 'OEC · API tesseract (BACI HS 2017)', 'gratuit', 'Commerce bilatéral SH2/SH4/SH6', env='', implementee=True),
    Source('comtrade', 'UN Comtrade · API publique (preview)', 'gratuit', 'Contrôle des flux déclarés, données miroir', implementee=False),
    Source('wdi', 'Banque mondiale · WDI', 'gratuit', 'PIB, population, dépenses de santé, IDE', implementee=False),
    Source('faostat', 'FAOSTAT', 'gratuit', 'Production et bilans agricoles', implementee=False),
    Source('fred', 'FRED (Fed de Saint-Louis)', 'gratuit', 'Prix des matières premières, taux de change', env='FRED_API_KEY', implementee=False),
    # Sources payantes (abonnement requis) — feuille de route
    Source('oec_pro', 'OEC Pro', 'payant', 'Données SH6 récentes, prévisions, volumes', env='OEC_API_TOKEN', implementee=True),
    Source('trademap', 'ITC Trade Map', 'payant', 'Commerce mensuel et SH8/SH10 national, tarifs appliqués', env='ITC_TRADEMAP_KEY'),
    Source('argus_cru', 'Argus / CRU', 'payant', 'Prix des engrais, de l\'ammoniac et des produits chimiques', env='ARGUS_API_KEY'),
    Source('fret', 'Drewry / Xeneta', 'payant', 'Taux de fret conteneur par corridor', env='XENETA_API_KEY'),
    Source('euromonitor', 'Euromonitor Passport', 'payant', 'Tailles de marché grand public (cosmétiques, hygiène, pharmacie OTC)', env='EUROMONITOR_API_KEY'),
    Source('fitch', 'Fitch Solutions (BMI)', 'payant', 'Risque pays, prévisions sectorielles pharma et chimie', env='FITCH_API_KEY'),
    Source('credit', 'Coface / Allianz Trade', 'payant', 'Risque de crédit acheteur et évaluations pays', env='COFACE_API_KEY'),
    Source('spglobal', 'S&P Global Market Intelligence', 'payant', 'Données entreprises, capacités de production, prix', env='SPGLOBAL_API_KEY'),
]


def par_cle(cle: str) -> Source:
    return next(s for s in SOURCES if s.cle == cle)


def tableau() -> list:
    return [[s.nom, s.acces, s.statut(), s.apport] for s in SOURCES]


if __name__ == '__main__':
    for nom, acces, statut, _ in tableau():
        print(f'{statut:15} {acces:8} {nom}')
