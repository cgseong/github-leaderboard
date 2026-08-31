'use client'

interface RecommendationPanelProps {
  recommendations: string[]
}

export default function RecommendationPanel({ recommendations }: RecommendationPanelProps) {
  // 제안 유형별 이모지
  const getRecommendationEmoji = (recommendation: string) => {
    if (recommendation.includes('라이선스')) return '📜'
    if (recommendation.includes('문서화') || recommendation.includes('README')) return '📚'
    if (recommendation.includes('CI/CD') || recommendation.includes('테스트')) return '🔧'
    if (recommendation.includes('릴리스')) return '📦'
    if (recommendation.includes('의존성') || recommendation.includes('잠금')) return '🔒'
    if (recommendation.includes('기여자')) return '👥'
    if (recommendation.includes('활동')) return '🔥'
    if (recommendation.includes('AI')) return '🤖'
    return '💡'
  }

  return (
    <div className="bg-gradient-to-r from-blue-900/30 to-cyan-900/30 rounded-xl p-6 border border-blue-700/50">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">💡</span>
        <h3 className="text-xl font-bold text-white">개선 제안</h3>
      </div>

      <div className="space-y-3">
        {recommendations.map((recommendation, index) => (
          <div 
            key={index}
            className="flex items-start gap-3 bg-gray-800/50 rounded-lg p-3"
          >
            <span className="text-xl mt-0.5">{getRecommendationEmoji(recommendation)}</span>
            <p className="text-gray-300">{recommendation}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
