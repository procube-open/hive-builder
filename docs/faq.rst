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

ビルドが止まってしまいます
----------------------------------------------------------------
ビルドで、ansible のタスク実行が次に進まなくなる場合があります。原因がわかっておりません。
対象のサーバにログインして、プロセスの実行状況をみて、タスクを実行している様子がなければ、 ^C キーで hive コマンドを中断し、再実行してください。

build-images, initialize-services で fail to create socket のエラーになります
------------------------------------------------------------------------------
:メッセージ: fail to create socket /var/tmp/hive/docker.sock@サーバ名, another hive process may doing build-image or the file has been left because previus hive process aborted suddenly
:コマンド: build-images, initialize-services
:対応方法: 他の hive コマンドが同じマザーマシンで動作している場合はその終了を待ってください。そうでない場合は rm コマンドで /var/tmp/hive/docker.sock@サーバ名を削除してください。

initialize-services で Authentication or permission failure のエラーになります
-------------------------------------------------------------------------------
:メッセージ: Authentication or permission failure. In some cases, you may have been able to authenticate and did not have permissions on the target directory. Consider changing the remote tmp path in ansible.cfg to a path rooted in "/tmp".
:コマンド: initialize-services
:原因: initialize-services の実行中にサービスの再起動が行われた可能性があります。
:対応方法: ログなどを確認して、initialize-services 実行中にサービスが再起動しないように修正してください。

build-infra で Vagrant command failed のエラーになります
-------------------------------------------------------------------------------
:メッセージ: Vagrant command failed: Command "["/usr/bin/vagrant", "up", "--provision"]" returned non-zero exit status 1
:コマンド: build-infra
:対応方法: cd .hive/ステージ名; /usr/bin/vagrant up --provision を実行してエラーメッセージを確認し、修正してください。

エラーメッセージに Could not create the directory が含まれる場合
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

エラーメッセージが以下のようなもので、 Could not create the directory が含まれている場合、 vagrant-disksize プラグインのバグにより、ディスクのサイズ拡張に失敗しています。
参考： https://github.com/sprotheroe/vagrant-disksize/pull/27

::


    There was an error while executing `VBoxManage`, a CLI used by Vagrant
    for controlling VirtualBox. The command and stderr is shown below.
    Command: ["clonemedium", "C:\\Users\\mitsuru\\VirtualBox VMs\\p-hive0.mic-env\\CentOS-8-Vagrant-8.0.1905-1.x86_64.vmdk", "./C:\\Users\\mitsuru\\VirtualBox VMs\\p-hive0.mic-env\\CentOS-8-Vagrant-8.0.1905-1.x86_64.vdi", "--format", "VDI"]
    Stderr: 0%...
    Progress state: VBOX_E_IPRT_ERROR
    VBoxManage.exe: error: Failed to clone medium
    VBoxManage.exe: error: Could not create the directory '\\wsl$\Ubuntu\home\mitsuru\hive\private\C:\Users\mitsuru\VirtualBox VMs\p-hive0.mic-env' (VERR_INVALID_NAME)
    VBoxManage.exe: error: Details: code VBOX_E_IPRT_ERROR (0x80bb0005), component VirtualBoxWrap, interface IVirtualBox
    VBoxManage.exe: error: Context: "enum RTEXITCODE __cdecl handleCloneMedium(struct HandlerArg *)" at line 1071 of file VBoxManageDisk.cpp

この場合、vagrant-disksize プラグインを修正することで回避できます。

vagrant-disksize プラグインを以下のように修正してください。

:ファイル: ~/.vagrant.d/gems/2.6.6/gems/vagrant-disksize-0.1.3/lib/vagrant/disksize/actions.rb
:修正箇所: 151行目
:修正前:

::


    dst = File.join(src_path, src_base) + '.vdi'

:修正後:

::


    dst = src_base + '.vdi'

エラーメッセージに Error: Unknown repo: 'C*-base' が含まれる場合
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

エラーが VirtualBox Guest addtions のインストール中に発生し、メッセージが Error: Unknown repo: 'C*-base' である場合、vagrant-vbguest プラグインのバグである可能性が高いです。
参考： https://github.com/dotless-de/vagrant-vbguest/issues/367

この場合は、vagrant-vbguest プラグインを vagrant plugin uninstall vagrant-vbguest コマンドでアンインストールしてください。


