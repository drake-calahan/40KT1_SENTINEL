"""Geste `arreter_conteneur` — `docker stop`, mais pas sur n'importe quel conteneur.

Retour arrière au catalogue : *« `docker start` — une commande »*. Vrai. Ce qui
n'est pas dit, et que ce module tranche : **certains conteneurs ne sont pas
arrêtables sans sortir du catalogue.**

── Le point qui a motivé ce module ─────────────────────────────────────────
Arrêter le conteneur `cloudflared`, **c'est** `couper_connecteur`. Or
`couper_connecteur` est classé **alerte** en nominal et **jamais** en tournoi
(`ADR-002`). Si `arreter_conteneur` acceptait `cloudflared`, un geste *alerte
seulement* deviendrait exécutable en passant par un autre nom — et le catalogue
fermé cesserait d'être fermé.

Le même raisonnement vaut pour :

- **`db`** — arrêter la base *touche la donnée* (`RULES` § 2), et une coupure en
  écriture n'est pas « une commande » à défaire ;
- **`caddy`** — il sert le nom public : l'arrêter, c'est changer l'identité de la
  machine qui répond, ce que `RULES` § 2 interdit explicitement ;
- **`api`** — c'est la version servie.

Restreindre ainsi ne demande **aucun amendement d'ADR** : `RULES` § 2 n'autorise
l'élargissement que par amendement. Rétrécir est toujours permis. Mais la liste
elle-même mérite d'être confirmée par le PO — c'est la tâche `P03.7`.
"""

from responder.gestes.base import CibleRefusee, GesteEchoue, binaire, executer

DELAI_ARRET = 10
"""Secondes laissées au conteneur pour s'arrêter proprement avant que Docker n'insiste."""

CONTENEURS_PROTEGES: frozenset[str] = frozenset(
    {
        # L'arrêter EST `couper_connecteur`, classé alerte / jamais au catalogue.
        "cloudflared",
        # Touche la donnée (RULES § 2).
        "db",
        "postgres",
        "40kt1-db",
        # Sert le nom public : identité de la machine qui répond (RULES § 2).
        "caddy",
        "40kt1-caddy",
        # La version servie.
        "api",
        "40kt1-api",
    }
)

PREFIXES_PROTEGES: tuple[str, ...] = ("40kt1-caddy", "40kt1-db", "40kt1-api")


def valider(brut: str) -> str:
    """Valide que la cible est un conteneur qu'on a le droit d'arrêter."""
    nom = brut.strip()
    if not nom:
        raise CibleRefusee("nom de conteneur vide.")

    # La comparaison se fait sur le nom en minuscules, sans le `/` que Docker
    # ajoute parfois en tête. Un refus qu'on contourne par une majuscule ne
    # protège de rien.
    normalise = nom.lstrip("/").lower()

    if normalise in CONTENEURS_PROTEGES or normalise.startswith(PREFIXES_PROTEGES):
        raise CibleRefusee(
            f"conteneur « {nom} » refusé : il sert la production de 40KT1_HQ. "
            "L'arrêter toucherait la donnée, la version servie ou l'identité de la "
            "machine qui sert le nom public (RULES § 2) — et pour cloudflared, ce "
            "serait jouer couper_connecteur, qui est ALERTE SEULEMENT au catalogue "
            "(ADR-002). Le catalogue ne se contourne pas en changeant de nom de "
            "geste. Alerter, et laisser un humain décider."
        )
    return normalise


def jouer(brut: str) -> str:
    """Arrête le conteneur et rend la commande exacte qui le relance."""
    nom = valider(brut)
    docker = binaire("docker")

    # On relève l'image AVANT d'arrêter : après, `docker inspect` marche encore,
    # mais si le conteneur est supprimé entre-temps on perd le moyen de dire à
    # l'exploitant ce qu'il relance. Le retour arrière doit être écrit au moment
    # où l'information est sûre.
    vu = executer([docker, "inspect", "--format", "{{.Config.Image}}", nom])
    if vu.returncode != 0:
        raise GesteEchoue(
            f"le conteneur « {nom} » est introuvable. Rien n'a été arrêté. "
            f"Détail : {vu.stderr.strip()}"
        )
    image = vu.stdout.strip() or "(image inconnue)"

    arret = executer(
        [docker, "stop", "--time", str(DELAI_ARRET), nom],
        # Le délai de la commande doit dépasser celui laissé au conteneur, sinon
        # on abandonne l'attente juste avant que Docker ne finisse le travail —
        # et on rendrait « inconnu » un arrêt qui allait aboutir.
        delai=DELAI_ARRET + 10,
    )
    if arret.returncode != 0:
        raise GesteEchoue(
            f"l'arrêt du conteneur « {nom} » a échoué : {arret.stderr.strip()}. "
            "Son état est à vérifier à la main."
        )

    return f"docker start {nom}  (image : {image})"
