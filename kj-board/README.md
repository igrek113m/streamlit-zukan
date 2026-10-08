# KJ Board

**KJ Board** は、知識整理・技術解説・研修・アイデア発散向けのインタラクティブな付箋ボードです。Streamlit Components v2 上で動作し、各付箋の要約をボードに、詳細をポップアップに表示できます。ボード全体を JSON に保存できるほか、各付箋の詳細を PDF にまとめられます。

> アプリケーションの Python エントリーポイントは **`kj_board_app.py`** です。旧 `kj_session_app.py` からファイル名を変更しています。

## 主な機能

| 機能 | 説明 |
| --- | --- |
| 付箋の作成 | Markdown / Code / Mermaid / Image の4種類 |
| 編集モード | 上部操作パネルから付箋を追加し、ポップアップで詳細やソースを編集 |
| 表示モード | 付箋をダブルクリックして Markdown・コード・図・画像を表示 |
| Z順 | 選択した付箋を前面・背面・最前面・最背面へ移動 |
| 配置 | キャンバス上の移動、横スクロール、全画面表示 |
| 履歴 | Undo / Redo |
| 保存・読込 | JSON エクスポート / インポート |
| PDF保存 | 位置順の**タイトル＋内容・メモの目次**に続けて、各付箋の詳細を出力 |
| AIオーサリング | `skills/kj-board-authoring/` を使って、AIエージェントにボードJSONの制作を依頼 |

グループ化・グループ接続機能は現行版では提供していません。旧形式の `groups` / `edges` は読み込み時に破棄されます。

## 動作環境

- Python 3.10 以降（推奨: 3.11 以降）
- Streamlit **1.52 以降 / 2.0 未満**（Components v2を利用）
- 最新の Chrome / Edge / Firefox などのブラウザ
- 初回レンダリング時に CDN へのアクセスが必要（下記参照）

## セットアップと起動

```bash
# このリポジトリに移動
cd kj-board

# 仮想環境を作成（Linux/macOS）
python -m venv .venv
source .venv/bin/activate

# 依存関係をインストール
python -m pip install -r requirements.txt

# 起動
streamlit run kj_board_app.py
```

Windows PowerShell の場合は、仮想環境を `.venv\Scripts\Activate.ps1` で有効化してください。実行後、ターミナルに表示される `http://localhost:8501` などの URL にアクセスします。

## ボードの使い方

### 1. 付箋を追加する

上部の **「付箋を追加」** でタイプ、タイトル、内容・メモ、色を指定し、**`＋追加`** を押します。専用の編集ポップアップが開くため、詳細を入力して **「保存」** します。追加時点ではなく、ポップアップ保存時に付箋を確定します。

| タイプ | ボードに表示するもの | ポップアップで設定・表示するもの |
| --- | --- | --- |
| **Markdown** | タイトル・内容／メモ | `markdownSource` を Markdown としてレンダリング。GFMテーブルにも対応 |
| **Code** | タイトル・内容／メモ | コード本文 `inline` と `language`。表示モードで構文ハイライト（ダーク配色） |
| **Mermaid** | タイトル・内容／メモ | Mermaid記法の `inline`。表示モードで図を描画 |
| **Image** | タイトル・内容／メモとサムネイル | `imageUrl` に画像URL。表示モードで画像ビューア |

色は **Yellow / Green / Blue / Pink / Orange / Purple** から選べます。タイトルと内容・メモは改行を保持できます（操作パネルの入力欄は省スペースの1行表示です）。

### 2. 編集・閲覧・配置を切り替える

- **編集モード**：付箋のドラッグ移動、選択、Z順変更、ダブルクリックによる詳細編集
- **表示モード**：付箋をダブルクリックするとレンダリング済み詳細がポップアップ
- **Z順**：選択中の付箋を「前面へ」「背面へ」「最前面へ」「最背面へ」移動
- **全画面／横スクロール**：広いキャンバスの閲覧に利用
- **Undo / Redo**：直近の編集を戻す・進める

### 3. JSON を保存・読み込む

上部の **「保存」/「読込」** からボードJSONをローカル保存・復元します。JSONには付箋のタイトル、要約、タイプ別ソース、画像URL、付箋色、座標、Z順が含まれます。

