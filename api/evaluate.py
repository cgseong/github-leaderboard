"""
GitHub 레포지토리 평가 API (Vercel Serverless Function)

사용법:
    POST /api/evaluate
    Body: { "repo": "owner/repo", "token": "optional_github_token" }
"""

import json
import math
import re
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from http.server import BaseHTTPRequestHandler

# ─── GitHub API ──────────────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"

def gh_get(endpoint: str, token: Optional[str] = None) -> Optional[dict | list]:
    """GitHub API GET 요청"""
    import urllib.request
    import urllib.error
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Repo-Evaluator/1.0"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        req = urllib.request.Request(
            f"{GITHUB_API}{endpoint}",
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code == 403:
            return {"error": "rate_limit"}
        return None
    except Exception:
        return None


def gh_get_file_content(owner: str, repo: str, path: str, token: Optional[str] = None) -> Optional[str]:
    """GitHub API로 파일 내용 가져오기"""
    endpoint = f"/repos/{owner}/{repo}/contents/{path}"
    data = gh_get(endpoint, token)
    if data and "content" in data:
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return None
    return None


# ─── AI 관련 패키지 매핑 ──────────────────────────────────────────────────────

AI_PACKAGES = {
    "python": {
        "tensorflow": "Deep Learning", "keras": "Deep Learning", "torch": "Deep Learning",
        "pytorch": "Deep Learning", "jax": "Deep Learning", "flax": "Deep Learning",
        "scikit-learn": "Machine Learning", "sklearn": "Machine Learning",
        "xgboost": "Machine Learning", "lightgbm": "Machine Learning",
        "transformers": "NLP/LLM", "huggingface-hub": "NLP/LLM",
        "langchain": "LLM Agent", "langchain-core": "LLM Agent",
        "llamaindex": "LLM Agent", "openai": "LLM API", "anthropic": "LLM API",
        "opencv-python": "Computer Vision", "torchvision": "Computer Vision",
        "diffusers": "Generative AI", "accelerate": "ML Training",
        "mlflow": "MLOps", "wandb": "MLOps",
        "autogen": "AI Agent", "crewai": "AI Agent", "metagpt": "AI Agent",
    },
    "javascript": {
        "@tensorflow/tfjs": "Deep Learning", "brain.js": "Neural Network",
        "natural": "NLP", "openai": "LLM API", "langchain": "LLM Agent",
        "chromadb": "Vector DB", "pinecone-client": "Vector DB",
    },
    "rust": {
        "candle": "Deep Learning", "burn": "Deep Learning", "tch": "Deep Learning",
    },
    "java": {
        "deeplearning4j": "Deep Learning", "weka": "Machine Learning",
    },
    "go": {
        "gonum": "Numerical Computing", "gorgonia": "Deep Learning",
    },
}

AI_CONFIG_FILES = {
    ".github/copilot-instructions.md": "GitHub Copilot",
    ".cursorrules": "Cursor AI", ".cursorignore": "Cursor AI",
    ".aider.conf.yml": "Aider", ".clinerules": "Cline",
    ".continue/config.json": "Continue", ".windsurfrules": "Windsurf",
}

AI_MODEL_PATTERNS = [
    r"\.pt$", r"\.pth$", r"\.onnx$", r"\.h5$", r"\.pb$", r"\.tflite$",
    r"\.safetensors$", r"\.gguf$", r"\.ggml$", r"\.ckpt$",
]

AI_TRAINING_PATTERNS = [
    r"train(?:ing)?\.py$", r"finetune\.py$", r"fine[-_]tune\.py$",
    r"evaluate\.py$", r"eval\.py$", r"infer(?:ence)?\.py$", r"predict\.py$",
]

AI_TOPICS = {
    "ai", "artificial-intelligence", "machine-learning", "deep-learning",
    "neural-network", "nlp", "llm", "large-language-model",
    "transformer", "pytorch", "tensorflow", "generative-ai",
    "reinforcement-learning", "computer-vision", "mlops",
}


# ─── 평가 엔진 ──────────────────────────────────────────────────────────────

