=========================
フェーズ
=========================
ここでは、 hive-builder のサイト構築機能をフェーズごとに説明します。

build-infra
=========================
ホストとネットワークを作成し、環境を構築します。

（未執筆）

プロバイダ
--------------------
build-infraフェーズでは、サーバを配備する基盤のプロバイダをステージオブジェクトの provider 属性に指定することで、様々なプロバイダを利用できます。
プロバイダとして有効な値は以下のとおりです。

============= ===============================================
プロバイダID  説明
============= ===============================================
vagrant       Vagrant for VirtualBox/libvirt on local machine
aws           Amazon Web Service
azure         Microsoft Azure（未実装）
gcp           Gooble Computing Platform
openstack     Some OpenStack Provider（未実装）
prepared      sshでアクセス可能なサーバ群
kickstart     OSが未インストールの物理サーバ
============= ===============================================

vagrant
^^^^^^^^^^^^^^
プロバイダIDにvagrant を指定した場合、vagrant のプロバイダは
libvirt, VirtualBox の順に試して、成功したものを使用します。

setup-hosts
=========================
ホストを設定します。

（未執筆）

build-images
=========================
コンテナイメージをビルドします。サービス定義で image 属性の下にfrom属性を指定した場合にビルドの対象となります。
build-images フェーズを複数回行う場合、前回のビルドに利用したコンテナを再利用することでビルドにかかる時間を短縮しています。
このため、image 属性の配下の属性を変更して build-images をやり直しても反映されません。
また、roles に指定したタスクについて内容が減少する方向の変更が行われた場合、反映されません。
たとえば、ファイルのインストール先が変更された場合や、設定ファイルの行追加をやめた場合などがこれに該当します。
このような場合は、 hive ssh でリポジトリサーバにログインし、 docker rm で build_サービス名の名前のコンテナを削除してから build-images をやり直してください。

build-networks
=========================
内部ネットワークを構築します。

（未執筆）

build-volumes
=========================
ボリュームを構築します。

（未執筆）

deploy-services
=========================
サービスを配備します。

（未執筆）

initialize-services
=========================
サービスを初期化します。

（未執筆）

docker コネクション
--------------------
initialize-serivices フェーズでは、ssh tunneling でサーバの /var/run/docker.sock
をマザーマシンの /var/tmp/hive/docker.sock@サーバ名 に転送します。
docker コネクションを使用してサービスのコンテナ内に対して ansible を実行する場合には、
最初に docker service ps でコンテナが動作しているノードを特定してから、ssh tunneling で
転送されているソケットに接続する必要があります。
以下に playbook の例を示します。

::

    - name: setup awx project
      gather_facts: False
      hosts: awx_web,awx_task

      tasks:
      - name: get server
        delegate_to: "{{ groups['first_hive'] | intersect(groups[hive_stage]) | first }}"
        shell: docker service ps --format "{% raw %}{{.Name}}.{{.ID}}@{{.Node}}{% endraw %}.{{ hive_name }}" --filter desired-state=running --no-trunc {{ inventory_hostname }}
        changed_when: False
        check_mode: False
        register: hive_safe_ps

      - name: setup docker socket
        set_fact:
          ansible_docker_extra_args: "-H unix://{{ hive_temp_dir }}/docker.sock@{{ hive_safe_ps.stdout.split('@') | last }}"
          ansible_connection: docker
          ansible_host: "{{ hive_safe_ps.stdout.split('@') | first }}"

      - name: copy project for fun
        copy:
          dest: /var/lib/awx/project
          src: fun

