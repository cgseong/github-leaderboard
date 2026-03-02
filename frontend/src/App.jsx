import { useState } from 'react';
import { Github, Search, CheckCircle, XCircle, AlertTriangle, Zap, BookOpen, Users, Activity, Loader2 } from 'lucide-react';

function App() {
  const [repo, setRepo] = useState('');
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // API 호출 함수
  const analyzeRepo = async () => {
    if (!repo) {
      setError('저장소 이름(owner/repo)을 입력해주세요.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // 로컬 FastAPI 백엔드 엔드포인트에 요청
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ repo, token: token || null }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '분석 중 오류가 발생했습니다.');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 아이콘 매퍼 (섹션 이름에 따라 아이콘 반환)
  const getSectionIcon = (name) => {
    const iconClass = "w-6 h-6 text-indigo-400";
    if (name.toLowerCase().includes('code')) return <Zap className={iconClass} />;
    if (name.toLowerCase().includes('doc')) return <BookOpen className={iconClass} />;
    if (name.toLowerCase().includes('collab')) return <Users className={iconClass} />;
    return <Activity className={iconClass} />;
  };

  return (
    <div className="min-h-screen bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black text-slate-100 p-6 md:p-12 font-sans selection:bg-indigo-500/30">

      {/* 최고 상단 헤더 영역 */}
      <header className="max-w-5xl mx-auto flex items-center gap-4 mb-12">
        <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
          <Github className="w-8 h-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
            GitHub Repo Evaluator
          </h1>
          <p className="text-slate-400 mt-1 font-medium text-sm md:text-base">
            리포지토리의 코드 품질, 활동성, 문서화, 협업 수준을 심층 분석합니다.
          </p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto space-y-8">
        {/* 검색 패널 (유리 질감) */}
        <section className="glass-panel p-6 md:p-8 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

          <div className="relative flex flex-col md:flex-row gap-4">
            <div className="flex-1 space-y-2">
              <label className="text-sm font-semibold text-slate-300 ml-1">저장소 (owner/repo 또는 URL)</label>
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="text"
                  className="w-full bg-slate-950/50 border border-slate-700/50 rounded-xl py-3 pl-12 pr-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                  placeholder="예: facebook/react"
                  value={repo}
                  onChange={(e) => setRepo(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && analyzeRepo()}
                />
              </div>
            </div>

            <div className="flex-1 space-y-2">
              <label className="text-sm font-semibold text-slate-300 ml-1">GitHub Token (선택 사항)</label>
              <input
                type="password"
                className="w-full bg-slate-950/50 border border-slate-700/50 rounded-xl py-3 px-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all gap-2"
                placeholder="ghp_xxxxxxxxxxxx"
                value={token}
                onChange={(e) => setToken(e.target.value)}
              />
            </div>

            <div className="flex items-end pb-1 md:pb-0">
              <button
                onClick={analyzeRepo}
                disabled={loading}
                className="w-full md:w-auto h-[46px] px-8 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg shadow-indigo-500/25 transition-all transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : '분석 시작'}
              </button>
            </div>
          </div>

          {error && (
            <div className="mt-6 flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
              <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <p className="text-sm leading-relaxed">{error}</p>
            </div>
          )}
        </section>

        {/* 결과 영역 */}
        {result && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">

            {/* 요약 스코어 카드 */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* 총점 */}
              <div className="glass-panel p-6 flex flex-col items-center justify-center text-center relative overflow-hidden group">
                <div className="absolute inset-0 bg-indigo-500/5 group-hover:bg-indigo-500/10 transition-colors" />
                <h3 className="text-slate-400 font-medium mb-2 relative z-10">총 평가 점수</h3>
                <div className="flex items-baseline gap-1 relative z-10">
                  <span className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-slate-400">
                    {result.total_score.toFixed(1)}
                  </span>
                  <span className="text-xl text-slate-500">/{result.max_score}</span>
                </div>
              </div>

              {/* 등급 */}
              <div className="glass-panel p-6 flex flex-col items-center justify-center text-center">
                <h3 className="text-slate-400 font-medium mb-2">종합 등급</h3>
                <span className={`text-6xl font-black drop-shadow-lg ${['A+', 'A', 'A-'].includes(result.grade) ? 'text-emerald-400' :
                  ['B+', 'B', 'B-'].includes(result.grade) ? 'text-blue-400' :
                    ['C+', 'C', 'C-'].includes(result.grade) ? 'text-amber-400' : 'text-red-400'
                  }`}>
                  {result.grade}
                </span>
              </div>

              {/* 결과 (Pass/Fail) */}
              <div className="glass-panel p-6 flex flex-col items-center justify-center text-center">
                <h3 className="text-slate-400 font-medium mb-3">최종 결과</h3>
                {result.pass_fail === 'PASS' ? (
                  <div className="flex items-center gap-2 px-6 py-3 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-400 font-bold text-2xl">
                    <CheckCircle className="w-8 h-8" /> PASS
                  </div>
                ) : (
                  <div className="flex items-center gap-2 px-6 py-3 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 font-bold text-2xl">
                    <XCircle className="w-8 h-8" /> FAIL
                  </div>
                )}
              </div>
            </section>

            {/* 섹션별 상세 점수 */}
            <section>
              <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
                <span className="w-1.5 h-6 bg-indigo-500 rounded-full inline-block" />
                섹션별 상세 점수
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {result.sections.map((sec, idx) => (
                  <div key={idx} className="glass-panel p-5 hover:border-indigo-500/30 transition-colors group">
                    <div className="flex items-center justify-between mb-4">
                      {getSectionIcon(sec.name)}
                      <span className="text-lg font-bold">
                        {sec.score.toFixed(1)} <span className="text-slate-500 font-medium text-sm">/ {sec.max_score}</span>
                      </span>
                    </div>
                    <h4 className="font-semibold text-slate-200 text-lg mb-2 capitalize">{sec.name.replace('_', ' ')}</h4>
                    <p className="text-slate-400 text-sm leading-relaxed">{sec.summary}</p>
                    {/* 프로그레스 바 */}
                    <div className="w-full h-1.5 bg-slate-800 rounded-full mt-4 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out"
                        style={{ width: `${(sec.score / sec.max_score) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* 경고 (Warnings) */}
            {result.warnings?.length > 0 && (
              <section className="glass-panel p-6 border-amber-500/20 bg-amber-500/5">
                <h3 className="text-lg font-bold text-amber-400 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  주의 / 개선 필요 사항
                </h3>
                <ul className="space-y-3">
                  {result.warnings.map((warn, idx) => (
                    <li key={idx} className="flex gap-3 text-slate-300 text-sm">
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-2 flex-shrink-0" />
                      {warn}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* 기여자 상세 (Contributors) */}
            {result.contributor_details?.length > 0 && (
              <section>
                <h2 className="text-2xl font-bold mb-6 mt-10 flex items-center gap-3">
                  <span className="w-1.5 h-6 bg-indigo-500 rounded-full inline-block" />
                  기여자 활동 상세
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {result.contributor_details.slice(0, 12).map((contributor, idx) => {
                    const maxContributions = result.contributor_details[0].C || 1;
                    const ratio = Math.min((contributor.C / maxContributions) * 100, 100);

                    return (
                      <div key={idx} className="glass-panel p-5 flex flex-col gap-4 hover:border-indigo-500/30 transition-all hover:-translate-y-1">
                        <div className="flex items-center gap-4">
                          <img
                            src={contributor.avatar_url || 'https://github.com/identicons/identicon.png'}
                            alt={contributor.login}
                            className="w-12 h-12 rounded-full border border-slate-700 bg-slate-800 flex-shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <a
                              href={contributor.html_url || `https://github.com/${contributor.login}`}
                              target="_blank"
                              rel="noreferrer"
                              className="font-bold text-slate-200 hover:text-indigo-400 transition-colors truncate block"
                              title={contributor.login}
                            >
                              {contributor.login}
                            </a>
                            <div className="w-full h-1.5 bg-slate-800/80 rounded-full overflow-hidden mt-2">
                              <div
                                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out"
                                style={{ width: `${ratio}%` }}
                              />
                            </div>
                          </div>
                        </div>

                        <div className="grid grid-cols-3 gap-2 text-center text-xs mt-2 border-t border-slate-700/50 pt-3">
                          <div className="flex flex-col bg-slate-900/50 p-1.5 rounded-lg border border-slate-800/50">
                            <span className="text-slate-400">커밋 (C)</span>
                            <span className="font-bold text-slate-200">{contributor.C}</span>
                          </div>
                          <div className="flex flex-col bg-slate-900/50 p-1.5 rounded-lg border border-slate-800/50">
                            <span className="text-slate-400">PR (Open)</span>
                            <span className="font-bold text-slate-200">{contributor.P_open}</span>
                          </div>
                          <div className="flex flex-col bg-slate-900/50 p-1.5 rounded-lg border border-slate-800/50">
                            <span className="text-slate-400">PR (Merged)</span>
                            <span className="font-bold text-emerald-400">{contributor.P_merged}</span>
                          </div>
                          <div className="flex flex-col bg-slate-900/50 p-1.5 rounded-lg border border-slate-800/50 mt-1">
                            <span className="text-slate-400">리뷰 (Total)</span>
                            <span className="font-bold text-slate-200">{contributor.R_total}</span>
                          </div>
                          <div className="flex flex-col bg-slate-900/50 p-1.5 rounded-lg border border-slate-800/50 mt-1">
                            <span className="text-slate-400">리뷰 (Approve)</span>
                            <span className="font-bold text-emerald-400">{contributor.R_approve}</span>
                          </div>
                          <div className="flex flex-col bg-slate-900/50 p-1.5 rounded-lg border border-slate-800/50 mt-1">
                            <span className="text-slate-400">리뷰 (Changes)</span>
                            <span className="font-bold text-amber-400">{contributor.R_changes}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                {result.contributor_details.length > 12 && (
                  <p className="text-sm text-slate-500 mt-4 text-center">
                    * 상위 12명의 기여자만 표시됩니다. (총 {result.contributor_details.length}명)
                  </p>
                )}
              </section>
            )}

            {/* 체크리스트 (로직 페이즈 기반) */}
            <section>
              <h2 className="text-2xl font-bold mb-6 mt-10 flex items-center gap-3">
                <span className="w-1.5 h-6 bg-indigo-500 rounded-full inline-block" />
                분석 체크리스트
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.entries(result.checklist).map(([phase, items], idx) => (
                  <div key={idx} className="glass-panel p-6">
                    <h3 className="font-bold text-slate-200 capitalize mb-4 text-emerald-400 border-b border-slate-700/50 pb-2">
                      {phase.replace('_', ' ')}
                    </h3>
                    <ul className="space-y-3">
                      {items.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                          <CheckCircle className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                          <span className="leading-snug">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>

          </div>
        )}
      </main>
    </div>
  );
}

export default App;
