#!/usr/bin/env python3
"""
GitHub Portfolio Analyzer for Claude Code
無料でGitHubリポジトリを分析し、技術的傾向とスキルギャップを可視化
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import argparse
from typing import Dict, List, Any, Optional
import re

# .envファイルの読み込み
def load_env_file(env_path: str = '.env'):
    """Load environment variables from .env file"""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


class GitHubAnalyzer:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_user_info(self) -> Dict[str, Any]:
        """認証されたユーザー情報を取得"""
        response = self.session.get('https://api.github.com/user')
        response.raise_for_status()
        return response.json()
    
    def get_all_repositories(self, max_repos: int = 500) -> List[Dict[str, Any]]:
        """全リポジトリを取得（ページネーション対応）"""
        repos = []
        page = 1
        per_page = 100
        
        print(f"📦 リポジトリを取得中...")
        
        while len(repos) < max_repos:
            params = {
                'type': 'all',
                'sort': 'updated',
                'per_page': per_page,
                'page': page
            }
            
            response = self.session.get('https://api.github.com/user/repos', params=params)
            response.raise_for_status()
            
            page_repos = response.json()
            if not page_repos:
                break
                
            repos.extend(page_repos[:max_repos - len(repos)])
            print(f"  📋 {len(repos)} 個のリポジトリを取得済み")
            page += 1
            
        return repos
    
    def get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """リポジトリの言語統計を取得"""
        try:
            response = self.session.get(f'https://api.github.com/repos/{owner}/{repo}/languages')
            response.raise_for_status()
            return response.json()
        except:
            return {}
    
    def get_repository_contents(self, owner: str, repo: str, path: str = '') -> List[Dict[str, Any]]:
        """リポジトリの内容を取得"""
        try:
            response = self.session.get(f'https://api.github.com/repos/{owner}/{repo}/contents/{path}')
            response.raise_for_status()
            return response.json()
        except:
            return []
    
    def get_repository_stats(self, owner: str, repo: str) -> Dict[str, Any]:
        """リポジトリの統計情報を取得（コミット数、コントリビューター数など）"""
        stats = {
            'commit_count': 0,
            'contributors_count': 0,
            'branches_count': 0,
            'readme_exists': False,
            'has_tests': False,
            'has_ci': False
        }
        
        try:
            # 基本的な存在チェックのみ（効率化）
            contents_response = self.session.get(f'https://api.github.com/repos/{owner}/{repo}/contents')
            if contents_response.status_code == 200:
                contents = contents_response.json()
                file_names = [item['name'].lower() for item in contents if item['type'] == 'file']
                
                # README存在チェック
                readme_files = ['readme.md', 'readme.rst', 'readme.txt']
                stats['readme_exists'] = any(readme in file_names for readme in readme_files)
                
                # Dockerfile存在チェック
                stats['has_ci'] = 'dockerfile' in file_names
                
                # テスト関連ファイル
                test_indicators = ['test', 'spec', 'tests', '__tests__']
                stats['has_tests'] = any(indicator in name for name in file_names for indicator in test_indicators)
            
            # コミット数は基本情報から推定（API効率化）
            # 更新頻度から大まかに推定
            # リポジトリサイズから推定（簡易版）
            repo_size = getattr(self, 'current_repo_size', 100)  # KB
            stats['commit_count'] = max(1, repo_size // 10)  # サイズから大まかに推定
                    
        except Exception as e:
            print(f"    ⚠️  統計取得エラー: {e}")
        
        return stats

    def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """特定ファイルの中身を取得"""
        try:
            response = self.session.get(f'https://api.github.com/repos/{owner}/{repo}/contents/{path}')
            response.raise_for_status()
            file_data = response.json()
            
            if file_data.get('type') == 'file' and file_data.get('size', 0) < 50000:  # 50KB制限
                import base64
                content = base64.b64decode(file_data['content']).decode('utf-8', errors='ignore')
                return content[:10000]  # 最大10000文字
        except:
            pass
        return None
    
    def analyze_repository_tech_stack(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """リポジトリの技術スタックを分析"""
        try:
            owner = repo['owner']['login']
            name = repo['name']
            
            # 基本情報
            analysis = {
                'name': name,
                'description': repo.get('description', '') or '',
                'primary_language': repo.get('language') or 'Unknown',
                'size': repo.get('size', 0),
                'stars': repo.get('stargazers_count', 0),
                'forks': repo.get('forks_count', 0),
                'created_at': repo.get('created_at', ''),
                'updated_at': repo.get('updated_at', ''),
                'topics': repo.get('topics', []) or [],
                'languages': {},
                'frameworks': [],
                'tools': [],
                'complexity': 'low',
                'category': 'other'
            }
            
            # 言語統計取得
            languages = self.get_repository_languages(owner, name)
            analysis['languages'] = languages
            
            # リポジトリ統計取得（効率化のため一部のみ）
            self.current_repo_size = analysis['size']  # サイズを渡す
            stats = self.get_repository_stats(owner, name)
            analysis.update(stats)
            
            # 重要ファイルの分析（効率化）
            tech_stack_files = ['package.json', 'requirements.txt', 'go.mod', 'Cargo.toml']
            config_files = ['docker-compose.yml', 'Dockerfile']
            
            # 技術スタック検出用ファイルのみ内容を読み込み
            for file_name in tech_stack_files + config_files:
                content = self.get_file_content(owner, name, file_name)
                if content:
                    analysis = self._analyze_file_content(analysis, file_name, content)
            
            # 複雑度とカテゴリの推定
            analysis = self._estimate_complexity_and_category(analysis)
            
            return analysis
        
        except Exception as e:
            print(f"    ⚠️  {name} の分析中にエラー: {e}")
            # エラー時のデフォルト値を返す
            return {
                'name': name,
                'description': '',
                'primary_language': 'Unknown',
                'size': 0,
                'stars': 0,
                'forks': 0,
                'created_at': '',
                'updated_at': '',
                'topics': [],
                'languages': {},
                'frameworks': [],
                'tools': [],
                'complexity': 'low',
                'category': 'other'
            }
    
    def _analyze_file_content(self, analysis: Dict[str, Any], filename: str, content: str) -> Dict[str, Any]:
        """ファイル内容から技術スタックを推定"""
        
        if filename == 'package.json':
            try:
                pkg_data = json.loads(content)
                deps = list(pkg_data.get('dependencies', {}).keys())
                dev_deps = list(pkg_data.get('devDependencies', {}).keys())
                
                # フレームワーク検出
                frameworks = []
                if any(dep in deps for dep in ['react', '@types/react']):
                    frameworks.append('React')
                if any(dep in deps for dep in ['vue', 'nuxt']):
                    frameworks.append('Vue.js')
                if any(dep in deps for dep in ['angular', '@angular/core']):
                    frameworks.append('Angular')
                if any(dep in deps for dep in ['express', 'koa', 'fastify']):
                    frameworks.append('Node.js Backend')
                if any(dep in deps for dep in ['next', 'gatsby']):
                    frameworks.append('Static Site Generator')
                
                analysis['frameworks'].extend(frameworks)
                analysis['tools'].extend(['npm/yarn'])
                
            except json.JSONDecodeError:
                pass
        
        elif filename == 'requirements.txt':
            lines = content.strip().split('\n')
            frameworks = []
            
            for line in lines:
                package = line.split('==')[0].split('>=')[0].split('~=')[0].strip()
                if package in ['django', 'Django']:
                    frameworks.append('Django')
                elif package in ['flask', 'Flask']:
                    frameworks.append('Flask')
                elif package in ['fastapi', 'FastAPI']:
                    frameworks.append('FastAPI')
                elif package in ['streamlit']:
                    frameworks.append('Streamlit')
                elif package in ['pandas', 'numpy', 'scipy']:
                    frameworks.append('Data Science')
                elif package in ['tensorflow', 'torch', 'pytorch']:
                    frameworks.append('Machine Learning')
            
            analysis['frameworks'].extend(frameworks)
            analysis['tools'].extend(['pip'])
        
        elif filename in ['go.mod']:
            if 'gin-gonic/gin' in content:
                analysis['frameworks'].append('Gin (Go)')
            if 'gorilla/mux' in content:
                analysis['frameworks'].append('Gorilla Mux')
            analysis['tools'].append('Go Modules')
        
        elif filename == 'Cargo.toml':
            if 'actix-web' in content:
                analysis['frameworks'].append('Actix Web')
            if 'rocket' in content:
                analysis['frameworks'].append('Rocket')
            analysis['tools'].append('Cargo')
        
        elif filename == 'Dockerfile':
            analysis['tools'].append('Docker')
        
        elif filename == 'docker-compose.yml':
            analysis['tools'].append('Docker Compose')
        
        return analysis
    
    def _estimate_complexity_and_category(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """複雑度とカテゴリを推定"""
        
        # 複雑度推定
        complexity_score = 0
        
        # 言語数
        lang_count = len(analysis['languages'])
        complexity_score += min(lang_count * 10, 30)
        
        # フレームワーク数
        framework_count = len(analysis['frameworks'])
        complexity_score += min(framework_count * 15, 45)
        
        # ファイルサイズ
        size = analysis['size']
        if size > 10000:
            complexity_score += 30
        elif size > 1000:
            complexity_score += 15
        
        # スター数（人気度）
        stars = analysis['stars']
        if stars > 100:
            complexity_score += 20
        elif stars > 10:
            complexity_score += 10
        
        if complexity_score >= 60:
            analysis['complexity'] = 'high'
        elif complexity_score >= 30:
            analysis['complexity'] = 'medium'
        else:
            analysis['complexity'] = 'low'
        
        # カテゴリ推定
        primary_lang = (analysis['primary_language'] or '').lower()
        frameworks = [f.lower() for f in analysis['frameworks']]
        
        if any(f in frameworks for f in ['react', 'vue.js', 'angular', 'static site generator']):
            analysis['category'] = 'frontend'
        elif any(f in frameworks for f in ['django', 'flask', 'fastapi', 'node.js backend', 'gin (go)', 'actix web']):
            analysis['category'] = 'backend'
        elif any(f in frameworks for f in ['data science', 'machine learning']):
            analysis['category'] = 'data/ml'
        elif 'docker' in analysis['tools']:
            analysis['category'] = 'devops'
        elif primary_lang in ['javascript', 'typescript', 'html', 'css']:
            analysis['category'] = 'frontend'
        elif primary_lang in ['python', 'java', 'go', 'rust', 'c++']:
            analysis['category'] = 'backend'
        else:
            analysis['category'] = 'other'
        
        return analysis
    
    def generate_portfolio_report(self, analyses: List[Dict[str, Any]]) -> str:
        """ポートフォリオレポートを生成"""
        
        # 統計計算
        total_repos = len(analyses)
        languages = Counter()
        frameworks = Counter()
        categories = Counter()
        complexities = Counter()
        
        total_stars = 0
        total_forks = 0
        
        for analysis in analyses:
            # 言語統計（バイト数加重）
            for lang, bytes_count in analysis['languages'].items():
                languages[lang] += bytes_count
            
            # フレームワーク統計
            for framework in analysis['frameworks']:
                frameworks[framework] += 1
            
            # カテゴリ統計
            categories[analysis['category']] += 1
            
            # 複雑度統計
            complexities[analysis['complexity']] += 1
            
            # スター・フォーク数
            total_stars += analysis['stars']
            total_forks += analysis['forks']
        
        # レポート生成
        report = f"""
