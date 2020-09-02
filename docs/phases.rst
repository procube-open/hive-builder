=========================
フェーズ
=========================
ここでは、 hive-builder のサイト構築機能をフェーズごとに説明します。

build-infra
=========================
ホストとネットワークを作成し、環境を構築します。

（未執筆）

プロバイダ
--------------------
build-infraフェーズでは、サーバを配備する基盤のプロバイダをステージオブジェクトの provider 属性に指定することで、様々なプロバイダを利用できます。
プロバイダとして有効な値は以下のとおりです。

============= ===============================================
プロバイダID  説明
============= ===============================================
vagrant       Vagrant for VirtualBox/libvirt on local machine
aws           Amazon Web Service
azure         Microsoft Azure（未実装）
gcp           Gooble Computing Platform
openstack     Some OpenStack Provider（未実装）
prepared      sshでアクセス可能なサーバ群
kickstart     OSが未インストールの物理サーバ
============= ===============================================

vagrant
^^^^^^^^^^^^^^
プロバイダIDにvagrant を指定した場合、vagrant のプロバイダは
libvirt, VirtualBox の順に試して、成功したものを使用します。

setup-hosts
=========================
ホストを設定します。setup-hosts は3個のPLAYに分割された27個の role からなります。
setup-hosts コマンドでは -T オプションで適用する role を限定できます。
以下にインストールされるソフトウェアとそれぞれの PLAY で実行される role のタスク内容について説明します。

インストールされるソフトウェア
-------------------------------

以下にインストールされるソフトウェアの一覧を示します。

..  list-table::
    :widths: 16 16 28 50
    :header-rows: 1

    * - パッケージ名
      - role
      - リポジトリ
      - 説明
    * - bridge-utils
      - base
      - CentOS yum repository
      - 仮想ブリッジ制御
    * - docker
      - docker
      - docker CE repository (1)
      - docker（ただし、 AWS EC2 の場合は Amazon Linux Repository からインストール）
    * - docker (Python)
      - docker
      - PyPI
      - docker python API
    * - docker-compose
      - docker-compose
      - PyPI
      - docker-compose コマンド
    * - drbd
      - drbd
      - procube-open/drbd-rpm(2)
      - drbd
    * - glibc-common
      - base
      - CentOS yum repository
      - ロケール情報（hive_localeが設定されているときのみ）
    * - iptables
      - iptalbes
      - CentOS yum repository
      - サーバファイアウォール（firewalldは削除します）
    * - libselinux-python
      - base
      - CentOS yum repository
      - SE Linux python API
    * - lsof
      - base
      - CentOS yum repository
      - ファイルディスクリプタ情報採取
    * - mariadb
      - zabbix
      - dockerhub
      - zabbix 用 DBMS
    * - NetworkManager
      - internal-network
      - CentOS yum repository
      - ネットワーク管理サービス
    * - pip
      - pip-venv
      - PyPI
      - Python パッケージマネージャ（pytho3-pip でインストールされたものをバージョンアップ）
    * - python3
      - pip-venv
      - CentOS yum repository
      - Python処理系
    * - python3-libs
      - pip-venv
      - CentOS yum repository
      - Python処理系ライブラリ
    * - python3-devel
      - pip-venv
      - CentOS yum repository
      - Python処理系開発ツール
    * - python3-pip
      - pip-venv
      - CentOS yum repository
      - Python パッケージマネージャ
    * - python3-setuptools
      - pip-venv
      - CentOS yum repository
      - Python パッケージマネージャ開発ツール
    * - python-dxf
      - pip-venv
      - PyPI
      - Docer registry API
    * - python-virtualenv
      - pip-venv
      - CentOS yum repository
      - Python 仮想環境構築ツール
    * - registry
      - registry
      - dockerhub
      - docker プライベートリポジトリ
    * - strace
      - base
      - CentOS yum repository
      - システムコールトレース
    * - sysstat
      - base
      - CentOS yum repository
      - 性能統計情報採取
    * - tcpdump
      - base
      - CentOS yum repository
      - パケットキャプチャ
    * - telnet
      - base
      - CentOS yum repository
      - telnetコマンド
    * - unzip
      - base
      - CentOS yum repository
      - 圧縮ファイル解凍
    * - vim
      - base
      - CentOS yum repository
      - テキストエディタ
    * - wget
      - base
      - CentOS yum repository
      - ファイルダウンロード
    * - zabbix
      - zabbix-agent
      - zabbix download site (3)
      - zabbix エージェント
    * - zabbix/zabbix-server-mysql
      - zabbix
      - dockerhub
      - zabbix server
    * - zabbix/zabbix-web-mysql
      - zabbix
      - dockerhub
      - zabbix web UI


