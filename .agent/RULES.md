# RULES.md — Règles de 40KT1_SENTINEL

> **À relire au début de CHAQUE session.** Ces règles priment sur la rapidité.
> Ce dépôt pose du code qui tourne en `root` sur les deux machines de production
> du parc. Un agent qui enfreint ces règles ne crée pas de la dette : il crée un
> incident.

## 1. Doctrine — la règle qui prime sur toutes les autres

- **Tout est désarmé par défaut.** Agents, alertes, timers, réponse automatique.
  **Armer est un geste d'exploitation**, décrit par un runbook et joué par un
  humain — jamais l'effet de bord d'un `apply` ou d'un merge.
- **On prouve d'abord qu'une alerte arrive, on arme ensuite.** Dans cet ordre, et
  pas un autre. Un dispositif armé sans destinataire est exactement le défaut que
  ce dépôt existe pour corriger.
- **Une automatisation n'a le droit de faire que ce qu'un humain peut défaire
  sans arbitrage.** Le critère n'est pas la confiance dans le code, c'est la
  **réversibilité**, et elle se vérifie geste par geste. Repris d'`ADR-062` de
  `40KT1_HQ`, qui reste la référence.
- **Un `ok` n'est pas un `inconnu`.** Une sonde qui n'a pas pu mesurer rend
  `unknown`, jamais `ok`. Le faux vert — un contrôle qui réussit sans avoir
  regardé — a déjà coûté deux incidents dans HQ. Toute sonde écrite ici doit
  distinguer les trois états.

## 2. Périmètre d'action sur les machines

- **Aucun `ansible-playbook` sans `--check --diff` d'abord.** Sans exception.
- **Aucun `apply` sur `patator-tower` ou `patator-standby` sans ordre PO
  explicite**, formulé dans la session courante. Un ordre donné hier pour une
  autre tâche ne vaut pas pour celle-ci.
- **Le catalogue de réponse est fermé.** Un geste qui n'y figure pas ne
  s'implémente pas, même s'il est manifestement utile. L'élargir se fait par
  **amendement de l'ADR**, jamais par ajout dans un script.
- **Aucun geste automatique ne touche la donnée, la version servie, ou
  l'identité de la machine qui sert le nom public.**
- **Le budget de remédiation est une garde, pas un réglage.** Le désactiver ou
  l'augmenter est une décision d'ADR.

## 3. Frontière avec `40KT1_HQ`

- **HQ possède l'infrastructure de base** : politique `ufw`, Docker, Tailscale,
  mises à jour, arborescence de la stack, unités `40kt1-*`.
- **Sentinelle ajoute, ne réécrit jamais.** Règles pare-feu dans une chaîne
  dédiée et taguées ; unités préfixées `sentinel-*` ; `.env` séparé, dans son
  propre répertoire.
- **Le mode tournoi appartient à HQ.** Sentinelle **lit** le fichier témoin ;
  elle ne le pose ni ne le retire.
- Toute évolution de cette frontière se fait dans
  [`docs/contrat-hq.md`](../docs/contrat-hq.md) **et** dans son jumeau côté HQ.
  Une frontière écrite d'un seul côté n'est pas une frontière.

## 4. Données & secrets (priment sur tout)

- **Jamais de secret commité.** Trois secrets existent ici — clé d'enrôlement des
  agents, jeton d'API du serveur central, webhook Discord dédié — et l'un d'eux
  permet d'inscrire un faux agent. Tout passe par `.env` (gitignored) ou GitHub
  Secrets. `gitleaks` en CI ne remplace pas la relecture.
- **Le serveur central n'est joignable que par le tailnet.** Jamais de Funnel,
  jamais via cloudflared, jamais sur le nom public.
- **Les journaux de sécurité décrivent l'infrastructure entière** — chemins,
  comptes, horaires, empreintes. Les traiter comme une donnée sensible : pas de
  collage dans une issue, pas d'export non chiffré.
- **Aucune donnée nominative de joueur** n'a de raison d'entrer dans ce dépôt.
  Si une règle de détection en capture, elle est mal écrite.

## 5. Qualité de code

- **Python** : type hints partout, `ruff` (lint + format), `pytest`.
  L'exécuteur de réponse est le composant le plus sensible du dépôt : il est
  testé, y compris sur ses **refus** (geste hors catalogue, budget épuisé, mode
  tournoi, désarmement).
- **Ansible** : idempotent, `ansible-lint` + `yamllint` verts. Un rôle doit
  pouvoir être rejoué sur une machine en production **sans rien redémarrer** —
  c'est la règle de `host_baseline` dans HQ, et elle vaut ici.
- **Les règles de détection sont du code.** Versionnées dans `rules/`, revues en
  PR, jamais éditées à la main sur une machine.
- **Pas de code mort.** Si on remplace, on supprime dans la même PR.

## 6. Git & traçabilité

- **Une branche par tâche**, préfixée par l'identité (`claude/`, `cursor/`).
  Base = `origin/main` fraîchement récupéré. **Jamais de push sur `main`.**
- **Commits conventionnels** : `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`,
  `test:`, avec la tâche en référence
  (`feat(responder): budget horaire — TASKS#P01.4`).
- **Une décision d'architecture = un ADR** dans `docs/adr/`, numéroté, **avant**
  l'implémentation.
- **Vérité du suivi.** Ne cocher `[x]` qu'après commit et validation au niveau
  revendiqué. Ne jamais annoncer « vert » sur une vérification partielle.
- **PR petites et thématiques.**

## 7. Documentation — Actif / Consigné / Archivé

- **Lecture session** : `RULES` -> prompt -> [`ACTIVE.md`](ACTIVE.md) -> Focus
  `TASKS.md`. Ne pas relire les archives au démarrage.
- **Archiver = déplacer** (`git mv`) vers `.agent/archive/` ou `docs/archive/`,
  + stub à l'ancien chemin. **Jamais supprimer** sans ordre PO.
- **Les ADR restent dans `docs/adr/`** ; le statut porte la couche.
- **Langue de production : français.** Y compris les commentaires des rôles
  Ansible et des règles de détection — ils seront lus à 3 h du matin.

## 8. Ce qui n'appartient pas à ce dépôt

Le durcissement du système (c'est `host_baseline`, côté HQ) · la supervision de
disponibilité (c'est `watchdog.py`, côté HQ) · la sécurité de la chaîne Git ·
tout ce qui relève de la réparation et non de la sécurité (c'est `selfheal.py`,
côté HQ, sous `ADR-062`). En cas de doute sur l'appartenance d'un sujet : il va
dans HQ, et Sentinelle le lit.
