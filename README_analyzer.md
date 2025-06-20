# 🔍 GitHub Portfolio Analyzer (Claude Code版)

Claude Code環境でGitHubのポートフォリオを分析し、技術的傾向とスキルギャップを可視化するPythonスクリプトです。

## 特徴

- **無料**: GitHub REST APIのみを使用（Anthropic API不要）
- **包括的分析**: 全リポジトリの技術スタック、複雑度、カテゴリを分析
- **詳細レポート**: Markdown形式で読みやすいレポートを生成
- **推奨事項**: スキル向上とポートフォリオ強化の具体的な提案
- **軽量**: 必要な依存関係は requests のみ

## セットアップ

1. 依存関係をインストール:
```bash
pip install -r requirements_analyzer.txt
```

2. GitHub Personal Access Tokenを取得:
   - [GitHub Settings > Developer settings > Personal access tokens > Fine-grained tokens](https://github.com/settings/tokens?type=beta)
   - "Generate new token" をクリック
   - Repository access で "All repositories" を選択
   - Repository permissions で "Contents: Read-only" を選択
   - トークンを生成してコピー

## 使用方法

### 基本的な使用方法

1. `.env`ファイルを作成してトークンを設定:
```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集してトークンを設定
# GITHUB_TOKEN=your_actual_token_here
```

2. 分析を実行:
```bash
# 分析実行（デフォルト: 100リポジトリ）
python github_analyzer.py

# 結果: report.md が生成される
```

### オプション付きの使用方法

```bash
# 全リポジトリを分析（最大500個）
python github_analyzer.py --max-repos 500

# トークンを直接指定
python github_analyzer.py --token your_github_token_here

# カスタム出力ファイル名
python github_analyzer.py --output my_portfolio_report.md

# 詳細分析結果をJSONでも保存
python github_analyzer.py --save-json

# すべてのオプションを組み合わせ
python github_analyzer.py --token your_token --max-repos 500 --output detailed_report.md --save-json
```

## 分析内容

### 📊 Portfolio Overview
- 総リポジトリ数、スター数、フォーク数
- 平均スター数

### 💻 技術スタック分析
- **プログラミング言語**: バイト数に基づく使用率ランキング
- **フレームワーク・ライブラリ**: プロジェクト数でのランキング

### 🎯 プロジェクト分析
- **カテゴリ別分布**: Frontend, Backend, Data/ML, DevOps, Other
- **複雑度分布**: Low, Medium, High（言語数、フレームワーク数、ファイルサイズ、人気度で算出）

### 🎯 推奨事項
- **技術スキル向上**: 学習すべき言語・フレームワーク
- **ポートフォリオ強化**: 不足している分野のプロジェクト提案
- **コード品質向上**: README改善、テストコード、ドキュメント作成

## 出力例

```markdown
# 🚀 GitHub Portfolio Analysis Report
生成日時: 2024-06-20 14:30:15

## 📊 Portfolio Overview
- **総リポジトリ数**: 45
- **総スター数**: 128
- **総フォーク数**: 23
- **平均スター数**: 2.8

## 💻 技術スタック分析

### プログラミング言語 (上位10位)
 1. **Python**: 45.2% (234,567 bytes)
 2. **JavaScript**: 28.1% (145,890 bytes)
 3. **TypeScript**: 12.3% (63,821 bytes)
 ...

### フレームワーク・ライブラリ (上位10位)
 1. **React**: 8 projects (17.8%)
 2. **Django**: 5 projects (11.1%)
 3. **FastAPI**: 3 projects (6.7%)
 ...
```

## 技術的特徴

### 自動検出される技術要素

- **言語**: GitHub API の言語統計を使用
- **フレームワーク**: package.json, requirements.txt, go.mod, Cargo.toml を解析
- **ツール**: Docker, Docker Compose, npm/yarn, pip, Go Modules, Cargo を検出
- **カテゴリ**: 言語とフレームワークの組み合わせから推定
- **複雑度**: 多次元スコアリング（言語数、フレームワーク数、サイズ、人気度）

### ファイル分析対象

- `package.json` - Node.js依存関係とフレームワーク
- `requirements.txt` - Python依存関係
- `go.mod` - Go モジュール
- `Cargo.toml` - Rust依存関係
- `Dockerfile`, `docker-compose.yml` - コンテナ化
- `README.md` - プロジェクト説明

## API制限について

- GitHub API の rate limit: 認証ありで 5,000 requests/hour
- 本スクリプトは効率的にAPIを使用：
  - リポジトリ一覧: ~5 requests (500リポジトリの場合)
  - 各リポジトリ分析: ~10 requests
  - 合計: ~500リポジトリで約 5,005 requests (1時間の制限内)

## トラブルシューティング

### 403 Forbidden エラー
```
❌ GitHub API エラー: 403 Client Error: Forbidden
```
- GitHub Personal Access Token が無効または権限不足
- Contents: Read-only権限が設定されているか確認

### Rate Limit エラー
```
❌ GitHub API エラー: 403 Client Error: rate limit exceeded
```
- 1時間待ってから再実行
- `--max-repos` オプションでリポジトリ数を制限

### 空のレポート
- プライベートリポジトリのアクセス権限を確認
- GitHub Personal Access Token の Repository access 設定を確認

## Claude Code での活用

このスクリプトをClaude Codeで実行することで：

1. **分析結果の解釈**: 生成されたレポートを Claude が詳しく解説
2. **具体的な学習計画**: 推奨事項を基にした詳細な学習ロードマップ作成
3. **プロジェクト提案**: 不足分野を補完する具体的なプロジェクトアイデア
4. **コードレビュー**: 既存プロジェクトの改善点を詳細分析

## ライセンス

MIT License