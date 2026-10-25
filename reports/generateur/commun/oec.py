"""Client minimal de l'API OEC (tesseract, BACI HS 2017), avec cache disque.

Même source et même codage des identifiants SH que le module Statistiques du SaaS
(backend/services/oec_trade_service.py) : préfixe de section SH + code SH2/SH4/SH6.
Sans clé, l'API publique suffit ; OEC_API_TOKEN (offre Pro) est utilisé s'il est défini.
"""
import hashlib
import json
import os
from pathlib import Path

import httpx

URL = 'https://api.oec.world/tesseract/data.jsonrecords'
CUBE = 'trade_i_baci_a_17'
SECTIONS = [(1, 5), (6, 14), (15, 15), (16, 24), (25, 27), (28, 38), (39, 40), (41, 43), (44, 46), (47, 49),
            (50, 63), (64, 67), (68, 70), (71, 71), (72, 83), (84, 85), (86, 89), (90, 92), (93, 93), (94, 96), (97, 97)]
CACHE = Path(os.environ.get('RG_CACHE', Path(__file__).resolve().parents[1] / '_cache')) / 'oec'


def hs_id(code: str) -> str:
    """'33' -> '633', '3304' -> '63304', '330499' -> '6330499'."""
    ch = int(code[:2])
    sec = next(i for i, (a, b) in enumerate(SECTIONS, 1) if a <= ch <= b)
    return f'{sec}{code}'


def pays_id(iso3: str) -> str:
    return 'af' + iso3.lower()


def requete(**params) -> list:
    """Interroge le cube BACI ; réponses mises en cache (données annuelles, révisées rarement)."""
    params = {'cube': CUBE, 'measures': 'Trade Value', **params}
    cle = hashlib.sha1(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
    f = CACHE / f'{cle}.json'
    if f.exists():
        return json.loads(f.read_text())
    headers = {}
    if os.environ.get('OEC_API_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['OEC_API_TOKEN']
    r = httpx.get(URL, params=params, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json().get('data', [])
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(data))
    return data


def importations(iso3: str, codes_hs2: list, annee: int) -> dict:
    """Importations d'un pays par chapitre SH2 (USD)."""
    rows = requete(drilldowns='HS2', **{'Importer Country': pays_id(iso3), 'HS2': ','.join(hs_id(c) for c in codes_hs2), 'Year': annee})
    return {str(r['HS2 ID'])[-2:]: r['Trade Value'] for r in rows}


def exportations(iso3: str, codes_hs2: list, annee: int) -> dict:
    rows = requete(drilldowns='HS2', **{'Exporter Country': pays_id(iso3), 'HS2': ','.join(hs_id(c) for c in codes_hs2), 'Year': annee})
    return {str(r['HS2 ID'])[-2:]: r['Trade Value'] for r in rows}


def importateurs_africains(codes_hs2: list, annee: int) -> dict:
    """Importations des pays africains sur un périmètre de chapitres (USD), par pays."""
    rows = requete(drilldowns='Importer Country', **{'Importer Continent': 'af', 'HS2': ','.join(hs_id(c) for c in codes_hs2), 'Year': annee})
    return {str(r['Importer Country ID'])[2:].upper(): r['Trade Value'] for r in rows}
