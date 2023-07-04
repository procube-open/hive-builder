=========================
プロキシ環境下での構築
=========================
hive-builder では、サーバの構築、コンテナのビルド時に yum, PyPi, dockerhub などのリポジトリにアクセスして、ソフトウェアをダウンロードしてセットアップします。
したがって、プロキシ環境下でインターネットへのアクセスがプロキシ経由に限定されている場合、各インストーラがプロキシ経由でインタネットにアクセスするように設定する必要があります。
ここでは、 hive-builder をプロキシ環境下で使用する際の使用方法について説明します。

.. warning::

  プロキシサーバはmother マシン側からアクセス可能である必要があります。
  ただし、ビルドするステージのプロバイダが vagrant プロバイダ、kickstartプロバイダ、 prepared プロバイダを使用する場合はサーバ側のプロキシを使用して構築していただけます。

mother マシン側プロキシサーバの利用
========================================

mother マシン側のプロキシサーバを利用する場合、プロキシサーバのアドレスを http_proxy 変数に設定して頂く必要があります。
たとえば、 mother マシンで squid が起動していて、 3128番ポートでサービスを提供している場合、以下のように設定してください。

::


    hive set http_proxy localhost:3128

オフラインキャッシュサーバの利用
--------------------------------

上記の設定とともに弊社が提供しているオフラインキャッシュサーバを使用することで、以下の効果を得ることができます。

- yum, dockerhub, pipy, npmjs などからダウンロード・インストールしたソフトウェアのバージョンを将来に渡って固定できる
- yum のリポジトリから互換性のあるバージョンのパッケージが削除されてしまってもキャッシュに残っているものをインストールできる
- サーバからインターネットへのアクセスを禁じられている場合でもインストールできる

.. warning::
    ここで紹介するオフラインキャッシュサーバは dockerhub 以外の外部コンテナリポジトリはサポートしていません。
    dockerhub 以外の外部コンテナリポジトリを利用しているプロジェクトでは個々に記載されている方法は利用できませんので、注意してください。

以下に適用手順を示します。

0. hive-builderコードの修正
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

hive-builder のコードで build-images や  initialize-services でパブリックリポジトリにアクセスするものについては、image.roles にビルトインロール hive_trust_ca を追加してください。

1. ソースコードの取得
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下のコマンドでオフラインキャッシュサーバのソースコードを取得してください。git の混乱を避けるために mother 環境とは別のディレクトリに取得してください。
ただし、mother マシンに docker のサーバがインストールされている必要があります。

::


    git clone https://github.com/procube-open/offline-cache.git
    export HIVE_HIVE_CONTEXT_DIR=<hiveのコンテキストディレクトリのパス>
    docker-compose up -d

2. ビルド
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下のコマンドで全ビルドをかけてください。

::

    cd hiveのルートディレクトリ
    hive set stage private # or staging or production
    hive install-collection
    hive set http_proxy localhost:3128
    hive all

3. オフライン化
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下のコマンドでオフライン化を実行してください。このときはまだネットワークに繋がっている必要があります。
dockerhub のアカウントにログインするためのユーザIDとパスワードを用意してください。

::


    ansible-playbook -i squid,registry, -e dockerhub_login_user=dockerhubアカウント -e dockerhub_login_password=dockerhubパスワード offline.yml 


4. docker イメージの push
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

以下のコマンドでコンテナ収容サーバとリポジトリサーバにダウンロードされているコンテナイメージを擬似dockerhub に push してください。
このとき、間違って本物の dockerhub に push するのをさけるためにネットワークが切れていることが望ましいです。

::


    hive ssh
    docker image ls --format='docker push {{.Repository}}:{{.Tag}}' | grep -v :5000 | sh -x
    exit
    hive ssh -t コンテナ収容サーバ1号機 # separate_repository が false の場合は不要
    docker image ls --format='docker push {{.Repository}}:{{.Tag}}' | grep -v :5000 | sh -x
    exit

5. 再ビルド
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

この mother 環境があれば、オフラインの状態で全サーバをOSインストールから再構築( hive all )することができます。


vagrant プロバイダの場合
=========================

vagrant プロバイダを使用する場合は vagrant-proxyconf プラグインを使用することで、プロキシ環境下で hive-builder を利用することが可能です。
以下のコマンドで vagrant-proxyconf プラグインを mother マシンにインストールしてください。

::


    vagrant add vagrant-proxyconf

