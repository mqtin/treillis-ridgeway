#!/usr/bin/env python3
"""Aide à l'audit de fidélité : vérifie, page par page, ce qui peut l'être mécaniquement.

Pour chaque élément :
- chaque citation anglaise (champ `citation`, passages entre guillemets du corps anglais)
  doit se trouver sur les pages citées par l'élément (à une page près, les phrases
  pouvant enjamber un saut de page) ;
- chaque nom d'auteur d'une prémisse A ou E (dans son titre ou son énoncé) doit figurer
  sur l'une des pages citées ;
- chaque nombre de l'énoncé ou du corps (pourcentages, rapports, corrélations) doit
  figurer sur l'une des pages citées.
Demande source/texte/ (outils/extract_epub.py).

Usage :
    python outils/audit_pages.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_citations import CHAPTERS, TEXTE, norm  # noqa: E402
from build_explorer import collect  # noqa: E402

NAME_RE = re.compile(r"\b([A-Z][a-zé]+(?:-[A-Z][a-z]+)?)\b")
STOP = {"Le", "La", "Les", "Un", "Une", "Des", "Ce", "Ces", "Chez", "Par", "Dans", "Quand", "Pour", "Il", "Elle", "On",
        "The", "In", "By", "And", "Théorie", "Psychologie", "Interactionnisme", "Américains", "Blancs", "Asiatiques",
        "Latinos", "Afro", "Toutes", "Toute", "Une", "Un", "Des", "Dans", "Rendre", "Malgré", "Se", "Les", "Il",
        "Weber", "Fiske", "Ridgeway", "Facebook", "Michelin", "Harvard", "MBA", "États", "Unis", "Amérique", "Nord",
        "Louisianais", "Théoriciens", "Menace", "Dilemmes", "Doubles", "Irlandais", "Italiens", "Black", "Lives", "Matter", "Ivy", "League", "Sachs", "Goldman"}


def pages_text():
    out, cur = {}, None
    for c in CHAPTERS:
        for tok in re.split(r"(\[p\d+\])", (TEXTE / c).read_text(encoding="utf-8")):
            m = re.fullmatch(r"\[p(\d+)\]", tok)
            if m:
                cur = int(m.group(1))
            elif cur is not None:
                out[cur] = out.get(cur, "") + " " + tok
    return {k: norm(v) for k, v in out.items()}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pg = pages_text()
    data = collect()
    issues = []
    for e in data["elements"]:
        near = set()
        for n in e["pages"]:
            near |= {n - 1, n, n + 1}
        txt = " ".join(pg.get(n, "") for n in sorted(near))
        quotes = ([e["citation"].strip("“”\" ")] if e["citation"] else []) + re.findall(r'"([^"]+)"', e["body_en"])
        # passages anglais cités dans le corps français, entre « »
        quotes += [x for x in re.findall(r"«\s*([^«»]+?)\s*»", e["body"])
                   if re.search(r"(the|of|and|is|to|that|we|it|what|who)", x)]
        for q in quotes:
            core = norm(q).strip(" .,;:")
            if core and core not in txt:
                issues.append(f"{e['id']} : citation pas aux pages citées : « {q} »")
        if e["type"] in ("auteur", "etude"):
            lead = re.match(r"\(([^)]*)\)", e["enonce"])  # auteurs nommés en tête : « (Hays et Greer.) »
            names = set(NAME_RE.findall((lead.group(1) if lead else "") + " " + e["titre"].split(":")[0])) - STOP
            for nm in names:
                if nm.lower() not in txt:
                    issues.append(f"{e['id']} : « {nm} » absent des pages citées")
        for num in set(re.findall(r"\b\d+(?:[.,]\d+)?\s?%|\br\s?≈\s?[\d.,]+|\b\d+ pour cent\b", e["enonce"] + " " + e["body"])):
            digits = re.sub(r"[^\d]", "", num).lstrip("0")
            if digits and digits not in re.sub(r"[^\d ]", "", txt):
                issues.append(f"{e['id']} : nombre « {num} » absent des pages citées")
    for i in issues:
        print(i)
    print(f"{len(data['elements'])} éléments · {len(issues)} point(s) à vérifier")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
