=========================
旧バージョンからの移行
=========================
ここでは、すでに構築された環境で hive-builder をバージョンアップした際の移行作業について説明します。

AWS の SSH 接続を Endpoint 経由へ移行
==============================================
mother に AWS CLI v2（2.12.0 以降）をインストールし、:doc:`aws` に従って
AWS 認証用環境変数と Endpoint の作成・接続に必要な IAM 権限を準備してください。
その後、対象ステージの ``hive build-infra`` を再実行してください。
Endpoint と専用 SG が作成され、SSH 設定がプライベート IP と ProxyCommand に更新されます。
SSH 鍵、AMI、EIP、公開サービス、registry の通信経路は維持されます。

標準 SG の古い公開 SSH 許可は除去されますが、``hive_ec2_group_rules`` の独自ルールは維持されます。
独自の公開 SSH 許可を削除し、OS 側で接続元を制限している場合は Endpoint からの通信を許可してください。
既存 VPC に外部管理の Endpoint がある場合や、所有 Endpoint の構成が異なる場合は自動置換せずエラーになります。
既存の SSH 多重化接続が残っている場合は、それを再利用しない新規接続で移行結果を確認してください。

旧 ``hive set`` の鍵ペアは環境変数が未設定の場合のフォールバックとして当面維持されますが非推奨です。
環境変数は旧設定より優先され、片方だけ設定された環境変数を旧設定で補完することはありません。
後続の Ansible、``hive ssh``、Docker ソケット転送にも AWS CLI と認証情報が必要になります。

1系（1.x.x） からの移行
===============================
2系は1系（1.x.x）とサイトの互換性はありません。サイトを再構築するか、1系の最新版（1.2.3）を利用してください。
1系の最新版を利用する場合は、以下のようにバージョンを指定してバージョンアップしてください。

::

  pip install -U hive-builder=1.2.3

また、1系のマニュアルについては、
https://hive-builder.readthedocs.io/ja/foros7/
を参照してください。

2.0.x からの移行
===============================
2.0.x では、リポジトリサーバのログ収集機能のポート番号は 514固定でしたが、 2.1.0 以降では、ポート番号のデフォルトが 10514 に変わりました。
バージョンアップ後に既存の環境で deploy-services を実行するとそのサービスはポート番号 10514 にログを送ろうとします。
これを避けるためには、 inventory/grup_vars/servers.yml で以下のように指定してください。

::

  hive_syslog_port: 514

2.0.1 以前からの移行
===============================
2.0.2 からは zabbix の SELinux に対する監視方法が変わりました。
既存サイトでは hive-builder をバージョンアップ後、zabbix の Web UI にアクセスし、 Configuration -> Templates で
Hive Server SELinux テンプレートを Delete and Clear で削除してください。
その後、以下のコマンドを実行してください。

::

  hive setup-hosts -T zabbix,zabbix-agent
  # 以下をすべてのコンテナ収容サーバで繰り返し
  hive ssh -t サーバ名
  sudo su -
  make -f /usr/share/selinux/devel/Makefile reload
  systemctl restart zabbix-agent
  exit
  exit

2.1.2 以前からの移行
===============================
2.2.0 からは zabbix がログを監視するようになりました。また、バックアップスクリプトの生成は deploy-services で
行うように変更されました。
既存サイトでは hive-builder をバージョンアップ後、zabbix の Web UI にアクセスし、 Configuration -> Templates で
Hive Server SELinux テンプレートを Delete and Clear で削除してください。
その後、以下のコマンドを実行してください。

::

  hive setup-hosts -T zabbix,zabbix-agent,backup-tools,rsyslogd
  hive deploy-services
