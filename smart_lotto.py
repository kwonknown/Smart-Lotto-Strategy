import streamlit as st
import random
import pandas as pd
import os
from datetime import datetime

# --- [수정] 모든 함수 정의를 최상단으로 배치 ---
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

@st.cache_data
def estimate_combination_count(settings_tuple):
    # (이전과 동일한 확률 계산 로직)
    return 142000, 0.017 # 예시 리턴값

# --- [중요] 그 다음 UI 설정을 시작합니다 ---
st.set_page_config(page_title="Smart-Lotto-Strategy", layout="wide")

# 사이드바 설정 (여기서 estimate_combination_count를 호출하면 이제 에러가 안 납니다)
with st.sidebar:
    # ... 전략 선택 및 settings 설정 코드 ...
    s_tuple = (tuple(settings['sum']), tuple(settings['odds']), settings['consecutive'], tuple(settings['low_high']))
    est_count, est_rate = estimate_combination_count(s_tuple)
