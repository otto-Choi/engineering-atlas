# 데이터 계약

Python 표준 라이브러리로 읽는 UTF-8 JSON을 사용합니다. 필드명은 영어, 설명은 한국어입니다. 별도 스키마 프레임워크는 사용하지 않으며 [validator](../scripts/validate.py)가 실행 가능한 형식 계약입니다. 계약을 바꾸면 이 문서·예시·테스트를 함께 갱신합니다.

## 공통 규칙

- ID는 소문자 kebab-case이며 각 목록에서 유일합니다. 개념 ID는 저장소 전체에서 하나의 뜻을 가지며 가능한 한 변경하지 않습니다.
- 모든 아래 필드는 필수입니다. 명시한 null과 빈 배열만 허용합니다. 알 수 없는 필드는 오타로 보고 실패합니다.
- 날짜는 유효한 `YYYY-MM-DD`, 단계·수준은 boolean이 아닌 정수입니다.
- 실제 상태는 루트의 4개 JSON 배열, 예시 상태는 examples 아래의 같은 4개 배열에 저장합니다. 실제 record는 `is_example: false`, 예시는 `true`입니다. namespace 간 project/case/document 참조는 금지하며 catalog ID만 공유합니다.
- 문서·근거 경로는 저장소 루트 기준 상대 경로로 `.md` 파일을 가리킵니다. `..`·절대 경로·저장소 밖 symlink를 허용하지 않습니다. Markdown 본문의 링크는 문서 위치 기준 `../`를 쓸 수 있지만 저장소 밖으로 나갈 수 없습니다.
- 배열의 문자열은 비어 있을 수 없고 중복되지 않습니다. 빈 배열 허용 여부는 아래 규칙을 따릅니다.
- 외부 URL은 실시간 확인하지 않습니다. 형태가 맞더라도 실제 커밋·PR·실행 결과인지 사람과 멘토가 확인해야 합니다.

## curriculum/catalog.json

최상위 객체는 `areas`, `sources`, `concepts` 배열을 가집니다.

| 대상 | 필드와 제약 |
| --- | --- |
| area | `id`, `name`(한국어 이름) |
| source | `id`, `title`, `url`(인증정보 없는 HTTPS) |
| concept | `id`, `name_ko`, `name_en`, `area`(area ID), `summary`(1~2문장 권장), `prerequisites`, `related`, `objectives`, `applications`, `stage`, `references` |

`prerequisites`, `related`는 존재하는 concept ID 배열로 빈 배열이 가능합니다. 선수 관계는 자기 참조와 순환을 금지하며, related는 자기 참조만 금지합니다. `objectives`, `applications`는 하나 이상의 문자열, `references`는 하나 이상의 source ID, `stage`는 1~4입니다. 정의한 모든 영역에는 개념이 있어야 합니다. 출처는 재사용을 위해 sources에 한 번만 저장합니다.

## projects/registry.json

| 필드 | 의미 |
| --- | --- |
| id / is_example | 프로젝트 ID / 예시 구분 |
| name / purpose | 이름 / 제품의 목적 |
| repository_url | `https://github.com/OWNER/REPO` 형식. `.git`·마지막 `/` 없이 통일 |
| visibility | `public` 또는 `private` |
| stack | 하나 이상의 기술명 |
| stage | `planning`, `development`, `maintenance`, `archived` |
| documentation | 하나 이상의 `{label, location}` 객체. location은 제품 저장소 내 상대 파일 경로 또는 공개 HTTPS URL |

예시는 [예시 registry](../examples/projects/registry.json)를 봅니다. 문서와 핵심 코드의 제품 내 경로는 로컬 존재 검사를 하지 않습니다. 학습 저장소에 제품 코드를 복사하지 않기 때문입니다.

## cases/index.json

| 필드 | 의미 |
| --- | --- |
| id / is_example / title / date | 사례 식별·구분·제목·학습 또는 결정 날짜 |
| concept_ids | 하나 이상의 유효한 concept ID |
| document | cases 안의 상세 Markdown 원본 경로 |
| references | 하나 이상의 `{project_id, commit_sha, pr_number, files}` |
| validation | `{status, method, result}` |
| public_safe | 사람이 해당 사례 공개 가능 여부를 점검한 boolean |

