# TASKS.md — Backlog 40KT1_SENTINEL

> Source de vérité des tâches **ouvertes**. États : `[ ]` à faire · `[~]` en cours
> (agent: nom, date) · `[x]` fait. Un agent = une tâche `[~]` à la fois.
>
> **Lecture agents** : [`.agent/ACTIVE.md`](ACTIVE.md) d'abord.
>
> ⚠️ **Sans hub de coordination, ce fichier committé est le seul état partagé.**
> Une tâche prise sans être écrite ici est une collision programmée.
>
> **Affectation et ordre de lancement** :
> [`docs/plans/P02`](../docs/plans/P02-lancement-implementation.md).
> Chaque lot `cursor` a un **brief** dans [`briefs/`](briefs/) : il porte le
> périmètre, les critères d'acceptation et les preuves attendues.
> Le numéro d'un lot dit son **identité**, pas son rang — le rang est dans `P02`.

## Comment lire une ligne

`- [ ] **P0X.Y** (agent) sujet — bloqué par …`

L'agent entre parenthèses est le **propriétaire du lot**, décidé en `P02` § 2 :
`claude` prend ce qui exécute du privilégié, fixe un contrat ou traverse la
frontière HQ ; `cursor` prend ce dont la spécification est complète avant la
première ligne de code ; `PO` prend les gestes d'exploitation — **armer en fait
partie, toujours.**

## Focus — Vagues 0 et 1 : débloquer le tronc, puis formaliser

> **2026-09-07** — les 30 réponses sont consignées dans `ACTIVE.md` § « Réponses
> au cadrage ». Les quatre STRUCTURANTES (`C1`, `E2`, `E4`, `H3`) sont tranchées.
> Les ADR restent *Proposé* : la suite = les passer *Accepté*, pas re-décider.
>
> **Rien ne part avant `P00.6`** : les branches se basent sur `origin/main`, et
> `main` ne porte qu'une racine vide tant que l'amorce n'est pas fusionnée.
>
> **Ensuite, en parallèle** : `P00.7` et `P00.8` (`cursor`) · `P00.2` (`cursor`)
> · `P00.3` → `P00.4` → `P00.5` (`claude`) · `P01.7` (`cursor`).
>
> **Toujours bloqué** : **aucun rôle Ansible** tant qu'`ADR-003` n'est pas
> *Accepté* (`P00.3`).

- [x] **P00.0** Amorce du dépôt : harnais `.agent/`, couche Cursor, hub docs,
      trois ADR au statut *Proposé*, plan `P01`, contrat de frontière avec HQ,
      squelette Ansible, CI. **Aucune machine touchée.**
- [x] **P00.1** Réponses du PO au questionnaire
      ([`docs/cadrage/questionnaire.md`](../docs/cadrage/questionnaire.md)).
      Consignées dans `ACTIVE.md`, question par question, date 2026-09-07.
- [x] **P00.10** (claude) Cadrage du lancement : découpage en lots, affectation
      `claude` / `cursor` / `PO`, briefs des lots `cursor`.
      → [`docs/plans/P02`](../docs/plans/P02-lancement-implementation.md).
- [ ] **P00.6** (PO) Fusionner l'amorce sur `main`, activer la **protection de
      branche** (PR obligatoire, pas de push direct), vérifier que les trois
      workflows tournent. **Bloque tout le reste.**
- [ ] **P00.7** (cursor) Nettoyage post-amorce : `AMORCE.md` retiré, `README` et
      `docs/README` remis à l'état réel du 2026-09-07 —
      [brief](briefs/P00.7-nettoyage-post-amorce.md).
- [ ] **P00.8** (cursor) Garde CI « rien n'est armé » : la case de la checklist
      devient un contrôle qui échoue —
      [brief](briefs/P00.8-garde-ci-armement.md).
- [ ] **P00.2** (cursor) `ADR-001` (moteur et profil) passe *Proposé* → *Accepté*,
      à partir des réponses `A2`, `A3`, `A4`, `C2`, `F4` consignées —
      [brief](briefs/P00.2-adr-001-accepte.md).
- [ ] **P00.3** (claude) `ADR-003` (hôte du serveur central) tranché —
      **bloquant `P1`**. L'hôte est `patator-standby` : l'ADR doit écrire **la
      sortie**, comme l'exception `P31.7` l'a fait pour le cockpit dans HQ.
- [ ] **P00.4** (claude) `ADR-002` (catalogue, budget, mode tournoi) tranché —
      **bloquant `P3`**. Le tableau geste par geste du § 2.5 de la proposition
      est le point de départ, pas la conclusion.
- [ ] **P00.5** (claude) [`docs/contrat-hq.md`](../docs/contrat-hq.md) relu et
      **son jumeau créé côté HQ**. Une frontière écrite d'un seul côté n'est pas
      une frontière.

## Phase 1 — Observation seule

> Bloquée par `P00.3`. Aucune alerte poussée, aucune réponse : on mesure le bruit
> de fond. Ordre réel : `P01.7` → `P01.6` → `P01.0` → `P01.2` → `P01.1` →
> `P01.8` → `P01.3` → `P01.4` → `P01.9` → `P01.5`.

- [ ] **P01.7** (cursor) Instrumentation de la période d'observation : protocole
      et journal des faux positifs, avec le troisième état `indeterminee` —
      [brief](briefs/P01.7-instrumentation-observation.md). *Non bloqué par
      `ADR-003` : aucun fichier de machine.*
