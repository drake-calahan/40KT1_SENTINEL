# P01 — Mise en service de Sentinelle

> **Statut** : phase `P0` en cours. Rien n'est installé.
> **ADR** : [`ADR-001`](../adr/ADR-001-moteur-et-profil-de-deploiement.md) ·
> [`ADR-002`](../adr/ADR-002-catalogue-et-budget-de-reponse.md) ·
> [`ADR-003`](../adr/ADR-003-hote-du-serveur-central.md) — **`002` et `003`
> *Acceptées* le 2026-09-07 ; `001` encore *Proposé*.**
> **Découpage et affectation** : [`P02`](P02-lancement-implementation.md)
> **Suivi** : [`.agent/TASKS.md`](../../.agent/TASKS.md)

## 1. Ce que ce plan livre

Un dispositif de détection et de réponse sur les deux nœuds Linux du parc,
mis en service **dans un ordre qui rend chaque étape défaisable** : on regarde
avant d'alerter, on alerte avant d'agir, on agit à blanc avant d'agir pour de
vrai.

Cet ordre n'est pas de la prudence de façade. Il vient du runbook
`supervision-croisee.md` de HQ, dont la phrase fondatrice tient encore :

> *Armer un watchdog sans destinataire, c'est reconstruire exactement ce que ce
> chantier corrige.*

## 2. Le principe qui gouverne tout le plan

**Code livré ≠ dispositif armé.** Les deux états sont distincts et suivis
séparément :

- `TASKS.md` porte le **code** ;
- `.agent/ACTIVE.md` § « Ce qui est armé » porte le **dispositif**.

Un agent qui coche une tâche n'arme rien. Un humain qui joue un runbook arme.
Confondre les deux est la façon la plus simple de croire protégée une machine
qui ne l'est pas.

## 3. Les phases

### P0 — Cadrage *(en cours — réponses consignées 2026-09-07)*

Réponses au questionnaire **consignées** dans `ACTIVE.md`. `ADR-002` et
`ADR-003` sont passées *Acceptées* le 2026-09-07 ; restent `ADR-001` (`P00.2`),
le **jumeau** du contrat de frontière côté HQ (`P00.5`) et la mise en place du
dépôt (`P00.6`).

**Aucune machine touchée.**

> **Sortie P0** : quatre STRUCTURANTES tranchées **et** formalisées en ADR
> *Accepté* + contrat HQ jumeau. Voir Focus [`TASKS.md`](../../.agent/TASKS.md).

### P1 — Observation seule

Serveur central sur l'hôte tranché par `ADR-003`, profil frugal. Agents sur
`patator-tower` et `patator-standby`. Intégrité, journaux, conformité,
inventaire, événements Docker.

**Aucune alerte poussée, aucune réponse.** On mesure le bruit de fond.

Deux points à ne pas repousser :

- **La règle anti-rafale de perte de contact s'écrit maintenant**, pas après le
  premier week-end bruyant. Motif : le défaut réseau récidivant de
  `patator-standby` (4 occurrences en trois semaines).
- **Le bornage `cgroup`** et, si l'hôte est le standby, l'arrêt automatique
  pendant la relève — sinon la condition d'`ADR-003` reste déclarative.

> **Sortie, chiffrée** : moins de 3 alertes non pertinentes par semaine, **deux
> semaines de suite**, sur une période couvrant au moins un déploiement complet
> et une sauvegarde offsite.

### P2 — Alerte

Câblage de `notify.sh` vers le salon Discord dédié et le sujet ntfy dédié.
Grille de sévérité calquée sur `watchdog.py`, plus la sévérité `critique`.
Agrégation par fenêtre de 15 minutes **avec compteur** — le compteur est
l'information, pas les 143 messages.

**La preuve d'arrivée sur le téléphone vient avant tout le reste.** Si le message
n'arrive pas, on s'arrête ici.

> **Sortie** : une alerte de test reçue sur les deux canaux, **et** une alerte
> réelle traitée de bout en bout.

### P3 — Réponse à blanc, puis armée

L'exécuteur local journalise ce qu'il **aurait** fait, pendant deux semaines.
Puis armement du catalogue minimal, **hors mode tournoi d'abord**.
Vue « sécurité » dans le cockpit ops de HQ.

Le runbook de désarmement d'urgence est **testé depuis un téléphone** avant
l'armement, pas après. Un frein qu'on n'a jamais essayé n'est pas un frein.

> **Sortie** : zéro geste à blanc jugé injustifié sur la période, et procédure
> de désarmement jouée pour de vrai.

### P4 — Extension

Agent sur `AEGIS-TOWER` en **alerte seulement**. Couche conteneur (Falco eBPF)
sur la tour **si et seulement si** la phase 1 a montré qu'elle manque. Bascule
vers le profil complet si un matériel dédié est arrivé.

> **Sortie** : décidée à l'entrée de la phase, pas maintenant.

## 4. Ce que ce plan ne fait pas

Détection réseau · moteur antiviral à signatures · tout ce qui est sous le
système · la sécurité de la chaîne Git. Justifications dans
[`ADR-001`](../adr/ADR-001-moteur-et-profil-de-deploiement.md).

## 5. Risques suivis

| Risque | Gravité | Réduction |
|---|---|---|
| Un composant privilégié de plus sur deux nœuds de production | réel | coût honnête d'un EDR ; version épinglée, tailnet uniquement, aucune exposition publique |
| Le serveur central devient la cible la plus intéressante du parc | réel | il corrèle et ordonne, il n'exécute pas — la décision est prise sur le nœud |
| Le réseau récidivant du standby produit des alertes en rafale | **avéré** | règle d'agrégation écrite en `P1.3`, avant la mise sous tension |
| Le faux vert : un contrôle qui rend `ok` sans avoir mesuré | grave | trois états obligatoires (`ok` / `ko` / `unknown`) ; déjà deux occurrences dans HQ |
| Le dispositif n'est plus exploité au bout de trois mois | **grave** | c'est le risque le plus probable. Profil frugal et alertes poussées ne sont pas une économie : ce sont les seules choses qui survivront à 30 min d'attention par semaine |
