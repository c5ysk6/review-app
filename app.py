import streamlit as st
from openai import OpenAI

# --- 🏢 店舗データ設定エリア（ここを書き換えてください！） ---
# 形式: "店舗名": "その店のGoogleクチコミリンク"
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
    # ... ここにずらっと並べる
}

# --- ページ設定 ---
st.set_page_config(page_title="口コミ作成", layout="centered")

# CSS: スマホで見やすく調整
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; font-weight: bold; padding: 10px; background-color: #FF4B4B; color: white;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 📍 店舗自動判定ロジック ---
# URLに ?store=店舗名 がついているかチェック
query_params = st.query_params
pre_selected_store = query_params.get("store", None)

# 店舗が決まっている場合
if pre_selected_store and pre_selected_store in STORES:
    selected_store_name = pre_selected_store
    selected_store_link = STORES[pre_selected_store]
    st.title(f"{selected_store_name}へ\nご来店ありがとうございます！")
# 店舗が決まっていない場合（選択させる）
else:
    st.title("ご来店ありがとうございます！")
    selected_store_name = st.selectbox(
        "利用した店舗を選んでください",
        list(STORES.keys())
    )
    selected_store_link = STORES[selected_store_name]

st.write("簡単な質問に答えるだけで、口コミ文を作成します✨")

# --- 入力フォーム ---
with st.form("review_form"):
    menu = st.multiselect(
        "① 本日のメニュー",
        ["メンズカット", "パーマ", "カラー", "ブリーチ", "ストレートパーマ", "縮毛矯正", "眉毛カット", "ヘッドスパ", "トリートメント"],
        default=["メンズカット"]
    )

    rating = st.slider("② 満足度", 1, 5, 5)

    points = st.multiselect(
        "③ 気に入ったポイント",
        ["仕上がりが満足", "丁寧なカウンセリング", "店の雰囲気が良い", "スタッフが話しやすい"]
    )
    
    submit_button = st.form_submit_button("口コミを生成する 🤖")

# --- 生成ロジック ---
if submit_button:
    if not menu:
        st.error("メニューを選んでください")
    else:
        # Secretsから鍵を取り出す
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        system_prompt = f"""
        あなたは「メンズサロン EIGHT MEN {selected_store_name}」を利用した男性客です。
        以下の条件でGoogleマップ用の口コミを書いてください。
        メニュー: {', '.join(menu)}
        店舗名: {selected_store_name}
        満足度: 星{rating}
        ポイント: {', '.join(points)}
        文字数: 100文字程度
        条件: 自然な口語体。絵文字は使わない。
        """

        with st.spinner("AIが文章を考えています..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": system_prompt}],
                )
                generated_text = response.choices[0].message.content
                
                st.success("生成完了！下のボタンを押してGoogleマップに貼り付けてください 👇")
                st.text_area("口コミ内容", generated_text, height=150)
                
                # 店舗ごとのリンクに飛ばす
                st.link_button(f"{selected_store_name}のGoogleマップを開く 📍", selected_store_link)
                
            except Exception as e:
                st.error(f"エラー: {e}")
