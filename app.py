import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="レターパック追跡管理システム", page_icon="📦", layout="wide")

st.title("📦 レターパック追跡管理システム")

# Googleスプレッドシートへの接続
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 既存データの読み込み
    df = conn.read(ttl="0")
except Exception as e:
    st.error("Googleスプレッドシートとの接続に失敗しました。Secretsの設定を確認してください。")
    df = pd.DataFrame(columns=["tracking_number", "label"])

# データの整形（万が一空だった場合の対応）
if df is None or df.empty:
    df = pd.DataFrame(columns=["tracking_number", "label"])
else:
    # 列名を綺麗にする
    df.columns = df.columns.str.strip()

st.header("✍️ 追跡番号の追加")
col1, col2 = st.columns(2)

with col1:
    new_number = st.text_input("追跡番号（スペースやハイフン対応）", placeholder="例: 3383-9953-2575")
with col2:
    new_label = st.text_input("ラベル（例: 〇〇様宛）", placeholder="例: 山田様宛")

if st.button("➕ リストに追加する"):
    if new_number:
        # ハイフンやスペースを除去
        cleaned_number = new_number.replace("-", "").replace(" ", "")
        
        # 新しい行を作成
        new_data = pd.DataFrame([{"tracking_number": cleaned_number, "label": new_label}])
        
        # 既存データの下に新しい行を追加
        df = pd.concat([df, new_data], ignore_index=True)
        
        try:
            # 安全な方法（上書きではなく、新しいデータとしてスプレッドシートに反映）
            conn.update(data=df)
            st.success(f"「{new_number}」を追加しました！")
            st.rerun()
        except Exception as e:
            st.error(f"書き込みエラーが発生しました。スプレッドシートの共有設定が『編集者』になっているかご確認ください。")
    else:
        st.error("追跡番号を入力してください。")

st.markdown("---")
st.header("📋 追跡リスト")

# 表示部分（空でない場合のみループ）
if df is not None and not df.empty:
    # 念のため必要な列があるかチェック
    if "tracking_number" in df.columns:
        for index, row in df.iterrows():
            num = str(row["tracking_number"]).strip()
            # 1行目の見出しそのものや空行はスキップ
            if num == "tracking_number" or num == "" or num == "nan":
                continue
                
            lbl = row["label"] if ("label" in df.columns and pd.notna(row["label"])) else ""
            if lbl == "label" or lbl == "nan":
                lbl = ""
            
            # 日本郵便の追跡URL
            postal_url = f"https://trackings.post.japanpost.jp/services/srv/search/direct?reqCodeNo1={num}"
            
            with st.container():
                c1, c2, c3 = st.columns([3, 3, 2])
                c1.write(f"**番号**: {num}")
                c2.write(f"**ラベル**: {lbl}")
                c3.markdown(f"[🔍 郵便局で追跡]({postal_url})")
                st.markdown(" ")
    else:
        st.info("追跡データがまだありません。上の入力欄から追加してください。")
else:
    st.info("上の入力欄に、レターパックの番号を入れて追加してください。")
