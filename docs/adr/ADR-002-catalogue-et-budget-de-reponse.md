# ADR-002 : Catalogue de réponse, budget, et comportement en mode tournoi

- **Statut** : **Accepté** — décidé le 2026-09-07 (réponses `E1` à `E7`)
- **Date** : rédigée le 2026-09-07 · décidée le 2026-09-07
- **Décideurs** : Thomas (PO) + agent DevSecOps
- **Plan** : [`P01`](../plans/P01-mise-en-service.md) — phase `P3` ·
  [`P02`](../plans/P02-lancement-implementation.md) — vague 5
- **Prolonge** : `ADR-062` de `40KT1_HQ` (auto-réparation bornée) ·
  `ADR-061` de `40KT1_HQ` (relève en lecture seule, mode tournoi)
- **Bloque** : plus rien. Cette ADR **débloque** l'écriture de l'exécuteur
  (`P03.0`). Elle **n'arme rien** : l'armement a ses conditions, § 6.

> C'est l'ADR qui porte le plus de risque du dépôt : elle décrit ce qu'une
> machine a le droit de faire sans nous, la nuit, sur les deux nœuds de
> production.

## 1. Contexte

La demande porte sur une réponse automatique. Le dépôt frère a déjà tranché la
question voisine — la réparation automatique — et sa décision est directement
transposable.

`ADR-062` de HQ pose un **critère d'admission objectif**, repris ici **mot pour
mot** (`E1`) :

> Une automatisation n'a le droit de faire que ce qu'un humain peut défaire sans
> arbitrage.

Le critère n'est pas la confiance dans le code, c'est la **réversibilité**, et
elle se vérifie geste par geste. Redémarrer un conteneur se défait tout seul.
Restaurer une base ne se défait pas.

`ADR-062` pose aussi un **budget** : trois gestes automatiques par heure
glissante, le troisième déclenchant un rouge, et au-delà le système cesse
d'agir. Le motif est le mode d'échec classique de tout automatisme : *une machine
qui se répare quarante fois par heure ne se répare pas — elle masque une panne,
et elle la masque d'autant mieux que la réparation marche.*

## 2. Options envisagées

1. **Utiliser la réponse active du moteur telle quelle.** Écartée : elle exécute
   en `root` sans budget, sans mode tournoi, et dans un journal séparé du nôtre.
2. **N'automatiser aucune réponse, alerter seulement.** Défendable, et c'est
   l'état de la phase 2. Écartée comme cible : la demande porte explicitement
   sur la réponse, et une alerte à 3 h du matin sur une rafale
   d'authentification ne réveille personne utilement.
3. **Un catalogue fermé, borné par un budget, évalué localement.** **Retenue.**

## 3. Où la décision est prise (`E7`)

**Le serveur central corrèle et ordonne ; le nœud vérifie et exécute.**
Catalogue, budget, mode tournoi et témoin de désarmement sont évalués
**localement**, jamais côté serveur. Conséquence voulue : un serveur central
compromis peut faire du bruit, pas n'importe quoi.

Le mécanisme de réponse active du moteur sert de **transport** — c'est un bon
transport. Le script qu'il appelle est un **relais mince** vers l'exécuteur de
ce dépôt (`responder/`), dont le catalogue, le budget et le journal sont revus
en pull request.

**Aucune réponse automatique sur les postes d'administration** (`E6`) : alerte
seulement, et cela vaut aussi pour `AEGIS-TOWER` en phase 4.

## 4. Le catalogue (`E2`, `E4`) — fermé

La colonne qui décide n'est pas « est-ce utile » mais **« que faut-il faire pour
le défaire »**. La colonne « mode tournoi » applique `E4` : **moins agressive
pendant l'event**, seuls les gestes **invisibles pour l'équipe en salle**
s'exécutent.

| Geste | Retour arrière | Nominal | Mode tournoi |
|---|---|---|---|
| Bloquer une IP | expiration automatique à 1 h | **armé** | **armé** |
| Arrêter un processus | il se relance, ou on le relance | **armé** | **armé** |
| Arrêter un conteneur | `docker start` — une commande | **armé** | alerte |
| Mettre un fichier en quarantaine | déplacement inverse, empreinte conservée | **armé** | **armé** |
| Désactiver un compte système | réactivation simple, mais coupe l'accès de secours | alerte | alerte |
| Révoquer les sessions JWT | reconnexion Discord de tous les utilisateurs | alerte | alerte |
| Couper le connecteur `cloudflared` | une commande — mais le site est hors ligne entre-temps | alerte | **jamais** |
| Passer l'app en lecture seule | réversible, saisies perdues entre-temps | alerte | alerte |
| Isoler le nœud du LAN | réversible *si* le tailnet tient — sinon déplacement physique à 70 km | **jamais** | **jamais** |

**Quatre gestes armés, cinq en alerte seulement**, dont un qui ne s'exécute
jamais pendant un event et un qui ne s'exécute jamais du tout.

### « Invisible pour l'équipe en salle » — la définition

Un geste est invisible s'il ne modifie **ni le service rendu, ni la session en
cours** d'un joueur ou d'un arbitre. Bloquer une adresse extérieure, arrêter un
processus qui n'est pas dans le chemin de service, déplacer un fichier en
quarantaine : invisibles. Arrêter un conteneur de la stack, couper le
connecteur, passer l'application en lecture seule : visibles, immédiatement.

Le doute tranche vers **visible**. Un samedi de ronde, se tromper coûte une panne
pour vingt personnes.

### Ce n'était pas une évidence

