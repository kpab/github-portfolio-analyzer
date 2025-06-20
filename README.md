# 🔍 GitHub Portfolio Analyzer

あなたの GitHub ポートフォリオを分析し、技術スキルとキャリア戦略を可視化する Python ツールです。

## ✨ 特徴

- 🆓 **完全無料** - GitHub API のみ使用、外部サービス不要
- 📊 **包括的分析** - 全リポジトリの技術スタック、複雑度、カテゴリを自動分析
- 📋 **詳細レポート** - Markdown 形式の読みやすいレポート生成
- 🎯 **具体的推奨** - スキル向上とポートフォリオ強化の提案
- ⚡ **軽量** - 依存関係は `requests` のみ

## 🚀 クイックスタート

### 1. インストール

```bash
git clone <this-repository>
cd github-portfolio-analyzer
pip install -r requirements_analyzer.txt
```

### 2. GitHub Token の設定

[GitHub Settings > Personal access tokens](https://github.com/settings/tokens?type=beta) から Fine-grained token を作成：

- Repository access: "All repositories"
- Repository permissions: "Contents: Read-only"

### 3. 実行

```bash
# .envファイルにトークンを設定
echo "GITHUB_TOKEN=your_token_here" > .env

# 分析実行
python github_analyzer.py
```

📄 `report.md` ファイルに詳細な分析結果が生成されます！

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
# より多くのリポジトリを分析
python github_analyzer.py --max-repos 500

# トークンを直接指定
python github_analyzer.py --token your_github_token

# カスタム出力ファイル名
python github_analyzer.py --output my_report.md

# JSON形式でも保存
python github_analyzer.py --save-json
```

## 📋 生成されるファイル

- **`report.md`** - メインの分析レポート
- **`claude_analysis_prompt.md`** - Claude 用の詳細分析プロンプト
- **`developer_card.html`** - 視覚的なスキルカード
- **`portfolio_analysis.json`** - 詳細データ（--save-json オプション時）

## 🛠️ 技術仕様

- **言語**: Python 3.7+
- **依存関係**: requests >= 2.25.0
- **API**: GitHub REST API v3
- **レート制限**: 5,000 requests/hour（認証あり）

## 🐛 トラブルシューティング

### 403 Forbidden エラー

- GitHub トークンの権限を確認
- Contents: Read-only 権限が設定されているか確認

### Rate Limit エラー

- 1 時間待ってから再実行
- `--max-repos` で分析対象を制限

## 🤝 Claude Code との連携

このツールで生成された `claude_analysis_prompt.md` を Claude Code で使用すると：

- 📈 **詳細分析** - スキル評価とキャリア戦略の詳細レポート
- 🎓 **学習計画** - 具体的な技術習得ロードマップ
- 💼 **転職戦略** - 市場価値向上のための具体的提案
- 🏆 **開発者称号** - あなたの特徴を表現するユニークな称号

## 📄 ライセンス

MIT License

---

⭐ このツールが役に立ったら、ぜひスターをお願いします！
