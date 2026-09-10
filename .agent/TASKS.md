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
> **2026-09-09, quatrième temps — quatre des six sont cochés.** La PR #9 est
> fusionnée et les quatre contrôles sont verts sur `main` (`c512271`) :
> `P01.6`, `P02.2`, `P03.6` et `P03.1` n'attendaient que ça. **`P01.0` et
> `P01.4` restent `[~]`** — leur condition n'était pas le vert de la CI mais un
> `--check --diff` réel sur la machine, et aucune machine n'a été touchée. La
> distinction n'est pas administrative : ce sont exactement les deux lots qui
> exécutent du privilégié sur `patator-standby`.
>
> **Revue de la PR #13 (`P01.1`, `cursor`) le 2026-09-09** — quatre corrections
> demandées, aucune de fond : la clé d'enrôlement passée en argument de ligne de
> commande (donc lisible dans `/proc` par tout utilisateur local, alors que
> `sentinel_server` pose déjà le secret dans un fichier), `<active-response>`
> absent au lieu d'être explicitement désactivé (sur un **agent**, l'omission
> vaut `disabled=no` — l'inverse du manager), un `assert` de secours rendu
> inatteignable par un `| first` sur `None`, et le port des événements écrit en
> dur. Deux défauts **hérités de `sentinel_server`** en sortent, et ne sont pas
> à la charge de ce lot : `P01.15` et `P01.16`, ci-dessous.
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
> - `claude` → `P01.10` **tranché** (issue B, `4.14.7`). Ensuite, et dans cet
>   ordre : **`P01.15`** et **`P01.16`** (les deux suites de la revue de
>   `P01.1`, à jouer sur les *deux* rôles à la fois — ce sont les seules tâches
>   de `claude` qui ne dépendent ni d'une machine ni d'un arbitrage), puis
>   `P01.3`, qui attend toujours qu'un agent existe. `P01.14` et `P03.9` se
>   mesurent sur la machine ; `P00.5` attend un dépôt tiers.
>
> **Plus bloqué** : plus rien côté décisions — les trois ADR sont *Acceptées* et
> l'amorce est sur `main`.
>
> **2026-09-10 — quatre PR de `cursor` fusionnées, puis passe de `claude`.**
> `P01.8` (PR #17), `P01.11`/`P01.12` (PR #18), `P01.17` (PR #19) et `P03.2`
> (PR #20) sont sur `main`. La fusion de la PR #20 a **réintroduit deux blocs
> périmés dans ce fichier** — un doublon de `P01.1` et l'ancienne ligne `[ ]`
> de `P01.17`, qui décochait un lot rendu. Retirés. *Ce que ça enseigne* : ce
> fichier est l'état partagé, et un conflit de fusion mal résolu dedans se lit
> comme une tâche à refaire.
>
> Dans la foulée, `claude` a rendu les trois lots qui ne dépendaient ni d'une
> machine ni d'un arbitrage : **`P01.15`** et **`P01.16`** (les moitiés agent,
> débloquées par la fusion de la PR #13 — les deux rôles jumeaux se relisent
> de nouveau à l'identique) et **`P03.10`** (gel collant en mode à blanc,
> révélé par la revue de `P03.2`).
>
> **Ce qui reste à `claude`** : `P01.3` (la règle anti-rafale, maintenant qu'un
> agent existe), puis ce qui se mesure sur la machine (`P01.14`, `P03.9`) ou
> attend un arbitrage PO (`P01.13`, `P03.8`) ou un dépôt tiers (`P00.5`).

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
- [x] **P00.12** (PO — ordre, 2026-09-09 · claude — mise en œuvre) Rendre les
      contrôles **obligatoires** dans le ruleset `main-protection`. **Fait — et
      le constat est plus large que la tâche.**
      À l'ouverture, le ruleset ne portait **aucune** règle
      `required_status_checks` : ni `garde-armement`, ni les trois workflows que
      `P00.6` affirme avoir rendus obligatoires. **Une PR rouge sur les quatre
      contrôles était fusionnable.** `P00.6` a donc été cochée sur une
      affirmation qui n'était pas vraie — ce n'est pas une négligence de plus,
      c'est le rappel qu'un réglage de forge ne se vérifie qu'en le lisant.
      Les quatre contextes sont désormais requis : `Ansible & YAML Lint`,
      `garde-armement`, `gitleaks`, `ruff & pytest`.
      **Et un piège a été refermé dans le même geste** : trois des quatre
      workflows portaient un filtre `paths` / `paths-ignore`. Un contrôle requis
      qui ne se **déclenche** pas ne rend jamais son verdict, et GitHub attend
      indéfiniment : toute PR documentaire — c'est-à-dire la plupart des PR de
      ce dépôt — serait devenue **infusionnable**. Les filtres sont retirés, et
      chaque fichier de workflow porte l'encadré qui dit pourquoi il n'en aura
      plus jamais. Le coût est de quelques secondes de CI sur une PR de texte.

## Suites de la revue de `P01.2` — ouvertes le 2026-09-09

> Relevées en relisant la PR #10 (`cursor`, règles d'intégrité). **Ni l'une ni
> l'autre n'est un défaut du lot** : les deux règles concernées sont bien
> écrites, et leur auteur a signalé la première en commentaire XML. Ce qui
> manque est ailleurs — dans `sentinel_fim_realtime_paths`, dont `P01.2` n'est
> pas l'écrivain. Les trois corrections demandées *dans* le lot restent sur la
> PR, pas ici.

- [x] **P01.11** (cursor, 2026-09-10) Chemins FIM alignés sur les règles
      `100131` (`/usr/bin/sudo.ws`) et démon Tailscale (`/usr/sbin/tailscaled`)
      + règle `100132`. Sans règle dédiée, le chemin surveillé restait un faux
      vert silencieux (événement générique sans sévérité Sentinelle).
      **Limite logtest** : `analysisd -t` 4.14.7 accepte `field name="file"` ;
      matching FIM réel = événement agent (plugin decoder), hors lot code —
      voir `DISCOVERY.md` § champ FIM.
- [x] **P01.12** (cursor, 2026-09-10) Cas `critique` `100101` : surveillance
      explicite de `/root/.ssh/authorized_keys` **et** de
      `/home/{{ ansible_user }}/.ssh/authorized_keys` (compte humain du parc).
      Le `HOME` dynamique sous `become` ne suffit pas — il pointe souvent vers
      `/root` et aveuglait le compte inventaire. **Limite** : rejeu sur machine
      (toucher un `authorized_keys` → événement `100101`) = geste
      d'exploitation après apply agent, hors cochage de ce lot code.
- [ ] **P01.18** (cursor) **Valider `<nodiff>` FIM sur agent réel** — gabarit +
      `sentinel_fim_nodiff_paths` (`.env`, clés, binaires) livrés avec
      `P01.11`/`P01.12`. Reste : après apply, confirmer qu'un changement du
      `.env` n'embarque **pas** le diff de secrets dans l'alerte.

## Suites de la revue de `P01.1` — ouvertes le 2026-09-09

> Relevées en relisant la PR #13 (`cursor`, rôle `sentinel_agent`, tête
> `1ca33be`). **Les quatre corrections demandées restent sur la PR** : elles
> appartiennent au lot et se rendent avant la fusion. Les deux entrées
> ci-dessous sont d'une autre nature — ce sont des défauts que
> `sentinel_agent` a **hérités** de `sentinel_server`, en le copiant fidèlement
> comme le gabarit le demande. Les corriger dans le seul rôle agent créerait
> une divergence entre deux rôles jumeaux ; ils se traitent donc ensemble, et
> par `claude`, à qui `sentinel_server` appartient.
>
> *Ce que la revue enseigne au passage* : un gabarit propage aussi ses défauts.
> C'est le prix du gabarit, et il vaut le coup — mais il impose de relire le
> modèle quand on relit la copie.

