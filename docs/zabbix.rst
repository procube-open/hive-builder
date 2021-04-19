========================
hive 内 zabbixの設定
========================
リポジトリサーバではサーバと Swarm サービスを監視する Zabbix が稼働しています。
この Zabbix の設定方法を示します。

Slack に通知する
=================================
Slack に通知する手順を示します。

slack 側の設定
---------------------------------

１．Application を作成
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
slack に Application を作成してください。
`Slack の Your Apps <https://api.slack.com/apps>`_ の「Create New App」でアプリケーション「hive_builder_zabbix」を作成してください。この名前は任意のもので構いません。

２．Bots を追加
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Basic InformationのAdd features and functionalityでBotsを選択してください。

３．OAuth & Permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
左メニュー「Features」-「OAuth & Permissions」を選択してください。
「Scopes」で Add an OAuth Scope を実行して chat: writeを追加してください。

４．Access Token コピー
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
「Bot User OAuth Access Token」の Token 文字列をコピーしておいてください（後ほど Zabbix に設定する）。

hive-builder 設定
---------------------------------

１．メディアタイプを作成
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
「Administration」-「Media Types」で（標準添付の）「Slack」を開き、「Parameters」で以下３点を修正してください。

- 「bot_token」に、前項でコピーした Token を入力
- 「channel」に、通知先のチャネル名を入力
- 「zabbix_url」に、「http://127.0.0.1:10052/」を入力

.. note:: zabbix_url は slack に通知されるメッセージに「Open in Zabbx」というリンクで埋め込まれます。
          プロキシサーバなどを使用して hive内 zabbix に外部からアクセスできるようにしている場合は zabbix_url にその URLを設定するほうが良いでしょう。

参考：https://qiita.com/migaras/items/bc0dde421af9650d109c
