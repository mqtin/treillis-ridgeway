#!/usr/bin/env python3
"""Contrôles de cohérence du treillis (AGENT.md § 8).

Les mêmes contrôles sont affichés dans l'onglet « Audit » de l'explorateur ;
ce script permet de les lancer sans navigateur et renvoie un code d'erreur.

Usage :
    python outils/check.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_explorer import ID_RE, ROOT, collect  # noqa: E402

TYPES = {"definition", "auteur", "etude", "these", "refutee"}
STATUTS = {"brouillon", "verifie-texte"}
PREFIX = {"definition": "D", "auteur": "A", "etude": "E", "these": "T", "refutee": "R"}
MAX_CITATION = 300
PAGES = range(1, 165)  # pages du texte principal (chapitres 1 à 7)
PAGE_RE = re.compile(r"\bp\. (\d+)(?:-(\d+))?")
SECTIONS_EN = {"Démonstration": "Demonstration", "Argumentation": "Argument", "Scolie": "Scholium",
               "Chez Ridgeway": "In Ridgeway", "Telle que Ridgeway la présente": "As Ridgeway presents it"}


def body_pages(text):
    out = set()
    for a, b in PAGE_RE.findall(text):
        out.update(range(int(a), int(b or a) + 1))
    return out

LOC_FR = lambda s: re.findall(r"\bp\. (\d+(?:-\d+)?)", s)
LOC_DE = lambda s: re.findall(r"\bS\. (\d+(?:-\d+)?)", s)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = collect()
    els = data["elements"]
    by_id = {e["id"]: e for e in els}
    errors, warnings = [], []

    for p in data["problems"]:
        errors.append(f"{p['file']} : {p['msg']}")

    ids = [e["id"] for e in els]
    for i in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"{i} : identifiant en double")

    for e in els:
        eid, t = e["id"], e["type"]
        if t not in TYPES:
            errors.append(f"{eid} : type « {t} » inconnu")
        elif not eid.startswith(PREFIX[t]):
            errors.append(f"{eid} : un élément de type {t} commence par {PREFIX[t]}")
        if e["statut_revision"] not in STATUTS:
            errors.append(f"{eid} : statut_revision « {e['statut_revision']} »")
        if e["partie"] not in data["parties"]:
            warnings.append(f"{eid} : partie « {e['partie']} » sans fiche dans parties/")
        if not e["enonce"]:
            errors.append(f"{eid} : énoncé vide")
        if not e["pages"]:
            errors.append(f"{eid} : aucun repère (pages)")
        for n in e["pages"]:
            if n not in PAGES:
                errors.append(f"{eid} : page {n} hors du texte (1-164)")
        bp = body_pages(e["body"])
        if bp != set(e["pages"]):
            errors.append(f"{eid} : pages du corps et champ pages diffèrent ({', '.join(map(str, sorted(bp ^ set(e['pages']))))})")
        if len(e["citation"]) > MAX_CITATION:
            errors.append(f"{eid} : citation de {len(e['citation'])} caractères (max. {MAX_CITATION})")
        for d in e["depends_on"]:
            base = d.split("-C")[0]
            if base not in by_id:
                errors.append(f"{eid} dépend de {d}, qui n'existe pas")
            elif t != "these" and by_id[base]["type"] in {"these", "refutee"}:
                warnings.append(f"{eid} ({t}) dépend de {d} ({by_id[base]['type']})")
        for r in e["contre"]:
            if r not in by_id:
                errors.append(f"{eid} contre {r}, qui n'existe pas")
            elif by_id[r]["type"] != "refutee":
                errors.append(f"{eid} contre {r}, qui n'est pas une position écartée")
        if t == "these":
            if not isinstance(e["lien_explicite"], bool):
                warnings.append(f"{eid} : lien_explicite absent")
            if "Démonstration" not in e["sections"] and "Argumentation" not in e["sections"]:
                errors.append(f"{eid} : ni Démonstration ni Argumentation")
        if "Démonstration" in e["sections"] or "Argumentation" in e["sections"]:
            refs = {r for r in e["demo_refs"] if r != eid and r not in e["contre"]}
            deps = set(e["depends_on"])
            if refs - deps:
                errors.append(f"{eid} invoque sans déclarer : {', '.join(sorted(refs - deps))}")
            if deps - refs:
                errors.append(f"{eid} déclare sans invoquer : {', '.join(sorted(deps - refs))}")

        # Version anglaise (AGENT.md § 5) : mêmes champs, mêmes étapes, mêmes renvois.
        miss = [k for k in ("titre_en", "enonce_en", "body_en") if not e[k]]
        if miss:
            warnings.append(f"{eid} : traduction anglaise manquante ({', '.join(miss)})")
        else:
            steps = lambda s: len(re.findall(r"^\d+\. ", s, re.M))
            if steps(e["body"]) != steps(e["body_en"]):
                errors.append(f"{eid} : {steps(e['body'])} étapes en français, {steps(e['body_en'])} en anglais")
            if e["demo_refs"] != e["demo_refs_en"]:
                errors.append(f"{eid} : la démonstration anglaise invoque {e['demo_refs_en']}, la française {e['demo_refs']}")
            if set(e["mentions"]) != set(ID_RE.findall(e["body_en"])):
                warnings.append(f"{eid} : identifiants différents entre corps français et anglais")
            if PAGE_RE.findall(e["body"]) != PAGE_RE.findall(e["body_en"]):
                warnings.append(f"{eid} : repères différents entre français et anglais")
            for f, en in SECTIONS_EN.items():
                if (f in e["sections"]) != (en in e["sections_en"]):
                    errors.append(f"{eid} : section « {f} » sans équivalent « {en} » (ou l'inverse)")

        # Version allemande (AGENT.md § 5 ter) : mêmes étapes, mêmes renvois, mêmes repères.
        SECTIONS_DE = {"Démonstration": "Beweis", "Argumentation": "Argumentation", "Scolie": "Anmerkung",
                       "Chez Ridgeway": "Bei Ridgeway", "Telle que Ridgeway la présente": "Wie Ridgeway sie darstellt"}
        miss = [k for k in ("titre_de", "enonce_de", "body_de") if not e[k]]
        if miss:
            warnings.append(f"{eid} : traduction allemande manquante ({', '.join(miss)})")
        else:
            steps = lambda s: len(re.findall(r"^\d+\. ", s, re.M))
            if steps(e["body"]) != steps(e["body_de"]):
                errors.append(f"{eid} : {steps(e['body'])} étapes en français, {steps(e['body_de'])} en allemand")
            if e["demo_refs"] != e["demo_refs_de"]:
                errors.append(f"{eid} : la démonstration allemande invoque {e['demo_refs_de']}, la française {e['demo_refs']}")
            if set(e["mentions"]) != set(ID_RE.findall(e["body_de"])):
                warnings.append(f"{eid} : identifiants différents entre corps français et allemand")
            if LOC_FR(e["body"]) != LOC_DE(e["body_de"]):
                warnings.append(f"{eid} : repères différents entre français et allemand")
            for f, de in SECTIONS_DE.items():
                if (f in e["sections"]) != (de in e["sections_de"]):
                    errors.append(f"{eid} : section « {f} » sans équivalent « {de} » (ou l'inverse)")

    for p in data["partie_docs"]:
        if not (p["titre_de"] and p["body_de"]):
            warnings.append(f"parties/{p['id']}.md : traduction allemande manquante")
        if not (p["titre_en"] and p["body_en"]):
            warnings.append(f"parties/{p['id']}.md : traduction anglaise manquante")

    for r in (e for e in els if e["type"] == "refutee"):
        if not any(r["id"] in e["contre"] for e in els):
            warnings.append(f"{r['id']} : aucune thèse ne l'écarte")

    # Cycles
    state = {}

    def visit(v, path):
        state[v] = 1
        path.append(v)
        for p in by_id[v]["depends_on"]:
            p = p.split("-C")[0]
            if p not in by_id:
                continue
            if state.get(p) == 1:
                errors.append("cycle : " + " → ".join(path[path.index(p):] + [p]))
            elif not state.get(p):
                visit(p, path)
        path.pop()
        state[v] = 2

    for e in els:
        if not state.get(e["id"]):
            visit(e["id"], [])

    # INDEX.md
    idx = set(data["index_ids"])
    for e in els:
        if e["id"] not in idx:
            warnings.append(f"{e['id']} absent de INDEX.md")
    for i in idx:
        if i not in by_id and not any(i in e["corollaires"] for e in els):
            warnings.append(f"{i} listé dans INDEX.md sans fichier")

    # Droits : rien de source/ ne doit être suivi par Git, et les citations restent courtes
    gi = ROOT / ".gitignore"
    if not gi.exists() or "source/" not in gi.read_text(encoding="utf-8"):
        errors.append(".gitignore doit exclure source/ (texte du livre, sous droits)")
    try:
        tracked = subprocess.run(["git", "ls-files", "source"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    except OSError:
        tracked = []
    for t in tracked:
        errors.append(f"{t} est suivi par Git : le texte du livre ne doit jamais être versionné")
    for e in els:
        for q in re.findall(r"«\s*([^«»]+?)\s*»|\"([^\"]+)\"", e["body"] + " " + e["body_en"] + " " + e["body_de"]):
            q = q[0] or q[1]
            if len(q) > MAX_CITATION:
                errors.append(f"{e['id']} : citation de {len(q)} caractères dans le corps (max. {MAX_CITATION})")

    for w in warnings:
        print("attention :", w)
    for x in errors:
        print("ERREUR :", x)
    print(f"{len(els)} éléments · {len(errors)} erreur(s) · {len(warnings)} avertissement(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
