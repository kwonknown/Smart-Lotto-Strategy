import streamlit as st
import random
import pandas as pd
import requests  # <-- 이 부분이 반드시 있어야 합니다!
from datetime import datetime

# --- 당첨 정보 조회 함수 (차단 회피 헤더 추가) ---
def get_lotto_win_info(drw_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={drw_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("returnValue") == "success":
                win_nums = [data[f"drwtNo{i}"] for i in range(1, 7)]
                return win_nums, data["bnusNo"]
    except Exception as e:
        # 터미널에 에러 로그 출력 (디버깅용)
        print(f"조회 에러: {e}")
    return None, None

# --- 등수 확인 함수 ---
def check_rank(my_nums, win_nums, bonus_num):
    match_count = len(set(my_nums) & set(win_nums))
    if match_count == 6: return "🥇 1등"
    if match_count == 5 and bonus_num in my_nums: return "🥈 2등"
    if match_count == 5: return "🥉 3등"
    if match_count == 4: return "4등"
    if match_count == 3: return "5등"
    return "낙첨"

# --- [이전 UI 코드 생략 - 번호 생성 로직 등] ---

# 🎯 과거 당첨 확인 섹션
st.divider()
st.header("🎯 과거 당첨 확인")
col1, col2 = st.columns([3, 1])
with col1:
    # 1210회 정보가 없을 수 있으니 기본값을 1150 정도로 낮춰서 테스트해보세요.
    target_drw = st.number_input("조회할 회차 입력", min_value=1, value=1150)

if st.button("결과 확인"):
    # 1. 번호 생성 이력이 있는지 확인
    if not st.session_state.get('history'):
        st.warning("먼저 '행운의 5조합 생성하기' 버튼을 눌러 번호를 생성해주세요.")
    else:
        # 2. API 호출
        win_n, bonus_n = get_lotto_win_info(target_drw)
        
        if win_n:
            st.success(f"✅ {target_drw}회 당첨번호: {win_n} + 보너스 {bonus_n}")
            
            # 3. 결과 판정
            res_data = []
            latest_picks = st.session_state.history[0]['numbers']
            group_labels = ["A조", "B조", "C조", "D조", "E조"]
            
            for i, my_combo in enumerate(latest_picks):
                rank = check_rank(my_combo, win_n, bonus_n)
                res_data.append({
                    "조": group_labels[i],
                    "내 번호": str(my_combo),
                    "결과": rank
                })
            
            # 결과 테이블 출력
            st.table(pd.DataFrame(res_data))
            
            # 축하 효과
            if any("등" in r['결과'] for r in res_data):
                st.balloons()
                st.confetti() # 설치되어 있다면 작동
        else:
            st.error(f"⚠️ {target_drw}회차 정보를 불러오지 못했습니다. 아직 추첨 전이거나 네트워크 문제일 수 있습니다.")
