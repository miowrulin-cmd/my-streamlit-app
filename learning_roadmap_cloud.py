import streamlit as st
import pandas as pd
import time
import base64
from streamlit_gsheets import GSheetsConnection # 👈 匯入 Google Sheets 連線模組

# ==========================================
# 1. 網頁基本設定 & 護眼暗黑模式 CSS
# ==========================================
st.set_page_config(
    page_title="🦖 恐龍特派員：全球夢想航線",
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
    .badge-box { background-color: #0f172a; padding: 15px; border-radius: 10px; border: 1px solid #475569; margin-bottom: 15px; }
    
    @keyframes pulse-btn {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { transform: scale(1.02); box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    .epic-congratulations {
        background: linear-gradient(135deg, #2e1065 0%, #4c1d95 100%);
        padding: 40px; border-radius: 25px; text-align: center;
        border: 4px solid #f43f5e; margin-bottom: 25px;
        box-shadow: 0px 10px 30px rgba(244,63,94,0.3);
    }
    div[data-testid="stButton"] button {
        width: 100% !important;
        font-size: 26px !important; padding: 20px !important;
        background: linear-gradient(135deg, #e11d48 0%, #9f1239 100%) !important;
        color: white !important; font-weight: 900 !important; border-radius: 15px !important;
        border: 2px solid #fda4af !important;
        box-shadow: 0px 8px 15px rgba(225,29,72,0.4) !important;
        animation: pulse-btn 1.4s infinite ease-in-out !important; letter-spacing: 1px;
    }
    div[data-testid="stButton"] button:hover { background: linear-gradient(135deg, #f43f5e 0%, #be123c 100%) !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 全局狀態與【內建 Base64 音效】註冊區 (維持原樣，暫不處理)
# ==========================================
if 'audio_trigger' not in st.session_state:
    st.session_state.audio_trigger = None

audio_b64 = {
    'coin': "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tQxAAAAAH8AAABAAgCAAAAAC4BAAAAgIAQAAAAAAACAQAAAAAARAAAAYAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAAAAA//tQxAgAAAH8AAABAAgCAAAAAC4BAAAAgIAQAAAAAAACAQAAAAAARAAAAYAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAAAAA",
    'level_up': "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tQxAAAAAH8AAABAAgCAAAAAC4BAAAAgIAQAAAAAAACAQAAAAAARAAAAYAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAAAAA//tQxAgAAAH8AAABAAgCAAAAAC4BAAAAgIAQAAAAAAACAQAAAAAARAAAAYAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAAAAA",
    'wrong': "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4LjI5LjEwMAAAAAAAAAAAAAAA//tQxAAAAAH8AAABAAgCAAAAAC4BAAAAgIAQAAAAAAACAQAAAAAARAAAAYAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAABgAAAEACAEAAAAALgEAAACAgBAAAAAAAAIBAAAAAABEAAAAA"
}

# ==========================================
# 3. 核心大腦：建立 Google Sheets 雲端連線
# ==========================================
# 建立連線物件
conn = st.connection("gsheets", type=GSheetsConnection)

# 讀取雲端資料庫 (加入 ttl=0 確保每次重整抓取最新數據，避免 iPad 與 PC 快取不同步)
df_coins = conn.read(worksheet="coins", ttl=15)
time.sleep(0.5)  # 👈 休息半秒
df_sites = conn.read(worksheet="sites", ttl=15)
time.sleep(0.5)  # 👈 休息半秒
df_milestones = conn.read(worksheet="milestones", ttl=15)
time.sleep(0.5)  # 👈 休息半秒
df_resources = conn.read(worksheet="resources", ttl=15)
time.sleep(0.5)  # 👈 休息半秒
df_quiz = conn.read(worksheet="quiz", ttl=15)
time.sleep(0.5)  # 👈 休息半秒

# 啟動時讀取狀態 (從 df_coins)
if 'coins' not in st.session_state:
    st.session_state.coins = int(df_coins.loc[0, "coins"]) if not df_coins.empty and "coins" in df_coins.columns else 0
    st.session_state.previous_unlocked_count = int(df_coins.loc[0, "previous_count"]) if not df_coins.empty and "previous_count" in df_coins.columns else 1
    st.session_state.target_points = int(df_coins.loc[0, "target_points"]) if not df_coins.empty and "target_points" in df_coins.columns else 200
    st.session_state.dino_lat = float(df_coins.loc[0, "dino_lat"]) if not df_coins.empty and "dino_lat" in df_coins.columns else -27.4698
    st.session_state.dino_lon = float(df_coins.loc[0, "dino_lon"]) if not df_coins.empty and "dino_lon" in df_coins.columns else 153.0251
    
    st.session_state.quiz_correct_total = int(df_coins.loc[0, "quiz_correct_total"]) if not df_coins.empty and "quiz_correct_total" in df_coins.columns else 0
    st.session_state.daily_quiz_count = int(df_coins.loc[0, "daily_quiz_count"]) if not df_coins.empty and "daily_quiz_count" in df_coins.columns else 0
    st.session_state.last_quiz_date = str(df_coins.loc[0, "last_quiz_date"]) if not df_coins.empty and "last_quiz_date" in df_coins.columns else time.strftime("%Y-%m-%d")
    st.session_state.quiz_idx = int(df_coins.loc[0, "quiz_idx"]) if not df_coins.empty and "quiz_idx" in df_coins.columns else 0
    
    st.session_state.just_unlocked = False
    st.session_state.trigger_map_animation = False
    st.session_state.completed_countries = []
    st.session_state.just_completed_country = None
    
today_str = time.strftime("%Y-%m-%d")
if st.session_state.last_quiz_date != today_str:
    st.session_state.daily_quiz_count = 0
    st.session_state.last_quiz_date = today_str

# 【架構重構】全域存檔函式：直接對接 Google Sheets API 進行 Update
def save_core_state():
    state_df = pd.DataFrame([{
        "coins": st.session_state.coins, 
        "previous_count": st.session_state.previous_unlocked_count,
        "target_points": st.session_state.target_points,
        "dino_lat": st.session_state.dino_lat,
        "dino_lon": st.session_state.dino_lon,
        "quiz_correct_total": st.session_state.quiz_correct_total,
        "daily_quiz_count": st.session_state.daily_quiz_count,
        "last_quiz_date": st.session_state.last_quiz_date,
        "quiz_idx": st.session_state.quiz_idx
    }])
    conn.update(worksheet="coins", data=state_df)
    st.cache_data.clear() # 清除快取確保其他裝置能立刻讀取到更新

# ==========================================
# 4. 側邊欄控制台
# ==========================================
with st.sidebar:
    st.markdown("## 🎒 我的探險裝備包")
    st.markdown(f"""
    <div class="coin-box">
        <span style='font-size: 14px; font-weight: bold; color: #9ca3af;'>🪙 當前累積未來幣</span><br>
        <span style='font-size: 34px; font-weight: bold; color: #fbbf24;'>{st.session_state.coins} 枚</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    country_options = df_sites["國家"].unique() if "國家" in df_sites.columns else ["未知名國家"]
    selected_country = st.selectbox("🌍 任務地圖切換器：", country_options)

# ==========================================
# 5. 主畫面分頁系統
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"🗺️ {selected_country} 大富翁",
    "📅 今日任務", 
    "📚 學習基地", 
    "🦖 知識挑戰 (徽章)",
    "⚙️ 題庫與後台"
])

# ------------------------------------------
# Tab 1: 大富翁 (獨立且唯一的解鎖判定區)
# ------------------------------------------
with tab1:
    df_sites["解鎖所需代幣"] = pd.to_numeric(df_sites.get("解鎖所需代幣"), errors='coerce').fillna(0).astype(int)
    df_sites["站點順序"] = pd.to_numeric(df_sites.get("站點順序"), errors='coerce').fillna(1).astype(int)
    df_sites["是否解鎖"] = df_sites["解鎖所需代幣"].apply(lambda x: st.session_state.coins >= x)
    
    current_unlocked_count = df_sites["是否解鎖"].sum()

    if current_unlocked_count > st.session_state.previous_unlocked_count:
        st.session_state.just_unlocked = True
        new_completed = []
        if '國家' in df_sites.columns:
            for country in df_sites['國家'].unique():
                country_sites = df_sites[df_sites['國家'] == country]
                if country_sites['是否解鎖'].all() and country not in st.session_state.completed_countries:
                    new_completed.append(country)
                
        if new_completed:
            st.session_state.completed_countries.extend(new_completed)
            st.session_state.audio_trigger = 'level_up' 
            st.session_state.just_completed_country = new_completed[0]
        else:
            st.session_state.audio_trigger = 'level_up' 
            st.session_state.just_completed_country = None

        st.session_state.previous_unlocked_count = current_unlocked_count
        save_core_state()

    if st.session_state.just_unlocked:
        st.balloons()
        if st.session_state.get('just_completed_country'):
            msg = f"🎉 史詩級通關！【{st.session_state.just_completed_country}】全境解鎖！ 🎉"
            sub_msg = f"太不可思議了！妳的 🪙 {st.session_state.coins} 枚未來幣，已經找齊了這個國家的所有史前碎片！"
        else:
            msg = "🎉 LEVEL UP! 新基地解鎖！ 🎉"
            sub_msg = f"太厲害了！妳目前累積的 🪙 {st.session_state.coins} 枚未來幣，點亮了全新考古基地！"

        st.markdown(f"""
        <div class="epic-congratulations">
            <h1 style="color: #fca5a5; font-size: 48px; font-weight: 900; margin: 0; text-shadow: 2px 2px #000;">{msg}</h1>
            <p style="color: #e0e7ff; font-size: 24px; font-weight: bold; margin-top: 15px;">{sub_msg}</p>
            <p style="color: #93c5fd; font-size: 20px; font-weight: bold; margin-bottom: 15px;">👇 趕快按下按鈕，陪特派員前進下一站！</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🦖 帶領甲龍特派員出發長征 (START DINO MARCH) ➔"):
            st.session_state.just_unlocked = False
            st.session_state.trigger_map_animation = True 
            st.session_state.just_completed_country = None
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    st.subheader(f"📍 {selected_country} 探險進度")
    df_country_sites = df_sites[df_sites.get("國家", "") == selected_country]
    
    if not df_country_sites.empty:
        cols_per_row = 5
        rows = [df_country_sites.iloc[i:i+cols_per_row] for i in range(0, len(df_country_sites), cols_per_row)]
        for r_df in rows:
            site_cols = st.columns(cols_per_row)
            for idx, (_, row) in enumerate(r_df.iterrows()):
                with site_cols[idx]:
                    s_name = row.get('站點名稱', '未命名')
                    s_story = row.get('解鎖冒險故事', '暫無')
                    s_order = row.get('站點順序', idx+1)
                    s_token = row.get('解鎖所需代幣', 0)
                    if row.get("是否解鎖", False):
                        st.markdown(f"""<div class='game-node-unlocked'><span style='font-size:24px;'>🦖</span><br><strong style='color:#60a5fa;'>第 {s_order} 站</strong><br><strong>{s_name}</strong><br><p style='font-size:12px; margin-top:5px; color:#cbd5e1;'>{s_story}</p></div>""", unsafe_allow_html=True)
                    else:
                        diff = int(s_token - st.session_state.coins)
                        st.markdown(f"""<div class='game-node-locked'><span style='font-size:24px;'>🔒</span><br><span>第 {s_order} 站</span><br><span>{s_name}</span><br><span style='font-size:11px; color:#64748b;'>再收集 {diff} 🪙</span></div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader(f"🗺️ 實時雷達導航：{selected_country}")
        
        df_active_sites = df_country_sites[df_country_sites["是否解鎖"] == True].dropna(subset=['latitude', 'longitude'])
        all_sites_coords = df_country_sites[['latitude', 'longitude']].values.tolist()
        unlocked_coords = df_active_sites[['latitude', 'longitude']].values.tolist()
        
        if not df_active_sites.empty:
            target_lat = float(df_active_sites.iloc[-1]['latitude'])
            target_lon = float(df_active_sites.iloc[-1]['longitude'])
        else:
            target_lat = float(df_country_sites.iloc[0]['latitude'])
            target_lon = float(df_country_sites.iloc[0]['longitude'])
            
        if st.session_state.get('current_map_country') != selected_country:
            st.session_state.dino_lat = target_lat
            st.session_state.dino_lon = target_lon
            st.session_state.current_map_country = selected_country
            st.session_state.trigger_map_animation = False

        if st.session_state.trigger_map_animation:
            start_lat = st.session_state.dino_lat
            start_lon = st.session_state.dino_lon
            end_lat = target_lat
            end_lon = target_lon
            is_animated_js = "true"
            st.session_state.dino_lat = target_lat
            st.session_state.dino_lon = target_lon
            st.session_state.trigger_map_animation = False
            save_core_state()
        else:
            start_lat = target_lat
            start_lon = target_lon
            end_lat = target_lat
            end_lon = target_lon
            is_animated_js = "false"

        bases_js_code = ""
        for _, b_row in df_active_sites.iterrows():
            safe_name = str(b_row['站點名稱']).replace("'", "\\'")
            bases_js_code += f"L.marker([{b_row['latitude']}, {b_row['longitude']}], {{icon: baseIcon}}).addTo(map).bindPopup('<b>第{b_row['站點順序']}站: {safe_name}</b>');\n"

        leaflet_html = f"""
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            .dino-skeletal-box {{ position: relative; width: 120px; height: 80px; transform-origin: center center; }}
            .dino-core-body {{ position: absolute; width: 66px; height: 44px; background: #4d5656; border-radius: 45%; left: 27px; top: 18px; box-shadow: inset 0 0 15px #1a252f, 0 8px 16px rgba(0,0,0,0.5); z-index: 30; animation: bodyLumberCycle 0.8s infinite ease-in-out; }}
            .dino-core-body::after {{ content: '▲▲▲▲▲\\n▲▲▲▲▲\\n▲▲▲▲▲'; white-space: pre; position: absolute; font-size: 8px; font-weight: 900; color: #95a5a6; top: 6px; left: 14px; letter-spacing: 4px; line-height: 1.1; }}
            .dino-skeletal-head {{ position: absolute; width: 18px; height: 16px; background: #2c3e50; border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%; right: -13px; top: 14px; border-left: 3px solid #1a252f; }}
            .dino-skeletal-head::before {{ content: '◀'; position: absolute; font-size: 8px; color: #bdc3c7; top: -5px; left: -2px; transform: rotate(30deg); }}
            .dino-skeletal-head::after {{ content: '◀'; position: absolute; font-size: 8px; color: #bdc3c7; bottom: -5px; left: -2px; transform: rotate(-30deg); }}
            .dino-skeletal-tail {{ position: absolute; width: 35px; height: 8px; background: #4d5656; left: -32px; top: 18px; transform-origin: right center; animation: tailClubWag 0.8s infinite ease-in-out; }}
            .dino-tail-club {{ position: absolute; width: 18px; height: 16px; background: #1c2833; border-radius: 40% 60% 60% 40%; left: -12px; top: -4px; box-shadow: -2px 4px 6px rgba(0,0,0,0.6); }}
            .dino-foot {{ position: absolute; width: 16px; height: 18px; background: #2e4053; border-radius: 6px; z-index: 20; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
            .dino-foot::after {{ content: '...'; font-size: 18px; font-weight: 900; color: #fff; position: absolute; top: -6px; left: 1px; letter-spacing: -1px; }}
            .leg-bottom::after {{ top: auto; bottom: -11px; transform: rotate(180deg); }}
            .leg-left-front  {{ left: 36px; top: 6px;  transform-origin: center bottom; animation: heavyStrideA 0.8s infinite ease-in-out; }}
            .leg-right-back  {{ left: 68px; top: 56px; transform-origin: center top;    animation: heavyStrideA 0.8s infinite ease-in-out; }}
            .leg-right-front {{ left: 36px; top: 56px; transform-origin: center top;    animation: heavyStrideB 0.8s infinite ease-in-out; }}
            .leg-left-back   {{ left: 68px; top: 6px;  transform-origin: center bottom; animation: heavyStrideB 0.8s infinite ease-in-out; }}
            @keyframes heavyStrideA {{ 0% {{ transform: translateX(-5px) scaleY(1); background: #1b2631; }} 50% {{ transform: translateX(6px) scaleY(1.1); background: #34495e; }} 100% {{ transform: translateX(-5px) scaleY(1); background: #1b2631; }} }}
            @keyframes heavyStrideB {{ 0% {{ transform: translateX(6px) scaleY(1.1); background: #34495e; }} 50% {{ transform: translateX(-5px) scaleY(1); background: #1b2631; }} 100% {{ transform: translateX(6px) scaleY(1.1); background: #34495e; }} }}
            @keyframes bodyLumberCycle {{ 0% {{ transform: translateY(-1px) rotate(1deg); }} 50% {{ transform: translateY(1px) rotate(-1deg); }} 100% {{ transform: translateY(-1px) rotate(1deg); }} }}
            @keyframes tailClubWag {{ 0% {{ transform: rotate(-18deg); }} 50% {{ transform: rotate(18deg); }} 100% {{ transform: rotate(-18deg); }} }}
        </style>
        
        <div id="map" style="width: 100%; height: 500px; border-radius: 15px; border: 3px solid #475569;"></div>
        <script>
            var startLat = {start_lat} || -27.4698; var startLon = {start_lon} || 153.0251;
            var endLat = {end_lat} || -27.4698; var endLon = {end_lon} || 153.0251;
            var animateFlow = {is_animated_js};
            
            var map = L.map('map', {{ zoomControl: false }}).setView([startLat, startLon], 7);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);

            var baseIcon = L.divIcon({{ html: '<div style="font-size: 26px; transform: translate(-13px, -13px);">🔵</div>', className: 'custom-base-marker' }});
            {bases_js_code}

            var allSitesCoords = {str(all_sites_coords)};
            var unlockedCoords = {str(unlocked_coords)};
            L.polyline(allSitesCoords, {{color: '#94a3b8', dashArray: '5, 10', weight: 3}}).addTo(map);
            L.polyline(unlockedCoords, {{color: '#3b82f6', weight: 5}}).addTo(map);

            var dinoIcon = L.divIcon({{
                html: `<div class="dino-skeletal-box" id="dino-avatar">
                        <div class="dino-foot leg-left-front"></div><div class="dino-foot leg-left-back"></div>
                        <div class="dino-core-body"><div class="dino-skeletal-head"></div><div class="dino-skeletal-tail"><div class="dino-tail-club"></div></div></div>
                        <div class="dino-foot leg-right-front leg-bottom"></div><div class="dino-foot leg-right-back leg-bottom"></div>
                       </div>`,
                className: 'custom-dino-layer', iconSize: [120, 80], iconAnchor: [60, 40]
            }});

            var dinoMarker = L.marker([startLat, startLon], {{icon: dinoIcon}}).addTo(map);

            function calculateAngle(lat1, lon1, lat2, lon2) {{
                var dLon = (lon2 - lon1) * Math.PI / 180;
                var lat1Rad = lat1 * Math.PI / 180; var lat2Rad = lat2 * Math.PI / 180;
                var y = Math.sin(dLon) * Math.cos(lat2Rad);
                var x = Math.cos(lat1Rad) * Math.sin(lat2Rad) - Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);
                var brng = Math.atan2(y, x) * 180 / Math.PI;
                return (brng + 360) % 360;
            }}
            var bearingAngle = calculateAngle(startLat, startLon, endLat, endLon);

            var observer = new IntersectionObserver(function(entries) {{
                if(entries[0].isIntersecting) {{
                    map.invalidateSize(); 
                    if (animateFlow && !window.hasAnimated) {{
                        window.hasAnimated = true;
                        map.setView([startLat, startLon], 8); 
                        setTimeout(function() {{
                            var startTime = null; var duration = 8000; 
                            function stepMarch(timestamp) {{
                                if (!startTime) startTime = timestamp;
                                var pct = Math.min((timestamp - startTime) / duration, 1);
                                var easePct = pct < .5 ? 2 * pct * pct : -1 + (4 - 2 * pct) * pct; 

                                var currLat = startLat + (endLat - startLat) * easePct;
                                var currLon = startLon + (endLon - startLon) * easePct;
                                
                                dinoMarker.setLatLng([currLat, currLon]);
                                map.panTo([currLat, currLon], {{animate: false}}); 
                                
                                var element = document.getElementById('dino-avatar');
                                if (element) element.style.transform = 'rotate(' + (bearingAngle - 90) + 'deg)';
                                
                                if (pct < 1) requestAnimationFrame(stepMarch);
                                else {{
                                    setTimeout(() => {{ map.flyTo([endLat, endLon], 6, {{duration: 1.5}}); }}, 500);
                                }}
                            }}
                            requestAnimationFrame(stepMarch);
                        }}, 1000);
                    }} else {{
                        dinoMarker.setLatLng([endLat, endLon]); map.setView([endLat, endLon], 6);
                        setTimeout(function() {{
                            var element = document.getElementById('dino-avatar');
                            if (element) element.style.transform = 'rotate(' + (bearingAngle - 90) + 'deg)';
                        }}, 150);
                    }}
                }}
            }});
            observer.observe(document.getElementById('map'));
        </script>
        """
        st.components.v1.html(leaflet_html, height=520)

# ------------------------------------------
# Tab 2: 今日任務 (合法獲得硬幣的來源)
# ------------------------------------------
with tab2:
    st.subheader("📋 任務檢查清單卡")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        tasks = [
            "1. App單字闖關 15 分鐘",
            "2. 兒童版國家地理影片 15 分鐘",
            "3. 齊斌老師教材+測驗 2集",
            "4. 英文認証教材影片 15 分鐘",
            "5. 英文認証單字表 背熟10個",
            "6. 當天作業或評量沒有跳題",
            "7. 當天作業或評量全對"
        ]
        
        new_checked_event = False
        current_checked_count = 0
        
        for i, task_name in enumerate(tasks):
            cb_key = f"task_{i}"
            prev_key = f"prev_{cb_key}"
            
            if prev_key not in st.session_state:
                st.session_state[prev_key] = False
                
            is_checked = st.checkbox(task_name, key=cb_key)
            if is_checked: current_checked_count += 1
            if is_checked and not st.session_state[prev_key]:
                new_checked_event = True
            st.session_state[prev_key] = is_checked

        if new_checked_event:
            st.session_state.audio_trigger = 'coin'
            st.toast("🎉 太棒了！完成一項任務！", icon="✨")

        if st.button("✅ 結算發放未來幣"):
            if current_checked_count > 0:
                st.session_state.coins += current_checked_count
                st.session_state.audio_trigger = 'coin' 
                save_core_state()
                st.toast(f"🎉 結算完成！入帳 {current_checked_count} 枚未來幣！", icon="🪙")
            else:
                st.toast("要先勾選完成的任務喔！", icon="⚠️")
                
    with col2:
        st.markdown("### ⏱️ 專注力計時盤")
        timer_placeholder = st.empty()
        if st.button("🚀 開始 15 分鐘專注挑戰"):
            for t in range(15*60, -1, -1):
                mins, secs = divmod(t, 60)
                timer_placeholder.markdown(f"## ⏳ 剩餘時間：`{mins:02d}:{secs:02d}`")
                time.sleep(1)
            st.session_state.coins += 2
            st.session_state.audio_trigger = 'level_up'
            save_core_state()

# ------------------------------------------
# Tab 3: 帶狀資源進度追蹤
# ------------------------------------------
with tab3:
    st.subheader("📚 數位學習基地")
    if not df_resources.empty:
        for idx, row in df_resources.iterrows():
            r_cat = row.get('分類', '其他')
            r_name = row.get('名稱', '未命名資源')
            r_url = row.get('網址', '#')
            r_done = row.get('已完成集數', 0)
            r_total = max(row.get('總集數', 1), 1)
            
            st.markdown(f"""<div class='resource-card'><span style='font-size:12px; color:#94a3b8;'>{r_cat}</span><br><strong style='font-size:18px; color:#e2e8f0;'>📖 {r_name}</strong><br><a href='{r_url}' target='_blank' style='color:#60a5fa;'>🔗 官方線上課程網頁傳送門</a></div>""", unsafe_allow_html=True)
            
            course_perf = (r_done / r_total) * 100
            c_col1, c_col2, c_col3 = st.columns([2, 1, 1])
            with c_col1: st.progress(course_perf / 100)
            with c_col2: st.write(f"📈 已完成：**{r_done}** 集 / 共 {r_total} 集")
            with c_col3:
                if st.button(f"➕ 聽完第 {r_done + 1} 集", key=f"inc_{idx}"):
                    if r_done < r_total:
                        df_resources.loc[idx, "已完成集數"] = r_done + 1
                        # 【替換寫入雲端邏輯】
                        conn.update(worksheet="resources", data=df_resources)
                        st.cache_data.clear()
                        st.toast("雲端進度已即時儲存！", icon="☁️")
            st.markdown("---")

# ------------------------------------------
# Tab 4: 恐龍知識大挑戰 (徽章榮譽制 & 每日限制，絕對不給硬幣)
# ------------------------------------------
with tab4:
    st.subheader("🦖 恐龍知識大挑戰")
    st.info("💡 透過雙語問答收集知識徽章吧！特派員每天最多只能挖掘 10 題化石喔！(此區無金幣獎勵)")
    
    badges_info = [
        (1000, "💎", "地球史守護者 (神話)", "linear-gradient(135deg, #1e3a8a, #3b82f6)"),
        (700, "👑", "考古大師 (傳奇)", "linear-gradient(135deg, #78350f, #f59e0b)"),
        (400, "🦖", "暴龍尖牙 (戰鬥員)", "linear-gradient(135deg, #7f1d1d, #ef4444)"),
        (100, "🦕", "腕龍寶寶 (探索者)", "linear-gradient(135deg, #064e3b, #10b981)"),
        (10, "🥚", "恐龍蛋 (新手)", "linear-gradient(135deg, #374151, #9ca3af)")
    ]
    
    current_badge = next((b for b in badges_info if st.session_state.quiz_correct_total >= b[0]), None)
    next_badge = next((b for b in reversed(badges_info) if st.session_state.quiz_correct_total < b[0]), None)
    
    if current_badge:
        st.markdown(f"""
        <div class="badge-container">
            <div class="badge-icon-box" style="background: {current_badge[3]};">
                {current_badge[1]}
            </div>
            <div class="badge-text-box">
                <h3 style="margin: 0; color: #f8fafc;">目前榮譽階級：{current_badge[2]}</h3>
                <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 14px;">已累積答對 {st.session_state.quiz_correct_total} 題！</p>
                {f'<p style="margin: 5px 0 0 0; color: #fbbf24; font-size: 14px;">再答對 {next_badge[0] - st.session_state.quiz_correct_total} 題即可晉升為 <b>{next_badge[2]}</b>！</p>' if next_badge else '<p style="margin: 5px 0 0 0; color: #fbbf24; font-size: 14px;">🎉 您已達成最高榮譽！</p>'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="badge-container">
            <div class="badge-icon-box" style="background: #334155;">🔒</div>
            <div class="badge-text-box">
                <h3 style="margin: 0; color: #f8fafc;">尚未獲得徽章</h3>
                <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 14px;">目前累積答對 {st.session_state.quiz_correct_total} 題，差 {10 - st.session_state.quiz_correct_total} 題即可獲得第一個徽章【🥚 恐龍蛋】！</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.daily_quiz_count >= 10:
        st.warning("⏳ 今天的考古探勘體力已經用盡囉！特派員每天最多只能挖掘 10 個知識化石，我們明天繼續吧！")
    else:
        st.markdown(f"**⛏️ 今日挖掘體力：** `{st.session_state.daily_quiz_count} / 10`")
        st.progress(st.session_state.daily_quiz_count / 10)
        
        if st.session_state.quiz_idx < len(df_quiz):
            current_q = df_quiz.iloc[st.session_state.quiz_idx]
            raw_options = [current_q.get('選項A'), current_q.get('選項B'), current_q.get('選項C'), current_q.get('選項D')]
            options = [str(opt) for opt in raw_options if pd.notna(opt) and str(opt).strip() != ""]
            
            st.markdown(f"#### ❓ 全球圖鑑第 {st.session_state.quiz_idx + 1} 題：{current_q['題目']}")
            user_ans = st.radio("請選擇你的答案：", options, key=f"q_{st.session_state.quiz_idx}")
            
            if st.button("🚀 送出答案"):
                st.session_state.daily_quiz_count += 1
                
                if str(user_ans).strip() == str(current_q["正確答案"]).strip():
                    st.session_state.quiz_correct_total += 1
                    st.session_state.audio_trigger = 'coin' 
                    st.session_state.quiz_idx += 1
                    save_core_state()
                    st.toast("🎉 答對了！雲端知識點數增加！", icon="☁️")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.session_state.audio_trigger = 'wrong' 
                    save_core_state()
                    st.toast("❌ 哎呀，答錯囉！再仔細想想看！", icon="❌")
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.success("🏆 太厲害了！目前題庫中的挑戰已全數通關！請通知媽咪去後台擴充新題目！")
            if st.button("🔄 重新挑戰一次"):
                st.session_state.quiz_idx = 0
                save_core_state()
                st.rerun()

# ------------------------------------------
# Tab 5: 媽媽後台 (雲端同步總控)
# ------------------------------------------
with tab5:
    st.subheader("⚙️ 媽媽專屬雲端資料庫管理艙")
    
    st.markdown("### 🪙 調整/發放當前的未來幣代幣")
    input_coins = st.number_input("當前擁有未來幣數量：", min_value=0, value=st.session_state.coins, step=1)
    if input_coins != st.session_state.coins:
        st.session_state.coins = input_coins
        save_core_state()
        st.toast(f"未來幣已手動調節為 {input_coins} 枚！(雲端已同步)", icon="☁️")
        
    st.markdown("---")
    st.markdown("### 🦖 恐龍知識雙語題庫編輯器")
    edited_quiz_df = st.data_editor(df_quiz, use_container_width=True, num_rows="dynamic", key="quiz_editor")
    
    if st.button("💾 儲存並同步至 Google 雲端題庫", key="save_quiz_btn"):
        conn.update(worksheet="quiz", data=edited_quiz_df) # 👈 替換寫入雲端邏輯
        st.cache_data.clear()
        st.toast("🎉 題庫已成功同步至 Google Sheets！", icon="✅")
        
    st.markdown("---")
    st.markdown("### 🗺️ 編輯大富翁站點條件")
    edited_map_df = st.data_editor(
        df_sites, use_container_width=True, num_rows="dynamic", key="map_editor",
        column_config={
            "站點順序": st.column_config.NumberColumn("站點順序", min_value=1, step=1, format="%d"),
            "解鎖所需代幣": st.column_config.NumberColumn("解鎖所需代幣", min_value=0, step=1, format="%d")
        }
    )
    
    if st.button("💾 儲存並同步至 Google 雲端地圖資料庫", key="save_site_btn"):
        conn.update(worksheet="sites", data=edited_map_df) # 👈 替換寫入雲端邏輯
        st.cache_data.clear()
        st.toast("🎉 地圖資料庫已成功同步至 Google Sheets！", icon="✅")

# ==========================================
# 8. 音效廣播系統 (維持原樣)
# ==========================================
if st.session_state.audio_trigger:
    b64 = audio_b64.get(st.session_state.audio_trigger)
    if b64:
        try:
            b64 += "=" * ((4 - len(b64) % 4) % 4)
            audio_bytes = base64.b64decode(b64)
            st.markdown("<style>audio { display: none !important; }</style>", unsafe_allow_html=True)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        except Exception as e:
            st.warning(f"音效解碼失敗，但已攔截錯誤: {e}")
            
    st.session_state.audio_trigger = None
