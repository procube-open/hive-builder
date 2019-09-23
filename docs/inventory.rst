====================
インベントリ
====================
hive-builder のインベントリは以下の2つからなります。

hive 定義
  サーバやネットワークで構成される基盤（infrastructure）を定義する

サービス定義
  コンテナイメージ、ボリューム、内部ネットワークで構成されるサービスを定義する

.. _defineHive:

hive 定義
====================
hive 定義では基盤を構成するサーバやネットワークを記述します。

IaaS 上にサイトを構築する場合、コンテナ収容サーバは3つの Availability Zone
に分かれて配置されます。以下にその例を示します。

.. image:: imgs/infra.png
   :align: center


hive 定義のフォーマット
---------------------------
hive 定義のフォーマットは以下の通り。

============  ==============  ============  ================================================
パラメータ    選択肢/例       デフォルト    意味
============  ==============  ============  ================================================
plugin        hive_inventory  ..            このファイルがhive定義で有ることを示す
stages        ..              ..            | ステージオブジェクトへの辞書
                                            | private, staging, production の3つが定義できる
============  ==============  ============  ================================================

stages の下にステージ名をキーとしてステージオブエクトを指定します。以下に例を
示します。

::

  plugin: hive_inventory
  stages:
    private:
      provider: vagrant
      separate_repository: False
      cidr: 192.168.0.96/27
      memory_size: 4096
      mirrored_disk_size: 10
      number_of_hosts: 1
    production:
      provider: aws
      separate_repository: False
      cidr: 192.168.0.0/24
      instance_type: t3.medium
      region: ap-northeast-1
      mirrored_disk_size: 20
      repository_instance_type: t3.large
      subnets:
      - cidr: 192.168.0.0/26
        name: subnet-a
        available_zone: ap-northeast-1d
      - cidr: 192.168.0.64/26
        name: subnet-b
        available_zone: ap-northeast-1b
      - cidr: 192.168.0.128/26
        name: subnet-c
        available_zone: ap-northeast-1c

この例では、private ステージと production ステージが定義されています。
private ステージは vagrant で VirtualBox 上に 4G のメモリの
サーバ1台を構築します。

private ステージは vagrant で VirtualBox 上に 4G のメモリの
サーバ1台を構築します。

production ステージでは aws 上に t3.medium のサーバ3台を
東京リージョンの3つの可用性ゾーンに分けて構築します。
リポジトリサーバは3台目のコンテナ収容サーバと兼用し、
t3.large で構築します。

ステージオブジェクト
-----------------------------
ステージオブジェクトのフォーマットは以下の通り。

..  list-table::
    :widths: 18 18 18 50
    :header-rows: 1

    * - パラメータ
      - 選択肢/例
      - デフォルト
      - 意味
    * - provider
      - - aws
        - azure
        - gcp
        - prepared
        - vagrant
      - 必須
      - 基盤を提供するシステム
    * - cidr
      - 192.168.1.0/24
      - 必須
      - ネットワークのアドレス
    * - number_of_hosts
      - 1
      - 3
      - コンテナ収容サーバの台数
    * - separate_repository
      - - True
        - False
      - True
      - リポジトリサーバをコンテナ収容サーバとは別に建てるか否か
    * - disk_size
      - 16
      - プロバイダによる
      - コンテナ収容サーバの起動ディスクのサイズ（GBytes)
    * - repository_disk_size
      - 16
      - プロバイダによる
      - リポジトリサーバの起動ディスクのサイズ（GBytes)
    * - mirrored_disk_size
      - 16
      - 必須
      - drbdで複製同期するディスクのサイズ（GBytes)

上記はプロバイダ共通の属性ですが、プロバイダ固有の属性もあります。
以下にプロバイダ固有の属性をプロバイダごとに説明します。

vagrant プロバイダ
^^^^^^^^^^^^^^^^^^^
vagrant プロバイダ固有の属性には以下のものがあります。

..  list-table::
    :widths: 18 18 18 50
    :header-rows: 1

    * - パラメータ
      - 選択肢/例
      - デフォルト
      - 意味
    * - memory_size
      - 4096
      - Vagrant のデフォルト
      - コンテナ収容サーバに割り当てるメモリのサイズで(MBytes)
    * - repository_memory_size
      - 4096
      - Vagrant のデフォルト
      - リポジトリサーバに割り当てるメモリのサイズで(MBytes)
    * - cpus
      - 2
      - Vagrant のデフォルト
      - サーバに割り当てる仮想CPUの個数

vagrant プロバイダで disk_size, repository_disk_size を省略した場合、Vagrant のデフォルトのサイズになります。

aws プロバイダ
^^^^^^^^^^^^^^^^^^^
aws プロバイダ固有の属性には以下のものがあります。

..  list-table::
    :widths: 18 18 18 50
    :header-rows: 1

    * - パラメータ
      - 選択肢/例
      - デフォルト
      - 意味
    * - instance_type
      - t3.medium
      - 必須
      - コンテナ収容サーバのインスタンスタイプ
    * - repository_instance_type
      - t3.medium
      - 必須
      - リポジトリサーバのインスタンスタイプ

.. 台数をへらす方法：リポジトリサーバの分割、1台だけで動作

サービス定義
====================

(未執筆)


docker のコンテナにはスタンドアローン型とマイクロサービス型の2種類に分類することができます。

=================== ================================================================
型                  説明
=================== ================================================================
スタンドアローン型  - centos:7 などスーパバイザ機能を持った OS のイメージをベースとして構築する
                    - 実行時には /sbin/init を起動する
                    - systemd により内部のプロセスが管理される
マイクロサービス型  - dockerhub のオフィシャルイメージをベースとして構築する
                    - ベースの OS はUbuntuやalpineなどの軽量 OS を採用する
                    - 実行時にはサービスを提供するプロセス1個を起動する
=================== ================================================================


