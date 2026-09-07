"""Les refus — la partie qu'on oublie de tester, et celle qui porte la sécurité.

Un exécuteur dont seuls les succès sont testés n'est pas testé.

Les quatre cas obligatoires du `responder/README.md` sont ici, plus les cas de
**dégradation** : ce qui se passe quand une garde ne peut pas lire ce dont elle a
besoin pour décider. La réponse doit toujours être la même — l'état le plus
restrictif.
"""

from pathlib import Path

import pytest

from responder.config import Config
from responder.executeur import Executeur
from responder.ordre import Ordre

from .conftest import ORDRE_VALIDE, avec


def test_le_temoin_de_desarmement_refuse_avant_toute_autre_verification(
    config: Config, joues: list[Ordre]
) -> None:
    config.fichier_desarmement.write_text("desarme\n", encoding="utf-8")
    executeur = Executeur(config, gestes_cables={"bloquer_ip": joues.append})

    # Ordre volontairement hors catalogue : si la garde 1 passe en premier, le
    # motif parle du désarmement, pas du catalogue. On ne discute pas un ordre
    # quand le frein est tiré.
    decision = executeur.traiter({**ORDRE_VALIDE, "geste": "formater_le_disque"})

    assert decision.refuse
    assert "désarmement" in decision.motif
    assert joues == []


def test_un_repertoire_d_etat_absent_vaut_desarmement(config: Config, tmp_path: Path) -> None:
    # Installation incomplète : on ne peut pas savoir si le frein est tiré.
    absent = tmp_path / "nulle-part" / "response-disarmed"
    executeur = Executeur(avec(config, fichier_desarmement=absent))

    decision = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.refuse
    assert "désarmement" in decision.motif


def test_un_geste_hors_catalogue_est_refuse(executeur: Executeur, joues: list[Ordre]) -> None:
    decision = executeur.traiter({**ORDRE_VALIDE, "geste": "redemarrer_la_base"})

    assert decision.refuse
    assert "hors catalogue" in decision.motif
    assert joues == []


def test_un_geste_en_alerte_seulement_est_refuse(executeur: Executeur) -> None:
    decision = executeur.traiter({**ORDRE_VALIDE, "geste": "couper_connecteur"})

    assert decision.refuse
    assert "alerte seulement" in decision.motif


def test_un_geste_marque_jamais_est_refuse(executeur: Executeur) -> None:
    decision = executeur.traiter({**ORDRE_VALIDE, "geste": "isoler_noeud"})

    assert decision.refuse
    assert "jamais" in decision.motif


def test_un_poste_d_administration_ne_repond_jamais(config: Config) -> None:
    executeur = Executeur(avec(config, role_noeud="workstation"))

    decision = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.refuse
    assert "E6" in decision.motif


def test_le_mode_tournoi_refuse_un_geste_visible(config: Config) -> None:
    config.fichier_mode_tournoi.write_text("actif\n", encoding="utf-8")
    executeur = Executeur(config, gestes_cables={"arreter_conteneur": lambda _: None})

    decision = executeur.traiter({**ORDRE_VALIDE, "geste": "arreter_conteneur"})

    assert decision.refuse
    assert "mode tournoi" in decision.motif
    assert decision.entree["mode"] == "tournoi"


def test_le_mode_tournoi_laisse_passer_un_geste_invisible(
    config: Config, joues: list[Ordre]
) -> None:
    config.fichier_mode_tournoi.write_text("actif\n", encoding="utf-8")
    executeur = Executeur(config, gestes_cables={"bloquer_ip": joues.append})

    decision = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.a_agi
    assert len(joues) == 1


def test_un_temoin_de_tournoi_illisible_est_traite_comme_un_tournoi(
    config: Config, tmp_path: Path
) -> None:
    # L'emplacement du témoin n'existe pas : on ne sait pas si un event est en
    # cours. Ne pas savoir n'autorise rien de plus que savoir.
    introuvable = tmp_path / "hq-deplace" / "node-state" / "tournament-mode"
    executeur = Executeur(
        avec(config, fichier_mode_tournoi=introuvable),
        gestes_cables={"arreter_conteneur": lambda _: None},
    )

    decision = executeur.traiter({**ORDRE_VALIDE, "geste": "arreter_conteneur"})

    assert decision.refuse
    assert "illisible" in decision.motif
    assert decision.entree["mode"] == "tournoi_inconnu"


@pytest.mark.parametrize(
    "cible",
    [
        "203.0.113.7; rm -rf /",
        "$(cat /etc/shadow)",
        "203.0.113.7 && curl attaquant",
        "",
    ],
)
def test_une_cible_qui_ressemble_a_une_commande_est_refusee(
    executeur: Executeur, joues: list[Ordre], cible: str
) -> None:
    decision = executeur.traiter({**ORDRE_VALIDE, "cible": cible})

    assert decision.refuse
    assert "ordre invalide" in decision.motif
    assert joues == []


def test_un_refus_est_journalise_avec_son_motif(executeur: Executeur, config: Config) -> None:
    executeur.traiter({**ORDRE_VALIDE, "geste": "isoler_noeud"})

    lignes = config.journal.read_text(encoding="utf-8").splitlines()
    assert len(lignes) == 1
    assert "isoler_noeud" in lignes[0]
    assert "refuse" in lignes[0]
