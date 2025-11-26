import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5001";

function PRDetail() {
  const { subscriptionId, testId } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTestDetail();
  }, [testId]);

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
      completed: "bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg",
      failed: "bg-gradient-to-r from-red-500 to-rose-500 text-white shadow-lg",
      running: "bg-gradient-to-r from-yellow-400 to-orange-400 text-white shadow-lg animate-pulse",
      pending: "bg-gradient-to-r from-gray-400 to-gray-500 text-white shadow-lg",
    };
    const labels = {
      completed: "✅ 완료",
      failed: "❌ 실패",
      running: "🔄 실행 중",
      pending: "⏳ 대기",
    };
    return (
      <span
        className={`px-6 py-2 text-sm font-bold rounded-full ${styles[status] || styles.pending}`}
      >
        {labels[status] || "⏳ 대기"}
      </span>
    );
  };

  const renderTestResults = (results) => {
    if (!results) return <p className="text-gray-500">테스트 결과가 없습니다.</p>;

    if (typeof results === "string") {
      try {
        results = JSON.parse(results);
      } catch {
        return <pre className="whitespace-pre-wrap">{results}</pre>;
      }
    }

    if (Array.isArray(results)) {
      return (
        <div className="space-y-4">
          {results.map((scenario, idx) => (
            <div
              key={idx}
              className="border-2 border-gray-200 rounded-xl p-6 bg-white shadow-md hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg p-2 text-white font-bold">
                  {idx + 1}
                </div>
                <h4 className="font-bold text-lg text-gray-900">시나리오 {idx + 1}</h4>
              </div>
              {scenario.description && (
                <div className="bg-blue-50 rounded-lg p-3 mb-4 border-l-4 border-blue-500">
                  <p className="text-sm text-gray-700 font-medium">{scenario.description}</p>
                </div>
              )}
              {scenario.actions && (
                <div className="mb-4">
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
              <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-200">
                {scenario.success !== undefined && (
                  <div
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold ${
                      scenario.success
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    <span className="text-lg">{scenario.success ? "✅" : "❌"}</span>
                    <span>{scenario.success ? "성공" : "실패"}</span>
                  </div>
                )}
                {scenario.error && (
                  <div className="flex-1 bg-red-50 border-l-4 border-red-500 rounded p-3">
                    <p className="text-sm text-red-700 font-medium">오류: {scenario.error}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
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
                {typeof value === "object" ? JSON.stringify(value, null, 2) : String(value)}
              </pre>
            </div>
          ))}
        </div>
      );
    }

    return <pre className="whitespace-pre-wrap">{JSON.stringify(results, null, 2)}</pre>;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">로딩 중...</div>
        </div>
      </div>
    );
  }

  if (!test) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-red-600">테스트 정보를 찾을 수 없습니다.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/subscriptions/${subscriptionId}`)}
            className="mb-6 text-blue-600 hover:text-blue-800 flex items-center gap-2 font-medium transition-colors group"
          >
            <span className="group-hover:-translate-x-1 transition-transform">←</span>
            <span>뒤로 가기</span>
          </button>
          <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl shadow-2xl p-8 text-white overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32"></div>
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full -ml-24 -mb-24"></div>
            <div className="relative z-10">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-4 shadow-lg">
                    <span className="text-4xl">🔍</span>
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold mb-2">
                      PR #{test.pr_number}
                    </h1>
                    <p className="text-purple-100">Pull Request Test Details</p>
                  </div>
                </div>
                <div className="transform scale-110">
                  {getStatusBadge(test.status)}
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <p className="text-purple-100 text-xs mb-1 font-medium">저장소</p>
                  <p className="text-white font-semibold text-lg">{test.repo_full_name}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <p className="text-purple-100 text-xs mb-1 font-medium">생성일</p>
                  <p className="text-white font-semibold">
                    {new Date(test.created_at).toLocaleString("ko-KR")}
                  </p>
                </div>
                {test.completed_at && (
                  <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                    <p className="text-purple-100 text-xs mb-1 font-medium">완료일</p>
                    <p className="text-white font-semibold">
                      {new Date(test.completed_at).toLocaleString("ko-KR")}
                    </p>
                  </div>
                )}
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
                  <p className="text-purple-100 text-xs mb-1 font-medium">PR URL</p>
                  <a
                    href={test.pr_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-white font-semibold hover:text-purple-200 transition-colors underline truncate block"
                  >
                    {test.pr_url}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 테스트 결과 */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl p-3">
              <span className="text-2xl">📊</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">테스트 결과</h2>
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

