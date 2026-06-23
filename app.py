import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests

st.set_page_config(page_title="レターパック追跡管理システム", page_icon="📦", layout="wide")

st.title("📦 レターパック追跡管理システム")

# 1. Googleスプレッドシートからのデータ読み込み（閲覧）
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="0")
except Exception as e:
    df = pd.DataFrame(columns=["tracking_number", "label"])

# データの初期整形
if df is None or df.empty:
    df = pd.DataFrame(columns=["tracking_number", "label"])
else:
    df.columns = df.columns.str.strip()

st.header("✍️ 追跡番号の追加")
col1, col2 = st.columns(2)

with col1:
    new_number = st.text_input("追跡番号（スペースやハイフン対応）", placeholder="例: 3383-9953-2575")
with col2:
    new_label = st.text_input("ラベル（例: 〇〇様宛）", placeholder="例: 山田様宛")

if st.button("➕ リストに追加する"):
    if new_number:
        cleaned_number = new_number.replace("-", "").replace(" ", "")
        
        # SecretsからスプレッドシートのURLを取得
        try:
            sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
            # 共有URLからスプレッドシートIDを抽出
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
            
            # Googleフォームを使わない、直接書き込み用代替ロジック
            # エラーを回避するため、内部のデータフレームを更新してupdateを試みる
            new_data = pd.DataFrame([{"tracking_number": cleaned_number, "label": new_label}])
            df = pd.concat([df, new_data], ignore_index=True)
            
            # 既存のupdate関数をもう一度、データ構造をより単純化して試行
            clean_df = pd.DataFrame({
                "tracking_number": df["tracking_number"].astype(str),
                "label": df["label"].astype(str)
            })
            
            conn.update(data=clean_df)
            st.success(f"「{new_number}」を追加しました！")
            st.rerun()
            
        except Exception as e:
            # 万が一Googleのセキュリティで弾かれた場合の、画面上だけの一時保持フォールバック
            if "temp_list" not in st.session_state:
                st.session_state.temp_list = []
            st.session_state.temp_list.append({"tracking_number": cleaned_number, "label": new_label})
            st.success(f"「{new_number}」を一時リストに追加しました（スプレッドシートの認証制限により、画面上のみ保持されています）")
            st.rerun()
    else:
        st.error("追跡番号を入力してください。")

st.markdown("---")
st.header("📋 追跡リスト")

# セッション状態の一時データも統合して表示
display_df = df.copy()
if "temp_list" in st.session_state and st.session_state.temp_list:
    temp_df = pd.DataFrame(st.session_state.temp_list)
    display_df = pd.concat([display_df, temp_df], ignore_index=True)

if not display_df.empty:
    if "tracking_number" in display_df.columns:
        # 重複を排除して綺麗にする
        display_df = display_df.drop_duplicates(subset=["tracking_number"], keep="last")
        
        for index, row in display_df.iterrows():
            num = str(row["tracking_number"]).strip()
            if num == "tracking_number" or num == "" or num == "nan":
                continue
                
            lbl = row["label"] if ("label" in display_df.columns and pd.notna(row["label"])) else ""
            if lbl == "label" or lbl == "nan":
                lbl = ""
            
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
