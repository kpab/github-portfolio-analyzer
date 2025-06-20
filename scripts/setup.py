#!/usr/bin/env python3
"""
GitHub Portfolio Analyzer - セットアップスクリプト
初回セットアップを簡単にするためのヘルパー
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Python バージョンをチェック"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8以上が必要です")
        print(f"現在のバージョン: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """依存関係をインストール"""
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    
    try:
        print("📦 依存関係をインストール中...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ 依存関係のインストール完了")
        return True
    except subprocess.CalledProcessError:
        print("❌ 依存関係のインストールに失敗しました")
        return False

def setup_env_file():
    """環境設定ファイルを作成"""
    project_root = Path(__file__).parent.parent
    env_example = project_root / ".env.example"
    env_file = project_root / ".env"
    
    if env_file.exists():
        print("✅ .env ファイルは既に存在します")
        return True
    
    if env_example.exists():
        # .env.example をコピー
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env ファイルを作成しました")
        print("📝 .env ファイルを編集してGitHub Tokenを設定してください:")
        print(f"   {env_file}")
        return True
    else:
        print("❌ .env.example ファイルが見つかりません")
        return False

def create_directories():
    """必要なディレクトリを作成"""
    project_root = Path(__file__).parent.parent
    directories = ["results", "docs"]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        print(f"✅ {directory}/ ディレクトリを作成しました")

def main():
    """セットアップメイン処理"""
    print("🚀 GitHub Portfolio Analyzer - セットアップ")
    print("=" * 50)
    
    # Python バージョンチェック
    if not check_python_version():
        return 1
    
    # ディレクトリ作成
    create_directories()
    
    # 依存関係インストール
    if not install_dependencies():
        return 1
    
    # 環境ファイル設定
    if not setup_env_file():
        return 1
    
    print("\n🎉 セットアップ完了!")
    print("\n📋 次の手順:")
    print("1. .env ファイルにGitHub Tokenを設定")
    print("2. python scripts/analyze.py で分析実行")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())