#!/usr/bin/env python3
"""Calcule les SHA-256 des documents archivés et met à jour _manifest.json."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
manifest_path = HERE / "_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

for doc in manifest["documents"]:
    p = HERE / doc["file"]
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    doc["sha256"] = h
    print(f"{doc['file']}: {h[:16]}... ({p.stat().st_size} bytes)")

manifest_path.write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("manifest updated")
