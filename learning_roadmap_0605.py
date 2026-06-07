import streamlit as st
import pandas as pd
import time
import os
import base64
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 0. 後端：異步計時器重新導向管線監聽器 (防刷防呆)
# ==========================================
if st.query_params.get("magic_timer_done") == "true":
    if 'coins' in st.session_state:
        st.session_state.coins += 1
        st.session_state.daily_timer_done = True
        st.session_state.audio_trigger = 'coin'
    st.query_params.clear()  # 瞬間抹除網址參數，防止重新整理刷幣
    # 延遲重新載入交給後續流程處理，此處不單獨阻塞

# ==========================================
# 0.1 環境變數切換開關 (全自動偵測版)
# ==========================================
if os.name == 'nt': ENVIRONMENT = "DEV"
else: ENVIRONMENT = "PROD"

SUFFIX = "_dev" if ENVIRONMENT == "DEV" else ""
WS_COINS = f"coins{SUFFIX}"
WS_SITES = f"sites{SUFFIX}"
WS_RESOURCES = f"resources{SUFFIX}"
WS_QUIZ = f"quiz{SUFFIX}"
WS_MILESTONES = f"milestones{SUFFIX}"
WS_REWARDS = f"rewards{SUFFIX}" 

# ==========================================
# 1. 網頁基本設定 & 護眼暗黑風格 CSS
# ==========================================
st.set_page_config(
    page_title=f"🦖 澳洲恐龍特派員 ({ENVIRONMENT} 模式)",
    page_icon="🦖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔥【特派員總部徽章注入器・穿透 iframe 封裝版】
import streamlit.components.v1 as components
components.html("""
<script>
    function injectDinoIcons() {
        const parentDoc = window.parent.document;
        const parentHead = parentDoc.head;
        const dinoIconUrl = "https://img.icons8.com/color/144/ankylosaurus.png";
        const oldApple = parentDoc.getElementById("dino-pwa-apple");
        if (oldApple) oldApple.remove();
        const oldAndroid = parentDoc.getElementById("dino-pwa-android");
        if (oldAndroid) oldAndroid.remove();
        const appleLink = parentDoc.createElement("link");
        appleLink.id = "dino-pwa-apple"; appleLink.rel = "apple-touch-icon"; appleLink.href = dinoIconUrl;
        parentHead.appendChild(appleLink);
        const androidLink = parentDoc.createElement("link");
        androidLink.id = "dino-pwa-android"; androidLink.rel = "icon"; androidLink.sizes = "192x192"; androidLink.href = dinoIconUrl;
        parentHead.appendChild(androidLink);
    }
    injectDinoIcons(); setTimeout(injectDinoIcons, 1000);
</script>
""", height=0, width=0)

st.markdown("""
<style>
    .coin-box { background-color: #1e293b; border-radius: 15px; padding: 15px; border: 2px dashed #f59e0b; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .admin-box { background-color: #0f172a; border-radius: 15px; padding: 15px; border: 2px solid #10b981; text-align: center; margin-bottom: 20px; }
    .game-node-unlocked { background: linear-gradient(145deg, #1e3a8a, #172554); border: 2px solid #3b82f6; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.4); height: 100%; color: #eff6ff; }
    .game-node-locked { background: #0f172a; border: 2px dashed #475569; border-radius: 12px; padding: 15px; text-align: center; color: #94a3b8; height: 100%; }
    .resource-card { background-color: #1e293b; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 10px; border-radius: 6px; color: #f8fafc; }
    div[data-testid="stButton"] button { width: 100% !important; font-size: 26px !important; padding: 20px !important; background: linear-gradient(135deg, #e11d48 0%, #9f1239 100%) !important; color: white !important; font-weight: 900 !important; border-radius: 15px !important; border: 2px solid #fda4af !important; box-shadow: 0px 8px 15px rgba(225,29,72,0.4) !important; letter-spacing: 1px; }
    div[data-testid="stButton"] button:hover { background: linear-gradient(135deg, #f43f5e 0%, #be123c 100%) !important; color: white !important; }
    .sync-btn-container div[data-testid="stButton"] button { background: linear-gradient(135deg, #059669 0%, #047857 100%) !important; border: 2px solid #34d399 !important; font-size: 22px !important; }
    .logout-btn-container div[data-testid="stButton"] button { background: linear-gradient(135deg, #475569 0%, #334155 100%) !important; border: 2px solid #94a3b8 !important; font-size: 18px !important; padding: 10px !important; margin-top: 20px !important;}
    .magic-timer-box { background: linear-gradient(135deg, #fef08a 0%, #fde047 100%); padding: 20px; border-radius: 15px; text-align: center; border: 3px dashed #ca8a04; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .wish-progress-bg { background: #334155; border-radius: 10px; width: 100%; height: 20px; position: relative; margin: 10px 0; }
    .wish-progress-fill { background: linear-gradient(90deg, #3b82f6, #60a5fa); height: 100%; border-radius: 10px; transition: width 0.5s; }
</style>
""", unsafe_allow_html=True)

if 'audio_trigger' not in st.session_state: st.session_state.audio_trigger = None
if 'country_unlocked_counts' not in st.session_state: st.session_state.country_unlocked_counts = {}
if 'just_unlocked' not in st.session_state: st.session_state.just_unlocked = False
if 'trigger_map_animation' not in st.session_state: st.session_state.trigger_map_animation = False

# ==========================================
# 2. 前端：強制安全認證大門
# ==========================================
USER_CREDENTIALS = {"Ailey": "0000", "Kelly": "8888"}

def verify_login(username, password):
    if USER_CREDENTIALS.get(username) == password:
        st.session_state.is_authenticated = True
        st.session_state.logged_in_user = username
        return True
    return False

if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

if not st.session_state.is_authenticated:
    st.markdown("<h1 style='text-align: center; color: #3b82f6; margin-top: 50px;'>🦖 澳洲恐龍特派員總部 - 安全驗證</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='background-color: #1e293b; padding: 30px; border-radius: 15px; border: 2px solid #64748b; box-shadow: 0 10px 25px rgba(0,0,0,0.5);'>", unsafe_allow_html=True)
        login_user = st.selectbox("👤 請選擇特派員身分：", ["Ailey", "Kelly"])
        login_pwd = st.text_input("🔑 請輸入通行密碼：", type="password")
        
        if st.button("🚀 啟動導航艙", use_container_width=True):
            if verify_login(login_user, login_pwd):
                st.success(f"✅ 驗證成功！歡迎回來，{login_user}！")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ 密碼錯誤，請重新輸入！")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()  # ⛔ 未驗證通過前強制斷路，不與 Google Sheets 進行連線

# ==========================================
# 3. 雲端資料庫讀寫模組 (通過驗證後才可渲染)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

# 🎯【規格升級】：只保留您指定的 6 項願望作為底層預設資產
DEFAULT_REWARDS_ASSETS = [
    {"獎勵名稱": "恐龍電影或紀錄片", "所需未來幣": 80},
    {"獎勵名稱": "高雄科工館3D電影", "所需未來幣": 120},
    {"獎勵名稱": "台南左鎮化石園區", "所需未來幣": 150},
    {"獎勵名稱": "台中科工館恐龍展覽", "所需未來幣": 200},
    {"獎勵名稱": "臺灣博物館土銀展示館", "所需未來幣": 300},
    {"獎勵名稱": "基隆AR恐龍生態園區", "所需未來幣": 300}
]

@st.cache_data(ttl=600)
def load_cloud_data_store():
    data = {
        "coins": conn.read(worksheet=WS_COINS, ttl=0),
        "sites": conn.read(worksheet=WS_SITES, ttl=0),
        "resources": conn.read(worksheet=WS_RESOURCES, ttl=0),
        "quiz": conn.read(worksheet=WS_QUIZ, ttl=0),
        "milestones": conn.read(worksheet=WS_MILESTONES, ttl=0)
    }
    try:
        data["rewards"] = conn.read(worksheet=WS_REWARDS, ttl=0)
        if data["rewards"].empty or len(data["rewards"]) == 0:
            data["rewards"] = pd.DataFrame(DEFAULT_REWARDS_ASSETS)
    except:
        data["rewards"] = pd.DataFrame(DEFAULT_REWARDS_ASSETS)
    return data

data_store = load_cloud_data_store()
df_coins = data_store["coins"]
df_sites = data_store["sites"]
df_resources = data_store["resources"]
df_quiz = data_store["quiz"]
df_milestones = data_store["milestones"]
df_rewards = data_store["rewards"]

if 'current_map_country' not in st.session_state: st.session_state.current_map_country = None
if 'completed_countries' not in st.session_state: st.session_state.completed_countries = []
if 'just_completed_country' not in st.session_state: st.session_state.just_completed_country = None

user_row_idx = 0 if st.session_state.logged_in_user == "Ailey" else 1
if not df_coins.empty and "使用者" in df_coins.columns:
    user_rows = df_coins[df_coins["使用者"] == st.session_state.logged_in_user]
    if not user_rows.empty: user_row_idx = user_rows.index[0]

# 記憶體變數初始化防護
if 'coins' not in st.session_state:
    st.session_state.coins = int(df_coins.loc[user_row_idx, "coins"]) if not df_coins.empty and len(df_coins) > user_row_idx and "coins" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "coins"]) else 0
    st.session_state.target_points = int(df_coins.loc[user_row_idx, "target_points"]) if not df_coins.empty and len(df_coins) > user_row_idx and "target_points" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "target_points"]) else 200
    st.session_state.dino_lat = float(df_coins.loc[user_row_idx, "dino_lat"]) if not df_coins.empty and len(df_coins) > user_row_idx and "dino_lat" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "dino_lat"]) else 0.0
    st.session_state.dino_lon = float(df_coins.loc[user_row_idx, "dino_lon"]) if not df_coins.empty department else 0.0
    if not df_coins.empty and len(df_coins) > user_row_idx and "dino_lon" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "dino_lon"]):
        st.session_state.dino_lon = float(df_coins.loc[user_row_idx, "dino_lon"])
    st.session_state.quiz_correct_total = int(df_coins.loc[user_row_idx, "quiz_correct_total"]) if not df_coins.empty and len(df_coins) > user_row_idx and "quiz_correct_total" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "quiz_correct_total"]) else 0
    st.session_state.daily_quiz_count = int(df_coins.loc[user_row_idx, "daily_quiz_count"]) if not df_coins.empty and len(df_coins) > user_row_idx and "daily_quiz_count" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "daily_quiz_count"]) else 0
    st.session_state.last_quiz_date = str(df_coins.loc[user_row_idx, "last_quiz_date"]) if not df_coins.empty and len(df_coins) > user_row_idx and "last_quiz_date" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "last_quiz_date"]) else time.strftime("%Y-%m-%d")
    st.session_state.quiz_idx = int(df_coins.loc[user_row_idx, "quiz_idx"]) if not df_coins.empty and len(df_coins) > user_row_idx and "quiz_idx" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "quiz_idx"]) else 0
    timer_val = df_coins.loc[user_row_idx, "daily_timer_done"] if not df_coins.empty and len(df_coins) > user_row_idx and "daily_timer_done" in df_coins.columns else False
    st.session_state.daily_timer_done = True if str(timer_val).strip().upper() == "TRUE" else False

