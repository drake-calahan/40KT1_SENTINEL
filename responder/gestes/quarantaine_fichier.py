"""Geste `quarantaine_fichier` — déplacement vers un coffre, empreinte conservée.

Retour arrière au catalogue : *« déplacement inverse, empreinte conservée »*.
Ce module le rend littéral : il écrit à côté du fichier mis de côté un
**manifeste** qui porte le chemin d'origine, le mode, le propriétaire et
l'empreinte `SHA-256` — de quoi remettre le fichier **exactement** où il était,
tel qu'il était, sans que personne ait à s'en souvenir.

L'empreinte sert deux fois : elle prouve que le fichier remis est bien celui qui
a été retiré, et elle reste la seule trace utile si le fichier doit être détruit.

── Ce qui est refusé, et pourquoi ──────────────────────────────────────────
**L'arborescence de HQ** (`/srv/40kt1`, `~/40KT1_HQ`) : le contrat de frontière
dit que Sentinelle la **surveille en lecture** et **n'y écrit pas**. Or déplacer
un fichier hors d'un répertoire, c'est y écrire.

C'est une vraie limite, et elle est gênante : un fichier déposé par un attaquant
dans la stack est exactement ce qu'on voudrait mettre de côté. Le geste alerte
donc au lieu d'agir, et la question est posée au PO — voir `P03.8`. Elle ne se
tranche pas ici : élargir le périmètre d'écriture de Sentinelle chez HQ est un
amendement du contrat, **des deux côtés**.

**Les répertoires du système** (`/etc`, `/usr`, `/bin`, `/boot`, …) : mettre en
quarantaine `/etc/passwd` ou `/etc/shadow` casse la machine plus sûrement que
l'attaque. Le retour arrière serait alors « démarrer sur une clé USB », ce qui
n'est pas défaire *sans arbitrage*.

**Nos propres répertoires** : retirer notre journal ou notre témoin de
désarmement reviendrait à saboter le frein d'urgence.
"""

import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from responder.gestes.base import CibleRefusee, GesteEchoue, sous_un_de

RACINES_SYSTEME: tuple[str, ...] = (
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/lib",
    "/lib64",
    "/boot",
    "/proc",
    "/sys",
    "/dev",
    "/var/ossec",
)
"""Retirer un fichier d'ici casse la machine plus sûrement que l'attaque."""

TAILLE_MAX = 512 * 1024 * 1024
"""512 Mio. Au-delà, on n'a probablement pas la place, et le coffre remplirait le disque."""


def _quarantaine(racine_etat: Path) -> Path:
    return racine_etat / "quarantaine"


def valider(brut: str, *, racine_etat: Path, racines_hq: tuple[str, ...]) -> Path:
    """Valide que le chemin est un fichier qu'on a le droit de mettre de côté."""
    chemin = Path(brut)
    if not chemin.is_absolute():
        raise CibleRefusee(
            f"« {brut} » n'est pas un chemin absolu. On ne met pas en quarantaine "
            "un chemin dont l'interprétation dépend du répertoire courant."
        )

    protege = sous_un_de(chemin, RACINES_SYSTEME)
    if protege is not None:
        raise CibleRefusee(
            f"« {brut} » est sous « {protege} » : répertoire du système. Le retirer "
            "casserait la machine plus sûrement que l'attaque, et le défaire "
            "demanderait de démarrer sur une clé — ce n'est pas « sans arbitrage » "
            "(ADR-062). Alerter, et laisser un humain décider."
        )

    chez_hq = sous_un_de(chemin, racines_hq)
    if chez_hq is not None:
        raise CibleRefusee(
            f"« {brut} » est sous « {chez_hq} », l'arborescence de 40KT1_HQ. Le "
            "contrat de frontière dit que Sentinelle la surveille en LECTURE et n'y "
            "écrit pas — or déplacer un fichier hors d'un répertoire, c'est y écrire "
            "(docs/contrat-hq.md). Alerte, pas geste. Cette limite est réelle et "
            "gênante : elle est posée au PO en P03.8."
        )

    sous_nous = sous_un_de(chemin, (str(racine_etat),))
    if sous_nous is not None:
        raise CibleRefusee(
            f"« {brut} » appartient à Sentinelle. Retirer notre journal ou notre "
            "témoin de désarmement reviendrait à saboter le frein d'urgence."
        )

    if chemin.is_symlink():
        raise CibleRefusee(
            f"« {brut} » est un lien symbolique. Le déplacer ne met rien de côté : "
            "la cible reste en place, et on croirait la menace traitée."
        )
    if not chemin.is_file():
        raise GesteEchoue(
            f"« {brut} » n'est pas un fichier ordinaire, ou n'existe plus. Rien n'a été fait."
        )
    return chemin