- [x] **P01.15** (claude, 2026-09-10) **Le premier geste imposé par le dépôt
      échouait sur un hôte vierge.** `RULES` et `AGENTS` imposent
      `--check --diff` avant tout `apply`. Or, dans les deux rôles, la tâche
      « s'assurer que l'unité n'est ni activée ni démarrée » interroge
      `wazuh-manager.service` / `wazuh-agent.service` alors qu'en `--check`
      `apt` n'a rien installé : l'unité n'existe pas et `systemd_service`
      échoue. Le `--check` obligatoire ne rendait donc **pas** son verdict la
      première fois — le seul moment où on en a réellement besoin.
      `99_desinstallation.yml` connaissait déjà la parade (`failed_when:
      false`), mais elle n'est pas au bon endroit : ici il faut **distinguer**
      « unité absente parce que `--check` n'a rien posé » (normal, à signaler)
      de « unité absente après un apply » (défaut).
      **Fait dans `sentinel_server`** : l'unité est relevée par
      `systemctl list-unit-files` avant d'être touchée ; absente en `--check`,
      elle entre au bilan avec ce qu'elle ne prouve pas (« ce `--check` ne
      prouve donc PAS que le moteur restera à l'arrêt ») ; absente hors
      `--check`, le rôle **refuse de poursuivre**. **Moitié agent portée le
      2026-09-10**, à la fusion de la PR #13 : même relevé par
      `service_facts`, même distinction `--check` / apply, même refus de
      poursuivre. Les deux rôles jumeaux se lisent de nouveau à l'identique.
