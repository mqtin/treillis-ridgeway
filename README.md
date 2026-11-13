# *Status* de Cecilia Ridgeway en treillis

L'argument de Cecilia L. Ridgeway, *Status: Why Is It Everywhere? Why Does It Matter?* (Russell Sage Foundation, 2019), reconstruit dans l'ordre géométrique et rendu explorable comme un graphe. Les prémisses que Ridgeway reprend (thèses d'autres auteurs, résultats d'études), ses concepts et ses thèses s'enchaînent chapitre par chapitre ; les positions qu'elle écarte sont reliées aux thèses qui les écartent.

C'est une reconstruction, pas une critique ni une reproduction : les énoncés reformulent le livre, avec leurs pages, et les citations sont courtes. Pour lire Ridgeway, lisez Ridgeway.

**Brouillon complet, en relecture.** Le livre entier est reconstruit (175 éléments) ; l'audit de fidélité élément par élément reste à faire.

## Utilisation

Ouvrir `explorer.html` dans un navigateur : le fichier est autonome et fonctionne hors ligne. Il est **bilingue** : un bouton FR / EN en haut à droite (ou `?lang=en` dans l'adresse) bascule toute l'interface et tous les textes.

Pour entrer dans le livre : un **parcours de lecture** en seize étapes (`PARCOURS.md`), une vue des **trois ordres de croyance** (ce que je pense, ce que je pense que les autres pensent, ce que pense « la plupart des gens ») et une vue du **cycle du micro au macro** (de l'interaction à l'inégalité durable, et retour).

Pour le régénérer (Python 3 et PyYAML) :

```
python outils/check.py             # contrôles de cohérence
python outils/audit_citations.py   # citations mot pour mot dans le livre (demande source/texte/)
python outils/build_index.py       # -> tables d'INDEX.md
python outils/build_explorer.py    # -> explorer.html
```

## Organisation

| dossier ou fichier | contenu |
|---|---|
| `parties/` | prémisses et chapitres : titre, pages, résumé |
| `definitions/` | concepts (D) |
| `premisses/` | prémisses : thèses d'auteurs (A) et résultats d'études (E) |
| `theses/` | thèses de Ridgeway (T), avec démonstration ou argumentation |
| `refutees/` | positions écartées (R) |
| `PARCOURS.md` | parcours de lecture en seize étapes (`PARCOURS.en.md` : en anglais) |
| `INDEX.md` | table des éléments, plan, journal |
| `AGENT.md` | méthode, conventions et règles de fidélité |
| `LICENSE`, `NOTICE.md`, `LICENSES/` | licences, sources et mentions de droits (`NOTICE.en.md` : en anglais) |

---

## Droits et licences

Code sous GPL-3.0 ; travail de reconstruction (et sa traduction) sous CC BY-SA 4.0 ; les citations de Ridgeway en sont exclues et restent à leurs ayants droit. Le texte du livre n'est pas distribué. Voir `LICENSE` et `NOTICE.md`.

---

## In English

Cecilia L. Ridgeway's *Status: Why Is It Everywhere? Why Does It Matter?* (2019), reconstructed in geometrical order as an explorable graph: the premises she takes from other authors and studies, her concepts and theses chapter by chapter, and the positions she rejects. Written in French with a full English version: open `explorer.html` and click EN, or add `?lang=en`. Paraphrase and short quotations only; the book's text is not distributed. To read Ridgeway, read Ridgeway.
