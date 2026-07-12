"""
Google Sheets 연결 및 초기화 유틸리티
=====================================

이 파일은 DreamBaseball 앱이 Google Sheets를 "데이터베이스"처럼
사용할 수 있도록 연결하고, 필요한 6개 탭(시트)을 자동으로
만들어주는 역할을 합니다.

[비개발자를 위한 용어 설명]
- gspread: 파이썬에서 Google Sheets를 읽고 쓸 수 있게 해주는 라이브러리
- 서비스 계정(Service Account): 사람 대신 프로그램이 구글 API에
  접속할 때 쓰는 "로봇 계정". JSON 키 파일로 인증합니다.
- worksheet: 구글시트 파일(spreadsheet) 안에 있는 개별 "탭"을 의미합니다.
  엑셀로 치면 하단의 시트1, 시트2 같은 것입니다.
"""

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# 구글 API 사용 범위 (Sheets 읽기/쓰기 + Drive 접근)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# DreamBaseball에서 사용할 6개 탭의 이름과 헤더(첫 줄 컬럼명) 정의
# 이후 버전에서 컬럼이 늘어나면 이 딕셔너리에만 추가하면 됩니다.
SHEET_SCHEMA = {
    "목표_만다라트": [
        "목표ID", "위치(행,열)", "목표명", "카테고리",
        "유형", "단위", "목표값", "활성여부", "이미지링크"   # 이미지링크 추가
    ],
    "일일기록": [
        "기록ID", "날짜", "목표ID", "실행값", "완료여부", "등록시각"
    ],
    "레벨경험치": [
        "사용자ID", "현재LV", "누적경험치", "연속일수", "최종갱신일"
    ],
    "배지": [
        "배지ID", "배지명", "획득조건", "획득여부", "획득일자"
    ],
    "부모메모": [
        "메모ID", "날짜", "메모내용", "칭찬여부", "작성자"
    ],
    "성장타임라인": [
        "타임라인ID", "연도", "학년", "이벤트내용", "사진URL"
    ],
}


@st.cache_resource
def get_gspread_client():
    """
    구글 서비스 계정 인증 정보로 gspread 클라이언트를 생성합니다.

    st.secrets["gcp_service_account"]에 서비스 계정 JSON 내용을
    저장해두어야 합니다. (.streamlit/secrets.toml 참고)
    """
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client


def get_spreadsheet(spreadsheet_id: str):
    """
    spreadsheet_id로 특정 구글시트 파일을 엽니다.

    주의: 캐시 함수의 인자로 spreadsheet_id를 명시적으로 넘겨야
    (기존 주식 앱에서 겪었던) 사용자 간 캐시 공유 버그를 피할 수 있습니다.
    """
    client = get_gspread_client()
    return client.open_by_key(spreadsheet_id)


def initialize_sheets(spreadsheet_id: str) -> dict:
    """
    SHEET_SCHEMA에 정의된 6개 탭이 없으면 새로 만들고,
    각 탭의 첫 줄에 헤더(컬럼명)를 채워 넣습니다.

    이미 탭이 존재하면 건드리지 않습니다 (데이터 보호).

    반환값: {탭이름: "생성됨" 또는 "이미존재"} 형태의 결과 딕셔너리
    """
    sh = get_spreadsheet(spreadsheet_id)
    existing_titles = [ws.title for ws in sh.worksheets()]
    result = {}

    for sheet_name, headers in SHEET_SCHEMA.items():
        if sheet_name in existing_titles:
            result[sheet_name] = "이미존재"
            continue

        ws = sh.add_worksheet(
            title=sheet_name, rows=200, cols=max(len(headers), 8)
        )
        ws.update("A1", [headers])
        # 헤더 행 서식(굵게)을 넣어 부모가 봐도 구분되게 함
        ws.format("A1:Z1", {"textFormat": {"bold": True}})
        result[sheet_name] = "생성됨"

    return result


