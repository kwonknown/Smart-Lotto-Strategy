import streamlit as st
import random
import pandas as pd
import os
import requests
from datetime import datetime

# --- [1] 함수 정의 (무조건 최상단) ---

@st.cache_data(ttl=3600) # 1시간 동안은 API 다시 안 불러오고 저장된 값 사용
def get_latest_lotto_api(drw_no):
    """동행복권 API 시도 (실패 시 None 반환)"""
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200 and "html" not in response.text:
            data = response.json()
            if data.get("returnValue") == "success":
                nums = [data[f"drwtNo{i}"] for i in range(1, 7)]
                return nums, data["bnusNo"]
    except: pass
    return None, None

def load_local_db(drw_no):
    """CSV에서 데이터 찾기"""
    if os.path.exists('lotto_data.csv'):
        df = pd.read_csv('lotto_data.csv')
        row = df[df['회차'] == drw_no]
        if not row.empty:
            return row.iloc[0, 1:7].tolist(), row.iloc[0, 7]
    return None, None

def get_max_consecutive(nums):
    nums = sorted(nums)
    max_c, cur_c = 1, 1
    for i in range(len(nums)-1):
        if nums[i]+1 == nums[i+1]: cur_c += 1
        else: max_c = max(max_c, cur_c); cur_c = 1
    return max(max_c, cur_c)

@st.cache_data
def estimate_count(s_tuple):
    """희소성 계산 (캐싱)"""
    total, sample, pass_c = 8145060, 3000, 0
    s_sum, s_odd, s_con, s_low = s_tuple
    for _ in range(sample):
        n = sorted(random.sample(range(1, 46), 6))
        if not (s_sum[0] <= sum(n) <= s_sum[1]): continue
        if sum(1 for x in n if x % 2 != 0) not in s_odd: continue
        if get_max_consecutive(n) > s_con: continue
        if sum(1 for x in n if x <= 22) not in s_low: continue
        pass_c += 1
    rate = pass_c / sample
    return int(total * rate), rate

# --- [2] UI 설정 ---
st.set_page_config(page_title="Smart-Lotto-Strategy", layout="wide")
st.title("🎰 Smart Lotto Strategy (Hybrid API)")

# 디자인용 CSS (공 모양)
st.markdown("""
    <style>
    .ball { width: 35px; height: 35px; border-radius: 50%; display: inline-flex; align-items: center; 
            justify-content: center; color: white; font-weight: bold; margin: 2px; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

# --- [3] 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 전략 설정")
    mode = st.radio("모드", ["보수", "중간", "공격", "사용자"], index=1)
    if mode == "보수": settings = {'sum':(120,160), 'odds':[3], 'consecutive':3, 'low_high':[3]}
    elif mode == "중간": settings = {'sum':(100,175), 'odds':[2,3,4], 'consecutive':4, 'low_high':[2,3,4]}
    elif mode == "공격": settings = {'sum':(80,200), 'odds':[1,2,3,4,5], 'consecutive':5, 'low_high':[1,2,3,4,5]}
    else: # 커스텀
        s_r = st.slider("합계", 21, 255, (100, 175))
        c_l = st.number_input("연속수 제한", 1, 6, 4)
        settings = {'sum': s_r, 'odds': [2,3,4], 'consecutive': c_l, 'low_high': [2,3,4]}

    tup = (tuple(settings['sum']), tuple(settings['odds']), settings['consecutive'], tuple(settings['low_high']))
    count, rate = estimate_count(tup)
    st.metric("📊 필터 통과율", f"{rate*100:.1f}%")
    st.write(f"조합 수: 약 {count:,}개")

# --- [4] 번호 생성 ---
if st.button("🚀 행운의 조합 생성", use_container_width=True):
    res = [sorted(random.sample(range(1, 46), 6)) for _ in range(5)]
    st.session_state.last_picks = res

if 'last_picks' in st.session_state:
    st.subheader("✨ 추천 번호")
    for combo in st.session_state.last_picks:
        html = "".join([f'<div class="ball" style="background-color:{"#fbc400" if n<=10 else "#69c8f2" if n<=20 else "#ff7272" if n<=30 else "#aaaaaa" if n<=40 else "#b0d840"};">{n}</div>' for n in combo])
        st.markdown(html, unsafe_allow_html=True)

# --- [5] 과거 당첨 확인 (API + CSV 하이브리드) ---
st.divider()
st.header("🎯 당첨 확인 (API/DB)")
target = st.number_input("회차 입력", min_value=1, value=1150)

if st.button("결과 확인"):
    # 1. API 먼저 시도
    with st.spinner('데이터 연동 중...'):
        win_n, bonus_n = get_latest_lotto_api(target)
        source = "실시간 API"
        
        # 2. API 실패 시 CSV 로드
        if not win_n:
            win_n, bonus_n = load_local_db(target)
            source = "로컬 DB"

    if win_n:
        st.success(f"✅ {source} 연결 성공! ({target}회)")
        st.write(f"당첨번호: {win_n} + 보너스: {bonus_n}")
    else:
        st.error("데이터를 가져올 수 없습니다. 서버 차단 혹은 CSV 파일을 확인하세요.")
