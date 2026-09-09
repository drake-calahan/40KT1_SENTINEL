"""Le relais — testé surtout sur ce qu'il REFUSE de comprendre.

Le relais est la surface exposée au serveur central. Ce qu'on veut éprouver, ce
n'est pas qu'il transmette un ordre bien formé — c'est qu'il ne **fabrique** rien
quand l'enveloppe est incomplète, tordue, ou simplement d'une forme qu'il ne
connaît pas. Un ordre inventé serait un geste privilégié que personne n'a
demandé.
"""

import json
from typing import Any

import pytest

from responder.config import Config
from responder.relais import (
    CODE_ENVELOPPE_ILLISIBLE,
    CODE_OK,
    EnveloppeInvalide,
    extraire,
    traiter_flux,
)


def enveloppe(
    *,
    geste: str = "bloquer_ip",
    cible: str = "203.0.113.7",
    regle: str = "100201",
    commande: str = "add",
) -> dict[str, Any]:
    """Une enveloppe de la forme que le relais prétend comprendre."""
    return {
        "version": 1,
        "origin": {"name": "node", "module": "wazuh-execd"},
        "command": commande,
        "parameters": {
            "extra_args": [geste, cible],
            "alert": {"rule": {"id": regle, "level": 10}, "agent": {"name": "patator-tower"}},
            "program": "sentinel-relais",
        },
    }


# ══════════════════════════════════════════════════════════════════════════
# Ce qu'il extrait
# ══════════════════════════════════════════════════════════════════════════


def test_extrait_les_trois_champs_et_rien_d_autre() -> None:
    assert extraire(enveloppe()) == {
        "geste": "bloquer_ip",
        "cible": "203.0.113.7",
        "regle": "100201",
    }


# ══════════════════════════════════════════════════════════════════════════
# Ce qu'il refuse — un champ absent n'est jamais une occasion de deviner
# ══════════════════════════════════════════════════════════════════════════


def test_refuse_une_enveloppe_qui_n_est_pas_un_objet() -> None:
    with pytest.raises(EnveloppeInvalide):
        extraire(["bloquer_ip", "203.0.113.7"])  # type: ignore[arg-type]


def test_refuse_sans_parametres() -> None:
    brut = enveloppe()
    del brut["parameters"]
    with pytest.raises(EnveloppeInvalide, match="parameters"):
        extraire(brut)


def test_refuse_sans_alerte() -> None:
    brut = enveloppe()
    del brut["parameters"]["alert"]
    with pytest.raises(EnveloppeInvalide, match="alert"):
        extraire(brut)


def test_refuse_sans_identifiant_de_regle() -> None:
    """Sans la règle, le journal ne dit pas CE QUI a déclenché le geste.

    Le repassage hebdomadaire de `D5` se fait sur ce champ : une entrée qui ne
    le porte pas est une ligne qu'on ne peut pas classer, donc une `indeterminee`
    de plus — et une `indeterminee` non reclassée fait tomber la semaine.
    """
    brut = enveloppe()
    brut["parameters"]["alert"]["rule"] = {"level": 10}
    with pytest.raises(EnveloppeInvalide, match="règle"):
        extraire(brut)


@pytest.mark.parametrize("arguments", [[], ["bloquer_ip"], "bloquer_ip 203.0.113.7", None])
def test_refuse_quand_le_geste_n_est_pas_ORDONNE(arguments: object) -> None:
    """Le relais ne déduit JAMAIS le geste de la règle.

    Déduire, ce serait décider — et décider est le travail du catalogue, pas
    celui du fichier le moins relu du dépôt.
    """
    brut = enveloppe()
    brut["parameters"]["extra_args"] = arguments
    with pytest.raises(EnveloppeInvalide, match="extra_args"):
        extraire(brut)


def test_refuse_l_annulation_par_le_moteur() -> None:
    """Nos gestes portent leur propre retour arrière, tracé au journal.

    Laisser le moteur « annuler » créerait un second chemin de défaisance,
    invisible de notre journal — et le journal est ce sur quoi le mode à blanc
    se juge.
    """
    with pytest.raises(EnveloppeInvalide, match="retour arrière"):
        extraire(enveloppe(commande="delete"))


@pytest.mark.parametrize("valeur", ["", "   ", 42, None, ["x"]])
def test_refuse_un_geste_qui_n_est_pas_une_chaine_utile(valeur: object) -> None:
    brut = enveloppe()
    brut["parameters"]["extra_args"] = [valeur, "203.0.113.7"]
    with pytest.raises(EnveloppeInvalide):
        extraire(brut)


# ══════════════════════════════════════════════════════════════════════════
# Le flux complet — et le fait qu'un refus n'est pas une panne de transport
# ══════════════════════════════════════════════════════════════════════════


def test_une_enveloppe_illisible_ne_transmet_rien(config: Config) -> None:
    code, message = traiter_flux("{ceci n'est pas du json", config)
    assert code == CODE_ENVELOPPE_ILLISIBLE
    assert "Rien n'a été transmis" in message
    assert not config.journal.exists()


def test_une_enveloppe_refusee_ne_transmet_rien(config: Config) -> None:
    """Refuser à la lecture, c'est ne rien écrire au journal de l'exécuteur.

    Voulu : le journal de l'exécuteur porte les décisions SUR DES ORDRES. Une
    enveloppe qu'on n'a pas su lire n'est pas un ordre — la consigner comme un
    refus de l'exécuteur brouillerait le compte du budget.
    """
    brut = enveloppe()
    del brut["parameters"]["alert"]
    code, message = traiter_flux(json.dumps(brut), config)
    assert code == CODE_ENVELOPPE_ILLISIBLE
    assert "Rien n'a été transmis" in message
    assert not config.journal.exists()


def test_un_refus_de_l_executeur_n_est_pas_une_panne_du_relais(config: Config) -> None:
    """Un geste hors catalogue est refusé par l'exécuteur — et le relais rend `0`.

    Faire remonter un refus comme une erreur de transport apprendrait au moteur à
    traiter les refus comme des incidents, et on finirait par les regarder moins.
    """
    code, message = traiter_flux(json.dumps(enveloppe(geste="formater_le_disque")), config)
    assert code == CODE_OK
    assert message.startswith("refuse")
    # Le refus, lui, EST journalisé : c'est un ordre, et tout ordre laisse une trace.
    assert config.journal.exists()
    assert "formater_le_disque" in config.journal.read_text(encoding="utf-8")


def test_le_relais_ne_contourne_aucune_garde(config: Config) -> None:
    """Le témoin de désarmement posé, le relais ne joue rien — il ne le sait même pas.

    C'est la propriété qui compte : le relais n'a aucune connaissance des gardes,
    donc il ne peut ni les doubler ni les contourner.
    """
    config.fichier_desarmement.write_text("frein tiré\n", encoding="utf-8")
    code, message = traiter_flux(json.dumps(enveloppe()), config)
    assert code == CODE_OK
    assert message.startswith("refuse")
    assert "désarmement" in message
