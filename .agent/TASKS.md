# TASKS.md — Backlog 40KT1_SENTINEL

> Source de vérité des tâches **ouvertes**. États : `[ ]` à faire · `[~]` en cours
> (agent: nom, date) · `[x]` fait. Un agent = une tâche `[~]` à la fois.
>
> **Lecture agents** : [`.agent/ACTIVE.md`](ACTIVE.md) d'abord.
>
> ⚠️ **Sans hub de coordination, ce fichier committé est le seul état partagé.**
> Une tâche prise sans être écrite ici est une collision programmée.

## Focus — Phase 0 : formalisation ADR (cadrage consigné)

> **2026-09-07** — les 30 réponses sont consignées dans `ACTIVE.md` § « Réponses
> au cadrage ». Les quatre STRUCTURANTES (`C1`, `E2`, `E4`, `H3`) sont tranchées.
> Les ADR restent *Proposé* : la suite = les passer *Accepté*, pas re-décider.
>
> **Débloqué maintenant** : rédaction / acceptation ADR (`P00.2`–`P00.4`), contrat
> HQ jumeau (`P00.5`), amorce GitHub (`P00.6`).
>
> **Toujours bloqué** : **aucun rôle Ansible** tant que `ADR-003` n'est pas
> *Accepté* (`P00.3` — hôte `patator-standby` frugal + sortie écrite).
>
> **Enchaînement proposé** : `P00.2` → `P00.3` → `P00.4` → `P00.5` → `P00.6` →
> entrée `P1`.

- [x] **P00.0** Amorce du dépôt : harnais `.agent/`, couche Cursor, hub docs,
      trois ADR au statut *Proposé*, plan `P01`, contrat de frontière avec HQ,
      squelette Ansible, CI. **Aucune machine touchée.**
- [x] **P00.1** Réponses du PO au questionnaire
      ([`docs/cadrage/questionnaire.md`](../docs/cadrage/questionnaire.md)).
      Consignées dans `ACTIVE.md`, question par question, date 2026-09-07.
- [ ] **P00.2** `ADR-001` (moteur et profil) passe *Proposé* → *Accepté* ou
      *Remplacé*, à partir des réponses `A2`, `A3`, `C2`, `F4` consignées.
- [ ] **P00.3** `ADR-003` (hôte du serveur central) tranché — **bloquant `P1`**.
      Si l'hôte est `patator-standby`, l'ADR doit écrire **la sortie**, comme
      l'exception `P31.7` l'a fait pour le cockpit dans HQ.
- [ ] **P00.4** `ADR-002` (catalogue, budget, mode tournoi) tranché —
      **bloquant `P3`**. Le tableau geste par geste du § 2.5 de la proposition
      est le point de départ, pas la conclusion.
- [ ] **P00.5** [`docs/contrat-hq.md`](../docs/contrat-hq.md) relu et **son jumeau
      créé côté HQ**. Une frontière écrite d'un seul côté n'est pas une frontière.
- [ ] **P00.6** Créer le dépôt GitHub (privé), pousser l'amorce, activer
      la protection de branche sur `main` et les deux workflows.

## Phase 1 — Observation seule

> Bloquée par `P00.3`. Aucune alerte poussée, aucune réponse : on mesure le bruit
> de fond.

- [ ] **P01.0** Rôle `sentinel_server` — installation et configuration du serveur
      central sur l'hôte tranché en `C1`, **profil frugal** (pas d'indexeur, pas
      de console). Écoute sur `tailscale0` uniquement.
- [ ] **P01.1** Rôle `sentinel_agent` — agent sur `patator-tower` et
      `patator-standby`, enrôlement par clé, aucun redémarrage de service de
      production déclenché par le rôle.
- [ ] **P01.2** Règles d'intégrité (`rules/integrite/`) sur la liste courte de
      `D1`. Temps réel sur la liste courte, balayage 12 h sur le reste.
- [ ] **P01.3** Règle **anti-rafale** pour la perte de contact d'un agent —
      écrite **avant** le premier week-end, pas après. Motif : le défaut réseau
      récidivant de `patator-standby` (4 occurrences connues).
- [ ] **P01.4** Bornage des ressources (`cgroup`) et, si l'hôte est le standby,
      arrêt automatique du serveur central quand la relève s'arme (`C3`).
- [ ] **P01.5** Période d'observation (`D5`, défaut 14 jours) couvrant au moins
      un déploiement complet et une sauvegarde offsite. Journal des faux positifs.

**Critère de sortie** : moins de 3 alertes non pertinentes par semaine, deux
semaines de suite. Chiffré, mesuré, écrit — pas « ça a l'air calme ».

## Phase 2 — Alerte

- [ ] **P02.0** Câblage `notify.sh` vers le salon Discord dédié et le sujet ntfy
      dédié. **Preuve d'arrivée sur le téléphone avant tout le reste.**
- [ ] **P02.1** Grille de sévérité calquée sur `watchdog.py` + la sévérité
      `critique` (`F2`).
- [ ] **P02.2** Agrégation par fenêtre de 15 min avec compteur (`F3`).

**Critère de sortie** : une alerte de test reçue sur les deux canaux, et une
alerte réelle traitée de bout en bout.

## Phase 3 — Réponse

> Bloquée par `P00.4`.

- [ ] **P03.0** `responder/` — catalogue, budget horaire, lecture du mode
      tournoi, lecture du témoin de désarmement. Tests sur les **refus** autant
      que sur les gestes.
- [ ] **P03.1** Relais mince côté agent : le mécanisme de réponse active de
      l'outil sert de transport, l'exécuteur local décide.
- [ ] **P03.2** Mode à blanc — l'exécuteur journalise ce qu'il **aurait** fait,
      deux semaines.
- [ ] **P03.3** Runbook de désarmement d'urgence **testé depuis un téléphone**.
- [ ] **P03.4** Armement du catalogue minimal, hors mode tournoi d'abord.
- [ ] **P03.5** Vue « sécurité » dans le cockpit ops de HQ.

**Critère de sortie** : zéro geste à blanc jugé injustifié sur la période.

## Phase 4 — Extension

- [ ] **P04.0** Agent sur `AEGIS-TOWER`, **alerte seulement** (`E6`).
- [ ] **P04.1** Couche conteneur (Falco eBPF) sur la tour — **seulement si** la
      phase 1 a montré qu'elle manque.
- [ ] **P04.2** Bascule vers le profil complet — seulement si `C1` a débouché
      sur du matériel dédié.

**Critère de sortie** : décidé à l'entrée de la phase, pas maintenant.
