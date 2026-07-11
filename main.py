"""
DreamBaseball - 초등학교 6학년 야구선수 꿈나무를 위한 성장 기록 앱
=================================================================
버전: v0.1 (기본 뼈대 + Google Sheets 6개 탭 초기화)

[구조 설명 - 비개발자를 위한 안내]
Streamlit 앱은 위에서 아래로 코드를 실행하는 구조입니다.
이 파일(main.py)이 "진입점"이고, 사이드바에서 메뉴를 선택하면
각 화면에 해당하는 함수를 호출하는 방식(if/elif)으로 페이지를 전환합니다.
(추후 화면이 많아지면 st.Page / st.navigation 방식으로 리팩터링 가능)
"""

import streamlit as st
import pandas as pd
from utils.sheets import (
    initialize_sheets,
    classify_cell,
    load_mandalart,
    save_mandalart,
)

# 목표 유형 선택지 (개발계획서의 '목표 유형' 표 반영)
GOAL_TYPES = [
    "", "체크형", "숫자형", "시간형", "거리형",
    "사진형", "영상형", "기록형", "성장형",
]

# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="DreamBaseball ⚾",
    page_icon="⚾",
    layout="centered",
)

# secrets.toml에 등록된 사용자(아이)별 구글시트 ID 목록을 불러옵니다.
# 지금은 아드님 한 명만 등록되어 있지만, 나중에 다른 아이가 추가되면
# secrets.toml의 [dreambaseball_users] 아래에 한 줄만 추가하면 됩니다.
# (코드 수정 없이 확장 가능한 구조 - 주식 앱의 '템플릿 풀' 방식과 동일한 개념)
USER_SHEETS = dict(st.secrets.get("dreambaseball_users", {}))

# 화면 전환 함수들이 참조할 전역 변수. 사이드바에서 사용자를 선택한 뒤
# 실제 값이 채워집니다 (아래 '사이드바 메뉴' 섹션 참고).
SPREADSHEET_ID = ""


# ------------------------------------------------------------
# 화면(페이지)별 함수 - v0.1에서는 자리만 잡아두는 뼈대 상태
# 다음 버전(v0.2~)에서 각 함수 내부를 실제 기능으로 채워나갑니다.
# ------------------------------------------------------------

def page_home():
    st.title("⚾ DreamBaseball")
    st.caption("노력은 재능을 이긴다")
    st.markdown("### 오늘도 한 걸음!")

    col1, col2, col3 = st.columns(3)
    col1.metric("오늘 달성률", "- %")
    col2.metric("레벨", "LV -")
    col3.metric("연속 성공", "- 일")

    st.info("v0.2에서 실제 데이터가 연결될 예정입니다.")
    st.button("오늘 시작하기 ▶", use_container_width=True, type="primary")


def page_today_mission():
    st.title("📋 오늘의 미션")
    st.write("(v0.3에서 만다라트 목표를 불러와 체크리스트로 표시합니다)")