today_str = time.strftime("%Y-%m-%d")
if st.session_state.last_quiz_date != today_str:
    st.session_state.daily_quiz_count = 0
    st.session_state.daily_timer_done = False
    st.session_state.last_quiz_date = today_str

def sync_to_cloud():
    global df_coins, user_row_idx
    while len(df_coins) <= user_row_idx:
        new_row = {col: None for col in df_coins.columns}
        df_coins = pd.concat([df_coins, pd.DataFrame([new_row])], ignore_index=True)
    
    for col in df_coins.columns: df_coins[col] = df_coins[col].astype(object)
    if "使用者" in df_coins.columns: df_coins.loc[user_row_idx, "使用者"] = st.session_state.logged_in_user
        
    df_coins.loc[user_row_idx, "coins"] = int(st.session_state.coins)
    df_coins.loc[user_row_idx, "previous_count"] = 0
    df_coins.loc[user_row_idx, "target_points"] = int(st.session_state.target_points)
    df_coins.loc[user_row_idx, "dino_lat"] = float(st.session_state.dino_lat)
    df_coins.loc[user_row_idx, "dino_lon"] = float(st.session_state.dino_lon)
    df_coins.loc[user_row_idx, "quiz_correct_total"] = int(st.session_state.quiz_correct_total)
    df_coins.loc[user_row_idx, "daily_quiz_count"] = int(st.session_state.daily_quiz_count)
    df_coins.loc[user_row_idx, "last_quiz_date"] = str(st.session_state.last_quiz_date)
    df_coins.loc[user_row_idx, "daily_timer_done"] = "TRUE" if st.session_state.daily_timer_done else "FALSE"
    df_coins.loc[user_row_idx, "quiz_idx"] = int(st.session_state.quiz_idx)

    conn.update(worksheet=WS_COINS, data=df_coins)
    st.cache_data.clear()

