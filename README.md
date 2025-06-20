# 🔍 GitHub Portfolio Analyzer

あなたの GitHub ポートフォリオを分析し、技術スキルとキャリア戦略を可視化する Python ツールです。

## ✨ 特徴

- 🆓 **完全無料** - GitHub API のみ使用、外部サービス不要
- 📊 **包括的分析** - 全リポジトリの技術スタック、複雑度、カテゴリを自動分析
- 📋 **詳細レポート** - Markdown 形式の読みやすいレポート生成
- 🎯 **具体的推奨** - スキル向上とポートフォリオ強化の提案
- ⚡ **軽量** - 依存関係は `requests` のみ
- 🤖 **Claude Code 連携** - AI による詳細分析とファンタジー称号生成

## 🚀 クイックスタート

### 方法1: 自動セットアップ（推奨）

```bash
# プロジェクトをダウンロード
git clone <this-repository>
cd github-portfolio-analyzer

# 自動セットアップ + 実行
./scripts/run.sh
```

### 方法2: 手動セットアップ

```bash
# 1. プロジェクトセットアップ
git clone <this-repository>
cd github-portfolio-analyzer
python3 scripts/setup.py

# 2. GitHub Token を設定
cp .env.example .env
# .env ファイルを編集してトークンを設定

# 3. 分析実行
python3 scripts/analyze.py
```

### GitHub Token の取得方法

[GitHub Settings > Personal access tokens](https://github.com/settings/tokens?type=beta) から Fine-grained token を作成：

- Repository access: "All repositories" または "Selected repositories"
- Repository permissions: "Contents: Read-only", "Metadata: Read"

📄 結果は `results/` フォルダに保存されます！

## 📊 何が分析される？

### 技術スタック分析

- **プログラミング言語** - 使用率とコード量
- **フレームワーク・ライブラリ** - プロジェクトでの採用状況
- **開発ツール** - Docker、パッケージマネージャーなど

### プロジェクト評価

- **カテゴリ分類** - Frontend/Backend/Data/DevOps
- **複雑度判定** - Low/Medium/High
- **品質指標** - README、テスト、CI/CD の有無

### キャリア推奨

- **スキルギャップ** - 学習すべき技術の特定
- **ポートフォリオ改善** - 作るべきプロジェクトの提案
- **品質向上** - ドキュメント、テスト改善の具体案

## ⚙️ オプション

```bash
# 特定のユーザーを分析
python3 scripts/analyze.py --username octocat

# より多くのリポジトリを分析
python3 scripts/analyze.py --max-repos 500

# JSON形式でも保存
python3 scripts/analyze.py --save-json
```

## 📋 生成されるファイル

結果は `results/` フォルダに保存されます：

- **`report.md`** - メインの分析レポート
- **`claude_analysis_prompt.md`** - Claude Code 用の詳細分析プロンプト
- **`portfolio_analysis.json`** - 詳細データ（--save-json オプション時）

## 🛠️ 技術仕様

- **言語**: Python 3.8+
- **依存関係**: requests >= 2.25.0
- **API**: GitHub REST API v3
- **レート制限**: 5,000 requests/hour（認証あり）

## 📁 プロジェクト構成

```
github-portfolio-analyzer/
├── scripts/           # 実行スクリプト
│   ├── run.sh        # 自動セットアップ + 実行
│   ├── setup.py      # 初回セットアップ
│   └── analyze.py    # 分析実行エントリポイント
├── src/              # ソースコード
│   └── github_analyzer.py
├── results/          # 分析結果（自動生成）
├── requirements.txt  # Python依存関係
├── .env.example     # 環境変数テンプレート
└── README.md        # このファイル
```

## 🐛 トラブルシューティング

### 403 Forbidden エラー

```bash
# トークンの権限を確認
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### Rate Limit エラー

```bash
# 残りAPI制限を確認
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```

### Python環境の問題

```bash
# Python バージョン確認
python3 --version  # 3.8以上が必要

# 依存関係の手動インストール
pip3 install -r requirements.txt
```

## 🤝 Claude Code との連携

このツールで生成された `claude_analysis_prompt.md` を Claude Code で使用すると：

- 📈 **詳細分析** - スキル評価とキャリア戦略の詳細レポート
- 🎓 **学習計画** - 具体的な技術習得ロードマップ
- 💼 **転職戦略** - 市場価値向上のための具体的提案
- 🏆 **開発者称号** - あなたの特徴を表現するユニークなファンタジー称号

### Claude Code での使用例

```bash
# 1. 分析実行
./scripts/run.sh

# 2. 生成されたプロンプトをClaude Codeで使用
# results/claude_analysis_prompt.md の内容をClaude Codeに貼り付け
```

## 📄 ライセンス

MIT License

---

⭐ このツールが役に立ったら、ぜひスターをお願いします！
