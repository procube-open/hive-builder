====================
インストール
====================

ここでは、hive-builder を mother マシンにインストールする方法について説明します。

動作環境
====================

インターネット上の各種リポジトリに http, https でアクセスできる必要があります。
プロキシ経由でのみアクセスできる環境の場合、「プロキシ環境下での構築」を参照して事前準備を行ってください。

mother マシンの OS は、AlmaLinux, Windows Subsystem for Linux, Mac OS, Ubuntu などの環境で以下を満たしている必要があります。

- openssl コマンドが利用できること
- pip が利用できること
- Python 3.11 以上が利用できること
- git コマンドが利用できること
- docker コマンドが利用できること

インストールの手順を示します。
OSごとにインストール方法が異なる手順もありますので注意してください。

Step 1. python3, docker, sshpass コマンドのインストール
=============================================================
hive-builder では、python3, docker, sshpass コマンドが必要です。
python3 は Python 3.11 以上である必要があります。各OSごとの手順に従って
インストールしてください。

.. note::

    Python 3.9 / 3.10 は hive-builder の実行環境としてサポートしません。
    OS 標準の Python が 3.11 未満の場合は、Python 3.11 以上を別途インストールしてください。

1-A. RHEL 互換 OS の場合
----------------------------------------

Python 3.11 パッケージを提供する AlmaLinux 9 などでは、以下のコマンドを
root ユーザで実行して Python と Docker CLI をインストールしてください。

::

  dnf install -y dnf-plugins-core
  dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  dnf install -y python3.11 python3.11-pip docker-ce-cli

.. note::

    prepared プロバイダを使用し、その対象サーバ内に mother 環境を作成する場合は、
    docker コマンドをインストールする必要はありません。
    その場合はこのステップをスキップしてください。
    逆に CentOS 標準の docker-client パッケージがインストールされていると、
    hive-builder がインストールする docker-ce と競合して構築に失敗しますので、注意してください。

1-B. Windows の場合
--------------------------------------------
Windows 利用する場合は WSL(Windows Subsystem for Linux) 上で実行する必要があります。
WSL を公式サイト https://docs.microsoft.com/ja-jp/windows/wsl/install-win10 に従ってインストールしてください。
その後、Ubuntu 24.04 以降など Python 3.11 以上を提供する WSL 環境で、
以下のコマンドを root ユーザで実行して python3, docker, sshpass をインストールしてください。

::

  apt update
  apt upgrade
  apt install -y python3 python3-venv python3-pip openssl git docker.io sshpass

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

1-C. Mac OS の場合
------------------------------
Python と sshpass コマンドのインストールには Homebrew が必要です。Homebrewが未インストールの場合は
公式ページ https://brew.sh/index_ja に従って Homebrew をインストールしてください。

以下のコマンドで Python 3.11 と sshpass コマンドをインストールしてください。

::

  brew install python@3.11 sshpass

後述の仮想環境を作成するときは、``"$(brew --prefix python@3.11)/bin/python3.11"`` を使用してください。

docker コマンドのインストールの手順は以下のページに従ってください。
https://docs.docker.com/docker-for-mac/install/
インストール後、一度は docker アプリケーションを起動しないと docker コマンドがインストールされません。
デスクトップからdocker アプリケーションを起動して、docker コマンドが使えるようになったことを確認した後、
ステータスバーの docker のアイコンをクリックして docker を終了しても構いません。
hive-builder は docker コマンドを必要としますが、端末のdocker デーモンにアクセスしません。
docker desktop for mac は VM を起動しますので、リソースを消費します。
他に docker を必要とすることがなければ、落としておいてください。

1-D. Raspberry Pi OS の場合
------------------------------
Python 3.11 以上を提供する Bookworm 以降で、以下のコマンドを root ユーザで実行して
python3, docker, sshpass をインストールしてください。

::

  apt-get update
  apt-get upgrade
  apt install -y python3 python3-venv python3-pip openssl git sshpass
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
    部分では Python 3.11 以上を明示的に指定してください。例えば、AlmaLinux 9 の場合は
    python3.11 コマンドを使用してください。Mac OS の場合は、
    ``"$(brew --prefix python@3.11)/bin/python3.11"`` を使用してください。

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
