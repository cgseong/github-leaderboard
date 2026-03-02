from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from .config import load_rubric
from .evaluator import RepositoryEvaluator
from .github_client import GitHubClient
from .models import EvaluationReport


def parse_repo(value: str) -> tuple[str, str]:
    value = value.strip()
    if value.startswith("http://") or value.startswith("https://"):
        match = re.search(r"github\.com/([^/]+)/([^/]+)", value)
        if not match:
            raise ValueError(f"유효한 GitHub URL이 아닙니다: {value}")
        owner, repo = match.group(1), match.group(2)
        return owner, repo.removesuffix(".git")
    if "/" not in value:
        raise ValueError("레포 입력은 owner/repo 또는 GitHub URL이어야 합니다.")
    owner, repo = value.split("/", 1)
    return owner, repo.removesuffix(".git")


def to_markdown(report: EvaluationReport) -> str:
    lines: list[str] = [
        f"# Repository Evaluation Report: `{report.repo}`",
        "",
        f"- Generated At: `{report.generated_at}`",
        f"- Total Score: **{report.total_score:.2f} / {report.max_score:.2f}**",
        f"- Grade: **{report.grade}**",
        f"- Result: **{report.pass_fail}**",
        "",
        "## Section Scores",
        "",
        "| Section | Score | Summary |",
        "|---|---:|---|",
    ]
    for section in report.sections:
        lines.append(f"| {section.name} | {section.score:.2f} / {section.max_score:.2f} | {section.summary} |")

    lines.append("")
    lines.append("## Evidence")
    lines.append("")
    for section in report.sections:
        lines.append(f"### {section.name}")
        lines.append("")
        for key, value in section.evidence.items():
            lines.append(f"- {key}: `{value}`")
        lines.append("")

    lines.append("## Checklist")
    lines.append("")
    for phase, entries in report.checklist.items():
        lines.append(f"### {phase}")
        lines.append("")
        for item in entries:
            lines.append(f"- {item}")
        lines.append("")

    if report.warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in report.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    if report.contributor_details:
        lines.append("## Contributor Activity Details")
        lines.append("")
        lines.append("| Contributor | Commits (C) | PR Open | PR Merged | Reviews Total | Approved | Changes Requested |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for c in report.contributor_details:
            lines.append(
                f"| {c['login']} | {c['C']} | {c['P_open']} | {c['P_merged']} | "
                f"{c['R_total']} | {c['R_approve']} | {c['R_changes']} |"
            )
        lines.append("")

    lines.append("## Raw Metrics")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report.raw_metrics, ensure_ascii=False, indent=2))
    lines.append("```")
    return "\n".join(lines)


def write_file(path: str | None, content: str) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_json(path: str | None, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def print_autograde_summary(report: EvaluationReport) -> None:
    print(f"RESULT={report.pass_fail}")
    print(f"SCORE={report.total_score:.2f}")
    print(f"MAX_SCORE={report.max_score:.2f}")
    print(f"GRADE={report.grade}")

    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as f:
            f.write(f"result={report.pass_fail}\n")
            f.write(f"score={report.total_score:.2f}\n")
            f.write(f"max_score={report.max_score:.2f}\n")
            f.write(f"grade={report.grade}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze and evaluate a GitHub repository.")
    parser.add_argument("repo", help="owner/repo or GitHub URL")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token (or GITHUB_TOKEN env)")
    parser.add_argument("--rubric", default=None, help="Path to rubric YAML")
    parser.add_argument("--output-md", default="reports/report.md", help="Markdown output path")
    parser.add_argument("--output-json", default="reports/report.json", help="JSON output path")
    parser.add_argument("--mode", choices=["standard", "autograde"], default="standard", help="Output mode")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        owner, repo = parse_repo(args.repo)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    rubric = load_rubric(args.rubric)
    client = GitHubClient(token=args.token)
    evaluator = RepositoryEvaluator(client, rubric)

    try:
        report = evaluator.evaluate(owner, repo)
    except Exception as exc:
        print(f"평가 실패: {exc}", file=sys.stderr)
        return 1

    payload = evaluator.report_to_dict(report)
    markdown = to_markdown(report)
    write_file(args.output_md, markdown)
    write_json(args.output_json, payload)

    if args.mode == "autograde":
        print_autograde_summary(report)
        return 0 if report.pass_fail == "PASS" else 3

    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

