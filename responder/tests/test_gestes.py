"""Les quatre gestes armables — testés sur leurs REFUS autant que sur leurs gestes.

`.agent/prompts/claude.md` : *« Écrire l'exécuteur de réponse et le tester sur ses
refus — geste hors catalogue, budget épuisé, mode tournoi, désarmement — autant
que sur ses gestes. »* Ce fichier applique la même exigence un cran plus bas : ce
qui compte dans un geste privilégié, ce n'est pas qu'il agisse, c'est **ce sur
quoi il refuse d'agir**.

Aucun test de ce fichier n'exécute `nft`, `docker` ou `kill` sur la machine : les
refus tombent à la validation de la cible, donc **avant** toute commande. C'est
en soi une propriété du code — une validation qui n'arrive qu'après avoir touché
la machine ne protège rien.
"""

import json
import os
from pathlib import Path

import pytest

from responder import gestes
from responder.catalogue import CATALOGUE, Etat
from responder.executeur import Executeur
from responder.gestes import arreter_conteneur, arreter_processus, bloquer_ip, quarantaine_fichier
from responder.gestes.base import CibleRefusee, GesteEchoue, sous_un_de
from responder.tests.conftest import avec

# Les nœuds cibles sont des Linux, et ces refus reposent sur la sémantique POSIX
# des chemins : sur Windows, « /etc/passwd » n'est même pas un chemin absolu, et
# le test échouerait pour une raison qui n'existe pas sur la machine visée. La CI
# tourne sur `ubuntu-latest` : c'est là que ces tests comptent, et ils y tournent.
posix_seulement = pytest.mark.skipif(
    os.name != "posix", reason="sémantique de chemin POSIX — les nœuds cibles sont des Linux"
)

# ══════════════════════════════════════════════════════════════════════════
# La cohérence entre ce qui est câblé et ce que l'ADR autorise
# ══════════════════════════════════════════════════════════════════════════


def test_aucun_geste_cable_hors_de_ce_que_le_catalogue_arme() -> None:
    """Câbler un geste « alerte » le rendrait exécutable sans amender `ADR-002`."""
    assert gestes.verifier_coherence() == []


def test_les_quatre_gestes_armes_d_adr_002_sont_cables() -> None:
    """`E2` a tranché **quatre** gestes armés. Si le compte bouge, un fichier a dérivé."""
    armes = {nom for nom, g in CATALOGUE.items() if g.nominal is Etat.ARME}
    assert armes == set(gestes.JOUEURS)
    assert len(armes) == 4


# ══════════════════════════════════════════════════════════════════════════
# `bloquer_ip` — ce qu'il refuse de bloquer
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "cible",
    [
        "127.0.0.1",  # se bloquer soi-même
        "10.0.0.4",  # LAN d'administration
        "192.168.1.20",  # LAN
        "100.64.1.2",  # plage du tailnet
        "::1",
        "fd00::1",
    ],
)
def test_bloquer_ip_refuse_ce_qui_couperait_le_chemin_du_retour(cible: str) -> None:
    """Bloquer le tailnet ou le LAN, c'est se couper le moyen de venir débloquer.

    Le geste cesserait d'être réversible « sans arbitrage » (`ADR-062`) : il
    exigerait 70 km de voiture, ce qui est le motif pour lequel `isoler_noeud`
    est classé « jamais » au catalogue.
    """
    with pytest.raises(CibleRefusee):
        bloquer_ip.valider(cible)


@pytest.mark.parametrize("cible", ["pas-une-ip", "203.0.113.0/24", "/etc/passwd", "1234"])
def test_bloquer_ip_refuse_ce_qui_n_est_pas_une_adresse(cible: str) -> None:
    """`ordre.py` filtre les caractères ; il ne sait pas qu'une IP n'est pas un chemin."""
    with pytest.raises(CibleRefusee):
        bloquer_ip.valider(cible)


def test_bloquer_ip_accepte_une_adresse_publique() -> None:
    cible = bloquer_ip.valider("203.0.113.7")
    assert cible.adresse == "203.0.113.7"
    assert cible.famille == "ip"
    assert bloquer_ip.valider("2001:db8::1").famille == "ip6"


