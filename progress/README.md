# 학습 진도

[records.json](records.json)은 실제 개념별 상태입니다. 기록이 없는 개념은 **Level 0, 미학습**으로 읽습니다. 모든 개념의 0 값을 미리 복제하지 않습니다. 수준의 의미와 근거 종류는 [평가 기준](../mentor/assessment.md), 필드 규칙은 [데이터 계약](../docs/data-contract.md)을 따릅니다.

학습 세션은 [템플릿](../templates/session.md)을 이용해 이 폴더에 Markdown으로 기록하고, 근거의 `source`로 참조합니다. 세션마다 실제 학습한 내용, 확인된 설명/판단, 미확인 내용, 추가 학습, 적용 사례를 구별합니다. 기록에는 날짜를 남기고 Git으로 수정 이력을 보존합니다.

`verified_level`과 `estimated_level`은 별개입니다. 추정은 확정이 아니며 빈 값(null)도 허용합니다. verified 수준은 근거가 없으면 0입니다. 수준을 수정할 때 과거 근거를 삭제해 덮어쓰지 말고, 새 근거와 한계를 추가합니다. 여러 제품의 사례를 한 concept record의 `case_ids`로 연결합니다. 퀴즈는 필수가 아닙니다.
