# server/services/slack_notifier.py
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import json
from datetime import datetime

class SlackNotifier:
    def __init__(self):
        self.client = WebClient(token=os.getenv('SLACK_TOKEN'))
        self.channel = os.getenv('SLACK_CHANNEL', '#test-alerts')
    
    def send_test_report(self, pr, test_results, timestamp, pr_url=None):
        """테스트 결과 리포트 전송"""
        
        # 통계 계산
        total = len(test_results)
        success = sum(1 for r in test_results if r['success'])
        failed = total - success
        
        # 검증 결과 분석
        validation_failed = sum(
            1 for r in test_results 
            if r.get('validation') and not r['validation'].get('is_valid', True)
        )
        
        # 메시지 작성
        status_emoji = "✅" if failed == 0 else "🚨"
        message_blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} NightWatch E2E Test Report"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*PR:* <{pr.html_url}|#{pr.number} {pr.title}>"},
                    {"type": "mrkdwn", "text": f"*Author:* {pr.user.login}"},
                    {"type": "mrkdwn", "text": f"*Total Tests:* {total}"},
                    {"type": "mrkdwn", "text": f"*Success:* {success} | *Failed:* {failed}"},
                ]
            }
        ]
        
        # PR 배포 URL 추가
        if pr_url:
            message_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🌐 Test URL:* <{pr_url}|{pr_url}>"
                }
            })
        
        message_blocks.append({"type": "divider"})
        
        # 실패한 테스트 상세 정보
        if failed > 0:
            message_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*❌ Failed Tests:*"
                }
            })
            
            for result in test_results:
                if not result['success']:
                    message_blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• *{result['scenario_name']}*\n  Error: `{result['error']}`"
                        }
                    })
        
        # Vision 검증 실패
        if validation_failed > 0:
            message_blocks.append({"type": "divider"})
            message_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*👁️ Vision Validation Issues: {validation_failed}*"
                }
            })
            
            for result in test_results:
                validation = result.get('validation')
                if validation and not validation.get('is_valid', True):
                    issues_text = '\n'.join(f"  - {issue}" for issue in validation.get('issues', []))
                    message_blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• *{result['scenario_name']}*\n{issues_text}"
                        }
                    })
        
        # 슬랙 메시지 전송
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=message_blocks,
                text=f"E2E Test Report for PR #{pr.number}"
            )
            
            # 스크린샷 업로드
            self._upload_screenshots(test_results, response['ts'])
            
            # 상세 리포트 JSON 파일 업로드
            self._upload_detailed_report(pr, test_results, timestamp, response['ts'])
            
        except SlackApiError as e:
            print(f"Slack API Error: {e.response['error']}")
    
    def _upload_screenshots(self, test_results, thread_ts):
        """스크린샷 업로드"""
        for result in test_results:
            if result.get('screenshot_path'):
                try:
                    self.client.files_upload_v2(
                        channel=self.channel,
                        file=result['screenshot_path'],
                        title=f"{result['scenario_name']} - Screenshot",
                        thread_ts=thread_ts
                    )
                except Exception as e:
                    print(f"Screenshot upload error: {e}")
    
    def _upload_detailed_report(self, pr, test_results, timestamp, thread_ts):
        """상세 리포트 JSON 업로드"""
        report = {
            "timestamp": timestamp,
            "pr": {
                "number": pr.number,
                "title": pr.title,
                "author": pr.user.login,
                "url": pr.html_url
            },
            "test_results": test_results
        }
        
        import os
        from ..config import REPORTS_DIR
        os.makedirs(REPORTS_DIR, exist_ok=True)
        report_path = os.path.join(REPORTS_DIR, f"report_{timestamp}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        try:
            self.client.files_upload_v2(
                channel=self.channel,
                file=report_path,
                title=f"Detailed Report - {timestamp}",
                thread_ts=thread_ts
            )
        except Exception as e:
            print(f"Report upload error: {e}")
    
    def send_error_notification(self, pr, error_message):
        """에러 알림 전송"""
        try:
            self.client.chat_postMessage(
                channel=self.channel,
                text=f"🚨 *NightWatch Pipeline Error*\n\nPR: #{pr.number} {pr.title}\nError: ```{error_message}```"
            )
        except SlackApiError as e:
            print(f"Slack error notification failed: {e}")

