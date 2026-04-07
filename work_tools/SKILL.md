---
name: task-writer
description:
  AI를 사용하여 Taiga에 유저스토리 및 태스크를 자동으로 관리합니다. 브라우저 세션의 토큰을 활용하여 인증을 처리하며, 사용자의 요청 성격에 맞는 가이드라인(References)을 참조하여 구조화된 태스크를 작성합니다.
---

# Skill: Taiga Task Writer

## Instructions
1. **인증 확인**: 항상 `task-writer/scripts/get_token.py`를 사용하여 브라우저(Chrome)에서 최신 Taiga 인증 토큰을 가져오는지 확인하세요.
2. **프로젝트 선택**: 기본적으로 프로젝트가 환경변수로 선택되어 있다고 가정하고 진행합니다. 단, API 호출 중 프로젝트 관련 오류가 발생한 경우에만 `task-writer/scripts/taiga_api.py list-projects`를 실행하여 사용 가능한 프로젝트 목록을 사용자에게 보여주고 다시 선택하게 하세요.
3. **가이드라인 라우팅**: 사용자의 요청 내용에 따라 적절한 가이드라인을 참조하세요.
   - **스크립트 명령어 API**: `task-writer/references/api_spec.md`를 참조하여 API 명세를 숙지하고, 각 명령어의 사용법과 옵션을 정확히 이해하세요.
   - **고객사 이슈 등록**: `task-writer/references/issue_guideline.md` 참조
   - **추후 작업/TODO**: `task-writer/references/future_task_guideline.md` 참조
   - **신규 기능 추가/큰 작업**: `task-writer/references/feature_guideline.md` 참조
4. **태스크 구조화**: 선택된 가이드라인의 제목 패턴과 설명 템플릿을 엄격히 준수하세요. Markdown 형식을 활용하여 가독성 있게 작성합니다.
5. **User Story 조회**: 기존 US를 조회할 때는 아래 두 가지 방법을 사용합니다.
   - **이름으로 검색** (`search-userstories`): 키워드로 여러 US를 조회할 때 사용합니다.
     - `task-writer/scripts/taiga_api.py search-userstories --project <PROJECT_ID> --query "<검색어>" --me`
     - 검색 결과로 `ID`, `Ref(#번호)`, `Subject`, `Assignee`가 출력됩니다.
     - 검색 결과가 **1개**이면 자동으로 해당 US를 선택하고 바로 다음 단계로 진행하세요.
     - 검색 결과가 **2개 이상**이면 사용자가 원하는 US를 선택하게 하세요.
   - **ID 또는 Ref 번호로 단건 조회** (`get-userstory`): 정확한 내부 ID 또는 `#ref` 번호를 알고 있을 때 사용합니다.
     - 내부 ID로 조회: `task-writer/scripts/taiga_api.py get-userstory --id <US_ID>`
     - Ref 번호로 조회: `task-writer/scripts/taiga_api.py get-userstory --ref <REF> --project <PROJECT_ID>`
     - 조회 결과로 `ID`, `Ref(#번호)`, `Subject`, `Assignee`, `Version`, `URL`이 출력됩니다.
6. **태스크 생성**: Taiga 관리 체계에 따라 **항상 User Story를 생성**하는 것을 원칙으로 합니다.
   - **User Story 수정**: 이미 생성된 User Story의 제목/설명/상태/담당자를 변경할 때 사용합니다.
     1. 대상 US의 내부 ID를 확인합니다. **5번 항목**을 참고하여 이름 검색 또는 ref 번호 조회로 내부 ID를 확인하세요.
     2. `update-userstory`로 변경할 필드만 지정합니다. `--id` 또는 `--ref`를 사용할 수 있습니다.
        - 제목 변경: `--subject "<새 제목>"`
        - 설명 변경: `--description "<새 설명>"`
        - 상태 변경: `--status <STATUS_ID>`
        - 담당자 변경: `--assigned-to <USER_ID>` 또는 `--me`
        - ID로 수정 예시: `task-writer/scripts/taiga_api.py update-userstory --id <US_ID> --subject "<새 제목>" --description "<새 설명>" --me`
        - Ref로 수정 예시: `task-writer/scripts/taiga_api.py update-userstory --ref <REF> --project <PROJECT_ID> --subject "<새 제목>" --me`
   - **User Story 생성**: `task-writer/scripts/taiga_api.py create-userstory --project <PROJECT_ID> --subject "<US_SUBJECT>" --description "<US_DESCRIPTION>"`
     - 하위 태스크가 필요한 경우에만 `--tasks-json` 또는 `--tasks` 옵션을 추가합니다.
     - JSON 형식: `[{"subject": "Task 1", "description": "..."}, {"subject": "Task 2", "description": "..."}]`
   - **기존 US에 Task 추가**: 이미 생성된 특정 User Story에 추가 작업만 등록할 때만 `create-task`를 사용합니다.
     1. 대상 US의 내부 ID를 확인합니다. **5번 항목**을 참고하여 이름 검색 또는 ref 번호 조회로 내부 ID를 확인하세요.
     2. US ID 확인 후 `create-task --us <US_ID>` 혹은 `create-task --us-ref <US_REF>`로 태스크를 **한 번에 여러 개** 생성합니다.
        - **여러 태스크 (권장)**: `--tasks-json '[{"subject": "...", "description": "..."}, ...]'`
        - **단순 여러 태스크**: `--tasks "태스크1" "태스크2" "태스크3"`
        - **단일 태스크**: `--subject "<TASK_SUBJECT>" --description "<TASK_DESCRIPTION>"`
        - 전체 예시: `task-writer/scripts/taiga_api.py create-task --project <PROJECT_ID> --us <US_ID> --tasks-json '[{"subject": "...", "description": "..."}, ...]'`
   - 사용자가 **"나에게 할당"** 또는 **"내가 할 일"**이라고 언급하면 `--me` 옵션을 반드시 추가하세요.
