AWS の準備
===============================
aws プロバイダを使用する場合は AWS マネジメントコンソールから hive-builder 用のユーザを作成して、そのアクセスキーを設定してください。
また、暗号化ボリュームを使用する場合は、暗号化鍵を設定してください。

0. AWS CLI v2 のインストール
----------------------------------------
mother マシンに AWS CLI v2（2.12.0 以降）をインストールしてください。
`AWS 公式のインストール手順 <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>`_
に従い、hive を実行する環境の PATH で以下のコマンドが使えることを確認してください。

::

  aws --version

表示が ``aws-cli/2.`` で始まる必要があります。AWS CLI v1 は使用できません。
hive-builder は AWS CLI の自動インストールや ``aws configure`` による設定ファイルの作成は行いません。

1. ユーザグループの作成
----------------------------------------
ユーザにポリシーを適用するためにユーザグループを作成することをおすすめします。
ユーザグループを作成し、アクセス許可に組み込みポリシー AmazonEC2FullAccess および AWSKeyManagementServicePowerUser をアタッチしてください。

EC2 Instance Connect Endpoint の管理・接続には、以下の権限も必要です。
既存のポリシーで許可されている操作を確認し、不足分を追加してください。

- ``ec2:CreateInstanceConnectEndpoint``、``ec2:DescribeInstanceConnectEndpoints``、``ec2:DeleteInstanceConnectEndpoint``
- Endpoint の ENI、タグ、セキュリティグループの作成・参照・削除とルール変更に必要な EC2 権限
- ``ec2-instance-connect:OpenTunnel``（対象 Endpoint と SSH ポートに制限可能）
- サービスリンクロールがまだない場合の ``iam:CreateServiceLinkedRole``（サービス名 ``ec2-instance-connect.amazonaws.com``）

固定 SSH 鍵を使用するため、``ec2-instance-connect:SendSSHPublicKey`` は不要です。
具体的な IAM 設定は
`AWS の権限説明 <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/permissions-for-ec2-instance-connect-endpoint.html>`_
を参照してください。Endpoint の接続権限と作成・削除権限は別です。

2. ユーザの作成
----------------------------------------
以下の手順でユーザを作成してください。

2-1. ユーザを追加ウィザードの起動
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AWS マネジメントコンソールのIAMサービスで、「ユーザ」を開き、「ユーザを追加」ボタンをクリックしてユーザを追加ウィザードの起動してください。

2-2. ユーザを追加
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ユーザ名を指定してください。ユーザ名は hive-builder 用のものであることが分かる名前にすることをおすすめします。
作成時の「AWS アクセスの種類を選択」で「プログラムによるアクセス」を選択してください。
「AWS マネジメントコンソールへのアクセス」は不要ですので、選択しないでください。
入力が完了したら、「次のステップ：アクセス権限」をクリックしてください。

2-2. アクセス権限
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
「ユーザをグループに追加」で手順1. で作成したユーザグループを選択してください。
入力が完了したら、「次のステップ：タグ」をクリックしてください。

2-3. タグ
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
hive-builder では特に必要なタグはありません。業務の都合に応じてタグを設定してください。
入力が完了したら、「次のステップ：確認」をクリックしてください。

2-4. 確認
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
内容を確認し問題がなければ、「ユーザの作成」をクリックしてください。

2-5. アクセスキーの取得
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ユーザを追加に成功すると「成功」が表示され、アクセスキーIDとシークレットアクセスキーが表示されます。
シークレットアクセスキーが ****** となっている場合は「表示」をクリックして内容を表示してください。
アクセスキーIDとシークレットアクセスキーを、hive を実行するシェルの環境変数に設定してください。
リージョンは inventory の ``region`` が優先され、省略時は ``AWS_DEFAULT_REGION`` を使用します。

::

  export AWS_ACCESS_KEY_ID="アクセスキーID"
  export AWS_SECRET_ACCESS_KEY="シークレットアクセスキー"
  export AWS_DEFAULT_REGION="ap-northeast-1"

