# 제품 연결

[registry.json](registry.json)에 제품마다 고유 ID, 이름, 목적, GitHub URL, 공개 여부, 기술 스택, 개발 단계, 참고 문서 목록을 등록합니다. 정확한 필드는 [데이터 계약](../docs/data-contract.md)의 프로젝트를 참고합니다.

`repository_url`은 `https://github.com/OWNER/REPO`로 통일합니다. `.git`, 마지막 `/`, PR 경로는 넣지 않습니다. `documentation`은 `{"label": "설계 문서", "location": "docs/architecture.md"}`처럼 **제품 저장소 기준 위치**를 쓰거나 공개 HTTPS 문서를 가리킵니다. 이 경로는 학습 저장소의 내부 링크로 검사하지 않습니다.

비공개 제품은 `visibility: private`로 명시하되 등록 자체의 공개 권한도 먼저 확인합니다. 고객명·내부 주소가 드러나는 저장소 URL조차 허용되지 않으면 등록하지 않습니다. 비공개 코드나 문서 본문을 복제하지 않습니다. 공개 가능한 가명과 설명만으로 학습을 이어가며 민감한 근거는 이 공개 저장소에 저장하지 않습니다.

case는 project ID와 전체 40자리 커밋 SHA, PR 번호(없으면 null), 핵심 파일, 검증 결과를 저장합니다. URL은 registry의 원본을 바탕으로 구성합니다. PR은 `.../pull/번호`, 고정 코드는 `.../blob/SHA/파일`로 열 수 있습니다. 브랜치 이름만으로 과거 상태를 기록하지 않습니다. 이 연결은 제품 저장소의 실행과 CI에 아무 영향도 주지 않습니다.
