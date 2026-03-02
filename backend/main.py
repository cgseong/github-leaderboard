import sys
import os

# src 폴더를 경로에 추가하여 github_analysis 모듈을 불러올 수 있도록 설정합니다.
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from github_analysis.evaluator import RepositoryEvaluator
from github_analysis.github_client import GitHubClient
from github_analysis.config import DEFAULT_RUBRIC, Rubric
from github_analysis.cli import parse_repo

app = FastAPI(
    title="GitHub Repo Evaluator API",
    description="GitHub 레포지토리를 분석하고 점수를 반환하는 API",
    version="0.1.0"
)

# CORS 설정: 프론트엔드 연동을 위해 모든 오리진 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    repo: str
    token: str | None = None

@app.post("/api/analyze")
def analyze_repo(request: AnalyzeRequest):
    """
    제공된 토큰과 레포지토리 정보(owner/repo)를 기반으로 분석을 수행하고 결과를 반환합니다.
    """
    try:
        owner, repo = parse_repo(request.repo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # GitHub 클라이언트 및 채점 기준(Rubric) 초기화
    client = GitHubClient(token=request.token)
    rubric = Rubric(
        pass_score=DEFAULT_RUBRIC["pass_score"],
        sections={k: float(v) for k, v in DEFAULT_RUBRIC["sections"].items()}
    )
    evaluator = RepositoryEvaluator(client, rubric)
    
    try:
        # 레포지토리 기본 정보 가져오기 및 평가 진행
        repo_info = client.get_repo(owner, repo)
        report = evaluator.evaluate(owner, repo, repo_info=repo_info)
        
        # 분석 결과를 딕셔너리 형태로 변환하여 반환
        payload = evaluator.report_to_dict(report)
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