# 🚀 GitHub Portfolio Analysis Report
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Portfolio Overview
- **総リポジトリ数**: {total_repos}
- **総スター数**: {total_stars}
- **総フォーク数**: {total_forks}
- **平均スター数**: {total_stars/max(total_repos, 1):.1f}

## 💻 技術スタック分析

### プログラミング言語 (上位10位)
"""
        
        # 言語ランキング
        top_languages = languages.most_common(10)
        total_bytes = sum(languages.values())
        
        for i, (lang, bytes_count) in enumerate(top_languages, 1):
            percentage = (bytes_count / max(total_bytes, 1)) * 100
            report += f"{i:2d}. **{lang}**: {percentage:.1f}% ({bytes_count:,} bytes)\n"
        
        report += "\n### フレームワーク・ライブラリ (上位10位)\n"
        
        # フレームワークランキング
        top_frameworks = frameworks.most_common(10)
        for i, (framework, count) in enumerate(top_frameworks, 1):
            percentage = (count / max(total_repos, 1)) * 100
            report += f"{i:2d}. **{framework}**: {count} projects ({percentage:.1f}%)\n"
        
        report += f"""
## 🎯 プロジェクト分析

### カテゴリ別分布
"""
        
        # カテゴリ分布
        for category, count in categories.most_common():
            percentage = (count / max(total_repos, 1)) * 100
            report += f"- **{category.title()}**: {count} projects ({percentage:.1f}%)\n"
        
        report += "\n### 複雑度分布\n"
        
        # 複雑度分布
        for complexity, count in complexities.most_common():
            percentage = (count / max(total_repos, 1)) * 100
            report += f"- **{complexity.title()}**: {count} projects ({percentage:.1f}%)\n"
        
        # 推奨事項
        report += self._generate_recommendations(analyses, languages, frameworks, categories)
        
        return report
    
    def _generate_recommendations(self, analyses: List[Dict[str, Any]], 
                                languages: Counter, frameworks: Counter, 
                                categories: Counter) -> str:
        """推奨事項を生成"""
        
        recommendations = "\n## 🎯 推奨事項\n\n"
        
        # 技術的多様性の分析
        lang_diversity = len(languages)
        framework_diversity = len(frameworks)
        
        recommendations += "### 技術スキル向上\n"
        
        # 言語の推奨
        top_lang = languages.most_common(1)[0][0] if languages else "Unknown"
        
        if lang_diversity < 3:
            recommendations += f"- 現在のメイン言語は **{top_lang}** です。技術的多様性向上のため、以下の言語学習を推奨:\n"
            suggestions = []
            if 'Python' not in languages:
                suggestions.append("Python（データサイエンス・バックエンド）")
            if 'JavaScript' not in languages and 'TypeScript' not in languages:
                suggestions.append("JavaScript/TypeScript（フロントエンド・フルスタック）")
            if 'Go' not in languages:
                suggestions.append("Go（高性能バックエンド）")
            
            for suggestion in suggestions[:2]:  # 最大2つまで
                recommendations += f"  - {suggestion}\n"
        
        # フレームワークの推奨
        if framework_diversity < 5:
            recommendations += "- モダンなフレームワーク学習を推奨:\n"
            
            frontend_frameworks = [f for f in frameworks if f in ['React', 'Vue.js', 'Angular']]
            if not frontend_frameworks:
                recommendations += "  - **React** または **Vue.js** (フロントエンド開発)\n"
            
            backend_frameworks = [f for f in frameworks if f in ['Django', 'Flask', 'FastAPI', 'Express']]
            if not backend_frameworks:
                recommendations += "  - **FastAPI** または **Express** (バックエンドAPI開発)\n"
        
        # プロジェクトタイプの推奨
        recommendations += "\n### ポートフォリオ強化\n"
        
        if categories['frontend'] == 0:
            recommendations += "- **フロントエンド・プロジェクト**: ユーザーインターフェース開発スキルの証明\n"
        
        if categories['backend'] == 0:
            recommendations += "- **バックエンド・API**: サーバーサイド開発とデータベース設計スキルの証明\n"
        
        if categories['data/ml'] == 0:
            recommendations += "- **データ分析・機械学習**: 現代的なデータ活用スキルの証明\n"
        
        if categories['devops'] < 2:
            recommendations += "- **DevOps・インフラ**: Docker、CI/CD、クラウドデプロイメントスキルの証明\n"
        
        # 品質向上の推奨
        recommendations += "\n### コード品質向上\n"
        
        low_star_repos = len([a for a in analyses if a['stars'] == 0])
        if low_star_repos > len(analyses) * 0.8:
            recommendations += "- **README改善**: プロジェクトの目的・使用方法・技術選択理由を明確に記載\n"
            recommendations += "- **デモ・スクリーンショット**: 実際の動作を視覚的に示す\n"
        
        recommendations += "- **テストコード**: 品質保証とプロフェッショナリズムの証明\n"
        recommendations += "- **ドキュメント**: API仕様書、アーキテクチャ図などの技術文書\n"
        
        return recommendations
    
    def generate_developer_persona(self, analyses: List[Dict[str, Any]], languages: Counter, frameworks: Counter) -> Dict[str, str]:
        """開発者のペルソナ・キャラクター分析を生成"""
        
        total_repos = len(analyses)
        total_commits = sum(a.get('commit_count', 0) for a in analyses)
        test_repos = sum(1 for a in analyses if a.get('has_tests', False))
        ci_repos = sum(1 for a in analyses if a.get('has_ci', False))
        readme_repos = sum(1 for a in analyses if a.get('readme_exists', False))
        
        # 主要言語とその割合
        top_lang = languages.most_common(1)[0] if languages else ('Unknown', 0)
        lang_name, lang_bytes = top_lang
        total_bytes = sum(languages.values())
        lang_percentage = (lang_bytes / max(total_bytes, 1)) * 100
        
        # キャラクター分析
        persona = {}
        
        # メイン称号の決定
        if lang_percentage > 60:
            if lang_name == 'TypeScript':
                persona['title'] = "🛡️ Type Guardian - 型安全の守護者"
                persona['description'] = "TypeScriptの型システムを駆使し、実行時エラーを事前に防ぐ堅実な開発者"
            elif lang_name == 'JavaScript':
                persona['title'] = "⚡ Script Wizard - 動的魔法使い"
                persona['description'] = "JavaScriptの柔軟性を活かし、フロントエンドからバックエンドまで幅広く活躍"
            elif lang_name == 'Python':
                persona['title'] = "🐍 Python Charmer - 蛇使いマスター"
                persona['description'] = "Pythonの直感的な記法で、データ分析からWeb開発まで効率的に実装"
            elif lang_name == 'Go':
                persona['title'] = "🚀 Gopher Elite - 高速処理の達人"
                persona['description'] = "Goの並行処理能力を駆使し、スケーラブルなバックエンドシステムを構築"
            elif lang_name == 'Rust':
                persona['title'] = "⚔️ Memory Samurai - メモリ安全の侍"
                persona['description'] = "Rustの所有権システムを極め、安全で高性能なシステムプログラミングを実践"
            else:
                persona['title'] = f"🎯 {lang_name} Specialist - 専門職人"
                persona['description'] = f"{lang_name}に特化した深い知識を持つスペシャリスト開発者"
        else:
            persona['title'] = "🌈 Polyglot Engineer - 多言語エンジニア"
            persona['description'] = "複数の言語を巧みに使い分け、適材適所で最適な技術選択を行う"
        
        # サブ特性の決定
        traits = []
        
        # 品質への意識
        if test_repos / max(total_repos, 1) > 0.5:
            traits.append("🧪 Quality Assurance Master - 品質保証の達人")
        if ci_repos / max(total_repos, 1) > 0.3:
            traits.append("🔄 DevOps Practitioner - 自動化推進者")
        if readme_repos / max(total_repos, 1) > 0.7:
            traits.append("📚 Documentation Evangelist - ドキュメント伝道師")
        
        # コミット頻度
        avg_commits = total_commits / max(total_repos, 1)
        if avg_commits > 50:
            traits.append("⚡ Commit Machine - コミット製造機")
        elif avg_commits > 20:
            traits.append("🔨 Steady Builder - 着実な構築者")
        
        # フレームワーク使用状況
        framework_count = len(frameworks)
        if framework_count > 5:
            traits.append("🛠️ Framework Explorer - フレームワーク探検家")
        elif 'React' in frameworks and frameworks['React'] > 2:
            traits.append("⚛️ React Artisan - React職人")
        
        # Docker使用
        docker_usage = sum(1 for a in analyses if 'Docker' in a.get('tools', []))
        if docker_usage > 2:
            traits.append("🐳 Container Captain - コンテナ船長")
        
        persona['traits'] = traits[:3]  # 最大3つまで
        
        # 総合評価
        quality_score = 0
        if test_repos / max(total_repos, 1) > 0.3:
            quality_score += 2
        if ci_repos / max(total_repos, 1) > 0.2:
            quality_score += 2
        if readme_repos / max(total_repos, 1) > 0.5:
            quality_score += 1
        if framework_count > 3:
            quality_score += 1
        if avg_commits > 10:
            quality_score += 1
        
        if quality_score >= 6:
            persona['level'] = "🏆 Senior Level - シニアエンジニア級"
        elif quality_score >= 4:
            persona['level'] = "💪 Mid Level - 中堅エンジニア級"
        else:
            persona['level'] = "🌱 Growing Level - 成長中エンジニア級"
        
        return persona
    
    def save_detailed_analysis(self, analyses: List[Dict[str, Any]], filename: str = 'portfolio_analysis.json'):
        """詳細分析結果をJSONで保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analyses, f, ensure_ascii=False, indent=2)
        print(f"💾 詳細分析結果を {filename} に保存しました")
    
    def generate_claude_analysis_prompt(self, analyses: List[Dict[str, Any]], user_info: Dict[str, Any]) -> str:
        """Claude Code用の詳細分析プロンプトを生成"""
        
        # 統計計算
        total_repos = len(analyses)
        languages = Counter()
        frameworks = Counter()
        categories = Counter()
        tools = Counter()
        
        recent_projects = []
        complex_projects = []
        popular_projects = []
        total_commits = 0
        test_coverage = 0
        ci_usage = 0
        
        for analysis in analyses:
            # 言語統計
            for lang, bytes_count in analysis['languages'].items():
                languages[lang] += bytes_count
            
            # フレームワーク・ツール統計
            for framework in analysis['frameworks']:
                frameworks[framework] += 1
            for tool in analysis['tools']:
                tools[tool] += 1
            
            # カテゴリ統計
            categories[analysis['category']] += 1
            
            # 統計値蓄積
            total_commits += analysis.get('commit_count', 0)
            if analysis.get('has_tests', False):
                test_coverage += 1
            if analysis.get('has_ci', False):
                ci_usage += 1
            
            # 注目プロジェクト分類
            if analysis['updated_at']:
                try:
                    updated = datetime.fromisoformat(analysis['updated_at'].replace('Z', '+00:00'))
                    if updated > datetime.now().replace(tzinfo=updated.tzinfo) - timedelta(days=180):
                        recent_projects.append(analysis)
                except:
                    pass
            
            if analysis['complexity'] == 'high':
                complex_projects.append(analysis)
            
            if analysis['stars'] > 0:
                popular_projects.append(analysis)
        
        # ペルソナ分析生成
        persona = self.generate_developer_persona(analyses, languages, frameworks)
        
        # プロンプト生成
        prompt = f"""# GitHub Portfolio 深層分析依頼

## 🎭 開発者ペルソナ分析結果

### メイン称号
**{persona['title']}**
{persona['description']}

### レベル
{persona['level']}

### 特性バッジ
{chr(10).join(f"- {trait}" for trait in persona['traits']) if persona['traits'] else "- まだ特性バッジを獲得していません"}

### 統計サマリー
- **総コミット数**: {total_commits:,}
- **平均コミット数/repo**: {total_commits/max(total_repos, 1):.1f}
- **テストカバレッジ**: {test_coverage}/{total_repos} repos ({test_coverage/max(total_repos, 1)*100:.1f}%)
- **CI/CD導入率**: {ci_usage}/{total_repos} repos ({ci_usage/max(total_repos, 1)*100:.1f}%)

---

あなたは経験豊富なテックリードかつキャリアコンサルタントです。以下のGitHubポートフォリオデータを詳細に分析し、技術的評価とキャリア戦略を提案してください。

## 📊 基本情報
- **GitHub ユーザー名**: {user_info.get('login', 'N/A')}
- **公開リポジトリ数**: {user_info.get('public_repos', 'N/A')}
- **フォロワー数**: {user_info.get('followers', 'N/A')}
- **分析対象リポジトリ**: {total_repos}

## 💻 技術スタック詳細

### プログラミング言語分布
```json
{json.dumps(dict(languages.most_common()), ensure_ascii=False, indent=2)}
```

### フレームワーク・ライブラリ使用状況
```json
{json.dumps(dict(frameworks.most_common()), ensure_ascii=False, indent=2)}
```

### 開発ツール・技術
```json
{json.dumps(dict(tools.most_common()), ensure_ascii=False, indent=2)}
```

### プロジェクトカテゴリ分布
```json
{json.dumps(dict(categories.most_common()), ensure_ascii=False, indent=2)}
```

## 🎯 注目プロジェクト

### 最近のアクティブプロジェクト (過去6ヶ月)
```json
{json.dumps([{
    'name': p['name'],
    'primary_language': p['primary_language'],
    'frameworks': p['frameworks'],
    'complexity': p['complexity'],
    'description': p['description'][:100] + '...' if len(p['description']) > 100 else p['description']
} for p in recent_projects[:5]], ensure_ascii=False, indent=2)}
```

### 高複雑度プロジェクト
```json
{json.dumps([{
    'name': p['name'],
    'primary_language': p['primary_language'],
    'frameworks': p['frameworks'],
    'tools': p['tools'],
    'languages_count': len(p['languages']),
    'description': p['description'][:100] + '...' if len(p['description']) > 100 else p['description']
} for p in complex_projects[:5]], ensure_ascii=False, indent=2)}
```

### 人気プロジェクト (スター獲得)
```json
{json.dumps([{
    'name': p['name'],
    'stars': p['stars'],
    'forks': p['forks'],
    'primary_language': p['primary_language'],
    'frameworks': p['frameworks'],
    'description': p['description'][:100] + '...' if len(p['description']) > 100 else p['description']
} for p in popular_projects[:5]], ensure_ascii=False, indent=2)}
```

## 📋 分析依頼内容

以下の観点から詳細に分析・評価してください：

### 1. 技術的スキル評価 (各項目10点満点)
- **フロントエンド技術力**
- **バックエンド技術力**
- **データベース・データ処理**
- **DevOps・インフラ**
- **モバイル開発**
- **AI/ML技術**
- **技術の多様性と深度**
- **モダンな技術への適応**

### 2. エンジニアリング品質評価
- **コード設計・アーキテクチャ**
- **プロジェクト構成・管理**
- **ドキュメント・README品質**
- **テスト・品質保証への取り組み**
- **セキュリティ意識**
- **パフォーマンス最適化**

### 3. プロダクト・ビジネス視点
- **実用性・市場価値**
- **UI/UX設計力**
- **問題解決アプローチ**
- **継続的な開発・メンテナンス**
- **オープンソース貢献**

### 4. キャリア戦略提案
- **現在の市場価値(年収レンジ予想)**
- **強みと弱みの明確化**
- **次に習得すべき技術(優先度順)**
- **ポートフォリオ改善項目(具体的)**
- **転職・キャリアアップ戦略**
- **学習計画(6ヶ月・1年・3年)**

### 5. 具体的改善提案
- **不足している技術領域**
- **作るべきプロジェクト(3-5個)**
- **既存プロジェクトの改善点**
- **技術ブログ・発信すべき内容**
- **参加すべきコミュニティ・イベント**

## 📝 出力形式
- 各セクションは詳細かつ具体的に
- スコアは根拠とともに提示
- 改善提案は実行可能な具体案を
- 市場動向と照らし合わせた分析を
- エンジニアのレベル感を考慮した現実的な提案を

よろしくお願いします！"""

        return prompt


