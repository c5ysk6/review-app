import streamlit as st
from openai import OpenAI
import pandas as pd

# --- ⚙️ 設定エリア ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRmDV5UTQENMNag-AjCx-FLMx7nTo8egWu7kdt5Df-n13Tst-ctf6Ew48MbcMpsTAs844v0Zbfv3gfS/pub?output=csv"

# 店舗リスト
STORES = {
    "メンズサロン EIGHT MEN 渋谷店": "https://g.page/r/CdXIDXyii4lgEAE/review",
    "メンズサロン EIGHT MEN 池袋西口店": "https://g.page/r/CaV4ekjwYsV1EAE/review",
    "メンズサロン EIGHT MEN 池袋東口店": "https://g.page/r/CdTMjlluc_OFEAE/review",
    "メンズサロン EIGHT MEN 新宿店": "https://g.page/r/CYky-2vp6Y0REAE/review",
    "メンズサロン EIGHT MEN 上野店": "https://g.page/r/CQh9ZNzN-HMPEAE/review",
    "メンズサロン EIGHT MEN 北千住店": "https://g.page/r/CVCsbonX5vKQEAE/review",
    "メンズサロン EIGHT MEN 吉祥寺店": "https://g.page/r/CUFrBrlWrjwaEAE/review",
    "メンズサロン EIGHT MEN 博多店": "https://g.page/r/Cfs_-7LhTWtDEAE/review",
    "メンズサロン EIGHT MEN 那覇新都心店": "https://g.page/r/CU_5fyrZxjvwEAE/review",
}

# エリア名辞書
STORE_AREAS = {
    "メンズサロン EIGHT MEN 渋谷店": "渋谷",
    "メンズサロン EIGHT MEN 池袋西口店": "池袋",
    "メンズサロン EIGHT MEN 池袋東口店": "池袋",
    "メンズサロン EIGHT MEN 新宿店": "新宿",
    "メンズサロン EIGHT MEN 上野店": "上野",
    "メンズサロン EIGHT MEN 北千住店": "北千住",
    "メンズサロン EIGHT MEN 吉祥寺店": "吉祥寺",
    "メンズサロン EIGHT MEN 博多店": "博多",
    "メンズサロン EIGHT MEN 那覇新都心店": "那覇新都心・おもろまち",
}

# リスト定義
MOTIVATION_LIST = [
    "剛毛・広がり・癖を抑えたい", "絶壁・骨格をカバーしたい", "セットを楽に・時短したい",
    "ビジネス・就活で使いたい", "ガラッとイメチェンしたい", "自分に似合う髪型を知りたい", "その他"
]
ATMOSPHERE_LIST = [
    "丁寧なカウンセリング", "会話が楽しく盛り上がった", "静かにリラックスできた",
    "テキパキして早かった", "プロの技術・アドバイス", "店内がお洒落で清潔", "その他"
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
    # URLにない場合は選択させる
    selected_store_name = st.selectbox("ご利用の店舗", list(STORES.keys()))

selected_store_link = STORES[selected_store_name]
area_keyword = STORE_AREAS.get(selected_store_name, "駅近")

# --- 🖼️ 店舗名表示（元に戻しました） ---
# white-space: nowrap で「絶対に改行させない」設定にしています
# スマホで長すぎる場合は少し文字が小さくなるように調整しています
st.markdown(f"""
<h3 style='
    margin-top: 20px; 
    text-align: center; 
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis;
    font-size: 18px;
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
csv_store_key = selected_store_name.replace("メンズサロン ", "")
current_staff_list = staff_data_dict.get(csv_store_key, [])
if not current_staff_list:
    current_staff_list = staff_data_dict.get(selected_store_name, ["指定しない"])
staff_name = st.selectbox("担当スタッフ", current_staff_list, label_visibility="collapsed")

st.write("")
st.markdown('<span class="step-label"><span class="step-number">②</span>本日のメニュー（複数可）</span>', unsafe_allow_html=True)
menu = st.pills("メニュー", ["メンズカット", "フェードカット", "波巻きパーマ", "ツイストスパイラル", "ニュアンスパーマ", "カラー", "ブリーチ", "眉毛カット", "ヘッドスパ"], selection_mode="multi", label_visibility="collapsed")

st.write("")
st.markdown('<span class="step-label"><span class="step-number">③</span>お悩み・来店動機（複数可）</span>', unsafe_allow_html=True)
motivations = st.pills("きっかけ", MOTIVATION_LIST, selection_mode="multi", label_visibility="collapsed")

st.write("")
st.markdown('<span class="step-label"><span class="step-number">④</span>店内の雰囲気・接客（感想）</span>', unsafe_allow_html=True)
atmospheres = st.pills("雰囲気", ATMOSPHERE_LIST, selection_mode="multi", label_visibility="collapsed")

st.write("")
st.markdown('<span class="step-label"><span class="step-number">⑤</span>その他の詳細・一言メモ（任意）</span>', unsafe_allow_html=True)
free_text = st.text_input("その他の詳細", placeholder="例：デート前、自分へのご褒美、近所だったから、など", label_visibility="collapsed")

st.write("")
submit_button = st.button("口コミを生成する ✨")

# --- 🤖 生成ロジック ---
if submit_button:
    if not menu and not motivations and not atmospheres and not free_text:
        st.warning("項目をいくつか選択するか、一言メモを入力してください")
    else:
        menu_text = ", ".join(menu) if menu else "カット"
        clean_motivations = [m for m in motivations if m != "その他"] if motivations else []
        motivation_text = ", ".join(clean_motivations)
        clean_atmospheres = [a for a in atmospheres if a != "その他"] if atmospheres else []
        atmosphere_text = ", ".join(clean_atmospheres) if clean_atmospheres else "良かった"

        system_instruction = f"""
        あなたは「{selected_store_name}」に通う、トレンドに敏感な男性客です。
        入力情報を元に、Googleマップ用の自然な口コミを150文字以内で作成してください。
        【重要ルール】
        1. 「〜に行きました」は禁止。「{area_keyword}」のエリア名を文脈に自然に混ぜる。
        2. 店名を連呼せず「このお店」など自然な指示語を使う。
        3. 「担当：{staff_name}」「メニュー：{menu_text}」を含める。
        4. 動機「{motivation_text}」がどう解決したか書く。
        5. 雰囲気「{atmosphere_text}」を反映。
        6. メモ「{free_text}」があれば最優先する。
        """
        user_content = f"動機: {motivation_text}\n雰囲気: {atmosphere_text}\nメモ: {free_text}"

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