# ==========================================
# 4. 側邊欄 UI & 里程碑與徽章鎖定
# ==========================================
badges_info = [(1000, "💎", "地球史守護者"), (700, "👑", "考古大師"), (400, "🦖", "暴龍尖牙"), (100, "🦕", "腕龍寶寶"), (10, "🥚", "恐龍蛋")]
current_badge = next((b for b in badges_info if st.session_state.quiz_correct_total >= b[0]), None)
badge_display = f"{current_badge[1]} {current_badge[2]}" if current_badge else "🔒 尚未解鎖徽章"

with st.sidebar:
    country_options = df_sites["國家"].unique() if "國家" in df_sites.columns else ["未知名國家"]
    selected_country = st.selectbox("🌍 任務地圖切換器：", country_options)

df_country_sites = pd.DataFrame()
if not df_sites.empty and "國家" in df_sites.columns:
    df_country_sites = df_sites[df_sites["國家"].astype(str).str.strip() == selected_country.strip()].copy()

df_active_sites = pd.DataFrame()
if not df_country_sites.empty:
    df_country_sites["站點順序"] = pd.to_numeric(df_country_sites.get("站點順序"), errors='coerce').fillna(999).astype(int)
    df_country_sites = df_country_sites.sort_values(by="站點順序")  
    df_country_sites["解鎖所需代幣"] = pd.to_numeric(df_country_sites.get("解鎖所需代幣"), errors='coerce').fillna(0).astype(int)
    df_country_sites["是否解鎖"] = df_country_sites["解鎖所需代幣"].apply(lambda x: st.session_state.coins >= x)
    
    current_unlocked = df_country_sites["是否解鎖"].sum()
    df_active_sites = df_country_sites[df_country_sites["是否解鎖"] == True].dropna(subset=['latitude', 'longitude'])

    if selected_country not in st.session_state.country_unlocked_counts:
        st.session_state.country_unlocked_counts[selected_country] = current_unlocked
    else:
        prev_unlocked = st.session_state.country_unlocked_counts[selected_country]
        if current_unlocked > prev_unlocked:
            st.session_state.just_unlocked = True
            st.session_state.audio_trigger = 'level_up'  
            st.session_state.country_unlocked_counts[selected_country] = current_unlocked

def safe_float(val, fallback=0.0):
    try: return float(val)
    except: return fallback
    
all_sites_coords = [[safe_float(r['latitude']), safe_float(r['longitude'])] for _, r in df_country_sites.iterrows()] if not df_country_sites.empty else []
unlocked_coords = [[safe_float(r['latitude']), safe_float(r['longitude'])] for _, r in df_active_sites.iterrows()] if not df_active_sites.empty else []