`ADR-061` de HQ a inversé l'intuition pour la bascule : l'automatisme n'existe
*que* pendant l'event, parce que c'est le seul moment où personne ne peut
intervenir. **Pour la sécurité, l'arbitrage rendu est l'inversion inverse** :
pendant l'event, le coût d'un faux positif dépasse le bénéfice d'une réponse
rapide, sauf pour les gestes que personne ne voit passer. Le reste part en
**alerte rouge avec une action proposée à un clic** depuis le téléphone.

Si le scénario redouté devenait le rançongiciel, se couper du monde serait le
bon geste — et cet arbitrage se reprendrait par **amendement de cette ADR**,
jamais dans un script.

## 5. Le budget (`E3`) — une garde à trois états

**Trois gestes automatiques par heure glissante**, aligné sur `ADR-062` de HQ.

| État | Condition | Comportement |
|---|---|---|
| **sous budget** | moins de 3 gestes dans l'heure glissante | le geste s'exécute, il est journalisé |
| **dernier geste** | le 3ᵉ geste de l'heure | il s'exécute, et il déclenche un **rouge** |
| **gelé** | au-delà de 3 | **plus aucun geste ne s'exécute** — refus journalisé, alerte **`critique`** (c'est le troisième cas `critique` de `F2`) |

Le dégel est un **geste humain**, jamais l'expiration d'un compteur. Une garde
qui se relâche toute seule au bout d'une heure ne garde rien : elle retarde.

Le budget est une **garde, pas un réglage**. Le désactiver ou l'augmenter est une
décision d'ADR.

## 6. Les conditions d'armement (lot `P03.4`)

L'ADR décrit ce que le dispositif **aura** le droit de faire. Elle ne le lui
donne pas. Le passage de `sentinel_response_enabled` à `true` est un **geste
d'exploitation, joué par le PO**, décrit par
[`armement-de-la-reponse.md`](../runbooks/armement-de-la-reponse.md) — jamais
l'effet de bord d'un `apply` ou d'un merge, et jamais un geste d'agent.

**Les cinq portes, dans cet ordre. Aucune ne se saute.**

1. **La phase 1 est sortie sur son critère chiffré** — moins de 3 alertes non
   pertinentes par semaine, deux semaines de suite, sur une période couvrant un
   déploiement complet et une sauvegarde offsite. Armer sur un bruit de fond non
   mesuré, c'est armer sur des faux positifs.
2. **L'alerte est prouvée sur les deux canaux** — `#securite` et le push mobile,
   preuve consignée dans `ACTIVE.md`. Un dispositif armé sans destinataire est
   exactement le défaut que ce dépôt existe pour corriger.
3. **Le mode à blanc a tourné quatorze jours** et son journal montre **zéro geste
   jugé injustifié**. Un seul geste injustifié remet le compteur à zéro : ce
   n'est pas une moyenne, c'est une condition.
4. **Le désarmement d'urgence a été joué depuis un téléphone**, pour de vrai, pas
   relu. Un frein qu'on n'a jamais essayé n'est pas un frein.
5. **Un geste à la fois, hors mode tournoi d'abord**, et **au moins sept jours**
   entre deux armements. Armer les quatre gestes le même soir, c'est renoncer à
   savoir lequel s'est trompé.

Chaque armement se consigne dans `ACTIVE.md` § « Ce qui est armé » : le geste, la
date, qui l'a joué. Le tableau est le seul endroit qui dise ce qui tourne.

**Le retour en arrière est symétrique et immédiat** : un geste armé qui produit
un geste injustifié est **désarmé le jour même** et repasse en mode à blanc —
lui seul, pas le dispositif entier. Le désarmement ne demande l'accord de
personne ; c'est l'armement qui demande des preuves.

## 7. Le désarmement d'urgence (`E5`)

Trois chemins, dont un qui ne demande que SSH :

1. le fichier témoin `response-disarmed` sur le nœud, lu **à chaque geste**,
   **avant** toute autre vérification ;
2. une commande du cockpit ops ;
3. une note dans le runbook de secours.

Le témoin prime sur tout, y compris sur la validité de l'ordre reçu : on ne
vérifie pas si un geste est légitime quand le frein est tiré, on s'arrête.

## 8. Traçabilité

Chaque geste **et chaque refus** est journalisé, avec son motif, et poussé en
orange. Au matin, on doit pouvoir lire ce que la machine a fait sans nous — **et
ce qu'elle n'a pas fait**. Une réponse invisible est une dérive qui a l'air d'un
miracle.

## Conséquences

- **Positives** : les incidents bénins se traitent sans réveiller personne ; le
  budget garantit qu'un incident réel finit **toujours** par se voir ; aucun
  geste du catalogue ne peut détruire de la donnée.
- **Négatives / dette** : un catalogue fermé ne couvre pas ce qu'on n'a pas
  prévu — c'est le prix. Les cinq portes de l'armement rendent la mise en service
  lente : un mois au minimum entre la fin de la phase 1 et le premier geste armé,
  et c'est délibéré.
- **Réversibilité** : le catalogue est désarmable en bloc par une variable, geste
  par geste par le catalogue, et hors bande par le témoin.

## Ce que cette décision n'autorise pas

Restaurer une base · revenir à une version antérieure · promouvoir le standby en
écriture · supprimer ou modifier une donnée métier · faire tourner un secret ·
poser ou retirer le mode tournoi (il appartient à HQ) · **élargir le catalogue
autrement que par amendement de cette ADR** · armer plus d'un geste à la fois ·
armer en mode tournoi un geste qui n'a pas d'abord tourné armé hors tournoi ·
dégeler le budget automatiquement.