スキーマの実例は [`skills/kj-board-authoring/references/reference-board.json`](skills/kj-board-authoring/references/reference-board.json) を、詳しいフィールド仕様は [`board-format.md`](skills/kj-board-authoring/references/board-format.md) を参照してください。

### 4. PDF に出力する

画面右上の **「PDF」** ボタンを押すと、セッションタイトル、付箋一覧の目次、および各付箋の詳細をA4 PDFに出力します。付箋は **上から下、同じ段では左から右** の順に並びます。Markdown・Code・Mermaid・Image をタイプ別に描画します。

PDFはブラウザ側でページを画像としてキャプチャしているため、**生成PDFのテキストは必ずしも検索・コピー可能ではありません**。外部画像・MermaidのPDF化はブラウザや画像配信元の制約に左右される場合があります。

## AI によるボード制作（Agent Skill）

`skills/kj-board-authoring/SKILL.md` を AI エージェントの指示として読み込ませ、テーマ・対象読者・付箋枚数・教育目標を伝えると、本アプリが読めるボードJSONを設計できます。

このスキルは、添付の旧 `kj-session-board-json-authoring` を**リネーム・再編成**したものです。旧版の核となる「Popup-first（三階層情報設計）」「意味的類縁度（Affinity）」「空間配置」「品質ゲート」を継承しました。現行アプリで廃止された **groups / edges** の操作・JSON は含めません。

詳細は [`authoring-guidelines.md`](skills/kj-board-authoring/references/authoring-guidelines.md) を参照してください。参照ボードは旧スキルの **Mermaid Sequence Diagram 12付箋**から変換しており、解説・ソース・描画を横に、4つの学習段階を縦に配置しています。

例：

> kj-board-authoring スキルに従い、「シーケンス図の書き方」を初心者向けに8枚の付箋で解説するボードJSONを作成してください。付箋は短く興味を引く表現にし、Markdown / Mermaid / Code を織り交ぜてください。

```bash
# 参照ボードJSONの構造を確認
python skills/kj-board-authoring/scripts/validate_board.py \
  skills/kj-board-authoring/references/reference-board.json --strict

# 生成した自分のボードJSONを検証
python skills/kj-board-authoring/scripts/validate_board.py path/to/board.json --strict
```

バリデータは Python 標準ライブラリのみで動作します。検証後、アプリの「読込」からJSONを開きます。

## ディレクトリ構成

```text
kj-board/
├── kj_board_app.py
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── .github/workflows/validate.yml
├── tests/test_board_validator.py
└── skills/
    └── kj-board-authoring/
        ├── SKILL.md
        ├── references/
        │   ├── board-format.md
        │   ├── authoring-guidelines.md
        │   └── reference-board.json
        └── scripts/
            └── validate_board.py
```

## ネットワークと運用上の注意

ブラウザで利用するリッチ表示には以下の CDN 依存があります。**閉域ネットワークではライブラリのローカル配布化が必要**です。

- `marked` v16（Markdown）
- `mermaid` v11（図）
- `highlight.js` v11.11.1（コード）
- `html2canvas` v1.4.1、`jsPDF` v2.5.2（PDF）

PDF用の外部画像は Streamlit サーバー側でも取得します。**不特定多数が利用できる公開環境で、信頼できないJSONや画像URLを無制限に受け入れないでください**。画像 URL の取得先制御、プライベートIP/localhostへのアクセス制限、リクエスト制限、認証等を実装してから公開することを推奨します。Markdown/HTMLの取り扱いについても、信頼できない投稿を処理する場合はHTMLサニタイズ等を追加してください。

## GitHubへの登録

GitHubで空のリポジトリを作成してから、次を実行します。`<YOUR-REPOSITORY-URL>` は作成したリポジトリの URL に置き換えてください。

```bash
git init
git add .
git commit -m "Initial release of KJ Board"
git branch -M main
git remote add origin <YOUR-REPOSITORY-URL>
git push -u origin main
```

GitHub Actions は Python構文、埋め込みJavaScript構文、サンプルJSONとバリデータのテストを自動検証します。実際のStreamlit画面とPDF出力のブラウザ検証は別途実施してください。

## ライセンス

[MIT License](LICENSE)。第三者のCDNライブラリや外部画像には、それぞれのライセンス・利用条件が適用されます。
