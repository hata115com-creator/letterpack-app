import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import time
import os

st.set_page_config(page_title="レターパック追跡管理", layout="wide")
st.title("📦 レターパック追跡管理システム")

# 💾 データの保存先ファイル名
DATA_FILE = "tracking_data.csv"

# 💾 ファイルからデータを読み込む関数
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE).to_dict(orient="records")
        except:
            return []
    return []

# 💾 ファイルへデータを保存する関数
def save_data(data):
    df = pd.DataFrame(data)
    df.to_csv(DATA_FILE, index=False)

# セッション状態の初期化（ファイルから読み込む）
if "tracking_list" not in st.session_state:
    st.session_state.tracking_list = load_data()

# --- 郵便追跡ステータス取得関数 ---
def get_tracking_status(tracking_no):
    url = f"https://trackings.post.japanpost.jp/services/srv/search/direct?reqCodeNo1={tracking_no}"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table", class_="table_type01")
        if len(tables) > 1:
            rows = tables[1].find_all("tr")
            latest_status = rows[-1].find_all("td")[2].text.strip()
            return latest_status
        return "データなし（番号未登録）"
    except Exception as e:
        return "取得エラー"

# --- 追跡リスト一括更新関数 ---
def update_all_statuses():
    updated = False
    for item in st.session_state.tracking_list:
        if item["status"] == "配達完了":
            continue
        new_status = get_tracking_status(item["tracking_no"])
        if item["status"] != new_status:
            item["status"] = new_status
            updated = True
    if updated:
        save_data(st.session_state.tracking_list)

# --- ✍️ メイン画面：番号追加エリア ---
st.header("✍️ 追跡番号の追加")
col1, col2 = st.columns(2)

with col1:
    input_no = st.text_input("追跡番号（スペースやハイフン対応）", placeholder="例: 3383-9953-2575")
with col2:
    input_label = st.text_input("ラベル（例: 〇〇様宛）", placeholder="例: 山田様宛")

if st.button("➕ リストに追加する", type="primary"):
    if input_no:
        clean_no = re.sub(r'\D', '', input_no)
        
        if len(clean_no) == 12:
            if not any(d['tracking_no'] == clean_no for d in st.session_state.tracking_list):
                with st.spinner("追加と同時に最初の状態を確認中..."):
                    initial_status = get_tracking_status(clean_no)
                    
                st.session_state.tracking_list.append({
                    "tracking_no": clean_no,
                    "label": input_label if input_label else "ラベルなし",
                    "status": initial_status
                })
                # 💡 追加したらファイルに保存
                save_data(st.session_state.tracking_list)
                st.success(f"追加しました！現在の状況: {initial_status}")
                st.rerun()
            else:
                st.warning("この番号は既にリストに存在します。")
        else:
            st.error("12桁の数字になるように確認してください。")
    else:
        st.error("追跡番号を入力してください。")

st.write("---")

# --- 📋 メイン画面：リスト表示 & ステータス更新 ---
st.header("📋 追跡リスト")

if st.session_state.tracking_list:
    col_btn1, col_btn2 = st.columns([1, 5])
    with col_btn1:
        if st.button("🔄 状況を更新する"):
            with st.spinner("未完了の追跡状況を更新中..."):
                update_all_statuses()
            st.success("更新が完了しました！（配達完了分はスキップしました）")
            st.rerun()
            
    with col_btn2:
        if st.button("リストをすべてクリア"):
            st.session_state.tracking_list = []
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.rerun()

    df = pd.DataFrame(st.session_state.tracking_list)
    df.columns = ["追跡番号", "ラベル", "現在の状況"]
    st.dataframe(df, use_container_width=True)
    
    st.caption("※アプリを開いたままの場合、3時間ごとに自動更新します。")
    time.sleep(0.1)
    st.fragment(run_every=10800)(update_all_statuses)

else:
    st.info("上の入力欄に、レターパックの番号を入れて追加してください。")