def main():
    parser = argparse.ArgumentParser(description='GitHub Portfolio Analyzer')
    parser.add_argument('--token', help='GitHub Personal Access Token')
    parser.add_argument('--max-repos', type=int, default=100, help='分析するリポジトリの最大数')
    parser.add_argument('--output', default='report.md', help='レポート出力ファイル名')
    parser.add_argument('--save-json', action='store_true', help='詳細分析結果をJSONで保存')
    
    args = parser.parse_args()
    
    # .envファイルを読み込み
    load_env_file()
    
    # GitHub Token取得
    token = args.token or os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ GitHub Personal Access Tokenが必要です")
        print("   --token オプションまたは GITHUB_TOKEN 環境変数を設定してください")
        sys.exit(1)
    
    try:
        analyzer = GitHubAnalyzer(token)
        
        # ユーザー情報取得
        user_info = analyzer.get_user_info()
        print(f"🔍 {user_info['login']} のポートフォリオを分析中...")
        
        # リポジトリ取得
        repos = analyzer.get_all_repositories(args.max_repos)
        print(f"📦 {len(repos)} 個のリポジトリを取得しました")
        
        # 各リポジトリを分析
        analyses = []
        for i, repo in enumerate(repos, 1):
            print(f"🔎 [{i:3d}/{len(repos):3d}] {repo['name']} を分析中...")
            analysis = analyzer.analyze_repository_tech_stack(repo)
            analyses.append(analysis)
        
        # レポート生成
        print("📊 レポートを生成中...")
        report = analyzer.generate_portfolio_report(analyses)
        
        # レポート保存
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 分析完了！レポートを {args.output} に保存しました")
        
        # 詳細分析結果をJSONで保存（オプション）
        if args.save_json:
            analyzer.save_detailed_analysis(analyses)
        
        # Claude Code用の詳細分析プロンプトを生成
        claude_prompt = analyzer.generate_claude_analysis_prompt(analyses, user_info)
        claude_prompt_file = 'claude_analysis_prompt.md'
        with open(claude_prompt_file, 'w', encoding='utf-8') as f:
            f.write(claude_prompt)
        
        print(f"🤖 Claude Code分析用プロンプトを {claude_prompt_file} に保存しました")
        print("\n" + "="*80)
        print("📋 次の手順:")
        print("1. Claude Codeでこのプロンプトファイルを読み込んでください")
        print("2. 詳細な技術分析とキャリア提案を受け取れます")
        print("="*80)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ GitHub API エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()