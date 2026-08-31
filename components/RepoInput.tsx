'use client'

import { useState } from 'react'

interface RepoInputProps {
  onEvaluate: (repoPath: string, token?: string) => void
  loading: boolean
}

export default function RepoInput({ onEvaluate, loading }: RepoInputProps) {
  const [repoPath, setRepoPath] = useState('')
  const [token, setToken] = useState('')
  const [showToken, setShowToken] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (repoPath.trim()) {
      onEvaluate(repoPath.trim(), token.trim() || undefined)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 레포지토리 경로 입력 */}
        <div>
          <label htmlFor="repo" className="block text-sm font-medium text-gray-300 mb-2">
            GitHub 레포지토리 URL
          </label>
          <input
            type="text"
            id="repo"
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="예: https://github.com/facebook/react"
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
        </div>

        {/* 토큰 입력 (접이식) */}
        <div>
          <button
            type="button"
            onClick={() => setShowToken(!showToken)}
            className="text-sm text-gray-400 hover:text-gray-300 mb-2"
          >
            {showToken ? '▼ 토큰 숨기기' : '▶ GitHub 토큰 (선택사항)'}
          </button>
          
          {showToken && (
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="ghp_xxxx 또는 GITHUB_TOKEN 환경변수"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent mt-2"
              disabled={loading}
            />
          )}
        </div>

        {/* 제출 버튼 */}
        <button
          type="submit"
          disabled={loading || !repoPath.trim()}
          className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
        >
          {loading ? '평가 중...' : '평가 시작'}
        </button>
      </form>

      {/* 도움말 */}        <div className="mt-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
        <h3 className="text-sm font-medium text-gray-300 mb-2">💡 사용법</h3>
        <ul className="text-sm text-gray-400 space-y-1">
          <li>• GitHub 레포지토리 URL을 입력하세요 (예: https://github.com/facebook/react)</li>
          <li>• <code className="bg-gray-700 px-1 rounded">github.com/owner/repo</code> 형식도 가능합니다</li>
          <li>• 비공개 레포지토리는 GitHub 토큰이 필요합니다</li>
          <li>• 토큰 없이도 공개 레포지토리는 평가 가능 (rate limit 적용)</li>
        </ul>
      </div>
    </div>
  )
}
