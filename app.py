import streamlit as st

st.set_page_config(page_title="レターパック追跡管理システム", page_icon="📦", layout="wide")

st.title("📦 レターパック追跡管理システム")

# 画面上でデータを一時保存するためのリストを準備（セッション状態）
if "tracking_list" not in st.session_state:
    st.session_state.tracking_list = []

st.header("✍️ 追跡番号の追加")
col1, col2 = st.columns(2)

with col1:
    new_number = st.text_input("追跡番号（スペースやハイフン対応）", placeholder="例: 3383-9953-2575")
with col2:
    new_label = st.text_input("ラベル（例: 〇〇様宛）", placeholder="例: 山田様宛")

if st.button("➕ リストに追加する"):
    if new_number:
        # ハイフンやスペースを除去して数字だけにする
        cleaned_number = new_number.replace("-", "").replace(" ", "")
        
        # リストに重複がないかチェックして追加
        exists = any(item["tracking_number"] == cleaned_number for item in st.session_state.tracking_list)
        if not exists:
            st.session_state.tracking_list.append({
                "tracking_number": cleaned_number,
                "label": new_label
            })
            st.success(f"「{new_number}」を追加しました！")
            st.rerun()
        else:
            st.warning("この番号はすでにリストに追加されています。")
    else:
        st.error("追跡番号を入力してください。")

st.markdown("---")
st.header("📋 追跡リスト")

# 登録されている番号があれば一覧表示する
if st.session_state.tracking_list:
    for index, item in enumerate(st.session_state.tracking_list):
        num = item["tracking_number"]
        lbl = item["label"]
        
        # 日本郵便の追跡URLを作成
        postal_url = f"https://trackings.post.japanpost.jp/services/srv/search/direct?reqCodeNo1={num}"
        
        with st.container():
            c1, c2, c3 = st.columns([3, 3, 2])
            c1.write(f"**番号**: {num}")
            c2.write(f"**ラベル**: {lbl if lbl else '（ラベルなし）'}")
            c3.markdown(f"[🔍 郵便局で追跡]({postal_url})")
            st.markdown(" ")
else:
    st.info("上の入力欄に、レターパックの番号を入れて追加してください。")
