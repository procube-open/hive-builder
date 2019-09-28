====================
インストール
====================

ここでは、hive-builder のインストールについて説明します。

動作環境
====================

Windows Subsystem for Linux, Mac OS, Ubuntu, Centos などの環境で以下を満たしている必要があります。

- openssl コマンドが利用できること
- pip が利用できること
- python 3.6 以上が利用できること
- git コマンドが利用できること
- docker コマンドが利用できること

docker コマンドのインストール
------------------------------
docker コマンドのインストールは、OSごとに以下に従ってください。docker のパッケージをインストールしても
dockerデーモンやコンテナを動作させる必要はないことに注意してください。
hive-builder は docker コマンドをクライアントとして利用するだけですので、
dockerデーモンやコンテナを動作させるためのVMは不要であれば、停止させておいてください。



Windows Subsystem for Linux, Ubuntu の場合
  インストールの手順は以下のページに従ってください。
  https://docs.docker.com/install/linux/docker-ce/ubuntu/

Centos の場合
  以下のコマンドを root で実行して docker-client をインストールしてください。

::

  yum install -y docker-client

Mac OS の場合
  インストールの手順は以下のページに従ってください。
  https://docs.docker.com/docker-for-mac/install/
  インストール後、一度は docker アプリケーションを起動しないと docker コマンドがインストールされません。
  デスクトップからdocker アプリケーションを起動して、docker コマンドが使えるようになったことを確認した後、
  ステータスバーの docker のアイコンをクリックして docker を終了しても構いません。
  hive-builder は docker コマンドを必要としますが、端末のdocker デーモンにアクセスしません。

インストール方法
====================

pyenv, virtualenv などでpython の仮想環境を作成し、環境を activate して、以下のコマンドでインストールしてください。

::

  pip install hive_builder

