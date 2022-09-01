証明書について
===============================
hive-builderでは必要に応じてCA局証明書の共有および証明書の生成が可能となっています。
複数hive間でCA局証明書を共有したい場合の手続きと証明書生成の流れを以下に示します。

CA局証明書の共有
----------------------------------------
CA局証明書を共有したい場合は、変数hive_ca_certにサーバー証明書を、変数hive_ca_keyにサーバ鍵を設定して、inventory/group_vars/all.ymlに保存してください。
以下に例を示します。
::

    hive_ca_cert: |
      -----BEGIN CERTIFICATE-----
      MIIE6TCCAtECFFq7Q+zMjH+HbQILdIJV+dWM7vIeMA0GCSqGSIb3DQEBCwUAMDAx
      GDAWBgoJkiaJk/IsZAEZFghob2dlaGl2ZTEUMBIGA1UEAwwLY2EuaG9nZWhpdmUw
                                    .
                                    .
      /8RdE53g5XuXaHna5w==
      -----END CERTIFICATE-----

    hive_ca_key: |
      -----BEGIN PRIVATE KEY-----
      MIIJQwIBADANBgkqhkiG9w0BAQEFAASCCS0wggkpAgEAAoICAQC5LaqGi+VrKEt/
      avMBKhnKhJ8Fuo37Zr/bNETEtPTfSnJ4xxVkNaCzksgLTNjPu3iF+rCw3QPUA4Bg
                                    .
                                    .
      K5hfEuwyPeeCaBuJua19DO/fl87L5pU=
      -----END PRIVATE KEY-----

CA局証明書の共有機能を利用する場合は、必ず正しいペアの証明書と鍵の両方定義するようにしてください。
また、証明書、鍵の内容が全行インデントされていないと正常に動作しないため、ご注意ください。

証明書生成ビルトインロール
----------------------------------------
hive_builderのビルトインロールでアプリケーションのサーバに利用できるサーバ証明書を生成することが可能です。
inventory/group_vars/all.ymlで変数hive_certificate_fqdnにサブジェクトを指定することで指定のドメインで証明書が生成されます。
以下に例を示します。
::

    hive_certificate_fqdn: "*.hogehoge.jp"


ルート証明書信頼設定ビルトインロール
----------------------------------------
以下のタスクでビルトインロールで生成したサーバー証明書類をデフォルトトラストストアにインストールします。(alpine系の例)
::  

    - name: install CA cert files(alpine)
      copy:
        src: "{{ hive_safe_ca_dir }}/cacert.pem"
        dest:  /etc/ssl/certs/cacert.pem
        group: root
        owner: root
        mode: 0644
      register: ca_certs_alpine
    - name: install built server cert files(alpine)
      copy:
        src: "{{ hive_safe_ca_dir }}/built-server-cert.pem"
        dest:  /etc/ssl/certs/built-server-cert.pem
        group: root
        owner: root
        mode: 0644
      register: ca_certs_alpine
    - name: install built CA key files(alpine)
      copy:
        src: "{{ hive_safe_ca_dir }}/built-key.pem"
        dest:  /etc/ssl/certs/built-key.pem
        group: root
        owner: root
        mode: 0644
      register: ca_certs_alpine
    - name: install built csr files(alpine)
      copy:
        src: "{{ hive_safe_ca_dir }}/built.csr"
        dest:  /etc/ssl/certs/built.csr
        group: root
        owner: root
        mode: 0644
      register: ca_certs_alpine


OSごとのデフォルトトラストストア確認コマンド
------------------------------------------------
alpine系、ubuntu系、centos系それぞれのOSでhive_builderを用いて環境を構築した際のデフォルトトラストストアを確認する方法を示します。
ビルトインロールにて作成したサーバ証明書、サーバ鍵は以下のコマンドを実行することで確認することが可能です。

alpine系
::

    ls /etc/pki/ca-trust/source/anchors/

ubuntu系
::

    ls /etc/ssl/certs/

centos系
::

    ls /etc/ssl/certs/