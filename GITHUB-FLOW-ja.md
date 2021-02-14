# github flow
このリポジトリは [github flow] (http://scottchacon.com/2011/08/31/github-flow.html) に基づいて管理されています。github flow におけるプルリクエストのブランチの命名規則を以下に示します。

機能種別/$(git describe --tags)/機能名

例えば、 Feature/2.2.12/support-bonding-NIC のようなブランチ名を使用します。

## 機能種別
機能種別には以下のいずれかを指定します。

### Feature
新機能を実装する場合には機能種別に "Feature" を指定します。

### Support
OS、ミドルウェア、ライブラリ、フレームワークなどの新しいバージョンをサポートする場合には機能種別に "Support" を指定します。

### Fix
バグ修正を行う場合には機能種別に "Fix" を指定します。

### Docs
ドキュメント、サンプルを修正する場合には機能種別に "Docs" を指定します。

### Dev
hive-builder 自身の開発にのみ影響する修正を行う場合には機能種別に "Dev" を指定します。

## 機能名
機能名は短い英文です。空白の代わりにハイフン(-)を使用します。