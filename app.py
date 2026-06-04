import base64
import random
import streamlit as st
from openai import OpenAI
import pandas as pd


# ====== Supabase クライアント（任意・失敗時は保存スキップ） ======
@st.cache_resource
def _get_supabase_client():
    """Supabaseクライアントを返す。secrets未設定・パッケージ未インストール時はNone。"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except (KeyError, FileNotFoundError):
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


def save_review_log(payload: dict) -> tuple[bool, str | None]:
    """review_logs テーブルに1件保存。成功=(True, None) / 失敗=(False, エラー文)。"""
    client = _get_supabase_client()
    if client is None:
        return False, "Supabase未設定"
    try:
        client.table("review_logs").insert(payload).execute()
        return True, None
    except Exception as e:
        return False, str(e)


# --- ⚙️ 設定エリア ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmDV5UTQENMNag-AjCx-FLMx7nTo8egWu7kdt5Df-n13Tst-ctf6Ew48MbcMpsTAs844v0Zbfv3gfS/pub?output=csv"

# 店舗リスト（EIGHT MEN 〇〇店 に統一）
STORES = {
    "EIGHT MEN 渋谷店": "https://g.page/r/CdXIDXyii4lgEAE/review",
    "EIGHT MEN 池袋西口店": "https://g.page/r/CaV4ekjwYsV1EAE/review",
    "EIGHT MEN 池袋東口店": "https://g.page/r/CdTMjlluc_OFEAE/review",
    "EIGHT MEN 新宿店": "https://g.page/r/CYky-2vp6Y0REAE/review",
    "EIGHT MEN 上野店": "https://g.page/r/CQh9ZNzN-HMPEAE/review",
    "EIGHT MEN 北千住店": "https://g.page/r/CVCsbonX5vKQEAE/review",
    "EIGHT MEN 吉祥寺店": "https://g.page/r/CUFrBrlWrjwaEAE/review",
    "EIGHT MEN 博多店": "https://g.page/r/Cfs_-7LhTWtDEAE/review",
    "EIGHT MEN 那覇新都心店": "https://g.page/r/CU_5fyrZxjvwEAE/review",
}

# エリア名辞書
STORE_AREAS = {
    "EIGHT MEN 渋谷店": "渋谷",
    "EIGHT MEN 池袋西口店": "池袋",
    "EIGHT MEN 池袋東口店": "池袋",
    "EIGHT MEN 新宿店": "新宿",
    "EIGHT MEN 上野店": "上野",
    "EIGHT MEN 北千住店": "北千住",
    "EIGHT MEN 吉祥寺店": "吉祥寺",
    "EIGHT MEN 博多店": "博多",
    "EIGHT MEN 那覇新都心店": "那覇新都心・おもろまち",
}

# --- リスト定義 ---
# 来店回数リスト
VISIT_LIST = ["初回", "2回目", "3回以上"]

# メニューリスト
MENU_LIST = [
    "メンズカット", 
    "カラー", 
    "ブリーチ", 
    "パーマ", 
    "ストレートパーマ", 
    "縮毛矯正", 
    "眉毛カット", 
    "ヘッドスパ"
]

# 来店動機リスト
MOTIVATION_LIST = [
    "伸びたから短くしたい",
    "広がり・癖を抑えたい",
    "骨格をカバーしたい",
    "セットを楽に・時短したい",
    "仕事・就活で使いたい",
    "ガラッとイメチェンしたい",
    "自分に似合う髪型を知りたい",
    "その他"
]

# 良かった点リスト
ATMOSPHERE_LIST = [
    "接客・対応",
    "技術・仕上がり",
    "カウンセリング",
    "店内の雰囲気",
    "価格の満足度",
    "その他"
]

# 口コミ生成時のペルソナ pool（同じ人格に偏らないよう毎回ランダム選択）
REVIEW_PERSONAS = [
    {"name": "IT系20代", "desc": "20代後半のITエンジニア。仕事帰りに通っている。カジュアルだがテンションは控えめ。短文寄りで要点を絞る。"},
    {"name": "営業30代", "desc": "30代前半の営業職。スーツ仕事で清潔感重視。丁寧めの口調で具体的に書く。"},
    {"name": "大学生", "desc": "20代前半の大学生。SNS的なノリの軽い口調。「やばい」「マジで」など気軽な言葉を混ぜる。"},
    {"name": "クリエイター30代", "desc": "30代後半のデザイナー／映像系。お洒落な雰囲気を求める。雰囲気や内装の描写が多め。"},
    {"name": "接客業20代", "desc": "20代後半の接客業（飲食・販売）。接客の質に敏感で、スタッフの対応の細部に触れる。"},
    {"name": "地方サラリーマン", "desc": "30代の地方出身サラリーマン。素朴でまっすぐな書き方。シンプルで誇張少なめ。"},
    {"name": "婚活中の男性", "desc": "20代後半、第一印象重視。「印象がよくなった」「人から褒められた」観点。"},
    {"name": "フリーランス", "desc": "20代後半のフリーランス。時間効率を重視。「早い」「楽」「セットしやすい」観点が強い。"},
    {"name": "既婚30代", "desc": "30代の既婚男性。「妻に褒められた」「家族から好評」観点もあり。"},
    {"name": "音楽芸術系20代", "desc": "20代の音楽・芸術系。個性派の髪型を求める。自由でやや独特なトーン。"},
]

# 良かった点アイコン（インラインSVG・線画）
_ATM_SVG = {
    "接客・対応": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0F0F0F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>',
    "技術・仕上がり": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0F0F0F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.12 15.88"/><path d="M14.47 14.48 20 20"/><path d="M8.12 8.12 12 12"/></svg>',
    "カウンセリング": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0F0F0F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "店内の雰囲気": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0F0F0F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 9V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v2"/><path d="M2 11v5a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v2H6v-2a2 2 0 0 0-4 0Z"/><path d="M4 18v2"/><path d="M20 18v2"/></svg>',
    "価格の満足度": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0F0F0F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9 8l3 4 3-4M9 13h6M9 16h6M12 12v6"/></svg>',
    "その他": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0F0F0F" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="8" cy="12" r="1" fill="#0F0F0F"/><circle cx="12" cy="12" r="1" fill="#0F0F0F"/><circle cx="16" cy="12" r="1" fill="#0F0F0F"/></svg>',
}

def _svg_to_md_img(svg: str) -> str:
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"![](data:image/svg+xml;base64,{b64})"

ATMOSPHERE_ICONS = {k: _svg_to_md_img(v) for k, v in _ATM_SVG.items()}

# 良かった点 サブ選択肢（MEO/SEOキーワード強化用）
ATMOSPHERE_SUBOPTIONS = {
    "接客・対応": [
        "笑顔の挨拶",
        "気遣いが細やか",
        "距離感が心地よい",
        "親しみやすい",
        "礼儀正しく丁寧",
        "会話量がちょうど良い",
    ],
    "技術・仕上がり": [
        "想像以上の仕上がり",
        "イメチェンが叶った",
        "クセを上手に抑えてくれた",
        "セットしやすい",
        "顔型に合った提案",
        "ダメージを抑えた施術",
        "持ちが良い",
    ],
    "カウンセリング": [
        "じっくり要望を聞いてくれた",
        "写真を見ながら相談できた",
        "プロ目線の提案",
        "似合う髪型を一緒に検討",
        "ライフスタイルに合った提案",
        "アフターケアの説明",
    ],
    "店内の雰囲気": [
        "明るく賑やか",
        "落ち着いた空間",
        "お洒落な内装",
        "高級感がある",
        "プライベート感",
        "BGMが心地よい",
        "店内が清潔",
    ],
    "価格の満足度": [
        "コスパが良い",
        "仕上がりに対して適正",
        "メンズ価格が良心的",
        "メニュー料金が明朗",
        "クーポンがお得",
        "リピートしやすい価格",
    ],
}

# --- 🎨 ページ設定 & デザイン ---
st.set_page_config(page_title="GUEST REVIEW", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=Noto+Serif+JP:wght@400;500;600;700&family=Noto+Sans+JP:wght@300;400;500;700&display=swap');

    /* サイドバーのページナビ（dashboardへのリンク）を非表示にする
       お客さん向けの画面でDashboardが見えないようにする目的 */
    [data-testid="stSidebarNav"] { display: none !important; }

    /* ベース：クリーム背景＋エディトリアル */
    html, body, [class*="css"] {
        font-family: "Inter", "Noto Sans JP", -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F0F0F;
        letter-spacing: 0.02em;
    }
    .stApp {
        background-color: #F5F1E8;
    }
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 560px;
    }

    /* 生成ボタン：コバルトブルー */
    .stButton>button {
        width: 100%;
        border-radius: 2px;
        font-weight: 600;
        padding: 20px;
        background: #1E3A8A;
        color: #FFFFFF;
        border: none;
        box-shadow: 0 8px 20px rgba(30, 58, 138, 0.25);
        transition: all 0.25s ease;
        font-size: 13px;
        letter-spacing: 0.25em;
        margin-top: 24px;
        text-transform: uppercase;
    }
    .stButton>button:hover {
        background: #15296B;
        transform: translateY(-1px);
        box-shadow: 0 12px 28px rgba(30, 58, 138, 0.35);
    }
    .stButton>button:active {
        transform: translateY(0);
    }

    /* 直行ボタン：黒アウトライン */
    .direct-link-btn {
        display: block;
        width: 100%;
        text-align: center;
        padding: 16px;
        margin: 24px 0 12px 0;
        background-color: transparent;
        color: #0F0F0F;
        border: 1px solid #0F0F0F;
        border-radius: 2px;
        text-decoration: none;
        font-weight: 500;
        font-size: 12px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        transition: all 0.2s ease;
    }
    .direct-link-btn:hover {
        background-color: #0F0F0F;
        color: #F5F1E8;
    }

    /* ステップラベル：番号は円形チップ */
    .step-label {
        color: #0F0F0F;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        letter-spacing: 0.04em;
    }
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #0F0F0F;
        color: #F5F1E8;
        font-family: "Playfair Display", serif;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0;
        margin-right: 12px;
        line-height: 1;
    }

    /* 見出し：セリフ体エディトリアル */
    h3 {
        color: #0F0F0F !important;
        margin-bottom: 0px !important;
        font-family: "Playfair Display", "Noto Serif JP", serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
    }
    h4 {
        color: #0F0F0F !important;
        font-weight: 600 !important;
        letter-spacing: 0.15em !important;
        margin-top: 12px !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
    }

    /* 入力フィールド */
    .stTextInput > div > div > input {
        border-radius: 2px;
        padding: 14px;
        font-size: 14px;
        border: 1px solid #D8D2C5;
        background-color: #FFFFFF;
        color: #0F0F0F;
    }
    .stTextInput > div > div > input:focus {
        border-color: #1E3A8A;
        box-shadow: 0 0 0 2px rgba(30, 58, 138, 0.12);
    }

    /* セレクトボックス */
    .stSelectbox > div > div {
        border-radius: 2px;
        border: 1px solid #D8D2C5;
        background-color: #FFFFFF;
    }
    .stSelectbox > div > div:hover {
        border-color: #0F0F0F;
    }

    /* Pills 共通 */
    button[data-baseweb="button"] {
        border-radius: 2px !important;
        font-weight: 500 !important;
        letter-spacing: 0.04em !important;
    }

    /* Pills 非選択：白×細枠 */
    div[data-baseweb="button-group"] button[aria-pressed="false"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D8D2C5 !important;
        color: #0F0F0F !important;
    }
    div[data-baseweb="button-group"] button[aria-pressed="false"]:hover {
        border-color: #0F0F0F !important;
        background-color: #FAF7F0 !important;
    }

    /* Pills 選択中：コバルト塗り */
    div[data-baseweb="button-group"] button[aria-pressed="true"] {
        background-color: #1E3A8A !important;
        border: 1px solid #1E3A8A !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 10px rgba(30, 58, 138, 0.2) !important;
    }

    /* Divider：細い実線 */
    hr {
        border: none !important;
        height: 1px !important;
        background: #D8D2C5 !important;
        margin: 2rem 0 !important;
    }

    /* 生成された口コミの表示枠 */
    .stCode {
        border-radius: 2px;
        border: 1px solid #D8D2C5;
        background-color: #FFFFFF !important;
    }

    /* アラート */
    div[data-testid="stAlert"] {
        border-radius: 2px;
        border-left: 3px solid #1E3A8A;
    }

    /* ====== ブランド・ウォードマーク（最上段） ====== */
    .brand-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 4px 18px 4px;
        border-bottom: 1px solid #D8D2C5;
        margin-bottom: 28px;
    }
    .brand-mark {
        font-family: "Playfair Display", serif;
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 0.18em;
        color: #0F0F0F;
    }
    .brand-tag {
        font-size: 9px;
        letter-spacing: 0.4em;
        color: #6B6B6B;
        font-weight: 600;
        text-transform: uppercase;
    }

    /* ====== ステップ・プログレス・インジケーター ====== */
    .progress-wrap {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 8px 0 28px 0;
        padding: 4px 0;
    }
    .progress-step {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: transparent;
        border: 1px solid #0F0F0F;
        color: #0F0F0F;
        font-family: "Playfair Display", serif;
        font-weight: 600;
        font-size: 12px;
        flex-shrink: 0;
    }
    .progress-line {
        flex: 1;
        height: 1px;
        background: #D8D2C5;
        margin: 0 4px;
    }
    .progress-eyebrow {
        text-align: center;
        font-size: 10px;
        letter-spacing: 0.4em;
        color: #1E3A8A;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    /* ====== チェックボックス・カード（良かった点） ====== */
    /* カード全体クリック可能 + チェック時にサブピル展開対応 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #D8D2C5 !important;
        border-radius: 2px !important;
        background: #FFFFFF !important;
        padding: 0 !important;
        margin-bottom: 10px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
        min-height: 60px !important;
        cursor: pointer !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] {
        width: 100% !important;
        margin: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: #0F0F0F !important;
        box-shadow: 0 2px 8px rgba(15, 15, 15, 0.06);
    }
    /* labelをカード上部全域に拡張＝チェックの上半分はカード全体クリックで反応 */
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        min-height: 60px !important;
        padding: 10px 12px !important;
        margin: 0 !important;
        cursor: pointer !important;
        box-sizing: border-box !important;
        font-size: 13px !important;
        letter-spacing: 0.02em !important;
    }

    /* ====== サブ選択肢カテゴリラベル（カード直下） ====== */
    .sub-category-label {
        font-size: 11px;
        font-weight: 600;
        color: #1E3A8A;
        margin: 0 0 8px 0;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    /* カード内のSVGアイコン（markdown image）のサイズ・整列 */
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] img {
        width: 18px !important;
        height: 18px !important;
        vertical-align: middle !important;
        margin-right: 4px !important;
        display: inline-block !important;
    }

    /* ====== ステップ5：CSS Grid + dense flow ====== */
    /* デスクトップ3列・スマホ2列。サブ選択肢は該当カード直下に全幅で挿入。
       重要：.st-key-atm_grid を直接ターゲット（descendant指定にすると
       サブコンテナ自身もstVerticalBlockなのでgrid化されてしまう） */
    .st-key-atm_grid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        grid-auto-flow: dense !important;
        gap: 10px !important;
    }
    @media (max-width: 640px) {
        .st-key-atm_grid {
            grid-template-columns: repeat(2, 1fr) !important;
        }
    }
    /* グリッド内のカード余白はgapで管理するのでmargin-bottom削除 */
    .st-key-atm_grid [data-testid="stVerticalBlockBorderWrapper"] {
        margin-bottom: 0 !important;
    }

    /* サブコンテナ（grid item）を全幅spanさせる：
       grid直下のstElementContainer内にst-key-atm_subs_X要素があるものを対象 */
    .st-key-atm_grid > [data-testid="stElementContainer"]:has([class*="st-key-atm_subs_"]) {
        grid-column: 1 / -1 !important;
    }
    .st-key-atm_grid [class*="st-key-atm_subs_"] {
        padding: 4px 0 8px 0 !important;
        border-left: none !important;
        background: transparent !important;
    }
    /* サブ選択肢ピルを左詰め横並び＋お悩み・来店動機と同じ丸角オーバル形状 */
    .st-key-atm_grid [class*="st-key-atm_subs_"] div[data-baseweb="button-group"] {
        display: flex !important;
        flex-direction: row !important;
        justify-content: flex-start !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        width: 100% !important;
    }
    .st-key-atm_grid [class*="st-key-atm_subs_"] div[data-baseweb="button-group"] button {
        border-radius: 999px !important;
        padding: 8px 18px !important;
        font-size: 12px !important;
        min-height: 34px !important;
        flex: 0 0 auto !important;
        width: auto !important;
        max-width: max-content !important;
    }

    /* ====== ステップ3（メニュー）等のスマホ折り返し ====== */
    @media (max-width: 640px) {
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 8px !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            flex: 0 0 calc(50% - 4px) !important;
            max-width: calc(50% - 4px) !important;
            min-width: calc(50% - 4px) !important;
            width: calc(50% - 4px) !important;
        }
    }

    /* ====== 必須バッジ（黒枠ニュートラル） ====== */
    .required-badge {
        display: inline-block;
        margin-left: 10px;
        padding: 2px 8px;
        background: transparent;
        color: #0F0F0F;
        border: 1px solid #0F0F0F;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.15em;
        border-radius: 2px;
        vertical-align: middle;
        line-height: 1.4;
    }

    /* ====== フッター・サイン ====== */
    .footer-mark {
        margin-top: 48px;
        padding-top: 24px;
        border-top: 1px solid #D8D2C5;
        text-align: center;
        font-family: "Playfair Display", serif;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.3em;
        color: #0F0F0F;
    }
    .footer-sub {
        font-family: "Inter", sans-serif;
        font-size: 9px;
        letter-spacing: 0.35em;
        color: #6B6B6B;
        font-weight: 500;
        text-transform: uppercase;
        margin-top: 6px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ブランドバー（最上段） ---
st.markdown("""
<div class="brand-bar">
    <div class="brand-mark">EIGHT MEN</div>
    <div class="brand-tag">Style · Cut · Life</div>
