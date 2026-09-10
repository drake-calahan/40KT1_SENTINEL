"""Sonde d'inspection Docker — lecture seule (TASKS#P01.17).

`docker events` ne porte ni `privileged`, ni montages, ni ports publiés
(DISCOVERY § réseau). Cette sonde interroge `docker inspect` et rend trois
états : `ok`, `ko`, `unknown`. Jamais `ok` faute d'avoir mesuré.

Périmètre mesuré : **l'exposition courante** (`docker ps -q` — conteneurs
en cours d'exécution seulement). Un conteneur arrêté qui fut `--privileged`
n'apparaît plus : on ne veut pas un `ko` collant jusqu'à `docker rm`. Les
définitions présentes sur disque (`-aq`) sont hors périmètre de cette sonde.

Parc vide → `ok` (on a mesuré). Sur `patator-tower`, cinq conteneurs sont
attendus ; zéro conteneur veut dire que la stack est à terre — c'est le
`watchdog.py` de HQ qui le voit (`RULES` § 8), pas cette sonde.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any

# Les deux formes courantes : `/var/run` → `/run` sur Ubuntu.
SOCKETS_DOCKER = frozenset({"/var/run/docker.sock", "/run/docker.sock"})
# Adresses « toutes les interfaces » — la détecter EST le but de la sonde (S104).
TOUTES_INTERFACES = frozenset(
    {
        "0.0.0.0",  # noqa: S104
        "::",
        "[::]",
    }
)
DELAI_S = 30


class Etat(str, Enum):
    OK = "ok"
    KO = "ko"
    UNKNOWN = "unknown"


CODES_RETOUR = {Etat.OK: 0, Etat.KO: 1, Etat.UNKNOWN: 2}


@dataclass(frozen=True)
class Constat:
    """Un conteneur fautif, ou une raison de ne pas avoir mesuré."""

    etat: Etat
    message: str


Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _runner_defaut(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 — argv figé, pas de shell
        list(argv),
        capture_output=True,
        text=True,
        timeout=DELAI_S,
        check=False,
    )


def _docker_bin() -> str | None:
    return shutil.which("docker")


def _chemin_est_socket_docker(chemin: str) -> bool:
    """Vrai si le chemin (hôte) désigne le socket Docker, sous /var/run ou /run."""
    if not chemin:
        return False
    if chemin in SOCKETS_DOCKER:
        return True
    # Compare sur le nom de fichier pour les variantes absentes de la liste.
    return PurePosixPath(chemin).name == "docker.sock" and (
        chemin.endswith("/docker.sock") or chemin == "docker.sock"
    )


def lister_ids(runner: Runner, docker: str) -> Constat | list[str]:
    """Rend les IDs des conteneurs **en cours**, ou un Constat unknown.

    `docker ps -q` (pas `-aq`) : exposition courante uniquement.
    """
    try:
        proc = runner([docker, "ps", "-q"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Constat(Etat.UNKNOWN, f"impossible d'exécuter docker ps : {exc}")
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or f"code={proc.returncode}"
        return Constat(Etat.UNKNOWN, f"docker ps a échoué : {err}")
    ids = [ligne.strip() for ligne in proc.stdout.splitlines() if ligne.strip()]
    return ids


def inspecter(runner: Runner, docker: str, ids: list[str]) -> Constat | list[dict[str, Any]]:
    if not ids:
        return []
    try:
        proc = runner([docker, "inspect", *ids])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return Constat(Etat.UNKNOWN, f"impossible d'exécuter docker inspect : {exc}")
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip() or f"code={proc.returncode}"
        return Constat(Etat.UNKNOWN, f"docker inspect a échoué : {err}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return Constat(Etat.UNKNOWN, f"sortie inspect illisible : {exc}")
    if not isinstance(data, list):
        return Constat(Etat.UNKNOWN, "sortie inspect : attendait une liste JSON")
    return data


def _nom(conteneur: dict[str, Any]) -> str:
    name = conteneur.get("Name")
    if isinstance(name, str) and name.strip():
        return name.lstrip("/")
    cid = conteneur.get("Id")
    if isinstance(cid, str) and cid:
        return cid[:12]
    return "?"


def _privileged(conteneur: dict[str, Any]) -> bool:
    host = conteneur.get("HostConfig")
    if not isinstance(host, dict):
        return False
    return bool(host.get("Privileged"))


def _socket_monte(conteneur: dict[str, Any]) -> bool:
    host = conteneur.get("HostConfig")
    if isinstance(host, dict):
        binds = host.get("Binds") or []
        if isinstance(binds, list):
            for bind in binds:
                if not isinstance(bind, str):
                    continue
                source = bind.split(":")[0]
                if _chemin_est_socket_docker(source):
                    return True
    mounts = conteneur.get("Mounts") or []
    if isinstance(mounts, list):
        for mount in mounts:
            if not isinstance(mount, dict):
                continue
            source = str(mount.get("Source") or "")
            if _chemin_est_socket_docker(source):
                return True
    return False


def _port_sur_tout_le_monde(conteneur: dict[str, Any]) -> list[str]:
    """Ports publiés sur toutes les interfaces (IPv4 `0.0.0.0` ou IPv6 `::`)."""
    network = conteneur.get("NetworkSettings")
    if not isinstance(network, dict):
        return []
    ports = network.get("Ports") or {}
    if not isinstance(ports, dict):
        return []
    trouves: list[str] = []
    for cle, bindings in ports.items():
        if not bindings:
            continue
        if not isinstance(bindings, list):
            continue
        for binding in bindings:
            if not isinstance(binding, dict):
                continue
            host_ip = str(binding.get("HostIp") or "")
            host_port = str(binding.get("HostPort") or "")
            # Docker omet souvent HostIp pour « toutes les interfaces » (IPv4).
            if host_ip == "" or host_ip in TOUTES_INTERFACES:
                affiche = host_ip or "0.0.0.0"  # noqa: S104
                trouves.append(f"{cle}→{affiche}:{host_port}")
    return trouves


def evaluer_conteneur(conteneur: dict[str, Any]) -> list[Constat]:
    nom = _nom(conteneur)
    fautes: list[Constat] = []
    if _privileged(conteneur):
        fautes.append(Constat(Etat.KO, f"{nom} : Privileged=true"))
    if _socket_monte(conteneur):
        fautes.append(Constat(Etat.KO, f"{nom} : montage de docker.sock"))
    for pub in _port_sur_tout_le_monde(conteneur):
        fautes.append(Constat(Etat.KO, f"{nom} : port publié sur toutes interfaces ({pub})"))
    return fautes


def inspecter_parc(runner: Runner | None = None) -> tuple[Etat, list[Constat]]:
    """Parcourt les conteneurs en cours et agrège l'état du parc."""
    run = runner or _runner_defaut
    docker = _docker_bin()
    if docker is None:
        return Etat.UNKNOWN, [Constat(Etat.UNKNOWN, "binaire docker introuvable dans PATH")]

    ids_ou = lister_ids(run, docker)
    if isinstance(ids_ou, Constat):
        return Etat.UNKNOWN, [ids_ou]
    if not ids_ou:
        # Aucun conteneur en cours : on a mesuré → ok (stack down = HQ watchdog).
        return Etat.OK, []

    data_ou = inspecter(run, docker, ids_ou)
    if isinstance(data_ou, Constat):
        return Etat.UNKNOWN, [data_ou]

    fautes: list[Constat] = []
    non_mesures = 0
    for conteneur in data_ou:
        if not isinstance(conteneur, dict):
            # Garder les ko déjà collectés ; ne pas jeter un fait pour un
            # élément malformé plus loin dans la liste.
            non_mesures += 1
            continue
        fautes.extend(evaluer_conteneur(conteneur))

    if non_mesures:
        fautes.append(
            Constat(
                Etat.UNKNOWN,
                f"{non_mesures} conteneur(s) non mesuré(s) (élément inspect non-objet)",
            )
        )

    if any(c.etat is Etat.KO for c in fautes):
        return Etat.KO, fautes
    if fautes:
        return Etat.UNKNOWN, fautes
    return Etat.OK, []


def formater(etat: Etat, constats: list[Constat]) -> str:
    lignes = [f"etat={etat.value}"]
    if not constats and etat is Etat.OK:
        lignes.append("aucun conteneur en cours privileged / docker.sock / port toutes interfaces")
    for c in constats:
        lignes.append(c.message)
    return "\n".join(lignes) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspection Docker en lecture seule "
            "(privileged, socket, ports toutes interfaces — conteneurs en cours)."
        )
    )
    parser.parse_args(argv)
    etat, constats = inspecter_parc()
    sys.stdout.write(formater(etat, constats))
    return CODES_RETOUR[etat]


if __name__ == "__main__":
    raise SystemExit(main())
