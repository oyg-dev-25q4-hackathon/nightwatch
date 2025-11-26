# server/services/pr_analyzer_service.py
"""
PR 분석 및 테스트 시나리오 생성 서비스
"""
import google.generativeai as genai
import os
import json

class PRAnalyzerService:
    """PR 분석 서비스"""
    
    def __init__(self, base_url=None):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.base_url = base_url or os.getenv('BASE_URL', 'localhost:5173')
    
    def analyze_and_generate_scenarios(self, pr_diff, pr_url=None):
        """PR diff를 분석하여 테스트 시나리오 생성"""
        diff_text = self._format_diff(pr_diff)
        test_url = pr_url if pr_url else f"https://{self.base_url}"
        
        prompt = f"""
당신은 E2E 테스트 전문가입니다. 다음 GitHub PR의 변경사항을 분석하고, 테스트해야 할 시나리오를 생성해주세요.

**테스트 대상 사이트:** {test_url}
**기본 사이트:** https://{self.base_url}

PR 변경사항:

{diff_text}

다음 형식의 JSON으로 응답해주세요:

{{
  "scenarios": [
    {{
      "name": "테스트 시나리오 이름",
      "description": "시나리오 설명",
      "actions": [
        {{"type": "goto", "url": "{test_url}"}},
        {{"type": "wait", "seconds": 2}},
        {{"type": "click", "selector": "#some-button"}},
        {{"type": "fill", "selector": "#input-field", "value": "test-value"}},
        {{"type": "screenshot", "name": "result"}}
      ],
      "expected_result": "예상 결과 설명"
    }}
  ]
}}

**중요 규칙:**

1. 실제로 실행 가능한 액션만 포함
2. selector는 일반적인 CSS selector 사용 (id, class, tag 등)
3. 최소 3개, 최대 5개의 시나리오 생성
4. 변경된 코드와 직접 관련된 기능만 테스트
5. URL은 {test_url} 또는 상대 경로(/)를 사용
6. JSON 형식만 반환 (마크다운 코드블록 없이)
7. global.oliveyoung.com 사이트의 실제 구조를 고려하여 시나리오 작성

"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            scenarios_data = json.loads(response_text)
            scenarios = scenarios_data.get('scenarios', [])
            
            if pr_url:
                for scenario in scenarios:
                    for action in scenario.get('actions', []):
                        if action.get('type') == 'goto':
                            url = action['url']
                            if self.base_url in url or 'example.com' in url:
                                action['url'] = url.replace('example.com', pr_url).replace(self.base_url, pr_url)
            
            return scenarios
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating scenarios: {error_msg}")
            # API 키 관련 에러인 경우 예외를 다시 던짐
            if 'API key' in error_msg or 'API_KEY' in error_msg or 'API key not valid' in error_msg:
                raise ValueError(f"Gemini API 키가 유효하지 않습니다: {error_msg}")
            # 그 외의 경우 기본 시나리오 반환 (기존 동작 유지)
            return self._get_default_scenarios(pr_url)
    
    def _format_diff(self, pr_diff):
        """PR diff를 읽기 쉬운 형식으로 변환"""
        formatted = []
        for file in pr_diff:
            formatted.append(f"\n파일: {file['filename']}")
            formatted.append(f"상태: {file['status']}")
            if file.get('patch'):
                formatted.append(f"변경사항:\n{file['patch']}")
        return '\n'.join(formatted)
    
    def _get_default_scenarios(self, pr_url=None):
        """기본 테스트 시나리오"""
        test_url = pr_url if pr_url else f"https://{self.base_url}"
        return [
            {
                "name": "홈페이지 접속 테스트",
                "description": "메인 페이지가 정상적으로 로드되는지 확인",
                "actions": [
                    {"type": "goto", "url": test_url},
                    {"type": "wait", "seconds": 2},
                    {"type": "screenshot", "name": "homepage"}
                ],
                "expected_result": "홈페이지가 정상적으로 표시됨"
            }
        ]

