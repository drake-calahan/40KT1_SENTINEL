#!/usr/bin/env python3
"""Garde `beforeShellExecution` de Cursor pour 40KT1_SENTINEL.

Ce dépôt vise DEUX MACHINES DE PRODUCTION. Le garde est donc plus strict que
son jumeau de 40KT1_HQ sur deux points, et c'est délibéré :

  * `ansible-playbook` SANS `--check` est refusé net, pas seulement questionné.
    La règle du dépôt est « --check --diff d'abord » (RULES § 2) ; un garde qui
    se contente de demander finit par être approuvé par réflexe.
  * Toute commande qui ARME quelque chose (`SENTINEL_*_ENABLED=true`, activation
    d'un timer `sentinel-*`, suppression du témoin de désarmement) est refusée.
    Armer est un geste d'exploitation décrit par un runbook, joué par un humain
    — jamais une commande d'agent.

Un `ask` n'est pas un ordre PO. Il signale à l'humain qu'il est en train
d'autoriser quelque chose ; il ne le remplace pas.
"""

from __future__ import annotations

import json
import re
import sys


def _emit(permission: str, user: str = "", agent: str = "") -> None:
    payload: dict[str, str] = {"permission": permission}
    if user:
        payload["user_message"] = user
    if agent:
        payload["agent_message"] = agent
    json.dump(payload, sys.stdout)


def deny(user: str, agent: str) -> None:
    _emit("deny", user, agent)


def ask(user: str, agent: str) -> None:
    _emit("ask", user, agent)


def allow() -> None:
    _emit("allow")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        allow()
        return 0

    command = str(payload.get("command") or "")
    lowered = command.lower()

    # --- 1. Armement ---------------------------------------------------------
    # Le dispositif est désarmé par défaut (RULES § 1). Aucune commande d'agent
    # ne l'arme, même « pour tester ».
    if re.search(r"sentinel_[a-z_]*enabled\s*=\s*(true|1|yes|on)", lowered):
        deny(
            "Armement du dispositif bloqué : c'est un geste d'exploitation, pas une commande d'agent.",
            "Never arm the response/detection stack from a shell command. Arming is a documented ops gesture (see docs/runbooks/armement-de-la-reponse.md).",
        )
        return 0

    if re.search(r"\b(rm|del|remove-item)\b.*response-disarmed", lowered):
        deny(
            "Suppression du témoin de désarmement d'urgence bloquée.",
            "The disarm witness file is the out-of-band emergency brake. Only a human removes it.",
        )
        return 0

    if re.search(r"systemctl\s+(enable|start)\s+.*sentinel", lowered):
        deny(
            "Activation d'une unité sentinel-* bloquée : armer passe par un runbook.",
            "Do not enable or start sentinel-* units from a shell command; follow the arming runbook.",
        )
        return 0

    # --- 2. Ansible ----------------------------------------------------------
    if re.search(r"\bansible-playbook\b", lowered):
        if "--check" not in lowered:
            deny(
                "ansible-playbook sans --check refusé. RULES §2 : --check --diff d'abord, ordre PO ensuite, apply en dernier.",
                "Run the playbook with --check --diff first. An apply on patator-tower / patator-standby requires an explicit PO order given in the current session.",
            )
            return 0
        ask(
            "Playbook en --check sur une cible réelle — confirmer que c'est bien une répétition.",
            "Even in check mode this reaches a production node over the tailnet. Confirm intent.",
        )
        return 0

    # --- 3. Git --------------------------------------------------------------
    if re.search(r"\bgit\s+push\b", lowered):
        if re.search(r"\b(main|master)\b", lowered) or re.search(
            r"git\s+push\s+\S+\s+HEAD:.*(main|master)", command, re.I
        ):
            deny(
                "Push vers main/master bloqué par le hook projet 40KT1_SENTINEL.",
                "Do not push to main/master. Deliver via a cursor/<task> branch + PR.",
            )
            return 0
        ask(
            "Vérifie que tu n'es pas en train de pousser main/master.",
            "Confirm the branch is cursor/* (or a feature branch), never main.",
        )
        return 0

    # --- 4. Secrets ----------------------------------------------------------
    # `.env` porte la clé d'enrôlement : elle permet d'inscrire un faux agent.
    if re.search(r"(^|[^\w.-])\.env([^\w.-]|$)", command) and not re.search(
        r"\.env\.example", lowered
    ):
        if re.search(r"\b(rm|del|move|copy|cp|mv|set-content|out-file|tee)\b|>>|>", lowered):
            deny(
                "Modification d'un fichier .env bloquée (seul .env.example est éditable).",
                "Only .env.example may be edited. The .env holds the agent enrollment key.",
            )
            return 0

    if re.search(r"\bgh\s+secret\b", lowered):
        deny(
            "Manipulation des GitHub Secrets bloquée sans ordre PO.",
            "Do not change GitHub Secrets unless the PO explicitly ordered it.",
        )
        return 0

    allow()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
