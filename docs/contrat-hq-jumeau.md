# Jumeau du contrat de frontière — texte à porter dans `40KT1_HQ`

> **Ce fichier n'est pas un document de Sentinelle.** C'est le texte destiné au
> dépôt `40KT1_HQ`, à créer là-bas sous `docs/contrat-sentinel.md`. Il vit ici en
> attendant d'être porté, parce qu'un texte écrit et non porté se perd, et parce
> que `P00.5` n'est **pas** terminé tant que le jumeau n'est pas fusionné dans HQ.
>
> **Quand le jumeau est en place** : retirer ce fichier (`git rm`), et remplacer
> la mise en garde d'ouverture de [`contrat-hq.md`](contrat-hq.md) par la
> référence au document jumeau, avec sa date de fusion.

## Comment le porter

1. Dans `40KT1_HQ`, branche dédiée depuis un `main` frais.
2. Créer `docs/contrat-sentinel.md` avec le texte ci-dessous, entre les deux
   marqueurs, **sans le modifier** : si un point doit changer, il change **des
   deux côtés**, dans la même journée, avec la date.
3. Ajouter la ligne au hub documentaire de HQ.
4. PR, et **c'est la fusion là-bas** qui clôt `P00.5` ici — pas l'ouverture.

---

<!-- DÉBUT DU TEXTE À COPIER DANS 40KT1_HQ -->

# Contrat de frontière avec `40KT1_SENTINEL`

> **Statut** : en vigueur · **Date** : 2026-09-07
> **Jumeau** : `docs/contrat-hq.md` dans `40KT1_SENTINEL`. Ce document et son
> jumeau se modifient **ensemble**. Un contrat modifié d'un seul côté est pire
> que pas de contrat : il donne l'illusion d'un accord.

## Pourquoi ce document existe dans HQ

`40KT1_SENTINEL` déploie un dispositif de détection et de réponse sur
`patator-tower` et `patator-standby` — les deux machines que ce dépôt-ci
provisionne. Deux dépôts qui provisionnent les mêmes machines par Ansible
finissent par se défaire l'un l'autre, et le symptôme est **une règle qui
disparaît toute seule** entre deux `apply`. Ça ne ressemble pas à un conflit :
ça ressemble à une panne.

Ce texte dit ce que HQ possède, ce que Sentinelle ajoute, et les **trois seules
choses** que HQ doit s'engager à ne pas faire.

## Le principe

**HQ possède l'infrastructure. Sentinelle s'y greffe et ne la reconfigure
jamais.** Sentinelle ajoute ; elle ne réécrit pas.

## Ce que HQ possède, et que Sentinelle ne touche pas

Politique `ufw` · Docker Engine et sa configuration · Tailscale, le tailnet et
ses ACL · `unattended-upgrades` · les unités `40kt1-*` · le `.env` de la stack ·
l'arborescence `/srv/40kt1` et `~/40KT1_HQ` · le mode tournoi · l'état de la
relève · `scripts/notify.sh`, `watchdog.py`, `selfheal.py`, `failover.py`,
`backup.sh`, `mirror-sync.sh` · l'exposition publique par `cloudflared`.

Sentinelle **lit** tout cela. Elle n'en configure rien.

## Ce que Sentinelle possède, et que HQ ne touche pas

| Objet | Forme |
|---|---|
| Ses unités et timers | préfixés `sentinel-*` — jamais `40kt1-*` |
| Son `.env` | dans son propre répertoire, distinct de celui de la stack |
| Ses règles de détection, son catalogue de réponse, son exécuteur | dans son dépôt, revus en PR |
| Ses journaux de sécurité | donnée sensible : ils décrivent l'infrastructure entière |
| **Sa chaîne pare-feu de réponse** | chaîne dédiée, règles taguées, **à expiration automatique** |

## Les trois engagements de HQ

Ils sont volontairement petits. Sentinelle ne demande ni configuration, ni
exception, ni ouverture de port.

1. **Ne pas vider ni réordonner la chaîne pare-feu de Sentinelle** lors d'un
   `apply` de `host_baseline`. C'est le seul objet de Sentinelle qu'un rôle de HQ
   pourrait effacer sans le vouloir. Les règles y expirent seules — c'est leur
   garantie de réversibilité, et les retirer à la main la casse.
2. **Ne pas renommer ni déplacer** le témoin de mode tournoi
   (`node-state/tournament-mode`) ni le mécanisme qui porte l'état de la relève,
   sans amender ce contrat des deux côtés. Sentinelle les **lit** :
   - le mode tournoi **restreint** son catalogue de réponse ;
   - l'armement de la relève **arrête son serveur central** sur le standby.
3. **Garder `scripts/notify.sh` appelable** avec des destinataires passés par
   l'environnement. Sentinelle réutilise le mécanisme avec **son** salon Discord
   et **son** sujet ntfy. Aucun changement de comportement demandé.

## Ce que HQ peut attendre de Sentinelle

- **Aucun redémarrage** d'un service de production déclenché par un rôle
  Sentinelle. Un changement qui l'exigerait est signalé, pas joué.
- **Aucune écriture** dans `/srv/40kt1` ni `~/40KT1_HQ`.
- **Aucune pose de verrou** partagé : Sentinelle ne pose ni ne retire le mode
  tournoi, n'arme ni ne désarme la relève.
- **Aucune mise à jour de paquet** : elle signale un retard, `unattended-upgrades`
  décide.
- Sur `patator-standby`, où vit le serveur central : un **bornage de ressources
  permanent** (mémoire et CPU plafonnés) et un **arrêt automatique pendant la
  relève**, pour que la sécurité ne coûte jamais la disponibilité du secours.

## En cas de doute

**Un sujet qui pourrait appartenir aux deux appartient à HQ**, et Sentinelle le
lit. C'est la règle par défaut, et elle tranche sans réunion.

## Modification

Par amendement **simultané des deux fichiers**, avec la date.

<!-- FIN DU TEXTE À COPIER DANS 40KT1_HQ -->
