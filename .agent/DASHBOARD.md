# DASHBOARD.md — État du programme 40KT1_SENTINEL

> Photo « où en est-on ». **Lecture agents** : commencer par [`ACTIVE.md`](ACTIVE.md).
> Mis à jour à chaque fin de session.

## En une ligne

**Phase 0 — cadrage consigné, formalisation faite.** Trente réponses PO
(2026-09-07), quatre STRUCTURANTES tranchées. Les **trois ADR sont Acceptées**
(2026-09-07). **Aucune machine du parc ne porte quoi
que ce soit de ce dépôt, et rien n'est armé.**

## Avancement

| Phase | Sujet | État |
|-------|-------|------|
| **P0** | Cadrage, ADR, amorce du dépôt | **en cours** — `ADR-002`/`ADR-003` acceptées ; restent `P00.2`, `P00.5` (jumeau HQ), `P00.6` |
| P1 | Observation seule | **débloquée** — attend `P00.6` puis `P01.6` |
| P2 | Alerte | non commencée |
| P3 | Réponse (à blanc, puis armée) | **noyau de l'exécuteur livré** (`P03.0`) ; gestes en `P03.6` ; armement sous les cinq portes d'`ADR-002` § 6 |
| P4 | Extension : poste Windows, couche conteneur, profil complet | non commencée |

## Ce qui a été décidé

**Tranché au cadrage (2026-09-07), et formalisé le jour même — sauf la moitié
HQ du contrat de frontière :**

| # | Décision | Résumé |
|---|----------|--------|
| **C1** | Hôte serveur central | `patator-standby` frugal ; plan B `bluefin` jour MVP |
| **E2** | Catalogue armé | quatre premiers gestes |
| **E4** | Mode tournoi | réponse moins agressive |
| **H3** | Frontière HQ | HQ base · Sentinelle ajoute tagué |

`ADR-002` et `ADR-003` sont *Acceptées* ; `ADR-001` attend `P00.2`. Le contrat de
frontière n'engage que Sentinelle tant que son jumeau n'est pas fusionné dans HQ
(`P00.5`). **Rien n'est armé.**

## Ce qui est mesuré

| Indicateur | Valeur | Depuis |
|---|---|---|
| Endpoints sous agent | 0 / 2 (P1) | — |
| Alertes non pertinentes / semaine | non mesuré | — |
| Gestes automatiques / semaine | 0 (désarmé) | — |
| Faux positifs traités | — | — |

> Ce tableau est vide et le restera jusqu'à `P1`. Il est ici parce qu'un
> indicateur qu'on n'a pas prévu de mesurer est un indicateur qu'on ne mesurera
> jamais.

## Journal

| Date | Événement |
|------|-----------|
| 2026-09-07 | Proposition rendue (questionnaire 30 questions + solution). Dépôt amorcé : harnais `.agent/`, couche Cursor, 3 ADR *Proposé*, plan `P01`, contrat de frontière, squelette Ansible, CI. Aucune machine touchée. |
| 2026-09-07 | Cadrage consigné : 30 réponses dans `ACTIVE.md`, clarifications PO (C1 standby/bluefin, C2 zéro budget, A3/F4/H2). Focus TASKS → formalisation ADR `P00.2`–`P00.6`. |
| 2026-09-07 | Lancement cadré (`P00.10`) : plan `P02` — 27 lots en six vagues, répartis 12 `cursor` / 11 `claude` / 3 PO (+1 à trancher), briefs des lots `cursor` dans `.agent/briefs/`. Deux lots ajoutés au passage : nettoyage post-amorce (`P00.7`) et garde CI d'armement (`P00.8`). **Rien n'est armé.** |
| 2026-09-07 | `P03.0` — noyau de l'exécuteur : quatre gardes, catalogue fermé, budget à trois états, journal des gestes **et** des refus, dégel tracé. 36 tests, `ruff` + `pytest` verts. Aucun geste privilégié n'existe : rien ne peut être joué. |
| 2026-09-07 | `ADR-003` **Acceptée** : hôte `patator-standby` frugal, quatre conditions vérifiables, sortie à trois déclencheurs, revue au 2027-03-07. `ADR-002` **Acceptée** : catalogue fermé, budget à trois états, cinq portes d'armement. Contrat de frontière complété côté Sentinelle ; **jumeau HQ à porter**. |
