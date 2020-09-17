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

リポジトリの掃除
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
build-images フェーズを実行すると新しいコンテナイメージが登録されますが、
古いコンテナイメージはリポジトリに残ったままになります。
ディスク残量が少なくなってきた場合には、  hive ssh コマンドでリポジトリサーバに
ログインし、以下のコマンドを実行してリポジトリを掃除してください。

::

  docker exec -it registry registry garbage-collect -m /etc/docker/registry/config.yml


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
通常は、このデフォルトのネットワークで十分ですので、
特にインベントリにネットワークを定義する必要はありません。

ネットワークの配備は build-networks フェーズで行われます。以下のコマンドで
実行できます。

::

  hive build-networks

サービスのデプロイ
------------------------------
ここでは、 docker swarm サービスをデプロイします。
デプロイ時ににサイト固有のパラメータを渡すために、起動時にコマンドラインを指定したり、
環境変数にパラメータを指定したりするのが一般的です。
また、デプロイしたサービスを外部に対して公開する場合の
ポート番号を指定する必要があります。

例えば、サンプルの powerdns サービスでは、以下の指定で、サイト固有パラメータ
を指定しています。

::

    environment:
      MYSQL_PASSWORD: "{{db_password}}"
      MYSQL_HOST: pdnsdb
      MYSQL_DNSSEC: "yes"
      PDNSCONF_DEFAULT_SOA_NAME: "{{ (groups['first_hive'] | intersect(groups[hive_stage]) | first) + '.' + domain }}"
    command:
    - "--api=yes"
    - "--api-key={{db_password}}"
    - "--webserver=yes"
    - "--webserver-address=0.0.0.0"
    - "--webserver-allow-from=0.0.0.0/0"
    ports:
    - "53:53/tcp"
    - "8081"
    - "53:53/udp"

環境変数(environments の配下)で DBサーバへの接続パラメータを渡しています。ここでは、DBにアクセスする
ためのパスワード（MYSQL_PASSWOWRD）は動的に生成したものを ansible のテンプレート機能で展開しています。
また、コマンド引数(command の配下)でPOWERDNS の API を有効化しています。
さらに ports でサービスの公開仕様を定義しています。この例では udp/tcp DNSサービスを 53 番ポートで公開し、
APIサービスのポート 8081 を自動的に割当られるポート番号で公開しています。

ただし、 hive は 10000 以上の番号は外部に公開しないようになっています。
IaaS のファイアウォールおよび iptables （未実装）で外部からのアクセスを
遮断しています。上記であれば、APIサービスは
内部からのみアクセスでき、外部には公開されません。

このようにして、定義されたサービスを以下のコマンドで起動することができます。

::

  hive deploy-services

サイトの初期データのロード
------------------------------

複数のマイクロサービスが連携して機能を実装する場合、build-images や deploy-services では
初期データをロードできない場合があります。たとえば、サンプルの powerdns では、
ゾーンやAレコードをAPIから登録しようとすると、 Power DNS とバックエンドの
データベースの両方を稼働させる必要があります。

hive では、 initialize-services フェーズですべてのサービスを稼働させた状態で
初期データを登録できます。 initialize-services フェーズで初期データを登録するためには、
サービス定義の initialize_roles プロパティにデータを初期化するためのrole を指定し、
その role を定義する必要があります。例えば、サンプルでは Power DNS のモジュールを使って
初期データを登録しています。サービス定義で initialize_roles にpowerdns-init を
指定しており、 roles/powerdns-init/tasks/main.yml の内容は以下のとおりです。

