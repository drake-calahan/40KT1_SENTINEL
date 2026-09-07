"""Fixtures communes — un nœud de test complet, dans un répertoire temporaire."""

from dataclasses import replace
from pathlib import Path

import pytest

from responder.config import Config
from responder.executeur import Executeur
from responder.ordre import Ordre

ORDRE_VALIDE: dict[str, object] = {
    "geste": "bloquer_ip",
    "cible": "203.0.113.7",
    "regle": "100201",
}


@pytest.fixture
def config(tmp_path: Path) -> Config:
    """Un nœud armé, hors mode à blanc : l'état le plus permissif possible.

    Les tests qui comptent partent de là et referment une garde à la fois — c'est
    la seule façon de vérifier qu'une garde refuse *par elle-même* et non parce
    qu'une autre l'avait déjà fait.
    """
    etat = tmp_path / "etat"
    etat.mkdir()
    hq = tmp_path / "hq" / "node-state"
    hq.mkdir(parents=True)
    return Config(
        role_noeud="primary",
        repertoire_etat=etat,
        fichier_desarmement=etat / "response-disarmed",
        fichier_mode_tournoi=hq / "tournament-mode",
        journal=etat / "reponse.jsonl",
        reponse_armee=True,
        mode_a_blanc=False,
        budget_par_heure=3,
    )


@pytest.fixture
def joues() -> list[Ordre]:
    """Les gestes réellement joués pendant un test. Doit rester vide sauf mention."""
    return []


@pytest.fixture
def executeur(config: Config, joues: list[Ordre]) -> Executeur:
    """Un exécuteur dont le seul geste câblé enregistre son appel, sans rien faire."""
    return Executeur(config, gestes_cables={"bloquer_ip": joues.append})


def avec(config: Config, **champs: object) -> Config:
    """Rend une configuration modifiée — les `Config` sont figées, et c'est voulu."""
    return replace(config, **champs)
