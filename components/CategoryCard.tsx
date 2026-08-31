'use client'

import { useState } from 'react'

interface CategoryCardProps {
  category: {
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
  }
}

export default function CategoryCard({ category }: CategoryCardProps) {
  const [expanded, setExpanded] = useState(false)
  const { name, score, items } = category

  // 점수별 색상
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-400'
    if (score >= 6) return 'text-yellow-400'
    if (score >= 4) return 'text-orange-400'
    return 'text-red-400'
  }

  // 점수별 배경색
  const getScoreBg = (score: number) => {
    if (score >= 8) return 'bg-green-900/30'
    if (score >= 6) return 'bg-yellow-900/30'
    if (score >= 4) return 'bg-orange-900/30'
    return 'bg-red-900/30'
  }

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      {/* 헤더 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-750 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className={`text-lg font-bold ${getScoreColor(score)}`}>
            {score.toFixed(1)}/10
          </span>
          <span className="text-white font-medium">{name}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">{items.length}개 항목</span>
          <span className={`transform transition-transform ${expanded ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </div>
      </button>

      {/* 상세 내용 */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {items.map((item, index) => (
            <div 
              key={index} 
              className={`rounded-lg p-3 ${getScoreBg(item.score)}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-white">{item.name}</span>
                <span className={`font-bold ${getScoreColor(item.score)}`}>
                  {item.score}/{item.max_score}
                </span>
              </div>
              
              <p className="text-sm text-gray-300 mb-2">{item.details}</p>
              
              {item.sub_items.length > 0 && (
                <div className="space-y-1">
                  {item.sub_items.map((subItem, subIndex) => (
                    <div key={subIndex} className="text-xs text-gray-400 flex items-start gap-2">
                      <span className="text-gray-500">•</span>
                      <span>{subItem}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