- [x] **P01.16** (claude, 2026-09-10) **La clé du dépôt transitait par un
      chemin prévisible de `/tmp`.** Les deux rôles téléchargeaient la clé GPG
      dans `/tmp/sentinel-repo-key.asc` / `/tmp/sentinel-agent-repo-key.asc` en
      `0644`, relevaient son empreinte, puis la dé-blindaient — trois
      opérations sur un fichier à nom fixe dans un répertoire mondialement
      inscriptible. La fenêtre entre le contrôle d'empreinte et l'usage est
      étroite, et la menace n° 2 du classement `B1` est précisément celle-là.
      **Fait dans `sentinel_server`** : `ansible.builtin.tempfile` crée un
      répertoire `0700` appartenant à `root`, la clé y est écrite en `0600`
      `root:root`, et c'est le **répertoire** qui est retiré à la fin. La
      fenêtre n'est pas rétrécie, elle est supprimée : le chemin n'est plus
      devinable. **Moitié agent portée le 2026-09-10** : `/tmp/sentinel-agent-
      repo-key.asc` en `0644` a disparu du rôle `sentinel_agent`.
      **Limite** : le rejeu sur machine (`--check --diff` réel) reste un geste
      d'exploitation — ce lot ne prouve que la lecture du code.

## Phase 1 — Observation seule

> **Débloquée** : `ADR-003` est *Acceptée* (2026-09-07). Aucune alerte poussée,
> aucune réponse : on mesure le bruit de fond. Ordre réel : `P01.7` → `P01.6` → `P01.0` → `P01.2` → `P01.1` →
> `P01.8` → `P01.3` → `P01.4` → `P01.9` → `P01.5`.

- [x] **P01.7** (cursor, 2026-09-08) Instrumentation de la période d'observation :
      protocole et journal des faux positifs, avec le troisième état
      `indeterminee` — [brief](briefs/P01.7-instrumentation-observation.md).
      *Non bloqué par `ADR-003` : aucun fichier de machine.*
- [x] **P01.6** (claude, 2026-09-09) **Gabarit de rôle Ansible** :
      [`roles/GABARIT.md`](../infra/ansible/roles/GABARIT.md) (le contrat) +
      [`roles/gabarit/`](../infra/ansible/roles/gabarit/) (le squelette à
      copier) ; garde `*_enabled` **de type** (une chaîne `"false"` est vraie en
      Jinja) ; politique « aucun redémarrage d'un service de HQ » rendue
      mécanique par affirmation du préfixe `sentinel-` dans le handler ; bilan
      de rôle **et** bilan de play ; **garde de cible** contre le play qui vise
      zéro hôte ; [`playbooks/00_check.yml`](../infra/ansible/playbooks/00_check.yml)
      en lecture seule ; groupe `sentinel_server` rempli (`patator-standby`,
      `ADR-003`). `yamllint` vert au réglage de la CI ; **`ansible-lint` non joué en
      local** (non installable sur le poste Windows) — il tranchait en CI, et il
      a tranché : `Ansible & YAML Lint` **vert sur `main`** (`c512271`,
      2026-09-09), PR #9 fusionnée. Le gabarit a depuis servi deux fois —
      `sentinel_bornage`, puis le `sentinel_agent` de `P01.1` écrit par un autre
      agent — et les deux s'y sont tenus sans qu'il faille l'amender. C'est la
      seule preuve qui comptait pour un gabarit.
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
- [x] **P01.1** (cursor, 2026-09-09) Rôle `sentinel_agent` — agents sur
      `patator-tower` et `patator-standby`, enrôlement par clé, aucun redémarrage
      de service de production déclenché par le rôle —
      [brief](briefs/P01.1-role-sentinel-agent.md). **Fusionné PR #13** ; CI verte.
      Pose désarmée ; `--check --diff` réel sur machine = geste d'exploitation
      (empreinte clé + `.env`), hors cochage de ce lot code. Suites `P01.11` /
      `P01.12` : PR #18.
- [x] **P01.8** (cursor, 2026-09-09) Règles authentification et événements Docker —
      [brief](briefs/P01.8-regles-auth-docker.md). **Fusionné PR #17** (2026-09-10).
      *Revue : retiré privileged / socket / port `0.0.0.0` du lot — hors flux
      `docker events` ; manque consignés → `P01.17`.*
