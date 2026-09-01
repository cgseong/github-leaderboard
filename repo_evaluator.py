#!/usr/bin/env python3
"""
GitHub 레포지토리 평가 프로그램 (GitHub Repository Evaluator)

지정된 GitHub 레포지토리를 탐색하고 다양한 기준으로 평가하는 프로그램입니다.

사용법:
    python repo_evaluator.py <owner/repo> [--token YOUR_GITHUB_TOKEN] [--json]

예시:
    python repo_evaluator.py facebook/react
    python repo_evaluator.py tensorflow/tensorflow --token ghp_xxxx
    python repo_evaluator.py rust-lang/rust --json
"""

import argparse
import json
import math
import os
import sys
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    import requests
except ImportError:
    print("❌ requests 라이브러리가 필요합니다. 설치해주세요:")
    print("   pip install requests")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# AI 활용도 평가 모듈 import
try:
    from ai_utilization_evaluator import AIUtilizationEvaluator
    HAS_AI_EVAL = True
except ImportError:
    HAS_AI_EVAL = False

# ─── GitHub API ──────────────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"


def gh_get(endpoint: str, token: Optional[str] = None) -> Optional[dict | list]:
    """GitHub API GET 요청"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        resp = requests.get(f"{GITHUB_API}{endpoint}", headers=headers, timeout=15)
        if resp.status_code == 404:
            return None
        if resp.status_code == 403:
            print("⚠️  GitHub API rate limit에 도달했습니다. --token 옵션을 사용해주세요.")
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        print(f"⚠️  API 요청 실패: {e}")
        return None


def gh_get_file_content(owner: str, repo: str, path: str, token: Optional[str] = None) -> Optional[str]:
    """GitHub API로 파일 내용 가져오기 (base64 디코딩)"""
    import base64
    endpoint = f"/repos/{owner}/{repo}/contents/{path}"
    data = gh_get(endpoint, token)
    if data and "content" in data:
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return None
    return None


# ─── 데이터 모델 ──────────────────────────────────────────────────────────────

@dataclass
class EvalResult:
    """하나의 평가 항목 결과"""
    name: str
    score: float          # 0~10
    max_score: float      # 10
    details: str
    sub_items: list = field(default_factory=list)


@dataclass
class CategoryResult:
    """카테고리별 평가 결과"""
    name: str
    weight: float
    score: float = 0.0
    max_score: float = 10.0
    items: list = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


# ─── 평가 엔진 ──────────────────────────────────────────────────────────────

class RepoEvaluator:
    """GitHub 레포지토리 평가 엔진"""

    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.repo_data: Optional[dict] = None
        self.categories: list[CategoryResult] = []

    # ── 데이터 수집 ──────────────────────────────────────────────────────

    def get_file_content(self, path: str) -> Optional[str]:
        """파일 내용 가져오기"""
        return gh_get_file_content(self.owner, self.repo, path, self.token)

    def fetch_repo_info(self) -> bool:
        """레포지토리 기본 정보 수집"""
        self.repo_data = gh_get(f"/repos/{self.owner}/{self.repo}", self.token)
        return self.repo_data is not None

    def fetch_commits(self, since_days: int = 90) -> list:
        """최근 커밋 목록"""
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/commits?since={since}&per_page=100",
            self.token,
        )
        return result if isinstance(result, list) else []

    def fetch_issues(self, since_days: int = 90) -> list:
        """최근 이슈 목록"""
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/issues?since={since}&state=all&per_page=100",
            self.token,
        )
        return result if isinstance(result, list) else []

    def fetch_pulls(self, since_days: int = 90) -> list:
        """최근 PR 목록"""
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/pulls?state=all&sort=updated&direction=desc&per_page=100",
            self.token,
        )
        return result if isinstance(result, list) else []

    def fetch_contributors(self) -> list:
        """기여자 목록"""
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/contributors?per_page=100",
            self.token,
        )
        return result if isinstance(result, list) else []

    def fetch_languages(self) -> dict:
        """사용 언어"""
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/languages",
            self.token,
        )
        return result if isinstance(result, dict) else {}

    def fetch_tree(self, ref: str = "HEAD", recursive: bool = True) -> list:
        """파일 트리 조회"""
        params = "?recursive=1" if recursive else ""
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/git/trees/{ref}{params}",
            self.token,
        )
        if result and "tree" in result:
            return result["tree"]
        return []

    def fetch_releases(self) -> list:
        """릴리스 목록"""
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/releases?per_page=100",
            self.token,
        )
        return result if isinstance(result, list) else []

    def fetch_workflows(self) -> list:
        """GitHub Actions 워크플로우"""
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/actions/workflows?per_page=100",
            self.token,
        )
        if result and "workflows" in result:
            return result["workflows"]
        return []

    def fetch_branches(self) -> list:
        """브랜치 목록"""
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/branches?per_page=100",
            self.token,
        )
        return result if isinstance(result, list) else []

    def fetch_dependabot_alerts(self) -> list:
        """Dependabot 알림"""
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/dependabot/alerts?per_page=20",
            self.token,
        )
        return result if isinstance(result, list) else []

    def fetch_security_advisories(self) -> list:
        """보안 권고문"""
        result = gh_get(
            f"/repos/{self.owner}/{self.repo}/security-advisories?per_page=20",
            self.token,
        )
        return result if isinstance(result, list) else []

    # ── 평가 메서드 ──────────────────────────────────────────────────────

    def _score_popularity(self, r: dict) -> EvalResult:
        """⭐ 인기도 평가"""
        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        watchers = r.get("watchers_count", 0)

        # Log scale for stars
        star_score = min(10, math.log10(stars + 1) * 1.67)  # 1000 stars ≈ 5.0
        fork_score = min(10, math.log10(forks + 1) * 2.0)   # 100 forks ≈ 4.0
        watcher_score = min(10, math.log10(watchers + 1) * 2.5)

        score = star_score * 0.5 + fork_score * 0.3 + watcher_score * 0.2

        return EvalResult(
            name="인기도 (Popularity)",
            score=round(score, 1),
            max_score=10,
            details=f"⭐ {stars:,} stars · 🍴 {forks:,} forks · 👀 {watchers:,} watchers",
            sub_items=[
                f"Stars: {stars:,} ({star_score:.1f}/10)",
                f"Forks: {forks:,} ({fork_score:.1f}/10)",
                f"Watchers: {watchers:,} ({watcher_score:.1f}/10)",
            ],
        )

    def _score_license(self, r: dict) -> EvalResult:
        """📜 라이선스 평가"""
        license_info = r.get("license")
        if license_info and license_info.get("spdx_id") and license_info["spdx_id"] != "NOASSERTION":
            score = 10.0
            details = f"✅ {license_info['spdx_id']} ({license_info.get('name', '')})"
        elif license_info and license_info.get("spdx_id") == "NOASSERTION":
            score = 3.0
            details = "⚠️ 라이선스 감지되었으나 SPDX 미인증"
        else:
            score = 0.0
            details = "❌ 라이선스 없음 (오픈소스 프로젝트에 필수)"

        return EvalResult(
            name="라이선스 (License)",
            score=score,
            max_score=10,
            details=details,
        )

    def _score_description(self, r: dict) -> EvalResult:
        """📝 설명/README 평가"""
        desc = r.get("description") or ""
        homepage = r.get("homepage") or ""
        score = 0.0

        if len(desc) > 10:
            score += 4.0
        elif len(desc) > 0:
            score += 2.0

        if homepage:
            score += 2.0

        # README 존재 여부는 파일 트리에서 확인
        score += 0  # 별도 평가에서 처리

        details_parts = []
        if desc:
            details_parts.append(f"설명: \"{desc[:80]}{'...' if len(desc) > 80 else ''}\"")
        else:
            details_parts.append("설명: 없음 ❌")
        if homepage:
            details_parts.append(f"홈페이지: {homepage}")

        return EvalResult(
            name="프로젝트 설명 (Description)",
            score=min(10, score),
            max_score=10,
            details=" · ".join(details_parts) if details_parts else "설명 없음",
        )

    def _score_activity(self, commits: list, issues: list, pulls: list) -> EvalResult:
        """🔥 개발 활동성 평가"""
        # Recent activity window
        now = datetime.now(timezone.utc)
        recent_30 = now - timedelta(days=30)
        recent_90 = now - timedelta(days=90)

        commits_30 = sum(
            1 for c in commits
            if c.get("commit", {}).get("author", {}).get("date", "")
            and datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00")) > recent_30
        )
        commits_90 = len(commits)

        issues_opened = len([i for i in issues if not i.get("pull_request")])
        issues_closed = sum(1 for i in issues if not i.get("pull_request") and i.get("state") == "closed")
        pr_opened = len([i for i in pulls])
        pr_merged = sum(1 for p in pulls if p.get("merged_at"))

        # Scoring
        commit_score = min(10, commits_30 * 0.5)  # 20 commits/month = 10
        issue_score = min(10, issues_opened * 0.3 + issues_closed * 0.5)
        pr_score = min(10, pr_opened * 0.3 + pr_merged * 0.5)

        score = commit_score * 0.5 + issue_score * 0.2 + pr_score * 0.3

        details = (
            f"최근 30일 커밋: {commits_30} · "
            f"90일 커밋: {commits_90} · "
            f"이슈: {issues_opened}개 열림/{issues_closed}개 닫힘 · "
            f"PR: {pr_opened}개 열림/{pr_merged}개 병합"
        )

        return EvalResult(
            name="개발 활동성 (Activity)",
            score=round(score, 1),
            max_score=10,
            details=details,
            sub_items=[
                f"커밋 활동: {commits_30}개/30일 ({commit_score:.1f}/10)",
                f"이슈 관리: {issues_opened}개 열림, {issues_closed}개 닫힘 ({issue_score:.1f}/10)",
                f"PR 관리: {pr_opened}개 열림, {pr_merged}개 병합 ({pr_score:.1f}/10)",
            ],
        )

    def _score_contributors(self, contributors: list) -> EvalResult:
        """👥 커뮤니티/기여자 평가"""
        total = len(contributors)
        # Categorize by contribution count
        core = sum(1 for c in contributors if c.get("contributions", 0) > 50)
        active = sum(1 for c in contributors if 5 < c.get("contributions", 0) <= 50)
        casual = sum(1 for c in contributors if 0 < c.get("contributions", 0) <= 5)

        contributor_score = min(10, math.log10(total + 1) * 2.0)
        diversity_score = min(10, (core * 2 + active * 1.5 + casual * 1))

        # Bonus for having many contributors
        if total > 100:
            contributor_score = min(10, contributor_score + 1)
        if total > 1000:
            contributor_score = min(10, contributor_score + 1)

        score = contributor_score * 0.6 + diversity_score * 0.4

        details = (
            f"총 {total}명 · "
            f"핵심 기여자: {core}명 · "
            f"활발한 기여자: {active}명 · "
            f"일반 기여자: {casual}명"
        )

        return EvalResult(
            name="커뮤니티 (Community)",
            score=round(score, 1),
            max_score=10,
            details=details,
            sub_items=[
                f"총 기여자: {total}명",
                f"핵심(50+ 커밋): {core}명",
                f"활발(5~50 커밋): {active}명",
                f"일반(1~5 커밋): {casual}명",
            ],
        )

    def _score_documentation(self, tree: list, r: dict) -> EvalResult:
        """📚 문서화 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        file_names = [p.split("/")[-1].lower() for p in file_paths]
        dir_names = set()
        for p in file_paths:
            parts = p.split("/")
            if len(parts) > 1:
                dir_names.add(parts[0].lower())

        score = 0.0
        details_items = []

        # README
        readme = any(f.startswith("readme") for f in file_names)
        if readme:
            score += 2.5
            details_items.append("✅ README.md")
        else:
            details_items.append("❌ README.md 없음")

        # Contributing guide
        contributing = any(f in ("contributing.md", "contributing.rst", "contributing.txt", "contribute.md") for f in file_names)
        if contributing:
            score += 1.5
            details_items.append("✅ CONTRIBUTING.md")
        else:
            details_items.append("❌ CONTRIBUTING.md 없음")

        # Code of Conduct
        coc = any("code_of_conduct" in f for f in file_names)
        if coc:
            score += 1.0
            details_items.append("✅ CODE_OF_CONDUCT")
        else:
            details_items.append("❌ CODE_OF_CONDUCT 없음")

        # Changelog
        changelog = any(f in ("changelog.md", "changelog.rst", "changelog.txt", "changes.md", "history.md", "news.md") for f in file_names)
        if changelog:
            score += 1.0
            details_items.append("✅ CHANGELOG")
        else:
            details_items.append("❌ CHANGELOG 없음")

        # Docs directory
        docs = any(d in ("docs", "doc", "documentation", "wiki") for d in dir_names)
        if docs:
            score += 2.0
            details_items.append("✅ docs/ 디렉토리")
        else:
            details_items.append("❌ docs/ 디렉토리 없음")

        # Examples
        examples = any(d in ("examples", "example", "samples", "demo") for d in dir_names)
        if examples:
            score += 1.0
            details_items.append("✅ examples/ 디렉토리")
        else:
            details_items.append("❌ examples/ 디렉토리 없음")

        # GitHub templates
        has_issue_template = any("issue_template" in p.lower() or p.startswith(".github/ISSUE_TEMPLATE") for p in file_paths)
        has_pr_template = any("pull_request_template" in p.lower() or p.startswith(".github/PULL_REQUEST_TEMPLATE") for p in file_paths)
        if has_issue_template:
            score += 0.5
        if has_pr_template:
            score += 0.5

        return EvalResult(
            name="문서화 (Documentation)",
            score=min(10, round(score, 1)),
            max_score=10,
            details=" · ".join(details_items),
            sub_items=details_items,
        )

    def _score_code_quality(self, tree: list, workflows: list) -> EvalResult:
        """🔍 코드 품질 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        file_names_lower = [p.split("/")[-1].lower() for p in file_paths]
        dir_names = set()
        for p in file_paths:
            parts = p.split("/")
            if len(parts) > 1:
                dir_names.add(parts[0].lower())

        score = 0.0
        details = []

        # CI/CD
        has_ci = len(workflows) > 0
        if has_ci:
            score += 2.5
            details.append(f"✅ CI/CD ({len(workflows)}개 워크플로우)")
        else:
            # Check for .travis.yml, .circleci, etc.
            if any("travis" in f for f in file_names_lower):
                score += 1.5
                details.append("⚠️ Travis CI (레거시)")
            elif any(".circleci" in d for d in dir_names):
                score += 1.5
                details.append("⚠️ CircleCI")
            else:
                details.append("❌ CI/CD 없음")

        # Linting/Formatting
        linter_files = ["eslint", ".eslintrc", ".prettierrc", ".flake8", "pylint",
                       ".rubocop", "golangci", ".clang-format", "biome.json", "biome.jsonc",
                       "deno.json", "deno.jsonc", ".ruff", "ruff.toml", ".editorconfig"]
        linting = any(lf in fn for fn in file_names_lower for lf in linter_files)
        if linting:
            score += 1.5
            details.append("✅ 린터/포맷터 설정")
        else:
            details.append("❌ 린터/포맷터 설정 없음")

        # Type checking
        type_check = any(fn in ("tsconfig.json", "mypy.ini", "mypy.cfg", "py.typed",
                                ".mypy.ini", "pyrightconfig.json", "setup.cfg") for fn in file_names_lower)
        if type_check:
            score += 1.0
            details.append("✅ 타입 체크 설정")

        # Test files
        test_patterns = ["test", "spec", "__tests__", "tests"]
        has_tests = any(
            any(tp in f for tp in test_patterns)
            for f in file_names_lower
        )
        test_dirs = any(any(tp in d for tp in test_patterns) for d in dir_names)
        if has_tests or test_dirs:
            score += 2.0
            details.append("✅ 테스트 존재")
        else:
            details.append("❌ 테스트 없음")

        # .gitignore
        gitignore = ".gitignore" in file_names_lower
        if gitignore:
            score += 0.5
            details.append("✅ .gitignore")

        # Pre-commit hooks
        precommit = any(".pre-commit" in p or "pre-commit" in f for f in file_names_lower for p in [f])
        if precommit:
            score += 0.5
            details.append("✅ pre-commit hooks")

        # Security policies
        security = any("security" in f for f in file_names_lower)
        if security:
            score += 1.0
            details.append("✅ Security Policy")

        # Docker
        docker = any(f in ("dockerfile", "docker-compose.yml", "docker-compose.yaml") for f in file_names_lower)
        if docker:
            score += 0.5
            details.append("✅ Docker 설정")

        return EvalResult(
            name="코드 품질 (Code Quality)",
            score=min(10, round(score, 1)),
            max_score=10,
            details=" · ".join(details),
            sub_items=details,
        )

    def _score_release_management(self, releases: list) -> EvalResult:
        """📦 릴리스 관리 평가"""
        score = 0.0
        details = []

        if releases:
            score += 3.0
            details.append(f"릴리스 {len(releases)}개")

            # Check for recent release
            now = datetime.now(timezone.utc)
            for rel in releases[:5]:
                pub_date = rel.get("published_at", "")
                if pub_date:
                    try:
                        dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                        days_ago = (now - dt).days
                        if days_ago < 30:
                            score += 2.0
                            details.append(f"최근 릴리스: {days_ago}일 전")
                            break
                        elif days_ago < 90:
                            score += 1.0
                            details.append(f"최근 릴리스: {days_ago}일 전")
                            break
                    except ValueError:
                        pass

            # Semver check
            import re
            semver_pattern = re.compile(r"^\d+\.\d+\.\d+")
            semver_count = sum(
                1 for r in releases
                if r.get("tag_name") and semver_pattern.match(r["tag_name"])
            )
            if semver_count > 0:
                score += 2.0
                details.append(f"Semver 태그: {semver_count}개")

            # Changelog in release
            with_body = sum(1 for r in releases if r.get("body"))
            if with_body > len(releases) * 0.5:
                score += 1.0
                details.append("릴리스 노트 포함")

            # Pre-release
            pre_releases = sum(1 for r in releases if r.get("prerelease"))
            if pre_releases > 0:
                score += 0.5
                details.append(f"Pre-release: {pre_releases}개")

        else:
            details.append("릴리스 없음 ❌")

        return EvalResult(
            name="릴리스 관리 (Release Management)",
            score=min(10, round(score, 1)),
            max_score=10,
            details=" · ".join(details) if details else "릴리스 정보 없음",
            sub_items=details,
        )

    def _score_dependencies(self, tree: list) -> EvalResult:
        """📦 의존성 관리 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        # Use set for deduplication
        file_names_lower = set(f.split("/")[-1].lower() for f in file_paths)

        score = 0.0
        details = []

        # Lock files
        lock_files = {
            "package-lock.json": "npm",
            "yarn.lock": "yarn",
            "pnpm-lock.yaml": "pnpm",
            "bun.lockb": "bun",
            "poetry.lock": "Poetry",
            "Pipfile.lock": "Pipenv",
            "go.sum": "Go",
            "Cargo.lock": "Cargo",
            "Gemfile.lock": "Bundler",
            "composer.lock": "Composer",
            "pnpm-workspace.yaml": "pnpm workspace",
        }

        found_locks = [(f, lock_files[f]) for f in file_names_lower if f in lock_files]
        if found_locks:
            score += 3.0
            details.append(f"잠금 파일: {', '.join(name for _, name in found_locks)}")
        else:
            details.append("잠금 파일 없음 ⚠️")

        # Package files
        pkg_files = {
            "package.json": "npm",
            "pyproject.toml": "Python",
            "setup.py": "Python",
            "setup.cfg": "Python",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "build.gradle": "Java",
            "build.gradle.kts": "Java",
            "pom.xml": "Java",
            "Gemfile": "Ruby",
            "composer.json": "PHP",
        }

        found_pkgs = [(f, pkg_files[f]) for f in file_names_lower if f in pkg_files]
        if found_pkgs:
            score += 2.0
            details.append(f"패키지 파일: {', '.join(name for _, name in found_pkgs)}")

        # Dependabot / Renovate
        has_dependabot = any("dependabot" in p.lower() for p in file_paths)
        has_renovate = any("renovate" in p.lower() for p in file_paths)
        if has_dependabot:
            score += 2.5
            details.append("✅ Dependabot")
        elif has_renovate:
            score += 2.5
            details.append("✅ Renovate")
        else:
            details.append("❌ 의존성 자동 업데이트 없음")

        # Multiple language ecosystems
        if len(found_pkgs) > 1:
            score += 1.0
            details.append(f"다중 에코시스템: {len(found_pkgs)}개")

        # Workspace / monorepo detection
        workspace_files = ["pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json"]
        if any(wf in file_names_lower for wf in workspace_files):
            score += 1.5
            details.append("✅ 모노레포/워크스페이스")

        return EvalResult(
            name="의존성 관리 (Dependencies)",
            score=min(10, round(score, 1)),
            max_score=10,
            details=" · ".join(details) if details else "의존성 정보 없음",
            sub_items=details,
        )

    def _score_ecosystem(self, r: dict, languages: dict) -> EvalResult:
        """🌍 에코시스템/기술 스택 평가"""
        primary_lang = r.get("language") or "Unknown"
        total_bytes = sum(languages.values()) if languages else 1

        lang_pct = []
        for lang, bytes_val in sorted(languages.items(), key=lambda x: -x[1])[:5]:
            pct = (bytes_val / total_bytes) * 100
            lang_pct.append(f"{lang}: {pct:.1f}%")

        # Topic tags
        topics = r.get("topics", [])

        score = 0.0
        details = []

        # Primary language
        score += 3.0
        details.append(f"주 언어: {primary_lang}")

        # Language diversity
        if len(languages) > 3:
            score += 1.0
            details.append(f"사용 언어: {len(languages)}개")

        # Topics
        if topics:
            score += min(3.0, len(topics) * 0.5)
            details.append(f"태그: {', '.join(topics[:5])}{'...' if len(topics) > 5 else ''}")

        # Homepage
        if r.get("homepage"):
            score += 1.0

        return EvalResult(
            name="에코시스템 (Ecosystem)",
            score=min(10, round(score, 1)),
            max_score=10,
            details=" · ".join(details),
            sub_items=details + lang_pct,
        )

    def _score_safety(self, r: dict, tree: list) -> EvalResult:
        """🛡️ 안전성 평가"""
        score = 0.0
        details = []

        # Fork status (original vs fork)
        if r.get("fork"):
            score += 0.0
            details.append("포크된 레포지토리 ⚠️")
        else:
            score += 2.0
            details.append("원본 레포지토리 ✅")

        # Archived
        if r.get("archived"):
            score -= 3.0
            details.append("보관됨 (Archived) ⚠️")
        else:
            score += 2.0

        # Template repo
        if r.get("is_template"):
            score += 1.0
            details.append("템플릿 레포지토리")

        # Default branch
        default_branch = r.get("default_branch", "")
        if default_branch in ("main", "master"):
            score += 1.0

        # Security policy
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        has_security_policy = any("security" in p.lower() for p in file_paths)
        if has_security_policy:
            score += 2.0
            details.append("✅ 보안 정책")

        # Issue/PR templates
        has_templates = any(".github" in p for p in file_paths)
        if has_templates:
            score += 1.0

        # Branch protection (can't fully check without admin access)
        score += 1.0  # Base score

        return EvalResult(
            name="안전성 (Safety)",
            score=max(0, min(10, round(score, 1))),
            max_score=10,
            details=" · ".join(details) if details else "안전성 정보 없음",
            sub_items=details,
        )

    # ── 전체 평가 실행 ──────────────────────────────────────────────────

    def evaluate(self) -> dict:
        """전체 평가를 수행하고 결과를 반환"""
        r = self.repo_data
        if not r:
            return {"error": "레포지토리 정보를 가져올 수 없습니다."}

        # Collect data
        commits = self.fetch_commits()
        issues = self.fetch_issues()
        pulls = self.fetch_pulls()
        contributors = self.fetch_contributors()
        languages = self.fetch_languages()
        tree = self.fetch_tree()
        releases = self.fetch_releases()
        workflows = self.fetch_workflows()

        # Run evaluations
        categories = []

        # 1. 인기도
        cat_pop = CategoryResult(name="⭐ 인기도", weight=0.15)
        cat_pop.items.append(self._score_popularity(r))
        categories.append(cat_pop)

        # 2. 라이선스 & 기본 정보
        cat_basic = CategoryResult(name="📋 기본 정보", weight=0.10)
        cat_basic.items.append(self._score_license(r))
        cat_basic.items.append(self._score_description(r))
        categories.append(cat_basic)

        # 3. 개발 활동성
        cat_activity = CategoryResult(name="🔥 개발 활동성", weight=0.20)
        cat_activity.items.append(self._score_activity(commits, issues, pulls))
        categories.append(cat_activity)

        # 4. 커뮤니티
        cat_community = CategoryResult(name="👥 커뮤니티", weight=0.15)
        cat_community.items.append(self._score_contributors(contributors))
        categories.append(cat_community)

        # 5. 문서화
        cat_docs = CategoryResult(name="📚 문서화", weight=0.10)
        cat_docs.items.append(self._score_documentation(tree, r))
        categories.append(cat_docs)

        # 6. 코드 품질
        cat_quality = CategoryResult(name="🔍 코드 품질", weight=0.15)
        cat_quality.items.append(self._score_code_quality(tree, workflows))
        categories.append(cat_quality)

        # 7. 릴리스 관리
        cat_release = CategoryResult(name="📦 릴리스 관리", weight=0.05)
        cat_release.items.append(self._score_release_management(releases))
        categories.append(cat_release)

        # 8. 의존성 관리
        cat_deps = CategoryResult(name="📚 의존성 관리", weight=0.05)
        cat_deps.items.append(self._score_dependencies(tree))
        categories.append(cat_deps)

        # 9. 에코시스템
        cat_eco = CategoryResult(name="🌍 에코시스템", weight=0.03)
        cat_eco.items.append(self._score_ecosystem(r, languages))
        categories.append(cat_eco)

        # 10. 안전성
        cat_safety = CategoryResult(name="🛡️ 안전성", weight=0.02)
        cat_safety.items.append(self._score_safety(r, tree))
        categories.append(cat_safety)

        # 11. AI 활용도 (새로 추가)
        ai_utilization_data = None
        if HAS_AI_EVAL:
            ai_evaluator = AIUtilizationEvaluator(file_content_fetcher=self.get_file_content)
            topics = r.get("topics", [])
            branches = self.fetch_branches()
            ai_result = ai_evaluator.evaluate(
                tree=tree,
                languages=languages,
                topics=topics,
                repo_data=r,
                commits=commits,
                pulls=pulls,
                branches=branches,
            )
            cat_ai = CategoryResult(name="🤖 AI 활용도", weight=0.10)
            cat_ai.score = ai_result.total_score

            # AI 하위 항목들을 EvalResult로 변환
            for item in ai_result.items:
                eval_item = EvalResult(
                    name=item.name,
                    score=item.score,
                    max_score=item.max_score,
                    details=item.details,
                    sub_items=item.sub_items + item.evidence[:3],
                )
                cat_ai.items.append(eval_item)

            categories.append(cat_ai)
            ai_utilization_data = {
                "score": ai_result.total_score,
                "grade": ai_result.grade,
                "level": ai_result.ai_level,
                "summary": ai_result.summary,
                "detected_packages": ai_result.detected_packages,
                "detected_files": ai_result.detected_files[:10],
                "detected_topics": ai_result.detected_topics,
            }

        # 가중치 재조정 (합계 1.0 유지)
        # 기존 가중치 합계: 0.15+0.10+0.20+0.15+0.10+0.15+0.05+0.05+0.03+0.02 = 1.00
        # AI 활용도 10% 추가 시, 기존 가중치를 90%로 스케일링
        total_original_weight = sum(cat.weight for cat in categories if cat.name != "🤖 AI 활용도")
        if total_original_weight > 0:
            scale_factor = 0.90 / total_original_weight
            for cat in categories:
                if cat.name != "🤖 AI 활용도":
                    cat.weight = round(cat.weight * scale_factor, 4)

        # Calculate category scores
        for cat in categories:
            if cat.items and cat.name != "🤖 AI 활용도":  # AI는 이미 점수 설정됨
                cat.score = round(sum(i.score for i in cat.items) / len(cat.items), 1)

        self.categories = categories

        # Calculate total score (weighted average, 0-10 scale)
        total_weighted = sum(cat.weighted_score for cat in categories)
        total_weight = sum(cat.weight for cat in categories)
        total_score = round(total_weighted / total_weight, 1) if total_weight > 0 else 0

        # Grade
        if total_score >= 9:
            grade = "A+"
        elif total_score >= 8:
            grade = "A"
        elif total_score >= 7:
            grade = "B+"
        elif total_score >= 6:
            grade = "B"
        elif total_score >= 5:
            grade = "C+"
        elif total_score >= 4:
            grade = "C"
        elif total_score >= 3:
            grade = "D"
        else:
            grade = "F"

        result = {
            "repo": f"{self.owner}/{self.repo}",
            "total_score": total_score,
            "grade": grade,
            "categories": categories,
            "metadata": {
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "language": r.get("language"),
                "license": (r.get("license") or {}).get("spdx_id"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "size_kb": r.get("size", 0),
                "open_issues": r.get("open_issues_count", 0),
                "topics": r.get("topics", []),
            },
        }

        # AI 활용도 결과 추가
        if ai_utilization_data:
            result["ai_utilization"] = ai_utilization_data

        return result


# ─── 보고서 출력 ──────────────────────────────────────────────────────────────

def _grade_emoji(grade: str) -> str:
    grades = {"A+": "🏆", "A": "🥇", "B+": "🥈", "B": "🥉", "C+": "⭐", "C": "📌", "D": "⚠️", "F": "❌"}
    return grades.get(grade, "❓")


def _score_bar(score: float, max_score: float = 10, width: int = 20) -> str:
    filled = int(score / max_score * width)
    empty = width - filled
    return f"{'█' * filled}{'░' * empty}"


def _score_color_rich(console, score: float):
    """Rich 출력용 색상"""
    if score >= 8:
        return "[bold green]"
    elif score >= 6:
        return "[bold yellow]"
    elif score >= 4:
        return "[bold dark_orange]"
    else:
        return "[bold red]"


def print_report_rich(result: dict):
    """Rich 포맷으로 보고서 출력"""
    console = Console()

    repo = result["repo"]
    total = result["total_score"]
    grade = result["grade"]
    meta = result["metadata"]
    categories = result["categories"]

    # Header
    console.print()
    console.print(Panel(
        f"[bold cyan]GitHub 레포지토리 평가 보고서[/]\n"
        f"[bold white]{repo}[/]\n\n"
        f"{_grade_emoji(grade)} [bold {'green' if total >= 7 else 'yellow' if total >= 5 else 'red'}]"
        f"총점: {total}/10  ({grade})[/]",
        title="📊 Evaluation Report",
        border_style="cyan",
        padding=(1, 2),
    ))

    # Metadata
    meta_table = Table(show_header=False, box=None, padding=(0, 2))
    meta_table.add_column("Key", style="dim")
    meta_table.add_column("Value")
    meta_table.add_row("⭐ Stars", f"{meta['stars']:,}")
    meta_table.add_row("🍴 Forks", f"{meta['forks']:,}")
    meta_table.add_row("💻 언어", meta["language"] or "N/A")
    meta_table.add_row("📜 라이선스", meta["license"] or "N/A")
    meta_table.add_row("📅 생성일", meta["created_at"][:10] if meta["created_at"] else "N/A")
    meta_table.add_row("🔄 수정일", meta["updated_at"][:10] if meta["updated_at"] else "N/A")
    meta_table.add_row("📁 크기", f"{meta['size_kb']:,} KB")
    if meta["topics"]:
        meta_table.add_row("🏷️ 태그", ", ".join(meta["topics"][:5]))
    console.print(Panel(meta_table, title="📋 레포지토리 정보", border_style="blue"))

    # Category scores
    cat_table = Table(title="📊 카테고리별 점수", box=box.ROUNDED)
    cat_table.add_column("카테고리", style="bold", width=22)
    cat_table.add_column("점수", justify="center", width=14)
    cat_table.add_column("바", width=22)
    cat_table.add_column("가중치", justify="center", width=8)

    for cat in categories:
        bar = _score_bar(cat.score)
        color = _score_color_rich(console, cat.score)
        cat_table.add_row(
            cat.name,
            f"{color}{cat.score}/10[/]",
            f"{color}{bar}[/]",
            f"{cat.weight:.0%}",
        )

    console.print(cat_table)

    # AI 활용도 요약 (있는 경우)
    ai_data = result.get("ai_utilization")
    if ai_data:
        ai_panel_content = (
            f"[bold cyan]AI 활용 수준: {ai_data['level']}[/] (점수: {ai_data['score']}/10, 등급: {ai_data['grade']})\n"
            f"{ai_data['summary']}"
        )
        console.print(Panel(ai_panel_content, title="🤖 AI 활용도 요약", border_style="magenta"))

    # Detailed results per category
    console.print("\n[bold cyan]📝 상세 평가[/]")
    for cat in categories:
        console.print(f"\n[bold white]━━━ {cat.name} ({cat.score}/10) ━━━[/]")
        for item in cat.items:
            color = _score_color_rich(console, item.score)
            console.print(f"  {color}● {item.name}: {item.score}/{item.max_score}[/]")
            console.print(f"    {item.details}")
            if item.sub_items:
                for sub in item.sub_items:
                    console.print(f"      • {sub}")

    # Recommendations
    console.print("\n[bold cyan]💡 개선 제안[/]")
    recs = generate_recommendations(categories)
    for i, rec in enumerate(recs, 1):
        console.print(f"  {i}. {rec}")

    console.print()


def print_report_plain(result: dict):
    """일반 텍스트 보고서 출력"""
    repo = result["repo"]
    total = result["total_score"]
    grade = result["grade"]
    meta = result["metadata"]
    categories = result["categories"]

    print()
    print("=" * 60)
    print(f"  GitHub 레포지토리 평가 보고서")
    print(f"  {repo}")
    print(f"  {_grade_emoji(grade)} 총점: {total}/10  ({grade})")
    print("=" * 60)

    print(f"\n📋 레포지토리 정보")
    print(f"  Stars: {meta['stars']:,} | Forks: {meta['forks']:,}")
    print(f"  언어: {meta['language'] or 'N/A'} | 라이선스: {meta['license'] or 'N/A'}")
    print(f"  생성: {meta['created_at'][:10] if meta['created_at'] else 'N/A'}")
    print(f"  수정: {meta['updated_at'][:10] if meta['updated_at'] else 'N/A'}")

    print(f"\n📊 카테고리별 점수")
    for cat in categories:
        bar = _score_bar(cat.score)
        print(f"  {cat.name:<20s} {cat.score:>4.1f}/10  {bar}  (가중치: {cat.weight:.0%})")

    print(f"\n📝 상세 평가")
    for cat in categories:
        print(f"\n  ━━ {cat.name} ({cat.score}/10) ━━")
        for item in cat.items:
            print(f"    ● {item.name}: {item.score}/{item.max_score}")
            print(f"      {item.details}")
            for sub in item.sub_items:
                print(f"        • {sub}")

    print(f"\n💡 개선 제안")
    recs = generate_recommendations(categories)
    for i, rec in enumerate(recs, 1):
        print(f"  {i}. {rec}")
    print()


def generate_recommendations(categories: list) -> list:
    """평가 결과를 바탕으로 개선 제안 생성"""
    recs = []
    for cat in categories:
        for item in cat.items:
            if item.score < 4:
                if "라이선스" in item.name:
                    recs.append("라이선스를 추가하세요. MIT, Apache 2.0 등 오픈소스 라이선스를 검토하세요.")
                elif "문서화" in item.name and "AI" not in item.name:
                    recs.append("README.md를 작성하고, CONTRIBUTING.md, CHANGELOG 등 문서를 추가하세요.")
                elif "코드 품질" in item.name:
                    recs.append("CI/CD 파이프라인과 테스트를 추가하고, 린터를 설정하세요.")
                elif "릴리스" in item.name:
                    recs.append("릴리스를 자주 만들고, Semver를 따르세요.")
                elif "의존성" in item.name:
                    recs.append("잠금 파일을 추가하고, Dependabot을 설정하세요.")
                elif "기여자" in item.name:
                    recs.append("기여자를 늘리기 위해 CONTRIBUTING.md를 작성하고 이슈 템플릿을 추가하세요.")
                elif "활동" in item.name:
                    recs.append("개발 활동을 늘리기 위해 정기적인 커밋과 이슈 관리를 하세요.")
                # AI 활용도 관련 제안
                elif "AI/ML 라이브러리" in item.name:
                    recs.append("AI/ML 라이브러리를 활용하세요: TensorFlow, PyTorch, scikit-learn 등.")
                elif "AI 설정" in item.name:
                    recs.append("AI 코딩 도구를 설정하세요: GitHub Copilot, Cursor, Aider 등.")
                elif "AI 모델" in item.name:
                    recs.append("학습된 모델을 모델 카드와 함께 공유하세요.")
                elif "AI 에이전트" in item.name:
                    recs.append("AI 에이전트 프레임워크를 도입하세요: LangChain, CrewAI 등.")
                elif "학습/추론" in item.name:
                    recs.append("학습 파이프라인을 구축하세요: train.py, evaluate.py 등.")
                elif "노트북" in item.name:
                    recs.append("Jupyter 노트북으로 실험을 기록하세요.")
                elif "AI 문서화" in item.name:
                    recs.append("모델 카드와 벤치마크 문서를 작성하세요.")
            elif item.score < 6:
                if "문서화" in item.name and "AI" not in item.name:
                    recs.append("문서화를 개선하세요: docs/ 디렉토리, 예제 코드, 기여 가이드 추가.")
                elif "코드 품질" in item.name:
                    recs.append("코드 품질을 개선하세요: 테스트 커버리지, 타입 체크 설정.")
                elif "AI" in item.name:
                    recs.append("AI 활용도를 높이세요: 관련 라이브러리 추가, 설정 파일 구성.")

    if not recs:
        recs.append("전반적으로 우수한 레포지토리입니다! 🎉")

    return recs[:5]  # Top 5 recommendations


# ─── JSON 출력 ──────────────────────────────────────────────────────────────

def print_report_json(result: dict):
    """JSON 형식으로 보고서 출력"""
    output = {
        "repo": result["repo"],
        "total_score": result["total_score"],
        "grade": result["grade"],
        "metadata": result["metadata"],
        "categories": [],
        "recommendations": generate_recommendations(result["categories"]),
    }
    for cat in result["categories"]:
        cat_data = {
            "name": cat.name,
            "score": cat.score,
            "weight": cat.weight,
            "items": [
                {
                    "name": item.name,
                    "score": item.score,
                    "max_score": item.max_score,
                    "details": item.details,
                    "sub_items": item.sub_items,
                }
                for item in cat.items
            ],
        }
        output["categories"].append(cat_data)

    # AI 활용도 결과 추가
    if "ai_utilization" in result:
        output["ai_utilization"] = result["ai_utilization"]

    # Windows 콘솔 인코딩 문제 회피
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ─── CLI ──────────────────────────────────────────────────────────────────

def main():
    # Windows 콘솔 인코딩 문제 해결
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="GitHub 레포지토리 평가 프로그램",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python repo_evaluator.py facebook/react
  python repo_evaluator.py tensorflow/tensorflow --token ghp_xxxx
  python repo_evaluator.py rust-lang/rust --json
  python repo_evaluator.py denoland/deno --token $GITHUB_TOKEN
        """,
    )
    parser.add_argument(
        "repository",
        help="GitHub 레포지토리 (owner/repo 형식)",
    )
    parser.add_argument(
        "--token",
        help="GitHub Personal Access Token (API rate limit 해제)",
        default=os.environ.get("GITHUB_TOKEN"),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 형식으로 출력",
    )

    args = parser.parse_args()

    # Parse owner/repo
    repo_parts = args.repository.strip("/").split("/")
    if len(repo_parts) != 2 or not repo_parts[0] or not repo_parts[1]:
        print("❌ 올바른 형식: owner/repo (예: facebook/react)")
        sys.exit(1)

    owner, repo = repo_parts

    # Banner
    if not args.json:
        print("\n🔍 GitHub 레포지토리 평가 프로그램")
        print(f"   📂 평가 대상: {owner}/{repo}")
        if not args.token:
            print("   ⚠️  토큰 없음 (rate limit 적용, --token 또는 GITHUB_TOKEN 환경변수 사용 권장)")
        print()

    # Evaluate
    evaluator = RepoEvaluator(owner, repo, args.token)

    if not evaluator.fetch_repo_info():
        print(f"❌ 레포지토리 '{owner}/{repo}'를 찾을 수 없습니다.")
        print("   • 레포지토리 경로가 올바른지 확인하세요.")
        print("   • 비공개 레포지토리인 경우 --token 옵션을 사용하세요.")
        sys.exit(1)

    result = evaluator.evaluate()

    # Output
    if args.json:
        print_report_json(result)
    elif HAS_RICH:
        print_report_rich(result)
    else:
        print_report_plain(result)


if __name__ == "__main__":
    main()
