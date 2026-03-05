# GitHub Repository Analysis & Evaluation System

GitHub 레포지토리를 `수동 분석 프레임워크 + 자동 메트릭 수집 + 교육용 자동 채점`으로 통합 평가하는 시스템입니다.

## 1. 무엇을 평가하나요?

본 시스템은 다음 4개 섹션 점수를 합산해 총점을 계산합니다.

- `code_quality` (기본 40점): Reliability, Maintainability, Security, Coverage 신호
- `activity` (기본 25점): 최근 커밋/기여자/최근 업데이트
- `documentation` (기본 20점): README/라이선스/문서 자산
- `collaboration` (기본 15점): PR/Issue 흐름, 템플릿, CODEOWNERS

기본 합격 기준은 `70점`(`rubric.default.yaml`)입니다.

## 2. 구성 요소

- CLI 분석기: `repo-eval`
- 핵심 로직: `src/github_analysis/evaluator.py`
- GitHub API 클라이언트: `src/github_analysis/github_client.py`
- 기본 루브릭: `rubric.default.yaml`
- 자동 실행 워크플로우:
  - `.github/workflows/repository-analysis.yml` (수동 실행/주기 실행)
  - `.github/workflows/autograding.yml` (push/PR 자동 채점)

## 3. 로컬 실행

```bash
pip install .
repo-eval owner/repo --token YOUR_GITHUB_TOKEN
```

URL도 지원합니다.

```bash
repo-eval https://github.com/owner/repo --token YOUR_GITHUB_TOKEN
```

결과물:

- Markdown: `reports/report.md`
- JSON: `reports/report.json`

## 4. 웹 앱 모드 실행 (React + FastAPI)

이 프로젝트는 React 프랜트엔드와 FastAPI 백엔드로 구성된 웹 애플리케이션으로도 활용할 수 있습니다. 각 서버를 개별적으로 실행해야 합니다.

### A. 백엔드 (FastAPI) 실행
```bash
# 기본 8000번 포트로 실행됩니다.
python -m uvicorn backend.main:app --reload
```

### B. 프론트엔드 (React) 실행
```bash
cd frontend
npm install
npm run dev
```

### 자동 채점 모드

```bash
repo-eval owner/repo --mode autograde --token YOUR_GITHUB_TOKEN

![Alt](https://repobeats.axiom.co/api/embed/b4c6e16d5a126d33f6c5b6f645b38b03ebae3433.svg "Repobeats analytics image") 
```

출력 예:

```text
RESULT=PASS
SCORE=81.25
MAX_SCORE=100.00
GRADE=B
```

`--mode autograde`는 점수가 기준 미만이면 non-zero 코드(`3`)로 종료합니다.

## 4. 평가 방식 매핑 (요청하신 3관점)

### A. 수동 분석 관점

`report.md`에 아래 체크리스트를 자동 포함합니다.

- `phase_1`: README/브랜치/최근 푸시/대표 언어
- `phase_2`: 코드 품질/문서화 점수/테스트 자산
- `phase_3`: 협업/활동 점수/워크플로우 자산

리뷰어는 체크리스트와 Evidence를 같이 보며 정성 평가를 보완할 수 있습니다.

### B. 자동화 도구 관점

GitHub REST API로 다음 데이터를 수집합니다.

- 레포 기본 메트릭(stars, forks, issues, pushed_at)
- commits(30/90일), contributors
- pull requests(merged ratio, merge 시간)
- issues(open/closed 샘플)
- 파일 트리(README, SECURITY, tests, workflows, templates 등)

이를 정규화해 섹션별 점수로 환산합니다.

### C. 교육 환경(자동 채점) 관점

`.github/workflows/autograding.yml`에서

1. 테스트 실행 (`pytest`)
2. `repo-eval --mode autograde`
3. 결과 아티팩트 업로드

를 자동 수행합니다. 즉시 피드백 가능한 과제 채점 파이프라인으로 사용할 수 있습니다.

## 5. GitHub Actions 실행

`Repository Analysis` 워크플로우를 `workflow_dispatch`로 실행할 때:

- `target_repo`: 평가 대상 (`owner/repo` 또는 URL)
- `mode`: `standard` 또는 `autograde`

결과는 아티팩트와 Actions Summary로 확인할 수 있습니다.

## 6. 루브릭 커스터마이징

`rubric.default.yaml`을 복제해 점수 비중/합격선 조정:

```yaml
pass_score: 75
sections:
  code_quality: 35
  activity: 20
  documentation: 20
  collaboration: 25
```

실행:

```bash
repo-eval owner/repo --rubric my-rubric.yaml --token YOUR_GITHUB_TOKEN
```

## 7. 한계와 확장 포인트

- GitHub API rate limit 및 비공개 레포 접근은 토큰 권한에 의존
- 현재 정적 코드 복잡도/lint/실제 커버리지 수치는 신호 기반 추정
- 확장 권장:
  - CodeQL/Sonar/coverage 리포트 연동
  - LLM 피드백 단계 추가 (파일 단위 개선 제안)
  - 과목별 채점 기준 템플릿 분리
