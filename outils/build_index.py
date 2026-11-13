#!/usr/bin/env python3
"""Régénère les tables d'INDEX.md à partir des éléments (AGENT.md § 4).

Le journal, après la ligne « ## Journal », est conservé tel quel.

Usage :
    python outils/build_index.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_explorer import PARTIE_ORDER, ROOT, collect  # noqa: E402

TYPE = {"definition": "concept", "auteur": "auteur", "etude": "étude", "these": "thèse", "refutee": "écartée"}
ORDER = {"definition": 0, "auteur": 1, "etude": 2, "these": 3, "refutee": 4}


def pages(ps):
    out, start, prev = [], None, None
    for n in ps + [None]:
        if start is None:
            start = prev = n
        elif n is not None and n == prev + 1:
            prev = n
        else:
            out.append(f"{start}" if start == prev else f"{start}-{prev}")
            start = prev = n
    return ", ".join(out)


def main():
    data = collect()
    els = data["elements"]
    parts = {p["id"]: p for p in data["partie_docs"]}
    idx = ROOT / "INDEX.md"
    journal = ""
    if idx.exists():
        text = idx.read_text(encoding="utf-8")
        if "## Journal" in text:
            journal = text[text.index("## Journal"):]
    out = ["# INDEX", "",
           "Table de tous les éléments, par partie. Chaque ligne : identifiant, type, titre, pages, statut. "
           "Régénérée par `outils/build_index.py` à chaque ajout, modification ou retrait (AGENT.md § 4).", "",
           "**Texte de travail** : EPUB de l'édition Russell Sage Foundation (2019), avec la pagination de l'édition papier ; "
           "repères en pages, extraits par `outils/extract_epub.py` (AGENT.md § 6).", "",
           "## Plan", "", "| partie | titre | pages | éléments |", "|---|---|---|---|"]
    for pid in PARTIE_ORDER:
        if pid in parts:
            n = sum(1 for e in els if e["partie"] == pid)
            out.append(f"| {pid} | {parts[pid]['titre']} | {parts[pid]['loc']} | {n} |")
    out.append("")
    for pid in PARTIE_ORDER:
        mine = sorted((e for e in els if e["partie"] == pid), key=lambda e: (ORDER.get(e["type"], 9), e["id"]))
        if not mine:
            continue
        label = "Prémisses" if pid == "P" else f"Chapitre {pid}. {parts[pid]['titre']}"
        out += [f"## {pid}. {label}" if pid == "P" else f"## {label}", "",
                "| id | type | titre | pages | statut |", "|---|---|---|---|---|"]
        for e in mine:
            out.append(f"| {e['id']} | {TYPE.get(e['type'], e['type'])} | {e['titre']} | {pages(e['pages'])} | {e['statut_revision']} |")
        out.append("")
    out.append(journal.rstrip() + "\n" if journal else "## Journal\n")
    idx.write_text("\n".join(out), encoding="utf-8", newline="\n")
    print(f"Écrit : {idx}")


if __name__ == "__main__":
    main()