7. **Custom Attributes 처리**: Taiga 유저스토리에는 프로젝트별로 고정된 Custom Attribute 필드가 있습니다.
   - **가이드라인 활용 (권장)**: 각 가이드라인에서 제안하는 Custom Attribute ID 값을 참조하여 사용하세요.
     - 예시: `**기능 상세 (ID: 8)**: 해당 기능의 목적 및 핵심 로직 요약`
   - **조회**: `task-writer/scripts/taiga_api.py get-custom-attr-values --ref <REF> --project <PROJECT_ID>`
     - 또는 내부 ID: `task-writer/scripts/taiga_api.py get-custom-attr-values --id <US_ID>`
   - **목록 확인**: `task-writer/scripts/taiga_api.py list-custom-attributes --project <PROJECT_ID>`
   - **수정**: `task-writer/scripts/taiga_api.py update-custom-attr-values --ref <REF> --project <PROJECT_ID> --values-json '{"<ATTR_ID>": "value"}'`
     - `<ATTR_ID>`는 `list-custom-attributes`로 확인하거나 환경변수 `TAIGA_CA_*` 값을 그대로 사용합니다.
     - 여러 속성 동시 수정 가능: `'{"123": "High", "456": "Sprint 3"}'`
   - **US 생성 시 Custom Attributes 설정**: `create-userstory`는 Custom Attributes를 직접 지원하지 않으므로, US 생성 후 별도로 `update-custom-attr-values`를 호출하세요.

## References
- `task-writer/references/issue_guideline.md`
- `task-writer/references/future_task_guideline.md`
- `task-writer/references/feature_guideline.md`

## Scripts
- `task-writer/scripts/get_token.py`: 토큰 추출 스크립트
- `task-writer/scripts/taiga_api.py`: Taiga API 연동 스크립트 (User Story 중심 생성)

## Example Usage
- "고객사 A에서 결제 오류가 발생했대. 관련 로그 복사해줄게, 이걸로 태스크 만들어줘." -> `issue_guideline.md` 적용, `create-userstory` 실행
- "나중에 코드 리팩토링 해야 할 것 같은데, 일단 TODO로 등록해줘. 내용은 'API 모듈화'야." -> `future_task_guideline.md` 적용, `create-userstory` 실행
- "이번에 새로운 '다크모드 지원' 기능을 추가하기로 했어. 백엔드랑 프론트 작업 쪼개서 태스크 생성해줘. 나한테 할당해주는 거 잊지 말고." -> `feature_guideline.md` 적용, `create-userstory`에 `--tasks-json` 및 `--me` 옵션 사용
- "'로그인 개선' 유저 스토리에 태스크 하나 더 추가해줘." -> `search-userstories --query "로그인 개선" --me`로 US ID 확인 후 `create-task --us <ID>` 실행
- "#42번 유저 스토리에 태스크 추가해줘." -> `get-userstory --ref 42 --project <PROJECT_ID>`로 내부 ID 확인 후 `create-task --us <ID>` 실행
- "'다크모드 지원' US 제목을 '다크모드 지원 (v2)'로 바꾸고 나한테 할당해줘." -> `search-userstories --query "다크모드 지원"`으로 ID 확인 후 `update-userstory --id <ID> --subject "다크모드 지원 (v2)" --me` 실행
- "#42번 US 제목 바꿔줘." -> `update-userstory --ref 42 --project <PROJECT_ID> --subject "<새 제목>"` 실행