::

    ---
    - name: get my public IP
      ipify_facts:
      delegate_to: "{{item}}"
      delegate_facts: True
      when: hive_provider not in ['vagrant']
      loop: "{{ groups['hives'] | intersect(groups[hive_stage]) }}"
    - name: set published
      set_fact:
        published_ip: "{% if hive_provider not in ['vagrant'] %}{{ hostvars['p-hive0.pdns'].hive_private_ip }}{% else %}{{ hostvars['p-hive0.pdns'].ansible_facts.ipify_public_ip }}{% endif %}"
      delegate_to: "{{item}}"
      delegate_facts: True
      loop: "{{ groups['hives'] | intersect(groups[hive_stage]) }}"
    - name: install pip
      apk:
        name: py-pip
    - name: install requests module
      pip:
        name: requests
    - name: wait for powerdns api available
      wait_for:
        host: localhost
        port: 8081
    - name: add zone
      powerdns_zone:
        name: "{{ hive_name }}.{{ domain }}."
        nameservers: "{{ groups['hives'] | intersect(groups[hive_stage]) | map('regex_replace', '^(.*)$', '\\1.' + domain +'.' ) | list }}"
        kind: native
        state: present
        pdns_api_key: "{{ hostvars['powerdns'].db_password }}"
    - name: add records for hives
      powerdns_record:
        name: "{{ item + '.' + domain + '.' }}"
        zone: "{{ hive_name }}.{{ domain }}"
        type: A
        content: "{{ hostvars[item].published_ip }}"
        ttl: 3600
        pdns_api_key: "{{ hostvars['powerdns'].db_password }}"
      loop: "{{ groups['hives'] | intersect(groups[hive_stage]) }}"
    - name: add records for web services
      powerdns_record:
        name: "{{ item + '.' }}"
        zone: "{{ hive_name }}.{{ domain }}"
        type: LUA
        content: A "ifportup(80, {'{{ groups['hives'] | intersect(groups[hive_stage]) | map('extract', hostvars, ['published_ip']) | join(delimiter)}}'})"
        ttl: 20
        pdns_api_key: "{{ hostvars['powerdns'].db_password }}"
      loop: "{{ groups['services'] | intersect(groups[hive_stage]) | map('extract', hostvars, 'hive_labels') | select('defined') | map(attribute='published_fqdn') | select('defined') | list }}"


最初の2つのタスクで各コンテナ収容サーバ(グループ名= hives)のグローバルIPを調べて、
host変数の published_ip に設定しています。この role は powerdns サービスの
initialize_roles を定義されているので、対象が powerdns サービスのコンテナとなることに
注意してください。最初の2つのタスクではコンテナ収容サーバに対象を切り替えるために
delegate_to, delegate_facts を使用しています。

続くタスクでゾーンとレコードを登録しています。
ここで使用している powerdns_zone モジュールと powerdns_record モジュールは ansible の
オフィシャルモジュールではありません。
hive ではlibディレクトリの下に置くことでカスタムモジュールを使用できます。
サンプルでは、 github の https://github.com/Nosmoht/ansible-module-powerdns で公開されているモジュールを
ダウンロードして、lib の下に配置しています。
また、このモジュールは pdns_port プロパティにAPIのポート番号を指定する必要がありますが、
サンプルでは、 hive-builder が自動的に割り当てたポート番号を powerdns サービスのホスト変数 hive_ports からポート番号 8081 を公開しているものを検索し、
公開されるポート番号を取得しています。

サービスのログの閲覧
------------------------------

サービスのログはデフォルト(サービス定義で logging 属性を指定しなければ)ではリポジトリサーバに収集されます。
サービスのログを採取するためには

::

  hive ssh

コマンドでリポジトリサーバにログインし /var/log/services/サービス名 のファイルを参照してください。

スタンドアロン型サービスのログ収集
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
スタンドアロン型サービスではサービス自身のログは initプロセス（=systemd）の出力となり、何も出力されません。
スタンドアロン型サービスのログをリポジトリサーバに収集する場合は、image のビルド時にビルトイン role の
hive-syslog を指定してください。

外部リポジトリへのログイン
------------------------------

build-images、および deploy-services フェーズでイメージをダウンロードする際に外部リポジトリを利用することができます。
外部リポジトリにアクセスする際にログインが必要な場合、 hive_ext_repositories にログインに必要な情報を設定してください。
例えば、dockerhub にアクセスする場合、インベントリ（例えば、inventory/group_vars/all.yml）に以下のように設定してください。

::

  credentials: "{{ lookup('file', lookup('env', 'HOME') + '/.hive/credentials.yml') | from_yaml }}"
  hive_ext_repositories:
    - login_user: "{{ credentials.dockerhub_login_user}}"
      password: "{{ credentials.dockerhub_login_password}}"

上記では、ログインユーザとパスワードを秘密情報をまとめたファイル ~/.hive/credentials.yml から読み込んでます。