with st.sidebar:
    next_site_token = None
    if not df_country_sites.empty:
        locked_sites = df_country_sites[df_country_sites["解鎖所需代幣"] > st.session_state.coins]
        if not locked_sites.empty: next_site_token = int(locked_sites.iloc[0]["解鎖所需代幣"])

    target = st.session_state.target_points
    current = st.session_state.coins
    wish_costs = df_rewards["所需未來幣"].tolist() if not df_rewards.empty and "所需未來幣" in df_rewards.columns else []
    is_wish = target in wish_costs
    
    if not is_wish and next_site_token is not None:
        display_target = next_site_token
        target_label = "📍 下一站解鎖目標"
    elif not is_wish and next_site_token is None:
        display_target = current if current > 0 else 1
        target_label = "🎉 探險全境通關"
    else:
        display_target = target
        target_label = "🎯 願望兌換進度"

    if st.session_state.logged_in_user == "Ailey":
        st.markdown(f"## 🎒 {st.session_state.logged_in_user} 的探險裝備包")
        ratio = min(current / display_target, 1.0) if display_target > 0 else 0
        pct = int(ratio * 100)
        
        sidebar_html = (
            "<div class='coin-box'>"
            "<span style='font-size: 14px; font-weight: bold; color: #9ca3af;'>🪙 當前累積未來幣</span><br>"
            f"<span style='font-size: 34px; font-weight: bold; color: #fbbf24;'>{current} 枚</span>"
            "<hr style='border-top: 1px dashed #475569; margin: 15px 0;'>"
            f"<p style='color: #94a3b8; font-size: 13px; margin-bottom: 2px; text-align: left;'>{target_label}：{pct}%</p>"
            "<div class='wish-progress-bg'>"
            f"<div class='wish-progress-fill' style='width: {ratio*100}%;'></div>"
            "</div>"
            f"<p style='text-align: right; color: #fbbf24; font-size: 12px; margin-top: 2px;'>{current} / {display_target} 🪙</p>"
            "<hr style='border-top: 1px dashed #475569; margin: 15px 0;'>"
            "<span style='font-size: 14px; font-weight: bold; color: #9ca3af;'>🎖️ 當前取得徽章</span><br>"
            f"<span style='font-size: 18px; font-weight: bold; color: #3b82f6;'>{badge_display}</span>"
            "</div>"
        )
        st.markdown(sidebar_html, unsafe_allow_html=True)
    else:
        st.markdown("## ⚙️ 管理員中控艙")
        admin_html = (
            "<div class='admin-box'>"
            "<span style='font-size: 15px; font-weight: bold; color: #10b981;'>🔒 系統核心已解鎖</span><br>"
            "<p style='color: #94a3b8; font-size: 13px; margin-top: 5px; text-align: left;'>• 目前身分：系統總監 (Kelly)</p>"
            "<p style='color: #94a3b8; font-size: 13px; text-align: left;'>• 資料庫狀態：雙軌安全備份已就緒</p>"
            "</div>"
        )
        st.markdown(admin_html, unsafe_allow_html=True)
    
    st.markdown("<div class='sync-btn-container'>", unsafe_allow_html=True)
    if st.button("☁️ 儲存並同步至雲端"):
        sync_to_cloud()
        st.toast("✅ 所有進度已安全備份至 Google Sheets！", icon="☁️")
    st.markdown("</div>", unsafe_allow_html=True)

    # 🚪 安全登出按鈕 (點擊清除快取)
    st.markdown("<div class='logout-btn-container'>", unsafe_allow_html=True)
    if st.button("🚪 登出特派員系統", use_container_width=True):
        st.session_state.is_authenticated = False
        st.session_state.logged_in_user = None
        clear_keys = ['coins', 'target_points', 'dino_lat', 'dino_lon', 'quiz_correct_total', 'daily_quiz_count', 'quiz_idx', 'daily_timer_done', 'current_map_country', 'country_unlocked_counts', 'just_unlocked', 'trigger_map_animation']
        for k in clear_keys:
            if k in st.session_state: del st.session_state[k]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 🎯【前端更新】：重塑寫實重裝甲龍 SVG，分離肢體關節並注入前後交替踏步動畫
