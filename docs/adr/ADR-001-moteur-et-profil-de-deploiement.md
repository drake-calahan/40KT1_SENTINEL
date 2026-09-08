# ADR-001 : Moteur de détection et profil de déploiement

- **Statut** : **Accepté** — décidé le 2026-09-07 (réponses A2, A3, A4, C2, F4)
- **Date** : 2026-09-07 (rédaction) · décision 2026-09-07
- **Décideurs** : Thomas (PO) + agent DevSecOps
- **Plan** : [`P01`](../plans/P01-mise-en-service.md) — lot `P01.0`
- **Dépend de** : [`ADR-003`](ADR-003-hote-du-serveur-central.md) (l'hôte décide
  du profil possible)

> **Décidé.** Wazuh 4.x en profil frugal, installé d'abord en observation seule ;
> l'hôte du manager et toute bascule de profil restent conditionnés par
> [`ADR-003`](ADR-003-hote-du-serveur-central.md).

## Contexte

Le parc compte **cinq endpoints** au plus : deux serveurs Linux
(`patator-tower` sous Ubuntu 26.04, `patator-standby` sous Linux Mint, 16 Go) et
trois postes d'administration dont aucun n'est allumé la nuit.

La production tourne intégralement en Docker derrière un tunnel sortant. La
surface d'attaque réelle est : l'application exposée, la chaîne
d'approvisionnement (pip, npm, images, le scraper qui télécharge du contenu
externe), la clé SSH d'administration, le rançongiciel.

Deux faits du dépôt frère bornent le choix :

- **16 Go partagés sur le standby**, avec un miroir Postgres et le rôle de relève
  en lecture seule. Un moteur d'indexation à 4–5 Go n'y entre pas sans coût.
- **`heal.ps1`, 514 lignes, a été supprimé par le plan `P30` de HQ**, avec ce
  constat : « l'essentiel de ce qu'il faisait, Docker le fait mieux et sans
  code ». Le sur-mesure a déjà été payé une fois.

## Options envisagées

1. **Wazuh 4.x, profil complet** — manager + indexeur + console web.
   Couvre tout : intégrité, conformité CIS, inventaire de vulnérabilités, agent
   Windows, corrélation historisée, réponse active. **~6 Go de RAM.**
   Écartée *en phase 1* : le coût mémoire n'est pas payable sur l'hôte
   disponible, et une console que personne n'ouvre ne vaut pas 5 Go.
2. **Wazuh 4.x, profil frugal** — manager seul, sans indexeur ni console.
   Mêmes agents, mêmes règles, mêmes alertes ; pas de recherche historique.
   **~1 Go.** **Retenue.**
3. **Assemblage Falco + CrowdSec (+ osquery)** — plus léger encore (~0,3 Go),
   excellente télémétrie de processus en eBPF. Écartée : il faut écrire
   soi-même l'intégrité, la conformité, l'inventaire et la corrélation —
   exactement le sur-mesure que `P30` a démonté. **Falco reste retenu en
   couche 2**, phase 4, pour ce que Wazuh voit mal : l'intérieur des conteneurs
   — **seulement si** la phase 1 produit un **constat écrit** qu'il manque de
   la visibilité *dans* les conteneurs (hôte + événements Docker déjà en P1).
   Sans ce constat, la couche 2 ne s'ouvre pas.
4. **Ne rien installer** et investir les mêmes journées dans le durcissement.
   Option honnête, meilleure que beaucoup de déploiements d'EDR ratés. Écartée
   parce que la demande porte explicitement sur la détection et la réponse —
   mais elle **fixe la barre** : un dispositif qui ne serait pas exploité
   vaudrait moins que ces journées de durcissement.

## Décision

**Wazuh 4.x en profil frugal**, agents sur les deux nœuds Linux, serveur central
sur l'hôte tranché par [`ADR-003`](ADR-003-hote-du-serveur-central.md).

Le profil frugal n'est **pas** un provisoire en attendant du matériel : c'est le
profil de la phase 1 (zéro budget matériel, `C2`). L'option ~250 € reste une
**option future documentée** ; la bascule vers un autre profil ou un autre hôte
est conditionnée par [`ADR-003`](ADR-003-hote-du-serveur-central.md), pas par
cette ADR.

Le profil frugal **n'installe aucune console**. La vue « sécurité » arrive en
phase 3, **dans le cockpit ops de HQ**. Une éventuelle console SecOps est une
**intention distincte**, liée au labo `bluefin` : elle ne se confond pas avec le
cockpit ops.

Le moteur est installé **en observation seule** : la réponse ne s'arme qu'après
la période d'observation `D5`. Cet ordre — voir d'abord, armer ensuite — est une
propriété de la décision, pas une consigne d'exploitation.

**Le point décisif est que ce choix ne ferme rien** : agents, règles, catalogue
de réponse et alertes sont identiques dans les deux profils. La bascule vers le
profil complet se fait plus tard, **sans retoucher les agents** — le manager
conserve son fichier d'alertes, l'indexation se branche au-dessus.

### La réponse automatique n'est pas déléguée au moteur

Le mécanisme de réponse active livré avec l'outil exécute des commandes `root`
sur l'agent, sans budget, sans notion de mode tournoi, et dans son propre
journal. Il est utilisé comme **transport** — c'est un bon transport — mais le
script qu'il appelle est un **relais mince** vers un exécuteur local. Catalogue,
budget et journal restent dans ce dépôt, revus en PR.
Détail : [`ADR-002`](ADR-002-catalogue-et-budget-de-reponse.md).

## Conséquences

- **Positives** : couverture large sans code à maintenir ; ~1 Go de RAM ;
  agent Windows disponible pour la phase 4 ; bascule vers le profil complet
  gratuite. Moteur sur étagère ; **règles et catalogue écrits ici** et
  versionnés — c'est ce qui justifie `rules/` et `responder/` plutôt qu'un
  paquet de règles tout fait.
- **Négatives / dette** : pas de recherche historique en phase 1 — une
  investigation se fait en ligne de commande sur les journaux. L'intérieur des
  conteneurs reste un angle mort jusqu'à une éventuelle phase 4 (déclencheur
  ci-dessus). Un composant privilégié de plus tourne sur les deux nœuds de
  production : c'est le coût honnête d'un EDR, et il n'existe pas de version
  indolore.
- **Réversibilité** : désinstallation par le rôle Ansible ; aucun état de
  production n'est modifié par l'installation.

## Ce que cette décision n'autorise pas

Exposer le serveur central ailleurs que sur le tailnet · confier l'exécution
d'un geste privilégié au moteur sans passer par l'exécuteur local · installer le
profil complet sur `patator-standby`.
