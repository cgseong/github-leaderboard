'use client'

import ScoreCard from './ScoreCard'
import CategoryCard from './CategoryCard'
import AIUtilizationPanel from './AIUtilizationPanel'
import RecommendationPanel from './RecommendationPanel'

interface EvaluationResultProps {
  result: {
    repo: string
    total_score: number
    grade: string
    metadata: {
      stars: number
      forks: number
      language: string | null
      license: string | null
      created_at: string
      updated_at: string
      size_kb: number
      open_issues: number
      topics: string[]
    }
    categories: Array<{
      name: string
      score: number
      weight: number
      items: Array<{
        name: string
        score: number
        max_score: number
        details: string
        sub_items: string[]
      }>
    }>
    ai_utilization?: {
      score: number
      grade: string
      level: string
      summary: string
      detected_packages: Record<string, string>
      detected_files: string[]
      detected_topics: string[]
    }
    recommendations: string[]
  }
}

export default function EvaluationResult({ result }: EvaluationResultProps) {
  const { repo, total_score, grade, metadata, categories, ai_utilization, recommendations } = result

  // 등급별 색상
  const gradeColors: Record<string, string> = {
    'A+': 'from-green-500 to-emerald-600',
    'A': 'from-green-400 to-green-600',
    'B+': 'from-yellow-400 to-yellow-600',
    'B': 'from-yellow-300 to-orange-400',
    'C+': 'from-orange-400 to-orange-600',
    'C': 'from-orange-300 to-red-400',
    'D': 'from-red-400 to-red-600',
    'F': 'from-red-500 to-red-700',
  }

  const gradeEmoji: Record<string, string> = {
    'A+': '🏆',
    'A': '🥇',
    'B+': '🥈',
    'B': '🥉',
    'C+': '⭐',
    'C': '📌',
    'D': '⚠️',
    'F': '❌',
  }

  return (
    <div className="mt-8 space-y-8">
      {/* 헤더 카드 */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white">{repo}</h2>
            <p className="text-gray-400 mt-1">
              {metadata.language || 'N/A'} • 
              {metadata.license ? ` ${metadata.license}` : ' 라이선스 없음'} • 
              {metadata.topics.length > 0 ? ` ${metadata.topics.slice(0, 3).join(', ')}` : ''}
            </p>
          </div>
          
          {/* 총점 */}
          <div className={`bg-gradient-to-r ${gradeColors[grade] || 'from-gray-500 to-gray-600'} rounded-xl p-4 text-center min-w-[120px]`}>
            <div className="text-3xl mb-1">{gradeEmoji[grade] || '❓'}</div>
            <div className="text-2xl font-bold text-white">{total_score}/10</div>
            <div className="text-sm text-white/80">{grade}</div>
          </div>
        </div>

        {/* 메타데이터 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-gray-700/50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-yellow-400">⭐ {metadata.stars.toLocaleString()}</div>
            <div className="text-xs text-gray-400">Stars</div>
          </div>
          <div className="bg-gray-700/50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-400">🍴 {metadata.forks.toLocaleString()}</div>
            <div className="text-xs text-gray-400">Forks</div>
          </div>
          <div className="bg-gray-700/50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-400">📅 {metadata.created_at.slice(0, 10)}</div>
            <div className="text-xs text-gray-400">생성일</div>
          </div>
          <div className="bg-gray-700/50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-purple-400">📁 {(metadata.size_kb / 1024).toFixed(1)} MB</div>
            <div className="text-xs text-gray-400">크기</div>
          </div>
        </div>
      </div>

      {/* 카테고리별 점수 */}
      <div>
        <h3 className="text-xl font-bold text-white mb-4">📊 카테고리별 점수</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map((category, index) => (
            <ScoreCard key={index} category={category} />
          ))}
        </div>
      </div>

      {/* AI 활용도 패널 */}
      {ai_utilization && <AIUtilizationPanel data={ai_utilization} />}

      {/* 상세 평가 */}
      <div>
        <h3 className="text-xl font-bold text-white mb-4">📝 상세 평가</h3>
        <div className="space-y-4">
          {categories.map((category, index) => (
            <CategoryCard key={index} category={category} />
          ))}
        </div>
      </div>

      {/* 개선 제안 */}
      {recommendations.length > 0 && <RecommendationPanel recommendations={recommendations} />}
    </div>
  )
}