</div>
""", unsafe_allow_html=True)

# --- 📥 データ読み込み ---
@st.cache_data(ttl=600)
def load_staff_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.groupby('店舗名')['スタッフ名'].apply(list).to_dict()
    except:
        return {}

staff_data_dict = load_staff_data()

# --- 📍 店舗選択 ---
query_params = st.query_params
url_store_param = query_params.get("store")
found_store_name = None

if url_store_param:
    for store_key in STORES.keys():
        if url_store_param in store_key:
            found_store_name = store_key
            break

if found_store_name:
    selected_store_name = found_store_name
else:
    selected_store_name = st.selectbox("ご利用の店舗", list(STORES.keys()))

selected_store_link = STORES[selected_store_name]
area_keyword = STORE_AREAS.get(selected_store_name, "駅近")

# --- 店舗名表示（エディトリアル） ---
st.markdown(f"""
<div style='text-align: center; margin: 20px 0 4px 0;'>
    <div style='
        font-size: 11px;
        letter-spacing: 0.45em;
        color: #1E3A8A;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 14px;
    '>Guest Review</div>
    <h3 style='
        margin: 0;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-family: "Playfair Display", "Noto Serif JP", serif;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: 0.03em;
        line-height: 1.1;
        width: 100%;
        color: #0F0F0F;
    '>{selected_store_name}</h3>
    <div style='
        width: 48px;
        height: 1px;
        background: #0F0F0F;
        margin: 22px auto 4px auto;
    '></div>
