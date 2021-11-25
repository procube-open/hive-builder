====================
タグマッピング
====================

docker のイメージをサービスの元イメージとしてダウンロードする場合に不本意にバージョンアップしていしまい、障害の原因となる場合があります。
タグマッピングでは、これを避けるために docker のイメージのタグを固定する方法を提供します。

タグマッピング指定
=========================

コンテキストディレクトリ(.hive/ステージ名)に tag-mapping.json というファイルを作成し、
その中にタグマッピングオブジェクトを記述することでダウンロードするタグを変換できます。
タグマッピングオブジェクトは、マッピング前のタグをキー、マッピング後のタグを値に持つオブジェクトです。
例えば、以下のように指定することで、 mariadb:10.5 を mariadb:10.5.12 に、
hive3.pdns:5000/image_pdnsrecursor:latest を hive3.pdns:5000/image_pdnsrecursor@sha256:cdf0f7d5ac067a3df4b5e08047e7240d57cc49fff55742e66be5a816cce968c2
に変換することができます。

::

  {
    "mariadb:10.5": "mariadb:10.5.12",
    "hive3.pdns:5000/image_pdnsrecursor:latest": "hive3.pdns:5000/image_pdnsrecursor@sha256:cdf0f7d5ac067a3df4b5e08047e7240d57cc49fff55742e66be5a816cce968c2"
  }

タグマッピングの対象
=========================

以下の3つのケースで docker がイメージをダウンロードする場合にそのイメージのタグ指定がタグマッピングの対象となります。

- build-images フェーズでサービス定義の image.from 属性に指定されいるものをダウンロードする場合
- deploy-services フェーズでサービス定義の image 属性に指定されいるものをダウンロードする場合
- deploy-services フェーズでビルドされてリポジトリサーバに登録されているものをダウンロードする場合

最後のケースでは、変換対象のイメージタグは以下のパターンになります。

::

  ${リポジトリサーバ名}:5000/image_${サービス名}:latest

例えば、サーバが1台で hive名が "pdns"、 ステージが "private" 、サービス名が pdnsrecursor の場合は以下のようなイメージタグになります。

::

  p-hive3.pdns:5000/image_pdnsrecursor:latest

また、リポジトリ上のダイジェスト値を @ に続けて指定することで、最新でない(latestタグが付いていない)ものを指定してダウンロードすることが可能です。
例えば、イメージIDがわかっていれば、

::

  docker inspect --format='{{index .RepoDigests 0}}' イメージID

を実行して、リポジトリ上のダイジェスト値を調べ、

::

  hive3.pdns:5000/image_pdnsrecursor@sha256:cdf0f7d5ac067a3df4b5e08047e7240d57cc49fff55742e66be5a816cce968c2

のように指定することができます。
