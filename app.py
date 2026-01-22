import streamlit as st
from openai import OpenAI

# --- 設定エリア ---
SHOP_NAME = "メンズサロン EIGHT MEN 那覇新都心店"
AREA_NAME = "那覇新都心"
GOOGLE_REVIEW_LINK = "https://search.google.com/local/writereview?placeid=YOUR_PLACE_ID" 
# ※後で正式なリンクに書き換えますが、一旦これで動きます

# ページ設定
st.set_page_config(page_title=f"{SHOP_NAME} 口コミ作成", layout="centered")

# CSSでスマホで見やすく調整
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; font-weight: bold; padding: 10px;}
    </style>
    """, unsafe_allow_html=True)

st.title("ご来店ありがとうございます！")
st.write("簡単な質問に答えるだけで、口コミ文を作成します✨")

# --- 入力フォーム ---
with st.form("review_form"):
    menu = st.multiselect(
        "① 本日のメニュー",
        ["メンズカット", "パーマ", "カラー", "ヘッドスパ", "眉毛カット", "ツイストスパイラル", "フェードカット"],
        default=["メンズカット"]
    )

    rating = st.slider("② 満足度", 1, 5, 5)

    points = st.multiselect(
        "③ 気に入ったポイント",
        ["セットが楽になった", "丁寧なカウンセリング", "店の雰囲気が良い", "スタッフが話しやすい", "技術が高い", "また来たい"]
    )
    
    # ★ここにさっきコピーした「sk-...」の鍵を入れます
    api_key = st.text_input("パスワード（APIキー）", type="password")
    
    submit_button = st.form_submit_button("口コミを生成する 🤖")

# --- 生成ロジック ---
if submit_button:
    if not api_key:
        st.error("パスワード（APIキー）を入力してください")
    elif not menu:
        st.error("メニューを選んでください")
    else:
        client = OpenAI(api_key=api_key)
        
        system_prompt = f"""
        あなたは「{SHOP_NAME}」を利用した男性客です。
        以下の条件でGoogleマップ用の口コミを書いてください。
        メニュー: {', '.join(menu)}
        地名: {AREA_NAME}
        満足度: 星{rating}
        ポイント: {', '.join(points)}
        文字数: 150文字程度
        条件: 自然な口語体。絵文字を少し使う。
        """

        with st.spinner("AIが文章を考えています..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": system_prompt}],
                )
                generated_text = response.choices[0].message.content
                
                st.success("生成完了！コピーして投稿してください 👇")
                st.text_area("口コミ内容", generated_text, height=150)
                
                st.link_button("Googleマップを開く 📍", GOOGLE_REVIEW_LINK)
                
            except Exception as e:
                st.error(f"エラー: {e}")
