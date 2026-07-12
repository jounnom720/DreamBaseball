# -*- coding: utf-8 -*-
"""
DreamBaseball v0.3 - 오늘의 미션 체크리스트 화면

전제(반드시 기존 앱 구조에 맞게 확인/수정 필요):
- 인증된 gspread 클라이언트를 반환하는 get_gspread_client() 함수가
  기존 stock_app_main.py 또는 공통 auth 모듈에 이미 존재한다고 가정.
  (없다면 기존 Stock_app에서 쓰던 서비스 계정 인증 코드를 그대로 재사용하세요.)
- 'mandalart' 시트에 아래 8개 열이 그대로 존재:
  핵심영역_번호 | 핵심영역명 | 실천행동_번호 | 실천행동명 | 유형 | 단위 | 목표값 | 주기
  -> 구글 시트에서 직접 수정하신 내용이 이 열 이름과 다르면 COLUMNS 부분만 맞춰 바꾸면 됩니다.
- 다중 사용자 구조이므로 spreadsheet_id를 모든 캐시 함수의 명시적 인자로 넘김
  (Stock_app과 동일한 패턴).
"""

import streamlit as st
import pandas as pd
from datetime import date
import gspread


# ---------------------------------------------------------------------------
# 주기 -> 요일 매핑
# 월=0 ... 일=6. 같은 '주3회'라도 실천행동마다 다른 요일이 필요하면
# WEEKDAY_SCHEDULE을 실천행동 단위로 세분화하면 됩니다 (현재는 유형 단위 배분).
# ---------------------------------------------------------------------------
WEEKDAY_SCHEDULE = {
    "매일": {0, 1, 2, 3, 4, 5, 6},
    "주1회": {0},            # 월요일
    "주2회": {1, 3},          # 화, 목
    "주3회": {0, 2, 4},       # 월, 수, 금
    "주4회": {0, 1, 3, 4},    # 월, 화, 목, 금
}
# 날짜가 아니라 상황에 따라 발생하는 항목 (매일 화면 상단이 아닌 별도 섹션에 노출)
EVENT_BASED = {"필요 시", "경기일", "경기 전", "경기 후", "경기 시", "훈련 시"}

LOG_COLUMNS = ["날짜", "핵심영역_번호", "핵심영역명", "실천행동_번호",
               "실천행동명", "유형", "입력값", "완료여부"]


def is_scheduled_today(period: str, today: date) -> bool:
    """주기 문자열을 보고 오늘 노출해야 하는 정기 미션인지 판단."""
    if period in WEEKDAY_SCHEDULE:
        return today.weekday() in WEEKDAY_SCHEDULE[period]
    if period == "월1회":
        return today.day == 1
    return False  # 상황별 항목은 별도 처리


def _parse_target(target) -> float | None:
    """목표값 열에 '측정·기록', '60 이하' 같은 문자열이 섞여 있어도
    앞쪽 숫자만 뽑아 진행률 판정에 사용."""
    try:
        first_token = str(target).replace(",", "").split()[0]
        return float(first_token)
    except (ValueError, IndexError):
        return None


@st.cache_data(ttl=30)
def load_mandalart(spreadsheet_id: str) -> pd.DataFrame:
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet("mandalart")
    # 프로젝트 공통 규칙: 콤마 포함 문자열이 숫자로 잘못 변환되는 것 방지
    records = ws.get_all_records(numericise_ignore=["all"])
    return pd.DataFrame(records)


def render_daily_checklist(spreadsheet_id: str):
    st.subheader("오늘의 미션 체크리스트")

    today = date.today()
    df = load_mandalart(spreadsheet_id)
    if df.empty:
        st.info("mandalart 시트에서 등록된 실천행동을 찾을 수 없습니다. 시트 내용을 확인해주세요.")
        return

    scheduled = df[df["주기"].apply(lambda p: is_scheduled_today(p, today))]
    event_based = df[df["주기"].isin(EVENT_BASED)]

    st.caption(f"{today.strftime('%Y년 %m월 %d일')} · 오늘의 정기 미션 {len(scheduled)}개")

    responses = {}

    # 핵심영역별로 묶어서 표시
    for core_no, group in scheduled.groupby("핵심영역_번호"):
        core_name = group["핵심영역명"].iloc[0]
        with st.expander(f"{core_no}. {core_name}  ({len(group)}개)", expanded=True):
            for _, row in group.iterrows():
                key = f"{core_no}_{row['실천행동_번호']}"
                if row["유형"] == "체크형":
                    checked = st.checkbox(row["실천행동명"], key=f"chk_{key}")
                    responses[key] = {"row": row, "value": 1 if checked else 0, "done": checked}
                else:
                    val = st.number_input(
                        f"{row['실천행동명']} (목표 {row['목표값']}{row['단위']})",
                        min_value=0.0, step=1.0, key=f"num_{key}",
                    )
                    target = _parse_target(row["목표값"])
                    done = target is not None and val >= target
                    responses[key] = {"row": row, "value": val, "done": done}

    # 상황별(경기 전후, 필요 시 등) 미션은 별도 섹션 - 전체 완료율 계산에서는 제외
    if not event_based.empty:
        with st.expander("상황별 미션 (경기 전후 · 필요 시)", expanded=False):
            for _, row in event_based.iterrows():
                key = f"event_{row['핵심영역_번호']}_{row['실천행동_번호']}"
                checked = st.checkbox(f"{row['실천행동명']} ({row['주기']})", key=f"chk_{key}")
                responses[key] = {"row": row, "value": 1 if checked else 0,
                                   "done": checked, "event": True}

    # 진행률은 정기 미션 기준으로만 계산
    regular_results = [r for r in responses.values() if not r.get("event")]
    completed = sum(1 for r in regular_results if r["done"])
    total = len(regular_results)
    st.progress(completed / total if total else 0)
    st.write(f"완료: {completed} / {total}")

    if st.button("오늘 기록 저장하기", type="primary"):
        save_daily_log(spreadsheet_id, today, responses)
        st.cache_data.clear()
        st.success("저장되었습니다.")


def save_daily_log(spreadsheet_id: str, log_date: date, responses: dict):
    gc = get_gspread_client()
    sh = gc.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet("daily_log")
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title="daily_log", rows=1000, cols=len(LOG_COLUMNS))
        ws.update([LOG_COLUMNS], value_input_option="USER_ENTERED")

    date_str = log_date.strftime("%Y-%m-%d")
    existing = ws.get_all_records(numericise_ignore=["all"])
    # 같은 날짜 기존 기록은 지우고 새로 씀 (하루 여러 번 저장해도 중복 안 쌓이게)
    keep_rows = [r for r in existing if r.get("날짜") != date_str]

    new_rows = []
    for r in responses.values():
        row = r["row"]
        new_rows.append([
            date_str, row["핵심영역_번호"], row["핵심영역명"],
            row["실천행동_번호"], row["실천행동명"], row["유형"],
            r["value"], "완료" if r["done"] else "미완료",
        ])

    all_rows = [[k.get(c, "") for c in LOG_COLUMNS] for k in keep_rows] + new_rows

    ws.batch_clear([f"A2:H{len(existing) + len(new_rows) + 10}"])
    if all_rows:
        ws.update("A2", all_rows, value_input_option="USER_ENTERED")
