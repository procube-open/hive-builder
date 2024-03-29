=========================
サンプルを構築してみる
=========================

ここでは、 hive のソースコードの github に登録されているサンプルを使って、AWS上に GSLB 機能を持つ権威DNSサーバを構築してみます。

前提条件と準備
=========================

サンプルを構築するためには IaaS のAPIに対する鍵を取得する必要があります。また、ドメインを保有していれば実際にサブドメインを管理できます。

IaaS
------------------------
このサンプルを実行するためには AWS EC2, VPC にアクセスできるユーザのAPI鍵が必要です。
 :doc:`aws` に従って IAM でビルド用のユーザを作成し、そのAPI鍵を取得してください。

サブドメイン委譲
------------------------
ここで構築する権威DNSサーバを保有するドメインに登録して、サブドメインの管理を委譲することで新しいサブドメインを管理できます。
これにより、GSLBとして動作させるとともに、Lets Encryptでサーバ証明書を自動的に取得させることができます。
このサンプルでは ddclient で自身のアドレスをDNSに登録し、自動的にサブドメインの委譲を受けれるようになっています。
そのコードを利用するためには Google Domains など DDNS をサポートするDNSサーバでドメインを管理している必要があります。
以下では Google Domains で管理されている前提で手順を説明します。

サンプルソースコードの取得
================================
サンプルソースコードをgithub からダウンロードします。

::

  svn export https://github.com/procube-open/hive-builder/branches/master/examples/pdns
  cd pdns

svn コマンドを使用しない場合は、 hive-builder のソースコード全体を clone してください。

::

  git clone https://github.com/procube-open/hive-builder
  cd hive-builder/examples/pdns

zipファイルをダウンロードした場合、解凍してください。その後、サンプルのディレクトリを部分的に切り取ってください。

::

  tar xvzf hive-builder-master.zip
  cp -r hive-builder/examples/pdns . || cd pdns
  

仮想環境の activate
=========================
hive 用の仮想環境を作成し、activate します。仮想環境ツールが pyenv で python 3.9.5 がインストールされている場合、以下のコマンドで activate できます。

::

  pyenv virtualenv 3.9.5 hive
  pyenv local hive

virtualenv, pipenv, conda を利用されている場合は、それぞれの方法で仮想環境を activate してください。

hive-builder のインストール
===============================
仮想環境が activate されている状態で以下のコマンドで hive-builder をインストールしてください。詳しくは :doc:`install` を参照してください。

::

  pip install hive_builder

パラメータを設定
=========================
hive_email 変数にメールアドレス、domain 変数にドメイン名を設定して、 inventory/group_vars/all.yml に保存してください。
以下に例を示します。

.. code-block:: yaml

  hive_email: hostmaster@example.com
  domain: example.com


AWS の設定
=========================

GCPプロバイダを使用する場合、このセクションをスキップして、「GCPの設定」に進んんでください。

inventory/hive.yml に AWS の環境のパラメータを設定します。
services.staging.region にリージョンを指定し、services.staging.subnets
の available_zone にアカウントが利用できる3つの可用性ゾーンを指定してください。
サンプルでは東京リージョンが設定されていますが、可用性ゾーンについては、
4つのうちどの3個が利用できるかがアカウントごとに異なるので、注意してください。

また、以下のコマンドで hive の環境に AWS EC2 API の鍵を設定してください。

::

  hive set aws_access_key_id アクセスキーID
  hive set aws_secret_access_key アクセスキー
 
GCPの設定
=========================
 
AWSプロバイダを使用する場合、このセクションをスキップしてください。

inventory/hive.yml を編集してください。8行目から37行目をコメントアウトして、38行目から45行目のコメントアウトを外してください.
 
修正後

:: 

  #production:
  #  provider: azure
  #  separate_repository: True
  #  cidr: 192.168.0.0/24
  #  instance_type: Standard_D2s_v3
  #  region: japaneast
  #  disk_size: 100
  #  repository_disk_size: 150
  #  mirrored_disk_size: 20
  #  repository_instance_type: Standard_D2s_v3
  production:
    provider: gcp
    separate_repository: True
    cidr: 192.168.0.0/24
    instance_type: n1-standard-2
    region: asia-northeast2
    mirrored_disk_size: 20
    repository_instance_type: n1-standard-2
    
GCPプロバイダを使用する場合は、プロジェクトのルートディレクトリに gcp_credential.json という 名前でサービスアカウントキーを保持するファイルを置く必要があります。 サービスアカウントの作成については、 https://cloud.google.com/iam/docs/creating-managing-service-accounts?hl=ja を参照してください。サービスアカウントを作成する際には「Compute 管理者」のロールを割り当ててください。 サービスアカウントキーについては、 https://cloud.google.com/iam/docs/creating-managing-service-account-keys?hl=ja を参照してください。 鍵の形式でJSONを選択して、プロジェクトのルートディレクトリに gcp_credential.json という名前で保存してください。

