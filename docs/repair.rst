=========================
障害からの復旧方法
=========================

サーバのディスク残量
=================================
zabbix のトリガーで、ディスク残量が少なくなり、 "Problem: /: Disk space is low (used > 80%)" などの警告メッセージが上がる場合があります。
このような場合、以下の方法で空き領域を確保してください。

docker の不要なイメージ
-------------------------------
サーバで docker の不要なイメージやコンテナが残存してディスクを圧迫している場合があります。
この場合、対象サーバに hive ssh コマンドでログインし、以下のコマンドを実行して使用していないイメージやコンテナを回収してください。

::

  docker system prune

ログファイルの肥大化（リポジトリサーバ）
-------------------------------------------
リポジトリサーバでディスク容量が不足した場合、 /var/log/services の下のログファイルのサイズを確認してください。
特定のサービスのログファイルが極端に大きくなっている場合、その内容を確認し、デバッグログの抑制などの対策を実施してください。

リポジトリの肥大化（リポジトリサーバ）
-------------------------------------------
デバッグ環境などで build-images の回数が多くなりますと、過去のイメージがリポジトリサーバ内に蓄積され、リポジトリサーバのディスクを消費します。
hive ssh でリポジトリサーバにログインし、以下のコマンドでリポジトリのディスク使用量をチェックしてください。

::

  sudo du -s -B G /var/lib/docker/volumes/registry_regdata

このディスク使用量がサーバのディスク残量不足の原因である場合は、以下のコマンドでリポジトリを一旦削除にした後、イメージをビルドし直してください。
（本番運用環境では利用中のイメージが失われるため、おすすめできません）

::

  hive ssh
  cd registry
  docker-compose down -v
  docker-compose up -d
  logout
  hive build-images

コンテナ内のディスク消費量の増加
===================================
コンテナがディスクに書き込むとディスクが消費され、これによりコンテナ収容サーバのディスク残量やDRBDボリュームのディスク残量が逼迫する場合があります。以下に対象となるボリュームごとに対応を示します。

DRBDボリュームのディスク残量
-------------------------------------------
コンテナがマウントするボリュームのうち drbd 属性が付与されたものはDRBDによるボリュームとなり、サーバのディスクとは独立したものとなります。このボリュームの残量が少なくなった場合、zabbix のトリガーで "Problem: Exceed 90% Docker volume ボリューム名 in サービス名 usage" のような警告メッセージが上がります。
このボリュームのディスクの拡大が必要でDRBD用の物理ボリュームに余裕がある場合、以下の手順でボリュームを拡張できます。

1. バックアップ採取
^^^^^^^^^^^^^^^^^^^^^^^^^^^
対象ボリューム内のデータのバックアップを採取してください。hive のサービス定義の backup_scripts に対象ボリュームの内容のバックアップスクリプトが指定されている場合は、以下のコマンドでバックアップを採取できます。

::

    hive ssh
    hive-backup.sh -l サービス名
    logout

.. note::

    上記はバックアップスクリプトが指定されている場合の方法であり、設定されていない場合は dsh, dcp などを使用してバックアップを採取する必要があります。

.. note::

    内部のデータを新しいボリュームに引き継ぐ必要がない場合はこの手順はスキップできます。

2. ボリュームの削除
^^^^^^^^^^^^^^^^^^^^^^^^^^^
一旦、ボリュームを削除してください。ボリュームを削除するためにサービスも削除する必要があります。

::

    hive deploy-services -l サービス名 -D
    hive build-images -l ボリューム名 -D

3 ボリュームのサイズを修正
^^^^^^^^^^^^^^^^^^^^^^^^^^^
サービス定義内に定義されているボリューム定義の drbd 属性の size 属性を修正し、必要なボリュームのサイズを指定してください。

4. ボリュームのビルド
^^^^^^^^^^^^^^^^^^^^^^^^^^^
ボリュームをビルドしてください。ビルド後サービスをデプロイしてください。

::

    hive deploy-services -l サービス名
    hive build-images -l ボリューム名