def test_bloquer_ip_refuse_si_notre_table_n_existe_pas(monkeypatch: pytest.MonkeyPatch) -> None:
    """Il ne CRÉE pas la structure de filtrage au milieu d'un incident.

    Poser du pare-feu sans revue, sur une machine qui sert `hq.40kt1.com`, au pire
    moment : le geste refuse et le dit, plutôt que d'improviser.
    """
    monkeypatch.setattr(bloquer_ip, "binaire", lambda _nom: "/usr/sbin/nft")

    class Resultat:
        returncode = 1
        stderr = "No such file or directory"
        stdout = ""

    monkeypatch.setattr(bloquer_ip, "executer", lambda *_a, **_k: Resultat())
    with pytest.raises(GesteEchoue, match="n'existe pas"):
        bloquer_ip.jouer("203.0.113.7")


# ══════════════════════════════════════════════════════════════════════════
# `arreter_processus` — ce qu'il refuse d'arrêter
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("pid", ["0", "1"])
def test_arreter_processus_refuse_init(pid: str) -> None:
    """Arrêter `init` arrête la machine, et elle est à 70 km."""
    with pytest.raises(CibleRefusee, match="init"):
        arreter_processus.valider(pid)


def test_arreter_processus_refuse_l_executeur_lui_meme() -> None:
    """Un exécuteur qui s'arrête laisse l'incident sans réponse."""
    with pytest.raises(CibleRefusee, match="exécuteur"):
        arreter_processus.valider(str(os.getpid()))


@pytest.mark.parametrize("cible", ["sshd", "nginx", "-1", "12.5", ""])
def test_arreter_processus_refuse_ce_qui_n_est_pas_un_pid(cible: str) -> None:
    with pytest.raises(CibleRefusee, match="PID"):
        arreter_processus.valider(cible)


@pytest.mark.parametrize(
    "nom", ["sshd", "tailscaled", "dockerd", "postgres", "caddy", "cloudflared"]
)
def test_arreter_processus_refuse_hq_et_le_chemin_d_administration(
    monkeypatch: pytest.MonkeyPatch, nom: str
) -> None:
    """`RULES` § 2 : aucun geste automatique ne touche la version servie ni la donnée.

    Et couper `sshd` ou `tailscaled`, c'est perdre le moyen de venir défaire le
    geste — le geste sortirait du catalogue en cessant d'être réversible.
    """
    monkeypatch.setattr(arreter_processus.Path, "exists", lambda _self: True)
    monkeypatch.setattr(
        arreter_processus, "_lire", lambda _pid, quoi: nom if quoi == "comm" else ""
    )
    with pytest.raises(CibleRefusee, match="40KT1_HQ|administration"):
        arreter_processus.valider("4242")


def test_arreter_processus_refuse_un_processus_de_hq_par_son_cgroup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Le nom ne suffit pas : un conteneur de HQ porte un nom quelconque."""
    monkeypatch.setattr(arreter_processus.Path, "exists", lambda _self: True)
    monkeypatch.setattr(
        arreter_processus,
        "_lire",
        lambda _pid, quoi: "python3" if quoi == "comm" else "0::/system.slice/40kt1-api.service",
    )
    with pytest.raises(CibleRefusee, match="40kt1-"):
        arreter_processus.valider("4242")


def test_arreter_processus_refuse_quand_l_identite_est_inconnue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un `inconnu` n'est pas un `ok` : on n'arrête pas ce qu'on n'a pas pu identifier."""
    monkeypatch.setattr(arreter_processus.Path, "exists", lambda _self: True)
    monkeypatch.setattr(arreter_processus, "_lire", lambda _pid, _quoi: None)
    with pytest.raises(CibleRefusee, match="n'a pas pu être lu"):
        arreter_processus.valider("4242")


