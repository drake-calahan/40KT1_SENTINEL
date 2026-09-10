"""Tests de la sonde d'inspection Docker — dégradation d'abord."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence

from scripts.inspection_docker import (
    Etat,
    evaluer_conteneur,
    formater,
    inspecter_parc,
)


def _proc(stdout: str = "", stderr: str = "", code: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["docker"], returncode=code, stdout=stdout, stderr=stderr
    )


def test_docker_absent_rend_unknown(monkeypatch) -> None:
    monkeypatch.setattr("scripts.inspection_docker._docker_bin", lambda: None)
    etat, constats = inspecter_parc(runner=lambda _: _proc())
    assert etat is Etat.UNKNOWN
    assert constats[0].etat is Etat.UNKNOWN
    assert "introuvable" in constats[0].message


def test_docker_ps_echoue_rend_unknown(monkeypatch) -> None:
    monkeypatch.setattr("scripts.inspection_docker._docker_bin", lambda: "/usr/bin/docker")

    def runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        assert argv[1:] == ["ps", "-q"]
        return _proc(stderr="Cannot connect", code=1)

    etat, constats = inspecter_parc(runner=runner)
    assert etat is Etat.UNKNOWN
    assert "docker ps" in constats[0].message


def test_docker_inspect_echoue_rend_unknown(monkeypatch) -> None:
    monkeypatch.setattr("scripts.inspection_docker._docker_bin", lambda: "/usr/bin/docker")

    def runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if argv[1] == "ps":
            return _proc(stdout="abc123\n")
        return _proc(stderr="permission denied", code=1)

    etat, constats = inspecter_parc(runner=runner)
    assert etat is Etat.UNKNOWN
    assert "docker inspect" in constats[0].message


def test_inspect_json_invalide_rend_unknown(monkeypatch) -> None:
    monkeypatch.setattr("scripts.inspection_docker._docker_bin", lambda: "/usr/bin/docker")

    def runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if argv[1] == "ps":
            return _proc(stdout="abc123\n")
        return _proc(stdout="pas-du-json")

    etat, constats = inspecter_parc(runner=runner)
    assert etat is Etat.UNKNOWN
    assert "illisible" in constats[0].message


def test_aucun_conteneur_rend_ok(monkeypatch) -> None:
    monkeypatch.setattr("scripts.inspection_docker._docker_bin", lambda: "/usr/bin/docker")

    def runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        assert argv[1:] == ["ps", "-q"]
        return _proc(stdout="")

    etat, constats = inspecter_parc(runner=runner)
    assert etat is Etat.OK
    assert constats == []


def test_privileged_rend_ko() -> None:
    fautes = evaluer_conteneur(
        {"Name": "/evil", "HostConfig": {"Privileged": True}, "Mounts": [], "NetworkSettings": {}}
    )
    assert any(f.etat is Etat.KO and "Privileged" in f.message for f in fautes)


def test_socket_var_run_monte_rend_ko() -> None:
    fautes = evaluer_conteneur(
        {
            "Name": "/sock",
            "HostConfig": {
                "Privileged": False,
                "Binds": ["/var/run/docker.sock:/var/run/docker.sock"],
            },
            "Mounts": [],
            "NetworkSettings": {"Ports": {}},
        }
    )
    assert any("docker.sock" in f.message for f in fautes)


def test_socket_run_monte_rend_ko() -> None:
    # Ubuntu : /var/run → /run ; Docker résout souvent Source=/run/docker.sock.
    fautes = evaluer_conteneur(
        {
            "Name": "/sock-run",
            "HostConfig": {"Privileged": False, "Binds": []},
            "Mounts": [{"Source": "/run/docker.sock", "Destination": "/var/run/docker.sock"}],
            "NetworkSettings": {"Ports": {}},
        }
    )
    assert any("docker.sock" in f.message for f in fautes)


def test_port_0_0_0_0_rend_ko() -> None:
    toutes = "0.0.0.0"  # noqa: S104 — détecter cette adresse EST le but du test
    fautes = evaluer_conteneur(
        {
            "Name": "/web",
            "HostConfig": {"Privileged": False},
            "Mounts": [],
            "NetworkSettings": {"Ports": {"80/tcp": [{"HostIp": toutes, "HostPort": "8080"}]}},
        }
    )
    assert any(toutes in f.message for f in fautes)


def test_port_ipv6_toutes_interfaces_rend_ko() -> None:
    fautes = evaluer_conteneur(
        {
            "Name": "/web6",
            "HostConfig": {},
            "NetworkSettings": {"Ports": {"80/tcp": [{"HostIp": "::", "HostPort": "8080"}]}},
        }
    )
    assert any("::" in f.message for f in fautes)


def test_port_hostip_vide_compte_comme_toutes_interfaces() -> None:
    # Docker omet souvent HostIp pour « toutes les interfaces ».
    fautes = evaluer_conteneur(
        {
            "Name": "/web",
            "HostConfig": {},
            "NetworkSettings": {"Ports": {"443/tcp": [{"HostIp": "", "HostPort": "443"}]}},
        }
    )
    toutes = "0.0.0.0"  # noqa: S104 — détecter cette adresse EST le but du test
    assert any(toutes in f.message for f in fautes)


def test_conteneur_sain_sans_faute() -> None:
    fautes = evaluer_conteneur(
        {
            "Name": "/ok",
            "HostConfig": {"Privileged": False, "Binds": ["/data:/data"]},
            "Mounts": [{"Source": "/data", "Destination": "/data"}],
            "NetworkSettings": {"Ports": {"80/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8080"}]}},
        }
    )
    assert fautes == []


def test_parc_ko_agrege(monkeypatch) -> None:
    monkeypatch.setattr("scripts.inspection_docker._docker_bin", lambda: "/usr/bin/docker")
    payload = [
        {
            "Name": "/bad",
            "HostConfig": {"Privileged": True},
            "Mounts": [],
            "NetworkSettings": {"Ports": {}},
        }
    ]

    def runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if argv[1] == "ps":
            return _proc(stdout="deadbeef\n")
        return _proc(stdout=json.dumps(payload))

    etat, constats = inspecter_parc(runner=runner)
    assert etat is Etat.KO
    assert constats
    texte = formater(etat, constats)
    assert "etat=ko" in texte
    assert "Privileged" in texte


def test_ko_conserve_malgre_element_malforme(monkeypatch) -> None:
    """Un ko établi ne disparaît pas derrière un élément inspect non-objet."""
    monkeypatch.setattr("scripts.inspection_docker._docker_bin", lambda: "/usr/bin/docker")
    payload = [
        {
            "Name": "/bad",
            "HostConfig": {"Privileged": True},
            "Mounts": [],
            "NetworkSettings": {"Ports": {}},
        },
        "pas-un-objet",
    ]

    def runner(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
        if argv[1] == "ps":
            return _proc(stdout="a\nb\n")
        return _proc(stdout=json.dumps(payload))

    etat, constats = inspecter_parc(runner=runner)
    assert etat is Etat.KO
    assert any("Privileged" in c.message for c in constats)
    assert any("non mesuré" in c.message for c in constats)
