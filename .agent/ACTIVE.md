# ACTIVE.md — Index actif (lecture obligatoire)

> **État au 2026-09-07 : dépôt amorcé, cadrage répondu (30/30), rien n'est installé
> ni armé.** Aucune machine du parc ne porte quoi que ce soit de ce dépôt.
> **Les trois ADR sont *Acceptées*** (2026-09-07) : `P1` et l'écriture de
> l'exécuteur sont débloquées ; `ADR-001` a été acceptée en `P00.2`. Le contrat de
> frontière est en vigueur **côté Sentinelle seulement** — son jumeau reste à
> porter dans HQ (`P00.5`), et sans lui il n'engage personne.

## Phase courante

**Phase 0 — Cadrage.** Le questionnaire
([`docs/cadrage/questionnaire.md`](../docs/cadrage/questionnaire.md), 30 questions,
8 blocs) a reçu les réponses du PO le **2026-09-07**. Les quatre STRUCTURANTES
sont tranchées et consignées ci-dessous § « Réponses au cadrage ».

**Suite immédiate** (voir [`TASKS.md`](TASKS.md) Focus) : `P00.6` — tant que
l'amorce n'est pas sur `main`, aucune branche n'a de base, et rien ne fusionne.
Ensuite : `P00.7`, `P00.8`, `P00.2`, `P01.7` (`cursor`) · `P01.6` puis `P01.0`
(`claude`) · **porter le jumeau du contrat dans HQ** (`P00.5`, dernière moitié).

**Le lancement est cadré** : découpage en lots, affectation et ordre des vagues
dans [`docs/plans/P02`](../docs/plans/P02-lancement-implementation.md) ; briefs
des lots `cursor` dans [`briefs/`](briefs/). Un lot `cursor` ne part pas sans son
brief au statut `prêt`.

### Quatre décisions structurantes — tranchées au cadrage

Les arbitrages sont rendus **et formalisés**, sauf la moitié HQ du contrat de
frontière — un texte écrit d'un seul côté n'est pas une frontière.

| # | Décision | Résumé (cadrage 2026-09-07) | Formalisation |
|---|----------|-----------------------------|---------------|
| **C1** | Où vit le serveur central | **`patator-standby`**, profil frugal (zéro budget). Plan B : **`bluefin` temporaire jour** (MVP) ; secours **24/7** seulement en **pire cas**. | [`ADR-003`](../docs/adr/ADR-003-hote-du-serveur-central.md) **Acceptée** — revue le 2027-03-07 |
| **E2** | Quels gestes entrent au catalogue armé | **Quatre premiers** armés (bloquer IP, tuer processus, arrêter conteneur, quarantaine fichier) ; cinq autres alerte seulement. | [`ADR-002`](../docs/adr/ADR-002-catalogue-et-budget-de-reponse.md) **Acceptée** |
| **E4** | Réponse en mode tournoi | **Moins agressive** : gestes invisibles seulement ; le reste alerte rouge + action proposée à un clic. | [`ADR-002`](../docs/adr/ADR-002-catalogue-et-budget-de-reponse.md) **Acceptée** |
| **H3** | Frontière de propriété avec HQ | HQ possède la **base** ; Sentinelle **ajoute** (règles taguées, unités `sentinel-*`), ne réécrit jamais une politique HQ. Contrat **dans les deux dépôts**. | [`docs/contrat-hq.md`](../docs/contrat-hq.md) en vigueur ici ; **jumeau à porter** (`P00.5`) |

### Ce qui est armé

**Rien.** Et ce n'est pas un manque : c'est l'état nominal de la Phase 0.
Le tableau ci-dessous est le tableau de bord de l'armement — il se remplit au
fil des phases, une ligne à la fois, chacune par un geste d'exploitation
documenté par un runbook.

| Dispositif | État | Armé par |
|---|---|---|
| Agent sur `patator-tower` | absent | `P1` |
| Agent sur `patator-standby` | absent | `P1` |
| Serveur central | absent | `P1` — hôte **tranché** : `patator-standby` frugal |
| Alerte Discord + push | non câblée | `P2` |
| Réponse à blanc | non — noyau livré, aucun geste câblé | `P3` |
| Réponse armée | non | `P3` |
| Agent sur `AEGIS-TOWER` | absent | `P4` |

