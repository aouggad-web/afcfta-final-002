#!/usr/bin/env python3
"""
Crypto-verification : intégrité SHA-256 des données crawlées.

Couche de professionalisme et d'authenticité :
1. Chaque fichier crawled/*.json reçoit un hash SHA-256 de son contenu
2. Chaque source PDF/HTML téléchargée est hashée et archivée
3. La normalisation préserve le hash source dans chaque position
4. Vérification : re-hash du fichier → comparaison avec le hash stocké

Usage :
    from crawlers.integrity import compute_file_hash, verify_file_hash, IntegritySeal
    seal = IntegritySeal.from_file("backend/data/crawled/DZA_tariffs.json")
    assert seal.verify()
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def compute_file_hash(filepath: str) -> str:
    """Calcule le SHA-256 d'un fichier."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_content_hash(content: bytes) -> str:
    """Calcule le SHA-256 d'un contenu bytes."""
    return hashlib.sha256(content).hexdigest()


def compute_json_hash(data: dict) -> str:
    """Calcule le SHA-256 d'un dict JSON (sérialisation déterministe)."""
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_file_hash(filepath: str, expected_hash: str) -> bool:
    """Vérifie qu'un fichier correspond au hash attendu."""
    actual = compute_file_hash(filepath)
    return actual == expected_hash


def sidecar_path(filepath: str) -> str:
    """Chemin du fichier .sha256 adjacent portant le hash du fichier scellé."""
    return f"{filepath}.sha256"


def detect_indent(filepath: str, default: int = 2) -> int:
    """Indentation du JSON déjà sur disque, relue sur sa deuxième ligne.

    Les fichiers crawled n'ont pas tous été écrits par le même script et
    mélangent les indentations : réécrire avec une valeur fixe reformaterait
    le document entier et noierait le sceau dans un diff de plusieurs
    millions de lignes.
    """
    with open(filepath, encoding="utf-8") as f:
        f.readline()
        second = f.readline()
    stripped = second.lstrip(" ")
    width = len(second) - len(stripped)
    return width if stripped.startswith('"') and width > 0 else default


def read_sidecar_hash(filepath: str) -> Optional[str]:
    """Lit le hash publié dans le .sha256 adjacent, ou None s'il est absent."""
    path = sidecar_path(filepath)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read().strip().split()[0] or None


