=========================
プロキシ環境下での構築
=========================
hive-builder では、サーバの構築、コンテナのビルド時に yum, PyPi, dockerhub などのリポジトリにアクセスして、ソフトウェアをダウンロードしてセットアップします。
したがって、プロキシ環境下でインターネットへのアクセスがプロキシ経由に限定されている場合、各インストーラがプロキシ経由でインタネットにアクセスするように設定する必要があります。
ここでは、 hive-builder をプロキシ環境下で使用する際の使用方法について説明します。

.. warning::

   ビルドするステージのプロバイダが vagrant プロバイダ、kickstartプロバイダ、 prepared プロバイダを使用する場合のみプロキシ環境下で構築していただけます。
   AWS,GCP,Azure などのIaaS環境ではプロキシを利用いただけませんので、ご注意ください。


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

prepared プロバイダの場合
=========================

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

サービス内のプロセスへの環境変数の引き継ぎ
=============================================
サービス内から REST API 呼び出したり yum, npm, pip などのリポジトリへアクセスしたりする場合は
サービス内のプロキシ関係の環境変数が適切に設定されている必要があります。
各サービス内のプロキシ関係の環境変数は、それぞれ、 hive build-images の時はリポジトリサーバ、hive deploy-services 時は最初のコンテナ収容サーバの値が引き継がれます。
各サーバの/etc/environment でサービス内に必要な値も設定してください。特にサービス間の REST API アクセスなどについては
サービス名を no_proxy に設定しておく必要がありますので、注意してください。例えば、examples/pdnsのように pdnsadmin サービスから
powerdns サービスの REST API を http://powerdns:8081/ のようなURLで呼び出す場合、no_proxy には以下のように powerdns を追加する必要があります。

::


    NO_PROXY=powerdns,p-hive0.pdns,localhost,127.0.0.1
    no_proxy=powerdns,p-hive0.pdns,localhost,127.0.0.1
