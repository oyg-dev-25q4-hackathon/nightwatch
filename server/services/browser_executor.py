# server/services/browser_executor.py
"""
Browser MCP를 사용하는 브라우저 실행기
MCP 서버를 통해 브라우저 자동화를 수행
"""
import base64
import time
import os
from .browser_mcp_client import BrowserMCPClient
from playwright.sync_api import sync_playwright

class BrowserExecutor:
    """
    Browser MCP를 사용하여 시나리오를 실행하는 클래스
    MCP 서버가 없을 경우 Playwright로 폴백
    """
    def __init__(self, video_dir=None, use_mcp=True, base_url=None):
        """
        Args:
            video_dir: 비디오 저장 디렉토리 (MCP 사용 시 무시됨)
            use_mcp: Browser MCP 사용 여부 (기본값: True)
            base_url: 기본 URL (기본값: global.oliveyoung.com)
        """
        self.base_url = base_url or os.getenv('BASE_URL', 'global.oliveyoung.com')
        self.use_mcp = use_mcp and os.getenv('USE_BROWSER_MCP', 'true').lower() == 'true'
        
        if self.use_mcp:
            self.mcp_client = BrowserMCPClient()
            self.playwright = None
            self.browser = None
            self.page = None
        else:
            # Playwright 폴백
            from ..config import VIDEOS_DIR
            self.video_dir = video_dir or os.path.join(VIDEOS_DIR, "fallback")
            os.makedirs(self.video_dir, exist_ok=True)
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                record_video_dir=self.video_dir,
                record_video_size={'width': 1920, 'height': 1080}
            )
            self.page = self.context.new_page()
            self.mcp_client = None
    
    def execute_scenario(self, scenario, pr_url=None):
        """
        시나리오 실행
        
        Args:
            scenario: 테스트 시나리오 딕셔너리
            pr_url: PR 배포 URL (있을 경우 시나리오의 URL을 대체)
        """
        result = {
            'scenario_name': scenario['name'],
            'description': scenario['description'],
            'expected_result': scenario['expected_result'],
            'actions_executed': [],
            'success': True,
            'error': None,
            'screenshot': None
        }
        
        try:
            for action in scenario['actions']:
                # PR URL이 있으면 goto 액션의 URL을 대체
                if action['type'] == 'goto' and pr_url:
                    # 상대 경로인 경우 PR URL과 결합
                    if action['url'].startswith('/'):
                        action['url'] = f"https://{pr_url}{action['url']}"
                    elif not action['url'].startswith('http'):
                        action['url'] = f"https://{pr_url}/{action['url']}"
                    else:
                        # 전체 URL인 경우 도메인만 교체
                        if self.base_url in action['url'] or 'example.com' in action['url']:
                            action['url'] = action['url'].replace('example.com', pr_url).replace(self.base_url, pr_url)
                
                action_result = self._execute_action(action)
                result['actions_executed'].append(action_result)
                
                if not action_result['success']:
                    result['success'] = False
                    result['error'] = action_result.get('error')
                    break
            
            # 최종 스크린샷
            if result['success']:
                screenshot_result = self._take_screenshot()
                if screenshot_result['success']:
                    result['screenshot'] = screenshot_result.get('screenshot')
                    result['screenshot_path'] = screenshot_result.get('screenshot_path')
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def _execute_action(self, action):
        """개별 액션 실행"""
        action_type = action['type']
        
        try:
            if self.use_mcp and self.mcp_client:
                return self._execute_action_mcp(action)
            else:
                return self._execute_action_playwright(action)
                
        except Exception as e:
            return {
                'action': action,
                'success': False,
                'error': str(e)
            }
    
    def _execute_action_mcp(self, action):
        """Browser MCP를 사용하여 액션 실행"""
        action_type = action['type']
        
        if action_type == 'goto':
            result = self.mcp_client.navigate(action['url'])
            return {'action': action, 'success': result.get('success', False), 'error': result.get('error')}
        
        elif action_type == 'fill':
            result = self.mcp_client.fill(action['selector'], action['value'])
            return {'action': action, 'success': result.get('success', False), 'error': result.get('error')}
        
        elif action_type == 'click':
            result = self.mcp_client.click(action['selector'])
            return {'action': action, 'success': result.get('success', False), 'error': result.get('error')}
        
        elif action_type == 'wait':
            result = self.mcp_client.wait(action.get('seconds', 1))
            return {'action': action, 'success': result.get('success', True)}
        
        elif action_type == 'screenshot':
            result = self.mcp_client.screenshot(full_page=True)
            if result.get('success'):
                screenshot_data = result.get('screenshot')
                # MCP에서 받은 스크린샷을 base64로 변환
                screenshot_b64 = screenshot_data if isinstance(screenshot_data, str) else base64.b64encode(screenshot_data).decode()
                return {
                    'action': action,
                    'success': True,
                    'screenshot': screenshot_b64
                }
            return {'action': action, 'success': False, 'error': result.get('error')}
        
        else:
            return {
                'action': action,
                'success': False,
                'error': f'Unknown action type: {action_type}'
            }
    
    def _execute_action_playwright(self, action):
        """Playwright를 사용하여 액션 실행 (폴백)"""
        action_type = action['type']
        
        if action_type == 'goto':
            self.page.goto(action['url'], wait_until='networkidle', timeout=30000)
            return {'action': action, 'success': True}
        
        elif action_type == 'fill':
            self.page.fill(action['selector'], action['value'])
            return {'action': action, 'success': True}
        
        elif action_type == 'click':
            self.page.click(action['selector'])
            return {'action': action, 'success': True}
        
        elif action_type == 'wait':
            time.sleep(action.get('seconds', 1))
            return {'action': action, 'success': True}
        
        elif action_type == 'screenshot':
            screenshot_bytes = self.page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            return {
                'action': action,
                'success': True,
                'screenshot': screenshot_b64
            }
        
        else:
            return {
                'action': action,
                'success': False,
                'error': f'Unknown action type: {action_type}'
            }
    
    def _take_screenshot(self):
        """스크린샷 촬영"""
        try:
            if self.use_mcp and self.mcp_client:
                result = self.mcp_client.screenshot(full_page=True)
                if result.get('success'):
                    screenshot_data = result.get('screenshot')
                    screenshot_b64 = screenshot_data if isinstance(screenshot_data, str) else base64.b64encode(screenshot_data).decode()
                    
                    # 파일로 저장
                    from ..config import SCREENSHOTS_DIR
                    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
                    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"mcp_screenshot_{int(time.time())}.png")
                    screenshot_bytes = base64.b64decode(screenshot_b64)
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                    return {
                        'success': True,
                        'screenshot': screenshot_b64,
                        'screenshot_path': screenshot_path
                    }
            else:
                screenshot_bytes = self.page.screenshot(full_page=True)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                
                from ..config import SCREENSHOTS_DIR
                os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"playwright_screenshot_{int(time.time())}.png")
                with open(screenshot_path, 'wb') as f:
                    f.write(screenshot_bytes)
                
                return {
                    'success': True,
                    'screenshot': screenshot_b64,
                    'screenshot_path': screenshot_path
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def close(self):
        """브라우저 종료"""
        if self.playwright:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            self.playwright.stop()