5. データのリストア
^^^^^^^^^^^^^^^^^^^^^^^^^^^
手順1. で採取したバックアップデータをリストアしてください。hive のサービス定義の backup_scripts に対象ボリュームの内容のバックアップスクリプトが指定されている場合は、以下のコマンドでリストアできます。

::

    hive ssh
    hive-backup.sh -l サービス名 -r
    logout

コンテナ収容サーバのディスク残量
-------------------------------------------
コンテナのディスクの一時的な領域に大量にデータが書き込まれることにより、コンテナ収容サーバのディスクが逼迫する場合があります。このような場合、以下の手順でデータを消費しているサービスを特定してください。

1. Overlay ディレクトリの特定
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ディスク容量が逼迫しているホストで以下のコマンドを実行し、どのOverlay ディレクトリがディスクを消費しているか特定してください。

::

    hive ssh -t ホスト名
    sudo su -
    du -s -BM /var/lib/docker/overlay2/* | sort -nr | head -5

出力例：
::

    13457M	/var/lib/docker/overlay2/50109e612bd497c812ecffcedcfe890eadf69033c133a1e33b56962781c5080b
    1639M	/var/lib/docker/overlay2/4b280aa02d57f2cd2adf6bd1bd88b7917f253032b7bdffcebe4cf451e3d958e0
    1363M	/var/lib/docker/overlay2/947092c7f5914fd2b9341003d571045649a2d201005b8f024ece71a294760c5a
    1363M	/var/lib/docker/overlay2/17ec482a80844f10cea6e6f1257a055ae596634eb0bcb2993378395f368f291c
    1109M	/var/lib/docker/overlay2/0e8e71e842aed54fbce7fa711508d67eca1b627ebac5f9aacbad0184728dd18c

2. サービスの特定
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
上記で表示されたディレクトリの配下の merged ディレクトリに移ると、サービスの '/' ディレクトリが見えます。その配下のファイルを調べることでどのサービスのディレクトリであるかを特定してください。例えば、前項の例のトップのOverlay ディレクトリを調べる場合は以下のようなコマンドを実行してください。

::

    cd /var/lib/docker/overlay2/50109e612bd497c812ecffcedcfe890eadf69033c133a1e33b56962781c5080b/merged
    ls
    ls etc
    ls var/log

サービスが特定できたら logout を1回実行して root ユーザのセッションを抜けてください。

3. ディスク領域の回収
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
前項で特定したサービスに dsh でログインし、ディスク領域の回収操作を実施してください。回収操作の終了後、ホストをログアウトしてください。

ホスト内サービスの失敗
=================================
ホストの中でサービスの実行に失敗し、zabbix から "Problem: At least one of the services is in a failed state" の警告メッセージが上がる場合があります。

この場合、以下のコマンドで失敗しているサービスを特定しその原因を追求して対策を講じてください。

::

    hive ssh -l ホスト名
    systemctl list-units --type=service --no-pager --no-legend --state=failed --all
    logout

この失敗しているサービスがシステムとして不要な場合、このサービスを停止してもいいかもしれません。例えば、dnf-makecache.timerや getty@tty1.service を停止する場合、以下のコマンドで停止してください。

::

    hive ssh -l ホスト名
    sudo systemctl disable --now dnf-makecache.timer getty@tty1.service
    logout


DRBDディスクの同期の失敗
=================================
DRBDディスクの同期に失敗し、zabbix から "Problem: DRBD resource ボリューム名 status is not UpToDate/Diskless client" の警告メッセージが上がる場合があります。
この場合は、まず以下のコマンドでサービスを停止してください。

::

    hive deploy-services -l サービス名 -D


その後、リポジトリサーバを除く各ホストで以下のコマンドを実行し、DRBDの状態を確認します。

::

    hive ssh -l ホスト名
    sudo drbdadm status ボリューム名
    logout

以下に対象方法についてパターンごとに示します。

全部のホストで Outdated
--------------------------------
すべてのホストで以下のように表示され、 Outdated になっている場合があります。

::

    $ drbdadm status ボリューム名
    ボリューム名 role:Secondary
      disk:Outdated
      hive1.hive名 role:Secondary
        peer-disk:Outdated
      hive2.hive名 role:Secondary
        peer-disk:Outdated

この場合は、以下のコマンドで１号機のディスクを強制的にPrimaryに昇格してください。

::

    hive ssh -l １号機
    sudo drbdadm primary --force ボリューム名
    logout

その後、他のホストで再接続を実行してください。

::

    hive ssh -l ホスト名
    sudo drbdadm disconnect ボリューム名
    sudo drbdadm connect ボリューム名
    logout

その後、１号機のディスクを secondary に降格してください。

::

    hive ssh -l １号機
    sudo drbdadm secondary ボリューム名
    logout

接続が不完全
--------------------------------
DRBD のステータスで片側から見るとエラーにはなっていないのに、反対側から見るとエラーに見える場合があります。例えば、

１号機の結果（正常）
::

    $ drbdadm status ボリューム名
    ボリューム名 role:Secondary
      disk:UpToDate
      hive1.hive名 role:Primary
        peer-disk:UpToDate
      hive2.hive名 role:Secondary
        peer-disk:UpToDate

２号機の結果（同期途中）
::

    $ drbdadm status ボリューム名
    ボリューム名 role:Primary
      disk:UpToDate
      hive0.hive名 role:Secondary
        replication:WFBitMapS peer-disk:Consistent
      hive2.hive名 role:Secondary
        peer-disk:UpToDate

この場合、正常となっている方のホスト（上記の場合では１号機）で以下のコマンドを実行して再接続を行ってください。

::

    hive ssh -l ホスト名
    sudo drbdadm disconnect ボリューム名
    sudo drbdadm connect ボリューム名
    logout

サービスが再起動を繰り返す
=================================
障害からの復旧後、サービスが起動できず、再起動を繰り返す場合があります。このような場合、docker service ps コマンドに --no-trunc オプションを付与してそのエラーの原因を見てください。例えば、以下のように表示されます。

::

    docker service ps --no-trunc ldap
    ID                          NAME                IMAGE                               NODE                DESIRED STATE       CURRENT STATE             ERROR                                                                                                        PORTS
    swcu3n4b70urjtwhdzf92jgh9   ldap.1              s-hive2.op:5000/image_ldap:latest   s-hive1             Ready               Rejected 3 seconds ago    "failed to mount local volume: mount /dev/drbd8:/var/lib/docker/volumes/ldap_data/_data: invalid argument"
    vc210ej598da9yuc9l1iw3e0i    \_ ldap.1          s-hive2.op:5000/image_ldap:latest   s-hive2             Shutdown            Rejected 9 seconds ago    "failed to mount local volume: mount /dev/drbd8:/var/lib/docker/volumes/ldap_data/_data: invalid argument"
    dk8sxitj3v7uyjhmkh57cneoz    \_ ldap.1          s-hive2.op:5000/image_ldap:latest   s-hive0             Shutdown            Rejected 14 seconds ago   "failed to mount local volume: mount /dev/drbd8:/var/lib/docker/volumes/ldap_data/_data: invalid argument"
    xo6s6q13z2ipiok5459fnvhuy    \_ ldap.1          s-hive2.op:5000/image_ldap:latest   s-hive1             Shutdown            Rejected 19 seconds ago   "failed to mount local volume: mount /dev/drbd8:/var/lib/docker/volumes/ldap_data/_data: invalid argument"
    bues7ycsvddiohserzage69lx    \_ ldap.1          s-hive2.op:5000/image_ldap:latest   s-hive2             Shutdown            Rejected 23 seconds ago   "failed to mount local volume: mount /dev/drbd8:/var/lib/docker/volumes/ldap_data/_data: invalid argument"

ここでは、エラーメッセージは "failed to mount local volume: mount /dev/drbd8:/var/lib/docker/volumes/ldap_data/_data: invalid argument" となっています。

DRBDのファイルシステムの破損
--------------------------------
前項エラーメッセージ例の "invalid argument" はファイルシステムが破損している場合に出るメッセージです。以下のコマンドで修復してください。

::

    hive ssh -l １号機
    docker service scale サービス名=0
    sudo xfs_repair $(docker volume inspect ボリューム名 --format '{{ .Options.device }}')
    docker service scale サービス名=1
    logout
