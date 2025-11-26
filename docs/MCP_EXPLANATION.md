# Browser MCP Server URL 설명

## 🤔 MCP_SERVER_URL이란?

`MCP_SERVER_URL`은 **Browser MCP (Model Context Protocol) 서버**의 주소를 지정하는 환경 변수입니다.

## 📍 사용 위치

`src/browser_mcp_client.py`에서 사용됩니다:

```python
# BrowserMCPClient 클래스에서
self.mcp_server_url = mcp_server_url or os.getenv('MCP_SERVER_URL', 'http://localhost:3000')
```

## 🔄 동작 방식

1. **Browser MCP 사용 시**:
   - `USE_BROWSER_MCP=true`로 설정되어 있고
   - MCP 서버가 실행 중이면
   - 브라우저 자동화를 MCP 서버를 통해 수행

2. **Playwright 폴백**:
   - MCP 서버가 없거나 연결 실패 시
   - 자동으로 Playwright로 전환하여 브라우저 자동화 수행

## ⚙️ 설정 방법

### 옵션 1: MCP 서버 사용 (선택사항)

별도의 Browser MCP 서버를 실행하고 URL을 설정:

```bash
# .env 파일
MCP_SERVER_URL=http://localhost:3000
USE_BROWSER_MCP=true
```

### 옵션 2: Playwright만 사용 (권장)

MCP 서버 없이 Playwright만 사용:

```bash
# .env 파일
USE_BROWSER_MCP=false
# MCP_SERVER_URL은 설정하지 않아도 됨
```

## 💡 실제 사용 시나리오

### 현재 구현 상태

현재 코드는 **MCP 서버가 없어도 정상 작동**합니다:

1. `USE_BROWSER_MCP=true`로 설정되어 있어도
2. MCP 서버에 연결 실패 시 자동으로 Playwright로 폴백
3. 모든 브라우저 자동화 기능이 Playwright로 수행됨

### 권장 설정

**대부분의 경우 Playwright만 사용하는 것을 권장합니다:**

```bash
# .env 파일
USE_BROWSER_MCP=false
```

이렇게 설정하면:
- ✅ MCP 서버 설정 불필요
- ✅ Playwright로 모든 기능 작동
- ✅ 추가 서버 관리 불필요

## 🎯 MCP 서버가 필요한 경우

다음과 같은 경우에만 MCP 서버가 필요합니다:

1. **Cursor의 Browser MCP 확장 기능 사용**
   - Cursor IDE의 브라우저 확장 기능을 통합하려는 경우

2. **별도의 브라우저 자동화 서버 운영**
   - 중앙화된 브라우저 자동화 서버를 운영하는 경우

3. **특정 브라우저 환경 요구**
   - MCP 서버에서만 제공하는 특정 기능이 필요한 경우

## 📝 결론

**MCP_SERVER_URL은 선택사항입니다.**

- 설정하지 않아도 됨 (기본값: `http://localhost:3000`)
- `USE_BROWSER_MCP=false`로 설정하면 MCP 관련 코드를 건너뛰고 Playwright만 사용
- 대부분의 경우 Playwright만으로도 모든 기능이 정상 작동

## 🔧 설정 예시

### 최소 설정 (Playwright만 사용)

```bash
# .env
USE_BROWSER_MCP=false
# MCP_SERVER_URL은 설정하지 않음
```

### MCP 서버 사용 (선택사항)

```bash
# .env
USE_BROWSER_MCP=true
MCP_SERVER_URL=http://localhost:3000
```