ステージの設定
=========================
今回は staging ステージを構築します。以下のコマンドで対象ステージ（デフォルトでは private）を 切り替えてください。AWSプロバイダを使用する場合は対象ステージがstaging, GCPプロバイダを使用する場合は対象ステージがproduction になります。

AWSの場合

::

  hive set stage staging
 
GCPの場合

::

  hive set stage production

collection と role のインストール
======================================
仮想環境が activate されている状態で以下のコマンドで collection をインストールしてください。

::

  hive install-collection
  
続いて以下のコマンドで　role をインストールしてください。ただし、AWSとGCPでステージが異なります。

AWSの場合

::

  ansible-galaxy role install -p .hive/staging/roles powerdns.pdn


GCPの場合

::

  ansible-galaxy role install -p .hive/production/roles powerdns.pdn
  
ドメインの委譲設定
=========================
この手順は必須ではありません。ドメインを保有していない場合は、この手順をスキップして「構築」セクションに進んでください。

certbot サービスの有効化
-------------------------
保有しているドメインからサブドメインの委譲ができる場合には、DNSの管理画面に対して Lets Encrypt 発行の
サーバ証明書を自動的に付与することができます。
この機能は certbot サービスで提供されるため、利用するためには、certbotサービスを staging 環境で有効化する必要があります。
具体的には、inventory/powerdns.yml の serices.certbot.available_on 属性のステージのリストに 'staging' を追加します。

修正前

::

      available_on:
      - production

修正後

::

      available_on:
      - production
      - staging



DNS レコードの登録
-------------------------
親ドメインにNSレコードと DDNS 対応のAレコードを登録してサブドメインの管理を構築したサーバに委譲してください。
Google Domains で設定する場合は、以下の手順で設定します。

1. DNS管理画面へのアクセス
^^^^^^^^^^^^^^^^^^^^^^^^^^^

トップメニューの「マイドメイン」で対象のドメインの「管理」をクリックしてください。
表示された画面のメニューで「DNS」をクリックしてDNS管理画面を開いてください。

2. NSレコードの追加
^^^^^^^^^^^^^^^^^^^^^^^^^^^
「カスタムレコード」の「^」をクリックして詳細を開き「カスタムレコードの管理」をクリックしてカスタムレコードの管理画面を開いてください。
カスタムレコードの管理画面で「新しいレコードを追加」をクリックしてください。
ホスト名に "pdns" を入力し、タイプ "NS" を選択し、データに "s-hive0.pdns.ドメイン名" を入力します。
次に「このレコードにさらに追加」をクリックし、データに "s-hive1.pdns.ドメイン名" を入力します。
もう一度「このレコードにさらに追加」をクリックし、データに "s-hive2.pdns.ドメイン名" を入力します。
その後、保存をクリックしてデータを登録してください。

3. ダイナミックDNSレコードの追加
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
DNS管理画面で「詳細設定を表示」をクリックしてダイナミックDNSを表示し、「ダイナミックDNSの管理」をクリックしてダイナミックDNSの管理画面を開いてください。
ダイナミックDNSの管理画面で「新しいレコードを追加」をクリックしてください。
ホスト名にs-hive0.pdns を入力し、もう一度「新しいレコードを追加」をクリックしてください。
次のホスト名にs-hive1.pdns を入力し、もう一度「新しいレコードを追加」をクリックしてください。
次のホスト名にs-hive2.pdns を入力し、保存をクリックしてデータを登録してください。

4. 認証情報の入力
^^^^^^^^^^^^^^^^^^^^^^^^^^^
「カスタムレコード」の「^」をクリックして詳細を開き各レコードごとの「認証方法を表示」をクリックし、表示された画面で「表示」をクリックして、
認証情報を取得してください。
取得した認証情報を inventory/group_vars/all.yml内に以下のように ddclient_cred変数を書き加えてください。

::

 ddclient_cred:
  s-hive0.pdns:
    name: ユーザー名
    password: パスワード
  s-hive1.pdns:
    name: ユーザー名
    password: パスワード
  s-hive2.pdns:
    name: ユーザー名
    password: パスワード
  s-hive3.pdns:
    name:
    password:

レポジトリサーバーを設定している場合はname,passwordは空欄で書いてください。

構築
=========================
以下のコマンドで構築してください。

::

  hive all

このコマンドで以下のことが行われます。

- 前のセクション「ドメインの委譲設定」をスキップしている場合には、このコマンドにより、
  VPC, サブネット、ゲートウェイ、ファイアウォール、EC2インスタンス、 Elastic IP が 作成されます
