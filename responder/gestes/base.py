"""Socle commun des gestes privilégiés — ce qui vaut pour les quatre.

Trois règles portent tout ce fichier, et elles viennent des menaces du parc :

1. **Jamais de shell.** Aucun geste ne construit une commande depuis une chaîne.
   `subprocess.run` reçoit une liste d'arguments, `shell=False`, toujours. Une
   cible arrive du réseau (`ordre.py`) : elle est un argument, pas du texte à
   interpoler.
2. **Jamais d'attente sans fin.** Toute commande porte un délai. Un `docker stop`
   qui pend bloquerait l'exécuteur, donc le désarmement d'urgence, donc le seul
   frein hors bande. Le frein ne dépend de rien.
3. **Le retour arrière est produit par le geste, pas par la documentation.**
   Chaque geste rend la **commande exacte** qui le défait, avec ses valeurs
   réelles, et cette commande part au journal. `ADR-062` de HQ demande qu'un
   humain puisse défaire sans arbitrage : lui laisser retrouver la commande à
   3 h du matin, c'est de l'arbitrage.
"""

import shutil
import subprocess
from pathlib import Path

DELAI_PAR_DEFAUT = 15
"""Secondes. Assez pour un `docker stop`, trop peu pour bloquer le frein d'urgence."""


class GesteEchoue(RuntimeError):
    """Le geste n'a pas abouti.

    Levée plutôt que rendue : l'exécuteur la rattrape et journalise `echoue`.
    Un geste qui échoue en silence serait exactement le faux vert que ce dépôt
    combat — pire ici, puisqu'on croirait la menace traitée.
    """


class CibleRefusee(GesteEchoue):
    """La cible n'est pas acceptable pour CE geste.

    `ordre.py` filtre déjà le jeu de caractères, mais il ne sait pas qu'une IP
    n'est pas un chemin. Chaque geste revalide donc **sa** cible localement :
    le serveur central corrèle et ordonne, le nœud **vérifie** et exécute
    (`ADR-002` § 3). Un serveur central compromis peut faire du bruit, pas
    n'importe quoi.
    """


def binaire(nom: str) -> str:
    """Rend le chemin absolu d'un exécutable, ou refuse.

    Chemin absolu résolu à l'appel plutôt que nom nu : le `PATH` d'un service
    systemd n'est pas celui d'un interpréteur, et un binaire introuvable doit
    dire « introuvable » plutôt que d'échouer sur un message obscur.
    """
    chemin = shutil.which(nom)
    if chemin is None:
        raise GesteEchoue(
            f"« {nom} » est introuvable sur ce nœud. Le geste n'a PAS été joué. "
            "Ce n'est pas un incident de sécurité : c'est un prérequis manquant."
        )
    return chemin


def executer(argv: list[str], *, delai: int = DELAI_PAR_DEFAUT) -> subprocess.CompletedProcess[str]:
    """Exécute une commande sans shell, avec délai. Rend le résultat sans lever.

    Ne lève pas sur un code de retour non nul : c'est à l'appelant de décider si
    ce code est un échec. Certains gestes sont idempotents et un second passage
    rend un code non nul sans que rien n'aille mal.
    """
    if not argv:
        raise GesteEchoue("commande vide")
    try:
        return subprocess.run(  # noqa: S603 — argv est une liste, shell=False, cible revalidée
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=delai,
            check=False,
        )
    except subprocess.TimeoutExpired as erreur:
        raise GesteEchoue(
            f"délai dépassé ({delai} s) sur « {argv[0]} ». Le geste est dans un état "
            "INCONNU : il a pu aboutir, échouer, ou rester à moitié fait. Vérifier à "
            "la main avant de rejouer."
        ) from erreur
    except OSError as erreur:
        raise GesteEchoue(f"« {argv[0]} » n'a pas pu être lancé : {erreur}") from erreur


def sous_un_de(chemin: Path, racines: tuple[str, ...]) -> str | None:
    """Rend la racine protégée qui contient `chemin`, ou `None`.

    Comparaison sur le chemin **résolu** : sans cela, `/tmp/../etc/passwd` passe
    à côté de la liste, et un lien symbolique aussi. La cible vient du réseau —
    on ne lui fait pas confiance pour être ce qu'elle paraît.
    """
    try:
        resolu = chemin.resolve()
    except OSError:
        # Non résoluble : on ne sait pas où il pointe, donc on le traite comme
        # protégé. Un `inconnu` n'est pas un `ok` (`RULES` § 1).
        return "(chemin non résoluble)"
    for racine in racines:
        # La RACINE est résolue elle aussi. Sans cela, `/lib` ne couvrirait pas
        # `/usr/lib` sur une machine où `/lib` est un lien — et la liste
        # protégerait un chemin qui n'existe pas plutôt que le vrai.
        try:
            base = Path(racine).resolve()
        except OSError:
            base = Path(racine)
        if resolu == base or base in resolu.parents:
            return racine
    return None
