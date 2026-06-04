import streamlit as st
import pandas as pd
import time
import os
import base64
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 0. 環境變數切換開關 (全自動偵測版)
# ==========================================
if os.name == 'nt': ENVIRONMENT = "DEV"
else: ENVIRONMENT = "PROD"

SUFFIX = "_dev" if ENVIRONMENT == "DEV" else ""
WS_COINS = f"coins{SUFFIX}"
WS_SITES = f"sites{SUFFIX}"
WS_RESOURCES = f"resources{SUFFIX}"
WS_QUIZ = f"quiz{SUFFIX}"
WS_MILESTONES = f"milestones{SUFFIX}"
WS_REWARDS = f"rewards{SUFFIX}" # 🎯 新增願望兌換管線

# ==========================================
# 1. 網頁基本設定 & 護眼暗黑模式 CSS
# ==========================================
st.set_page_config(
    page_title=f"🦖 恐龍特派員 ({ENVIRONMENT} 模式)",
    page_icon="🦖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .coin-box { background-color: #1e293b; border-radius: 15px; padding: 15px; border: 2px dashed #f59e0b; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .game-node-unlocked { background: linear-gradient(145deg, #1e3a8a, #172554); border: 2px solid #3b82f6; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.4); height: 100%; color: #eff6ff; }
    .game-node-locked { background: #0f172a; border: 2px dashed #475569; border-radius: 12px; padding: 15px; text-align: center; color: #94a3b8; height: 100%; }
    .resource-card { background-color: #1e293b; border-left: 5px solid #3b82f6; padding: 15px; margin-bottom: 10px; border-radius: 6px; color: #f8fafc; }
    div[data-testid="stButton"] button { width: 100% !important; font-size: 26px !important; padding: 20px !important; background: linear-gradient(135deg, #e11d48 0%, #9f1239 100%) !important; color: white !important; font-weight: 900 !important; border-radius: 15px !important; border: 2px solid #fda4af !important; box-shadow: 0px 8px 15px rgba(225,29,72,0.4) !important; letter-spacing: 1px; }
    div[data-testid="stButton"] button:hover { background: linear-gradient(135deg, #f43f5e 0%, #be123c 100%) !important; color: white !important; }
    .sync-btn-container div[data-testid="stButton"] button { background: linear-gradient(135deg, #059669 0%, #047857 100%) !important; border: 2px solid #34d399 !important; font-size: 22px !important; }
    .magic-timer-box { background: linear-gradient(135deg, #fef08a 0%, #fde047 100%); padding: 20px; border-radius: 15px; text-align: center; border: 3px dashed #ca8a04; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 15px; }
    .wish-progress-bg { background: #334155; border-radius: 10px; width: 100%; height: 20px; position: relative; margin: 10px 0; }
    .wish-progress-fill { background: linear-gradient(90deg, #3b82f6, #60a5fa); height: 100%; border-radius: 10px; transition: width 0.5s; }
</style>
""", unsafe_allow_html=True)

if 'audio_trigger' not in st.session_state:
    st.session_state.audio_trigger = None

# ==========================================
# 2. 雲端資料庫讀寫模組 (含自動建表防護)
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

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
    except:
        data["rewards"] = pd.DataFrame([{"獎勵名稱": "去遊樂園玩", "所需未來幣": 200}, {"獎勵名稱": "買新玩具", "所需未來幣": 100}])
    return data

data_store = load_cloud_data_store()
df_coins = data_store["coins"]
df_sites = data_store["sites"]
df_resources = data_store["resources"]
df_quiz = data_store["quiz"]
df_milestones = data_store["milestones"]
df_rewards = data_store["rewards"]

# 👤 【新增】：帳號初始化設定
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = "Ailey"

if 'current_map_country' not in st.session_state: st.session_state.current_map_country = None
if 'country_unlocked_counts' not in st.session_state: st.session_state.country_unlocked_counts = {}

# 🎯 【架構升級】：動態計算當前登入特派員的雲端資料列索引
user_row_idx = 0 if st.session_state.logged_in_user == "Ailey" else 1
if not df_coins.empty and "使用者" in df_coins.columns:
    user_rows = df_coins[df_coins["使用者"] == st.session_state.logged_in_user]
    if not user_rows.empty:
        user_row_idx = user_rows.index[0]

# 🎯 依據登入帳號載入獨立進度
if 'coins' not in st.session_state:
    st.session_state.coins = int(df_coins.loc[user_row_idx, "coins"]) if not df_coins.empty and len(df_coins) > user_row_idx and "coins" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "coins"]) else 0
    st.session_state.target_points = int(df_coins.loc[user_row_idx, "target_points"]) if not df_coins.empty and len(df_coins) > user_row_idx and "target_points" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "target_points"]) else 200
    st.session_state.dino_lat = float(df_coins.loc[user_row_idx, "dino_lat"]) if not df_coins.empty and len(df_coins) > user_row_idx and "dino_lat" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "dino_lat"]) else 0.0
    st.session_state.dino_lon = float(df_coins.loc[user_row_idx, "dino_lon"]) if not df_coins.empty and len(df_coins) > user_row_idx and "dino_lon" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "dino_lon"]) else 0.0
    st.session_state.quiz_correct_total = int(df_coins.loc[user_row_idx, "quiz_correct_total"]) if not df_coins.empty and len(df_coins) > user_row_idx and "quiz_correct_total" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "quiz_correct_total"]) else 0
    st.session_state.daily_quiz_count = int(df_coins.loc[user_row_idx, "daily_quiz_count"]) if not df_coins.empty and len(df_coins) > user_row_idx and "daily_quiz_count" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "daily_quiz_count"]) else 0
    st.session_state.last_quiz_date = str(df_coins.loc[user_row_idx, "last_quiz_date"]) if not df_coins.empty and len(df_coins) > user_row_idx and "last_quiz_date" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "last_quiz_date"]) else time.strftime("%Y-%m-%d")
    st.session_state.quiz_idx = int(df_coins.loc[user_row_idx, "quiz_idx"]) if not df_coins.empty and len(df_coins) > user_row_idx and "quiz_idx" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "quiz_idx"]) else 0
    st.session_state.daily_timer_done = bool(df_coins.loc[user_row_idx, "daily_timer_done"]) if not df_coins.empty and len(df_coins) > user_row_idx and "daily_timer_done" in df_coins.columns and pd.notna(df_coins.loc[user_row_idx, "daily_timer_done"]) else False
    st.session_state.just_unlocked = False
    st.session_state.trigger_map_animation = False
    st.session_state.completed_countries = []
    st.session_state.just_completed_country = None
    
today_str = time.strftime("%Y-%m-%d")
if st.session_state.last_quiz_date != today_str:
    st.session_state.daily_quiz_count = 0
    st.session_state.daily_timer_done = False
    st.session_state.last_quiz_date = today_str
    for key in list(st.session_state.keys()):
        if key.startswith("task_locked_"): del st.session_state[key]

# 🎯 【重要修復】：多帳號安全同步機制，防止覆蓋另一個使用者的儲存格
def sync_to_cloud():
    global df_coins
    # 確保資料表長度足夠支援該索引列
    while len(df_coins) <= user_row_idx:
        new_row = {col: None for col in df_coins.columns}
        df_coins = pd.concat([df_coins, pd.DataFrame([new_row])], ignore_index=True)
        
    if "使用者" in df_coins.columns:
        df_coins.loc[user_row_idx, "使用者"] = st.session_state.logged_in_user
        
    df_coins.loc[user_row_idx, "coins"] = st.session_state.coins
    df_coins.loc[user_row_idx, "previous_count"] = 0
    df_coins.loc[user_row_idx, "target_points"] = st.session_state.target_points
    df_coins.loc[user_row_idx, "dino_lat"] = st.session_state.dino_lat
    df_coins.loc[user_row_idx, "dino_lon"] = st.session_state.dino_lon
    df_coins.loc[user_row_idx, "quiz_correct_total"] = st.session_state.quiz_correct_total
    df_coins.loc[user_row_idx, "daily_quiz_count"] = st.session_state.daily_quiz_count
    df_coins.loc[user_row_idx, "last_quiz_date"] = st.session_state.last_quiz_date
    df_coins.loc[user_row_idx, "quiz_idx"] = st.session_state.quiz_idx
    df_coins.loc[user_row_idx, "daily_timer_done"] = st.session_state.daily_timer_done

    conn.update(worksheet=WS_COINS, data=df_coins)
    st.cache_data.clear()

# ==========================================
# 3. 側邊欄總主控台 (含帳號登入切換器)
# ==========================================
badges_info = [(1000, "💎", "地球史守護者"), (700, "👑", "考古大師"), (400, "🦖", "暴龍尖牙"), (100, "🦕", "腕龍寶寶"), (10, "🥚", "恐龍蛋")]
current_badge = next((b for b in badges_info if st.session_state.quiz_correct_total >= b[0]), None)
badge_display = f"{current_badge[1]} {current_badge[2]}" if current_badge else "🔒 尚未解鎖徽章"

with st.sidebar:
    st.warning(f"⚡ 目前運行模式：{ENVIRONMENT}")
    
    # 👤 【新增】：常駐頂部的特派員登入切換功能
    selected_user = st.selectbox("👤 切換特派員帳號：", ["Ailey", "Kelly"], index=0 if st.session_state.logged_in_user == "Ailey" else 1)
    if selected_user != st.session_state.logged_in_user:
        st.session_state.logged_in_user = selected_user
        # 帳號切換時，深度重置專屬記憶體防污染
        clear_keys = ['coins', 'target_points', 'dino_lat', 'dino_lon', 'quiz_correct_total', 'daily_quiz_count', 'quiz_idx', 'daily_timer_done', 'current_map_country', 'country_unlocked_counts']
        for k in clear_keys:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

    st.markdown(f"## 🎒 {st.session_state.logged_in_user} 的探險裝備包")
    
    # 🎯 願望進度條 UI
    target = st.session_state.target_points
    current = st.session_state.coins
    ratio = min(current / target, 1.0) if target > 0 else 0
    pct = int(ratio * 100)
    
    # 🛡️ 完美的單行拼接防程式碼外顯技術
    sidebar_html = (
        "<div class='coin-box'>"
        "<span style='font-size: 14px; font-weight: bold; color: #9ca3af;'>🪙 當前累積未來幣</span><br>"
        f"<span style='font-size: 34px; font-weight: bold; color: #fbbf24;'>{current} 枚</span>"
        "<hr style='border-top: 1px dashed #475569; margin: 15px 0;'>"
        f"<p style='color: #94a3b8; font-size: 13px; margin-bottom: 2px; text-align: left;'>🎯 當前願望進度：{pct}%</p>"
        "<div class='wish-progress-bg'>"
        f"<div class='wish-progress-fill' style='width: {ratio*100}%;'></div>"
        "</div>"
        f"<p style='text-align: right; color: #fbbf24; font-size: 12px; margin-top: 2px;'>{current} / {target} 🪙</p>"
        "<hr style='border-top: 1px dashed #475569; margin: 15px 0;'>"
        "<span style='font-size: 14px; font-weight: bold; color: #9ca3af;'>🎖️ 當前取得徽章</span><br>"
        f"<span style='font-size: 18px; font-weight: bold; color: #3b82f6;'>{badge_display}</span>"
        "</div>"
    )
    st.markdown(sidebar_html, unsafe_allow_html=True)
    
    st.markdown("<div class='sync-btn-container'>", unsafe_allow_html=True)
    if st.button("☁️ 儲存並同步至雲端"):
        sync_to_cloud()
        st.toast("✅ 所有進度已安全備份至 Google Sheets！", icon="☁️")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    country_options = df_sites["國家"].unique() if "國家" in df_sites.columns else ["未知名國家"]
    selected_country = st.selectbox("🌍 任務地圖切換器：", country_options)

# ==========================================
# 4. 主畫面分頁系統
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([f"🗺️ {selected_country} 大富翁", "📅 今日任務", "📚 學習基地", "🎁 願望兌換", "🦖 知識挑戰", "⚙️ 媽媽後台"])

# ------------------------------------------
# Tab 1: 大富翁
# ------------------------------------------
with tab1:
    st.markdown("""
    <div style="background-color: #f0fdf4; padding: 15px; border-left: 6px solid #4ade80; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h4 style="color: #166534; margin-top: 0;">🦕 特派員報到：甲龍出動！</h4>
        <p style="color: #14532d; font-size: 16px; margin-bottom: 0; font-weight: 500;">
        準備好了嗎？帶上妳的裝備！這隻擁有超強綠色背甲和無敵尾錘的甲龍小夥伴，已經迫不及待要跟妳一起出發，敲開下一個神秘考古基地的大門囉！
        </p>
    </div>
    """, unsafe_allow_html=True)

    df_country_sites = df_sites[df_sites.get("國家", "") == selected_country].copy()
    if df_country_sites.empty:
        st.error(f"⚠️ {selected_country} 尚未建立站點資料，請至媽媽後台新增吧。")
    else:
        df_country_sites["解鎖所需代幣"] = pd.to_numeric(df_country_sites.get("解鎖所需代幣"), errors='coerce').fillna(0).astype(int)
        df_country_sites["站點順序"] = pd.to_numeric(df_country_sites.get("站點順序"), errors='coerce').fillna(1).astype(int)
        df_country_sites["是否解鎖"] = df_country_sites["解鎖所需代幣"].apply(lambda x: st.session_state.coins >= x)
        
        current_country_unlocked = df_country_sites["是否解鎖"].sum()
        total_country_sites = len(df_country_sites)
        prev_country_unlocked = st.session_state.country_unlocked_counts.get(selected_country, current_country_unlocked)

        if current_country_unlocked > prev_country_unlocked:
            st.session_state.just_unlocked = True
            st.session_state.audio_trigger = 'level_up' 
            st.session_state.country_unlocked_counts[selected_country] = current_country_unlocked
            if current_country_unlocked == total_country_sites and selected_country not in st.session_state.completed_countries:
                st.session_state.completed_countries.append(selected_country)
                st.session_state.just_completed_country = selected_country
            else: st.session_state.just_completed_country = None

        if st.session_state.just_unlocked:
            st.balloons()
            if st.session_state.just_completed_country:
                st.markdown(f"""<div class="epic-congratulations"><h1 style="color: #fca5a5; font-size: 48px; margin: 0;">🎉 史詩級通關！【{selected_country}】全境解鎖！ 🎉</h1><p style="color: #e0e7ff; font-size: 24px;">太不可思議了！妳的 🪙 {st.session_state.coins} 枚未來幣，找齊了所有的史前碎片！</p></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="epic-congratulations"><h1 style="color: #fca5a5; font-size: 48px; margin: 0;">🎉 LEVEL UP! 新基地解鎖！ 🎉</h1><p style="color: #e0e7ff; font-size: 24px;">太厲害了！妳目前累積的 🪙 {st.session_state.coins} 枚未來幣，點亮了新基地！</p></div>""", unsafe_allow_html=True)
            if st.button("🦖 帶領甲龍小夥伴出發到下一站吧 ➔"):
                st.session_state.just_unlocked = False
                st.session_state.trigger_map_animation = True 
                st.session_state.just_completed_country = None
                st.rerun()

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

        df_active_sites = df_country_sites[df_country_sites["是否解鎖"] == True].dropna(subset=['latitude', 'longitude'])
        def safe_float(val, fallback=0.0):
            try: return float(val)
            except: return fallback
            
        all_sites_coords = [[safe_float(r['latitude']), safe_float(r['longitude'])] for _, r in df_country_sites.iterrows()]
        unlocked_coords = [[safe_float(r['latitude']), safe_float(r['longitude'])] for _, r in df_active_sites.iterrows()]

        if not df_active_sites.empty: target_lat, target_lon = unlocked_coords[-1][0], unlocked_coords[-1][1]
        elif not df_country_sites.empty: target_lat, target_lon = all_sites_coords[0][0], all_sites_coords[0][1]
        else: target_lat, target_lon = -27.4698, 153.0251

        if st.session_state.current_map_country != selected_country:
            st.session_state.dino_lat, st.session_state.dino_lon = target_lat, target_lon
            st.session_state.current_map_country = selected_country
            st.session_state.trigger_map_animation = False

        start_lat, start_lon = st.session_state.dino_lat, st.session_state.dino_lon
        end_lat, end_lon = target_lat, target_lon
        if st.session_state.trigger_map_animation:
            is_animated_js = "true"
            st.session_state.dino_lat, st.session_state.dino_lon = target_lat, target_lon
            st.session_state.trigger_map_animation = False
        else:
            start_lat, start_lon = target_lat, target_lon
            is_animated_js = "false"

        bases_js_code = "".join([f"L.marker([{coord[0]}, {coord[1]}], {{icon: baseIcon}}).addTo(map);" for coord in unlocked_coords])

        cute_ankylosaurus_svg = """
        <svg viewBox='0 0 120 60' xmlns='http://www.w3.org/2000/svg'>
          <path d='M 30 35 Q 10 35 15 20' fill='none' stroke='#65a30d' stroke-width='8' stroke-linecap='round'/>
          <circle cx='15' cy='20' r='8' fill='#ca8a04' stroke='#854d0e' stroke-width='2'/>
          <ellipse cx='60' cy='35' rx='35' ry='18' fill='#84cc16'/>
          <polygon points='40,20 45,8 50,20' fill='#bef264' stroke='#4d7c0f' stroke-width='1'/>
          <polygon points='55,17 60,5 65,17' fill='#bef264' stroke='#4d7c0f' stroke-width='1'/>
          <polygon points='70,20 75,8 80,20' fill='#bef264' stroke='#4d7c0f' stroke-width='1'/>
          <circle cx='95' cy='30' r='14' fill='#84cc16'/>
          <circle cx='98' cy='26' r='3' fill='#ffffff'/>
          <circle cx='99' cy='26' r='1.5' fill='#000000'/>
          <ellipse cx='102' cy='32' rx='3' ry='2' fill='#fca5a5'/>
          <rect x='40' y='45' width='10' height='12' rx='4' fill='#65a30d'/>
          <rect x='70' y='45' width='10' height='12' rx='4' fill='#65a30d'/>
        </svg>
        """
        
        # 🎯 【圖層修正】：藍點縮小 50%，甲龍加入 zIndexOffset: 1000 絕對置頂
        leaflet_html = f"""
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <div id="map" style="width: 100%; height: 450px; border-radius: 15px; border: 3px solid #475569;"></div>
        <script>
            var sLat = isNaN({start_lat}) ? 0 : {start_lat}; var sLon = isNaN({start_lon}) ? 0 : {start_lon};
            var eLat = isNaN({end_lat}) ? 0 : {end_lat}; var eLon = isNaN({end_lon}) ? 0 : {end_lon};
            var map = L.map('map', {{ zoomControl: false }}).setView([sLat, sLon], 7);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);
            
            var baseIcon = L.divIcon({{ html: '<div style=\"font-size: 13px; line-height: 1;\">🔵</div>', className: 'custom-base-marker', iconSize: [13, 13], iconAnchor: [6.5, 6.5] }});
            {bases_js_code}
            
            var allCoords = {str(all_sites_coords)};
            if(allCoords.length > 0) {{ L.polyline(allCoords, {{color: '#94a3b8', dashArray: '5, 10', weight: 3}}).addTo(map); }}
            var unlockedCoords = {str(unlocked_coords)};
            if(unlockedCoords.length > 0) {{ L.polyline(unlockedCoords, {{color: '#3b82f6', weight: 5}}).addTo(map); }}

            var ankyloIcon = L.divIcon({{ html: `{cute_ankylosaurus_svg}`, className: 'custom-dino-layer', iconSize: [90, 45], iconAnchor: [45, 22] }});
            var dinoMarker = L.marker([sLat, sLon], {{icon: ankyloIcon, zIndexOffset: 1000}}).addTo(map);
            
            if ({is_animated_js}) {{
                setTimeout(function() {{ dinoMarker.setLatLng([eLat, eLon]); map.flyTo([eLat, eLon], 6, {{duration: 2.0}}); }}, 800);
            }} else {{
                dinoMarker.setLatLng([eLat, eLon]); map.setView([eLat, eLon], 6);
            }}
        </script>
        """
        st.components.v1.html(leaflet_html, height=470)

        st.markdown("---")
        st.subheader("🏆 探險里程碑與升學目標")
        if not df_milestones.empty: st.dataframe(df_milestones, use_container_width=True, hide_index=True)
        else: st.info("💡 尚未設定任何里程碑目標。")

# ------------------------------------------
# Tab 2: 今日任務
# ------------------------------------------
with tab2:
    st.info("💡 貼心提示：為了遊戲流暢度，打勾與結算將「瞬間」完成。離開前請記得點擊左側【☁️ 同步雲端】存檔喔！")
    col1, col2 = st.columns([1, 1])
    with col1:
        tasks = ["1. App單字闖關 15 分鐘", "2. 兒童版國家地理影片 15 分鐘", "3. 齊斌老師教材+測驗 2集", "4. 英文認証教材影片 15 分鐘", "5. 英文認証單字表 背熟10個", "6. 作業或評量沒有跳題", "7. 作業或評量全對"]
        new_checked_event = False; current_checked_count = 0
        for i, task_name in enumerate(tasks):
            cb_key = f"task_{i}"; lock_key = f"task_locked_{i}"
            if lock_key not in st.session_state: st.session_state[lock_key] = False
            is_checked = st.checkbox(task_name, key=cb_key, disabled=st.session_state[lock_key])
            if is_checked and not st.session_state[lock_key]:
                current_checked_count += 1; new_checked_event = True

        if new_checked_event: st.toast("🎉 任務狀態已選取，記得按下結算！", icon="✨")

        if st.button("✅ 來結算妳累積多少未來幣了吧"):
            if current_checked_count > 0:
                st.session_state.coins += current_checked_count
                st.session_state.audio_trigger = 'coin' 
                for i in range(len(tasks)):
                    if st.session_state.get(f"task_{i}"): st.session_state[f"task_locked_{i}"] = True
                
                if st.session_state.coins % 5 == 0:
                    sync_to_cloud(); st.toast(f"🎉 瞬間入帳 {current_checked_count} 枚未來幣！（已自動備份）", icon="🪙")
                else: st.toast(f"🎉 瞬間入帳 {current_checked_count} 枚未來幣！", icon="🪙")
                time.sleep(0.5); st.rerun()
            else: st.toast("沒有新的未結算任務喔！", icon="⚠️")
                
    with col2:
        st.markdown("""
        <div class="magic-timer-box">
            <h3 style="color: #854d0e; margin-top:0;">⏳ 魔法專注沙漏</h3>
            <p style="color: #a16207; font-size: 15px; font-weight: bold;">啟動魔法陣！15 分鐘不分心，就能召喚出 1 枚未來幣喔！</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.daily_timer_done:
            st.success("✅ 今天的魔法挑戰已經成功囉！")
        else:
            timer_placeholder = st.empty()
            if st.button("🚀 啟動魔法沙漏"):
                for t in range(15*60, -1, -1):
                    mins, secs = divmod(t, 60)
                    timer_placeholder.markdown(f"<h2 style='text-align: center; color: #ef4444;'>⏳ 剩餘魔法時間：`{mins:02d}:{secs:02d}`</h2>", unsafe_allow_html=True)
                    time.sleep(1)
                st.session_state.coins += 1
                st.session_state.daily_timer_done = True
                st.session_state.audio_trigger = 'coin'
                sync_to_cloud()
                st.success("🎉 召喚成功！獲得 1 枚未來幣！（進度已自動備份）")
                time.sleep(0.5); st.rerun()

# ------------------------------------------
# Tab 3: 學習基地
# ------------------------------------------
with tab3:
    if not df_resources.empty:
        for idx, row in df_resources.iterrows():
            r_cat, r_name, r_url, r_done, r_total = row.get('分類', '其他'), row.get('名稱', '未命名'), row.get('網址', '#'), row.get('已完成集數', 0), max(row.get('總集數', 1), 1)
            st.markdown(f"""<div class='resource-card'><span style='font-size:12px; color:#94a3b8;'>{r_cat}</span><br><strong style='font-size:18px;'>📖 {r_name}</strong><br><a href='{r_url}' target='_blank' style='color:#60a5fa;'>🔗 官方傳送門</a></div>""", unsafe_allow_html=True)
            c_col1, c_col2, c_col3 = st.columns([2, 1, 1])
            with c_col1: st.progress((r_done / r_total))
            with c_col2: st.write(f"📈 {r_done} / {r_total} 集")
            with c_col3:
                if st.button(f"➕ 第 {r_done + 1} 集", key=f"inc_{idx}") and r_done < r_total:
                    df_resources.loc[idx, "已完成集數"] = r_done + 1
                    conn.update(worksheet=WS_RESOURCES, data=df_resources)
                    st.cache_data.clear(); st.rerun()
            st.markdown("---")

# ------------------------------------------
# Tab 4: 🎁 願望兌換
# ------------------------------------------
with tab4:
    st.markdown("## 🎁 願望兌換所")
    st.info("💡 挑選一個妳最想要的禮物，按下「設定為目標」，側邊欄就會出現專屬進度條喔！")
    
    if not df_rewards.empty and "獎勵名稱" in df_rewards.columns:
        for idx, row in df_rewards.iterrows():
            r_name = row.get("獎勵名稱", "未命名")
            r_cost = int(row.get("所需未來幣", 0))
            
            with st.container():
                st.markdown(f"""
                <div style="background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 5px solid #f59e0b; margin-bottom: 15px;">
                    <h3 style="color: #fcd34d; margin-top: 0;">{r_name}</h3>
                    <p style="color: #94a3b8; font-size: 16px;">所需花費：<strong style="color: #fbbf24; font-size: 20px;">{r_cost} 🪙</strong></p>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.session_state.target_points == r_cost:
                        st.button("✅ 已鎖定此目標", key=f"lock_{idx}", disabled=True)
                    else:
                        if st.button("🎯 設定為目標", key=f"set_{idx}"):
                            st.session_state.target_points = r_cost
                            sync_to_cloud()
                            st.rerun()
                            
                with col_btn2:
                    if st.session_state.target_points == r_cost:
                        if st.session_state.coins >= r_cost:
                            if st.button(f"🎉 立即花費 {r_cost} 幣兌換！", key=f"redeem_{idx}"):
                                st.session_state.coins -= r_cost
                                st.session_state.target_points = 200 
                                st.session_state.audio_trigger = 'level_up'
                                sync_to_cloud()
                                st.balloons()
                                st.success(f"兌換成功！請馬上截圖找媽媽領取：【{r_name}】")
                                time.sleep(2)
                                st.rerun()
                        else:
                            st.button("🔒 金幣還不夠喔", key=f"short_{idx}", disabled=True)
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.warning("媽媽還沒有設定任何獎勵喔！趕快去找媽媽新增獎勵吧。")

# ------------------------------------------
# Tab 5: 知識挑戰
# ------------------------------------------
with tab5:
    if current_badge: st.markdown(f"### 🎖️ 目前階級：{badge_display} (答對 {st.session_state.quiz_correct_total} 題)")
    else: st.markdown(f"### 🔒 尚未獲得徽章 (答對 {st.session_state.quiz_correct_total} 題)")

    if st.session_state.daily_quiz_count >= 10:
        st.warning("⏳ 今天的體力用完囉，明天再來喔！")
    else:
        st.progress(st.session_state.daily_quiz_count / 10)
        if st.session_state.quiz_idx < len(df_quiz):
            current_q = df_quiz.iloc[st.session_state.quiz_idx]
            
            raw_question = str(current_q.get('題目', ''))
            if raw_question.strip() in ['nan', 'None', '']: display_question = "（⚠️ 題目好像在時空隧道迷路了！請媽媽確認一下喔！）"
            else: display_question = raw_question
                
            options = [str(current_q.get(col)) for col in ['選項A', '選項B', '選項C', '選項D'] if pd.notna(current_q.get(col)) and str(current_q.get(col)).strip() != 'nan']
            
            st.markdown(f"#### ❓ 全球恐龍大百科第 {st.session_state.quiz_idx + 1} 題：{display_question}")
            user_ans = st.empty().radio("請選擇答案：", options, key=f"q_{st.session_state.quiz_idx}")
            
            if st.button("🚀 瞬間送出答案"):
                st.session_state.daily_quiz_count += 1
                if str(user_ans).strip() == str(current_q["正確答案"]).strip():
                    st.session_state.quiz_correct_total += 1; st.session_state.audio_trigger = 'correct'; st.session_state.quiz_idx += 1
                    st.toast("🎉 答對了！", icon="✅")
                else:
                    st.session_state.audio_trigger = 'wrong'; st.toast("❌ 答錯囉！", icon="❌")
                    
                if st.session_state.daily_quiz_count == 10:
                    sync_to_cloud(); st.toast("☁️ 戰績已自動備份至雲端！", icon="☁️")
                    
                time.sleep(0.5); st.rerun()
        else: st.success("🏆 全數通關！請通知媽媽擴充題目吧！")

# ------------------------------------------
# Tab 6: 媽媽後台
# ------------------------------------------
with tab6:
    input_coins = st.number_input("手動調節未來幣：", min_value=0, value=st.session_state.coins, step=1)
    if input_coins != st.session_state.coins:
        st.session_state.coins = input_coins; sync_to_cloud(); st.toast(f"幣值已更新！", icon="☁️")
        
    st.markdown("---")
    st.markdown("### 🎁 雲端願望兌換所編輯器 (rewards)")
    edited_rewards_df = st.data_editor(df_rewards, use_container_width=True, num_rows="dynamic", key="rewards_editor")
    if st.button("💾 儲存並覆寫願望清單"): conn.update(worksheet=WS_REWARDS, data=edited_rewards_df); st.cache_data.clear(); st.toast("🎉 願望清單已建立/覆寫！", icon="✅")

    st.markdown("---")
    st.markdown("### 🗺️ 雲端地圖站點編輯器 (sites)")
    edited_sites_df = st.data_editor(df_sites, use_container_width=True, num_rows="dynamic", key="sites_editor")
    if st.button("💾 儲存並覆寫站點"): conn.update(worksheet=WS_SITES, data=edited_sites_df); st.cache_data.clear(); st.toast("🎉 站點已覆寫！", icon="✅")

    st.markdown("### 📚 雲端學習資源編輯器 (resources)")
    edited_resources_df = st.data_editor(df_resources, use_container_width=True, num_rows="dynamic", key="resources_editor")
    if st.button("💾 儲存並覆寫資源"): conn.update(worksheet=WS_RESOURCES, data=edited_resources_df); st.cache_data.clear(); st.toast("🎉 資源已覆寫！", icon="✅")
    
    st.markdown("### 🏆 雲端里程碑即時編輯器 (milestones)")
    edited_milestones_df = st.data_editor(df_milestones, use_container_width=True, num_rows="dynamic", key="milestones_editor")
    if st.button("💾 儲存並覆寫里程碑"): conn.update(worksheet=WS_MILESTONES, data=edited_milestones_df); st.cache_data.clear(); st.toast("🎉 里程碑已覆寫！", icon="✅")

    st.markdown("### 🦖 雲端雙語題庫即時編輯器 (quiz)")
    edited_quiz_df = st.data_editor(df_quiz, use_container_width=True, num_rows="dynamic", key="quiz_editor")
    if st.button("💾 儲存並覆寫題庫"): conn.update(worksheet=WS_QUIZ, data=edited_quiz_df); st.cache_data.clear(); st.toast("🎉 題庫已覆寫！", icon="✅")

# ==========================================
# 5. 音效引擎
# ==========================================
@st.cache_data
def load_audio_b64(file_name):
    if os.path.exists(file_name):
        with open(file_name, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

if st.session_state.audio_trigger:
    target_file = f"{st.session_state.audio_trigger}.mp3"
    b64_audio = load_audio_b64(target_file)
    if b64_audio: st.components.v1.html(f'<script>var a = new Audio("data:audio/mp3;base64,{b64_audio}"); a.play();</script>', height=0)
    st.session_state.audio_trigger = None
