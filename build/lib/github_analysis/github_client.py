from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from typing import Any

import requests


class GitHubClient:
    def __init__(self, token: str | None, timeout: int = 20) -> None:
        self.base_url = "https://api.github.com"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "github-analysis-v2",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()

    def get_repo(self, owner: str, repo: str) -> dict[str, Any]:
        return self._get(f"/repos/{owner}/{repo}")

    def get_readme(self, owner: str, repo: str) -> str:
        payload = self._get(f"/repos/{owner}/{repo}/readme")
        encoded = payload.get("content", "")
        return base64.b64decode(encoded).decode("utf-8", errors="replace")

    def get_tree(self, owner: str, repo: str, branch: str) -> list[dict[str, Any]]:
        payload = self._get(f"/repos/{owner}/{repo}/git/trees/{branch}", params={"recursive": "1"})
        return payload.get("tree", [])

    def get_commits(self, owner: str, repo: str, days: int, per_page: int = 100) -> list[dict[str, Any]]:
        since = (datetime.now(UTC) - timedelta(days=days)).replace(microsecond=0).isoformat()
        return self._get(
            f"/repos/{owner}/{repo}/commits",
            params={"since": since, "per_page": per_page, "page": 1},
        )

    def get_pulls(self, owner: str, repo: str, state: str = "closed", per_page: int = 100) -> list[dict[str, Any]]:
        return self._get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": per_page, "sort": "updated", "direction": "desc"},
        )

    def get_issues(self, owner: str, repo: str, state: str, per_page: int = 100) -> list[dict[str, Any]]:
        issues = self._get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page, "sort": "updated", "direction": "desc"},
        )
        return [issue for issue in issues if "pull_request" not in issue]

    def get_contributors(self, owner: str, repo: str, per_page: int = 100) -> list[dict[str, Any]]:
        return self._get(
            f"/repos/{owner}/{repo}/contributors",
            params={"per_page": per_page, "anon": "false"},
        )

    def get_languages(self, owner: str, repo: str) -> dict[str, int]:
        return self._get(f"/repos/{owner}/{repo}/languages")