def page_mandalart():
    st.title("🗂️ 만다라트 등록/수정")
    st.caption("사진 속 81칸 내용을 그대로 아래 표에 옮겨 적으면 됩니다.")

    if not SPREADSHEET_ID:
        st.error("연결된 구글시트가 없습니다. secrets.toml의 [dreambaseball_users] 설정을 확인해주세요.")
        return

    # 1) 기존 저장된 데이터 불러오기 (없으면 빈 값)
    try:
        existing = load_mandalart(SPREADSHEET_ID)
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다 (종류: {type(e).__name__})")
        st.exception(e)
        return

    # ----------------------------------------------------
    # STEP 1. 9x9 격자에 목표명 입력하기
    # ----------------------------------------------------
    st.subheader("1단계. 81칸 목표명 입력")
    st.info(
        "정중앙(5행 5열)은 궁극적인 꿈, 그 둘레 8칸은 핵심목표, "
        "나머지 8개 블록 각각의 가운데 칸은 해당 핵심목표를 반복 입력, "
        "그 외 칸들이 매일 실천할 행동입니다."
    )

    name_grid = pd.DataFrame(
        [
            [existing.get((r, c), {}).get("목표명", "") for c in range(1, 10)]
            for r in range(1, 10)
        ],
        index=[f"{r}행" for r in range(1, 10)],
        columns=[f"{c}열" for c in range(1, 10)],
    )

    edited_names = st.data_editor(
        name_grid, use_container_width=True, key="mandalart_name_editor"
    )

    if st.button("1단계 저장 (목표명만 먼저 저장)"):
        rows = []
        for r in range(1, 10):
            for c in range(1, 10):
                name = str(edited_names.loc[f"{r}행", f"{c}열"]).strip()
                prev = existing.get((r, c), {})
                rows.append({
                    "목표ID": f"{r}-{c}",
                    "위치(행,열)": f"{r},{c}",
                    "목표명": name,
                    "카테고리": classify_cell(r, c),
                    "유형": prev.get("유형", ""),
                    "단위": prev.get("단위", ""),
                    "목표값": prev.get("목표값", ""),
                    "활성여부": prev.get("활성여부", True),
                })
        try:
            save_mandalart(SPREADSHEET_ID, rows)
            st.success("목표명이 저장되었습니다. 아래 2단계로 진행해주세요.")
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다 (종류: {type(e).__name__})")
            st.exception(e)

    st.divider()

    # ----------------------------------------------------
    # STEP 2. 실천행동 칸(72개)에 유형/단위/목표값 지정하기
    # ----------------------------------------------------
    st.subheader("2단계. 실천행동 목표 유형 지정")
    st.caption(
        "매일 체크할 '실천행동' 칸에만 유형을 지정합니다. "
        "예: 티배팅 300개 → 숫자형 / 개, 달리기 30분 → 시간형 / 분"
    )

    existing = load_mandalart(SPREADSHEET_ID)  # 1단계 저장 후 최신 데이터 재조회
    st.caption(f"🔍 진단: 구글시트에서 불러온 전체 셀 개수 = {len(existing)}개 (81개여야 정상)")

    action_rows = []
    for r in range(1, 10):
        for c in range(1, 10):
            if classify_cell(r, c) != "실천행동":
                continue
            rec = existing.get((r, c), {})
            name = rec.get("목표명", "")
            if not name:
                continue  # 아직 이름이 없는 칸은 2단계 표에 표시하지 않음
            action_rows.append({
                "위치": f"{r},{c}",
                "목표명": name,
                "유형": rec.get("유형", "") or "",
                "단위": rec.get("단위", ""),
                "목표값": rec.get("목표값", ""),
            })

    st.caption(f"🔍 진단: '실천행동' 중 이름이 채워진 칸 = {len(action_rows)}개 (72개여야 정상)")

    if not action_rows:
        st.warning("먼저 1단계에서 목표명을 입력하고 저장해주세요.")
        return

    action_df = pd.DataFrame(action_rows)
    edited_actions = st.data_editor(
        action_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "위치": st.column_config.TextColumn(disabled=True),
            "목표명": st.column_config.TextColumn(disabled=True),
            "유형": st.column_config.SelectboxColumn(options=GOAL_TYPES),
        },
        key="mandalart_action_editor",
    )

    if st.button("2단계 저장 (유형/단위/목표값)"):
        edited_map = {row["위치"]: row for row in edited_actions.to_dict("records")}
        rows = []
        for r in range(1, 10):
            for c in range(1, 10):
                prev = existing.get((r, c), {})
                pos_key = f"{r},{c}"
                if pos_key in edited_map:
                    upd = edited_map[pos_key]
                    유형, 단위, 목표값 = upd["유형"], upd["단위"], upd["목표값"]
                else:
                    유형 = prev.get("유형", "")
                    단위 = prev.get("단위", "")
                    목표값 = prev.get("목표값", "")
                rows.append({
                    "목표ID": f"{r}-{c}",
                    "위치(행,열)": pos_key,
                    "목표명": prev.get("목표명", ""),
                    "카테고리": classify_cell(r, c),
                    "유형": 유형,
                    "단위": 단위,
                    "목표값": 목표값,
                    "활성여부": prev.get("활성여부", True),
                })
        try:
            save_mandalart(SPREADSHEET_ID, rows)
            st.success("유형/단위/목표값이 저장되었습니다.")
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다 (종류: {type(e).__name__})")
            st.exception(e)


