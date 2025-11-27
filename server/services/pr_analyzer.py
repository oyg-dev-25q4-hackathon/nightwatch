# src/pr_analyzer.py
import json
import os

from vertexai.generative_models import GenerativeModel

from .vertex_ai import get_text_model

class PRAnalyzer:
    def __init__(self, base_url=None):
        """
        Args:
            base_url: 기본 웹사이트 URL (기본값: global.oliveyoung.com)
        """
        model_name = os.getenv('VERTEX_MODEL_NAME')
        self.model: GenerativeModel = get_text_model(model_name)
        self.base_url = base_url or os.getenv('BASE_URL', 'localhost:5173')
    
    def analyze_and_generate_scenarios(self, pr_diff, pr_url=None):
        """
        PR diff를 분석하여 테스트 시나리오 생성
        
        Args:
            pr_diff: PR 변경사항
            pr_url: PR 배포 URL (있을 경우 시나리오에 사용)
        """
        
        # PR diff를 텍스트로 변환
        diff_text = self._format_diff(pr_diff)
        
        # 테스트 대상 URL
        test_url = pr_url if pr_url else f"https://{self.base_url}"
        
        prompt = f"""
당신은 E2E 테스트 전문가입니다. 다음 GitHub PR의 변경사항을 심층 분석하고, 테스트해야 할 모든 시나리오를 생성해주세요.

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

**시나리오 생성 전략:**

PR 변경사항을 철저히 분석하여 다음을 고려하세요:

1. **변경사항의 범위와 복잡도 평가**
   - 단순한 버그 수정이나 스타일 변경: 최소한의 핵심 시나리오만 생성
   - 새로운 기능 추가: 해당 기능의 모든 주요 사용자 플로우를 테스트하는 시나리오 생성
   - 대규모 리팩토링: 영향받는 모든 기능에 대한 포괄적인 시나리오 생성
   - 여러 파일/컴포넌트 변경: 각 변경사항에 대해 독립적인 시나리오 생성

2. **테스트 우선순위 결정**
   - 핵심 기능 (사용자 인증, 결제, 데이터 저장 등): 반드시 포함
   - 변경된 UI 컴포넌트: 해당 컴포넌트의 모든 상호작용 시나리오
   - API 엔드포인트 변경: 프론트엔드에서 해당 API를 호출하는 모든 플로우
   - 라우팅/네비게이션 변경: 모든 관련 페이지 이동 시나리오

3. **시나리오 개수 결정 원칙**
   - PR의 복잡도와 변경 범위에 따라 필요한 만큼 생성
   - 각 주요 변경사항마다 최소 1개 이상의 시나리오 생성
   - 단순 변경: 1-3개, 중간 복잡도: 3-7개, 복잡한 변경: 7개 이상
   - 개수 제한 없음 - PR을 완전히 커버할 수 있는 만큼 생성

4. **시나리오 품질 기준**
   - 각 시나리오는 독립적으로 실행 가능해야 함
   - 변경사항과 직접적으로 관련된 기능만 테스트
   - 중복되거나 불필요한 시나리오는 제외
   - 각 시나리오는 명확한 목적과 예상 결과를 가져야 함

**기술적 규칙:**

1. 실제로 실행 가능한 액션만 포함
2. selector는 일반적인 CSS selector 사용 (id, class, tag 등)
3. URL은 {test_url} 또는 상대 경로(/)를 사용
4. JSON 형식만 반환 (마크다운 코드블록 없이)
5. global.oliveyoung.com 사이트의 실제 구조를 고려하여 시나리오 작성
6. 각 시나리오는 명확하고 구체적인 expected_result를 포함해야 합니다

**중요:** PR 변경사항을 완전히 커버할 수 있는 충분한 시나리오를 생성하되, 불필요한 중복은 피하세요. 품질과 완전성을 우선시하세요.

"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # 마크다운 코드블록 제거
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            scenarios_data = json.loads(response_text)
            scenarios = scenarios_data.get('scenarios', [])
            
            # PR URL이 있으면 시나리오의 URL 업데이트
            if pr_url:
                for scenario in scenarios:
                    for action in scenario.get('actions', []):
                        if action.get('type') == 'goto':
                            url = action['url']
                            if self.base_url in url or 'example.com' in url:
                                action['url'] = url.replace('example.com', pr_url).replace(self.base_url, pr_url)
            
            return scenarios
            
        except Exception as e:
            print(f"Error generating scenarios: {e}")
            # 기본 시나리오 반환
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

