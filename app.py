import streamlit as st
import qrcode
from io import BytesIO
import socket
from PIL import Image, ImageDraw, ImageFont

# 1. ページ設定
st.set_page_config(page_title="野菜・果物 Tier表", layout="centered")

# 自分のローカルIPアドレスを自動取得する関数
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

local_ip = get_local_ip()
app_url = f"http://{local_ip}:8501"

# サイドバーにスマホ接続用のQRコードを表示
with st.sidebar:
    st.header("📱 スマホで開く")
    st.caption("PCと同じWi-Fiに接続したスマホのカメラで読み取ってください")
    
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(app_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    st.image(buf.getvalue(), caption=app_url)

st.title("🥦 野菜・果物 Tier表")
st.caption("ボタンを押して野菜をTierに配置しよう！")

# 2. データ（状態）の初期化
if "vegetables" not in st.session_state:
    st.session_state.vegetables = [
        "🌽 とうもろこし", "🥑 アボカド", "🥔 じゃがいも", "🍠 さつまいも",
        "🫛 えだまめ", "🎃 かぼちゃ", "🌰 栗", "🍎 りんご", "🍊 みかん",
        "🍇 ぶどう", "🍓 いちご", "🍑 もも", "🍒 さくらんぼ", "🍌 バナナ",
        "🥒 きゅうり", "🍅 トマト", "🥦 ブロッコリー", "🧅 たまねぎ", "🥕 にんじん"
    ]

if "tier_data" not in st.session_state:
    st.session_state.tier_data = {
        "S": [],
        "A": [],
        "B": [],
        "C": [],
        "D": []
    }

tier_info = {
    "S": {"name": "S (Suki)", "color": "🔴", "desc": "自分から積極的に食べる", "bg_color": "#ffcccc"},
    "A": {"name": "A (Able)", "color": "🟡", "desc": "食事に入ってたら食べる", "bg_color": "#ffffcc"},
    "B": {"name": "B (Bad)", "color": "🟢", "desc": "スープなどと一緒なら食べられる", "bg_color": "#ccffcc"},
    "C": {"name": "C (Cannot)", "color": "🔵", "desc": "残すけど飲み込むことはできる", "bg_color": "#cce5ff"},
    "D": {"name": "D (Dead)", "color": "🟣", "desc": "自分の命がかかってても食べないかも", "bg_color": "#e5ccff"},
}

def move_to_tier(veg, target_tier):
    if veg in st.session_state.vegetables:
        st.session_state.vegetables.remove(veg)
    st.session_state.tier_data[target_tier].append(veg)

def reset_veg(veg, current_tier):
    st.session_state.tier_data[current_tier].remove(veg)
    st.session_state.vegetables.append(veg)

import re

# 【説明文追加・文字化け対策版】Tier表を画像として生成する関数
def generate_tier_image():
    width, height = 1000, 650
    img = Image.new("RGB", (width, height), color="#f8f9fa")
    draw = ImageDraw.Draw(img)
    
    # OSごとの日本語フォント自動読み込み
    font_path_candidates = [
        "C:\\Windows\\Fonts\\meiryo.ttc",       # Windows (メイリオ)
        "C:\\Windows\\Fonts\\msgothic.ttc",     # Windows (MS ゴシック)
        "/System/Library/Fonts/Hiragino Sans GB.ttc", # Mac
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    
    font = None
    sub_font = None
    title_font = None
    for path in font_path_candidates:
        try:
            font = ImageFont.truetype(path, 16)
            sub_font = ImageFont.truetype(path, 11)  # 説明文用（小さめ）
            title_font = ImageFont.truetype(path, 22)
            break
        except OSError:
            continue
            
    if font is None:
        font = ImageFont.load_default()
        sub_font = font
        title_font = font

    # タイトル描画
    draw.text((20, 15), "Vegetable & Fruit Tier List", fill="black", font=title_font)
    
    y_offset = 55
    row_height = 105
    label_width = 230  # 説明文が入るように左側のラベル幅を拡大
    
    for code, info in tier_info.items():
        # Tierラベル背景（暗いグレー）
        draw.rectangle([20, y_offset, label_width, y_offset + row_height - 10], fill="#333333")
        
        # Tier名（S, A, B...）
        draw.text((30, y_offset + 20), f"Tier {code}", fill="white", font=title_font)
        
        # Tierの説明文
        draw.text((30, y_offset + 58), info["desc"], fill="#dddddd", font=sub_font)
        
        # アイテムエリア背景（カラー）
        draw.rectangle([label_width + 10, y_offset, width - 20, y_offset + row_height - 10], fill=info["bg_color"], outline="#cccccc")
        
        # 配置されたアイテムテキストから絵文字を取り除いて文字だけに整形
        raw_items = st.session_state.tier_data[code]
        clean_items = []
        for item in raw_items:
            clean_name = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', item).strip()
            clean_items.append(clean_name if clean_name else item)
            
        text_content = " ,  ".join(clean_items) if clean_items else "(配置なし)"
        
        # アイテム描画
        draw.text((label_width + 25, y_offset + 38), text_content, fill="black", font=font)
        
        y_offset += row_height
        
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# 3. 画面表示：Tier一覧エリア
st.subheader("📊 Tier一覧")

for code, info in tier_info.items():
    with st.container(border=True):
        st.markdown(f"### {info['color']} {info['name']}")
        st.caption(info["desc"])
        
        placed_vegs = st.session_state.tier_data[code]
        if placed_vegs:
            for veg in list(placed_vegs):
                col_name, col_btn = st.columns([4, 1])
                col_name.write(f"**{veg}**")
                if col_btn.button("✕ 戻す", key=f"reset_{code}_{veg}"):
                    reset_veg(veg, code)
                    st.rerun()
        else:
            st.write("*(まだ何も配置されていません)*")

# 画像ダウンロードボタンの配置
st.write("")
image_bytes = generate_tier_image()
st.download_button(
    label="💾 完成したTier表を画像としてダウンロード",
    data=image_bytes,
    file_name="vegetable_tier_list.png",
    mime="image/png",
    use_container_width=True
)

st.divider()

# 4. 自由追加エリア
st.subheader("➕ 好きな野菜・料理を追加")

with st.form(key="add_item_form", clear_on_submit=True):
    col_input, col_add_btn = st.columns([3, 1])
    new_item = col_input.text_input("追加したい食べ物の名前", placeholder="例: 🥑 パクチー, 🍜 ラーメン", label_visibility="collapsed")
    submit_button = col_add_btn.form_submit_button("追加する", use_container_width=True)
    
    if submit_button:
        item_name = new_item.strip()
        if item_name:
            all_placed = [v for items in st.session_state.tier_data.values() for v in items]
            
            if item_name in st.session_state.vegetables or item_name in all_placed:
                st.warning(f"「{item_name}」はすでにリストまたはTier表に存在します！")
            else:
                st.session_state.vegetables.insert(0, item_name)
                st.success(f"「{item_name}」を追加しました！")
                st.rerun()
        else:
            st.warning("名前を入力してください。")

st.divider()

# 5. 画面表示：未配置の野菜エリア
st.subheader("🥬 未配置の野菜・果物")

if not st.session_state.vegetables:
    st.success("🎉 すべての野菜の配置が完了しました！")
else:
    for veg in list(st.session_state.vegetables):
        st.markdown(f"#### {veg}")
        
        btn_s, btn_a, btn_b, btn_c, btn_d = st.columns(5)
        
        if btn_s.button("🔴 S\n(好き)", key=f"s_{veg}", use_container_width=True):
            move_to_tier(veg, "S")
            st.rerun()
            
        if btn_a.button("🟡 A\n(食べる)", key=f"a_{veg}", use_container_width=True):
            move_to_tier(veg, "A")
            st.rerun()
            
        if btn_b.button("🟢 B\n(料理で)", key=f"b_{veg}", use_container_width=True):
            move_to_tier(veg, "B")
            st.rerun()
            
        if btn_c.button("🔵 C\n(残す)", key=f"c_{veg}", use_container_width=True):
            move_to_tier(veg, "C")
            st.rerun()
            
        if btn_d.button("🟣 D\n(無理)", key=f"d_{veg}", use_container_width=True):
            move_to_tier(veg, "D")
            st.rerun()
        
        st.write("")