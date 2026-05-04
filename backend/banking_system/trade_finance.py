"""
Trade finance instruments available for AfCFTA commercial operations.
"""

from typing import List, Optional
from .models import TradeFinanceInstrument

# ---------------------------------------------------------------------------
# CATALOGUE OF TRADE FINANCE INSTRUMENTS
# ---------------------------------------------------------------------------

TRADE_FINANCE_INSTRUMENTS: List[TradeFinanceInstrument] = [
    TradeFinanceInstrument(
        code="LC_IRREVOCABLE",
        name="Irrevocable Documentary Letter of Credit",
        name_fr="Crédit Documentaire Irrévocable (L/C)",
        description=(
            "Engagement bancaire irrévocable de paiement au vendeur, sous "
            "réserve de présentation de documents conformes. Instrument le "
            "plus sécurisé pour l'exportateur. Obligatoire dans plusieurs "
            "pays africains à régulation stricte (NG, ET, DZ, AO)."
        ),
        applicable_to=["import", "export"],
        typical_cost_pct=1.5,
        typical_duration_days=90,
        risk_coverage="full",
        requirements=[
            "contrat_commercial",
            "facture_proforma",
            "banque_emettrice_agreee",
            "banque_confirmatrice_si_pays_risque",
        ],
    ),
    TradeFinanceInstrument(
        code="LC_CONFIRMED",
        name="Confirmed Documentary Letter of Credit",
        name_fr="Crédit Documentaire Confirmé",
        description=(
            "L/C irrévocable avec confirmation d'une banque internationale "
            "de premier rang. Élimine le risque pays et le risque bancaire "
            "pour l'exportateur. Recommandé pour les pays à notation C ou D."
        ),
        applicable_to=["export"],
        typical_cost_pct=2.5,
        typical_duration_days=90,
        risk_coverage="full",
        requirements=[
            "LC_irrevocable_emis",
            "banque_confirmatrice_internationale",
        ],
    ),
    TradeFinanceInstrument(
        code="DOC_COLLECTION_DP",
        name="Documentary Collection – Documents against Payment (D/P)",
        name_fr="Remise Documentaire Contre Paiement (D/P)",
        description=(
            "Les documents sont remis à l'acheteur contre paiement immédiat. "
            "Moins coûteux que le L/C mais ne protège pas contre "
            "le refus de paiement. Adapté aux relations commerciales établies."
        ),
        applicable_to=["import", "export"],
        typical_cost_pct=0.5,
        typical_duration_days=30,
        risk_coverage="partial",
        requirements=[
            "facture_commerciale",
            "documents_expedition",
            "lettre_instruction_banque",
        ],
    ),
    TradeFinanceInstrument(
        code="DOC_COLLECTION_DA",
        name="Documentary Collection – Documents against Acceptance (D/A)",
        name_fr="Remise Documentaire Contre Acceptation (D/A)",
        description=(
            "Les documents sont remis contre acceptation d'une traite à terme. "
            "Crée un crédit commercial pour l'acheteur. Risque élevé pour "
            "l'exportateur : utilisable uniquement avec des partenaires fiables."
        ),
        applicable_to=["import", "export"],
        typical_cost_pct=0.4,
        typical_duration_days=90,
        risk_coverage="partial",
        requirements=[
            "facture_commerciale",
            "documents_expedition",
            "effet_de_commerce",
        ],
    ),
    TradeFinanceInstrument(
        code="BANK_GUARANTEE_BID",
        name="Bid Bond (Tender Guarantee)",
        name_fr="Caution de Soumission (Bid Bond)",
        description=(
            "Garantie bancaire émise pour couvrir le risque que le soumissionnaire "
            "retire son offre ou ne signe pas le contrat. "
            "Généralement 2-5% du montant de l'offre."
        ),
        applicable_to=["export"],
        typical_cost_pct=0.5,
        typical_duration_days=180,
        risk_coverage="partial",
        requirements=["appel_offre", "contrat_projet", "contre_garantie_banque"],
    ),
    TradeFinanceInstrument(
        code="BANK_GUARANTEE_PERFORMANCE",
        name="Performance Bond",
        name_fr="Caution de Bonne Exécution (Performance Bond)",
        description=(
            "Garantie bancaire couvrant l'inexécution des obligations "
            "contractuelles du vendeur/entrepreneur. "
            "Généralement 10% du montant du contrat."
        ),
        applicable_to=["export"],
        typical_cost_pct=1.0,
        typical_duration_days=365,
        risk_coverage="partial",
        requirements=["contrat_signe", "contre_garantie_banque"],
    ),
    TradeFinanceInstrument(
        code="BANK_GUARANTEE_ADVANCE",
        name="Advance Payment Guarantee",
        name_fr="Garantie de Remboursement d'Acompte",
        description=(
            "Protège l'acheteur en cas de non-livraison après versement d'un acompte. "
            "Montant = acompte versé. Très courant dans les marchés publics africains."
        ),
        applicable_to=["import"],
        typical_cost_pct=0.8,
        typical_duration_days=180,
        risk_coverage="partial",
        requirements=["contrat_commercial", "facture_acompte"],
    ),
    TradeFinanceInstrument(
        code="PRE_SHIPMENT_FINANCE",
        name="Pre-Shipment Export Finance",
        name_fr="Financement Pré-Expédition",
        description=(
            "Crédit accordé à l'exportateur pour financer la production "
            "ou l'achat de marchandises avant expédition. "
            "Remboursé dès réception du paiement de l'acheteur."
        ),
        applicable_to=["export"],
        typical_cost_pct=6.0,
        typical_duration_days=90,
        risk_coverage="none",
        requirements=["commande_ferme", "LC_ou_contrat", "garantie_banque"],
    ),
    TradeFinanceInstrument(
        code="POST_SHIPMENT_FINANCE",
        name="Post-Shipment Export Finance",
        name_fr="Financement Post-Expédition",
        description=(
            "Crédit accordé à l'exportateur après expédition, contre cession "
            "de créance commerciale. Permet de mobiliser les délais de paiement "
            "accordés à l'acheteur."
        ),
        applicable_to=["export"],
        typical_cost_pct=5.5,
        typical_duration_days=60,
        risk_coverage="none",
        requirements=["documents_expedition_conformes", "facture_commerciale"],
    ),
    TradeFinanceInstrument(
        code="EXPORT_FACTORING",
        name="Export Factoring",
        name_fr="Affacturage Export",
        description=(
            "Cession des créances export à un factor qui avance jusqu'à 80% "
            "du montant et assure le recouvrement + l'assurance-crédit. "
            "Disponible via Afreximbank et quelques banques pan-africaines."
        ),
        applicable_to=["export"],
        typical_cost_pct=3.0,
        typical_duration_days=90,
        risk_coverage="partial",
        requirements=["factures_commerciales", "historique_client", "contrat_factor"],
    ),
    TradeFinanceInstrument(
        code="SUPPLY_CHAIN_FINANCE",
        name="Supply Chain Finance (Reverse Factoring)",
        name_fr="Financement de la Chaîne d'Approvisionnement",
        description=(
            "Programme initié par le grand acheteur permettant à ses fournisseurs "
            "d'être payés rapidement à taux préférentiel. "
            "Développé par Standard Bank, Ecobank, Afreximbank."
        ),
        applicable_to=["import", "export"],
        typical_cost_pct=4.0,
        typical_duration_days=60,
        risk_coverage="partial",
        requirements=["programme_acheteur_eligible", "factures_approuvees"],
    ),
    TradeFinanceInstrument(
        code="STANDBY_LC",
        name="Standby Letter of Credit (SBLC)",
        name_fr="Lettre de Crédit Stand-by (SBLC)",
        description=(
            "Garantie bancaire sous forme de L/C, utilisée comme filet de sécurité "
            "si l'acheteur ne paie pas. Très utilisée dans les marchés américains et asiatiques."
        ),
        applicable_to=["export"],
        typical_cost_pct=1.0,
        typical_duration_days=365,
        risk_coverage="full",
        requirements=["contrat_commercial", "banque_emettrice_agreee"],
    ),
]

