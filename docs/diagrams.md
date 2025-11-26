# 나이트워치 프로젝트 - 다이어그램

## 📊 전체 워크플로우 (시퀀스 다이어그램)

```mermaid
sequenceDiagram
    participant Dev as 개발자
    participant GH as GitHub
    participant WH as Agent
    participant K8s as K8s Deployer
    participant AI as Gemini AI
    participant MCP as Browser MCP
    participant Vision as Vision Validator
    participant Slack as Slack

    Dev->>GH: PR 생성/업데이트
    GH->>WH: Webhook 이벤트 전송

    WH->>WH: 서명 검증
    WH->>GH: PR 정보 조회
    GH-->>WH: PR 데이터 (diff, 메타데이터)

    WH->>K8s: PR 배포 요청
    K8s->>K8s: Pod 생성 (pr-123.global.oliveyoung.com)
    K8s-->>WH: 배포 완료 (URL 반환)

    WH->>AI: PR diff 분석 요청
    AI->>AI: 변경사항 분석
    AI->>AI: 테스트 시나리오 생성
    AI-->>WH: 시나리오 리스트 반환

    loop 각 시나리오 실행
        WH->>MCP: 시나리오 실행 요청
        MCP->>MCP: 브라우저에서 액션 수행
        MCP-->>WH: 실행 결과 + 스크린샷
    end

    loop 각 결과 검증
        WH->>Vision: 스크린샷 검증 요청
        Vision->>Vision: 이미지 분석
        Vision-->>WH: 검증 결과 반환
    end

    WH->>WH: 리포트 생성
    WH->>Slack: 테스트 리포트 전송
    Slack-->>Dev: 알림 수신

    Note over Dev,Slack: PR이 닫히거나 머지되면
    GH->>WH: PR closed/merged 이벤트
    WH->>K8s: 배포 정리 요청
    K8s->>K8s: Pod 삭제
```

## 🏗️ 시스템 아키텍처 (컴포넌트 다이어그램)

```mermaid
graph TB
    subgraph "GitHub"
        PR[Pull Request]
        Webhook[Webhook Event]
    end

    subgraph "NightWatch Server"
        WS[Agent<br/>Flask]
        PA[PR Analyzer<br/>Gemini API]
        BE[Browser Executor<br/>Browser MCP]
        VV[Vision Validator<br/>Gemini Vision]
        SN[Slack Notifier]
    end

    subgraph "Infrastructure"
        K8S[Kubernetes<br/>K8s Deployer]
        MCP[Browser MCP Server]
        K8S_POD[PR Pod<br/>pr-123.domain.com]
    end

    subgraph "External Services"
        GEMINI[Gemini API]
        SLACK[Slack API]
    end

    PR -->|PR 생성/업데이트| Webhook
    Webhook -->|POST /webhook| WS

    WS -->|PR 정보 조회| PR
    WS -->|배포 요청| K8S
    K8S -->|Pod 생성| K8S_POD

    WS -->|PR diff 분석| PA
    PA -->|API 호출| GEMINI
    GEMINI -->|시나리오 생성| PA
    PA -->|시나리오 리스트| WS

    WS -->|시나리오 실행| BE
    BE -->|브라우저 제어| MCP
    MCP -->|페이지 접근| K8S_POD
    MCP -->|스크린샷| BE

    BE -->|스크린샷| VV
    VV -->|이미지 분석| GEMINI
    GEMINI -->|검증 결과| VV
    VV -->|검증 결과| WS

    WS -->|테스트 리포트| SN
    SN -->|알림 전송| SLACK

    style WS fill:#e1f5ff
    style PA fill:#fff4e1
    style BE fill:#e1ffe1
    style VV fill:#fff4e1
    style K8S fill:#ffe1f5
    style MCP fill:#e1ffe1
```

## 🔄 상세 프로세스 플로우 (플로우차트)

