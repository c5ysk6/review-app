import streamlit as st
from openai import OpenAI
import pandas as pd

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

# 雰囲気リスト
ATMOSPHERE_LIST = [
    "会話が楽しく盛り上がった",
    "店内がお洒落",
    "静かにリラックスできた",
    "丁寧なカウンセリング",
    "テキパキして早かった",
    "プロの技術・アドバイス",
    "要望をうまく汲み取ってくれた",
    "その他"
]

# --- 🎨 ページ設定 & デザイン ---
st.set_page_config(page_title="GUEST REVIEW", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=Noto+Serif+JP:wght@400;500;600;700&family=Noto+Sans+JP:wght@300;400;500;700&display=swap');

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
    </style>
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
        font-size: 10px;
        letter-spacing: 0.45em;
        color: #6B6B6B;
        font-weight: 500;
        text-transform: uppercase;
        margin-top: 12px;
    '>Style · Cut · Life</div>
    <div style='
        width: 48px;
        height: 1px;
        background: #0F0F0F;
        margin: 18px auto 4px auto;
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
st.write("")

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
st.markdown('<span class="step-label"><span class="step-number">03</span>本日のメニュー（複数可）</span>', unsafe_allow_html=True)

menu = st.pills(
    "メニュー", 
    MENU_LIST, 
    selection_mode="multi", 
    default=[MENU_LIST[0]], 
    label_visibility="collapsed"
)

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
st.markdown('<span class="step-label"><span class="step-number">05</span>店内の雰囲気・接客の良かった点（複数可）</span>', unsafe_allow_html=True)

atmospheres = st.pills(
    "雰囲気", 
    ATMOSPHERE_LIST, 
    selection_mode="multi", 
    default=[], 
    label_visibility="collapsed"
)

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

        # 雰囲気の処理
        clean_atmospheres = [a for a in atmospheres if a != "その他"] if atmospheres else []
        atmosphere_text_parts = clean_atmospheres.copy()
        if atmosphere_detail:
            atmosphere_text_parts.append(atmosphere_detail)
        atmosphere_final_text = "、".join(atmosphere_text_parts) if atmosphere_text_parts else "良かった"

        # 💡 プロンプトをさらに厳密に修正！
        system_instruction = f"""
        あなたは「{selected_store_name}」に通う、トレンドに敏感な20代〜30代の男性客です。
        【美容室（メンズサロン）での体験】について、Googleマップ用の自然な口コミを150文字以内で作成してください。

        【重要ルール：AIっぽさを消すための絶対条件】
        1. 【エリア名の自然な使い方】「{area_keyword}のこのお店」という直訳のような不自然な表現は絶対禁止。代わりに「{area_keyword}の職場から近くて」「わざわざ{area_keyword}まで通ってます」「{area_keyword}周辺で予定がある時に」など、自分の生活圏や行動パターンに馴染んだ自然な形でエリア名を混ぜること。店名は出さなくてよい。
        2. 【美容室としての文脈を厳守】お客様は「髪を切る」ために来ています。「静かにリラックスできた」という情報を「作業に集中できた」「勉強が捗る」などカフェやコワーキングスペースのように勘違いして書くのは絶対に禁止。「落ち着いて過ごせた」「シャンプーでウトウトしてしまった」「タブレットで動画を見てくつろげた」など、美容室として100%自然な感想に変換すること。
        3. 「担当：{staff_name}」「メニュー：{menu_text}」のような箇条書きは禁止。「{staff_last_name}さんに{menu_text}をお願いして〜」と文脈に溶け込ませる。
        4. 来店動機・悩み「{motivation_final_text}」について、どう解決したか（ベネフィット）を書く。
        5. 雰囲気・感想「{atmosphere_final_text}」を反映させる。
        6. 今回の来店回数は「{visit_count}」です。初回なら「初めての利用」という背景を、2回目以降なら「リピートしている」ニュアンスを自然に含める。
        7. 【禁止ワード】AI特有の不自然な表現（「プロフェッショナルな」「至福のひととき」「まるで〜のようです」「大変満足しております」「強くお勧めします」）は絶対に使わない。
        8. 【文体】スマホでサクッと書いたような、少しラフでリアルな口語体（「〜でよかったです！」「〜してもらいました」「最高です」「また行きます」など）にする。
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
            
            st.markdown(f"""<a href="{selected_store_link}" target="_blank" style="text-decoration: none;"><button style="width: 100%; background: #1E3A8A; color: #FFFFFF; padding: 20px; border: none; border-radius: 2px; font-weight: 600; margin-top: 16px; font-size: 13px; letter-spacing: 0.25em; text-transform: uppercase; cursor: pointer; transition: all 0.25s ease; box-shadow: 0 8px 20px rgba(30, 58, 138, 0.25);">Googleマップを開いて投稿する</button></a>""", unsafe_allow_html=True)

        except Exception as e:
            st.error("エラーが発生しました。APIキーを確認してください。")
