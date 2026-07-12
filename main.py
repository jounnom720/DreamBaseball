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
    get_spreadsheet,
    load_sheet,
)
from datetime import date, datetime

# 목표 유형 선택지 (개발계획서의 '목표 유형' 표 반영)
GOAL_TYPES = [
    "", "체크형", "숫자형", "시간형", "거리형",
    "사진형", "영상형", "기록형", "성장형",
]

# 8대 핵심목표 이모지 (오늘의 미션 화면에서 그룹 제목 앞에 표시)
CORE_EMOJI = {
    "타격력 강화": "⚾", "투구·수비 능력": "🧤", "스피드·주루 능력": "🏃",
    "체력·몸 관리": "💪", "멘탈 관리": "🧠", "생활 습관·인성": "🌱",
    "야구 지식·전략": "📖", "팀워크·인간관계": "🤝",
}

# 실천행동 64개 이모지 (목표명과 정확히 일치해야 매칭됨)
ACTION_EMOJI = {
    "매일 티배팅 실시": "🏏", "스윙 폼 영상 촬영 후 분석": "🎥", "스윙 스피드 측정 훈련": "⏱️",
    "변화구 대응 타격 연습": "🌀", "선구안 훈련": "👀", "상체 근력 강화 웨이트": "🏋️",
    "실전 타석 데이터 기록·분석": "📊", "좌·우 투수 상대 타격 연습": "🔄",
    "포지션별 수비 반복 훈련": "🧤", "송구 정확도 훈련": "🎯", "캐치볼 어깨 유연성 관리": "🤾",
    "수비 풋워크 훈련": "👣", "타구 판단력 훈련": "🧐", "글러브 포구 안정성 훈련": "🧤",
    "팀 수비 포지셔닝 학습": "🗺️", "실전 수비 상황 시뮬레이션": "🎮",
    "단거리 스프린트(10m·30m)": "🏃‍♂️", "도루 스타트 타이밍 연습": "💨", "베이스러닝 코스 훈련": "🔁",
    "플라이오메트릭 순발력 훈련": "🤸", "진루·귀루 판단력 훈련": "🧭", "하체 근력 강화 운동": "🦵",
    "어질리티 사다리 훈련": "🪜", "실전 주루 상황 반복 훈련": "🔂",
    "스트레칭·유연성 운동": "🧘", "부상예방 웜업·쿨다운 습관화": "🩹", "균형 잡힌 식단 관리": "🥗",
    "8시간 이상 수면 확보": "😴", "코어 근력 강화 운동": "🔥", "정기적 체력측정 기록": "📏",
    "폼롤러 등 회복 관리": "🛌", "성장기 맞춤 웨이트 트레이닝": "🏋️‍♂️",
    "실패 후 감정회복 루틴 만들기": "💙", "긍정적 자기대화 연습": "💬", "경기 전 준비 루틴 만들기": "🎽",
    "목표 일지 작성 습관": "📔", "압박 상황 대처 훈련": "🛡️", "코치·부모 피드백 수용 태도": "👂",
    "짧은 명상 집중력 훈련": "🧘‍♂️", "장·단기 목표 구분 관리": "🗂️",
    "훈련 준비물 스스로 챙기기": "🎒", "훈련 일지 매일 작성": "📝", "훈련 시간 엄수 습관": "⏰",
    "감사 인사·예의 바른 태도": "🙏", "학업·훈련 균형 시간표 관리": "📅", "정리정돈 습관": "🧹",
    "스마트폰·게임 시간 조절": "📵", "규칙적인 기상·취침 습관": "🌅",
    "프로야구 경기 분석 시청": "📺", "좋아하는 선수 플레이 연구": "⭐", "야구 규칙·전략 공부": "📘",
    "상대팀 분석법 배우기": "🔍", "포지션별 역할 이해": "🧩", "야구 관련 책·자료 읽기": "📚",
    "경기 후 스스로 복기": "🔄", "코치 설명 이해·질문하기": "❓",
    "팀 동료와 적극 소통": "💬", "동료 격려 습관": "👏", "맡은 역할 책임감 있게 수행": "✅",
    "갈등 대화로 해결 연습": "🕊️", "코치와 신뢰관계 쌓기": "🤝", "팀 승리 위한 개인 역할 이해": "🏆",
    "상대팀 스포츠맨십 실천": "🫱", "가족과 훈련 상황 공유·소통": "👨‍👩‍👧",
}

# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="DreamBaseball ⚾",
    page_icon="⚾",
    layout="centered",
)

USER_SHEETS = dict(st.secrets.get("dreambaseball_users", {}))