def test_arreter_processus_refuse_quand_le_cgroup_est_illisible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On ne conclut pas « il n'est pas à HQ » faute d'avoir pu regarder."""
    monkeypatch.setattr(arreter_processus.Path, "exists", lambda _self: True)
    monkeypatch.setattr(
        arreter_processus, "_lire", lambda _pid, quoi: "python3" if quoi == "comm" else None
    )
    with pytest.raises(CibleRefusee, match="INCONNUE"):
        arreter_processus.valider("4242")


# ══════════════════════════════════════════════════════════════════════════
# `arreter_conteneur` — le contournement du catalogue, refusé
# ══════════════════════════════════════════════════════════════════════════


def test_arreter_conteneur_refuse_cloudflared_car_ce_serait_couper_connecteur() -> None:
    """Le test qui a motivé le module.

    Arrêter `cloudflared`, **c'est** `couper_connecteur` — classé *alerte* en
    nominal et *jamais* en tournoi. L'autoriser ici rendrait exécutable un geste
    alerte-seulement en passant par un autre nom, et le catalogue fermé cesserait
    d'être fermé.
    """
    assert CATALOGUE["couper_connecteur"].nominal is Etat.ALERTE
    with pytest.raises(CibleRefusee, match="couper_connecteur"):
        arreter_conteneur.valider("cloudflared")


@pytest.mark.parametrize("nom", ["db", "postgres", "caddy", "api", "40kt1-db", "40kt1-caddy"])
def test_arreter_conteneur_refuse_ce_qui_sert_la_production(nom: str) -> None:
    """Donnée, version servie, identité de la machine qui sert le nom public (`RULES` § 2)."""
    with pytest.raises(CibleRefusee, match="production"):
        arreter_conteneur.valider(nom)


@pytest.mark.parametrize("nom", ["CloudFlared", "/db", "  caddy  ", "40KT1-API"])
def test_arreter_conteneur_ne_se_contourne_pas_par_la_casse_ou_un_slash(nom: str) -> None:
    """Un refus qu'on contourne par une majuscule ne protège de rien."""
    with pytest.raises(CibleRefusee):
        arreter_conteneur.valider(nom)


@pytest.mark.parametrize(
    "nom",
    [
        "fortyk-db-1",
        "fortyk-caddy-1",
        "fortyk-api-1",
        "fortyk-cloudflared-1",
        # Compose numérote ses instances : `-2` le jour où l'on met à l'échelle.
        "fortyk-db-2",
        # Un refus qu'on contourne par une majuscule ou un slash ne protège de rien.
        "/fortyk-API-1",
    ],
)
def test_arreter_conteneur_refuse_les_noms_reels_du_parc(nom: str) -> None:
    """Les vrais noms, relevés par `docker ps` sur `patator-tower` le 2026-09-09.

    Le lot `P03.7` demandait de confirmer que la liste couvrait les noms réels.
    Elle ne les couvrait pas : le projet Compose s'appelle `fortyk`, pas
    `40kt1`, et les quatre conteneurs protégés étaient tous arrêtables sous leur
    vrai nom. La protection était écrite, relue, testée — et vide. Ce test est
    celui qui manquait, et il ne peut être écrit qu'après avoir regardé la
    machine.
    """
    with pytest.raises(CibleRefusee):
        arreter_conteneur.valider(nom)


def test_arreter_conteneur_laisse_le_scraper_arretable() -> None:
    """`fortyk-scraper-1` n'est **pas** protégé, et c'est délibéré.

    Il ne sert ni la donnée, ni le nom public, ni la version servie. Un scraper
    compromis est exactement ce qu'on veut pouvoir arrêter — protéger tout le
    projet Compose d'un bloc aurait vidé le geste de son objet.
    """
    assert arreter_conteneur.valider("fortyk-scraper-1") == "fortyk-scraper-1"


def test_arreter_conteneur_accepte_un_conteneur_quelconque() -> None:
    assert arreter_conteneur.valider("scraper-jetable") == "scraper-jetable"


# ══════════════════════════════════════════════════════════════════════════
# `quarantaine_fichier` — le coffre, et ce qui n'y entre pas
# ══════════════════════════════════════════════════════════════════════════


