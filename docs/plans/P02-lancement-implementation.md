# P02 — Lancement de l'implémentation : découpage et affectation

> **Statut** : actif · **Date** : 2026-09-07 · **Auteur** : `claude` (tech lead)
> **Prolonge** : [`P01`](P01-mise-en-service.md) — il dit *quoi* et *dans quel
> ordre* ; ce plan dit **qui**, **en combien de morceaux**, et **à quelle
> condition un lot part**.
> **Suivi** : [`.agent/TASKS.md`](../../.agent/TASKS.md) ·
> **Briefs** : [`.agent/briefs/`](../../.agent/briefs/)

## 1. Ce que ce plan livre

Pas une phase de plus. Une **répartition du travail** entre les deux seuls
acteurs du dépôt — `claude` et `cursor` — en lots dont chacun tient dans une PR
et se prouve par une commande.

Il existe parce que la coordination de ce dépôt n'a pas de hub : `TASKS.md` est
le seul état partagé, et deux agents qui découvrent leur périmètre au moment de
coder se marchent dessus au troisième lot. Le découpage se fait donc **avant**,
et il est écrit.

## 2. La règle de partage

Un lot me revient s'il coche **au moins un** des trois critères :

1. **Il exécute du privilégié sur un nœud de production** — un rôle qui installe
   un démon, l'exécuteur de réponse, le bornage de ressources.
2. **Il fixe un contrat que d'autres lots implémentent** — une ADR, le gabarit de
   rôle, le format du journal de réponse, le catalogue.
3. **Il traverse la frontière avec `40KT1_HQ`** — contrat jumeau, lecture du mode
   tournoi, arrêt du serveur central pendant la relève.

Tout le reste va à Cursor. **Pas par défaut** : parce que ce sont les lots dont
la spécification est complète *avant* la première ligne de code.

Le corollaire est la partie qui coûte, et elle est à ma charge : **un lot Cursor
n'est lançable que si son brief ne laisse aucune question ouverte.** Le brief est
le livrable de conception ; le code en est la conséquence. Un brief qui dit
« faire au mieux » n'est pas un brief, c'est une délégation de l'arbitrage — et
l'arbitrage est exactement ce que le critère 2 me garde.

## 3. Prêt à lancer (DoR) — fini (DoD)

**Un lot est prêt** quand : la décision amont est rendue (ADR *Acceptée* si le
lot en dépend) · son brief existe et porte le statut `prêt` · aucune autre tâche
`[~]` ne touche sa zone de fichiers · le périmètre tient dans **une** PR.

**Un lot est fini** quand : la branche et le SHA sont donnés · les validations du
niveau revendiqué ont été **exécutées et collées** dans la PR (pas « CI verte » :
la sortie) · la checklist de PR est honnête, y compris la ligne *« cette PR
n'arme rien »* · `TASKS.md` est coché **après** les preuves · `ACTIVE.md` et
`DASHBOARD.md` sont à jour si la phase ou une décision a bougé.

Le numéro d'un lot dit son **identité**, pas son rang. Le rang est ci-dessous.

## 4. Les vagues

### Vague 0 — débloquer le tronc

Rien ne part avant : les branches se basent sur `origin/main`, et `main` ne porte
aujourd'hui qu'une racine vide. Le harnais vit dans la PR d'amorce.

| Lot | Sujet | Pour | Bloqué par |
|-----|-------|------|------------|
| `P00.6` | Fusionner l'amorce, protéger `main`, vérifier les trois workflows | **PO** | — |
| `P00.7` | Nettoyage post-amorce : `AMORCE.md` retiré, état du dépôt remis à jour | `cursor` | `P00.6` |
| `P00.8` | Garde CI « rien n'est armé » — rendre vérifiable une case de la checklist | `cursor` | `P00.6` |

### Vague 1 — formaliser la phase 0

Les quatre décisions sont **tranchées** (cadrage du 2026-09-07). Cette vague ne
re-décide rien : elle transforme des réponses consignées en ADR *Acceptées*, ce
qui est la seule forme qu'un rôle Ansible a le droit de lire.

| Lot | Sujet | Pour | Bloqué par |
|-----|-------|------|------------|
| `P00.2` | `ADR-001` (moteur, profil frugal) → *Accepté* | `cursor` | `P00.6` |
| `P00.3` | `ADR-003` (hôte du serveur central) → *Accepté*, **avec la sortie écrite** | `claude` | `P00.6` |
| `P00.4` | `ADR-002` (catalogue, budget, mode tournoi) → *Accepté* | `claude` | `P00.6` |
| `P00.5` | Contrat de frontière relu **et son jumeau créé côté HQ** | `claude` | `P00.6` |
| `P01.7` | Instrumentation de la période d'observation (journal des faux positifs) | `cursor` | `P00.6` |

