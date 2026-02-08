import streamlit as st
import random
import pandas as pd
import os
from datetime import datetime

# --- 1. 핵심 로직 함수 ---
def get_max_consecutive(nums):
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

def generate_lotto_combination(settings):
    while True:
        nums = sorted(random.sample(range(1, 46), 6))
        if not (settings['sum'][0] <= sum(nums) <= settings['sum'][1]): continue
        odds = sum(1 for n in nums if n % 2 != 0)
        if odds not in settings['odds']: continue
        # 사용자 요청 반영: 보수(3), 중간(4), 공격(5) 연속수 필터
        if get_max_consecutive(nums) > settings['consecutive']: continue
        lows = sum(1 for n in nums if n <= 22)
        if lows not in settings['low_high']: continue
        return nums

# --- 2. [변경됨] CSV 기반 DB 조회 함수 ---
def get_lotto_win_info_from_db(drw_no):
    file_path = 'lotto_data.csv'
    if not os.path.exists(file_path):
        st.error("⚠️ lotto_data.csv 파일이 없습니다. 파일을 먼저 생성해주세요.")
        return None, None
    
    df = pd.read_csv(file_path)
    # 입력한 회차와 일치하는 행 찾기
    row = df[df['회차'] == drw_no]
    
    if not row.empty:
        win_nums = row.iloc[0, 1:7].tolist() # 번호1~6
        bonus_num = row.iloc[0, 7]           # 보너스
        return [int(x) for x in win_nums], int(bonus_num)
    return None, None

def check_rank(my, win, bonus):
    match = len(set(my) & set(win))
    if match == 6: return "🥇 1등"
    if match == 5 and bonus in my: return "🥈 2등"
    if match == 5: return "🥉 3등"
    if match == 4: return "4등"
    if match == 3: return "5등"
    return "낙첨"

# --- 3. UI 및 디자인 설정 ---
st.set_page_config(page_title="Smart-Lotto-Strategy", layout="wide")
st.title("🎰 Smart Lotto Strategy (DB Mode)")

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

# --- 4. 사이드바 설정 ---
with st.sidebar:
    st.header("⚙️ 모드 설정")
    mode = st.radio("전략 선택", ["보수", "중간", "공격"], index=1)
    if mode == "보수": settings = {'sum':(120,160), 'odds':[3], 'consecutive':3, 'low_high':[3]}
    elif mode == "중간": settings = {'sum':(100,175), 'odds':[2,3,4], 'consecutive':4, 'low_high':[2,3,4]}
    else: settings = {'sum':(80,200), 'odds':[1,2,3,4,5], 'consecutive':5, 'low_high':[1,2,3,4,5]}
    st.divider()
    st.info(f"**{mode} 모드 작동 중**")

# --- 5. 메인: 번호 생성 ---
if st.button("행운의 5조합 생성하기", use_container_width=True):
    new_picks = [generate_lotto_combination(settings) for _ in range(5)]
    st.session_state.history.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "mode": mode, "numbers": new_picks})

if st.session_state.history:
    latest = st.session_state.history[0]
    st.subheader(f"✨ 최근 추천 ({latest['mode']})")
    group_labels = "ABCDE"
    for i, combo in enumerate(latest['numbers']):
        balls_html = "".join([f'<div class="ball" style="background-color:{"#fbc400" if n<=10 else "#69c8f2" if n<=20 else "#ff7272" if n<=30 else "#aaaaaa" if n<=40 else "#b0d840"};">{n}</div>' for n in combo])
        st.markdown(f'<div class="lotto-container"><div class="lotto-label">{group_labels[i]}조</div>{balls_html}</div>', unsafe_allow_html=True)

# --- 6. [DB 방식] 과거 당첨 확인 ---
st.divider()
st.header("🎯 로또 DB 당첨 확인")
col1, col2 = st.columns([3, 1])
with col1:
    target_drw = st.number_input("조회할 회차 입력 (CSV에 있는 회차)", min_value=1, value=1150)

if st.button("결과 확인"):
    if not st.session_state.history:
        st.warning("번호를 먼저 생성해주세요.")
    else:
        win_n, bonus_n = get_lotto_win_info_from_db(target_drw)
        if win_n:
            st.success(f"✅ DB 데이터 확인 완료: {target_drw}회 당첨번호")
            res_table = []
            for i, c in enumerate(st.session_state.history[0]['numbers']):
                res_table.append({"조": "ABCDE"[i]+"조", "내 번호": str(c), "결과": check_rank(c, win_n, bonus_n)})
            st.table(pd.DataFrame(res_table))
            if any("등" in r['결과'] for r in res_table): st.balloons()
        else:
            st.error(f"⚠️ {target_drw}회 정보가 CSV 파일에 없습니다. 내용을 업데이트해주세요.")

# --- 7. 히스토리 ---
st.divider()
with st.expander("📜 히스토리 보기"):
    if st.session_state.history:
        for h in st.session_state.history:
            st.write(f"**📅 {h['time']} ({h['mode']})**")
            st.table(pd.DataFrame(h['numbers'], index=[f"{"ABCDE"[i]}조" for i in range(5)]))
