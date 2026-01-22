import streamlit as st
from openai import OpenAI

# --- 設定エリア ---
SHOP_NAME = "メンズサロン EIGHT MEN 那覇新都心店"
AREA_NAME = "那覇新都心"
# ★ここに「自分の店のGoogle口コミ投稿用URL」を貼ります
GOOGLE_REVIEW_LINK = "https://search.google.com/local/writereview?placeid=YOUR_PLACE_ID" 

# ページ設定
st.set_page_config(page_title=f"{SHOP_NAME} 口コミ作成", layout="centered")

# CSS: スマホで見やすく、不要なリンクを隠す
st.markdown("""
    <style>
    .stButton>button {width: 100%; border-radius: 20px; font-weight: bold; padding: 10px; background-color: #FF4B4B; color: white;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
    
    # ★パスワード入力欄を削除しました
    
    submit_button = st.form_submit_button("口コミを生成する 🤖")

# --- 生成ロジック ---
if submit_button:
    if not menu:
        st.error("メニューを選んでください")
    else:
        # Secretsから鍵を勝手に取り出す
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
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
                
                st.success("生成完了！下のボタンを押してGoogleマップに貼り付けてください 👇")
                st.text_area("口コミ内容", generated_text, height=150)
                
                st.link_button("Googleマップを開いて投稿する 📍", GOOGLE_REVIEW_LINK)
                
            except Exception as e:
                st.error(f"エラー: {e}")
