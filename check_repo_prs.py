#!/usr/bin/env python3
"""
레포지토리의 감지된 PR 확인 스크립트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.models import init_db, get_db, Subscription, Test
from datetime import datetime

def check_repo_prs(repo_full_name: str):
    """특정 레포지토리의 구독 정보와 감지된 PR 확인"""
    init_db()
    db = next(get_db())
    
    try:
        print(f"🔍 Checking repository: {repo_full_name}\n")
        
        # 구독 정보 조회
        subscription = db.query(Subscription).filter(
            Subscription.repo_full_name == repo_full_name
        ).first()
        
        if not subscription:
            print(f"❌ 구독 정보를 찾을 수 없습니다: {repo_full_name}")
            return
        
        print(f"✅ 구독 정보 발견:")
        print(f"   - 구독 ID: {subscription.id}")
        print(f"   - 레포지토리: {subscription.repo_full_name}")
        print(f"   - 사용자 ID: {subscription.user_id}")
        print(f"   - 생성일: {subscription.created_at}")
        print(f"   - 마지막 Polling: {subscription.last_polled_at}")
        print(f"   - 제외 브랜치: {subscription.exclude_branches}")
        print(f"   - 활성 상태: {subscription.is_active}")
        print()
        
        # 활성 상태가 False인 경우 경고
        if not subscription.is_active:
            print("⚠️ 경고: 이 구독이 비활성화되어 있어 polling에서 제외됩니다!")
            print("   활성화하시겠습니까? (y/n): ", end="")
            response = input().strip().lower()
            if response == 'y':
                subscription.is_active = True
                db.commit()
                print("✅ 구독이 활성화되었습니다!")
            print()
        
        # 테스트 기록 조회
        tests = db.query(Test).filter(
            Test.subscription_id == subscription.id
        ).order_by(Test.created_at.desc()).all()
        
        print(f"📋 감지된 PR 목록 (총 {len(tests)}개):\n")
        
        if not tests:
            print("   ⚠️ 감지된 PR이 없습니다.")
            print()
            print("💡 가능한 원인:")
            print("   1. PR이 아직 감지되지 않았습니다")
            print("   2. PR이 제외 브랜치(main)에서 생성되었습니다")
            print("   3. PR이 마지막 polling 이전에 생성되어 감지되지 않았습니다")
            print("   4. '지금 감지하기' 버튼을 눌러 수동으로 감지해보세요")
        else:
            for i, test in enumerate(tests, 1):
                print(f"   {i}. PR #{test.pr_number}")
                print(f"      - 상태: {test.status}")
                print(f"      - URL: {test.pr_url}")
                print(f"      - 생성일: {test.created_at}")
                if test.completed_at:
                    print(f"      - 완료일: {test.completed_at}")
                print()
        
        # 최근 polling 이후의 PR 확인
        if subscription.last_polled_at:
            print(f"📅 마지막 Polling 이후 생성된 PR:")
            recent_tests = [t for t in tests if t.created_at > subscription.last_polled_at]
            if recent_tests:
                for test in recent_tests:
                    print(f"   - PR #{test.pr_number} (생성: {test.created_at})")
            else:
                print("   - 없음")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    repo_name = "oyg-dev-25q4-hackathon/nightwatch"
    if len(sys.argv) > 1:
        repo_name = sys.argv[1]
    
    check_repo_prs(repo_name)