def generate_map_html(start_lat, start_lon, end_lat, end_lon, is_animating):
    bases_js_code = "".join([f"L.marker([{coord[0]}, {coord[1]}], {{icon: baseIcon}}).addTo(map);" for coord in unlocked_coords])
    
    walk_active_class = "walk-active" if is_animating else ""
    
    realistic_ankylosaurus_svg = f"""
    <svg class="{walk_active_class}" viewBox="0 0 160 80" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:100%;">
        <style>
            @keyframes swing-front {{ 0%, 100% {{ transform: rotate(-10deg); }} 50% {{ transform: rotate(15deg); }} }}
            @keyframes swing-back {{ 0%, 100% {{ transform: rotate(15deg); }} 50% {{ transform: rotate(-10deg); }} }}
            .walk-active .leg-fl {{ animation: swing-front 0.4s infinite ease-in-out; transform-origin: 52px 38px; }}
            .walk-active .leg-fr {{ animation: swing-back 0.4s infinite ease-in-out; transform-origin: 88px 38px; }}
            .walk-active .leg-bl {{ animation: swing-back 0.4s infinite ease-in-out; transform-origin: 42px 42px; }}
            .walk-active .leg-br {{ animation: swing-front 0.4s infinite ease-in-out; transform-origin: 98px 42px; }}
        </style>
        <path class="leg-bl" d="M35 42 Q30 58 36 64 Q42 64 43 54 Z" fill="#2d3319"/>
        <path class="leg-br" d="M92 42 Q86 58 92 64 Q98 64 99 54 Z" fill="#2d3319"/>
        <path class="leg-fl" d="M48 38 Q42 56 48 62 Q54 62 55 50 Z" fill="#464f26"/>
        <path class="leg-fr" d="M82 38 Q76 56 82 62 Q88 62 89 50 Z" fill="#464f26"/>
        <path d="M15 35 C10 32 5 36 3 40 C1 44 8 46 15 42 Z" fill="#1f2210"/>
        <path d="M15 42 Q35 42 45 38" fill="none" stroke="#353b1c" stroke-width="8" stroke-linecap="round"/>
        <ellipse cx="70" cy="35" rx="36" ry="18" fill="#464f26"/>
        <path d="M34 25 L24 16 L34 28 M48 20 L42 8 L50 22 M68 18 L68 4 L74 19 M88 20 L94 8 L92 22 M102 25 L112 16 L104 28" stroke="#71644d" stroke-width="3" fill="none"/>
        <path d="M106 35 Q125 32 132 38 Q125 46 106 43 Z" fill="#353b1c"/>
        <circle cx="124" cy="36" r="2" fill="#000"/>
    </svg>
    """
    
    is_anim_str = "true" if is_animating else "false"
    
    leaflet_html = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div id="map" style="width: 100%; height: 450px; border-radius: 15px; border: 3px solid #475569;"></div>
    <script>
        var map = L.map('map', {{ zoomControl: false }}).setView([{start_lat}, {start_lon}], 7);
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);
        var baseIcon = L.divIcon({{ html: '<div style=\"font-size: 13px; line-height: 1;\">🔵</div>', className: 'custom-base-marker', iconSize: [13, 13], iconAnchor: [6.5, 6.5] }});
        {bases_js_code}
        var allCoords = {str(all_sites_coords)};
        if(allCoords.length > 0) {{ L.polyline(allCoords, {{color: '#94a3b8', dashArray: '5, 10', weight: 3}}).addTo(map); }}
        var unlockedCoords = {str(unlocked_coords)};
        if(unlockedCoords.length > 0) {{ L.polyline(unlockedCoords, {{color: '#3b82f6', weight: 5}}).addTo(map); }}

        var ankyloIcon = L.divIcon({{ html: `{realistic_ankylosaurus_svg}`, className: 'custom-dino-layer', iconSize: [110, 55], iconAnchor: [55, 27] }});
        var dinoMarker = L.marker([{start_lat}, {start_lon}], {{icon: ankyloIcon, zIndexOffset: 1000}}).addTo(map);
        
        if ({is_anim_str}) {{
            setTimeout(function() {{ 
                dinoMarker.setLatLng([{end_lat}, {end_lon}]); 
                map.panTo([{end_lat}, {end_lon}], {{animate: true, duration: 2.5}}); 
            }}, 800);
        }} else {{
            dinoMarker.setLatLng([{end_lat}, {end_lon}]); map.setView([{end_lat}, {end_lon}], 6);
        }}
    </script>
    """
    return leaflet_html

# ==========================================
# 5. 全螢幕強制慶祝攔截系統
# ==========================================
if st.session_state.just_unlocked:
    st.balloons()
    st.markdown("""
    <div style="background: linear-gradient(90deg, #10b981, #059669); padding: 25px; border-radius: 12px; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 15px rgba(16,185,129,0.4); border: 3px solid #34d399;">
        <h2 style="margin: 0; font-size: 36px;">🎉 金幣達標！新考古站點已解鎖！</h2>
        <p style="margin: 10px 0 0 0; font-size: 20px; font-weight: bold;">重裝甲龍肢體踏步已啟動，正在全速向新營地推進中：</p>
    </div>
    """, unsafe_allow_html=True)
    
    if len(unlocked_coords) > 1: s_lat, s_lon = unlocked_coords[-2][0], unlocked_coords[-2][1]
    elif len(all_sites_coords) > 0: s_lat, s_lon = all_sites_coords[0][0] - 1.0, all_sites_coords[0][1] - 1.0
    else: s_lat, s_lon = -27.4698, 153.0251
        
    e_lat, e_lon = unlocked_coords[-1][0], unlocked_coords[-1][1] if len(unlocked_coords) > 0 else (s_lat, s_lon)
    html_map = generate_map_html(s_lat, s_lon, e_lat, e_lon, True)
    st.components.v1.html(html_map, height=500)
    
    if st.button("✅ 我看完了！抵達新營地並繼續探險", use_container_width=True):
        st.session_state.just_unlocked = False
        st.rerun()

else:
    # ==========================================
    # 6. 主畫面動態分頁系統 
    # ==========================================
    if st.session_state.logged_in_user == "Kelly":
        tab_list = [f"🗺️ {selected_country} 大富翁", "📅 今日任務", "📚 學習基地", "🎁 願望兌換", "🦖 知識挑戰", "⚙️ 媽媽後台"]
        all_tabs = st.tabs(tab_list)
        tab1, tab2, tab3, tab4, tab5, tab6 = all_tabs
    else:
        tab_list = [f"🗺️ {selected_country} 大富翁", "📅 今日任務", "📚 學習基地", "🎁 願望兌換", "🦖 知識挑戰"]
        all_tabs = st.tabs(tab_list)
        tab1, tab2, tab3, tab4, tab5 = all_tabs
        tab6 = None 

    # ------------------------------------------
    # Tab 1: 大富翁
    # ------------------------------------------
    with tab1:
        st.markdown("""
        <div style="background-color: #f0fdf4; padding: 15px; border-left: 6px solid #4ade80; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="color: #166534; margin-top: 0;">🦕 特派員報到：寫實重裝甲龍出動！</h4>
            <p style="color: #14532d; font-size: 16px; margin-bottom: 0; font-weight: 500;">
            帶上妳的裝備！這隻加寬了防禦刺突與厚重尾槌的甲龍，現在在移動時四隻腳會前後交替擺動踏步囉！一起出發探索史前航線吧！
            </p>
        </div>
        """, unsafe_allow_html=True)

        if df_country_sites.empty:
            st.error(f"⚠️ {selected_country} 尚未建立站點資料，請至媽媽後台新增吧。")
        else:
            if st.button("🚁 手動重播：甲龍步行關節動畫"):
                st.session_state.trigger_map_animation = True
                st.rerun()

            target_lat, target_lon = -27.4698, 153.0251
            if len(unlocked_coords) > 0: target_lat, target_lon = unlocked_coords[-1][0], unlocked_coords[-1][1]
            elif len(all_sites_coords) > 0: target_lat, target_lon = all_sites_coords[0][0], all_sites_coords[0][1]

            if st.session_state.current_map_country != selected_country:
                st.session_state.dino_lat, st.session_state.dino_lon = target_lat, target_lon
                st.session_state.current_map_country = selected_country
                st.session_state.trigger_map_animation = False

            start_lat, start_lon = st.session_state.dino_lat, st.session_state.dino_lon
            
            if st.session_state.trigger_map_animation:
                if len(unlocked_coords) > 1: start_lat, start_lon = unlocked_coords[-2][0], unlocked_coords[-2][1]
                elif len(all_sites_coords) > 0: start_lat, start_lon = all_sites_coords[0][0] - 1.0, all_sites_coords[0][1] - 1.0
                st.session_state.dino_lat, st.session_state.dino_lon = target_lat, target_lon
            
            is_animating = st.session_state.trigger_map_animation
            html_map = generate_map_html(start_lat, start_lon, target_lat, target_lon, is_animating)
            st.components.v1.html(leaflet_html=html_map, height=450)
            
            if st.session_state.trigger_map_animation: st.session_state.trigger_map_animation = False

            st.subheader(f"📍 {selected_country} 探險進度")
            cols_per_row = 5
            rows = [df_country_sites.iloc[i:i+cols_per_row] for i in range(0, len(df_country_sites), cols_per_row)]
            for r_df in rows:
                site_cols = st.columns(cols_per_row)
                for idx, (_, row) in enumerate(r_df.iterrows()):
                    with site_cols[idx]:
                        s_name, s_order, s_token = row.get('站點名稱', '未命名'), row.get('站點順序', idx+1), row.get('解鎖所需代幣', 0)
                        if row.get("是否解鎖", False): st.markdown(f"""<div class='game-node-unlocked'><span style='font-size:24px;'>🦖</span><br><strong style='color:#60a5fa;'>第 {s_order} 站</strong><br><strong>{s_name}</strong></div>""", unsafe_allow_html=True)
                        else: st.markdown(f"""<div class='game-node-locked'><span style='font-size:24px;'>🔒</span><br><span>第 {s_order} 站</span><br><span>{s_name}</span><br><span style='font-size:11px;'>再收集 {int(s_token - st.session_state.coins)} 🪙</span></div>""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

    # ------------------------------------------
    # Tab 2: 📅 今日任務 (無限次當次結算 & 純前端 JS 計時器)
    # ------------------------------------------
    with tab2:
        st.info("💡 貼心提示：今天不設學習上限！每次完成都可以立刻點擊結算，結算後數量將「自動歸零」，方便下一次學習繼續累積！")
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📝 單位數量提交區")
            # 初始化暫存控制變數
            for i in range(6):
                if f"task_amt_{i}" not in st.session_state: st.session_state[f"task_amt_{i}"] = 0

            # 🎯【防呆升級】：限制只能使用上下箭頭增減級距數量
            u1 = st.number_input("1. App單字闖關次數 (每 15 分鐘 = 1 幣)", min_value=0, step=1, key="task_amt_0")
            u2 = st.number_input("2. 英文教學影片看過次數 (每 15 分鐘 = 1 幣)", min_value=0, step=1, key="task_amt_1")
            u3 = st.number_input("3. 英文教學教材完成集數 (每 1 集 = 1 幣)", min_value=0, step=1, key="task_amt_2")
            u4 = st.number_input("4. 英文認証單字表背熟個數 (每熟背 10 個 = 1 幣)", min_value=0, step=10, key="task_amt_3")
            u5 = st.number_input("5. 作業或評量沒有跳題次數 (每 1 次 = 1 幣)", min_value=0, step=1, key="task_amt_4")
            u6 = st.number_input("6. 作業或評量全對次數 (每 1 次 = 1 幣)", min_value=0, step=1, key="task_amt_5")

            if st.button("✅ 立即結算當次累積未來幣"):
                earned = u1 + u2 + u3 + (u4 // 10) + u5 + u6
                if earned > 0:
                    st.session_state.coins += earned
                    st.session_state.audio_trigger = 'coin'
                    # 瞬間歸零，釋放狀態鎖
                    for i in range(6): st.session_state[f"task_amt_{i}"] = 0
                    sync_to_cloud()
                    st.toast(f"🪙 結算成功！加碼進帳 {earned} 枚未來幣！", icon="🎉")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("⚠️ 妳這次尚未調整任何任務單位的個數喔！")
                    
        with col2:
            st.markdown("""
            <div class="magic-timer-box">
                <h3 style="color: #854d0e; margin-top:0;">⏳ 網頁級防休眠魔法沙漏</h3>
                <p style="color: #a16207; font-size: 14px; font-weight: bold;">內建 WakeLock 防護罩，不受螢幕保護程式阻擋！滿 15 分鐘將強制跳出原生提示視窗並播放警報！</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.daily_timer_done:
                st.success("✅ 今天的魔法專注挑戰已經大功告成囉！")
            else:
                # 🎯【硬體升級】：使用純前端 JS 定時器，調用 Wake Lock 阻止睡眠，過期強制 Native Alert 彈窗
                js_timer_html = """
                <div id="timer-display" style="text-align:center; font-size:42px; font-weight:bold; color:#ef4444; background:#1e293b; padding:15px; border-radius:10px; border:2px solid #ef4444;">
                    ⏳ 魔法沙漏已就緒
                </div>
                <button id="start-btn" style="width:100%; margin-top:10px; font-size:20px; padding:12px; background:#ef4444; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">
                    🚀 啟動防睡死魔法沙漏
                </button>

                <script>
                    let lockToken = null;
                    let clockSeconds = 15 * 60;
                    let displayBox = document.getElementById("timer-display");
                    let actionBtn = document.getElementById("start-btn");

                    async function requestScreenLock() {
                        try {
                            if ('wakeLock' in navigator) {
                                lockToken = await navigator.wakeLock.request('screen');
                            }
                        } catch (e) { console.log("WakeLock Lock Failed."); }
                    }

                    actionBtn.addEventListener("click", () => {
                        actionBtn.disabled = true;
                        actionBtn.style.background = "#475569";
                        actionBtn.innerText = "🔒 防休眠保護中...";
                        requestScreenLock();

                        let loop = setInterval(() => {
                            clockSeconds--;
                            let m = Math.floor(clockSeconds / 60);
                            let s = clockSeconds % 60;
                            displayBox.innerText = "⏳ 剩餘 " + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);

                            if (clockSeconds <= 0) {
                                clearInterval(loop);
                                if (lockToken !== null) lockToken.release();
                                
                                // 原生音訊合成嗶嗶聲
                                try {
                                    let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                                    let osc = audioCtx.createOscillator();
                                    osc.type = "sine"; osc.frequency.setValueAtTime(880, audioCtx.currentTime);
                                    osc.connect(audioCtx.destination); osc.start(); setTimeout(() => osc.stop(), 1000);
                                } catch(e){}

                                // 原生系統級最高優先權強制攔截彈窗
                                alert("⏳ 時間到了！專注完成！1 枚未來幣已成功召喚！");
                                
                                // 信號反向傳回後端管線
                                const url = new URL(window.parent.location.href);
                                url.searchParams.set("magic_timer_done", "true");
                                window.parent.location.href = url.href;
                            }
                        }, 1000);
                    });
                </script>
                """
                st.components.v1.html(js_timer_html, height=160)

    # ------------------------------------------
    # Tab 3: 📚 學習基地
    # ------------------------------------------
    with tab3:
        if not df_resources.empty:
            for idx, row in df_resources.iterrows():
                r_done = 0.0 if pd.isna(row.get('已完成集數')) else float(row.get('已完成集數'))
                r_total = 1.0 if pd.isna(row.get('總集數')) else float(row.get('總集數'))
                r_total = max(r_total, 1.0)
                
                st.markdown(f"<div class='resource-card'><span style='font-size:12px; color:#94a3b8;'>{str(row.get('分類','其他'))}</span><br><strong style='font-size:18px;'>📖 {str(row.get('名稱','未命名'))}</strong><br><a href='{str(row.get('網址','#'))}' target='_blank' style='color:#60a5fa;'>🔗 官方傳送門</a></div>", unsafe_allow_html=True)
                c_col1, c_col2, c_col3 = st.columns([2, 1, 1])
                with c_col1: st.progress(min(max(r_done / r_total, 0.0), 1.0))
                with c_col2: st.write(f"📈 {int(r_done)} / {int(r_total)} 集")
                with c_col3:
                    if st.button(f"➕ 第 {int(r_done) + 1} 集", key=f"inc_{idx}") and r_done < r_total:
                        df_resources.loc[idx, "已完成集數"] = r_done + 1
                        conn.update(worksheet=WS_RESOURCES, data=df_resources)
                        st.cache_data.clear(); st.rerun()
                st.markdown("---")

    # ------------------------------------------
    # Tab 4: 🎁 願望兌換 (完全動態資料編輯驅動)
    # ------------------------------------------
    with tab4:
        st.markdown("## 🎁 願望兌換所")
        st.info("💡 挑選一個妳最想要的禮物，按下「設定為目標」，側邊欄就會出現專屬進度條喔！")
        
        if not df_rewards.empty and "獎勵名稱" in df_rewards.columns:
            for idx, row in df_rewards.iterrows():
                r_name = row.get("獎勵名稱", "未命名")
                r_cost = 0 if pd.isna(row.get("所需未來幣")) else int(float(row.get("所需未來幣")))
                
                with st.container():
                    st.markdown(f"<div style='background-color:#1e293b; padding:20px; border-radius:10px; border-left:5px solid #f59e0b; margin-bottom:15px;'><h3 style='color:#fcd34d; margin-top:0;'>{r_name}</h3><p style='color:#94a3b8; font-size:16px;'>所需花費：<strong style='color:#fbbf24; font-size:20px;'>{r_cost} 🪙</strong></p></div>", unsafe_allow_html=True)
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.session_state.target_points == r_cost:
                            if st.button("❌ 取消鎖定", key=f"unlock_{idx}"):
                                st.session_state.target_points = 200
                                sync_to_cloud(); st.toast("已取消願望鎖定！", icon="🔓"); st.rerun()
                        else:
                            if st.button("🎯 設定為目標", key=f"set_{idx}"):
                                st.session_state.target_points = r_cost
                                sync_to_cloud(); st.toast(f"已鎖定新目標：{r_name}！", icon="🎯"); st.rerun()
                                
                    with col_btn2:
                        if st.session_state.target_points == r_cost:
                            if st.session_state.coins >= r_cost:
                                if st.button(f"🎉 立即花費 {r_cost} 幣兌換！", key=f"redeem_{idx}"):
                                    st.session_state.coins -= r_cost
                                    st.session_state.target_points = 200 
                                    st.session_state.audio_trigger = 'level_up'
                                    sync_to_cloud(); st.balloons()
                                    st.success(f"兌換成功！請馬上截圖找媽媽領取：【{r_name}】")
                                    time.sleep(2); st.rerun()
                            else:
                                st.button("🔒 金幣還不夠喔", key=f"short_{idx}", disabled=True)
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.warning("目前後台尚未設定任何願望清單喔。")

    # ------------------------------------------
    # Tab 5: 🦖 知識挑戰
    # ------------------------------------------
    with tab5:
        if current_badge: st.markdown(f"### 🎖️ 目前階級：{badge_display} (答對 {st.session_state.quiz_correct_total} 題)")
        if st.session_state.daily_quiz_count >= 10:
            st.warning("⏳ 今天的體力用完囉，明天再來喔！")
        else:
            q_progress = min(max(st.session_state.daily_quiz_count / 10.0, 0.0), 1.0)
            st.progress(q_progress)
            
            if st.session_state.quiz_idx < len(df_quiz):
                current_q = df_quiz.iloc[st.session_state.quiz_idx]
                raw_q = str(current_q.get('題目', ''))
                display_question = "（⚠️ 題目漏失，請至後台確認）" if raw_q.strip() in ['nan','None',''] else raw_q
                options = [str(current_q.get(col)) for col in ['選項A', '選項B', '選項C', '選項D'] if pd.notna(current_q.get(col)) and stroke(current_q.get(col)) != 'nan']
                
                st.markdown(f"#### ❓ 全球恐龍大百科第 {st.session_state.quiz_idx + 1} 題：{display_question}")
                user_ans = st.empty().radio("請選擇答案：", options, key=f"q_{st.session_state.quiz_idx}")
                
                if st.button("🚀 瞬間送出答案"):
                    st.session_state.daily_quiz_count += 1
                    if str(user_ans).strip() == str(current_q["正確答案"]).strip():
                        st.session_state.quiz_correct_total += 1; st.session_state.audio_trigger = 'correct'; st.session_state.quiz_idx += 1
                        st.toast("🎉 答對了！", icon="✅")
                    else:
                        st.session_state.audio_trigger = 'wrong'; st.toast("❌ 答錯囉！", icon="❌")
                    if st.session_state.daily_quiz_count == 10: sync_to_cloud()
                    time.sleep(0.5); st.rerun()
            else: st.success("🏆 全數通關！請通知媽媽擴充題目吧！")

    # ------------------------------------------
    # Tab 6: ⚙️ 媽媽後台 (資料與安全性雙軌鎖定)
    # ------------------------------------------
    if tab6 is not None:
        with tab6:
            input_coins = st.number_input("手動調節未來幣：", min_value=0, value=st.session_state.coins, step=1)
            if input_coins != st.session_state.coins:
                st.session_state.coins = input_coins; sync_to_cloud(); st.toast(f"幣值已更新！", icon="☁️")
                
            st.markdown("---")
            st.markdown("### 🎁 雲端願望兌換所編輯器 (rewards)")
            edited_rewards_df = st.data_editor(df_rewards, use_container_width=True, num_rows="dynamic", key="rewards_editor")
            if st.button("💾 儲存並覆寫願望清單"): 
                conn.update(worksheet=WS_REWARDS, data=edited_rewards_df); st.cache_data.clear(); st.toast("🎉 願望清單已同步覆寫！", icon="✅")

            st.markdown("---")
            st.markdown("### 🗺️ 雲端地圖站點預覽 (sites 唯讀鎖定)")
            st.info("💡 為了避免格式錯誤，地圖站點已被安全鎖定。請直接前往 Google Sheets 資料庫的 `sites` 分頁進行維護。")
            st.dataframe(df_sites, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("### 📚 雲端學習資源編輯器 (resources)")
            edited_resources_df = st.data_editor(df_resources, use_container_width=True, num_rows="dynamic", key="resources_editor")
            if st.button("💾 儲存並覆寫資源"): conn.update(worksheet=WS_RESOURCES, data=edited_resources_df); st.cache_data.clear(); st.toast("🎉 資源已覆寫！", icon="✅")
            
            st.markdown("---")
            st.markdown("### 🏆 雲端里程碑即時編輯器 (milestones)")
            edited_milestones_df = st.data_editor(df_milestones, use_container_width=True, num_rows="dynamic", key="milestones_editor")
            if st.button("💾 儲存並覆寫里程碑"): conn.update(worksheet=WS_MILESTONES, data=edited_milestones_df); st.cache_data.clear(); st.toast("🎉 里程碑已覆寫！", icon="✅")

            st.markdown("---")
            st.markdown("### 🦖 雲端雙語題庫即時編輯器 (quiz)")
            edited_quiz_df = st.data_editor(df_quiz, use_container_width=True, num_rows="dynamic", key="quiz_editor")
            if st.button("💾 儲存並覆寫題庫"): conn.update(worksheet=WS_QUIZ, data=edited_quiz_df); st.cache_data.clear(); st.toast("🎉 題庫已覆寫！", icon="✅")

# ==========================================
# 8. 全域音效引導引擎
# ==========================================
def load_audio_b64(file_name):
    if os.path.exists(file_name):
        with open(file_name, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

if st.session_state.audio_trigger:
    target_file = f"{st.session_state.audio_trigger}.mp3"
    b64_audio = load_audio_b64(target_file)
    if b64_audio: st.components.v1.html(f'<script>var a = new Audio("data:audio/mp3;base64,{b64_audio}"); a.play();</script>', height=0)
    st.session_state.audio_trigger = None
