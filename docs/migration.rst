=========================
旧バージョンからの移行
=========================
ここでは、すでに構築された環境で hive-builder をバージョンアップした際の移行作業について説明します。

1.2.1 からの移行
===============================
バージョン 1.2.1 では、リポジトリサーバのログローテートの設定が間違っていました。リポジトリサーバにログインして /etc/logrotate.d/syslog を編集してください。

誤： /var/log/services/*

正： /var/log/services/*.log

修正せずに新しいバージョンで setup-hosts を実行すると設定が2行になってしまいますので、ご注意ください。

1.2.1 以前からの移行
===============================
リポジトリサーバにインストールされる zabbix のテンプレートが 1.2.2 で変更になりました。以下の手順で更新してください。
1. hive ssh -z でログイン
2. ブラウザで http://localhost:10052 を開いて、zabbix のコンソールにログイン（id: admin, password: zabbix)
3. 「設定」→「テンプレート」を開いて、一覧表示
4. 「Hive Repository Server」のチェックボックスをチェックして、最下行の削除をクリック
5. 「削除しますか」の確認メッセージが表示されるので、OKをクリック
6. 「設定」→「ホストグループ」を開いて、一覧表示
7. 「Docker」のチェックボックスをチェックして、最下行の削除をクリック
8. 「削除しますか」の確認メッセージが表示されるので、OKをクリック
9. 「設定」→「ホスト」を開いて、一覧表示
10. hive0 の「ディスカバリールール」クリックして一覧表示
11. 「Volume usage discoverry」のチェックボックスをチェックして、最下行の削除をクリック
12. 「削除しますか」の確認メッセージが表示されるので、OKをクリック
13. 10. から 12. の操作を hive1, hive2 についても実行
14. 1. のコマンドを exit
15. hive setup-hosts -T zabbix,zabbix-agent を実行
16. hive ssh -t hive0.hive名 で hive0 にログイン
17. sudo systemctl restart zabbix-agent
18. exit
19. 16.から 18. を hive1, hive2 についても実行


1.1.7 以前からの移行
===============================
1.1.7 以前でマイクロサービス型のサービスのログを参照する場合には、コンテナ収容サーバにログインして、 docker service logs サービス名で参照する必要がありましたが、
1.1.8 からはリポジトリサーバの /var/log/services/サービス名.log で参照できるようになりました。
これを利用するためには、 hive setup-hosts -T rsyslogd を実行してリポジトリサーバに rsyslogd をセットアップし、 hive deploy-services でサービスをデプロイし直す必要があります。


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