build-images で Release file is not valid yet のエラーが出ます
-------------------------------------------------------------------------------
:メッセージ: Release file for http://security.ubuntu.com/ubuntu/dists/focal-security/InRelease is not valid yet (invalid for another XXh XXmin XXs). Updates for this repository will not be applied.
:コマンド: build-images
:発生条件: Vagrant プロバイダでパソコン内の VirtualBox 上に hive を構築している場合で、仮想マシンが起動している状態でパソコンをスリープ状態から復帰させた場合
:原因: サーバの時刻がずれているため、apt のリポジトリの正当性の検証に失敗しています。
:対応方法: 各サーバで systemctl restart chroyd を実行してください。

zabbix でDetect SELinux alert の障害（problem）が残ったままになります。
-------------------------------------------------------------------------------
:現象: Zabbix でアイテム SELinux alert の値が0 になっているにも関わらず、トリガー Detect SELinux alert
       による障害（problem）が残ったままになります。
:発生条件: SELinux alert の値が一度でも 1になった場合（構築時には起こりやすいです）
:原因: このトリガーにはクローズの条件が指定されておらず、手動でクローズして頂く必要があります。
:対応方法: 構築時の SELinux alert は無視していただいてかまいません。
           構築時以外でアラートが上がった場合は、 SELinux のログで問題がないか確認してください。
           障害をクローズするために障害を開き、「確認済」 のリンクを開き、メッセージを入力し、
           「障害確認」と「障害のクローズ」をチェックしてください。

zabbix の SELinux alert でエラーが出ます
-------------------------------------------------------------------------------
:メッセージ: Corrupted checkpoint file. Inode match, but newer complete event (XXX:YYY) found before loaded checkpoint XXXX:YYY
:zabbix item: SELinux alert
:発生条件: SELinux の audit log が短時間に大量に出力された場合
:原因: SELinux の audit log が短時間に大量に出力されたために、 /var/log/audit/audit.log がローテートしてしまい、チェックポイント機能が利用できなかった
:対応方法: 対象サーバにログインして sudo  ausearch -m AVC,USER_AVC,SELINUX_ERR,USER_SELINUX_ERR -i を実行し、 SELinux の audit ログが出力された原因を取り除いてください。
           その後、 sudo rm /var/run/zabbix/ausearch でチェックポイントファイルを削除してください。

deploy-services で renaming services is not supported のエラーが出ます
-------------------------------------------------------------------------------
:メッセージ:

::


    An exception occurred during task execution. To see the full traceback, use -vvv. The error was: docker.errors.APIError: 501 Server Error: Not Implemented ("rpc error: code = Unimplemented desc = renaming services is not supported")
    failed: [s-hive0.hive名] (item=サービス名) => changed=false
      ansible_loop_var: item
      item: サービス名
    msg: 'An unexpected docker error occurred: 501 Server Error: Not Implemented ("rpc error: code = Unimplemented desc = renaming services is not supported")'

:発生条件: 不明
:原因: 不明
:対応方法: hive ssh -t ステージプリフィクスhive0.hive名 でログインして、 docker service rm サービス名 を実行後に hive deploy-services を再実行してください。


build-volumes で modprobe: ERROR: could not insert 'drbd': Required key not available のエラーが出ます
------------------------------------------------------------------------------------------------------
:メッセージ:

::

    modprobe: ERROR: could not insert 'drbd': Required key not available
    Failed to modprobe drbd (No such file or directory)
    Command 'drbdsetup new-resource kea_config 2 --quorum=majority --on-no-quorum=io-error' terminated with exit code 20

:原因: カーネルの機能でUEFI Secure boot が有効になっているため、署名されていない DRBDのカーネルモジュールは読み込むことができません
:対応方法: 物理サーバの場合は起動時のUEFIの設定画面で、VMWareなどの仮想サーバの場合はVsphere client などの設定ツールで、サーバの
           UEFI Secure Bootを無効にしてください。
           参考：https://docs.vmware.com/jp/VMware-vSphere/6.5/com.vmware.vsphere.vm_admin.doc/GUID-898217D4-689D-4EB5-866C-888353FE241C.html

mother 環境構築直後の build-infra フェーズで Unexpected failure during module execution. のエラーが出ます
----------------------------------------------------------------------------------------------------------
:メッセージ:

::

    TASK [Gathering Facts] **********************************************************************************************************************************
    An exception occurred during task execution. To see the full traceback, use -vvv. The error was: TypeError: can only concatenate str (not "NoneType") to str
    fatal: [p-mother.op]: FAILED! =>
      msg: Unexpected failure during module execution.
      stdout: ''

