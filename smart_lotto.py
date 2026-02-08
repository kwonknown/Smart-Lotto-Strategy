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
    
    group_names = ["A조", "B조", "C조", "D조", "E조"]
    
    # 상하좌우 여백 및 열 간격 제어를 위한 CSS
    st.markdown("""
        <style>
        .lotto-row {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            gap: 10px; /* 공 사이의 간격 고정 */
        }
        .lotto-label {
            width: 50px;
            font-size: 1.2rem;
            font-weight: bold;
        }
        .ball {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 18px;
        }
        </style>
    """, unsafe_allow_html=True)

    for i, combo in enumerate(latest['numbers']):
        # 한 줄을 HTML 컨테이너로 구성
        balls_html = "".join([
            f'<div class="ball" style="background-color:{"orange" if n <= 10 else "blue" if n <= 20 else "red" if n <= 30 else "gray" if n <= 40 else "green"};">{n}</div>'
            for n in combo
        ])
        
        st.markdown(f"""
            <div class="lotto-row">
                <div class="lotto-label">{group_names[i]}</div>
                {balls_html}
            </div>
        """, unsafe_allow_html=True)

    st.divider()

# --- 히스토리 섹션 (깔끔한 한 줄 정리) ---
with st.expander("📜 번호 생성 히스토리 보기"):
    if st.session_state.history:
        for entry in st.session_state.history:
            st.markdown(f"**📅 {entry['time']} ({entry['mode']})**")
            # 히스토리를 표 형태로 깔끔하게 표시
            history_df = pd.DataFrame(entry['numbers'], 
                                    index=["A조", "B조", "C조", "D조", "E조"], 
                                    columns=["1", "2", "3", "4", "5", "6"])
            st.table(history_df)
    else:
        st.write("아직 생성된 히스토리가 없습니다.")
