"""Geste `bloquer_ip` — blocage d'une adresse, **à expiration automatique**.

Le retour arrière est ce qui rend ce geste armable : l'adresse **sort toute
seule** au bout d'une heure. Personne n'a à se souvenir de la retirer, et une
règle oubliée ne s'accumule pas. C'est la définition d'`ADR-062` reprise mot pour
mot — *ce qu'un humain peut défaire sans arbitrage* — poussée un cran plus loin :
ici, il n'a même pas à le défaire.

── La frontière avec HQ ────────────────────────────────────────────────────
`ufw` appartient à HQ. Ce geste n'y touche **jamais** : il ajoute un élément à un
**ensemble nommé, dans une table `nftables` qui nous appartient**
(`docs/contrat-hq.md`). HQ ne vide pas cette table ; nous ne réordonnons pas ses
règles.

── Pourquoi le geste ne CRÉE pas la table ──────────────────────────────────
Il **refuse** si elle n'existe pas. Créer une structure de filtrage au vol, en
réponse à un incident, sur une machine qui sert `hq.40kt1.com`, serait poser de
l'infrastructure pare-feu dans le pire moment possible et sans revue. La table se
pose par un rôle Ansible, en `--check --diff`, avant tout armement. Absente, le
geste rend `échoué` — un état honnête — plutôt que d'improviser.
"""

import ipaddress
from dataclasses import dataclass

from responder.gestes.base import CibleRefusee, GesteEchoue, binaire, executer

TABLE = "sentinel"
"""Notre table `nftables`. Jamais `filter`, jamais une chaîne d'`ufw`."""

ENSEMBLE = "bloque"
"""Ensemble à `timeout` : c'est lui qui fait expirer l'adresse sans intervention."""

DUREE = "1h"
"""Durée du blocage. `ADR-002` : « expiration automatique à 1 h dans la chaîne dédiée »."""


@dataclass(frozen=True)
class Cible:
    """Une adresse validée, prête à devenir un argument."""

    adresse: str
    famille: str
    """`ip` ou `ip6` — l'ensemble `nftables` diffère."""


# ── Les plages qu'on refuse de bloquer, NOMMÉES une par une ────────────────
# Volontairement explicites plutôt que `adresse.is_private`. Deux raisons, et la
# seconde a mordu pendant l'écriture de ce module :
#
#   1. **`is_private` bouge d'une version de Python à l'autre.** La plage
#      `100.64.0.0/10` — celle du tailnet — n'y est pas classée de la même façon
#      selon les versions. Faire dépendre le chemin d'administration du parc de
#      ce détail serait le confier au hasard d'une mise à jour d'interpréteur.
#   2. **`is_private` couvre aussi les plages de documentation** (`203.0.113.0/24`
#      et voisines), qui n'ont aucune raison d'être protégées ici.
#
# Ce qui doit être protégé, c'est le CHEMIN DU RETOUR : le tailnet et le LAN
# d'administration. Les bloquer, c'est se couper le moyen de venir débloquer, et
# le geste cesserait d'être réversible « sans arbitrage » (`ADR-062`) — il
# exigerait 70 km de voiture, motif exact pour lequel `isoler_noeud` est classé
# « jamais » au catalogue.
PLAGES_PROTEGEES: tuple[tuple[str, str], ...] = (
    ("100.64.0.0/10", "plage du tailnet (CGNAT) — le chemin d'exploitation du parc"),
    ("10.0.0.0/8", "LAN privé"),
    ("172.16.0.0/12", "LAN privé"),
    ("192.168.0.0/16", "LAN d'administration — SSH de secours depuis 192.168.1.0/24"),
    ("169.254.0.0/16", "lien-local"),
    ("fd00::/8", "adresses locales uniques — tailnet IPv6"),
    ("fe80::/10", "lien-local IPv6"),
)

_RESEAUX_PROTEGES = tuple((ipaddress.ip_network(plage), motif) for plage, motif in PLAGES_PROTEGEES)


def valider(brut: str) -> Cible:
    """Valide que la cible est bien une **adresse**, et une adresse qu'on a le droit de bloquer."""
    try:
        adresse = ipaddress.ip_address(brut)
    except ValueError as erreur:
        raise CibleRefusee(
            f"« {brut} » n'est pas une adresse IP. Le geste bloquer_ip ne prend "
            "qu'une adresse — pas un nom d'hôte, pas un réseau, pas un chemin."
        ) from erreur

    if adresse.is_loopback:
        raise CibleRefusee(f"{adresse} est une adresse de bouclage : blocage sans objet.")
    if adresse.is_multicast or adresse.is_unspecified:
        raise CibleRefusee(f"{adresse} n'est pas une adresse d'hôte.")

    for reseau, motif in _RESEAUX_PROTEGES:
        if adresse.version == reseau.version and adresse in reseau:
            raise CibleRefusee(
                f"{adresse} est dans {reseau} — {motif}. La bloquer couperait le "
                "chemin par lequel on viendrait la débloquer : le geste cesserait "
                "d'être réversible sans arbitrage (ADR-062). Refusé."
            )

    return Cible(adresse=str(adresse), famille="ip6" if adresse.version == 6 else "ip")


def _ensemble(cible: Cible) -> str:
    return ENSEMBLE if cible.famille == "ip" else f"{ENSEMBLE}6"


def jouer(brut: str) -> str:
    """Bloque l'adresse et rend la commande exacte qui la débloque avant l'heure."""
    cible = valider(brut)
    nft = binaire("nft")
    ensemble = _ensemble(cible)

    # On vérifie que NOTRE structure existe. Absente, on refuse — on ne la crée
    # pas au milieu d'un incident (voir l'en-tête du module).
    vu = executer([nft, "list", "set", "inet", TABLE, ensemble])
    if vu.returncode != 0:
        raise GesteEchoue(
            f"l'ensemble « inet {TABLE} {ensemble} » n'existe pas sur ce nœud. Le "
            "blocage n'a PAS été posé. Cette structure se pose par un rôle Ansible, "
            "en --check --diff, avant tout armement — pas au vol pendant un "
            "incident, sur une machine qui sert hq.40kt1.com. "
            f"Détail : {vu.stderr.strip()}"
        )

    ajout = executer(
        [nft, "add", "element", "inet", TABLE, ensemble, "{", cible.adresse, "timeout", DUREE, "}"]
    )
    if ajout.returncode != 0:
        raise GesteEchoue(
            f"le blocage de {cible.adresse} a échoué : {ajout.stderr.strip()}. "
            "Rien n'a été posé."
        )

    # Le retour arrière, avec ses valeurs réelles. Il part au journal : c'est ce
    # que l'exploitant copie-colle, sans avoir à retrouver la syntaxe.
    return (
        f"expire seule dans {DUREE} · pour la retirer tout de suite : "
        f"nft delete element inet {TABLE} {ensemble} {{ {cible.adresse} }}"
    )
