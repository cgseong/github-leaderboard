# 🔍 GitHub 레포지토리 평가 웹 애플리케이션

GitHub 레포지토리를 다양한 기준으로 평가하고 AI 활용도를 분석하는 웹 애플리케이션입니다.

## 🚀 기능

- **10개 카테고리 평가**: 인기도, 기본 정보, 개발 활동성, 커뮤니티, 문서화, 코드 품질, 릴리스 관리, 의존성 관리, 에코시스템, 안전성
- **AI 활용도 분석**: AI/ML 라이브러리, 설정 파일, 모델 파일, 에이전트 프레임워크, 학습 스크립트, 노트북, 문서화
- **실시간 평가**: GitHub API를 활용한 실시간 데이터 분석
- **반응형 디자인**: 모바일/데스크톱 모두 대응

## 🛠️ 기술 스택

- **프론트엔드**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **백엔드**: Vercel Serverless Functions (Python)
- **API**: GitHub REST API v3

## 📦 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build
```

## 🚀 배포

```bash
# Vercel CLI로 배포
vercel

# 프로덕션 배포
vercel --prod
```

## 📁 프로젝트 구조

```
├── app/                    # Next.js 앱 디렉토리
│   ├── api/               # API 라우트
│   ├── globals.css        # 글로벌 스타일
│   ├── layout.tsx         # 메인 레이아웃
│   └── page.tsx           # 메인 페이지
├── components/            # React 컴포넌트
│   ├── RepoInput.tsx      # 레포지토리 입력
│   ├── EvaluationResult.tsx # 평가 결과
│   ├── ScoreCard.tsx      # 점수 카드
│   ├── CategoryCard.tsx   # 카테고리 카드
│   ├── AIUtilizationPanel.tsx # AI 활용도 패널
│   └── RecommendationPanel.tsx # 개선 제안
├── api/
│   └── evaluate.py        # Vercel 서버리스 함수
├── vercel.json            # Vercel 설정
└── package.json           # npm 설정
```

## 📊 평가 항목

### 10개 카테고리

| 카테고리 | 가중치 | 설명 |
|---------|--------|------|
| ⭐ 인기도 | 13.5% | Stars, Forks, Watchers |
| 📋 기본 정보 | 9% | 라이선스, 설명 |
| 🔥 개발 활동성 | 18% | 커밋, 이슈, PR |
| 👥 커뮤니티 | 13.5% | 기여자 수 |
| 📚 문서화 | 9% | README, CONTRIBUTING |
| 🔍 코드 품질 | 13.5% | CI/CD, 테스트, 린터 |
| 📦 릴리스 관리 | 4.5% | 릴리스 빈도, Semver |
| 📚 의존성 관리 | 4.5% | 잠금 파일, Dependabot |
| 🌍 에코시스템 | 2.7% | 언어, 태그 |
| 🛡️ 안전성 | 1.8% | 보안 정책 |

### AI 활용도 (8개 하위 항목)

1. AI/ML 라이브러리 사용
2. AI 설정 파일
3. AI 관련 태그
4. AI 모델 파일
5. AI 에이전트 프레임워크
6. 학습/추론 스크립트
7. 노트북/데이터셋
8. AI 문서화

## 📝 라이선스

MIT License
