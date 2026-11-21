import base64
import html as html_mod
import random
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI, BadRequestError
import pandas as pd


# ====== Supabase クライアント（任意・失敗時は保存スキップ） ======
@st.cache_resource
def _get_supabase_client():
    """Supabaseクライアントを返す。secrets未設定・パッケージ未インストール時はNone。"""
    try:
        # 前後の空白・改行が混じると接続先ホスト名が壊れDNS解決に失敗するため除去
        url = st.secrets["SUPABASE_URL"].strip()
        key = st.secrets["SUPABASE_KEY"].strip()
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
# スタッフ一覧シート（売上ダッシュボード・日報照合と同じ読み方に統一）
# 旧「ウェブに公開」URLは 2026-11 に 410 で失効し、スタッフが選べなくなった
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1BvzUNUK8XFv18VrZmGok6YFWMwltj5bQQlSNtx67TU0"
    "/export?format=csv&gid=0"
)

# 店舗リスト（EIGHT MEN 〇〇店 に統一）
STORES = {
    "EIGHT MEN 渋谷店": "https://g.page/r/CdXIDXyii4lgEAE/review",
    "EIGHT MEN 池袋西口店": "https://g.page/r/CaV4ekjwYsV1EAE/review",
    "EIGHT MEN 池袋東口店": "https://g.page/r/CdTMjlluc_OFEAE/review",
    "EIGHT MEN 新宿店": "https://g.page/r/CYky-2vp6Y0REAE/review",
    "EIGHT MEN 上野店": "https://g.page/r/CQh9ZNzN-HMPEAE/review",
    "EIGHT MEN 北千住店": "https://g.page/r/CVCsbonX5vKQEAE/review",
    "EIGHT MEN 吉祥寺南口店": "https://g.page/r/CUFrBrlWrjwaEAE/review",
    "EIGHT MEN 博多店": "https://g.page/r/Cfs_-7LhTWtDEAE/review",
    "EIGHT MEN 那覇新都心店": "https://g.page/r/CU_5fyrZxjvwEAE/review",
    "EIGHT MEN 天神大名店": "https://g.page/r/CdPtJJT-D7pIEAE/review",
    "EIGHT MEN 藤沢店": "https://g.page/r/CVIbotoazgOpEBM/review",
    "EIGHT MEN 吉祥寺北口店": "https://g.page/r/Cbj-Wa4U8z8XEBM/review",
}

# 改名した店舗の旧名 → 現在名（配布済みQRの ?store= とスタッフ一覧シートの旧名を読み替える）
RENAMED_STORES = {
    "吉祥寺店": "吉祥寺南口店",
}

