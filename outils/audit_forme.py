#!/usr/bin/env python3
"""Audit de forme (AGENT.md § 8) : mise en forme, repères, notes, citations.

Ne juge pas l'argument : vérifie que chaque élément est bien formé et que ce qu'il
attribue au livre (repères, numéros de note, passages entre guillemets) s'y trouve.
Les contrôles qui lisent le texte du livre demandent source/texte/ (outils/extract_epub.py) ;
sans lui, ils sont sautés.

Usage :
    python outils/audit_forme.py
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_explorer import ROOT, collect, sections as split_sections  # noqa: E402

TEXTE = ROOT / "source" / "texte"
LOC_IN_BODY = re.compile(r"\b(\d\d)\.(\d+)\b")
NOTE_RE = re.compile(r"\bnotes? (\d+)(?:[-–](\d+))?(?:,? (?:et )?(\d+))?")
QUOTE_RE = re.compile(r"«\s*([^«»]{4,}?)\s*»")


def norm(s: str) -> str:
    s = s.replace("*", "").replace("’", "'").replace("‘", "'").replace(" ", " ").replace(" ", " ")
    for q in "“”«»\"":
        s = s.replace(q, '"')
    s = re.sub(r'"\s+', '"', s)
    s = re.sub(r'\s+"', '"', s)
    return re.sub(r"\s+", " ", s).strip().lower()


def load_book():
    if not TEXTE.is_dir():
        return None
    paras, notes_by_section = {}, defaultdict(set)
    for f in sorted(TEXTE.glob("[0-9][0-9].md")):
        sec = f.stem
        for m in re.finditer(r"^\[¶(\d+)\] (.*)$", f.read_text(encoding="utf-8"), re.M):
            paras[(sec, int(m.group(1)))] = m.group(2)
            if sec != "45":
                for n in re.findall(r"\[(\d+)\]", m.group(2)):
                    notes_by_section[sec].add(int(n))
    return paras, notes_by_section


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = collect()
    els = data["elements"]
    book = load_book()
    full = None
    if book:
        paras, notes_by_section = book
        full = norm(" ".join(paras.values()))
        notes_text = {k[1]: v for k, v in paras.items() if k[0] == "45"}
    out = defaultdict(list)

    for e in els:
        eid, body, t = e["id"], e["body"], e["type"]
        secs = split_sections(body)
        # 1. Énoncé et titre
        if e["enonce"] and not e["enonce"].rstrip().endswith((".", "»", "!", "?")):
            out["énoncé sans point final"].append(eid)
        if e["titre"].endswith("."):
            out["titre terminé par un point"].append(eid)
        # 2. Typographie
        for label, pat in [("guillemets droits", r'(?<![=\w])"[^"\n]{2,}"'), ("espace manquante avant ; : ? !", r"[^\s\d(«\[/*:]([;?!])(\s|$)"),
                           ("double espace", r"[^\s] {2,}[^\s|]"), ("espace avant virgule ou point", r"\s[,.](\s|$)")]:
            if re.search(pat, body + " " + e["enonce"]):
                out[label].append(eid)
        if re.search(r"«[^\s]|[^\s]»", body + e["enonce"] + e["citation"]):
            out["guillemets « » sans espace intérieure"].append(eid)
        # 3. Structure des thèses
        if t == "these":
            demo = secs.get("Démonstration") or secs.get("Argumentation") or ""
            if not demo.rstrip().endswith("∎"):
                out["démonstration sans ∎ final"].append(eid)
            steps = re.findall(r"^\d+\. (.*)$", demo, re.M)
            for i, s in enumerate(steps, 1):
                if not LOC_IN_BODY.search(s):
                    out["étape sans repère"].append(f"{eid} étape {i}")
            nums = [int(n) for n in re.findall(r"^(\d+)\. ", demo, re.M)]
            if nums != list(range(1, len(nums) + 1)):
                out["étapes mal numérotées"].append(eid)
            order = list(secs)
            if "Scolie" in order and order.index("Scolie") < max(order.index(x) for x in ("Démonstration", "Argumentation") if x in order):
                out["scolie avant la démonstration"].append(eid)
        elif t in ("spinoza", "marx", "definition"):
            if "Chez Lordon" not in secs:
                out["section « Chez Lordon » absente"].append(eid)
        elif t == "refutee" and "Telle que Lordon la présente" not in secs:
            out["section « Telle que Lordon la présente » absente"].append(eid)
        # 4. Repères du corps ⊂ repères déclarés (par section)
        declared = {l.split(".")[0] for l in e["loc"]}
        cited = {m.group(1) for m in LOC_IN_BODY.finditer(body) if m.group(1) in data["sections"]}
        if cited - declared:
            out["repère du corps hors du champ loc"].append(f"{eid} : {', '.join(sorted(cited - declared))}")
        if declared - cited and body:
            out["section du champ loc jamais citée dans le corps"].append(f"{eid} : {', '.join(sorted(declared - cited))}")
        if not book:
            continue
        # 5. Repères existants
        for l in e["loc"] + [f"{a}.{b}" for a, b in LOC_IN_BODY.findall(body) if a in data["sections"]]:
            a, b = l.split(".")
            if (a, int(b)) not in paras:
                out["paragraphe inexistant"].append(f"{eid} : {l}")
        # 6. Notes : le numéro doit apparaître dans une section du champ loc
        for m in NOTE_RE.finditer(body):
            a, b, c = m.group(1), m.group(2), m.group(3)
            ns = list(range(int(a), int(b) + 1)) if b else [int(a)] + ([int(c)] if c else [])
            for n in ns:
                if not any(n in notes_by_section[s] for s in declared):
                    out["note hors des sections citées"].append(f"{eid} : note {n}")
        # 7. Citations et passages entre guillemets
        for q in ([e["citation"]] if e["citation"] else []) + QUOTE_RE.findall(body):
            parts = [p.strip(" .,;:") for p in re.split(r"\[…\]|…", q.strip("«» "))]
            for p in parts:
                if len(p) >= 4 and norm(p) not in full and not any(norm(p) in norm(v) for v in notes_text.values()):
                    out["passage entre guillemets introuvable"].append(f"{eid} : « {p[:90]} »")

    total = 0
    for k, v in out.items():
        total += len(v)
        print(f"\n## {k} ({len(v)})")
        for x in v:
            print("  -", x)
    print(f"\n{len(els)} éléments · {total} remarque(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
