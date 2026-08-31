export default function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative">
        {/* 메인 스피너 */}
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        
        {/* 중앙 아이콘 */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl">🔍</span>
        </div>
      </div>
      
      <p className="mt-4 text-gray-400 text-lg">레포지토리를 분석하고 있습니다...</p>
      <p className="mt-2 text-gray-500 text-sm">GitHub API에서 데이터를 가져오는 중</p>
    </div>
  )
}
