# Browser MCP 서버 설정 가이드

## 📋 개요

Browser MCP 서버는 선택사항입니다. 현재 프로젝트는 **MCP 서버가 없어도 자동으로 Playwright로 폴백**되어 정상 작동합니다.

## 🎯 두 가지 옵션

### 옵션 1: Playwright만 사용 (권장) ⭐

**가장 간단하고 권장되는 방법입니다.**

```bash
# .env 파일
USE_BROWSER_MCP=false
```

**장점:**

- ✅ 추가 서버 설치/관리 불필요
- ✅ 모든 브라우저 자동화 기능 정상 작동
- ✅ 안정적이고 검증된 방식

### 옵션 2: Browser MCP 서버 사용

MCP 서버를 사용하려면 별도의 MCP 서버를 실행해야 합니다.

## 🔧 Browser MCP 서버 설정 방법

### 방법 1: Cursor의 Browser MCP 확장 사용

Cursor IDE를 사용하는 경우, Browser MCP 확장 기능을 사용할 수 있습니다:

1. **Cursor 설정 확인**

   - Cursor → Settings → Extensions → Browser MCP
   - MCP 서버가 자동으로 실행됨

2. **환경 변수 설정**
   ```bash
   # .env 파일
   USE_BROWSER_MCP=true
   MCP_SERVER_URL=http://localhost:3000
   ```

### 방법 2: 별도 MCP 서버 실행

표준 MCP 서버를 별도로 실행하는 경우:

#### 1. MCP 서버 설치

```bash
# 예시: browserbase MCP 서버
git clone https://github.com/browserbase/mcp-server-browserbase.git
cd mcp-server-browserbase
npm install && npm run build
```

#### 2. MCP 서버 실행

```bash
# MCP 서버를 포트 3000에서 실행
node dist/cli.js --port 3000
```

#### 3. 환경 변수 설정

```bash
# .env 파일
USE_BROWSER_MCP=true
MCP_SERVER_URL=http://localhost:3000
```

#### 4. 서버 확인

MCP 서버가 정상 실행되었는지 확인:

```bash
curl http://localhost:3000/health
```

## ⚠️ 현재 프로젝트의 MCP 통신 방식

현재 프로젝트는 다음과 같은 방식으로 MCP 서버와 통신합니다:

```python
# server/services/browser_mcp_client.py
POST http://localhost:3000/mcp/call
{
    "method": "browser_navigate",
    "params": {"url": "https://example.com"}
}
```

**중요:** 표준 MCP 서버는 이 API 형식을 지원하지 않을 수 있습니다.
현재 프로젝트는 **Playwright 폴백**이 자동으로 작동하도록 설계되어 있습니다.

## 💡 권장 사항

**대부분의 경우 Playwright만 사용하는 것을 권장합니다:**

1. **설정 간단**: `.env`에 `USE_BROWSER_MCP=false`만 설정
2. **안정적**: 검증된 Playwright 라이브러리 사용
3. **추가 관리 불필요**: 별도 서버 실행/관리 불필요

## 🔄 자동 폴백 동작

현재 코드는 다음과 같이 작동합니다:

1. `USE_BROWSER_MCP=true`로 설정되어 있어도
2. MCP 서버 연결 실패 시 **자동으로 Playwright로 폴백**
3. 모든 브라우저 자동화가 Playwright로 수행됨

따라서 **MCP 서버 없이도 정상 작동**합니다!

## 📝 결론

- **간단하게 사용**: `USE_BROWSER_MCP=false` 설정 (권장)
- **MCP 서버 사용**: 별도 MCP 서버 설치 및 실행 필요
- **자동 폴백**: MCP 서버가 없어도 Playwright로 자동 전환