- [ ] **P01.6** (claude) **Gabarit de rôle Ansible** : disposition, garde
      `*_enabled`, politique « aucun redémarrage d'un service de HQ », bilan de
      fin de rôle avec le nombre d'hôtes touchés, playbook `00_check.yml`,
      groupe `sentinel_server` rempli dans l'inventaire.
- [ ] **P01.0** (claude) Rôle `sentinel_server` — serveur central sur l'hôte
      tranché en `C1`, **profil frugal** (pas d'indexeur, pas de console).
      Écoute sur `tailscale0` uniquement.
- [ ] **P01.2** (cursor) Règles d'intégrité (`rules/integrite/`) sur la liste
      courte de `D1` — [brief](briefs/P01.2-regles-integrite.md). Fixe les plages
      d'identifiants et la correspondance sévérité ↔ niveau pour tous les lots de
      règles suivants.
- [ ] **P01.1** (cursor) Rôle `sentinel_agent` — agents sur `patator-tower` et
      `patator-standby`, enrôlement par clé, aucun redémarrage de service de
      production déclenché par le rôle —
      [brief](briefs/P01.1-role-sentinel-agent.md).
- [ ] **P01.8** (cursor) Règles authentification et événements Docker —
      [brief](briefs/P01.8-regles-auth-docker.md).
- [ ] **P01.3** (claude) Règle **anti-rafale** pour la perte de contact d'un
      agent — écrite **avant** le premier week-end, pas après. Motif : le défaut
      réseau récidivant de `patator-standby` (4 occurrences connues). Livre le
      noyau du moteur de bruit, généralisé en `P02.2`.
- [ ] **P01.4** (claude) Bornage des ressources (`cgroup`) et, l'hôte étant le
      standby, arrêt automatique du serveur central quand la relève s'arme (`C3`).
- [ ] **P01.9** (cursor) Rapports hebdomadaires conformité (`D3`) et
      vulnérabilités (`D4`), **lecture seule**, unités `sentinel-*` livrées
      désarmées — [brief](briefs/P01.9-rapports-hebdomadaires.md).
- [ ] **P01.5** (PO) Période d'observation (`D5`, 14 jours) couvrant au moins un
      déploiement complet et une sauvegarde offsite. Journal des faux positifs
      tenu selon `P01.7`.

**Critère de sortie** : moins de 3 alertes non pertinentes par semaine, deux
semaines de suite. Chiffré, mesuré, écrit — pas « ça a l'air calme ».

## Phase 2 — Alerte

- [ ] **P02.0** (cursor) Câblage `notify.sh` vers le salon Discord dédié et le
      sujet ntfy dédié. **Preuve d'arrivée sur le téléphone avant tout le reste**
      — [brief](briefs/P02.0-cablage-alerte.md).
- [ ] **P02.1** (cursor) Grille de sévérité calquée sur `watchdog.py` + la
      sévérité `critique` et ses trois cas (`F2`) —
      [brief](briefs/P02.1-grille-severite.md).
- [ ] **P02.2** (claude) Agrégation par fenêtre de 15 min avec compteur (`F3`) —
      généralisation du moteur de bruit livré en `P01.3`.

**Critère de sortie** : une alerte de test reçue sur les deux canaux, et une
alerte réelle traitée de bout en bout.

## Phase 3 — Réponse

> Bloquée par `P00.4`. L'exécuteur se livre en trois lots : le noyau et ses
> gardes **avant** le premier geste privilégié.

- [ ] **P03.0** (claude) `responder/` — catalogue déclaratif, budget horaire,
      lecture du mode tournoi, lecture du témoin de désarmement. Tests sur les
      **refus** autant que sur les gestes.
- [ ] **P03.6** (claude) Les quatre gestes armables du catalogue, chacun avec son
      retour arrière : blocage d'IP à expiration, arrêt de processus, arrêt de
      conteneur, mise en quarantaine d'un fichier.
- [ ] **P03.1** (claude) Relais mince côté agent : le mécanisme de réponse active
      de l'outil sert de transport, l'exécuteur local décide.
- [ ] **P03.2** (cursor) Mode à blanc — runbook de lecture du journal et
      définition d'un geste injustifié —
      [brief](briefs/P03.2-runbook-mode-a-blanc.md).
- [ ] **P03.3** (cursor + PO) Runbook de désarmement d'urgence **testé depuis un
      téléphone** — [brief](briefs/P03.3-runbook-desarmement.md).
- [ ] **P03.4** (PO) Armement du catalogue minimal, hors mode tournoi d'abord.
- [ ] **P03.5** (à trancher) Vue « sécurité » dans le cockpit ops de HQ — vit
      dans `40KT1_HQ`, pas ici.

**Critère de sortie** : zéro geste à blanc jugé injustifié sur la période.

## Phase 4 — Extension

- [ ] **P04.0** Agent sur `AEGIS-TOWER`, **alerte seulement** (`E6`).
- [ ] **P04.1** Couche conteneur (Falco eBPF) sur la tour — **seulement si** la
      phase 1 a produit le constat écrit qu'elle manque (`A3`, critère fixé par
      `ADR-001`).
- [ ] **P04.2** Bascule vers le profil complet — seulement si `C1` a débouché
      sur du matériel dédié.

**Critère de sortie** : décidé à l'entrée de la phase, pas maintenant.
