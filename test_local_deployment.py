#!/usr/bin/env python3
"""
로컬 배포 테스트 스크립트
실제 PR을 감지하고 로컬 배포를 테스트합니다.
"""
import sys
import os
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from server.models import init_db, get_db, Subscription
from server.services.polling_service import PollingService
from github import Github

def test_local_deployment():
    """로컬 배포 테스트"""
    print("=" * 60)
    print("🧪 로컬 배포 테스트 시작")
    print("=" * 60)
    print()
    
    # 환경 변수 확인
    deployment_mode = os.getenv('DEPLOYMENT_MODE', 'local')
    print(f"📋 배포 모드: {deployment_mode}")
    
    if deployment_mode != 'local':
        print(f"⚠️ DEPLOYMENT_MODE이 'local'이 아닙니다: {deployment_mode}")
        print("   .env 파일에서 DEPLOYMENT_MODE=local로 설정해주세요.")
        return
    
    # 데이터베이스 초기화
    init_db()
    
    # 구독 정보 확인
    db = next(get_db())
    try:
        subscriptions = db.query(Subscription).filter(
            Subscription.is_active == True
        ).all()
        
        if not subscriptions:
            print("❌ 활성 구독이 없습니다.")
            print("   프론트엔드에서 레포지토리를 구독해주세요.")
            return
        
        print(f"✅ {len(subscriptions)}개의 활성 구독 발견")
        for sub in subscriptions:
            print(f"   - {sub.repo_full_name} (ID: {sub.id})")
        print()
        
        # 첫 번째 구독으로 테스트
        subscription = subscriptions[0]
        print(f"🔍 테스트 대상: {subscription.repo_full_name}")
        print()
        
        # Polling 서비스 생성
        polling_service = PollingService()
        
        # 수동으로 PR 감지 및 테스트 실행
        print("🚀 PR 감지 및 로컬 배포 테스트 시작...")
        print()
        
        try:
            # 강제로 PR을 다시 테스트하려면 last_polled_at을 None으로 설정
            print("💡 기존 PR을 강제로 다시 테스트하려면 last_polled_at을 None으로 설정합니다...")
            subscription.last_polled_at = None
            db.commit()
            print("✅ last_polled_at이 초기화되었습니다.")
            print()
            
            detected_count, pr_list = polling_service._poll_subscription(subscription)
            
            print()
            print("=" * 60)
            if detected_count > 0:
                print(f"✅ {detected_count}개의 PR이 감지되어 테스트가 시작되었습니다!")
                for pr_info in pr_list:
                    print(f"   - PR #{pr_info['number']}: {pr_info['title']}")
                    print(f"     브랜치: {pr_info['branch']}")
                    print(f"     URL: {pr_info['url']}")
                print()
                print("📝 로컬 배포가 진행 중입니다...")
                print("   ./pr_deployments/ 디렉토리를 확인하세요.")
            else:
                print("ℹ️ 새로운 PR이 없습니다.")
                print("   💡 새로운 PR을 만들거나 기존 PR을 업데이트해보세요.")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()

if __name__ == "__main__":
    test_local_deployment()

