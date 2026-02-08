import streamlit as st
import random
import pandas as pd
import requests
from datetime import datetime

# --- 1. 핵심 로직 함수 ---
def get_max_consecutive(nums):
    """연속 번호 개수 계산"""
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
    """필터 조건에 맞는 번호 1세트 생성"""
    while True:
        nums = sorted(random.sample(range(1, 46), 6))
        # 합계 필터
        if not (settings['sum'][0] <= sum(nums) <= settings['sum'][1]): continue
        # 홀짝 필터
        odds = sum(1 for n in nums if n % 2 != 0)
        if odds not in settings['odds']: continue
        # 연속수 필터 (사용자 요청 반영: 보수 3, 중간 4, 공격 5)
        if get_max_consecutive(nums) > settings['consecutive']: continue
        # 저고 필터 (1~22 저, 23~45 고)
        lows = sum(1 for n in nums if n <= 22)
        if lows not in settings['low_high']: continue
        return nums

def get_lotto_win_info(drw_no):
    """차단 가능성을 최소화한 강력한 API 호출 로직"""
    # 동행복권 공식 API 주소
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    
    # 실제 크롬 브라우저가 보내는 것과 거의 흡사한 상세 헤더
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.dhlottery.co.kr/common.do?method=main",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    try:
        # verify=False를 통해 SSL 인증서 문제를 무시하고 강제로 연결 시도
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=10, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                win_nums = [data[f"drwtNo{i}"] for i in range(1, 7)]
                return win_nums, data["bnusNo"]
    except Exception as e:
        # 에러 내용을 화면에 잠깐 띄워 확인 (디버깅 완료 후 삭제 가능)
        st.error(f"데이터 연결 중 특이사항 발생: {str(e)}")
    
    return None, None

def check_rank(my, win, bonus):
    """당첨 등수 판정 (낙첨 포함)"""
    match = len(set(my) & set(win))
    if match == 6: return "🥇 1등"
    if match == 5 and bonus in my: return "🥈 2등"
    if match == 5: return "🥉 3등"
    if match == 4: return "4등"
    if match == 3: return "5등"
    return "낙첨"

# --- 2. UI 및 디자인 설정 ---
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

# --- 3. 사이드바: 모드 설정 (연속수 기준 상향) ---
with st.sidebar:
    st.header("⚙️ 모드 설정")
    mode = st.radio("전략 선택", ["보수", "중간", "공격"], index=1)
    
    if mode == "보수":
        # 보수: 3연번까지 허용
        settings = {'sum':(120,160), 'odds':[3], 'consecutive':3, 'low_high':[3]}
    elif mode == "중간":
        # 중간: 4연번까지 허용
        settings = {'sum':(100,175), 'odds':[2,3,4], 'consecutive':4, 'low_high':[2,3,4]}
    else: 
        # 공격: 5연번까지 허용
        settings = {'sum':(80,200), 'odds':[1,2,3,4,5], 'consecutive':5, 'low_high':[1,2,3,4,5]}
    
    st.divider()
    st.info(f"**현재 필터: {mode}**\n\n- 합계: {settings['sum'][0]}~{settings['sum'][1]}\n- 연속수 허용: {settings['consecutive']}개 까지")

# --- 4. 메인: 번호 생성 버튼 ---
if st.button("행운의 5조합 생성하기", use_container_width=True):
    new_picks = [generate_lotto_combination(settings) for _ in range(5)]
    st.session_state.history.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "numbers": new_picks
    })

# --- 5. 결과 출력 (최신 번호) ---
if st.session_state.history:
    latest = st.session_state.history[0]
    st.subheader(f"✨ 최근 추천 ({latest['mode']} 모드)")
    group_labels = "ABCDE"
    for i, combo in enumerate(latest['numbers']):
        balls_html = "".join([f'<div class="ball" style="background-color:{"#fbc400" if n<=10 else "#69c8f2" if n<=20 else "#ff7272" if n<=30 else "#aaaaaa" if n<=40 else "#b0d840"};">{n}</div>' for n in combo])
        st.markdown(f'<div class="lotto-container"><div class="lotto-label">{group_labels[i]}조</div>{balls_html}</div>', unsafe_allow_html=True)

# --- 6. 과거 당첨 확인 (백테스팅) ---
st.divider()
st.header("🎯 과거 당첨 확인")
col1, col2 = st.columns([3, 1])
with col1:
    # 1150회는 확실히 데이터가 있는 회차입니다. 테스트용으로 좋습니다.
    target_drw = st.number_input("조회할 회차 입력", min_value=1, value=1150)

if st.button("결과 확인"):
    if not st.session_state.history:
        st.warning("먼저 '행운의 5조합 생성하기' 버튼을 눌러 번호를 생성해주세요.")
    else:
        with st.spinner('당첨 번호를 불러오는 중...'):
            win_n, bonus_n = get_lotto_win_info(target_drw)
            
        if win_n:
            st.success(f"✅ {target_drw}회 당첨번호: {win_n} + 보너스 {bonus_n}")
            res_table = []
            group_labels = "ABCDE"
            # 현재 화면에 보이는(가장 최근 생성된) 번호와 비교
            latest_nums = st.session_state.history[0]['numbers']
            
            for i, c in enumerate(latest_nums):
                rank = check_rank(c, win_n, bonus_n)
                res_table.append({
                    "조": group_labels[i]+"조",
                    "내 번호": str(c),
                    "결과": rank
                })
            
            # 결과 표 출력
            st.table(pd.DataFrame(res_table))
            
            if any("등" in r['결과'] for r in res_table):
                st.balloons()
        else:
            st.error("당첨 정보를 가져오지 못했습니다. 회차 번호를 다시 확인하거나 잠시 후 시도해 주세요.")

# --- 7. 히스토리 섹션 ---
st.divider()
with st.expander("📜 번호 생성 히스토리 보기"):
    if st.session_state.history:
        for h in st.session_state.history:
            st.write(f"**📅 {h['time']} ({h['mode']})**")
            group_labels = "ABCDE"
            df_h = pd.DataFrame(h['numbers'], index=[f"{group_labels[i]}조" for i in range(5)], columns=[f"번호{j+1}" for j in range(6)])
            st.table(df_h)
    else:
        st.write("히스토리가 없습니다.")
