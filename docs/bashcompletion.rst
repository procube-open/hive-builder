==========================
bash completion の利用
==========================

hive で bash completion を利用するためにはシェルに hive-completion.sh を bash に読み込ませる必要があります。
例えば、 hive-builder がインストールされている仮想環境を activate した後、
以下を実行することで hive の bash completion を利用できます。

::

  source "$(hive get-install-dir)/hive-completion.sh"

あるいは、仮想環境が activate している状態で、以下のコマンドを実行することで、
仮想環境の activate 時に自動的に hive-completion.sh を読み込むように設定することができます。

::

  hive setup-bash-completion

このコマンドは、仮想環境の activate スクリプトを編集してスクリプトの末尾に以下のコードを追加します。

::

  source "$(hive get-install-dir)/hive-completion.sh"
  HIVE_VIRTUAL_ENV_INIT=1

bash completion を利用するためには、コマンド実行後、 activate しなおしてください。
ただし、 pyenv で仮想環境を切り替えている場合は activate スクリプトは評価されませんので、
この方法は利用できません。