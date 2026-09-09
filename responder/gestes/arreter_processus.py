"""Geste `arreter_processus` — `SIGTERM` à un processus, jamais à n'importe lequel.

Retour arrière au catalogue : *« il se relance, ou on le relance »*. C'est vrai
d'un processus applicatif ; c'est faux de `sshd`, de `tailscaled` ou de `init`.
La différence entre les deux est **toute** la valeur de ce module.

── Ce qui est refusé, et pourquoi ──────────────────────────────────────────
- **PID 1** : arrêter `init` arrête la machine. À 70 km.
- **Les processus de HQ** — `40kt1-*`, Docker, Postgres, Caddy, `cloudflared` :
  ils servent `hq.40kt1.com`. `RULES` § 2 : aucun geste automatique ne touche la
  donnée, la version servie, ou l'identité de la machine qui sert le nom public.
- **Le chemin d'administration** — `sshd`, `tailscaled` : les couper, c'est
  perdre le moyen de venir défaire le geste. Le geste cesserait d'être
  réversible sans arbitrage, ce qui le sortirait du catalogue.
- **Nos propres processus** : un exécuteur qui s'arrête lui-même laisse
  l'incident sans réponse et le journal sans fin.

`SIGTERM` et non `SIGKILL` : on demande, on ne casse pas. Un processus qui ignore
`SIGTERM` reste — et c'est un fait à voir dans le journal, pas à écraser.
"""

import os
import signal
from pathlib import Path

from responder.gestes.base import CibleRefusee, GesteEchoue

PROC = Path("/proc")

NOMS_PROTEGES: frozenset[str] = frozenset(
    {
        # Le chemin par lequel on reviendrait défaire le geste.
        "sshd",
        "tailscaled",
        "systemd",
        "init",
        "dbus-daemon",
        # 40KT1_HQ — la stack de production et ce qui la sert.
        "dockerd",
        "containerd",
        "containerd-shim",
        "containerd-shim-runc-v2",
        "postgres",
        "caddy",
        "cloudflared",
        # Nous-mêmes.
        "wazuh-modulesd",
        "wazuh-analysisd",
        "wazuh-remoted",
        "wazuh-execd",
        "wazuh-agentd",
    }
)

CGROUPS_PROTEGES: tuple[str, ...] = ("40kt1-", "docker/", "docker.service", "sentinel-")
"""Un processus dont le `cgroup` porte l'un de ces motifs appartient à HQ ou à nous."""


def _lire(pid: int, quoi: str) -> str | None:
    """Lit un fichier de `/proc/<pid>`. Rend `None` si on n'a pas pu — jamais `""`.

    La distinction compte : `""` se confondrait avec « ce processus n'a pas de
    nom », et on conclurait qu'il n'est pas protégé. Un `inconnu` n'est pas un
    `ok` (`RULES` § 1).
    """
    try:
        return (PROC / str(pid) / quoi).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def valider(brut: str) -> int:
    """Valide que la cible est un PID qu'on a le droit d'arrêter. Rend le PID."""
    if not brut.isdigit():
        raise CibleRefusee(
            f"« {brut} » n'est pas un PID. Le geste arreter_processus ne prend qu'un "
            "identifiant de processus — pas un nom, pas un motif."
        )
    pid = int(brut)

    if pid <= 1:
        raise CibleRefusee(
            f"PID {pid} refusé : arrêter init arrête la machine, et elle est à 70 km."
        )
    if pid == os.getpid() or pid == os.getppid():
        raise CibleRefusee(
            f"PID {pid} refusé : c'est l'exécuteur lui-même ou son parent. Un "
            "exécuteur qui s'arrête laisse l'incident sans réponse."
        )

    if not (PROC / str(pid)).exists():
        raise GesteEchoue(
            f"le processus {pid} n'existe plus. Rien n'a été fait. Ce n'est pas "
            "forcément un échec : il a pu se terminer entre la détection et l'ordre."
        )

    nom_brut = _lire(pid, "comm")
    if nom_brut is None:
        raise CibleRefusee(
            f"PID {pid} refusé : son nom n'a pas pu être lu. On n'arrête pas un "
            "processus qu'on n'a pas pu identifier — un `inconnu` n'est pas un `ok`."
        )
    nom = nom_brut.strip()
    if nom in NOMS_PROTEGES:
        raise CibleRefusee(
            f"PID {pid} (« {nom} ») refusé : ce processus appartient à 40KT1_HQ ou "
            "porte le chemin d'administration. L'arrêter toucherait la version "
            "servie, la donnée, ou le moyen de venir défaire le geste "
            "(RULES § 2, docs/contrat-hq.md). Le signaler, pas l'arrêter."
        )

    cgroup = _lire(pid, "cgroup")
    if cgroup is None:
        raise CibleRefusee(
            f"PID {pid} (« {nom} ») refusé : son cgroup n'a pas pu être lu, donc son "
            "appartenance est INCONNUE. On ne conclut pas « il n'est pas à HQ » "
            "faute d'avoir pu regarder."
        )
    for motif in CGROUPS_PROTEGES:
        if motif in cgroup:
            raise CibleRefusee(
                f"PID {pid} (« {nom} ») refusé : son cgroup porte « {motif} », donc il "
                "appartient à 40KT1_HQ ou à Sentinelle. Pour un conteneur, le geste "
                "du catalogue est arreter_conteneur — et il a ses propres refus."
            )

    return pid


def jouer(brut: str) -> str:
    """Envoie `SIGTERM` au processus et rend ce qu'il faut savoir pour revenir en arrière."""
    pid = valider(brut)
    nom = (_lire(pid, "comm") or "?").strip()
    ligne_brute = _lire(pid, "cmdline") or ""
    commande = ligne_brute.replace("\x00", " ").strip() or nom

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError as erreur:
        raise GesteEchoue(
            f"le processus {pid} a disparu avant le signal. Rien n'a été fait."
        ) from erreur
    except PermissionError as erreur:
        raise GesteEchoue(
            f"permission refusée sur le PID {pid} (« {nom} »). Le geste n'a PAS été "
            "joué — et c'est une information : l'exécuteur ne devrait pas manquer de "
            "droit sur un processus qu'il a le droit d'arrêter."
        ) from erreur

    # SIGTERM et pas SIGKILL : on ne vérifie donc pas que le processus est mort.
    # S'il ignore le signal, il reste — et c'est un fait qui doit se voir dans le
    # journal plutôt que d'être écrasé par un second signal plus brutal.
    return (
        f"SIGTERM envoyé à {pid} (« {nom} »). S'il est supervisé, il se relance seul. "
        f"Sinon, le relancer à la main : {commande[:200]}"
    )
