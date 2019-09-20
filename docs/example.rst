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
保有するドメインに構築する権威DNSサーバを登録して、サブドメインの管理を委譲することで新しいサブドメインを管理できます。
これにより、GSLBとして動作させるとともに、Lets Encryptでサーバ証明書を自動的に取得させることができます。
このためには、親ドメインにNSレコードとAレコードを登録する必要がありますが、これは必須ではありません。

サンプルソースコードの取得
=========================
サンプルソースコードをgithub からダウンロードします。

::

  svn export https://github.com/procube-open/hive-builder/branches/master/examples/pdns
  cd pdns

svn コマンドを使用しない場合は、 hive-builder のソースコード全体を clone してください。

::

  git clone htpps://github.com/procube-open/hive-builder
  cd hive-builder/examples/pdns

仮想環境の activate
=========================
hive 用の仮想環境を作成し、activate します。仮想環境ツールが pyenv で python 3.7.3 がインストールされている場合、以下のコマンドで activate できます。

::

  pyenv virtualenv hive 3.7.3
  pynev local hive

virtualenv, pipenv, conda を利用されている場合は、それぞれの方法で仮想環境を activate してください。

hive-builder のインストール
=========================
仮想環境が activate されている状態で以下のコマンドで hive-builder をインストールしてください。

::

  pip install hive-builder


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

また、以下のコマンドで hive の環境に AWS EC2 API の鍵を設定してください。

::

  hive set aws_access_key_id アクセスキーID
  hive set aws_secret_access_key アクセスキー

ドメインの委譲設定
=========================
この手順は必須ではありません。ドメインを保有していない場合は、この手順をスキップしてください。

build-infra の実行
-------------------------
以下のコマンドで build-infra フェーズを実行して、 Elastic IP を割り当ててください。

::

  hive build-infra

DNS レコードの登録
-------------------------
親ドメインにNSレコードとAレコードを登録してサブドメインの管理を構築したサーバに委譲してください。
設定例は以下の通り。

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

テスト
=========================
dig コマンドで以下をテストしてください。10.1.1.4 は s-hive0 の Elastic IPアドレスで置き換えてください。

::

  watch dig @10.1.1.4 pdnsadmin.pdns.example.com

このコマンドで2秒おきに構築した権威DNSサーバにGSLBとして設定されているアドレスが返ります。また、
http://10.1.1.4(s-hive0の Elastid IPアドレスで置き換えてください) にアクセスすることでDNSの管理画面にアクセスできます。
この画面にログインする際の ID は administrator でパスワードは .hive/staging/registry_password の値となります。

また、AWS のコンソールから3台のEC2インスタンスが起動していることを確認し、
そのうち、1台を落としても上記テストに異常がない（フェールオーバ時に一時的にエラーになりますが、数秒で復帰します）ことを確認してください。
このとき、dig コマンドのテストでは GSLB が死活監視しているために、落とした1台のアドレスを返さなくなっていることを確認してください。
さらに落としたサーバをAWSコンソールから起動し、dig コマンドの結果に復帰することを確認してください。

サブドメインの委譲の設定をしている場合には、正式なURL https://pdnsadmin.pdns.example.com で管理画面にアクセスできるはずです。
サーバ証明書が Lets encrypt から発行されていることを確認してください。
