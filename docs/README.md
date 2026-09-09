# Documentation 40KT1 Sentinelle

> **Audience** : tous · **Statut** : amorce · **Vérité agents** :
> [`.agent/ACTIVE.md`](../.agent/ACTIVE.md) · **Photo** :
> [`.agent/DASHBOARD.md`](../.agent/DASHBOARD.md)

Point d'entrée unique. Une intention par porte.

## Choisir sa porte

| Porte | Pour qui | Intention |
|-------|----------|-----------|
| [Cadrage](cadrage/) | PO | Répondre aux 30 questions qui débloquent le chantier |
| [Décisions](adr/) | Architecte, revue | ADR — `001`, `002` et `003` *Acceptées* (2026-09-07) |
| [Plans](plans/) | PO, agents | `P01` — mise en service, phases P0 → P4 · `P02` — découpage et affectation des lots |
| [Runbooks](runbooks/) | Ops | Procédures — **aucune n'est jouable aujourd'hui** |
| [Contrat HQ](contrat-hq.md) | Architecte, ops | Frontière de propriété avec `40KT1_HQ` |
| [Observation](observation/) | PO | Protocole et journal de la période `D5` |
| [Harnais agents](../AGENTS.md) | Claude Code, Cursor | Protocole multi-outil |

## État réel, au 2026-09-07

**Les décisions sont rendues ; rien n'est installé.** Les quatre structurantes
ont été tranchées par le PO, `ADR-002` et `ADR-003` sont *Acceptées* et
`ADR-001` attend son tour (`P00.2`). Le contrat de frontière n'engage encore que
ce dépôt : son jumeau reste à porter dans `40KT1_HQ`. Les runbooks décrivent des
gestes qui ne sont pas encore jouables — chacun le dit dans son encadré
d'ouverture.

Cet état est correct et il ne doit pas être maquillé en progrès. Le seul fichier
qui dit **ce qui est armé** est [`.agent/ACTIVE.md`](../.agent/ACTIVE.md).

## Ce qui vit dans le dépôt frère

`40KT1_HQ` porte l'infrastructure, la supervision de disponibilité
(`watchdog.py`), l'auto-réparation (`ADR-062`), la relève en lecture seule
(`ADR-061`) et le chemin d'alerte (`notify.sh`). Sentinelle **lit** et
**réutilise** ; elle ne réécrit pas. Voir [`contrat-hq.md`](contrat-hq.md).