Armer la réponse n'est pas une case à cocher : `ADR-002` § 6 pose **cinq portes**
— sortie chiffrée de la phase 1, alerte prouvée sur les deux canaux, quatorze
jours de mode à blanc sans geste injustifié, désarmement joué depuis un
téléphone, puis **un geste à la fois** à sept jours d'intervalle. Le geste
appartient au PO (`P03.4`).

## Ce qu'il faut savoir avant de toucher au dépôt

⚠️ **Les cibles sont les deux machines de production du parc.**
`patator-tower` sert `hq.40kt1.com` ; `patator-standby` porte le miroir et la
relève en lecture seule. Un playbook joué ici n'est pas un playbook de
laboratoire. `--check --diff`, puis ordre PO, puis apply.

⚠️ **`patator-standby` a un défaut réseau récidivant** — quatre pertes totales
d'IPv4 en trois semaines (28/08, 30/08, 05/09, 06/09), cause NetworkManager.
Conséquence pour nous : la perte de contact avec l'agent de ce nœud doit être
**une** alerte agrégée, jamais une rafale. Le cas s'écrit dans les règles dès la
phase 1, pas après le premier week-end bruyant.

⚠️ **Aucun des trois postes ops n'est allumé la nuit.** C'est la contrainte `B1`
du plan `P37` de HQ, jamais levée. Elle interdit de faire d'un poste le serveur
central ; le plan B `bluefin` est **jour / MVP**, pas l'hôte nominal 24/7.

⚠️ **Le mode tournoi appartient à HQ.** Sentinelle lit le fichier témoin
`node-state/tournament-mode` ; elle ne le pose ni ne le retire. Deux automates
qui se posent le même verrou est un mode de panne connu.

## Ce qui vient du dépôt frère, et qu'on ne réécrit pas

| Pièce (dans HQ) | Ce qu'on en fait |
|---|---|
| `scripts/notify.sh` | **réutilisé tel quel** — Discord + ntfy, salon dédié |
| `scripts/watchdog.py` | grille de sévérité et anti-répétition **calquées** |
| `ADR-062` (auto-réparation bornée) | modèle du catalogue et du budget |
| `ADR-061` (relève en lecture seule) | fournit la notion de mode tournoi |
| `roles/host_baseline` | définit la frontière — HQ possède la base |
| Cockpit ops | hôte d'une vue « sécurité » en `P3`, pas avant |

## Plans actifs

| Plan | Sujet | État |
|------|--------|------|
| [`P01`](../docs/plans/P01-mise-en-service.md) | Mise en service, phases P0 → P4 | **P0** — cadrage consigné ; suite = ADR *Accepté* |
| [`P02`](../docs/plans/P02-lancement-implementation.md) | Lancement : découpage des lots, affectation, vagues | **actif** — vague 0 bloquée par `P00.6` |

## ADR

| # | Décision | Statut |
|---|----------|--------|
| [001](../docs/adr/ADR-001-moteur-et-profil-de-deploiement.md) | Moteur de détection et profil de déploiement | **Accepté** (2026-09-07) |
| [002](../docs/adr/ADR-002-catalogue-et-budget-de-reponse.md) | Catalogue de réponse, budget, mode tournoi | **Accepté** 2026-09-07 — débloque `P3` ; porte les **conditions d'armement** |
| [003](../docs/adr/ADR-003-hote-du-serveur-central.md) | Hôte du serveur central | **Accepté** 2026-09-07 — débloque `P1` ; **revue le 2027-03-07** |

Index : [`docs/adr/README.md`](../docs/adr/README.md).

## Réponses au cadrage

> Format : `Q — réponse — date`. Une réponse consignée ici fait autorité sur le
> défaut proposé du questionnaire. Source inline :
> [`docs/cadrage/questionnaire-reponse.md`](../docs/cadrage/questionnaire-reponse.md).

**A1** — `patator-tower` et `patator-standby` seuls en phase 1 ; postes admin/SRE
(`AEGIS-TOWER`, `pc-devsecops`, `bluefin`) hors périmètre initial — 2026-09-07

**A2** — voir d'abord ; réponse armée seulement après la période d'observation `D5`
— 2026-09-07

**A3** — hôte + événements Docker en phase 1 ; Falco/eBPF conteneur en phase 4 **si
la phase 1 montre qu'il manque** (pas descopé définitivement) — 2026-09-07

**A4** — oui, terrain d'apprentissage DevSecOps ; moteur sur étagère, règles et
catalogue écrits par nous — 2026-09-07

**B1** — classement défaut accepté : 1. application exposée · 2. chaîne
d'approvisionnement · 3. clé SSH / session admin · 4. rançongiciel · 5.
exfiltration · 6. abus interne — 2026-09-07