# エリア名辞書
STORE_AREAS = {
    "EIGHT MEN 渋谷店": "渋谷",
    "EIGHT MEN 池袋西口店": "池袋",
    "EIGHT MEN 池袋東口店": "池袋",
    "EIGHT MEN 新宿店": "新宿",
    "EIGHT MEN 上野店": "上野",
    "EIGHT MEN 北千住店": "北千住",
    "EIGHT MEN 吉祥寺南口店": "吉祥寺",
    "EIGHT MEN 博多店": "博多",
    "EIGHT MEN 那覇新都心店": "那覇新都心・おもろまち",
    "EIGHT MEN 天神大名店": "天神・大名",
    "EIGHT MEN 藤沢店": "藤沢",
    "EIGHT MEN 吉祥寺北口店": "吉祥寺",
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

# 口コミ生成時のペルソナ pool（年代別・各10人）
AGE_GROUPS = ["10代", "20代", "30代", "40代以上"]

REVIEW_PERSONAS = {
    "10代": [
        {"name": "高校生・初体験", "desc": "高校2〜3年生。友達に連れられて初めてメンズ専門店へ。美容室慣れしていない素直な驚きを丁寧な敬語で書く。短めでシンプル。"},
        {"name": "専門学校生・おしゃれ好き", "desc": "専門学校1〜2年生。ファッション好きでSNSから情報収集。スタイルの変化を素直に喜ぶ。丁寧な口調でやや前向き。"},
        {"name": "アルバイト高校生・コスパ派", "desc": "高校生でバイト代でカット。予算感覚があってコスパに言及する。シンプルで率直な敬語。"},
        {"name": "運動部系高校生", "desc": "部活（サッカー・野球等）に打ち込む高校生。短くさっぱりしたい実用志向。短文で率直な敬語。"},
        {"name": "大学入学前・イメチェン", "desc": "18歳、進学を機にイメチェン。初めてちゃんとした美容室に感動している。素直で前向きな敬語。"},
        {"name": "インドア・ゲーム系10代", "desc": "普段あまり美容室に行かない17歳。たまたま来店。率直でやや淡白だが丁寧な敬語。"},
        {"name": "バンド系・個性派10代", "desc": "バンドをやっている19歳。個性的なスタイルを求める。少し独特なトーンだが敬語で書く。"},
        {"name": "就活準備中の専門学生", "desc": "19歳、就職活動を前に清潔感を意識し始めた。真剣で丁寧な敬語。清潔感への言及が多い。"},
        {"name": "SNS意識高め系10代", "desc": "Instagramを意識する18歳。見た目の変化を重視。テンションは少し高めだが敬語で統一。"},
        {"name": "スポーツ実用派10代", "desc": "運動系で実用重視の16〜17歳。「さっぱりした」「動きやすい」観点。超シンプルな敬語。"},
    ],
    "20代": [
        {"name": "ITエンジニア20代後半", "desc": "20代後半のITエンジニア。仕事帰りに通っている。テンションは控えめで要点を絞った丁寧な敬語。"},
        {"name": "大学生20代前半", "desc": "20代前半の大学生。率直で素直な感想を丁寧な敬語で書く。難しい言葉は使わない。"},
        {"name": "営業職20代前半", "desc": "20代前半の営業職。スーツ仕事で清潔感重視。具体的な体験を丁寧な敬語で書く。"},
        {"name": "フリーランス20代後半", "desc": "20代後半のフリーランス。時間効率を重視。「早い」「楽」「セットしやすい」観点を敬語で書く。"},
        {"name": "接客業20代後半", "desc": "20代後半の接客業（飲食・販売）。接客の質に敏感で、スタッフの対応の細部に触れる。丁寧な敬語。"},
        {"name": "クリエイター20代後半", "desc": "20代後半のデザイナー。お洒落な雰囲気を求める。雰囲気や仕上がりの描写が多め。落ち着いた敬語。"},
        {"name": "婚活中20代後半", "desc": "20代後半、第一印象重視。「印象がよくなった」「清潔感が出た」観点を前向きな敬語で書く。"},
        {"name": "地方出身・上京したて20代", "desc": "20代前半、地方から上京して間もない。シンプルで素直な敬語。地元との比較が出ることも。"},
        {"name": "音楽芸術系20代", "desc": "20代の音楽・芸術系。個性派の髪型を求める。自分のスタイルへのこだわりを敬語で書く。"},
        {"name": "体育会系20代後半", "desc": "20代後半の体育会系。短くて清潔感重視。「さっぱり」「すっきり」が中心の簡潔な敬語。"},
    ],
    "30代": [
        {"name": "中堅会社員30代前半", "desc": "30代前半の中堅会社員。落ち着いた丁寧な敬語。仕事や日常生活との結びつきで語る。"},
        {"name": "管理職30代後半", "desc": "30代後半の管理職。清潔感・信頼感を重視。落ち着いた品のある敬語。部下や取引先への印象を意識。"},
        {"name": "既婚・子持ち30代", "desc": "30代の既婚男性。「妻に褒められた」「家族から好評」観点も含む。温かみのある丁寧な敬語。"},
        {"name": "転職活動中30代", "desc": "30代前半の転職活動中。面接での第一印象を意識。真剣で具体的な敬語。"},
        {"name": "起業家・経営者30代", "desc": "30代の起業家。効率とクオリティを両立重視。簡潔で無駄のない成果ベースの敬語。"},
        {"name": "デザイナー・クリエイター30代後半", "desc": "30代後半のデザイナー。こだわりが強く仕上がりの細部に言及する。落ち着いたおしゃれな敬語。"},
        {"name": "ベテラン営業職30代", "desc": "30代後半のベテラン営業。目が肥えていて接客品質の評価が具体的。信頼の積み重ねを語る敬語。"},
        {"name": "士業・医療系30代", "desc": "30代の医師・弁護士等。清潔感・信頼性を最重視。落ち着いた品格ある短めの敬語。"},
        {"name": "地方サラリーマン30代", "desc": "30代の地方出身サラリーマン。素朴でまっすぐな敬語。シンプルで誇張少なめ。"},
        {"name": "ITリーダー30代", "desc": "30代のITエンジニア（チームリーダー）。論理的で簡潔。効率・品質・コスパで評価する敬語。"},
    ],
    "40代以上": [
        {"name": "経営者・役員40代", "desc": "40代の経営者。品格と信頼を重視。落ち着いた品のある敬語。サービスの一貫性・プロ意識を評価する。"},
        {"name": "ベテランサラリーマン40代後半", "desc": "40代後半の会社員。長年の経験から安定感・信頼感を重視した落ち着いた敬語で評価する。"},
        {"name": "自営業・個人事業主40代", "desc": "40代の自営業。定期的なメンテナンスとして通う視点。コスパと安定性を重視する実直な敬語。"},
        {"name": "士業・専門職40代", "desc": "40代の医師・弁護士・会計士等。清潔感・信頼性を最重視。品格ある落ち着いた敬語で観察眼鋭く書く。"},
        {"name": "アウトドア・趣味充実40代", "desc": "40代のアウトドア好き。さっぱりした清潔感を好む。明るく率直な敬語。"},
        {"name": "単身赴任中40代", "desc": "40代の単身赴任中。新しい土地で信頼できる美容室を探していた視点。落ち着いた安心感を語る敬語。"},
        {"name": "子育て一段落した父40代後半", "desc": "40代後半、子供が独立し自分のケアを再開した父親。久しぶりに自分のために来た喜びと感謝を丁寧な敬語で書く。"},
        {"name": "再婚・婚活中40代", "desc": "40代の婚活・再婚活動中。見た目のリフレッシュを意識。第一印象・清潔感重視の前向きな敬語。"},
        {"name": "クリエイター・アーティスト40代", "desc": "40代のクリエイター。個性を大切にしつつ清潔感も重視。スタイルへのこだわりと自由な感性を持ちながら敬語で書く。"},
        {"name": "健康・美容意識高め40代以上", "desc": "40代以上の健康・美容に気を使う男性。頭皮ケアや髪のコンディションにも関心がある。丁寧な自己管理の文脈で語る敬語。"},
    ],
}

# --- 口コミの多様性を生む軸 ---
# 全例をまとめて見せると文章の骨格が1つの型に収束するため、
# 生成のたびに数例だけをランダム抽出して提示する
REVIEW_EXAMPLES = [
    "伸びてきたのでカットしてもらいました。渡辺さんの提案が的確で、クセ毛のまとめ方も教えてもらえて助かりました。北千住にこういうメンズ向けのお店があるとは知りませんでした。",
    "田中さんに担当してもらっています。毎回カウンセリングで細かく聞いてくれるので、希望通りに仕上がります。池袋の職場から近いので、これからもこちらを利用したいと思っています。",
    "パーマが初めてだったのですが、佐藤さんがイメージ写真を一緒に見ながら相談に乗ってくれました。仕上がりがセットしやすくて、朝の準備が楽になりました。",
    "仕事帰りによく利用しています。カットと眉毛をまとめてお願いでき、手際よく対応していただけます。清潔感を大事にしたいメンズにはちょうどいいと思います。",
    "初めて来店しましたが、山田さんが自然に話しかけてくださって緊張せずに過ごせました。縮毛矯正が思ったより自然な仕上がりで驚きました。また利用したいと思います。",
    "博多の職場からの帰り道に寄れるのが便利です。川口さんのカット技術が毎回安定していて、メンズカット専門の安心感があります。価格も良心的で助かっています。",
    "友人に勧められて来てみました。入った瞬間から対応が丁寧で、ヘッドスパは本当に気持ちよくてウトウトしてしまいました。またぜひ伺いたいと思います。",
    "イメチェンしたくてブリーチとカラーをお願いしました。仕上がりが思っていた以上で、職場でも褒めていただきました。上野でこのクオリティのメンズサロンはなかなかないと思います。",
    "クセが強くて毎回どうにもならなかったのですが、乾かし方まで教えていただけて助かりました。メンズカット専門というだけあって、話が早いです。",
    "打ち合わせの前に寄らせてもらっています。短時間でもきちんと整えていただけるので、予定の合間に使いやすいです。",
    "セットが本当に楽になりました。伸ばしかけで中途半端だった部分を、鈴木さんがうまく馴染ませてくださったおかげだと思います。",
    "白髪が気になり始めて相談したところ、自然に見える範囲で提案していただきました。家族に言われるまで気づかれなかったので、ちょうどよかったです。",
    "眉毛までお願いできるのを知らずに来たのですが、思った以上に印象が変わりました。次はヘッドスパも試してみようと思います。",
    "無理に話しかけられることもなく、こちらのペースで過ごせました。メンズ専門ということもあってか、店内も落ち着いた雰囲気です。",
]

# 文章の骨格（毎回1つを指定して型の収束を防ぐ）
REVIEW_STRUCTURES = [
    "来店のきっかけから書き始め、施術中のやりとりに触れ、仕上がりの感想で終える",
    "仕上がりの感想から書き始め、なぜそうなったのか（提案・技術）を後から説明する",
    "普段の生活の文脈（仕事帰り・移動の途中・休日など）から入り、店の使い勝手に触れてから仕上がりに移る",
    "髪の悩みの話から入り、それをどう相談してどう解決したかを書く",
    "店内で過ごした時間の体験（会話の距離感・空気感・施術中の心地よさ）を中心に書く",
    "担当者の対応で印象に残った場面をひとつだけ具体的に掘り下げ、他は詳しく書かない",
    "施術後の日常の変化（朝が楽・周囲の反応・清潔感）を軸に書く",
]

# 締め方（「また利用したいと思います」への偏りを防ぐ）
REVIEW_CLOSINGS = [
    "また来たい気持ちを、定型句を避けた自分の言葉で書いて終える",
    "締めの言葉をあえて作らず、仕上がりや体験の話で言い切って終える",
    "施術後の日常の変化や周囲の反応に触れて終える",
    "店やエリアの使いやすさ・通いやすさに触れて終える",
    "次に頼んでみたいメニューや今後の希望に触れて終える",
    "担当者やお店への感謝を、かしこまりすぎない言い方で書いて終える",
]

# --- 「毎回変えて」「場合によっては」はモデルには実行できない ---
# 生成は1回ごとに独立しており、モデルは前回の出力を知らない。
# プロンプトで揺らぎを頼むと毎回いちばん無難な選択に収束するため、
# 揺らぎはすべてここでコード側の乱数として決め、プロンプトには確定した指示として渡す。

# 来店回数の扱い（言い回し例を見せると丸写しされるため、方針だけを渡す）
VISIT_MODES_FIRST = [
    "初めての来店だったことに、文の途中でさりげなく触れる",
    "初めての来店だったことを、来店前の不安や期待と絡めて書く",
    "初めての来店かどうかには触れない",
]
VISIT_MODES_REPEAT = [
    "通い続けていることを、回数の数字を使わずに自分の言葉で匂わせる",
    "前回までと比べて今回どうだったか、という視点を一言入れる（回数の数字は出さない）",
    "来店回数・継続利用には一切触れない",
]

# 「メンズ」を置く位置（毎回文末に付け足すパターンへの収束を防ぐ）
MENS_PLACEMENTS = [
    "メニュー名として（例：メンズカット）",
    "お店の種類として（例：メンズ専門・メンズサロン）",
    "書き出しの1文目のどこか",
    "最後の1文のどこか",
]

# 文末の語尾（「〜ました。〜と思います。」の連続を防ぐ）
ENDING_STYLES = [
    "「〜ました」で終わる文を続けすぎず、「〜です」「〜ています」も混ぜる",
    "「〜と思います」は使わない",
    "1文だけ「〜でした！」のように少し感情が出る語尾を使う（敬語は保つ）",
    "淡々とした語尾で、感想を盛りすぎない",
]

# 文量（短文〜やや詳しめまで振る）
REVIEW_LENGTHS = [
    "2文程度で、60〜90文字に収める。短くても物足りなくならないよう具体を1つに絞る",
    "3文程度で、90〜120文字に収める",
    "3〜4文で、120〜150文字に収める",
]

# 良かった点アイコン（インラインSVG・線画）
_ATM_SVG = {
    "接客・対応": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a2530" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>',
    "技術・仕上がり": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a2530" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.12 15.88"/><path d="M14.47 14.48 20 20"/><path d="M8.12 8.12 12 12"/></svg>',
    "カウンセリング": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a2530" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "店内の雰囲気": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a2530" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 9V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v2"/><path d="M2 11v5a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5a2 2 0 0 0-4 0v2H6v-2a2 2 0 0 0-4 0Z"/><path d="M4 18v2"/><path d="M20 18v2"/></svg>',
    "価格の満足度": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a2530" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9 8l3 4 3-4M9 13h6M9 16h6M12 12v6"/></svg>',
    "その他": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a2530" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="8" cy="12" r="1" fill="#1a2530"/><circle cx="12" cy="12" r="1" fill="#1a2530"/><circle cx="16" cy="12" r="1" fill="#1a2530"/></svg>',
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
    /* ─────────────────────────────────────────────
       薄いグレーの地に白いパネル。差し色はティール1色（スタイル自動投稿と同じ配色）。
       色は --accent と --bg を動かせば全体が連動する
       ───────────────────────────────────────────── */
    :root {
        --accent:      #1d96b4;
        --bg:          #f4f5f7;
        --surface:     #ffffff;
        --ink:         #1a2530;
        --line:        #e7e9ec;
        --radius:      10px;
        --accent-soft: color-mix(in srgb, var(--accent) 9%,  #fff);
        --accent-line: color-mix(in srgb, var(--accent) 35%, #fff);
        --accent-dark: color-mix(in srgb, var(--accent) 82%, #000);
        --line-2:      color-mix(in srgb, var(--ink) 16%, #fff);
        --ink-2:       color-mix(in srgb, var(--ink) 62%, #fff);
        --ink-3:       color-mix(in srgb, var(--ink) 40%, #fff);
        --shadow: 0 1px 2px rgba(16,37,48,.04), 0 6px 20px rgba(16,37,48,.05);
    }

    /* お客様向け画面にページナビ・標準ヘッダーは出さない */
    [data-testid="stSidebarNav"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic Medium", "Noto Sans JP", sans-serif;
        color: var(--ink);
        -webkit-font-smoothing: antialiased;
    }
    .stApp { background-color: var(--bg); }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 560px;
    }

    /* ====== 店舗ヘッダー：淡いティールの面で、重くせずに目立たせる ====== */
    .store-head {
        background: var(--accent-soft);
        border: 1px solid var(--accent-line);
        border-left: 4px solid var(--accent);
        border-radius: var(--radius);
        padding: 18px 20px;
        text-align: left;
    }
    .store-brand {
        font-size: 11.5px;
        font-weight: 700;
        letter-spacing: .16em;
        color: var(--accent);
        margin-bottom: 2px;
    }
    .store-name {
        margin: 0 !important;
        padding: 0 !important;
        font-size: clamp(26px, 8vw, 32px) !important;
        font-weight: 800 !important;
        line-height: 1.25 !important;
        letter-spacing: .02em !important;
        word-break: keep-all;
        overflow-wrap: anywhere;
        color: var(--ink) !important;
    }

    /* ====== ボタン ====== */
    /* 生成ボタン：ティール塗り・全幅 */
    div[data-testid="stElementContainer"]:has(.stButton),
    .stButton {
        width: 100% !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: var(--radius);
        font-weight: 700;
        padding: 16px;
        background: var(--accent);
        color: #fff;
        border: none;
        box-shadow: none;
        font-size: 15px;
        letter-spacing: .04em;
        margin-top: 20px;
        transition: background .15s;
    }
    .stButton>button:hover { background: var(--accent-dark); color: #fff; }
    .stButton>button:focus:not(:active) { color: #fff; }

    /* 直行ボタン：白パネル×細枠 */
    .direct-link-btn {
        display: block;
        width: 100%;
        text-align: center;
        padding: 14px;
        margin: 14px 0 4px 0;
        background: var(--surface);
        color: var(--ink) !important;
        border: 1px solid var(--line-2);
        border-radius: var(--radius);
        text-decoration: none !important;
        font-weight: 600;
        font-size: 14px;
        transition: border-color .15s, color .15s;
    }
    .direct-link-btn:hover {
        border-color: var(--accent);
        color: var(--accent) !important;
    }

    /* ====== セクション見出し ====== */
    h4 {
        color: var(--ink) !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        letter-spacing: .02em !important;
        margin-top: 4px !important;
    }
    p.lead {
        color: var(--ink-2);
        font-size: 13px !important;
        margin-top: -6px;
    }
    .step-label {
        color: var(--ink);
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 26px;
        height: 22px;
        padding: 0 6px;
        border-radius: 6px;
        background: var(--accent-soft);
        color: var(--accent);
        font-weight: 700;
        font-size: 11.5px;
        font-variant-numeric: tabular-nums;
        margin-right: 10px;
        line-height: 1;
    }

    /* ====== 入力 ====== */
    .stTextInput > div > div > input {
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        background-color: var(--surface);
        color: var(--ink);
    }
    .stTextInput > div > div:focus-within {
        border-color: var(--accent) !important;
    }
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid var(--line-2);
        background-color: var(--surface);
    }
    .stSelectbox > div > div:hover { border-color: var(--accent); }

    /* Pills */
    div[data-baseweb="button-group"] button {
        border-radius: 999px !important;
        font-weight: 500 !important;
    }
    div[data-baseweb="button-group"] button[aria-pressed="false"] {
        background-color: var(--surface) !important;
        border: 1px solid var(--line-2) !important;
        color: var(--ink) !important;
    }
    div[data-baseweb="button-group"] button[aria-pressed="false"]:hover {
        border-color: var(--accent) !important;
        color: var(--accent) !important;
    }
    div[data-baseweb="button-group"] button[aria-pressed="true"] {
        background-color: var(--accent-soft) !important;
        border: 1px solid var(--accent) !important;
        color: var(--accent) !important;
        font-weight: 700 !important;
    }

    hr {
        border: none !important;
        height: 1px !important;
        background: var(--line) !important;
        margin: 1.75rem 0 !important;
    }

    div[data-testid="stAlert"] { border-radius: var(--radius); }

    /* ====== 良かった点：1列カード・詳細はカード内に展開 ====== */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid var(--line) !important;
        border-radius: var(--radius) !important;
        background: var(--surface) !important;
        padding: 0 !important;
        margin-bottom: 0 !important;
        transition: border-color .15s;
        cursor: pointer !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div,
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] {
        width: 100% !important;
        margin: 0 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: var(--accent-line) !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        min-height: 54px !important;
        padding: 10px 14px !important;
        margin: 0 !important;
        cursor: pointer !important;
        box-sizing: border-box !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCheckbox"] img {
        width: 18px !important;
        height: 18px !important;
        vertical-align: middle !important;
        margin-right: 4px !important;
        display: inline-block !important;
    }
    .st-key-atm_list { gap: 8px !important; }
    /* カード（新しいStreamlitではkey付きコンテナ自身が枠になる）の余白を0にし、
       チェックボックスのラベルを枠の幅いっぱいまで広げる＝枠内のどこを押しても反応する */
    .st-key-atm_list [class*="st-key-atm_card_"] {
        gap: 0 !important;
        padding: 0 !important;
        background: var(--surface) !important;
        border: 1px solid var(--line) !important;
        border-radius: var(--radius) !important;
        transition: border-color .15s;
    }
    .st-key-atm_list [class*="st-key-atm_card_"]:hover { border-color: var(--accent-line) !important; }
    .st-key-atm_list [class*="st-key-atm_card_"] > [data-testid="stElementContainer"]:has([data-testid="stCheckbox"]),
    .st-key-atm_list [class*="st-key-atm_card_"] [data-testid="stCheckbox"] {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
    }
    .st-key-atm_list [class*="st-key-atm_card_"] [data-testid="stCheckbox"] label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        min-height: 56px !important;
        padding: 14px 16px !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        cursor: pointer !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    .st-key-atm_list [class*="st-key-atm_card_"] [data-testid="stCheckbox"] img {
        width: 18px !important;
        height: 18px !important;
        vertical-align: middle !important;
        margin-right: 4px !important;
    }
    .st-key-atm_list [class*="st-key-atm_card_"]:has(input[type="checkbox"]:checked),
    .st-key-atm_list [data-testid="stVerticalBlockBorderWrapper"]:has(input[type="checkbox"]:checked) {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) inset;
    }
    .sub-category-label {
        font-size: 11.5px;
        font-weight: 600;
        color: var(--ink-3);
        margin: 0 0 8px 0;
    }
    .st-key-atm_list [class*="st-key-atm_subs_"] {
        border-top: 1px solid var(--line) !important;
        margin: 0 16px !important;
        padding: 12px 0 14px 0 !important;
        width: auto !important;
        background: transparent !important;
    }
    .st-key-atm_list [class*="st-key-atm_subs_"] div[data-baseweb="button-group"] {
        display: flex !important;
        flex-direction: row !important;
        justify-content: flex-start !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        width: 100% !important;
    }
    .st-key-atm_list [class*="st-key-atm_subs_"] div[data-baseweb="button-group"] button {
        padding: 6px 14px !important;
        font-size: 12.5px !important;
        min-height: 32px !important;
        flex: 0 0 auto !important;
        width: auto !important;
        max-width: max-content !important;
    }

    /* ====== メニュー等のスマホ2列折り返し ====== */
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

    /* ====== 投稿ボタン（生成後） ====== */
    .post-btn {
        display: block;
        width: 100%;
        text-align: center;
        padding: 16px;
        margin-top: 12px;
        background: var(--ink);
        color: #fff !important;
        border-radius: var(--radius);
        text-decoration: none !important;
        font-weight: 700;
        font-size: 15px;
    }
    .post-btn:hover { background: #0f1b23; }

    /* ====== フッター ====== */
    .footer-mark {
        margin-top: 40px;
        padding-top: 18px;
        border-top: 1px solid var(--line);
        text-align: center;
        font-size: 11.5px;
        color: var(--ink-3);
    }
    </style>
    """, unsafe_allow_html=True)


# --- 📥 データ読み込み ---
@st.cache_data(ttl=600)
def load_staff_data():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.groupby('店舗名')['スタッフ名'].apply(list).to_dict()
    except Exception as e:
        # 失敗するとスタッフ選択が「指定しない」だけになる。原因を追えるようサーバーログに残す
        print(f"[staff] スタッフ一覧の読み込み失敗: {e}")
        return {}

staff_data_dict = load_staff_data()

# --- 📍 店舗選択 ---
query_params = st.query_params
url_store_param = query_params.get("store")
found_store_name = None

if url_store_param:
    url_store_param = RENAMED_STORES.get(url_store_param, url_store_param)
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

# --- 店舗ヘッダー ---
# 「EIGHT MEN」は小見出しに分け、大きく出すのは店舗名だけ（長い店名でも省略されないように）
store_short_name = selected_store_name.replace("EIGHT MEN ", "")
st.markdown(f"""
<div class="store-head">
    <div class="store-brand">EIGHT MEN</div>
    <h3 class="store-name">{store_short_name}</h3>
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
st.markdown("<p class='lead'>質問に答えるだけで、口コミの下書きを作成します。</p>", unsafe_allow_html=True)


# --- 📝 入力フォーム ---
st.markdown('<span class="step-label"><span class="step-number">01</span>担当スタッフ</span>', unsafe_allow_html=True)

csv_store_key = selected_store_name.replace("EIGHT MEN ", "")
current_staff_list = staff_data_dict.get(csv_store_key, [])
if not current_staff_list:
    old_names = [old for old, new in RENAMED_STORES.items() if new == csv_store_key]
    current_staff_list = staff_data_dict.get(old_names[0], []) if old_names else []

if not current_staff_list:
    current_staff_list = staff_data_dict.get(selected_store_name, [])

# 「指定しない」はシートに依存せず常に先頭に置く
current_staff_list = ["指定しない"] + [s for s in current_staff_list if isinstance(s, str) and s.strip() and s != "指定しない"]

staff_name = st.selectbox("担当スタッフ", current_staff_list, label_visibility="collapsed")

st.write("")
st.markdown('<span class="step-label"><span class="step-number">02</span>お客様の年代</span>', unsafe_allow_html=True)

age_group = st.pills(
    "年代",
    AGE_GROUPS,
    selection_mode="single",
    default="20代",
    label_visibility="collapsed"
)

st.write("")
st.markdown('<span class="step-label"><span class="step-number">03</span>来店回数</span>', unsafe_allow_html=True)

visit_count = st.pills(
    "来店回数",
    VISIT_LIST,
    selection_mode="single",
    default="初回",
    label_visibility="collapsed"
)

st.write("")
st.markdown('<span class="step-label"><span class="step-number">04</span>ご利用いただいたサービス（複数可）</span>', unsafe_allow_html=True)

menu_cols = st.columns(2)
menu = []
for i, item in enumerate(MENU_LIST):
    with menu_cols[i % 2]:
        if st.checkbox(item, value=(i == 0), key=f"menu_{item}"):
            menu.append(item)

st.write("")
st.markdown('<span class="step-label"><span class="step-number">05</span>お悩み・来店動機（複数可）</span>', unsafe_allow_html=True)

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
st.markdown('<span class="step-label"><span class="step-number">06</span>良かった点（複数可）</span>', unsafe_allow_html=True)

atmospheres = []
atmosphere_subdetails = {}
atmosphere_detail = ""
# 詳細はチェックしたカードの「中」に展開する（カード外に出すとどのカードの詳細か分からなくなる）
with st.container(key="atm_list"):
    for idx, item in enumerate(ATMOSPHERE_LIST):
        with st.container(border=True, key=f"atm_card_{idx}"):
            checked = st.checkbox(f"{ATMOSPHERE_ICONS[item]} {item}", key=f"atm_{item}")
            if checked:
                atmospheres.append(item)
                if ATMOSPHERE_SUBOPTIONS.get(item):
                    with st.container(key=f"atm_subs_{idx}"):
                        st.markdown('<div class="sub-category-label">当てはまるものをタップ（任意）</div>', unsafe_allow_html=True)
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
                elif item == "その他":
                    with st.container(key=f"atm_subs_{idx}"):
                        atmosphere_detail = st.text_input(
                            "雰囲気・接客の詳細（その他）",
                            placeholder="スタッフの対応や店内の様子など",
                            label_visibility="collapsed",
                        )

st.write("")
submit_button = st.button("口コミを生成する")

# --- 🤖 生成ロジック ---
if submit_button:
    if not menu and not motivations and not atmospheres and not motivation_detail and not atmosphere_detail:
        st.warning("項目をいくつか選択してください")
    else:
        # スタッフ名を苗字だけにする処理
        staff_specified = staff_name != "指定しない"
        staff_last_name = staff_name.replace("　", " ").split(" ")[0] if staff_specified else ""
        staff_display = f"{staff_last_name}さん" if staff_specified else f"{selected_store_name}（担当者名の指定なし）"

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

        # 💡 プロンプト：few-shot実例でAIっぽさを排除
        selected_age = age_group if age_group else "20代"
        persona = random.choice(REVIEW_PERSONAS[selected_age])

        # 毎回同じ型に収束しないよう、参考例・骨格・締め方・文量をランダムに振る
        sampled_examples = random.sample(REVIEW_EXAMPLES, 3)
        example_block = "\n\n".join(
            f"例{i}）\n{ex}" for i, ex in enumerate(sampled_examples, 1)
        )
        structure = random.choice(REVIEW_STRUCTURES)
        closing = random.choice(REVIEW_CLOSINGS)
        visit_mode = random.choice(VISIT_MODES_FIRST if visit_count == "初回" else VISIT_MODES_REPEAT)
        mens_placement = random.choice(MENS_PLACEMENTS)
        ending_style = random.choice(ENDING_STYLES)
        area_rule = (
            f"エリア名「{area_keyword}」を、生活圏・行動パターンに溶け込ませて1回入れる（「{area_keyword}のこのお店」のような言い方は避ける）"
            if random.random() < 0.5
            else "エリア名・地名は入れない"
        )

        staff_rule = (
            f"・担当者名「{staff_last_name}さん」を必ず1回以上、自然な形で書く"
            if staff_specified
            else ""
        )

        # 入力が同じ客同士で中身まで揃わないよう、主役にする要素をコード側で1つ決める
        focus_candidates = motivation_text_parts + atmosphere_text_parts + (menu or [])
        focus = random.choice(focus_candidates) if focus_candidates else menu_text

        # 選択項目が多いときに短文枠を引くと拾いきれないため、情報量に応じて文量枠を絞る
        # （REVIEW_LENGTHS は短い順に並んでいる前提）
        detail_count = (
            len(motivation_text_parts)
            + sum(len(atmosphere_subdetails.get(atm, [])) or 1 for atm in clean_atmospheres)
            + (1 if atmosphere_detail else 0)
        )
        if detail_count <= 2:
            length_spec = random.choice(REVIEW_LENGTHS)
        elif detail_count <= 4:
            length_spec = random.choice(REVIEW_LENGTHS[1:])
        else:
            length_spec = REVIEW_LENGTHS[-1]

        coverage_rule = (
            "・「良かった点」に挙がっている要素はできるだけ拾う。ただし箇条書きの羅列にせず、ひと続きの体験としてつなげる"
            if detail_count >= 3
            else "・「良かった点」の要素は無理に全部入れず、1つを選んで具体的に掘り下げる"
        )

        system_instruction = f"""
あなたは「{selected_store_name}」に通う男性客です。
ペルソナ：{persona["desc"]}

以下の入力情報をもとに、Googleマップ用の口コミを書いてください。

【入力情報】
担当：{staff_display}／メニュー：{menu_text}／来店：{visit_count}／年代：{selected_age}
悩み・動機：{motivation_final_text}
良かった点：{atmosphere_final_text}
エリア：{area_keyword}

---
【今回の書き方の指定 ― 必ずこの通りにする】
・文章の骨格：{structure}
・いちばん厚く書く要素：{focus}
・締め方：{closing}
・来店回数：{visit_mode}
・エリア：{area_rule}
・「メンズ」の位置：{mens_placement}
・語尾：{ending_style}
・文量：{length_spec}（上限150文字は絶対に超えない）

---
【文体の参考 ― 文体と自然さだけを参考にする。構成は上の指定に従い、丸写しはしない】

{example_block}

---
【守ること】
・文体は必ず敬語（です・ます調）で統一する。タメ口・体言止めは使わない
・上の実例のように、説明くさくなく、スマホで打ったような自然な敬語で書く
・書き出しの一文は、参考例と同じ入り方をしない。骨格の指定に沿って自分で入口を決める
・「メンズ」という言葉を、上で指定した位置に自然な形で必ず1回含める
{staff_rule}
・「正解だった」「至福の」「プロフェッショナルな」「強くお勧め」「いつもお世話になっています」は使わない
・「丁寧に対応していただきました」「大変満足しています」のような、どの店にも当てはまる無難な一文で埋めない。入力情報にある具体を必ず1つ以上、体験として書く
{coverage_rule}
・入力情報の項目名をそのまま「〜を希望し」「〜という動機で」のような申請書・ビジネス文書的な言い方に変換しない。「イメチェンしたくて」「思い切ってイメチェンしようと」のように、話し言葉に近い自然な理由の書き方に言い換える
・担当が「（担当者名の指定なし）」の場合、「スタッフさんにお願いしました」のように人名扱いで書かない。個人名を使わず「{selected_store_name}にお願いしました」「{selected_store_name}で仕上げてもらいました」のように店名を主語にして自然に書く
・来店回数に触れる場合も、「2回目です」「3回目になります」のように回数の数字は出さない
"""
        user_content = f"担当：{staff_display}、メニュー：{menu_text}、来店：{visit_count}、悩み：{motivation_final_text}、良かった点：{atmosphere_final_text}"

        try:
            with st.spinner("AIが文章を考えています..."):
                client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
                messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_content}]
                # gpt-4o-mini は 2027-01-14 にAPI停止。後継の gpt-6-luna へ移行。
                # 新世代モデルはサンプリング系パラメータを受け付けない場合があるため、
                # 400系で弾かれたらパラメータなしで再試行する（揺らぎはコード側の乱数で担保済み）
                try:
                    response = client.chat.completions.create(
                        model="gpt-6-luna",
                        messages=messages,
                        temperature=0.95,
                        presence_penalty=0.4,
                        frequency_penalty=0.3,
                    )
                except BadRequestError:
                    response = client.chat.completions.create(model="gpt-6-luna", messages=messages)
                review_text = response.choices[0].message.content

            escaped_review = html_mod.escape(review_text)
            approx_lines = max(4, len(review_text) // 38 + 1)
            component_height = approx_lines * 28 + 180
            components.html(f"""
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic Medium", "Noto Sans JP", sans-serif;
    background: transparent;
    color: #1a2530;
    -webkit-font-smoothing: antialiased;
  }}
  .review-card {{
    background: #ffffff;
    border: 1px solid #e7e9ec;
    border-radius: 10px;
    padding: 18px;
    box-shadow: 0 1px 2px rgba(16,37,48,.04), 0 6px 20px rgba(16,37,48,.05);
  }}
  .review-label {{
    font-size: 12px;
    font-weight: 700;
    color: #1d96b4;
    margin-bottom: 8px;
  }}
  .review-text {{
    font-size: 14px;
    line-height: 1.85;
    color: #1a2530;
    white-space: pre-wrap;
    margin-bottom: 20px;
  }}
  .copy-btn {{
    width: 100%;
    padding: 16px;
    background: #1d96b4;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    font-family: inherit;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: .04em;
    cursor: pointer;
    transition: background .15s;
  }}
  .copy-btn:hover {{ background: #18809a; }}
  .copy-btn.copied {{ background: #15803d; }}
</style>
<div class="review-card">
  <div class="review-label">生成された口コミ</div>
  <div class="review-text" id="review-text">{escaped_review}</div>
  <button class="copy-btn" id="copy-btn" onclick="copyReview()">口コミをコピーする</button>
</div>
<script>
  function copyReview() {{
    const text = document.getElementById('review-text').innerText;
    const btn = document.getElementById('copy-btn');
    navigator.clipboard.writeText(text).then(() => {{
      btn.textContent = 'コピーしました';
      btn.classList.add('copied');
      setTimeout(() => {{
        btn.textContent = '口コミをコピーする';
        btn.classList.remove('copied');
      }}, 3000);
    }});
  }}
</script>
""", height=component_height)

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
                # 保存ログは社内用。お客様の画面に内部エラーを出さず、サーバーログにだけ残す
                print(f"[review_logs] 保存失敗: {err}")

            st.markdown(f"""<a href="{selected_store_link}" target="_blank" class="post-btn">Googleマップを開いて投稿する</a>""", unsafe_allow_html=True)

        except Exception as e:
            st.error("エラーが発生しました。APIキーを確認してください。")

# --- フッター ---
st.markdown('<div class="footer-mark">EIGHT MEN</div>', unsafe_allow_html=True)
