# Mode à blanc — lire le journal sans rien laisser jouer

> ⚠️ **PAS ENCORE JOUABLE sur une machine.** L'exécuteur et le relais sont
> **écrits** (`P03.0`, `P03.1`, `P03.6`) ; rien n'est installé ni branché sur
> `patator-tower` / `patator-standby`. Ce runbook devient jouable quand la
> réponse tourne en mode à blanc sur au moins un nœud
> (`SENTINEL_RESPONSE_ENABLED` vrai **et** `SENTINEL_RESPONSE_DRY_RUN` non faux —
> voir § 1 pour les valeurs acceptées).
>
> Il ne décrit **pas** l'armement réel — c'est
> [`armement-de-la-reponse.md`](armement-de-la-reponse.md) (`P03.4`, geste PO).

## À quoi sert cette période

Deux semaines pendant lesquelles l'exécuteur **décide et journalise** ce qu'il
aurait fait, **sans exécuter** le geste. Le catalogue, le mode tournoi et le
frein de désarmement se comportent comme en mode armé. Le **budget compte**
les `aurait_execute` dans la fenêtre glissante (un 4ᵉ ordre de l'heure est
refusé) **et pose le témoin `budget-gele`** comme en mode armé : le gel ne se
relâche pas quand la fenêtre glisse, il attend un `degel` humain. Corrigé par
`P03.10` (2026-09-10) — avant quoi le mode à blanc aurait prouvé un budget plus
permissif que celui qu'on veut armer.

Critère de sortie de la phase 3 (extrait) : *zéro geste à blanc jugé
injustifié sur la période*. Ce runbook rend ce jugement possible **sans relire
du code**.

## 1. Vérifier que le mode à blanc est *effectivement* actif

Ne pas se fier à ce qu'on croit avoir mis dans un `.env`. **Constater d'abord
dans le journal** : `armement`, `a_blanc` et `motif` sont écrits depuis la
config **vivante** à chaque décision. Le `.env` n'est qu'une déclaration — un
fichier corrigé sans redémarrage, une unité avec son propre `Environment=`, et
les deux divergent.

Sur le nœud :

```bash
# 1) Autorité : ce que le processus a réellement décidé
ls -la /var/lib/sentinel/reponse.jsonl
tail -n 5 /var/lib/sentinel/reponse.jsonl

# 2) Déclaration (pour expliquer un écart journal ↔ fichier)
grep -E '^SENTINEL_RESPONSE_(ENABLED|DRY_RUN)=' /opt/sentinel/.env
```

Valeurs acceptées par `responder.config` (minuscules, espaces ignorés) :

| Variable | Vrai / armant | Faux / désarmant |
|----------|---------------|------------------|
| `SENTINEL_RESPONSE_ENABLED` | `true`, `1`, `oui`, `yes` | toute autre valeur ou absent → **désarmé** |
| `SENTINEL_RESPONSE_DRY_RUN` | défaut / absent / autre → **à blanc** | `false`, `0`, `non`, `no` → dry-run **éteint** |

| Constat **journal** | Verdict |
|---------------------|---------|
| `armement: "desarme"` | **Désarmé** — la période à blanc n'a **pas** commencé (même si `a_blanc: true` et `aurait_execute`) |
| `armement: "arme"` + `a_blanc: true` + motif « mode à blanc » | **OK** — état nominal de cette période |
| `armement: "arme"` + `a_blanc: false` | **Armé pour de vrai** — **stop** ; revenir à dry-run ou désarmer (`desarmement-d-urgence.md`) |
| Une ligne `resultat=execute` pendant la période | **Anomalie** — le mode à blanc a fuité ; désarmer, ouvrir un lot |

`a_blanc: true` **seul** ne suffit pas : un nœud entièrement désarmé journalise
aussi `aurait_execute` avec `a_blanc: true`. Le champ qui tranche est
`armement` (et le `motif` : « réponse désarmée : … » vs « mode à blanc : … »).

Le frein d'urgence (`SENTINEL_DISARM_FILE`, défaut
`/var/lib/sentinel/response-disarmed`) reste prioritaire : s'il est posé, chaque
ordre devient `refuse` / « désarmement d'urgence actif ». Ce n'est pas le mode à
blanc ; c'est le frein.

## 2. Lecture quotidienne (~5 minutes)

Fichier : `/var/lib/sentinel/reponse.jsonl` (surchargeable via
`SENTINEL_RESPONSE_LOG`). Une décision = une ligne JSON.

### Ce qu'on cherche, dans l'ordre

1. **Y a-t-il des `resultat=execute` ?** Si oui → anomalie (tableau ci-dessus).
2. **Les `aurait_execute`** — gestes qui auraient passé les quatre gardes.
   Relire `geste`, `cible`, `regle`, `motif` (le motif porte le retour arrière
   *prévu*, même sans exécution). Vérifier `armement: "arme"` sur ces lignes.
