import axios from "axios";
import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import "./App.css";
import Header from "./components/Header";
import PRDetail from "./pages/PRDetail";
import RepositoryDetail from "./pages/RepositoryDetail";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5001";

// 홈 페이지 컴포넌트
function Home() {
  const navigate = useNavigate();
  const [subscriptions, setSubscriptions] = useState([]);
  const [tests, setTests] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pollingAll, setPollingAll] = useState(false);
  const [userId] = useState("user123"); // 실제로는 인증에서 가져옴

  // 폼 상태
  const [formData, setFormData] = useState({
    repo_full_name: "",
    pat: "",
    base_url: "", // 기본 배포 URL (예: global.oliveyoung.com) - PR URL은 pr-{번호}.{base_url} 형식으로 자동 생성
    auto_test: true,
    slack_notify: false, // 기본값: 비활성화
    exclude_branches: "main", // 기본값: main만 제외
  });

  // 구독 목록 조회
  const fetchSubscriptions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/subscriptions`, {
        params: { user_id: userId },
      });
      if (response.data.success) {
        setSubscriptions(response.data.subscriptions);
      }
    } catch (error) {
      console.error("구독 목록 조회 실패:", error);
    }
  };

  // 테스트 기록 조회
  const fetchTests = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/tests`, {
        params: { user_id: userId, limit: 20 },
      });
      if (response.data.success) {
        setTests(response.data.tests);
      }
    } catch (error) {
      console.error("테스트 기록 조회 실패:", error);
    }
  };

  useEffect(() => {
    fetchSubscriptions();
    fetchTests();

    // 주기적으로 갱신
    const interval = setInterval(() => {
      fetchSubscriptions();
      fetchTests();
    }, 30000); // 30초마다

    return () => clearInterval(interval);
  }, []);

  // PAT 검증
  const verifyPAT = async (pat) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/pat/verify`, {
        pat: pat,
      });
      return response.data;
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || "검증 실패",
      };
    }
  };

  // 레포지토리 접근 확인
  const checkRepoAccess = async (pat, repoFullName) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/pat/check-repo`, {
        pat: pat,
        repo_full_name: repoFullName,
      });
      return response.data;
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || "접근 확인 실패",
      };
    }
  };

  // GitHub URL을 owner/repo 형식으로 변환
  const normalizeRepoName = (repoInput) => {
    if (!repoInput) return "";

    let normalized = repoInput.trim();

    // 앞뒤 슬래시 제거
    normalized = normalized.replace(/^\/+|\/+$/g, "");

    // https://github.com/owner/repo 형식인 경우
    const githubUrlPattern = /github\.com[/:]([^/]+)\/([^/]+?)(?:\.git)?\/?$/;
    const match = normalized.match(githubUrlPattern);
    if (match) {
      return `${match[1]}/${match[2]}`;
    }

    // 이미 owner/repo 형식인 경우 (앞뒤 슬래시 제거 후)
    if (normalized.includes("/") && !normalized.includes("http")) {
      return normalized;
    }

    return normalized;
  };

  // 구독 추가
  const handleAddSubscription = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // 레포지토리 이름 정규화
      const normalizedRepoName = normalizeRepoName(formData.repo_full_name);
      if (!normalizedRepoName || !normalizedRepoName.includes("/")) {
        alert(
          "올바른 레포지토리 형식을 입력해주세요.\n예: owner/repo-name 또는 https://github.com/owner/repo"
        );
        setLoading(false);
        return;
      }

      // PAT 필수 체크
      if (!formData.pat || formData.pat.trim() === "") {
        alert(
          "❌ Personal Access Token (PAT)는 필수입니다. PAT를 입력해주세요."
        );
        setLoading(false);
        return;
      }

      // 기본 배포 URL은 선택사항 (비워두면 로컬 배포 사용)

      // 1. PAT 검증
      try {
        const verifyResult = await verifyPAT(formData.pat);
        if (!verifyResult.success) {
          alert(`❌ PAT 검증 실패: ${verifyResult.error}`);
          setLoading(false);
          return;
        }
      } catch (error) {
        alert(`❌ PAT 검증 중 오류: ${error.message}`);
        setLoading(false);
        return;
      }

      // 2. 레포지토리 접근 확인
      try {
        const accessResult = await checkRepoAccess(
          formData.pat,
          normalizedRepoName
        );
        if (!accessResult.success) {
          alert(`❌ 레포지토리 접근 불가: ${accessResult.error}`);
          setLoading(false);
          return;
        }
      } catch (error) {
        alert(`❌ 레포지토리 접근 확인 중 오류: ${error.message}`);
        setLoading(false);
        return;
      }

      // 3. 구독 추가
      // 제외할 브랜치 목록 처리 (기본값: main)
      const excludeBranches = formData.exclude_branches
        ? formData.exclude_branches
            .split(",")
            .map((b) => b.trim())
            .filter(Boolean)
        : ["main"]; // 기본값: main만 제외

      const response = await axios.post(`${API_BASE_URL}/api/subscriptions`, {
        user_id: userId,
        repo_full_name: normalizedRepoName, // 정규화된 레포지토리 이름 사용
        pat: formData.pat, // PAT 필수
        base_url: formData.base_url.trim() || null, // 기본 배포 URL (선택사항, 예: global.oliveyoung.com)
        auto_test: formData.auto_test,
        slack_notify: formData.slack_notify,
        exclude_branches: excludeBranches,
      });

      if (response.data.success) {
        alert(
          "✅ 구독이 추가되었습니다!\n\n💡 PAT가 연결되어 rate limit이 5,000회/시간으로 설정되었습니다."
        );
        setShowAddModal(false);
        setFormData({
          repo_full_name: "",
          pat: "",
          base_url: "",
          auto_test: true,
          slack_notify: false, // 기본값: 비활성화
          exclude_branches: "main",
        });
        fetchSubscriptions();
      } else {
        alert(`구독 추가 실패: ${response.data.error}`);
      }
    } catch (error) {
      alert(`오류: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 전체 PR 감지 트리거
  const triggerAllPolling = async () => {
    try {
      setPollingAll(true);
      const response = await axios.post(
        `${API_BASE_URL}/api/subscriptions/poll-all`
      );

      if (response.data.success) {
        alert("✅ 모든 레포지토리에서 PR 감지가 완료되었습니다!");
        // 목록 새로고침
        setTimeout(() => {
          fetchSubscriptions();
          fetchTests();
        }, 1000);
      } else {
        const errorData = response.data || {};
        if (errorData.error_type === "rate_limit") {
          alert(
            `⚠️ GitHub API Rate Limit 초과\n\n${errorData.error}\n\n💡 해결 방법: Personal Access Token (PAT)을 추가하면 rate limit이 60회/시간에서 5,000회/시간으로 증가합니다.`
          );
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
        alert(
          `⚠️ GitHub API Rate Limit 초과\n\n${
            errorData.error || error.message
          }\n\n💡 해결 방법: Personal Access Token (PAT)을 추가하면 rate limit이 60회/시간에서 5,000회/시간으로 증가합니다.\n\n레포지토리 설정에서 PAT를 추가해주세요.`
        );
      } else {
        alert(`오류: ${error.response?.data?.error || error.message}`);
      }
    } finally {
      setPollingAll(false);
    }
  };

  // 구독 삭제
  const handleDeleteSubscription = async (id) => {
    if (!confirm("정말 구독을 해제하시겠습니까?")) return;

    try {
      const response = await axios.delete(
        `${API_BASE_URL}/api/subscriptions/${id}`,
        {
          params: { user_id: userId },
        }
      );
      if (response.data.success) {
        alert("구독이 해제되었습니다.");
        fetchSubscriptions();
      }
    } catch (error) {
      alert(`구독 해제 실패: ${error.response?.data?.error || error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex justify-end gap-3">
          <button
            onClick={triggerAllPolling}
            disabled={pollingAll}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-4 py-2 rounded-lg font-medium transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {pollingAll ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>감지 중...</span>
              </>
            ) : (
              <>
                <span>🚀</span>
                <span>전체 감지</span>
              </>
            )}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            + 레포지토리 추가
          </button>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 구독 목록 */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            구독 중인 레포지토리
          </h2>
          {subscriptions.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              구독 중인 레포지토리가 없습니다. 레포지토리를 추가해주세요.
            </div>
          ) : (
            <div className="grid gap-4">
              {subscriptions.map((sub) => (
                <div
                  key={sub.id}
                  onClick={() => navigate(`/subscriptions/${sub.id}`)}
                  className="bg-white rounded-lg shadow p-6 hover:shadow-lg cursor-pointer transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="text-lg font-semibold text-gray-900">
                          📦 {sub.repo_full_name}
                        </span>
                        {sub.auto_test && (
                          <span className="ml-2 px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                            자동 테스트
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>
                          생성일:{" "}
                          {new Date(sub.created_at).toLocaleString("ko-KR")}
                        </p>
                        {sub.last_polled_at && (
                          <p>
                            마지막 확인:{" "}
                            {new Date(sub.last_polled_at).toLocaleString(
                              "ko-KR"
                            )}
                          </p>
                        )}
                        {sub.exclude_branches && (
                          <p>제외 브랜치: {sub.exclude_branches.join(", ")}</p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSubscription(sub.id);
                      }}
                      className="ml-4 px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
                    >
                      구독 해제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 테스트 기록 */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            최근 테스트 기록
          </h2>
          {tests.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
              테스트 기록이 없습니다.
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      PR
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      레포지토리
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      상태
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      생성일
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      완료일
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {tests.map((test) => (
                    <tr key={test.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <a
                          href={test.pr_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                        >
                          PR #{test.pr_number}
                        </a>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {test.repo_full_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${
                            test.status === "completed"
                              ? "bg-green-100 text-green-800"
                              : test.status === "failed"
                              ? "bg-red-100 text-red-800"
                              : test.status === "running"
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {test.status === "completed" && "✅ 완료"}
                          {test.status === "failed" && "❌ 실패"}
                          {test.status === "running" && "🔄 실행 중"}
                          {test.status === "pending" && "⏳ 대기"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(test.created_at).toLocaleString("ko-KR")}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {test.completed_at
                          ? new Date(test.completed_at).toLocaleString("ko-KR")
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      {/* Add Subscription Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">
                  레포지토리 구독 추가
                </h2>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleAddSubscription} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    GitHub 레포지토리 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="owner/repo-name 또는 https://github.com/owner/repo"
                    value={formData.repo_full_name}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        repo_full_name: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    형식: owner/repo-name 또는 https://github.com/owner/repo
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Personal Access Token (PAT){" "}
                    <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                    value={formData.pat}
                    onChange={(e) =>
                      setFormData({ ...formData, pat: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    GitHub → Settings → Developer settings → Personal access
                    tokens → Generate new token
                    <br />
                    필요한 권한:{" "}
                    <code className="bg-gray-100 px-1 rounded">repo</code> (전체
                    접근 권한)
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    기본 배포 URL (선택사항)
                  </label>
                  <input
                    type="text"
                    placeholder="global.oliveyoung.com (비워두면 로컬 배포 사용)"
                    value={formData.base_url}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        base_url: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    <span className="font-semibold text-blue-600">
                      입력한 경우:
                    </span>{" "}
                    PR이 감지되면 자동으로{" "}
                    <code className="bg-gray-100 px-1 rounded">
                      pr-{"{번호}"}.{"{base_url}"}
                    </code>{" "}
                    형식으로 URL이 생성됩니다.
                    <br />
                    <span className="font-semibold text-purple-600">
                      로컬 테스트:
                    </span>{" "}
                    이 필드를 비워두세요!
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    제외할 브랜치 (선택사항)
                  </label>
                  <input
                    type="text"
                    placeholder="main (기본값, 쉼표로 구분)"
                    value={formData.exclude_branches}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        exclude_branches: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    이 브랜치들의 PR은 감지하지 않습니다. 기본값: main
                    <br />
                    와일드카드 지원: main* (main으로 시작하는 모든 브랜치 제외)
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.auto_test}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          auto_test: e.target.checked,
                        })
                      }
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">
                      자동 테스트 실행
                    </span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.slack_notify}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          slack_notify: e.target.checked,
                        })
                      }
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">
                      Slack 알림 전송
                    </span>
                  </label>
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? "처리 중..." : "구독 추가"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 메인 App 컴포넌트 (라우터 설정)
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/subscriptions/:subscriptionId"
          element={<RepositoryDetail />}
        />
        <Route
          path="/subscriptions/:subscriptionId/prs/:testId"
          element={<PRDetail />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