`P00.3` et `P00.4` sont à moi parce qu'elles sont le critère 2 à l'état pur :
tout ce que la phase 1 et la phase 3 écriront lit ces deux textes.

### Vague 2 — fondations de la phase 1

| Lot | Sujet | Pour | Bloqué par |
|-----|-------|------|------------|
| `P01.6` | **Gabarit de rôle** + `00_check.yml` + groupe `sentinel_server` rempli | `claude` | `P00.3` |
| `P01.0` | Rôle `sentinel_server` — profil frugal, écoute `tailscale0` | `claude` | `P01.6` |
| `P01.2` | Règles d'intégrité (`rules/integrite/`) sur la liste courte `D1` | `cursor` | `P00.2` |

Le gabarit passe **avant** le premier rôle et non l'inverse : c'est lui qui fixe
la disposition des fichiers, la politique « aucun redémarrage », le bilan de fin
de rôle et la garde `*_enabled`. Sans lui, le deuxième rôle recopie les choix
implicites du premier, et on ne les revoit jamais.

### Vague 3 — la phase 1 pour de vrai

| Lot | Sujet | Pour | Bloqué par |
|-----|-------|------|------------|
| `P01.1` | Rôle `sentinel_agent` sur les deux nœuds | `cursor` | `P01.0` |
| `P01.8` | Règles authentification + Docker | `cursor` | `P01.2` |
| `P01.3` | **Anti-rafale** de perte de contact d'un agent | `claude` | `P01.1` |
| `P01.4` | Bornage `cgroup` + arrêt pendant la relève (`C3`) | `claude` | `P01.0` |
| `P01.9` | Rapports hebdomadaires conformité (`D3`) et vulnérabilités (`D4`) | `cursor` | `P01.1` |
| `P01.5` | Période d'observation, 14 jours, journal tenu | **PO** | tout ce qui précède |

### Vague 4 — alerte

| Lot | Sujet | Pour | Bloqué par |
|-----|-------|------|------------|
| `P02.0` | Câblage `notify.sh` → salon et sujet dédiés, **preuve avant tout** | `cursor` | `P01.5` |
| `P02.1` | Grille de sévérité, dont les trois cas `critique` (`F2`) | `cursor` | `P02.0` |
| `P02.2` | Moteur d'agrégation 15 min avec compteur | `claude` | `P02.1` |

`P02.2` et `P01.3` sont le **même composant** vu deux fois : l'anti-rafale est
l'agrégation appliquée à un cas particulier. Les écrire séparément, c'est écrire
deux fois la même logique et n'en corriger qu'une le jour où elle se trompe.
`P01.3` livre le noyau ; `P02.2` le généralise.

### Vague 5 — réponse

| Lot | Sujet | Pour | Bloqué par |
|-----|-------|------|------------|
| `P03.0` | Exécuteur : catalogue déclaratif, **quatre gardes**, journal, tests de refus | `claude` | `P00.4`, `P02.2` |
| `P03.6` | Les quatre gestes armables, chacun avec son retour arrière | `claude` | `P03.0` |
| `P03.1` | Relais mince côté agent | `claude` | `P03.6` |
| `P03.2` | Mode à blanc : runbook et lecture du journal | `cursor` | `P03.1` |
| `P03.3` | Runbook de désarmement, **testé depuis un téléphone** | `cursor` + **PO** | `P03.2` |
| `P03.4` | Armement du catalogue minimal | **PO** | `P03.3` |
| `P03.5` | Vue « sécurité » dans le cockpit ops (dépôt `40KT1_HQ`) | à trancher | `P03.4` |

L'exécuteur ne se sous-traite pas, et il ne se livre pas en une PR : trois lots,
parce que le noyau — les gardes — doit être vert et relu **avant** que le premier
geste privilégié existe. Un catalogue écrit avant ses gardes est un catalogue
qu'on arme par mégarde.

## 5. Ce que je garde, et à quoi ça ressemblera

Le détail se décide dans chaque lot ; l'intention est écrite ici pour que Cursor
sache **où s'arrêter**.