def page_growth_chart():
    st.title("📈 성장 그래프")
    st.write("(v0.6에서 Plotly 그래프가 연결됩니다)")


def page_level_badge():
    st.title("🏅 레벨 & 배지")
    st.write("(v0.4~v0.5에서 경험치·배지 시스템이 추가됩니다)")


def page_parent_mode():
    st.title("👨‍👩‍👦 부모 모드")
    pw = st.text_input("비밀번호", type="password")
    if pw:
        if pw == st.secrets.get("parent_password", ""):
            st.success("인증되었습니다. (v0.7에서 메모/통계 기능이 추가됩니다)")
        else:
            st.error("비밀번호가 올바르지 않습니다.")


def page_admin_setup():
    """
    관리자 전용: Google Sheets 6개 탭을 처음 한 번 생성하는 화면.
    실제 서비스 오픈 후에는 사이드바 메뉴에서 숨겨도 됩니다.
    """
    st.title("🔧 초기 설정 (관리자)")

    if not SPREADSHEET_ID:
        st.error("연결된 구글시트가 없습니다. secrets.toml의 [dreambaseball_users] 설정을 확인해주세요.")
        return

    st.write(f"현재 사용자: **{selected_user}**")
    st.write(f"연결된 스프레드시트 ID: `{SPREADSHEET_ID}`")

    if st.button("Google Sheets 6개 탭 생성/확인하기"):
        with st.spinner("시트를 확인하고 있습니다..."):
            try:
                result = initialize_sheets(SPREADSHEET_ID)
                for name, status in result.items():
                    if status == "생성됨":
                        st.success(f"'{name}' 탭 생성 완료")
                    else:
                        st.info(f"'{name}' 탭은 이미 존재합니다")
            except Exception as e:
                st.error(f"오류가 발생했습니다 (종류: {type(e).__name__})")
                st.code(repr(e), language="text")
                response = getattr(e, "response", None)
                if response is not None:
                    try:
                        st.json(response.json())
                    except Exception:
                        st.code(str(getattr(response, "text", "")), language="text")
                st.exception(e)


# ------------------------------------------------------------
# 사이드바 - 사용자 선택 (지금은 1명, 나중에 여러 명으로 확장 가능)
# ------------------------------------------------------------
st.sidebar.title("⚾ DreamBaseball")

if not USER_SHEETS:
    st.sidebar.error("secrets.toml에 [dreambaseball_users]가 설정되어 있지 않습니다.")
    st.stop()

user_names = list(USER_SHEETS.keys())

if len(user_names) == 1:
    # 사용자가 한 명뿐이면 선택 UI 없이 자동으로 그 사용자로 진행
    selected_user = user_names[0]
    st.sidebar.caption(f"사용자: {selected_user}")
else:
    # 사용자가 여러 명이면 드롭다운으로 선택 (나중에 자동 적용됨)
    selected_user = st.sidebar.selectbox("사용자 선택", user_names)

SPREADSHEET_ID = USER_SHEETS[selected_user]

# ------------------------------------------------------------
# 사이드바 메뉴 - 화면 전환
# ------------------------------------------------------------
PAGES = {
    "🏠 메인 화면": page_home,
    "📋 오늘의 미션": page_today_mission,
    "🗂️ 만다라트 등록": page_mandalart,
    "📈 성장 그래프": page_growth_chart,
    "🏅 레벨/배지": page_level_badge,
    "👨‍👩‍👦 부모 모드": page_parent_mode,
    "🔧 초기 설정(관리자)": page_admin_setup,
}

choice = st.sidebar.radio("메뉴", list(PAGES.keys()))
st.sidebar.caption("v0.2 · 만다라트 등록 단계")

PAGES[choice]()
