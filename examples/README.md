# 예시 전용 데이터 — 실제 제품·학습·성과가 아닙니다

이 폴더는 연결 방식의 검증을 위한 **가상 시나리오**입니다. 실제 학습 진도와 섞거나 루트 배열에 그대로 복사하지 않습니다. 각 record는 is_example=true이며, 검증 도구는 이 namespace를 실제 상태와 분리합니다. 여섯 기초 개념 ID는 실제 catalog를 재사용합니다.

- [제품](projects/registry.json): 가상의 가격 계산 연습 제품. GitHub URL은 현재 학습 저장소 주소를 형식 시연에만 사용하며 이 주소에 제품 코드가 있다는 뜻이 아닙니다.
- [사례](cases/index.json)와 [상세 기록](cases/demo-module-boundary.md): 계산과 입출력을 분리했다는 가상 상황.
- [진도](progress/records.json)와 [세션](progress/demo-session.md): 확인/추정/미확인/보충/적용을 구별하는 예시.
- [후보](portfolio/index.json)와 [소개](portfolio/demo-boundary.md): 원본 사례를 참조하는 후보 예시.
- [함수 지식](knowledge/prog-functions.md): 부분만 작성한 사전 문서 예시.

커밋 SHA 40개의 0, 파일명, 대화 요약, 테스트 결과는 모두 가상이며 실제 실행이나 사용자 역량을 주장하지 않습니다. 이 SHA로 GitHub 링크를 열거나 실제 코드 분석 근거로 쓰지 마세요. 실제 기록을 시작할 때에는 루트의 빈 배열에 검증 가능한 데이터만 작성합니다.
