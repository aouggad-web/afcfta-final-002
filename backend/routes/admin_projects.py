"""Admin endpoints to manage `projets_structurants_afrique.json`.

All endpoints require an admin-tier API key (X-API-Key header).
File is read/written atomically; an in-memory lock prevents concurrent writes.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import require_admin

router = APIRouter(prefix="/admin/projects", tags=["Admin - Structuring Projects"])

# File location resolution (mirrors backend/projects_data.py)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_FILE = ROOT_DIR / "data" / "json" / "projets_structurants_afrique.json"
BACKUP_DIR = ROOT_DIR / "data" / "json" / "_backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

_write_lock = asyncio.Lock()


class ProjectIn(BaseModel):
    titre: str = Field(..., min_length=2)
    secteur: str = ""
    statut: str = ""
    budget: str = ""
    echeance: str = ""
    description: str = ""
    impact: str = ""
    partenaires: str = ""
    source: str = ""


class ProjectOut(ProjectIn):
    pass


class CountrySummary(BaseModel):
    iso3: str
    project_count: int


def _read_data() -> dict:
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_data(data: dict) -> None:
    # Backup before write
    if DATA_FILE.exists():
        ts = __import__("time").strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DATA_FILE, BACKUP_DIR / f"projets_structurants_afrique.{ts}.json")
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


@router.get("/countries", response_model=List[CountrySummary])
async def list_countries(_: dict = Depends(require_admin)):
    data = _read_data()
    return [CountrySummary(iso3=k, project_count=len(v or [])) for k, v in sorted(data.items())]


@router.get("/{iso3}", response_model=List[ProjectOut])
async def list_projects(iso3: str, _: dict = Depends(require_admin)):
    data = _read_data()
    return data.get(iso3.upper(), [])


@router.post("/{iso3}", response_model=List[ProjectOut])
async def add_project(iso3: str, project: ProjectIn, _: dict = Depends(require_admin)):
    iso3 = iso3.upper()
    async with _write_lock:
        data = _read_data()
        data.setdefault(iso3, []).append(project.model_dump())
        _write_data(data)
        return data[iso3]


@router.put("/{iso3}/{index}", response_model=List[ProjectOut])
async def update_project(
    iso3: str, index: int, project: ProjectIn, _: dict = Depends(require_admin)
):
    iso3 = iso3.upper()
    async with _write_lock:
        data = _read_data()
        items = data.get(iso3, [])
        if not (0 <= index < len(items)):
            raise HTTPException(status_code=404, detail="Project index out of range")
        items[index] = project.model_dump()
        data[iso3] = items
        _write_data(data)
        return data[iso3]


@router.delete("/{iso3}/{index}", response_model=List[ProjectOut])
async def delete_project(iso3: str, index: int, _: dict = Depends(require_admin)):
    iso3 = iso3.upper()
    async with _write_lock:
        data = _read_data()
        items = data.get(iso3, [])
        if not (0 <= index < len(items)):
            raise HTTPException(status_code=404, detail="Project index out of range")
        items.pop(index)
        data[iso3] = items
        _write_data(data)
        return data[iso3]


@router.delete("/{iso3}", response_model=dict)
async def delete_country(iso3: str, _: dict = Depends(require_admin)):
    """Remove all projects for a country."""
    iso3 = iso3.upper()
    async with _write_lock:
        data = _read_data()
        if iso3 in data:
            del data[iso3]
            _write_data(data)
        return {"ok": True, "iso3": iso3}
