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

