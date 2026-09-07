<div align="center">
  <h1>40KT1 Sentinelle</h1>
  <p><b>EDR / HIDS auto-hébergé du parc 40KT1</b> — un agent par endpoint, un serveur central qui corrèle,<br/>et une réponse automatique <i>bornée</i> sur <code>patator-tower</code> et <code>patator-standby</code>.</p>
</div>

---

> **État du dépôt : amorce.** Rien n'est installé, rien n'est décidé.
> Le cadrage attend des réponses, et **quatre questions doivent être tranchées
> avant le premier rôle Ansible** : `C1` (où vit le serveur central) ·
> `E2` (catalogue de réponse) · `E4` (mode tournoi) ·
> `H3` (frontière de propriété avec HQ).
>
> Questionnaire : [`docs/cadrage/questionnaire.md`](docs/cadrage/questionnaire.md).

## Trois portes

| Tu es… | Va ici | En une phrase |
|--------|--------|----------------|
| **PO / décideur** | [`docs/cadrage/questionnaire.md`](docs/cadrage/questionnaire.md) | Trente questions, un défaut proposé par question |
| **Agent IA** (Claude Code, Cursor) | [`AGENTS.md`](AGENTS.md) | Harnais `.agent/` — lire avant toute modif |
| **Ops** | [`docs/runbooks/`](docs/runbooks/) | Procédures — **aucune n'est jouable aujourd'hui** |

## Ce que ce dépôt fera

- **Voir** — intégrité de fichiers, journaux système, `auditd`, conformité, inventaire de paquets, événements Docker, sur les deux nœuds Linux du parc.
- **Corréler** — un serveur central qui rapproche les événements des deux sites.
- **Alerter** — par le chemin déjà éprouvé de HQ (`notify.sh` : Discord + push mobile), sur un salon dédié.
- **Répondre** — un catalogue **fermé**, un budget de gestes par heure, un mode tournoi, et un désarmement d'urgence hors bande.

## Ce que ce dépôt ne fera pas

Détection réseau · moteur antiviral à signatures · tout ce qui est sous le système
(micrologiciel, démarrage) · la sécurité de la chaîne Git elle-même.
Détail et justification : [`docs/adr/`](docs/adr/).

## Le dépôt frère

L'infrastructure appartient à **`40KT1_HQ`**. Sentinelle s'y greffe et ne la
reconfigure jamais. La frontière est écrite — et elle doit exister **des deux
côtés** : [`docs/contrat-hq.md`](docs/contrat-hq.md).

## Documentation

| Besoin | Lien |
|--------|------|
| Hub documentaire | [`docs/README.md`](docs/README.md) |
| Décisions d'archi (ADR) | [`docs/adr/`](docs/adr/) |
| Plan de mise en service | [`docs/plans/P01-mise-en-service.md`](docs/plans/P01-mise-en-service.md) |
| Index actif (agents) | [`.agent/ACTIVE.md`](.agent/ACTIVE.md) |
| Backlog ouvert | [`.agent/TASKS.md`](.agent/TASKS.md) |
| Playbook Cursor | [`.cursor/PLAYBOOK.md`](.cursor/PLAYBOOK.md) |