</div>
""", unsafe_allow_html=True)


# --- 直行ボタン ---
st.markdown(f"""
<a href="{selected_store_link}" target="_blank" class="direct-link-btn">
    自分で口コミを書く（Googleマップへ）
</a>
""", unsafe_allow_html=True)

st.divider()

# --- AIにお任せ ---
st.markdown("#### AIにお任せする方はこちら")
st.markdown("<p style='color: #666; font-size: 13px; letter-spacing: 0.03em; margin-top: -8px;'>簡単な質問に答えるだけで、下書きを作成します。</p>", unsafe_allow_html=True)

# --- ステップ・プログレス ---
st.markdown("""
<div class="progress-wrap">
    <div class="progress-step">1</div>
    <div class="progress-line"></div>
    <div class="progress-step">2</div>
    <div class="progress-line"></div>
    <div class="progress-step">3</div>
    <div class="progress-line"></div>
    <div class="progress-step">4</div>
    <div class="progress-line"></div>
    <div class="progress-step">5</div>
</div>
""", unsafe_allow_html=True)

# --- 📝 入力フォーム ---
st.markdown('<span class="step-label"><span class="step-number">01</span>担当スタッフ</span>', unsafe_allow_html=True)

csv_store_key = selected_store_name.replace("EIGHT MEN ", "")
current_staff_list = staff_data_dict.get(csv_store_key, [])

if not current_staff_list:
    current_staff_list = staff_data_dict.get(selected_store_name, ["指定しない"])

staff_name = st.selectbox("担当スタッフ", current_staff_list, label_visibility="collapsed")

st.write("")
st.markdown('<span class="step-label"><span class="step-number">02</span>来店回数</span>', unsafe_allow_html=True)

visit_count = st.pills(
    "来店回数", 
    VISIT_LIST, 
    selection_mode="single", 
    default="初回",
    label_visibility="collapsed"
)

st.write("")
st.markdown('<span class="step-label"><span class="step-number">03</span>ご利用いただいたサービス（複数可）</span>', unsafe_allow_html=True)

menu_cols = st.columns(2)
menu = []
for i, item in enumerate(MENU_LIST):
    with menu_cols[i % 2]:
        if st.checkbox(item, value=(i == 0), key=f"menu_{item}"):
            menu.append(item)

st.write("")
st.markdown('<span class="step-label"><span class="step-number">04</span>お悩み・来店動機（複数可）</span>', unsafe_allow_html=True)

motivations = st.pills(
    "きっかけ", 
    MOTIVATION_LIST, 
    selection_mode="multi", 
    default=[], 
    label_visibility="collapsed"
)

motivation_detail = ""
if motivations and "その他" in motivations:
    motivation_detail = st.text_input(
        "お悩み・動機の詳細（その他）", 
        placeholder="その他：具体的なお悩みや、こうなりたい！という希望など", 
        label_visibility="collapsed"
    )

st.write("")
st.markdown('<span class="step-label"><span class="step-number">05</span>良かった点（複数選択可）<span class="required-badge">必須</span></span>', unsafe_allow_html=True)

atmospheres = []
atmosphere_subdetails = {}
with st.container(key="atm_grid"):
    for idx, item in enumerate(ATMOSPHERE_LIST):
        with st.container(border=True):
            checked = st.checkbox(f"{ATMOSPHERE_ICONS[item]} {item}", key=f"atm_{item}")
        if checked:
            atmospheres.append(item)
            if ATMOSPHERE_SUBOPTIONS.get(item):
                with st.container(key=f"atm_subs_{idx}"):
                    st.markdown(f'<div class="sub-category-label">{item}</div>', unsafe_allow_html=True)
                    sel = st.pills(
                        f"{item}_詳細",
                        ATMOSPHERE_SUBOPTIONS[item],
                        selection_mode="multi",
                        default=[],
                        key=f"atm_sub_{item}",
                        label_visibility="collapsed",
                    )
                    if sel:
                        atmosphere_subdetails[item] = sel

atmosphere_detail = ""
if atmospheres and "その他" in atmospheres:
    atmosphere_detail = st.text_input(
        "雰囲気・接客の詳細（その他）", 
        placeholder="その他：スタッフの対応や店内の様子など", 
        label_visibility="collapsed"
    )

st.write("")
submit_button = st.button("口コミを生成する")

# --- 🤖 生成ロジック ---
if submit_button:
    if not menu and not motivations and not atmospheres and not motivation_detail and not atmosphere_detail:
        st.warning("項目をいくつか選択してください")
    else:
        # スタッフ名を苗字だけにする処理
        staff_last_name = staff_name.replace("　", " ").split(" ")[0] if staff_name != "指定しない" else "スタッフ"

        # データ整形
        menu_text = "と".join(menu) if menu else "カット"
        
        # 動機の処理
        clean_motivations = [m for m in motivations if m != "その他"] if motivations else []
        motivation_text_parts = clean_motivations.copy()
        if motivation_detail:
            motivation_text_parts.append(motivation_detail)
        motivation_final_text = "、".join(motivation_text_parts) if motivation_text_parts else "特になし"

        # 良かった点の処理（カテゴリ + サブ詳細を組み合わせる）
        clean_atmospheres = [a for a in atmospheres if a != "その他"] if atmospheres else []
        atmosphere_text_parts = []
        for atm in clean_atmospheres:
            subs = atmosphere_subdetails.get(atm, [])
            if subs:
                atmosphere_text_parts.append(f"{atm}（{'、'.join(subs)}）")
            else:
                atmosphere_text_parts.append(atm)
        if atmosphere_detail:
            atmosphere_text_parts.append(atmosphere_detail)
        atmosphere_final_text = "、".join(atmosphere_text_parts) if atmosphere_text_parts else "良かった"

        # 💡 プロンプト：ペルソナをランダム選択して人格を多様化、メンズキーワードを必須化
        persona = random.choice(REVIEW_PERSONAS)
        system_instruction = f"""
        あなたは「{selected_store_name}」に通う次のような男性客です：{persona["desc"]}
        【美容室（メンズサロン）での体験】について、Googleマップ用の自然な口コミを150文字以内で作成してください。

        【重要ルール：AIっぽさを消すための絶対条件】
        1. 【エリア名の自然な使い方】「{area_keyword}のこのお店」という直訳のような不自然な表現は絶対禁止。代わりに「{area_keyword}の職場から近くて」「わざわざ{area_keyword}まで通ってます」「{area_keyword}周辺で予定がある時に」など、自分の生活圏や行動パターンに馴染んだ自然な形でエリア名を混ぜること。店名は出さなくてよい。
        2. 【美容室としての文脈を厳守】お客様は「髪を切る」ために来ています。「静かにリラックスできた」という情報を「作業に集中できた」「勉強が捗る」などカフェやコワーキングスペースのように勘違いして書くのは絶対に禁止。「落ち着いて過ごせた」「シャンプーでウトウトしてしまった」「タブレットで動画を見てくつろげた」など、美容室として100%自然な感想に変換すること。
        3. 「担当：{staff_name}」「メニュー：{menu_text}」のような箇条書きは禁止。「{staff_last_name}さんに{menu_text}をお願いして〜」と文脈に溶け込ませる。
        4. 来店動機・悩み「{motivation_final_text}」について、どう解決したか（ベネフィット）を書く。
        5. 【良かった点とその詳細】「{atmosphere_final_text}」を反映させる。カッコ内の詳細キーワード（例：明るく賑やか／コスパが良い／シャンプー台がきれい等）は、そのままコピペせず文脈に自然に溶け込ませる。ただし2〜3個の具体ワードは必ず本文に含めること（MEO観点：抽象的な感想だけでは検索評価が弱いため、具体的な体験ワードが必要）。
        6. 今回の来店回数は「{visit_count}」です。初回なら「初めての利用」という背景を、2回目以降なら「リピートしている」ニュアンスを自然に含める。
        7. 【禁止ワード】AI特有の不自然な表現（「プロフェッショナルな」「至福のひととき」「まるで〜のようです」「大変満足しております」「強くお勧めします」）は絶対に使わない。
        8. 【文体の統一】上記の客像に合った口調・テンションで、スマホでサクッと書いたような自然な口語体にする。客像によってラフ・丁寧・テンション高めなど書き分ける。**最重要：1つの口コミ内で文末と語彙のレベルを必ず統一すること**。書き始めに使った文体（敬語 or タメ口、丁寧 or ラフ）と途中で混在させるのは絶対NG。例：
           - 悪い例①「初めて行ったけど、お願いしました。」→「行った」（タメ口）と「お願いしました」（敬語）が混在。敬語ベースなら「初めて行きましたが、お願いしました」に統一
           - 悪い例②「丁寧にカットしてくれました。結果は想像以上！」→ 落ち着いた敬語の途中で「！」付きの感情爆発が不自然。テンションは全体で均一にする
           - 「！」「最高」「やばい」「マジで」などの強い言葉を使うかどうかは、口コミ全体で揃える。1つの口コミ内に1個だけポンと入れない
        9. 【MEO必須キーワード】本文中に「メンズ」というワードを必ず1〜2回、自然に含める。例：「メンズカット」「メンズサロン」「メンズ向け」「メンズスタイル」など、文脈に合わせて選ぶ。1文目に入れる必要はないが、本文のどこかに自然な形で必ず含めること。
        """
        user_content = f"動機・悩み: {motivation_final_text}\n雰囲気・感想: {atmosphere_final_text}"

        try:
            with st.spinner("AIが文章を考えています..."):
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": user_content}],
                    temperature=0.8,
                )
                review_text = response.choices[0].message.content

            st.success("✅ 作成完了！枠の右上にあるアイコン（📋）から1タップでコピーできます！")
            st.code(review_text, language="text", wrap_lines=True)

            # ====== Supabase 保存（失敗してもアプリは続行） ======
            satisfaction_points_flat = []
            for atm in clean_atmospheres:
                subs = atmosphere_subdetails.get(atm, [])
                if subs:
                    for s in subs:
                        satisfaction_points_flat.append(f"{atm}:{s}")
                else:
                    satisfaction_points_flat.append(atm)
            if atmosphere_detail:
                satisfaction_points_flat.append(f"その他:{atmosphere_detail}")

            log_payload = {
                "store_name": selected_store_name,
                "staff_name": staff_name,
                "menu": menu_text,
                "visit_reason": motivation_final_text,
                "satisfaction_points": satisfaction_points_flat,
                "review_tone": [persona["name"]],
                "generated_review": review_text,
                "copied": False,
            }
            ok, err = save_review_log(log_payload)
            if not ok and err and err != "Supabase未設定":
                st.warning(f"保存に失敗しましたが、口コミ生成は完了しています。（{err}）")

            st.markdown(f"""<a href="{selected_store_link}" target="_blank" style="text-decoration: none;"><button style="width: 100%; background: #1E3A8A; color: #FFFFFF; padding: 20px; border: none; border-radius: 2px; font-weight: 600; margin-top: 16px; font-size: 13px; letter-spacing: 0.25em; text-transform: uppercase; cursor: pointer; transition: all 0.25s ease; box-shadow: 0 8px 20px rgba(30, 58, 138, 0.25);">Googleマップを開いて投稿する</button></a>""", unsafe_allow_html=True)

        except Exception as e:
            st.error("エラーが発生しました。APIキーを確認してください。")

# --- フッター・サイン ---
st.markdown("""
<div class="footer-mark">
    EIGHT MEN
    <div class="footer-sub">Be Your Style · Be Your Voice</div>
</div>
""", unsafe_allow_html=True)
