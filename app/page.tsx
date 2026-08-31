'use client'

import { useState } from 'react'
import RepoInput from '@/components/RepoInput'
import EvaluationResult from '@/components/EvaluationResult'
import LoadingSpinner from '@/components/LoadingSpinner'

export default function Home() {
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleEvaluate = async (repoInput: string, token?: string) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      // URL에서 owner/repo 추출
      let repo = repoInput.trim()

      // GitHub URL 파싱
      const githubUrlMatch = repo.match(/github\.com\/([^/]+)\/([^/]+)/)
      if (githubUrlMatch) {
        repo = `${githubUrlMatch[1]}/${githubUrlMatch[2]}`
      }

      // owner/repo 형식 검증
      const parts = repo.split('/')
      if (parts.length !== 2 || !parts[0] || !parts[1]) {
        throw new Error('올바른 GitHub 레포지토리 URL을 입력해주세요.\n예: https://github.com/facebook/react')
      }

      const response = await fetch('/api/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo, token }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || '평가 중 오류가 발생했습니다.')
      }

      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* 헤더 */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            🔍 GitHub 레포지토리 평가
          </h1>
          <p className="text-gray-400 text-lg">
            GitHub 레포지토리를 다양한 기준으로 평가하고 AI 활용도를 분석합니다
          </p>
        </div>

        {/* 입력 폼 */}
        <RepoInput onEvaluate={handleEvaluate} loading={loading} />

        {/* 로딩 */}
        {loading && <LoadingSpinner />}

        {/* 에러 */}
        {error && (
          <div className="mt-8 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200">
            ❌ {error}
          </div>
        )}

        {/* 결과 */}
        {result && <EvaluationResult result={result} />}

        {/* 푸터 */}
        <footer className="mt-16 text-center text-gray-500 text-sm">
          <p>GitHub 레포지토리 평가 프로그램 v1.0</p>
          <p className="mt-2">
            평가 항목: 인기도, 기본 정보, 개발 활동성, 커뮤니티, 문서화, 코드 품질, 
            릴리스 관리, 의존성 관리, 에코시스템, 안전성, AI 활용도
          </p>
        </footer>
      </div>
    </main>
  )
}
