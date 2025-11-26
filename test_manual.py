# test_manual.py
from src.pr_analyzer import PRAnalyzer
from src.browser_executor import BrowserExecutor
from src.vision_validator import VisionValidator

# 1. 시나리오 생성 테스트
analyzer = PRAnalyzer()
scenarios = analyzer.analyze_and_generate_scenarios([{
    'filename': 'src/discount.js',
    'status': 'modified',
    'patch': '- return price * 0.1\n+ return price * 0.2'
}])

print("Generated scenarios:", scenarios)

# 2. 브라우저 테스트
executor = BrowserExecutor("videos/test_manual")
result = executor.execute_scenario(scenarios[0])
executor.close()

print("Test result:", result)

# 3. Vision 검증
validator = VisionValidator()
validation = validator.validate_screenshot(
    result['screenshot'],
    result['expected_result']
)

print("Validation:", validation)

