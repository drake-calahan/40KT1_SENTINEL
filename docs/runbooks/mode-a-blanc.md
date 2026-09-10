# Mode à blanc — lire le journal sans rien laisser jouer

> ⚠️ **PAS ENCORE JOUABLE sur une machine.** L'exécuteur et le relais sont
> **écrits** (`P03.0`, `P03.1`, `P03.6`) ; rien n'est installé ni branché sur
> `patator-tower` / `patator-standby`. Ce runbook devient jouable quand la
> réponse tourne en mode à blanc sur au moins un nœud
> (`SENTINEL_RESPONSE_ENABLED=true` **et** `SENTINEL_RESPONSE_DRY_RUN` ≠ `false`).
>
> Il ne décrit **pas** l'armement réel — c'est
> [`armement-de-la-reponse.md`](armement-de-la-reponse.md) (`P03.4`, geste PO).

## À quoi sert cette période

Deux semaines pendant lesquelles l'exécuteur **décide et journalise** ce qu'il
aurait fait, **sans exécuter** le geste. Le budget, le catalogue, le mode
tournoi et le frein de désarmement se comportent **comme en mode armé**. Seule
la dernière ligne change : pas de commande privilégiée.

Critère de sortie de la phase 3 (extrait) : *zéro geste à blanc jugé
injustifié sur la période*. Ce runbook rend ce jugement possible **sans relire
du code**.

## 1. Vérifier que le mode à blanc est *effectivement* actif

Ne pas se fier à ce qu'on croit avoir mis dans un `.env`. Constater.

Sur le nœud :

```bash
# Variables lues par responder.config — « true » littéral pour armer la
# décision ; dry-run faux seulement si la valeur dit clairement non.
grep -E '^SENTINEL_RESPONSE_(ENABLED|DRY_RUN)=' /opt/sentinel/.env

# Le journal doit exister dès qu'un ordre a été traité.
ls -la /var/lib/sentinel/reponse.jsonl

# Une ligne récente doit porter a_blanc=true et resultat=aurait_execute
# (ou refuse / echoue) — jamais resultat=execute pendant cette période.
tail -n 5 /var/lib/sentinel/reponse.jsonl
```

| Constat | Verdict |
|---------|---------|
| `ENABLED` absent / autre que true | **Désarmé** — rien à lire ici ; on n'est pas en mode à blanc |
| `ENABLED=true` et `DRY_RUN=false` | **Armé pour de vrai** — **stop** ; revenir à dry-run ou désarmer (`desarmement-d-urgence.md`) |
| `ENABLED=true` et dry-run non-false, mais une ligne `resultat=execute` | **Anomalie** — le mode à blanc a fuité ; désarmer, ouvrir un lot |
| Lignes `aurait_execute` avec `"a_blanc": true` | **OK** — c'est l'état nominal de cette période |

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
   *prévu*, même sans exécution).
3. **Les `refuse`** — autant d'information que les gestes. Motifs typiques :
   hors catalogue, budget gelé / illisible, mode tournoi, désarmement, ordre
   invalide.
4. **Les `echoue`** — ne devraient **pas** apparaître en mode à blanc (rien
   n'est joué). S'ils apparaissent, le chemin d'exécution a été pris à tort.

### Commandes utiles

```bash
# Comptage du jour (UTC) par résultat
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
from datetime import datetime, UTC, timedelta
chemin = Path("/var/lib/sentinel/reponse.jsonl")
depuis = datetime.now(UTC) - timedelta(hours=24)
c = Counter()
for ligne in chemin.read_text(encoding="utf-8").splitlines():
    if not ligne.strip():
        continue
    e = json.loads(ligne)
    h = datetime.fromisoformat(e["horodatage"])
    if h >= depuis:
        c[e["resultat"]] += 1
print(dict(c))
PY
```

Pas de script versionné pour ça dans ce lot : cinq minutes, pas une usine.

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
| Phase 3 mode à blanc | tableau ci-dessous (ou copie locale ops) | gestes simulés |

Reporter un geste injustifié **aussi** dans le journal des faux positifs si la
règle source est en cause — une seule vérité sur « cette règle crie à tort ».

### Carnet mode à blanc (à tenir hors dépôt ou ici en PR docs)

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

## Format d'une ligne de journal (référence)

Champs écrits par `responder.executeur` (ne pas les « améliorer » dans une
relecture ad hoc) :

`horodatage`, `noeud`, `geste`, `cible`, `regle`, `mode`, `armement`,
`a_blanc`, `resultat`, `motif`, `severite`.

Résultats : `execute` · `aurait_execute` · `refuse` · `echoue` · `degel`
(ce dernier via `responder.degel`, geste humain).
