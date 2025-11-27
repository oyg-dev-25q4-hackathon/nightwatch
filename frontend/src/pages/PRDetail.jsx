import axios from "axios";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../components/Header";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5001";

function PRDetail() {
  const { subscriptionId, testId } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rerunningScenarios, setRerunningScenarios] = useState(new Set());
  const [regeneratingScenarios, setRegeneratingScenarios] = useState(false);
  const [expandedScenarios, setExpandedScenarios] = useState(new Set());

  useEffect(() => {
    fetchTestDetail();

    // running 또는 pending 상태일 때 주기적으로 상태 확인
    const interval = setInterval(() => {
      if (test && (test.status === "running" || test.status === "pending")) {
        fetchTestDetail();
      }
    }, 2000); // 2초마다 확인

    return () => {
      clearInterval(interval);
    };
  }, [testId, test?.status]);

  const fetchTestDetail = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/tests/${testId}`);
      if (response.data.success) {
        setTest(response.data.test);
      }
    } catch (error) {
      console.error("테스트 상세 조회 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      completed:
        "bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg",
      failed: "bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-lg",
      running:
        "bg-gradient-to-r from-yellow-400 to-orange-400 text-white shadow-lg animate-pulse",
      pending:
        "bg-gradient-to-r from-gray-400 to-gray-500 text-white shadow-lg",
    };
    const labels = {
      completed: "✅ 완료",
      failed: "❌ 실패",
      running: "🔄 실행 중",
      pending: "⏳ 대기",
    };

    // status가 없거나 undefined인 경우 기본값 처리
    const normalizedStatus = status ? status.toLowerCase() : "pending";

    return (
      <span
        className={`px-6 py-2.5 text-sm font-bold rounded-full whitespace-nowrap ${
          styles[normalizedStatus] || styles.pending
        }`}
      >
        {labels[normalizedStatus] || "⏳ 대기"}
      </span>
    );
  };

  const toggleScenario = (idx) => {
    setExpandedScenarios((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(idx)) {
        newSet.delete(idx);
      } else {
        newSet.add(idx);
      }
      return newSet;
    });
  };

  const renderTestResults = (results) => {
    if (!results)
      return <p className="text-gray-500">테스트 결과가 없습니다.</p>;

    if (typeof results === "string") {
      try {
        results = JSON.parse(results);
      } catch {
        return <pre className="whitespace-pre-wrap">{results}</pre>;
      }
    }

    if (Array.isArray(results)) {
      return (
        <div className="space-y-3">
          {results.map((scenario, idx) => {
            const isExpanded = expandedScenarios.has(idx);
            return (
              <div
                key={idx}
                className="border-2 border-gray-200 rounded-xl bg-white shadow-md hover:shadow-lg transition-all overflow-hidden"
              >
                {/* 드롭다운 헤더 */}
                <button
                  onClick={() => toggleScenario(idx)}
                  className="w-full p-6 flex items-center justify-between hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-2 text-white font-bold min-w-[40px] text-center">
                      {idx + 1}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-lg text-gray-900 mb-1">
                        시나리오 {idx + 1}
                      </h4>
                      {scenario.description && (
                        <p className="text-sm text-gray-600 line-clamp-1">
                          {scenario.description}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      {scenario.success !== undefined && (
                        <div
                          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg font-semibold text-sm ${
                            scenario.success
                              ? "bg-green-100 text-green-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          <span className="text-base">
                            {scenario.success ? "✅" : "❌"}
                          </span>
                          <span>{scenario.success ? "성공" : "실패"}</span>
                        </div>
                      )}
                      <div
                        className={`transform transition-transform duration-200 ${
                          isExpanded ? "rotate-180" : ""
                        }`}
                      >
                        <svg
                          className="w-6 h-6 text-gray-500"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </div>
                    </div>
                  </div>
                </button>

                {/* 드롭다운 내용 */}
                {isExpanded && (
                  <div className="px-6 pb-6 border-t border-gray-100 pt-4 space-y-4 animate-fadeIn">
                    {scenario.description && (
                      <div className="bg-blue-50 rounded-lg p-3 border-l-4 border-blue-500">
                        <p className="text-sm text-gray-700 font-medium">
                          {scenario.description}
                        </p>
                      </div>
                    )}
                    {scenario.actions && (
                      <div>
                        <p className="text-xs font-bold text-gray-700 mb-2 uppercase tracking-wide">
                          액션 목록
                        </p>
                        <div className="grid gap-2">
                          {scenario.actions.map((action, aidx) => (
                            <div
                              key={aidx}
                              className="bg-gray-50 rounded-lg p-3 flex items-center gap-2 border border-gray-200"
                            >
                              <span className="bg-blue-100 text-blue-700 rounded px-2 py-1 text-xs font-bold">
                                {action.type}
                              </span>
                              <span className="text-sm text-gray-700">
                                {action.selector || action.url || action.value}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {scenario.error && (
                      <div className="bg-red-50 border-l-4 border-red-500 rounded p-3">
                        <p className="text-sm text-red-700 font-medium">
                          오류: {scenario.error}
                        </p>
                      </div>
                    )}
                    <div className="flex justify-end pt-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRerunScenario(idx);
                        }}
                        disabled={rerunningScenarios.has(idx)}
                        className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                      >
                        {rerunningScenarios.has(idx) ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <span>재실행 중...</span>
                          </>
                        ) : (
                          <>
                            <span>🔄</span>
                            <span>재테스트</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      );
    }

    if (typeof results === "object") {
      return (
        <div className="space-y-2">
          {Object.entries(results).map(([key, value]) => (
            <div key={key} className="border-b pb-2">
              <p className="font-medium text-sm">{key}:</p>
              <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                {typeof value === "object"
                  ? JSON.stringify(value, null, 2)
                  : String(value)}
              </pre>
            </div>
          ))}
        </div>
      );
    }

    return (
      <pre className="whitespace-pre-wrap">
        {JSON.stringify(results, null, 2)}
      </pre>
    );
  };

  const handleRerunScenario = async (scenarioIndex) => {
    if (!confirm(`시나리오 ${scenarioIndex + 1}을 다시 실행하시겠습니까?`)) {
      return;
    }

    setRerunningScenarios((prev) => new Set(prev).add(scenarioIndex));

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/tests/${testId}/rerun-scenario`,
        { scenario_index: scenarioIndex }
      );

      if (response.data.success) {
        alert(`✅ 시나리오 ${scenarioIndex + 1} 재실행이 완료되었습니다!`);
        // 테스트 정보 새로고침
        fetchTestDetail();
      } else {
        alert(`❌ 재실행 실패: ${response.data.error}`);
      }
    } catch (error) {
      alert(`❌ 오류: ${error.response?.data?.error || error.message}`);
    } finally {
      setRerunningScenarios((prev) => {
        const newSet = new Set(prev);
        newSet.delete(scenarioIndex);
        return newSet;
      });
    }
  };

  const handleRegenerateScenarios = async () => {
    if (
      !confirm(
        "시나리오를 다시 생성하고 즉시 테스트를 재실행할까요?\n\n기존 결과는 새 실행 결과로 대체됩니다."
      )
    ) {
      return;
    }

    setRegeneratingScenarios(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/tests/${testId}/regenerate-scenarios`
      );

      if (response.data.success) {
        alert(
          `✅ ${
            response.data.message ||
            `${response.data.scenarios_count}개의 시나리오가 실행되었습니다!`
          }`
        );
        // 테스트 정보 새로고침
        fetchTestDetail();
      } else {
        alert(`❌ 시나리오 생성 실패: ${response.data.error}`);
      }
    } catch (error) {
      alert(`❌ 오류: ${error.response?.data?.error || error.message}`);
    } finally {
      setRegeneratingScenarios(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div
              className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"
              style={{ animationDelay: "0ms" }}
            ></div>
            <div
              className="w-3 h-3 bg-purple-600 rounded-full animate-bounce"
              style={{ animationDelay: "150ms" }}
            ></div>
            <div
              className="w-3 h-3 bg-pink-600 rounded-full animate-bounce"
              style={{ animationDelay: "300ms" }}
            ></div>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">NightWatch</h2>
          <p className="text-gray-600">테스트 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (!test) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-red-600">
            테스트 정보를 찾을 수 없습니다.
          </div>
        </div>
      </div>
    );
  }

  // running 또는 pending 상태일 때 로딩 화면 표시
  if (test.status === "running" || test.status === "pending") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
        <Header />
        <div className="max-w-7xl mx-auto p-8">
          <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
            <div className="flex items-center justify-center gap-3 mb-6">
              <div
                className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"
                style={{ animationDelay: "0ms" }}
              ></div>
              <div
                className="w-3 h-3 bg-purple-600 rounded-full animate-bounce"
                style={{ animationDelay: "150ms" }}
              ></div>
              <div
                className="w-3 h-3 bg-pink-600 rounded-full animate-bounce"
                style={{ animationDelay: "300ms" }}
              ></div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {test.status === "running"
                ? "🔄 AI 분석 진행 중..."
                : "⏳ 대기 중..."}
            </h2>
            <p className="text-gray-600 mb-2">
              PR #{test.pr_number}: {test.pr_title || "제목 없음"}
            </p>
            <p className="text-sm text-gray-500">
              {test.status === "running"
                ? "Gemini AI가 PR 변경사항을 분석하고 테스트 시나리오를 생성하고 있습니다."
                : "테스트 실행을 대기 중입니다."}
            </p>
            <p className="text-xs text-gray-400 mt-4">
              분석이 완료되면 자동으로 결과가 표시됩니다...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      <Header />
      <div className="max-w-7xl mx-auto p-8">
        {/* 헤더 */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/subscriptions/${subscriptionId}`)}
            className="mb-6 text-blue-600 hover:text-blue-800 flex items-center gap-2 font-medium transition-colors group"
          >
            <span className="group-hover:-translate-x-1 transition-transform">
              ←
            </span>
            <span>뒤로 가기</span>
          </button>
          <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl shadow-2xl p-8 text-white overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32"></div>
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full -ml-24 -mb-24"></div>
            <div className="relative z-10">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h1 className="text-4xl font-bold mb-2">
                    {test.pr_title || `PR #${test.pr_number}`}
                  </h1>
                  <p className="text-purple-100">Pull Request Test Details</p>
                </div>
                <div>{getStatusBadge(test.status)}</div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                {test.branch_name && (
                  <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                    <p className="text-purple-100 text-xs mb-1 font-medium">
                      브랜치
                    </p>
                    <p className="text-white font-semibold text-lg">
                      {test.branch_name}
                    </p>
                  </div>
                )}
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <p className="text-purple-100 text-xs mb-1 font-medium">
                    PR URL
                  </p>
                  <a
                    href={test.pr_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-white font-semibold hover:text-purple-200 transition-colors underline truncate block"
                  >
                    {test.pr_url}
                  </a>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 md:col-span-2">
                  <p className="text-purple-100 text-xs mb-1 font-medium">
                    배포 경로
                  </p>
                  <a
                    href="https://preview-dev.oliveyoung.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-white font-semibold text-lg hover:text-purple-200 transition-colors underline block"
                  >
                    https://preview-dev.oliveyoung.com
                  </a>
                  <p className="text-purple-100 text-xs mt-2">
                    💡 preview 브랜치의 모든 PR은 동일한 배포 경로로
                    테스트됩니다.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 테스트 결과 */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl p-3">
                <span className="text-2xl">📊</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">테스트 결과</h2>
            </div>
            <button
              onClick={handleRegenerateScenarios}
              disabled={regeneratingScenarios}
              className="px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl font-semibold hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transform hover:-translate-y-0.5"
            >
              {regeneratingScenarios ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>생성 중...</span>
                </>
              ) : (
                <>
                  <span className="text-xl">✨</span>
                  <span>시나리오 생성하기</span>
                </>
              )}
            </button>
          </div>
          <div className="border-2 border-gray-100 rounded-xl p-6 bg-gradient-to-br from-gray-50 to-blue-50">
            {renderTestResults(test.test_results)}
          </div>
        </div>

        {/* 리포트 다운로드 */}
        {test.report_path && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl p-3">
                <span className="text-2xl">📄</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">리포트</h2>
            </div>
            <a
              href={`${API_BASE_URL}/api/tests/${testId}/report`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              <span>📥</span>
              <span>리포트 다운로드</span>
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

export default PRDetail;
