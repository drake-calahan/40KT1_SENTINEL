# ACTIVE.md — Index actif (lecture obligatoire)

> **État au 2026-09-10 : dépôt amorcé, cadrage répondu (30/30), rien n'est installé
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

**Suite immédiate** (voir [`TASKS.md`](TASKS.md) Focus), au **2026-09-09** :
l'amorce est sur `main`, les quatre lots de `cursor` de la vague 0/1 sont rendus
et **acceptés en revue**.

`claude` a ensuite enchaîné **six lots sur une seule branche**, sur consigne du
PO, pour une PR unique : `P01.6` (gabarit + `00_check`), `P01.0` (serveur
central), `P01.4` (bornage + interlock), `P03.6` (les quatre gestes), `P03.1`
(relais) et `P02.2` (moteur de bruit). La PR #9 est fusionnée et la CI est verte
sur `main` : **quatre sont cochés** (`P01.6`, `P02.2`, `P03.6`, `P03.1`).
**`P01.0` et `P01.4` restent ouverts** — leur condition n'a jamais été le vert
de la CI mais un `--check --diff` réel, et ce sont précisément les deux lots qui
exécutent du privilégié sur une machine de production.

**2026-09-09, revue puis fusion des PR #10, #11 et #12** : `P01.2` (règles
d'intégrité) est **fusionnée après trois corrections de revue**, et `P00.11`
(garde `garde-armement`) est fusionnée **puis prolongée** à la classe booléenne
complète — sept formes valides passaient encore au vert. Deux suites hors lot
restent ouvertes (`P01.11`, `P01.12`), toutes deux à traiter dans `P01.1`.

