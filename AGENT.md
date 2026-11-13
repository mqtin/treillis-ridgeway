# AGENT.md : *Status* de Cecilia Ridgeway en treillis

Ce fichier définit l'objectif, la méthode et les conventions du projet. Il s'adresse à l'agent (Claude) et à l'auteur. Tout travail dans ce dépôt doit s'y conformer. Il évolue avec le projet, et toute modification est discutée avec l'auteur.

Projet indépendant, publié parmi les « treillis d'idées » (treillis.qpetit.com), dont il partage l'outillage. Projet voisin par le sujet : Homo Status (`/status`, dépôt `status-and-politics`), qui prend chez Ridgeway ses définitions du statut.

## 1. Objectif

Reconstruire **fidèlement** l'argument de Cecilia L. Ridgeway, *Status: Why Is It Everywhere? Why Does It Matter?* (New York, Russell Sage Foundation, 2019), dans l'ordre géométrique, et le rendre explorable comme un graphe. Depuis une thèse, on doit pouvoir voir le chemin qui y mène, jusqu'aux concepts et aux prémisses (travaux d'autres auteurs, résultats d'études), et ce qui en découle.

C'est une **reconstruction, non une critique**. On ne juge pas les thèses, on ne cherche pas de rivales et on ne dit pas ce qui les réfuterait : ce travail appartient à Homo Status. Ici, la seule question est : *qu'est-ce que Ridgeway dit, et comment est-ce que cela s'enchaîne ?*

## 2. Fidélité

1. **Rien qui ne soit dans le livre.** Chaque élément reformule un passage du livre. Si un pas manque pour relier deux thèses, on le signale (§ 2.4) ; on n'ajoute pas de contenu.
2. **Toute affirmation a son repère** : la page de l'édition papier, entre parenthèses, « (p. 37) » ou « (p. 37-39) ». Le champ `pages` est la liste exacte des pages citées dans le corps français ; `check.py` le vérifie.
3. **Les travaux cités sont ceux de Ridgeway.** Une prémisse A ou E dit ce qu'un auteur ou une étude établit *tel que Ridgeway le rapporte* ; on ne va pas vérifier la source, et on ne cite pas d'étude qu'elle ne cite pas.
4. **Explicite ou reconstruit.** Le champ `lien_explicite` d'une thèse dit si Ridgeway fait elle-même les liens déclarés dans `depends_on` (`true`) ou si on les a reconstruits (`false`). Dans le corps, un pas qu'elle ne fait pas est marqué *[reconstruit]*.
5. **Démonstration ou argumentation.** Une thèse a une `## Démonstration` quand Ridgeway enchaîne des raisons, et une `## Argumentation` quand elle établit par exemples, comparaison ou réfutation. On ne fabrique pas de déduction absente du livre.
6. **Le vocabulaire de Ridgeway** est conservé et traduit de façon constante : schème culturel (*cultural schema*), norme fondamentale du statut (*basic status norm*), croyances de statut (*status beliefs*), attentes de performance, caractéristiques de statut diffuses et spécifiques, généralisation du statut, avantage de statut, inférence de troisième ordre, biais de légitimité, biais de préférence associative, institutions-portails (*gateway institutions*). Il n'existe pas, à notre connaissance, de traduction française publiée du livre ; ces traductions sont les nôtres.

## 3. Types d'éléments

