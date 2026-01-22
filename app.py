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

# 来店動機リスト
MOTIVATION_LIST = [
    "剛毛・広がり・癖を抑えたい",
    "絶壁・骨格をカバーしたい",
    "セットを楽に・時短したい",
    "ビジネス・就活で使いたい",
    "ガラッとイメチェンしたい",
    "自分に似合う髪型を知りたい",
    "その他"
]

# 雰囲気・接客リスト
ATMOSPHERE_LIST = [
    "丁寧なカウンセリング",
    "会話が楽しく盛り上がった",
    "静かにリラックスできた",
    "テキパキして早かった",
    "プロの技術・アドバイス",
    "店内がお洒落で清潔"
]

# --- 🎨 ページ設定 & デザイン ---
st.set_page_config(page_title="GUEST REVIEW", layout="centered")

st.markdown("""
    <style>
    body { font-family: "Helvetica Neue", Arial, sans-serif; }
    
    /* AI生成ボタン */
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
        margin-top: 10px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(211, 47, 47, 0.5);
    }

    /* 「自分で書く」ボタン */
    .direct-link-btn {
        display: block;
        width: 100%;
        text-align: center;
        padding: 12px;
        margin: 15px 0 10px 0;
        background-color: #f0f2f6;
        color: #555;
        border: 1px solid #ddd;
        border-radius: 10px;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px
