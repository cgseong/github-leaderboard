'use client'

interface AIUtilizationPanelProps {
  data: {
    score: number
    grade: string
    level: string
    summary: string
    detected_packages: Record<string, string>
    detected_files: string[]
    detected_topics: string[]
  }
}

export default function AIUtilizationPanel({ data }: AIUtilizationPanelProps) {
  const { score, grade, level, summary, detected_packages, detected_files, detected_topics } = data

  // AI 수준별 색상
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'AI-Native': return 'from-purple-500 to-pink-600'
      case 'Advanced': return 'from-blue-500 to-cyan-600'
      case 'Moderate': return 'from-green-500 to-emerald-600'
      case 'Basic': return 'from-yellow-500 to-orange-600'
      case 'Minimal': return 'from-gray-500 to-gray-600'
      default: return 'from-gray-600 to-gray-700'
    }
  }

  // AI 수준별 이모지
  const getLevelEmoji = (level: string) => {
    switch (level) {
      case 'AI-Native': return '🤖'
      case 'Advanced': return '🚀'
      case 'Moderate': return '⚡'
      case 'Basic': return '🌱'
      case 'Minimal': return '🔬'
      default: return '❓'
    }
  }

  // 패키지 카테고리별 색상
  const getCategoryColor = (category: string) => {
    if (category.includes('Deep Learning')) return 'bg-purple-900/50 text-purple-300'
    if (category.includes('LLM') || category.includes('NLP')) return 'bg-blue-900/50 text-blue-300'
    if (category.includes('Computer Vision')) return 'bg-green-900/50 text-green-300'
    if (category.includes('Agent')) return 'bg-pink-900/50 text-pink-300'
    if (category.includes('MLOps')) return 'bg-cyan-900/50 text-cyan-300'
    return 'bg-gray-900/50 text-gray-300'
  }

  return (
    <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-6 border border-purple-700/50">
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl">🤖</span>
        <h3 className="text-xl font-bold text-white">AI 활용도</h3>
      </div>

      {/* AI 수준 헤더 */}
      <div className={`bg-gradient-to-r ${getLevelColor(level)} rounded-lg p-4 mb-4`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-3xl">{getLevelEmoji(level)}</span>
              <span className="text-2xl font-bold text-white">{level}</span>
            </div>
            <p className="text-white/80 mt-1">{summary}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-white">{score.toFixed(1)}</div>
            <div className="text-sm text-white/80">{grade}</div>
          </div>
        </div>
      </div>

      {/* 감지된 AI 관련 항목들 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 감지된 패키지 */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">📦 감지된 AI 패키지</h4>
          {Object.keys(detected_packages).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(detected_packages).slice(0, 5).map(([pkg, category]) => (
                <div key={pkg} className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${getCategoryColor(category)}`}>
                    {category}
                  </span>
                  <span className="text-sm text-gray-300">{pkg}</span>
                </div>
              ))}
              {Object.keys(detected_packages).length > 5 && (
                <p className="text-xs text-gray-500">
                  외 {Object.keys(detected_packages).length - 5}개
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">감지된 패키지 없음</p>
          )}
        </div>

        {/* 감지된 파일 */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">📄 감지된 AI 파일</h4>
          {detected_files.length > 0 ? (
            <div className="space-y-1">
              {detected_files.slice(0, 5).map((file, index) => (
                <div key={index} className="text-sm text-gray-300 truncate">
                  {file}
                </div>
              ))}
              {detected_files.length > 5 && (
                <p className="text-xs text-gray-500">
                  외 {detected_files.length - 5}개
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">감지된 파일 없음</p>
          )}
        </div>

        {/* 감지된 태그 */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">🏷️ AI 관련 태그</h4>
          {detected_topics.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {detected_topics.slice(0, 8).map((topic, index) => (
                <span 
                  key={index} 
                  className="px-2 py-1 bg-purple-900/50 text-purple-300 rounded text-xs"
                >
                  {topic}
                </span>
              ))}
              {detected_topics.length > 8 && (
                <span className="text-xs text-gray-500">
                  +{detected_topics.length - 8}개
                </span>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-500">감지된 태그 없음</p>
          )}
        </div>
      </div>
    </div>
  )
}
