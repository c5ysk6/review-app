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

# リスト定義
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
ATMOSPHERE_LIST = [
    "丁寧なカウンセリング", "会話が楽しく盛り上がった", "静かにリラックスできた",
    "テキパキして早かった", "プロの技術・アドバイス", "店内がお洒落", "その他"
]

# --- 🎨 ページ設定 & デザイン ---
st.set_page_config(page_title="GUEST REVIEW", layout="centered")

st.markdown("""
    <style>
    body { font-family: "Helvetica Neue", Arial, sans-serif; }
    
    /* 生成ボタン */
    .stButton>button {
        width: 100%; border-radius: 30px; font-weight: bold; padding: 16px; 
        background: linear-gradient(135deg, #D32F2F 0%, #FF5252 100%); 
        color: white; border: none; box-shadow: 0 4px 10px rgba(211, 47, 47, 0.3);
        transition: all 0.3s ease; font-size: 18px; margin-top: 10px;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(211, 47, 47, 0.5); }

    /* 直行ボタン */
    .direct-link-btn {
        display: block; width: 100%; text-align: center; padding: 12px; margin: 15px 0 10px 0;
        background-color: #f0f2f6; color: #555; border: 1px solid #ddd; border-radius: 10px;
        text-decoration: none; font-weight: bold; font-size: 14px;
    }
    
    /* ステップ番号 */
    .step-label { color: #333; font-weight: bold; font-size: 16px; margin-bottom: 8px; display: block; }
    .step-number { color: #D32F2F; font-weight: 900; margin-right: 6px; }
    h3 { color: #D32F2F !important; margin-bottom: 0px !important; }
    
    /* 入力フィールドの調整（ここを変更しました） */
    .stTextInput > div > div > input {
        border-radius: 10px;
        padding: 10px;
        font-size: 12px; /* 文字サイズを小さく統一 */
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

# --- 🖼️ 店舗名表示 ---
st.markdown(f"""
<h3 style='
    margin-top: 10px; 
    text-align: center; 
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis;
    font-size: 28px;
    font-weight: 800;
    width: 100%;
    color: #333;
'>
    📍 {selected_store_name}
</h3>
""", unsafe_allow_html=True)


# --- 📝 直行ボタン ---
st.markdown(f"""
<a href="{selected_store_link}" target="_blank" class="direct-link-btn">
    Googleマップで自分で口コミを書く方はこちら 📝
</a>
""", unsafe_allow_html=True)

st.divider()

# --- 🤖 AIにお任せ ---
st.markdown("#### 🤖 AIにお任せする方はこちら")
st.write("簡単な質問に答えるだけで、下書きを作成します。")
st.write("")

# --- 📝 入力フォーム ---
st.markdown('<span class="step-label"><span class="step-number">①</span>担当スタッフ</span>', unsafe_allow_html=True)

csv_store_key = selected_store_name.replace("EIGHT MEN ", "")
current_staff_list = staff_data_dict.get(csv_store_key, [])

if not current_staff_list:
    current_staff_list = staff_data_dict.get(selected_store_name, ["指定しない"])

staff_name = st.selectbox("担当スタッフ", current_staff_list, label_visibility="collapsed")

st.write("")
st.markdown('<span class="step-label"><span class="step-number">②</span>本日のメニュー（複数可）</span>', unsafe_allow_html=True)
menu = st.pills("メニュー", ["メンズカット", "カラー", "ブリーチ", "パーマ", "ストレートパーマ", "縮毛矯正", "眉毛カット", "ヘッドスパ"], selection_mode="multi", label_visibility="collapsed")

st.write("")
# ③ お悩み・動機
st.markdown('<span class="step-label"><span class="step-number">③</span>お悩み・来店動機（複数可）</span>', unsafe_allow_html=True)
motivations = st.pills("きっかけ", MOTIVATION_LIST, selection_mode="multi", label_visibility="collapsed")

# 【条件分岐】「その他」が選択されている場合のみ入力欄を表示
motivation_detail = ""
if motivations and "その他" in motivations:
    motivation_detail = st.text_input(
        "お悩み・動機の詳細（その他）", 
        placeholder="その他：具体的なお悩みや、こうなりたい！という希望など", 
        label_visibility="collapsed"
    )

st.write("")
# ④ 雰囲気
st.markdown('<span class="step-label"><span class="step-number">④</span>店内の雰囲気・接客（感想）</span>', unsafe_allow_html=True)
atmospheres = st.pills("雰囲気", ATMOSPHERE_LIST, selection_mode="multi", label_visibility="collapsed")

# 【条件分岐】「その他」が選択されている場合のみ入力欄を表示
atmosphere_detail = ""
if atmospheres and "その他" in atmospheres:
    atmosphere_detail = st.text_input(
        "雰囲気・接客の詳細（その他）", 
        placeholder="その他：スタッフの対応や店内の様子など", 
        label_visibility="collapsed"
    )

st.write("")
submit_button = st.button("口コミを生成する ✨")

# --- 🤖 生成ロジック ---
if submit_button:
    # 必須チェック（メニューか動機か雰囲気が選ばれていればOK）
    if not menu and not motivations and not atmospheres and not motivation_detail and not atmosphere_detail:
        st.warning("項目をいくつか選択してください")
    else:
        # データ整形
        menu_text = ", ".join(menu) if menu else "カット"
        
        # 動機の処理（選択肢 + 自由記述）
        clean_motivations = [m for m in motivations if m != "その他"] if motivations else []
        motivation_text_parts = clean_motivations.copy()
        if motivation_detail:
            motivation_text_parts.append(motivation_detail)
        motivation_final_text = "、".join(motivation_text_parts) if motivation_text_parts else "特になし"

        # 雰囲気の処理（選択肢 + 自由記述）
        clean_atmospheres = [a for a in atmospheres if a != "その他"] if atmospheres else []
        atmosphere_text_parts = clean_atmospheres.copy()
        if atmosphere_detail:
            atmosphere_text_parts.append(atmosphere_detail)
        atmosphere_final_text = "、".join(atmosphere_text_parts) if atmosphere_text_parts else "良かった"

        system_instruction = f"""
        あなたは「{selected_store_name}」に通う、トレンドに敏感な男性客です。
        入力情報を元に、Googleマップ用の自然な口コミを150文字以内で作成してください。
        【重要ルール】
        1. 「〜に行きました」は禁止。「{area_keyword}」のエリア名を文脈に自然に混ぜる。
        2. 店名を連呼せず「このお店」など自然な指示語を使う。
        3. 「担当：{staff_name}」「メニュー：{menu_text}」を含める。
        4. 来店動機・悩み「{motivation_final_text}」について、どう解決したか（ベネフィット）を書く。
        5. 雰囲気・感想「{atmosphere_final_text}」を反映させる。
        """
        user_content = f"動機・悩み: {motivation_final_text}\n雰囲気・感想: {atmosphere_final_text}"

        try:
            with st.spinner("AIが文章を考えています..."):
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": user_content}],
                    temperature=0.7,
                )
                review_text = response.choices[0].message.content

            st.success("✅ 作成完了！以下のテキストをコピーしてください")
            st.text_area("生成された口コミ", review_text, height=200, label_visibility="collapsed")
            st.markdown(f"""<a href="{selected_store_link}" target="_blank"><button style="width: 100%; background-color: #4285F4; color: white; padding: 14px; border: none; border-radius: 30px; font-weight: bold; margin-top: 10px; font-size: 18px; cursor: pointer;">Googleマップを開いて投稿する 🌍</button></a>""", unsafe_allow_html=True)

        except Exception as e:
            st.error("エラーが発生しました。APIキーを確認してください。")
