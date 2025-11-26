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
        self.base_url = base_url or os.getenv('BASE_URL', 'localhost:5173')
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
            scenario: 테스트 시나리오 딕셔너리 (원본 형태 또는 결과 형태)
            pr_url: PR 배포 URL (있을 경우 시나리오의 URL을 대체)
        """
        # 시나리오가 결과 형태인지 원본 형태인지 확인
        scenario_name = scenario.get('scenario_name') or scenario.get('name', 'Unknown Scenario')
        description = scenario.get('description', '')
        expected_result = scenario.get('expected_result', '')
        actions = scenario.get('actions', [])
        
        # actions가 없고 actions_executed가 있으면 원본 actions 추출 시도
        if not actions and 'actions_executed' in scenario:
            actions_executed = scenario.get('actions_executed', [])
            for action_result in actions_executed:
                if 'action' in action_result:
                    actions.append(action_result['action'])
                elif 'type' in action_result:
                    # action_result 자체가 action 형태일 수 있음
                    action = {k: v for k, v in action_result.items() 
                             if k not in ['success', 'error', 'screenshot', 'screenshot_path']}
                    if action:
                        actions.append(action)
        
        if not actions:
            return {
                'scenario_name': scenario_name,
                'description': description,
                'expected_result': expected_result,
                'actions_executed': [],
                'success': False,
                'error': '시나리오에 실행할 액션이 없습니다.',
                'screenshot': None
            }
        
        result = {
            'scenario_name': scenario_name,
            'description': description,
            'expected_result': expected_result,
            'actions_executed': [],
            'success': True,
            'error': None,
            'screenshot': None
        }
        
        try:
            for action in actions:
                # PR URL이 있으면 goto 액션의 URL을 대체
                if action['type'] == 'goto' and pr_url:
                    original_url = action['url']
                    # 상대 경로인 경우 PR URL과 결합
                    if original_url.startswith('/'):
                        action['url'] = f"https://{pr_url}{original_url}"
                    elif not original_url.startswith('http'):
                        action['url'] = f"https://{pr_url}/{original_url}"
                    else:
                        # 전체 URL인 경우
                        # 이미 pr_url이 포함되어 있으면 교체하지 않음 (중복 방지)
                        if pr_url in original_url:
                            action['url'] = original_url
                        else:
                            # example.com 또는 base_url을 pr_url로 교체
                            if 'example.com' in original_url:
                                action['url'] = original_url.replace('example.com', pr_url)
                            elif self.base_url in original_url:
                                # base_url을 pr_url로 교체 (도메인 부분만)
                                # https://pr-1.global.oliveyoung.com -> https://pr-1.global.oliveyoung.com (이미 PR URL)
                                # https://global.oliveyoung.com -> https://pr-1.global.oliveyoung.com
                                url_parts = original_url.split('://')
                                if len(url_parts) == 2:
                                    protocol = url_parts[0]
                                    domain_path = url_parts[1]
                                    # 도메인 부분만 교체
                                    if domain_path.startswith(self.base_url):
                                        # global.oliveyoung.com/path -> pr-1.global.oliveyoung.com/path
                                        action['url'] = f"{protocol}://{pr_url}{domain_path[len(self.base_url):]}"
                                    elif f'.{self.base_url}' in domain_path:
                                        # subdomain.global.oliveyoung.com -> subdomain.pr-1.global.oliveyoung.com (이건 이상하지만)
                                        action['url'] = original_url.replace(f'.{self.base_url}', f'.{pr_url}')
                                    else:
                                        # base_url이 중간에 있는 경우
                                        action['url'] = original_url.replace(self.base_url, pr_url)
                                else:
                                    action['url'] = original_url.replace(self.base_url, pr_url)
                            else:
                                # 다른 도메인인 경우 그대로 사용
                                action['url'] = original_url
                
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
                result = self._execute_action_mcp(action)
                # MCP 연결 실패 시 Playwright로 폴백
                if not result.get('success') and result.get('error') and 'Connection' in result.get('error', ''):
                    print(f"⚠️ MCP 연결 실패, Playwright로 폴백: {result.get('error')}")
                    # Playwright 초기화 (아직 안 되어 있다면)
                    if not self.playwright:
                        self._init_playwright()
                    return self._execute_action_playwright(action)
                return result
            else:
                return self._execute_action_playwright(action)
                
        except Exception as e:
            return {
                'action': action,
                'success': False,
                'error': str(e)
            }
    
    def _init_playwright(self):
        """Playwright 초기화 (폴백용)"""
        if self.playwright:
            return
        
        from ..config import VIDEOS_DIR
        self.video_dir = os.path.join(VIDEOS_DIR, "fallback")
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
    
    def _execute_action_mcp(self, action):
        """Browser MCP를 사용하여 액션 실행"""
        action_type = action['type']
        
        try:
            if action_type == 'goto':
                result = self.mcp_client.navigate(action['url'])
            elif action_type == 'fill':
                result = self.mcp_client.fill(action['selector'], action['value'])
            elif action_type == 'click':
                result = self.mcp_client.click(action['selector'])
            elif action_type == 'wait':
                result = self.mcp_client.wait(action.get('seconds', 1))
                return {'action': action, 'success': result.get('success', True)}
            elif action_type == 'screenshot':
                result = self.mcp_client.screenshot(full_page=True)
                if result.get('success'):
                    screenshot_data = result.get('screenshot')
                    screenshot_b64 = screenshot_data if isinstance(screenshot_data, str) else base64.b64encode(screenshot_data).decode()
                    return {'action': action, 'success': True, 'screenshot': screenshot_b64}
                return {'action': action, 'success': False, 'error': result.get('error')}
            else:
                return {'action': action, 'success': False, 'error': f'Unknown action type: {action_type}'}
            
            if not result.get('success') and result.get('fallback'):
                raise Exception(result.get('error', 'MCP connection failed'))
            return {'action': action, 'success': result.get('success', False), 'error': result.get('error')}
        except Exception as e:
            # MCP 연결 실패 시 예외를 다시 발생시켜 폴백 로직으로 전달
            return {'action': action, 'success': False, 'error': str(e), 'fallback': True}
    
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
