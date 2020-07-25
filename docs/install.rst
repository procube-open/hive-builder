====================
インストール
====================

ここでは、hive-builder のインストールについて説明します。

動作環境
====================

インターネット上の各種リポジトリに http, https でアクセスできる必要があります。
プロキシ経由でのみアクセスできる環境の場合、「プロキシ環境下での構築」を参照して事前準備を行ってください。

mother マシンの OS は、CentOS, Windows Subsystem for Linux, Mac OS, Ubuntu などの環境で以下を満たしている必要があります。

- openssl コマンドが利用できること
- pip が利用できること
- python 3.6 以上が利用できること
- git コマンドが利用できること
- docker コマンドが利用できること

各OSごとにインストールの手順を示します。

Centos 7 の場合
=================================

.. note::

    現在サポートしているのは CentOS 7/8 です。CentOS 6 は未サポートです。

docker コマンドのインストール
------------------------------
以下のコマンドを root で実行して docker-client をインストールしてください。

::

  yum install -y docker-client

Centos 8 の場合
=================================

docker コマンドのインストール
------------------------------
以下のコマンドを root で実行して docker-ce-cli をインストールしてください。

::

  yum config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  yum install -y  docker-ce-cli

.. note::

    prepared プロバイダを使用し、その対象サーバ内に mother 環境を作成する場合は、 docker コマンドをインストールする必要はありません。
    逆に CentOS 標準の docker-client パッケージがインストールされていると、 hive-builder がインストールする docker-ce と競合して構築に失敗しますので、注意してください。


.. _basic:

仮想環境の作成例
----------------------------
hive-builder をインストールするための仮想環境 Python3 の venv モジュールを用いて作成する場合のコマンド例を示します。
仮想環境の作成は pyenv, conda, pipenv など、他のツールを用いることもできますし、
もともと hive-builder 専用に用意されたOSであれば、仮想環境を作成せずに利用しても良いでしょう。

::

  cd ~
  python3 -m venv hive
  echo source ~/hive/bin/activate >> .bashrc
  source ~/hive/bin/activate
  pip install -U pip wheel

hive-builder のインストール
----------------------------
以下のコマンドでインストールしてください。

::

  pip install hive_builder

インストールがエラーになる場合は、 pip install -U pip wheel で pip と wheel を最新バージョンにアップデートしてみてください。

Windows Subsystem for Linuxの場合
===================================

docker コマンドのインストール
------------------------------
  以下のコマンドを root で実行して docker.io をインストールしてください。

::

  apt-get update
  apt-get install docker
  apt docker.io

仮想環境と hive-builder のインストール
--------------------------------------
仮想環境と hive-builder のインストールについては、Cent OS の場合と同じです。 :ref:`そちら <basic>` を参照してください。

ssh鍵のmode の問題
---------------------
ansible でサーバへのログインに使用する ssh 鍵のファイルについて、
owner は自分で modeは 0400 となっていて、他人から参照できない状態である必要があります。
Windows 10 WSL 環境で /mnt/c/Users/lucy のように
Windows から見えるディレクトリに hive のルートディレクトリを作成すると、ssh 鍵の
mode が 0777 となってしまい、 ssh ログイン時にエラーになります。その場合、
context_dir を ~/hive-context などに設定することで回避できます。
以下のコマンドを実行してください。

::

  mkdir -p ~/.hive/private
  hive set context_dir ~/.hive/private

この操作はステージごとに必要であり、context_dir はステージごとに異なる
必要があります。

Mac OS の場合
=================================

docker コマンドのインストール
------------------------------
インストールの手順は以下のページに従ってください。
https://docs.docker.com/docker-for-mac/install/
インストール後、一度は docker アプリケーションを起動しないと docker コマンドがインストールされません。
デスクトップからdocker アプリケーションを起動して、docker コマンドが使えるようになったことを確認した後、
ステータスバーの docker のアイコンをクリックして docker を終了しても構いません。
hive-builder は docker コマンドを必要としますが、端末のdocker デーモンにアクセスしません。
docker desktop for mac は VM を起動しますので、リソースを消費します。
他に docker を必要とすることがなければ、落としておいてください。

仮想環境と hive-builder のインストール
--------------------------------------
仮想環境と hive-builder のインストールについては、Cent OS の場合と同じです。 :ref:`そちら<basic>` を参照してください。


raspbian へのインストール
=================================
raspberry pi にインストールする場合は、OSに raspbian を利用し、以下の手順で必要なソフトウェアをインストールしてください。

::

  apt-get update
  apt-get upgrade
  curl -sSL https://get.docker.com | sh
  usermod -aG docker pi
  apt-get install build-essential libssl-dev libffi-dev python3-dev subversion python3-venv subversion xorriso

仮想環境と hive-builder のインストール
--------------------------------------
仮想環境と hive-builder のインストールについては、Cent OS の場合と同じです。 :ref:`そちら<basic>` を参照してください。