@posix_seulement
@pytest.mark.parametrize(
    "cible", ["/etc/passwd", "/etc/shadow", "/usr/bin/tailscale", "/boot/vmlinuz", "/var/ossec/x"]
)
def test_quarantaine_refuse_le_systeme(cible: str, tmp_path: Path) -> None:
    """Le défaire demanderait de démarrer sur une clé : ce n'est pas « sans arbitrage »."""
    with pytest.raises(CibleRefusee, match="système"):
        quarantaine_fichier.valider(cible, racine_etat=tmp_path, racines_hq=("/srv/40kt1",))


@posix_seulement
def test_quarantaine_refuse_l_arborescence_de_hq(tmp_path: Path) -> None:
    """Déplacer un fichier hors d'un répertoire, c'est y écrire — et on n'écrit pas chez HQ."""
    with pytest.raises(CibleRefusee, match="40KT1_HQ"):
        quarantaine_fichier.valider(
            "/srv/40kt1/webshell.php", racine_etat=tmp_path, racines_hq=("/srv/40kt1",)
        )


def test_quarantaine_refuse_nos_propres_fichiers(tmp_path: Path) -> None:
    """Retirer le témoin de désarmement reviendrait à saboter le frein d'urgence."""
    with pytest.raises(CibleRefusee, match="Sentinelle"):
        quarantaine_fichier.valider(
            str(tmp_path / "response-disarmed"), racine_etat=tmp_path, racines_hq=("/srv/40kt1",)
        )


def test_quarantaine_refuse_un_chemin_relatif(tmp_path: Path) -> None:
    with pytest.raises(CibleRefusee, match="absolu"):
        quarantaine_fichier.valider("etc/passwd", racine_etat=tmp_path, racines_hq=())


def test_quarantaine_refuse_un_lien_symbolique(tmp_path: Path) -> None:
    """Déplacer le lien laisse la cible en place : on croirait la menace traitée."""
    reel = tmp_path / "reel.bin"
    reel.write_bytes(b"charge")
    lien = tmp_path / "lien.bin"
    try:
        lien.symlink_to(reel)
    except (OSError, NotImplementedError):
        pytest.skip("liens symboliques indisponibles sur cette plateforme")
    with pytest.raises(CibleRefusee, match="lien symbolique"):
        quarantaine_fichier.valider(str(lien), racine_etat=tmp_path / "etat", racines_hq=())


def test_quarantaine_deplace_conserve_l_empreinte_et_rend_le_retour_arriere(
    tmp_path: Path,
) -> None:
    """Le retour arrière doit être une COMMANDE, pas une phrase.

    `ADR-062` demande qu'un humain puisse défaire sans arbitrage. Lui laisser
    retrouver le chemin d'origine et les droits à 3 h du matin est de l'arbitrage.
    """
    suspect = tmp_path / "depot" / "charge.php"
    suspect.parent.mkdir()
    suspect.write_text("<?php system($_GET['c']); ?>", encoding="utf-8")
    etat = tmp_path / "etat"

    retour = quarantaine_fichier.jouer(str(suspect), racine_etat=etat, racines_hq=())

    # Le fichier n'est plus là, et il n'est nulle part deux fois.
    assert not suspect.exists()
    coffre = etat / "quarantaine"
    deplaces = [f for f in coffre.iterdir() if f.suffix != ".json"]
    assert len(deplaces) == 1
    assert deplaces[0].read_text(encoding="utf-8").startswith("<?php")

    # L'empreinte est conservée, et le manifeste porte de quoi remettre en place.
    # Comparaison sur le JSON analysé, et non sur le texte : un chemin Windows
    # y est échappé, et le test échouerait pour une raison sans rapport.
    manifeste = coffre / f"{deplaces[0].name}.json"
    assert manifeste.exists()
    contenu = json.loads(manifeste.read_text(encoding="utf-8"))
    assert contenu["origine"] == str(suspect)
    assert len(contenu["sha256"]) == 64
    assert contenu["taille"] == deplaces[0].stat().st_size

    # Le retour arrière est copiable-collable.
    assert "mv " in retour
    assert str(suspect) in retour