また、プロキシサーバの情報を mother 環境の環境変数に設定する必要があります。
設定すべき環境変数は、HTTP_PROXY、HTTPS_PROXY、NO_PROXYとそれぞれの小文字の変数です。
NO_PROXY には、リポジトリサーバのサーバ名と localhost, 127.0.0.1 を含めてください。
たとえば、プロキシサーバのURLが http://192.168.200.1:3128 の場合、 .bashrc などに以下のように記述してください。

::


    ### PROXY
    export HTTP_PROXY=http://192.168.200.1:3128
    export http_proxy=${HTTP_PROXY}
    export HTTPS_PROXY=${HTTP_PROXY}
    export https_proxy=${HTTPS_PROXY}
    export NO_PROXY=p-hive0.pdns,localhost,127.0.0.1
    export no_proxy=${NO_PROXY}
    ### PROXY END

上記の例ではリポジトリサーバのホスト名として p-hive0.pdns を指定しています。
このホスト名は、hive名が pdns で、private 環境で、サーバが1台（number_of_hosts=1）の場合のリポジトリサーバのホスト名です。
リポジトリサーバのホスト名は以下のとおり決定できます。

ステージプリフィックス + "hive" + サーバ台数から1を引いた数字 + "." + hive名

ステージプリフィックスは private 環境では "p-"、 staging 環境では "s-"、 production 環境では "" となります。

kickstart/prepared プロバイダの場合
========================================

kickstart プロバイダ、prepared プロバイダを使用する場合、setup-hosts フェーズの実行前に全てのサーバの /etc/environment でプロキシサーバの情報を環境変数に設定する必要があります。
設定すべき環境変数は、HTTP_PROXY、HTTPS_PROXY、NO_PROXYとそれぞれの小文字の変数です。
NO_PROXY には、リポジトリサーバのサーバ名と localhost, 127.0.0.1 を含めてください。
例えば、プロキシサーバのIPアドレスが 192.168.56.100 で 3128番ポートで待ち受けている場合、root ユーザで以下を実行します。

::


    # cat <<'_EOF' > /etc/environment
    HTTP_PROXY=http://192.168.56.100:3128
    http_proxy=http://192.168.56.100:3128
    HTTPS_PROXY=http://192.168.56.100:3128
    https_proxy=http://192.168.56.100:3128
    NO_PROXY=p-hive0.pdns,localhost,127.0.0.1
    no_proxy=p-hive0.pdns,localhost,127.0.0.1
    _EOF

上記の例ではリポジトリサーバのホスト名として p-hive0.pdns を指定しています。
このホスト名は、hive名が pdns で、private 環境で、サーバが1台（number_of_hosts=1）の場合のリポジトリサーバのホスト名です。
リポジトリサーバのホスト名は以下のとおり決定できます。

ステージプリフィックス + "hive" + サーバ台数から1を引いた数字 + "." + hive名

ステージプリフィックスは private 環境では "p-"、 staging 環境では "s-"、 production 環境では "" となります。

プロキシ環境の共通事項
==========================
以下にプロキシ環境での共通事項を説明します。

BUMP SSL のルートCA局を信頼
---------------------------------------
プロキシサーバが BUMP SSL を使用する場合、ダウンロード・インストールを実行するサーバおよびコンテナでCA局の証明書を信頼する必要があります。
その方法については  :doc:`cashare` を参照してください。

サービス内のプロセスへの環境変数の引き継ぎ
--------------------------------------------
サービス内から REST API 呼び出したり yum, npm, pip などのリポジトリへアクセスしたりする場合は
サービス内のプロキシ関係の環境変数が適切に設定されている必要があります。
各サービス内のプロキシ関係の環境変数は、それぞれ、 hive build-images の時はリポジトリサーバ、hive deploy-services 時は最初のコンテナ収容サーバの値が引き継がれます。
各サーバの/etc/environment でサービス内に必要な値も設定してください。特にサービス間の REST API アクセスなどについては
サービス名を no_proxy に設定しておく必要がありますので、注意してください。例えば、examples/pdnsのように pdnsadmin サービスから
powerdns サービスの REST API を http://powerdns:8081/ のようなURLで呼び出す場合、no_proxy には以下のように powerdns を追加する必要があります。
ただし、 hive set http_proxy を設定している場合は、 /etc/environment の設定は自動的に行われ、 no_proxy にはすべてのサービス名が登録されます。

::


    NO_PROXY=powerdns,p-hive0.pdns,localhost,127.0.0.1
    no_proxy=powerdns,p-hive0.pdns,localhost,127.0.0.1

.. warning::
    alpine linux のコンテナで最小構成の場合、 wget コマンドは no_proxy 環境変数が聞かない場合があります。
    この場合は apk add wget で GNU 版の wget をインストールすることで回避できます。
    参考： https://github.com/gliderlabs/docker-alpine/issues/259