```mermaid
flowchart TD
    Start([GitHub PR 생성/업데이트]) --> Webhook[Webhook 이벤트 수신]
    Webhook --> Verify{서명 검증}
    Verify -->|실패| Error1[에러 응답]
    Verify -->|성공| CheckAction{이벤트 타입}

    CheckAction -->|closed/merged| Cleanup[배포 정리]
    Cleanup --> End1([종료])

    CheckAction -->|opened/synchronize| GetPR[PR 정보 조회]
    GetPR --> GetDiff[PR Diff 추출]

    GetDiff --> Deploy[쿠버네티스 배포]
    Deploy --> WaitDeploy{배포 완료 대기}
    WaitDeploy -->|타임아웃| Error2[배포 실패]
    WaitDeploy -->|성공| DeployURL[PR URL 획득<br/>pr-123.domain.com]

    DeployURL --> Analyze[Gemini로 PR 분석]
    Analyze --> GenScenarios[테스트 시나리오 생성]

    GenScenarios --> LoopStart{시나리오 반복}
    LoopStart -->|다음 시나리오| Execute[Browser MCP 실행]

    Execute --> ActionLoop{액션 반복}
    ActionLoop -->|goto| Navigate[페이지 이동]
    ActionLoop -->|click| Click[요소 클릭]
    ActionLoop -->|fill| Fill[텍스트 입력]
    ActionLoop -->|wait| Wait[대기]
    ActionLoop -->|screenshot| Screenshot[스크린샷]

    Navigate --> CheckActionResult{액션 성공?}
    Click --> CheckActionResult
    Fill --> CheckActionResult
    Wait --> CheckActionResult
    Screenshot --> CheckActionResult

    CheckActionResult -->|실패| FailResult[시나리오 실패 기록]
    CheckActionResult -->|성공| NextAction{다음 액션?}

    NextAction -->|있음| ActionLoop
    NextAction -->|없음| VisionCheck[Vision API 검증]

    FailResult --> NextScenario
    VisionCheck --> VisionResult{검증 결과}
    VisionResult -->|통과| PassResult[시나리오 성공]
    VisionResult -->|실패| FailResult

    PassResult --> NextScenario{다음 시나리오?}
    FailResult --> NextScenario
    NextScenario -->|있음| LoopStart
    NextScenario -->|없음| GenerateReport[리포트 생성]

    GenerateReport --> SendSlack[Slack 알림 전송]
    SendSlack --> End2([완료])

    Error1 --> End1
    Error2 --> SendError[에러 알림 전송]
    SendError --> End1

    style Start fill:#e1f5ff
    style End1 fill:#ffe1e1
    style End2 fill:#e1ffe1
    style Deploy fill:#fff4e1
    style Analyze fill:#fff4e1
    style Execute fill:#e1ffe1
    style VisionCheck fill:#fff4e1
    style SendSlack fill:#ffe1f5
```

## 📦 데이터 플로우 다이어그램

```mermaid
graph LR
    subgraph "Input"
        PR_DIFF[PR Diff<br/>파일 변경사항]
        PR_META[PR 메타데이터<br/>번호, 제목, 작성자]
    end

    subgraph "Processing"
        SCENARIOS[테스트 시나리오<br/>JSON 배열]
        ACTIONS[액션 리스트<br/>goto, click, fill 등]
        SCREENSHOTS[스크린샷<br/>Base64 이미지]
        VALIDATION[검증 결과<br/>is_valid, issues]
    end

    subgraph "Output"
        REPORT[테스트 리포트<br/>JSON]
        SLACK_MSG[Slack 메시지<br/>Blocks 형식]
    end

    PR_DIFF --> SCENARIOS
    PR_META --> SCENARIOS

    SCENARIOS --> ACTIONS
    ACTIONS --> SCREENSHOTS
    SCREENSHOTS --> VALIDATION

    SCENARIOS --> REPORT
    VALIDATION --> REPORT
    PR_META --> REPORT

    REPORT --> SLACK_MSG

    style PR_DIFF fill:#e1f5ff
    style SCENARIOS fill:#fff4e1
    style ACTIONS fill:#e1ffe1
    style SCREENSHOTS fill:#ffe1f5
    style VALIDATION fill:#fff4e1
    style REPORT fill:#e1ffe1
    style SLACK_MSG fill:#ffe1f5
```

## 🔌 컴포넌트 상호작용 다이어그램

