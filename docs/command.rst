====================
hive コマンド
====================
hiveコマンドはいくつかのサブコマンドを指定して利用します。
以下にその形式とオプションを説明します。

.. argparse::
   :module: hive_builder.hive
   :func: get_parser
   :prog: hive

変数
====================
hiveコマンドは様々な変数を参照しながら動作します。変数の値は以下の順序で決定します。

- root_dir にカレントディレクトリをセット
- install_dir にhive がインストールされているディレクトリをセット
- local_python_path に python コマンドの絶対パスをセット
- コマンドラインで --root-dir が指定されている場合は、 root_dir にセット
- context_dir に {root_dir}/.hive' をセット
- 永続変数を {context_dir}/persistent_values.yml からロード
- 変数stageの値が設定されていなければデフォルト値をセット
- 永続変数でglobal値を持つものをセット
- 永続変数でstage固有値を持つものをセット
- コマンドラインの root_dir 以外の変数値をセット
- デフォルト値のうちまだ設定されていないものをセット
- フェーズを実行するサブコマンドの場合は phase 変数にサブコマンド名をセット

ログレベル
====================
--verbose を指定するか set サブコマンドで verbose 変数に True を設定することでデバッグログを出力することができます。


.hive ディレクトリ
====================
hive コマンドを実行するとカレントディレクトリの下に .hive ディレクトリが生成され、様々なコンテキストを保存します。
- .hive/persistent_values.yml にはhiveの永続変数が保存されます。

作業ディレクトリ
====================
hive コマンドを実行すると/var/tmp/hiveディレクトリが生成され、hive の作業ディレクトリとして利用されます。

マザーマシンからサーバへのアクセス
===================================
マザーマシンからは各サーバの ssh にアクセスします。
build-infra の playbook では、処理の最後に ssh_config をコンテキストディレクトリに出力します。
以降の ansible からのssh アクセスはこのファイルに基づいて行われるため、サーバ名がDNSやhostsファイルで解決できる必要はありません。
build-images のフェーズでは、イメージ構築用の playbook をリポジトリサーバに転送してコンテナイメージを構築します。

ステージング
====================
ステージングはインベントリ内でステージごとのグループを定義し、そのグループ名で対象となるホストを切り替えます。
ステージ名は hive  コマンドの -s オプションでにより指定できます。
有効なステージの値は production, staging, private であり、ステージのデフォルト値は private です。

::

  hive set stage ステージ名

を実行することで、以降のhiveコマンド実行時のステージを指定できます。
このコマンドにより、ステージ名が .hive/persistent_values.yml に保存されます

ステージングの切り替え
===================================
グループ名でインベントリ内のどのホストを対象とするかを切り替えるので、
同一の役割のホストでもステージが異なる場合はその名前が異なる必要があり、
staging ステージのホスト名には s-、 privaite ステージのホスト名には p- のプリフィックスを付与されます。
サービス、ボリューム、イメージ、ネットワークなどのリソースはデフォルトですべてのステージで有効です。available_on を指定して、
有効なステージを指定することができます。
プロジェクトのロール内でステージ固有の挙動を行う場合は、hive_stage 変数の値で挙動を切り替える必要があります。


hive コマンドを使わずに playbook を実行
=========================================
hive コマンドを使わずに playbook を実行する場合は、ANSIBLE_CONFIG環境変数に/var/tmp/hive/ansible.cfgを
指定し、ansibleの変数を/var/tmp/hive/vars.ymlから読み込んでください。また、 -l オプションにステージ名を
指定し対象を絞り込んでください。
例えば、private ステージで test.yml を実行する場合は、
以下のように指定してください。

::

  ANSIBLE_CONFIG=/var/tmp/hive/ansible.cfg ansible-playbook -e @/var/tmp/hive/vars.yml -l private test.yml

ただし、この場合、hiveの組み込み変数のいくつかが使えません。hive の組み込み変数を
参照したい場合は、playbook で以下のように変数の定義を読み込んでください。

::

  vars_files:
  - "{{ hive_playbooks_dir }}/group_vars/hosts.yml"

hive コマンドを使わずに ssh/scp を実行
=========================================
hive コマンドを使わずに ssh/scp を実行する場合は、コンテキストディレクトリの ssh_config ファイルを
使用してください。例えば、hive0.pdns の /etc/hosts ファイルをカレントディレクトリにコピーする場合は、
以下のコマンドを実行してください。

::

  scp -F .hive/production/ssh_config hive0.pdns:/etc/hosts .

