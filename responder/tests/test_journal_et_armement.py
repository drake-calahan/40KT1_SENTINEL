"""Ce que l'exécuteur écrit, et ce qu'il refuse de jouer tant qu'il est désarmé."""

import json
from pathlib import Path

from responder.config import Config
from responder.executeur import Executeur
from responder.journal import Journal
from responder.ordre import Ordre

from .conftest import ORDRE_VALIDE, avec


def _entrees(chemin: Path) -> list[dict[str, object]]:
    lignes = chemin.read_text(encoding="utf-8").splitlines()
    return [json.loads(ligne) for ligne in lignes if ligne.strip()]


def test_une_reponse_desarmee_journalise_et_ne_joue_rien(
    config: Config, joues: list[Ordre]
) -> None:
    executeur = Executeur(
        avec(config, reponse_armee=False), gestes_cables={"bloquer_ip": joues.append}
    )

    decision = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.resultat == "aurait_execute"
    assert "désarmée" in decision.motif
    assert joues == []
    assert _entrees(config.journal)[0]["armement"] == "desarme"


def test_un_geste_non_cable_ne_rend_jamais_un_succes(config: Config) -> None:
    # C'est l'etat de la phase : le noyau decide, les gestes arrivent en P03.6.
    # Un « execute » sans geste cable serait un faux vert de plus.
    executeur = Executeur(config, gestes_cables={})

    decision = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.resultat == "aurait_execute"
    assert "non câblé" in decision.motif


def test_le_journal_porte_le_geste_la_regle_et_le_motif(
    executeur: Executeur, config: Config
) -> None:
    executeur.traiter(dict(ORDRE_VALIDE))

    entree = _entrees(config.journal)[0]
    assert entree["geste"] == "bloquer_ip"
    assert entree["cible"] == "203.0.113.7"
    assert entree["regle"] == "100201"
    assert entree["resultat"] == "execute"
    assert entree["motif"]
    assert entree["horodatage"].endswith("+00:00")


def test_le_journal_ajoute_sans_jamais_reecrire(executeur: Executeur, config: Config) -> None:
    executeur.traiter(dict(ORDRE_VALIDE))
    executeur.traiter({**ORDRE_VALIDE, "geste": "isoler_noeud"})

    entrees = _entrees(config.journal)
    assert [e["resultat"] for e in entrees] == ["execute", "refuse"]


def test_un_journal_absent_compte_zero_geste(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "jamais-ecrit.jsonl")

    assert journal.gestes_dans_la_fenetre() == 0


def test_les_gestes_hors_fenetre_ne_comptent_plus(tmp_path: Path) -> None:
    chemin = tmp_path / "reponse.jsonl"
    chemin.write_text(
        json.dumps({"horodatage": "2020-01-01T00:00:00+00:00", "resultat": "execute"}) + "\n",
        encoding="utf-8",
    )

    assert Journal(chemin).gestes_dans_la_fenetre() == 0


def test_un_horodatage_sans_fuseau_rend_inconnu(tmp_path: Path) -> None:
    # Une heure sans fuseau ne se compare pas de facon fiable : plutot inconnu
    # qu'un comptage faux qui desserrerait la garde.
    chemin = tmp_path / "reponse.jsonl"
    chemin.write_text(
        json.dumps({"horodatage": "2026-09-07T12:00:00", "resultat": "execute"}) + "\n",
        encoding="utf-8",
    )

    assert Journal(chemin).gestes_dans_la_fenetre() is None