```mermaid
graph TB
    subgraph "Core Modules"
        WS[agent<br/>메인 오케스트레이터]
        K8S[k8s_deployer.py<br/>배포 관리]
        PA[pr_analyzer.py<br/>AI 분석]
        BE[browser_executor.py<br/>브라우저 실행]
        BMCP[browser_mcp_client.py<br/>MCP 클라이언트]
        VV[vision_validator.py<br/>이미지 검증]
        SN[slack_notifier.py<br/>알림 전송]
    end

    WS -->|1. 배포 요청| K8S
    K8S -->|배포 URL 반환| WS

    WS -->|2. PR 분석 요청| PA
    PA -->|시나리오 반환| WS

    WS -->|3. 시나리오 실행| BE
    BE -->|MCP 호출| BMCP
    BMCP -->|결과 반환| BE
    BE -->|실행 결과| WS

    WS -->|4. 검증 요청| VV
    VV -->|검증 결과| WS

    WS -->|5. 리포트 전송| SN

    style WS fill:#e1f5ff
    style K8S fill:#ffe1f5
    style PA fill:#fff4e1
    style BE fill:#e1ffe1
    style BMCP fill:#e1ffe1
    style VV fill:#fff4e1
    style SN fill:#ffe1f5
```

## 🎯 에러 처리 플로우

```mermaid
flowchart TD
    Start([프로세스 시작]) --> Try{각 단계 실행}

    Try -->|성공| Next[다음 단계]
    Try -->|실패| ErrorType{에러 타입}

    ErrorType -->|배포 실패| DeployError[배포 에러 로깅]
    ErrorType -->|시나리오 생성 실패| ScenarioError[기본 시나리오 사용]
    ErrorType -->|브라우저 실행 실패| BrowserError[Playwright 폴백]
    ErrorType -->|Vision 검증 실패| VisionError[검증 스킵]
    ErrorType -->|Slack 전송 실패| SlackError[에러 로깅]

    DeployError --> Cleanup[배포 정리]
    Cleanup --> NotifyError[에러 알림 전송]

    ScenarioError --> Next
    BrowserError --> Next
    VisionError --> Next
    SlackError --> Next

    Next --> Continue{계속 진행?}
    Continue -->|예| Try
    Continue -->|아니오| End([종료])

    NotifyError --> End

    style Start fill:#e1f5ff
    style End fill:#ffe1e1
    style ErrorType fill:#fff4e1
    style NotifyError fill:#ffe1e1
```

---

## 🔐 PAT 기반 레포지토리 구독 시스템 (최종 버전)

### 전체 워크플로우 (PAT + Polling 방식)

```mermaid
sequenceDiagram
    participant User as 사용자
    participant UI as React UI
    participant API as Backend API
    participant DB as Database
    participant GH as GitHub API
    participant K8s as K8s Deployer
    participant AI as Gemini AI
    participant MCP as Browser MCP
    participant Vision as Vision Validator
    participant Slack as Slack

    Note over User,Slack: 1단계: 초기 설정 및 인증
    User->>UI: 레포지토리 링크 입력<br/>(company/repo-name)
    UI->>User: PAT 입력 요청
    User->>UI: Personal Access Token 입력
    UI->>API: PAT 검증 요청
    API->>GH: 사용자 정보 조회 (PAT 사용)
    GH-->>API: 사용자 정보 반환
    API->>GH: 레포지토리 접근 권한 확인
    GH-->>API: 접근 가능 확인
    API->>DB: PAT 암호화하여 저장
    API->>DB: 구독 정보 저장
    API-->>UI: 구독 완료

    Note over User,Slack: 2단계: Polling으로 PR 탐지
    loop 주기적 Polling (5분마다)
        API->>DB: 구독한 레포지토리 목록 조회
        DB-->>API: 구독 정보 반환
        API->>DB: PAT 복호화
        API->>GH: PR 목록 조회 (PAT 사용)<br/>since=last_polled_at
        GH-->>API: PR 목록 반환
        API->>API: 새 PR 또는 업데이트된 PR 감지
    end

    Note over User,Slack: 3단계: 자동 테스트 실행
    API->>GH: PR 정보 상세 조회
    GH-->>API: PR 데이터 (diff, 메타데이터)

    API->>K8s: PR 배포 요청
    K8s->>K8s: Pod 생성<br/>(pr-123.global.oliveyoung.com)
    K8s-->>API: 배포 완료 (URL 반환)

    API->>AI: PR diff 분석 요청
    AI->>AI: 변경사항 분석
    AI->>AI: 테스트 시나리오 생성
    AI-->>API: 시나리오 리스트 반환

    loop 각 시나리오 실행
        API->>MCP: 시나리오 실행 요청
        MCP->>MCP: 브라우저에서 액션 수행<br/>(pr-123.domain.com)
        MCP-->>API: 실행 결과 + 스크린샷
    end

    loop 각 결과 검증
        API->>Vision: 스크린샷 검증 요청
        Vision->>Vision: 이미지 분석
        Vision-->>API: 검증 결과 반환
    end

    API->>DB: 테스트 결과 저장
    API->>Slack: 테스트 리포트 전송
    Slack-->>User: 알림 수신
    API->>UI: 실시간 결과 업데이트 (WebSocket/SSE)
    UI-->>User: 대시보드에 결과 표시
```

