=========================
旧バージョンからの移行
=========================
ここでは、すでに構築された環境で hive-builder をバージョンアップした際の移行作業について説明します。

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