- [x] **P01.17** (cursor, 2026-09-10) Sonde d'inspection Docker (lecture seule) :
      détecter conteneur `--privileged`, montage de `docker.sock`, port publié
      sur `0.0.0.0` — cas que `docker events` / `P01.8` ne voient pas
      ([`DISCOVERY.md`](DISCOVERY.md) § réseau ;
      [brief](briefs/P01.17-sonde-inspection-docker.md)). Unités
      `sentinel-inspection-docker.{service,timer}` livrées désarmées ;
      `ok` / `ko` / `unknown`. Hors périmètre : configurer le démon (HQ).
      **Limite** : enable du timer + lecture sur parc réel = geste
      d'exploitation, hors cochage de ce lot code.
- [x] **P01.3** (claude, 2026-09-10) Règle **anti-rafale** pour la perte de
      contact d'un agent — [`rules/agents/10-contact-agent.xml`](../rules/agents/10-contact-agent.xml),
      plage `100500`–`100599`. Quatre règles : perte de contact (`100501`,
      orange), **cas `patator-standby` agrégé sur 15 min** par `<ignore>900</ignore>`
      (`100502`), retour de contact (`100503`, info — sans clôture une alerte
      finit classée `indeterminee`) et **retrait d'un agent** (`100505`, rouge :
      c'est un geste, pas une panne, et `MITRE T1562.001` le dit déjà).
      **Mesuré `wazuh-manager:4.14.7`** (Docker, `analysisd -t` + `logtest`) :
      `100501` sur la tour, `100502` sur le standby, et le **deuxième**
      événement du standby ne produit PAS d'alerte — l'agrégation mord. Deux
      découvertes en écrivant : le premier démarrage d'un agent rend `501` et
      non `503` (`<if_fts/>`), et le décodeur `ossec` n'extrait aucun champ
      nommé — voir `DISCOVERY.md`. Le noyau `bruit/` (`P02.2`) porte le
      **compteur** que `<ignore>` ne sait pas porter ; son câblage est `P02.0`.
- [x] **P01.19** (claude, 2026-09-10) **Les règles n'étaient posées sur aucune
      machine.** `rules/` portait trente-huit règles (huit fichiers) écrites
      par trois lots — et rien, dans aucun rôle, ne les copiait sur le serveur
      central. Pire : le
      `ossec.conf` rendu **n'avait pas de bloc `<ruleset>`**, et sans lui le
      moteur charge son jeu de base en ignorant `etc/rules` (mesuré 4.14.7 : un
      événement retombait sur la règle `504` au lieu de `100501`). Un serveur
      installé ainsi tourne, journalise, et n'applique **aucune** détection du
      dépôt — sans produire la moindre erreur. Livré :
      `tasks/15_regles.yml` (pose préfixée `sentinel-`, retrait de ce que le
      dépôt ne justifie plus, refus de continuer si le dépôt est vide) + le bloc
      `<ruleset>` qui **étend** le jeu de l'éditeur au lieu de le remplacer +
      la preuve par `wazuh-analysisd -t` après la pose.
- [x] **P01.20** (claude, 2026-09-10) **Répétition à blanc du premier
      déploiement** — conteneur Debian 12 `systemd`, `tailscale0` factice, `.env`
      de test, inventaire de production joué en local. **Aucune machine du parc
      touchée.** Le premier `--check --diff` échouait à **trois** endroits et le
      premier `apply` à **deux** de plus ; les cinq sont corrigés et les trois
      playbooks rendent maintenant leur verdict de bout en bout sur un hôte
      vierge (`rc=0`). Détail dans `DISCOVERY.md` § répétition à blanc. Ce qui
      en sort et qui n'était pas dans le code : `service_facts` ne liste pas les
      `.timer` · `command` est sauté en `--check` · `systemctl show` rend
      `MemoryMax=infinity` pour une unité qu'il ne connaît pas · **un
      commentaire qui cite une balise que `wazuh-control` grep empêche l'unité
      entière de démarrer**.
      **Chaîne complète prouvée en bac à sable** : `00_check` → `--check` →
      apply désarmé (unité `inactive`/`disabled`, huit fichiers de règles,
      `analysisd -t` propre) → second passage (plafond mesuré) → armement
      (`active`, **une seule socket**, `remoted` sur le tailnet). Reste non
      prouvable ainsi : l'`apply` d'un agent avec enrôlement (deux machines),
      et la durée réelle du premier démarrage.
