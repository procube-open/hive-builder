=========================
よくある質問
=========================

build-images で Bad local forwarding specification のエラーになります
---------------------------------------------------------------------

hive-builder は OpenSSH の unix domain socket のフォワーディング機能を使用していますが、
OpenSSH-6.7 より古いバージョンの OpenSSH （例えば、 CentOS 7.2 では、OpenSSH-6.6）では、
この機能をサポートしていません。OpenSSH-6.7以上にバージョンアップしてご利用ください。

リポジトリサーバのログ収集で fluentd を使用しないのはなぜですか
----------------------------------------------------------------

docker の fluentd ロギングドライバーは fluentd とTCP接続できないとサービスが起動しません。
このため、リポジトリサーバに配置した fulentd が死んでいる場合はサービスが起動できません。
hive-builder の要件としてリポジトリサーバが死んでいてもサービス提供を続けることというのがあり、採用できませんでした。


build-images, initialize-services で fail to create socket のエラーになります
------------------------------------------------------------------------------
:メッセージ: fail to create socket /var/tmp/hive/docker.sock@サーバ名, another hive process may doing build-image or the file has been left because previus hive process aborted suddenly
:コマンド: build-images, initialize-services
:対応方法: 他の hive コマンドが同じマザーマシンで動作している場合はその終了を待ってください。そうでない場合は rm コマンドで /var/tmp/hive/docker.sock@サーバ名を削除してください。

initialize-services で Authentication or permission failure のエラーになります
-------------------------------------------------------------------------------
:メッセージ: Authentication or permission failure. In some cases, you may have been able to authenticate and did not have permissions on the target directory. Consider changing the remote tmp path in ansible.cfg to a path rooted in "/tmp".
:コマンド: initialize-services
:対応方法: initialize-services の実行中にサービスの再起動が行われた可能性があります。ログなどを確認して、initialize-services 実行中にサービスが再起動しないように修正してください。

build-infra で Vagrant command failed のエラーになります
-------------------------------------------------------------------------------
:メッセージ: Vagrant command failed: Command "["/usr/bin/vagrant", "up", "--provision"]" returned non-zero exit status 1
:コマンド: build-infra
:対応方法: cd .hive/ステージ名; /usr/bin/vagrant up --provision を実行してエラーメッセージを確認し、修正してください。


UDP のサービスが特定のクライアントからのパケットを全く受信できません
----------------------------------------------------------------------------------------------------------
:準備:
      hive-builder で構築したサーバでは conntrack コマンドがインストールされていません。 コンテナ収容サーバに
      yum install conntrack-tools で conntrack コマンドをインストールしてください

:発生条件: 1系の hive-builder で構築したサーバで
      特定のIPアドレス、ポート番号から30秒より短い間隔で常時 UDP パケットを受信している状態で
      サービスを起動あるいは再起動した場合に発生します。忙しいDHCPリレーエージェントや syslog クライアントのリクエストを
      hive-builder のサービスで処理する場合はこれに該当します。

:原因: ホストに着信したパケットは、仮想ブリッジを経由してサービスを実装するコンテナに転送されるべきですが、
      この転送機能が機能していません。
      docker では、Linux の iptables の DNAT機能を使用してパケットを転送しますが、このパケット転送が設定されていない状態で UDP パケットを受信すると
      DNATがされていない情報が conntrack に登録されます。
      その状態でサービスを起動すると、docker が iptables に DNAT を登録しますが、 iptables の DNAT 機能は対象となるパケットにマッチする情報が
      conntrack テーブルにすでに登録されている場合は、その情報が優先して利用されるため、作動しません。
      conntrack テーブルには、送信元IPアドレス、宛先ポート番号、宛先IPアドレス、宛先ポート番号をキーとして登録されますが、
      プロトコルが UDPの場合はパケットを着信しない状態で30秒経過すると削除されます。
      発生しているかどうかは conntrack コマンドで確認できます。
      conntrack に DNAT された情報が登録されていれば、2個めの src= の後ろにコンテナのIPアドレスが表示されますが、
      問題が発生している場合は、サーバのIPアドレスが表示されます。
      以下にリクエストを受け付けるポート番号が 20514 である場合の例を示します。

::

    # 正常な場合
    $ sudo conntrack -L -p udp --dport 20514
    udp      17 26 src=192.168.56.1 dst=192.168.56.4 sport=55646 dport=20514 [UNREPLIED] src=172.21.34.130 dst=192.168.56.1 sport=514 dport=55646 mark=0 secctx=system_u:object_r:unlabeled_t:s0 use=1
    conntrack v1.4.4 (conntrack-tools): 1 flow entries have been shown.
    # 問題が発生している場合
    $ sudo conntrack -L -p udp --dport 20514
    udp      17 26 src=192.168.56.1 dst=192.168.56.4 sport=64953 dport=20514 [UNREPLIED] src=192.168.56.4 dst=192.168.56.1 sport=20514 dport=64953 mark=0 secctx=system_u:object_r:unlabeled_t:s0 use=1
    conntrack v1.4.4 (conntrack-tools): 1 flow entries have been shown.

:対応方法: 問題となる conntrack 情報を削除してください。conntrack コマンドに -D オプションを指定することで削除できます。
      conntrack コマンド実行直後のパケットから受信を再開するはずです。
      以下にリクエストを受け付けるポート番号が 20514 である場合の例を示します。

::

    $ conntrack -D -p udp --dport 20514
    udp      17 25 src=192.168.56.1 dst=192.168.56.4 sport=51109 dport=20514 [UNREPLIED] src=192.168.56.4 dst=192.168.56.1 sport=20514 dport=51109 mark=0 secctx=system_u:object_r:unlabeled_t:s0 use=1
    conntrack v1.4.4 (conntrack-tools): 1 flow entries have been deleted.

