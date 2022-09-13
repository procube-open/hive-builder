証明書について
===============================
hive-builderでは必要に応じてCA局証明書の共有および証明書の生成が可能となっています。
サーバー間でCA局証明書を共有した上での運用例を解説していきます。

コンテナをクライアントとして運用したい場合
--------------------------------------------

コンテナをクライアントとして運用する場合、1.CA局証明書の信頼および2.コンテナへのクライアント証明書の付与ができるようになります。

1.CA局証明書の信頼
hiveの機能でCA局証明書をトラストストアに配置するため、通信相手のサーバー証明書を検証することが可能です。

.. image:: imgs/share_ca.png
   :align: center

put CA cert files → CA局証明書をコンテキストディレクトリ、コンテナのトラストストアに配置する
put CA key files → CA 局の秘密鍵をコンテキストディレクトリに配置する

2.コンテナへのクライアント証明書の付与
「1.サーバー証明書の信頼」を行った上でクライアント証明書を付与することで、TLS相互認証が可能となります。

.. image:: imgs/set_client_cert.png
   :align: center

put CA cert files → CA局証明書をコンテキストディレクトリ、コンテナのトラストストアに配置する
put CA key files → CA 局の秘密鍵をコンテキストディレクトリに配置する
server/client CSP → クライアント(サーバー)証明書のCSRを作成する
server/client certificate → CA局証明書によるクライアント(サーバー)証明書への署名および証明書の生成を行う

コンテナをサーバーとして運用したい場合
--------------------------------------------
コンテナをサーバーとして運用する場合、コンテナへのサーバー証明書の付与が可能です。

.. image:: imgs/set_server_cert.png
   :align: center

put CA cert files → CA局証明書をコンテキストディレクトリ、コンテナのトラストストアに配置する
put CA key files → CA 局の秘密鍵をコンテキストディレクトリに配置する
server/client CSP → クライアント(サーバー)証明書のCSRを作成する
server/client certificate → CA局証明書によるクライアント(サーバー)証明書への署名および証明書の生成を行う

※クライアント(サーバー)証明書およびクライアント(サーバー)の秘密鍵について
---------------------------------------------------------------------------
クライアント(サーバー)証明書およびクライアント(サーバー)の秘密鍵はアプリケーションごとにユーザーがコピーする必要があります。
以下に生成した証明書および秘密鍵をコピーするタスクの例を示します。
::

    - name: install server/client cert file
      copy:
        src: "{{ hive_safe_ca_dir }}/{{ item.certificate_fqdn }}-server-cert.pem"
        dest: /dd-cert.pem
      with_items: "{{ certificates }}"
    - name: install server/client key file
      copy:
        src: "{{ hive_safe_ca_dir }}/{{ item.certificate_fqdn }}-key.pem"
        dest: /dd-key.pem
      with_items: "{{ certificates }}"

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
下記の形式でインベントリ(例えば、inventory/group_vars/all.yml)に変数certificate_fqdn, sub_prefix, ca_valid_inを定義することで指定のドメイン、サブプレフィックス、期間で証明書が生成されます。
以下に例を示します。
::

    certificates:
      - certificate_fqdn: "dnsdist-example-slave.test.procube-demo.jp"
        ca_valid_in: "{{ 365 * 100 }}"
        sub_prefix: /DC={{ hive_name.split('.') | reverse | join('/DC=') }}
      - certificate_fqdn: "ddex.test.procube-demo.jp"
        ca_valid_in: "{{ 365 * 100 }}"
        sub_prefix: /DC={{ hive_name.split('.') | reverse | join('/DC=') }}
    
上記の例で作成される証明書は、
1枚目:
CN=dnsdist-example-slave.test.procube-demo.jp, DC=${ hive_name }, 証明期間=100年
2枚目:
CN=ddex.test.procube-demo.jp, DC=${ hive_name }, 証明期間=10年
となります。
sub_prefixについては値のみを定義していただくことで指定の値をDCに設定することができます。(DCを'boo'にしたい時は、sub_prefix: /DC=booとすることで設定可能)


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
        src: "{{ hive_safe_ca_dir }}/{{ item }}-server-cert.pem"
        dest:  /etc/ssl/certs/built-server-cert.pem
        group: root
        owner: root
        mode: 0644
      register: ca_certs_alpine
      loop: "{{ hive_certificate_fqdn }}"
    - name: install built CA key files(alpine)
      copy:
        src: "{{ hive_safe_ca_dir }}/{{ item }}-key.pem"
        dest:  /etc/ssl/certs/built-key.pem
        group: root
        owner: root
        mode: 0644
      register: ca_certs_alpine
      loop: "{{ hive_certificate_fqdn }}"
    - name: install built csr files(alpine)
      copy:
        src: "{{ hive_safe_ca_dir }}/{{ item }}.csr"
        dest:  /etc/ssl/certs/built.csr
        group: root
        owner: root
        mode: 0644
      register: ca_certs_alpine
      loop: "{{ hive_certificate_fqdn }}"


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