| type | préfixe | dossier | rôle |
|---|---|---|---|
| `definition` | `D` | `definitions/` | un concept que Ridgeway définit ou reprend (statut, schème culturel, croyance de statut…) |
| `auteur` | `A` | `premisses/` | la thèse d'un autre auteur ou d'une autre théorie que Ridgeway prend comme prémisse (Sewell, Weber, Tilly, la théorie des états d'attente…) |
| `etude` | `E` | `premisses/` | un résultat empirique que Ridgeway cite (Bales, Ridgeway et Diekema, Hays et Greer…) |
| `these` | `T` | `theses/` | une thèse de Ridgeway, avec sa démonstration ou son argumentation |
| `refutee` | `R` | `refutees/` | une position que Ridgeway écarte (la dominance comme fondement, le statut comme vanité, le vernis idéologique de Tilly…), énoncée telle qu'elle la présente |

- Concepts, prémisses et positions écartées ne s'appuient que sur des concepts et des prémisses. Seules les thèses s'appuient sur des thèses.
- Le champ `contre` d'une thèse liste les positions `R` qu'elle écarte. Ces arêtes « contre » n'entrent ni dans le chemin ni dans les conséquences.
- Les identifiants sont globaux et numérotés dans l'ordre d'apparition dans le livre ; toute renumérotation est répercutée partout.

## 4. Structure du dépôt

```
AGENT.md          ce fichier
README.md
PARCOURS.md       parcours de lecture : un fil de seize étapes, de la question du livre à sa conclusion
PARCOURS.en.md    sa version anglaise ; de même NOTICE.en.md (§ 5 bis) ; PARCOURS.de.md, NOTICE.de.md en allemand (§ 5 ter)
INDEX.md          table de tous les éléments (générée), plan, journal
parties/          P (prémisses), 1 à 7 (chapitres) : titre, pages, résumé
definitions/      D01.md …
premisses/        A01.md …, E01.md …
theses/           T001.md …
refutees/         R01.md …
outils/           build_explorer.py, explorer_template.html, check.py, audit_citations.py, audit_pages.py, build_index.py, extract_epub.py
source/           NON VERSIONNÉ : le fichier du livre et le texte extrait (§ 6)
explorer.html     généré
```

Chaque élément porte un champ `partie` : `P` pour les prémisses A et E, sinon le chapitre où il apparaît. `INDEX.md` est régénéré par `python outils/build_index.py` (le journal est conservé).

## 5. Format d'un fichier

```markdown
---
id: T012
type: these                 # definition | auteur | etude | these | refutee
partie: "2"                 # P | 1 … 7
titre: "Titre court"
enonce: "Reformulation de la thèse, en une ou deux phrases."
pages: [39, 40, 41, 42]     # exactement les pages citées dans le corps français
citation: "“…”"             # facultative ; une phrase au plus, en anglais, mot pour mot (§ 6)
depends_on: [T011, D09, E09]
contre: [R07]               # thèses seulement
lien_explicite: true        # thèses seulement (§ 2.4)
statut_revision: brouillon  # brouillon | verifie-texte
titre_en: "…"
enonce_en: "…"
---

## Démonstration            (ou ## Argumentation)
1. Par T011, … (p. 39-40).
2. Par E09, … (p. 40). ∎

## Scolie
Exemples et digressions du livre, résumés.

<!-- en -->

## Demonstration
1. By T011, … (p. 39-40).
2. By E09, … (p. 40). ∎

## Scholium
…
```

Concepts et prémisses ont une section `## Chez Ridgeway` (*In Ridgeway*) ; les positions écartées, `## Telle que Ridgeway la présente` (*As Ridgeway presents it*).

`depends_on` correspond exactement aux identifiants invoqués dans la démonstration ou l'argumentation.

**§ 5 bis. Version anglaise.** Chaque élément et chaque partie a sa version anglaise dans le même fichier : `titre_en`, `enonce_en` (ou `resume_en`) dans le front-matter, et, après une ligne `<!-- en -->`, le corps anglais. Il garde les mêmes étapes, les mêmes identifiants et les mêmes repères que le français, ce que `check.py` vérifie. Le livre étant en anglais, les mots de Ridgeway y sont cités tels quels entre guillemets droits ; dans le corps français, ils sont soit cités en anglais, soit traduits par nous entre « ». Un document `NOM.md` a sa version dans `NOM.en.md`. Toute correction du français se reporte dans l'anglais.

**§ 5 ter. Version allemande.** Sur le même modèle, chaque élément et chaque partie a sa version allemande : `titre_de`, `enonce_de` (ou `resume_de`), et, après une ligne `<!-- de -->` placée après le corps anglais, le corps allemand, avec les sections `## Beweis` (ou `## Argumentation`), `## Anmerkung`, `## Bei Ridgeway`, `## Wie Ridgeway sie darstellt`. Il garde les mêmes étapes, les mêmes identifiants et les mêmes repères (pages en « (S. 37) »), ce que `check.py` vérifie. Il traduit la reconstruction, sans recourir à une traduction publiée du livre ; les mots de Ridgeway y sont rendus brièvement par nous entre guillemets allemands („…“). Un document `NOM.md` a sa version dans `NOM.de.md`. Toute correction du français se reporte dans l'anglais et dans l'allemand.

## 6. Droits et texte source

Le livre est sous droits (© Russell Sage Foundation, 2019).

- Le fichier du livre et le texte extrait vivent dans `source/`, **exclu de Git** (`.gitignore`). On ne les publie jamais, ni en tout ni en partie. `outils/check.py` signale une erreur si un fichier de `source/` est suivi par Git ou si une citation dépasse 300 caractères.
- Les citations ne sont pas couvertes par les licences du dépôt (CC BY-SA 4.0 pour la reconstruction, GPL-3.0 pour le code) : voir `LICENSE` et `NOTICE.md`.
- Les éléments **reformulent**. Une citation tient en une phrase au plus, entre guillemets, avec sa page, et seulement quand la formule compte. `outils/audit_citations.py` vérifie que le champ `citation` et les passages entre guillemets du corps anglais sont dans le livre mot pour mot.
- **Repères.** L'EPUB conserve la pagination de l'édition papier ; `outils/extract_epub.py` l'extrait dans `source/texte/` (marques `[p37]`), avec un fichier par chapitre.

## 7. Méthode de travail

1. Le livre a été reconstruit d'un seul tenant le 13 novembre 2026, tous les éléments en `brouillon`.
2. **Audit de fidélité** : chaque élément est relu contre les pages citées (reformulation exacte, page juste, liens explicites ou reconstruits bien marqués), puis passe à `verifie-texte`.
3. **Relecture par l'auteur** : toute correction est consignée dans le journal d'`INDEX.md`.
4. Après chaque modification : `python outils/check.py`, `python outils/audit_citations.py`, `python outils/build_index.py`, `python outils/build_explorer.py`.
5. Les commits et les push se font seulement à la demande de l'auteur.

## 8. Contrôles

`python outils/check.py` vérifie : identifiants et types, pages présentes et concordantes avec le corps, longueur des citations, existence des dépendances, absence de cycle, concordance entre `depends_on` et la démonstration, arêtes `contre` vers des `R`, cohérence avec `INDEX.md`, exclusion de `source/`, complétude et concordance des versions anglaise et allemande (§ 5 bis et 5 ter). L'onglet « Audit » de l'explorateur affiche les mêmes contrôles.

`python outils/audit_citations.py` vérifie les citations contre le livre ; `python outils/audit_pages.py` vérifie, page par page, que chaque citation (y compris les passages anglais du corps français), chaque auteur nommé dans une prémisse et chaque chiffre se trouvent aux pages citées (les deux demandent `source/texte/`).

Aucun de ces contrôles ne remplace l'audit de fidélité.

## 9. Style

Le style est celui des projets voisins : phrases courtes, vocabulaire précis, pas de jargon ajouté. Le texte est écrit en français, avec ses versions anglaise et allemande.
