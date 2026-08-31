import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { repo, token } = body

    // GitHub API로 직접 평가 수행 (Python 대신 TypeScript로 처리)
    const GITHUB_API = 'https://api.github.com'

    const headers: Record<string, string> = {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'GitHub-Repo-Evaluator/1.0',
    }
    if (token) {
      headers['Authorization'] = `token ${token}`
    }

    const ghGet = async (endpoint: string) => {
      const resp = await fetch(`${GITHUB_API}${endpoint}`, { headers })
      if (resp.status === 404) return null
      if (resp.status === 403) return { error: 'rate_limit' }
      if (!resp.ok) return null
      return resp.json()
    }

    // URL에서 owner/repo 추출
    let repoPath = repo.trim()
    const urlMatch = repoPath.match(/github\.com\/([^/]+)\/([^/]+)/)
    if (urlMatch) {
      repoPath = `${urlMatch[1]}/${urlMatch[2]}`
    }

    const parts = repoPath.replace(/^\//, '').replace(/\/$/, '').split('/')
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      return NextResponse.json({ error: '올바른 형식: owner/repo 또는 GitHub URL' }, { status: 400 })
    }

    const [owner, repoName] = parts

    // 레포지토리 기본 정보
    const repoData = await ghGet(`/repos/${owner}/${repoName}`)
    if (!repoData || (repoData as any).error) {
      return NextResponse.json(
        { error: `레포지토리 '${owner}/${repoName}'를 찾을 수 없습니다.` },
        { status: 404 }
      )
    }

    const r = repoData as any

    // 병렬로 데이터 수집
    const now = new Date()
    const since = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString()

    const [commits, issues, pulls, contributors, languages, treeData, releases, workflows] = await Promise.all([
      ghGet(`/repos/${owner}/${repoName}/commits?since=${since}&per_page=100`) as Promise<any[]>,
      ghGet(`/repos/${owner}/${repoName}/issues?since=${since}&state=all&per_page=100`) as Promise<any[]>,
      ghGet(`/repos/${owner}/${repoName}/pulls?state=all&sort=updated&direction=desc&per_page=100`) as Promise<any[]>,
      ghGet(`/repos/${owner}/${repoName}/contributors?per_page=100`) as Promise<any[]>,
      ghGet(`/repos/${owner}/${repoName}/languages`) as Promise<Record<string, number>>,
      ghGet(`/repos/${owner}/${repoName}/git/trees/HEAD?recursive=1`) as Promise<any>,
      ghGet(`/repos/${owner}/${repoName}/releases?per_page=100`) as Promise<any[]>,
      ghGet(`/repos/${owner}/${repoName}/actions/workflows?per_page=100`) as Promise<any>,
    ])

    const commitList = Array.isArray(commits) ? commits : []
    const issueList = Array.isArray(issues) ? issues : []
    const pullList = Array.isArray(pulls) ? pulls : []
    const contributorList = Array.isArray(contributors) ? contributors : []
    const langMap = (languages && typeof languages === 'object' && !('error' in languages)) ? languages : {}
    const tree: any[] = treeData?.tree || []
    const releaseList = Array.isArray(releases) ? releases : []
    const wfList = workflows?.workflows || []
    const fileBlobs = tree.filter((t: any) => t.type === 'blob')
    const filePaths = fileBlobs.map((t: any) => t.path)
    const fileNames = filePaths.map((p: string) => p.split('/').pop()?.toLowerCase() || '')
    const dirNames = new Set(filePaths.filter((p: string) => p.includes('/')).map((p: string) => p.split('/')[0].toLowerCase()))

    // ── 점수 계산 ──
    const log10 = Math.log10

    // 인기도
    const stars = r.stargazers_count || 0
    const forks = r.forks_count || 0
    const watchers = r.watchers_count || 0
    const starScore = Math.min(10, log10(stars + 1) * 1.67)
    const forkScore = Math.min(10, log10(forks + 1) * 2.0)
    const watcherScore = Math.min(10, log10(watchers + 1) * 2.5)
    const popularityScore = +(starScore * 0.5 + forkScore * 0.3 + watcherScore * 0.2).toFixed(1)

    // 라이선스
    const lic = r.license
    const licenseScore = (lic?.spdx_id && lic.spdx_id !== 'NOASSERTION') ? 10.0 : 0.0

    // 설명
    const desc = r.description || ''
    const homepage = r.homepage || ''
    let descScore = (desc.length > 10) ? 4.0 : (desc.length > 0 ? 2.0 : 0.0)
    if (homepage) descScore += 2.0
    descScore = Math.min(10, descScore)

    // 개발 활동성
    const recent30 = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
    const commits30 = commitList.filter((c: any) => {
      const d = c.commit?.author?.date
      return d && new Date(d) > recent30
    }).length
    const issuesOpened = issueList.filter((i: any) => !i.pull_request).length
    const issuesClosed = issueList.filter((i: any) => !i.pull_request && i.state === 'closed').length
    const prMerged = pullList.filter((p: any) => p.merged_at).length
    const commitScore2 = Math.min(10, commits30 * 0.5)
    const issueScore2 = Math.min(10, issuesOpened * 0.3 + issuesClosed * 0.5)
    const prScore2 = Math.min(10, pullList.length * 0.3 + prMerged * 0.5)
    const activityScore = +(commitScore2 * 0.5 + issueScore2 * 0.2 + prScore2 * 0.3).toFixed(1)

    // 커뮤니티
    const total = contributorList.length
    const contributorScore = Math.min(10, log10(total + 1) * 2.0)
    const communityScore = +(total > 100 ? Math.min(10, contributorScore + 1) : contributorScore).toFixed(1)

    // 문서화
    let docScore = 0.0
    if (fileNames.some(f => f.startsWith('readme'))) docScore += 2.5
    if (fileNames.some(f => f === 'contributing.md')) docScore += 1.5
    if (fileNames.some(f => f.includes('code_of_conduct'))) docScore += 1.0
    if (['docs', 'doc', 'documentation'].some(d => dirNames.has(d))) docScore += 2.0
    if (['examples', 'example', 'samples'].some(d => dirNames.has(d))) docScore += 1.0
    docScore = Math.min(10, docScore)

    // 코드 품질
    let qualityScore = 0.0
    if (wfList.length > 0) qualityScore += 2.5
    const linting = fileNames.some(f => ['eslint', '.prettierrc', '.flake8', 'ruff', '.editorconfig'].some(l => f.includes(l)))
    if (linting) qualityScore += 1.5
    if (fileNames.some(f => ['tsconfig.json', 'mypy.ini', 'py.typed'].includes(f))) qualityScore += 1.0
    const testPatterns = ['test', 'spec', '__tests__', 'tests']
    if (fileNames.some(f => testPatterns.some(tp => f.includes(tp))) || Array.from(dirNames).some(d => testPatterns.some(tp => d.includes(tp)))) qualityScore += 2.0
    qualityScore = Math.min(10, qualityScore)

    // 릴리스 관리
    let releaseScore = 0.0
    if (releaseList.length > 0) {
      releaseScore += 3.0
      for (const rel of releaseList.slice(0, 5)) {
        if (rel.published_at) {
          const daysAgo = Math.floor((now.getTime() - new Date(rel.published_at).getTime()) / 86400000)
          if (daysAgo < 30) { releaseScore += 2.0; break }
          if (daysAgo < 90) { releaseScore += 1.0; break }
        }
      }
      if (releaseList.some((r: any) => r.tag_name && /^\d+\.\d+\.\d+/.test(r.tag_name))) releaseScore += 2.0
    }
    releaseScore = Math.min(10, releaseScore)

    // 의존성 관리
    let depsScore = 0.0
    const lockFiles = ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'go.sum', 'Cargo.lock']
    if (fileNames.some(f => lockFiles.includes(f))) depsScore += 3.0
    if (filePaths.some(p => p.toLowerCase().includes('dependabot'))) depsScore += 2.5
    depsScore = Math.min(10, depsScore)

    // 에코시스템
    let ecoScore = 3.0
    if (Object.keys(langMap).length > 3) ecoScore += 1.0
    const topics = r.topics || []
    if (topics.length > 0) ecoScore += Math.min(3.0, topics.length * 0.5)
    if (r.homepage) ecoScore += 1.0
    ecoScore = Math.min(10, ecoScore)

    // 안전성
    let safetyScore = 0.0
    if (!r.fork) safetyScore += 2.0
    if (!r.archived) safetyScore += 2.0
    if (['main', 'master'].includes(r.default_branch)) safetyScore += 1.0
    if (filePaths.some(p => p.toLowerCase().includes('security'))) safetyScore += 2.0
    safetyScore = Math.min(10, Math.max(0, safetyScore))

    // AI 활용도
    const AI_TOPICS = new Set(['ai', 'artificial-intelligence', 'machine-learning', 'deep-learning', 'neural-network', 'nlp', 'llm', 'large-language-model', 'transformer', 'pytorch', 'tensorflow', 'generative-ai', 'reinforcement-learning', 'computer-vision', 'mlops'])
    const AI_CONFIG = { '.github/copilot-instructions.md': 'GitHub Copilot', '.cursorrules': 'Cursor AI', '.aider.conf.yml': 'Aider', '.clinerules': 'Cline', '.windsurfrules': 'Windsurf', 'CLAUDE.md': 'Claude', 'claude.md': 'Claude', '.claude': 'Claude', 'codex.md': 'Codex', '.codex': 'Codex', 'GEMINI.md': 'Gemini', 'gemini.md': 'Gemini', '.gemini': 'Gemini' }
    const AI_MODEL_RE = /\.(pt|pth|onnx|h5|pb|tflite|safetensors|gguf|ggml|ckpt)$/
    const AI_TRAIN_RE = /(train(?:ing)?|finetune|fine[-_]tune|evaluate|eval|infer(?:ence)?|predict)\.py$/

    let aiConfigScore = 0, aiModelScore = 0, aiTopicScore = 0, aiScriptScore = 0
    const aiFiles: string[] = []
    const aiTopicsList: string[] = []

    for (const p of filePaths) {
      for (const [pattern, tool] of Object.entries(AI_CONFIG)) {
        if (p.includes(pattern)) { aiConfigScore += 3; aiFiles.push(p) }
      }
      if (AI_MODEL_RE.test(p)) { aiModelScore += 1; aiFiles.push(p) }
      if (AI_TRAIN_RE.test(p)) { aiScriptScore += 1.5; aiFiles.push(p) }
    }
    for (const t of topics) {
      if (AI_TOPICS.has(t.toLowerCase())) { aiTopicScore += 2; aiTopicsList.push(t) }
    }
    const aiTotal = Math.min(10, (aiConfigScore + aiModelScore + aiTopicScore + aiScriptScore) / 5)
    let aiLevel = 'None', aiGrade = 'N/A'
    if (aiTotal >= 8) { aiLevel = 'AI-Native'; aiGrade = 'A+' }
    else if (aiTotal >= 6) { aiLevel = 'Advanced'; aiGrade = 'A' }
    else if (aiTotal >= 4) { aiLevel = 'Moderate'; aiGrade = 'B+' }
    else if (aiTotal >= 2) { aiLevel = 'Basic'; aiGrade = 'B' }
    else if (aiTotal >= 1) { aiLevel = 'Minimal'; aiGrade = 'C' }

    // 카테고리 구성
    const categories = [
      { name: '⭐ 인기도', weight: 0.135, score: popularityScore, items: [{ name: '인기도 (Popularity)', score: popularityScore, max_score: 10, details: `⭐ ${stars.toLocaleString()} stars · 🍴 ${forks.toLocaleString()} forks`, sub_items: [] }] },
      { name: '📋 기본 정보', weight: 0.09, score: +((licenseScore + descScore) / 2).toFixed(1), items: [
        { name: '라이선스 (License)', score: licenseScore, max_score: 10, details: lic?.spdx_id ? `✅ ${lic.spdx_id}` : '❌ 라이선스 없음', sub_items: [] },
        { name: '프로젝트 설명', score: descScore, max_score: 10, details: desc ? `"${desc.slice(0, 80)}"` : '설명 없음', sub_items: [] },
      ]},
      { name: '🔥 개발 활동성', weight: 0.18, score: activityScore, items: [{ name: '개발 활동성', score: activityScore, max_score: 10, details: `커밋: ${commits30}/30일, 이슈: ${issuesOpened}/${issuesClosed}, PR: ${prMerged}`, sub_items: [] }] },
      { name: '👥 커뮤니티', weight: 0.135, score: communityScore, items: [{ name: '커뮤니티', score: communityScore, max_score: 10, details: `총 ${total}명 기여자`, sub_items: [] }] },
      { name: '📚 문서화', weight: 0.09, score: docScore, items: [{ name: '문서화', score: docScore, max_score: 10, details: `점수: ${docScore}/10`, sub_items: [] }] },
      { name: '🔍 코드 품질', weight: 0.135, score: qualityScore, items: [{ name: '코드 품질', score: qualityScore, max_score: 10, details: `CI/CD: ${wfList.length}개`, sub_items: [] }] },
      { name: '📦 릴리스 관리', weight: 0.045, score: releaseScore, items: [{ name: '릴리스 관리', score: releaseScore, max_score: 10, details: `릴리스 ${releaseList.length}개`, sub_items: [] }] },
      { name: '📚 의존성 관리', weight: 0.045, score: depsScore, items: [{ name: '의존성 관리', score: depsScore, max_score: 10, details: `점수: ${depsScore}/10`, sub_items: [] }] },
      { name: '🌍 에코시스템', weight: 0.027, score: ecoScore, items: [{ name: '에코시스템', score: ecoScore, max_score: 10, details: `언어: ${Object.keys(langMap).length}개`, sub_items: [] }] },
      { name: '🛡️ 안전성', weight: 0.018, score: safetyScore, items: [{ name: '안전성', score: safetyScore, max_score: 10, details: `점수: ${safetyScore}/10`, sub_items: [] }] },
      { name: '🤖 AI 활용도', weight: 0.1, score: aiTotal, items: [] },
    ]

    // 총점
    let totalWeighted = 0, totalWeight = 0
    for (const cat of categories) {
      totalWeighted += cat.score * cat.weight
      totalWeight += cat.weight
    }
    const totalScore = +(totalWeighted / totalWeight).toFixed(1) || 0

    let grade = 'F'
    if (totalScore >= 9) grade = 'A+'
    else if (totalScore >= 8) grade = 'A'
    else if (totalScore >= 7) grade = 'B+'
    else if (totalScore >= 6) grade = 'B'
    else if (totalScore >= 5) grade = 'C+'
    else if (totalScore >= 4) grade = 'C'
    else if (totalScore >= 3) grade = 'D'

    // 개선 제안
    const recommendations: string[] = []
    if (licenseScore < 4) recommendations.push('라이선스를 추가하세요.')
    if (docScore < 4) recommendations.push('README.md와 문서화를 개선하세요.')
    if (qualityScore < 4) recommendations.push('CI/CD와 테스트를 추가하세요.')
    if (activityScore < 4) recommendations.push('개발 활동을 늘리세요.')
    if (aiTotal < 2) recommendations.push('AI 관련 라이브러리와 설정을 검토하세요.')
    if (recommendations.length === 0) recommendations.push('전반적으로 우수한 레포지토리입니다! 🎉')

    return NextResponse.json({
      repo: `${owner}/${repoName}`,
      total_score: totalScore,
      grade,
      categories,
      ai_utilization: {
        score: aiTotal,
        grade: aiGrade,
        level: aiLevel,
        summary: `AI 활용 수준: ${aiLevel} (${aiTotal}/10)`,
        detected_packages: {},
        detected_files: Array.from(new Set(aiFiles)).slice(0, 10),
        detected_topics: aiTopicsList,
      },
      recommendations: recommendations.slice(0, 5),
      metadata: {
        stars,
        forks,
        language: r.language,
        license: lic?.spdx_id || null,
        created_at: r.created_at,
        updated_at: r.updated_at,
        size_kb: r.size || 0,
        open_issues: r.open_issues_count || 0,
        topics,
      },
    })
  } catch (err: any) {
    return NextResponse.json(
      { error: err?.message || '평가 중 오류가 발생했습니다.' },
      { status: 500 }
    )
  }
}
