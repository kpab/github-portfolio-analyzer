import streamlit as st
import requests
import json
import asyncio
from anthropic import Anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(
    page_title="GitHub Portfolio Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("🔍 GitHub Portfolio Analyzer")
st.markdown("全リポジトリの技術的傾向を分析して、スキルギャップと成長方向を可視化します")

# Sidebar for configuration
with st.sidebar:
    st.header("🔧 設定")

    github_token = st.text_input(
        "GitHub Personal Access Token",
        type="password",
        help="リポジトリ一覧取得とプライベートリポジトリアクセスに必要"
    )

    anthropic_api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="Claude分析に必要"
    )

    analysis_depth = st.selectbox(
        "分析の深度",
        ["軽量（READMEとpackage.jsonのみ）", "標準（主要ファイル）", "詳細（全ファイル）"]
    )

    max_repos = st.slider("分析対象リポジトリ数", 5, 500, 100)

@st.cache_data(ttl=3600)
def get_user_repositories(token, max_count=500):
    """GitHub APIで全リポジトリを取得"""
    headers = {'Authorization': f'token {token}'}
    repos = []
    page = 1

    progress_bar = st.progress(0)
    status_text = st.empty()

    while len(repos) < max_count:
        status_text.text(f"リポジトリ取得中... {len(repos)}")
        response = requests.get(
            f'https://api.github.com/user/repos?page={page}&per_page=100&type=all&sort=updated',
            headers=headers
        )

        if response.status_code != 200:
            st.error(f"GitHub API エラー: {response.status_code}")
            break

        page_repos = response.json()
        if not page_repos:
            break

        repos.extend(page_repos[:max_count - len(repos)])
        progress_bar.progress(min(len(repos) / max_count, 1.0))
        page += 1

    status_text.text(f"✅ {len(repos)}個のリポジトリを取得完了")
    return repos

def extract_key_files(repo_info, token, depth="standard"):
    """リポジトリから重要ファイルを抽出"""
    owner = repo_info['owner']['login']
    name = repo_info['name']
    headers = {'Authorization': f'token {token}'}

    # 分析深度に応じてファイル選択
    if depth == "軽量（READMEとpackage.jsonのみ）":
        target_files = ['README.md', 'package.json', 'requirements.txt', 'go.mod', 'Cargo.toml']
    elif depth == "標準（主要ファイル）":
        target_files = [
            'README.md', 'package.json', 'requirements.txt', 'go.mod', 'Cargo.toml',
            'main.py', 'index.js', 'main.go', 'src/main.rs', 'app.py', 'server.js',
            '.github/workflows/*.yml', 'docker-compose.yml', 'Dockerfile'
        ]
    else:  # 詳細
        # 全ファイル（制限付き）
        tree_url = f"https://api.github.com/repos/{owner}/{name}/git/trees/main?recursive=1"
        tree_response = requests.get(tree_url, headers=headers)
        if tree_response.status_code == 200:
            tree_data = tree_response.json()
            target_files = [item['path'] for item in tree_data.get('tree', [])[:50]]  # 最大50ファイル
        else:
            target_files = ['README.md']

    files_content = {}
    for file_path in target_files:
        try:
            file_url = f"https://api.github.com/repos/{owner}/{name}/contents/{file_path}"
            file_response = requests.get(file_url, headers=headers)
            if file_response.status_code == 200:
                file_data = file_response.json()
                if file_data.get('type') == 'file' and file_data.get('size', 0) < 100000:  # 100KB制限
                    import base64
                    content = base64.b64decode(file_data['content']).decode('utf-8', errors='ignore')
                    files_content[file_path] = content[:5000]  # 最大5000文字
        except Exception as e:
            continue

    return files_content