:原因: python コマンドがインストールされていない。例えば、Ubuntu などで python2系もインストールされていない状態で
      python3 コマンドをインストールし、 pip install hive-builder で mother 環境を構築した場合、 python3 コマンドしかなく
      python コマンドがない状態となる。
:対応方法: 仮想環境を作成し、そこに hive-builder をインストールして、仮想環境をアクティベートしてから hiveコマンドを実行してください。
      仮想環境をアクティベートすると、OSには python3 しかインストールされていな状態でも pythonコマンドが利用できます。

異常がないのに zabbix で At least one of the services is in a failed state のトリガーがあがります
----------------------------------------------------------------------------------------------------------
:現象:

異常がないのに zabbix で At least one of the services is in a failed state のトリガーがあがる。
以下のコマンドを実行すると失敗しているサービス名はわかったが、そのサービスはすでに削除されている。
たとえば、DRBD のボリュームがエラーになった後、 build-volumes -l ボリューム名 -D などで削除した場合、
以下のように表示される

::

    $ systemctl list-units --type=service --no-pager --no-legend --state=failed --all
    drbd-resource@some_data.service loaded failed failed DRBD resource : some_data

:原因: サービスを削除した後、 systemd が失敗したユニットを記憶しているため、アイテムの数が 0になりません。
:対応方法: 以下のコマンドでリセットしてください。

::

    $ sudo systemctl reset-failed

異なるホストに配置されたサービス間の通信ができません
----------------------------------------------------------------------------------------------------
:現象: 異なるホストに配置されたサービス間で通信できない。例えば、hive-builder のサンプルにおいて、
       powerdns サービスから pdnsdb へのアクセスが異なるホストに配置されたときのみアクセスができないという現象が発生する場合がある。
:原因1: VMWare の NSX機能やネットワーク機器のVXLAN機能が動作していることが原因で swarm のオーバレイネットワークの通信に必要な 4789/udp のパケットが到達できない。
        https://stackoverflow.com/questions/43933143/docker-swarm-overlay-network-is-not-working-for-containers-in-different-hosts
:原因2: ホストに複数のネットワークインタフェースがある場合に swarm のオーバレイネットワークの通信に利用するIPアドレスが間違っている
:原因3: ネットワークカードに offload したチェックサム照合機能がパケットをチェックサム不整合で破棄している。VMWare の仮想NICはこれに該当する。
        https://stackoverflow.com/questions/66251422/docker-swarm-overlay-network-icmp-works-but-not-anything-else
:原因4: ホスト間のネットワークの mtu が1500より小さく、 VXLAN のヘッダが付いたパケットをドロップしてしまう。
        ただし、この場合は全く通信できないわけではなく、サイズが大きいパケットのみがドロップされる。
:対応方法: 原因1, 原因2 の場合は、以下の手順でdocker swarm のオーバレイネットワークが使用するポート番号やIPアドレスを変更してください。
           原因3 の場合は各ホストで ethtool -K <interface> tx off コマンドを実行してネットワークカードへの offload を無効化してください。
           原因4 の場合は各環境に応じてホスト間のネットワークの mtu が 1500以上となるように設定してください。
           ただし、GCPのVPNと併用する場合は、VPN側の制限と相反する場合がありますので、注意が必要です。
           `MTU に関する考慮事項 <https://cloud.google.com/network-connectivity/docs/vpn/concepts/mtu-considerations?hl=ja>`_ を参照してください。

1. 全サービスを削除
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
オーバレイネットワークを再構築するために一旦全サービスを削除してください。

::

    hive deploy-services -D

2. iptables を修正
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
リポジトリサーバを除く各ホストの以下の手順で /etc/sysconfig/iptables を修正し、4789 を 8472 に置換して iptables を再起動してください。

::

    hive ssh -t ホスト名
    vim /etc/sysconfig/iptables
    sudo systemctl restart iptables
    sudo systemctl restart docker
    logout

3. swarm クラスタの解除
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
リポジトリサーバを除く各ホストの以下の手順でクラスタを解除してください。

::

    hive ssh -t ホスト名
    docker swarm leave --force
    logout

4. swarm クラスタの初期化
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1号機で以下の手順を実行してクラスタを構築してください。

::

    hive ssh -t １号機のホスト名
    docker swarm init --advertise-addr １号機のIPアドレス --data-path-port 8472
    docker swarm join-token manager
    logout

docker swarm join-token manager で表示されたトークンの値を記録してください。

