import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate import ROOT, Validator


class AtlasValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'atlas'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', '__pycache__', '.venv'))

    def edit(self, path, change):
        target = self.root / path
        value = json.loads(target.read_text(encoding='utf-8'))
        change(value)
        target.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def errors(self):
        return '\n'.join(Validator(self.root).run())

    def test_repository_and_examples_pass(self):
        self.assertEqual(self.errors(), '')

    def test_real_namespace_accepts_complete_records(self):
        for folder, filename in [('projects', 'registry.json'), ('cases', 'index.json'),
                                 ('progress', 'records.json'), ('portfolio', 'index.json')]:
            source = self.root / 'examples' / folder / filename
            records = json.loads(source.read_text(encoding='utf-8'))
            for record in records:
                record['is_example'] = False
                if 'document' in record:
                    original = record['document']
                    record['document'] = original.removeprefix('examples/')
                    shutil.copyfile(self.root / original, self.root / record['document'])
                    # The fixture needs no Markdown links into the example namespace.
                    (self.root / record['document']).write_text('# Test fixture', encoding='utf-8')
                for evidence in record.get('evidence', []):
                    evidence['source'] = 'progress/test-session.md'
                for ref in record.get('references', []):
                    ref['commit_sha'] = 'a' * 40
            (self.root / folder / filename).write_text(json.dumps(records), encoding='utf-8')
        (self.root / 'progress/test-session.md').write_text('# Temporary fixture', encoding='utf-8')
        self.assertEqual(self.errors(), '')

    def test_empty_catalog_is_rejected(self):
        (self.root / 'curriculum/catalog.json').write_text(
            '{"areas": [], "sources": [], "concepts": []}', encoding='utf-8')
        self.assertIn('비어 있지 않은 배열', self.errors())

    def test_duplicate_concept_id(self):
        self.edit('curriculum/catalog.json', lambda c: c['concepts'].append(c['concepts'][0].copy()))
        self.assertIn('ID 중복', self.errors())

    def test_missing_prerequisite(self):
        self.edit('curriculum/catalog.json', lambda c: c['concepts'][0]['prerequisites'].append('missing-concept'))
        self.assertIn('존재하지 않는 참조: missing-concept', self.errors())

    def test_cycle_across_branches(self):
        self.edit('curriculum/catalog.json', lambda c: c['concepts'][0]['prerequisites'].append('prog-modules'))
        self.assertIn('선수 지식 순환', self.errors())

    def test_self_cycle(self):
        self.edit('curriculum/catalog.json', lambda c: c['concepts'][0]['prerequisites'].append('prog-values'))
        self.assertIn('선수 지식 순환', self.errors())

    def test_missing_metadata(self):
        self.edit('curriculum/catalog.json', lambda c: c['concepts'][0].pop('objectives'))
        self.assertIn('필수 필드 누락: objectives', self.errors())

    def test_unknown_reference_source(self):
        self.edit('curriculum/catalog.json', lambda c: c['concepts'][0]['references'].append('imaginary-book'))
        self.assertIn('존재하지 않는 참조: imaginary-book', self.errors())

    def test_unknown_progress_concept(self):
        self.edit('examples/progress/records.json', lambda r: r[0].update(concept_id='does-not-exist'))
        self.assertIn('존재하지 않는 참조: does-not-exist', self.errors())

    def test_duplicate_progress(self):
        self.edit('examples/progress/records.json', lambda r: r.append(r[0].copy()))
        self.assertIn('개념별 진도 중복', self.errors())

    def test_lecture_is_not_evidence(self):
        self.edit('examples/progress/records.json', lambda r: r[0].update(verified_level=1, evidence=[]))
        self.assertIn('뒷받침하는 근거가 없습니다', self.errors())

    def test_estimate_can_be_unverified(self):
        self.edit('examples/progress/records.json', lambda r: r[0].update(verified_level=0, estimated_level=3, evidence=[]))
        self.assertEqual(self.errors(), '')

    def test_wrong_evidence_kind(self):
        self.edit('examples/progress/records.json', lambda r: r[0]['evidence'][0].update(kind='code_reading'))
        self.assertIn('근거 종류와 수준', self.errors())

    def test_application_requires_case(self):
        self.edit('examples/progress/records.json', lambda r: r[4]['evidence'][0].pop('case_id'))
        self.assertIn('Level 4 적용 근거는 case_id', self.errors())

    def test_application_requires_executed_validation(self):
        self.edit('examples/cases/index.json', lambda r: r[0]['validation'].update(status='not_run'))
        self.assertIn('실행한 검증 결과', self.errors())

    def test_unknown_case_concept(self):
        self.edit('examples/cases/index.json', lambda r: r[0]['concept_ids'].append('missing-concept'))
        self.assertIn('존재하지 않는 참조: missing-concept', self.errors())

    def test_progress_case_must_contain_concept(self):
        self.edit('examples/cases/index.json', lambda r: r[0]['concept_ids'].remove('prog-functions'))
        self.assertIn('해당 개념이 없습니다', self.errors())

    def test_namespace_isolation(self):
        example = json.loads((self.root / 'examples/cases/index.json').read_text(encoding='utf-8'))
        example[0]['is_example'] = False
        (self.root / 'cases/index.json').write_text(json.dumps(example), encoding='utf-8')
        errors = self.errors()
        self.assertIn('교차 참조', errors)
        self.assertIn('존재하지 않는 참조: demo-pricing', errors)
        self.assertIn('실제 기록에 0 SHA 금지', errors)

    def test_example_label_required(self):
        self.edit('examples/projects/registry.json', lambda r: r[0].update(is_example=False))
        self.assertIn('is_example은 True', self.errors())

    def test_project_url_format(self):
        self.edit('examples/projects/registry.json', lambda r: r[0].update(repository_url='https://github.com/otto-Choi/engineering-atlas.git'))
        self.assertIn('repository_url은', self.errors())

    def test_full_commit_sha(self):
        self.edit('examples/cases/index.json', lambda r: r[0]['references'][0].update(commit_sha='123abcd'))
        self.assertIn('전체 40자리', self.errors())

    def test_invalid_pr_number_and_boolean_level(self):
        self.edit('examples/cases/index.json', lambda r: r[0]['references'][0].update(pr_number=0))
        self.edit('examples/progress/records.json', lambda r: r[0].update(verified_level=True))
        errors = self.errors()
        self.assertIn('pr_number', errors)
        self.assertIn('verified_level', errors)

    def test_publication_requires_review_and_safe_case(self):
        self.edit('examples/portfolio/index.json', lambda r: r[0].update(status='ready'))
        self.edit('examples/cases/index.json', lambda r: r[0].update(public_safe=False))
        errors = self.errors()
        self.assertIn('공개 점검 기록', errors)
        self.assertIn('공개 가능한 사례', errors)

    def test_publication_with_review_passes(self):
        self.edit('examples/portfolio/index.json', lambda r: r[0].update(status='ready', publication_review={'date': '2026-11-17', 'notes': '가상 공개 점검'}))
        self.assertEqual(self.errors(), '')

    def test_missing_file_and_broken_links(self):
        (self.root / 'knowledge/README.md').unlink()
        errors = self.errors()
        self.assertIn('필수 파일 없음', errors)
        self.assertIn('파일 없음: knowledge/README.md', errors)

    def test_reference_links_unicode_anchors_and_code_ignored(self):
        (self.root / 'progress/link-test.md').write_text('''# 한글 제목

[정상](#한글-제목)
[파일 참조][guide]
[guide]: ../README.md

`[무시](missing-inline.md)`

```md
[무시](missing-fenced.md)
```
''', encoding='utf-8')
        self.assertEqual(self.errors(), '')
        with (self.root / 'progress/link-test.md').open('a', encoding='utf-8') as f:
            f.write('\n[잘못된 앵커](#없는-제목)\n[missing]: ../missing.md\n')
        errors = self.errors()
        self.assertIn('문서 앵커 없음', errors)
        self.assertIn('파일 없음: ../missing.md', errors)

    def test_local_link_cannot_escape_repository(self):
        (self.root / 'progress/escape.md').write_text('[밖](../../outside.md)', encoding='utf-8')
        self.assertIn('저장소 밖 경로', self.errors())

    def test_metadata_path_cannot_escape_repository(self):
        self.edit('examples/cases/index.json', lambda r: r[0].update(document='../outside.md'))
        self.assertIn('상대 경로', self.errors())

    def test_invalid_date(self):
        self.edit('examples/progress/records.json', lambda r: r[0].update(last_reviewed='2026-02-30'))
        self.assertIn('유효한 날짜', self.errors())

    def test_future_evidence_relative_to_review(self):
        self.edit('examples/progress/records.json', lambda r: r[0]['evidence'][0].update(date='2026-11-18'))
        self.assertIn('마지막 검토일보다 늦습니다', self.errors())

    def test_knowledge_requires_known_id(self):
        (self.root / 'knowledge/imaginary.md').write_text('# Test', encoding='utf-8')
        self.assertIn('지식 문서 파일명', self.errors())

    def test_invalid_json_and_duplicate_keys(self):
        (self.root / 'projects/registry.json').write_text('{broken', encoding='utf-8')
        (self.root / 'curriculum/catalog.json').write_text('{"areas": [], "areas": []}', encoding='utf-8')
        errors = self.errors()
        self.assertIn('JSON 읽기 실패', errors)
        self.assertIn('JSON 키 중복', errors)

    def test_malformed_metadata_reports_errors_without_crash(self):
        self.edit('curriculum/catalog.json', lambda c: c['concepts'][0].update(prerequisites={}, related=None, stage=True, references=[{}]))
        self.edit('examples/cases/index.json', lambda r: r[0].update(references=[None], validation=[]))
        self.edit('examples/progress/records.json', lambda r: r[0].update(evidence=[None], case_ids=[{}]))
        self.assertIn('필요합니다', self.errors())

    def test_unknown_field_is_error(self):
        self.edit('examples/projects/registry.json', lambda r: r[0].update(repostory_url='typo'))
        self.assertIn('알 수 없는 필드: repostory_url', self.errors())

    def test_malformed_url_is_reported(self):
        self.edit('curriculum/catalog.json', lambda c: c['sources'][0].update(url='https://['))
        self.assertIn('URL', self.errors())


if __name__ == '__main__':
    unittest.main()