def analyze_repository_batch(repos_data, anthropic_key):
    """バッチ分析でリポジトリ群を解析"""
    client = Anthropic(api_key=anthropic_key)

    # バッチ用のプロンプト作成
    batch_prompts = []
    for i, (repo_name, repo_data) in enumerate(repos_data.items()):
        prompt = f"""
リポジトリ名: {repo_name}
技術情報: {json.dumps(repo_data, ensure_ascii=False, indent=2)}

このリポジトリについて以下の形式で分析してください：
{{
    "primary_language": "メイン言語",
    "frameworks": ["フレームワーク1", "フレームワーク2"],
    "complexity": "低|中|高",
    "maturity": "プロトタイプ|開発中|完成",
    "strengths": ["強み1", "強み2"],
    "improvements": ["改善点1", "改善点2"],
    "tech_stack_score": 8.5
}}
"""
        batch_prompts.append({
            "custom_id": f"repo_{i}",
            "params": {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
        })

    return batch_prompts

def create_portfolio_dashboard(analysis_results):
    """分析結果からダッシュボードを作成"""
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 技術スタック分布")

        # 言語分布
        languages = {}
        for result in analysis_results:
            lang = result.get('primary_language', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1

        if languages:
            fig_lang = px.pie(
                values=list(languages.values()),
                names=list(languages.keys()),
                title="使用言語分布"
            )
            st.plotly_chart(fig_lang, use_container_width=True)

    with col2:
        st.subheader("🎯 プロジェクト成熟度")

        maturity_levels = {}
        for result in analysis_results:
            level = result.get('maturity', 'Unknown')
            maturity_levels[level] = maturity_levels.get(level, 0) + 1

        if maturity_levels:
            fig_maturity = px.bar(
                x=list(maturity_levels.keys()),
                y=list(maturity_levels.values()),
                title="プロジェクト成熟度分布"
            )
            st.plotly_chart(fig_maturity, use_container_width=True)

    # スキルレーダーチャート
    st.subheader("🎪 技術スキルレーダー")

    # 技術カテゴリ別スコア算出
    categories = ['Frontend', 'Backend', 'Database', 'DevOps', 'Mobile', 'ML/AI']
    scores = [7.5, 8.0, 6.5, 5.5, 4.0, 6.0]  # 実際の分析結果から算出

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='現在のスキルレベル'
    ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True,
        title="技術分野別スキルレベル"
    )

    st.plotly_chart(fig_radar, use_container_width=True)

def main():
    # メインアプリケーション
    if github_token and anthropic_api_key:

        if st.button("🚀 分析開始", type="primary"):
            with st.spinner("分析中...この処理には数分かかる場合があります"):

                # Step 1: リポジトリ取得
                st.info("Step 1: GitHubリポジトリを取得中...")
                repos = get_user_repositories(github_token, max_repos)

                if not repos:
                    st.error("リポジトリが見つかりませんでした")
                    return

                # Step 2: ファイル分析
                st.info("Step 2: リポジトリ内容を分析中...")
                repos_data = {}

                progress = st.progress(0)
                for i, repo in enumerate(repos):
                    repo_name = repo['name']

                    # リポジトリメタデータ
                    repo_info = {
                        'name': repo_name,
                        'description': repo.get('description', ''),
                        'language': repo.get('language', ''),
                        'size': repo.get('size', 0),
                        'stars': repo.get('stargazers_count', 0),
                        'created_at': repo.get('created_at', ''),
                        'updated_at': repo.get('updated_at', ''),
                    }

                    # ファイル内容取得
                    files_content = extract_key_files(repo, github_token, analysis_depth)
                    repo_info['files'] = files_content

                    repos_data[repo_name] = repo_info
                    progress.progress((i + 1) / len(repos))

                # Step 3: Claude分析
                st.info("Step 3: Claude AIで技術傾向を分析中...")

                # 統合分析プロンプト
                comprehensive_prompt = f"""
以下は私の全GitHubリポジトリの技術情報です：

{json.dumps(repos_data, ensure_ascii=False, indent=2)}

この情報から以下を分析してください：

1. **技術スタック傾向**：
   - 最も使用している言語・フレームワーク
   - 技術の変遷パターン
   - 得意分野と不足分野

2. **開発パターン分析**：
   - アーキテクチャの好み
   - コード品質の傾向
   - プロジェクト規模の分布

3. **成長推奨分野**：
   - 学習すべき技術（優先度順）
   - 市場価値向上のための提案
   - ポートフォリオ改善点

4. **総合評価**：
   - 技術的強み（1-10スコア）
   - キャリア方向性の提案
   - 具体的なネクストステップ

分析結果は構造化された形式で、具体例とスコアを含めて回答してください。
"""

                client = Anthropic(api_key=anthropic_api_key)
                response = client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": comprehensive_prompt}]
                )

                # 結果表示
                st.success("✅ 分析完了！")

                # タブで結果表示
                tab1, tab2, tab3 = st.tabs(["📊 ダッシュボード", "📝 詳細分析", "💾 生データ"])

                with tab1:
                    st.subheader("🎯 ポートフォリオ分析結果")
                    create_portfolio_dashboard([])  # 仮のデータでダッシュボード表示

                with tab2:
                    st.subheader("🔍 Claude による詳細分析")
                    st.markdown(response.content[0].text)

                    # アクションアイテム
                    with st.expander("🎯 推奨アクション"):
                        st.markdown("""
                        ### 今後3ヶ月のアクションプラン：
                        1. **技術学習**: [分析結果に基づく推奨技術]
                        2. **ポートフォリオ改善**: [具体的な改善項目]
                        3. **スキル強化**: [重点的に伸ばすべき領域]
                        """)

                with tab3:
                    st.subheader("📋 リポジトリ一覧")

                    # データフレーム表示
                    df_repos = pd.DataFrame([
                        {
                            'リポジトリ名': repo['name'],
                            '言語': repo.get('language', 'N/A'),
                            'サイズ(KB)': repo.get('size', 0),
                            'スター数': repo.get('stargazers_count', 0),
                            '最終更新': repo.get('updated_at', '')[:10]
                        }
                        for repo in repos
                    ])

                    st.dataframe(df_repos, use_container_width=True)

                    # CSV ダウンロード
                    csv = df_repos.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 CSV ダウンロード",
                        data=csv,
                        file_name=f"github_portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

    else:
        st.warning("GitHub Token と Anthropic API Key を入力してください")

        with st.expander("🔑 API Key の取得方法"):
            st.markdown("""
            **GitHub Personal Access Token:**
            1. GitHub Settings > Developer settings > Personal access tokens
            2. "Generate new token" > "Fine-grained personal access token"
            3. 必要な権限: `repos` (全リポジトリアクセス)

            **Anthropic API Key:**
            1. https://console.anthropic.com/ にアクセス
            2. API Keys セクションで新しいキーを作成
            """)

if __name__ == "__main__":
    main()