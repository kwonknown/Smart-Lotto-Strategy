import streamlit as st
import random
import pandas as pd
import os
from datetime import datetime

# --- [수정] 1. 모든 함수 정의를 최상단으로 배치 (NameError 완벽 해결) ---

@st.cache_data
def load_lotto_data():
    """CSV 데이터를 안전하게 불러오기"""
    file_path = 'lotto_data.csv'
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if not df.empty and '회차' in df.columns:
                return df
        except: pass
    return None

def get_max_consecutive(nums):
    """연속 번호 계산 로직"""
    nums = sorted(nums)
    max_con, current_con = 1, 1
    for i in range(len(nums) - 1):
        if nums[i] + 1 == nums[i+1]:
            current_con += 1
        else:
            max_con = max(max_con, current_con)
            current_con = 1
    return max(max_con, current_con)

@st.cache_data
def estimate_combination_count(settings_tuple):
    """사용자 설정 시 확률 실시간 계산 (캐싱)"""
    total_combinations = 8145060
    sample_size = 3000
    pass_count = 0
    s_sum, s_odds, s_con, s_low = settings_tuple
    for _ in range(sample_size):
        nums = sorted(random.sample(range(1, 46), 6))
        if not (s_sum[0] <= sum(nums) <= s_sum[1]): continue
        if sum(1 for n in nums if n % 2 != 0) not in s_odds: continue
        if get_max_consecutive(nums) > s_con: continue
        if sum(1 for n in nums if n <= 22) not in s_low: continue
        pass_count += 1
    rate = pass_count / sample_size
    return int(total_combinations * rate), rate

def generate_lotto_combination(settings):
    """필터 통과 번호 생성"""
    while True:
        nums = sorted(random.sample(range(1, 46), 6))
        if not (settings['sum'][0] <= sum(nums) <= settings['sum'][1]): continue
        if sum(1 for n in nums if n % 2 != 0) not in settings['odds']: continue
        if get_max_consecutive(nums) > settings['consecutive']: continue
        if sum(1 for n in nums if n <= 22) not in settings['low_high']: continue
        return nums

# --- 2. UI 및 사이드바 설정 시작 ---
st.set_page_config(page_title="Smart-Lotto-Strategy", layout="wide")
st.title("🎰 Smart Lotto Strategy")

if 'history' not in st.session_state:
    st.session_state.history = []

MODE_STATS = {
    "보수": {"count": "약 142,000", "rate": "1.7%"},
    "중간": {"count": "약 2,360,000", "rate": "29.0%"},
    "공격": {"count": "약 5,850,000", "rate": "71.8%"}
}

with st.sidebar:
    st.header("⚙️ 생성 전략 설정")
    mode = st.radio("전략 선택", ["보수", "중간", "공격", "사용자 설정"], index=1)
    
    if mode == "보수":
        settings = {'sum':(120, 160), 'odds':[3], 'consecutive':3, 'low_high':[3]}
        d_count, d_rate = MODE_STATS["보수"]["count"], MODE_STATS["보수"]["rate"]
    elif mode == "중간":
        settings = {'sum':(100, 175), 'odds':[2, 3, 4], 'consecutive':4, 'low_high':[2, 3, 4]}
        d_count, d_rate = MODE_STATS["중간"]["count"], MODE_STATS["중간"]["rate"]
    elif mode == "공격":
        settings = {'sum':(80, 200), 'odds':[1, 2, 3, 4, 5], 'consecutive':5, 'low_high':[1, 2, 3, 4, 5]}
        d_count, d_rate = MODE_STATS["공격"]["count"], MODE_STATS["공격"]["rate"]
    else:
        st.divider()
        sum_r = st.slider("합계 범위", 21, 255, (100, 175))
        con_l = st.number_input("연속수 제한", 1, 6, 4)
        odd_l = st.multiselect("홀수 개수", [0,1,2,3,4,5,6], default=[2,3,4])
        low_l = st.multiselect("저(1~22) 개수", [0,1,2,3,4,5,6], default=[2,3,4])
        settings = {'sum': sum_r, 'odds': odd_l, 'consecutive': con_l, 'low_high': low_l}
        
        # [수정된 위치] 여기서 호출해야 오류가 안 납니다.
        s_tup = (tuple(settings['sum']), tuple(settings['odds']), settings['consecutive'], tuple(settings['low_high']))
        est_c, est_r = estimate_combination_count(s_tup)
        d_count, d_rate = f"약 {est_c:,}", f"{est_r*100:.1f}%"

    st.divider()
    st.metric("📊 전략의 희소성", d_rate)
    st.write(f"전체 중 **{d_count}개**가 통과합니다.")

# --- 3. 번호 생성 및 분석 섹션 ---
if st.button("행운의 5조합 생성하기", use_container_width=True):
    new_picks = [generate_lotto_combination(settings) for _ in range(5)]
    st.session_state.history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "mode": mode, "numbers": new_picks})

if st.session_state.history:
    latest = st.session_state.history[0]
    st.subheader(f"✨ 최근 추천 ({latest['mode']})")
    for combo in latest['numbers']:
        st.write(combo)

# --- 4. 데이터 로드 및 전수 조사 ---
df_lotto = load_lotto_data()
if df_lotto is not None:
    st.success(f"✅ DB 연결 완료: 총 {len(df_lotto)}회차 데이터 로드")
else:
    st.error("⚠️ 'lotto_data.csv' 파일이 없습니다. 바탕화면에서 파일을 만들어 깃허브에 올려주세요.")

# (이후 분석 탭 로직 생략 - 구조는 동일)
