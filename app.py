import streamlit as st
import json
import os
import qrcode
from io import BytesIO
import base64
from pytube import Playlist, YouTube
import time

# ========== Page Setup ==========
st.set_page_config(page_title="🎵 Trình phát Playlist YouTube PRO+", layout="centered")

# ========== Auto play meme intro ==========
st.markdown("""
<iframe width="0" height="0" src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1" frameborder="0" allow="autoplay"></iframe>
""", unsafe_allow_html=True)

# ========== Background Music ==========
st.markdown("""
<audio autoplay loop hidden>
  <source src="bg.mp3" type="audio/mp3">
</audio>
""", unsafe_allow_html=True)

# ========== Theme Selection ==========
theme = st.selectbox("🎨 Chọn chủ đề giao diện", ["Tối", "Sáng", "Gradient tím", "Nền ảnh"])
theme_css = {
    "Tối": "background-color: #0e1117; color: white;",
    "Sáng": "background-color: #f5f5f5; color: black;",
    "Gradient tím": "background: linear-gradient(135deg, #6e8efb, #a777e3); color: white;",
    "Nền ảnh": "background: url('https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1350&q=80'); background-size: cover; color: white;",
}
st.markdown(f"<style>body {{{theme_css[theme]}}}</style>", unsafe_allow_html=True)

# ========== Loader Style ==========
st.markdown("""
<style>
.loader {
  border: 6px solid #f3f3f3;
  border-top: 6px solid #3498db;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.glow-text {
  color: white;
  font-size: 28px;
  font-weight: bold;
  text-align: center;
  text-shadow: 0 0 10px #fff, 0 0 20px #00f, 0 0 30px #0ff;
}
</style>
""", unsafe_allow_html=True)

# ========== Playlist Data ==========
playlist_file = "playlists.json"
if not os.path.exists(playlist_file):
    with open(playlist_file, "w") as f:
        json.dump([], f)

def load_playlists():
    with open(playlist_file, "r") as f:
        return json.load(f)

def save_playlist(entry):
    data = load_playlists()
    if all(d["id"] != entry["id"] for d in data):
        data.insert(0, entry)
        with open(playlist_file, "w") as f:
            json.dump(data[:15], f, indent=2)

def extract_id(u):
    if "list=" in u:
        return u.split("list=")[1].split("&")[0]
    else:
        return u.strip()

# ========== UI ==========
st.title("🎶 Trình phát Playlist YouTube PRO+")

url = st.text_input("📋 Nhập link playlist YouTube hoặc ID:")
col1, col2 = st.columns([3, 1])
with col1:
    note = st.text_input("💬 Ghi chú / bình luận")
with col2:
    tags = st.text_input("🏷️ Tag (phân cách bằng dấu phẩy)", placeholder="chill, gym")

st.markdown("---")
st.subheader("🗂️ Danh sách Playlist đã lưu")

data = load_playlists()
selected_tag = st.selectbox("📌 Lọc theo tag", ["Tất cả"] + sorted({tag for d in data for tag in d.get("tags", []) if tag}))
filtered = [d for d in data if selected_tag == "Tất cả" or selected_tag in d.get("tags", [])]

for item in filtered:
    st.markdown(f"""
    - 🎵 **[{item['id']}](https://www.youtube.com/playlist?list={item['id']})**
      - 💬 {item.get("note", "_(không ghi chú)_")}
      - 🏷️ {', '.join(item.get("tags", [])) if item.get("tags") else "_(không có tag)_"}
    """)

if url:
    pl_id = extract_id(url)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    save_playlist({"id": pl_id, "note": note, "tags": tag_list})

    st.markdown("---")
    st.markdown("### 🖼️ Thông tin bài hát đầu tiên")

    loading_placeholder = st.empty()
    with loading_placeholder.container():
        st.markdown("⏳ Đang tải thông tin bài hát...")
        st.markdown("<div class='loader'></div>", unsafe_allow_html=True)
        time.sleep(2)

    try:
        playlist = Playlist(f"https://www.youtube.com/playlist?list={pl_id}")
        first_video = playlist.video_urls[0]
        yt = YouTube(first_video)

        title = yt.title
        thumbnail_url = yt.thumbnail_url
        views = yt.views
        likes = yt.rating

        loading_placeholder.empty()
        st.image(thumbnail_url, width=400, caption=title)
        st.markdown(f"<div class='glow-text'>🎵 {title}</div>", unsafe_allow_html=True)
        st.markdown(f"👁️ **Lượt xem:** {views:,}")
        st.markdown(f"⭐ **Đánh giá trung bình:** {likes if likes else 'Không rõ'}")

    except Exception as e:
        loading_placeholder.empty()
        st.error(f"Lỗi lấy thông tin video: {e}")

    st.markdown("### ▶️ Trình phát nâng cao")

    html = f"""
    <div id=\"player\"></div>
    <div style=\"margin-top:10px\">
        <button onclick=\"player.playVideo()\">▶️ Play</button>
        <button onclick=\"player.pauseVideo()\">⏸ Pause</button>
        <button onclick=\"player.setShuffle(true); player.nextVideo()\">🔀 Shuffle</button>
        <input type=\"range\" min=\"0\" max=\"100\" value=\"50\" oninput=\"player.setVolume(this.value)\">
        <label>Âm lượng</label>
    </div>

    <script>
    var tag = document.createElement('script');
    tag.src = \"https://www.youtube.com/iframe_api\";
    var firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    var player;
    function onYouTubeIframeAPIReady() {
        player = new YT.Player('player', {
            height: '0',
            width: '0',
            playerVars: {
                listType: 'playlist',
                list: '""" + pl_id + """',
                autoplay: 1,
                loop: 1
            },
            events: {
                'onReady': onPlayerReady
            }
        });
    }
    function onPlayerReady(event) {
        event.target.setVolume(50);
        event.target.playVideo();
    }
    </script>
    """
    st.components.v1.html(html, height=150)

    st.markdown("### 🔗 Mã QR chia sẻ playlist")
    share_url = f"https://www.youtube.com/playlist?list={pl_id}"
    qr_img = qrcode.make(share_url)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    img_b64 = base64.b64encode(buffer.getvalue()).decode()
    st.image(f"data:image/png;base64,{img_b64}", caption="Quét để mở playlist", width=200)

else:
    st.info("⏳ Nhập link playlist để bắt đầu phát và xem thông tin.")
