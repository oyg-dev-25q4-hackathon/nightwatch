# server/services/pr_analyzer_service.py
"""
PR 분석 및 테스트 시나리오 생성 서비스
"""
import json
import os

from vertexai.generative_models import GenerativeModel

from .vertex_ai import get_text_model

class PRAnalyzerService:
    """PR 분석 서비스"""
    
    def __init__(self, base_url=None):
        model_name = os.getenv('VERTEX_MODEL_NAME')
        self.model: GenerativeModel = get_text_model(model_name)
        self.base_url = base_url or os.getenv('BASE_URL', 'localhost:5173')
    
    def analyze_and_generate_scenarios(self, pr_diff, pr_url=None):
        """PR diff를 분석하여 테스트 시나리오 생성"""
        diff_text = self._format_diff(pr_diff)
        
        # preview 브랜치는 항상 preview-dev.oliveyoung.com 사용
        if pr_url:
            print(f"📝 PR URL received: {pr_url}")
            # pr_url이 http:// 또는 https://로 시작하지 않으면 https:// 추가
            if not pr_url.startswith(('http://', 'https://')):
                test_url = f"https://{pr_url}"
            else:
                test_url = pr_url
            print(f"📝 Test URL generated: {test_url}")
        else:
            # pr_url이 없으면 기본값으로 preview-dev.oliveyoung.com 사용
            test_url = "https://preview-dev.oliveyoung.com"
            print(f"📝 Using default preview URL: {test_url}")
        
        prompt = f"""
당신은 E2E 테스트 전문가입니다. 다음 GitHub PR의 변경사항을 심층 분석하고, 테스트해야 할 모든 시나리오를 생성해주세요.

**테스트 대상 사이트:** {test_url}
**기본 사이트:** https://preview-dev.oliveyoung.com

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
        {{"type": "set_viewport", "width": 1920, "height": 1080}},
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

1. 실제로 실행 가능한 액션만 포함 (goto, click, fill, wait, screenshot, set_viewport만 사용)
2. selector는 일반적인 CSS selector 사용 (id, class, tag 등)
3. URL은 {test_url} 또는 상대 경로(/)를 사용
4. JSON 형식만 반환 (마크다운 코드블록 없이)
5. global.oliveyoung.com 사이트의 실제 구조를 고려하여 시나리오 작성
6. **절대 comment 타입의 액션을 생성하지 마세요. 설명은 description 필드에만 작성하세요.**
7. 모바일 테스트가 필요한 경우 set_viewport 액션을 사용하세요 (예: {{"type": "set_viewport", "width": 375, "height": 667}})
8. 각 시나리오는 명확하고 구체적인 expected_result를 포함해야 합니다

**중요:** PR 변경사항을 완전히 커버할 수 있는 충분한 시나리오를 생성하되, 불필요한 중복은 피하세요. 품질과 완전성을 우선시하세요.

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
            
            # pr_url이 있으면 모든 goto 액션의 URL을 pr_url로 교체
            if pr_url:
                # pr_url을 http:// 형식으로 변환
                if not pr_url.startswith(('http://', 'https://')):
                    if pr_url.startswith('localhost') or pr_url.startswith('127.'):
                        pr_url_http = f"http://{pr_url}"
                    else:
                        pr_url_http = f"https://{pr_url}"
                else:
                    pr_url_http = pr_url
                
                print(f"📝 Updating scenario URLs to use: {pr_url_http}")
                
                for scenario in scenarios:
                    for action in scenario.get('actions', []):
                        if action.get('type') == 'goto':
                            url = action.get('url', '')
                            original_url = url
                            
                            # test_url이 포함된 경우 (프롬프트에서 생성된 URL)
                            if test_url in url:
                                action['url'] = pr_url_http
                                print(f"   ✅ Updated URL (test_url match): {original_url} → {pr_url_http}")
                            # localhost가 포함된 경우 (모든 localhost를 preview-dev.oliveyoung.com으로 변경)
                            elif 'localhost' in url or '127.0.0.1' in url:
                                action['url'] = pr_url_http
                                print(f"   ✅ Updated URL (localhost match): {original_url} → {pr_url_http}")
                            # example.com이 포함된 경우
                            elif 'example.com' in url:
                                action['url'] = url.replace('example.com', pr_url.replace('http://', '').replace('https://', ''))
                                if not action['url'].startswith(('http://', 'https://')):
                                    action['url'] = pr_url_http
                                print(f"   ✅ Updated URL (example.com match): {original_url} → {action['url']}")
                            # 상대 경로인 경우 pr_url_http와 결합
                            elif url.startswith('/'):
                                action['url'] = f"{pr_url_http}{url}"
                                print(f"   ✅ Updated relative URL: {original_url} → {action['url']}")
                            # 그 외의 경우 (다른 도메인 등)는 그대로 유지
                            else:
                                print(f"   ℹ️ Keeping original URL: {original_url}")
            
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
        """PR diff를 읽기 쉬운 형식으로 변환 (구조화된 분석 포함)"""
        formatted = []
        
        # 전체 통계
        total_files = len(pr_diff)
        added_lines = 0
        removed_lines = 0
        file_types = {'frontend': [], 'backend': [], 'config': [], 'other': []}
        
        for file in pr_diff:
            filename = file['filename']
            status = file['status']
            patch = file.get('patch', '')
            
            # 파일 타입 분류
            if any(ext in filename for ext in ['.jsx', '.tsx', '.js', '.ts', '.css', '.html', '.vue']):
                file_type = 'frontend'
            elif any(ext in filename for ext in ['.py', '.java', '.go', '.rs', '.cpp', '.c']):
                file_type = 'backend'
            elif any(ext in filename for ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.env']):
                file_type = 'config'
            else:
                file_type = 'other'
            
            file_types[file_type].append(filename)
            
            # 변경된 라인 수 계산
            if patch:
                added = patch.count('\n+') - patch.count('\n+++')
                removed = patch.count('\n-') - patch.count('\n---')
                added_lines += max(0, added)
                removed_lines += max(0, removed)
            
            # 파일 정보 추가
            formatted.append(f"\n{'='*60}")
            formatted.append(f"📄 파일: {filename}")
            formatted.append(f"📊 상태: {status}")
            formatted.append(f"🏷️  타입: {file_type}")
            
            if patch:
                # 주요 변경사항 추출 (함수/컴포넌트 이름 등)
                lines = patch.split('\n')
                changed_functions = []
                for line in lines:
                    if line.startswith('+') and ('function' in line or 'def ' in line or 'const ' in line or 'class ' in line):
                        # 함수/컴포넌트 이름 추출 시도
                        if 'function' in line:
                            parts = line.split('function')
                            if len(parts) > 1:
                                func_name = parts[1].split('(')[0].strip()
                                if func_name:
                                    changed_functions.append(f"추가된 함수: {func_name}")
                        elif 'def ' in line:
                            func_name = line.split('def ')[1].split('(')[0].strip()
                            if func_name:
                                changed_functions.append(f"추가된 함수: {func_name}")
                        elif 'const ' in line and '=' in line:
                            var_name = line.split('const ')[1].split('=')[0].strip()
                            if var_name:
                                changed_functions.append(f"추가된 상수: {var_name}")
                        elif 'class ' in line:
                            class_name = line.split('class ')[1].split('(')[0].split('{')[0].strip()
                            if class_name:
                                changed_functions.append(f"추가된 클래스: {class_name}")
                
                if changed_functions:
                    formatted.append(f"🔧 주요 변경사항:")
                    for func in changed_functions[:5]:  # 최대 5개만
                        formatted.append(f"   - {func}")
                
                # 변경된 라인 수
                if added > 0 or removed > 0:
                    formatted.append(f"📈 변경 라인: +{added} / -{removed}")
                
                # 실제 diff 내용 (너무 길면 일부만)
                if len(patch) > 2000:
                    formatted.append(f"📝 변경사항 (일부):\n{patch[:2000]}...\n(전체 내용은 너무 깁니다)")
                else:
                    formatted.append(f"📝 변경사항:\n{patch}")
            else:
                formatted.append("📝 변경사항: (diff 정보 없음)")
        
        # 요약 정보 추가
        summary = [
            f"\n{'='*60}",
            "📊 PR 변경사항 요약",
            f"{'='*60}",
            f"총 파일 수: {total_files}",
            f"추가된 라인: +{added_lines}",
            f"삭제된 라인: -{removed_lines}",
            f"\n파일 타입별 분류:",
            f"  - 프론트엔드: {len(file_types['frontend'])}개",
            f"  - 백엔드: {len(file_types['backend'])}개",
            f"  - 설정 파일: {len(file_types['config'])}개",
            f"  - 기타: {len(file_types['other'])}개",
        ]
        
        if file_types['frontend']:
            summary.append(f"\n프론트엔드 파일:")
            for f in file_types['frontend'][:5]:
                summary.append(f"  - {f}")
        
        if file_types['backend']:
            summary.append(f"\n백엔드 파일:")
            for f in file_types['backend'][:5]:
                summary.append(f"  - {f}")
        
        return '\n'.join(summary + formatted)
    
    def _get_default_scenarios(self, pr_url=None):
        """기본 테스트 시나리오"""
        test_url = pr_url if pr_url else "https://preview-dev.oliveyoung.com"
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