### 시스템 아키텍처 (PAT + Polling)

```mermaid
graph TB
    subgraph "Frontend"
        UI[React UI<br/>레포지토리 구독 관리]
    end

    subgraph "Backend API"
        API[Flask/FastAPI Server]
        Auth[PAT 인증 모듈]
        Poll[Polling Scheduler]
        WS[WebSocket/SSE Server]
    end

    subgraph "Database"
        DB[(Database)]
        Creds[user_credentials<br/>암호화된 PAT]
        Subs[subscriptions<br/>구독 정보]
        Tests[tests<br/>테스트 기록]
    end

    subgraph "GitHub"
        GH_API[GitHub API]
        REPO[Repository]
        PR[Pull Requests]
    end

    subgraph "NightWatch Core"
        K8S[K8s Deployer]
        PA[PR Analyzer]
        BE[Browser Executor]
        BMCP[Browser MCP Client]
        VV[Vision Validator]
        SN[Slack Notifier]
    end

    subgraph "External Services"
        GEMINI[Gemini API]
        MCP_SERVER[Browser MCP Server]
        SLACK[Slack API]
        K8S_CLUSTER[Kubernetes Cluster]
    end

    UI -->|1. 레포지토리 링크 + PAT 입력| API
    API -->|2. PAT 검증| GH_API
    GH_API -->|사용자 정보| API
    API -->|3. PAT 암호화 저장| Creds
    API -->|4. 구독 정보 저장| Subs

    Poll -->|5. 주기적 조회 (5분)| DB
    DB -->|구독 정보| Poll
    Poll -->|6. PAT 복호화| Creds
    Poll -->|7. PR 목록 조회| GH_API
    GH_API -->|PR 목록| Poll

    Poll -->|8. 새 PR 감지| API
    API -->|9. PR 상세 조회| GH_API
    GH_API -->|PR diff| API

    API -->|10. 배포 요청| K8S
    K8S -->|Pod 생성| K8S_CLUSTER
    K8S_CLUSTER -->|pr-123.domain.com| K8S

    API -->|11. PR 분석| PA
    PA -->|API 호출| GEMINI
    GEMINI -->|시나리오| PA

    API -->|12. 시나리오 실행| BE
    BE -->|MCP 호출| BMCP
    BMCP -->|브라우저 제어| MCP_SERVER
    MCP_SERVER -->|페이지 접근| K8S_CLUSTER
    MCP_SERVER -->|스크린샷| BMCP

    BE -->|13. 스크린샷 검증| VV
    VV -->|이미지 분석| GEMINI
    GEMINI -->|검증 결과| VV

    API -->|14. 결과 저장| Tests
    API -->|15. 리포트 전송| SN
    SN -->|알림| SLACK

    API -->|16. 실시간 업데이트| WS
    WS -->|푸시| UI

    style UI fill:#e1f5ff
    style API fill:#fff4e1
    style Auth fill:#ffe1f5
    style Poll fill:#e1ffe1
    style DB fill:#fff4e1
    style K8S fill:#ffe1f5
    style PA fill:#fff4e1
    style BE fill:#e1ffe1
    style VV fill:#fff4e1
    style SN fill:#ffe1f5
```

### 상세 프로세스 플로우 (PAT + Polling)

