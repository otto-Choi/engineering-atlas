# 함수 (Functions) — 예시

개념 ID: `prog-functions`. 교육용 설명이며 사용자의 이해 근거가 아닙니다.

## 정의와 필요성

함수는 입력을 받아 동작하고 결과를 반환하는 단위입니다. 계산 규칙을 이름으로 묶으면 입력이 바뀔 때마다 같은 규칙을 재사용하고 별도로 검사할 수 있습니다.

```python
def subtotal(price, quantity):
    return price * quantity
```

`subtotal(10, 3)`은 30을 반환합니다. `return`은 값을 호출자에게 전달하며 `print`는 화면에 표시하는 부수효과입니다. 둘을 혼동하면 함수의 결과가 None인 이유를 놓칠 수 있습니다.

## 연결

선수 개념·목표의 원본은 [catalog](../../curriculum/catalog.json)이며 실제 적용 형태는 [가상 사례](../cases/demo-module-boundary.md)에서 볼 수 있습니다. [Python 함수 문서](https://docs.python.org/3/tutorial/)를 참고합니다. 이 문서만으로 학습 완료를 기록하지 않습니다.