- [x] **P01.21** (claude, 2026-09-10) **Deux impossibilités du plan, trouvées en
      le jouant.** (a) L'inventaire prévoyait un agent sur `patator-standby`
      **et** le serveur central sur le même hôte — or `wazuh-agent` et
      `wazuh-manager` se déclarent en **conflit de paquet** : `apt` refuse. Le
      nœud qui héberge le moteur serait donc resté le seul nœud non surveillé du
      parc, c'est-à-dire celui où vivent les preuves. Corrigé : `02_agent.yml`
      vise `sentinel_agents_linux:!sentinel_server`, le rôle agent refuse de
      s'exécuter sur l'hôte du manager, et le manager **se surveille lui-même**
      (`syscheck` + journaux + `docker-listener` dans sa propre configuration,
      à partir des **mêmes** variables `sentinel_fim_*` — une seule liste, deux
      lecteurs).
      (b) `wazuh-authd` écoute sur **`0.0.0.0`** et Wazuh n'offre aucune option
      pour le lier à une interface : le port d'enrôlement et le secret qui le
      protège étaient exposés au LAN, contre `C4` — et le contrôle d'écoute de
      l'armement le refusait, à juste titre. L'enrôlement devient une
      **fenêtre** (`sentinel_server_authd_ouvert`, `false` par défaut) que
      l'exploitant ouvre puis referme ; les deux états sont signalés au bilan.
      ⚠️ **Alternative écartée** : filtrer le port par `ufw` — `ufw` appartient à
      HQ (contrat de frontière) et ne couvre pas les ports publiés par Docker.
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
- [x] **P02.2** (claude, 2026-09-09) Paquet `bruit/` — le moteur de bruit, écrit
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
      13 tests, 120 verts au total ; **127 verts et `ruff` vert au relevé du
      2026-09-09 sur `main`**, PR #9 fusionnée.
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
- [x] **P03.6** (claude, 2026-09-09) `responder/gestes/` — les quatre gestes
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
- [x] **P03.1** (claude, 2026-09-09) `responder/relais.py` — le mécanisme de
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
      **Fusionné (PR #9), CI verte sur `main`.** Ce que le relais *comprend*
      n'est toujours pas confronté à ce que le moteur *envoie* — c'est `P03.9`,
      et c'est une porte d'armement, pas une finition.
- [ ] **P03.9** (claude) Confirmer la forme réelle de l'enveloppe de réponse
      active **contre la version du moteur effectivement installée**
      (`sentinel_server_wazuh_version`). `responder/relais.py` lit aujourd'hui un
      sous-ensemble documenté et refuse ce qu'il ne comprend pas — donc il se
      teste, mais il **ne s'arme pas**. À faire après `P01.1`, quand un agent
      existe pour produire une vraie enveloppe. **Porte d'armement de `P03.4`.**
- [x] **P03.2** (cursor, 2026-09-10) Mode à blanc — runbook de lecture du journal et
      définition d'un geste injustifié —
      [brief](briefs/P03.2-runbook-mode-a-blanc.md) ·
      [`docs/runbooks/mode-a-blanc.md`](../docs/runbooks/mode-a-blanc.md).
      *Pas encore jouable sur machine : rien d'installé ; le format journal est
      celui de `responder/executeur.py`. Revue : distinguer désarmé / à blanc via
      `armement` ; budget compte mais gel non collant → `P03.10`, **corrigé le
      2026-09-10**.*
- [x] **P03.10** (claude, 2026-09-10) **Gel collant en mode à blanc.**
      `budget.geler()` n'était appelé que sur les chemins où le geste avait été
      *joué* : en `aurait_execute`, le témoin `budget-gele` n'était jamais posé
      et le gel se relâchait tout seul en sortant de la fenêtre glissante, là
      où le mode armé attend un dégel humain. Le mode à blanc prouvait donc un
      budget **plus permissif** que celui qu'on veut armer — l'inverse de ce
      que promet l'en-tête de `responder/executeur.py`. `geler()` est désormais
      appelé sur le chemin `aurait_execute` quand `etat_budget is DERNIER`, et
      la garde mord dans les deux sens : le test vieillit le journal d'un jour
      et le 4ᵉ ordre reste refusé `critique` (il échoue sans le correctif).
      Docstring de `responder/config.py` aligné sur `_VRAI` / `_FAUX`.
      Runbook `mode-a-blanc.md` § intro et § 5 remis à l'état réel : le
      `degel` humain s'exerce maintenant **pendant** la période à blanc.
      Révélé par la revue de `P03.2`.
- [ ] **P03.3** (cursor + PO) Runbook de désarmement d'urgence **testé depuis un
      téléphone** — [brief](briefs/P03.3-runbook-desarmement.md).
      *Brief encore esquisse : attend `P03.2` livré et un témoin lu pour de vrai.*
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
