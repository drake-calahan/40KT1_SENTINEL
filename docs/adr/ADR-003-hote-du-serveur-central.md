# ADR-003 : Hôte du serveur central

- **Statut** : **Proposé** — attend les réponses `C1` à `C5`
- **Date** : 2026-09-07
- **Décideurs** : Thomas (PO) + agent DevSecOps
- **Plan** : [`P01`](../plans/P01-mise-en-service.md) — lot `P01.0`
- **Bloque** : toute la phase `P1`

> ⚠️ **Décision la plus structurante du chantier.** Tout le dimensionnement en
> dépend, et elle ne se change pas après coup sans réinstaller.

## Contexte

Quatre hôtes possibles, aucun parfait.

| Option | Pour | Contre |
|---|---|---|
| **(a) `patator-standby`** | allumé 24/7 · **à 70 km de la tour** — un attaquant qui prend la tour ne prend pas le serveur de sécurité · ne sert pas le nom public | 16 Go partagés avec le miroir **et** le rôle de relève · défaut réseau récidivant (4 occurrences) · domaine de panne commun entre sécurité et secours |
| **(b) matériel dédié** (mini-PC N100 / 16 Go, ordre de 250 €) | le bon choix d'architecture · aucun domaine de panne partagé · profil complet possible | coût · un hôte de plus à entretenir |
| **(c) `patator-tower`** | puissance disponible | **le serveur surveille la machine sur laquelle il tourne** : un compromis de la tour emporte les preuves |
| **(d) un poste ops** | rien | éliminé : **aucun des trois n'est allumé la nuit** (contrainte `B1` du plan `P37` de HQ) |

L'option (d) n'est pas un choix : c'est une contrainte déjà établie, et elle est
la moitié de la réponse.

## Options envisagées

1. **(c) la tour.** Écartée sur un motif simple et suffisant : un dispositif qui
   surveille son propre hôte ne survit pas au compromis de cet hôte. Les
   journaux qui comptent sont exactement ceux qu'un attaquant efface.
2. **(a) le standby, profil frugal.** Retenue par défaut, sous conditions.
3. **(b) matériel dédié.** Retenue **si le budget existe** (`C2`).

## Décision

**(b) si le budget existe ; sinon (a) en profil frugal, avec la sortie écrite.**

C'est exactement la forme qu'a prise l'exception `P31.7` pour le cockpit dans
HQ : une cohabitation transitoire, assumée, **datée**, et dont la sortie est
décrite dans l'ADR plutôt que renvoyée à plus tard.

### Si l'hôte est `patator-standby` — conditions non négociables

1. **Bornage `cgroup` permanent** : 1,5 Go de mémoire et une part de CPU
   plafonnée pour l'ensemble du dispositif. Ce qui rend la condition vérifiable
   plutôt que déclarative.
2. **Arrêt automatique du serveur central quand la relève s'arme** (`C3`).
   Pendant la relève, le standby sert l'équipe en salle ; un serveur de sécurité
   qui consomme mémoire et disque devient un risque de disponibilité.
   Les **agents**, eux, continuent d'écrire en local.
3. **Écoute sur `tailscale0` uniquement.** Jamais de Funnel, jamais via
   cloudflared, jamais sur le nom public (`C4`).
4. **La sortie est écrite** : dès qu'un matériel dédié existe, le serveur central
   déménage, et cette ADR est amendée avec la date.

### Chiffrement du stockage (`C5`)

LUKS si matériel dédié — à l'installation, cela ne coûte rien. Sur le standby :
hors périmètre de la phase 1, **noté comme dette**, pas comme oubli. Le serveur
central porte des journaux qui décrivent l'infrastructure entière : un disque
volé est une carte du système.

## Conséquences

- **Positives** : le serveur de sécurité vit sur une machine allumée en
  permanence, à 70 km de la cible principale, hors du chemin public.
- **Négatives / dette** : en option (a), sécurité et secours partagent un
  domaine de panne — c'est exactement le reproche fait à `P31.7` dans HQ, et il
  vaut ici aussi. Le défaut réseau récidivant du standby rendra les premières
  semaines bruyantes.
- **Réversibilité** : le déménagement vers un matériel dédié ne demande pas de
  retoucher les agents — seulement de les ré-enrôler.

## Ce que cette décision n'autorise pas

Installer le profil complet (indexeur + console) sur `patator-standby` ·
exposer le serveur central hors du tailnet · faire d'un poste d'administration
l'hôte du serveur central.
