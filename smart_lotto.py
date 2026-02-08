import streamlit as st
import random
import pandas as pd
from datetime import datetime

# --- 필터링 함수 정의 ---
def get_max_consecutive(nums):
    """최대 연속수 계산"""
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

def generate_lotto_combination(mode_settings):
    """설정된 필터에 맞는 조합 1개 생성"""
    while True:
        nums = sorted(random.sample(range(1, 46), 6))
        
        # 1. 합계 필터
        if not (mode_settings['sum'][0] <= sum(nums) <= mode_settings['sum'][1]):
            continue
        
        # 2. 홀짝 필터
        odds = sum(1 for n in nums if n % 2 != 0)
        if odds not in mode_settings['odds']:
            continue
            
        # 3. 연속수 필터
        if get_max_consecutive(nums) > mode_settings['consecutive']:
            continue
            
        # 4. 저고 필터 (1~22: 저, 23~45: 고)
        lows = sum(1 for n in nums if n <= 22)
        if lows not in mode_settings['low_high']:
            continue
            
        return nums

# --- UI 설정 ---
st.set_page_config(page_title="AI 로또 전략 분석기", layout="wide")
st.title("🎰 AI 전략 로또 번호 생성기")

# 세션 상태 초기화 (히스토리 저장용)
if 'history' not in st.session_state:
    st.session_state.history = []

# --- 사이드바: 모드 설정 ---
with st.sidebar:
    st.header("⚙️ 분석 모드 설정")
    mode = st.radio("전략 선택", ["보수", "중간", "공격"])
    
    if mode == "보수":
        settings = {'sum': (120, 160), 'odds': [3], 'consecutive': 1, 'low_high': [3]}
    elif mode == "중간":
        settings = {'sum': (100, 175), 'odds': [2, 3, 4], 'consecutive': 2, 'low_high': [2, 3, 4]}
    else: # 공격
        settings = {'sum': (80, 200), 'odds': [1, 2, 3, 4, 5], 'consecutive': 4, 'low_high': [1, 2, 3, 4, 5]}

    st.write(f"**현재 필터 강도:** {mode}")
    st.info(f"합계: {settings['sum'][0]}~{settings['sum'][1]}\n\n홀짝/저고: {settings['odds']}\n\n연속수: {settings['consecutive']}개 이하")

# --- 메인 화면: 번호 생성 ---
if st.button("행운의 5조합 생성하기", use_container_width=True):
    new_combinations = []
    for _ in range(5):
        combo = generate_lotto_combination(settings)
        new_combinations.append(combo)
    
    # 히스토리 저장
    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "numbers": new_combinations
    })

# --- 결과 출력 (로또 용지 스타일) ---
if st.session_state.history:
    latest = st.session_state.history[0]
    st.subheader(f"✨ 최근 추천 조합 ({latest['mode']} 모드)")
    
    # 조 이름 리스트 (A조 ~ E조)
    group_names = ["A조", "B조", "C조", "D조", "E조"]
    
    for i, combo in enumerate(latest['numbers']):
        # 조 이름과 번호를 포함한 전체 컨테이너 (상하 간격을 위해 margin-bottom 추가)
        st.markdown(f"### {group_names[i]}")
        cols = st.columns([0.5, 1, 1, 1, 1, 1, 1]) # 조 이름을 위한 앞칸 확보
        
        for idx, num in enumerate(combo):
            # 번호별 색상 로직
            color = "orange" if num <= 10 else "blue" if num <= 20 else "red" if num <= 30 else "gray" if num <= 40 else "green"
            
            # cols[idx+1]에 번호 출력 (상하 간격을 위해 padding 추가)
            cols[idx+1].markdown(f"""
                <div style="background-color:{color}; color:white; border-radius:50%; 
                width:50px; height:50px; display:flex; align-items:center; 
                justify-content:center; font-weight:bold; font-size:20px; 
                margin: 10px auto;">
                    {num}
                </div>
            """, unsafe_allow_html=True)
        st.write("") # 조별 구분을 위한 추가 간격

    st.divider()

# --- 히스토리 섹션 (한 조합당 한 줄씩) ---
with st.expander("📜 번호 생성 히스토리 보기"):
    if st.session_state.history:
        for entry in st.session_state.history:
            st.markdown(f"**📅 생성 시간: {entry['time']} ({entry['mode']} 모드)**")
            group_labels = ["A조", "B조", "C조", "D조", "E조"]
            for i, nums in enumerate(entry['numbers']):
                # 한 조합을 한 줄에 깔끔하게 표시
                st.write(f"- **{group_labels[i]}:** {', '.join(map(str, nums))}")
            st.divider()
    else:
        st.write("아직 생성된 히스토리가 없습니다.")
