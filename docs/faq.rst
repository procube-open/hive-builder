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