```mermaid
flowchart TD
    Start([사용자가 레포지토리 링크 입력]) --> InputPAT[PAT 입력]
    InputPAT --> VerifyPAT{PAT 검증}
    VerifyPAT -->|실패| PATError[에러 메시지 표시]
    PATError --> InputPAT
    VerifyPAT -->|성공| CheckAccess{레포지토리 접근 가능?}

    CheckAccess -->|불가능| AccessError[접근 권한 없음]
    AccessError --> InputPAT
    CheckAccess -->|가능| EncryptPAT[PAT 암호화]

    EncryptPAT --> SaveCreds[(DB: 인증 정보 저장)]
    SaveCreds --> SaveSub[(DB: 구독 정보 저장)]
    SaveSub --> Subscribed[구독 완료]

    Subscribed --> StartPolling[Polling 시작<br/>5분 주기]

    StartPolling --> GetSubs[(DB: 구독 목록 조회)]
    GetSubs --> DecryptPAT[PAT 복호화]
    DecryptPAT --> PollPRs[GitHub API: PR 목록 조회]

    PollPRs --> CheckNew{새 PR 또는<br/>업데이트?}
    CheckNew -->|없음| Wait[대기 5분]
    Wait --> GetSubs

    CheckNew -->|있음| GetPRInfo[PR 상세 정보 조회]
    GetPRInfo --> GetDiff[PR Diff 추출]

    GetDiff --> Deploy[쿠버네티스 배포]
    Deploy --> WaitDeploy{배포 완료?}
    WaitDeploy -->|타임아웃| DeployError[배포 실패]
    WaitDeploy -->|성공| DeployURL[PR URL 획득<br/>pr-123.domain.com]

    DeployURL --> Analyze[Gemini로 PR 분석]
    Analyze --> GenScenarios[테스트 시나리오 생성]

    GenScenarios --> LoopStart{시나리오 반복}
    LoopStart -->|다음 시나리오| Execute[Browser MCP 실행]

    Execute --> ActionLoop{액션 반복}
    ActionLoop -->|goto| Navigate[페이지 이동<br/>pr-123.domain.com]
    ActionLoop -->|click| Click[요소 클릭]
    ActionLoop -->|fill| Fill[텍스트 입력]
    ActionLoop -->|wait| Wait[대기]
    ActionLoop -->|screenshot| Screenshot[스크린샷]

    Navigate --> CheckAction{액션 성공?}
    Click --> CheckAction
    Fill --> CheckAction
    Wait --> CheckAction
    Screenshot --> CheckAction

    CheckAction -->|실패| FailResult[시나리오 실패]
    CheckAction -->|성공| NextAction{다음 액션?}

    NextAction -->|있음| ActionLoop
    NextAction -->|없음| VisionCheck[Vision API 검증]

    FailResult --> NextScenario
    VisionCheck --> VisionResult{검증 결과}
    VisionResult -->|통과| PassResult[시나리오 성공]
    VisionResult -->|실패| FailResult

    PassResult --> NextScenario{다음 시나리오?}
    FailResult --> NextScenario
    NextScenario -->|있음| LoopStart
    NextScenario -->|없음| SaveResults[(DB: 테스트 결과 저장)]

    SaveResults --> GenerateReport[리포트 생성]
    GenerateReport --> SendSlack[Slack 알림 전송]
    SendSlack --> UpdateUI[UI 실시간 업데이트]
    UpdateUI --> UpdateLastPoll[(DB: last_polled_at 업데이트)]
    UpdateLastPoll --> Wait

    DeployError --> SendError[에러 알림]
    SendError --> Wait

    style Start fill:#e1f5ff
    style Subscribed fill:#e1ffe1
    style StartPolling fill:#fff4e1
    style Deploy fill:#fff4e1
    style Analyze fill:#fff4e1
    style Execute fill:#e1ffe1
    style VisionCheck fill:#fff4e1
    style SendSlack fill:#ffe1f5
    style UpdateUI fill:#e1f5ff
```

### 데이터 플로우 (PAT + 구독 시스템)