def _empreinte(chemin: Path) -> str:
    """Empreinte SHA-256, lue par blocs — un fichier de 500 Mio ne tient pas en mémoire."""
    somme = hashlib.sha256()
    with chemin.open("rb") as flux:
        for bloc in iter(lambda: flux.read(1024 * 1024), b""):
            somme.update(bloc)
    return somme.hexdigest()


def jouer(brut: str, *, racine_etat: Path, racines_hq: tuple[str, ...]) -> str:
    """Met le fichier de côté et rend la commande exacte qui le remet en place."""
    chemin = valider(brut, racine_etat=racine_etat, racines_hq=racines_hq)

    try:
        infos = chemin.stat()
    except OSError as erreur:
        raise GesteEchoue(f"« {chemin} » n'a pas pu être lu : {erreur}") from erreur
    if infos.st_size > TAILLE_MAX:
        raise GesteEchoue(
            f"« {chemin} » fait {infos.st_size} octets, au-delà du plafond "
            f"({TAILLE_MAX}). Non déplacé : remplir le disque du nœud pendant un "
            "incident aggraverait l'incident."
        )

    # L'empreinte est prise AVANT le déplacement. Après, on ne pourrait plus
    # prouver que ce qu'on a mis de côté est bien ce qui a été détecté.
    empreinte = _empreinte(chemin)

    coffre = _quarantaine(racine_etat)
    try:
        coffre.mkdir(parents=True, exist_ok=True)
        # 0700 : le coffre contient ce qu'un attaquant a déposé. Personne d'autre
        # que root n'a de raison de le lire, et surtout pas de l'exécuter.
        coffre.chmod(0o700)
    except OSError as erreur:
        raise GesteEchoue(f"le coffre de quarantaine est inutilisable : {erreur}") from erreur

    horodatage = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = coffre / f"{horodatage}-{empreinte[:12]}-{chemin.name}"

    manifeste = {
        "origine": str(chemin),
        "horodatage": datetime.now(UTC).isoformat(),
        "sha256": empreinte,
        "taille": infos.st_size,
        "mode": oct(infos.st_mode & 0o7777),
        "uid": infos.st_uid,
        "gid": infos.st_gid,
        "mtime": infos.st_mtime,
    }

    try:
        # `move` et non `copy` + `unlink` : le fichier ne doit pas exister aux
        # deux endroits, même une seconde. On croirait la menace traitée alors
        # qu'elle est encore là.
        shutil.move(str(chemin), str(destination))
        destination.chmod(0o600)
        (coffre / f"{destination.name}.json").write_text(
            json.dumps(manifeste, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except OSError as erreur:
        raise GesteEchoue(
            f"la mise en quarantaine de « {chemin} » a échoué : {erreur}. Vérifier à "
            "la main où se trouve le fichier — il peut être à l'un des deux endroits."
        ) from erreur

    # Le retour arrière, avec ses valeurs réelles, prêt à copier-coller.
    return (
        f"empreinte {empreinte[:16]}… conservée · remise en place : "
        f"mv {destination} {chemin} "
        f"&& chmod {oct(infos.st_mode & 0o7777)[2:]} {chemin} "
        f"&& chown {infos.st_uid}:{infos.st_gid} {chemin} "
        f"· manifeste : {coffre / (destination.name + '.json')}"
    )


def racines_hq_par_defaut() -> tuple[str, ...]:
    """Arborescences de HQ, lues dans l'environnement du nœud — les deux chemins diffèrent.

    `/srv/40kt1` sur la tour, `/home/calahan/40KT1_HQ` sur le standby. Présumer
    l'un des deux ferait marcher le refus sur un nœud et pas sur l'autre.
    """
    declare = os.environ.get("SENTINEL_HQ_STACK_DIR", "").strip()
    racines = ["/srv/40kt1"]
    if declare:
        racines.append(declare)
    return tuple(racines)