**B2** — pas d'exigence RGPD formelle ; traçage des accès admin par hygiène — 2026-09-07

**B3** — oui, connexions sortantes conteneurs en observation seule, sans liste
blanche au départ — 2026-09-07

**C1** — serveur central sur **`patator-standby`**, profil frugal (zéro budget).
Plan B : **`bluefin` temporaire jour** pour le MVP ; bascule **hôte de secours
24/7** uniquement en **pire cas** — 2026-09-07

**C2** — **zéro budget** matériel ; profil frugal obligatoire ; ~250 € documenté
comme option future — 2026-09-07

**C3** — oui : bornage `cgroup` permanent et arrêt automatique du serveur central
dès que la relève s'arme ; dérogation exceptionnelle autorisée à la demande —
2026-09-07

**C4** — tailnet uniquement ; jamais Funnel, cloudflared ni nom public — 2026-09-07

**C5** — LUKS hors périmètre phase 1 sur standby ; **dette** assumée, pas prioritaire
— 2026-09-07

**D1** — liste courte défaut (`/etc`, `.env`, clés SSH, systemd, compose, scripts,
`/srv/40kt1` hors backups/volumes, binaires sensibles) — 2026-09-07

**D2** — temps réel sur liste courte ; balayage complet toutes les 12 h — 2026-09-07

**D3** — conformité durcissement en lecture seule, rapport hebdomadaire ; aucune
remédiation automatique — 2026-09-07

**D4** — inventaire vulnérabilités paquets, rapport hebdomadaire Discord ; pas
d'alerte temps réel — 2026-09-07

**D5** — **14 jours** d'observation incluant un déploiement complet et une
sauvegarde offsite ; sortie : moins de 3 alertes non pertinentes / semaine — 2026-09-07

**E1** — critère `ADR-062` HQ repris mot pour mot (réversibilité sans arbitrage)
— 2026-09-07

**E2** — **quatre premiers** gestes armés ; cinq autres alerte seulement — 2026-09-07

**E3** — budget **3 gestes / heure glissante** ; au-delà gel — 2026-09-07

**E4** — **moins agressive** en mode tournoi ; gestes invisibles seulement ;
reste alerte rouge + action proposée — 2026-09-07

**E5** — trois chemins de désarmement d'urgence (fichier témoin, cockpit, SSH)
— 2026-09-07

**E6** — pas de réponse automatique sur postes ; alerte seulement — 2026-09-07

**E7** — serveur central corrèle et ordonne ; nœud vérifie et exécute localement
— 2026-09-07

**F1** — `notify.sh` réutilisé ; salon Discord `#securite` et sujet ntfy distincts
— 2026-09-07

**F2** — grille calquée sur `watchdog.py` + sévérité `critique` (trois cas définis)
— 2026-09-07

**F3** — alerte à la transition + agrégation 15 min avec compteur — 2026-09-07

**F4** — vue « sécurité » dans le **cockpit SRE** (ops) en P3 ; console / labo
**SecOps** = intention distincte ; console dédiée liée au labo SecOps (`bluefin`),
sans confondre avec le cockpit ops — 2026-09-07

**F5** — un exploitant (~5 min/jour + ~1 h/semaine de repassage) — 2026-09-07

**G1** — 90 jours en ligne, 12 mois archive compressée — 2026-09-07

**G2** — offsite existant, dossier séparé, archives chiffrées ; **prouver** l'écriture
(retex 04/09) — 2026-09-07

**G3** — envoi immédiat vers le serveur central ; pas de journal WORM nœud en P1
— 2026-09-07

**H1** — dépôt `40KT1_SENTINEL`, privé, même propriétaire GitHub que HQ — 2026-09-07

**H2** — harnais `.agent/` adapté : **Claude Code + Cursor uniquement**, **aucun
serveur MCP** ; ADR repartent à `ADR-001` — 2026-09-07

**H3** — HQ possède la base ; Sentinelle ajoute tagué ; contrat écrit des deux
côtés — 2026-09-07

**H4** — pas d'`apply` production sans go PO ; `--check --diff` obligatoire — 2026-09-07

**H5** — mêmes workflows CI (ansible-lint, ruff/pytest, gitleaks) ; GitHub-hosted
au départ — 2026-09-07

**H6** — secrets en `.env` non versionné + `.env.example` + gitleaks ; pas de coffre
P1 (dette écrite) — 2026-09-07