```mermaid
graph LR
    subgraph "User Input"
        REPO_LINK[레포지토리 링크<br/>company/repo-name]
        PAT_INPUT[Personal Access Token<br/>ghp_xxxxx]
    end

    subgraph "Authentication"
        PAT_VERIFY[PAT 검증<br/>GitHub API]
        PAT_ENCRYPT[PAT 암호화<br/>AES-256]
        PAT_STORE[(암호화된 PAT<br/>DB 저장)]
    end

    subgraph "Subscription"
        SUB_INFO[구독 정보<br/>repo, options]
        SUB_STORE[(구독 정보<br/>DB 저장)]
    end

    subgraph "Polling"
        POLL_SCHEDULE[Polling 스케줄러<br/>5분 주기]
        PAT_DECRYPT[PAT 복호화]
        PR_LIST[PR 목록 조회<br/>GitHub API]
        PR_DETECT[새 PR 감지]
    end

    subgraph "Processing"
        PR_DIFF[PR Diff]
        SCENARIOS[테스트 시나리오]
        ACTIONS[브라우저 액션]
        SCREENSHOTS[스크린샷]
        VALIDATION[검증 결과]
    end

    subgraph "Output"
        TEST_RESULTS[(테스트 결과<br/>DB 저장)]
        REPORT[리포트]
        SLACK_MSG[Slack 알림]
        UI_UPDATE[UI 실시간 업데이트]
    end

    REPO_LINK --> PAT_VERIFY
    PAT_INPUT --> PAT_VERIFY
    PAT_VERIFY --> PAT_ENCRYPT
    PAT_ENCRYPT --> PAT_STORE
    REPO_LINK --> SUB_INFO
    SUB_INFO --> SUB_STORE

    SUB_STORE --> POLL_SCHEDULE
    POLL_SCHEDULE --> PAT_DECRYPT
    PAT_STORE --> PAT_DECRYPT
    PAT_DECRYPT --> PR_LIST
    PR_LIST --> PR_DETECT

    PR_DETECT --> PR_DIFF
    PR_DIFF --> SCENARIOS
    SCENARIOS --> ACTIONS
    ACTIONS --> SCREENSHOTS
    SCREENSHOTS --> VALIDATION

    VALIDATION --> TEST_RESULTS
    TEST_RESULTS --> REPORT
    REPORT --> SLACK_MSG
    TEST_RESULTS --> UI_UPDATE

    style REPO_LINK fill:#e1f5ff
    style PAT_INPUT fill:#ffe1e1
    style PAT_VERIFY fill:#fff4e1
    style PAT_ENCRYPT fill:#fff4e1
    style POLL_SCHEDULE fill:#e1ffe1
    style PR_DETECT fill:#e1ffe1
    style SCENARIOS fill:#fff4e1
    style ACTIONS fill:#e1ffe1
    style VALIDATION fill:#fff4e1
    style REPORT fill:#e1ffe1
    style SLACK_MSG fill:#ffe1f5
    style UI_UPDATE fill:#e1f5ff
```

### 컴포넌트 상호작용 (PAT 기반)

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React UI]
    end

    subgraph "API Layer"
        API[Backend API Server]
        AUTH[PAT Auth Module]
        POLL[Polling Service]
        WS[WebSocket/SSE]
    end

    subgraph "Data Layer"
        DB[(Database)]
        CREDS[Credentials Storage]
        SUBS[Subscriptions]
        TESTS[Test Results]
    end

    subgraph "GitHub Integration"
        GH_CLIENT[GitHub API Client]
    end

    subgraph "Core Modules"
        K8S[K8s Deployer]
        PA[PR Analyzer]
        BE[Browser Executor]
        BMCP[Browser MCP Client]
        VV[Vision Validator]
        SN[Slack Notifier]
    end

    UI -->|1. 레포지토리 + PAT| API
    API -->|2. PAT 검증| AUTH
    AUTH -->|3. GitHub API 호출| GH_CLIENT
    GH_CLIENT -->|사용자 정보| AUTH
    AUTH -->|4. 암호화| CREDS
    API -->|5. 구독 저장| SUBS

    POLL -->|6. 주기적 실행| SUBS
    SUBS -->|구독 정보| POLL
    POLL -->|7. PAT 조회| CREDS
    CREDS -->|복호화된 PAT| POLL
    POLL -->|8. PR 조회| GH_CLIENT
    GH_CLIENT -->|PR 목록| POLL
    POLL -->|9. 새 PR 감지| API

    API -->|10. 배포| K8S
    API -->|11. 분석| PA
    API -->|12. 실행| BE
    BE -->|MCP 호출| BMCP
    API -->|13. 검증| VV
    API -->|14. 알림| SN

    API -->|15. 결과 저장| TESTS
    API -->|16. 실시간 푸시| WS
    WS -->|업데이트| UI

    style UI fill:#e1f5ff
    style API fill:#fff4e1
    style AUTH fill:#ffe1f5
    style POLL fill:#e1ffe1
    style DB fill:#fff4e1
    style GH_CLIENT fill:#e1f5ff
    style K8S fill:#ffe1f5
    style PA fill:#fff4e1
    style BE fill:#e1ffe1
    style VV fill:#fff4e1
    style SN fill:#ffe1f5
```