(1) docker CE repository
https://download.docker.com/linux/centos/docker-ce.repo を yum リポジトリとして登録後、 yum でインストール。

(2) procube のオープンソース
https://github.com/procube-open/drbd9-rpm からカーネルのバージョンに従ってダウンロード。

- Amazon Linux の場合、9.0.22/drbd9-rpm-amzn2
- カーネルのバージョンが 3.10.0-1127 より小さい場合、 9.0.20/drbd9-rpm
- 上記以外の場合、9.0.22/drbd9-rpm

(3) zabbix repository
https://repo.zabbix.com/zabbix/3.0/rhel/7/x86_64/zabbix-release-3.0-1.el7.noarch.rpm
をインストール。

hive サーバ設定 PLAY
---------------------
最初に実行される "setup hive servers" という名称の PLAY では各サーバに共通の role を適用します。
以下に各 role について説明します。

base role
^^^^^^^^^^^^^^^^^^^
base role で実施するタスクについて以下に説明します。

yum の設定
+++++++++++++++++++++
hive_yum_url を指定されている場合は、 CentOS の Base リポジトリの yum のダウンロード元として指定します。
また、この場合、yum の fastestmirror の機能を無効にします。
CentOS のミラーサイトで近いものがわかっている場合は、指定してインストールにかかる時間を短縮できます。
AWS, Azure, GCP などの IaaS の場合は、デフォルトで近くのサイトが設定されている場合が多いので、
指定しないほうが良いでしょう。

パッケージのインストール
+++++++++++++++++++++++++
yumでCentOSの標準パッケージをインストールします。
インストールされるソフトウェアの節で示したパッケージのうち、 role 欄が base となっているものをインストールします。
sysstat については、インストール後、有効にします。

selinux の無効化
+++++++++++++++++++++++++

selinux を無効にします。

ホスト名の設定
+++++++++++++++++++++++++
ホスト名を設定します。プロバイダが AWS の場合は、再起動時にホスト名が巻き戻らないように /etc/cloud/cloud.cfg に preserve_hostname: true　の設定を追加します。

デフォルトタイムゾーンの設定
++++++++++++++++++++++++++++
hive_timezone が設定されている場合、その値を OSのデフォルトのタイムゾーンとして設定します。

デフォルトロケールの設定
+++++++++++++++++++++++++
hive_locale が設定されている場合、その値を OSのデフォルトのロケールとして設定します。この場合、ロケール設定のために glibc-common を追加でインストールします。

sshd の設定
+++++++++++++++++++++++++
sshdを以下の仕様で設定します。

- パスワードによるログインはできません
- チャレンジレスポンスによるログインはできません
- 送信元IPに対するDNS への逆引き問い合わせは行いません

NetworkManager へのパッチ
+++++++++++++++++++++++++
仮想マシンを起動する過程で、インタフェースのデバイスの生成前にサービスが起動してしまい起動に失敗する場合があり、これを回避するパッチをあてます。

::

    Bringing up interface eth0: Error: Connection activation failed: No suitable device found for this connection.

具体的には、NetworkManager-wait-online.service で実行される nm-online コマンドの -s オプションを削除します。

hostsfile role
^^^^^^^^^^^^^^^^^^^
サーバ間で通信する際に互いを hive0.pdns のような内部名で指定できるように /etc/hosts ファイルに登録します。

ntp-client role
^^^^^^^^^^^^^^^^^^^
hive_ntp_servers が指定されている場合、その値の NTP サーバから時刻を取得するように chronyd を設定します。

iptables role
^^^^^^^^^^^^^^^^^^^
iptables をインストールし、 firewalld を削除します。

pip-venv role
^^^^^^^^^^^^^^^^^^^
python, pip, virtualenv をインストールします。
インストールされるソフトウェアの節で示したパッケージのうち、 role 欄が pip-venv となっているものをインストールします。

