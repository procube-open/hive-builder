=========================
サンプルを構築してみる
=========================

ここでは、 hive のソースコードの github に登録されているサンプルを使って、AWS上に GSLB 機能を持つ権威DNSサーバを構築してみます。

前提条件と準備
=========================

サンプルを構築するためには IaaS のAPIに対する鍵を取得する必要があります。また、ドメインを保有していれば実際にサブドメインを管理できます。

IaaS
------------------------
このサンプルを実行するためには AWS EC2, VPC にアクセスできるユーザのAPI鍵が必要です。以下の権限を持つ IAM ユーザを作成し、そのAPI鍵を取得してください。

.. code-block:: json

  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "VisualEditor0",
        "Effect": "Allow",
        "Action": [
          "iam:PassRole",
          "aws-marketplace:*",
          "resource-groups:*",
          "ec2:*",
          "tag:*",
          "route53:AssociateVPCWithHostedZone"
        ],
        "Resource": "*"
      }
    ]
  }

サブドメイン委譲
------------------------
ここで構築する権威DNSサーバを保有するドメインに登録して、サブドメインの管理を委譲することで新しいサブドメインを管理できます。
これにより、GSLBとして動作させるとともに、Lets Encryptでサーバ証明書を自動的に取得させることができます。
このためには、親ドメインにNSレコードとAレコードを登録する必要がありますが、これは必須ではありません。

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

仮想環境の activate
=========================
hive 用の仮想環境を作成し、activate します。仮想環境ツールが pyenv で python 3.7.3 がインストールされている場合、以下のコマンドで activate できます。

::

  pyenv virtualenv 3.7.3 hive
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

ステージの設定
=========================
今回は staging ステージを構築します。以下のコマンドで対象ステージ（デフォルトでは private）を staging  に切り替えてください。

::

  hive set stage staging

AWS の設定
=========================

inventory/hive.yml に AWS の環境のパラメータを設定します。
services.staging.region にリージョンを指定し、services.staging.subnets
の available_zone にアカウントが利用できる3つの可用性ゾーンを指定してください。
サンプルでは東京リージョンが設定されていますが、可用性ゾーンについては、
4つのうちどの3個が利用できるかがアカウントごとに異なるので、注意してください。

また、以下のコマンドで hive の環境に AWS EC2 API の鍵を設定してください。

::

  hive set aws_access_key_id アクセスキーID
  hive set aws_secret_access_key アクセスキー

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


build-infra の実行
-------------------------
以下のコマンドで build-infra フェーズを実行して、 Elastic IP を割り当ててください。

::

  hive build-infra

このコマンドにより、VPC, サブネット、ゲートウェイ、ファイアウォール、EC2インスタンス、 Elastic IP が
作成されます。また、コマンドの実行に成功すると、 start_phase 変数に 'setup-hosts' が設定され、
次に hive all を実行した際には setup-hosts フェーズから始まります。

DNS レコードの登録
-------------------------
親ドメインにNSレコードとAレコードを登録してサブドメインの管理を構築したサーバに委譲してください。
設定例は以下の通りです。

::

  pdns.example.com. IN NS s-hive0.pdns.example.com.
  pdns.example.com. IN NS s-hive1.pdns.example.com.
  pdns.example.com. IN NS s-hive2.pdns.example.com.
  s-hive0.pdns.example.com. IN A 10.1.1.4
  s-hive1.pdns.example.com. IN A 10.1.2.4
  s-hive2.pdns.example.com. IN A 10.1.3.4

ここで 10.1.1.4, 10.1.2.4, 10.1.3.4 の部分は EC2 インスタンスに関連付けられたElastic IP で置き換えます。
Elastic IP は AWSコンソールか .hive/staging/ssh_config のファイル内の Host ディレクティブの値を見ることで調べることができます。

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
- リポジトリサーバにリポジトリサービス（registry）、監視サービス（zabbix）、日次バックサップサービスを起動します
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
管理画面にアクセスできるはずです。
サーバ証明書が Lets Encrypt から発行されていることを確認してください。

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

:ID: admin
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
