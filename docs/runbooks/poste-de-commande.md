# Poste de commande — WSL sur `AEGIS-TOWER`

> **Décidé par le PO le 2026-09-10** : les playbooks se jouent depuis **WSL2 sur
> `AEGIS-TOWER`**. Ce runbook prépare ce poste, et **ne touche aucune machine du
> parc** : tout ce qui suit se passe sur le poste, sauf la pose d'une clé
> publique SSH (§ 3), qui est un geste explicite sur les deux nœuds.
>
> Ansible ne tourne pas nativement sous Windows — ce n'est pas une préférence,
> c'est une absence de support. WSL2 est donc le poste, et il a ses propres
> pièges : deux d'entre eux sont mesurés ci-dessous.

## 1. Le dépôt vit DANS WSL, jamais sous `/mnt/c`

⚠️ **Mesuré**, et le symptôme ne dit pas la cause : un dépôt lu depuis
`/mnt/c/...` est vu par Ansible comme un répertoire **mondialement inscriptible**.
Ansible **ignore alors `ansible.cfg`** — silencieusement, avec un simple
avertissement — donc `roles_path`, `collections_path` et le format de sortie
sautent. Le premier symptôme est un incompréhensible *« the role
'sentinel_server' was not found »* alors que le rôle est bien là.

```bash
# Dans WSL, pas sous /mnt/c :
git clone git@github.com:drake-calahan/40KT1_SENTINEL.git ~/40KT1_SENTINEL
cd ~/40KT1_SENTINEL/infra/ansible
```

Éditer depuis Windows reste possible (VS Code « WSL: Ubuntu »), mais **le dépôt
qu'on joue** est celui de WSL.

## 2. Ansible, à la version de la CI

La CI épingle `ansible-core 2.17` : jouer une autre version, c'est jouer autre
chose que ce qui a été validé.

```bash
sudo apt-get update && sudo apt-get install -y python3-venv
python3 -m venv ~/.venv-sentinel
~/.venv-sentinel/bin/pip install --upgrade pip
~/.venv-sentinel/bin/pip install "ansible-core==2.17.*"
echo 'export PATH="$HOME/.venv-sentinel/bin:$PATH"' >> ~/.bashrc && exec bash
cd ~/40KT1_SENTINEL/infra/ansible
ansible-galaxy collection install -r requirements.yml
```

Contrôle :

```bash
ansible --version && ansible-galaxy collection list | grep -i community
```

## 3. L'accès SSH aux deux nœuds

Le compte est `calahan` sur les deux nœuds (inventaire). Générer une clé
**propre à ce poste** — une clé recopiée d'ailleurs mélange deux identités :

```bash
ssh-keygen -t ed25519 -C "wsl-aegis-tower-sentinel" -f ~/.ssh/id_ed25519_sentinel
```

Puis la poser sur chaque nœud (geste explicite, à faire depuis une session déjà
ouverte) :

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_sentinel.pub calahan@patator-tower.tail29e268.ts.net
ssh-copy-id -i ~/.ssh/id_ed25519_sentinel.pub calahan@patator-standby.tail29e268.ts.net
```

⚠️ Cette pose **modifie `authorized_keys`** sur les deux nœuds. Faite maintenant,
avant que les agents soient posés, elle ne produit aucune alerte. Faite après,
elle déclenchera la règle `100101` — la seule règle `critique` du dépôt. Ce
n'est pas un défaut : c'est exactement ce qu'on lui demande de faire.

Déclarer la clé pour Ansible (`~/.ssh/config`, dans WSL) :

```
Host patator-*
  User calahan
  IdentityFile ~/.ssh/id_ed25519_sentinel
  IdentitiesOnly yes
```

## 4. Le tailnet, vu depuis WSL2 — le point à vérifier, pas à supposer

WSL2 a sa propre pile réseau derrière une traduction d'adresses : **le fait que
Tailscale tourne sous Windows ne suffit pas** à ce que les noms MagicDNS
résolvent dans WSL. Vérifier, dans cet ordre :

```bash
# a) la résolution du nom
getent hosts patator-standby.tail29e268.ts.net

# b) l'accès réseau
ping -c 2 patator-standby.tail29e268.ts.net

# c) l'accès SSH réel — le seul qui compte
ssh calahan@patator-standby.tail29e268.ts.net 'hostname; ip -4 addr show tailscale0 | grep inet'
```

- **(a) échoue, (b) réussit avec l'IP `100.x`** → c'est la résolution qui
  manque, pas le réseau. Deux issues : activer MagicDNS pour WSL, ou surcharger
  `ansible_host` par l'adresse `100.x` du nœud pour cette session
  (`-e ansible_host=100.x.y.z`). La seconde est acceptable ponctuellement ;
  **ne pas la committer** — l'inventaire porte des noms, pas des IP de tailnet
  qui changeront.
- **(b) échoue aussi** → installer Tailscale **dans** WSL et l'y connecter au
  tailnet, ou jouer depuis une autre machine. Ne pas contourner par une IP
  publique : `C4` l'interdit, et ce n'est pas négociable.

⚠️ Rappel `patator-standby` : quatre pertes totales d'IPv4 en trois semaines
(`.agent/DISCOVERY.md`). Un `ping` qui échoue sur CE nœud n'est pas forcément un
problème de WSL. Vérifier `IP4.ADDRESS` sur la machine avant de conclure.

## 5. L'élévation de privilège

`sudo-rs` est le `sudo` par défaut d'Ubuntu 26.04 et casse `become` avec un
message qui ressemble à un problème de réseau. Le contournement
(`ansible_become_exe: /usr/bin/sudo.ws`) est **déjà dans l'inventaire** pour
`patator-tower`. Le contrôle qui le vérifie est dans `00_check.yml`, et il rend
son verdict même en `--check` depuis `P01.20`.

Si l'élévation demande un mot de passe, ajouter `--ask-become-pass` aux
commandes du runbook de mise en service. Ne **jamais** poser un mot de passe
dans le dépôt, l'inventaire ou un `-e`.

## 6. Le contrôle de terrain, qui clôt cette préparation

```bash
cd ~/40KT1_SENTINEL/infra/ansible
ansible-playbook -i inventory/production.yml playbooks/00_check.yml --check --diff
```

Il ne pose rien. Il dit qui répond, si l'élévation marche, où est la stack HQ,
et surtout **ce qu'il n'a pas pu mesurer** : un nœud injoignable ressort
`INCONNU`, jamais `ok`.

**Le poste est prêt quand ce playbook rend son verdict sur les deux nœuds.**
La suite est [`mise-en-service.md`](mise-en-service.md).
