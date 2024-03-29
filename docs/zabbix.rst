========================
hive 内 zabbixの利用
========================
リポジトリサーバではサーバと Swarm サービスを監視する Zabbix が稼働しています。

監視内容
=================================
hive 内 zabbix では、以下の状態が発生するとイベントが発生します。
このイベントをメールや Slack などに通知することによって、障害の発生や予兆を検知できます。

- プロセス数が上限の80%を超えると警告
- CPU使用率が5分間継続して90%を超えると警告
- メモリ使用率が5分間継続して90%を超えると警告
- スワップの使用率が5分間継続して50%を超えると警告
- メモリ残量が5分間継続して5Mbytes を切ると警告
- ロードアベレージが5分間継続して1.5 を超えるとと警告
- サーバの時刻が60秒以上ずれると警告
- サーバのZabbixエージェントが3分以上にわたって応答がない場合は警告
- サーバの再起動が行われると警告
- ディスクI/Oの応答時間が15分間に渡って20msを超えている場合は警告
- マウントしているファイルシステムの使用率が80%を超えて、かつ残量が10Gを切ると警告 - マウントしているファイルシステムのinodeの残量が5分間継続して20%を切ると警告
- ネットワークインタフェースのエラー率が5分間継続して2%を超えると警告
- ネットワークインタフェースのリンクダウンがあると警告
- サービスに対応するコンテナが落ちていると警告
- サービスに対応するコンテナが再起動すると警告
- ボリュームの使用率が30分間継続して90%を超えると警告
- DRBDの同期状態が崩れると警告
- Standalone型コンテナの内部サービスが落ちていると警告
- Standalone型コンテナの内部サービスが再起動すると警告
- リポジトリサーバに送られてくるログの中に monitor_error 属性で指定された文字列が含まれていると警告
- SE Linux で設定されたポリシーに違反したアクセスがあると警告
- /etc/passwd の内容が変更されると警告

Slack に通知する
=================================
Zabbix のイベントを Slack に通知するための、設定手順を示します。

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
