#!/usr/bin/env python3
"""Vérifie que les citations de Ridgeway sont dans le livre, mot pour mot (AGENT.md § 6).

Contrôle le champ `citation` et les passages entre guillemets droits du corps anglais.
Le corps français, qui met entre « » aussi bien des mots anglais que nos traductions, n'est
contrôlé que pour ses passages en anglais (signalés quand ils ne sont pas dans le livre).
Demande source/texte/ (outils/extract_epub.py).

Usage :
    python outils/audit_citations.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_explorer import ROOT, collect  # noqa: E402

TEXTE = ROOT / "source" / "texte"
CHAPTERS = [f"{n:02d}.md" for n in range(7, 14)]  # chapitres 1 à 7


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"\[p\d+\]|\[¶\d+\]|\^\d+|\*", " ", s)
    s = s.replace('"', " ").replace("—", " — ").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not TEXTE.is_dir():
        print("source/texte/ absent : lancer outils/extract_epub.py")
        return 1
    book = norm(" ".join((TEXTE / c).read_text(encoding="utf-8") for c in CHAPTERS))
    data = collect()
    bad, n = [], 0
    for e in data["elements"]:
        quotes = []
        if e["citation"]:
            quotes.append(("citation", e["citation"].strip("“”\" ")))
        quotes += [("corps anglais", q) for q in re.findall(r'"([^"]+)"', e["body_en"])]
        for where, q in quotes:
            n += 1
            core = norm(q).strip(" .,;:")
            if core and core not in book:
                bad.append(f"{e['id']} ({where}) : « {q} »")
    for b in bad:
        print("absent du livre :", b)
    print(f"{n} citations contrôlées · {len(bad)} introuvable(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
