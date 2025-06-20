#!/bin/bash
# GitHub Portfolio Analyzer - 実行スクリプト
# Pythonがない人向けの簡単実行スクリプト

set -e

echo "🔍 GitHub Portfolio Analyzer"
echo "=================================="

# Python の存在チェック
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 が見つかりません"
    echo ""
    echo "📦 Python のインストール方法:"
    echo ""
    echo "【macOS (Homebrew)】"
    echo "  brew install python"
    echo ""
    echo "【macOS (公式)】"
    echo "  https://www.python.org/downloads/ からダウンロード"
    echo ""
    echo "【Windows】"
    echo "  https://www.python.org/downloads/ からダウンロード"
    echo "  または Microsoft Store から Python を検索"
    echo ""
    echo "【Ubuntu/Debian】"
    echo "  sudo apt update && sudo apt install python3 python3-pip"
    echo ""
    exit 1
fi

# pip の存在チェック
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 が見つかりません"
    echo "💡 pip をインストールしてください:"
    echo "  python3 -m ensurepip --upgrade"
    exit 1
fi

echo "✅ Python3 $(python3 --version | cut -d' ' -f2) detected"

# プロジェクトディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "📁 プロジェクトディレクトリ: $PROJECT_DIR"

# 初回セットアップ
if [ ! -f "requirements_installed.flag" ]; then
    echo "🚀 初回セットアップを実行中..."
    python3 scripts/setup.py
    
    if [ $? -eq 0 ]; then
        touch requirements_installed.flag
        echo "✅ セットアップ完了"
    else
        echo "❌ セットアップに失敗しました"
        exit 1
    fi
fi

# .env ファイルの確認
if [ ! -f ".env" ]; then
    echo "❌ .env ファイルが見つかりません"
    echo "💡 GitHub Token を設定してください:"
    echo "  1. .env.example を .env にコピー"
    echo "  2. GitHub Token を設定"
    exit 1
fi

# GitHub Token の確認
if ! grep -q "GITHUB_TOKEN=gh_" .env 2>/dev/null; then
    echo "⚠️  GitHub Token が設定されていない可能性があります"
    echo "💡 .env ファイルでGITHUB_TOKENを設定してください"
fi

# 分析実行
echo "🔍 分析を開始します..."
python3 scripts/analyze.py "$@"

echo ""
echo "🎉 分析完了!"
echo "📁 結果は results/ ディレクトリに保存されました"