`project_id`는 같은 namespace의 등록 제품입니다. `commit_sha`는 전체 40자리 소문자 hex, `pr_number`는 1 이상의 정수 또는 null, `files`는 하나 이상의 제품 상대 파일 경로입니다. SHA가 없는 검토 메모는 progress 세션에 보류하고 확정된 개발 사례로 등록하지 않습니다. 예시만 0으로 채운 가상 SHA를 허용합니다.

`validation.status`는 `passed`, `failed`, `not_run`; method에는 명령·환경·조건, result에는 관찰 결과와 한계를 씁니다. 실행하지 않았다면 not_run을 쓰고 실행한 것처럼 적지 않습니다. 상세 실험은 case 문서에 둡니다. `public_safe`는 자동 보안 검사의 결과가 아닙니다.

## progress/records.json

| 필드 | 의미 |
| --- | --- |
| concept_id / is_example | 유효한 concept ID(한 개념당 한 record) / 예시 구분 |
| verified_level | 근거로 확인한 0~4. 기록 부재는 0 |
| estimated_level | 추정 0~4 또는 null. 검증 수준과 독립 |
| last_reviewed | 마지막 검토 날짜 |
| learning_notes | 실제로 학습한 내용의 짧은 요약 배열 |
| unverified_notes | 이해가 아직 확인되지 않은 내용 배열 |
| needs_learning | 보충할 부분 배열 |
| case_ids | 해당 개념을 포함하는 사례 ID 배열; 여러 제품 경험 통합 |
| evidence | `{kind, level, date, summary, source}` 객체 배열. 선택 필드 `case_id` |

notes·case_ids·evidence는 빈 배열이 가능합니다. verified가 1 이상이면 해당 수준 이상을 입증하는 근거가 하나 이상 있어야 합니다. kind별 허용 level은 [평가 기준](../mentor/assessment.md)의 1:1 대응을 따릅니다. 근거 날짜는 last_reviewed 이후일 수 없습니다. source는 공개 가능한 실제 설명/판단/실행 결과를 담은 Markdown 파일입니다.

Level 4는 `case_id`가 필수이고 record의 case_ids에도 포함되어야 합니다. 해당 사례에는 실행된 검증(passed/failed)이 필요합니다. 실패를 분석하고 해결·검증했는지는 근거 본문을 사람이 판단합니다. Level 4를 자동으로 부여하지 않습니다. 낮은 수준에서도 case_id를 선택적으로 연결할 수 있습니다.

## portfolio/index.json

| 필드 | 의미 |
| --- | --- |
| id / is_example / title | 후보 식별·구분·제목 |
| case_ids | 하나 이상의 같은 namespace 사례 ID |
| document | portfolio 안의 외부 독자용 소개 문서 |
| status | `candidate`, `ready`, `published` |
| publication_review | null 또는 `{date, notes}` 공개 점검 기록 |

ready/published는 점검 기록, public_safe가 true인 사례, 실행된 검증 결과가 필요합니다. 실패 사례도 근거와 배운 점이 있다면 가능합니다. 실제 공개 행위와 의미의 적합성은 사람이 확인합니다. 포트폴리오에 사례 전체를 중복 저장하지 않습니다.

## 검사 범위와 제한

검사기는 필수 파일·JSON 형태·메타데이터·참조·DAG·근거 형식·내부 Markdown 파일/앵커 링크를 검사합니다. Markdown의 inline/reference 링크와 ATX 제목, 명시적 HTML id 앵커를 지원하며 코드 블록/인라인 코드는 링크로 검사하지 않습니다. 복잡한 Markdown 확장 구문·HTML 링크·외부 URL의 응답·코드 SHA의 실재·비밀정보·학습 진실성·정당한 공개 권한까지 판정하지 않습니다. 이 범위 밖 판단은 멘토와 사용자가 맡습니다.
