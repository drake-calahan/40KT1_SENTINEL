# Journal des faux positifs — phase 1

> **Audience** : PO / ops · **Usage** : une ligne par alerte · **Aucune donnée
> nominative de joueur** — le gabarit n'a aucune colonne qui en appellerait.
>
> Protocole : [`README.md`](README.md).

## Journal

| Date, heure (UTC) | Nœud | Règle | Sévérité | Verdict | Motif | Suite donnée |
|-------------------|------|-------|----------|---------|-------|--------------|
| *ex. 2026-09-10 03:32* | *patator-standby* | *ex. contact-agent* | *orange* | *non pertinente* | *EXEMPLE — coupure IPv4 connue du standby, un épisode agrégé* | *rien* |

> La ligne ci-dessus est un **exemple**. Ne pas la compter dans un récapitulatif
> réel. Effacer ou barrer dès la première vraie entrée.

**Colonnes**

| Colonne | Ce qu'elle porte |
|---------|------------------|
| Date, heure | horodatage de l'alerte |
| Nœud | `patator-tower` / `patator-standby` / *inconnu* |
| Règle | identifiant de la règle |
| Sévérité | `critique` / `rouge` / `orange` / `info` |
| Verdict | `pertinente` / `non pertinente` / `indeterminee` |
| Motif | une phrase — une exclusion sans motif finit par cacher une vraie détection |
| Suite donnée | règle affinée / exclusion écrite / rien |

**Rappels de comptage** (voir protocole § 2 et § 4) :

- Un compteur d'agrégation = **une** ligne.
- Perte de contact `patator-standby` : **une ligne par épisode**, pas par sonde.
- Deux `indeterminee` de suite sur la même règle → ouvrir une tâche.

## Récapitulatif hebdomadaire

Semaine calendaire = lundi → dimanche. Remplir une ligne par semaine de la
période `D5` (14 jours, couverture déploiement + sauvegarde offsite).

| Semaine (lun–dim) | Alertes (total) | Dont non pertinentes | Indéterminées restantes après repassage | Critère de sortie (`< 3` non pertinentes **et** 0 indéterminée restante) |
|-------------------|-----------------|----------------------|------------------------------------------|--------------------------------------------------------------------------|
| _aaaa-mm-jj → aaaa-mm-jj_ | | | | oui / non |
| _aaaa-mm-jj → aaaa-mm-jj_ | | | | oui / non |

**Sortie de phase 1** : deux semaines de suite avec « oui » **et** période
couvrant au moins un déploiement complet et une sauvegarde offsite.

Une `indeterminee` non reclassée au repassage hebdomadaire fait tomber la
semaine à « non », même à zéro alerte non pertinente (protocole § 4). Un `ok`
n'est pas un `inconnu`.