- 各サーバにソフトウェアをインストールし、各種設定を行います
- 3台のサーバを docker swarm と drbd9 のクラスタとして結合(join)します
- リポジトリサーバにリポジトリサービス（registry）、監視サービス（zabbix）、日次バックアップサービスを起動します
- マイクロサービスを実装するコンテナイメージを構築し、サイト内のリポジトリに登録します
- ネットワークやボリュームを配備し、マイクロサービス群をデプロイします

テスト
=========================
dig コマンドで以下をテストしてください。10.1.1.4 は s-hive0 の Elastic IPアドレスで置き換えてください。

WSL, Linux の場合、

::

  watch dig @10.1.1.4 pdnsadmin.pdns.example.com

Mac OS の場合

::

  while :; do clear; dig @10.1.1.4 pdnsadmin.pdns.example.com; sleep 2; done

このコマンドで2秒おきに構築した権威DNSサーバにGSLBとして設定されているアドレスが返ります。
すなわち、3個の Elastic IP のうちの1個がランダムに選択されて表示され、ときどき値が変わります。
また、http://10.1.1.4(s-hive0の Elastid IPアドレスで置き換えてください) にアクセスすることでDNSの管理画面にアクセスできます。
この画面にログインする際の ID は admin でパスワードは .hive/staging/registry_password の値となります。

また、AWS のコンソールから3台のEC2インスタンスが起動していることを確認し、
そのうち、1台をAWSコンソールから落としても上記テストに異常がない（フェールオーバ時に一時的にエラーになりますが、数秒で復帰します）ことを確認してください。
このとき、dig コマンドのテストでは GSLB が死活監視しているために、落とした1台のアドレスを返さなくなっていることを確認してください。
さらに落としたサーバをAWSコンソールから起動し、dig コマンドの結果に復帰することを確認してください。

サブドメインの委譲の設定をしている場合には、正式なURL https://pdnsadmin.pdns.example.com （example.com の部分は設定した保有ドメインで置き換えてください）で
管理画面にアクセスできるはずです。この管理画面には以下のアカウントでログインできます。
サーバ証明書が Lets Encrypt から発行されていることを確認してください。

:ID: admin
:Password: .hive/staging/registry_passwordに書き込まれている値

サーバへのログインと zabbix の参照
====================================
hive コマンドでサーバにログインしてマイクロサービスの稼働状況を見てみましょう。
また、zabbix の Web コンソールへのアクセスをポートフォワーディングしてブラウザで参照してみましょう。
まず、以下のコマンドでサーバにログインしてください。

::

  hive ssh -z

これでサーバにログインしますので、以下のコマンドでマイクロサービスの稼働状況を見ることができます。

::

  docker service ls

表示されたサービスの REPLICAS 欄が 1/1 や 3/3 であれば正常です。 0/1 や 0/3 があれば、そのサービスは
動作していないことになります。
また、以下のコマンドで各サービスのログを見ることができます。

::

  docker service logs サービス名

docker service logs コマンドの詳細については https://docs.docker.com/engine/reference/commandline/service_logs/
を参照してください。

ログイン時の hive ssh コマンドでは -z オプションを指定しているので、zabbix の Web コンソールへのアクセスが
localhost の 10052 ポートにポートフォワーディングされています。ssh でログインしたままの状態で
ブラウザから http://localhost:10052 にアクセスして、以下のIDでログインしてください。

:ID: Admin
:Password: zabbix

一度、Web で接続した後、ssh をログアウトしようとすると、ポートの解放待ちで長い時間待たされます。
その場合は、Ctrl-C を押して中断してください。

サーバの停止と環境の削除
=========================
hive の build-infra コマンドでサーバの停止と環境の削除が実行できます。

サーバの停止
-------------------------
以下のコマンドでサーバを停止できます。

::

  hive build-infra -H

停止したサーバは以下のコマンドで起動できます。

::

  hive build-infra

環境の削除
-------------------------
以下のコマンドで環境を削除できます。

::

  hive build-infra -D

このコマンドにより、VPC, サブネット、ゲートウェイ、ファイアウォール、EC2インスタンス、 Elastic IP が
削除されます。Elastic IP が開放されるため、再構築した際にはグローバルIPアドレスが変わることに注意してください。

サンプルのサービス
=========================
サンプルの inventory/powerdns.yml に定義されているマイクロサービスについて、以下に説明します。

============ ==================================================================
サービス名   説明
============ ==================================================================
powerdns     GSLBとして動作する権威DNSサーバです
pdnsdb       powerdns のデータを保持するデータベースです
pdnsadmin    powerdns の Web コンソールです
proxy        サイト内のWeb サービス（今はpdnsadminのみ）に Web のリクエストを
             振り分けるためのリバースプロキシです
configure    Web サービスやサーバ証明書を自動的に検知して、proxy を設定します
certbot      サーバ証明書の取得・更新を自動的に実行します
============ ==================================================================
