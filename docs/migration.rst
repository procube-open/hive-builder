=========================
旧バージョンからの移行
=========================
ここでは、すでに構築された環境で hive-builder をバージョンアップした際の移行作業について説明します。

1.1.5 以前からの移行
===============================
1.1.5 以前では zabbix/zabbix-web-nginx-mysql:ubuntu-trunk で提供されるイメージが 8080番ポートを公開している前提でしたが、
zabbix/zabbix-web-nginx-mysql:ubuntu-trunk の公開ポートが 80 に変わったためイメージをロードし直す必要があります。
hive setup-hosts を実行する場合は、その前に以下のコマンドを実行して、zabbix のイメージを更新してください。

::

  $ hive ssh
  $ cd zabbix
  $ docker-compose down
  $ docker image rm zabbix/zabbix-server-mysql:ubuntu-trunk
  $ docker image rm zabbix/zabbix-web-nginx-mysql:ubuntu-trunk
  $ exit

この後、hive setup-hosts を実行してください。


1.1.7 以前からの移行
===============================
1.1.7 以前でマイクロサービス型のサービスのログを参照する場合には、コンテナ収容サーバにログインして、 docker service logs サービス名で参照する必要がありましたが、
1.1.8 からはリポジトリサーバの /var/log/services/サービス名.log で参照できるようになりました。
これを利用するためには、 hive setup-hosts -T rsyslogd を実行してリポジトリサーバに rsyslogd をセットアップし、 hive deploy-services でサービスをデプロイし直す必要があります。