SPREADSHEET_ID = ""


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

    if not SPREADSHEET_ID:
        st.error("연결된 구글시트가 없습니다. secrets.toml의 [dreambaseball_users] 설정을 확인해주세요.")
        return

    try:
        existing = load_mandalart(SPREADSHEET_ID)
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다 (종류: {type(e).__name__})")
        st.exception(e)
        return

    def block_center(r, c):
        br, bc = (r - 1) // 3, (c - 1) // 3
        return br * 3 + 2, bc * 3 + 2

    groups = {}
    for (r, c), rec in existing.items():
        if classify_cell(r, c) != "실천행동":
            continue
        name = str(rec.get("목표명", "")).strip()
        if not name:
            continue
        active = str(rec.get("활성여부", True)).strip().lower() not in ("false", "0", "거짓", "")
        if not active:
            continue
        cr, cc = block_center(r, c)
        core_name = existing.get((cr, cc), {}).get("목표명", "기타")
        groups.setdefault(core_name, []).append((r, c, rec))

    if not groups:
        st.warning("만다라트에 등록된 실천행동이 없습니다. 먼저 '만다라트 등록' 메뉴에서 입력해주세요.")
        return

    today = date.today()
    st.caption(f"{today.strftime('%Y년 %m월 %d일')}")

    responses = {}
    for core_name, items in groups.items():
        core_emoji = CORE_EMOJI.get(core_name, "")
        with st.expander(f"{core_emoji} {core_name}  ({len(items)}개)", expanded=True):
            for r, c, rec in items:
                goal_id = f"{r}-{c}"
                goal_type = rec.get("유형", "")
                unit = rec.get("단위", "")
                target = rec.get("목표값", "")
                emoji = ACTION_EMOJI.get(rec["목표명"], "")
                img_link = str(rec.get("이미지링크", "") or "").strip()

                if goal_type == "체크형":
                    checked = st.checkbox(f"{emoji} {rec['목표명']}", key=f"chk_{goal_id}")
                    responses[goal_id] = (1 if checked else 0, checked)

                elif goal_type == "영상형":
                    checked = st.checkbox(f"{emoji} {rec['목표명']} (영상 촬영 완료)", key=f"chk_{goal_id}")
                    responses[goal_id] = (1 if checked else 0, checked)

                elif goal_type == "기록형":
                    val = st.number_input(
                        f"{emoji} {rec['목표명']} ({unit})", min_value=0.0, step=1.0, key=f"num_{goal_id}",
                    )
                    responses[goal_id] = (val, val > 0)

                else:  # 숫자형, 시간형 등 목표값이 있는 유형
                    label = f"{emoji} {rec['목표명']} (목표 {target}{unit})" if target != "" else f"{emoji} {rec['목표명']}"
                    val = st.number_input(label, min_value=0.0, step=1.0, key=f"num_{goal_id}")
                    try:
                        target_num = float(str(target).replace(",", "").split()[0])
                    except (ValueError, IndexError):
                        target_num = None
                    done = target_num is not None and val >= target_num
                    responses[goal_id] = (val, done)

                if img_link:
                    st.image(img_link, width=120)

    completed = sum(1 for _, done in responses.values() if done)
    total = len(responses)
    st.progress(completed / total if total else 0)
    st.write(f"완료: {completed} / {total}")

    if st.button("오늘 기록 저장하기", type="primary"):
        try:
            save_today_log(SPREADSHEET_ID, today, responses)
            st.success("저장되었습니다.")
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다 (종류: {type(e).__name__})")
            st.exception(e)


def save_today_log(spreadsheet_id: str, log_date: date, responses: dict):
    date_str = log_date.strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    existing = load_sheet(spreadsheet_id, "일일기록")
    keep = [r for r in existing if str(r.get("날짜", "")) != date_str]

    new_rows = [{
        "기록ID": f"{date_str}_{goal_id}",
        "날짜": date_str,
        "목표ID": goal_id,
        "실행값": val,
        "완료여부": "완료" if done else "미완료",
        "등록시각": now_str,
    } for goal_id, (val, done) in responses.items()]

    headers = ["기록ID", "날짜", "목표ID", "실행값", "완료여부", "등록시각"]
    all_rows = keep + new_rows
    values = [[row.get(h, "") for h in headers] for row in all_rows]

    sh = get_spreadsheet(spreadsheet_id)
    ws = sh.worksheet("일일기록")
    ws.batch_clear(["A2:F100000"])
    if values:
        ws.update("A2", values, value_input_option="USER_ENTERED")


def page_mandalart():
    st.title("🗂️ 만다라트 등록/수정")
    st.caption("사진 속 81칸 내용을 그대로 아래 표에 옮겨 적으면 됩니다.")

    if not SPREADSHEET_ID:
        st.error("연결된 구글시트가 없습니다. secrets.toml의 [dreambaseball_users] 설정을 확인해주세요.")
        return

    try:
        existing = load_mandalart(SPREADSHEET_ID)
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다 (종류: {type(e).__name__})")
        st.exception(e)
        return

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
                    "이미지링크": prev.get("이미지링크", ""),
                })
        try:
            save_mandalart(SPREADSHEET_ID, rows)
            st.success("목표명이 저장되었습니다. 아래 2단계로 진행해주세요.")
            st.rerun()
        except Exception as e:
            st.error(f"저장 중 오류가 발생했습니다 (종류: {type(e).__name__})")
            st.exception(e)

    st.divider()

    st.subheader("2단계. 실천행동 목표 유형 지정")
    st.caption(
        "매일 체크할 '실천행동' 칸에만 유형을 지정합니다. "
        "예: 티배팅 300개 → 숫자형 / 개, 달리기 30분 → 시간형 / 분"
    )

    existing = load_mandalart(SPREADSHEET_ID)  # 1단계 저장 후 최신 데이터 재조회
    action_rows = []
    for r in range(1, 10):
        for c in range(1, 10):
            if classify_cell(r, c) != "실천행동":
                continue
            rec = existing.get((r, c), {})
            name = rec.get("목표명", "")
            if not name:
                continue
            action_rows.append({
                "위치": f"{r},{c}",
                "목표명": name,
                "유형": rec.get("유형", "") or "",
                "단위": rec.get("단위", ""),
                "목표값": rec.get("목표값", ""),
            })

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
                    "이미지링크": prev.get("이미지링크", ""),
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


st.sidebar.title("⚾ DreamBaseball")

if not USER_SHEETS:
    st.sidebar.error("secrets.toml에 [dreambaseball_users]가 설정되어 있지 않습니다.")
    st.stop()

user_names = list(USER_SHEETS.keys())

if len(user_names) == 1:
    selected_user = user_names[0]
    st.sidebar.caption(f"사용자: {selected_user}")
else:
    selected_user = st.sidebar.selectbox("사용자 선택", user_names)

SPREADSHEET_ID = USER_SHEETS[selected_user]

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
