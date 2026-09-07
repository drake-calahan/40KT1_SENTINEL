"""Le budget : trois gestes par heure glissante, puis plus rien jusqu'à un humain."""

from pathlib import Path

from responder.config import Config
from responder.degel import degeler
from responder.executeur import Executeur
from responder.ordre import Ordre

from .conftest import ORDRE_VALIDE, avec


def test_les_deux_premiers_gestes_passent_en_orange(
    executeur: Executeur, joues: list[Ordre]
) -> None:
    premier = executeur.traiter(dict(ORDRE_VALIDE))
    second = executeur.traiter(dict(ORDRE_VALIDE))

    assert [premier.severite, second.severite] == ["orange", "orange"]
    assert len(joues) == 2


def test_le_troisieme_geste_passe_et_declenche_un_rouge(
    executeur: Executeur, config: Config, joues: list[Ordre]
) -> None:
    for _ in range(3):
        decision = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.a_agi
    assert decision.severite == "rouge"
    assert len(joues) == 3
    # Le gel est posé par le geste qui consomme le dernier jeton, pas par le
    # suivant : c'est ce qui rend le refus suivant lisible dans le journal.
    assert config.fichier_gel.exists()


def test_au_dela_du_budget_plus_rien_ne_passe_et_l_alerte_est_critique(
    executeur: Executeur, joues: list[Ordre]
) -> None:
    for _ in range(3):
        executeur.traiter(dict(ORDRE_VALIDE))

    quatrieme = executeur.traiter(dict(ORDRE_VALIDE))

    assert quatrieme.refuse
    assert quatrieme.severite == "critique"
    assert "budget gelé" in quatrieme.motif
    assert len(joues) == 3


def test_le_mode_a_blanc_consomme_le_budget_comme_le_mode_arme(
    config: Config, joues: list[Ordre]
) -> None:
    # Un mode a blanc qui ne compterait pas ne prouverait rien du budget — et le
    # budget est precisement ce qu'on veut avoir eprouve avant d'armer.
    executeur = Executeur(
        avec(config, mode_a_blanc=True), gestes_cables={"bloquer_ip": joues.append}
    )

    for _ in range(3):
        decision = executeur.traiter(dict(ORDRE_VALIDE))
    quatrieme = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.resultat == "aurait_execute"
    assert quatrieme.refuse
    assert quatrieme.severite == "critique"
    assert joues == []


def test_le_degel_est_trace_et_remet_le_compteur_a_zero(
    executeur: Executeur, config: Config, joues: list[Ordre]
) -> None:
    for _ in range(4):
        executeur.traiter(dict(ORDRE_VALIDE))

    degeler(config, motif="faux positif corrigé", par="thomas")
    apres = executeur.traiter(dict(ORDRE_VALIDE))

    assert apres.a_agi
    assert len(joues) == 4
    assert not config.fichier_gel.exists()
    assert "dégel par thomas" in config.journal.read_text(encoding="utf-8")


def test_retirer_le_temoin_a_la_main_ne_suffit_pas(
    executeur: Executeur, config: Config, joues: list[Ordre]
) -> None:
    # Le compte de l'heure glissante vit dans le journal, pas dans le temoin.
    # Un `rm` ne laisse pas de trace : il ne rouvre donc pas le budget.
    for _ in range(3):
        executeur.traiter(dict(ORDRE_VALIDE))
    config.fichier_gel.unlink()

    apres = executeur.traiter(dict(ORDRE_VALIDE))

    assert apres.refuse
    assert len(joues) == 3


def test_un_journal_illisible_refuse_au_lieu_de_supposer_zero(
    config: Config, joues: list[Ordre]
) -> None:
    config.journal.write_text("{ceci n'est pas du json\n", encoding="utf-8")
    executeur = Executeur(config, gestes_cables={"bloquer_ip": joues.append})

    decision = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.refuse
    assert "non mesurable" in decision.motif
    assert decision.severite == "rouge"
    assert joues == []


def test_un_budget_nul_ne_laisse_rien_passer(config: Config, tmp_path: Path) -> None:
    executeur = Executeur(avec(config, budget_par_heure=0))

    decision = executeur.traiter(dict(ORDRE_VALIDE))

    assert decision.refuse
    assert decision.severite == "critique"
