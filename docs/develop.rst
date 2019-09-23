=========================
hive 構築ガイド
=========================
ここでは、hive のサイトを構築する方法を説明します。

マザーマシンの構築
=========================
hive-builder でサイトを構築するために最初に
マザーマシンを構築する必要があります。
マザーマシンの OS は Linux か Mac OS である必要があります。
Windows 10 であれば、Windows Subsystem for Linux を利用していただけます。
マザーマシンにはCPU1個、メモリ1GB、ディスク3GB程度のリソースがあれば十分です。
そのようなマシンを用意し、 :doc:`install` を参照して、 hive-builder を
インストールしてください。

プロジェクトディレクトリの作成
===============================
マザーマシンにプロジェクトディレクトリを作成してください。
サンプルの pdns プロジェクトを例に ``hive`` のディレクトリ構造を説明します。

.. blockdiag::

    blockdiag {
      pdns -> initialize-services.yml
      pdns -> inventory -> group_vars -> all.yml
              group_vars -> servers.yml
              group_vars -> services.yml
          inventory -> hive.yml
          inventory -> powerdns.yml
      pdns -> lib -> powerdns_record.py
          lib -> powerdns_zone.py
      pdns -> roles -> certbot-runner
          roles -> powerdns
          roles -> powerdns-admin
          roles -> powerdns-initdb
          roles -> proxy-configure
    }

..  list-table::
    :widths: 22 8 50
    :header-rows: 1

    * - ディレクトリ/ファイル名
      - 必須
      - 説明
    * - pdns
      - 必須
      - プロジェクトのルートディレクトリ
    * - initialize-services.yml
      - 任意
      - サービスを初期化する playbook
    * - inventory
      - 必須
      - インベントリを保持するディレクトリ
    * - group_vars
      - 任意
      - リソースグループごとの変数を保持するディレクトリ
    * - all.yml
      - 任意
      - すべてのリソースに共通の変数を保持するディレクトリ
    * - servers.yml
      - 任意
      - すべてのサーバに共通の変数を保持するディレクトリ
    * - services.yml
      - 任意
      - すべてのサービスに共通の変数を保持するディレクトリ
    * - hive.yml
      - 必須
      - hive定義（ファイル名は任意）
    * - powerdns.yml
      - 必須
      - サービス定義（ファイル名は任意）
    * - lib
      - 任意
      - ansible モジュールを保持するディレクトリ
    * - powerdns_record.py
      - 必須
      - powerdns のレコードをプロビジョニングするモジュール
    * - powerdns_zone.py
      - 必須
      - powerdns のゾーンをプロビジョニングするモジュール
    * - roles
      - 任意
      - コンテナイメージの構築時に呼び出す role を保持するディレクトリ
    * - certbot-runner
      - 任意
      - サーバ証明書を自動的に取得する certbot-runner サービスのコンテナイメージを構築する role です
    * - powerdns
      - 任意
      - 権威DNSサーバである powerdns サービスのコンテナイメージを構築する role です
    * - powerdns-admin
      - 任意
      - 権威DNSサーバのWebコンソールである powerdns-admin サービスのコンテナイメージを構築する role です
    * - powerdns-initdb
      - 任意
      - 権威DNSサーバのデータベースを初期化する role です
    * - proxy-configure
      - 任意
      - リバースプロキシの構成を自動的に行う proxy-configure サービスのコンテナイメージを構築する role です

プロジェクトを新規に開発する際は、まず、上記の必須となっているディレクトリとファイルを作成する必要があります。

role のディレクトリ構造
------------------------
roles 配下にはrole ごとのディレクトリを作成する必要があります。
role の記述方法については `ansible の公式ドキュメント <https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html>`_ を参照してください。
たとえば、pdnsプロジェクトのpowerdns ロールでは以下のディレクトリ構造を持っています。

.. blockdiag::

    blockdiag {
        powerdns -> files -> docker-entrypoint.sh
        powerdns -> tasks -> main.yml
    }

powerdns/tasks/main.yml の内容は以下の通りです。

::

  ---
  - name: install powerdns
    apk:
      name:
        - pdns
        - pdns-backend-mysql
        - pdns-backend-lua
      state: present
      repository:
      - http://dl-cdn.alpinelinux.org/alpine/edge/community/
      - http://dl-cdn.alpinelinux.org/alpine/edge/main/
      update_cache: yes
  - name: install endpoint shell
    copy: src=docker-entrypoint.sh dest=/ mode=0775
  - name: "patch default config file - set default"
    lineinfile:
      path: /etc/pdns/pdns.conf
      regexp: "^(# *)?{{item.key}}=.*"
      line: "{{ item.key }}={{ item.value }}"
    with_items:
      - key: daemon
        value: "no"
      - key: guardian
        value: "no"
      - key: launch
        value: gmysql
      - key: chroot
        value: ""
  - name: "patch default config file - comment out"
    lineinfile:
      path: /etc/pdns/pdns.conf
      regexp: "^(# *)?{{ item }}=.*"
      line: "# {{ item }}="
    with_items:
      - use-logfile
      - wildcards