3. **Les `refuse`** — autant d'information que les gestes. Motifs typiques :
   hors catalogue, budget gelé / illisible, mode tournoi, désarmement, ordre
   invalide.
4. **Les `echoue`** — ne devraient **pas** apparaître en mode à blanc (rien
   n'est joué). S'ils apparaissent, le chemin d'exécution a été pris à tort.

### Commandes utiles

```bash
# Comptage du jour (UTC) par résultat — lignes illisibles comptées à part
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
from datetime import datetime, UTC, timedelta
chemin = Path("/var/lib/sentinel/reponse.jsonl")
depuis = datetime.now(UTC) - timedelta(hours=24)
c = Counter()
illisibles = 0
for ligne in chemin.read_text(encoding="utf-8").splitlines():
    if not ligne.strip():
        continue
    try:
        e = json.loads(ligne)
        h = datetime.fromisoformat(e["horodatage"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        illisibles += 1
        continue
    if h >= depuis:
        c[e.get("resultat", "?")] += 1
print(dict(c))
if illisibles:
    print(f"illisibles={illisibles}")
PY
```

Une ligne tronquée n'est **pas** un zéro : c'est une mesure qu'on n'a pas pu
prendre (`journal.py` traite le cas de la même façon). Pas de script versionné
pour ça dans ce lot : cinq minutes, pas une usine.

## 3. Qu'est-ce qu'un geste *injustifié* ?

Un `aurait_execute` est **injustifié** si, avec le même contexte (règle, cible,
heure, mode tournoi), un humain compétent **n'aurait pas** joué ce geste — ou
l'aurait joué seulement après arbitrage.

Exemples :

| Situation | Verdict probable | Suite |
|-----------|------------------|-------|
| Quarantaine d'un fichier clairement hostile hors arborescence HQ | justifié | rien |
| Blocage d'une IP du tailnet / d'un admin | injustifié | affiner la règle ou le geste |
| Arrêt d'un conteneur `fortyk-*` protégé | doit être `refuse` catalogue ; si `aurait_execute` → défaut | lot `claude` / catalogue |
| Geste pendant un déploiement annoncé | souvent injustifié *dans le temps* | exclusion documentée ou fenêtre |

Ce qui se corrige **dans une règle** (`rules/`) : trop large, mauvais chemin,
bruit de déploiement. Ce qui se corrige **dans le catalogue** (`ADR-002`) :
geste trop agressif, mauvais classement armé / alerte. **Un amendement
d'ADR avant toute ligne de code.**

## 4. Lien avec le journal des faux positifs (`P01.7`)

Même discipline, deux périodes :

| Période | Journal | Objet |
|---------|---------|-------|
| Phase 1 observation | [`docs/observation/journal-faux-positifs.md`](../observation/journal-faux-positifs.md) | alertes |
| Phase 3 mode à blanc | carnet **hors dépôt** (ops local / coffre) | gestes simulés |

Le carnet porte règles, cibles et horaires du parc : **il ne rentre pas dans
ce dépôt** (`RULES` § 4). Reporter un geste injustifié **aussi** dans le
journal des faux positifs si la règle source est en cause — une seule vérité
sur « cette règle crie à tort ».

### Carnet mode à blanc (modèle — à tenir hors dépôt)

| Date (UTC) | Nœud | Règle | Geste | Cible | Verdict | Motif | Suite |
|------------|------|-------|-------|-------|---------|-------|-------|
| | | | | | justifié / injustifié / indeterminee | | |

Trois `indeterminee` de suite sur la même règle → ouvrir une tâche, ne pas
espérer que ça se clarifie tout seul.

## 5. Fin de période

Avant d'ouvrir l'étape d'armement (`P03.4`) :

1. Zéro `execute` pendant toute la période à blanc.
2. Zéro geste jugé **injustifié** (ou chaque injustice corrigée *et* rejouée
   sans récidive).
3. Frein d'urgence **testé depuis un téléphone**
   ([`desarmement-d-urgence.md`](desarmement-d-urgence.md) / `P03.3`).
4. Preuve d'alerte sur les deux canaux déjà faite (`P02.0`) — sinon on armerait
   sans destinataire.
5. **Gel + `degel` humain exercés** — exerçables en mode à blanc depuis
   `P03.10` (2026-09-10) : le témoin `budget-gele` est posé sur
   `aurait_execute` comme sur `execute`. Le gel attend donc un humain des deux
   côtés, et c'est bien le `degel` de la période à blanc qui compte comme
   preuve.

## Format d'une ligne de journal (référence)

Champs écrits par `responder.executeur` (ne pas les « améliorer » dans une
relecture ad hoc) :

`horodatage`, `noeud`, `geste`, `cible`, `regle`, `mode`, `armement`,
`a_blanc`, `resultat`, `motif`, `severite`.

Résultats : `execute` · `aurait_execute` · `refuse` · `echoue` · `degel`
(ce dernier via `responder.degel`, geste humain).
