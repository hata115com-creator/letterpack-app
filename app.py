import streamlit as st
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="レターパック追跡管理システム", page_icon="📦", layout="wide")

st.title("📦 レターパック追跡管理システム")

# 画面上でデータを保持するためのリスト（セッション状態）
if "tracking_list" not in st.session_state:
    st.session_state.tracking_list = []

# --- 郵便局のページから現在のステータスを自動で持ってくる関数 ---
def fetch_status(tracking_number):
    url = f"https://trackings.post.japanpost.jp/services/srv/search/direct?reqCodeNo1={tracking_number}"
    try:
        response = requests.get(url, timeout=5)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        status_element = soup.find('td', class_='status')
        if status_element:
            return status_element.text.strip()
        
        tables = soup.find_all('table', class_='table_type01')
        if len(tables) >= 2:
            rows = tables[1].find_all('tr')
            if len(rows) >= 2:
                cols = rows[1].find_all('td')
                if len(cols) >= 2:
                    return cols[1].text.strip()
        return "データなし（番号確認中）"
    except Exception:
        return "取得エラー（再度お試しください）"

# --- 全員を一斉更新する関数 ---
def update_all_statuses():
    with st.spinner("すべてのレターパックの最新状況を確認中..."):
        for item in st.session_state.tracking_list:
            item["status"] = fetch_status(item["tracking_number"])
        st.session_state.last_update_time = time.time()

# --- 3時間（10800秒）毎に自動更新するタイマー設定 ---
if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = time.time()

current_time = time.time()
if current_time - st.session_state.last_update_time > 10800:
    update_all_statuses()
    st.rerun()


# --- 画面レイアウト：入力エリア ---
st.header("✍️ 追跡番号の追加")
col1, col2 = st.columns(2)

with col1:
    new_number = st.text_input("追跡番号（スペースやハイフン対応）", placeholder="例: 3383-9953-2575")
with col2:
    new_label = st.text_input("ラベル（例: 〇〇様宛）", placeholder="例: 山田様宛")

if st.button("➕ リストに追加する"):
    if new_number:
        cleaned_number = new_number.replace("-", "").replace(" ", "")
        
        # 重複チェック
        exists = any(item["tracking_number"] == cleaned_number for item in st.session_state.tracking_list)
        if not exists:
            with st.spinner("新規追加データの状態を調べています..."):
                current_status = fetch_status(cleaned_number)
            
            st.session_state.tracking_list.append({
                "tracking_number": cleaned_number,
                "label": new_label,
                "status": current_status
            })
            st.success(f"「{new_number}」を追加しました！")
            st.rerun()
        else:
            st.warning("この番号はすでにリストに追加されています。")
    else:
        st.error("追跡番号を入力してください。")

st.markdown("---")

# --- 画面レイアウト：リスト表示と操作ボタン ---
st.header("📋 追跡リスト")

if st.session_state.tracking_list:
    # 管理用ボタンを横並びにする（手動更新 ＆ 一括削除）
    btn_col1, btn_col2, _ = st.columns([3, 3, 4])
    
    with btn_col1:
        if st.button("🔄 今すぐリストを一斉更新する", use_container_width=True):
            update_all_statuses()
            st.success("すべてのステータスを最新に更新しました！")
            st.rerun()
            
    with btn_col2:
        if st.button("💥 全てのリストを削除する", type="primary", use_container_width=True):
            st.session_state.tracking_list = []
            st.success("すべてのリストを削除しました。")
            st.rerun()
        
    st.markdown(" ")

    # 各追跡番号のループ表示
    for index, item in enumerate(st.session_state.tracking_list):
        num = item["tracking_number"]
        lbl = item["label"]
        status = item.get("status", "未取得")
        
        postal_url = f"https://trackings.post.japanpost.jp/services/srv/search/direct?reqCodeNo1={num}"
        status_color = "🟢" if "完了" in status else "🔵"
        
        with st.container():
            # 列の配置（番号、ラベル、状態、郵便局リンク、個別の削除ボタン）
            c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 1])
            c1.write(f"**番号**: {num}")
            c2.write(f"**ラベル**: {lbl if lbl else '（なし）'}")
            c3.write(f"**状態**: {status_color} {status}")
            c4.markdown(f"[🔍 郵便局サイト]({postal_url})")
            
            # 個別削除ボタン（キーが重複しないよう、インデックスを付与しています）
            if c5.button("🗑️", key=f"del_{index}"):
                st.session_state.tracking_list.pop(index)
                st.rerun()
            st.markdown(" ")
else:
    st.info("上の入力欄に、レターパックの番号を入れて追加してください。")
