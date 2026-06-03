"""
口コミ生成ログ ダッシュボード
- Supabase の review_logs テーブルを集計表示
- 接続失敗時は警告のみ表示しアプリは生かす
"""
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="GUEST REVIEW · Dashboard", layout="wide")
st.title("Guest Review Dashboard")
st.caption("review_logs の集計ビュー")


# ====== Supabase クライアント（app.py と同じ実装をローカルに持つ） ======
@st.cache_resource
def _get_supabase_client():
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


@st.cache_data(ttl=60)
def fetch_logs() -> pd.DataFrame:
    """review_logs を最大10000件取得。失敗時は空DF + エラー文字列を返す。"""
    client = _get_supabase_client()
    if client is None:
        return pd.DataFrame(), "Supabase 未設定（SUPABASE_URL / SUPABASE_KEY が必要）"
    try:
        res = client.table("review_logs").select("*").order("created_at", desc=True).limit(10000).execute()
        df = pd.DataFrame(res.data or [])
        if not df.empty and "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert("Asia/Tokyo")
        return df, None
    except Exception as e:
        return pd.DataFrame(), f"取得に失敗しました：{e}"


df, err = fetch_logs()

if err:
    st.warning(f"⚠️ ダッシュボードを表示できません：{err}")
    st.stop()

if df.empty:
    st.info("まだ口コミ生成データがありません。app.py 側で口コミを生成すると、ここに集計されます。")
    st.stop()


# ====== フィルター ======
st.sidebar.header("フィルター")

min_date = df["created_at"].min().date() if "created_at" in df.columns else date.today()
max_date = df["created_at"].max().date() if "created_at" in df.columns else date.today()

date_from = st.sidebar.date_input("開始日", value=min_date, min_value=min_date, max_value=max_date)
date_to = st.sidebar.date_input("終了日", value=max_date, min_value=min_date, max_value=max_date)

store_options = ["全店舗"] + sorted(df["store_name"].dropna().unique().tolist())
selected_store = st.sidebar.selectbox("店舗", store_options)

staff_pool = df["staff_name"].dropna().unique().tolist()
staff_options = ["全スタッフ"] + sorted(staff_pool)
selected_staff = st.sidebar.selectbox("スタッフ", staff_options)


# ====== フィルタ適用 ======
mask = (df["created_at"].dt.date >= date_from) & (df["created_at"].dt.date <= date_to)
if selected_store != "全店舗":
    mask &= df["store_name"] == selected_store
if selected_staff != "全スタッフ":
    mask &= df["staff_name"] == selected_staff

filtered = df[mask].copy()

st.caption(f"対象: {date_from} 〜 {date_to} ／ {selected_store} ／ {selected_staff}　({len(filtered)} 件)")


# ====== サマリーメトリクス ======
c1, c2, c3, c4 = st.columns(4)
c1.metric("総生成数", f"{len(filtered):,}")
c2.metric("対象店舗数", f"{filtered['store_name'].nunique():,}")
c3.metric("対象スタッフ数", f"{filtered['staff_name'].nunique():,}")
copied_count = int(filtered["copied"].sum()) if "copied" in filtered.columns else 0
c4.metric("コピー済み件数", f"{copied_count:,}")

st.divider()


# ====== 件数チャート ======
def _value_counts_chart(col_label: str, series: pd.Series):
    if series.empty:
        st.info(f"{col_label}：データがありません")
        return
    counts = series.value_counts()
    st.subheader(col_label)
    st.bar_chart(counts)


col_a, col_b = st.columns(2)
with col_a:
    _value_counts_chart("店舗別件数", filtered["store_name"].dropna())
with col_b:
    _value_counts_chart("スタッフ別件数", filtered["staff_name"].dropna())

col_c, col_d = st.columns(2)
with col_c:
    _value_counts_chart("メニュー別件数", filtered["menu"].dropna())
with col_d:
    _value_counts_chart("来店理由ランキング", filtered["visit_reason"].dropna())

st.divider()


# ====== 配列カラムの集計（satisfaction_points / review_tone） ======
def _explode_count(col_name: str, label: str):
    if col_name not in filtered.columns:
        st.info(f"{label}：カラムなし")
        return
    exploded = filtered[col_name].dropna().apply(
        lambda v: v if isinstance(v, list) else []
    ).explode().dropna()
    if exploded.empty:
        st.info(f"{label}：データがありません")
        return
    counts = exploded.value_counts().reset_index()
    counts.columns = [label, "件数"]
    st.subheader(label)
    st.dataframe(counts, use_container_width=True, hide_index=True)


col_e, col_f = st.columns(2)
with col_e:
    _explode_count("satisfaction_points", "満足ポイントランキング")
with col_f:
    _explode_count("review_tone", "口コミトーンランキング")

st.divider()


# ====== 最新口コミ一覧 ======
st.subheader("最新口コミ一覧")
latest_cols = ["created_at", "store_name", "staff_name", "menu", "generated_review", "copied"]
available_cols = [c for c in latest_cols if c in filtered.columns]
st.dataframe(
    filtered[available_cols].head(100),
    use_container_width=True,
    hide_index=True,
)