# Indexed by code for quick lookup
_INSTRUMENTS_BY_CODE = {inst.code: inst for inst in TRADE_FINANCE_INSTRUMENTS}

# ---------------------------------------------------------------------------
# COUNTRY-SPECIFIC INSTRUMENT REQUIREMENTS
# ---------------------------------------------------------------------------

# Countries where LC is mandatory for all imports
LC_MANDATORY_COUNTRIES = {"NG", "ET", "DZ", "AO", "ER"}
# Countries where LC confirmation is strongly recommended (risk C/D)
LC_CONFIRMATION_RECOMMENDED = {"NG", "ET", "AO", "ZW", "SD", "LY", "SS", "BI", "SO"}


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def get_trade_finance_instruments() -> List[TradeFinanceInstrument]:
    """Return the full catalogue of trade finance instruments."""
    return TRADE_FINANCE_INSTRUMENTS


def recommend_instruments(
    country_code: str,
    transaction_type: str = "import",
    amount_usd: float = 0.0,
) -> List[TradeFinanceInstrument]:
    """
    Recommend appropriate trade finance instruments for a given country
    and transaction type.

    Args:
        country_code: ISO2 country code of the trade partner.
        transaction_type: "import" or "export".
        amount_usd: Transaction value in USD (affects recommendations).

    Returns:
        Ordered list of recommended instruments (most suitable first).
    """
    code = country_code.upper()
    t_type = transaction_type.lower()
    recommendations: List[TradeFinanceInstrument] = []

    # Filter by applicable_to
    applicable = [
        inst for inst in TRADE_FINANCE_INSTRUMENTS
        if t_type in inst.applicable_to
    ]

    if code in LC_MANDATORY_COUNTRIES:
        # LC is mandatory – put confirmed LC first
        if t_type == "export" and code in LC_CONFIRMATION_RECOMMENDED:
            recommendations = [
                _INSTRUMENTS_BY_CODE["LC_CONFIRMED"],
                _INSTRUMENTS_BY_CODE["LC_IRREVOCABLE"],
            ] + [i for i in applicable if i.code not in {"LC_CONFIRMED", "LC_IRREVOCABLE"}]
        else:
            recommendations = [
                _INSTRUMENTS_BY_CODE["LC_IRREVOCABLE"],
            ] + [i for i in applicable if i.code != "LC_IRREVOCABLE"]
    elif code in LC_CONFIRMATION_RECOMMENDED and t_type == "export":
        recommendations = [
            _INSTRUMENTS_BY_CODE["LC_CONFIRMED"],
            _INSTRUMENTS_BY_CODE["LC_IRREVOCABLE"],
        ] + [i for i in applicable if i.code not in {"LC_CONFIRMED", "LC_IRREVOCABLE"}]
    elif amount_usd >= 100_000:
        # High-value transaction → prefer secured instruments
        recommendations = [
            _INSTRUMENTS_BY_CODE["LC_IRREVOCABLE"],
        ] + [i for i in applicable if i.code != "LC_IRREVOCABLE"]
    else:
        recommendations = applicable

    return recommendations
