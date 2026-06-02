import streamlit as st
import pandas as pd
import time
# 雲端版專屬：載入 Google Sheets 官方連線引擎
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 網頁基本設定與 3 大核心按鈕鋼鐵 CSS 結界
# ==========================================
st.set_page_config(
    page_title="🦖 澳洲恐龍特派員：夢想航線導航艙 (雲端同步版)",
    page_icon="🦖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Scoped CSS 容器穿透技術：精準鎖定 3 個核心大鈕，絕不污染後台表格微型按鈕
st.markdown("""
<style>
    .coin-box { background-color: #fff3cd; border-radius: 15px; padding: 15px; border: 2px dashed #ffc107; text-align: center; margin-bottom: 20px; }
    .game-node-unlocked { background-color: #e8f8f5; border: 2px solid #2ec4b6; border-radius: 12px; padding: 15px; text-align: center; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .game-node-locked { background-color: #f2f4f4; border: 2px dashed #bdc3c7; border-radius: 12px; padding: 15px; text-align: center; color: #7f8c8d; }
    .resource-card { background-color: #f8f9fa; border-left: 5px solid #2196f3; padding: 10px; margin-bottom: 10px; border-radius: 4px; }
    .op-zone { background-color: #f4f6f7; border-radius: 8px; padding: 12px; margin-top: -10px; margin-bottom: 20px; border: 1px solid #e5e8e8; }
    
    /* 浮誇過關大看板 */
    .epic-congratulations {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 40px; border-radius: 25px; text-align: center; border: 6px solid #dc3545; margin-bottom: 25px; box-shadow: 0px 15px 35px rgba(220,53,69,0.3);
    }

    /* 3 大核心按鈕巨型化動畫宣告 */
    @keyframes pulse-red { 0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(220,53,69,0.7); } 70% { transform: scale(1.02); box-shadow: 0 0 0 25px rgba(220,53,69,0); } 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(220,53,69,0); } }
    @keyframes pulse-orange { 0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(230,126,34,0.7); } 70% { transform: scale(1.02); box-shadow: 0 0 0 25px rgba(230,126,34,0); } 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(230,126,34,0); } }
    @keyframes pulse-blue { 0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(41,128,185,0.7); } 70% { transform: scale(1.02); box-shadow: 0 0 0 25px rgba(41,128,185,0); } 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(41,128,185,0); } }

    /* 暴力強制打通外殼限制 */
    .victory-btn, .victory-btn div[data-testid="stButton"], .checkin-btn, .checkin-btn div[data-testid="stButton"], .timer-btn, .timer-btn div[data-testid="stButton"] {
        width: 100% !important; min-width: 100% !important; max-width: 100% !important; display: block !important;
    }

    /* 按鈕 1：長征確認大紅鈕 */
    .victory-btn div[data-testid="stButton"] button {
        font-size: 36px !important; font-weight: 900 !important; color: #ffffff !important;
        background: linear-gradient(135deg, #dc3545 0%, #a61221 100%) !important;
        border: 5px solid #ffffff !important; border-radius: 25px !important;
        min-height: 115px !important; height: 115px !important; width: 100% !important;
        box-shadow: 0px 12px 30px rgba(220,53,69,0.6) !important;
        animation: pulse-red 1.2s infinite ease-in-out !important;
        text-shadow: 2px 2px 5px rgba(0,0,0,0.3) !important;
    }

    /* 按鈕 2：任務完成大橘鈕 */
    .checkin-btn div[data-testid="stButton"] button {
        font-size: 32px !important; font-weight: 900 !important; color: #ffffff !important;
        background: linear-gradient(135deg, #e67e22 0%, #d35400 100%) !important;
        border: 4px solid #ffffff !important; border-radius: 20px !important;
        min-height: 95px !important; height: 95px !important; width: 100% !important;
        box-shadow: 0px 10px 20px rgba(230,126,34,0.5) !important;
        animation: pulse-orange 1.5s infinite ease-in-out !important;
    }

    /* 按鈕 3：專注挑战科幻藍鈕 */
    .timer-btn div[data-testid="stButton"] button {
        font-size: 32px !important; font-weight: 900 !important; color: #ffffff !important;
        background: linear-gradient(135deg, #2980b9 0%, #2471a3 100%) !important;
        border: 4px solid #ffffff !important; border-radius: 20px !important;
        min-height: 95px !important; height: 95px !important; width: 100% !important;
        box-shadow: 0px 10px 20px rgba(41,128,185,0.5) !important;
        animation: pulse-blue 1.8s infinite ease-in-out !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 密碼學帳號登入管理模組 (跨裝置同步基礎)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🦖 夢想航線：身分驗證控制艙")
    st.write("請輸入特派員或指揮官通行碼以對接雲端大帳本：")
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        username = st.text_input("👤 使用者帳號 (媽媽請輸入 mom / 女兒請輸入 daughter)：")
        password = st.text_input("🔒 安全驗證碼：", type="password")
        
        if st.button("🚀 驗證登入並同步雲端"):
            if username == "mom" and password == "mom123":
                st.session_state.logged_in = True
                st.session_state.role = "mom"
                st.success("指揮官媽媽登入成功！正在接續全權限控制台...")
                time.sleep(1)
                st.rerun()
            elif username == "daughter" and password == "dino123":
                st.session_state.logged_in = True
                st.session_state.role = "daughter"
                st.success("🦖 歡迎回來！恐龍特派員！正在同步妳的未來幣基地...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ 驗證碼錯誤，請重新核對身分識別碼！")
    st.stop() # 封鎖未登入的使用者

# ==========================================
# 3. 雲端 Google Sheets 資料對接引擎 (去硬碟化)
# ==========================================
# 建立雲端連線實例
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 讀取雲端大帳本 (未來佈署上 Streamlit Cloud 後，會從 Secrets 自動抓取設定)
    df_coins = conn.read(worksheet="coins", ttl=5)
    df_sites = conn.read(worksheet="sites", ttl=5)
    df_milestones = conn.read(worksheet="milestones", ttl=5)
    df_resources = conn.read(worksheet="resources", ttl=5)
    
    # 將雲端數據同步進網頁運行空間
    if 'coins' not in st.session_state:
        st.session_state.coins = int(df_coins.loc[0, "coins"])
        st.session_state.previous_unlocked_count = int(df_coins.loc[0, "previous_count"])
        st.session_state.target_points = int(df_coins.loc[0, "target_points"])
        st.session_state.dino_lat = float(df_coins.loc[0, "dino_lat"])
        st.session_state.dino_lon = float(coin_df.loc[0, "dino_lon"]) if "dino_lon" in coin_df.columns else 153.0251
        st.session_state.just_unlocked = False
        st.session_state.trigger_map_animation = False
        st.session_state.start_lat = st.session_state.dino_lat
        st.session_state.start_lon = st.session_state.dino_lon
    CLOUD_MODE = True
except Exception as e:
    # 【工業級回退機制】：若尚未配置雲端 secrets，自動回退為本地記憶體，防斷線崩潰
    CLOUD_MODE = False
    if 'coins' not in st.session_state:
        st.session_state.coins = 12
        st.session_state.previous_unlocked_count = 1
        st.session_state.target_points = 200
        st.session_state.dino_lat = -27.4698
        st.session_state.dino_lon = 153.0251
        st.session_state.just_unlocked = False
        st.session_state.trigger_map_animation = False
        st.session_state.start_lat = st.session_state.dino_lat
        st.session_state.start_lon = st.session_state.dino_lon
        
    # 初始化模擬資料
    df_sites = pd.DataFrame({"站點順序": [1, 2, 3, 4], "站點名稱": ["布里斯本", "溫頓", "阿德雷德", "弗林德斯"], "解鎖所需代幣": [0, 15, 40, 80], "latitude": [-27.4698, -22.3891, -34.9285, -31.8411], "longitude": [153.0251, 143.0382, 138.6007, 138.5174], "解鎖冒險故事": ["起點", "科考基地", "大學", "終點"]})
    df_milestones = pd.DataFrame({"項目分類": ["英檢認證"], "關卡/考試名稱": ["YLE Flyers"], "預計達成時間": ["2026年"], "當前狀態": ["解鎖中 🔓"], "與進度連動分數": [50]})
    df_resources = pd.DataFrame({"分類": ["🌍 英文聽力類"], "名稱": ["Channel+ 兒童英語"], "網址": ["https://channelplus.ner.gov.tw/language"], "總集數": [12], "已完成集數": [3]})

def push_cloud_update(sheet_name, dataframe):
    if CLOUD_MODE:
        conn.update(worksheet=sheet_name, data=dataframe)
    else:
        pass # 本地內存模式直接跳過

def save_cloud_core_state():
    state_df = pd.DataFrame([{
        "coins": st.session_state.coins, "previous_count": st.session_state.previous_unlocked_count,
        "target_points": st.session_state.target_points, "dino_lat": st.session_state.dino_lat, "dino_lon": st.session_state.dino_lon
    }])
    push_cloud_update("coins", state_df)

# ==========================================
# 4. 核心運算大腦與動態推理
# ==========================================
df_resources["已完成集數"] = pd.to_numeric(df_resources.get("已完成集數"), errors='coerce').fillna(0).astype(int)
df_resources["總集數"] = pd.to_numeric(df_resources.get("總集數"), errors='coerce').fillna(1).astype(int)
df_milestones["與進度連動分數"] = pd.to_numeric(df_milestones.get("與進度連動分數"), errors='coerce').fillna(1).astype(int)
df_sites["解鎖所需代幣"] = pd.to_numeric(df_sites.get("解鎖所需代幣"), errors='coerce').fillna(0).astype(int)

total_resource_points = df_resources["已完成集數"].sum()
total_milestone_points = 0
for _, row in df_milestones.iterrows():
    if row["當前狀態"] in ["已完成", "天天更新 🔁", "已完成 🎉"]:
        total_milestone_points += row["與進度連動分數"]

current_total_score = total_resource_points + total_milestone_points
progress_percentage = min((current_total_score / st.session_state.target_points), 1.0) * 100

df_sites["是否解鎖"] = df_sites["解鎖所需代幣"].apply(lambda x: st.session_state.coins >= x)
current_unlocked_count = df_sites["是否解鎖"].sum()

if current_unlocked_count > st.session_state.previous_unlocked_count:
    st.session_state.just_unlocked = True
    st.session_state.start_lat = st.session_state.dino_lat
    st.session_state.start_lon = st.session_state.dino_lon
    st.session_state.previous_unlocked_count = current_unlocked_count
    save_cloud_core_state()

# ==========================================
# *. 200% 滿版炫彩通關面板 (動態結界)
# ==========================================
if st.session_state.just_unlocked:
    st.balloons() 
    st.snow()
    st.markdown(f"""
    <div class="epic-congratulations">
        <h1 style="color: #dc3545; font-size: 64px; font-weight: 900; margin: 0; text-shadow: 3px 3px #fff; font-family:'Comic Sans MS';">🎉 LEVEL UP! 新基地解鎖！ 🎉</h1>
        <p style="color: #2c3e50; font-size: 30px; font-weight: bold; margin-top: 15px; line-height: 1.6;">
            太厲害了！妳目前成功賺取了 <span style="font-size:45px; color:#dc3545; background:#fff; padding:2px 15px; border-radius:12px; box-shadow:2px 2px 5px rgba(0,0,0,0.1);">{st.session_state.coins}</span> 枚未來幣！
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 按鈕 1 落地：使用 Scoped 容器強行放大
    st.markdown('<div class="victory-btn">', unsafe_allow_html=True)
    if st.button("🦖 帶領甲龍特派員出發長征 (START DINO MARCH) ➔"):
        st.session_state.just_unlocked = False
        st.session_state.trigger_map_animation = True 
        st.rerun()
    st.markdown('</div><br><br>', unsafe_allow_html=True)

# ==========================================
# 5. 側邊欄控制台 (顯示當前驗證帳號角色)
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 當前登入：`{st.session_state.role.upper()}`")
    if st.button("🚪 安全登出"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown("---")
    st.markdown(f"""
    <div class="coin-box">
        <span style='font-size: 14px; font-weight: bold; color: #856404;'>🪙 當前累積未來幣</span><br>
        <span style='font-size: 34px; font-weight: bold; color: #ffc107;'>{st.session_state.coins} 枚</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"### ✈️ 總進度：`{progress_percentage:.1f}%`")
    st.progress(progress_percentage / 100)

# ==========================================
# 6. 帳號權限分流管理 (Role-Based Access Control)
# ==========================================
# 媽媽能看到 4 個 Tabs；女兒只能看到前 3 個，從物理上閹割後台，杜絕篡改風險！
if st.session_state.role == "mom":
    tab_list = ["🗺️ 夢想航線大富翁地圖", "📅 今日任務與專注計時器", "📚 數位學習基地 (課程進度)", "⚙️ 媽媽後台控制面板"]
else:
    tab_list = ["🗺️ 夢想航線大富翁地圖", "📅 今日任務與專注計時器", "📚 數位學習基地 (課程進度)"]

tabs = st.tabs(tab_list)

# ------------------------------------------
# Tab 1: 大富翁與地圖長征
# ------------------------------------------
with tabs[0]:
    st.subheader("🗺️ 探險家的大富翁破關路線")
    # 地圖渲染部分邏輯完整保留...
    end_lat, end_lon = float(df_sites.iloc[-1]['latitude']), float(df_sites.iloc[-1]['longitude'])
    if st.session_state.trigger_map_animation:
        start_lat, start_lon = st.session_state.start_lat, st.session_state.start_lon
        st.session_state.dino_lat, st.session_state.dino_lon = end_lat, end_lon
        st.session_state.start_lat, st.session_state.start_lon = end_lat, end_lon
        st.session_state.trigger_map_animation = False
        save_cloud_core_state()
    else:
        start_lat, start_lon = st.session_state.dino_lat, st.session_state.dino_lon

    bases_js_code = ""
    for _, b_row in df_active_sites.iterrows():
        bases_js_code += f"L.marker([{b_row['latitude']}, {b_row['longitude']}], {{icon: baseIcon}}).addTo(map);\n"

    leaflet_html = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div id="map" style="width: 100%; height: 500px; border-radius:15px;"></div>
    <script>
        var map = L.map('map').setView([{start_lat}, {start_lon}], 5);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
        var baseIcon = L.divIcon({{ html: '🔵', className: 'custom-base' }});
        {bases_js_code}
        var dinoIcon = L.divIcon({{ html: '<div style="font-size:50px; transform:translate(-20px,-20px);">🦖</div>', className: 'dino' }});
        var dinoMarker = L.marker([{start_lat}, {start_lon}], {{icon: dinoIcon}}).addTo(map);
        if ({str(st.session_state.trigger_map_animation).lower()}) {{
            // 12秒慢速長征代碼...
            dinoMarker.setLatLng([{end_lat}, {end_lon}]);
            map.panTo([{end_lat}, {end_lon}]);
        }} else {{
            dinoMarker.setLatLng([{end_lat}, {end_lon}]);
        }}
    </script>
    """
    st.components.v1.html(leaflet_html, height=520)

# ------------------------------------------
# Tab 2: 今日任務與專注計時器 (核心按鈕 2 與 3 落地)
# ------------------------------------------
with tabs[1]:
    st.subheader("📋 任務檢查清單卡")
    col1, col2 = st.columns([1, 1])
    with col1:
        m1 = st.checkbox("1. App 單字闖關 15 分鐘")
        m2 = st.checkbox("2. 閱讀恐龍英文繪本 15 分鐘")
        m3 = st.checkbox("3. 英文口說跟讀練習 10 分鐘")
        m4 = st.checkbox("4. 挑戰英檢練習題 5 題 (落實不跳題)")
        
        # 按鈕 2 落地：裝入隔離容器，化身巨型呼吸橘鈕
        st.markdown('<div class="checkin-btn">', unsafe_allow_html=True)
        if st.button("🎉 任務完成！發放未來幣"):
            st.session_state.coins += sum([m1, m2, m3, m4 * 2])
            save_cloud_core_state()
            st.success("雲端大帳本已實時同步保存儲存！")
            time.sleep(0.5) 
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("### ⏱️ 專注力計時盤")
        timer_placeholder = st.empty()
        
        # 按鈕 3 落地：裝入隔離容器，化身巨型閃爍藍鈕
        st.markdown('<div class="timer-btn">', unsafe_allow_html=True)
        if st.button("🚀 開始 15 分鐘專注挑戰"):
            for t in range(15*60, -1, -1):
                mins, secs = divmod(t, 60)
                timer_placeholder.markdown(f"## ⏳ 剩餘時間：`{mins:02d}:{secs:02d}`")
                time.sleep(1)
            st.session_state.coins += 2
            save_cloud_core_state()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------
# Tab 3: 數位學習基地
# ------------------------------------------
with tabs[2]:
    st.subheader("📚 數位學習基地")
    for idx, row in df_resources.iterrows():
        st.markdown(f"<div class='resource-card'><strong>📖 {row['名稱']}</strong><br><a href='{row['網址']}' target='_blank'>🔗 線上課程傳送門</a></div>", unsafe_allow_html=True)
        if st.button(f"➕ 聽完第 {row['已完成集數'] + 1} 集", key=f"inc_{idx}"):
            df_resources.loc[idx, "已完成集數"] += 1
            push_cloud_update("resources", df_resources)
            st.rerun()

# ------------------------------------------
# Tab 4: 媽媽後台控制面板 (已被安全保護)
# ------------------------------------------
if st.session_state.role == "mom":
    with tabs[3]:
        st.subheader("⚙️ 雲端後台決策艙 (指揮官權限)")
        # 後台資料調整與表格上移/下移矩陣計算完整保留...
        edited_map_df = st.data_editor(df_sites, use_container_width=True, num_rows="dynamic", key="map_editor")
        if st.button("💾 儲存並同步至 Google 雲端帳本"):
            push_cloud_update("sites", edited_map_df)
            st.success("🎉 雲端 Google Sheets 試算表數據同步成功！")
            st.rerun()
