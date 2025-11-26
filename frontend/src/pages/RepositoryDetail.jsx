import axios from "axios";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../components/Header";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5001";

function RepositoryDetail() {
  const { subscriptionId } = useParams();
  const navigate = useNavigate();
  const [subscription, setSubscription] = useState(null);
  const [prs, setPrs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showPATModal, setShowPATModal] = useState(false);
  const [patInput, setPatInput] = useState("");
  const [updatingPAT, setUpdatingPAT] = useState(false);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    fetchSubscription();
    fetchPRs();
  }, [subscriptionId]);

  const fetchSubscription = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/subscriptions/${subscriptionId}`,
        {
          params: { user_id: "user123" },
        }
      );
      if (response.data.success) {
        setSubscription(response.data.subscription);
      }
    } catch (error) {
      console.error("구독 정보 조회 실패:", error);
    }
  };

  const fetchPRs = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/tests`, {
        params: {
          user_id: "user123",
          subscription_id: subscriptionId,
          limit: 100,
        },
      });
      if (response.data.success) {
        // PR 번호별로 그룹화 (같은 PR의 여러 테스트 중 최신 것만)
        const prMap = new Map();
        response.data.tests.forEach((test) => {
          const key = test.pr_number;
          if (
            !prMap.has(key) ||
            new Date(test.created_at) > new Date(prMap.get(key).created_at)
          ) {
            prMap.set(key, test);
          }
        });
        setPrs(
          Array.from(prMap.values()).sort((a, b) => b.pr_number - a.pr_number)
        );
      }
    } catch (error) {
      console.error("PR 목록 조회 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  const triggerPolling = async () => {
    try {
      setPolling(true);
      const response = await axios.post(
        `${API_BASE_URL}/api/subscriptions/${subscriptionId}/poll`,
        {},
        {
          params: { user_id: "user123" },
        }
      );

      if (response.data.success) {
        const detectedCount = response.data.detected_prs || 0;
        const prList = response.data.pr_list || [];

        if (detectedCount > 0) {
          // 감지된 PR 목록을 상세하게 표시
          let prListMessage = `✅ PR 감지가 완료되었습니다!\n\n${detectedCount}개의 PR이 감지되어 테스트가 시작되었습니다.\n\n`;
          prList.forEach((pr, index) => {
            prListMessage += `${index + 1}. PR #${pr.number}: ${
              pr.title
            }\n   브랜치: ${pr.branch}\n   URL: ${pr.url}\n\n`;
          });
          alert(prListMessage);
        } else {
          alert("✅ PR 감지가 완료되었습니다!\n\n새로운 PR이 없습니다.");
        }
        // PR 목록 즉시 새로고침
        fetchPRs();
        // DB 커밋 대기 후 다시 새로고침 (2초, 4초 후)
        setTimeout(() => {
          fetchPRs();
        }, 2000);
        setTimeout(() => {
          fetchPRs();
        }, 4000);
      } else {
        const errorData = response.data || {};
        if (errorData.error_type === "rate_limit") {
          const addPAT = confirm(
            `⚠️ GitHub API Rate Limit 초과\n\n${errorData.error}\n\n💡 해결 방법: Personal Access Token (PAT)을 추가하면 rate limit이 60회/시간에서 5,000회/시간으로 증가합니다.\n\n지금 PAT를 추가하시겠습니까?`
          );
          if (addPAT) {
            setShowPATModal(true);
          }
        } else {
          alert(`오류: ${response.data.error}`);
        }
      }
    } catch (error) {
      const errorData = error.response?.data || {};
      if (
        errorData.error_type === "rate_limit" ||
        error.response?.status === 429
      ) {
        const addPAT = confirm(
          `⚠️ GitHub API Rate Limit 초과\n\n${
            errorData.error || error.message
          }\n\n💡 해결 방법: Personal Access Token (PAT)을 추가하면 rate limit이 60회/시간에서 5,000회/시간으로 증가합니다.\n\n지금 PAT를 추가하시겠습니까?`
        );
        if (addPAT) {
          setShowPATModal(true);
        }
      } else {
        alert(`오류: ${error.response?.data?.error || error.message}`);
      }
    } finally {
      setPolling(false);
    }
  };

  const updatePAT = async () => {
    if (!patInput.trim()) {
      alert("PAT를 입력해주세요.");
      return;
    }

    try {
      setUpdatingPAT(true);
      const response = await axios.put(
        `${API_BASE_URL}/api/subscriptions/${subscriptionId}/pat`,
        { pat: patInput.trim(), user_id: "user123" }
      );

      if (response.data.success) {
        alert("✅ PAT가 성공적으로 추가되었습니다!");
        setShowPATModal(false);
        setPatInput("");
        fetchSubscription(); // 구독 정보 새로고침
      } else {
        alert(`오류: ${response.data.error}`);
      }
    } catch (error) {
      alert(`오류: ${error.response?.data?.error || error.message}`);
    } finally {
      setUpdatingPAT(false);
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
    return (
      <span
        className={`px-4 py-1.5 text-xs font-bold rounded-full ${
          styles[status] || styles.pending
        }`}
      >
        {labels[status] || "⏳ 대기"}
      </span>
    );
  };

  if (loading && !subscription) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">로딩 중...</div>
        </div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center text-red-600">
            구독 정보를 찾을 수 없습니다.
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
            onClick={() => navigate("/")}
            className="mb-6 text-blue-600 hover:text-blue-800 flex items-center gap-2 font-medium transition-colors group"
          >
            <span className="group-hover:-translate-x-1 transition-transform">
              ←
            </span>
            <span>뒤로 가기</span>
          </button>
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl shadow-xl p-8 text-white">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <div className="bg-white/20 backdrop-blur-sm rounded-xl p-3">
                    <span className="text-3xl">📦</span>
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold mb-1">
                      {subscription.repo_full_name}
                    </h1>
                    <p className="text-blue-100 text-sm">Repository Details</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
                    <p className="text-blue-100 text-xs mb-1">생성일</p>
                    <p className="text-white font-semibold">
                      {new Date(subscription.created_at).toLocaleDateString(
                        "ko-KR"
                      )}
                    </p>
                  </div>
                  {subscription.last_polled_at && (
                    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
                      <p className="text-blue-100 text-xs mb-1">마지막 확인</p>
                      <p className="text-white font-semibold">
                        {new Date(
                          subscription.last_polled_at
                        ).toLocaleDateString("ko-KR")}
                      </p>
                    </div>
                  )}
                  {subscription.exclude_branches && (
                    <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
                      <p className="text-blue-100 text-xs mb-1">제외 브랜치</p>
                      <p className="text-white font-semibold">
                        {subscription.exclude_branches.join(", ")}
                      </p>
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-4">
                {subscription.user_credential_id ? (
                  <div className="px-4 py-2 bg-green-500 text-white rounded-lg font-semibold shadow-lg flex items-center gap-2">
                    <span>✅</span>
                    <span>
                      PAT가 연결되어 있습니다 (Rate Limit: 5,000회/시간)
                    </span>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowPATModal(true)}
                    className="px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
                  >
                    <span>🔑</span>
                    <span>PAT 추가 (Rate Limit 증가)</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* PR 리스트 */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="bg-gradient-to-r from-gray-50 to-blue-50 p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-blue-100 rounded-lg p-2">
                  <span className="text-xl">🔍</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Pull Requests
                  </h2>
                  <p className="text-sm text-gray-600">
                    총 {prs.length}개의 PR이 감지되었습니다
                  </p>
                </div>
              </div>
              <button
                onClick={triggerPolling}
                disabled={polling}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transform hover:-translate-y-0.5"
              >
                {polling ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>감지 중...</span>
                  </>
                ) : (
                  <>
                    <span className="text-xl">🚀</span>
                    <span>지금 감지하기</span>
                  </>
                )}
              </button>
            </div>
          </div>
          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-500">로딩 중...</p>
            </div>
          ) : prs.length === 0 ? (
            <div className="p-12 text-center">
              <div className="inline-block bg-gray-100 rounded-full p-6 mb-4">
                <span className="text-4xl">📭</span>
              </div>
              <p className="text-gray-500 text-lg font-medium">
                아직 감지된 PR이 없습니다
              </p>
              <p className="text-gray-400 text-sm mt-2">
                새로운 PR이 생성되면 자동으로 표시됩니다
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {prs.map((pr, index) => (
                <div
                  key={pr.id}
                  onClick={() =>
                    navigate(`/subscriptions/${subscriptionId}/prs/${pr.id}`)
                  }
                  className="p-6 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 cursor-pointer transition-all duration-200 group"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-4 mb-3">
                        <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl p-3 text-white font-bold text-lg shadow-lg">
                          #{pr.pr_number}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-1">
                            <h3 className="text-lg font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
                              {pr.pr_title || `PR #${pr.pr_number}`}
                            </h3>
                            {pr.status === "completed" &&
                              getStatusBadge(pr.status)}
                          </div>
                          {pr.branch_name && (
                            <p className="text-sm text-gray-600 font-medium">
                              🌿 {pr.branch_name}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="ml-4 text-blue-600 group-hover:translate-x-1 transition-transform text-2xl">
                      →
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* PAT 추가 모달 */}
      {showPATModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">PAT 추가</h2>
              <button
                onClick={() => {
                  setShowPATModal(false);
                  setPatInput("");
                }}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Personal Access Token
                </label>
                <input
                  type="password"
                  value={patInput}
                  onChange={(e) => setPatInput(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      updatePAT();
                    }
                  }}
                />
                <p className="mt-2 text-xs text-gray-500">
                  PAT를 추가하면 rate limit이 60회/시간 → 5,000회/시간으로
                  증가합니다.
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowPATModal(false);
                    setPatInput("");
                  }}
                  className="flex-1 px-4 py-3 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={updatePAT}
                  disabled={updatingPAT || !patInput.trim()}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {updatingPAT ? "추가 중..." : "PAT 추가"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RepositoryDetail;