一時認証情報を使用する場合は ``AWS_SESSION_TOKEN`` も設定してください。
認証情報を inventory やソースコードに記載しないでください。

旧 ``hive set aws_access_key_id`` / ``hive set aws_secret_access_key`` の設定は当面利用できますが非推奨です。
AWS 認証用環境変数（``AWS_SESSION_TOKEN`` を含む）がすべて未設定の場合のみ、
旧設定の完全な鍵ペアにフォールバックし、警告を表示します。
環境変数の片方だけを設定しても、旧設定と組み合わせることはありません。
新方式は ``~/.aws`` や hive の永続設定に認証情報を書き込みません。

3. EBS暗号化用の鍵の設定
----------------------------------------
AWS マネジメントコンソールのKMS（Key Management Service）にアクセスし、AWS マネージド型キーを開き、aws/ebs をクリックしてください。
これは、EBSを暗号化する際にデフォルトで利用されるマスタキーです。
この鍵のARNをコピーし hive定義の kms_key_id に設定してください。変数名が _id となっていますが、設定するのは ID ではなく、 ARN であることに注意してください。
ボリュームを暗号化する際は、以下のように disk_encrypted、mirrored_disk_encrypted、repository_disk_encrypted属性に True を指定してください。

::

    disk_encrypted: True
    mirrored_disk_encrypted: True
    repository_disk_encrypted: True
    kms_key_id: "aws/ebs鍵のARN"

ボリュームを暗号化しない場合はこの設定は不要です。disk_encrypted, mirrored_disk_encrypted, repository_disk_encrypted, kms_key_id 属性を省略してください。

4. EC2 Instance Connect Endpoint による接続
----------------------------------------------------------
``build-infra`` は VPC ごとに Endpoint と専用セキュリティグループを作成し、
先頭の構築対象サブネットに Endpoint を配置します。
同じ構成で再実行した場合は既存 Endpoint を再利用し、停止時は残し、削除時に取り除きます。
同一 VPC の外部管理 Endpoint や、管理対象と設定が異なる Endpoint は自動で流用・置換しません。

mother からは AWS CLI の ``ec2-instance-connect open-tunnel`` を SSH の ProxyCommand として使用し、
EC2 のプライベート IP に接続します。
既存の SSH 鍵、EC2 キーペア、SSH ユーザを引き続き使用するため、AMI への EC2 Instance Connect パッケージ追加は不要です。
EC2 内部の SSH ポート（通常22）は引き続き必要ですが、標準のセキュリティグループではそのポートをインターネットに公開しません。
EIP、公開サービス、registry のネットワーク構成は変更しません。

``hive_ec2_group_rules`` を指定している場合は、独自ルールを維持したまま Endpoint の SG からの SSH 許可を追加します。
独自ルールに残る公開 SSH 許可は自動削除しないため、利用者側で見直してください。
また、``hive_ssh_source_ips`` 等で OS 側の SSH 接続元を制限している場合は、
Endpoint のプライベート IP（配置サブネット）からの通信を許可してください。
接続元は mother のパブリック IP ではなく Endpoint の ENI になります。

``hive ssh``、Ansible と既存の Docker ソケット転送は同じ生成済み SSH 設定を使用します。
そのため後続の操作にも mother の AWS CLI v2 と AWS 認証情報が必要です。
``deploy-services`` のイメージ pull は EC2 上の Docker が registry へ直接接続するため、
イメージ本体は mother の SSH トンネルを通りません。
``build-images`` / ``initialize-services`` の Docker ソケット経由の操作・ファイル転送等は Endpoint を通ります。

Endpoint は管理通信用です。接続は最長1時間、Endpoint あたり同時20接続で、
大容量転送は帯域制限の対象です。長時間トンネルの自動再接続は行いません。
詳細は `AWS の制限・注意点 <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect-with-ec2-instance-connect-endpoint.html>`_
を参照してください。

AWS ロールの check mode は前提条件のみを確認し、AWS リソースの変更・接続待ちをスキップします。