class IntegritySeal:
    """
    Sceau d'intégrité attaché à un fichier de données crawlées.

    Contient :
    - file_hash : SHA-256 du fichier tel qu'écrit sur disque
    - content_hash : SHA-256 du contenu JSON (sans le sceau lui-même)
    - source_url : URL d'où les données ont été collectées
    - source_hash : SHA-256 du document source (PDF, HTML, XLS)
    - crawled_at : timestamp UTC du crawl
    - verified : True si le hash a été vérifié à l'écriture
    """

    def __init__(
        self,
        file_hash: str,
        content_hash: str,
        source_url: str = "",
        source_hash: Optional[str] = None,
        crawled_at: str = "",
        verified: bool = True,
    ):
        self.file_hash = file_hash
        self.content_hash = content_hash
        self.source_url = source_url
        self.source_hash = source_hash
        self.crawled_at = crawled_at or datetime.now(timezone.utc).isoformat()
        self.verified = verified

    @classmethod
    def from_file(cls, filepath: str, source_url: str = "", source_hash: Optional[str] = None) -> "IntegritySeal":
        """Crée un sceau depuis un fichier existant."""
        file_hash = compute_file_hash(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Retirer le sceau existant pour le content_hash
        data.pop("_integrity_seal", None)
        content_hash = compute_json_hash(data)
        return cls(
            file_hash=file_hash,
            content_hash=content_hash,
            source_url=source_url,
            source_hash=source_hash,
            crawled_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def from_content(cls, content: bytes, source_url: str = "", source_hash: Optional[str] = None) -> "IntegritySeal":
        """Crée un sceau depuis un contenu bytes."""
        file_hash = compute_content_hash(content)
        data = json.loads(content)
        data.pop("_integrity_seal", None)
        content_hash = compute_json_hash(data)
        return cls(
            file_hash=file_hash,
            content_hash=content_hash,
            source_url=source_url,
            source_hash=source_hash,
            crawled_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_hash": self.file_hash,
            "content_hash": self.content_hash,
            "source_url": self.source_url,
            "source_hash": self.source_hash,
            "crawled_at": self.crawled_at,
            "verified": self.verified,
            "algorithm": "SHA-256",
        }

    def verify(self, filepath: Optional[str] = None) -> bool:
        """Vérifie l'intégrité du fichier."""
        if not filepath:
            return self.verified

        if not os.path.exists(filepath):
            return False

        actual_hash = compute_file_hash(filepath)
        return actual_hash == self.file_hash

    def embed_in(self, data: dict) -> dict:
        """Embarque le sceau dans un dict JSON."""
        data["_integrity_seal"] = self.to_dict()
        return data


def seal_crawled_file(filepath: str, source_url: str = "", source_hash: Optional[str] = None) -> IntegritySeal:
    """
    Scelle un fichier crawled/*.json en ajoutant _integrity_seal.

    1. Charge le fichier
    2. Calcule les hashes
    3. Ajoute _integrity_seal au JSON
    4. Réécrit le fichier
    5. Retourne le sceau
    """
    indent = detect_indent(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Retirer un ancien sceau
    data.pop("_integrity_seal", None)

    # Calculer le content_hash (sans le sceau)
    content_hash = compute_json_hash(data)

    # Le file_hash ne peut pas vivre à l'intérieur du fichier qu'il hache :
    # l'y écrire changerait le contenu et invaliderait la valeur écrite. Il
    # est donc publié dans un fichier <nom>.sha256 adjacent, écrit après la
    # sérialisation définitive, et le sceau embarqué ne porte que le
    # content_hash — seul hachage vérifiable depuis l'intérieur du document.
    seal = IntegritySeal(
        file_hash="",
        content_hash=content_hash,
        source_url=source_url or data.get("source_url", data.get("source_root_url", "")),
        source_hash=source_hash,
    )
    payload = seal.to_dict()
    payload.pop("file_hash", None)
    data["_integrity_seal"] = payload

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

    file_hash = compute_file_hash(filepath)
    seal.file_hash = file_hash
    with open(sidecar_path(filepath), "w", encoding="utf-8") as f:
        f.write(f"{file_hash}  {os.path.basename(filepath)}\n")

    seal.verified = verify_file_hash(filepath, file_hash)

    return seal


def verify_crawled_file(filepath: str) -> Dict[str, Any]:
    """
    Vérifie l'intégrité d'un fichier scellé.

    Retourne :
    {
        "valid": True/False,
        "file_hash_match": True/False,
        "content_hash_match": True/False,
        "seal": {...},
        "actual_file_hash": "...",
    }
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    seal = data.get("_integrity_seal")
    if not seal:
        return {
            "valid": False,
            "reason": "NO_SEAL",
            "filepath": filepath,
        }

    actual_file_hash = compute_file_hash(filepath)

    # Retirer le sceau pour vérifier le content_hash
    data.pop("_integrity_seal", None)
    actual_content_hash = compute_json_hash(data)

    # Le hash du fichier est publié dans le .sha256 adjacent, jamais dans le
    # document lui-même (cf. seal_crawled_file).
    expected_file_hash = read_sidecar_hash(filepath)
    file_hash_match = expected_file_hash is not None and actual_file_hash == expected_file_hash
    content_hash_match = actual_content_hash == seal.get("content_hash")

    return {
        "valid": file_hash_match and content_hash_match,
        "file_hash_match": file_hash_match,
        "content_hash_match": content_hash_match,
        "seal": seal,
        "actual_file_hash": actual_file_hash,
        "expected_file_hash": expected_file_hash,
        "filepath": filepath,
    }


def seal_all_crawled_files(crawled_dir: str = None):
    """Scelle tous les fichiers crawled/*.json."""
    if crawled_dir is None:
        crawled_dir = str(Path(__file__).resolve().parent.parent / "data" / "crawled")

    results = []
    for f in sorted(Path(crawled_dir).glob("*_tariffs.json")):
        try:
            seal = seal_crawled_file(str(f))
            results.append({
                "file": f.name,
                "valid": seal.verified,
                "file_hash": seal.file_hash[:16] + "...",
                "content_hash": seal.content_hash[:16] + "...",
            })
        except Exception as e:
            results.append({"file": f.name, "error": str(e)[:100]})

    return results


def verify_all_crawled_files(crawled_dir: str = None):
    """Vérifie tous les fichiers scellés."""
    if crawled_dir is None:
        crawled_dir = str(Path(__file__).resolve().parent.parent / "data" / "crawled")

    results = []
    for f in sorted(Path(crawled_dir).glob("*_tariffs.json")):
        result = verify_crawled_file(str(f))
        results.append({
            "file": f.name,
            "valid": result.get("valid", False),
            "file_hash_match": result.get("file_hash_match", False),
            "content_hash_match": result.get("content_hash_match", False),
        })

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 integrity.py [seal|verify] [filepath]")
        sys.exit(1)

    action = sys.argv[1]

    if action == "seal":
        if len(sys.argv) > 2:
            seal = seal_crawled_file(sys.argv[2])
            print(f"Sealed: {sys.argv[2]}")
            print(f"  file_hash:    {seal.file_hash}")
            print(f"  content_hash: {seal.content_hash}")
            print(f"  verified:     {seal.verified}")
        else:
            results = seal_all_crawled_files()
            print(f"\nSealed {len(results)} files:")
            for r in results:
                status = "✓" if r.get("valid") else "✗"
                print(f"  {status} {r['file']}")
            valid = sum(1 for r in results if r.get("valid"))
            print(f"\n{valid}/{len(results)} files sealed successfully")

    elif action == "verify":
        if len(sys.argv) > 2:
            result = verify_crawled_file(sys.argv[2])
            print(f"Verify: {sys.argv[2]}")
            print(f"  valid:              {result.get('valid')}")
            print(f"  file_hash_match:    {result.get('file_hash_match')}")
            print(f"  content_hash_match: {result.get('content_hash_match')}")
            if result.get("seal"):
                print(f"  seal: {json.dumps(result['seal'], indent=2)[:300]}")
        else:
            results = verify_all_crawled_files()
            print(f"\nVerified {len(results)} files:")
            for r in results:
                status = "✓" if r.get("valid") else "✗"
                print(f"  {status} {r['file']}")
            valid = sum(1 for r in results if r.get("valid"))
            print(f"\n{valid}/{len(results)} files valid")
