#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.models import init_db, get_db, Base, engine, Test, Subscription, UserCredential

def reset_database():
    """데이터베이스 초기화"""
    print("⚠️ 경고: 이 작업은 모든 데이터를 삭제합니다!")
    print("계속하시겠습니까? (yes/no): ", end="")
    response = input().strip().lower()
    
    if response != 'yes':
        print("❌ 취소되었습니다.")
        return
    
    print("\n🗑️ 데이터베이스 초기화 중...")
    
    # 모든 테이블 삭제
    Base.metadata.drop_all(bind=engine)
    print("✅ 기존 테이블 삭제 완료")
    
    # 모든 테이블 재생성
    Base.metadata.create_all(bind=engine)
    print("✅ 테이블 재생성 완료")
    
    print("\n✅ 데이터베이스 초기화 완료!")

def clean_unnecessary_data():
    """불필요한 데이터 정리"""
    init_db()
    db = next(get_db())
    
    try:
        print("🧹 불필요한 데이터 정리 중...\n")
        
        # 1. 완료된 오래된 테스트 삭제 (30일 이상)
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_tests = db.query(Test).filter(
            Test.status.in_(['completed', 'failed']),
            Test.completed_at < cutoff_date
        ).all()
        
        if old_tests:
            print(f"📋 삭제할 오래된 테스트: {len(old_tests)}개")
            for test in old_tests:
                db.delete(test)
            db.commit()
            print(f"✅ {len(old_tests)}개의 오래된 테스트 삭제 완료")
        else:
            print("ℹ️ 삭제할 오래된 테스트 없음")
        
        # 2. 비활성화된 구독 확인
        inactive_subs = db.query(Subscription).filter(
            Subscription.is_active == False
        ).all()
        
        if inactive_subs:
            print(f"\n📋 비활성화된 구독: {len(inactive_subs)}개")
            for sub in inactive_subs:
                print(f"   - {sub.repo_full_name} (ID: {sub.id})")
            print("   (비활성화된 구독은 유지됩니다)")
        else:
            print("\nℹ️ 비활성화된 구독 없음")
        
        # 3. 사용되지 않는 인증 정보 확인
        used_cred_ids = {sub.user_credential_id for sub in db.query(Subscription).filter(
            Subscription.user_credential_id != None
        ).all()}
        
        all_creds = db.query(UserCredential).all()
        unused_creds = [cred for cred in all_creds if cred.id not in used_cred_ids]
        
        if unused_creds:
            print(f"\n📋 사용되지 않는 인증 정보: {len(unused_creds)}개")
            for cred in unused_creds:
                print(f"   - User ID: {cred.user_id} (ID: {cred.id})")
            
            print("\n삭제하시겠습니까? (yes/no): ", end="")
            response = input().strip().lower()
            if response == 'yes':
                for cred in unused_creds:
                    db.delete(cred)
                db.commit()
                print(f"✅ {len(unused_creds)}개의 사용되지 않는 인증 정보 삭제 완료")
        else:
            print("\nℹ️ 사용되지 않는 인증 정보 없음")
        
        # 4. pr_title이나 branch_name이 없는 테스트 통계
        tests_without_info = db.query(Test).filter(
            (Test.pr_title == None) | (Test.branch_name == None)
        ).all()
        
        if tests_without_info:
            print(f"\n📋 PR 정보가 불완전한 테스트: {len(tests_without_info)}개")
            for test in tests_without_info:
                print(f"   - PR #{test.pr_number} (제목: {test.pr_title}, 브랜치: {test.branch_name})")
        
        print("\n✅ 데이터 정리 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        reset_database()
    else:
        clean_unnecessary_data()

