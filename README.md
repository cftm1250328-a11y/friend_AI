# 相棒AI - デスクトップコンパニオン

Gemini API を使ったローカル動作の相棒AIです。

## セットアップ

### 1. 依存パッケージのインストール

```bash
cd companion-ai
pip install -r requirements.txt
```

### 2. Gemini API キーの設定

[Google AI Studio](https://aistudio.google.com/app/apikey) でAPIキーを取得し、環境変数に設定します。

**macOS / Linux:**
```bash
export GEMINI_API_KEY=""
# .zshrc や .bashrc に書いておくと永続化できます
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY = ""
# 永続化: システム環境変数から設定
```

---

## 使い方

### 対話モード（ターミナルでチャット）

```bash
python cli/companion_cli.py
```

対話中に使えるコマンド:

| コマンド | 説明 |
|---|---|
| `/profiles` | プロファイル一覧を表示 |
| `/switch coding` | codingプロファイルに切替 |
| `/clear` | 会話履歴をクリア |
| `exit` | 終了 |

### ワンショット質問（エディタ連携）

```bash
# シンプルな質問
python cli/companion_cli.py ask "Pythonのデコレータを説明して"

# ファイルを渡してレビュー
python cli/companion_cli.py ask "このコードの問題点は？" --context "$(cat main.py)"

# プロファイル指定
python cli/companion_cli.py ask "命名を改善して" --profile coding

# クリップボードの内容を渡す（macOS）
python cli/companion_cli.py ask "バグを修正して" --context "$(pbpaste)"
```

### プロファイル操作

```bash
# 一覧表示
python cli/companion_cli.py profiles

# 切替（設定に保存される）
python cli/companion_cli.py switch writing

# 記憶ファイルを確認
python cli/companion_cli.py memory show
python cli/companion_cli.py memory show --profile coding
```

---

## VS Code / Cursor での使い方

`.vscode/tasks.json` が設定済みです。

1. `Ctrl+Shift+P` → `Tasks: Run Task`
2. 以下のタスクが使えます:
   - 🤖 AI: コードをレビュー
   - 🤖 AI: 選択テキストを送る
   - 🤖 AI: 対話モード起動

---

## プロファイルのカスタマイズ

`memories/` フォルダの `.txt` ファイルを直接編集してください。

```
[personality]
語尾は「〜だよ」を使う。

[rules]
回答は必ず日本語で返す。

[knowledge]
私の名前は田中。バックエンドエンジニア歴3年。
```

### 記憶の自動保存

以下のキーワードを含むメッセージを送ると、Geminiが内容を解析して自動保存します。

- 「覚えておいて」
- 「今後は〜して」
- 「話し方を変えて」
- 「記憶して」
- 「忘れないで」

---

## ファイル構成

```
companion-ai/
├── app.py                    # 中央アプリクラス
├── config.json               # 設定ファイル
├── requirements.txt
├── core/
│   ├── gemini_client.py      # Gemini API通信
│   ├── memory_manager.py     # 記憶ファイル管理
│   └── context_builder.py    # プロンプト構築
├── cli/
│   └── companion_cli.py      # CLIエントリーポイント
├── memories/
│   ├── default.txt           # デフォルトプロファイル
│   ├── coding.txt            # コーディング用
│   └── writing.txt           # 文章作成用
└── .vscode/
    └── tasks.json            # VS Codeタスク設定
```

---

## Phase 2 予定（GUI）

- PyQt6 によるチャットウィンドウ
- システムトレイ常駐
- ホットキー呼び出し（Ctrl+Shift+Space）
- 記憶ファイルのGUI編集