| Lot | Intention de conception |
|-----|-------------------------|
| `P00.3` | Accepter `(a) patator-standby` frugal **avec** ses quatre conditions rendues vérifiables et une **sortie datée** — le motif `P31.7` de HQ, pas une cohabitation sans fin. Le plan B `bluefin` y est écrit comme MVP de jour, jamais comme hôte 24/7. |
| `P00.4` | Figer le catalogue geste par geste : armé / alerte / jamais, en mode normal **et** en mode tournoi, avec la colonne « retour arrière » comme seul juge. Le budget devient une garde à trois états, pas un compteur. |
| `P00.5` | Le jumeau côté HQ, avec la liste d'objets identique et la date. Une frontière écrite d'un seul côté n'est pas une frontière. |
| `P01.6` | Un gabarit de rôle qui rend impossible ce qu'on ne veut pas : aucun handler de redémarrage d'un service de HQ, garde `*_enabled` en tête de rôle, bilan de fin de play avec le **nombre d'hôtes réellement touchés**. |
| `P01.0` | Le manager frugal : version épinglée, écoute `tailscale0` seule, aucun indexeur, aucune console, désinstallation par le rôle. |
| `P01.3` / `P02.2` | Un moteur de bruit unique : fenêtre, compteur, transition, et `unknown` distinct de `ko` — une perte de contact n'est pas une absence d'incident. |
| `P01.4` | Le bornage `cgroup` et l'interlock avec la relève de HQ : Sentinelle **lit** l'état de la relève et s'efface ; elle ne le pose jamais. |
| `P03.0` / `P03.6` / `P03.1` | Les quatre gardes dans l'ordre — désarmement, catalogue, budget, tournoi — évaluées **localement**, testées sur leurs refus autant que sur leurs gestes. |

## 6. Parallélisme : ce qui peut tourner ensemble

Sans hub, la collision se produit sur un **fichier**, pas sur une tâche. La règle
est donc : **pas deux lots ouverts sur la même zone**.

| Zone | Propriétaire pendant les vagues | Remarque |
|------|-------------------------------|----------|
| `docs/adr/ADR-001*` | `cursor` (`P00.2`) | chaque PR d'ADR ne touche **que sa ligne** dans les index |
| `docs/adr/ADR-002*`, `ADR-003*`, `docs/contrat-hq.md` | `claude` | — |
| `infra/ansible/roles/sentinel_server/`, `inventory/` | `claude` | l'inventaire est une zone à un seul écrivain |
| `infra/ansible/roles/sentinel_agent/` | `cursor` | après le gabarit |
| `rules/integrite/`, `rules/authentification/`, `rules/docker/` | `cursor` | — |
| `rules/agents/` (anti-rafale) | `claude` | c'est du moteur de bruit, pas une règle de contenu |
| `responder/` | `claude` | zone fermée jusqu'à la vague 5 |
| `scripts/` | `cursor` | rapports et wrapper d'alerte |
| `.github/` | `cursor` | — |
| `.agent/TASKS.md` | **les deux, une ligne à la fois** | seul fichier partagé : ne toucher que sa propre ligne |

## 7. Risques du lancement lui-même

| Risque | Gravité | Réduction |
|---|---|---|
| Un brief incomplet : Cursor arbitre à ma place, et l'arbitrage n'est écrit nulle part | **le plus probable** | statut `prêt` explicite sur chaque brief ; un brief sans critère d'acceptation vérifiable ne passe pas en `prêt` |
| Deux lots touchent `group_vars/all/main.yml` en même temps | réel | zone à un seul écrivain (§ 6) ; toute variable nouvelle passe par le lot propriétaire |
| Un lot arme quelque chose sans le dire | grave | `P00.8` : la CI refuse un `*_enabled: true` ajouté hors documentation |
| La preuve annoncée mais non collée — le faux vert de la livraison | grave | DoD § 3 ; la sortie, pas le verdict |
| La phase 1 démarre avant qu'une alerte sache arriver | grave | ordre des vagues ; `P01.5` (observation) est un lot **PO**, et il précède `P02.0` |
| Le dépôt reste en chantier trois mois et personne ne l'exploite | **grave** | c'est le risque de `P01` § 5 ; il se combat par des vagues courtes qui livrent chacune quelque chose de lisible |

## 8. Ce que ce plan ne fait pas

Il ne re-décide aucune des quatre structurantes · il n'arme rien · il ne crée
aucune tâche sur `40KT1_HQ` autre que le jumeau du contrat (`P00.5`) · il ne
fixe pas de date : la seule échéance du chantier est la période d'observation de
`D5`, et elle ne commence pas avant que la vague 3 soit finie.
