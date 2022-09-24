証明書について
===============================
| hive-builderでは必要に応じてCA局証明書の共有および証明書の生成が可能となっています。
| サーバー間でCA局証明書を共有した上での運用例を解説していきます。

A.コンテナをクライアントとして運用したい場合
--------------------------------------------

| コンテナをクライアントとして運用する場合、
| 「1.CA局証明書の信頼」および「2.コンテナへのクライアント証明書の付与」が可能です。

A-1.CA局証明書の信頼
^^^^^^^^^^^^^^^^^^^^^^^^^^
hiveの機能で共有したいCA局証明書をコンテナのトラストストアに配置して信頼するため、通信相手のサーバー証明書を検証することが可能です。

.. image:: imgs/share_ca.png
   :align: center

| 
| ①CA局の証明書と秘密鍵をmotherマシンのコンテキストディレクトリに配置します。証明書と鍵の配置方法は :ref:`「CA局証明書の共有」 <cashare-CA>` の節を参照してください。
| ②共有したCA局の証明書をコンテナのトラストストアにインストールします。詳しくは :ref:`「ルート証明書信頼設定ビルトインロール」 <cashare-catrust>` の節を参照してください。

A-2.コンテナへのクライアント証明書の付与
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
「1.CA局証明書の信頼」で共有したCA局証明書を用いて生成したクライアントの証明書と秘密鍵をコンテナに付与することで、通信相手とのTLS相互認証が可能となります。

.. image:: imgs/set_client_cert.png
   :align: center

| 
| ①CA局の証明書と秘密鍵をmotherマシンのコンテキストディレクトリに配置します。証明書と鍵の配置方法は :ref:`「CA局証明書の共有」 <cashare-CA>` の節を参照してください。
| ②共有したCA局証明書を用いて、motherマシンでクライアント証明書およびクライアントの秘密鍵を生成します。
| ③共有したCA局の証明書をコンテナのトラストストアにインストールします。詳しくは :ref:`「ルート証明書信頼設定ビルトインロール」 <cashare-catrust>` の節を参照してください。
| ④生成したクライアントの証明書と秘密鍵をコンテナに配置します。
| クライアント証明書の生成の際に指定するドメイン名、サフィックス、有効期限の設定およびコンテナへの証明書の配置については :ref:`「証明書生成ビルトインロール」<cashare-create>` の節を参照してください。


B.コンテナをサーバーとして運用したい場合
--------------------------------------------
コンテナをサーバーとして運用する場合、コンテナへのサーバー証明書の付与が可能です。

.. image:: imgs/set_server_cert.png
   :align: center

| 
| ①CA局の証明書と秘密鍵をmotherマシンのコンテキストディレクトリに配置します。証明書と鍵の配置方法は :ref:`「CA局証明書の共有」 <cashare-CA>` の節を参照してください。
| ②共有したCA局証明書を用いて、motherマシンでサーバー証明書およびサーバーの秘密鍵を生成します。
| ③生成したサーバー証明書と秘密鍵をコンテナに配置します。
| サーバー証明書の生成の際に指定するドメイン名、サフィックス、有効期限の設定およびコンテナへの証明書の配置については :ref:`「証明書生成ビルトインロール」<cashare-create>` の節を参照してください。


.. _cashare-CA:

CA局証明書の共有
----------------------------------------
hive_builderの機能でCA局の証明書を共有することが可能です。(motherマシンへの配置)
下記の形式でインベントリ(例えば、inventory/group_vars/all.yml)に変数hive_ca_certにサーバー証明書を、変数hive_ca_keyにサーバ鍵を定義してください。
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

| CA局の証明書と秘密鍵の共有はbuild-infraフェーズで実行されます。
| (hive_ca_cert, hive_ca_keyが定義されていない場合は、同様のフェーズで新たにCA局証明書と秘密鍵が生成されます。)
| 
| CA局証明書の共有機能を利用する場合は、必ず正しいペアの証明書と鍵の両方定義するようにしてください。
| また、証明書、鍵の内容が全行インデントされていないと正常に動作しないため、ご注意ください。
| 

.. _cashare-create:

証明書生成ビルトインロール
----------------------------------------
| hive_builderのビルトインロールhive-certificateでアプリケーションのサーバに利用できるクライアント(サーバー)証明書を生成することが可能です。
| 下記の形式でインベントリ(例えば、inventory/group_vars/all.yml)に変数certificate_fqdn, sub_prefix, ca_valid_inを定義することで指定のドメイン、サフィックス、有効期限で証明書が生成されます。
| また、証明書と秘密鍵をコピーしたいコンテナのパスは変数cert_dest, key_destで指定してください。
| 以下に例を示します。

::

    certificates:
      - certificate_fqdn: "dnsdist-example-slave.test.procube-demo.jp"
        ca_valid_in: "{{ 365 * 100 }}"
        sub_prefix: /DC={{ hive_name.split('.') | reverse | join('/DC=') }}
        cert_dest: /etc/pki/tls/certs/dnsdist-example-slave.test.procube-demo.jp.crt
        key_dest: /etc/pki/tls/private/dnsdist-example-slave.test.procube-demo.jp.key
      - certificate_fqdn: "ddex.test.procube-demo.jp"
        ca_valid_in: "{{ 365 * 100 }}"
        sub_prefix: /DC={{ hive_name.split('.') | reverse | join('/DC=') }}
        cert_dest: /etc/pki/tls/certs/ddex.test.procube-demo.jp.crt
        key_dest: /etc/pki/tls/private/ddex.test.procube-demo.jp.key

 証明書の生成はbuild-imagesフェーズで実行されます。

| 上記の例で作成される証明書は、
| 1枚目:
| CN=dnsdist-example-slave.test.procube-demo.jp, DC=${ hive_name }, 有効期限=100年
| 2枚目:
| CN=ddex.test.procube-demo.jp, DC=${ hive_name }, 有効期限=10年
| となります。
| sub_prefixについては値のみを定義していただくことで指定の値をDCに設定することができます。(DCを'boo'にしたい時は、sub_prefix: /DC=booとすることで設定可能)
| 
| ビルトインロールhive-certificateを適用するには、サービスのimage.roles属性の下に追加する必要があります。
| 以下に例を示します。

::

  hoge:
    image:
      from: alpine:edge
      roles:
        - python-aptk
        - hive-certificate

.. _cashare-catrust:

ルート証明書信頼設定ビルトインロール
----------------------------------------
| hive_builderのビルトインロールhive-trust-caでは、CA局証明書のコンテナのトラストストアにインストールします。ビルトインロールhive-trust-caを適用するには、サービスのimage.roles属性の下に追加する必要があります。
| 以下に例を示します。

::

  hoge:
    image:
      from: alpine:edge
      roles:
        - python-aptk
        - hive-certificate
        - hive-trust-ca


OSごとのデフォルトトラストストア確認コマンド
------------------------------------------------
| alpine系、ubuntu系、centos系それぞれのOSでhive_builderを用いて環境を構築した際のデフォルトトラストストアを確認する方法を示します。
| 共有したCA局の証明書、証明書生成ビルトインロールで生成されたクライアント(サーバー)の証明書と秘密鍵は、以下のコマンドを実行することで確認することが可能です。

alpine系
::

    ls /etc/pki/ca-trust/source/anchors/

ubuntu系
::

    ls /etc/ssl/certs/

centos系
::

    ls /etc/ssl/certs/