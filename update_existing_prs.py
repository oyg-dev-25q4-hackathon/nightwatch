#!/usr/bin/env python3
"""
기존 테스트 레코드의 PR 제목과 브랜치 정보 업데이트
"""
import sys
import os
from github import Github

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.models import init_db, get_db, Test, Subscription
from server.services.pat_auth_service import PATAuthService

def update_existing_prs():
    """기존 테스트 레코드의 PR 정보 업데이트"""
    init_db()
    db = next(get_db())
    pat_auth = PATAuthService()
    
    try:
        # pr_title이나 branch_name이 없는 테스트 조회
        tests = db.query(Test).filter(
            (Test.pr_title == None) | (Test.branch_name == None)
        ).all()
        
        print(f"📋 업데이트할 테스트 레코드: {len(tests)}개\n")
        
        if not tests:
            print("✅ 모든 테스트 레코드가 이미 업데이트되어 있습니다!")
            return
        
        updated_count = 0
        error_count = 0
        
        for test in tests:
            try:
                # 구독 정보 가져오기
                subscription = db.query(Subscription).filter(
                    Subscription.id == test.subscription_id
                ).first()
                
                if not subscription:
                    print(f"⚠️ 구독 정보를 찾을 수 없습니다 (test_id: {test.id})")
                    continue
                
                # PAT 가져오기 (실패해도 계속 진행)
                pat = None
                try:
                    if subscription.user_credential_id:
                        credential = pat_auth.get_credential_by_id(subscription.user_credential_id)
                        if credential:
                            pat = pat_auth.get_decrypted_pat(credential.user_id)
                except Exception as e:
                    print(f"  ⚠️ PAT 복호화 실패 (계속 진행): {str(e)}")
                
                # GitHub API 연결
                try:
                    if pat:
                        g = Github(pat)
                    else:
                        g = Github()
                except Exception as e:
                    print(f"  ❌ GitHub API 연결 실패: {str(e)}")
                    raise
                
                # PR 정보 가져오기
                repo = g.get_repo(test.repo_full_name)
                pr = repo.get_pull(test.pr_number)
                
                # 업데이트
                needs_update = False
                if not test.pr_title:
                    test.pr_title = pr.title
                    needs_update = True
                    print(f"  ✅ PR #{test.pr_number}: 제목 업데이트 - {pr.title[:50]}")
                
                if not test.branch_name:
                    test.branch_name = pr.head.ref
                    needs_update = True
                    print(f"  ✅ PR #{test.pr_number}: 브랜치 업데이트 - {pr.head.ref}")
                
                if needs_update:
                    db.commit()
                    updated_count += 1
                else:
                    print(f"  ℹ️ PR #{test.pr_number}: 이미 업데이트됨")
                    
            except Exception as e:
                error_count += 1
                error_msg = str(e) if str(e) else type(e).__name__
                print(f"  ❌ PR #{test.pr_number} 업데이트 실패: {error_msg}")
                import traceback
                traceback.print_exc()
                db.rollback()
        
        print(f"\n✅ 완료: {updated_count}개 업데이트, {error_count}개 실패")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_existing_prs()

