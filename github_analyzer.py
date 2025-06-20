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
    
    def generate_human_focused_analysis(self, analyses, user_info):
        """人に焦点を当てた開発者分析を生成"""
        
        total_repos = len(analyses)
        total_commits = sum(a.get('commit_count', 0) for a in analyses)
        test_repos = sum(1 for a in analyses if a.get('has_tests', False))
        ci_repos = sum(1 for a in analyses if a.get('has_ci', False))
        readme_repos = sum(1 for a in analyses if a.get('readme_exists', False))
        
        # 開発者の傾向分析
        analysis = {
            'working_style': {},
            'collaboration_style': {},
            'technical_habits': {},
            'productivity_patterns': {},
            'quality_consciousness': {}
        }
        
        # === 作業スタイル分析 ===
        avg_commits = total_commits / max(total_repos, 1)
        if avg_commits > 100:
            analysis['working_style']['commitment'] = "高頻度コミッター - 小さな変更を頻繁にコミットする丁寧な作業スタイル"
        elif avg_commits > 20:
            analysis['working_style']['commitment'] = "安定的コミッター - 適度なペースで着実に開発を進める"
        else:
            analysis['working_style']['commitment'] = "一気集中型 - まとまった機能を一度に実装するタイプ"
        
        # ドキュメント意識
        readme_rate = readme_repos / max(total_repos, 1)
        if readme_rate > 0.8:
            analysis['working_style']['documentation'] = "ドキュメント完璧主義者 - 他者への配慮を重視する丁寧な開発者"
        elif readme_rate > 0.5:
            analysis['working_style']['documentation'] = "ドキュメント意識良好 - バランス感覚のある実践的な開発者"
        elif readme_rate > 0.2:
            analysis['working_style']['documentation'] = "コード重視派 - 実装に集中し、ドキュメントは後回しにしがち"
        else:
            analysis['working_style']['documentation'] = "ドキュメント軽視派 - コードで語るタイプ（要改善）"
        
        # === コラボレーションスタイル ===
        # フォロワー数から判断
        followers = user_info.get('followers', 0)
        public_repos = user_info.get('public_repos', 0)
        
        if followers > 50:
            analysis['collaboration_style']['visibility'] = "コミュニティリーダー - 影響力のある発信者"
        elif followers > 10:
            analysis['collaboration_style']['visibility'] = "アクティブメンバー - コミュニティに積極参加"
        else:
            analysis['collaboration_style']['visibility'] = "サイレントワーカー - 静かに開発に取り組む職人気質"
        
        # リポジトリ公開率
        if public_repos > 30:
            analysis['collaboration_style']['openness'] = "オープンソース推進派 - 積極的にコードを公開・共有"
        elif public_repos > 10:
            analysis['collaboration_style']['openness'] = "適度な公開派 - バランス良くコードを共有"
        else:
            analysis['collaboration_style']['openness'] = "プライベート重視派 - 慎重にコードを管理"
        
        # === 技術習慣 ===
        test_rate = test_repos / max(total_repos, 1)
        if test_rate > 0.7:
            analysis['technical_habits']['testing'] = "テスト駆動開発者 - 品質第一の堅実な開発手法"
        elif test_rate > 0.3:
            analysis['technical_habits']['testing'] = "品質意識派 - 重要なプロジェクトではテストを実装"
        elif test_rate > 0.1:
            analysis['technical_habits']['testing'] = "テスト学習中 - 品質向上に取り組み始めている"
        else:
            analysis['technical_habits']['testing'] = "テスト後回し派 - スピード重視、品質は運用で解決しがち"
        
        ci_rate = ci_repos / max(total_repos, 1)
        if ci_rate > 0.5:
            analysis['technical_habits']['automation'] = "自動化マスター - 効率的なワークフローを構築"
        elif ci_rate > 0.2:
            analysis['technical_habits']['automation'] = "自動化導入中 - モダンな開発手法を学習・実践"
        else:
            analysis['technical_habits']['automation'] = "手動派 - 従来型の開発スタイルを維持"
        
        # === 成長パターン ===
        recent_activity = len([a for a in analyses if self._is_recent_project(a)])
        if recent_activity / max(total_repos, 1) > 0.6:
            analysis['productivity_patterns']['activity'] = "現在進行形 - 活発に新しいプロジェクトに取り組んでいる"
        elif recent_activity > 0:
            analysis['productivity_patterns']['activity'] = "選択的アクティブ - 厳選したプロジェクトに集中"
        else:
            analysis['productivity_patterns']['activity'] = "過去の遺産 - 現在はあまりアクティブでない可能性"
        
        # === 問題解決スタイル ===
        complexity_high = len([a for a in analyses if a.get('complexity') == 'high'])
        if complexity_high / max(total_repos, 1) > 0.4:
            analysis['technical_habits']['complexity'] = "複雑性挑戦者 - 難しい問題に積極的に取り組む"
        elif complexity_high > 0:
            analysis['technical_habits']['complexity'] = "バランス志向 - 適度な難易度のプロジェクトを選択"
        else:
            analysis['technical_habits']['complexity'] = "シンプル指向 - 分かりやすく実用的なソリューションを重視"
        
        return analysis
    
    def _is_recent_project(self, analysis: Dict[str, Any]) -> bool:
        """プロジェクトが最近アクティブかどうか判定"""
        try:
            if analysis.get('updated_at'):
                updated = datetime.fromisoformat(analysis['updated_at'].replace('Z', '+00:00'))
                return updated > datetime.now().replace(tzinfo=updated.tzinfo) - timedelta(days=180)
        except:
            pass
        return False
    
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
        
        # 人間重視の分析生成
        human_analysis = self.generate_human_focused_analysis(analyses, user_info)
        
        # プロンプト生成
        prompt = f"""# GitHub Portfolio 深層分析依頼

## 👤 開発者の人間性分析

### 作業スタイル
- **コミットパターン**: {human_analysis['working_style']['commitment']}
- **ドキュメント意識**: {human_analysis['working_style']['documentation']}

### コラボレーションスタイル  
- **コミュニティでの存在感**: {human_analysis['collaboration_style']['visibility']}
- **オープンソース姿勢**: {human_analysis['collaboration_style']['openness']}

### 技術習慣
- **テスト・品質への取り組み**: {human_analysis['technical_habits']['testing']}
- **自動化・効率化への姿勢**: {human_analysis['technical_habits']['automation']}
- **複雑性への対応**: {human_analysis['technical_habits']['complexity']}

### 開発活動パターン
- **現在のアクティビティ**: {human_analysis['productivity_patterns']['activity']}

### 数値サマリー
- **総コミット数**: {total_commits:,}
- **平均コミット数/repo**: {total_commits/max(total_repos, 1):.1f}
- **テストカバレッジ**: {test_coverage}/{total_repos} repos ({test_coverage/max(total_repos, 1)*100:.1f}%)
- **CI/CD導入率**: {ci_usage}/{total_repos} repos ({ci_usage/max(total_repos, 1)*100:.1f}%)
- **READMEカバレッジ**: {len([a for a in analyses if a.get('readme_exists', False)])}/{total_repos} repos ({len([a for a in analyses if a.get('readme_exists', False)])/max(total_repos, 1)*100:.1f}%)

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

## 🎯 開発者能力分析

### 得意分野・専門性
この開発者の技術的な強みと専門分野を技術スタックから分析：

**言語的専門性:**
{chr(10).join(f"- **{lang}**: {(bytes_count/sum(languages.values())*100):.1f}%の使用率" for lang, bytes_count in languages.most_common(3))}

**技術領域の傾向:**
- **フロントエンド志向**: {categories.get('frontend', 0)}/{total_repos} projects ({categories.get('frontend', 0)/max(total_repos, 1)*100:.1f}%)
- **バックエンド志向**: {categories.get('backend', 0)}/{total_repos} projects ({categories.get('backend', 0)/max(total_repos, 1)*100:.1f}%)
- **データ・ML志向**: {categories.get('data/ml', 0)}/{total_repos} projects ({categories.get('data/ml', 0)/max(total_repos, 1)*100:.1f}%)
- **DevOps志向**: {categories.get('devops', 0)}/{total_repos} projects ({categories.get('devops', 0)/max(total_repos, 1)*100:.1f}%)

### プロジェクト品質傾向
この開発者の開発品質・プロフェッショナリズムの指標：

**品質管理の取り組み:**
- **テストカバレッジ率**: {test_coverage}/{total_repos} repos ({test_coverage/max(total_repos, 1)*100:.1f}%) 
- **CI/CD導入率**: {ci_usage}/{total_repos} repos ({ci_usage/max(total_repos, 1)*100:.1f}%)
- **ドキュメント整備率**: {len([a for a in analyses if a.get('readme_exists', False)])}/{total_repos} repos ({len([a for a in analyses if a.get('readme_exists', False)])/max(total_repos, 1)*100:.1f}%)

**プロジェクト管理スタイル:**
- **平均プロジェクト複雑度**: {sum(1 for a in analyses if a.get('complexity') == 'high')}/{total_repos} high-complexity projects
- **技術多様性**: {len(languages)} programming languages across projects
- **フレームワーク活用度**: {len(frameworks)} different frameworks/libraries used

## 📋 分析依頼内容

以下の観点から詳細に分析・評価してください：

### 0. 開発者称号の命名 🏆
上記の人間性分析と技術データを基に、この開発者にふさわしい**キャッチーで面白い称号**を考案してください：

**称号の例（ファンタジック・RPG風も歓迎）:**
- 🛡️ TypeScript Guardian（型安全の守護者）
- 🧙‍♂️ Code Wizard（コード魔法使い）
- ⚔️ Bug Slayer（バグ討伐者）
- 🏰 Architecture Architect（設計建築家）
- 📜 Documentation Sage（ドキュメント賢者）
- ⚡ Lightning Coder（稲妻コーダー）
- 🌟 Framework Summoner（フレームワーク召喚師）
- 🗡️ Legacy Code Warrior（レガシーコード戦士）
- 🎯 Feature Sniper（機能狙撃手）
- 🔮 API Alchemist（API錬金術師）
- 🛠️ DevOps Paladin（DevOps聖騎士）
- 🐉 Performance Dragon Tamer（パフォーマンス竜使い）
- 🎭 Frontend Performer（フロントエンド芸人）
- 🏔️ Backend Mountain Builder（バックエンド山築師）

**不名誉称号も含めて（改善点として）:**
- 📝 README Hermit（説明書隠者）
- 🧪 Test Phobic（テスト恐怖症）
- 💾 Commit Hoarder（コミット貯蔵癖）
- 🔒 Solo Adventurer（一人冒険者）
- 🐛 Bug Breeder（バグ養殖家）
- 📊 Issue Collector（課題コレクター）

**要求:** 称号は必ず絵文字付きで、その人の特徴を的確に表現し、少し面白みのあるものにしてください。

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
    
    def generate_developer_card_html(self, analyses: List[Dict[str, Any]], user_info: Dict[str, Any], languages: Counter, frameworks: Counter) -> str:
        """開発者カード用のHTMLを生成"""
        
        human_analysis = self.generate_human_focused_analysis(analyses, user_info)
        total_commits = sum(a.get('commit_count', 0) for a in analyses)
        test_coverage = sum(1 for a in analyses if a.get('has_tests', False))
        ci_usage = sum(1 for a in analyses if a.get('has_ci', False))
        readme_coverage = sum(1 for a in analyses if a.get('readme_exists', False))
        
        # トップ3言語
        top_languages = languages.most_common(3)
        total_bytes = sum(languages.values())
        
        # トップフレームワーク
        top_frameworks = frameworks.most_common(3)
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Developer Card - {user_info.get('login', 'Unknown')}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        body {{
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .developer-card {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            max-width: 450px;
            width: 100%;
            position: relative;
            overflow: hidden;
        }}
        
        .developer-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 8px;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #ffeaa7);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 25px;
        }}
        
        .username {{
            font-size: 28px;
            font-weight: 700;
            margin: 10px 0 5px 0;
            color: #2d3436;
        }}
        
        .subtitle {{
            color: #636e72;
            font-size: 14px;
            margin-bottom: 15px;
        }}
        
        .title-section {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .title {{
            font-size: 18px;
            font-weight: 600;
            margin: 0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-item {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 20px;
            font-weight: 700;
            color: #2d3436;
            display: block;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: #636e72;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .skills-section {{
            margin-bottom: 20px;
        }}
        
        .section-title {{
            font-size: 14px;
            font-weight: 600;
            color: #2d3436;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .skill-bar {{
            margin-bottom: 8px;
        }}
        
        .skill-name {{
            font-size: 12px;
            color: #636e72;
            margin-bottom: 4px;
            display: flex;
            justify-content: space-between;
        }}
        
        .progress-bar {{
            height: 6px;
            background: #e9ecef;
            border-radius: 3px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }}
        
        .traits {{
            margin-bottom: 20px;
        }}
        
        .trait-item {{
            background: #e8f5e8;
            color: #2d5a2d;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 11px;
            margin: 5px 5px 0 0;
            display: inline-block;
        }}
        
        .generated-info {{
            text-align: center;
            color: #636e72;
            font-size: 10px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }}
    </style>
</head>
<body>
    <div class="developer-card">
        <div class="header">
            <div class="username">{user_info.get('login', 'Unknown')}</div>
            <div class="subtitle">GitHub Portfolio Analysis</div>
        </div>
        
        <div class="title-section">
            <div class="title">🎭 称号はClaude Codeで決定してもらってください</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-item">
                <span class="stat-number">{len(analyses)}</span>
                <span class="stat-label">Projects</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{total_commits:,}</span>
                <span class="stat-label">Commits</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{test_coverage}/{len(analyses)}</span>
                <span class="stat-label">Test Coverage</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">{readme_coverage}/{len(analyses)}</span>
                <span class="stat-label">Documentation</span>
            </div>
        </div>
        
        <div class="skills-section">
            <div class="section-title">💻 Top Languages</div>
            {chr(10).join(f'''
            <div class="skill-bar">
                <div class="skill-name">
                    <span>{lang}</span>
                    <span>{(bytes_count/max(total_bytes, 1)*100):.1f}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {(bytes_count/max(total_bytes, 1)*100):.1f}%"></div>
                </div>
            </div>''' for lang, bytes_count in top_languages)}
        </div>
        
        <div class="skills-section">
            <div class="section-title">🛠️ Frameworks</div>
            {chr(10).join(f'<div class="trait-item">{framework} ({count})</div>' for framework, count in top_frameworks)}
        </div>
        
        <div class="traits">
            <div class="section-title">🏷️ Developer Traits</div>
            <div class="trait-item">{human_analysis['working_style']['commitment'].split(' - ')[0]}</div>
            <div class="trait-item">{human_analysis['working_style']['documentation'].split(' - ')[0]}</div>
            <div class="trait-item">{human_analysis['collaboration_style']['visibility'].split(' - ')[0]}</div>
        </div>
        
        <div class="generated-info">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} • GitHub Portfolio Analyzer
        </div>
    </div>
</body>
</html>"""
        
        return html


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
        
        # 開発者カードHTML生成
        languages = Counter()
        frameworks = Counter()
        for analysis in analyses:
            for lang, bytes_count in analysis['languages'].items():
                languages[lang] += bytes_count
            for framework in analysis['frameworks']:
                frameworks[framework] += 1
        
        card_html = analyzer.generate_developer_card_html(analyses, user_info, languages, frameworks)
        card_file = 'developer_card.html'
        with open(card_file, 'w', encoding='utf-8') as f:
            f.write(card_html)
        
        print(f"🤖 Claude Code分析用プロンプトを {claude_prompt_file} に保存しました")
        print(f"🎨 開発者カードHTMLを {card_file} に保存しました")
        print("\n" + "="*80)
        print("📋 次の手順:")
        print("1. Claude Codeでこのプロンプトファイルを読み込んでください")
        print("2. 詳細な技術分析とキャリア提案を受け取れます")
        print(f"3. {card_file} をブラウザで開くと美しいカードが表示されます")
        print("="*80)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ GitHub API エラー: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()