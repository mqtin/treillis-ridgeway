#!/usr/bin/env python3
"""Extrait le texte d'un EPUB en un fichier par section, avec la pagination papier.

Le résultat va dans source/texte/ (exclu de Git : le livre est sous droits, AGENT.md § 6).
Chaque section de la table des matières devient `NN.md` ; les sauts de page de l'EPUB
y sont marqués `[p37]` : ce sont les pages citées dans les éléments, « (p. 37) ». Les
intertitres des chapitres deviennent des titres `##`, et les paragraphes sont numérotés
(`[¶3]`) pour s'y retrouver. Les notes sont dans leur propre section.

Usage :
    python -I outils/extract_epub.py source/livre.epub
"""
from __future__ import annotations

import html
import urllib.parse
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source" / "texte"
SKIP = {"head", "script", "style", "title"}
BLOCKS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "li", "div"}


class Text(HTMLParser):
    """Convertit le XHTML en paragraphes ; signale les images (schémas, formules)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras, self.buf, self.tags = [], [], []
        self.skip = 0  # dans <head>, <script>, <style>, <title>

    def flush(self, tag=None):
        t = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        if t:
            self.paras.append((tag or "p", t))
        self.buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in SKIP:
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "a" and a.get("epub:type") == "pagebreak":
            self.buf.append(f" [p{a.get('id', '').removeprefix('page_')}] ")
            return
        if tag in BLOCKS:
            self.flush()
            self.tags.append("h3" if tag == "p" and a.get("class", "").startswith("subhead") else tag)
        elif tag == "br":
            self.buf.append(" ")
        elif tag == "img":
            self.buf.append(f" [image : {a.get('src', '?')}] ")
        elif tag in {"i", "em"}:
            self.buf.append("*")
        elif tag == "sup":
            self.buf.append("^")

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in BLOCKS:
            self.flush(self.tags.pop() if self.tags else tag)
        elif tag in {"i", "em"}:
            self.buf.append("*")

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)

    def close(self):
        super().close()
        self.flush()
        return self.paras


def base(name: str) -> str:
    """Dossier d'un fichier dans l'archive : les chemins de l'OPF et du NCX lui sont relatifs."""
    return name.rsplit("/", 1)[0] + "/" if "/" in name else ""


def toc(z: zipfile.ZipFile):
    ncx = next(n for n in z.namelist() if n.endswith(".ncx"))
    raw = z.read(ncx).decode("utf-8")
    out = []
    for m in re.finditer(r'<navPoint[^>]*playOrder="(\d+)".*?<text>(.*?)</text>.*?<content src="([^"#]+)', raw, re.S):
        out.append((int(m.group(1)), html.unescape(m.group(2)).strip(), base(ncx) + urllib.parse.unquote(m.group(3))))
    return out


def spine(z: zipfile.ZipFile):
    opf = next(n for n in z.namelist() if n.endswith(".opf"))
    raw = z.read(opf).decode("utf-8")
    items = {m.group(2): html.unescape(m.group(1)) for m in re.finditer(r'<item href="([^"]+)" id="([^"]+)"', raw)}
    return [base(opf) + items[m.group(1)] for m in re.finditer(r'<itemref idref="([^"]+)"', raw) if m.group(1) in items]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    epub = Path(sys.argv[1])
    z = zipfile.ZipFile(epub)
    entries = toc(z)
    starts = {src: (n, title) for n, title, src in entries}
    OUT.mkdir(parents=True, exist_ok=True)
    sections, current = [], None
    for f in spine(z):
        if f in starts:
            current = {"n": starts[f][0], "titre": starts[f][1], "files": []}
            sections.append(current)
        elif current is None:
            current = {"n": 0, "titre": "(liminaire)", "files": []}
            sections.append(current)
        current["files"].append(f)
    sommaire = ["# Sommaire (extrait de l'EPUB)", "", "| n° | section | paragraphes |", "|---|---|---|"]
    for s in sections:
        paras = []
        for f in s["files"]:
            p = Text()
            p.feed(z.read(f).decode("utf-8", "replace"))
            paras += p.close()
        lines = [f"# {s['n']:02d}. {s['titre']}", ""]
        k = 0
        for tag, t in paras:
            if tag.startswith("h"):
                lines += [f"## {t}", ""]
            else:
                k += 1
                lines += [f"[¶{k}] {t}", ""]
        (OUT / f"{s['n']:02d}.md").write_text("\n".join(lines), encoding="utf-8")
        sommaire.append(f"| {s['n']:02d} | {s['titre']} | {k} |")
    (OUT / "sommaire.md").write_text("\n".join(sommaire) + "\n", encoding="utf-8")
    print("\n".join(sommaire))


if __name__ == "__main__":
    main()
