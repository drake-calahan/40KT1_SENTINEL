# `responder/` — L'exécuteur de réponse

> **Le composant le plus sensible du dépôt.** Il décide si un geste privilégié a
> le droit d'être joué sur une machine de production.
>
> **État au 2026-09-07** : le **noyau est livré** (`P03.0`) — les quatre gardes,
> le catalogue, le budget et le journal, testés sur leurs refus.
> **Aucun geste privilégié n'existe encore** : ils arrivent en `P03.6`, et rien
> n'est armé. Décision de référence :
> [`ADR-002`](../docs/adr/ADR-002-catalogue-et-budget-de-reponse.md).

## Ce qu'il fait, en une phrase

Il reçoit un **ordre** du serveur central, vérifie qu'il a le droit de
l'exécuter, agit, et journalise — **le geste comme le refus**.

## Pourquoi il existe, plutôt que la réponse active du moteur

Le mécanisme de réponse active livré avec Wazuh exécute des commandes `root` sur
l'agent : sans budget, sans notion de mode tournoi, et dans son propre journal.
Il est un bon **transport** — c'est à ce titre qu'on l'utilise. Le script qu'il
appelle est un **relais mince** vers ce module.

Résultat : le catalogue, le budget et le journal restent dans ce dépôt, revus en
pull request. C'est la seule façon de tenir le critère d'`ADR-062` de HQ sans le
déléguer à un tiers.

## Les quatre gardes, dans cet ordre

L'ordre compte : le frein d'urgence passe avant tout le reste, y compris avant
de savoir si le geste est valide.

1. **Le témoin de désarmement** (`response-disarmed`). S'il existe, rien ne
   s'exécute. C'est le chemin hors bande, celui qui ne demande que SSH.
2. **Le catalogue.** Fermé et déclaratif. Un geste absent est refusé, même si
   l'ordre est bien formé. **Jamais** de commande construite depuis une chaîne
   reçue du réseau.
3. **Le budget.** Trois gestes par heure glissante. Le troisième déclenche un
   rouge ; au-delà, plus rien ne s'exécute jusqu'à intervention humaine.
4. **Le mode tournoi.** Lu depuis le fichier témoin de `40KT1_HQ`. Selon `E4`,
   il restreint le catalogue au lieu de l'élargir.

## Où la décision est prise

**Le serveur central corrèle et ordonne ; le nœud vérifie et exécute.**
Les quatre gardes sont évaluées **localement**, jamais côté serveur.
Conséquence voulue : un serveur central compromis peut faire du bruit, pas
n'importe quoi.

## Tests — la partie qu'on oublie

**Tester les refus autant que les gestes.** Un exécuteur dont seuls les succès
sont testés n'est pas testé : ce sont les refus qui portent la sécurité.

Les quatre cas obligatoires :

- geste **hors catalogue** → refusé, journalisé, motif explicite
- **budget épuisé** → refusé, alerte rouge, gel jusqu'à intervention
- **mode tournoi** actif et geste restreint → refusé
- **témoin de désarmement** présent → refusé, avant toute autre vérification

## Ce qui est livré, module par module

| Module | Ce qu'il porte |
|---|---|
| `catalogue.py` | la transcription d'`ADR-002` : neuf gestes, leur retour arrière, leur état en nominal et en tournoi. Fermé. |
| `ordre.py` | ce que le serveur central a le droit de demander — **un nom de geste, pas une commande** |
| `gardes.py` | les quatre gardes, et les deux lectures de fichier dont elles dépendent |
| `budget.py` | l'heure glissante à trois états, et le témoin de gel |
| `journal.py` | le JSONL : gestes, refus, et la source du compte de l'heure glissante |
| `executeur.py` | l'enchaînement, dans l'ordre, et la journalisation systématique |
| `degel.py` | le dégel du budget — geste humain, **tracé** |

## Les trois règles qui tiennent ce module

**Ce qu'on n'a pas pu lire vaut l'état le plus restrictif.** Témoin de
désarmement illisible ou emplacement introuvable → on considère le frein tiré.
Témoin de mode tournoi illisible → on considère l'event en cours. Journal
illisible → le budget est *non mesurable*, donc refusé. `Path.exists()` n'est pas
utilisé pour ces lectures : il rend `False` aussi bien pour « absent » que pour
« je n'ai pas pu regarder », et ici la différence décide d'un geste privilégié.

**Le mode à blanc ne change qu'une chose : le geste n'est pas joué.** Toutes les
gardes, budget compris, se comportent à l'identique — un mode à blanc plus
permissif que le mode armé ne prouverait rien de ce qu'on veut avoir éprouvé
avant d'armer.

**Le dégel du budget est un geste humain et il laisse une trace.**
`python -m responder.degel "motif"` retire le témoin **et** écrit l'entrée dans
le journal ; c'est cette entrée, pas le fichier, qui remet le compteur de l'heure
glissante à zéro. Retirer le témoin à la main ne rouvre donc rien : un budget qui
se rouvre sans trace se rouvrira sans qu'on s'en aperçoive.

## Ce qui n'est pas encore là

Les quatre gestes armables (`P03.6`) et le relais mince appelé par le moteur
(`P03.1`). Tant qu'un geste n'est pas câblé, une décision favorable se journalise
en `aurait_execute` avec le motif « geste non câblé » — jamais en succès.
L'armement, lui, a ses cinq portes : `ADR-002` § 6, et le geste appartient au PO.

## Journalisation

Chaque geste **et chaque refus**, avec son motif, poussé en orange.
Au matin, on doit pouvoir lire ce que la machine a fait sans nous — **et ce
qu'elle n'a pas fait**. Une réponse invisible est une dérive qui a l'air d'un
miracle.