5. swarm クラスタの構築
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1号機以外のホスト（リポジトリサーバを除く）で以下の手順を実行してクラスタを構築してください。

::

    hive ssh -t ホスト名
    docker swarm join --advertise-addr ホストのIPアドレス --token トークン １号機のIPアドレス:2377
    logout

6. hive_default_network の復旧
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドで hive_default_network を復旧してください。

::

    hive build-networks

7. サービスを起動
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドで全サービスを起動してください。

::

    hive deploy-services

8. follow-swarm-service 再起動
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドをリポジトリサーバを除く各ホストで実行し、follow-swarm-service  を再起動してください。

::

    hive ssh -t ホスト名
    sudo systemctl restart follow-swarm-service.service
    logout

dockerhub からイメージをダウンロードするときにダウンロードでエラーになります
----------------------------------------------------------------------------------------------------
:現象: dockerhub からイメージをダウンロードする際に toomanyrequests のエラーになる。
       例えば、setup-hosts フェーズの zabbix サーバの起動タスクで以下のようなエラーになる。

::

  TASK [zabbix : compose up zabbix container] ***************************************************************************************************************
  fatal: [p-hive0.nec-hss]: FAILED! => changed=false
  errors: []
    module_stderr: ''
    module_stdout: ''
    msg: 'Error starting project 500 Server Error for http+docker://localhost/v1.41/images/create?tag=alpine-5.2-latest&fromImage=zabbix%2Fzabbix-server-mysql: Internal Server Error ("toomanyrequests: You have reached your pull rate limit. You may increase the limit by authenticating and upgrading: https://www.docker.com/increase-rate-limit")'

:原因: dockerhub の `アクセス頻度制限 <https://www.docker.com/increase-rate-limit>`_ の上限を超えてアクセスした。
       アクセス頻度制限は dockerhub から匿名でダウンロードしようとすると 100回/6時間の制限がかかる。
       通常、1ユーザで100回/6時間の制限に抵触することはが、匿名のアクセスについてはユーザを送信元IPアドレスで特定されるため、
       企業内のネットワークから複数人でアクセスすると同じユーザと認識されて制限にかかる場合がある。
:対応方法:
       hive_ext_repositories に dockerhub のアカウントを設定する。設定方法については :doc:`hive構築ガイド<develop>` の外部リポジトリへのログインの節を参照のこと。
       これにより送信元IPではなく、アカウントに結びついたダウンロードとなるため、200回/6時間の制限となるとともに
       企業内のネットワークから複数人でアクセスする場合でもここのユーザごとの制限数となる。

gcpプロバイダを使用している場合に hive build-infra で Permission denied のエラー
----------------------------------------------------------------------------------------------------
:現象:  gcp プロバイダを使用している場合に ssh 接続が Permission denied のエラーとなる。
        例えば、build-infra フェーズの wait_for_connection タスクで以下のようなエラーになる。
    
::

    TASK [wait_for_connection] *****************************************************
    fatal: [hive3.pdns]: FAILED! => changed=false
    elapsed: 600
    msg: 'timed out waiting for ping module test: Failed to connect to the host via ssh: admin@34.97.59.48: Permission denied (publickey,gssapi-keyex,gssapi-with-mic).'

:原因: プロジェクトの設定で OS Login が有効になっているため、 hive の管理者ユーザが生成されない。
:対応方法: 
        `OS Loginの設定方法 <https://cloud.google.com/compute/docs/troubleshooting/troubleshoot-os-login#checking_if_os_login_is_enabled>`_ 
        の「ステップ 1: OS Login を有効または無効にする」を参照してOS Loginを無効に設定する。
        具体的には、以下のように設定する。

        「[メタデータ]に移動」→GCPコンソール画面「メタデータ」→編集

        キー1: enable-oslogin 値1: TRUE

        ↓

        キー1: enable-oslogin 値1: FALSE

:参考: https://cloud.google.com/compute/docs/troubleshooting/troubleshooting-ssh

サービスが特定のサーバに偏ってしまったようですが、どうしたらいいですか
----------------------------------------------------------------------------------------------------
サーバの再起動などで、サービスの配置が偏ってしまった場合、以下の手順でサービスを再配置位することができます。

1. サービスの配置状況を確認
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
コンテナ収容サーバのいずれかに ssh でログインし、以下のコマンドを実行して replicated モードのサービスの配置状況を確認してください。global モードのサービスは
すべてのコンテナ収容サーバに配置されていますので、偏ることはないので、作業の対象から除外します。

