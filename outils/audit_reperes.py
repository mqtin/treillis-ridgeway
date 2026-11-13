#!/usr/bin/env python3
"""Aide à l'audit de fidélité : chaque étape renvoie-t-elle au bon passage ?

Pour chaque étape numérotée d'une démonstration ou d'une argumentation, et pour le corps
des autres éléments, compare le vocabulaire de l'étape avec celui des paragraphes cités
(repères 08.4) et avec tous les paragraphes du livre. Signale les étapes dont un autre
paragraphe correspond nettement mieux que ceux qu'elles citent. C'est un indice à relire,
pas un verdict. Demande source/texte/ (outils/extract_epub.py).

Usage :
    python outils/audit_reperes.py [seuil]      # seuil par défaut : 1.6
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_explorer import ROOT, collect, sections as split_sections  # noqa: E402

TEXTE = ROOT / "source" / "texte"
LOC = re.compile(r"\b(\d\d)\.(\d+)(?:[-–](\d\d)\.(\d+))?\b")
STOP = set("""a à au aux avec ce ces cet cette ceux d dans de des du elle elles en est et être eux il ils
l la le les leur leurs lui mais me même mon ne ni nos notre nous on ou où par pas plus pour qu que qui sa
se ses si son sont sur ta te tes toi ton tous tout toute toutes très tu un une vos votre vous y c s n j m
été fait faire comme dont sans sous aussi bien donc alors ainsi encore autre autres entre selon chaque
celui celle tant peut doit ont sera seront était avait""".split())


def words(s: str):
    s = s.lower().replace("’", "'")
    return [w for w in re.findall(r"[a-zàâçéèêëîïôûùüÿœæ-]{3,}", s) if w not in STOP]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    seuil = float(sys.argv[1]) if len(sys.argv) > 1 else 1.6
    if not TEXTE.is_dir():
        sys.exit("source/texte/ absent : lancer outils/extract_epub.py")
    paras = {}
    for f in sorted(TEXTE.glob("[0-9][0-9].md")):
        if f.stem in ("00", "44", "45"):  # couverture, bibliographie, notes
            continue
        for m in re.finditer(r"^\[¶(\d+)\] (.*)$", f.read_text(encoding="utf-8"), re.M):
            paras[(f.stem, int(m.group(1)))] = Counter(words(m.group(2)))
    df = Counter(w for c in paras.values() for w in c)
    n = len(paras)
    idf = {w: math.log(n / d) for w, d in df.items()}

    def vec(c):
        v = {w: (1 + math.log(k)) * idf.get(w, 0) for w, k in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        return {w: x / norm for w, x in v.items()}

    pv = {k: vec(c) for k, c in paras.items()}
    sim = lambda a, b: sum(x * b.get(w, 0) for w, x in a.items())

    def cited(text):
        out = set()
        for m in LOC.finditer(text):
            s1, p1, s2, p2 = m.group(1), int(m.group(2)), m.group(3), m.group(4)
            if s2 and s2 == s1:
                out |= {(s1, p) for p in range(p1, int(p2) + 1)}
            else:
                out.add((s1, p1))
                if s2:
                    out.add((s2, int(p2)))
        return {k for k in out if k in paras}

    flagged = 0
    for e in collect()["elements"]:
        secs = split_sections(e["body"])
        demo = secs.get("Démonstration") or secs.get("Argumentation")
        units = [(f"étape {i}", s) for i, s in enumerate(re.findall(r"^\d+\. (.*)$", demo or "", re.M), 1)] if demo else []
        units.append(("énoncé", e["enonce"] + " " + " ".join(f"{x}" for x in e["loc"])))
        for label, text in units:
            refs = cited(text)
            if not refs:
                continue
            clean = LOC.sub(" ", re.sub(r"\b[DSMTR]\d{2,3}\b", " ", text))
            v = vec(Counter(words(clean)))
            if len(v) < 4:
                continue
            best = max(paras, key=lambda k: sim(v, pv[k]))
            got = max(sim(v, pv[k]) for k in refs)
            top = sim(v, pv[best])
            if best not in refs and top > seuil * max(got, 0.02):
                flagged += 1
                print(f"{e['id']} {label} : cite {', '.join(f'{a}.{b}' for a, b in sorted(refs))} ({got:.2f}) ; "
                      f"meilleur {best[0]}.{best[1]} ({top:.2f})")
    print(f"\n{flagged} étape(s) à relire (seuil {seuil})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