addon role
^^^^^^^^^^^^^^^^^^^
サイト固有のインストールを実行します。サイトの roles に addon role が定義されていればそれを適用し、そうでなければ何もしません。

internal-network role
^^^^^^^^^^^^^^^^^^^^^^^
hive_internal_net_if が定義されている場合、その値でネットワークインタフェースを設定します。
このネットワークには hive_private_ip の値のIPアドレスが付与され、サーバ間のクラスタ通信に利用されます。
VPSサービス上の仮想マシンなどで、グローバルIPを持つインタフェースとは別に内部通信用のネットワークを追加できるが、OSには設定されていない状態で提供される場合に利用します。

users role
^^^^^^^^^^^^^^^^^^^^^^^
hive_users が指定されている場合、その値に従ってユーザを追加します。その場合、 hive_user_groups も指定しなければなりません。
また、ssh で root によるログインを拒否するよう設定します。

グループの定義
++++++++++++++++++++++
hive_user_groups にはグループ名をキーにしてグループオブジェクトを指定してください。
グループに属するユーザは sudo をパスワードなしで実行できるように設定します。
グループオブジェクトの属性は以下の通り。

============= ===============================================
属性名        説明
============= ===============================================
gid           グループの gid (1から2147483647までの整数)
============= ===============================================

ユーザの定義
++++++++++++++++++++++
hive_users にはユーザ名をキーにしてユーザオブジェクトを指定してください。
ユーザごとの SSH 設定で、公開鍵認証でログインできるように設定し、サーバの鍵を既知のホストとして登録します。
ユーザオブジェクトの属性は以下の通り。

============= ===============================================
属性名        説明
============= ===============================================
uid           ユーザの uid (1から2147483647までの整数)
group         ユーザの基本グループの gid
id_rsa_pub    ユーザのSSHログインのための公開鍵
============= ===============================================

strict-source-ip role
^^^^^^^^^^^^^^^^^^^^^^^
hive_ssh_source_ips が定義されている場合、sshd への接続の送信元IPアドレスを制限します。
hive_ssh_source_ips にはアクセスを許容するIPアドレスをリストで指定してください。
また、hive_safe_sshd_port が指定されている場合には、 sshd の受付ポート番号をその値に変更します。

tls-certificate role
^^^^^^^^^^^^^^^^^^^^^^^
docker API および registry API に使用するプライベート証明書を生成します。

docker role
^^^^^^^^^^^^^^^^^^^^^^^
docker をインストールします。

- リモートから docker APIを呼び出せるように設定します。
- docker デーモン間の通信を許可します。
- GCPの場合は、docker が仮想ネットワークを利用できるように IP forwarding を可能なように設定します。
- hive定義に internal_cidr 属性が定義されている場合は、その値の範囲からネットワークアドレスを割り当て docker ネットワークを設定します。

drbd role
^^^^^^^^^^^^^^^^^^^^^^^
drbd をインストールします。

- drbd 間の通信を許容します。
- セカンダリドライブに drbd resource pool を作成します。

docker-client role
^^^^^^^^^^^^^^^^^^^^^^^
docker python API をインストールし、 API クライアントの TLS 認証を設定し、 hive のユーティリティコマンドをインストールします。

follow-swarm-service role
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
swarm 拡張機能をインストールします。

docker-client-proxy role
^^^^^^^^^^^^^^^^^^^^^^^^^^^
プロキシに対応するように docker を設定します。HTTP_PROXY 環境変数が設定されている場合のみに適用されます。

zabbix-agent role
^^^^^^^^^^^^^^^^^^^^^^^
zabbix-agent をインストールします。

リポジトリサーバ設定 PLAY
--------------------------
二番目に実行される "setup repository and zabbix" という名称の PLAY ではリポジトリサーバに共通の role を適用します。
以下に各 role について説明します。

docker-compose role
^^^^^^^^^^^^^^^^^^^^^^^
docker-compose をインストールします。

zabbix role
^^^^^^^^^^^^^^^^^^^^^^^
zabbix コンテナをインストールします。

registry role
^^^^^^^^^^^^^^^^^^^^^^^
registry コンテナをインストールします。

