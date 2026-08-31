'use client'

interface ScoreCardProps {
  category: {
    name: string
    score: number
    weight: number
  }
}

export default function ScoreCard({ category }: ScoreCardProps) {
  const { name, score, weight } = category

  // 점수별 색상
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-400'
    if (score >= 6) return 'text-yellow-400'
    if (score >= 4) return 'text-orange-400'
    return 'text-red-400'
  }

  // 프로그레스 바 색상
  const getBarColor = (score: number) => {
    if (score >= 8) return 'bg-green-500'
    if (score >= 6) return 'bg-yellow-500'
    if (score >= 4) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex justify-between items-start mb-3">
        <h4 className="text-sm font-medium text-gray-300">{name}</h4>
        <span className={`text-lg font-bold ${getScoreColor(score)}`}>
          {score.toFixed(1)}
        </span>
      </div>
      
      {/* 프로그레스 바 */}
      <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
        <div 
          className={`h-2 rounded-full ${getBarColor(score)} transition-all duration-500`}
          style={{ width: `${(score / 10) * 100}%` }}
        ></div>
      </div>
      
      <div className="flex justify-between text-xs text-gray-500">
        <span>가중치: {(weight * 100).toFixed(1)}%</span>
        <span>0-10</span>
      </div>
    </div>
  )
}
