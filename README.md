# DreamBaseball ⚾

> 노력은 재능을 이긴다

초등학교 야구 꿈나무를 위한 만다라트 목표 관리 & 성장 기록 앱입니다.
Streamlit + Google Sheets 기반으로 개발합니다.

## 현재 버전: v0.1
- Streamlit 기본 화면 뼈대 (7개 메뉴)
- Google Sheets 6개 탭 자동 생성 기능

## 처음 설정하는 방법 (비개발자용 가이드)

### 1) Google 서비스 계정 만들기
기존 주식 앱과 별개의 새 프로젝트로 만들거나, 같은 GCP 프로젝트를 재사용해도 됩니다.

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. "API 및 서비스" → "라이브러리"에서 **Google Sheets API**, **Google Drive API** 사용 설정
3. "사용자 인증 정보" → "서비스 계정 만들기" → JSON 키 다운로드
4. 사용할 구글시트 파일을 새로 만든 뒤, 서비스 계정 이메일 주소(`...@...iam.gserviceaccount.com`)를
   **편집자(Editor)** 권한으로 공유

### 2) secrets.toml 설정
프로젝트 루트에 `.streamlit/secrets.toml` 파일을 만들고 아래처럼 채웁니다.

```toml
dreambaseball_spreadsheet_id = "여기에_구글시트_URL의_ID_부분_붙여넣기"
parent_password = "부모님이_원하는_비밀번호"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

다운로드한 JSON 파일을 열어보면 위 항목들이 그대로 들어있으니 값만 복사해서 붙여넣으면 됩니다.

### 3) 로컬 실행
```bash
pip install -r requirements.txt
streamlit run main.py
```

### 4) 6개 탭 생성하기
앱 실행 후 사이드바에서 **"🔧 초기 설정(관리자)"** 메뉴 → "Google Sheets 6개 탭 생성/확인하기" 버튼 클릭.
아래 6개 탭이 자동으로 만들어집니다.

| 탭 이름 | 용도 |
|---|---|
| 목표_만다라트 | 81칸 목표 데이터 |
| 일일기록 | 매일의 실천 기록 |
| 레벨경험치 | LV, 경험치, 연속일수 |
| 배지 | 배지 획득 현황 |
| 부모메모 | 부모 코멘트/칭찬 |
| 성장타임라인 | 연도별 성장 기록 |

## 다음 단계 (v0.2 예정)
만다라트 81칸을 화면에서 직접 입력/수정하는 기능을 개발합니다.