**`P01.1`** (`cursor` — rôle `sentinel_agent`) est **rendu, relu et fusionné**
(PR #13, 2026-09-09) : le lot tenait, **quatre corrections ont été demandées et
rendues avant fusion**.
La plus notable n'est pas un défaut d'écriture mais une asymétrie que le gabarit
ne pouvait pas attraper — sur un **agent**, un `<active-response>` absent vaut
`disabled=no`, là où sur le manager l'absence ne définit aucune commande. Le
même silence dit l'inverse des deux côtés du dialogue.

La revue a aussi montré qu'un gabarit propage ses défauts : deux problèmes de
`sentinel_agent` sont **hérités de `sentinel_server`** et se corrigent sur les
deux rôles à la fois — le `--check` obligatoire qui échoue sur un hôte vierge
(`P01.15`) et la clé de dépôt qui transite par un chemin fixe de `/tmp`
(`P01.16`).

**2026-09-10 — la vague `cursor` est rentrée, et `claude` a soldé ses trois
lots sans machine.** Quatre PR fusionnées : `P01.8` (#17, règles
authentification et événements Docker), `P01.11`/`P01.12` (#18, chemins FIM
alignés sur les règles), `P01.17` (#19, sonde d'inspection Docker) et `P03.2`
(#20, runbook du mode à blanc). La revue de `P03.2` a ouvert `P03.10`, et la
fusion de la PR #20 a laissé deux blocs périmés dans `TASKS.md` — un doublon de
`P01.1` et l'ancienne ligne `[ ]` de `P01.17` — depuis retirés. Un conflit mal
résolu dans le seul état partagé du dépôt se lit comme du travail à refaire.

Dans la foulée, `claude` a rendu les trois lots qui ne dépendaient ni d'une
machine ni d'un arbitrage :

- **`P01.15` et `P01.16`, moitiés agent** — débloquées par la fusion de la
  PR #13. Le `--check` obligatoire ne plante plus sur un hôte vierge (l'unité
  est relevée par `service_facts` ; absente en `--check` elle entre au bilan,
  absente après un apply elle arrête le rôle), et la clé du dépôt ne transite
  plus par `/tmp/sentinel-agent-repo-key.asc` en `0644` mais par un répertoire
  `0700` root créé pour l'occasion. Les deux rôles jumeaux se relisent de
  nouveau à l'identique — c'est tout l'intérêt d'avoir corrigé le gabarit et la
  copie en même temps.
- **`P03.10` — le gel du budget est collant en mode à blanc.** `geler()`
  n'était appelé que là où le geste avait été *joué* : en `aurait_execute`, le
  témoin `budget-gele` n'était jamais posé et le gel se relâchait avec la
  fenêtre glissante. Le mode à blanc prouvait donc un budget **plus permissif**
  que celui qu'on veut armer. Conséquence pratique pour la période
  d'observation : le `degel` humain s'exerce désormais **pendant** les quatorze
  jours, et non « en armement contrôlé, plus tard ».

Ce qui part maintenant : `claude` prend `P01.3` (règle anti-rafale — un agent
existe enfin) · **porter le jumeau du contrat dans HQ** (`P00.5`, dernière
moitié — dépôt tiers).

**2026-09-09 — quatre arbitrages rendus par le PO** (`A1`–`A3`, `B`). Ce qui en
sort :

- **`P01.10` tranché (issue B)** — `sentinel_server_wazuh_version` passe de
  `4.7.5` à **`4.14.7`**. Rester sur la branche de 2024 aurait figé un composant
  privilégié à ~2 ans de correctifs sur deux machines de production. Reste à
  mesurer où `D4` prend sa source (`P01.14`, **bloque `P01.9`**).
- **Empreinte de la clé du dépôt : CONFIRMÉE** sur deux infrastructures
  distinctes (CDN de l'éditeur + `keys.openpgp.org`) —
  `0DCFCA5547B19D2A6099506096B3EE5F29111145`, RSA 4096. Le rôle
  `sentinel_server` ne refuse plus de tourner. ⚠️ **La clé expire le
  2027-05-15**, avant quoi la revue d'`ADR-003` (2027-03-07) doit la reprendre.
- **Chemin de l'état de la relève : relevé, et l'hypothèse était fausse.**
  `node-state/failover-armed` **n'existe pas**. HQ ne persiste que
  `node-state/tournament-mode` (présence = booléen) et
  `backups/failover-state.json` (historique, toujours présent). Le sens de
  « la relève s'arme » n'est **pas** tranché → `P01.13`.
  `hq_failover_state_confirme` reste `false`.
- **`P03.7` : la liste des conteneurs protégés ne protégeait rien.** Les noms
  réels du parc sont `fortyk-*`, pas `40kt1-*` : les quatre conteneurs de
  production étaient tous arrêtables sous leur vrai nom. Corrigé et testé.

**2026-09-09 — la CI est enfin bloquante.** Le ruleset `main-protection` ne
portait **aucune** règle de contrôle requis : ni `garde-armement`, ni les trois
workflows que `P00.6` affirme avoir rendus obligatoires. Une PR rouge sur les
quatre contrôles était fusionnable. Les quatre contextes sont désormais requis,
et les filtres `paths` des workflows retirés — un contrôle requis qui ne se
déclenche pas bloque la PR pour toujours.

**Trois questions attendent encore le PO** — aucune ne bloque `cursor`, toutes
bloquent un armement : `P01.13` (que veut dire « la relève s'arme » — le chemin est relevé, le sens ne
l'est pas ; bloque l'armement de l'interlock `P01.4`) · `P03.8` (la quarantaine
refuse l'arborescence de HQ, conformément au contrat — et c'est gênant) ·
`P03.9` (confirmer l'enveloppe de réponse active).

**Un seul prérequis reste posé dans le code** : le chemin de l'état de la
relève (`hq_failover_state_confirme`), et il n'attend plus un fait mais un
**sens** — voir `P01.13`. L'autre, l'empreinte de la clé du dépôt de paquets
(`sentinel_server_repo_key_confirmee`), est **levée** : relevée le 2026-09-09
sur deux infrastructures distinctes.

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
| Serveur central | absent | `P1` — hôte **tranché** : `patator-standby` frugal, moteur `4.14.7` (`P01.10`) |
| Alerte Discord + push | non câblée | `P2` |
| Réponse à blanc | non — noyau **et** quatre gestes écrits, relais écrit ; **rien n'est installé sur une machine**, `SENTINEL_RESPONSE_ENABLED` reste `false` | `P3` |
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
