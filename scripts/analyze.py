#!/usr/bin/env python3
"""
GitHub Portfolio Analyzer - Entry Point
使いやすいインターフェースでGitHubポートフォリオ分析を実行
"""

import sys
import os
import subprocess
from pathlib import Path

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from github_analyzer import main, GitHubAnalyzer
except ImportError as e:
    print(f"❌ インポートエラー: {e}")
    print("💡 以下のコマンドで依存関係をインストールしてください:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

def check_dependencies():
    """依存関係をチェック"""
    try:
        import requests
        return True
    except ImportError:
        return False

def setup_output_directory():
    """結果出力ディレクトリを作成"""
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir

def main_wrapper():
    """メイン関数のラッパー"""
    print("🔍 GitHub Portfolio Analyzer")
    print("=" * 50)
    
    # 依存関係チェック
    if not check_dependencies():
        print("❌ 必要なライブラリがインストールされていません")
        print("💡 以下のコマンドで依存関係をインストールしてください:")
        print(f"   pip install -r {project_root}/requirements.txt")
        return 1
    
    # 出力ディレクトリ設定
    results_dir = setup_output_directory()
    
    # 現在のディレクトリを結果ディレクトリに変更
    original_cwd = os.getcwd()
    try:
        os.chdir(results_dir)
        
        # .env ファイルを読み込み
        env_file = project_root / ".env"
        if env_file.exists():
            print("✅ .env ファイルを読み込みました")
            # .env ファイルを手動で読み込み
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        
        # 環境変数の確認
        if not os.getenv('GITHUB_TOKEN'):
            print("⚠️  GitHub Token が設定されていません")
            print(f"💡 {project_root}/.env ファイルにGITHUB_TOKENを設定してください")
            return 1
        
        # メイン処理実行
        main()
        
        print(f"\n📁 結果が保存されました: {results_dir}")
        print("📋 生成されたファイル:")
        for file in results_dir.glob("*"):
            print(f"   - {file.name}")
            
    finally:
        os.chdir(original_cwd)
    
    return 0

if __name__ == "__main__":
    sys.exit(main_wrapper())