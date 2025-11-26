# src/browser_mcp_client.py
"""
Browser MCP 클라이언트
MCP 서버와 통신하여 브라우저 자동화 기능을 제공
"""
import os
import json
import base64
import time
import requests
from typing import Dict, List, Optional

class BrowserMCPClient:
    """Browser MCP 서버와 통신하는 클라이언트"""
    
    def __init__(self, mcp_server_url=None):
        """
        Args:
            mcp_server_url: MCP 서버 URL (기본값: 환경변수에서 가져옴)
        """
        self.mcp_server_url = mcp_server_url or os.getenv('MCP_SERVER_URL', 'http://localhost:3000')
        self.session_id = None
    
    def navigate(self, url: str) -> Dict:
        """URL로 이동"""
        return self._call_mcp('browser_navigate', {'url': url})
    
    def click(self, selector: str, element: str = None) -> Dict:
        """요소 클릭"""
        params = {'selector': selector}
        if element:
            params['element'] = element
        return self._call_mcp('browser_click', params)
    
    def fill(self, selector: str, text: str) -> Dict:
        """텍스트 입력"""
        return self._call_mcp('browser_fill', {'selector': selector, 'text': text})
    
    def screenshot(self, full_page: bool = False) -> Dict:
        """스크린샷 촬영"""
        return self._call_mcp('browser_screenshot', {'full_page': full_page})
    
    def wait(self, seconds: float) -> Dict:
        """대기"""
        time.sleep(seconds)
        return {'success': True}
    
    def snapshot(self) -> Dict:
        """페이지 스냅샷 (접근성 정보)"""
        return self._call_mcp('browser_snapshot', {})
    
    def _call_mcp(self, method: str, params: Dict) -> Dict:
        """
        MCP 서버에 요청 전송
        
        실제 구현은 MCP 서버의 API에 따라 다를 수 있음
        """
        try:
            # MCP 서버와의 통신 방식에 따라 구현
            # 예시 1: HTTP REST API
            response = requests.post(
                f"{self.mcp_server_url}/mcp/call",
                json={
                    'method': method,
                    'params': params
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # MCP 서버가 없는 경우 Playwright로 폴백
            print(f"⚠️ MCP server not available, using fallback: {e}")
            return {'success': False, 'error': str(e), 'fallback': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

