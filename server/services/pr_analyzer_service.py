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

