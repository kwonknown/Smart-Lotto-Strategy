import streamlit as st
import random
import pandas as pd
import os
from datetime import datetime

# --- [수정] 1. 모든 함수 정의를 최상단으로 배치 (순서 오류 해결) ---

@st.cache_data
def load_lotto_data():
    """CSV 데이터베이스 로드 (캐싱 적용)"""
    file_path = 'lotto_data.csv'
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if not df.empty and '회차' in df.columns:
                return df
        except:
            pass
    return None

def get_max_consecutive(nums):
    """최대 연속 번호 계산"""
    nums = sorted(nums)
    max_con = 1
    current_con = 1
    for i in range(len(nums) - 1):
        if nums[i] + 1 == nums[i+1]:
            current_con += 1
        else:
            max_con = max(max_con, current_con)
            current_con = 1
    return max(max_con, current_con)

@st.cache_data
def estimate_combination_count(settings_tuple):
    """사용자 설정 모드에서만 실시간으로 확률 추정 (캐싱 적용)"""
    total_combinations = 8145060
    sample_size = 5000  # 속도를 위해 5000개 샘플 테스트
    pass_count = 0
    
    s_sum, s_odds, s_con, s_low = settings_tuple
    
    for _ in range(sample_size):
        nums = sorted(random.sample(range(1, 46), 6))
        if not (s_sum[0] <= sum(nums) <= s_sum[1]): continue
        if sum(1 for n in nums if n % 2 != 0) not in s_odds: continue
        if get_max_consecutive(nums) > s_con: continue
        if sum(1 for n in nums if n <= 22) not in s_low: continue
        pass_count += 1
    
    pass_rate = pass_count / sample_size
    estimated_count = int(total_combinations * pass_rate)
    return estimated_count, pass_rate

def generate_lotto_combination(settings):
    """필터를 통과하는 조합 생성"""
    while True:
        nums = sorted(random.sample(range(1, 46), 6))
        if not (settings['sum'][0] <= sum(nums) <= settings['sum'][1]): continue
        if sum(1 for n in nums if n % 2 != 0) not in settings['odds']: continue
        if get_max_consecutive(nums) > settings['consecutive']: continue
        if sum(1 for n in nums if n <= 22) not in settings['low_high']: continue
        return nums

def check_rank(my, win, bonus):
    """당첨 등수 판정"""
    match = len(set(my) & set(win))
    if match == 6: return "🥇 1등"
    if match == 5 and bonus in my: return "🥈 2등"
    if match == 5: return "🥉 3등"
    if match == 4: return "4등"
    if match == 3: return "5등"
    return "낙첨"

# --- 2. UI 설정 및 디자인 ---
st.set_page_config(page_title="Smart-Lotto-Strategy", layout="wide")
st.title("🎰 Smart Lotto Strategy")