::
    
    docker service ps $(docker service ls -q --filter mode=replicated) --format "{{.Name}}\t{{.Node}}\t{{.CurrentState}}" -f desired-state=running  

2. サービスを再配置
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
コンテナ収容サーバのいずれかに ssh でログインし、以下のコマンドを実行してサービスを再配置してください。

::
    
    docker service ls -q --filter mode=replicated | xargs -L 1 docker service update --force 


1. サービスの配置状況を再確認
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. と同じコマンドでサービスの配置状況を確認してください。


構築後に internal_cidr の値を変更するにはどうしたらいいですか
----------------------------------------------------------------------------------------------------
以下の手順で変更してください。

1. internal_cidr を変更
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
inventory/hive.yml の internal_cidr の値を変更してください。

2. swarm クラスタの解除
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドをすべてのコンテナ収容サーバで実行して、 swarm クラスタを解除してください。

::
    
    docker swarm leave -f  

3. docker_gwbridge の削除
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドをすべてのコンテナ収容サーバで実行して、 docker_gwbridge を削除してください。

::

    docker network rm docker_gwbridge

4. zabbix とリポジトリサービスの停止
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドをリポジトリサーバで実行して、 zabbix とリポジトリサービスを停止してください。

::

    (cd zabbix; docker-compose down)
    (cd registry; docker-compose down)

5. setup-hosts フェーズの実行
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドをマザーマシンで実行して、setup-hosts フェーズを実行してください。

::

    hive setup-hosts

6. docker デーモンの再起動
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドをすべてのサーバで実行して、docker デーモンを再起動してください。

::

    systemctl restart docker

7. ネットワークのビルド
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドを実行して、ネットワークをビルドしてください。

::

    hive build-networks

8. サービスのデプロイ
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドを実行して、サービスをデプロイしてください。

::

    hive deploy-services


アドレスの確認
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
割り当てられているアドレスを確認するためには手順の前後で以下のコマンドを各サーバで実行してください。

::

    docker network inspect $(docker network ls --format "{{.Name}}") | grep Subnet

手順実行後に internal_cidr の範囲内のアドレスのみが出るようになれば正解です。
サービスやボリュームは作り直す必要はありません。

hive sshおよびsshコマンドでのssh接続ができません
----------------------------------------------------------------------------------------------------
:現象: hive sshまたはsshコマンドでのssh接続をしようとすると以下のメッセージが出て失敗する

::

    Host key verification failed.

:原因1: サーバーの公開鍵の紛失または誤って内容を変更してしまった
:原因2: サーバーの秘密鍵が変更された
:対応方法: 公開鍵と秘密鍵の不一致による現象であるため、現在入っている公開鍵を削除し、build-infraフェーズにて新たに公開鍵を生成する

1.公開鍵の削除
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドをマザーマシンで実行して、ssh接続に使用されるサーバーの公開鍵を削除してください。
::

    rm .hive/(ステージ名)/known_hosts
    rm ~/.ssh/known_hosts

2.build-infraフェーズを実行
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
以下のコマンドをマザーマシンで実行して、build-infraフェーズを実行してください。
::

    hive build-infra

ssh接続の確認
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
上記手順実行後に、以下のコマンドを実行してください。
::

    hive ssh

または
::

    ssh -F .hive/(ステージ名)/ssh_config ホスト名


build-infra の wait_for_connection で timed out waiting for ping module test のエラーになります
----------------------------------------------------------------------------------------------------
:現象: hive build-infra を実行したとき、wait_for_connection タスクで以下のエラーになる

::

    PLAY [wait for connectable] ******

      fatal: [p-hive0.nsag-dev]: FAILED! => changed=false ******
        elapsed: 601
        msg: 'timed out waiting for ping module test: ''ping'''

:原因: ansible の 2.17 以上のバージョンではインストール対象のサーバの Python インタプリタは 3.7 以上である必要がありますが、8系のOSの /usr/libexec/platform-python は 3.6 であり、このエラーが発生しています。
:対応方法: ansible-core のバージョンを 2.16以前にダウングレードしてください。


build-volumes の wait sync before format で ansibleからの応答がなくなります。
----------------------------------------------------------------------------------------------------
:現象: 複数サービスに跨ってマウントされている drbdボリュームに対して、それぞれのサービス定義内で異なるサイズで build-volumes を行うと、wait sync before format タスクのタイミングで応答がなくなる

:原因: 不明
:対応方法: 全てのボリューム定義で同一のサイズで記述してください。
