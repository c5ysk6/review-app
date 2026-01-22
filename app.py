import streamlit as st
from openai import OpenAI
import pandas as pd

# --- ⚙️ 設定エリア ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmDV5UTQENMNag-AjCx-FLMx7nTo8egWu7kdt5Df-n13Tst-ctf6Ew48MbcMpsTAs844v0Zbfv3gfS/pub?output=csv"

# 店舗ごとのGoogleマップリンク
STORES = {
    "渋谷店": "https://g.page/r/CdXIDXyii4lgEAE/review",
    "池袋西口店": "https://g.page/r/CaV4ekjwYsV1EAE/review",
    "池袋東口店": "https://g.page/r/CdTMjlluc_OFEAE/review",
    "新宿店": "https://g.page/r/CYky-2vp6Y0REAE/review",
    "上野店": "https://g.page/r/CQh9ZNzN-HMPEAE/review",
    "北千住店": "https://g.page/r/CVCsbonX5vKQEAE/review",
    "吉祥寺店": "https://g.page/r/CUFrBrlWrjwaEAE/review",
    "博多店": "https://g.page/r/Cfs_-7LhTWtDEAE/review",
    "那覇新都心店": "https://g.page/r/CU_5fyrZxjvwEAE/review",
}

# 【SEO/MEO用】店舗名に紐づく「狙いたい地名・駅名」
STORE_AREAS = {
    "渋谷店": "渋谷",
    "池袋西口店": "池袋",
    "池袋東口店": "池袋",
    "新宿店": "新宿",
    "上野店": "上野",
    "北千住店": "北千住",
    "吉祥寺店": "吉祥寺",
    "博多店": "博多",
    "那覇新都心店": "那覇",
}

# 【SEO対策】来店動機リスト（絵文字なし・ポジティブネガティブ混合）
MOTIVATION_LIST = [
    "剛毛・広がり・癖を抑えたい",
    "絶壁・骨格をカバーしたい",
    "セットを楽に・時短したい",
    "ビジネス・就活で使いたい",
    "ガラッとイメチェンしたい",
    "自分に似合う髪型を知りたい",
    "リラックスして過ごしたい"
]

# --- 🎨 ページ設定 & デザイン ---
st.set_page_config(page_title="EIGHT MEN 口コミ", layout="centered")