class RepoEvaluator:
    """GitHub 레포지토리 평가 엔진"""

    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.repo_data: Optional[dict] = None

    def get_file_content(self, path: str) -> Optional[str]:
        return gh_get_file_content(self.owner, self.repo, path, self.token)

    def fetch_repo_info(self) -> bool:
        self.repo_data = gh_get(f"/repos/{self.owner}/{self.repo}", self.token)
        return self.repo_data is not None

    def fetch_commits(self, since_days: int = 90) -> list:
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        result = gh_get(f"/repos/{self.owner}/{self.repo}/commits?since={since}&per_page=100", self.token)
        return result if isinstance(result, list) else []

    def fetch_issues(self, since_days: int = 90) -> list:
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        result = gh_get(f"/repos/{self.owner}/{self.repo}/issues?since={since}&state=all&per_page=100", self.token)
        return result if isinstance(result, list) else []

    def fetch_pulls(self, since_days: int = 90) -> list:
        result = gh_get(f"/repos/{self.owner}/{self.repo}/pulls?state=all&sort=updated&direction=desc&per_page=100", self.token)
        return result if isinstance(result, list) else []

    def fetch_contributors(self) -> list:
        result = gh_get(f"/repos/{self.owner}/{self.repo}/contributors?per_page=100", self.token)
        return result if isinstance(result, list) else []

    def fetch_languages(self) -> dict:
        result = gh_get(f"/repos/{self.owner}/{self.repo}/languages", self.token)
        return result if isinstance(result, dict) else {}

    def fetch_tree(self, ref: str = "HEAD", recursive: bool = True) -> list:
        params = "?recursive=1" if recursive else ""
        result = gh_get(f"/repos/{self.owner}/{self.repo}/git/trees/{ref}{params}", self.token)
        if result and "tree" in result:
            return result["tree"]
        return []

    def fetch_releases(self) -> list:
        result = gh_get(f"/repos/{self.owner}/{self.repo}/releases?per_page=100", self.token)
        return result if isinstance(result, list) else []

    def fetch_workflows(self) -> list:
        result = gh_get(f"/repos/{self.owner}/{self.repo}/actions/workflows?per_page=100", self.token)
        if result and "workflows" in result:
            return result["workflows"]
        return []

    # ── 평가 메서드 ──────────────────────────────────────────────────────

    def _score_popularity(self, r: dict) -> dict:
        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        watchers = r.get("watchers_count", 0)
        star_score = min(10, math.log10(stars + 1) * 1.67)
        fork_score = min(10, math.log10(forks + 1) * 2.0)
        watcher_score = min(10, math.log10(watchers + 1) * 2.5)
        score = star_score * 0.5 + fork_score * 0.3 + watcher_score * 0.2
        return {
            "name": "인기도 (Popularity)",
            "score": round(score, 1),
            "max_score": 10,
            "details": f"⭐ {stars:,} stars · 🍴 {forks:,} forks · 👀 {watchers:,} watchers",
            "sub_items": [f"Stars: {stars:,} ({star_score:.1f}/10)", f"Forks: {forks:,} ({fork_score:.1f}/10)", f"Watchers: {watchers:,} ({watcher_score:.1f}/10)"]
        }

    def _score_license(self, r: dict) -> dict:
        license_info = r.get("license")
        if license_info and license_info.get("spdx_id") and license_info["spdx_id"] != "NOASSERTION":
            return {"name": "라이선스 (License)", "score": 10.0, "max_score": 10, "details": f"✅ {license_info['spdx_id']}", "sub_items": []}
        return {"name": "라이선스 (License)", "score": 0.0, "max_score": 10, "details": "❌ 라이선스 없음", "sub_items": []}

    def _score_description(self, r: dict) -> dict:
        desc = r.get("description") or ""
        homepage = r.get("homepage") or ""
        score = 4.0 if len(desc) > 10 else (2.0 if len(desc) > 0 else 0.0)
        if homepage: score += 2.0
        details = f"설명: \"{desc[:80]}\"" if desc else "설명: 없음"
        if homepage: details += f" · 홈페이지: {homepage}"
        return {"name": "프로젝트 설명 (Description)", "score": min(10, score), "max_score": 10, "details": details, "sub_items": []}

    def _score_activity(self, commits: list, issues: list, pulls: list) -> dict:
        now = datetime.now(timezone.utc)
        recent_30 = now - timedelta(days=30)
        commits_30 = sum(1 for c in commits if c.get("commit", {}).get("author", {}).get("date", "") and datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00")) > recent_30)
        issues_opened = len([i for i in issues if not i.get("pull_request")])
        issues_closed = sum(1 for i in issues if not i.get("pull_request") and i.get("state") == "closed")
        pr_merged = sum(1 for p in pulls if p.get("merged_at"))
        commit_score = min(10, commits_30 * 0.5)
        issue_score = min(10, issues_opened * 0.3 + issues_closed * 0.5)
        pr_score = min(10, len(pulls) * 0.3 + pr_merged * 0.5)
        score = commit_score * 0.5 + issue_score * 0.2 + pr_score * 0.3
        return {
            "name": "개발 활동성 (Activity)", "score": round(score, 1), "max_score": 10,
            "details": f"최근 30일 커밋: {commits_30} · 이슈: {issues_opened}개 열림/{issues_closed}개 닫힘 · PR: {pr_merged}개 병합",
            "sub_items": [f"커밋 활동: {commits_30}개/30일", f"이슈 관리: {issues_opened}개 열림, {issues_closed}개 닫힘", f"PR 관리: {pr_merged}개 병합"]
        }

    def _score_contributors(self, contributors: list) -> dict:
        total = len(contributors)
        core = sum(1 for c in contributors if c.get("contributions", 0) > 50)
        active = sum(1 for c in contributors if 5 < c.get("contributions", 0) <= 50)
        contributor_score = min(10, math.log10(total + 1) * 2.0)
        if total > 100: contributor_score = min(10, contributor_score + 1)
        score = contributor_score
        return {
            "name": "커뮤니티 (Community)", "score": round(score, 1), "max_score": 10,
            "details": f"총 {total}명 · 핵심: {core}명 · 활발: {active}명",
            "sub_items": [f"총 기여자: {total}명", f"핵심(50+ 커밋): {core}명", f"활발(5~50 커밋): {active}명"]
        }

    def _score_documentation(self, tree: list) -> dict:
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        file_names = [p.split("/")[-1].lower() for p in file_paths]
        dir_names = set(p.split("/")[0].lower() for p in file_paths if "/" in p)
        score = 0.0
        details = []
        if any(f.startswith("readme") for f in file_names): score += 2.5; details.append("✅ README.md")
        else: details.append("❌ README.md 없음")
        if any(f in ("contributing.md", "contribute.md") for f in file_names): score += 1.5; details.append("✅ CONTRIBUTING.md")
        if any("code_of_conduct" in f for f in file_names): score += 1.0; details.append("✅ CODE_OF_CONDUCT")
        if any(d in ("docs", "doc", "documentation") for d in dir_names): score += 2.0; details.append("✅ docs/ 디렉토리")
        if any(d in ("examples", "example", "samples") for d in dir_names): score += 1.0; details.append("✅ examples/ 디렉토리")
        return {"name": "문서화 (Documentation)", "score": min(10, round(score, 1)), "max_score": 10, "details": " · ".join(details), "sub_items": details}

    def _score_code_quality(self, tree: list, workflows: list) -> dict:
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        file_names_lower = [p.split("/")[-1].lower() for p in file_paths]
        score = 0.0
        details = []
        if len(workflows) > 0: score += 2.5; details.append(f"✅ CI/CD ({len(workflows)}개)")
        else: details.append("❌ CI/CD 없음")
        linting = any(lf in fn for fn in file_names_lower for lf in ["eslint", ".prettierrc", ".flake8", "ruff", ".editorconfig"])
        if linting: score += 1.5; details.append("✅ 린터/포맷터")
        type_check = any(fn in ("tsconfig.json", "mypy.ini", "py.typed") for fn in file_names_lower)
        if type_check: score += 1.0; details.append("✅ 타입 체크")
        test_patterns = ["test", "spec", "__tests__", "tests"]
        if any(any(tp in f for tp in test_patterns) for f in file_names_lower): score += 2.0; details.append("✅ 테스트")
        if ".gitignore" in file_names_lower: score += 0.5; details.append("✅ .gitignore")
        return {"name": "코드 품질 (Code Quality)", "score": min(10, round(score, 1)), "max_score": 10, "details": " · ".join(details), "sub_items": details}

    def _score_release_management(self, releases: list) -> dict:
        score = 0.0
        details = []
        if releases:
            score += 3.0; details.append(f"릴리스 {len(releases)}개")
            now = datetime.now(timezone.utc)
            for rel in releases[:5]:
                pub_date = rel.get("published_at", "")
                if pub_date:
                    try:
                        dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                        days_ago = (now - dt).days
                        if days_ago < 30: score += 2.0; details.append(f"최근: {days_ago}일 전"); break
                        elif days_ago < 90: score += 1.0; details.append(f"최근: {days_ago}일 전"); break
                    except: pass
            if sum(1 for r in releases if r.get("tag_name") and re.match(r"^\d+\.\d+\.\d+", r["tag_name"])) > 0:
                score += 2.0; details.append("Semver 태그")
        else: details.append("릴리스 없음")
        return {"name": "릴리스 관리 (Release Management)", "score": min(10, round(score, 1)), "max_score": 10, "details": " · ".join(details) if details else "정보 없음", "sub_items": details}

    def _score_dependencies(self, tree: list) -> dict:
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        file_names_lower = set(f.split("/")[-1].lower() for f in file_paths)
        score = 0.0
        details = []
        lock_files = {"package-lock.json": "npm", "yarn.lock": "yarn", "poetry.lock": "Poetry", "go.sum": "Go", "Cargo.lock": "Cargo"}
        found_locks = [lock_files[f] for f in file_names_lower if f in lock_files]
        if found_locks: score += 3.0; details.append(f"잠금 파일: {', '.join(found_locks)}")
        has_dependabot = any("dependabot" in p.lower() for p in file_paths)
        if has_dependabot: score += 2.5; details.append("✅ Dependabot")
        return {"name": "의존성 관리 (Dependencies)", "score": min(10, round(score, 1)), "max_score": 10, "details": " · ".join(details) if details else "의존성 정보 없음", "sub_items": details}

    def _score_ecosystem(self, r: dict, languages: dict) -> dict:
        primary_lang = r.get("language") or "Unknown"
        topics = r.get("topics", [])
        score = 3.0
        details = [f"주 언어: {primary_lang}"]
        if len(languages) > 3: score += 1.0; details.append(f"사용 언어: {len(languages)}개")
        if topics: score += min(3.0, len(topics) * 0.5); details.append(f"태그: {', '.join(topics[:5])}")
        if r.get("homepage"): score += 1.0
        return {"name": "에코시스템 (Ecosystem)", "score": min(10, round(score, 1)), "max_score": 10, "details": " · ".join(details), "sub_items": details}

    def _score_safety(self, r: dict, tree: list) -> dict:
        score = 0.0
        details = []
        if not r.get("fork"): score += 2.0; details.append("원본 레포지토리 ✅")
        if not r.get("archived"): score += 2.0
        if r.get("default_branch") in ("main", "master"): score += 1.0
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        if any("security" in p.lower() for p in file_paths): score += 2.0; details.append("✅ 보안 정책")
        score += 1.0
        return {"name": "안전성 (Safety)", "score": max(0, min(10, round(score, 1))), "max_score": 10, "details": " · ".join(details) if details else "안전성 정보 없음", "sub_items": details}

    def _score_ai_utilization(self, tree: list, languages: dict, topics: list) -> dict:
        """AI 활용도 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        file_names = [p.split("/")[-1].lower() for p in file_paths]
        
        # 감지된 AI 관련 항목들
        detected_packages = {}
        detected_files = []
        detected_topics = []
        
        # 1. AI 설정 파일 감지
        config_score = 0.0
        for path in file_paths:
            for pattern, tool in AI_CONFIG_FILES.items():
                if pattern in path:
                    config_score += 3.0
                    detected_files.append(path)
        
        # 2. AI 모델 파일 감지
        model_score = 0.0
        for path in file_paths:
            for pattern in AI_MODEL_PATTERNS:
                if re.search(pattern, path, re.IGNORECASE):
                    model_score += 1.0
                    detected_files.append(path)
        
        # 3. AI 관련 태그
        topic_score = 0.0
        for topic in topics:
            if topic.lower() in AI_TOPICS:
                topic_score += 2.0
                detected_topics.append(topic)
        
        # 4. 학습/추론 스크립트
        script_score = 0.0
        for path in file_paths:
            for pattern in AI_TRAINING_PATTERNS:
                if re.search(pattern, path, re.IGNORECASE):
                    script_score += 1.5
                    detected_files.append(path)
        
        # 5. AI 문서화
        doc_score = 0.0
        ai_doc_patterns = ["model_card.md", "benchmarks.md", "training.md", "evaluation.md"]
        for fn in file_names:
            for pattern in ai_doc_patterns:
                if pattern in fn:
                    doc_score += 2.0
        
        # 총점 계산
        total_score = (config_score + model_score + topic_score + script_score + doc_score) / 5
        total_score = min(10, total_score)
        
        # AI 수준 결정
        if total_score >= 8: level, grade = "AI-Native", "A+"
        elif total_score >= 6: level, grade = "Advanced", "A"
        elif total_score >= 4: level, grade = "Moderate", "B+"
        elif total_score >= 2: level, grade = "Basic", "B"
        elif total_score >= 1: level, grade = "Minimal", "C"
        else: level, grade = "None", "N/A"
        
        summary = f"AI 활용 수준: {level} ({total_score:.1f}/10)"
        if detected_topics: summary += f" | 태그: {', '.join(detected_topics[:3])}"
        
        return {
            "score": round(total_score, 1),
            "grade": grade,
            "level": level,
            "summary": summary,
            "detected_packages": detected_packages,
            "detected_files": detected_files[:10],
            "detected_topics": detected_topics,
        }

    def evaluate(self) -> dict:
        """전체 평가 실행"""
        r = self.repo_data
        if not r:
            return {"error": "레포지토리 정보를 가져올 수 없습니다."}

        commits = self.fetch_commits()
        issues = self.fetch_issues()
        pulls = self.fetch_pulls()
        contributors = self.fetch_contributors()
        languages = self.fetch_languages()
        tree = self.fetch_tree()
        releases = self.fetch_releases()
        workflows = self.fetch_workflows()

        categories = [
            {"name": "⭐ 인기도", "weight": 0.135, "items": [self._score_popularity(r)]},
            {"name": "📋 기본 정보", "weight": 0.09, "items": [self._score_license(r), self._score_description(r)]},
            {"name": "🔥 개발 활동성", "weight": 0.18, "items": [self._score_activity(commits, issues, pulls)]},
            {"name": "👥 커뮤니티", "weight": 0.135, "items": [self._score_contributors(contributors)]},
            {"name": "📚 문서화", "weight": 0.09, "items": [self._score_documentation(tree)]},
            {"name": "🔍 코드 품질", "weight": 0.135, "items": [self._score_code_quality(tree, workflows)]},
            {"name": "📦 릴리스 관리", "weight": 0.045, "items": [self._score_release_management(releases)]},
            {"name": "📚 의존성 관리", "weight": 0.045, "items": [self._score_dependencies(tree)]},
            {"name": "🌍 에코시스템", "weight": 0.027, "items": [self._score_ecosystem(r, languages)]},
            {"name": "🛡️ 안전성", "weight": 0.018, "items": [self._score_safety(r, tree)]},
            {"name": "🤖 AI 활용도", "weight": 0.1, "items": []},
        ]

        # AI 활용도 평가
        ai_result = self._score_ai_utilization(tree, languages, r.get("topics", []))
        categories[-1]["score"] = ai_result["score"]

        # 카테고리 점수 계산
        for cat in categories:
            if cat["items"] and "score" not in cat:
                cat["score"] = round(sum(i["score"] for i in cat["items"]) / len(cat["items"]), 1)

        # 총점 계산
        total_weighted = sum(cat["score"] * cat["weight"] for cat in categories)
        total_weight = sum(cat["weight"] for cat in categories)
        total_score = round(total_weighted / total_weight, 1) if total_weight > 0 else 0

        # 등급
        if total_score >= 9: grade = "A+"
        elif total_score >= 8: grade = "A"
        elif total_score >= 7: grade = "B+"
        elif total_score >= 6: grade = "B"
        elif total_score >= 5: grade = "C+"
        elif total_score >= 4: grade = "C"
        elif total_score >= 3: grade = "D"
        else: grade = "F"

        # 개선 제안
        recommendations = []
        for cat in categories:
            for item in cat.get("items", []):
                if item.get("score", 10) < 4:
                    if "라이선스" in item["name"]: recommendations.append("라이선스를 추가하세요.")
                    elif "문서화" in item["name"]: recommendations.append("README.md와 CONTRIBUTING.md를 작성하세요.")
                    elif "코드 품질" in item["name"]: recommendations.append("CI/CD와 테스트를 추가하세요.")
                    elif "AI" in item["name"]: recommendations.append("AI 관련 라이브러리와 설정을 추가하세요.")
        if not recommendations: recommendations.append("전반적으로 우수한 레포지토리입니다! 🎉")

        return {
            "repo": f"{self.owner}/{self.repo}",
            "total_score": total_score,
            "grade": grade,
            "categories": categories,
            "ai_utilization": ai_result,
            "recommendations": recommendations[:5],
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


# ─── Vercel Serverless Function ──────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 요청 본문 읽기
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "잘못된 JSON 형식"}).encode())
            return

        repo = data.get("repo", "")
        token = data.get("token") or None

        # 레포지토리 경로 검증
        parts = repo.strip("/").split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "올바른 형식: owner/repo"}).encode())
            return

        owner, repo_name = parts

        # 평가 실행
        evaluator = RepoEvaluator(owner, repo_name, token)
        if not evaluator.fetch_repo_info():
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"레포지토리 '{owner}/{repo_name}'를 찾을 수 없습니다."}).encode())
            return

        result = evaluator.evaluate()

        # 응답 전송
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass  # 로그 비활성화
