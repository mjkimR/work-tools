# Taiga Task Writer

AI를 활용하여 Taiga **User Story(유저 스토리)**를 자동으로 생성하는 개인용 도구입니다. macOS 환경에서 브라우저(Chrome) 세션을 활용하여 인증을 처리하며, 상황별 가이드라인에 따라 User Story를 구조화합니다.

> **생성 단위**: Taiga의 기본 관리 단위인 **User Story** 생성이 메인입니다. 필요한 경우 하위 Task 목록도 함께 생성합니다.

## 🚀 기능
- **브라우저 토큰 자동 추출**: `osascript`를 통해 Chrome에서 Taiga `auth_token`을 가져옵니다.
- **맞춤형 User Story 생성**: 3가지 가이드라인(이슈, TODO, 기능 추가)에 따라 AI가 User Story를 작성합니다.
- **하위 Task 자동 생성**: 필요한 경우 User Story에 연결된 Task 목록을 함께 등록합니다.
- **프로젝트 목록 조회**: 가용한 Taiga 프로젝트 목록을 확인합니다.

## 📁 폴더 구조
- `task-writer/scripts/`: Python 스크립트
- `task-writer/references/`: 태스크 유형별 가이드라인 (.md)
  - `issue_guideline.md`: 고객사 이슈 대응용
  - `future_task_guideline.md`: 팀 내부 TODO/백로그용
  - `feature_guideline.md`: 신규 기능/대규모 작업용
- `task-writer/SKILL.md`: 스킬 정의 및 라우팅

## 📋 사전 준비
1. **macOS**: 이 스크립트는 macOS 환경 전용입니다.
2. **Chrome 설정**: Chrome 메뉴에서 `보기` → `개발자용` → `애플 이벤트의 자바스크립트 실행 허용`을 체크해야 합니다.
3. **Taiga 로그인**: Chrome 브라우저에서 사용할 Taiga 계정으로 로그인되어 있어야 합니다.

## 🛠️ 설치

### 로컬 개발 중 (현재)
```bash
# 의존성 설치 후 직접 스크립트 실행
uv sync
uv run task-writer/scripts/taiga_api.py list-projects
```

### 글로벌 설치 (개인 도구로 등록) — git repo 공개 후
`pyproject.toml`에 `[project.scripts]` entry point를 추가하면 아래처럼 어디서든 명령어로 호출할 수 있습니다.

```bash
# git repo에 올린 후 한 번만 실행
uv tool install git+https://github.com/<your-username>/taiga-task-writer.git

# 이후 어느 디렉토리에서든 바로 사용
taiga list-projects
taiga create-userstory --subject "제목" ...

# 업데이트
uv tool upgrade taiga-task-writer
```

> `uv tool`은 격리된 전용 venv를 글로벌로 관리하므로, 다른 프로젝트 환경에 영향을 주지 않습니다.

### entry point 설정 (`pyproject.toml`)
글로벌 설치 전에 `pyproject.toml`에 아래 항목을 추가해야 합니다:
```toml
[project.scripts]
taiga = "scripts.taiga_api:main"
```

## ⚙️ 환경 변수
`task-writer/scripts/setup_env.py`를 참고하거나, 아래 변수를 직접 설정하세요:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `TAIGA_BASE_URL` | `https://api.taiga.io/api/v1` | Taiga API 주소 |
| `TAIGA_DOMAIN` | `taiga` | 토큰 추출 대상 도메인 |
| `TAIGA_PROJECT_ID` | — | 기본으로 사용할 프로젝트 ID |

## 📖 사용 방법
AI 스킬(`SKILL.md`)을 통해 자연어로 요청하세요:
- "고객사 이슈 등록해줘"
- "내부 TODO 추가해줘"
- "신규 기능 작업 쪼개서 등록해줘"

## 💻 직접 실행 (CLI)
```bash
# 프로젝트 목록 확인
uv run task-writer/scripts/taiga_api.py list-projects

# User Story 생성 (기본)
uv run task-writer/scripts/taiga_api.py create-userstory --project <ID> --subject "제목" --description "설명"

# User Story + 하위 Task 함께 생성
uv run task-writer/scripts/taiga_api.py create-userstory --project <ID> --subject "제목" --description "설명" \
  --tasks-json '[{"subject": "Task 1", "description": "..."}, {"subject": "Task 2"}]'

# 기존 User Story에 Task 추가
uv run task-writer/scripts/taiga_api.py create-task --project <ID> --us <US_ID> --subject "태스크 제목"
```
