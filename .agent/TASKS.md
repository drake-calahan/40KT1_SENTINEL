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
> Les faire passer en ADR *Accepté* ne re-décide rien : c'est la seule forme
> qu'un rôle Ansible a le droit de lire.
>
> **Rien ne part avant `P00.6`** : les branches se basent sur `origin/main`, et
> `main` ne porte qu'une racine vide tant que l'amorce n'est pas fusionnée.
>
> **2026-09-07, dans la foulée** : `P00.3` et `P00.4` sont **faites** —
> `ADR-002` et `ADR-003` sont *Acceptées*. `P00.5` est à moitié faite : le jumeau
> du contrat reste à porter dans `40KT1_HQ`.
>
> **2026-09-09 — revue de `claude`.** Les quatre lots rendus par `cursor`
> (`P00.7`, `P00.8`, `P00.2`, `P01.7`) sont **acceptés**. Deux corrections de
> revue ont été portées, aucune fonctionnelle : le statut réel d'`ADR-001` (cinq
> phrases du dépôt affirmaient encore *Proposé*) et la porte des `indeterminee`
> au critère de sortie de la phase 1. Deux suites sont **ouvertes**, décrites
> plus bas en « Suites de revue ».
>
> **2026-09-09, seconde partie — six lots enchaînés sur une seule branche.**
> Sur instruction explicite du PO (« enchaîne le maximum sur cette branche, on
> fera une grosse PR »), `claude` a livré `P01.6`, `P01.0`, `P01.4`, `P03.6`,
> `P03.1` et `P02.2` sur `claude/cursor-work-review-2f7ede`.
>
> Six `[~]` pour un même agent **dérogent à « une tâche à la fois »**, et c'est
> écrit ici plutôt que passé sous silence. Ce que la règle protège — la
> collision avec `cursor` — n'est pas en cause : aucun de ces lots ne touche une
> zone de `cursor` (`rules/`, `scripts/`, `roles/sentinel_agent/`). Ce qui
> disparaît, en revanche, c'est le **grain de revue** : une PR de ~5 500 lignes
> se relit moins bien que six. C'est le coût assumé de la consigne, et il vaut
> d'être connu au moment de relire.
>
> **Aucun de ces six ne se coche avant le vert de la CI sur la PR.**
>
> **2026-09-09, troisième temps — les PR #10, #11 et #12 sont fusionnées.**
> `P01.2` (règles d'intégrité) a été relue, **trois corrections demandées**,
> **rendues par `cursor` et fusionnées** (détail sur la ligne `P01.2`). Deux
> suites **hors lot** restent ouvertes ci-dessus (`P01.11`, `P01.12`) : elles
> appartiennent à `P01.1`, parce que ce qui manque est dans
> `sentinel_fim_realtime_paths` et non dans `rules/`.
>
> `P00.11` (garde `garde-armement`) est fusionnée elle aussi, **et prolongée** :
> le motif livré bloquait bien les quatre cas du brief `P00.8`, mais sept formes
> tout aussi valides passaient encore — `TRUE`, `YES`, `ON`, `y`, `1` côté
> armement, `OFF` et `0` côté `dry_run`. La garde matche désormais la **classe**
> booléenne (YAML 1.1, toutes casses, formes courtes) plutôt qu'une liste
> d'orthographes, et une borne de fin de valeur supprime au passage un faux
> positif (`enabled: yesterday_placeholder`). Mesuré dans les deux sens.
>
> **La suite, en parallèle** :
> - `cursor` → **`P01.1`** (rôle `sentinel_agent`). **Débloqué et délégué le
>   2026-09-09** : `P01.6` (gabarit) et `P01.0` (rôle serveur) sont sur `main`
>   depuis la PR #9, et le brief est passé au statut **prêt**. Deuxième lot,
>   petit et indépendant, si `P01.1` attend une réponse : **`P00.11`** (garde
>   `garde-armement` élargie aux formes booléennes) — zone `.github/`, aucune
>   collision.
> - `claude` → `P01.10` **relevé rendu** (l'arbitrage est au PO) ; ensuite
>   `P01.3`, qui attend `P01.1`.
>
> **Plus bloqué** : plus rien côté décisions — les trois ADR sont *Acceptées* et
> l'amorce est sur `main`.

- [x] **P00.0** Amorce du dépôt : harnais `.agent/`, couche Cursor, hub docs,
      trois ADR au statut *Proposé*, plan `P01`, contrat de frontière avec HQ,
      squelette Ansible, CI. **Aucune machine touchée.**
- [x] **P00.1** Réponses du PO au questionnaire
      ([`docs/cadrage/questionnaire.md`](../docs/cadrage/questionnaire.md)).
      Consignées dans `ACTIVE.md`, question par question, date 2026-09-07.
- [x] **P00.10** (claude) Cadrage du lancement : découpage en lots, affectation
      `claude` / `cursor` / `PO`, briefs des lots `cursor`.
      → [`docs/plans/P02`](../docs/plans/P02-lancement-implementation.md).
- [x] **P00.6** (PO, 2026-09-07) Amorce sur `main` (PR #1 / #4) ; ruleset
      `main-protection` (PR obligatoire, pas de push direct ni force-push) ;
      trois workflows verts sur `main` (Ansible CI, Python CI, Secrets scan).
- [x] **P00.7** (cursor, 2026-09-07) Nettoyage post-amorce : `AMORCE.md` retiré,
      `README` remis à l'état réel du 2026-09-07 —
      [brief](briefs/P00.7-nettoyage-post-amorce.md).
- [x] **P00.8** (cursor, 2026-09-07) Garde CI « rien n'est armé » : la case de la
      checklist devient un contrôle qui échoue —
      [brief](briefs/P00.8-garde-ci-armement.md).
- [x] **P00.2** (cursor, 2026-09-07) `ADR-001` (moteur et profil) *Acceptée*, à
      partir des réponses `A2`, `A3`, `A4`, `C2`, `F4` consignées —
      [brief](briefs/P00.2-adr-001-accepte.md).
- [x] **P00.3** (claude, 2026-09-07) `ADR-003` **Acceptée** : hôte
      `patator-standby` en profil frugal, quatre conditions rendues vérifiables
      avec leur contrôle et leur lot, sortie écrite à trois déclencheurs et
      **revue datée au 2027-03-07**. Débloque `P1`.
- [x] **P00.4** (claude, 2026-09-07) `ADR-002` **Acceptée** : catalogue fermé
      geste par geste (4 armés / 4 alerte / 1 jamais), « invisible pour l'équipe »
      défini, budget en **trois états** avec dégel humain, et les **cinq portes
      de l'armement** (§ 6) qui cadrent `P03.4`. Débloque `P03.0`.
- [~] **P00.5** (claude, 2026-09-07) — **en attente d'un dépôt tiers, pas en
      cours ici** : le texte est prêt, la suite est une PR dans `40KT1_HQ`. Ce
      `[~]` ne consomme donc pas le « une tâche à la fois » de `claude`.
      Contrat de frontière : côté Sentinelle
      **fait** (relève et chaîne de blocage ajoutées à la liste d'objets, trois
      engagements de HQ explicités) ; le **jumeau reste à porter** dans
      `40KT1_HQ` — texte prêt dans
      [`docs/contrat-hq-jumeau.md`](../docs/contrat-hq-jumeau.md). **Ce lot ne se
      coche qu'à la fusion de la PR dans HQ**, pas à son ouverture.

## Suites de revue — ouvertes le 2026-09-09

> Deux constats de la revue des lots de `cursor`. Aucun n'est un défaut de
> livraison : les deux lots sont conformes à leur brief. Ce sont des **trous
> dans les briefs**, et ils se referment ici plutôt que dans une discussion.

- [x] **P00.11** (cursor, 2026-09-09) Garde `garde-armement` : élargir aux formes booléennes
      **équivalentes**. Le motif actuel ne reconnaît que `true` / `false`
      littéraux. Mesuré le 2026-09-09 sur `5ce90c0` : les quatre lignes
      `sentinel_response_enabled: yes`, `sentinel_agent_enabled: True`,
      `sentinel_bloc_enabled: on` et `sentinel_response_dry_run: no` ajoutées
      dans `infra/ansible/` passent la garde en **vert**. Or `yes` est l'idiome
      Ansible le plus courant : c'est exactement le mode de panne que le brief
      `P00.8` nommait (« un rôle qui pose `..._enabled: true` dans ses
      `defaults` »), et il passe. Étendre le motif à
      `true|yes|on|True|Yes|On` (et `false|no|off|…` pour `dry_run`), guillemets
      optionnels, puis **rejouer les quatre cas d'acceptation du brief `P00.8`**.
      **Fait et fusionné (PR #11), puis prolongé en revue (PR #12)** : le motif
      livré bloquait les quatre cas du brief mais laissait passer `TRUE`, `YES`,
      `ON`, `y`, `1` et, côté `dry_run`, `OFF` et `0` — mesuré. La garde matche
      désormais la **classe** booléenne (`grep -i`, formes courtes) et non une
      liste d'orthographes, sans quoi la prochaine variante rouvre le trou. Une
      borne de fin de valeur a été ajoutée : elle supprime un faux positif
      antérieur (`sentinel_desc_enabled: yesterday_placeholder` déclenchait), et
      une garde qui crie à tort finit désarmée.
      *Le gabarit `P01.6` impose déjà `false` littéral côté rôle ; cette garde
      est la ceinture, pas les bretelles.*
- [ ] **P00.12** (PO) Rendre `garde-armement` **obligatoire** dans le ruleset
      `main-protection`, aux côtés des trois workflows de `P00.6`. Un contrôle
      qui échoue mais ne bloque pas la fusion est un avis, pas une garde — et
      `RULES` § 1 ne demande pas un avis. **Geste d'exploitation : PO.**

## Suites de la revue de `P01.2` — ouvertes le 2026-09-09

> Relevées en relisant la PR #10 (`cursor`, règles d'intégrité). **Ni l'une ni
> l'autre n'est un défaut du lot** : les deux règles concernées sont bien
> écrites, et leur auteur a signalé la première en commentaire XML. Ce qui
> manque est ailleurs — dans `sentinel_fim_realtime_paths`, dont `P01.2` n'est
> pas l'écrivain. Les trois corrections demandées *dans* le lot restent sur la
> PR, pas ici.

- [ ] **P01.11** (cursor, à traiter **dans `P01.1`**) Les règles de `P01.2`
      surveillent des chemins que l'agent ne regarde pas. Deux cas mesurés sur
      la PR #10 : `100131` vise `/usr/bin/sudo.ws`, absent de
      `sentinel_fim_realtime_paths` — la règle ne mesurera **rien** ; `100130`
      ne couvre que `/usr/bin/tailscale`, alors que `/usr/sbin/tailscaled` est
      le démon **privilégié** et n'est pas surveillé. Pour chacun : ajouter le
      chemin à la liste, **ou** retirer la règle. Une règle qui ne peut pas
      recevoir d'événement est un faux vert silencieux — `RULES` § 1.
- [ ] **P01.12** (cursor, à traiter **dans `P01.1`**) **La seule règle
      `critique` du dépôt est aveugle à `root`.** `sentinel_fim_realtime_paths`
      ne déclare que le `authorized_keys` de l'utilisateur Ansible
      (`{{ HOME }}/.ssh/authorized_keys`). La règle `100101` est correctement
      écrite — son motif attrape n'importe quel chemin — mais l'agent ne lui
      enverra jamais d'événement pour `/root/.ssh/authorized_keys` ni pour les
      autres comptes. Or « modification d'`authorized_keys` » est le premier des
      **trois cas `critique`** de `F2`. Étendre la surveillance à `/root/.ssh/`
      et aux comptes humains du parc, puis **rejouer le cas** : toucher un
      `authorized_keys` de `root` doit produire un événement.

## Phase 1 — Observation seule

> **Débloquée** : `ADR-003` est *Acceptée* (2026-09-07). Aucune alerte poussée,
> aucune réponse : on mesure le bruit de fond. Ordre réel : `P01.7` → `P01.6` → `P01.0` → `P01.2` → `P01.1` →
> `P01.8` → `P01.3` → `P01.4` → `P01.9` → `P01.5`.

- [x] **P01.7** (cursor, 2026-09-08) Instrumentation de la période d'observation :
      protocole et journal des faux positifs, avec le troisième état
      `indeterminee` — [brief](briefs/P01.7-instrumentation-observation.md).
      *Non bloqué par `ADR-003` : aucun fichier de machine.*
- [~] **P01.6** (claude, 2026-09-09) **Gabarit de rôle Ansible** :
      [`roles/GABARIT.md`](../infra/ansible/roles/GABARIT.md) (le contrat) +
      [`roles/gabarit/`](../infra/ansible/roles/gabarit/) (le squelette à
      copier) ; garde `*_enabled` **de type** (une chaîne `"false"` est vraie en
      Jinja) ; politique « aucun redémarrage d'un service de HQ » rendue
      mécanique par affirmation du préfixe `sentinel-` dans le handler ; bilan
      de rôle **et** bilan de play ; **garde de cible** contre le play qui vise
      zéro hôte ; [`playbooks/00_check.yml`](../infra/ansible/playbooks/00_check.yml)
      en lecture seule ; groupe `sentinel_server` rempli (`patator-standby`,
      `ADR-003`). `yamllint` vert au réglage de la CI ; **`ansible-lint` non
      joué en local** (non installable sur le poste Windows) — il tranche en CI.
      Ne se coche qu'au vert de la CI sur la PR.
- [~] **P01.0** (claude, 2026-09-09) Rôle `sentinel_server` + playbook
      `01_server.yml` — manager seul (**profil frugal** refusé de continuer si
      un indexeur ou une console est présent), version **épinglée par apt *et*
      gelée** contre `unattended-upgrades`, clé de dépôt **vérifiée par
      empreinte**, écoute `tailscale0` résolue depuis les faits et **mesurée par
      `ss -lntp` à l'armement**, désinstallation jouable (état conservé, sa
      purge est un geste séparé). Livré **désarmé** : `policy-rc.d` empêche le
      paquet de démarrer son service à l'installation. Trois refus durs
      d'armement — témoin de désarmement posé **ou illisible**, bornage `P01.4`
      absent, écoute hors tailnet. Ne se coche qu'au vert de la CI **et** après
      un `--check --diff` réel sur la machine.
      ⚠️ **Deux prérequis avant le premier `--check`** : confirmer l'empreinte
      de la clé de dépôt (le rôle **refuse** de tourner tant que
      `sentinel_server_repo_key_confirmee` est `false`) et poser le `.env` avec
      `SENTINEL_ENROLL_KEY`. Voir le [README du rôle](../infra/ansible/roles/sentinel_server/README.md).
- [x] **P01.10** (relevé claude · **tranché PO**, 2026-09-09) **`D4` et le
      mineur du moteur.** Relevé :
      [`docs/releves/P01.10`](../docs/releves/P01.10-mineur-du-moteur-et-D4.md).
      La coupure est à `4.8.0` : avant, les résultats vivent dans une base
      **locale** du manager ; après, ils partent vers l'**indexeur** que le
      profil frugal n'installe pas, et les points de sortie `/vulnerability` de
      l'API du manager sont supprimés. **Issue B retenue** : on monte sur la
      branche courante, `D4` se produira autrement —
      `sentinel_server_wazuh_version` passe de `4.7.5` à **`4.14.7`** (la plus
      récente servie par le dépôt, relevée dans l'index apt). Motif : rester en
      `4.7.5` figeait un composant privilégié à ~2 ans de correctifs sur deux
      machines de production, pour ne gagner que la source du rapport le moins
      critique des quatre. **Ne débloque pas `P01.9` pour autant** — voir
      `P01.14`.
- [x] **P01.2** (cursor, 2026-09-09) Règles d'intégrité (`rules/integrite/`) sur la liste
      courte de `D1` — [brief](briefs/P01.2-regles-integrite.md). Fixe les plages
      d'identifiants et la correspondance sévérité ↔ niveau pour tous les lots de
      règles suivants. **Fusionné (PR #10) après les trois corrections de
      revue** : `100110` ne recouvre plus `/etc/ssh/` ni `/etc/sudoers` (la
      précédence est écrite dans la règle, plus dans l'ordre d'inclusion) ·
      `100154` visait `/etc/logrotate.status`, qui n'existe pas sur Ubuntu, et
      vise désormais `/etc/logrotate.d/` · `100150` couvre les artefacts `ucf`.
      Les motifs d'exclusion trop larges (`.tmp`, `.cache`) ont été resserrés
      sur les artefacts réels.
- [ ] **P01.1** (cursor) Rôle `sentinel_agent` — agents sur `patator-tower` et
      `patator-standby`, enrôlement par clé, aucun redémarrage de service de
      production déclenché par le rôle —
      [brief](briefs/P01.1-role-sentinel-agent.md).
- [ ] **P01.8** (cursor) Règles authentification et événements Docker —
      [brief](briefs/P01.8-regles-auth-docker.md).
- [ ] **P01.3** (claude) Règle **anti-rafale** pour la perte de contact d'un
      agent. **Le noyau est livré** (`bruit/`, voir `P02.2`) et le cas du standby
      est rejoué en test : 6 h de panne sondée à la minute → **25 alertes au lieu
      de 360**, et les quatre épisodes connus restent quatre ouvertures
      distinctes. **Reste à câbler la règle de détection elle-même**
      (`rules/agents/`) sur la sonde de contact — cela demande un agent qui
      existe, donc `P01.1`.
- [~] **P01.4** (claude, 2026-09-09) Rôle `sentinel_bornage` — les deux
      conditions vérifiables d'`ADR-003`, avec deux régimes **différents** :
      le **plafond** `cgroup` est une contrainte (posé sans garde, appliqué à
      chaud sans redémarrer, puis **relu par `systemctl show`** — le rôle échoue
      si `MemoryMax` revient à `infinity`, car un drop-in sans `daemon-reload`
      est un fichier et pas une limite) ; l'**interlock** de relève est un
      automate, donc **livré désarmé**. Trois états testés : relève armée →
      arrêt · au repos → silence · **inconnu → `signaler` par défaut**, parce
      qu'agir sur une mesure non prise est ce que `RULES` § 1 interdit et que le
      plafond borne déjà le risque. Ne se coche qu'au vert de la CI **et** après
      un `--check --diff` réel.
      ⚠️ **Armement de l'interlock bloqué** par `hq_failover_state_confirme:
      false` : le contrat de frontière nomme l'objet « état de la relève » mais
      pas le fichier qui le porte (`scripts/failover.py` / `ADR-061`, côté HQ).
      Le chemin actuel est une hypothèse. **Se confirme avec `P00.5`.**
- [ ] **P01.9** (cursor) Rapports hebdomadaires conformité (`D3`) et
      vulnérabilités (`D4`), **lecture seule**, unités `sentinel-*` livrées
      désarmées — [brief](briefs/P01.9-rapports-hebdomadaires.md).
      ⚠️ **Bloqué par `P01.10`** : la source de `D4` dépend du mineur du moteur.
      Ne pas démarrer ce lot avant l'arbitrage — le brief le présuppose résolu.
- [ ] **P01.5** (PO) Période d'observation (`D5`, 14 jours) couvrant au moins un
      déploiement complet et une sauvegarde offsite. Journal des faux positifs
      tenu selon `P01.7`.

**Critère de sortie** : moins de 3 alertes non pertinentes par semaine, deux
semaines de suite. Chiffré, mesuré, écrit — pas « ça a l'air calme ».

## Suites des arbitrages du 2026-09-09

> Trois lignes ouvertes en exécutant les décisions `A1`–`A3` et `P03.7`. Les
> deux premières sont des questions ; la troisième est une mesure qui ne peut
> se prendre que sur une machine.

- [ ] **P01.13** (PO — arbitrage · claude — mise en œuvre) **Que veut dire
      « la relève s'arme » ?** Le chemin est relevé (`A3`, 2026-09-09), le sens
      ne l'est pas. `scripts/failover.py` de HQ ne persiste que deux états :
      `node-state/tournament-mode` (présence = booléen, et c'est **lui** qui
      arme la bascule automatique) et `backups/failover-state.json` (historique,
      **présent en permanence** dès le premier passage). Le fichier
      `node-state/failover-armed` que ce dépôt supposait **n'existe pas**.
      Deux lectures possibles de `C3` : **(a)** la bascule est *armée* — c'est
      le mécanisme qui existe, mais le standby sert peut-être encore
      normalement et la RAM n'est pas sous pression ; **(b)** la bascule a *eu
      lieu* — c'est le motif d'`ADR-003`, qui est la mémoire. (b) demande de
      **parser un JSON**, pas de constater une présence : ce n'est plus le même
      interlock. `hq_failover_state_file` suit (a) en attendant, et **vaut donc
      exactement `hq_tournament_mode_file`** — deux variables pour un fichier,
      ce qui est le signal qu'il manque quelque chose côté HQ.
      `hq_failover_state_confirme` **reste `false`** : le chemin est relevé, le
      sens n'est pas tranché, et c'est le sens qui commande.
- [ ] **P01.14** (claude — mesure) **Où `D4` prend sa source en profil frugal
      sur `4.14.x`.** Non tranché par la documentation : l'éditeur dit que le
      module pousse vers l'indexeur, et dit aussi que son rapport part vers
      `analysisd` — ce qui laisserait des alertes dans `alerts.json` sans
      indexeur ; un fil de la communauté rapporte au contraire un refus
      d'initialisation quand aucun indexeur n'est joignable. Se mesure au
      premier `--check --diff` puis à la pose : le module se charge-t-il ·
      produit-il des alertes · sinon, `D4` se construit sur l'inventaire de
      paquets du `syscollector` confronté à une source CVE en lecture seule.
      **Bloque `P01.9`** — l'exigence « aucune donnée ≠ aucune vulnérabilité »
      est déjà dans son brief et n'attend, elle, aucune mesure.
## Phase 2 — Alerte

- [ ] **P02.0** (cursor) Câblage `notify.sh` vers le salon Discord dédié et le
      sujet ntfy dédié. **Preuve d'arrivée sur le téléphone avant tout le reste**
      — [brief](briefs/P02.0-cablage-alerte.md).
- [ ] **P02.1** (cursor) Grille de sévérité calquée sur `watchdog.py` + la
      sévérité `critique` et ses trois cas (`F2`) —
      [brief](briefs/P02.1-grille-severite.md).
- [~] **P02.2** (claude, 2026-09-09) Paquet `bruit/` — le moteur de bruit, écrit
      **avant le premier week-end** comme `P01` l'exige, pas après. Alerte à la
      **transition** et non à l'état ; agrégation sur fenêtre de 15 min où **le
      compteur EST l'information** (« 143 fois en 15 min » se lit, 143 messages
      apprennent à ignorer le canal — et c'est l'alerte *suivante* qu'on perd) ;
      `inconnu` a ses propres transitions, et passer de `ko` à `inconnu` n'est
      **pas** un retour à la normale ; la sévérité ne redescend jamais seule ;
      une sévérité non reconnue est traitée comme la **plus haute** (le bruit se
      corrige, le silence ne se remarque pas). Aucun booléen dans le paquet :
      impossible d'y écrire « pas ko, donc ok ». Moteur **pur** — l'instant est
      un argument, pas une horloge : les tests couvrent un week-end en 50 ms.
      13 tests, 120 verts au total.
      *N'envoie rien* : le câblage Discord/ntfy est `P02.0`, et sa première
      exigence reste la preuve d'arrivée sur le téléphone.

**Critère de sortie** : une alerte de test reçue sur les deux canaux, et une
alerte réelle traitée de bout en bout.

## Phase 3 — Réponse

> **Débloquée pour l'écriture** : `ADR-002` est *Acceptée* (2026-09-07). Rien
> n'est armé pour autant — les cinq portes de l'armement sont dans `ADR-002` § 6. L'exécuteur se livre en trois lots : le noyau et ses
> gardes **avant** le premier geste privilégié.

- [x] **P03.0** (claude, 2026-09-07) `responder/` — noyau : catalogue déclaratif,
      quatre gardes dans l'ordre, budget à trois états, journal JSONL (gestes
      **et** refus), dégel tracé. 36 tests, dont les quatre refus obligatoires et
      les cas de dégradation. `ruff` + `pytest` verts. **Aucun geste privilégié :
      rien ne peut être joué.**
- [~] **P03.6** (claude, 2026-09-09) `responder/gestes/` — les quatre gestes
      armables, **chacun rendant la commande exacte qui le défait**, avec ses
      valeurs, jusqu'au journal (`ADR-062` : défaire *sans arbitrage* ; laisser
      l'exploitant retrouver la commande à 3 h du matin **est** de l'arbitrage).
      Jamais de shell, délai sur toute commande, cible **revalidée localement**
      (le serveur central ordonne, le nœud vérifie — `ADR-002` § 3).
      `verifier_coherence()` interdit de câbler un geste que le catalogue ne
      classe pas *armé*. 88 tests verts, `ruff` 0.6.9 (version CI) vert.
      **Deux défauts corrigés au passage, tous deux dans `P03.0`** :
      (a) un geste qui **échoue** ne laissait *aucune* entrée au journal et
      l'exception s'échappait de `traiter()` — on croyait la menace traitée et
      la tentative ne consommait pas le budget, donc elle se rejouait sans fin.
      Nouveau résultat `echoue`, consommateur de budget ;
      (b) `bloquer_ip` s'appuyait d'abord sur `is_private`, qui **ne classe pas
      `100.64.0.0/10` — le tailnet — de la même façon selon la version de
      Python**. Le chemin d'administration du parc dépendait d'une mise à jour
      d'interpréteur. Plages désormais **nommées une par une**.
- [x] **P03.7** (PO — confirmation · claude — relevé et correctif, 2026-09-09)
      Liste des conteneurs non arrêtables. **Elle ne protégeait rien.** Relevé
      par `docker ps` sur `patator-tower` : les noms réels sont
      `fortyk-caddy-1`, `fortyk-db-1`, `fortyk-api-1`, `fortyk-cloudflared-1`,
      `fortyk-scraper-1` — le projet Compose s'appelle **`fortyk`**, pas
      `40kt1`. Les entrées `40kt1-db` / `40kt1-caddy` / `40kt1-api` et les
      formes nues ne correspondaient à **aucun** conteneur du parc : les quatre
      protégés étaient tous arrêtables sous leur vrai nom. Les préfixes
      `fortyk-*` sont ajoutés (le suffixe d'instance Compose `-1`, `-2` impose
      de comparer le début, pas le nom entier) ; `fortyk-scraper-1` **reste
      arrêtable**, délibérément. Rétrécir ne demande aucun amendement
      (`RULES` § 2). 8 tests ajoutés.
      *Ce que ce lot enseigne : les unités systemd de HQ portent bien `40kt1-`
      (`40kt1-backup.service`). Les deux préfixes coexistent, et c'est ce qui
      rendait l'erreur crédible à la relecture.*
- [ ] **P03.8** (PO — arbitrage · claude — mise en œuvre) **Quarantaine et
      frontière HQ.** `quarantaine_fichier` refuse tout chemin sous `/srv/40kt1`
      ou `~/40KT1_HQ` : le contrat dit que Sentinelle les surveille **en
      lecture** et n'y écrit pas — or déplacer un fichier hors d'un répertoire,
      c'est y écrire. La limite est conforme et **gênante** : un fichier déposé
      par un attaquant dans la stack est exactement ce qu'on voudrait mettre de
      côté. Trois issues : garder le refus (alerte seule) · amender le contrat
      **des deux côtés** pour autoriser le retrait depuis l'arborescence de HQ ·
      restreindre l'autorisation à des sous-chemins nommés. Ne se tranche pas
      dans un module Python.
- [~] **P03.1** (claude, 2026-09-09) `responder/relais.py` — le mécanisme de
      réponse active du moteur sert de **transport**, et rien d'autre. Le relais
      **extrait** trois champs et les passe à l'exécuteur ; il ne consulte ni le
      catalogue, ni le budget, ni le mode tournoi, ni le témoin de désarmement.
      C'est une propriété de sécurité, pas un goût d'architecture : le relais est
      la surface exposée au serveur central, et s'il décidait quoi que ce soit,
      un serveur compromis déciderait avec lui. Il **n'infère jamais le geste
      depuis la règle** — déduire, ce serait prendre la décision que le catalogue
      porte, dans le fichier le moins relu du dépôt. Il refuse l'annulation par
      le moteur : nos gestes portent leur propre retour arrière, tracé au
      journal, et une annulation externe serait un second chemin invisible.
      19 tests, presque tous sur des refus. 107 tests verts au total.
- [ ] **P03.9** (claude) Confirmer la forme réelle de l'enveloppe de réponse
      active **contre la version du moteur effectivement installée**
      (`sentinel_server_wazuh_version`). `responder/relais.py` lit aujourd'hui un
      sous-ensemble documenté et refuse ce qu'il ne comprend pas — donc il se
      teste, mais il **ne s'arme pas**. À faire après `P01.1`, quand un agent
      existe pour produire une vraie enveloppe. **Porte d'armement de `P03.4`.**
- [ ] **P03.2** (cursor) Mode à blanc — runbook de lecture du journal et
      définition d'un geste injustifié —
      [brief](briefs/P03.2-runbook-mode-a-blanc.md).
- [ ] **P03.3** (cursor + PO) Runbook de désarmement d'urgence **testé depuis un
      téléphone** — [brief](briefs/P03.3-runbook-desarmement.md).
- [ ] **P03.4** (claude — préparation · **PO — le geste**) Armement du catalogue
      minimal, hors mode tournoi d'abord. Les **cinq portes** sont posées
      (`ADR-002` § 6) ; restent le runbook rendu jouable, qui s'écrit sur le
      journal réel de l'exécuteur (`P03.0`–`P03.1`), et le geste lui-même.
      **Aucun agent n'arme** : `RULES` § 1.
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
