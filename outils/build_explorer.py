#!/usr/bin/env python3
"""Génère explorer.html : interface d'exploration du graphe et des textes.

Lit le front-matter YAML et le corps de chaque élément (definitions/, premisses/,
theses/, refutees/), les fiches de parties/, ainsi que les documents du projet, puis
injecte le tout dans un fichier HTML autonome (aucune dépendance réseau).

Bilingue : la version anglaise d'un élément ou d'une partie est dans le même fichier
(champs titre_en, enonce_en, resume_en ; corps anglais après la ligne « <!-- en --> ») ;
celle d'un document NOM.md est dans NOM.en.md.

Outil commun aux treillis d'idées (treillis.qpetit.com).

Usage :
    python outils/build_explorer.py           # génère explorer.html
    python outils/build_explorer.py --watch   # régénère à chaque modification
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML est requis : pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "explorer_template.html"
OUTPUT = ROOT / "explorer.html"

ELEMENT_DIRS = ["definitions", "premisses", "theses", "refutees"]
DOC_FILES = ["PARCOURS.md", "NOTICE.md", "AGENT.md", "INDEX.md"]

# Parties (AGENT.md § 4) : P (prémisses), puis les chapitres du livre.
PARTIE_DIR = "parties"
PARTIE_ORDER = ["P", "1", "2", "3", "4", "5", "6", "7"]

ID_PATTERN = r"[DAETR]\d{2,3}(?:-C\d+)?"
ID_RE = re.compile(rf"\b({ID_PATTERN})\b")
EN_MARK = re.compile(r"^<!--\s*en\s*-->\s*$", re.M)
FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)


def split_front_matter(text: str):
    m = FRONT_RE.match(text.replace("\r\n", "\n"))
    if not m:
        return None, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        return {"_yaml_error": str(exc)}, m.group(2)
    return meta, m.group(2)


def as_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if v is not None and str(v).strip()]
    return [s.strip() for s in str(value).split(",") if s.strip()]


def split_lang(body: str):
    """Corps français, corps anglais (après la ligne <!-- en -->)."""
    parts = EN_MARK.split(body, maxsplit=1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def sections(body: str) -> dict:
    """Découpe le corps en sections de niveau 2 (## Titre)."""
    out, current, buf = {}, None, []
    for line in body.split("\n"):
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h and not line.startswith("###"):
            if current is not None:
                out[current] = "\n".join(buf).strip()
            current, buf = h.group(1), []
        else:
            buf.append(line)
    if current is not None:
        out[current] = "\n".join(buf).strip()
    return out


def load_parties():
    out = []
    folder = ROOT / PARTIE_DIR
    if folder.is_dir():
        for p in folder.glob("*.md"):
            meta, body = split_front_matter(p.read_text(encoding="utf-8"))
            meta = meta if isinstance(meta, dict) else {}
            if "_yaml_error" in meta:
                print(f"Attention : YAML invalide dans {p.name} : {meta['_yaml_error']}", file=sys.stderr)
            pid = str(meta.get("id") or p.stem)
            fr, en = split_lang(body)
            out.append({"id": pid, "titre": meta.get("titre") or "", "resume": meta.get("resume") or "",
                        "titre_en": meta.get("titre_en") or "", "resume_en": " ".join(str(meta.get("resume_en") or "").split()),
                        "loc": meta.get("loc") or "",
                        "body": fr, "body_en": en, "file": p.relative_to(ROOT).as_posix()})
    out.sort(key=lambda x: PARTIE_ORDER.index(x["id"]) if x["id"] in PARTIE_ORDER else 99)
    return out


def load_elements():
    elements, problems = [], []
    for d in ELEMENT_DIRS:
        folder = ROOT / d
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta, body = split_front_matter(text)
            body, body_en = split_lang(body) if meta is not None else (body, "")
            rel = path.relative_to(ROOT).as_posix()
            if meta is None:
                problems.append({"kind": "frontmatter", "file": rel, "msg": "Pas de front-matter YAML."})
                continue
            if "_yaml_error" in meta:
                problems.append({"kind": "frontmatter", "file": rel, "msg": "YAML invalide : " + meta["_yaml_error"]})
                continue
            eid = str(meta.get("id") or path.stem)
            if eid != path.stem:
                problems.append({"kind": "frontmatter", "file": rel,
                                 "msg": f"L'id du front-matter ({eid}) diffère du nom de fichier ({path.stem})."})
            enonce = meta.get("enonce") or ""
            citation = meta.get("citation") or ""
            secs = sections(body)
            argued = secs.get("Démonstration", "") + "\n" + secs.get("Argumentation", "")
            corollaires = sorted(set(re.findall(rf"\b{re.escape(eid)}-C\d+\b", body)))
            elements.append({
                "id": eid,
                "file": rel,
                "type": meta.get("type") or "",
                "partie": str(meta.get("partie") if meta.get("partie") is not None else ""),
                "titre": meta.get("titre") or "",
                "enonce": " ".join(str(enonce).split()),
                "titre_en": meta.get("titre_en") or "",
                "enonce_en": " ".join(str(meta.get("enonce_en") or "").split()),
                "citation": " ".join(str(citation).split()),
                "pages": [int(x) for x in as_list(meta.get("pages")) if x.isdigit()],
                "depends_on": as_list(meta.get("depends_on")),
                "contre": as_list(meta.get("contre")),
                "lien_explicite": meta.get("lien_explicite"),
                "statut_revision": meta.get("statut_revision"),
                "body": body.strip(),
                "body_en": body_en,
                "sections_en": list(sections(body_en).keys()),
                "demo_refs_en": sorted(set(ID_RE.findall(" ".join(v for k, v in sections(body_en).items()
                                                                    if k in ("Demonstration", "Argument"))))),
                "sections": list(secs.keys()),
                "demo_refs": sorted(set(ID_RE.findall(argued))),
                "mentions": sorted(set(ID_RE.findall(body))),
                "corollaires": corollaires,
                "mtime": path.stat().st_mtime,
            })
    return elements, problems


def load_documents():
    docs = []
    for name in DOC_FILES:
        p = ROOT / name
        if p.exists():
            # Pas de « mentions » : AGENT.md et INDEX.md citent des identifiants en exemple ou en liste.
            en = p.with_name(p.stem + ".en.md")
            docs.append({"name": name, "kind": "projet", "body": p.read_text(encoding="utf-8"),
                         "body_en": en.read_text(encoding="utf-8") if en.exists() else ""})
    return docs


def index_ids():
    """Identifiants listés dans les tableaux de INDEX.md (première colonne)."""
    p = ROOT / "INDEX.md"
    if not p.exists():
        return []
    ids = []
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(rf"^\|\s*({ID_PATTERN})\s*\|", line)
        if m:
            ids.append(m.group(1))
    return ids


def collect():
    elements, problems = load_elements()
    parties = load_parties()
    return {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "elements": elements,
        "documents": load_documents(),
        "index_ids": index_ids(),
        "parties": {p["id"]: p["titre"] for p in parties},
        "partie_docs": parties,
        "problems": problems,
    }


def build() -> Path:
    payload = json.dumps(collect(), ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)
    OUTPUT.write_text(html, encoding="utf-8")
    return OUTPUT


def snapshot():
    files = [ROOT / n for n in DOC_FILES] + [ROOT / n.replace(".md", ".en.md") for n in DOC_FILES] + [TEMPLATE]
    for d in ELEMENT_DIRS + [PARTIE_DIR]:
        if (ROOT / d).is_dir():
            files += list((ROOT / d).glob("*.md"))
    return {str(f): f.stat().st_mtime for f in files if f.exists()}


def main():
    out = build()
    print(f"Écrit : {out}")
    if "--watch" in sys.argv:
        print("Surveillance des modifications (Ctrl+C pour arrêter)…")
        last = snapshot()
        try:
            while True:
                time.sleep(1)
                now = snapshot()
                if now != last:
                    last = now
                    build()
                    print(f"[{datetime.now():%H:%M:%S}] régénéré")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