st.markdown("""
    <style>
    .stButton>button {
        width: 100%; 
        border-radius: 30px; 
        font-weight: bold; 
        padding: 16px; 
        background: linear-gradient(135deg, #D32F2F 0%, #FF5252 100%); 
        color: white; 
        border: none;
        box-shadow: 0 4px 10px rgba(211, 47, 47, 0.3);
        transition: all 0.3s ease;
        font-size: 18px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(211, 47, 47, 0.5);
    }
    h1 {
        color: #333;
        font-family: sans-serif;
        font-weight: 800;
        border-bottom: 3px solid #D32F2F;
        display: inline-block;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .stCaption {
        font-size: 14px;
        color: #666;
        font-weight: bold;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 📥 データ読み込み ---
@st.cache_data(ttl=600)
def load_staff_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.groupby('店舗名')['スタッフ名'].apply(list).to_dict()
    except Exception:
        return {}

staff_data_dict = load_staff_data()

# --- 📍 店舗自動判定 ---
query_params = st.query_params
pre_selected_store = query_params.get("store", None)

if pre_selected_store and pre_selected_store in STORES:
    selected_store_name = pre_selected_store
    selected_store_link = STORES[pre_selected_store]
    # MEOエリアを取得
    area_keyword = STORE_AREAS.get(selected_store_name, "駅近")
    st.markdown(f"<h3 style='color: #D32F2F;'>📍 {selected_store_name}</h3>", unsafe_allow_html=True)
else:
    selected_store_name = st.selectbox("店舗を選択", list(STORES.keys()))
    selected_store_link = STORES[selected_store_name]
    area_keyword = STORE_AREAS.get(selected_store_name, "駅近")

st.title("GUEST REVIEW")
st.write("簡単な質問に答えるだけで、投稿用の文章を作成します。")

# --- 📝 入力フォーム ---
st.divider() 

# 1. スタッフ選択
st.caption("担当スタッフ")
current_staff_list = staff_data_dict.get(selected_store_name, ["指定しない"])
if not current_staff_list: current_staff_list = ["指定しない"]
staff_name = st.selectbox("担当スタッフ", current_staff_list, label_visibility="collapsed")

st.write("") 

# 2. メニュー選択
st.caption("① 本日のメニュー（複数選択可）")
menu = st.pills(
    "メニュー",
    ["メンズカット", "フェードカット", "波巻きパーマ", "ツイストスパイラル", "ニュアンスパーマ", "カラー", "ブリーチ", "眉毛カット", "ヘッドスパ"],
    selection_mode="multi",
    label_visibility="collapsed"
)

st.write("")

# 3. 動機・きっかけ（ハイブリッド入力の核）
st.caption("② ご来店・オーダーのきっかけ（複数選択可）")
motivations = st.pills(
    "きっかけ",
    MOTIVATION_LIST,
    selection_mode="multi",
    label_visibility="collapsed"
)

st.write("")

# 4. 自由記述（ここが最強のSEO）
st.caption("③ その他・一言メモ（任意）")
free_text = st.text_input(
    "label_hidden",
    placeholder="例：彼女とのデート前なので気合いを入れたい、など",
    label_visibility="collapsed"
)

st.divider() 

submit_button = st.button("口コミを生成する ✨")

# --- 🤖 生成ロジック ---
if submit_button:
    if not menu and not motivations and not free_text:
        st.warning("メニューまたはきっかけを選択してください")
    else:
        # データの整形
        menu_text = ", ".join(menu) if menu else "カット"
        motivation_text = ", ".join(motivations)
        
        # システムプロンプト（AIへの役割指示）
        system_instruction = f"""
        あなたは「メンズサロン EIGHT MEN {selected_store_name}」に通う男性客です。
        入力情報を元に、Googleマップ用の自然な口コミを150文字以内で作成してください。
        
        【重要ルール】
        1. エリア名「{area_keyword}」を自然に文中に含めること（MEO対策）。
        2. 「SEO」等の専門用語は使わず、少し話し言葉を混ぜてリアルにする。
        3. 「担当：{staff_name}」と「メニュー：{menu_text}」を含める。
        4. お客様の入力した「きっかけ（{motivation_text}）」や「メモ（{free_text}）」に対し、それがどう解決したか（ベネフィット）を書く。
        5. もし「メモ（{free_text}）」がある場合は、その内容を最優先で文章の核にする。
        """

        # ユーザープロンプト（変数渡し）
        user_content = f"動機: {motivation_text}\n自由メモ: {free_text}"

        try:
            with st.spinner("AIが文章を考えています..."):
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                
                response = client.chat.completions.create(
                    model="gpt-4", # または gpt-3.5-turbo
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.7,
                )
                
                review_text = response.choices[0].message.content

            # --- 結果表示 ---
            st.success("作成完了！下のテキストをコピーしてください。")
            
            # コピーしやすいようにコードブロックまたはテキストエリアで表示
            st.text_area("↓↓ タップしてすべて選択・コピー ↓↓", review_text, height=150)
            
            # Googleマップへ誘導
            st.markdown(f"""
            <a href="{selected_store_link}" target="_blank">
                <button style="
                    width: 100%;
                    background-color: #4285F4;
                    color: white;
                    padding: 12px;
                    border: none;
                    border-radius: 30px;
                    font-weight: bold;
                    margin-top: 10px;
                    cursor: pointer;">
                    Googleマップを開いて投稿する 🌍
                </button>
            </a>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
            st.info("APIキーの設定を確認してください。")
