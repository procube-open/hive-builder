====================
インストール
====================

ここでは、hive-builder を mother マシンにインストールする方法について説明します。

動作環境
====================

インターネット上の各種リポジトリに http, https でアクセスできる必要があります。
プロキシ経由でのみアクセスできる環境の場合、「プロキシ環境下での構築」を参照して事前準備を行ってください。

mother マシンの OS は、CentOS, Windows Subsystem for Linux, Mac OS, Ubuntu などの環境で以下を満たしている必要があります。

- openssl コマンドが利用できること
- pip が利用できること
- python 3.8 以上が利用できること
- git コマンドが利用できること
- docker コマンドが利用できること

インストールの手順を示します。
OSごとにインストール方法が異なる手順もありますので注意してください。

Step 1. python3, docker, sshpass コマンドのインストール
=============================================================
hive-builder では、python3, docker, sshpass コマンドが必要です。
python3 は python 3.8 以上である必要があります。各OSごとの手順に従って
インストールしてください。

.. note::

    Cent OS でサポートしているのは CentOS 7/8 です。CentOS 6 は非サポートです。

1-A. Centos 7 の場合
----------------------------------------

以下のコマンドを root ユーザで実行して python3.8, docker コマンドをインストールしてください。
Centos 7 の場合は sshpass コマンドは不要です。

::

  yum install -y centos-release-scl
  yum install -y rh-python38 which docker-client
  scl enable rh-python38 bash

1-B. Centos 8 の場合
----------------------------------------

以下のコマンドを root ユーザで実行して python3.9, docker コマンドをインストールしてください。
Centos 8 の場合は sshpass コマンドは不要です。

::

  yum config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  yum install -y python39 docker-ce-cli

.. note::

    prepared プロバイダを使用し、その対象サーバ内に mother 環境を作成する場合は、
    docker コマンドをインストールする必要はありません。
    その場合はこのステップをスキップしてください。
    逆に CentOS 標準の docker-client パッケージがインストールされていると、
    hive-builder がインストールする docker-ce と競合して構築に失敗しますので、注意してください。

1-C. Windows の場合
--------------------------------------------
Windows 利用する場合は WSL(Windows Subsystem for Linux) 上で実行する必要があります。
WSL を公式サイト https://docs.microsoft.com/ja-jp/windows/wsl/install-win10 に従ってインストールしてください。
その後、以下のコマンドを WSL の root ユーザで実行して python3, docker, sshpass  をインストールしてください。

::

  apt update
  apt upgrade
  apt install -y libffi-dev libbz2-dev liblzma-dev libsqlite3-dev libncurses5-dev libgdbm-dev zlib1g-dev libreadline-dev libssl-dev tk-dev build-essential libncursesw5-dev libc6-dev openssl git
  wget https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz
  tar -zxf Python-3.9.5.tgz
  cd Python-3.9.5
  ./configure --enable-optimizations
  make install
  apt install docker sshpass
  apt docker.io

ansible でサーバへのログインに使用する ssh 鍵のファイルについて、
owner は自分で modeは 0400 となっていて、他人から参照できない状態である必要があります。
Windows 10 WSL 環境で、例えば、 /mnt/c/Users/lucy のように
Windows から見えるディレクトリに hive のルートディレクトリを作成すると、ssh 鍵の
mode が 0777 となってしまい、 ssh ログイン時にエラーになります。その場合、
context_dir を ~/hive-context などに設定することで回避できます。
以下のコマンドを実行してください。

::

  mkdir -p ~/.hive/private
  hive set context_dir ~/.hive/private

この操作はステージごとに必要であり、context_dir はステージごとに異なる
必要があります。

1-D. Mac OS の場合
------------------------------
Python と sshpass コマンドのインストールには Homebrew が必要です。Homebrewが未インストールの場合は
公式ページ https://brew.sh/index_ja に従って Homebrew をインストールしてください。

以下のコマンドで Python3.9 と sshpass コマンドをインストールしてください。