def test_quarantaine_refuse_un_fichier_trop_gros(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Remplir le disque du nœud pendant un incident aggraverait l'incident."""
    gros = tmp_path / "gros.bin"
    gros.write_bytes(b"x" * 128)
    monkeypatch.setattr(quarantaine_fichier, "TAILLE_MAX", 10)
    with pytest.raises(GesteEchoue, match="plafond"):
        quarantaine_fichier.jouer(str(gros), racine_etat=tmp_path / "etat", racines_hq=())


def test_sous_un_de_resiste_a_la_traversee(tmp_path: Path) -> None:
    """`/tmp/../etc/passwd` doit être vu comme `/etc`. La cible vient du réseau."""
    assert sous_un_de(Path("/tmp/../etc/passwd"), ("/etc",)) == "/etc"


# ══════════════════════════════════════════════════════════════════════════
# L'exécuteur face à un geste qui échoue
# ══════════════════════════════════════════════════════════════════════════


def test_un_geste_qui_echoue_est_journalise_et_ne_remonte_pas(config, joues) -> None:
    """Le défaut corrigé en `P03.6` : l'échec ne laissait AUCUNE trace.

    Sans ce rattrapage, l'exception s'échappait de `traiter()` : ni geste, ni
    refus, ni ligne au journal. On croyait la menace traitée, et le budget ne
    comptait pas la tentative — donc on pouvait la rejouer sans fin.
    """

    def geste_qui_casse(_ordre: object) -> str:
        raise GesteEchoue("nft indisponible")

    executeur = Executeur(config, gestes_cables={"bloquer_ip": geste_qui_casse})
    decision = executeur.traiter({"geste": "bloquer_ip", "cible": "203.0.113.7", "regle": "100201"})

    assert decision.resultat == "echoue"
    assert "nft indisponible" in decision.motif
    assert decision.severite == "rouge"
    assert not decision.a_agi
    assert config.journal.read_text(encoding="utf-8").count("\n") == 1
    assert joues == []


def test_une_tentative_en_echec_consomme_le_budget(config) -> None:
    """Sinon un geste qui échoue se rejoue indéfiniment, et le budget ne garde rien."""

    def geste_qui_casse(_ordre: object) -> str:
        raise GesteEchoue("indisponible")

    executeur = Executeur(config, gestes_cables={"bloquer_ip": geste_qui_casse})
    ordre = {"geste": "bloquer_ip", "cible": "203.0.113.7", "regle": "100201"}
    for _ in range(3):
        executeur.traiter(ordre)

    # Le budget est à 3 : la quatrième tentative doit être refusée, pas retentée.
    decision = executeur.traiter(ordre)
    assert decision.refuse
    assert "gel" in decision.motif


def test_le_retour_arriere_du_geste_arrive_au_journal(config) -> None:
    """C'est ce que l'exploitant copie-colle : il doit porter les VALEURS réelles."""

    def geste(_ordre: object) -> str:
        return "nft delete element inet sentinel bloque { 203.0.113.7 }"

    executeur = Executeur(config, gestes_cables={"bloquer_ip": geste})
    decision = executeur.traiter({"geste": "bloquer_ip", "cible": "203.0.113.7", "regle": "100201"})
    assert decision.resultat == "execute"
    assert "203.0.113.7" in decision.motif
    assert "nft delete element" in decision.motif


# ══════════════════════════════════════════════════════════════════════════
# Un poste d'administration ne répond jamais (`E6`)
# ══════════════════════════════════════════════════════════════════════════


def test_un_poste_n_a_aucun_geste_cable(config) -> None:
    """`E6` : alerte seulement sur les postes. Refusé par construction, pas par réglage."""
    assert gestes.gestes_du_noeud(avec(config, role_noeud="workstation")) == {}
    assert set(gestes.gestes_du_noeud(avec(config, role_noeud="primary"))) == set(gestes.JOUEURS)
