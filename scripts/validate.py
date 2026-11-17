#!/usr/bin/env python3
"""Validate Atlas files without network access or third-party dependencies."""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
REPO = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
KINDS = {"learner_explanation": 1, "code_reading": 2, "design_decision": 3,
         "application_validation": 4}
DATA_FILES = {"projects": "projects/registry.json", "cases": "cases/index.json",
              "progress": "progress/records.json", "portfolio": "portfolio/index.json"}
REQUIRED = ["README.md", "curriculum/catalog.json", "docs/data-contract.md",
            "docs/publication.md", "mentor/README.md", "mentor/start.md",
            "mentor/assessment.md", "mentor/change-analysis.md", "scripts/validate.py",
            "tests/test_validate.py", ".github/workflows/validate.yml",
            "templates/README.md", "templates/knowledge.md", "templates/session.md",
            "templates/case.md", "templates/portfolio.md", "examples/README.md"]
REQUIRED += [f"{d}/README.md" for d in ("curriculum", "knowledge", "progress", "projects", "cases", "portfolio")]
REQUIRED += list(DATA_FILES.values()) + [f"examples/{p}" for p in DATA_FILES.values()]


def markdown_text(text):
    lines, fence = [], None
    for line in text.splitlines():
        mark = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if mark:
            token = mark[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return "\n".join(lines)


def anchors(text):
    found, counts = set(), {}
    for title in re.findall(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", markdown_text(text), re.M):
        title = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", title)
        slug = "".join(c for c in title.lower() if c.isalnum() or c in " _-").replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(f"{slug}-{count}" if count else slug)
    found.update(re.findall(r'''\b(?:id|name)=["']([^"']+)["']''', text))
    return found


class Validator:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.errors = []

    def error(self, where, message):
        self.errors.append(f"{where}: {message}")

    def fields(self, value, required, where, optional=()):
        if not isinstance(value, dict):
            self.error(where, "객체가 필요합니다")
            return False
        for key in sorted(set(required) - value.keys()):
            self.error(where, f"필수 필드 누락: {key}")
        for key in sorted(value.keys() - set(required) - set(optional)):
            self.error(where, f"알 수 없는 필드: {key}")
        return True

    def string(self, value, where):
        if not isinstance(value, str) or not value.strip():
            self.error(where, "비어 있지 않은 문자열이 필요합니다")
            return False
        return True

    def strings(self, value, where, nonempty=False):
        if not isinstance(value, list):
            self.error(where, "문자열 배열이 필요합니다")
            return []
        result = []
        for i, item in enumerate(value):
            if self.string(item, f"{where}[{i}]"):
                result.append(item)
        if len(result) != len(set(result)):
            self.error(where, "배열 값 중복")
        if nonempty and not result:
            self.error(where, "하나 이상의 값이 필요합니다")
        return result

    def enum(self, value, choices, where):
        if value not in list(choices):
            self.error(where, f"허용 값: {', '.join(map(str, choices))}")

    def boolean(self, value, where):
        if type(value) is not bool:
            self.error(where, "boolean이 필요합니다")

    def integer(self, value, low, high, where):
        if type(value) is not int or not low <= value <= high:
            self.error(where, f"정수 {low}~{high}가 필요합니다")
            return False
        return True

    def date(self, value, where):
        try:
            if not isinstance(value, str) or dt.date.fromisoformat(value).isoformat() != value:
                raise ValueError
        except ValueError:
            self.error(where, "YYYY-MM-DD 형식의 유효한 날짜가 필요합니다")

    def https(self, value, where):
        if not self.string(value, where):
            return
        try:
            parsed = urlsplit(value)
        except ValueError:
            self.error(where, "유효하지 않은 URL입니다")
            return
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            self.error(where, "인증정보 없는 HTTPS URL이 필요합니다")

    def path(self, value, where, base=None, must_exist=True, allow_parent=False):
        if not self.string(value, where):
            return None
        path = Path(unquote(value))
        if path.is_absolute() or (not allow_parent and ".." in path.parts) or "\\" in value or ":" in value:
            self.error(where, "저장소 안의 상대 경로가 필요합니다")
            return None
        target = ((base or self.root) / path).resolve()
        if not target.is_relative_to(self.root):
            self.error(where, "저장소 밖 경로")
            return None
        if must_exist and not target.is_file():
            self.error(where, f"파일 없음: {value}")
            return None
        return target

    def document(self, value, where, example, folder=None):
        target = self.path(value, where)
        if target:
            relative = target.relative_to(self.root)
            if target.suffix != ".md":
                self.error(where, "Markdown 문서가 필요합니다")
            if (relative.parts[0] == "examples") != example:
                self.error(where, "실제/예시 문서를 교차 참조할 수 없습니다")
            prefix = Path("examples") / folder if example and folder else Path(folder or ".")
            if folder and not relative.is_relative_to(prefix):
                self.error(where, f"문서는 {prefix}/ 안에 있어야 합니다")

    def read_json(self, relative, expected):
        path = self.root / relative
        try:
            def unique_keys(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError(f"JSON 키 중복: {key}")
                    result[key] = value
                return result
            data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
        except (OSError, ValueError) as exc:
            self.error(relative, f"JSON 읽기 실패: {exc}")
            return expected()
        if not isinstance(data, expected):
            self.error(relative, f"{expected.__name__} 형식이 필요합니다")
            return expected()
        return data

    def records(self, values, where):
        if not isinstance(values, list):
            self.error(where, "객체 배열이 필요합니다")
            return {}
        result = {}
        for n, item in enumerate(values):
            loc = f"{where}[{n}]"
            if not isinstance(item, dict):
                self.error(loc, "객체가 필요합니다")
                continue
            key = item.get("id")
            if not isinstance(key, str) or not ID.fullmatch(key):
                self.error(loc, "유효한 소문자 kebab-case ID가 필요합니다")
                continue
            if key in result:
                self.error(loc, f"ID 중복: {key}")
            result[key] = item
        return result

    def refs(self, value, valid, where, nonempty=False):
        values = self.strings(value, where, nonempty)
        for key in values:
            if key not in valid:
                self.error(where, f"존재하지 않는 참조: {key}")
        return values

    def catalog(self):
        catalog = self.read_json("curriculum/catalog.json", dict)
        self.fields(catalog, {"areas", "sources", "concepts"}, "catalog")
        for field in ("areas", "sources", "concepts"):
            if not catalog.get(field):
                self.error("catalog." + field, "비어 있지 않은 배열이 필요합니다")
        areas = self.records(catalog.get("areas"), "areas")
        for key, area in areas.items():
            self.fields(area, {"id", "name"}, key)
            self.string(area.get("name"), key + ".name")
        sources = self.records(catalog.get("sources"), "sources")
        for key, source in sources.items():
            self.fields(source, {"id", "title", "url"}, key)
            self.string(source.get("title"), key + ".title")
            self.https(source.get("url"), key + ".url")
        concepts = self.records(catalog.get("concepts"), "concepts")
        required = {"id", "name_ko", "name_en", "area", "summary", "prerequisites",
                    "related", "objectives", "applications", "stage", "references"}
        graph = {}
        used_areas = set()
        for key, concept in concepts.items():
            self.fields(concept, required, key)
            for field in ("name_ko", "name_en", "summary"):
                self.string(concept.get(field), f"{key}.{field}")
            area = concept.get("area")
            if not isinstance(area, str) or area not in areas:
                self.error(key, "유효한 학습 영역이 필요합니다")
            else:
                used_areas.add(area)
            self.integer(concept.get("stage"), 1, 4, key + ".stage")
            for field in ("objectives", "applications"):
                self.strings(concept.get(field), f"{key}.{field}", True)
            graph[key] = self.refs(concept.get("prerequisites"), concepts, key + ".prerequisites")
            self.refs(concept.get("related"), concepts, key + ".related")
            if key in self.valid_list(concept.get("related")):
                self.error(key, "자기 자신을 related로 참조할 수 없습니다")
            self.refs(concept.get("references"), sources, key + ".references", True)
        for key in areas.keys() - used_areas:
            self.error(key, "개념이 없는 학습 영역")
        # Kahn's algorithm avoids recursion depth limits as the curriculum grows.
        pending = {key: set(pre) & concepts.keys() for key, pre in graph.items()}
        ready = [key for key, pre in pending.items() if not pre]
        children = {key: [] for key in concepts}
        for key, pre in pending.items():
            for parent in pre:
                children[parent].append(key)
        visited = set()
        while ready:
            key = ready.pop()
            visited.add(key)
            for child in children[key]:
                pending[child].discard(key)
                if not pending[child]:
                    ready.append(child)
        if len(visited) != len(concepts):
            self.error("prerequisites", "선수 지식 순환 또는 순환에 의존하는 개념: " + ", ".join(sorted(concepts.keys() - visited)))
        return concepts

    def datasets(self, concepts, example=False):
        prefix = "examples/" if example else ""
        datasets = {kind: self.read_json(prefix + path, list) for kind, path in DATA_FILES.items()}
        projects = self.records(datasets["projects"], prefix + "projects")
        cases = self.records(datasets["cases"], prefix + "cases")
        portfolios = self.records(datasets["portfolio"], prefix + "portfolio")
        for kind in ("projects", "cases", "portfolio", "progress"):
            for index, record in enumerate(datasets[kind]):
                if not isinstance(record, dict):
                    self.error(f"{prefix}{kind}[{index}]", "객체가 필요합니다")
                    continue
                if record.get("is_example") is not example:
                    self.error(f"{prefix}{kind}[{index}]", f"is_example은 {example}여야 합니다")
        for key, project in projects.items():
            self.fields(project, {"id", "is_example", "name", "purpose", "repository_url", "visibility", "stack", "stage", "documentation"}, key)
            for field in ("name", "purpose"):
                self.string(project.get(field), key + "." + field)
            url = project.get("repository_url")
            if not isinstance(url, str) or not REPO.fullmatch(url) or url.endswith(".git"):
                self.error(key, "repository_url은 https://github.com/OWNER/REPO 형식이어야 합니다")
            self.enum(project.get("visibility"), ("public", "private"), key + ".visibility")
            self.enum(project.get("stage"), ("planning", "development", "maintenance", "archived"), key + ".stage")
            self.strings(project.get("stack"), key + ".stack", True)
            docs = project.get("documentation")
            if not isinstance(docs, list) or not docs:
                self.error(key, "documentation은 하나 이상의 문서 위치가 필요합니다")
            else:
                for doc in docs:
                    if not self.fields(doc, {"label", "location"}, key + ".documentation"):
                        continue
                    self.string(doc.get("label"), key + ".documentation.label")
                    location = doc.get("location")
                    if isinstance(location, str) and location.startswith("https://"):
                        self.https(location, key + ".documentation.location")
                    else:
                        self.path(location, key + ".documentation.location", must_exist=False)
        for key, case in cases.items():
            self.fields(case, {"id", "is_example", "title", "date", "concept_ids", "document", "references", "validation", "public_safe"}, key)
            self.string(case.get("title"), key + ".title")
            self.date(case.get("date"), key + ".date")
            self.refs(case.get("concept_ids"), concepts, key + ".concept_ids", True)
            self.document(case.get("document"), key + ".document", example, "cases")
            self.boolean(case.get("public_safe"), key + ".public_safe")
            refs = case.get("references")
            if not isinstance(refs, list) or not refs:
                self.error(key, "하나 이상의 제품 변경 참조가 필요합니다")
            else:
                for ref in refs:
                    if not self.fields(ref, {"project_id", "commit_sha", "pr_number", "files"}, key + ".references"):
                        continue
                    self.refs([ref.get("project_id")], projects, key + ".project_id", True)
                    sha = ref.get("commit_sha")
                    if not isinstance(sha, str) or not SHA.fullmatch(sha) or (not example and sha == "0" * 40):
                        self.error(key, "전체 40자리 소문자 commit SHA가 필요합니다 (실제 기록에 0 SHA 금지)")
                    if ref.get("pr_number") is not None:
                        self.integer(ref.get("pr_number"), 1, 2**31 - 1, key + ".pr_number")
                    for file in self.strings(ref.get("files"), key + ".files", True):
                        self.path(file, key + ".files", must_exist=False)
            validation = case.get("validation")
            if self.fields(validation, {"status", "method", "result"}, key + ".validation"):
                self.enum(validation.get("status"), ("passed", "failed", "not_run"), key + ".validation.status")
                for field in ("method", "result"):
                    self.string(validation.get(field), key + ".validation." + field)
        seen_concepts = set()
        for record in datasets["progress"]:
            if not self.fields(record, {"concept_id", "is_example", "verified_level", "estimated_level", "last_reviewed", "learning_notes", "unverified_notes", "needs_learning", "case_ids", "evidence"}, prefix + "progress"):
                continue
            concept = record.get("concept_id")
            loc = f"{prefix}progress:{concept}"
            self.refs([concept], concepts, loc, True)
            if isinstance(concept, str):
                if concept in seen_concepts:
                    self.error(loc, "개념별 진도 중복")
                seen_concepts.add(concept)
            level = record.get("verified_level")
            level_valid = self.integer(level, 0, 4, loc + ".verified_level")
            if record.get("estimated_level") is not None:
                self.integer(record.get("estimated_level"), 0, 4, loc + ".estimated_level")
            self.date(record.get("last_reviewed"), loc + ".last_reviewed")
            for field in ("learning_notes", "unverified_notes", "needs_learning"):
                self.strings(record.get(field), loc + "." + field)
            case_ids = self.refs(record.get("case_ids"), cases, loc + ".case_ids")
            for case_id in case_ids:
                if case_id in cases and concept not in self.valid_list(cases[case_id].get("concept_ids")):
                    self.error(loc, f"사례 {case_id}에 해당 개념이 없습니다")
            evidence = record.get("evidence")
            supported = 0
            if not isinstance(evidence, list):
                self.error(loc, "evidence는 배열이어야 합니다")
            else:
                for item in evidence:
                    if not self.fields(item, {"kind", "level", "date", "summary", "source"}, loc + ".evidence", {"case_id"}):
                        continue
                    self.enum(item.get("kind"), KINDS, loc + ".evidence.kind")
                    ev_level = item.get("level")
                    ev_valid = self.integer(ev_level, 1, 4, loc + ".evidence.level")
                    if ev_valid:
                        kind = item.get("kind")
                        if not isinstance(kind, str) or KINDS.get(kind) != ev_level:
                            self.error(loc, "근거 종류와 수준이 일치하지 않습니다")
                        else:
                            supported = max(supported, ev_level)
                    self.date(item.get("date"), loc + ".evidence.date")
                    self.string(item.get("summary"), loc + ".evidence.summary")
                    self.document(item.get("source"), loc + ".evidence.source", example)
                    if "case_id" in item:
                        self.refs([item["case_id"]], cases, loc + ".evidence.case_id", True)
                        if item["case_id"] not in case_ids:
                            self.error(loc, "근거의 case_id는 진도의 case_ids에도 있어야 합니다")
                    if ev_level == 4 and "case_id" not in item:
                        self.error(loc, "Level 4 적용 근거는 case_id가 필요합니다")
                    if ev_level == 4 and isinstance(item.get("case_id"), str) and item["case_id"] in cases:
                        validation = cases[item["case_id"]].get("validation")
                        if not isinstance(validation, dict) or validation.get("status") == "not_run":
                            self.error(loc, "Level 4 적용에는 실행한 검증 결과가 필요합니다")
                    reviewed = record.get("last_reviewed")
                    if isinstance(reviewed, str) and isinstance(item.get("date"), str) and item["date"] > reviewed:
                        self.error(loc, "근거 날짜가 마지막 검토일보다 늦습니다")
            if level_valid and level > supported:
                self.error(loc, "검증 수준을 뒷받침하는 근거가 없습니다")
        for key, portfolio in portfolios.items():
            self.fields(portfolio, {"id", "is_example", "title", "case_ids", "document", "status", "publication_review"}, key)
            self.string(portfolio.get("title"), key + ".title")
            case_ids = self.refs(portfolio.get("case_ids"), cases, key + ".case_ids", True)
            self.document(portfolio.get("document"), key + ".document", example, "portfolio")
            self.enum(portfolio.get("status"), ("candidate", "ready", "published"), key + ".status")
            review = portfolio.get("publication_review")
            if review is not None:
                if self.fields(review, {"date", "notes"}, key + ".publication_review"):
                    self.date(review.get("date"), key + ".publication_review.date")
                    self.string(review.get("notes"), key + ".publication_review.notes")
            if portfolio.get("status") in ("ready", "published"):
                if review is None:
                    self.error(key, "공개 준비/게시 상태는 공개 점검 기록이 필요합니다")
                for case_id in case_ids:
                    case = cases.get(case_id, {})
                    validation = case.get("validation", {})
                    if case.get("public_safe") is not True or not isinstance(validation, dict) or validation.get("status") not in ("passed", "failed"):
                        self.error(key, "공개 가능한 사례와 실행된 검증 결과가 필요합니다")

    @staticmethod
    def valid_list(value):
        return value if isinstance(value, list) else []

    def links(self):
        for path in sorted(self.root.rglob("*.md")):
            if any(part.startswith(".") for part in path.relative_to(self.root).parts):
                continue
            where = str(path.relative_to(self.root))
            try:
                text = markdown_text(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as exc:
                self.error(where, f"Markdown 읽기 실패: {exc}")
                continue
            text = re.sub(r"(`+).*?\1", "", text)
            targets = re.findall(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", text)
            targets += re.findall(r"^\s{0,3}\[[^]]+\]:\s*(<[^>]+>|\S+)", text, re.M)
            for target in targets:
                target = target.strip("<>")
                try:
                    parsed = urlsplit(target)
                except ValueError:
                    self.error(where, f"유효하지 않은 URL: {target}")
                    continue
                if parsed.scheme in ("http", "https", "mailto"):
                    continue
                if parsed.scheme or parsed.netloc:
                    self.error(where, f"지원하지 않는 링크 형식: {target}")
                    continue
                relative = unquote(parsed.path)
                base = self.root if relative.startswith("/") else path.parent
                linked = self.path(relative.lstrip("/"), where, base, allow_parent=True) if relative else path
                if linked and parsed.fragment and linked.suffix == ".md":
                    if unquote(parsed.fragment) not in anchors(linked.read_text(encoding="utf-8")):
                        self.error(where, f"문서 앵커 없음: {target}")

    def run(self):
        for relative in REQUIRED:
            if not (self.root / relative).is_file():
                self.error(relative, "필수 파일 없음")
        concepts = self.catalog()
        self.datasets(concepts)
        self.datasets(concepts, example=True)
        for folder in ("knowledge", "examples/knowledge"):
            for path in (self.root / folder).glob("*.md"):
                if path.name != "README.md" and path.stem not in concepts:
                    self.error(str(path.relative_to(self.root)), "지식 문서 파일명은 유효한 개념 ID여야 합니다")
        self.links()
        return self.errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="검사할 Atlas 저장소 경로")
    args = parser.parse_args()
    errors = Validator(args.root).run()
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)
    if errors:
        print(f"검증 실패: {len(errors)}개 오류", file=sys.stderr)
        return 1
    print("검증 통과: 필수 파일, 메타데이터, 선수 DAG, 실제/예시 참조, 평가 근거, 내부 링크")
    return 0


if __name__ == "__main__":
    sys.exit(main())
