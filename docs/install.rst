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
  以下のコマンドを root で実行して docker.io をインストールしてください。

::

  apt-get update
  apt-get install docker
  apt docker.io

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

インストール方法
====================

pyenv, virtualenv などでpython の仮想環境を作成し、環境を activate して、以下のコマンドでインストールしてください。

::

  pip install hive_builder

