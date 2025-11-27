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
  const [currentBannerIndex, setCurrentBannerIndex] = useState(0);

  // 폼 상태
  const [formData, setFormData] = useState({
    repo_full_name: "",
    pat: "",
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

  // 배너 자동 캐러셀
  useEffect(() => {
    const bannerInterval = setInterval(() => {
      setCurrentBannerIndex((prev) => (prev + 1) % 3);
    }, 5000); // 5초마다 자동 전환

    return () => clearInterval(bannerInterval);
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

      // preview 브랜치만 테스트 대상이므로 항상 preview-dev.oliveyoung.com 사용

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
        {/* 배너 캐러셀 */}
        <section className="mb-8">
          <div className="relative h-64 md:h-80 lg:h-96 rounded-2xl overflow-hidden shadow-2xl">
            {/* 배너 이미지들 */}
            <div className="relative w-full h-full">
              {/* 배너 1: AI 기반 테스트 자동화 */}
              <div
                className={`absolute inset-0 transition-opacity duration-1000 ${
                  currentBannerIndex === 0 ? "opacity-100" : "opacity-0"
                }`}
                style={{
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
                }}
              >
                {/* 배경 패턴 */}
                <svg
                  className="absolute inset-0 w-full h-full opacity-20"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <defs>
                    <pattern
                      id="grid1"
                      width="40"
                      height="40"
                      patternUnits="userSpaceOnUse"
                    >
                      <path
                        d="M 40 0 L 0 0 0 40"
                        fill="none"
                        stroke="white"
                        strokeWidth="1"
                      />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid1)" />
                </svg>

                {/* AI 로봇 일러스트 */}
                <div className="absolute top-10 right-10 w-32 h-32 md:w-48 md:h-48 opacity-30">
                  <svg viewBox="0 0 200 200" className="w-full h-full">
                    <circle
                      cx="100"
                      cy="60"
                      r="35"
                      fill="white"
                      opacity="0.3"
                    />
                    <rect
                      x="50"
                      y="100"
                      width="100"
                      height="80"
                      rx="10"
                      fill="white"
                      opacity="0.3"
                    />
                    <circle cx="80" cy="130" r="8" fill="white" />
                    <circle cx="120" cy="130" r="8" fill="white" />
                    <rect x="85" y="150" width="30" height="5" rx="2" fill="white" />
                    <path
                      d="M 100 60 L 100 100"
                      stroke="white"
                      strokeWidth="8"
                      opacity="0.3"
                    />
                  </svg>
                </div>

                {/* 데이터 흐름 일러스트 */}
                <div className="absolute bottom-10 left-10 w-24 h-24 md:w-32 md:h-32 opacity-20">
                  <svg viewBox="0 0 100 100" className="w-full h-full">
                    <circle cx="20" cy="50" r="8" fill="white" />
                    <circle cx="50" cy="50" r="8" fill="white" />
                    <circle cx="80" cy="50" r="8" fill="white" />
                    <path
                      d="M 28 50 L 42 50"
                      stroke="white"
                      strokeWidth="3"
                    />
                    <path
                      d="M 58 50 L 72 50"
                      stroke="white"
                      strokeWidth="3"
                    />
                  </svg>
                </div>

                <div className="absolute inset-0 flex items-center justify-center text-white p-8 z-10">
                  <div className="text-center max-w-3xl">
                    <div className="text-6xl md:text-7xl lg:text-8xl mb-4 animate-pulse">
                      🤖
                    </div>
                    <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 drop-shadow-lg">
                      AI 기반 E2E 테스트 자동화
                    </h2>
                    <p className="text-lg md:text-xl text-white/95 drop-shadow-md">
                      Gemini AI가 PR 변경사항을 분석하고<br />
                      자동으로 테스트 시나리오를 생성합니다
                    </p>
                  </div>
                </div>
              </div>

              {/* 배너 2: 실시간 PR 모니터링 */}
              <div
                className={`absolute inset-0 transition-opacity duration-1000 ${
                  currentBannerIndex === 1 ? "opacity-100" : "opacity-0"
                }`}
                style={{
                  background:
                    "linear-gradient(135deg, #f093fb 0%, #f5576c 50%, #4facfe 100%)",
                }}
              >
                {/* 배경 원형 패턴 */}
                <svg
                  className="absolute inset-0 w-full h-full opacity-15"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <circle cx="50" cy="50" r="30" fill="white" />
                  <circle cx="200" cy="100" r="40" fill="white" />
                  <circle cx="350" cy="150" r="25" fill="white" />
                  <circle cx="500" cy="80" r="35" fill="white" />
                  <circle cx="150" cy="200" r="20" fill="white" />
                  <circle cx="400" cy="250" r="30" fill="white" />
                </svg>

                {/* GitHub 로고 일러스트 */}
                <div className="absolute top-8 right-8 w-40 h-40 md:w-56 md:h-56 opacity-25">
                  <svg viewBox="0 0 100 100" className="w-full h-full">
                    <path
                      d="M 50 10 L 20 30 L 20 70 L 50 90 L 80 70 L 80 30 Z"
                      fill="white"
                    />
                    <circle cx="50" cy="45" r="8" fill="none" stroke="#f5576c" strokeWidth="2" />
                    <path
                      d="M 50 53 L 50 65"
                      stroke="#f5576c"
                      strokeWidth="3"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>

                {/* 알림 벨 일러스트 */}
                <div className="absolute bottom-12 left-12 w-28 h-28 md:w-36 md:h-36 opacity-20">
                  <svg viewBox="0 0 100 100" className="w-full h-full">
                    <path
                      d="M 50 20 L 50 20 L 30 20 Q 20 20 20 30 L 20 50 Q 20 60 30 60 L 50 60 L 50 80 L 60 80 L 60 60 L 70 60 Q 80 60 80 50 L 80 30 Q 80 20 70 20 Z"
                      fill="white"
                    />
                    <circle cx="50" cy="40" r="3" fill="#f5576c" />
                  </svg>
                </div>

                {/* 펄스 애니메이션 원 */}
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 md:w-96 md:h-96 opacity-10">
                  <div className="absolute inset-0 rounded-full border-4 border-white animate-ping"></div>
                </div>

                <div className="absolute inset-0 flex items-center justify-center text-white p-8 z-10">
                  <div className="text-center max-w-3xl">
                    <div className="text-6xl md:text-7xl lg:text-8xl mb-4 animate-bounce">
                      🔍
                    </div>
                    <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 drop-shadow-lg">
                      실시간 PR 모니터링
                    </h2>
                    <p className="text-lg md:text-xl text-white/95 drop-shadow-md">
                      GitHub PR을 자동으로 감지하고<br />
                      즉시 테스트를 실행합니다
                    </p>
                  </div>
                </div>
              </div>

              {/* 배너 3: 브라우저 자동화 테스트 */}
              <div
                className={`absolute inset-0 transition-opacity duration-1000 ${
                  currentBannerIndex === 2 ? "opacity-100" : "opacity-0"
                }`}
                style={{
                  background:
                    "linear-gradient(135deg, #4facfe 0%, #00f2fe 50%, #43e97b 100%)",
                }}
              >
                {/* 웹 브라우저 일러스트 */}
                <div className="absolute top-8 right-8 w-48 h-48 md:w-64 md:h-64 opacity-25">
                  <svg viewBox="0 0 200 200" className="w-full h-full">
                    {/* 브라우저 창 */}
                    <rect
                      x="20"
                      y="20"
                      width="160"
                      height="140"
                      rx="8"
                      fill="white"
                      opacity="0.3"
                    />
                    {/* 주소창 */}
                    <rect
                      x="30"
                      y="35"
                      width="140"
                      height="15"
                      rx="3"
                      fill="white"
                      opacity="0.5"
                    />
                    {/* 탭 */}
                    <rect
                      x="25"
                      y="25"
                      width="50"
                      height="8"
                      rx="2"
                      fill="white"
                      opacity="0.4"
                    />
                    {/* 콘텐츠 영역 */}
                    <rect
                      x="30"
                      y="60"
                      width="140"
                      height="90"
                      rx="4"
                      fill="white"
                      opacity="0.2"
                    />
                    {/* 체크마크 */}
                    <path
                      d="M 80 100 L 95 115 L 130 80"
                      stroke="white"
                      strokeWidth="6"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>

                {/* 코드 블록 일러스트 */}
                <div className="absolute bottom-10 left-10 w-32 h-32 md:w-40 md:h-40 opacity-20">
                  <svg viewBox="0 0 100 100" className="w-full h-full">
                    <rect
                      x="10"
                      y="10"
                      width="80"
                      height="80"
                      rx="4"
                      fill="white"
                      opacity="0.3"
                    />
                    <rect x="20" y="25" width="40" height="4" rx="2" fill="white" />
                    <rect x="20" y="35" width="50" height="4" rx="2" fill="white" />
                    <rect x="20" y="45" width="35" height="4" rx="2" fill="white" />
                    <rect x="20" y="55" width="45" height="4" rx="2" fill="white" />
                    <rect x="20" y="65" width="30" height="4" rx="2" fill="white" />
                  </svg>
                </div>

                {/* 파도 패턴 */}
                <svg
                  className="absolute bottom-0 left-0 w-full h-32 opacity-20"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 1200 120"
                  preserveAspectRatio="none"
                >
                  <path
                    d="M0,60 Q300,20 600,60 T1200,60 L1200,120 L0,120 Z"
                    fill="white"
                  />
                </svg>

                {/* 반짝이는 별들 */}
                <div className="absolute top-20 left-20 w-4 h-4 opacity-60">
                  <svg viewBox="0 0 20 20" className="w-full h-full animate-pulse">
                    <polygon
                      points="10,2 12,8 18,8 13,12 15,18 10,14 5,18 7,12 2,8 8,8"
                      fill="white"
                    />
                  </svg>
                </div>
                <div className="absolute top-32 right-32 w-3 h-3 opacity-50">
                  <svg viewBox="0 0 20 20" className="w-full h-full animate-pulse" style={{ animationDelay: '0.5s' }}>
                    <polygon
                      points="10,2 12,8 18,8 13,12 15,18 10,14 5,18 7,12 2,8 8,8"
                      fill="white"
                    />
                  </svg>
                </div>
                <div className="absolute bottom-24 right-24 w-5 h-5 opacity-40">
                  <svg viewBox="0 0 20 20" className="w-full h-full animate-pulse" style={{ animationDelay: '1s' }}>
                    <polygon
                      points="10,2 12,8 18,8 13,12 15,18 10,14 5,18 7,12 2,8 8,8"
                      fill="white"
                    />
                  </svg>
                </div>

                <div className="absolute inset-0 flex items-center justify-center text-white p-8 z-10">
                  <div className="text-center max-w-3xl">
                    <div className="text-6xl md:text-7xl lg:text-8xl mb-4 animate-spin" style={{ animationDuration: '20s' }}>
                      🌐
                    </div>
                    <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold mb-4 drop-shadow-lg">
                      브라우저 자동화 테스트
                    </h2>
                    <p className="text-lg md:text-xl text-white/95 drop-shadow-md">
                      Playwright와 Vision AI로<br />
                      실제 사용자 경험을 검증합니다
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* 인디케이터 */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2 z-10">
              {[0, 1, 2].map((index) => (
                <button
                  key={index}
                  onClick={() => setCurrentBannerIndex(index)}
                  className={`w-3 h-3 rounded-full transition-all ${
                    currentBannerIndex === index
                      ? "bg-white w-8"
                      : "bg-white/50 hover:bg-white/75"
                  }`}
                  aria-label={`배너 ${index + 1}로 이동`}
                />
              ))}
            </div>

            {/* 좌우 화살표 */}
            <button
              onClick={() =>
                setCurrentBannerIndex((prev) => (prev - 1 + 3) % 3)
              }
              className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-white/20 hover:bg-white/30 text-white p-2 rounded-full transition-all z-10"
              aria-label="이전 배너"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
            <button
              onClick={() =>
                setCurrentBannerIndex((prev) => (prev + 1) % 3)
              }
              className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-white/20 hover:bg-white/30 text-white p-2 rounded-full transition-all z-10"
              aria-label="다음 배너"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>
        </section>

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