backup-tools role
^^^^^^^^^^^^^^^^^^^^^^^
バックアップツールをインストールします。
サービス定義にしたがって、バックアップ/リストア用のシェルスクリプトを生成し、夜間バッチでバックアップを実行するように設定します。

rsyslogd role
^^^^^^^^^^^^^^^^^^^^^^^
マイクロサービス型のコンテナのログを受信して記録するように rsyslogd を設定します。

クラスタ構築 PLAY
---------------------
三番目に実行される "build cluster" という名称の PLAY ではコンテナ収容サーバ間のクラスタ連携を設定する role を適用します。
以下に各 role について説明します。

swarm role
^^^^^^^^^^^^^^^^^^^^^^^
docker swarm クラスタを設定します。

- hive定義に internal_cidr 属性が定義されている場合は、その値の範囲からネットワークアドレスを割り当て docker_gwbridge ネットワークを設定します。
- hive定義に internal_cidr 属性が定義されている場合は、その値の範囲からネットワークアドレスを割り当て ingress ネットワークを設定します。
- docker swarm ノードとして初期化し、クラスタとして結合します。
- サーバが属する ansible グループ名をノードのラベルとして設定します。


build-images
=========================
コンテナイメージをビルドします。サービス定義で image 属性の下にfrom属性を指定した場合にビルドの対象となります。

再実行
------------------------------

build-images フェーズを複数回行う場合、前回のビルドに利用したコンテナを再利用することでビルドにかかる時間を短縮しています。
このため、image 属性の配下の属性を変更して build-images をやり直しても反映されません。
また、roles に指定したタスクについて内容が減少する方向の変更が行われた場合、反映されません。
たとえば、ファイルのインストール先が変更された場合や、設定ファイルの行追加をやめた場合などがこれに該当します。
このような場合は、以下の手順でビルド用のコンテナを削除してから build-images をやり直してください。

::

    hive ssh
    docker rm build_image_サービス名
    exit


デバッグ
------------------------------

build-images でエラーが発生し、-v オプションで詳細ログをみても原因がわからない場合、以下の手順でビルド用コンテナにログインして
build-images で実行する内容をコマンドで実行してみることでデバッグすることができます。

1. リポジトリサーバへのログイン
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下のコマンドでリポジトリサーバにログインしてください。

::

    hive ssh

2. ビルド用のコンテナの起動
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下のコマンドでビルド用コンテナが起動しているかを確かめてください。

::

    CN=build_image_サービス名
    docker ps -f name=$CN -a

この結果 STATUS 列に Exited が表示される場合は次のコマンドでコンテナを起動してください。

::

    docker start $CN

3. ビルド用のコンテナへの起動
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下のコマンドでビルド用コンテナにログインしてデバッグしてください。

::

    docker exec -it $CN /bin/bash

ただし、alpineベースのコンテナの場合、/bin/bash が入っていない場合があります。
その場合、"stat /bin/bash: no such file or directory" というエラーが表示されますので、 /bin/bash のかわりに /bin/ash を利用してください。

作業が終わりましたら、exit を2回実行して mother 環境に戻ってください。

外部リポジトリへのログイン
------------------------------

イメージをダウンロードする際に外部リポジトリを利用することができます。
外部リポジトリにアクセスする際にログインが必要な場合、 hive_ext_repositories にログインに必要な情報を設定してください。
hive_ext_repositories は dockerログインオブジェクトの配列です。 dockerログインオブジェクトは以下の属性を持ちます。

============= ==============================================================================================
属性名        説明
============= ==============================================================================================
repository    リポジトリ。FQDN:ポート番号の形式で指定してください。省略すると dockerhub にログインします。
login_user    ユーザID
password      パスワード
email         メールアドレス（省略可能）
============= ==============================================================================================


build-networks
=========================
内部ネットワークを構築します。

（未執筆）

build-volumes
=========================
ボリュームを構築します。

（未執筆）

deploy-services
=========================
サービスを配備します。

（未執筆）


外部リポジトリへのログイン
------------------------------

イメージをダウンロードする際に外部リポジトリを利用することができます。
外部リポジトリにアクセスする際にログインが必要な場合、build-images の場合と同様に hive_ext_repositories にログインに必要な情報を設定してください。


initialize-services
=========================
サービスを初期化します。

（未執筆）

