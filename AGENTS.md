# Engineering Atlas 유지보수

- 제품 개발 코드나 서버를 추가하지 않는다. Markdown·JSON·Python 표준 라이브러리를 유지한다.
- 사용자 기록을 만들거나 숙련도를 올릴 때 실제 근거가 필요하다. examples는 실제 상태가 아니다.
- 개념 메타데이터는 curriculum/catalog.json, 필드 계약은 docs/data-contract.md가 원본이다.
- 변경 후 `python3 scripts/validate.py`와 `python3 -m unittest discover -s tests -v`를 실행한다.
- 공개 권한·비밀정보·개인정보·성과의 사실성은 사람이 검토한다. 자동 검사 통과만으로 공개 가능하다고 판단하지 않는다.
- 제품 저장소 코드를 수정하거나 학습 CI를 제품 빌드에 연결하지 않는다.
