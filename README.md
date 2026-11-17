# Engineering Atlas

AI로 제품을 만드는 사람이 코드의 동작·설계·품질을 스스로 판단하는 능력을 기르는 개인 소프트웨어 엔지니어링 학습 시스템입니다. 제품 코드는 각 제품 저장소에 두고, 여기에는 커리큘럼·지식·학습 근거·문제 해결 경험만 축적합니다. 기본 언어는 한국어이며 코드 식별자와 기술 용어는 영어를 유지합니다.

## 역할과 실행 환경

- **Claude Code**: 별도 제품 저장소에서 구현·테스트·디버깅·커밋·PR과 설계 결정 및 검증 결과를 기록합니다.
- **GPT**: 이 저장소와 제공된 제품 변경을 근거로 이론 강의·코드 해설·설계 멘토링·학습 관리를 합니다.
- **Codex**: 학습 저장소의 구조와 검증 도구를 구축·개선합니다.
- **GitHub**: 제품과 학습 이력을 독립적으로 보관합니다. 학습 CI를 제품 빌드·배포에 연결하지 않습니다.

Markdown을 읽을 수 있는 편집기, Git, **Python 3.12 이상**이면 충분합니다. 외부 Python 패키지·서버·API 키가 필요하지 않습니다.

```sh
git clone https://github.com/otto-Choi/engineering-atlas.git
cd engineering-atlas
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

## 구성과 원본 위치

| 경로 | 책임 |
| --- | --- |
| [curriculum/](curriculum/README.md) | 18개 영역, 주요 개념 메타데이터와 선수 지식 DAG |
| [knowledge/](knowledge/README.md) | 학습할 때 확장하는 기술 지식 사전 |
| [progress/](progress/README.md) | 이해가 확인된 수준·추정 수준·근거 |
| [projects/](projects/README.md) | 여러 제품의 등록 정보 |
| [cases/](cases/README.md) | 커밋에 고정된 문제 해결·설계 결정의 원본 |
| [portfolio/](portfolio/README.md) | 사례의 공개 후보 선정과 외부 독자용 소개 |
| [mentor/](mentor/README.md) | 멘토의 판단 기준과 운영 절차 |
| [templates/](templates/README.md) | 지식·학습 세션·사례·포트폴리오 작성 양식 |
| [examples/](examples/README.md) | 가상 제품과 가상 학습 데이터; 실제 상태와 완전히 분리 |
| [scripts/validate.py](scripts/validate.py) | 구조·형식·참조·순환·내부 링크 검사 |

구축 범위·실행 결과·검사 한계는 [초기 구축 점검](docs/build-report.md)에 정리했습니다.

JSON은 UTF-8이며 필드 규칙은 [데이터 계약](docs/data-contract.md)을 따릅니다. 개념 정의의 원본은 catalog, 제품 정보는 registry, 문제 해결의 상세 원본은 case 문서입니다. 다른 기록은 ID와 경로를 참조합니다.

## 시작과 일상 사용

1. [멘토 시작 지침](mentor/start.md)을 새 GPT 대화에 제공합니다. GPT에 저장소 읽기 권한이 없다면 지침과 catalog, 현재 progress, 해당 project·case만 첨부합니다. 저장소 URL만 전달했다고 파일 접근을 가정하지 않습니다.
2. 제품이 생기면 [프로젝트 등록법](projects/README.md)에 따라 registry에 추가합니다. 아직 제품이 없어도 변수·함수·Git 같은 기초 이론부터 읽기 중심으로 시작할 수 있습니다.
3. 사용자가 요청하거나 중요한 기능·설계·반복 오류가 발생하면 커밋 SHA/PR와 변경 diff, 검증 결과를 제공합니다. 멘토는 [변경 분석 절차](mentor/change-analysis.md)로 최대 1~3개 주제를 고릅니다.
4. 학습 내용을 knowledge에, 학습자가 실제로 설명하거나 판단한 근거를 progress에 기록합니다. 설명을 읽었다는 사실만으로 수준을 높이지 않습니다. 자세한 규칙은 [평가 기준](mentor/assessment.md)을 따릅니다.
5. 문제 해결 경험이 있으면 cases에 원본을 작성하고 portfolio에는 해당 사례 ID를 연결합니다. 일반 학습 일지와 공개 성과를 구별합니다.
6. 변경 전후 검증 명령을 실행하고 diff에서 공개 가능 여부를 확인한 뒤 학습 저장소에 커밋합니다. 자동 GPT 호출이나 자동 진도 갱신은 없습니다.

GPT가 쓰기 권한이 있으면 작은 diff로 갱신하고 검증 결과를 제시합니다. 읽기만 가능하면 **파일 경로와 정확한 변경 내용**을 제공해 사용자가 적용합니다. 실제 대화 내용·수준·검증 결과를 만들어내지 않습니다.

## 공개 운영과 확장

[공개 자료 기준](docs/publication.md)을 모든 기록에 적용합니다. 비공개 제품은 공개 허용된 설명만 기록하고 코드·내부 주소·고객 데이터를 복제하지 않습니다. 개인정보가 포함된 대화 원문 대신 허용된 범위의 비식별 요약을 근거로 남깁니다.

현재 실제 학습·프로젝트·사례·포트폴리오 데이터는 빈 배열입니다. 예시는 성과가 아닙니다. 향후 실제 필요가 확인되면 개념·제품·평가 근거를 늘립니다. 검색·시각화·웹 공개는 파일 형식을 유지하며 별도 검토할 수 있으나, 이번 기반에는 웹앱·DB·RAG·MCP·멀티 에이전트·자동 리뷰·GitHub Pages를 도입하지 않습니다.
