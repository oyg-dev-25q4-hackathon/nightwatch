# server/services/vision_validator.py
import google.generativeai as genai
import os
import json
import base64
from PIL import Image
import io

class VisionValidator:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def validate_screenshot(self, screenshot_b64, expected_result):
        """스크린샷이 예상 결과와 일치하는지 검증"""
        
        try:
            # base64를 PIL Image로 변환
            image_data = base64.b64decode(screenshot_b64)
            image = Image.open(io.BytesIO(image_data))
            
            prompt = f"""
당신은 UI/UX 테스트 전문가입니다. 다음 스크린샷을 분석하고, 예상 결과와 일치하는지 검증해주세요.

**예상 결과:**

{expected_result}

**검증 항목:**

1. 예상한 페이지/화면이 맞는가?
2. 에러 메시지나 문제가 보이는가?
3. UI 요소들이 정상적으로 표시되는가?
4. 레이아웃이 깨지지 않았는가?

다음 JSON 형식으로 응답해주세요:

{{
  "is_valid": true 또는 false,
  "confidence": 0.0 ~ 1.0 사이의 신뢰도,
  "reason": "판단 근거를 한국어로 상세히 설명",
  "issues": ["발견된 문제점들의 리스트"],
  "suggestions": ["개선 제안사항들"]
}}

JSON만 반환하세요 (마크다운 코드블록 없이).

"""
            
            response = self.model.generate_content([prompt, image])
            response_text = response.text.strip()
            
            # 마크다운 코드블록 제거
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            validation_result = json.loads(response_text)
            return validation_result
            
        except Exception as e:
            print(f"Vision validation error: {e}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "reason": f"검증 중 오류 발생: {str(e)}",
                "issues": [str(e)],
                "suggestions": []
            }