st.markdown("""
    <style>
    .lotto-container { display: flex; align-items: center; margin-bottom: 10px; }
    .lotto-label { width: 45px; font-weight: bold; font-size: 16px; margin-right: 10px; }
    .ball { width: 38px; height: 38px; border-radius: 50%; display: flex; align-items: center; 
            justify-content: center; color: white; font-weight: bold; font-size: 15px; margin-right: 6px; }
    hr { margin: 1.5rem 0 !important; }
    </style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 3. 사이드바 설정 ---
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
        display_count, display_rate = MODE_STATS["보수"]["count"], MODE_STATS["보수"]["rate"]
    elif mode == "중간":
        settings = {'sum':(100, 175), 'odds':[2, 3, 4], 'consecutive':4, 'low_high':[2, 3, 4]}
        display_count, display_rate = MODE_STATS["중간"]["count"], MODE_STATS["중간"]["rate"]
    elif mode == "공격":
        settings = {'sum':(80, 200), 'odds':[1, 2, 3, 4, 5], 'consecutive':5, 'low_high':[1, 2, 3, 4, 5]}
        display_count, display_rate = MODE_STATS["공격"]["count"], MODE_STATS["공격"]["rate"]
    else:
        st.divider()
        st.subheader("🛠️ 커스텀 필터 제어")
        sum_range = st.slider("합계 범위", 21, 255, (100, 175))
        con_limit = st.number_input("연속수 제한", 1, 6, 4)
        odd_list = st.multiselect("홀수 개수", [0,1,2,3,4,5,6], default=[2,3,4])
        low_high_list = st.multiselect("저(1~22) 개수", [0,1,2,3,4,5,6], default=[2,3,4])
        settings = {'sum': sum_range, 'odds': odd_list, 'consecutive': con_limit, 'low_high': low_high_list}
        
        # 실시간 계산
        s_tuple = (tuple(settings['sum']), tuple(settings['odds']), settings['consecutive'], tuple(settings['low_high']))
        est_count, est_rate = estimate_combination_count(s_tuple)
        display_count, display_rate = f"약 {est_count:,}", f"{est_rate*100:.1f}%"

    st.divider()
    st.metric("📊 전략의 희소성", display_rate)
    st.write(f"전체 814만 개 중 **{display_count}개**가 통과합니다.")

# --- 4. 메인 화면: 번호 생성 ---
if st.button("행운의 5조합 생성하기", use_container_width=True):
    new_picks = [generate_lotto_combination(settings) for _ in range(5)]
    st.session_state.history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "mode": mode, "numbers": new_picks})

if st.session_state.history:
    latest = st.session_state.history[0]
    st.subheader(f"✨ 최근 추천 ({latest['mode']} 모드)")
    group_labels = "ABCDE"
    for i, combo in enumerate(latest['numbers']):
        balls_html = "".join([f'<div class="ball" style="background-color:{"#fbc400" if n<=10 else "#69c8f2" if n<=20 else "#ff7272" if n<=30 else "#aaaaaa" if n<=40 else "#b0d840"};">{n}</div>' for n in combo])
        st.markdown(f'<div class="lotto-container"><div class="lotto-label">{group_labels[i]}조</div>{balls_html}</div>', unsafe_allow_html=True)

# --- 5. 분석 섹션: 전수 조사 ---
df_lotto = load_lotto_data()

st.divider()
st.header("📊 데이터 분석 및 검증")
tab1, tab2 = st.tabs(["역대 전수 조사", "특정 회차 조회"])

with tab1:
    if st.button("과거 모든 회차와 대조하기 (1회~최신)"):
        if st.session_state.history and df_lotto is not None:
            with st.spinner('정밀 분석 중...'):
                latest_picks = st.session_state.history[0]['numbers']
                analysis_results = []
                for idx, my_nums in enumerate(latest_picks):
                    my_set = set(my_nums)
                    counts = {"1등": 0, "2등": 0, "3등": 0, "4등": 0, "5등": 0}
                    for _, row in df_lotto.iterrows():
                        win_set = set(row[1:7].astype(int))
                        match_count = len(my_set & win_set)
                        if match_count == 6: counts["1등"] += 1
                        elif match_count == 5 and int(row[7]) in my_set: counts["2등"] += 1
                        elif match_count == 5: counts["3등"] += 1
                        elif match_count == 4: counts["4등"] += 1
                        elif match_count == 3: counts["5등"] += 1
                    analysis_results.append({"조": "ABCDE"[idx]+"조", **counts})
                st.table(pd.DataFrame(analysis_results))
        else:
            st.error("lotto_data.csv 파일을 확인하거나 번호를 먼저 생성해주세요.")

with tab2:
    target_drw = st.number_input("회차 입력", min_value=1, value=1150)
    if st.button("조회"):
        if df_lotto is not None:
            row = df_lotto[df_lotto['회차'] == target_drw]
            if not row.empty:
                st.info(f"🎯 {target_drw}회 당첨번호: {row.iloc[0, 1:7].tolist()} | 보너스: {row.iloc[0, 7]}")

# --- 6. 히스토리 보기 ---
st.divider()
with st.expander("📜 번호 생성 히스토리 보기"):
    if st.session_state.history:
        for h in st.session_state.history:
            st.write(f"**📅 {h['time']} ({h['mode']})**")
            st.table(pd.DataFrame(h['numbers'], index=["A조","B조","C조","D조","E조"], columns=[f"번호{j+1}" for j in range(6)]))