def load_sheet(spreadsheet_id: str, sheet_name: str):
    """
    특정 탭의 전체 데이터를 리스트[딕셔너리] 형태로 불러옵니다.
    (gspread의 get_all_records 사용 — 첫 줄을 헤더로 자동 인식)

    주의: numericise_ignore=["all"]을 반드시 지정해야 합니다.
    지정하지 않으면 gspread가 "1,1" 같은 값을 "천 단위 구분 콤마가 있는 숫자"로
    착각해서 콤마를 제거하고 11로 변환해버리는 문제가 있습니다.
    (이 버그 때문에 위치(행,열) 컬럼이 깨져 데이터를 못 읽어온 적이 있었습니다)
    """
    sh = get_spreadsheet(spreadsheet_id)
    ws = sh.worksheet(sheet_name)
    return ws.get_all_records(numericise_ignore=["all"])


def append_row(spreadsheet_id: str, sheet_name: str, row_values: list):
    """특정 탭 맨 아래에 한 줄(row)을 추가합니다."""
    sh = get_spreadsheet(spreadsheet_id)
    ws = sh.worksheet(sheet_name)
    ws.append_row(row_values, value_input_option="USER_ENTERED")


# ------------------------------------------------------------
# 만다라트(9x9=81칸) 전용 함수
# ------------------------------------------------------------
# 만다라트는 3x3짜리 블록 9개로 이루어져 있고, 그 중 정중앙 블록의
# 한가운데 칸이 "궁극목표"입니다. 정중앙 블록의 나머지 8칸은
# "핵심목표"(8개), 그리고 나머지 8개 블록 각각의 한가운데 칸은
# 해당 핵심목표를 반복해서 적는 칸("세부목표(반복)")이며,
# 그 8개 블록의 나머지 칸들이 실제로 매일 실천할 "실천행동"입니다.
def classify_cell(r: int, c: int) -> str:
    """
    행(r), 열(c) 모두 1~9 사이 값을 받아 만다라트 상의 역할을 반환합니다.
    """
    block_r, block_c = (r - 1) // 3, (c - 1) // 3
    local_r, local_c = (r - 1) % 3, (c - 1) % 3
    is_block_center = local_r == 1 and local_c == 1
    is_center_block = block_r == 1 and block_c == 1

    if is_center_block and is_block_center:
        return "궁극목표"
    if is_center_block:
        return "핵심목표"
    if is_block_center:
        return "세부목표(반복)"
    return "실천행동"


def load_mandalart(spreadsheet_id: str) -> dict:
    """
    '목표_만다라트' 탭의 데이터를 불러와 {(행, 열): 레코드} 형태로 반환합니다.
    아직 아무것도 저장되지 않았다면 빈 딕셔너리를 반환합니다.
    """
    records = load_sheet(spreadsheet_id, "목표_만다라트")
    grid = {}
    for rec in records:
        pos = str(rec.get("위치(행,열)", ""))
        if "," not in pos:
            continue
        try:
            r_str, c_str = pos.split(",")
            r, c = int(r_str.strip()), int(c_str.strip())
            grid[(r, c)] = rec
        except ValueError:
            continue
    return grid


def save_mandalart(spreadsheet_id: str, rows: list[dict]):
    """
    rows: SHEET_SCHEMA["목표_만다라트"] 헤더와 같은 키를 가진 딕셔너리 리스트.
    기존 데이터(헤더 제외)를 지우고 한 번에 새로 씁니다.
    (81칸을 한 칸씩 쓰면 API 호출이 81번 발생해 rate limit에
    걸리기 쉬우므로, 반드시 한 번의 update 호출로 묶어서 처리합니다)
    """
    sh = get_spreadsheet(spreadsheet_id)
    ws = sh.worksheet("목표_만다라트")
    headers = SHEET_SCHEMA["목표_만다라트"]

    values = [[row.get(h, "") for h in headers] for row in rows]

    ws.batch_clear(["A2:Z1000"])
    if values:
        ws.update("A2", values, value_input_option="USER_ENTERED")
