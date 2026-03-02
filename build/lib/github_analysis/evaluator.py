from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from statistics import median
from typing import Any

from requests import HTTPError

from .config import Rubric
from .github_client import GitHubClient
from .models import EvaluationReport, ScoreSection
from .utils import clamp, parse_iso8601, ratio, utc_now_iso


class RepositoryEvaluator:
    def __init__(self, client: GitHubClient, rubric: Rubric) -> None:
        self.client = client
        self.rubric = rubric

    def evaluate(self, owner: str, repo: str) -> EvaluationReport:
        warnings: list[str] = []
        repo_info = self.client.get_repo(owner, repo)
        default_branch = repo_info.get("default_branch", "main")

        try:
            readme_text = self.client.get_readme(owner, repo)
        except HTTPError:
            readme_text = ""
            warnings.append("README를 찾지 못했습니다.")

        try:
            tree = self.client.get_tree(owner, repo, default_branch)
        except HTTPError:
            tree = []
            warnings.append("파일 트리를 불러오지 못했습니다.")

        commits_30 = self._safe_call(lambda: self.client.get_commits(owner, repo, days=30), warnings, "30일 커밋")
        commits_90 = self._safe_call(lambda: self.client.get_commits(owner, repo, days=90), warnings, "90일 커밋")
        pulls_closed = self._safe_call(lambda: self.client.get_pulls(owner, repo, state="closed"), warnings, "PR")
        issues_open = self._safe_call(lambda: self.client.get_issues(owner, repo, state="open"), warnings, "Open issues")
        issues_closed = self._safe_call(lambda: self.client.get_issues(owner, repo, state="closed"), warnings, "Closed issues")
        contributors = self._safe_call(lambda: self.client.get_contributors(owner, repo), warnings, "Contributors")
        languages = self._safe_call(lambda: self.client.get_languages(owner, repo), warnings, "Languages")

        paths = [entry.get("path", "") for entry in tree]
        code_score, code_evidence = self._score_code_quality(paths, readme_text, commits_90)
        activity_score, activity_evidence = self._score_activity(repo_info, commits_30, commits_90, contributors)
        docs_score, docs_evidence = self._score_documentation(repo_info, readme_text, paths)
        collab_score, collab_evidence = self._score_collaboration(pulls_closed, issues_open, issues_closed, paths)

        sections = [
            ScoreSection(
                name="code_quality",
                score=round(code_score, 2),
                max_score=self.rubric.sections["code_quality"],
                summary="코드 안정성/유지보수성/보안 신호를 기반으로 평가",
                evidence=code_evidence,
            ),
            ScoreSection(
                name="activity",
                score=round(activity_score, 2),
                max_score=self.rubric.sections["activity"],
                summary="최근 커밋/기여자/업데이트 신선도 기반 평가",
                evidence=activity_evidence,
            ),
            ScoreSection(
                name="documentation",
                score=round(docs_score, 2),
                max_score=self.rubric.sections["documentation"],
                summary="README/라이선스/문서 자산의 완성도 평가",
                evidence=docs_evidence,
            ),
            ScoreSection(
                name="collaboration",
                score=round(collab_score, 2),
                max_score=self.rubric.sections["collaboration"],
                summary="PR/Issue 흐름 및 협업 템플릿 성숙도 평가",
                evidence=collab_evidence,
            ),
        ]

        total_score = round(sum(section.score for section in sections), 2)
        max_score = self.rubric.max_score
        grade = self._grade(total_score, max_score)
        pass_fail = "PASS" if total_score >= self.rubric.pass_score else "FAIL"

        checklist = self._build_checklist(sections, repo_info, paths)
        raw_metrics = {
            "stars": repo_info.get("stargazers_count", 0),
            "forks": repo_info.get("forks_count", 0),
            "open_issues": repo_info.get("open_issues_count", 0),
            "watchers": repo_info.get("subscribers_count", 0),
            "languages": languages,
            "contributors": len(contributors),
            "commits_30d": len(commits_30),
            "commits_90d": len(commits_90),
            "prs_closed_sample": len(pulls_closed),
            "issues_open_sample": len(issues_open),
            "issues_closed_sample": len(issues_closed),
        }

        return EvaluationReport(
            repo=f"{owner}/{repo}",
            generated_at=utc_now_iso(),
            total_score=total_score,
            max_score=max_score,
            grade=grade,
            pass_fail=pass_fail,
            sections=sections,
            checklist=checklist,
            raw_metrics=raw_metrics,
            warnings=warnings,
        )

    def _safe_call(self, fn: Any, warnings: list[str], name: str) -> list[dict[str, Any]] | dict[str, int]:
        try:
            return fn()
        except HTTPError:
            warnings.append(f"{name} 데이터를 가져오지 못했습니다.")
            return []

    def _score_code_quality(
        self,
        paths: list[str],
        readme_text: str,
        commits_90: list[dict[str, Any]],
    ) -> tuple[float, dict[str, Any]]:
        has_ci = any(p.startswith(".github/workflows/") for p in paths)
        has_tests = any(
            p.startswith("test/")
            or p.startswith("tests/")
            or p.endswith("_test.py")
            or p.endswith(".spec.ts")
            or p.endswith(".test.ts")
            for p in paths
        )
        has_security = any(p.upper() == "SECURITY.MD" for p in paths)
        has_dependabot = any(p == ".github/dependabot.yml" or p == ".github/dependabot.yaml" for p in paths)
        coverage_signal = "coverage" in readme_text.lower() or "codecov" in readme_text.lower()
        has_src_layout = any(p.startswith("src/") for p in paths)
        has_contributing = any(p.upper() == "CONTRIBUTING.MD" for p in paths)
        readme_struct = all(token in readme_text.lower() for token in ["install", "usage"])

        messages = [
            ((commit.get("commit") or {}).get("message") or "").strip()
            for commit in commits_90
        ]
        informative_messages = [m for m in messages if len(m) >= 12 and "update" not in m.lower()]
        message_quality = ratio(len(informative_messages), len(messages)) if messages else 0.0

        reliability = 0.45 * float(has_ci) + 0.35 * float(has_tests) + 0.20 * message_quality
        maintainability = 0.45 * float(has_src_layout) + 0.35 * float(readme_struct) + 0.20 * float(has_contributing)
        security = 0.60 * float(has_security) + 0.40 * float(has_dependabot)
        coverage = 1.0 if coverage_signal else (0.5 if has_tests else 0.0)

        normalized = clamp((reliability + maintainability + security + coverage) / 4, 0.0, 1.0)
        score = normalized * self.rubric.sections["code_quality"]
        evidence = {
            "has_ci": has_ci,
            "has_tests": has_tests,
            "has_security_policy": has_security,
            "has_dependabot": has_dependabot,
            "coverage_signal": coverage_signal,
            "message_quality_ratio": round(message_quality, 3),
            "reliability_subscore": round(reliability, 3),
            "maintainability_subscore": round(maintainability, 3),
            "security_subscore": round(security, 3),
            "coverage_subscore": round(coverage, 3),
        }
        return score, evidence

    def _score_activity(
        self,
        repo_info: dict[str, Any],
        commits_30: list[dict[str, Any]],
        commits_90: list[dict[str, Any]],
        contributors: list[dict[str, Any]],
    ) -> tuple[float, dict[str, Any]]:
        commit_count = len(commits_30)
        commit_score = clamp(commit_count / 20, 0.0, 1.0)

        recent_authors = {
            (((commit.get("commit") or {}).get("author") or {}).get("email") or "").lower()
            for commit in commits_90
        }
        recent_authors = {author for author in recent_authors if author}
        contributor_score = clamp(len(recent_authors) / 8, 0.0, 1.0)

        pushed_at = parse_iso8601(repo_info.get("pushed_at"))
        freshness = 0.0
        if pushed_at:
            age_days = (datetime.now(UTC) - pushed_at).days
            if age_days <= 7:
                freshness = 1.0
            elif age_days <= 30:
                freshness = 0.7
            elif age_days <= 90:
                freshness = 0.4
            else:
                freshness = 0.1

        normalized = clamp(0.45 * commit_score + 0.25 * contributor_score + 0.30 * freshness, 0.0, 1.0)
        score = normalized * self.rubric.sections["activity"]
        evidence = {
            "commits_30d": commit_count,
            "unique_authors_90d": len(recent_authors),
            "total_contributors": len(contributors),
            "freshness_score": round(freshness, 3),
        }
        return score, evidence

    def _score_documentation(
        self,
        repo_info: dict[str, Any],
        readme_text: str,
        paths: list[str],
    ) -> tuple[float, dict[str, Any]]:
        has_readme = bool(readme_text.strip())
        headings = ["install", "usage", "contribut", "license"]
        heading_score = ratio(sum(1 for h in headings if h in readme_text.lower()), len(headings))
        readme_length_score = clamp(len(readme_text) / 2000, 0.0, 1.0)
        has_docs_dir = any(p.startswith("docs/") for p in paths)
        has_license = repo_info.get("license") is not None
        has_api_docs = any("openapi" in p.lower() or "swagger" in p.lower() for p in paths) or "api" in readme_text.lower()

        normalized = clamp(
            0.30 * float(has_readme)
            + 0.25 * heading_score
            + 0.15 * readme_length_score
            + 0.15 * float(has_license)
            + 0.10 * float(has_docs_dir)
            + 0.05 * float(has_api_docs),
            0.0,
            1.0,
        )
        score = normalized * self.rubric.sections["documentation"]
        evidence = {
            "has_readme": has_readme,
            "readme_heading_coverage": round(heading_score, 3),
            "readme_length": len(readme_text),
            "has_docs_dir": has_docs_dir,
            "has_license": has_license,
            "has_api_docs_signal": has_api_docs,
        }
        return score, evidence

    def _score_collaboration(
        self,
        pulls_closed: list[dict[str, Any]],
        issues_open: list[dict[str, Any]],
        issues_closed: list[dict[str, Any]],
        paths: list[str],
    ) -> tuple[float, dict[str, Any]]:
        merged = [pr for pr in pulls_closed if pr.get("merged_at")]
        merged_ratio = ratio(len(merged), len(pulls_closed))

        merge_hours: list[float] = []
        for pr in merged:
            created_at = parse_iso8601(pr.get("created_at"))
            merged_at = parse_iso8601(pr.get("merged_at"))
            if created_at and merged_at and merged_at >= created_at:
                merge_hours.append((merged_at - created_at).total_seconds() / 3600)

        if merge_hours:
            med = median(merge_hours)
            if med <= 24:
                merge_speed_score = 1.0
            elif med <= 72:
                merge_speed_score = 0.7
            elif med <= 168:
                merge_speed_score = 0.4
            else:
                merge_speed_score = 0.1
        else:
            med = None
            merge_speed_score = 0.0

        issue_resolution = ratio(len(issues_closed), len(issues_closed) + len(issues_open))
        has_issue_template = any(p.startswith(".github/ISSUE_TEMPLATE/") for p in paths)
        has_pr_template = any(p.endswith("pull_request_template.md") for p in (path.lower() for path in paths))
        has_codeowners = any(p.upper() == ".GITHUB/CODEOWNERS" or p.upper() == "CODEOWNERS" for p in paths)

        normalized = clamp(
            0.35 * merged_ratio
            + 0.25 * merge_speed_score
            + 0.20 * issue_resolution
            + 0.10 * float(has_issue_template)
            + 0.05 * float(has_pr_template)
            + 0.05 * float(has_codeowners),
            0.0,
            1.0,
        )
        score = normalized * self.rubric.sections["collaboration"]
        evidence = {
            "closed_pr_sample": len(pulls_closed),
            "merged_pr_ratio": round(merged_ratio, 3),
            "median_merge_hours": round(med, 2) if med is not None else None,
            "open_issue_sample": len(issues_open),
            "closed_issue_sample": len(issues_closed),
            "issue_resolution_ratio": round(issue_resolution, 3),
            "has_issue_template": has_issue_template,
            "has_pr_template": has_pr_template,
            "has_codeowners": has_codeowners,
        }
        return score, evidence

    def _build_checklist(
        self,
        sections: list[ScoreSection],
        repo_info: dict[str, Any],
        paths: list[str],
    ) -> dict[str, list[str]]:
        section_map = {s.name: s for s in sections}
        phase1 = [
            f"README 존재: {'예' if any(p.upper() == 'README.MD' for p in paths) else '아니오'}",
            f"기본 브랜치: {repo_info.get('default_branch', 'N/A')}",
            f"최근 푸시: {repo_info.get('pushed_at', 'N/A')}",
            f"기술 스택 언어 수: {repo_info.get('language') or 'N/A'} (대표 언어)",
        ]
        phase2 = [
            f"코드 품질 점수: {section_map['code_quality'].score}/{section_map['code_quality'].max_score}",
            f"문서화 점수: {section_map['documentation'].score}/{section_map['documentation'].max_score}",
            f"테스트 디렉터리 존재: {'예' if any(p.startswith('tests/') or p.startswith('test/') for p in paths) else '아니오'}",
        ]
        phase3 = [
            f"협업 점수: {section_map['collaboration'].score}/{section_map['collaboration'].max_score}",
            f"활동 점수: {section_map['activity'].score}/{section_map['activity'].max_score}",
            f"워크플로우 파일 수: {sum(1 for p in paths if p.startswith('.github/workflows/'))}",
        ]
        return {"phase_1": phase1, "phase_2": phase2, "phase_3": phase3}

    def _grade(self, score: float, max_score: float) -> str:
        pct = 100 * ratio(score, max_score)
        if pct >= 90:
            return "A"
        if pct >= 80:
            return "B"
        if pct >= 70:
            return "C"
        if pct >= 60:
            return "D"
        return "F"

    @staticmethod
    def report_to_dict(report: EvaluationReport) -> dict[str, Any]:
        payload = asdict(report)
        payload["sections"] = [asdict(section) for section in report.sections]
        return payload