::

  brew install python@3.9 sshpass

後述の仮想環境を作成するときの python3 コマンドには /usr/local/Cellar/python@3.9/3.9.5/bin/python3.9 を使用してください。

docker コマンドのインストールの手順は以下のページに従ってください。
https://docs.docker.com/docker-for-mac/install/
インストール後、一度は docker アプリケーションを起動しないと docker コマンドがインストールされません。
デスクトップからdocker アプリケーションを起動して、docker コマンドが使えるようになったことを確認した後、
ステータスバーの docker のアイコンをクリックして docker を終了しても構いません。
hive-builder は docker コマンドを必要としますが、端末のdocker デーモンにアクセスしません。
docker desktop for mac は VM を起動しますので、リソースを消費します。
他に docker を必要とすることがなければ、落としておいてください。

1-E. raspbian の場合
------------------------------
以下のコマンドを root ユーザで実行して python3, docker, sshpass  をインストールしてください。

::

  apt-get update
  apt-get upgrade
  apt install -y libffi-dev libbz2-dev liblzma-dev libsqlite3-dev libncurses5-dev libgdbm-dev zlib1g-dev libreadline-dev libssl-dev tk-dev build-essential libncursesw5-dev libc6-dev openssl git sshpass
  wget https://www.python.org/ftp/python/3.9.5/Python-3.9.5.tgz
  tar -zxf Python-3.9.5.tgz
  cd Python-3.9.5
  ./configure --enable-optimizations
  make install
  curl -sSL https://get.docker.com | sh
  usermod -aG docker pi


Step 2. vagrant のインストール
==========================================
vagrant プロバイダを使用する場合は 次の :doc:`vagrant` を参照して vagrant をインストールしてください。

.. note::

    raspbian では vagrant プロバイダは利用できません。
    vagrant プロバイダを使用しない場合はこのステップは不要ですので、スキップしてください。


Step 3. 仮想環境の構築
==========================================
hive-builder をインストールするための仮想環境を作成したほうが良いでしょう。
仮想環境の作成は pyenv, conda, pipenv など、他のツールを用いることもできますし、
もともと hive-builder 専用に用意されたOSであれば、仮想環境を作成せずに利用することも可能です。
以下に Python3 の venv モジュールを用いて作成する場合のコマンド例を示します。

::

    cd ~
    python3 -m venv hive
    echo source ~/hive/bin/activate >> .bashrc
    source ~/hive/bin/activate
    pip install --upgrade pip wheel

.. note::

    python3 の複数のバージョンがインストールされている場合は、上記の「python3」の
    部分では明示的に最新バージョンを指定してください。例えば、 CentOS 8 の場合は、
    python39 コマンドを使用してください。Mac OS の場合は、
    /usr/local/Cellar/python@3.9/3.9.5/bin/python3.9 を使用してください。

Step 4. hive-builder のインストール
==========================================
以下のコマンドでインストールしてください。

::

  pip install hive_builder


Step 5. コレクションのインストール
==========================================
hive-builder をインストールすると、 ansible-core がインストールされます。
続いて、 hive-builder が使用する ansible コレクション, ansible ロールを
インストールする必要があります。
ansible コレクション, ansible ロールはプロジェクト/ステージの
コンテキストディレクトリにインストールされるため、プロエジェクトの
ディレクトリを作成し、hive set stage コマンドでステージを設定後に
以下のコマンドを実行してansible コレクション, ansible ロールをインストールしてください。

::

  hive install-collection

Step 6. プロキシ用の環境変数の設定
==========================================
コンテナ収容サーバ、リポジトリサーバが、 yum, docker, pip, npm などインターネット上の
リポジトリアクセスするときにプロキシ経由でアクセスする必要がある場合は、
setup-hosts を実行前に各サーバにプロキシ用の設定を行う必要があります。
その場合は、:doc:`proxy` を参照して設定してください。

.. note::

    サーバから直接リポジトリにアクセスできる場合は、
    このステップは不要ですので、スキップしてください。
