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

def estimate_combination_count(settings):
    """필터 조건을 통과할 확률을 계산하여 전체 조합 수 추정"""
    total_combinations = 8145060
    sample_size = 10000 # 1만 개 샘플 테스트
    pass_count = 0
    
    for _ in range(sample_size):
        nums = sorted(random.sample(range(1, 46), 6))
        # 필터 조건 체크
        if not (settings['sum'][0] <= sum(nums) <= settings['sum'][1]): continue
        if sum(1 for n in nums if n % 2 != 0) not in settings['odds']: continue
        if get_max_consecutive(nums) > settings['consecutive']: continue
        if sum(1 for n in nums if n <= 22) not in settings['low_high']: continue
        pass_count += 1
    
    # 통과 확률 계산
    pass_rate = pass_count / sample_size
    estimated_count = int(total_combinations * pass_rate)
    return estimated_count, pass_rate

# --- 사이드바 또는 메인 화면에 출력 ---
st.sidebar.divider()
est_count, est_rate = estimate_combination_count(settings)
st.sidebar.metric("📊 전략의 희소성", f"{est_rate*100:.1f}%")
st.sidebar.write(f"전체 814만 개 중 약 **{est_count:,}개**의 조합이 이 필터를 통과합니다.")

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

# --- 사이드바: 모드 설정 및 커스텀 제어 ---
with st.sidebar:
    st.header("⚙️ 생성 전략 설정")
    mode = st.radio("전략 선택", ["보수", "중간", "공격", "사용자 설정"], index=1)
    
    # 1. 모드별 고정 값 설정
    if mode == "보수":
        settings = {'sum':(120, 160), 'odds':[3], 'consecutive':3, 'low_high':[3]}
    elif mode == "중간":
        settings = {'sum':(100, 175), 'odds':[2, 3, 4], 'consecutive':4, 'low_high':[2, 3, 4]}
    elif mode == "공격":
        settings = {'sum':(80, 200), 'odds':[1, 2, 3, 4, 5], 'consecutive':5, 'low_high':[1, 2, 3, 4, 5]}
    else: # 사용자 설정 모드: 직접 수치 제어
        st.divider()
        st.subheader("🛠️ 커스텀 필터 제어")
        sum_range = st.slider("합계 범위 설정", 21, 255, (100, 175))
        con_limit = st.number_input("연속수 제한 (N연번까지)", 1, 6, 4)
        
        # 멀티 셀렉트로 홀짝/저고 비중 선택
        odd_list = st.multiselect("허용할 홀수 개수", [0,1,2,3,4,5,6], default=[2,3,4])
        low_high_list = st.multiselect("허용할 저(1~22) 개수", [0,1,2,3,4,5,6], default=[2,3,4])
        
        settings = {
            'sum': sum_range,
            'odds': odd_list,
            'consecutive': con_limit,
            'low_high': low_high_list
        }

    # 2. 현재 적용 중인 기준 시각화 (표)
    st.divider()
    st.subheader("📋 적용 기준 요약")
    filter_info = {
        "지표": ["합계 범위", "홀짝 비중", "연속수 제한", "저고 비중"],
        "기준": [
            f"{settings['sum'][0]} ~ {settings['sum'][1]}",
            f"{settings['odds']}개 허용",
            f"{settings['consecutive']}연번 이하",
            f"{settings['low_high']}개 허용"
        ]
    }
    st.table(pd.DataFrame(filter_info))

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

# --- [추가/수정된 로직] 전수 조사 함수 ---
def analyze_all_history(my_combinations):
    file_path = 'lotto_data.csv'
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    summary_results = []

    # 생성된 5개 조합(A~E조) 각각에 대해 전수 조사
    for idx, my_nums in enumerate(my_combinations):
        my_set = set(my_nums)
        label = "ABCDE"[idx] + "조"
        
        counts = {"1등": 0, "2등": 0, "3등": 0, "4등": 0, "5등": 0}
        details = [] # 당첨된 사례 저장용

        for _, row in df.iterrows():
            win_nums = set(row[1:7].astype(int))
            bonus = int(row[7])
            match_count = len(my_set & win_nums)

            rank = None
            if match_count == 6: rank = "1등"
            elif match_count == 5 and bonus in my_set: rank = "2등"
            elif match_count == 5: rank = "3등"
            elif match_count == 4: rank = "4등"
            elif match_count == 3: rank = "5등"

            if rank:
                counts[rank] += 1
                # 1, 2, 3등 같은 고액 당첨은 기록 보관
                if rank in ["1등", "2등", "3등"]:
                    details.append(f"{int(row['회차'])}회({rank})")

        summary_results.append({
            "조": label,
            "번호": str(my_nums),
            "1등": counts["1등"],
            "2등": counts["2등"],
            "3등": counts["3등"],
            "4등": counts["4등"],
            "5등": counts["5등"],
            "고액당첨이력": ", ".join(details) if details else "없음"
        })
    
    return pd.DataFrame(summary_results)

# --- UI 부분 수정 (결과 확인 버튼 클릭 시) ---
st.divider()
st.header("📊 역대 전수 조사 (1회~최신)")
if st.button("과거 모든 회차와 대조하기", use_container_width=True):
    if not st.session_state.history:
        st.warning("번호를 먼저 생성해주세요.")
    else:
        with st.spinner('역대 데이터를 분석 중입니다...'):
            latest_picks = st.session_state.history[0]['numbers']
            analysis_df = analyze_all_history(latest_picks)
            
            if analysis_df is not None:
                st.success("✅ 분석 완료! 생성된 번호의 과거 당첨 기록입니다.")
                st.table(analysis_df)
                
                # 고액 당첨 이력이 있다면 축하 메시지
                if analysis_df[["1등", "2등", "3등"]].sum().sum() > 0:
                    st.balloons()
                    st.info("💡 와우! 과거에 고액 당첨 이력이 있는 번호가 포함되어 있습니다.")
            else:
                st.error("lotto_data.csv 파일을 찾을 수 없습니다.")

# --- 7. 히스토리 ---
st.divider()
with st.expander("📜 히스토리 보기"):
    if st.session_state.history:
        for h in st.session_state.history:
            st.write(f"**📅 {h['time']} ({h['mode']})**")
            st.table(pd.DataFrame(h['numbers'], index=[f"{"ABCDE"[i]}조" for i in range(5)]))