上記の playbook で以下のことを実行しています。

- PowerDNS のソフトウェアのインストール
- エントリポイントのシェルスクリプトを追加
- 設定ファイル /etc/pdns/pdns.conf を編集

基盤の構築
=========================
基盤を構築するためには、inventory/hive.yml を作成し、hive 定義を記述する必要があります。
hive 定義の記述方法については :doc:`inventory` を参照してください。
最初は private ステージを作成することが推奨されます。
作業をするパソコンのメモリに余裕があれば、 vagrant プロバイダで 4G 以上のメモリをもった
サーバを構築するのが良いでしょう。

基盤のテスト
---------------------------

hive コマンドで build-infra フェーズと setup-hosts フェーズがエラーなく成功するように
なれば、hive 定義は完成と言えるでしょう。以下のコマンドがエラーなく成功するまで、
hive定義の内容を調整してください。

::

  hive build-infra
  hive setup-hosts

サービスの開発
=========================

hive の中でサービスを起動するためにはサービスをインベントリに定義する必要があります。

ほとんどのサービス（＝ docker コンテナ）は以下の5段階の構築が必要です。

- コンテナイメージのビルド（コンテナへのソフトウェアのインストール）
- ボリュームのマウント
- ネットワークの配備
- サービスのデプロイ（サイト固有パラメータの設定を含む）
- サイトの初期データのロード

以下に順に説明します。

コンテナイメージのビルド
---------------------------

docker では、ソフトウェアのインストールが終わったコンテナのイメージを
リポジトリに登録しておき、これをダウンロードして利用するのがベストプラクティスとなります。
dockerhub などの外部のリポジトリに登録されているコンテナイメージをそのまま
利用する場合は、 hive の中でコンテナイメージを作成する必要はありませんが、
プロジェクト固有のカスタマイズが入ったサービスを開発する場合は、 hive の中で
コンテナイメージをビルドし、プロジェクト内部のリポジトリに登録する必要があります。

hive ではコンテナイメージの登録とプロジェクト内部のリポジトリへの登録を
build-images フェーズで実行できます。このビルドを行うには、サービス定義の image 属性に
from 属性と roles 属性を持ったビルド定義オブジェクトを設定する必要があります。
image 属性にイメージタグの文字列が設定されている場合は、build-images フェーズの対象となりません。

以下のコマンドで、build-images を実行し、コンテナイメージを登録してください。

::

  hive build-images

サービス定義の from 属性、roles 属性の記述方法については :doc:`inventory` を参照してください。

ボリュームのマウント
----------------------
docker の通常のボリュームに加えて drbd でサーバ間で複製同期するボリュームを利用できます。
その仕組みについては、:doc:`overview` の高可用性の節を参照してください。
サーバ間で複製同期しているため、サービスがどのサーバで起動しても同じ内容の
ボリュームが見えます。
この複製同期するボリュームを使用する場合は、サービス定義のvolumes 属性に指定する
ボリューム定義で drbd 属性を指定してください。
drbd 属性の設定方法については :doc:`inventory` を参照してください。

ボリュームの作成は build-volume フェーズで行われます。以下のコマンドで
ボリュームを作成できます。

::

  hive build-volumes

ネットワークの配備
----------------------
hive は docker swarm の overlay ドライバを使用し、クラスタに参加するすべてのサービスが
接続するデフォルトのネットワークを1個作成します。このネットワークの名前は
hive_default_network です。
各サービスはこのネットワークを経由して他のサービスにアクセスすることができます。
たとえば、サンプルの powerdns のサービスはデータベースサービス pdnsdb に
その名前でアクセスします。docker の内部DNSが pdnsdb の hive_default_network
上のアドレスを解決し、PowerDNS のサーバはデータベースにアクセスできます。
この仕組みは powerdns サービスと pdnsdb サービスがどのホストで動作しているかと
関係なく動作します。

ネットワークの配備は build-networks フェーズで行われます。以下のコマンドで
実行できます。

::

  hive build-networks

サービスのデプロイ
------------------------------
docker コンテナにサイト固有のパラメータを渡す場合は、コンテナ起動時に環境変数に
パラメータを指定して渡すのが一般的です。

hive ではサービス定義の environment 属性で環境変数の値を指定できます。

（未執筆）

サイトの初期データのロード
------------------------------

（未執筆）

運用保守
=============================
（未執筆）

リポジトリの掃除
-----------------------------
build-images フェーズを実行すると新しいコンテナイメージが登録されますが、
古いコンテナイメージはリポジトリに残ったままになります。
ディスク残量が少なくなってきた場合には、以下のコマンドをリポジトリサーバで実行して
リポジトリを掃除してください。

::

  docker exec -it registry_registry_server_1 registry garbage-collect /etc/docker/registry/config.yml -m